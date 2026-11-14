import io
import json
import logging
import os
import re
import subprocess
import tempfile
import urllib.parse
import uuid
import wave
from typing import Dict, Any, List, Optional
from django.conf import settings
from .minio_service import upload_bytes
from .gemini_service import get_gemini_client, generate_voice_audio

logger = logging.getLogger(__name__)

ALLOWED_VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv", ".avi"}
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB


def probe_video_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extracts duration, dimensions, framerate, and audio presence from video file.
    """
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if res.returncode != 0:
            return {"duration": 5.0, "width": 1080, "height": 1920, "has_audio": False}

        data = json.loads(res.stdout)
        format_info = data.get("format", {})
        duration = float(format_info.get("duration", 5.0))

        width = 1080
        height = 1920
        has_audio = False

        for stream in data.get("streams", []):
            codec_type = stream.get("codec_type")
            if codec_type == "video" and not (width and height and width != 1080):
                width = int(stream.get("width", 1080))
                height = int(stream.get("height", 1920))
            elif codec_type == "audio":
                has_audio = True

        return {
            "duration": round(duration, 2),
            "width": width,
            "height": height,
            "has_audio": has_audio,
        }
    except Exception as e:
        logger.warning(f"Failed to probe video {file_path}: {e}")
        return {"duration": 5.0, "width": 1080, "height": 1920, "has_audio": False}


def save_uploaded_video(file_obj, filename: Optional[str] = None) -> Dict[str, Any]:
    """
    Validates uploaded video file, saves to MinIO and returns metadata.
    """
    name = filename or getattr(file_obj, "name", "video.mp4")
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED_VIDEO_EXTS:
        return {
            "success": False,
            "error": f"صيغة الفيديو غير مدعومة ({ext}). الصيغ المدعومة: MP4, MOV, WebM, MKV",
        }

    video_bytes = file_obj.read() if hasattr(file_obj, "read") else bytes(file_obj)
    if len(video_bytes) > MAX_VIDEO_SIZE:
        return {
            "success": False,
            "error": "حجم الفيديو يتجاوز الحد المسموح به (100 ميجابايت).",
        }

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name

    try:
        meta = probe_video_metadata(tmp_path)
        clean_ext = ".mp4" if ext != ".webm" else ".webm"
        s3_key = f"motion/videos/{uuid.uuid4().hex[:12]}_{os.path.basename(name).replace(' ', '_')}"
        if not s3_key.endswith(clean_ext):
            s3_key += clean_ext

        content_type = "video/mp4" if clean_ext == ".mp4" else "video/webm"
        public_url = upload_bytes(video_bytes, s3_key, content_type)

        return {
            "success": True,
            "url": public_url,
            "s3_key": s3_key,
            "filename": name,
            "duration": meta["duration"],
            "width": meta["width"],
            "height": meta["height"],
            "has_audio": meta["has_audio"],
        }
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def ingest_video_url(url: str) -> Dict[str, Any]:
    """
    Downloads or ingests a video from an external URL (YouTube or direct video link),
    stores it in MinIO, and returns metadata.
    """
    url = (url or "").strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        return {"success": False, "error": "رابط الفيديو غير صالح. يجب أن يبدأ بـ http:// أو https://"}

    parsed = urllib.parse.urlparse(url)
    path_lower = parsed.path.lower()
    is_direct_video = any(path_lower.endswith(ext) for ext in ALLOWED_VIDEO_EXTS)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = os.path.join(tmpdir, f"ingest_{uuid.uuid4().hex[:8]}.mp4")
        video_title = "فيديو خارجي"

        if is_direct_video:
            try:
                import requests
                with requests.get(url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    total_downloaded = 0
                    with open(tmp_file, "wb") as f:
                        for chunk in r.iter_content(chunk_size=65536):
                            total_downloaded += len(chunk)
                            if total_downloaded > MAX_VIDEO_SIZE:
                                return {"success": False, "error": "حجم الفيديو في الرابط يتجاوز الحد المسموح (100 ميجابايت)"}
                            f.write(chunk)
                video_title = os.path.basename(parsed.path) or "direct_video"
            except Exception as e:
                logger.error(f"Failed to download direct video URL {url}: {e}")
                return {"success": False, "error": f"فشل تحميل الفيديو من الرابط المباشر: {str(e)}"}
        else:
            try:
                import yt_dlp
                out_template = os.path.join(tmpdir, "%(id)s.%(ext)s")
                ydl_opts = {
                    "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "outtmpl": out_template,
                    "max_filesize": MAX_VIDEO_SIZE,
                    "quiet": True,
                    "no_warnings": True,
                    "merge_output_format": "mp4",
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    video_title = info.get("title", "فيديو يوتيوب")
                    downloaded_filename = ydl.prepare_filename(info)
                    if not os.path.exists(downloaded_filename):
                        base, _ = os.path.splitext(downloaded_filename)
                        if os.path.exists(f"{base}.mp4"):
                            downloaded_filename = f"{base}.mp4"
                    tmp_file = downloaded_filename
            except Exception as e:
                logger.error(f"yt-dlp failed for URL {url}: {e}")
                return {"success": False, "error": f"تعذر استخراج الفيديو من الرابط: {str(e)}"}

        if not os.path.exists(tmp_file) or os.path.getsize(tmp_file) == 0:
            return {"success": False, "error": "لم يتم العثور على ملف الفيديو بعد التحميل"}

        meta = probe_video_metadata(tmp_file)
        with open(tmp_file, "rb") as vf:
            video_bytes = vf.read()

        s3_key = f"motion/videos/{uuid.uuid4().hex[:12]}_web.mp4"
        public_url = upload_bytes(video_bytes, s3_key, "video/mp4")

        return {
            "success": True,
            "url": public_url,
            "s3_key": s3_key,
            "title": video_title,
            "duration": meta["duration"],
            "width": meta["width"],
            "height": meta["height"],
            "has_audio": meta["has_audio"],
        }


SUPPORTED_TEMPLATES = [
    {
        "id": "dark_neon",
        "name": "نيون فضائي وسينمائي (Dark Neon)",
        "description": "تدرجات نيون متوهجة، شبكة رقمية HUD، ونصوص مضيئة فائقة الجاذبية",
        "accentColor": "#00F0FF",
        "backgroundColor": "#08080a",
        "backgroundType": "gradient",
    },
    {
        "id": "tiktok_kinetic",
        "name": "كينيتك تيك توك (TikTok Kinetic)",
        "description": "نصوص سريعة متحركة، تباين لوني قوي، وحركات بوب تناسب السوشيال ميديا",
        "accentColor": "#FFE600",
        "backgroundColor": "#0e0e12",
        "backgroundType": "gradient",
    },
    {
        "id": "cinematic_narrative",
        "name": "رواية سينمائية (Cinematic Narrative)",
        "description": "توهج ذهبي دافئ، خطوط أنيقة، وأجواء روائية ووثائقية هادئة",
        "accentColor": "#F59E0B",
        "backgroundColor": "#0b0c10",
        "backgroundType": "gradient",
    },
    {
        "id": "clean_corporate",
        "name": "أعمال معاصر (Clean Corporate)",
        "description": "تصميم أنيق وعصري بخلفية فاتحة وألوان احترافية للشركات والتقارير",
        "accentColor": "#2563EB",
        "backgroundColor": "#f8fafc",
        "backgroundType": "gradient",
    },
]

SUPPORTED_ASPECT_RATIOS = [
    {"id": "9:16", "name": "طولي ريلز / تيك توك (9:16)", "width": 1080, "height": 1920},
    {"id": "16:9", "name": "عرضي سينمائي / يوتيوب (16:9)", "width": 1920, "height": 1080},
]

SUPPORTED_FONTS = [
    {"id": "IBM Plex Sans Arabic", "name": "IBM Plex Sans Arabic (معاصر وواضح)"},
    {"id": "Tajawal", "name": "Tajawal (تجوال - هندسي حديث)"},
    {"id": "Cairo", "name": "Cairo (كايرو - عريض وقوي للخطافات)"},
    {"id": "Amiri", "name": "Amiri (أميري - كلاسيكي سينمائي)"},
]

SUPPORTED_BGM_PRESETS = [
    {"id": "cyber_ambient", "name": "Cyber Ambient (سايبر فضائي)"},
    {"id": "cinematic_warm", "name": "Cinematic Warm (سينمائي دافئ)"},
    {"id": "lofi_chill", "name": "Lo-Fi Chill (لوفاي هادئ)"},
    {"id": "energetic_hook", "name": "Energetic Hook (إيقاع حماسي)"},
    {"id": "none", "name": "بدون موسيقى خلفية"},
]

SUPPORTED_ENTRY_ANIMATIONS = [
    {"id": "pop", "name": "Pop (انبثاق سريع)"},
    {"id": "bounce", "name": "Bounce (قفزة ارتدادية)"},
    {"id": "wave", "name": "Wave (موجة تموجية)"},
    {"id": "fade", "name": "Fade (تلاشي متدرج)"},
]

DEFAULT_SAMPLE_WORDS = [
    {"word": "أهلاً", "start": 0.1, "end": 0.6},
    {"word": "بكم", "start": 0.6, "end": 1.0},
    {"word": "في", "start": 1.0, "end": 1.3},
    {"word": "أستوديو", "start": 1.3, "end": 1.9},
    {"word": "HexMedia", "start": 1.9, "end": 2.7},
    {"word": "للموشن", "start": 2.7, "end": 3.3},
    {"word": "جرافيكس", "start": 3.3, "end": 4.0},
    {"word": "البرمجي", "start": 4.0, "end": 4.8},
]


def generate_word_timestamps(
    text: Optional[str] = None,
    duration_seconds: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Splits text into words and calculates synchronized timestamps for motion graphics.
    If duration_seconds is not provided, estimates duration based on word count.
    """
    if not text or not text.strip():
        return DEFAULT_SAMPLE_WORDS

    tokens = [w.strip() for w in text.split() if w.strip()]
    if not tokens:
        return DEFAULT_SAMPLE_WORDS

    num_words = len(tokens)
    if duration_seconds is None or duration_seconds <= 0:
        duration_seconds = max(2.5, round(num_words * 0.42 + 0.8, 1))

    duration_seconds = max(1.0, float(duration_seconds))

    lead_in = 0.15
    trail_out = 0.25
    usable_duration = max(0.4, duration_seconds - lead_in - trail_out)
    word_slot = usable_duration / num_words

    words: List[Dict[str, Any]] = []
    for i, token in enumerate(tokens):
        start = round(lead_in + (i * word_slot), 2)
        end = round(max(start + 0.05, min(duration_seconds - 0.02, start + (word_slot * 0.88))), 2)
        words.append({
            "word": token,
            "start": start,
            "end": end,
        })

    return words


def generate_viral_script(topic: str, tone: Optional[str] = "viral") -> Dict[str, Any]:
    """
    Calls Gemini Flash to generate a high-impact viral video script from topic/idea.
    Includes catchy hook, engaging body, call to action, title, subtitle, and estimated duration.
    Falls back gracefully if API key or client is unavailable.
    """
    clean_topic = (topic or "").strip()
    if not clean_topic:
        clean_topic = "أسرار الذكاء الاصطناعي وتأثيره على المستقبل"

    client, config = get_gemini_client()
    if client:
        try:
            from google.genai import types
            prompt = f"""
أنت خبير محتوى فيروسي (Viral Content Creator) ومصمم سكربتات ريلز وتيك توك وشورتس فائقة الانتشار.
قم بإنشاء سكربت فيديو كينيتك موشن جرافيكس عالي الجاذبية والتأثير حول الموضوع التالي:
"{clean_topic}"
النبرة المطلوبة: {tone or "viral حماسية وشيقة"}

القواعد:
1. hook: خطاف افتتاحي قوي جداً في جملة واحدة تخطف الانتباه خلال أول 3 ثوانٍ.
2. body: جملتان إلى ثلاث جمل متتالية تشرح الفكرة أو الفائدة الأساسية بأسلوب سريع ومثير.
3. call_to_action: دعوة تفاعلية لاتخاذ إجراء (متابعة، تعليق، مشاركة).
4. title: عنوان رئيسي قصير جداً للفيديو (3-4 كلمات).
5. subtitle: تصنيف فرعي قصير جذاب (مثل: "سر حصري", "نصيحة تقنية", "تحذير هام").
6. full_script: النص الكامل مجمعاً للقراءة بالصوت (Hook + Body + CTA) بدون فواصل إضافية.
7. estimated_duration: تقدير واقعي لمدة القراءة بالثواني (بين 4.0 و 15.0 ثانية).

أخرج النتيجة كـ JSON نقي فقط بدون أي كود ماركداون:
{{
  "title": "...",
  "subtitle": "...",
  "hook": "...",
  "body": "...",
  "call_to_action": "...",
  "full_script": "...",
  "estimated_duration": 6.5
}}
"""
            resp = client.models.generate_content(
                model=config.llm_model or "gemini-3.8-flash",
                contents=[prompt],
                config=types.GenerateContentConfig(
                    temperature=0.7,
                )
            )
            raw_text = (resp.text or "").strip()
            json_match = re.search(r"\{[\s\S]*\}", raw_text)
            if json_match:
                data = json.loads(json_match.group(0))
            else:
                cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
                cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
                data = json.loads(cleaned)
            full_script = data.get("full_script") or f"{data.get('hook', '')} {data.get('body', '')} {data.get('call_to_action', '')}".strip()
            word_count = len(full_script.split())
            est_dur = float(data.get("estimated_duration") or max(3.5, round(word_count * 0.42 + 0.8, 1)))
            return {
                "success": True,
                "topic": clean_topic,
                "title": data.get("title", f"أسرار {clean_topic[:20]}"),
                "subtitle": data.get("subtitle", "اكتشاف حصري ⚡"),
                "hook": data.get("hook", f"هل تعرف السر وراء {clean_topic}؟"),
                "body": data.get("body", "كل شيء يتغير بسرعة فائقة ومن لا يواكب سيفوته الكثير."),
                "call_to_action": data.get("call_to_action", "اشترك وتابع للمزيد 🔥"),
                "script": full_script,
                "full_script": full_script,
                "estimated_duration": est_dur,
            }
        except Exception as e:
            logger.warning(f"Gemini script generation fallback: {e}")

    # Fallback heuristic viral script
    hook = f"هل تعرف ما الذي يحدث حقاً في {clean_topic}؟ 🚀"
    body = "الحقيقة أن معظم الناس يغفلون عن هذه النقطة الأساسية، لكنها تغير كل قواعد اللعبة للأفضل تماماً."
    cta = "تابعنا الآن للمزيد من الأسرار اليومية! 🔥"
    full_script = f"{hook} {body} {cta}"
    word_count = len(full_script.split())
    dur = max(4.0, round(word_count * 0.42 + 0.8, 1))

    return {
        "success": True,
        "topic": clean_topic,
        "title": f"أسرار {clean_topic[:20]}",
        "subtitle": "اكتشاف حصري ⚡",
        "hook": hook,
        "body": body,
        "call_to_action": cta,
        "script": full_script,
        "full_script": full_script,
        "estimated_duration": dur,
    }


def synthesize_motion_speech(
    text: str,
    voice_profile: Optional[str] = "Charon",
    user=None,
) -> Dict[str, Any]:
    """
    Synthesizes speech for motion studio using Gemini TTS or ClonedVoice,
    converts to MP3, uploads to MinIO, and returns word timestamps and audio URL.
    """
    clean_text = (text or "").strip()
    if not clean_text:
        return {"success": False, "error": "النص المطلوب تحويله لصوت فارغ"}

    voice = voice_profile or "Charon"

    try:
        from tts.services.audio_stitcher import convert_to_mp3
        wav_bytes = generate_voice_audio(
            clean_text,
            voice_name=voice,
            emotion="neutral",
            language="ar",
            dialect="msa",
        )

        mp3_bytes = convert_to_mp3(wav_bytes)
        s3_key = f"motion/tts_{uuid.uuid4().hex[:12]}.mp3"
        audio_url = upload_bytes(mp3_bytes, s3_key, content_type="audio/mpeg")

        dur = 3.5
        try:
            with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
                calc_dur = round(wf.getnframes() / float(wf.getframerate() or 24000), 1)
                dur = calc_dur if calc_dur > 0 else max(2.5, round(len(clean_text.split()) * 0.42 + 0.8, 1))
        except Exception:
            dur = max(2.5, round(len(clean_text.split()) * 0.42 + 0.8, 1))

        words = generate_word_timestamps(clean_text, duration_seconds=dur)

        return {
            "success": True,
            "audio_url": audio_url,
            "duration": dur,
            "duration_seconds": dur,
            "words": words,
            "voice_profile": voice,
            "voice_id": voice,
            "s3_key": s3_key,
        }
    except Exception as e:
        logger.error(f"synthesize_motion_speech error: {e}")
        return {"success": False, "error": f"فشل توليد التعليق الصوتي: {str(e)}"}


def build_motion_props(
    text: Optional[str] = None,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    speaker_name: Optional[str] = None,
    words: Optional[List[Dict[str, Any]]] = None,
    template_id: str = "dark_neon",
    aspect_ratio: str = "9:16",
    audio_url: Optional[str] = None,
    background_url: Optional[str] = None,
    background_type: Optional[str] = None,
    background_color: Optional[str] = None,
    accent_color: Optional[str] = None,
    duration_seconds: Optional[float] = None,
    fps: int = 30,
    video_start_offset: Optional[float] = 0.0,
    video_volume: Optional[float] = 0.15,
    video_muted: Optional[bool] = False,
    transition_effect: Optional[str] = "zoom_in",
    font_family: Optional[str] = "IBM Plex Sans Arabic",
    entry_animation: Optional[str] = "pop",
    smart_emojis_enabled: Optional[bool] = True,
    word_glow_box: Optional[bool] = True,
    sfx_enabled: Optional[bool] = True,
    sfx_volume: Optional[float] = 0.25,
    bgm_preset: Optional[str] = "cyber_ambient",
    bgm_url: Optional[str] = None,
    bgm_volume: Optional[float] = 0.25,
    smart_ducking: Optional[bool] = True,
    dynamic_zoom: Optional[bool] = True,
    caption_position_percent: Optional[float] = 50.0,
    scenes: Optional[List[Dict[str, Any]]] = None,
    pip_url: Optional[str] = None,
    pip_position: Optional[str] = "top-left",
    pip_scale: Optional[float] = 0.28,
    pip_muted: Optional[bool] = True,
    export_format: Optional[str] = "mp4",
) -> Dict[str, Any]:
    """
    Constructs a validated Remotion MotionCompositionProps dictionary.
    """
    valid_templates = [t["id"] for t in SUPPORTED_TEMPLATES]
    if template_id not in valid_templates:
        template_id = "dark_neon"

    if aspect_ratio not in ["9:16", "16:9"]:
        aspect_ratio = "9:16"

    tpl_meta = next((t for t in SUPPORTED_TEMPLATES if t["id"] == template_id), SUPPORTED_TEMPLATES[0])

    if not words:
        words = generate_word_timestamps(text, duration_seconds)

    if not duration_seconds or duration_seconds <= 0:
        if words:
            duration_seconds = max(3.0, round(words[-1]["end"] + 0.5, 1))
        else:
            duration_seconds = 5.0

    duration_seconds = min(60.0, max(1.5, float(duration_seconds)))
    fps = max(15, min(60, int(fps or 30)))

    resolved_bg_type = background_type
    if not resolved_bg_type and background_url:
        bg_lower = background_url.lower()
        if any(bg_lower.endswith(ext) for ext in [".mp4", ".mov", ".webm", ".mkv"]) or "/videos/" in bg_lower:
            resolved_bg_type = "video"

    return {
        "title": (title or "HexMedia Motion Studio").strip(),
        "subtitle": (subtitle or "Code-to-Video Engine").strip(),
        "speakerName": (speaker_name or "الراوي الذكي").strip(),
        "words": words,
        "templateId": template_id,
        "aspectRatio": aspect_ratio,
        "durationInSeconds": duration_seconds,
        "fps": fps,
        "audioUrl": audio_url or "",
        "backgroundUrl": background_url or "",
        "backgroundType": resolved_bg_type or tpl_meta.get("backgroundType", "gradient"),
        "backgroundColor": background_color or tpl_meta.get("backgroundColor", "#08080a"),
        "accentColor": accent_color or tpl_meta.get("accentColor", "#00F0FF"),
        "videoStartOffset": float(video_start_offset or 0.0),
        "videoVolume": float(video_volume if video_volume is not None else 0.15),
        "videoMuted": bool(video_muted),
        "transitionEffect": str(transition_effect or "zoom_in"),
        "fontFamily": str(font_family or "IBM Plex Sans Arabic"),
        "entryAnimation": str(entry_animation or "pop"),
        "smartEmojisEnabled": bool(smart_emojis_enabled if smart_emojis_enabled is not None else True),
        "wordGlowBox": bool(word_glow_box if word_glow_box is not None else True),
        "sfxEnabled": bool(sfx_enabled if sfx_enabled is not None else True),
        "sfxVolume": float(sfx_volume if sfx_volume is not None else 0.25),
        "bgmPreset": str(bgm_preset or "cyber_ambient"),
        "bgmUrl": str(bgm_url or ""),
        "bgmVolume": float(bgm_volume if bgm_volume is not None else 0.25),
        "smartDucking": bool(smart_ducking if smart_ducking is not None else True),
        "dynamicZoom": bool(dynamic_zoom if dynamic_zoom is not None else True),
        "captionPositionPercent": float(caption_position_percent if caption_position_percent is not None else 50.0),
        "scenes": scenes or [],
        "pipUrl": str(pip_url or ""),
        "pipPosition": str(pip_position or "top-left"),
        "pipScale": float(pip_scale if pip_scale is not None else 0.28),
        "pipMuted": bool(pip_muted if pip_muted is not None else True),
        "exportFormat": str(export_format or "mp4"),
    }


def render_motion_video(
    props: Dict[str, Any],
    composition_id: Optional[str] = None,
    remotion_dir: Optional[str] = None,
    fps: Optional[int] = None,
    export_format: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Renders an MP4 motion graphic or animated GIF using the Remotion CLI,
    uploads to MinIO, and returns accessible playback and download URLs.
    """
    if remotion_dir is None:
        remotion_dir = os.path.join(settings.BASE_DIR.parent, "remotion")

    if not os.path.exists(remotion_dir):
        return {
            "success": False,
            "error": f"مجلد Remotion غير موجود في: {remotion_dir}",
        }

    # Normalize props to handle both camelCase and snake_case keys robustly
    norm_text = props.get("text")
    norm_words = props.get("words")
    norm_tpl = props.get("templateId") or props.get("template_id") or "dark_neon"
    norm_aspect = props.get("aspectRatio") or props.get("aspect_ratio") or "9:16"
    norm_dur = props.get("durationInSeconds") or props.get("duration_seconds")
    norm_fps = fps or props.get("fps") or 30

    norm_v_offset = props.get("videoStartOffset") or props.get("video_start_offset") or 0.0
    norm_v_vol = props.get("videoVolume") if props.get("videoVolume") is not None else props.get("video_volume", 0.15)
    norm_v_muted = props.get("videoMuted") if props.get("videoMuted") is not None else props.get("video_muted", False)
    norm_trans = props.get("transitionEffect") or props.get("transition_effect") or "zoom_in"

    norm_font = props.get("fontFamily") or props.get("font_family") or "IBM Plex Sans Arabic"
    norm_entry = props.get("entryAnimation") or props.get("entry_animation") or "pop"
    norm_smart_emoji = props.get("smartEmojisEnabled") if props.get("smartEmojisEnabled") is not None else props.get("smart_emojis_enabled", True)
    norm_glow_box = props.get("wordGlowBox") if props.get("wordGlowBox") is not None else props.get("word_glow_box", True)

    norm_sfx_en = props.get("sfxEnabled") if props.get("sfxEnabled") is not None else props.get("sfx_enabled", True)
    norm_sfx_vol = props.get("sfxVolume") if props.get("sfxVolume") is not None else props.get("sfx_volume", 0.25)

    norm_bgm_pre = props.get("bgmPreset") or props.get("bgm_preset") or "cyber_ambient"
    norm_bgm_url = props.get("bgmUrl") or props.get("bgm_url")
    norm_bgm_vol = props.get("bgmVolume") if props.get("bgmVolume") is not None else props.get("bgm_volume", 0.25)
    norm_duck = props.get("smartDucking") if props.get("smartDucking") is not None else props.get("smart_ducking", True)
    norm_dyn_zoom = props.get("dynamicZoom") if props.get("dynamicZoom") is not None else props.get("dynamic_zoom", True)

    norm_pos = props.get("captionPositionPercent") if props.get("captionPositionPercent") is not None else props.get("caption_position_percent", 50.0)
    norm_scenes = props.get("scenes") or []

    norm_pip_url = props.get("pipUrl") or props.get("pip_url")
    norm_pip_pos = props.get("pipPosition") or props.get("pip_position") or "top-left"
    norm_pip_scale = props.get("pipScale") if props.get("pipScale") is not None else props.get("pip_scale", 0.28)
    norm_pip_muted = props.get("pipMuted") if props.get("pipMuted") is not None else props.get("pip_muted", True)

    norm_format = export_format or props.get("exportFormat") or props.get("export_format") or "mp4"

    normalized_props = build_motion_props(
        text=norm_text,
        title=props.get("title"),
        subtitle=props.get("subtitle"),
        speaker_name=props.get("speakerName") or props.get("speaker_name"),
        words=norm_words,
        template_id=norm_tpl,
        aspect_ratio=norm_aspect,
        audio_url=props.get("audioUrl") or props.get("audio_url"),
        background_url=props.get("backgroundUrl") or props.get("background_url"),
        background_type=props.get("backgroundType") or props.get("background_type"),
        background_color=props.get("backgroundColor") or props.get("background_color"),
        accent_color=props.get("accentColor") or props.get("accent_color"),
        duration_seconds=float(norm_dur) if norm_dur else None,
        fps=int(norm_fps),
        video_start_offset=float(norm_v_offset),
        video_volume=float(norm_v_vol),
        video_muted=bool(norm_v_muted),
        transition_effect=str(norm_trans),
        font_family=str(norm_font),
        entry_animation=str(norm_entry),
        smart_emojis_enabled=bool(norm_smart_emoji),
        word_glow_box=bool(norm_glow_box),
        sfx_enabled=bool(norm_sfx_en),
        sfx_volume=float(norm_sfx_vol),
        bgm_preset=str(norm_bgm_pre),
        bgm_url=norm_bgm_url,
        bgm_volume=float(norm_bgm_vol),
        smart_ducking=bool(norm_duck),
        dynamic_zoom=bool(norm_dyn_zoom),
        caption_position_percent=float(norm_pos),
        scenes=norm_scenes,
        pip_url=norm_pip_url,
        pip_position=str(norm_pip_pos),
        pip_scale=float(norm_pip_scale),
        pip_muted=bool(norm_pip_muted),
        export_format=str(norm_format),
    )
    merged_props = {**props, **normalized_props}

    aspect_ratio = merged_props.get("aspectRatio", "9:16")
    suffix = "9-16" if aspect_ratio == "9:16" else "16-9"

    if not composition_id:
        composition_id = f"MotionStudio-Dynamic-{suffix}"

    duration_seconds = float(merged_props.get("durationInSeconds", 5.0))
    fps = int(merged_props.get("fps", 30))
    total_frames = max(30, int(round(duration_seconds * fps)))

    with tempfile.TemporaryDirectory() as tmpdir:
        props_file = os.path.join(tmpdir, "props.json")
        out_mp4 = os.path.join(tmpdir, "rendered.mp4")

        with open(props_file, "w", encoding="utf-8") as pf:
            json.dump(merged_props, pf, ensure_ascii=False)

        cmd = [
            "npx",
            "remotion",
            "render",
            "src/index.ts",
            composition_id,
            out_mp4,
            f"--props={props_file}",
            f"--frames=0-{total_frames - 1}",
            "--overwrite",
            "--quiet",
        ]

        logger.info(f"Rendering Remotion motion video: {' '.join(cmd)}")
        try:
            res = subprocess.run(
                cmd,
                cwd=remotion_dir,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if res.returncode != 0:
                err_msg = res.stderr or res.stdout or "فشل تنفيذ ريندر Remotion CLI"
                logger.error(f"Remotion render error: {err_msg}")
                return {"success": False, "error": f"Remotion CLI render failed: {err_msg}"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "استغرق ريندر الفيديو وقتاً أطول من المتوقع (Timeout)"}
        except Exception as e:
            logger.exception("Exception running Remotion CLI render")
            return {"success": False, "error": str(e)}

        if not os.path.exists(out_mp4) or os.path.getsize(out_mp4) == 0:
            return {"success": False, "error": "لم يتم العثور على ملف الفيديو الناتج من الريندر"}

        # Handle GIF Export if requested
        export_fmt = merged_props.get("exportFormat", "mp4").lower()
        if export_fmt == "gif":
            out_gif = os.path.join(tmpdir, "rendered.gif")
            cmd_gif = [
                "ffmpeg",
                "-y",
                "-i", out_mp4,
                "-vf", "fps=15,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
                "-loop", "0",
                out_gif,
            ]
            try:
                subprocess.run(cmd_gif, capture_output=True, text=True, timeout=60, check=True)
                if os.path.exists(out_gif) and os.path.getsize(out_gif) > 0:
                    with open(out_gif, "rb") as gf:
                        gif_bytes = gf.read()

                    s3_gif_key = f"motion/motion_{uuid.uuid4().hex[:12]}.gif"
                    gif_url = upload_bytes(gif_bytes, s3_gif_key, content_type="image/gif")

                    return {
                        "success": True,
                        "video_url": gif_url,
                        "gif_url": gif_url,
                        "download_url": gif_url,
                        "s3_key": s3_gif_key,
                        "composition_id": composition_id,
                        "duration_seconds": duration_seconds,
                        "total_frames": total_frames,
                        "aspect_ratio": aspect_ratio,
                        "template_id": merged_props.get("templateId"),
                        "file_size": len(gif_bytes),
                        "export_format": "gif",
                        "format": "gif",
                        "fps": fps,
                        "message": "تم ريندر وتصدير صورة GIF المتحركة بنجاح 🎬!",
                    }
            except Exception as e:
                logger.warning(f"GIF conversion fallback to MP4: {e}")

        with open(out_mp4, "rb") as vf:
            video_bytes = vf.read()

        file_size = len(video_bytes)
        s3_key = f"motion/motion_{uuid.uuid4().hex[:12]}.mp4"
        public_url = upload_bytes(video_bytes, s3_key, content_type="video/mp4")

        return {
            "success": True,
            "video_url": public_url,
            "download_url": public_url,
            "s3_key": s3_key,
            "composition_id": composition_id,
            "duration_seconds": duration_seconds,
            "total_frames": total_frames,
            "aspect_ratio": aspect_ratio,
            "template_id": merged_props.get("templateId"),
            "file_size": file_size,
            "export_format": "mp4",
            "format": "mp4",
            "fps": fps,
            "message": "تم ريندر وتصدير فيديو الموشن جرافيكس بنجاح 🎬!",
        }
