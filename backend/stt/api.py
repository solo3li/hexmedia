from typing import Optional, List, Dict, Any
from ninja import Router, Schema, File, Form
from ninja.files import UploadedFile
from ninja.errors import HttpError
from django.shortcuts import get_object_or_404
from ai_studio.auth import JWTAuth, django_auth, get_current_user
from .models import STTJob
from .services.stt_engine import process_stt_transcription

router = Router(auth=[JWTAuth(), django_auth])

SUPPORTED_LANGUAGES = [
    {"code": "auto", "name": "تلقائي (اكتشاف ذكي للغة)"},
    {"code": "ar", "name": "العربية (Arabic)"},
    {"code": "en", "name": "الإنجليزية (English)"},
    {"code": "fr", "name": "الفرنسية (Français)"},
    {"code": "es", "name": "الإسبانية (Español)"},
    {"code": "de", "name": "الألمانية (Deutsch)"},
    {"code": "tr", "name": "التركية (Türkçe)"},
    {"code": "it", "name": "الإيطالية (Italiano)"},
    {"code": "ru", "name": "الروسية (Русский)"},
    {"code": "zh", "name": "الصينية (Chinese)"},
    {"code": "ja", "name": "اليابانية (Japanese)"},
    {"code": "ko", "name": "الكورية (Korean)"},
    {"code": "hi", "name": "الهندية (Hindi)"},
    {"code": "ur", "name": "الأردية (Urdu)"},
    {"code": "fa", "name": "الفارسية (Persian)"},
]

TARGET_LANGUAGES = [
    {"code": "", "name": "نفس لغة الصوت الأصلية (بدون ترجمة)"},
    {"code": "ar", "name": "العربية (Arabic)"},
    {"code": "en", "name": "الإنجليزية (English)"},
    {"code": "fr", "name": "الفرنسية (Français)"},
    {"code": "es", "name": "الإسبانية (Español)"},
    {"code": "de", "name": "الألمانية (Deutsch)"},
    {"code": "tr", "name": "التركية (Türkçe)"},
    {"code": "it", "name": "الإيطالية (Italiano)"},
    {"code": "ru", "name": "الروسية (Русский)"},
    {"code": "zh", "name": "الصينية (Chinese)"},
]


class STTResponse(Schema):
    id: str
    title: str
    audio_url: str
    duration_seconds: float
    language: str
    target_language: str
    transcript_text: str
    srt_content: str
    diarization_data: List[Dict[str, Any]]
    has_diarization: bool
    has_timestamps: bool
    created_at: str


@router.get("/options", auth=None)
def get_stt_options(request):
    """Returns available STT models, source languages, and target translation languages."""
    return {
        "model": "gemini-3.5-transcribe",
        "languages": SUPPORTED_LANGUAGES,
        "target_languages": TARGET_LANGUAGES,
    }


@router.post("/transcribe", response=STTResponse)
def transcribe_audio_endpoint(
    request,
    audio_file: UploadedFile = File(...),
    title: Optional[str] = Form("تفريغ صوتي"),
    language: Optional[str] = Form("auto"),
    target_language: Optional[str] = Form(""),
    diarization: Optional[bool] = Form(False),
    timestamps: Optional[bool] = Form(True)
):
    """Transcribes uploaded audio file using Gemini 3.5 Transcribe with optional diarization and translation."""
    user = get_current_user(request)
    audio_bytes = audio_file.read()
    if not audio_bytes:
        raise HttpError(400, "ملف الصوت فارغ أو غير صالح")

    content_type = audio_file.content_type or "audio/wav"
    filename = audio_file.name or "recording.wav"

    diarize_flag = bool(diarization)
    timestamps_flag = True if timestamps is None else bool(timestamps)

    result = process_stt_transcription(
        audio_bytes=audio_bytes,
        filename=filename,
        content_type=content_type,
        language=language or "auto",
        target_language=target_language or "",
        diarization=diarize_flag,
        timestamps=timestamps_flag
    )

    clean_title = (title or "").strip() or f"تفريغ ({filename})"

    job = STTJob.objects.create(
        user=user,
        title=clean_title,
        audio_url=result["audio_url"],
        language=result["language"],
        target_language=result["target_language"],
        transcript_text=result["transcript_text"],
        srt_content=result["srt_content"],
        diarization_data=result["diarization_data"],
        has_diarization=diarize_flag,
        has_timestamps=timestamps_flag,
        duration_seconds=result["duration_seconds"],
        status='READY'
    )

    return {
        "id": str(job.id),
        "title": job.title,
        "audio_url": job.audio_url,
        "duration_seconds": job.duration_seconds,
        "language": job.language,
        "target_language": job.target_language,
        "transcript_text": job.transcript_text,
        "srt_content": job.srt_content,
        "diarization_data": job.diarization_data,
        "has_diarization": job.has_diarization,
        "has_timestamps": job.has_timestamps,
        "created_at": job.created_at.isoformat()
    }


@router.get("/history")
def list_stt_history(request):
    """List authenticated user's STT transcription jobs."""
    user = get_current_user(request)
    jobs = STTJob.objects.filter(user=user).order_by('-created_at')
    return [
        {
            "id": str(j.id),
            "title": j.title,
            "language": j.language,
            "target_language": j.target_language,
            "duration_seconds": j.duration_seconds,
            "has_diarization": j.has_diarization,
            "has_timestamps": j.has_timestamps,
            "transcript_text": j.transcript_text,
            "srt_content": j.srt_content,
            "audio_url": j.audio_url,
            "created_at": j.created_at.isoformat()
        }
        for j in jobs
    ]
