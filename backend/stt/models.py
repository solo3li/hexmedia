import uuid
from django.db import models
from django.contrib.auth.models import User


class STTJob(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'قيد المعالجة'),
        ('TRANSCRIBING', 'جاري التفريغ والتحليل'),
        ('READY', 'مكتمل وجاهز'),
        ('FAILED', 'فشل التفريغ'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stt_jobs')
    title = models.CharField(max_length=255, default="تفريغ صوتي")
    audio_url = models.CharField(max_length=500, blank=True)
    language = models.CharField(max_length=30, default='auto')
    target_language = models.CharField(max_length=30, blank=True, default='')
    transcript_text = models.TextField(blank=True)
    srt_content = models.TextField(blank=True)
    diarization_data = models.JSONField(default=list, blank=True)
    has_diarization = models.BooleanField(default=False)
    has_timestamps = models.BooleanField(default=False)
    duration_seconds = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='READY')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stt_job'
        verbose_name = "تفريغ صوتي (STT Job)"
        verbose_name_plural = "تفريغات الصوت (STT Jobs)"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.user.username}] {self.title} ({self.duration_seconds}s)"
