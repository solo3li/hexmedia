import json
import logging
import os
import subprocess
import tempfile
import urllib.request
import uuid
from typing import Dict, Any, Optional

import redis
from django.conf import settings
from ..models import BookProject, Scene, TimelineState
from .minio_service import upload_bytes

logger = logging.getLogger(__name__)

REDIS_URL = getattr(settings, 'REDIS_URL', 'redis://127.0.0.1:6379/0')

def get_redis_client():
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        r.ping()
        return r
    except Exception as e:
        logger.warning(f"Could not connect to Redis at {REDIS_URL}: {e}")
        return None

def build_remotion_payload(project: BookProject) -> Dict[str, Any]:
    """
    Constructs timeline clips payload matching Remotion / Revideo worker schema.
    """
    scenes = project.scenes.filter(status='GENERATED').order_by('order')
    if not scenes.exists():
        scenes = project.scenes.all().order_by('order')

    clips = []
    current_time = 0.0

    for idx, sc in enumerate(scenes):
        dur = max(2.5, sc.duration_seconds or 3.5)
        start = current_time

        # Visual Clip (Image / Video with 16:9 canvas: 1280x720)
        img_url = sc.image_url
        if img_url:
            clips.append({
                "id": f"visual_{sc.id}",
                "type": "video",
                "src": img_url,
                "x": 0,
                "y": 0,
                "width": 1280,
                "height": 720,
                "start": start,
                "duration": dur,
                "motion": sc.motion_type or "zoom_in"
            })

        # Voice Audio Clip
        if sc.audio_url:
            clips.append({
                "id": f"audio_{sc.id}",
                "type": "audio",
                "src": sc.audio_url,
                "start": start,
                "duration": dur
            })

        # Subtitle Text Clip
        text_content = sc.vocalized_text or sc.raw_text
        if text_content:
            short_text = text_content[:90] + ("..." if len(text_content) > 90 else "")
            clips.append({
                "id": f"text_{sc.id}",
                "type": "text",
                "text": f"{sc.speaker_name}: {short_text}",
                "x": 80,
                "y": 620,
                "width": 1120,
                "height": 60,
                "fontSize": 28,
                "color": "#FFFFFF",
                "start": start,
                "duration": dur
            })

        current_time += dur + 0.3

    total_duration = max(3.0, round(current_time, 1))

    return {
        "video_id": f"film_{project.id}",
        "title": project.title,
        "variables": {
            "duration": total_duration,
            "bgColor": "#08080a",
            "clips": clips
        }
    }

def render_film_locally(project_id: str) -> Dict[str, Any]:
    """
    Renders high-quality 1080p MP4 directly using FFmpeg with Ken Burns motion & voiceover sync.
    Guaranteed instant output that works on any machine where FFmpeg is installed.
    """
    project = BookProject.objects.get(id=project_id)
    scenes = project.scenes.filter(status='GENERATED').order_by('order')
    if not scenes.exists():
        scenes = project.scenes.all().order_by('order')

    if not scenes.exists():
        return {"success": False, "error": "لا توجد مشاهد جاهزة للريندر"}

    with tempfile.TemporaryDirectory() as tmpdir:
        scene_mp4s = []
        
        for idx, sc in enumerate(scenes):
            dur = max(2.5, sc.duration_seconds or 3.5)
            img_path = os.path.join(tmpdir, f"img_{idx}.jpg")
            audio_path = os.path.join(tmpdir, f"audio_{idx}.mp3")
            out_scene_mp4 = os.path.join(tmpdir, f"scene_{idx}.mp4")

            # 1. Download image
            if sc.image_url:
                try:
                    urllib.request.urlretrieve(sc.image_url, img_path)
                except Exception:
                    # Fallback blank image
                    subprocess.run(
                        f"ffmpeg -y -f lavfi -i color=c=0x0e0e12:s=1920x1080:d=1 -frames:v 1 {img_path}",
                        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
            else:
                subprocess.run(
                    f"ffmpeg -y -f lavfi -i color=c=0x0e0e12:s=1920x1080:d=1 -frames:v 1 {img_path}",
                    shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )

            # 2. Download audio or generate silence
            has_real_audio = False
            if sc.audio_url:
                try:
                    urllib.request.urlretrieve(sc.audio_url, audio_path)
                    has_real_audio = True
                except Exception:
                    pass

            if not has_real_audio:
                subprocess.run(
                    f"ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=stereo -t {dur} {audio_path}",
                    shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )

            # 3. Create Scene MP4 with subtle Ken Burns zoom (1.0 -> 1.08)
            # Zoompan filter: zoom from 1 to 1.08 over duration
            fps = 25
            total_frames = int(dur * fps)
            zoom_filter = f"scale=1920:1080,zoompan=z='min(zoom+0.0008,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s=1920x1080:fps={fps}"
            
            cmd = (
                f"ffmpeg -y -loop 1 -i '{img_path}' -i '{audio_path}' "
                f"-vf \"{zoom_filter}\" -c:v libx264 -preset ultrafast -tune stillimage "
                f"-c:a aac -b:a 192k -pix_fmt yuv420p -shortest '{out_scene_mp4}'"
            )
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if os.path.exists(out_scene_mp4):
                scene_mp4s.append(out_scene_mp4)

        if not scene_mp4s:
            return {"success": False, "error": "فشل إنشاء مقاطع المشاهد"}

        # 4. Concatenate all scene MP4s
        concat_txt = os.path.join(tmpdir, "concat.txt")
        with open(concat_txt, "w") as f:
            for s_mp4 in scene_mp4s:
                f.write(f"file '{s_mp4}'\n")

        final_mp4 = os.path.join(tmpdir, f"film_{project_id}.mp4")
        concat_cmd = f"ffmpeg -y -f concat -safe 0 -i '{concat_txt}' -c copy '{final_mp4}'"
        subprocess.run(concat_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if os.path.exists(final_mp4):
            with open(final_mp4, "rb") as f:
                mp4_bytes = f.read()
            s3_key = f"films/film_{project_id}_{uuid.uuid4().hex[:8]}.mp4"
            public_url = upload_bytes(mp4_bytes, s3_key, "video/mp4")

            # Update TimelineState
            timeline, _ = TimelineState.objects.get_or_create(project=project)
            timeline.exported_video_url = public_url
            timeline.save(update_fields=['exported_video_url'])

            return {
                "success": True,
                "video_url": public_url,
                "message": "تم ريندر وتجميع الفيلم الكامل بنجاح 🎬!"
            }

        return {"success": False, "error": "تعذر دمج مقاطع الفيلم"}

def render_or_queue_project(project_id: str) -> Dict[str, Any]:
    """
    Attempts Redis Remotion Worker queue dispatch if available, and performs instant local render.
    """
    project = BookProject.objects.get(id=project_id)
    r = get_redis_client()
    
    # 1. Dispatch Remotion Payload to Redis Queue for background container worker
    payload = build_remotion_payload(project)
    if r:
        try:
            r.rpush('revideo:render_queue', json.dumps(payload))
            logger.info(f"Dispatched project {project_id} to Remotion render queue.")
        except Exception as e:
            logger.warning(f"Failed to push to Remotion queue: {e}")

    # 2. Also run reliable local render to immediately yield video for chat
    return render_film_locally(project_id)
