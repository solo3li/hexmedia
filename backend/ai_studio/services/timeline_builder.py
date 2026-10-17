import uuid
from typing import Dict, Any
from ..models import BookProject, Scene, TimelineState

def build_designcombo_timeline(project: BookProject) -> Dict[str, Any]:
    scenes = project.scenes.filter(status='GENERATED').order_by('order')
    
    current_time = 0.0
    voice_items = []
    sfx_items = []
    subtitle_items = []
    image_items = []

    for scene in scenes:
        duration = max(2.0, scene.duration_seconds)
        start_time = current_time
        end_time = start_time + duration

        # Update scene start time in db
        scene.start_time_seconds = start_time
        scene.save(update_fields=['start_time_seconds'])

        # 0. Visual Track Item
        if scene.image_url:
            image_items.append({
                "id": str(uuid.uuid4()),
                "type": "image",
                "name": f"Visual: {scene.speaker_name}",
                "display": {
                    "from": start_time,
                    "to": end_time
                },
                "details": {
                    "src": scene.image_url,
                    "width": 1920,
                    "height": 1080
                },
                "metadata": {
                    "visual_prompt": scene.visual_prompt,
                    "media_type": scene.media_type,
                    "motion": scene.motion_type
                }
            })

        # 1. Voice Track Item
        item_id = str(uuid.uuid4())
        voice_items.append({
            "id": item_id,
            "type": "audio",
            "name": f"{scene.speaker_name}: {scene.raw_text[:20]}...",
            "display": {
                "from": start_time,
                "to": end_time
            },
            "details": {
                "src": scene.audio_url,
                "volume": 100
            },
            "metadata": {
                "speaker": scene.speaker_name,
                "text": scene.raw_text,
                "vocalized": scene.vocalized_text or scene.raw_text,
                "scene_id": str(scene.id)
            }
        })

        # 2. SFX Track Item (if present)
        if scene.sfx_url:
            sfx_duration = min(6.0, duration)
            sfx_items.append({
                "id": str(uuid.uuid4()),
                "type": "audio",
                "name": f"SFX: {scene.sfx_name}",
                "display": {
                    "from": start_time,
                    "to": start_time + sfx_duration
                },
                "details": {
                    "src": scene.sfx_url,
                    "volume": 65
                },
                "metadata": {
                    "sfx_name": scene.sfx_name
                }
            })

        # 3. Kinetic Subtitle Item
        subtitle_items.append({
            "id": str(uuid.uuid4()),
            "type": "text",
            "name": f"Sub: {scene.speaker_name}",
            "display": {
                "from": start_time,
                "to": end_time
            },
            "details": {
                "text": f"[{scene.speaker_name}] {scene.raw_text}",
                "fontSize": 44,
                "fontFamily": "Cairo",
                "color": "#FFFFFF",
                "textAlign": "center"
            }
        })

        # Small pause (0.4s) between scenes for dramatic pacing
        current_time = end_time + 0.4

    total_duration = current_time

    # Ambient Music Track (spans the entire piece with ducking)
    bgm_items = []
    # Add ambient drone track
    from django.conf import settings
    bgm_url = f"{settings.MINIO_PUBLIC_ENDPOINT}/{settings.MINIO_BUCKET}/sfx/suspense_drone.wav"
    if total_duration > 0:
        bgm_items.append({
            "id": str(uuid.uuid4()),
            "type": "audio",
            "name": "موسيقى محيطية تشويقية (BGM)",
            "display": {
                "from": 0.0,
                "to": total_duration
            },
            "details": {
                "src": bgm_url,
                "volume": 25,
                "loop": True
            }
        })

    tracks = [
        {
            "id": "track_subtitles",
            "type": "text",
            "title": "الترجمة والنص التفاعلي",
            "items": subtitle_items
        }
    ]
    if image_items:
        tracks.append({
            "id": "track_visuals",
            "type": "image",
            "title": "كادرات الفيديو والصور",
            "items": image_items
        })
    tracks.extend([
        {
            "id": "track_dialogue",
            "type": "audio",
            "title": "أصوات الشخصيات والراوي",
            "items": voice_items
        },
        {
            "id": "track_sfx",
            "type": "audio",
            "title": "المؤثرات الصوتية (SFX)",
            "items": sfx_items
        },
        {
            "id": "track_bgm",
            "type": "audio",
            "title": "الموسيقى التصويرية (BGM)",
            "items": bgm_items
        }
    ])

    timeline_json = {
        "version": "1.0",
        "fps": 30,
        "duration": total_duration,
        "size": {
            "width": 1920,
            "height": 1080
        },
        "tracks": tracks
    }

    # Save to TimelineState
    state, _ = TimelineState.objects.get_or_create(project=project)
    state.designcombo_json = timeline_json
    state.total_duration = total_duration
    state.save()

    return timeline_json
