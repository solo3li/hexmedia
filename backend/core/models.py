import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class AIConfiguration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gemini_api_key = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="أدخل مفتاح Gemini API هنا (سيتم استخدامه للشات والتحليل والصوت)"
    )
    llm_model = models.CharField(
        max_length=100,
        default="gemini-3.8-flash",
        help_text="اسم موديل الـ LLM للشات وتحليل الكتب (مثال: gemini-3.8-flash أو gemini-2.5-flash)"
    )
    tts_model = models.CharField(
        max_length=100,
        default="gemini-3.8-flash-tts",
        help_text="اسم موديل الـ TTS لتوليد أصوات الشخصيات (مثال: gemini-3.8-flash-tts)"
    )
    available_voices = models.JSONField(
        default=list,
        blank=True,
        help_text="قائمة أسماء الأصوات المتاحة"
    )
    is_active = models.BooleanField(default=True, help_text="تفعيل هذا الإعداد")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_studio_aiconfiguration'
        verbose_name = "إعدادات الذكاء الاصطناعي (AI Config)"
        verbose_name_plural = "إعدادات الذكاء الاصطناعي (AI Config)"

    def save(self, *args, **kwargs):
        if not self.available_voices:
            self.available_voices = [
                {"name": "Puck", "gender": "male", "description": "صوت رجالي عميق ومتحمس (مناسب للأبطال والشباب)"},
                {"name": "Charon", "gender": "male", "description": "صوت جهوري وقور وهادئ (مناسب للراوي والحكيم)"},
                {"name": "Kore", "gender": "female", "description": "صوت نسائي دافئ وواضح (مناسب للراوية أو البطلة)"},
                {"name": "Fenrir", "gender": "male", "description": "صوت حاد وقوي (مناسب للشخصيات الغامضة أو الأشرار)"},
                {"name": "Aoede", "gender": "female", "description": "صوت أنثوي هادئ ولطيف (مناسب للشخصيات العاطفية)"},
            ]
        super().save(*args, **kwargs)

    def __str__(self):
        status = "نشط" if self.is_active else "غير نشط"
        return f"Gemini Config ({self.llm_model} / {self.tts_model}) - [{status}]"


class ChatThread(models.Model):
    """Persistent conversation session (ChatGPT-style thread)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_threads')
    project = models.ForeignKey(
        'book_drama.BookProject', on_delete=models.SET_NULL, null=True, blank=True, related_name='threads'
    )
    title = models.CharField(max_length=255, default="محادثة جديدة")
    is_deleted = models.BooleanField(default=False)  # soft delete
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'ai_studio_chatthread'
        verbose_name = "خيط محادثة (Chat Thread)"
        verbose_name_plural = "خيوط المحادثات (Chat Threads)"
        ordering = ['-updated_at']

    def save(self, *args, **kwargs):
        if not self._state.adding and not kwargs.get('update_fields'):
            self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.user.username}] {self.title}"


class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('USER', 'المستخدم'),
        ('ASSISTANT', 'الوكيل الذكي'),
        ('SYSTEM', 'النظام'),
    ]

    MSG_TYPE_CHOICES = [
        ('TEXT', 'نص عادي'),
        ('CASTING_CARD', 'كارت اختيار أصوات الشخصيات'),
        ('PROGRESS', 'مؤشر تقدم التوليد'),
        ('STUDIO_LINK', 'رابط فتح استوديو المونتاج'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='chat_messages')
    thread = models.ForeignKey('ChatThread', on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
    project = models.ForeignKey('book_drama.BookProject', on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='ASSISTANT')
    content = models.TextField()
    msg_type = models.CharField(max_length=30, choices=MSG_TYPE_CHOICES, default='TEXT')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_studio_chatmessage'
        verbose_name = "رسالة شات (Chat Message)"
        verbose_name_plural = "سجل الشات (Chat Messages)"
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.get_role_display()}] {self.content[:40]}..."
