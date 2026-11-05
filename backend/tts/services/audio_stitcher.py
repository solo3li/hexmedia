import io
import wave
import subprocess
import logging
from typing import List

logger = logging.getLogger(__name__)


def stitch_wav_buffers(wav_buffers: List[bytes], pause_seconds: float = 0.3) -> bytes:
    """
    Concatenates multiple WAV byte buffers into a single unified master WAV buffer.
    Inserts a small silence pause between consecutive clips.
    """
    if not wav_buffers:
        return b""

    valid_buffers = [b for b in wav_buffers if b and len(b) > 44]
    if not valid_buffers:
        return b""

    if len(valid_buffers) == 1:
        return valid_buffers[0]

    master_buf = io.BytesIO()

    # Read audio parameters from the first valid buffer
    with wave.open(io.BytesIO(valid_buffers[0]), 'rb') as first_wf:
        nchannels = first_wf.getnchannels()
        sampwidth = first_wf.getsampwidth()
        framerate = first_wf.getframerate()

    with wave.open(master_buf, 'wb') as out_wf:
        out_wf.setnchannels(nchannels)
        out_wf.setsampwidth(sampwidth)
        out_wf.setframerate(framerate)

        silence_samples = int(framerate * pause_seconds)
        silence_bytes = b'\x00' * (silence_samples * nchannels * sampwidth)

        for idx, buf in enumerate(valid_buffers):
            try:
                with wave.open(io.BytesIO(buf), 'rb') as in_wf:
                    frames = in_wf.readframes(in_wf.getnframes())
                    out_wf.writeframes(frames)
                    # Add pause between segments (except after the last one)
                    if idx < len(valid_buffers) - 1 and silence_samples > 0:
                        out_wf.writeframes(silence_bytes)
            except Exception:
                continue

    return master_buf.getvalue()


def convert_to_mp3(audio_bytes: bytes, bitrate: str = "192k") -> bytes:
    """
    Converts audio bytes (e.g. WAV, PCM) to MP3 using ffmpeg libmp3lame.
    Falls back to original audio_bytes if ffmpeg fails.
    """
    if not audio_bytes:
        return b""
    cmd = [
        "ffmpeg", "-y",
        "-i", "pipe:0",
        "-c:a", "libmp3lame",
        "-b:a", bitrate,
        "-f", "mp3",
        "pipe:1"
    ]
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out, err = proc.communicate(input=audio_bytes, timeout=30)
        if proc.returncode == 0 and out and len(out) > 100:
            return out
        logger.warning(f"ffmpeg MP3 conversion returned code {proc.returncode}: {err.decode('utf-8', errors='ignore')[:300]}")
    except Exception as e:
        logger.warning(f"ffmpeg MP3 conversion failed: {e}")
    return audio_bytes

