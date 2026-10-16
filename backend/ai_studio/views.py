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

    recent_projects = BookProject.objects.all().order_by('-created_at')[:10]
    
    project_id = request.GET.get('project_id')
    current_project = None
    messages = []

    if project_id:
        try:
            current_project = BookProject.objects.get(id=project_id)
            messages = list(current_project.messages.all().order_by('created_at'))
        except BookProject.DoesNotExist:
            pass

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

    if current_project:
        project_chapters = list(current_project.chapters.all().order_by('number'))
        if project_chapters:
            chapters_data = [{
                'id': str(ch.id),
                'number': ch.number,
                'title': ch.title,
                'summary': ch.summary,
                'status': ch.status,
                'scenes_count': ch.scenes_count,
                'total_duration_seconds': round(ch.total_duration_seconds, 1)
            } for ch in project_chapters]
            
            for m in messages_data:
                if m.get('role') == 'ASSISTANT' and (m.get('msg_type') in ['CASTING_CARD', 'SCENE_AUDIO_CARDS'] or not m.get('metadata', {}).get('chapters')):
                    if not m.get('metadata'):
                        m['metadata'] = {}
                    m['metadata']['chapters'] = chapters_data
                    break

    return render(request, 'chat/index.html', {
        'config': config,
        'recent_projects': recent_projects,
        'current_project': current_project,
        'messages_json': json.dumps(messages_data, ensure_ascii=False),
    })
