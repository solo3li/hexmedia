import json
import logging
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from django.conf import settings
from ..models import BookProject, Character, Scene, ChatMessage, AIConfiguration, Chapter
from .gemini_service import (
    call_gemini_chat,
    analyze_book_text,
    break_into_scenes,
    generate_voice_audio,
    get_gemini_client,
    extract_chapters_from_book,
    parse_arabic_word_to_number
)
from .minio_service import upload_bytes
from .sfx_library import match_sfx
from .timeline_builder import build_designcombo_timeline

logger = logging.getLogger(__name__)

class AudioDramaState(TypedDict):
    project_id: Optional[str]
    user_prompt: str
    file_content: Optional[str]
    filename: Optional[str]
    narration_mode: Optional[str]
    action: str  # 'chat', 'upload_book', 'approve_casting', 'execute_scene', 'execute_chapter'
    tool: Optional[str]
    chapter_number: Optional[int]
    history: List[Dict[str, str]]
    
    # Outputs
    response_text: str
    msg_type: str  # 'TEXT', 'CASTING_CARD', 'SCENE_AUDIO_CARDS', 'STUDIO_LINK'
    metadata: Dict[str, Any]

def parse_file_text(file_bytes: bytes, filename: str) -> str:
    fname = filename.lower()
    if fname.endswith('.pdf'):
        from pypdf import PdfReader
        import io
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    elif fname.endswith('.epub'):
        from bs4 import BeautifulSoup
        import zipfile, io
        text = []
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            for item in z.namelist():
                if item.endswith('.html') or item.endswith('.xhtml'):
                    html = z.read(item).decode('utf-8', errors='ignore')
                    soup = BeautifulSoup(html, 'html.parser')
                    text.append(soup.get_text())
        return "\n".join(text)
    else:
        return file_bytes.decode('utf-8', errors='ignore')

import re

def find_matching_character(speaker_name: str, characters: list, default_narrator=None):
    if not characters:
        return None
    s_clean = speaker_name.strip().lower()
    # 1. Exact match
    for c in characters:
        if c.name.strip().lower() == s_clean:
            return c
    # 2. Substring match
    for c in characters:
        c_clean = c.name.strip().lower()
        if s_clean in c_clean or c_clean in s_clean:
            return c
    # 3. Check for narrator
    if any(n in s_clean for n in ["راوي", "سرد", "narrator"]):
        for c in characters:
            if c.role_type == 'NARRATOR' or "راوي" in c.name:
                return c
    return default_narrator or characters[0]

def extract_chapter_number_from_prompt(prompt: str) -> Optional[int]:
    if not prompt:
        return None
    p = prompt.strip().lower()

    # Compound Arabic numbers
    compounds = [
        ("الحادي عشر", 11), ("حادي عشر", 11),
        ("الثاني عشر", 12), ("ثاني عشر", 12),
        ("الثالث عشر", 13), ("ثالث عشر", 13),
        ("الرابع عشر", 14), ("رابع عشر", 14),
        ("الخامس عشر", 15), ("خامس عشر", 15),
        ("السادس عشر", 16), ("السادس عشر", 16),
        ("السابع عشر", 17), ("سابع عشر", 17),
        ("الثامن عشر", 18), ("ثامن عشر", 18),
        ("التاسع عشر", 19), ("تاسع عشر", 19),
        ("العشرون", 20), ("عشرون", 20), ("عشرين", 20)
    ]
    for text, val in compounds:
        if text in p:
            return val

    # Match single-token chapter references: "الفصل الأول", "فصل 2", "الفصل رقم 3", "chapter 4"
    m = re.search(r'(?:الفصل|فصل|باب|الباب|chapter|part)\s*(?:رقم\s*)?([0-9\u0660-\u0669]+|[^\s\.,!؟]+)', p)
    if m:
        val = m.group(1).strip()
        num = parse_arabic_word_to_number(val)
        if num:
            return num
    return None

def is_audio_execution_request(prompt: str) -> bool:
    if not prompt:
        return False
    p = prompt.strip().lower()

    # 1. Negative checks: Creative writing prompts or duration changes are NEVER audio executions
    writing_starters = [
        "اكتب", "ألف", "اعمل قصة", "اعمل مشهد", "اعمل حوار", "اعمل سيناريو", 
        "احكي", "سوي قصة", "قصة عن", "سيناريو عن", "حوار عن", "فكرة عن", 
        "عاوز قصة", "عايز قصة", "اريد قصة", "اقترح قصة", "ولد قصة", "ابدأ قصة",
        "ابدأ بكتابة", "ابدأ مشهد", "ارفع المشهد", "ارفع القصة", "مدد المشهد",
        "خليه", "طول"
    ]
    if any(p.startswith(w) for w in writing_starters):
        return False

    # 2. Exact match commands
    exact_cmds = [
        "نفذ", "تنفيذ", "نفذ الصوت", "توليد الصوت", "بدء التوليد", "ابدأ الصوت",
        "شغل الصوت", "طلع الصوت", "اعمل الصوت", "سمعني الصوت", "ابدأ توليد الصوت",
        "بدء الإنتاج الصوتي", "execute", "run", "produce", "play"
    ]
    if p in exact_cmds:
        return True

    # 3. Explicit audio execution keywords / chip texts
    exec_phrases = [
        "نفذ الصوت", "توليد الصوت", "توليد المشاهد الصوتية", "ابدأ توليد الصوت",
        "بدء التوليد الصوتي", "بدء الإنتاج الصوتي", "بدء توليد الصوت للمدة",
        "طلع الصوت", "اعمل الصوت", "سمعني الصوت", "شغل المشاهد الصوتية",
        "اعتماد الأصوات وتنفيذ", "تنفيذ المشاهد الصوتية", "نفذ لهذا المشهد",
        "نفذ هذا المشهد", "نفذ المشهد", "تنفيذ الفصل", "نفذ الفصل", "صوت الفصل",
        "تنفيذ صوت الفصل", "توليد صوت الفصل", "ابدأ هذا الفصل",
        "إنتاج المشاهد المصورة", "انتاج المشاهد المصورة", "توليد المشاهد المصورة",
        "توليد مشاهد الفيديو", "نفذ الفيديو", "انتاج الفيديو", "إنتاج المشاهد المصورة والصوت الآن"
    ]
    if any(phrase in p for phrase in exec_phrases):
        return True

    # 4. Starting with 'نفذ' or 'تنفيذ' that are not story creation
    if p.startswith("نفذ ") or p.startswith("تنفيذ "):
        if not any(w in p for w in ["قصة عن", "رواية عن", "سيناريو عن"]):
            return True

    # 5. Chapter execution with explicit action verbs
    if extract_chapter_number_from_prompt(p) is not None:
        if any(w in p for w in ["نفذ", "تنفيذ", "ولد", "توليد", "صوت", "ابدأ", "شغل", "أنتج", "انتاج"]):
            return True

    return False

def router_node(state: AudioDramaState) -> AudioDramaState:
    return state

def chat_node(state: AudioDramaState) -> AudioDramaState:
    prompt = state.get("user_prompt", "").strip()
    history = state.get("history", [])
    project_id = state.get("project_id")
    tool = state.get("tool")

    project = None
    if project_id:
        try:
            project = BookProject.objects.get(id=project_id)
        except BookProject.DoesNotExist:
            pass

    prompt_lower = prompt.lower()

    # 0. Check for Pause / Resume commands
    if project and any(k in prompt_lower for k in ["أوقف التوليد", "إيقاف مؤقت", "وقف التوليد", "pause"]):
        from .continuous_engine import pause_continuous_generation
        pause_continuous_generation(str(project.id))
        reply = (
            "⏸️ **تم إيقاف الإنتاج الدرامي مؤقتاً.**\n\n"
            f"📊 تم حتى الآن إنتاج **{project.scenes.count()} مشهد صوتي** بإجمالي مدة **{round(project.total_duration_seconds, 1)} ثانية**.\n"
            "يمكنك استئناف التوليد في أي وقت أو فتح المشروع في الاستوديو للمونتاج."
        )
        state["response_text"] = reply
        state["msg_type"] = "TEXT"
        state["metadata"] = {
            "project_id": str(project.id),
            "is_continuous": False,
            "status": "PAUSED",
            "action_chips": ["▶️ استئناف التوليد المستمر", "🎬 فتح استوديو DesignCombo"]
        }
        return state

    if project and any(k in prompt_lower for k in ["استأنف التوليد", "استئناف", "تابع التوليد", "كمل التوليد", "resume"]):
        from .continuous_engine import resume_continuous_generation
        resume_continuous_generation(str(project.id))
        reply = (
            "▶️ **تم استئناف الإنتاج الصوتي المستمر!**\n\n"
            f"⚡ يستمر النظام الآن في توليد بقية الفصول والمشاهد في الخلفية لمشروع **{project.title}**."
        )
        state["response_text"] = reply
        state["msg_type"] = "TEXT"
        state["metadata"] = {
            "project_id": str(project.id),
            "is_continuous": True,
            "status": "CONTINUOUS_GENERATING",
            "action_chips": ["⏸️ إيقاف مؤقت للتوليد", "🎬 فتح استوديو DesignCombo"]
        }
        return state

    # 0.1 Check if user explicitly clicked/commanded to start continuous audio/video generation
    from .continuous_engine import parse_duration_from_prompt, start_continuous_generation
    is_continuous_trigger = any(k in prompt_lower for k in [
        "بدء توليد الصوت للمدة", "بدء الإنتاج الصوتي للمدة", "ابدأ توليد الصوت للمدة", 
        "بدء توليد الصوت المستمر", "ابدأ الإنتاج المستمر", "شغل الإنتاج المستمر", "توليد الصوت للمدة",
        "إنتاج مستمر", "توليد مستمر",
        "بدء إنتاج الفيلم للمدة", "بدء إنتاج الفيلم", "ابدأ إنتاج الفيلم", "توليد الفيلم للمدة", "إنتاج الفيلم للمدة", "بدء التوليد السينمائي",
        "إنتاج المشاهد المصورة والصوت الآن"
    ])

    if is_continuous_trigger and project:
        target_dur = project.target_duration_minutes or 0
        start_continuous_generation(str(project.id), target_duration_minutes=target_dur)
        dur_label = "مفتوح ولانهائي (حتى توقفه أنت)" if target_dur == 0 else f"{target_dur} دقيقة"
        is_video = getattr(project, 'project_type', 'AUDIO_DRAMA') == 'VIDEO_STUDIO'
        
        if is_video:
            reply = (
                f"🎬 **تم بدء محرك الإنتاج السينمائي المستمر (Continuous Video Engine)!**\n\n"
                f"📖 **الفيلم:** {project.title}\n"
                f"⏱️ **الهدف الزمني:** {dur_label}\n\n"
                f"⚡ بدأ المخرج الذكي في توليد الكادرات البصرية 16:9 والأصوات السينمائية مشهداً تلو الآخر في الخلفية عبر **Gemini 3.8 Flash** و **Gemini TTS**.\n"
                f"🎥 ستظهر المشاهد المصورة تباعاً في الشات فور اكتمالها لتشاهدها وتستمع إليها فوراً دون انتظار!"
            )
            state["project_id"] = str(project.id)
            state["response_text"] = reply
            state["msg_type"] = "TEXT"
            state["metadata"] = {
                "project_id": str(project.id),
                "is_continuous": True,
                "project_type": "VIDEO_STUDIO",
                "target_duration_minutes": target_dur,
                "action_chips": ["⏸️ إيقاف مؤقت للتوليد", "🎬 تجميع وريندر الفيلم الكامل بـ Remotion", "🎬 فتح استوديو DesignCombo"]
            }
            return state
        else:
            reply = (
                f"🚀 **تم بدء محرك الإنتاج الدرامي المستمر (Continuous Drama Engine)!**\n\n"
                f"📖 **العمل:** {project.title}\n"
                f"⏱️ **الهدف:** {dur_label}\n\n"
                f"⚡ بدأ المخرج الذكي في تأليف وتوليد المشاهد الصوتية فصلاً تلو الآخر في الخلفية عبر **Gemini 3.8 Flash** و **Gemini TTS**.\n"
                f"🎧 ستظهر المشاهد الصوتية تباعاً في الشات فور اكتمالها لتستمع إليها فوراً دون انتظار!"
            )
            state["project_id"] = str(project.id)
            state["response_text"] = reply
            state["msg_type"] = "TEXT"
            state["metadata"] = {
                "project_id": str(project.id),
                "is_continuous": True,
                "target_duration_minutes": target_dur,
                "action_chips": ["⏸️ إيقاف مؤقت للتوليد", "🎬 فتح استوديو DesignCombo", "⬇️ تحميل الصوت الكامل"]
            }
            return state

    # 0.2 Check if user is asking to change or set duration WITHOUT starting audio generation
    target_duration = parse_duration_from_prompt(prompt)
    if target_duration is not None and project and any(k in prompt_lower for k in ["ارفع", "مدد", "خليه", "طول", "ساعة", "دقائق", "دقيقة", "مستمر", "مفتوح", "هدف", "تعديل"]):
        project.target_duration_minutes = target_duration
        project.save(update_fields=['target_duration_minutes'])
        dur_label = "مفتوح ولانهائي" if target_duration == 0 else f"{target_duration} دقيقة"
        is_video = getattr(project, 'project_type', 'AUDIO_DRAMA') == 'VIDEO_STUDIO'
        
        if is_video:
            reply = (
                f"⏱️ **تم تحديث الهدف الزمني للفيلم بنجاح: {dur_label}!**\n\n"
                f"📖 **الفيلم:** {project.title}\n"
                f"🎬 السيناريو والكاستينغ جاهزان تماماً.\n\n"
                f"اضغط على زر **'🎬 بدء إنتاج الفيلم للمدة ({dur_label})'** بالأسفل في أي وقت لتشغيل محرك التوليد السينمائي المستمر!"
            )
            chips = [
                f"🎬 بدء إنتاج الفيلم للمدة ({dur_label})",
                "⏱️ مدة مفتوحة ولانهائية",
                "🎬 تجميع وريندر الفيلم الكامل بـ Remotion",
                "🎬 فتح استوديو DesignCombo"
            ]
        else:
            reply = (
                f"⏱️ **تم تحديث الهدف الزمني للعمل بنجاح: {dur_label}!**\n\n"
                f"📖 **العمل:** {project.title}\n"
                f"📝 السيناريو والشخصيات جاهزة تماماً للمراجعة.\n\n"
                f"اضغط على زر **'🎙️ بدء توليد الصوت للمدة المطلوبة ({dur_label})'** بالأسفل في أي وقت لتشغيل محرك الصوت الفعلي!"
            )
            chips = [
                f"🎙️ بدء توليد الصوت للمدة المطلوبة ({dur_label})",
                "🎙️ نفذ الصوت لهذا المشهد فقط",
                "🎭 تعديل كاستينغ الشخصيات",
                "🎬 فتح استوديو DesignCombo"
            ]

        state["project_id"] = str(project.id)
        state["response_text"] = reply
        state["msg_type"] = "TEXT"
        state["metadata"] = {
            "project_id": str(project.id),
            "project_type": project.project_type,
            "target_duration_minutes": target_duration,
            "action_chips": chips
        }
        return state

    # 0.5 Check if user is asking to change narration mode
    if project and ("راوي" in prompt_lower or "سرد" in prompt_lower or "تقديم" in prompt_lower or "ربط" in prompt_lower or "شخصيات" in prompt_lower):
        if any(k in prompt_lower for k in ["شامل", "كل جملة", "كل سطر", "كل شخصية", "full"]):
            project.narration_mode = 'FULL'
            project.save(update_fields=['narration_mode'])
            reply = (
                "🎙️ **تم تفعيل نمط (الربط الشامل - Full Attribution) بنجاح!**\n\n"
                "سيتدخل الراوي قبل **كل سطر حواري بلا استثناء** ليعلن اسم المتحدث وحالته وانفعاله بأسلوب سينمائي وصفي مشوق.\n\n"
                "اضغط على زر 'نفذ الصوت' أو ابدأ التوليد لسماع النمط الجديد فوراً!"
            )
            state["response_text"] = reply
            state["msg_type"] = "TEXT"
            state["metadata"] = {
                "project_id": str(project.id),
                "narration_mode": "FULL",
                "action_chips": ["🎙️ نفذ الصوت لهذا المشهد الآن", "🎬 فتح استوديو DesignCombo"]
            }
            return state
        elif any(k in prompt_lower for k in ["ذكي", "تحولات", "smart"]):
            project.narration_mode = 'SMART'
            project.save(update_fields=['narration_mode'])
            reply = (
                "⚡ **تم تفعيل نمط (الربط الذكي الديناميكي - Smart Transitions) بنجاح!**\n\n"
                "سيتدخل الراوي سينمائياً **عند تغير المتحدث أو التحولات المشهدية المهمة فقط**، مع ترك الحوارات السريعة تتدفق بسلاسة.\n\n"
                "اضغط على زر 'نفذ الصوت' أو ابدأ التوليد لسماع النمط الجديد!"
            )
            state["response_text"] = reply
            state["msg_type"] = "TEXT"
            state["metadata"] = {
                "project_id": str(project.id),
                "narration_mode": "SMART",
                "action_chips": ["🎙️ نفذ الصوت لهذا المشهد الآن", "🎬 فتح استوديو DesignCombo"]
            }
            return state
        elif any(k in prompt_lower for k in ["مباشر", "بدون راوي", "بدون تقديم", "none", "إلغاء تقديم"]):
            project.narration_mode = 'NONE'
            project.save(update_fields=['narration_mode'])
            reply = "🎭 **تم تفعيل نمط (الحوار المباشر - Direct Dialogue) بدون تقديم الراوي للشخصيات.**"
            state["response_text"] = reply
            state["msg_type"] = "TEXT"
            state["metadata"] = {
                "project_id": str(project.id),
                "narration_mode": "NONE",
                "action_chips": ["🎙️ نفذ الصوت لهذا المشهد الآن", "🎬 فتح استوديو DesignCombo"]
            }
            return state

    # 1. Check if user is asking to change a character's voice in the current project
    voice_names = ["puck", "charon", "kore", "fenrir", "aoede"]
    if project and ("صوت" in prompt_lower or "voice" in prompt_lower) and any(v in prompt_lower for v in voice_names):
        target_voice = None
        for v in ["Puck", "Charon", "Kore", "Fenrir", "Aoede"]:
            if v.lower() in prompt_lower:
                target_voice = v
                break
        if target_voice:
            updated_char = None
            for c in project.characters.all():
                if c.name.lower() in prompt_lower or any(word in prompt_lower for word in c.name.lower().split()):
                    c.assigned_voice = target_voice
                    c.save(update_fields=['assigned_voice'])
                    updated_char = c
                    break
            if updated_char:
                reply = (
                    f"✅ **تم تحديث صوت الشخصية بنجاح!**\n\n"
                    f"🎭 تم تعيين صوت **{target_voice}** للشخصية **{updated_char.name}**.\n\n"
                    f"اضغط على زر **'🎙️ نفذ الصوت لهذا المشهد الآن'** بالأسفل لسماع المشهد بالصوت الجديد فوراً!"
                )
                state["response_text"] = reply
                state["msg_type"] = "TEXT"
                state["metadata"] = {
                    "project_id": str(project.id),
                    "action_chips": ["🎙️ نفذ الصوت لهذا المشهد الآن", "🎬 فتح استوديو DesignCombo"]
                }
                return state

    # 2.0 Check if user EXPLICITLY requested the Video & Film Studio tool
    explicit_video_starters = [
        "أنتج فيلم", "انتج فيلم", "اصنع فيلم", "توليد فيلم", "فيلم وثائقي",
        "فيلم كرتون", "انتاج فيديو", "اصنع فيديو", "أريد عمل فيلم", "فيديو كرتوني",
        "مشهد مصور", "فيلم سينمائي", "مانجا فيديو", "فيديو مانجا", "فيديو درامي"
    ]
    is_explicit_video = (
        tool == "video_studio" or
        any(prompt.startswith(phrase) for phrase in explicit_video_starters)
    )

    if is_explicit_video:
        target_dur = parse_duration_from_prompt(prompt)
        if target_dur is None:
            target_dur = 5  # default to 5 minutes if not specified
        dur_label = "مفتوح ولانهائي" if target_dur == 0 else f"{target_dur} دقيقة"

        p_lower = prompt.lower()
        if any(w in p_lower for w in ['وثائق', 'تاريخ', 'حرب', 'شاهد', 'معركة', 'حقيقة', 'documentary', 'history']):
            v_style = 'DOCUMENTARY'
            style_label = 'فيلم وثائقي / أرشيفي واقعي'
        elif any(w in p_lower for w in ['كرتون', 'أطفال', 'أرنب', 'مضحك', 'رسوم', 'cartoon', 'pixar', 'disney', 'anime']):
            v_style = 'CARTOON'
            style_label = 'كرتون / أنيميشن بيكسار ملون'
        elif any(w in p_lower for w in ['مانجا', 'أنمي', 'كوميك', 'manga']):
            v_style = 'MANGA'
            style_label = 'مانجا / كوميك درامي'
        else:
            v_style = 'CINEMATIC'
            style_label = 'سينمائي 35mm واقعي'

        system_instruction = (
            f"أنت 'المخرج السينمائي الذكي' (AI Film Director) داخل استوديو HexMedia.\n"
            f"مهمتك إخراج وتأليف فيلم سينمائي مصور يلبي رغبة المستخدم بدقة.\n"
            f"الهدف الزمني المحدد للفيلم: {dur_label}.\n"
            f"النمط البصري المحدد: {style_label}.\n"
            "1. قم بتأليف سيناريو مصور غني يحتوي على راوٍ وشخصيات مع حوارات مشكولة بدقة ومؤثرات صوتية.\n"
            "2. صف الكادر البصري لكل لقطة (Visual Description) باللغة الإنجليزية في سياق المشهد مع الإضاءة وزاوية الكاميرا.\n"
            f"3. في نهاية النص اذكر كاستينغ الشخصيات والمدة المستهدفة ({dur_label})، وأخبر المستخدم أنه يمكنه الضغط على '🎬 بدء إنتاج الفيلم للمدة ({dur_label})' لتشغيل محرك التوليد المستمر وتوليد الكادرات البصرية والأصوات بالكامل!"
        )

        reply = call_gemini_chat(prompt, history=history, system_instruction=system_instruction)

        analysis = analyze_book_text(reply, filename="فيلم_سينمائي.txt")
        title = analysis.get("title") or "فيلم سينمائي مصور"
        summary = analysis.get("summary") or "عمل سينمائي مرئي ومسموع."
        characters_data = analysis.get("characters", [])

        n_mode = state.get("narration_mode") or "SMART"
        new_project = BookProject.objects.create(
            title=title,
            author="Gemini 3.8 Flash",
            original_filename="film_script.txt",
            raw_text=reply,
            summary=summary,
            narration_mode=n_mode,
            project_type='VIDEO_STUDIO',
            visual_style=v_style,
            target_duration_minutes=target_dur,
            status='CASTING_PENDING',
            genre='فيلم ومونتاج فيديو',
            progress_percentage=25
        )

        saved_chars = []
        for c in characters_data:
            char_obj = Character.objects.create(
                project=new_project,
                name=c.get("name", "شخصية"),
                role_type=c.get("role_type", "SUPPORTING"),
                gender=c.get("gender", "MALE"),
                description=c.get("description", ""),
                assigned_voice=c.get("assigned_voice", "Puck"),
                speaking_style=c.get("speaking_style", "سينمائي")
            )
            saved_chars.append(char_obj)

        if not any(c.role_type == 'NARRATOR' for c in saved_chars):
            narrator = Character.objects.create(
                project=new_project,
                name="الراوي",
                role_type="NARRATOR",
                gender="MALE",
                assigned_voice="Charon",
                speaking_style="وقور وسينمائي"
            )
            saved_chars.append(narrator)

        chips = [
            f"🎬 بدء إنتاج الفيلم للمدة ({dur_label})",
            "⏱️ تعديل المدة إلى 10 دقائق",
            "⏱️ مدة مفتوحة ولانهائية",
            "🎭 تعديل كاستينغ الشخصيات",
            "🎬 فتح استوديو DesignCombo"
        ]

        state["project_id"] = str(new_project.id)
        state["response_text"] = reply
        state["msg_type"] = "TEXT"
        state["metadata"] = {
            "project_id": str(new_project.id),
            "project_type": "VIDEO_STUDIO",
            "visual_style": v_style,
            "target_duration_minutes": target_dur,
            "action_chips": chips
        }
        return state

    # 2. Check if user EXPLICITLY requested the Story / Scenario Generator tool
    explicit_drama_starters = [
        "أريد تأليف سيناريو", "اريد تاليف سيناريو", "ألف سيناريو", "الف سيناريو",
        "ألف لي سيناريو", "الف لي سيناريو", "اكتب سيناريو درامي", "ألف مشهد درامي",
        "الف مشهد درامي", "ألف قصة درامية صوتية", "اكتب مشهد صوتي"
    ]
    is_explicit_story = (
        tool == "story_generator" or
        any(prompt.startswith(phrase) for phrase in explicit_drama_starters)
    )

    if is_explicit_story:
        system_instruction = (
            "أنت 'المخرج الصوتي الذكي' (Audio Drama Director) داخل استوديو HexMedia. "
            "مهمتك تأليف وإخراج دراما صوتية سينمائية مشوقة تلبي رغبة المستخدم بدقة متناهية. "
            "المستخدم يقترح موضوعاً أو قصة سيناريو. التزم تماماً بموضوعه وفكرته دون الخروج عنها مطلقاً:\n"
            "1. قم بتأليف مشهد درامي حواري سينمائي مشوق (يتضمن راوياً وشخصيتين أو ثلاث شخصيات على الأقل).\n"
            "2. ضع علامات التشكيل العربي الكاملة والواضحة على كلمات الحوار لضبط النطق بدقة في Gemini TTS.\n"
            "3. ضع المؤثرات الصوتية المقترحة بين قوسين مثل: [مؤثر صوتي: صوت إنذار الطائرة ورياح عاصفة].\n"
            "4. في نهاية النص، اعرض أسماء الشخصيات ونبرات أصواتهم المقترحة (Puck, Charon, Kore, Fenrir, Aoede).\n"
            "5. أخبر المستخدم بوضوح أنه يستطيع الضغط على '🎙️ توليد الصوت لهذا المشهد الآن' لسماع المشهد فوراً بالأصوات البشرية والمؤثرات."
        )

        reply = call_gemini_chat(prompt, history=history, system_instruction=system_instruction)

        # Dynamically extract title and characters
        analysis = analyze_book_text(reply, filename="مشهد_درامي.txt")
        title = analysis.get("title") or "مشهد درامي سينمائي"
        summary = analysis.get("summary") or "مشهد حواري درامي مشوق."
        characters_data = analysis.get("characters", [])

        # Create fresh BookProject in DB
        n_mode = state.get("narration_mode") or "SMART"
        if n_mode not in ['SMART', 'FULL', 'NONE']:
            n_mode = 'SMART'

        target_duration = parse_duration_from_prompt(prompt) or 0
        new_project = BookProject.objects.create(
            title=title,
            author="Gemini 3.8 Flash",
            original_filename="dynamic_scene.txt",
            raw_text=reply,
            summary=summary,
            narration_mode=n_mode,
            target_duration_minutes=target_duration,
            status='CASTING_PENDING',
            genre='دراما صوتية',
            progress_percentage=25
        )

        saved_chars = []
        for c in characters_data:
            char_obj = Character.objects.create(
                project=new_project,
                name=c.get("name", "شخصية"),
                role_type=c.get("role_type", "SUPPORTING"),
                gender=c.get("gender", "MALE"),
                description=c.get("description", ""),
                assigned_voice=c.get("assigned_voice", "Puck"),
                speaking_style=c.get("speaking_style", "سينمائي")
            )
            saved_chars.append(char_obj)

        if not any(c.role_type == 'NARRATOR' for c in saved_chars):
            narrator = Character.objects.create(
                project=new_project,
                name="الراوي",
                role_type="NARRATOR",
                gender="MALE",
                assigned_voice="Charon",
                speaking_style="وقور وسينمائي"
            )
            saved_chars.append(narrator)

        chips = []
        if target_duration > 0:
            chips.append(f"🎙️ بدء توليد الصوت للمدة المطلوبة ({target_duration} دقيقة)")
            chips.append("🎙️ نفذ الصوت لهذا المشهد فقط")
        else:
            chips.append("🎙️ توليد الصوت لهذا المشهد الآن")
        chips.extend(["🎭 تعديل كاستينغ الشخصيات", "🎬 فتح استوديو DesignCombo"])

        state["project_id"] = str(new_project.id)
        state["response_text"] = reply
        state["msg_type"] = "TEXT"
        state["metadata"] = {
            "project_id": str(new_project.id),
            "target_duration_minutes": target_duration,
            "action_chips": chips
        }
        return state

    # 3. Existing Audio Drama Project conversation
    if project and project.status != 'CHAT':
        chars_str = ", ".join([f"{c.name} ({c.assigned_voice})" for c in project.characters.all()])
        project_context = f"\nالسياق الحالي: نعمل على عمل درامي بعنوان '{project.title}'. الشخصيات: {chars_str}\nنص المشهد الحالي:\n{project.raw_text[:1200]}"
        
        system_instruction = (
            "أنت 'المخرج الصوتي الذكي' (Audio Drama Director) داخل استوديو HexMedia. "
            "مهمتك مساعدة المستخدم في تحسين وتعديل المشهد الحالي أو توجيه الأداء التمثيلي للعمل الدرامي. "
            "إذا اقترح المستخدم تعديلاً في الحوار، أعد كتابة الحوار المشكل بدقة، وأخبره أنه يمكنه الضغط على 'نفذ الصوت'."
            + project_context
        )

        reply = call_gemini_chat(prompt, history=history, system_instruction=system_instruction)
        
        if ":" in reply and len(reply.split()) > 20:
            project.raw_text = reply
            project.save(update_fields=['raw_text'])

        chips = []
        if project.target_duration_minutes > 0:
            chips.append(f"🎙️ بدء توليد الصوت للمدة المطلوبة ({project.target_duration_minutes} دقيقة)")
            chips.append("🎙️ نفذ الصوت لهذا المشهد فقط")
        else:
            chips.append("🎙️ توليد الصوت لهذا المشهد الآن")
        chips.extend(["🎭 تعديل كاستينغ الشخصيات", "🎬 فتح استوديو DesignCombo"])

        state["response_text"] = reply
        state["msg_type"] = "TEXT"
        state["metadata"] = {
            "project_id": str(project.id),
            "target_duration_minutes": project.target_duration_minutes,
            "action_chips": chips
        }
        return state

    # 4. DEFAULT: GENERAL AI CHAT (ChatGPT Mode - Like ChatGPT / Gemini)
    # Answers any user inquiry naturally, politely, with clean markdown and NO forced drama
    system_instruction = (
        "أنت مساعد ذكاء اصطناعي محترف، ذكي، وودود (شبيه تماماً بـ ChatGPT و Gemini). "
        "مهمتك التفاعل والتحاور بأسلوب طبيعي ومريح وسلس باللغة العربية، والإجابة عن جميع استفسارات المستخدم وأسئلته، سواء كانت نقاشات عامة، شروحات علمية، برمجية، إجابات على أسئلة، تلخيص نصوص، أو مساعدة في الأفكار. "
        "نسق إجاباتك بشكل جميل ومريح للقراءة باستخدام Markdown (عناوين، نقاط، كتل كود عند الحاجة). "
        "مهم جداً: لا تقم بتأليف سيناريو درامي أو فرض شخصيات تمثيلية أو وضع علامات تشكيل كاملة أو اقتراح أصوات ما لم يطلب المستخدم ذلك صراحة."
    )

    reply = call_gemini_chat(prompt, history=history, system_instruction=system_instruction)

    # Persist in a CHAT project so user's conversation history appears cleanly in sidebar
    if not project or project.status != 'CHAT':
        clean_prompt = prompt.strip().replace("\n", " ")
        short_title = clean_prompt[:35].rsplit(" ", 1)[0] if len(clean_prompt) > 35 else clean_prompt
        if not short_title:
            short_title = "محادثة جديدة"
        project = BookProject.objects.create(
            title=short_title,
            author="المستخدم",
            genre="محادثة عامة",
            status='CHAT'
        )

    state["project_id"] = str(project.id)
    state["response_text"] = reply
    state["msg_type"] = "TEXT"
    state["metadata"] = {
        "project_id": str(project.id)
    }
    return state

def book_ingestion_node(state: AudioDramaState) -> AudioDramaState:
    """Parses novel/story, extracts characters with Gemini, and presents interactive casting card"""
    raw_text = state.get("file_content") or state.get("user_prompt", "")
    filename = state.get("filename") or "رواية_جديدة.txt"
    
    # 1. Analyze via Gemini 3.8 Flash
    analysis = analyze_book_text(raw_text, filename=filename)
    title = analysis.get("title") or filename.rsplit('.', 1)[0]
    author = analysis.get("author", "غير معروف")
    summary = analysis.get("summary", "")
    characters_data = analysis.get("characters", [])

    # 2. Create fresh Project in DB
    n_mode = state.get("narration_mode") or "SMART"
    if n_mode not in ['SMART', 'FULL', 'NONE']:
        n_mode = 'SMART'

    project = BookProject.objects.create(
        title=title,
        author=author,
        original_filename=filename,
        raw_text=raw_text,
        summary=summary,
        narration_mode=n_mode,
        status='CASTING_PENDING',
        progress_percentage=25
    )
    state["project_id"] = str(project.id)

    # 3. Create Characters and generate voice preview samples using Gemini TTS
    saved_chars = []
    for c in characters_data:
        char_obj = Character.objects.create(
            project=project,
            name=c.get("name", "شخصية"),
            role_type=c.get("role_type", "SUPPORTING"),
            gender=c.get("gender", "MALE"),
            description=c.get("description", ""),
            assigned_voice=c.get("assigned_voice", "Puck"),
            speaking_style=c.get("speaking_style", "طبيعي وسينمائي")
        )
        sample_text = f"مرحباً، أنا {char_obj.name}، وهذا صوتي المعتمد في الرواية."
        try:
            audio_bytes = generate_voice_audio(sample_text, voice_name=char_obj.assigned_voice)
            url = upload_bytes(audio_bytes, f"samples/{project.id}/{char_obj.id}.wav")
            char_obj.sample_audio_url = url
            char_obj.save(update_fields=['sample_audio_url'])
        except Exception as e:
            logger.error(f"Sample generation error: {e}")

        saved_chars.append({
            "id": str(char_obj.id),
            "name": char_obj.name,
            "role_type": char_obj.get_role_type_display(),
            "gender": char_obj.gender,
            "description": char_obj.description,
            "assigned_voice": char_obj.assigned_voice,
            "sample_audio_url": char_obj.sample_audio_url
        })

    # 4. Extract and Save Chapters via regex or Gemini dramatic division
    chapters_data = extract_chapters_from_book(raw_text, filename=filename)
    saved_chapters = []
    for ch in chapters_data:
        ch_num = ch.get("number") or (len(saved_chapters) + 1)
        ch_obj = Chapter.objects.create(
            project=project,
            number=ch_num,
            title=ch.get("title", f"الفصل {ch_num}"),
            summary=ch.get("summary", ""),
            raw_text=ch.get("raw_text", ""),
            status='PENDING',
            scenes_count=0,
            total_duration_seconds=0.0
        )
        saved_chapters.append({
            "id": str(ch_obj.id),
            "number": ch_obj.number,
            "title": ch_obj.title,
            "summary": ch_obj.summary,
            "status": ch_obj.status,
            "scenes_count": ch_obj.scenes_count,
            "total_duration_seconds": ch_obj.total_duration_seconds
        })

    config = AIConfiguration.objects.filter(is_active=True).first()
    voices_catalog = config.available_voices if config else [
        {"name": "Puck", "gender": "male", "description": "شاب حماسي وبطولي"},
        {"name": "Charon", "gender": "male", "description": "وقور وجهوري (راوي)"},
        {"name": "Kore", "gender": "female", "description": "دافئ وهادئ"},
        {"name": "Fenrir", "gender": "male", "description": "غامض وحاد"},
        {"name": "Aoede", "gender": "female", "description": "أنثوي ناعم"},
    ]

    chapters_info = f"📚 **الفصول المستخرجة:** تم تقسيم العمل إلى **{len(saved_chapters)} فصول** درامية متسلسلة.\n" if saved_chapters else ""
    response_text = (
        f"🎉 **تم تحليل الرواية بنجاح عبر Gemini 3.8 Flash!**\n\n"
        f"📖 **العنوان:** {project.title}\n"
        f"✍️ **المؤلف:** {project.author}\n"
        f"📝 **الملخص:** {project.summary}\n\n"
        f"{chapters_info}"
        f"🎭 استخرجت **{len(saved_chars)} شخصيات** ووزعت أصوات Gemini المناسبة لكل منهم. "
        f"يمكنك استعراض الفصول وتنفيذ صوت كل فصل بشكل مستقل، أو اعتماد الأصوات لتنفيذ المشاهد!"
    )

    action_chips = []
    if saved_chapters:
        action_chips.append(f"🎙️ تنفيذ صوت الفصل الأول ({saved_chapters[0]['title'][:25]})")
        if len(saved_chapters) > 1:
            action_chips.append(f"🎙️ تنفيذ صوت الفصل الثاني")
    action_chips.extend(["🚀 اعتماد الأصوات وتنفيذ المشاهد الصوتية فوراً", "🎭 تعديل أصوات الشخصيات"])

    state["response_text"] = response_text
    state["msg_type"] = "CASTING_CARD"
    state["metadata"] = {
        "project_id": str(project.id),
        "chapters": saved_chapters,
        "characters": saved_chars,
        "available_voices": voices_catalog,
        "action_chips": action_chips
    }
    return state

def execute_scene_node(state: AudioDramaState) -> AudioDramaState:
    """Executes scene generation dynamically using Gemini 3.8 Flash LLM and Gemini TTS"""
    project_id = state.get("project_id")
    user_prompt = state.get("user_prompt", "").strip()
    history = state.get("history", [])
    project = None

    if project_id:
        try:
            project = BookProject.objects.get(id=project_id)
        except BookProject.DoesNotExist:
            pass

    # Check if this execution request is intended for continuous duration production
    prompt_lower = user_prompt.lower()
    is_continuous_exec = any(k in prompt_lower for k in [
        "للمدة", "مستمر", "كامل المدة", "بدء توليد الصوت للمدة", "الإنتاج المستمر", "توليد مستمر",
        "بدء إنتاج الفيلم للمدة", "بدء إنتاج الفيلم", "إنتاج المشاهد المصورة والصوت الآن", "بدء التوليد السينمائي"
    ])
    if is_continuous_exec and project:
        from .continuous_engine import start_continuous_generation
        target_dur = project.target_duration_minutes or 0
        start_continuous_generation(str(project.id), target_duration_minutes=target_dur)
        dur_label = "مفتوح ولانهائي" if target_dur == 0 else f"{target_dur} دقيقة"
        is_video = getattr(project, 'project_type', 'AUDIO_DRAMA') == 'VIDEO_STUDIO'
        
        if is_video:
            reply = (
                f"🎬 **تم بدء محرك الإنتاج السينمائي المستمر (Continuous Video Engine)!**\n\n"
                f"📖 **الفيلم:** {project.title}\n"
                f"⏱️ **الهدف الزمني:** {dur_label}\n\n"
                f"⚡ بدأ المخرج الذكي في توليد الكادرات البصرية 16:9 والأصوات السينمائية مشهداً تلو الآخر في الخلفية عبر **Gemini 3.8 Flash** و **Gemini TTS**.\n"
                f"🎥 ستظهر المشاهد المصورة تباعاً في الشات فور اكتمالها لتشاهدها وتستمع إليها فوراً دون انتظار!"
            )
            chips = [
                "⏸️ إيقاف مؤقت للتوليد",
                "🎬 تجميع وريندر الفيلم الكامل بـ Remotion",
                "🎬 فتح استوديو DesignCombo"
            ]
        else:
            reply = (
                f"🚀 **تم بدء محرك الإنتاج الدرامي الصوتي المستمر بنجاح!**\n\n"
                f"📖 **العمل:** {project.title}\n"
                f"⏱️ **الهدف:** {dur_label}\n\n"
                f"⚡ يعمل المخرج الذكي الآن على تأليف وتوليد المشاهد الصوتية فصلاً تلو الآخر عبر **Gemini TTS**.\n"
                f"🎧 ستظهر المقاطع الصوتية الحية تباعاً في الشات للاستماع فوراً!"
            )
            chips = [
                "⏸️ إيقاف مؤقت للتوليد",
                "🎬 فتح استوديو DesignCombo",
                "⬇️ تحميل الصوت الكامل"
            ]

        state["project_id"] = str(project.id)
        state["response_text"] = reply
        state["msg_type"] = "TEXT"
        state["metadata"] = {
            "project_id": str(project.id),
            "is_continuous": True,
            "project_type": getattr(project, 'project_type', 'AUDIO_DRAMA'),
            "target_duration_minutes": target_dur,
            "action_chips": chips
        }
        return state

    # Check if project has chapters: route to execute_chapter_node
    if project and project.chapters.exists():
        ch_num = state.get("chapter_number") or extract_chapter_number_from_prompt(user_prompt) or 1
        state["chapter_number"] = ch_num
        return execute_chapter_node(state)

    # If no project exists, OR if project has no raw_text to execute, or is CHAT:
    if not project or not project.raw_text or project.status == 'CHAT':
        reply = (
            "⚠️ **لا يوجد سيناريو أو مشروع درامي لتوليد صوته حالياً.**\n\n"
            "لتوليد الصوت، يمكنك:\n"
            "1. اختيار **'✍️ تأليف وتطوير قصة وسيناريو'** من زر **(+)** بالأسفل وتحديد فكرة المشهد.\n"
            "2. أو اختيار **'📚 تحويل كتاب إلى دراما مسموعة'** لرفع رواية (PDF, EPUB, TXT)."
        )
        state["response_text"] = reply
        state["msg_type"] = "TEXT"
        state["metadata"] = {}
        return state

    # Clear old scenes to ensure fresh real audio generation
    project.scenes.all().delete()
    project.status = 'GENERATING_AUDIO'
    project.save(update_fields=['status'])

    characters = list(project.characters.all())
    if not characters:
        Character.objects.create(project=project, name="الراوي", assigned_voice="Charon", role_type="NARRATOR")
        Character.objects.create(project=project, name="الكابتن", assigned_voice="Fenrir", role_type="PROTAGONIST")
        Character.objects.create(project=project, name="المساعد", assigned_voice="Puck", role_type="SUPPORTING")
        characters = list(project.characters.all())

    char_names = [c.name for c in characters]
    narrator = project.characters.filter(role_type='NARRATOR').first() or characters[0]

    # Break novel into scenes with diacritics and cinematic narrator lead-ins using Gemini
    scenes_data = break_into_scenes(project.raw_text, char_names, narration_mode=project.narration_mode or 'SMART')

    # Generate REAL voice audio for each scene via Gemini TTS (parallelized)
    from concurrent.futures import ThreadPoolExecutor

    def synthesize_scene_task(item):
        idx, sc = item
        speaker_name = sc.get("speaker_name", "الراوي").strip()
        matched_char = find_matching_character(speaker_name, characters, narrator)
        text = sc.get("raw_text", "")
        emotion = sc.get("emotion", "calm")
        sfx_req = sc.get("sfx_name", "")

        sfx_key, _ = match_sfx(text)
        if not sfx_key and sfx_req:
            sfx_key = sfx_req
        sfx_url = f"{settings.MINIO_PUBLIC_ENDPOINT}/{settings.MINIO_BUCKET}/sfx/{sfx_key}.wav" if sfx_key else ""

        # Call real Gemini TTS!
        audio_bytes = generate_voice_audio(text, voice_name=matched_char.assigned_voice, emotion=emotion)
        audio_url = upload_bytes(audio_bytes, f"audio/{project.id}/scene_{idx+1}.wav")
        duration = max(2.5, min(15.0, len(text.split()) * 0.45))

        # Visual / Video Scene Card Generation
        from .visual_service import produce_scene_visual
        visual_url = ""
        visual_prompt = sc.get("visual_prompt") or f"{speaker_name}: {text[:90]}"
        media_type = "AI_IMAGE"
        motion_type = "zoom_in"

        if getattr(project, 'project_type', 'AUDIO_DRAMA') == 'VIDEO_STUDIO' or sc.get("visual_prompt"):
            v_res = produce_scene_visual(
                scene_id=f"{project.id}_{idx+1}",
                raw_prompt=visual_prompt,
                visual_style=getattr(project, 'visual_style', 'AUTO'),
                character_dna=matched_char.description or ""
            )
            visual_url = v_res.get("image_url", "")
            media_type = v_res.get("media_type", "AI_IMAGE")
            motion_type = v_res.get("motion_type", "zoom_in")
            visual_prompt = v_res.get("visual_prompt", visual_prompt)

        return {
            "idx": idx,
            "matched_char": matched_char,
            "text": text,
            "emotion": emotion,
            "sfx_key": sfx_key,
            "sfx_url": sfx_url,
            "audio_url": audio_url,
            "visual_url": visual_url,
            "visual_prompt": visual_prompt,
            "media_type": media_type,
            "motion_type": motion_type,
            "duration": duration
        }

    with ThreadPoolExecutor(max_workers=5) as executor:
        synth_results = list(executor.map(synthesize_scene_task, enumerate(scenes_data)))
    synth_results.sort(key=lambda x: x["idx"])

    scenes_list = []
    for item in synth_results:
        scene_obj = Scene.objects.create(
            project=project,
            order=item["idx"] + 1,
            speaker=item["matched_char"],
            speaker_name=item["matched_char"].name,
            raw_text=item["text"],
            vocalized_text=item["text"],
            emotion=item["emotion"],
            audio_url=item["audio_url"],
            image_url=item.get("visual_url", ""),
            visual_prompt=item.get("visual_prompt", ""),
            media_type=item.get("media_type", "AI_IMAGE"),
            motion_type=item.get("motion_type", "zoom_in"),
            duration_seconds=item["duration"],
            sfx_name=item["sfx_key"],
            sfx_url=item["sfx_url"],
            status='GENERATED'
        )

        scenes_list.append({
            "id": str(scene_obj.id),
            "order": scene_obj.order,
            "speaker_name": scene_obj.speaker_name,
            "voice": item["matched_char"].assigned_voice,
            "raw_text": scene_obj.raw_text,
            "vocalized_text": scene_obj.vocalized_text or scene_obj.raw_text,
            "audio_url": scene_obj.audio_url,
            "image_url": scene_obj.image_url,
            "visual_prompt": scene_obj.visual_prompt,
            "media_type": scene_obj.media_type,
            "motion_type": scene_obj.motion_type,
            "duration": round(scene_obj.duration_seconds, 1),
            "sfx_name": scene_obj.sfx_name or ""
        })

    # Build DesignCombo timeline
    build_designcombo_timeline(project)
    project.status = 'READY'
    project.progress_percentage = 100
    project.save(update_fields=['status', 'progress_percentage'])

    is_video = getattr(project, 'project_type', 'AUDIO_DRAMA') == 'VIDEO_STUDIO'
    if is_video:
        response_text = (
            f"🎬 **تم إنتاج وتجهيز المشاهد المصورة والصوتية بنجاح!**\n\n"
            f"📖 **الفيلم:** {project.title}\n"
            f"🎥 تم إخراج **{len(scenes_list)} مشهد مصور** بجودة عالية وأصوات حية متزامنة. "
            f"عاين الكادرات بالأسفل، أو اضغط **'🎬 تجميع وريندر الفيلم الكامل بـ Remotion'**:"
        )
        state["response_text"] = response_text
        state["msg_type"] = "SCENE_VIDEO_CARDS"
        state["metadata"] = {
            "project_id": str(project.id),
            "project_type": "VIDEO_STUDIO",
            "visual_style": getattr(project, 'visual_style', 'AUTO'),
            "scenes": scenes_list,
            "action_chips": [
                "🎬 تجميع وريندر الفيلم الكامل بـ Remotion",
                "▶️ تشغيل كل المشاهد بالتتابع",
                "🔄 إعادة توليد الكادرات",
                "🎬 فتح استوديو DesignCombo"
            ]
        }
        return state

    response_text = (
        f"🎙️ **تم تنفيذ وتوليد المشاهد الصوتية بنجاح عبر Gemini 3.8 Flash TTS!**\n\n"
        f"📖 **العمل:** {project.title}\n"
        f"🎧 تم توليد **{len(scenes_list)} مقطع صوتي حي** بأصوات الشخصيات والمؤثرات. "
        f"استمع لكل مشهد بالأسفل، أو اضغط **'▶️ تشغيل كل المشاهد بالتتابع'** لسماعها كدراما متواصلة:"
    )

    state["response_text"] = response_text
    state["msg_type"] = "SCENE_AUDIO_CARDS"
    state["metadata"] = {
        "project_id": str(project.id),
        "scenes": scenes_list,
        "action_chips": [
            "🎬 فتح استوديو DesignCombo",
            "⬇️ تحميل الصوت الكامل",
            "🔄 إعادة التوليد بنبرة مختلفة",
            "🎙️ ألف ونفذ مشهداً جديداً"
        ]
    }
    return state

def execute_chapter_node(state: AudioDramaState) -> AudioDramaState:
    """Executes scene generation dynamically for a specific chapter using Gemini 3.8 Flash and Gemini TTS"""
    project_id = state.get("project_id")
    user_prompt = state.get("user_prompt", "").strip()
    chapter_number = state.get("chapter_number")

    if not chapter_number:
        chapter_number = extract_chapter_number_from_prompt(user_prompt) or 1

    project = None
    if project_id:
        try:
            project = BookProject.objects.get(id=project_id)
        except BookProject.DoesNotExist:
            pass

    if not project:
        return execute_scene_node(state)

    chapter = project.chapters.filter(number=chapter_number).first()
    if not chapter:
        chapter = project.chapters.first()

    if not chapter:
        chapter = Chapter.objects.create(
            project=project,
            number=1,
            title=f"الفصل الأول: {project.title}",
            summary=project.summary or "",
            raw_text=project.raw_text or "",
            status='PENDING'
        )

    chapter.status = 'GENERATING'
    chapter.save(update_fields=['status'])
    project.status = 'GENERATING_AUDIO'
    project.save(update_fields=['status'])

    # Delete existing scenes for this specific chapter so they are freshly generated
    project.scenes.filter(chapter=chapter.number).delete()

    characters = list(project.characters.all())
    if not characters:
        narrator = Character.objects.create(project=project, name="الراوي", assigned_voice="Charon", role_type="NARRATOR")
        hero = Character.objects.create(project=project, name="البطل", assigned_voice="Fenrir", role_type="PROTAGONIST")
        characters = [narrator, hero]

    char_names = [c.name for c in characters]
    narrator = project.characters.filter(role_type='NARRATOR').first() or characters[0]

    # Break chapter text into scenes with diacritics and narration lead-in
    raw_text_to_break = chapter.raw_text or project.raw_text
    scenes_data = break_into_scenes(raw_text_to_break, char_names, narration_mode=project.narration_mode or 'SMART')

    total_ch_dur = 0.0
    created_scenes = []

    from concurrent.futures import ThreadPoolExecutor

    def synthesize_chapter_scene_task(item):
        idx, sc = item
        speaker_name = sc.get("speaker_name", "الراوي").strip()
        matched_char = find_matching_character(speaker_name, characters, narrator)
        text = sc.get("raw_text", "")
        emotion = sc.get("emotion", "calm")
        sfx_req = sc.get("sfx_name", "")

        sfx_key, _ = match_sfx(text)
        if not sfx_key and sfx_req:
            sfx_key = sfx_req
        sfx_url = f"{settings.MINIO_PUBLIC_ENDPOINT}/{settings.MINIO_BUCKET}/sfx/{sfx_key}.wav" if sfx_key else ""

        # Call real Gemini TTS!
        audio_bytes = generate_voice_audio(text, voice_name=matched_char.assigned_voice, emotion=emotion)
        audio_url = upload_bytes(audio_bytes, f"audio/{project.id}/ch{chapter.number}_scene_{idx+1}.wav")
        duration = max(2.5, min(15.0, len(text.split()) * 0.45))

        # Visual / Video Scene Card Generation
        from .visual_service import produce_scene_visual
        visual_url = ""
        visual_prompt = sc.get("visual_prompt") or f"{speaker_name}: {text[:90]}"
        media_type = "AI_IMAGE"
        motion_type = "zoom_in"

        if getattr(project, 'project_type', 'AUDIO_DRAMA') == 'VIDEO_STUDIO' or sc.get("visual_prompt"):
            v_res = produce_scene_visual(
                scene_id=f"{project.id}_ch{chapter.number}_{idx+1}",
                raw_prompt=visual_prompt,
                visual_style=getattr(project, 'visual_style', 'AUTO'),
                character_dna=matched_char.description or ""
            )
            visual_url = v_res.get("image_url", "")
            media_type = v_res.get("media_type", "AI_IMAGE")
            motion_type = v_res.get("motion_type", "zoom_in")
            visual_prompt = v_res.get("visual_prompt", visual_prompt)

        return {
            "idx": idx,
            "matched_char": matched_char,
            "text": text,
            "emotion": emotion,
            "sfx_key": sfx_key,
            "sfx_url": sfx_url,
            "audio_url": audio_url,
            "visual_url": visual_url,
            "visual_prompt": visual_prompt,
            "media_type": media_type,
            "motion_type": motion_type,
            "duration": duration
        }

    with ThreadPoolExecutor(max_workers=5) as executor:
        synth_results = list(executor.map(synthesize_chapter_scene_task, enumerate(scenes_data)))
    synth_results.sort(key=lambda x: x["idx"])

    for item in synth_results:
        total_ch_dur += item["duration"]
        scene_obj = Scene.objects.create(
            project=project,
            chapter=chapter.number,
            chapter_obj=chapter,
            order=item["idx"] + 1,
            speaker=item["matched_char"],
            speaker_name=item["matched_char"].name,
            raw_text=item["text"],
            vocalized_text=item["text"],
            emotion=item["emotion"],
            audio_url=item["audio_url"],
            image_url=item.get("visual_url", ""),
            visual_prompt=item.get("visual_prompt", ""),
            media_type=item.get("media_type", "AI_IMAGE"),
            motion_type=item.get("motion_type", "zoom_in"),
            duration_seconds=item["duration"],
            sfx_name=item["sfx_key"],
            sfx_url=item["sfx_url"],
            status='GENERATED'
        )
        created_scenes.append(scene_obj)

    # Re-index all scenes across project sequentially by chapter and creation time
    all_scenes_qs = project.scenes.all().order_by('chapter', 'created_at', 'id')
    for seq_idx, sc in enumerate(all_scenes_qs):
        if sc.order != seq_idx + 1:
            sc.order = seq_idx + 1
            sc.save(update_fields=['order'])

    chapter.scenes_count = len(created_scenes)
    chapter.total_duration_seconds = total_ch_dur
    chapter.status = 'READY'
    chapter.save(update_fields=['scenes_count', 'total_duration_seconds', 'status'])

    # Update project total duration and status
    total_proj_dur = sum(s.duration_seconds for s in project.scenes.filter(status='GENERATED'))
    project.total_duration_seconds = total_proj_dur
    project.status = 'READY'
    project.progress_percentage = 100
    project.save(update_fields=['total_duration_seconds', 'status', 'progress_percentage'])

    # Build DesignCombo timeline
    build_designcombo_timeline(project)

    # Prepare scenes list for chat response
    scenes_list = []
    for sc in project.scenes.filter(chapter=chapter.number).order_by('order'):
        scenes_list.append({
            "id": str(sc.id),
            "order": sc.order,
            "chapter": sc.chapter,
            "speaker_name": sc.speaker_name,
            "voice": sc.speaker.assigned_voice if sc.speaker else "Gemini",
            "raw_text": sc.raw_text,
            "vocalized_text": sc.vocalized_text or sc.raw_text,
            "audio_url": sc.audio_url,
            "image_url": sc.image_url,
            "visual_prompt": sc.visual_prompt,
            "media_type": sc.media_type,
            "motion_type": sc.motion_type,
            "duration": round(sc.duration_seconds, 1),
            "sfx_name": sc.sfx_name or ""
        })

    # Prepare chapters metadata
    all_chapters = [{
        "id": str(ch.id),
        "number": ch.number,
        "title": ch.title,
        "summary": ch.summary,
        "status": ch.status,
        "scenes_count": ch.scenes_count,
        "total_duration_seconds": round(ch.total_duration_seconds, 1)
    } for ch in project.chapters.all().order_by('number')]

    # Check next chapter
    next_chapter = project.chapters.filter(number__gt=chapter.number).order_by('number').first()

    is_video = getattr(project, 'project_type', 'AUDIO_DRAMA') == 'VIDEO_STUDIO' or any(s.get("image_url") for s in scenes_list)
    if is_video:
        chips = ["🎬 تجميع وريندر الفيلم الكامل بـ Remotion", "▶️ تشغيل كل المشاهد بالتتابع"]
        if next_chapter:
            chips.append(f"🎬 إنتاج مشاهد {next_chapter.title}")
        chips.extend(["🔄 إعادة توليد الكادرات", "🎬 فتح استوديو DesignCombo"])

        response_text = (
            f"🎬 **تم إنتاج وتجهيز المشاهد المصورة والصوتية لـ ({chapter.title}) بنجاح!**\n\n"
            f"📖 **الفيلم:** {project.title}\n"
            f"📑 **الفصل:** {chapter.title}\n"
            f"🎥 تم إخراج **{len(scenes_list)} مشهد مصور** بجودة عالية وأصوات حية متزامنة.\n\n"
            f"عاين الكادرات بالأسفل أو اضغط **'🎬 تجميع وريندر الفيلم الكامل بـ Remotion'**:"
        )
        state["response_text"] = response_text
        state["msg_type"] = "SCENE_VIDEO_CARDS"
        state["metadata"] = {
            "project_id": str(project.id),
            "chapter_number": chapter.number,
            "chapter_title": chapter.title,
            "chapters": all_chapters,
            "scenes": scenes_list,
            "action_chips": chips
        }
        return state

    chips = []
    if next_chapter:
        chips.append(f"🎙️ تنفيذ صوت {next_chapter.title}")
    chips.extend(["🎬 فتح استوديو DesignCombo", "⬇️ تحميل العمل الصوتي الكامل"])

    response_text = (
        f"🎙️ **تم تنفيذ وتوليد المشاهد الصوتية لـ ({chapter.title}) بنجاح عبر Gemini TTS!**\n\n"
        f"📖 **العمل:** {project.title}\n"
        f"📑 **الفصل:** {chapter.title}\n"
        f"⏱️ **المدة:** {round(total_ch_dur, 1)} ثانية • **المشاهد:** {len(scenes_list)} مشهد صوتي\n\n"
        f"استمع لكل مشهد بالأسفل أو اضغط **'▶️ تشغيل كل مشاهد الفصل بالتتابع'**:"
    )

    state["response_text"] = response_text
    state["msg_type"] = "SCENE_AUDIO_CARDS"
    state["metadata"] = {
        "project_id": str(project.id),
        "chapter_number": chapter.number,
        "chapter_title": chapter.title,
        "chapters": all_chapters,
        "scenes": scenes_list,
        "action_chips": chips
    }
    return state

# LangGraph Construction
def build_audio_drama_graph():
    builder = StateGraph(AudioDramaState)
    builder.add_node("router", router_node)
    builder.add_node("chat_agent", chat_node)
    builder.add_node("book_ingestion", book_ingestion_node)
    builder.add_node("execute_scene", execute_scene_node)
    builder.add_node("execute_chapter", execute_chapter_node)

    def route_action(state: AudioDramaState):
        action = state.get("action", "")
        tool = state.get("tool")
        prompt = state.get("user_prompt", "").lower().strip()
        project_id = state.get("project_id")
        
        if action == "execute_chapter":
            return "execute_chapter"
        elif action == "upload_book" or state.get("file_content"):
            return "book_ingestion"
        elif action in ["approve_casting", "execute_scene"]:
            ch_num = state.get("chapter_number") or extract_chapter_number_from_prompt(prompt)
            if ch_num:
                return "execute_chapter"
            return "execute_scene"

        # Check explicit audio execution commands (clicks or specific commands)
        if (is_audio_execution_request(prompt) or tool == "execute_audio") and project_id:
            try:
                p = BookProject.objects.get(id=project_id)
                if p.status != 'CHAT' and (p.scenes.exists() or p.raw_text):
                    ch_num = state.get("chapter_number") or extract_chapter_number_from_prompt(prompt)
                    if ch_num:
                        return "execute_chapter"
                    return "execute_scene"
            except BookProject.DoesNotExist:
                pass

        return "chat_agent"

    builder.set_entry_point("router")
    builder.add_conditional_edges(
        "router",
        route_action,
        {
            "book_ingestion": "book_ingestion",
            "execute_scene": "execute_scene",
            "execute_chapter": "execute_chapter",
            "chat_agent": "chat_agent",
        }
    )
    builder.add_edge("book_ingestion", END)
    builder.add_edge("execute_scene", END)
    builder.add_edge("execute_chapter", END)
    builder.add_edge("chat_agent", END)

    return builder.compile()

audio_drama_agent = build_audio_drama_graph()
