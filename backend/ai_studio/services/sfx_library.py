import io
import math
import random
import struct
import wave
from .minio_service import upload_bytes

def generate_sine_wave(frequency: float, duration: float, volume: float = 0.5, sample_rate: int = 24000) -> bytes:
    buf = io.BytesIO()
    num_samples = int(sample_rate * duration)
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        data = bytearray()
        for i in range(num_samples):
            t = float(i) / sample_rate
            # Add subtle envelope
            env = 1.0
            if t < 0.1:
                env = t / 0.1
            elif t > duration - 0.2:
                env = (duration - t) / 0.2
            sample = volume * env * math.sin(2.0 * math.pi * frequency * t)
            val = int(sample * 32767.0)
            val = max(-32768, min(32767, val))
            data.extend(struct.pack('<h', val))
        wf.writeframes(data)
    return buf.getvalue()

def generate_rain(duration: float = 6.0, sample_rate: int = 24000) -> bytes:
    buf = io.BytesIO()
    num_samples = int(sample_rate * duration)
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        data = bytearray()
        prev = 0.0
        for i in range(num_samples):
            # filtered pink-ish noise
            white = (random.random() * 2.0 - 1.0) * 0.15
            pink = (prev * 0.92) + (white * 0.08)
            prev = pink
            val = int(pink * 32767.0)
            val = max(-32768, min(32767, val))
            data.extend(struct.pack('<h', val))
        wf.writeframes(data)
    return buf.getvalue()

def generate_thunder(duration: float = 4.5, sample_rate: int = 24000) -> bytes:
    buf = io.BytesIO()
    num_samples = int(sample_rate * duration)
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        data = bytearray()
        for i in range(num_samples):
            t = float(i) / sample_rate
            # Impact rumble with decay
            env = math.exp(-t * 1.8)
            freq = 55.0 - (t * 8.0)
            noise = (random.random() * 2.0 - 1.0) * 0.3 * env
            sample = (math.sin(2.0 * math.pi * freq * t) * 0.5 + noise) * env
            val = int(sample * 32767.0)
            val = max(-32768, min(32767, val))
            data.extend(struct.pack('<h', val))
        wf.writeframes(data)
    return buf.getvalue()

def generate_door_knock(duration: float = 2.0, sample_rate: int = 24000) -> bytes:
    buf = io.BytesIO()
    num_samples = int(sample_rate * duration)
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        data = bytearray()
        knocks = [0.1, 0.45, 0.8]
        for i in range(num_samples):
            t = float(i) / sample_rate
            sample = 0.0
            for k in knocks:
                dt = t - k
                if 0 <= dt < 0.12:
                    env = math.exp(-dt * 40.0)
                    sample += math.sin(2.0 * math.pi * 120.0 * dt) * 0.7 * env
            val = int(sample * 32767.0)
            val = max(-32768, min(32767, val))
            data.extend(struct.pack('<h', val))
        wf.writeframes(data)
    return buf.getvalue()

def generate_footsteps(duration: float = 4.0, sample_rate: int = 24000) -> bytes:
    buf = io.BytesIO()
    num_samples = int(sample_rate * duration)
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        data = bytearray()
        steps = [0.2, 0.8, 1.4, 2.0, 2.6, 3.2]
        for i in range(num_samples):
            t = float(i) / sample_rate
            sample = 0.0
            for s in steps:
                dt = t - s
                if 0 <= dt < 0.15:
                    env = math.exp(-dt * 30.0)
                    noise = (random.random() * 2.0 - 1.0) * 0.4
                    sample += (math.sin(2.0 * math.pi * 85.0 * dt) * 0.3 + noise) * env
            val = int(sample * 32767.0)
            val = max(-32768, min(32767, val))
            data.extend(struct.pack('<h', val))
        wf.writeframes(data)
    return buf.getvalue()

def generate_suspense_drone(duration: float = 8.0, sample_rate: int = 24000) -> bytes:
    buf = io.BytesIO()
    num_samples = int(sample_rate * duration)
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        data = bytearray()
        for i in range(num_samples):
            t = float(i) / sample_rate
            # 65Hz root + 97.5Hz fifth with subtle beating
            sample = (
                math.sin(2.0 * math.pi * 65.0 * t) * 0.35 +
                math.sin(2.0 * math.pi * 97.5 * t + math.sin(t * 0.5)) * 0.25 +
                math.sin(2.0 * math.pi * 130.0 * t) * 0.15
            )
            val = int(sample * 32767.0)
            val = max(-32768, min(32767, val))
            data.extend(struct.pack('<h', val))
        wf.writeframes(data)
    return buf.getvalue()

# Pre-seeded catalog
SFX_CATALOG = {
    "rain": {"name": "صوت مطر مستمر", "duration": 6.0, "generator": generate_rain, "keywords": ["مطر", "عاصفة", "غيث", "ماء", "شتاء"]},
    "thunder": {"name": "هزيم رعد مدوي", "duration": 4.5, "generator": generate_thunder, "keywords": ["رعد", "برق", "صاعقة", "انفجار", "دوي"]},
    "door_knock": {"name": "طرق على الباب", "duration": 2.0, "generator": generate_door_knock, "keywords": ["طرق", "دق", "باب", "افتح", "يطرق"]},
    "footsteps": {"name": "خطوات أقدام تقترب", "duration": 4.0, "generator": generate_footsteps, "keywords": ["خطوات", "يمشي", "يقترب", "أقدام", "ركض", "سار"]},
    "suspense_drone": {"name": "موسيقى ترقب وغموض", "duration": 8.0, "generator": generate_suspense_drone, "keywords": ["غموض", "خوف", "سر", "ظلام", "صمت", "حذر", "مرعب"]},
}

def seed_sfx_library():
    """Generates and uploads built-in sound effects to MinIO if not present"""
    seeded_urls = {}
    for key, item in SFX_CATALOG.items():
        object_key = f"sfx/{key}.wav"
        try:
            audio_bytes = item["generator"]()
            url = upload_bytes(audio_bytes, object_key, content_type="audio/wav")
            seeded_urls[key] = {
                "name": item["name"],
                "url": url,
                "duration": item["duration"]
            }
        except Exception as e:
            print(f"Failed to seed SFX {key}: {e}")
    return seeded_urls

def match_sfx(text: str) -> tuple[str, float]:
    """Matches text keywords with available SFX"""
    text_lower = text.lower()
    for key, item in SFX_CATALOG.items():
        for kw in item["keywords"]:
            if kw in text_lower:
                return key, item["duration"]
    return "", 0.0
