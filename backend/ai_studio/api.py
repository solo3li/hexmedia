import json
import uuid
from typing import Optional, List, Dict, Any
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Schema, File, Form
from ninja.files import UploadedFile
from .models import BookProject, Character, Scene, TimelineState, ChatMessage, AIConfiguration, Chapter
from .services.langgraph_controller import audio_drama_agent, parse_file_text
from .services.timeline_builder import build_designcombo_timeline
from .services.minio_service import upload_bytes

api = NinjaAPI(
    title="HexMedia Audio Drama Studio API",
    version="1.0.0",
    description="API for AI Audio Drama Studio powered by Gemini 3.8 Flash and LangGraph"
)

# Schemas
class ChatRequest(Schema):
    prompt: str
    project_id: Optional[str] = None
    session_id: Optional[str] = "default"
    narration_mode: Optional[str] = None
    tool: Optional[str] = None

class ChatResponse(Schema):
    response: str
    msg_type: str
    metadata: Dict[str, Any]
    project_id: Optional[str] = None
    narration_mode: Optional[str] = None

class ExecuteChapterRequest(Schema):
    chapter_number: int

class CharacterVoiceUpdate(Schema):
    character_id: str
    assigned_voice: str

class UpdateVoicesRequest(Schema):
    updates: List[CharacterVoiceUpdate]

class ConfigResponse(Schema):
    llm_model: str
    tts_model: str
    has_api_key: bool
    available_voices: List[Dict[str, Any]]

class UpdateConfigRequest(Schema):
    gemini_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    tts_model: Optional[str] = None


@api.get("/health")
def health_check(request):
    return {"status": "ok", "service": "HexMedia Audio Drama Studio"}


@api.get("/config", response=ConfigResponse)
def get_config(request):
    config = AIConfiguration.objects.filter(is_active=True).first()
    if not config:
        config = AIConfiguration.objects.create(
            llm_model="gemini-3.8-flash",
            tts_model="gemini-3.8-flash-tts",
            is_active=True
        )
    return {
        "llm_model": config.llm_model,
        "tts_model": config.tts_model,
        "has_api_key": bool(config.gemini_api_key),
        "available_voices": config.available_voices or []
    }


@api.post("/config")
def update_config(request, data: UpdateConfigRequest):
    config = AIConfiguration.objects.filter(is_active=True).first()
    if not config:
        config = AIConfiguration.objects.create(is_active=True)
    if data.gemini_api_key is not None:
        config.gemini_api_key = data.gemini_api_key.strip()
    if data.llm_model:
        config.llm_model = data.llm_model.strip()
    if data.tts_model:
        config.tts_model = data.tts_model.strip()
    config.save()
    return {"success": True, "message": "تم تحديث إعدادات Gemini بنجاح!"}


@api.post("/chat", response=ChatResponse)
def chat_endpoint(request, data: ChatRequest):
    project = None
    if data.project_id:
        try:
            project = BookProject.objects.get(id=data.project_id)
        except BookProject.DoesNotExist:
            pass

    # Save user message
    user_msg = ChatMessage.objects.create(
        project=project,
        role='USER',
        content=data.prompt,
        msg_type='TEXT'
    )

    # Fetch last 8 messages for context
    history_msgs = []
    qs = ChatMessage.objects.filter(project=project) if project else ChatMessage.objects.filter(project__isnull=True)
    for m in qs.order_by('-created_at')[:8][::-1]:
        history_msgs.append({"role": m.role, "content": m.content})

    # Run LangGraph Agent
    state_input = {
        "project_id": str(project.id) if project else None,
        "user_prompt": data.prompt,
        "file_content": None,
        "filename": None,
        "narration_mode": data.narration_mode or (project.narration_mode if project else "SMART"),
        "action": "chat",
        "tool": data.tool,
        "history": history_msgs,
        "response_text": "",
        "msg_type": "TEXT",
        "metadata": {}
    }

    result = audio_drama_agent.invoke(state_input)

    # If LangGraph created or switched to a project, update references
    res_pid = result.get("metadata", {}).get("project_id") or result.get("project_id")
    if res_pid and (not project or str(project.id) != str(res_pid)):
        try:
            project = BookProject.objects.get(id=res_pid)
            user_msg.project = project
            user_msg.save(update_fields=['project'])
        except BookProject.DoesNotExist:
            pass

    # If narration_mode was passed explicitly in the request and project exists, update it
    if project and data.narration_mode:
        m = data.narration_mode.upper().strip()
        if m in ['SMART', 'FULL', 'NONE']:
            project.narration_mode = m
            project.save(update_fields=['narration_mode'])

    # Save Assistant message
    ChatMessage.objects.create(
        project=project,
        role='ASSISTANT',
        content=result.get("response_text", ""),
        msg_type=result.get("msg_type", "TEXT"),
        metadata=result.get("metadata", {})
    )

    return {
        "response": result.get("response_text", ""),
        "msg_type": result.get("msg_type", "TEXT"),
        "metadata": result.get("metadata", {}),
        "project_id": str(project.id) if project else res_pid,
        "narration_mode": project.narration_mode if project else None
    }


@api.post("/upload-book", response=ChatResponse)
def upload_book_endpoint(request, file: UploadedFile = File(...), prompt: str = Form("يرجى تحليل هذه الرواية"), narration_mode: Optional[str] = Form(None)):
    file_bytes = file.read()
    filename = file.name
    raw_text = parse_file_text(file_bytes, filename)

    # Run LangGraph Book Ingestion Node
    state_input = {
        "project_id": None,
        "user_prompt": prompt,
        "file_content": raw_text,
        "filename": filename,
        "narration_mode": narration_mode or "SMART",
        "action": "upload_book",
        "history": [],
        "response_text": "",
        "msg_type": "CASTING_CARD",
        "metadata": {}
    }

    result = audio_drama_agent.invoke(state_input)
    new_project_id = result.get("project_id")
    project = BookProject.objects.get(id=new_project_id) if new_project_id else None

    if project and narration_mode:
        m = narration_mode.upper().strip()
        if m in ['SMART', 'FULL', 'NONE']:
            project.narration_mode = m
            project.save(update_fields=['narration_mode'])

    # Save user upload prompt
    ChatMessage.objects.create(
        project=project,
        role='USER',
        content=f"📁 تم رفع الرواية: **{filename}** ({len(raw_text.split())} كلمة)",
        msg_type='TEXT'
    )

    # Save Assistant CASTING_CARD message
    ChatMessage.objects.create(
        project=project,
        role='ASSISTANT',
        content=result.get("response_text", ""),
        msg_type='CASTING_CARD',
        metadata=result.get("metadata", {})
    )

    return {
        "response": result.get("response_text", ""),
        "msg_type": result.get("msg_type", "CASTING_CARD"),
        "metadata": result.get("metadata", {}),
        "project_id": new_project_id,
        "narration_mode": project.narration_mode if project else None
    }


@api.post("/projects/{project_id}/update-characters")
def update_characters_endpoint(request, project_id: str, data: UpdateVoicesRequest):
    project = get_object_or_404(BookProject, id=project_id)
    for update in data.updates:
        try:
            char = Character.objects.get(id=update.character_id, project=project)
            char.assigned_voice = update.assigned_voice
            char.save(update_fields=['assigned_voice'])
        except Character.DoesNotExist:
            pass
    return {"success": True, "message": "تم تحديث أصوات الشخصيات بنجاح!"}


@api.post("/projects/{project_id}/approve-casting", response=ChatResponse)
def approve_casting_endpoint(request, project_id: str):
    project = get_object_or_404(BookProject, id=project_id)

    ChatMessage.objects.create(
        project=project,
        role='USER',
        content="✅ تم اعتماد الشخصيات والأصوات، ابدأ الإنتاج الكامل للدراما الصوتية الآن!",
        msg_type='TEXT'
    )

    state_input = {
        "project_id": str(project.id),
        "user_prompt": "approve",
        "file_content": None,
        "filename": None,
        "action": "approve_casting",
        "history": [],
        "response_text": "",
        "msg_type": "STUDIO_LINK",
        "metadata": {}
    }

    result = audio_drama_agent.invoke(state_input)

    msg_type = result.get("msg_type", "SCENE_AUDIO_CARDS")

    ChatMessage.objects.create(
        project=project,
        role='ASSISTANT',
        content=result.get("response_text", ""),
        msg_type=msg_type,
        metadata=result.get("metadata", {})
    )

    return {
        "response": result.get("response_text", ""),
        "msg_type": msg_type,
        "metadata": result.get("metadata", {}),
        "project_id": str(project.id)
    }


@api.post("/projects/{project_id}/execute-chapter", response=ChatResponse)
def execute_chapter_endpoint(request, project_id: str, data: ExecuteChapterRequest):
    project = get_object_or_404(BookProject, id=project_id)
    chapter = project.chapters.filter(number=data.chapter_number).first()
    ch_title = chapter.title if chapter else f"الفصل {data.chapter_number}"

    ChatMessage.objects.create(
        project=project,
        role='USER',
        content=f"🎙️ طلب تنفيذ المشاهد الصوتية لـ: **{ch_title}**",
        msg_type='TEXT'
    )

    state_input = {
        "project_id": str(project.id),
        "user_prompt": f"تنفيذ صوت {ch_title}",
        "file_content": None,
        "filename": None,
        "narration_mode": project.narration_mode,
        "action": "execute_chapter",
        "chapter_number": data.chapter_number,
        "history": [],
        "response_text": "",
        "msg_type": "SCENE_AUDIO_CARDS",
        "metadata": {}
    }

    result = audio_drama_agent.invoke(state_input)

    ChatMessage.objects.create(
        project=project,
        role='ASSISTANT',
        content=result.get("response_text", ""),
        msg_type=result.get("msg_type", "SCENE_AUDIO_CARDS"),
        metadata=result.get("metadata", {})
    )

    return {
        "response": result.get("response_text", ""),
        "msg_type": result.get("msg_type", "SCENE_AUDIO_CARDS"),
        "metadata": result.get("metadata", {}),
        "project_id": str(project.id),
        "narration_mode": project.narration_mode
    }


@api.get("/projects/{project_id}/chapters")
def list_chapters_endpoint(request, project_id: str):
    project = get_object_or_404(BookProject, id=project_id)
    chapters = project.chapters.all().order_by('number')
    data = []
    for ch in chapters:
        data.append({
            "id": str(ch.id),
            "number": ch.number,
            "title": ch.title,
            "summary": ch.summary,
            "status": ch.status,
            "scenes_count": ch.scenes_count,
            "total_duration_seconds": round(ch.total_duration_seconds, 1)
        })
    return {
        "project_id": str(project.id),
        "chapters_count": len(data),
        "chapters": data
    }


@api.get("/projects/{project_id}/timeline")
def get_timeline_endpoint(request, project_id: str):
    project = get_object_or_404(BookProject, id=project_id)
    timeline_state = TimelineState.objects.filter(project=project).first()
    if not timeline_state or not timeline_state.designcombo_json:
        timeline_json = build_designcombo_timeline(project)
    else:
        timeline_json = timeline_state.designcombo_json
    return {
        "project": {
            "id": str(project.id),
            "title": project.title,
            "author": project.author,
            "status": project.status,
            "summary": project.summary,
        },
        "timeline": timeline_json
    }


@api.post("/projects/{project_id}/export")
def export_timeline_endpoint(request, project_id: str):
    project = get_object_or_404(BookProject, id=project_id)
    state, _ = TimelineState.objects.get_or_create(project=project)
    
    # Concatenate or render all scene audio files into a complete master audio drama
    import io, wave
    scenes = project.scenes.filter(status='GENERATED').order_by('order')
    
    # Build complete master WAV in memory
    master_buf = io.BytesIO()
    sample_rate = 24000
    with wave.open(master_buf, 'wb') as out_wf:
        out_wf.setnchannels(1)
        out_wf.setsampwidth(2)
        out_wf.setframerate(sample_rate)
        
        for sc in scenes:
            from .services.gemini_service import generate_voice_audio
            # Get or re-synthesize scene audio
            wav_data = generate_voice_audio(sc.vocalized_text or sc.raw_text, sc.speaker.assigned_voice if sc.speaker else "Charon")
            try:
                with wave.open(io.BytesIO(wav_data), 'rb') as in_wf:
                    out_wf.writeframes(in_wf.readframes(in_wf.getnframes()))
            except Exception:
                pass
            # 0.4s pause between scenes
            pause_samples = int(sample_rate * 0.4)
            out_wf.writeframes(b'\x00\x00' * pause_samples)
            
    master_bytes = master_buf.getvalue()
    export_url = upload_bytes(master_bytes, f"exports/{project.id}/master_audio_drama.wav")
    state.exported_audio_url = export_url
    state.save(update_fields=['exported_audio_url'])

    return {
        "success": True,
        "message": "تم تصدير الدراما الصوتية بالكامل بنجاح!",
        "audio_url": export_url
    }


class StartContinuousRequest(Schema):
    target_duration_minutes: Optional[int] = 5


@api.get("/projects/{project_id}/live-progress")
def live_progress_endpoint(request, project_id: str, after: int = 0):
    project = get_object_or_404(BookProject, id=project_id)
    new_scenes_qs = project.scenes.filter(order__gt=after).order_by('order')
    new_scenes = []
    for sc in new_scenes_qs:
        new_scenes.append({
            "id": str(sc.id),
            "order": sc.order,
            "chapter": sc.chapter,
            "speaker_name": sc.speaker_name,
            "voice": sc.speaker.assigned_voice if sc.speaker else "Gemini",
            "raw_text": sc.raw_text,
            "vocalized_text": sc.vocalized_text or sc.raw_text,
            "audio_url": sc.audio_url,
            "duration": round(sc.duration_seconds, 1),
            "sfx_name": sc.sfx_name or ""
        })
    return {
        "project_id": str(project.id),
        "status": project.status,
        "total_duration_seconds": round(project.total_duration_seconds, 1),
        "target_duration_minutes": project.target_duration_minutes,
        "progress_percentage": project.progress_percentage,
        "current_act": project.current_act,
        "scenes_count": project.scenes.count(),
        "new_scenes": new_scenes
    }


@api.post("/projects/{project_id}/start-continuous")
def start_continuous_endpoint(request, project_id: str, data: StartContinuousRequest):
    from .services.continuous_engine import start_continuous_generation
    project = start_continuous_generation(project_id, target_duration_minutes=data.target_duration_minutes)
    return {
        "success": True,
        "message": "بدأ الإنتاج الصوتي المستمر في الخلفية بنجاح!",
        "status": project.status,
        "target_duration_minutes": project.target_duration_minutes
    }


@api.post("/projects/{project_id}/pause-continuous")
def pause_continuous_endpoint(request, project_id: str):
    from .services.continuous_engine import pause_continuous_generation
    project = pause_continuous_generation(project_id)
    return {
        "success": True,
        "message": "تم إيقاف الإنتاج مؤقتاً.",
        "status": project.status
    }


@api.post("/projects/{project_id}/resume-continuous")
def resume_continuous_endpoint(request, project_id: str):
    from .services.continuous_engine import resume_continuous_generation
    project = resume_continuous_generation(project_id)
    return {
        "success": True,
        "message": "تم استئناف الإنتاج الصوتي المستمر.",
        "status": project.status
    }


class SetNarrationModeRequest(Schema):
    narration_mode: str


@api.post("/projects/{project_id}/set-narration-mode")
def set_narration_mode_endpoint(request, project_id: str, data: SetNarrationModeRequest):
    project = get_object_or_404(BookProject, id=project_id)
    mode = data.narration_mode.upper().strip()
    if mode not in ['SMART', 'FULL', 'NONE']:
        mode = 'SMART'
    project.narration_mode = mode
    project.save(update_fields=['narration_mode'])
    return {
        "success": True,
        "message": f"تم ضبط نمط تقديم الراوي إلى: {project.get_narration_mode_display()}",
        "narration_mode": project.narration_mode
    }


class RegenerateSceneRequest(Schema):
    text: Optional[str] = None


@api.post("/scenes/{scene_id}/regenerate")
def regenerate_scene_endpoint(request, scene_id: str, data: Optional[RegenerateSceneRequest] = None):
    scene = get_object_or_404(Scene, id=scene_id)
    if data and data.text:
        scene.raw_text = data.text.strip()
        scene.vocalized_text = data.text.strip()

    from .services.gemini_service import generate_voice_audio
    from .services.minio_service import upload_bytes

    voice = scene.speaker.assigned_voice if scene.speaker else "Charon"
    text_to_synth = scene.vocalized_text or scene.raw_text
    audio_bytes = generate_voice_audio(text_to_synth, voice_name=voice, emotion=scene.emotion or "cinematic")
    audio_url = upload_bytes(audio_bytes, f"audio/{scene.project.id}/scene_{scene.order}_regen.wav")

    duration = max(2.5, min(20.0, len(text_to_synth.split()) * 0.45))
    scene.audio_url = audio_url
    scene.duration_seconds = duration
    scene.save(update_fields=['raw_text', 'vocalized_text', 'audio_url', 'duration_seconds'])

    return {
        "success": True,
        "scene": {
            "id": str(scene.id),
            "order": scene.order,
            "speaker_name": scene.speaker_name,
            "voice": voice,
            "raw_text": scene.raw_text,
            "vocalized_text": scene.vocalized_text,
            "audio_url": scene.audio_url,
            "duration": round(scene.duration_seconds, 1),
            "sfx_name": scene.sfx_name or ""
        }
    }


@api.delete("/scenes/{scene_id}")
def delete_scene_endpoint(request, scene_id: str):
    scene = get_object_or_404(Scene, id=scene_id)
    scene.delete()
    return {"success": True, "message": "تم حذف المشهد بنجاح"}



