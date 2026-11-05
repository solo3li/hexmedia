import io
import wave
import uuid
import logging
from typing import Optional, List, Dict, Any
from ninja import Router, Schema, File, Form
from ninja.files import UploadedFile
from ninja.errors import HttpError
from django.shortcuts import get_object_or_404
from ai_studio.auth import JWTAuth, django_auth, get_current_user
from .models import TTSJob, ClonedVoice
from .services.tts_options import LANGUAGES, VOICES, EMOTIONS, DELIVERY_STYLES
from .services.tts_engine import process_tts_generation
from .services.voice_cloner import convert_to_wav_24k_mono, replicate_voice_with_gemini, get_wav_duration
from ai_studio.services.gemini_service import generate_voice_audio, get_gemini_client
from ai_studio.services.minio_service import upload_bytes

logger = logging.getLogger(__name__)

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


class ClonedVoiceOut(Schema):
    id: str
    name: str
    gemini_voice_id: str
    source_audio_url: str
    consent_audio_url: str
    sample_audio_url: str
    status: str
    created_at: str


class ClonedVoiceTestRequest(Schema):
    text: Optional[str] = "أهلاً بك! هذا اختباري الأول بصوتي المستنسخ الجديد عبر تقنية جيميناي 3.8 فلاش."


class ClonedVoiceTestResponse(Schema):
    voice_id: str
    gemini_voice_id: str
    name: str
    audio_url: str
    duration_seconds: float
    text: str


@router.post("/voices/clone", response=ClonedVoiceOut)
def clone_voice_endpoint(
    request,
    name: Optional[str] = Form("صوتي المستنسخ"),
    source_audio: UploadedFile = File(...),
    consent_audio: UploadedFile = File(...)
):
    """
    Step 3 of voice cloning wizard:
    Accepts source_audio recording (up to 60s) and mandatory consent_audio phrase.
    Converts both to 24kHz mono 16-bit WAV, calls Gemini Voices API with store=True,
    and returns created cloned voice.
    """
    user = get_current_user(request)
    source_bytes = source_audio.read()
    consent_bytes = consent_audio.read()

    if not source_bytes:
        raise HttpError(400, "التسجيل الصوتي المرجعي (source_audio) فارغ أو غير صالح")
    if not consent_bytes:
        raise HttpError(400, "تسجيل إقرار الموافقة البيومترية (consent_audio) فارغ أو غير صالح")

    voice_name = (name or "").strip() or "صوتي المستنسخ"

    # Convert audio to 24kHz mono 16-bit WAV per Gemini specification
    source_wav = convert_to_wav_24k_mono(source_bytes)
    consent_wav = convert_to_wav_24k_mono(consent_bytes)

    source_dur = get_wav_duration(source_wav)
    if source_dur < 9.5:
        raise HttpError(400, "التسجيل الصوتي المرجعي قصير جداً. يجب أن تكون مدته 10 ثوانٍ على الأقل وحتى 60 ثانية.")
    if source_dur > 70.0:
        raise HttpError(400, "التسجيل الصوتي المرجعي يتجاوز الحد الأقصى المسموح به (60 ثانية).")

    voice_uuid = uuid.uuid4()
    source_filename = f"cloned_voices/{voice_uuid}/source.wav"
    consent_filename = f"cloned_voices/{voice_uuid}/consent.wav"

    source_url = upload_bytes(source_wav, source_filename)
    consent_url = upload_bytes(consent_wav, consent_filename)

    # Call Gemini voices.create API
    try:
        gemini_voice_id, status = replicate_voice_with_gemini(
            name=voice_name,
            source_wav=source_wav,
            consent_wav=consent_wav
        )
    except Exception as e:
        logger.error(f"Replication failed: {e}")
        raise HttpError(400, f"فشل استنساخ الصوت: {e}")

    cloned_voice = ClonedVoice.objects.create(
        id=voice_uuid,
        user=user,
        name=voice_name,
        gemini_voice_id=gemini_voice_id,
        source_audio_url=source_url,
        consent_audio_url=consent_url,
        status=status
    )

    return {
        "id": str(cloned_voice.id),
        "name": cloned_voice.name,
        "gemini_voice_id": cloned_voice.gemini_voice_id,
        "source_audio_url": cloned_voice.source_audio_url,
        "consent_audio_url": cloned_voice.consent_audio_url,
        "sample_audio_url": cloned_voice.sample_audio_url,
        "status": cloned_voice.status,
        "created_at": cloned_voice.created_at.isoformat()
    }


@router.get("/voices/cloned", response=List[ClonedVoiceOut])
def list_cloned_voices_endpoint(request):
    """Lists authenticated user's cloned voices."""
    user = get_current_user(request)
    voices = ClonedVoice.objects.filter(user=user).order_by('-created_at')
    return [
        {
            "id": str(v.id),
            "name": v.name,
            "gemini_voice_id": v.gemini_voice_id,
            "source_audio_url": v.source_audio_url,
            "consent_audio_url": v.consent_audio_url,
            "sample_audio_url": v.sample_audio_url,
            "status": v.status,
            "created_at": v.created_at.isoformat()
        }
        for v in voices
    ]


@router.post("/voices/cloned/{voice_id}/test", response=ClonedVoiceTestResponse)
def test_cloned_voice_endpoint(request, voice_id: str, data: Optional[ClonedVoiceTestRequest] = None):
    """Synthesizes a test speech sample with the cloned voice."""
    user = get_current_user(request)
    try:
        cloned_voice = ClonedVoice.objects.get(id=uuid.UUID(voice_id), user=user)
    except Exception:
        cloned_voice = get_object_or_404(ClonedVoice, gemini_voice_id=voice_id, user=user)

    test_text = (data.text if data and data.text else "").strip() or "أهلاً بك! هذا اختباري الأول بصوتي المستنسخ الجديد عبر تقنية جيميناي 3.8 فلاش."

    wav_bytes = generate_voice_audio(
        test_text,
        voice_name=cloned_voice.gemini_voice_id or str(cloned_voice.id),
        emotion="neutral",
        language="ar",
        dialect="msa"
    )

    sample_filename = f"cloned_voices/{cloned_voice.id}/sample_test.wav"
    sample_url = upload_bytes(wav_bytes, sample_filename)

    cloned_voice.sample_audio_url = sample_url
    cloned_voice.save(update_fields=['sample_audio_url'])

    duration = 3.0
    try:
        with wave.open(io.BytesIO(wav_bytes), 'rb') as wf:
            duration = round(wf.getnframes() / float(wf.getframerate() or 24000), 1)
    except Exception:
        pass

    return {
        "voice_id": str(cloned_voice.id),
        "gemini_voice_id": cloned_voice.gemini_voice_id,
        "name": cloned_voice.name,
        "audio_url": sample_url,
        "duration_seconds": duration,
        "text": test_text
    }


@router.delete("/voices/cloned/{voice_id}")
def delete_cloned_voice_endpoint(request, voice_id: str):
    """Deletes cloned voice from DB and removes it from Gemini Voices storage if applicable."""
    user = get_current_user(request)
    try:
        cloned_voice = ClonedVoice.objects.get(id=uuid.UUID(voice_id), user=user)
    except Exception:
        cloned_voice = get_object_or_404(ClonedVoice, gemini_voice_id=voice_id, user=user)

    client, _ = get_gemini_client()
    if client and cloned_voice.gemini_voice_id and not cloned_voice.gemini_voice_id.startswith("voice_rep_"):
        try:
            client.voices.delete(id=cloned_voice.gemini_voice_id)
        except Exception as e:
            logger.warning(f"client.voices.delete error for {cloned_voice.gemini_voice_id}: {e}")

    cloned_voice.delete()
    return {"success": True, "message": "تم حذف الصوت المستنسخ بنجاح"}

