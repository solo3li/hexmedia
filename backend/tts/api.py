from typing import Optional, List, Dict, Any
from ninja import Router, Schema
from ninja.errors import HttpError
from django.shortcuts import get_object_or_404
from ai_studio.auth import JWTAuth, django_auth, get_current_user
from .models import TTSJob
from .services.tts_options import LANGUAGES, VOICES, EMOTIONS, DELIVERY_STYLES
from .services.tts_engine import process_tts_generation

router = Router(auth=[JWTAuth(), django_auth])


class TTSGenerateRequest(Schema):
    text: str
    title: Optional[str] = "تسجيل صوتي"
    language: Optional[str] = "ar"
    dialect: Optional[str] = "msa"
    voice_profile: Optional[str] = "Charon"
    emotion: Optional[str] = "neutral"
    delivery_style: Optional[str] = "documentary"
    custom_instructions: Optional[str] = ""
    custom_directives: Optional[str] = ""
    auto_diacritize: Optional[bool] = False


class TTSChunkOut(Schema):
    order: int
    text: str
    duration: float
    audio_url: str


class TTSGenerateResponse(Schema):
    id: str
    title: str
    audio_url: str
    duration_seconds: float
    chunks_count: int
    chunks: List[TTSChunkOut]
    vocalized_text: str
    text: Optional[str] = ""
    char_count: Optional[int] = 0
    language: str
    dialect: str
    voice_profile: str
    emotion: str
    delivery_style: str


@router.get("/options", auth=None)
def get_tts_options(request):
    """Returns available languages, dialects, voice profiles, emotions, and styles."""
    return {
        "languages": LANGUAGES,
        "voices": VOICES,
        "emotions": EMOTIONS,
        "delivery_styles": DELIVERY_STYLES
    }


@router.post("/generate", response=TTSGenerateResponse)
def generate_tts_endpoint(request, data: TTSGenerateRequest):
    """Synthesize speech with smart chunking and audio stitching."""
    user = get_current_user(request)
    raw_text = (data.text or "").strip()
    if not raw_text:
        raise HttpError(400, "النص المطلوب تحويله لصوت لا يمكن أن يكون فارغاً")

    effective_directives = (data.custom_directives or data.custom_instructions or "").strip()
    auto_diacritize_flag = data.auto_diacritize if data.auto_diacritize is not None else False

    result = process_tts_generation(
        text=raw_text,
        voice_profile=data.voice_profile or "Charon",
        language=data.language or "ar",
        dialect=data.dialect or "msa",
        emotion=data.emotion or "neutral",
        delivery_style=data.delivery_style or "documentary",
        custom_instructions=effective_directives,
        auto_diacritize=auto_diacritize_flag
    )

    job = TTSJob.objects.create(
        user=user,
        title=data.title or f"تسجيل ({data.voice_profile})",
        input_text=raw_text,
        vocalized_text=result["vocalized_text"],
        language=result["language"],
        dialect=result["dialect"],
        voice_profile=result["voice_profile"],
        emotion=result["emotion"],
        delivery_style=result["delivery_style"],
        custom_instructions=effective_directives,
        audio_url=result["master_audio_url"],
        duration_seconds=result["duration_seconds"],
        chunks_count=result["chunks_count"],
        status='READY'
    )

    displayed_text = result.get("vocalized_text") or raw_text

    return {
        "id": str(job.id),
        "title": job.title,
        "audio_url": job.audio_url,
        "duration_seconds": job.duration_seconds,
        "chunks_count": job.chunks_count,
        "chunks": result["chunks"],
        "vocalized_text": job.vocalized_text,
        "text": displayed_text,
        "char_count": len(displayed_text),
        "language": job.language,
        "dialect": job.dialect,
        "voice_profile": job.voice_profile,
        "emotion": job.emotion,
        "delivery_style": job.delivery_style
    }


@router.get("/history")
def list_tts_history(request):
    """List authenticated user's TTS history."""
    user = get_current_user(request)
    jobs = TTSJob.objects.filter(user=user).order_by('-created_at')
    return [
        {
            "id": str(j.id),
            "title": j.title,
            "voice_profile": j.voice_profile,
            "language": j.language,
            "dialect": j.dialect,
            "emotion": j.emotion,
            "delivery_style": j.delivery_style,
            "duration_seconds": j.duration_seconds,
            "chunks_count": j.chunks_count,
            "audio_url": j.audio_url,
            "created_at": j.created_at.isoformat()
        }
        for j in jobs
    ]
