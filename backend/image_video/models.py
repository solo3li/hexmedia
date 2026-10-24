import uuid
from django.db import models


class Scene(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'معلق'),
        ('GENERATING', 'قيد التوليد'),
        ('GENERATED', 'تم التوليد'),
        ('FAILED', 'فشل'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey('book_drama.BookProject', on_delete=models.CASCADE, related_name='scenes')
    order = models.IntegerField(default=0)
    chapter = models.IntegerField(default=1)
    chapter_obj = models.ForeignKey('book_drama.Chapter', on_delete=models.SET_NULL, null=True, blank=True, related_name='scenes')
    speaker = models.ForeignKey('book_drama.Character', on_delete=models.SET_NULL, null=True, blank=True, related_name='scenes')
    speaker_name = models.CharField(max_length=100, default="الراوي")
    raw_text = models.TextField()
    vocalized_text = models.TextField(blank=True, help_text="النص بعد التشكيل العربي لضمان سلامة النطق")
    emotion = models.CharField(max_length=100, blank=True, default="calm and narrative")
    
    # Audio outputs
    audio_url = models.CharField(max_length=500, blank=True)
    duration_seconds = models.FloatField(default=0.0)
    start_time_seconds = models.FloatField(default=0.0)

    # Sound design & Ambient
    sfx_name = models.CharField(max_length=100, blank=True)
    sfx_url = models.CharField(max_length=500, blank=True)
    bgm_name = models.CharField(max_length=100, blank=True)
    bgm_url = models.CharField(max_length=500, blank=True)

    # Visual & Video assets
    image_url = models.CharField(max_length=500, blank=True)
    visual_prompt = models.TextField(blank=True, help_text="الوصف البصري الإنجليزي لتوليد الكادر")
    MEDIA_TYPE_CHOICES = [
        ('AI_IMAGE', 'توليد ذكاء اصطناعي (Imagen 3)'),
        ('ARCHIVE_WEB', 'أرشيف وصور ويب واقعية'),
    ]
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES, default='AI_IMAGE')
    MOTION_TYPE_CHOICES = [
        ('zoom_in', 'زووم للداخل (Ken Burns)'),
        ('zoom_out', 'زووم للخارج'),
        ('pan_left', 'بانوراما لليسار'),
        ('pan_right', 'بانوراما لليمين'),
        ('static', 'ثابت'),
    ]
    motion_type = models.CharField(max_length=30, choices=MOTION_TYPE_CHOICES, default='zoom_in')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_studio_scene'
        verbose_name = "مشهد / حوار (Scene)"
        verbose_name_plural = "المشاهد والحوارات (Scenes)"
        ordering = ['order']

    def __str__(self):
        return f"مشهد #{self.order}: {self.speaker_name} ({self.duration_seconds}s)"


class TimelineState(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField('book_drama.BookProject', on_delete=models.CASCADE, related_name='timeline')
    designcombo_json = models.JSONField(default=dict, blank=True)
    total_duration = models.FloatField(default=0.0)
    exported_audio_url = models.CharField(max_length=500, blank=True)
    exported_video_url = models.CharField(max_length=500, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_studio_timelinestate'
        verbose_name = "شريط التايم لاين (Timeline State)"
        verbose_name_plural = "أشرطة التايم لاين (Timeline States)"

    def __str__(self):
        return f"تايم لاين: {self.project.title} ({self.total_duration}s)"
