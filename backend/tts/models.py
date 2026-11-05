import uuid
from django.db import models
from django.contrib.auth.models import User


class TTSJob(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'قيد المعالجة'),
        ('GENERATING', 'جاري التوليد الصوتي'),
        ('READY', 'جاهز للاستماع'),
        ('FAILED', 'فشل التوليد'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tts_jobs')
    title = models.CharField(max_length=255, default="تسجيل صوتي")
    input_text = models.TextField()
    vocalized_text = models.TextField(blank=True)
    language = models.CharField(max_length=20, default='ar')
    dialect = models.CharField(max_length=50, default='msa')
    voice_profile = models.CharField(max_length=50, default='Charon')
    emotion = models.CharField(max_length=50, default='neutral')
    delivery_style = models.CharField(max_length=50, default='documentary')
    custom_instructions = models.TextField(blank=True)
    audio_url = models.CharField(max_length=500, blank=True)
    duration_seconds = models.FloatField(default=0.0)
    chunks_count = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='READY')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tts_job'
        verbose_name = "تحويل صوتي (TTS Job)"
        verbose_name_plural = "تحويلات الصوت (TTS Jobs)"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.user.username}] {self.title} ({self.voice_profile} - {self.duration_seconds}s)"


class ClonedVoice(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'قيد المعالجة'),
        ('READY', 'جاهز للاستخدام'),
        ('FAILED', 'فشل الاستنساخ'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cloned_voices')
    name = models.CharField(max_length=255)
    gemini_voice_id = models.CharField(max_length=255, blank=True)
    source_audio_url = models.CharField(max_length=500, blank=True)
    consent_audio_url = models.CharField(max_length=500, blank=True)
    sample_audio_url = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='READY')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cloned_voice'
        verbose_name = "صوت مستنسخ (Cloned Voice)"
        verbose_name_plural = "الأصوات المستنسخة (Cloned Voices)"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.user.username}] {self.name} ({self.gemini_voice_id or self.status})"

