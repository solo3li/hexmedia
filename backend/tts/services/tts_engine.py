import io
import re
import uuid
import wave
import logging
from typing import List, Dict, Any, Tuple
from .chunker import split_text_into_chunks
from .audio_stitcher import stitch_wav_buffers
from ai_studio.services.gemini_service import generate_voice_audio, call_gemini_chat
from ai_studio.services.minio_service import upload_bytes

logger = logging.getLogger(__name__)


def auto_diacritize_text(text: str, language: str = 'ar', dialect: str = 'msa') -> str:
    """
    Applies automatic diacritization (تشكيل) and phonetic enhancement for Arabic text
    to guarantee accurate pronunciation by Gemini TTS.
    """
    if language != 'ar' or not text:
        return text

    # If text already has substantial Arabic diacritics, return it as is
    diacritics_count = len(re.findall(r'[\u064B-\u0652\u0670]', text))
    if diacritics_count > len(text) * 0.2:
        return text

    try:
        prompt = (
            f"أنت خبير في علم الصرف والنحو ومخارج الحروف العربية. "
            f"قم بضبط وتشكيل النص التالي بالكامل بالحركات الإعرابية التامة (فتحة، ضمة، كسرة، سكون، شدة، تنوين) "
            f"ليكون جاهزاً للقراءة الصوتية بلهجة ({dialect}) بدقة لغوية 100% دون حذف أو إضافة أي كلمات:\n\n{text}"
        )
        vocalized = call_gemini_chat(prompt)
        if vocalized and len(vocalized) > len(text) * 0.7:
            # Clean any backticks or conversational meta from LLM
            vocalized = re.sub(r'```.*?```', '', vocalized, flags=re.DOTALL)
            vocalized = re.sub(r'[*_#]', '', vocalized).strip()
            return vocalized
    except Exception as e:
        logger.warning(f"Auto-diacritization fallback to raw text: {e}")

    return text


def process_tts_generation(
    text: str,
    voice_profile: str = "Charon",
    language: str = "ar",
    dialect: str = "msa",
    emotion: str = "neutral",
    delivery_style: str = "documentary",
    custom_instructions: str = ""
) -> Dict[str, Any]:
    """
    Core engine function:
    1. Splits long-form text into sentence-bounded chunks (< 2500 chars).
    2. Auto-diacritizes text if Arabic.
    3. Synthesizes WAV audio for each chunk using Gemini TTS.
    4. Stitches all chunks into a seamless master WAV audio.
    5. Uploads to MinIO and returns complete URLs and metadata.
    """
    raw_chunks = split_text_into_chunks(text, max_chars=2500)
    job_id = uuid.uuid4().hex[:12]

    chunk_wav_list = []
    chunk_meta_list = []
    vocalized_chunks = []
    sample_rate = 24000

    for idx, c in enumerate(raw_chunks):
        vocalized_c = auto_diacritize_text(c, language=language, dialect=dialect)
        vocalized_chunks.append(vocalized_c)

        wav_bytes = generate_voice_audio(vocalized_c, voice_name=voice_profile, emotion=emotion)
        chunk_wav_list.append(wav_bytes)

        # Calculate chunk duration
        chunk_dur = 0.0
        try:
            with wave.open(io.BytesIO(wav_bytes), 'rb') as wf:
                chunk_dur = wf.getnframes() / float(wf.getframerate() or 24000)
                sample_rate = wf.getframerate()
        except Exception:
            chunk_dur = max(2.0, len(c.split()) * 0.45)

        chunk_filename = f"tts/{job_id}/chunk_{idx + 1}.wav"
        chunk_url = upload_bytes(wav_bytes, chunk_filename)

        chunk_meta_list.append({
            "order": idx + 1,
            "text": c[:120] + ("..." if len(c) > 120 else ""),
            "duration": round(chunk_dur, 1),
            "audio_url": chunk_url
        })

    # Stitch master WAV
    master_wav = stitch_wav_buffers(chunk_wav_list, pause_seconds=0.35)
    master_dur = 0.0
    try:
        with wave.open(io.BytesIO(master_wav), 'rb') as mwf:
            master_dur = mwf.getnframes() / float(mwf.getframerate() or 24000)
    except Exception:
        master_dur = sum(c["duration"] for c in chunk_meta_list)

    master_filename = f"tts/{job_id}/master_tts.wav"
    master_audio_url = upload_bytes(master_wav, master_filename)

    full_vocalized = "\n\n".join(vocalized_chunks)

    return {
        "job_id": job_id,
        "master_audio_url": master_audio_url,
        "duration_seconds": round(master_dur, 1),
        "chunks_count": len(raw_chunks),
        "chunks": chunk_meta_list,
        "vocalized_text": full_vocalized,
        "voice_profile": voice_profile,
        "language": language,
        "dialect": dialect,
        "emotion": emotion,
        "delivery_style": delivery_style
    }
