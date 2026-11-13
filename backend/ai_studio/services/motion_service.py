import json
import logging
import os
import subprocess
import tempfile
import urllib.parse
import uuid
from typing import Dict, Any, List, Optional
from django.conf import settings
from .minio_service import upload_bytes

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
        # Standard speech rate: ~0.42s per word + 0.8s padding
        duration_seconds = max(2.5, round(num_words * 0.42 + 0.8, 1))

    # Clamp duration to a sensible minimum to prevent timestamp inversion
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
) -> Dict[str, Any]:
    """
    Constructs a validated Remotion MotionCompositionProps dictionary.
    """
    valid_templates = [t["id"] for t in SUPPORTED_TEMPLATES]
    if template_id not in valid_templates:
        template_id = "dark_neon"

    if aspect_ratio not in ["9:16", "16:9"]:
        aspect_ratio = "9:16"

    # Find template defaults
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

    # Determine background type: if background_url looks like a video or background_type is video
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
    }


def render_motion_video(
    props: Dict[str, Any],
    composition_id: Optional[str] = None,
    remotion_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Renders an MP4 motion graphic using the Remotion CLI, uploads to MinIO,
    and returns accessible playback and download URLs.
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
    norm_fps = props.get("fps") or 30

    norm_v_offset = props.get("videoStartOffset") or props.get("video_start_offset") or 0.0
    norm_v_vol = props.get("videoVolume") if props.get("videoVolume") is not None else props.get("video_volume", 0.15)
    norm_v_muted = props.get("videoMuted") if props.get("videoMuted") is not None else props.get("video_muted", False)
    norm_trans = props.get("transitionEffect") or props.get("transition_effect") or "zoom_in"

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
    )
    # Merge with original props so any custom metadata is preserved
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

        with open(out_mp4, "rb") as vf:
            video_bytes = vf.read()

        file_size = len(video_bytes)
        s3_key = f"motion/motion_{uuid.uuid4().hex[:12]}.mp4"
        public_url = upload_bytes(video_bytes, s3_key, "video/mp4")

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
            "message": "تم ريندر وتصدير فيديو الموشن جرافيكس بنجاح 🎬!",
        }
