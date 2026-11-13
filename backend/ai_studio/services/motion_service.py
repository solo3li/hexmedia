import json
import logging
import os
import subprocess
import tempfile
import uuid
from typing import Dict, Any, List, Optional
from django.conf import settings
from .minio_service import upload_bytes

logger = logging.getLogger(__name__)

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

    lead_in = 0.15
    trail_out = 0.35
    usable_duration = max(0.5, duration_seconds - lead_in - trail_out)
    word_slot = usable_duration / num_words

    words: List[Dict[str, Any]] = []
    for i, token in enumerate(tokens):
        start = round(lead_in + (i * word_slot), 2)
        end = round(min(duration_seconds - 0.05, start + (word_slot * 0.88)), 2)
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
        "backgroundType": background_type or tpl_meta.get("backgroundType", "gradient"),
        "backgroundColor": background_color or tpl_meta.get("backgroundColor", "#08080a"),
        "accentColor": accent_color or tpl_meta.get("accentColor", "#00F0FF"),
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

    aspect_ratio = props.get("aspectRatio", "9:16")
    suffix = "9-16" if aspect_ratio == "9:16" else "16-9"

    if not composition_id:
        composition_id = f"MotionStudio-Dynamic-{suffix}"

    duration_seconds = float(props.get("durationInSeconds", 5.0))
    fps = int(props.get("fps", 30))
    total_frames = max(30, int(round(duration_seconds * fps)))

    with tempfile.TemporaryDirectory() as tmpdir:
        props_file = os.path.join(tmpdir, "props.json")
        out_mp4 = os.path.join(tmpdir, "rendered.mp4")

        with open(props_file, "w", encoding="utf-8") as pf:
            json.dump(props, pf, ensure_ascii=False)

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
            "template_id": props.get("templateId"),
            "file_size": file_size,
            "message": "تم ريندر وتصدير فيديو الموشن جرافيكس بنجاح 🎬!",
        }
