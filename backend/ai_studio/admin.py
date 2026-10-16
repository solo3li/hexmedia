from django.contrib import admin
from .models import AIConfiguration, BookProject, Character, Chapter, Scene, TimelineState, ChatMessage

@admin.register(AIConfiguration)
class AIConfigurationAdmin(admin.ModelAdmin):
    list_display = ('llm_model', 'tts_model', 'is_active', 'updated_at')
    fields = ('gemini_api_key', 'llm_model', 'tts_model', 'available_voices', 'is_active')
    list_editable = ('is_active',)

    def has_add_permission(self, request):
        # Allow only 1 active configuration or standard add
        return super().has_add_permission(request)


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 0
    fields = ('number', 'title', 'status', 'scenes_count', 'total_duration_seconds')
    readonly_fields = ('scenes_count', 'total_duration_seconds')


class CharacterInline(admin.TabularInline):
    model = Character
    extra = 0
    fields = ('name', 'role_type', 'gender', 'assigned_voice', 'speaking_style')


class SceneInline(admin.TabularInline):
    model = Scene
    extra = 0
    fields = ('order', 'speaker_name', 'raw_text', 'emotion', 'duration_seconds', 'status')
    readonly_fields = ('duration_seconds',)


@admin.register(BookProject)
class BookProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'progress_percentage', 'created_at')
    list_filter = ('status', 'genre')
    search_fields = ('title', 'author')
    inlines = [ChapterInline, CharacterInline, SceneInline]


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('project', 'number', 'title', 'status', 'scenes_count', 'total_duration_seconds')
    list_filter = ('status', 'project')
    search_fields = ('title', 'summary', 'project__title')


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'role_type', 'gender', 'assigned_voice')
    list_filter = ('role_type', 'gender', 'assigned_voice')
    search_fields = ('name', 'project__title')


@admin.register(Scene)
class SceneAdmin(admin.ModelAdmin):
    list_display = ('project', 'order', 'speaker_name', 'emotion', 'duration_seconds', 'status')
    list_filter = ('status', 'project')
    search_fields = ('speaker_name', 'raw_text')


@admin.register(TimelineState)
class TimelineStateAdmin(admin.ModelAdmin):
    list_display = ('project', 'total_duration', 'updated_at')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('project', 'role', 'msg_type', 'created_at')
    list_filter = ('role', 'msg_type')
