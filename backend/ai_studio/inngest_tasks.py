import inngest
from .models import BookProject, Character, Scene
from .services.gemini_service import break_into_scenes, generate_voice_audio
from .services.minio_service import upload_bytes
from .services.sfx_library import match_sfx
from .services.timeline_builder import build_designcombo_timeline

inngest_client = inngest.Inngest(
    app_id="hexmedia_audio_drama",
    is_production=False,
)

@inngest_client.create_function(
    fn_id="generate-full-audio-drama",
    trigger=inngest.TriggerEvent(event="audio_drama/generate"),
    rate_limit=inngest.RateLimit(
        limit=20,
        period=60,
        key="event.data.project_id"
    )
)
async def generate_full_audio_drama(ctx: inngest.ContextSync):
    project_id = ctx.event.data.get("project_id")
    project = BookProject.objects.get(id=project_id)
    
    # Step 1: Break text into scenes
    characters = list(project.characters.all())
    char_names = [c.name for c in characters]
    scenes_data = break_into_scenes(project.raw_text, char_names)

    # Step 2: Generate audio for each scene with durable steps
    char_map = {c.name.strip(): c for c in characters}
    narrator = project.characters.filter(role_type='NARRATOR').first() or characters[0]

    for idx, sc in enumerate(scenes_data):
        speaker_name = sc.get("speaker_name", "الراوي").strip()
        matched_char = char_map.get(speaker_name, narrator)
        text = sc.get("raw_text", "")
        emotion = sc.get("emotion", "calm")
        sfx_req = sc.get("sfx_name", "")

        sfx_key, _ = match_sfx(text)
        if not sfx_key and sfx_req:
            sfx_key = sfx_req
        from django.conf import settings
        sfx_url = f"{settings.MINIO_PUBLIC_ENDPOINT}/{settings.MINIO_BUCKET}/sfx/{sfx_key}.wav" if sfx_key else ""

        audio_bytes = generate_voice_audio(text, voice_name=matched_char.assigned_voice, emotion=emotion)
        audio_url = upload_bytes(audio_bytes, f"audio/{project.id}/scene_{idx+1}.wav")
        duration = max(2.5, min(15.0, len(text.split()) * 0.45))

        Scene.objects.create(
            project=project,
            order=idx + 1,
            speaker=matched_char,
            speaker_name=matched_char.name,
            raw_text=text,
            vocalized_text=text,
            emotion=emotion,
            audio_url=audio_url,
            duration_seconds=duration,
            sfx_name=sfx_key,
            sfx_url=sfx_url,
            status='GENERATED'
        )

    # Step 3: Build DesignCombo timeline
    timeline_json = build_designcombo_timeline(project)
    project.status = 'READY'
    project.progress_percentage = 100
    project.save(update_fields=['status', 'progress_percentage'])

    return {
        "status": "complete",
        "project_id": str(project.id),
        "scenes_count": len(scenes_data)
    }

inngest_functions = [generate_full_audio_drama]
