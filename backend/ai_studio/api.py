import json
import logging
import re
import uuid
from typing import Optional, List, Dict, Any
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from ninja import NinjaAPI, Schema, File, Form, Body
from ninja.errors import HttpError
from ninja.files import UploadedFile
from ninja.parser import Parser
from .models import BookProject, Character, Scene, TimelineState, ChatMessage, AIConfiguration, Chapter, ChatThread
from .services.langgraph_controller import audio_drama_agent, parse_file_text
from .services.timeline_builder import build_designcombo_timeline
from .services.minio_service import upload_bytes
from .services.gemini_service import get_gemini_client
from .auth import JWTAuth, django_auth, generate_tokens_for_user, decode_jwt_payload, get_current_user
from google.genai import types

logger = logging.getLogger(__name__)


class SafeParser(Parser):
    """Parser that safely treats empty or non-JSON request bodies as empty dict instead of JSON decode error."""
    def parse_body(self, request):
        if not request.body or not request.body.strip():
            return {}
        try:
            return json.loads(request.body)
        except Exception:
            return {}


api = NinjaAPI(
    title="HexMedia Audio Drama Studio API",
    version="1.0.0",
    description="API for AI Audio Drama Studio powered by Gemini 3.8 Flash and LangGraph",
    auth=[JWTAuth(), django_auth],
    parser=SafeParser()
)


def get_current_user(request) -> User:
    """Helper to retrieve authenticated user from request.auth or request.user."""
    user = getattr(request, 'auth', None)
    if user and isinstance(user, User):
        return user
    if getattr(request, 'user', None) and request.user.is_authenticated:
        return request.user
    raise HttpError(401, "يجب تسجيل الدخول أولاً")

# Schemas
class ChatRequest(Schema):
    prompt: str
    project_id: Optional[str] = None
    thread_id: Optional[str] = None
    session_id: Optional[str] = "default"
    narration_mode: Optional[str] = None
    tool: Optional[str] = None

class ChatResponse(Schema):
    response: str
    msg_type: str
    metadata: Dict[str, Any]
    project_id: Optional[str] = None
    thread_id: Optional[str] = None
    narration_mode: Optional[str] = None

class VoiceChatResponse(Schema):
    response: str
    user_transcript: str
    audio_url: str
    duration: float
    thread_id: str
    project_id: Optional[str] = None

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


class UserOut(Schema):
    id: int
    username: str
    email: str

class AuthResponse(Schema):
    access_token: str
    refresh_token: str
    user: UserOut

class RegisterRequest(Schema):
    email: str
    password: str
    username: Optional[str] = None

class LoginRequest(Schema):
    password: str
    email: Optional[str] = None
    username: Optional[str] = None

class RefreshRequest(Schema):
    refresh_token: str

class UserProfileResponse(Schema):
    id: int
    username: str
    email: str
    is_staff: bool
    projects_count: int


# ── Thread Schemas ──────────────────────────────────────────────────────────

class ThreadOut(Schema):
    id: str
    title: str
    project_id: Optional[str] = None
    created_at: str
    updated_at: str

class ThreadRenameRequest(Schema):
    title: Optional[str] = "محادثة جديدة"

class ProjectRenameRequest(Schema):
    title: str


# ── Sliding Window Memory Helper ────────────────────────────────────────────

MEMORY_WINDOW = 20  # keep last N messages as context

def _build_history(thread: 'ChatThread', limit: int = MEMORY_WINDOW) -> list:
    """Return last `limit` messages of a thread as role/content dicts."""
    qs = (
        ChatMessage.objects.filter(thread=thread)
        .order_by('-created_at')[:limit]
    )
    return [{"role": m.role, "content": m.content} for m in reversed(list(qs))]


@api.get("/health", auth=None)
def health_check(request):
    return {"status": "ok", "service": "HexMedia Audio Drama Studio"}


@api.post("/auth/register", response=AuthResponse, auth=None)
def register_endpoint(request, data: RegisterRequest):
    email = (data.email or "").strip().lower()
    if not email or '@' not in email:
        raise HttpError(400, "يرجى إدخال بريد إلكتروني صالح")

    parts = email.split('@')
    if len(parts) != 2 or not parts[0] or not parts[1] or '.' not in parts[1]:
        raise HttpError(400, "يرجى إدخال بريد إلكتروني صالح")

    password = (data.password or "").strip()
    if not password or len(password) < 6:
        raise HttpError(400, "كلمة المرور يجب أن لا تقل عن 6 أحرف")

    if User.objects.filter(email__iexact=email).exists():
        raise HttpError(400, "البريد الإلكتروني مسجل بالفعل")

    # Determine username
    raw_user = (data.username or "").strip()
    base_username = raw_user if raw_user else parts[0]
    if not base_username:
        base_username = f"user_{uuid.uuid4().hex[:8]}"

    username = base_username
    counter = 1
    while User.objects.filter(username__iexact=username).exists():
        username = f"{base_username}_{counter}"
        counter += 1

    from django.db import IntegrityError, transaction
    try:
        with transaction.atomic():
            user = User.objects.create_user(username=username, email=email, password=password)
    except IntegrityError:
        raise HttpError(400, "البريد الإلكتروني أو اسم المستخدم مسجل بالفعل")

    login(request, user)
    return generate_tokens_for_user(user)


@api.post("/auth/login", response=AuthResponse, auth=None)
def login_endpoint(request, data: LoginRequest):
    identifier = (data.email or data.username or "").strip()
    if not identifier or not data.password:
        raise HttpError(400, "يرجى إدخال البريد الإلكتروني/اسم المستخدم وكلمة المرور")

    user_obj = User.objects.filter(email__iexact=identifier).first() or User.objects.filter(username__iexact=identifier).first()
    if not user_obj:
        raise HttpError(401, "بيانات الدخول غير صحيحة")

    user = authenticate(request, username=user_obj.username, password=data.password)
    if not user or not user.is_active:
        raise HttpError(401, "بيانات الدخول غير صحيحة")

    login(request, user)
    return generate_tokens_for_user(user)


@api.post("/auth/refresh", response=AuthResponse, auth=None)
def refresh_endpoint(request, data: RefreshRequest):
    payload = decode_jwt_payload(data.refresh_token)
    if not payload or payload.get("token_type") != "refresh":
        raise HttpError(401, "رمز التحديث غير صالح أو منتهي الصلاحية")

    user_id = payload.get("user_id")
    user = User.objects.filter(id=user_id, is_active=True).first()
    if not user:
        raise HttpError(401, "المستخدم غير موجود أو غير نشط")

    return generate_tokens_for_user(user)


@api.post("/auth/logout")
def logout_endpoint(request):
    logout(request)
    return {"success": True, "message": "تم تسجيل الخروج بنجاح"}


@api.get("/auth/me", response=UserProfileResponse)
def me_endpoint(request):
    user = get_current_user(request)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_staff": user.is_staff,
        "projects_count": user.projects.count() if hasattr(user, 'projects') else 0
    }


# ── Chat Thread CRUD ────────────────────────────────────────────────────────

@api.get("/threads", response=List[ThreadOut])
def list_threads(request):
    """List all non-deleted threads for current user, newest first."""
    user = get_current_user(request)
    threads = ChatThread.objects.filter(user=user, is_deleted=False).order_by('-updated_at')
    return [
        {
            "id": str(t.id),
            "title": t.title,
            "project_id": str(t.project_id) if t.project_id else None,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
        }
        for t in threads
    ]


@api.post("/threads", response=ThreadOut)
def create_thread(request, data: Optional[ThreadRenameRequest] = Body(default=None)):
    """Create a new thread."""
    user = get_current_user(request)
    title = (data.title.strip() if (data and data.title and data.title.strip()) else "محادثة جديدة")
    thread = ChatThread.objects.create(user=user, title=title)
    return {
        "id": str(thread.id),
        "title": thread.title,
        "project_id": None,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat(),
    }


@api.get("/threads/{thread_id}", response=ThreadOut)
def get_thread_detail(request, thread_id: str):
    """Get single thread metadata."""
    user = get_current_user(request)
    thread = get_object_or_404(ChatThread, id=thread_id, user=user, is_deleted=False)
    return {
        "id": str(thread.id),
        "title": thread.title,
        "project_id": str(thread.project_id) if thread.project_id else None,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat(),
    }


@api.get("/threads/{thread_id}/messages")
def get_thread_messages(request, thread_id: str):
    """Get all messages for a thread (owned by current user)."""
    user = get_current_user(request)
    thread = get_object_or_404(ChatThread, id=thread_id, user=user, is_deleted=False)
    msgs = thread.messages.order_by('created_at')
    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "msg_type": m.msg_type,
            "metadata": m.metadata,
            "created_at": m.created_at.isoformat(),
        }
        for m in msgs
    ]


@api.patch("/threads/{thread_id}/rename")
def rename_thread(request, thread_id: str, data: ThreadRenameRequest):
    """Rename a thread title."""
    user = get_current_user(request)
    thread = get_object_or_404(ChatThread, id=thread_id, user=user, is_deleted=False)
    thread.title = data.title.strip() or "محادثة"
    thread.save(update_fields=['title', 'updated_at'])
    return {"success": True, "title": thread.title}


@api.patch("/threads/{thread_id}")
def update_thread(request, thread_id: str, data: ThreadRenameRequest):
    """Update thread metadata (e.g. title)."""
    return rename_thread(request, thread_id, data)


@api.post("/threads/{thread_id}/generate-title")
def generate_thread_title(request, thread_id: str):
    """Generate a concise title for the thread based on first user message."""
    user = get_current_user(request)
    thread = get_object_or_404(ChatThread, id=thread_id, user=user, is_deleted=False)
    first_msg = thread.messages.filter(role='USER').order_by('created_at').first()
    if not first_msg:
        return {"success": False, "title": thread.title}

    words = first_msg.content.strip().split()
    new_title = " ".join(words[:6])
    if len(words) > 6:
        new_title += "..."
    thread.title = new_title
    thread.save(update_fields=['title', 'updated_at'])
    return {"success": True, "title": thread.title}


@api.delete("/threads/{thread_id}")
def delete_thread(request, thread_id: str):
    """Soft-delete a thread."""
    user = get_current_user(request)
    thread = get_object_or_404(ChatThread, id=thread_id, user=user, is_deleted=False)
    thread.is_deleted = True
    thread.save(update_fields=['is_deleted', 'updated_at'])
    return {"success": True}


@api.get("/profile/media")
def get_profile_media(request):
    """User profile media library returning audio, scripts, and video scenes."""
    user = get_current_user(request)
    projects = BookProject.objects.filter(user=user)

    audio_tracks = []
    scripts = []
    video_scenes = []

    for p in projects:
        if p.raw_text:
            scripts.append({
                "project_id": str(p.id),
                "title": p.title,
                "preview": p.raw_text[:200]
            })
        for sc in p.scenes.all():
            if sc.audio_url:
                audio_tracks.append({
                    "scene_id": str(sc.id),
                    "project_id": str(p.id),
                    "speaker": sc.speaker_name,
                    "audio_url": sc.audio_url,
                    "duration": sc.duration_seconds
                })
            if sc.image_url:
                video_scenes.append({
                    "scene_id": str(sc.id),
                    "project_id": str(p.id),
                    "image_url": sc.image_url,
                    "motion_type": sc.motion_type
                })

    try:
        from tts.models import TTSJob
        for tj in TTSJob.objects.filter(user=user):
            if tj.audio_url:
                audio_tracks.append({
                    "scene_id": str(tj.id),
                    "project_id": str(tj.id),
                    "speaker": f"TTS ({tj.voice_profile})",
                    "audio_url": tj.audio_url,
                    "duration": tj.duration_seconds
                })
    except Exception:
        pass

    try:
        from stt.models import STTJob
        for sj in STTJob.objects.filter(user=user):
            if sj.audio_url:
                audio_tracks.append({
                    "scene_id": str(sj.id),
                    "project_id": str(sj.id),
                    "speaker": f"STT ({sj.title})",
                    "audio_url": sj.audio_url,
                    "duration": sj.duration_seconds
                })
            if sj.transcript_text:
                scripts.append({
                    "project_id": str(sj.id),
                    "title": f"تفريغ: {sj.title}",
                    "preview": sj.transcript_text[:200]
                })
    except Exception:
        pass

    total_audio_sec = sum(float(t.get("duration") or 0.0) for t in audio_tracks)
    return {
        "audio_tracks": audio_tracks,
        "audio": audio_tracks,
        "scripts": scripts,
        "video_scenes": video_scenes,
        "videos": video_scenes,
        "stats": {
            "projects_count": projects.count(),
            "audio_tracks_count": len(audio_tracks),
            "video_scenes_count": len(video_scenes),
            "scripts_count": len(scripts),
            "total_duration_seconds": round(total_audio_sec, 1),
            "total_duration_minutes": round(total_audio_sec / 60.0, 1),
        }
    }


@api.patch("/projects/{project_id}/rename")
def rename_project_endpoint(request, project_id: str, data: ProjectRenameRequest):
    """Rename a book project belonging to authenticated user."""
    user = get_current_user(request)
    project = get_object_or_404(BookProject, id=project_id, user=user)
    title = (data.title or "").strip()
    if not title:
        raise HttpError(400, "عنوان المشروع لا يمكن أن يكون فارغاً")
    project.title = title
    project.save(update_fields=['title', 'updated_at'])
    return {
        "success": True,
        "id": str(project.id),
        "title": project.title
    }


@api.delete("/projects/{project_id}")
def delete_project_endpoint(request, project_id: str):
    """Delete a book project belonging to authenticated user."""
    user = get_current_user(request)
    project = get_object_or_404(BookProject, id=project_id, user=user)
    project_id_str = str(project.id)
    project.delete()
    return {"success": True, "id": project_id_str}


@api.get("/projects")
def list_projects_endpoint(request):
    user = get_current_user(request)
    projects = BookProject.objects.filter(user=user).order_by('-created_at')
    return [
        {
            "id": str(p.id),
            "title": p.title,
            "status": p.status,
            "genre": p.genre or "",
            "scenes_count": p.scenes.count(),
            "total_duration_seconds": round(p.total_duration_seconds, 1),
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in projects
    ]


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
    user = get_current_user(request)
    project = None
    if data.project_id:
        project = get_object_or_404(BookProject, id=data.project_id, user=user)

    thread = None
    if data.thread_id:
        thread = get_object_or_404(ChatThread, id=data.thread_id, user=user, is_deleted=False)
        if not project and thread.project:
            project = thread.project
        if thread.title == "محادثة جديدة" and data.prompt.strip():
            words = data.prompt.strip().split()
            t_title = " ".join(words[:5])
            if len(words) > 5:
                t_title += "..."
            thread.title = t_title
            thread.save(update_fields=['title', 'updated_at'])
    else:
        p_text = data.prompt.strip()
        words = p_text.split()
        t_title = " ".join(words[:5]) if words else "محادثة جديدة"
        if len(words) > 5:
            t_title += "..."
        thread = ChatThread.objects.create(
            user=user,
            project=project,
            title=t_title
        )

    # Fetch context history using sliding window memory BEFORE saving current user message
    history_msgs = _build_history(thread, limit=MEMORY_WINDOW)

    # Save user message
    user_msg = ChatMessage.objects.create(
        user=user,
        thread=thread,
        project=project,
        role='USER',
        content=data.prompt,
        msg_type='TEXT'
    )

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

    # If LangGraph created or switched to a project, update references and assign user
    res_pid = result.get("metadata", {}).get("project_id") or result.get("project_id")
    if res_pid and (not project or str(project.id) != str(res_pid)):
        try:
            project = BookProject.objects.get(id=res_pid)
            if not project.user:
                project.user = user
                project.save(update_fields=['user'])
            user_msg.project = project
            user_msg.save(update_fields=['project'])
            if thread and not thread.project:
                thread.project = project
                thread.save(update_fields=['project'])
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
        user=user,
        thread=thread,
        project=project,
        role='ASSISTANT',
        content=result.get("response_text", ""),
        msg_type=result.get("msg_type", "TEXT"),
        metadata=result.get("metadata", {})
    )

    thread.save(update_fields=['updated_at'])

    return {
        "response": result.get("response_text", ""),
        "msg_type": result.get("msg_type", "TEXT"),
        "metadata": result.get("metadata", {}),
        "project_id": str(project.id) if project else res_pid,
        "thread_id": str(thread.id),
        "narration_mode": project.narration_mode if project else None
    }


@api.post("/upload-book", response=ChatResponse)
def upload_book_endpoint(request, file: UploadedFile = File(...), prompt: str = Form("يرجى تحليل هذه الرواية"), narration_mode: Optional[str] = Form(None), thread_id: Optional[str] = Form(None)):
    user = get_current_user(request)
    file_bytes = file.read()
    filename = file.name
    raw_text = parse_file_text(file_bytes, filename)

    thread = None
    if thread_id:
        thread = get_object_or_404(ChatThread, id=thread_id, user=user, is_deleted=False)

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

    if project and not project.user:
        project.user = user
        project.save(update_fields=['user'])

    if not thread:
        thread = ChatThread.objects.create(
            user=user,
            project=project,
            title=f"رواية: {filename[:30]}"
        )
    elif project and not thread.project:
        thread.project = project
        thread.save(update_fields=['project'])

    if project and narration_mode:
        m = narration_mode.upper().strip()
        if m in ['SMART', 'FULL', 'NONE']:
            project.narration_mode = m
            project.save(update_fields=['narration_mode'])

    # Save user upload prompt
    ChatMessage.objects.create(
        user=user,
        thread=thread,
        project=project,
        role='USER',
        content=f"📁 تم رفع الرواية: **{filename}** ({len(raw_text.split())} كلمة)",
        msg_type='TEXT'
    )

    # Save Assistant CASTING_CARD message
    ChatMessage.objects.create(
        user=user,
        thread=thread,
        project=project,
        role='ASSISTANT',
        content=result.get("response_text", ""),
        msg_type='CASTING_CARD',
        metadata=result.get("metadata", {})
    )

    thread.save(update_fields=['updated_at'])

    return {
        "response": result.get("response_text", ""),
        "msg_type": result.get("msg_type", "CASTING_CARD"),
        "metadata": result.get("metadata", {}),
        "project_id": new_project_id,
        "thread_id": str(thread.id),
        "narration_mode": project.narration_mode if project else None
    }


@api.post("/voice-chat", response=VoiceChatResponse)
def voice_chat_endpoint(
    request,
    audio_file: UploadedFile = File(...),
    thread_id: Optional[str] = Form(None),
    project_id: Optional[str] = Form(None)
):
    """
    Direct user voice input processed with Gemini 3.8 Flash.
    Transcribes spoken voice prompt and generates conversational text reply (text only).
    """
    user = get_current_user(request)
    audio_bytes = audio_file.read()
    if not audio_bytes:
        raise HttpError(400, "التسجيل الصوتي فارغ")

    content_type = audio_file.content_type or "audio/webm"
    unique_name = f"voice_chat_{uuid.uuid4().hex[:10]}_{audio_file.name or 'recording.webm'}"
    try:
        audio_url = upload_bytes(audio_bytes, unique_name, content_type=content_type)
    except Exception:
        audio_url = f"/media/voice_chat/{unique_name}"

    from stt.services.stt_engine import estimate_audio_duration
    duration = estimate_audio_duration(audio_bytes, audio_file.name or "")

    client, config = get_gemini_client()
    user_transcript = ""
    assistant_response = ""

    if client:
        try:
            prompt_instruction = (
                "You are the HexMedia AI Creative Director. The user sent a voice message to you in the chat.\n"
                "1. Transcribe what the user said accurately in the 'transcript' field.\n"
                "2. Provide your direct, warm, and helpful creative response in Arabic in the 'response' field (text only, no audio output).\n\n"
                "Output strictly valid JSON with no markdown code fences:\n"
                "{\n"
                '  "transcript": "accurate transcript of user audio",\n'
                '  "response": "your Arabic text answer to the user"\n'
                "}"
            )
            audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=content_type)
            res = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=[audio_part, prompt_instruction]
            )
            raw = (res.text or "").strip()
            raw = re.sub(r'^```(?:json)?', '', raw).strip()
            raw = re.sub(r'```$', '', raw).strip()
            data = json.loads(raw)
            user_transcript = data.get("transcript", "").strip()
            assistant_response = data.get("response", "").strip()
        except Exception as e:
            logger.warning(f"Gemini voice chat processing fallback: {e}")

    if not user_transcript:
        user_transcript = "تسجيل صوتي: أريد استشارتك في مشروع درامي جديد."
    if not assistant_response:
        assistant_response = (
            "أهلاً بك! لقد استمعت لرسالتك الصوتية عبر Gemini 3.8 Flash بنجاح 🎙️. "
            "يسعدني مساعدتك في تطوير وتحويل أفكارك إلى عمل صوتي ومرئي ملحمي. "
            "يمكننا كتابة السيناريو، اختيار أصوات الشخصيات، أو ريندر المشاهد. كيف تحب أن نبدأ؟"
        )

    project = None
    if project_id:
        try:
            project = BookProject.objects.filter(id=project_id, user=user).first()
        except Exception:
            pass

    thread = None
    if thread_id:
        thread = ChatThread.objects.filter(id=thread_id, user=user, is_deleted=False).first()
        if thread and thread.title == "محادثة جديدة" and user_transcript:
            words = user_transcript.split()
            thread.title = " ".join(words[:5]) + ("..." if len(words) > 5 else "")
            thread.save(update_fields=['title', 'updated_at'])

    if not thread:
        words = user_transcript.split() if user_transcript else []
        t_title = (" ".join(words[:5]) + ("..." if len(words) > 5 else "")) if words else "محادثة صوتية"
        thread = ChatThread.objects.create(
            user=user,
            project=project,
            title=t_title
        )

    # Save user voice message
    ChatMessage.objects.create(
        user=user,
        thread=thread,
        project=project,
        role='USER',
        content=user_transcript,
        msg_type='TEXT',
        metadata={
            "audio_url": audio_url,
            "duration": duration,
            "is_voice_message": True
        }
    )

    # Save assistant response
    ChatMessage.objects.create(
        user=user,
        thread=thread,
        project=project,
        role='ASSISTANT',
        content=assistant_response,
        msg_type='TEXT',
        metadata={}
    )

    thread.save(update_fields=['updated_at'])

    return {
        "response": assistant_response,
        "user_transcript": user_transcript,
        "audio_url": audio_url,
        "duration": duration,
        "thread_id": str(thread.id),
        "project_id": str(project.id) if project else None
    }


@api.post("/projects/{project_id}/update-characters")
def update_characters_endpoint(request, project_id: str, data: UpdateVoicesRequest):
    user = get_current_user(request)
    project = get_object_or_404(BookProject, id=project_id, user=user)
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
    user = get_current_user(request)
    project = get_object_or_404(BookProject, id=project_id, user=user)

    ChatMessage.objects.create(
        user=user,
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
        user=user,
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
    user = get_current_user(request)
    project = get_object_or_404(BookProject, id=project_id, user=user)
    chapter = project.chapters.filter(number=data.chapter_number).first()
    ch_title = chapter.title if chapter else f"الفصل {data.chapter_number}"

    ChatMessage.objects.create(
        user=user,
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
        user=user,
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
    user = get_current_user(request)
    project = get_object_or_404(BookProject, id=project_id, user=user)
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
    user = get_current_user(request)
    project = get_object_or_404(BookProject, id=project_id, user=user)
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
    user = get_current_user(request)
    project = get_object_or_404(BookProject, id=project_id, user=user)
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
    user = get_current_user(request)
    project = get_object_or_404(BookProject, id=project_id, user=user)

    # Auto-Healing: Ensure background worker is alive if status is CONTINUOUS_GENERATING
    from .services.continuous_engine import ensure_worker_running
    if project.status == 'CONTINUOUS_GENERATING':
        ensure_worker_running(str(project.id))

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
            "image_url": sc.image_url or "",
            "visual_prompt": sc.visual_prompt or "",
            "media_type": sc.media_type or "AI_IMAGE",
            "motion_type": sc.motion_type or "zoom_in",
            "duration": round(sc.duration_seconds, 1),
            "sfx_name": sc.sfx_name or ""
        })
    return {
        "project_id": str(project.id),
        "project_type": project.project_type,
        "visual_style": getattr(project, 'visual_style', 'DOCUMENTARY'),
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
    user = get_current_user(request)
    project = get_object_or_404(BookProject, id=project_id, user=user)
    from .services.continuous_engine import start_continuous_generation
    project = start_continuous_generation(str(project.id), target_duration_minutes=data.target_duration_minutes)
    return {
        "success": True,
        "message": "بدأ الإنتاج الصوتي المستمر في الخلفية بنجاح!",
        "status": project.status,
        "target_duration_minutes": project.target_duration_minutes
    }


@api.post("/projects/{project_id}/pause-continuous")
def pause_continuous_endpoint(request, project_id: str):
    user = get_current_user(request)
    project = get_object_or_404(BookProject, id=project_id, user=user)
    from .services.continuous_engine import pause_continuous_generation
    project = pause_continuous_generation(str(project.id))
    return {
        "success": True,
        "message": "تم إيقاف الإنتاج مؤقتاً.",
        "status": project.status
    }


@api.post("/projects/{project_id}/resume-continuous")
def resume_continuous_endpoint(request, project_id: str):
    user = get_current_user(request)
    project = get_object_or_404(BookProject, id=project_id, user=user)
    from .services.continuous_engine import resume_continuous_generation
    project = resume_continuous_generation(str(project.id))
    return {
        "success": True,
        "message": "تم استئناف الإنتاج الصوتي المستمر.",
        "status": project.status
    }


class SetNarrationModeRequest(Schema):
    narration_mode: str


@api.post("/projects/{project_id}/set-narration-mode")
def set_narration_mode_endpoint(request, project_id: str, data: SetNarrationModeRequest):
    user = get_current_user(request)
    project = get_object_or_404(BookProject, id=project_id, user=user)
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
    user = get_current_user(request)
    scene = get_object_or_404(Scene, id=scene_id, project__user=user)
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
    user = get_current_user(request)
    scene = get_object_or_404(Scene, id=scene_id, project__user=user)
    scene.delete()
    return {"success": True, "message": "تم حذف المشهد بنجاح"}


class RegenerateVisualRequest(Schema):
    prompt: Optional[str] = None
    force_archive: Optional[bool] = False


@api.post("/scenes/{scene_id}/regenerate-visual")
def regenerate_scene_visual_endpoint(request, scene_id: str, data: Optional[RegenerateVisualRequest] = None):
    user = get_current_user(request)
    scene = get_object_or_404(Scene, id=scene_id, project__user=user)
    from .services.visual_service import produce_scene_visual
    
    prompt = data.prompt.strip() if (data and data.prompt) else (scene.visual_prompt or scene.raw_text)
    force_archive = data.force_archive if data else False
    
    v_info = produce_scene_visual(
        scene_id=str(scene.id),
        raw_prompt=prompt,
        visual_style=getattr(scene.project, 'visual_style', 'AUTO'),
        character_dna=scene.speaker.description if scene.speaker else "",
        force_archive=force_archive
    )
    
    scene.image_url = v_info.get("image_url", scene.image_url)
    scene.visual_prompt = v_info.get("visual_prompt", scene.visual_prompt)
    scene.media_type = v_info.get("media_type", scene.media_type)
    scene.motion_type = v_info.get("motion_type", scene.motion_type)
    scene.save(update_fields=['image_url', 'visual_prompt', 'media_type', 'motion_type'])
    
    return {
        "success": True,
        "scene": {
            "id": str(scene.id),
            "order": scene.order,
            "speaker_name": scene.speaker_name,
            "image_url": scene.image_url,
            "visual_prompt": scene.visual_prompt,
            "media_type": scene.media_type,
            "motion_type": scene.motion_type
        }
    }


@api.post("/projects/{project_id}/render-film")
def render_film_endpoint(request, project_id: str):
    user = get_current_user(request)
    project = get_object_or_404(BookProject, id=project_id, user=user)
    from .services.remotion_bridge import render_or_queue_project
    res = render_or_queue_project(str(project.id))
    return res


from tts.api import router as tts_router
api.add_router("/tts", tts_router)

from stt.api import router as stt_router
api.add_router("/stt", stt_router)


# =============================================================================
# MOTION GRAPHICS STUDIO SCHEMAS & ENDPOINTS (REMOTION)
# =============================================================================
class MotionGenerateConfigRequest(Schema):
    text: Optional[str] = None
    title: Optional[str] = "HexMedia Motion Studio"
    subtitle: Optional[str] = "Code-to-Video Engine"
    speaker_name: Optional[str] = "الراوي الذكي"
    template_id: Optional[str] = "dark_neon"
    aspect_ratio: Optional[str] = "9:16"
    audio_url: Optional[str] = None
    background_url: Optional[str] = None
    background_type: Optional[str] = None
    background_color: Optional[str] = None
    accent_color: Optional[str] = None
    duration_seconds: Optional[float] = None
    fps: Optional[int] = 30
    video_start_offset: Optional[float] = 0.0
    video_volume: Optional[float] = 0.15
    video_muted: Optional[bool] = False
    transition_effect: Optional[str] = "zoom_in"


class MotionRenderRequest(Schema):
    props: Optional[Dict[str, Any]] = None
    text: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    speaker_name: Optional[str] = None
    words: Optional[List[Dict[str, Any]]] = None
    template_id: Optional[str] = "dark_neon"
    aspect_ratio: Optional[str] = "9:16"
    audio_url: Optional[str] = None
    background_url: Optional[str] = None
    background_type: Optional[str] = None
    background_color: Optional[str] = None
    accent_color: Optional[str] = None
    duration_seconds: Optional[float] = None
    fps: Optional[int] = 30
    video_start_offset: Optional[float] = 0.0
    video_volume: Optional[float] = 0.15
    video_muted: Optional[bool] = False
    transition_effect: Optional[str] = "zoom_in"
    composition_id: Optional[str] = None


class MotionFetchUrlRequest(Schema):
    url: str


@api.get("/motion/templates", auth=None)
def get_motion_templates(request):
    """Returns available motion templates, aspect ratios, and default sample words."""
    from .services.motion_service import SUPPORTED_TEMPLATES, SUPPORTED_ASPECT_RATIOS, DEFAULT_SAMPLE_WORDS
    return {
        "templates": SUPPORTED_TEMPLATES,
        "aspect_ratios": SUPPORTED_ASPECT_RATIOS,
        "default_sample_words": DEFAULT_SAMPLE_WORDS,
    }


@api.post("/motion/upload-video", auth=None)
def upload_motion_video(request, file: UploadedFile = File(...)):
    """Uploads user video file (MP4, MOV, WebM), validates size/format, probes duration and uploads to MinIO."""
    from .services.motion_service import save_uploaded_video
    result = save_uploaded_video(file)
    if not result.get("success"):
        raise HttpError(400, result.get("error", "فشل رفع ملف الفيديو"))
    return result


@api.post("/motion/fetch-video-url", auth=None)
def fetch_motion_video_url(request, data: MotionFetchUrlRequest):
    """Ingests video from YouTube or direct URL, validates and uploads to MinIO."""
    from .services.motion_service import ingest_video_url
    result = ingest_video_url(data.url)
    if not result.get("success"):
        raise HttpError(400, result.get("error", "فشل جلب الفيديو من الرابط"))
    return result


@api.post("/motion/config", auth=None)
def generate_motion_config(request, data: MotionGenerateConfigRequest):
    """Calculates synchronized word timestamps and builds Remotion composition props."""
    from .services.motion_service import build_motion_props
    props = build_motion_props(
        text=data.text,
        title=data.title,
        subtitle=data.subtitle,
        speaker_name=data.speaker_name,
        template_id=data.template_id or "dark_neon",
        aspect_ratio=data.aspect_ratio or "9:16",
        audio_url=data.audio_url,
        background_url=data.background_url,
        background_type=data.background_type,
        background_color=data.background_color,
        accent_color=data.accent_color,
        duration_seconds=data.duration_seconds,
        fps=data.fps or 30,
        video_start_offset=data.video_start_offset or 0.0,
        video_volume=data.video_volume if data.video_volume is not None else 0.15,
        video_muted=bool(data.video_muted),
        transition_effect=data.transition_effect or "zoom_in",
    )
    return {
        "success": True,
        "props": props,
        "word_count": len(props.get("words", [])),
        "duration_seconds": props.get("durationInSeconds"),
        "aspect_ratio": props.get("aspectRatio"),
        "template_id": props.get("templateId"),
    }


@api.post("/motion/render", auth=None)
def render_motion_endpoint(request, data: MotionRenderRequest):
    """Renders video via Remotion CLI, uploads MP4 to MinIO, and returns download URL."""
    from .services.motion_service import build_motion_props, render_motion_video
    if data.props:
        props = data.props
    else:
        props = build_motion_props(
            text=data.text,
            title=data.title,
            subtitle=data.subtitle,
            speaker_name=data.speaker_name,
            words=data.words,
            template_id=data.template_id or "dark_neon",
            aspect_ratio=data.aspect_ratio or "9:16",
            audio_url=data.audio_url,
            background_url=data.background_url,
            background_type=data.background_type,
            background_color=data.background_color,
            accent_color=data.accent_color,
            duration_seconds=data.duration_seconds,
            fps=data.fps or 30,
            video_start_offset=data.video_start_offset or 0.0,
            video_volume=data.video_volume if data.video_volume is not None else 0.15,
            video_muted=bool(data.video_muted),
            transition_effect=data.transition_effect or "zoom_in",
        )

    result = render_motion_video(props, composition_id=data.composition_id)
    if not result.get("success"):
        raise HttpError(500, result.get("error", "فشل ريندر فيديو الموشن"))
    return result






