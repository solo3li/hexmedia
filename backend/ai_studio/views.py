import json
from django.shortcuts import render
from .models import BookProject, ChatMessage, AIConfiguration

def chat_home_view(request):
    config = AIConfiguration.objects.filter(is_active=True).first()
    if not config:
        config = AIConfiguration.objects.create(
            llm_model="gemini-3.8-flash",
            tts_model="gemini-3.8-flash-tts",
            is_active=True
        )

    recent_projects_qs = BookProject.objects.all().order_by('-created_at')[:15]
    
    project_id = request.GET.get('project_id')
    current_project = None
    if project_id:
        try:
            current_project = BookProject.objects.get(id=project_id)
        except BookProject.DoesNotExist:
            pass

    available_voices = [
        {"name": "Charon", "description": "صوت جهوري عميق ورزين (مثالي للراوي)", "gender": "MALE", "pitch": 95},
        {"name": "Puck", "description": "صوت شبابي واضح وحيوي (مثالي للأبطال)", "gender": "MALE", "pitch": 130},
        {"name": "Fenrir", "description": "صوت خشن وقوي (للشخصيات الصارمة والمحاربين)", "gender": "MALE", "pitch": 110},
        {"name": "Kore", "description": "صوت أنثوي دافئ وهادئ (للبطلات والراوية)", "gender": "FEMALE", "pitch": 220},
        {"name": "Aoede", "description": "صوت أنثوي تعبيري وحيوي", "gender": "FEMALE", "pitch": 260},
    ]

    initial_project_data = None
    if current_project:
        characters = [{
            "id": str(c.id),
            "name": c.name,
            "role_type": c.role_type,
            "assigned_voice": c.assigned_voice,
            "description": c.description or "",
            "sample_audio_url": c.sample_audio_url or ""
        } for c in current_project.characters.all()]

        chapters = [{
            "id": str(ch.id),
            "number": ch.number,
            "title": ch.title,
            "summary": ch.summary,
            "status": ch.status,
            "scenes_count": ch.scenes_count,
            "total_duration_seconds": round(ch.total_duration_seconds, 1)
        } for ch in current_project.chapters.all().order_by('number')]

        scenes = [{
            "id": str(s.id),
            "order": s.order,
            "chapter": s.chapter,
            "speaker_name": s.speaker_name,
            "voice": s.speaker.assigned_voice if s.speaker else "Charon",
            "raw_text": s.raw_text,
            "vocalized_text": s.vocalized_text or s.raw_text,
            "audio_url": s.audio_url,
            "duration": round(s.duration_seconds, 1),
            "duration_formatted": f"00:{int(s.duration_seconds):02d}",
            "sfx_name": s.sfx_name or ""
        } for s in current_project.scenes.filter(status='GENERATED').order_by('order')]

        initial_project_data = {
            "id": str(current_project.id),
            "title": current_project.title,
            "author": current_project.author,
            "status": current_project.status,
            "narration_mode": current_project.narration_mode or "SMART",
            "target_duration_minutes": current_project.target_duration_minutes,
            "total_duration_seconds": round(current_project.total_duration_seconds, 1),
            "characters": characters,
            "chapters": chapters,
            "scenes": scenes,
            "scenes_count": len(scenes)
        }

    projects_list = [{
        "id": str(p.id),
        "title": p.title,
        "status": p.status,
        "genre": p.genre or "",
        "scenes_count": p.scenes.count(),
        "total_duration_seconds": round(p.total_duration_seconds, 1)
    } for p in recent_projects_qs]

    messages = []
    if current_project:
        messages = list(current_project.messages.all().order_by('created_at'))

    messages_data = [
        {
            'id': str(m.id),
            'role': m.role,
            'content': m.content,
            'msg_type': m.msg_type,
            'metadata': m.metadata or {}
        }
        for m in messages
    ]

    return render(request, 'chat/index.html', {
        'config': config,
        'recent_projects': recent_projects_qs,
        'current_project': current_project,
        'messages_json': json.dumps(messages_data, ensure_ascii=False),
        'initial_project_json': json.dumps(initial_project_data, ensure_ascii=False),
        'projects_list_json': json.dumps(projects_list, ensure_ascii=False),
        'available_voices_json': json.dumps(available_voices, ensure_ascii=False)
    })
