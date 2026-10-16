import json
import logging
import re
import threading
import time
from typing import Optional, Dict, Any
from django.conf import settings
from ..models import BookProject, Character, Scene, TimelineState
from .gemini_service import (
    get_gemini_client,
    call_gemini_chat,
    break_into_scenes,
    generate_voice_audio,
    analyze_book_text
)
from .minio_service import upload_bytes
from .sfx_library import match_sfx
from .timeline_builder import build_designcombo_timeline
from google.genai import types

logger = logging.getLogger(__name__)

# Registry for active background threads
ACTIVE_WORKERS: Dict[str, threading.Thread] = {}
WORKER_LOCK = threading.Lock()

def find_matching_character(speaker_name: str, characters: list, default_narrator=None):
    if not characters:
        return None
    s_clean = speaker_name.strip().lower()
    for c in characters:
        if c.name.strip().lower() == s_clean:
            return c
    for c in characters:
        c_clean = c.name.strip().lower()
        if s_clean in c_clean or c_clean in s_clean:
            return c
    if any(n in s_clean for n in ["راوي", "سرد", "narrator"]):
        for c in characters:
            if c.role_type == 'NARRATOR' or "راوي" in c.name:
                return c
    return default_narrator or characters[0]

def parse_duration_from_prompt(prompt: str) -> Optional[int]:
    """Extracts target duration in minutes from user prompt, or 0 for infinite/open-ended"""
    p = prompt.lower()

    if any(k in p for k in ["مفتوح", "لانهائي", "غير محدود", "بدون توقف", "مستمر", "1000 ساعة", "الف ساعة", "مفتوحة"]):
        return 0  # 0 means infinite / open-ended

    # Hours check
    hour_match = re.search(r'(\d+)\s*(ساعات|ساعة)', p)
    if hour_match:
        return int(hour_match.group(1)) * 60
    if "ساعتين" in p or "ساعتان" in p:
        return 120
    if "نصف ساعة" in p or "نص ساعة" in p:
        return 30
    if "ساعة" in p:
        return 60

    # Minutes check
    min_match = re.search(r'(\d+)\s*(دقائق|دقيقة|د)', p)
    if min_match:
        return int(min_match.group(1))

    return None

def continuous_generation_worker(project_id: str):
    """Background worker that continuously produces dramatic acts, synthesizes TTS, and streams scenes"""
    logger.info(f"Starting continuous generation worker for project {project_id}")
    
    try:
        project = BookProject.objects.get(id=project_id)
    except BookProject.DoesNotExist:
        logger.error(f"Project {project_id} not found.")
        return

    client, config = get_gemini_client()

    while True:
        # 1. Refresh project state from DB
        try:
            project.refresh_from_db()
        except Exception:
            break

        if project.status in ['PAUSED', 'FAILED']:
            logger.info(f"Worker for {project_id} paused or stopped (status={project.status}).")
            break

        # Check if duration target reached (unless target is 0 for infinite)
        if project.target_duration_minutes > 0:
            target_secs = project.target_duration_minutes * 60
            if project.total_duration_seconds >= target_secs:
                logger.info(f"Target duration {target_secs}s reached for project {project_id}.")
                project.status = 'READY'
                project.progress_percentage = 100
                project.save(update_fields=['status', 'progress_percentage'])
                break

        # 2. Prepare Story Bible & context for Act N
        characters = list(project.characters.all())
        if not characters:
            Character.objects.create(project=project, name="الراوي", assigned_voice="Charon", role_type="NARRATOR")
            Character.objects.create(project=project, name="البطل", assigned_voice="Fenrir", role_type="PROTAGONIST")
            characters = list(project.characters.all())

        char_names = [c.name for c in characters]
        narrator = project.characters.filter(role_type='NARRATOR').first() or characters[0]
        char_desc = ", ".join([f"{c.name} ({c.assigned_voice})" for c in characters])

        bible = project.story_bible or {}
        recap = bible.get("recap", project.summary or "")
        current_act = project.current_act

        narration_mode = project.narration_mode or "SMART"
        if narration_mode == "FULL":
            narration_rule = (
                "قاعدة الربط الصوتي (الربط الشامل): قبل كل سطر حواري لأي شخصية، يجب أن يسبقه مقطع مستقل للراوي "
                "بأسلوب سينمائي وصفي مشوق يحدد حركة الشخصية وحالتها النفسية وهيئتها "
                "(مثال: مقطع للراوي: 'الْتَفَتَتْ سَارَةُ بِذُعْرٍ نَحْوَ شَاشَاتِ الْمُرَاقَبَةِ وَصَرَخَتْ:' يليه مقطع لسارة: 'سَيِّدِي! نَفِدَ الْوَقُودُ!'). "
                "يجب إخراج مقطع الراوي كعنصر مستقل في مصفوفة JSON يسبق حوار الشخصية."
            )
        elif narration_mode == "SMART":
            narration_rule = (
                "قاعدة الربط الصوتي (الربط الذكي عند التحولات): عندما تبدأ شخصية جديدة في الكلام أو عند حدوث تحول درامي، "
                "ضع مقطعاً سينمائياً قصيراً للراوي يصف حركة المتحدث وانفعاله "
                "(مثال: مقطع للراوي: 'قَبَضَ الْكَابْتِن عَلَى الْمِقْوَدِ بِحَزْمٍ وَقَالَ:' يليه مقطع للكابتن: 'تَمَاسَكُوا!'). "
                "أما الحوارات الثنائية السريعة المتلاحقة فدعها تتدفق مباشرة دون تكرار جمل الربط لتفادي الرتابة."
            )
        else:
            narration_rule = "الحوارات مباشرة بين الشخصيات دون تقديم الراوي إلا في المشاهد السردية."

        logger.info(f"Generating Act {current_act} for project {project.title} (narration_mode={narration_mode})...")

        # 3. Generate script for Act N via Gemini 3.8 Flash
        act_prompt = f"""
أنت كاتب سيناريو ومخرج درامي صوتي ملحمي.
نحن نقوم بإنتاج عمل درامي إذاعي صوتي مستمر بعنوان: '{project.title}'.
الشخصيات المعتمدة وأصواتها: {char_desc}
نمط تقديم الراوي: {narration_mode}
قاعدة السرد: {narration_rule}

ملخص الأحداث حتى الآن:
{recap if recap else "بداية الأحداث والانطلاق في القصة."}

المطلوب:
تأليف الفصل الدرامي رقم {current_act}.
يجب أن يتكون الفصل من 4 إلى 8 مشاهد حوارية وسردية متتابعة تصعّد الأحداث والتشويق بسلاسة، مع المحافظة على اتساق الشخصيات.
لكل مشهد:
- المتحدث (يجب أن يكون من قائمة الشخصيات المعتمدة، مثل الراوي أو الشخصيات الحوارية).
- النص مع التشكيل العربي الكامل والواضح لكل الكلمات لضبط نطق Gemini TTS بدقة.
- المشاعر (emotion).
- المؤثر الصوتي المقترح (sfx_name).

أخرج مصفوفة JSON نقية فقط بالهيكل التالي:
[
  {{
    "speaker_name": "اسم الشخصية",
    "raw_text": "النَّصُّ مَعَ التَّشْكِيلِ الْكَامِلِ...",
    "emotion": "urgent and dramatic",
    "sfx_name": "thunder"
  }}
]
"""
        scenes_data = []
        if client:
            try:
                response = client.models.generate_content(
                    model=config.llm_model or "gemini-3.8-flash",
                    contents=act_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.7
                    )
                )
                scenes_data = json.loads(response.text)
            except Exception as e:
                logger.error(f"Error generating act script: {e}")

        if not scenes_data or not isinstance(scenes_data, list):
            # Fallback scenes
            scenes_data = [
                {"speaker_name": "الراوي", "raw_text": f"تَتَسَارَعُ الأَحْدَاثُ فِي الفَصْلِ {current_act} مَعَ تَصَاعُدِ الخَطَرِ...", "emotion": "dramatic", "sfx_name": "suspense_drone"}
            ]

        # 4. Synthesize TTS and stream each scene individually
        last_order = project.scenes.count()
        new_act_text = []

        for idx, sc in enumerate(scenes_data):
            # Check pause status before synthesizing next line
            project.refresh_from_db()
            if project.status == 'PAUSED':
                logger.info(f"Project {project_id} paused during act synthesis.")
                return

            speaker_name = sc.get("speaker_name", "الراوي").strip()
            matched_char = find_matching_character(speaker_name, characters, narrator)
            text = sc.get("raw_text", "").strip()
            if not text:
                continue

            emotion = sc.get("emotion", "calm")
            sfx_req = sc.get("sfx_name", "")

            sfx_key, _ = match_sfx(text)
            if not sfx_key and sfx_req:
                sfx_key = sfx_req
            sfx_url = f"{settings.MINIO_PUBLIC_ENDPOINT}/{settings.MINIO_BUCKET}/sfx/{sfx_key}.wav" if sfx_key else ""

            # Call Gemini TTS!
            audio_bytes = generate_voice_audio(text, voice_name=matched_char.assigned_voice, emotion=emotion)
            scene_order = last_order + idx + 1
            audio_url = upload_bytes(audio_bytes, f"audio/{project.id}/scene_{scene_order}.wav")
            duration = max(2.5, min(20.0, len(text.split()) * 0.45))

            Scene.objects.create(
                project=project,
                order=scene_order,
                chapter=current_act,
                speaker=matched_char,
                speaker_name=matched_char.name,
                raw_text=text,
                vocalized_text=text,
                emotion=emotion,
                audio_url=audio_url,
                duration_seconds=duration,
                sfx_name=sfx_key,
                sfx_url=sfx_url,
                status='GENERATED'
            )

            project.total_duration_seconds += duration
            new_act_text.append(f"{matched_char.name}: {text}")
            
            # Progress calculation
            if project.target_duration_minutes > 0:
                target_secs = project.target_duration_minutes * 60
                project.progress_percentage = min(99, int((project.total_duration_seconds / target_secs) * 100))
            else:
                project.progress_percentage = (project.progress_percentage + 1) % 100

            project.save(update_fields=['total_duration_seconds', 'progress_percentage'])
            logger.info(f"Synthesized scene {scene_order} ({matched_char.name}, {round(duration, 1)}s). Total: {round(project.total_duration_seconds, 1)}s")

            # Update timeline state incrementally
            build_designcombo_timeline(project)

        # 5. Summarize Act N into the Story Bible recap to preserve continuity
        act_summary_prompt = f"لخص في سطرين ما حدث في هذا الفصل لاستكمال القصة:\n" + "\n".join(new_act_text[:6])
        act_summary = call_gemini_chat(act_summary_prompt, system_instruction="لخص بدقة وبدون تفاصيل زائدة.")
        
        bible["recap"] = (recap + "\n" + act_summary)[-3000:]  # Keep fresh moving window
        project.story_bible = bible
        project.current_act = current_act + 1
        project.save(update_fields=['story_bible', 'current_act'])

        logger.info(f"Completed Act {current_act}. Total runtime so far: {round(project.total_duration_seconds, 1)}s")
        time.sleep(1.0)  # Brief breathing space between acts

def start_continuous_generation(project_id: str, target_duration_minutes: Optional[int] = 5) -> BookProject:
    """Spawns or resumes background continuous drama synthesis"""
    project = BookProject.objects.get(id=project_id)
    if target_duration_minutes is not None:
        project.target_duration_minutes = target_duration_minutes

    project.status = 'CONTINUOUS_GENERATING'
    project.save(update_fields=['status', 'target_duration_minutes'])

    with WORKER_LOCK:
        existing_thread = ACTIVE_WORKERS.get(project_id)
        if existing_thread and existing_thread.is_alive():
            logger.info(f"Worker for {project_id} is already running.")
            return project

        thread = threading.Thread(
            target=continuous_generation_worker,
            args=(project_id,),
            daemon=True,
            name=f"ContinuousGenWorker-{project_id}"
        )
        ACTIVE_WORKERS[project_id] = thread
        thread.start()

    return project

def pause_continuous_generation(project_id: str) -> BookProject:
    """Pauses background generation"""
    project = BookProject.objects.get(id=project_id)
    project.status = 'PAUSED'
    project.save(update_fields=['status'])
    return project

def resume_continuous_generation(project_id: str) -> BookProject:
    """Resumes background generation"""
    return start_continuous_generation(project_id, target_duration_minutes=None)
