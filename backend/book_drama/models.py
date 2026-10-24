import uuid
from django.db import models
from django.contrib.auth.models import User


class BookProject(models.Model):
    STATUS_CHOICES = [
        ('CHAT', 'محادثة عامة'),
        ('DRAFT', 'مسودة'),
        ('UPLOADED', 'تم الرفع'),
        ('ANALYZING', 'جاري تحليل الرواية واستخراج الشخصيات'),
        ('CASTING_PENDING', 'بانتظار تأكيد أصوات الشخصيات'),
        ('GENERATING_AUDIO', 'جاري توليد الدراما الصوتية'),
        ('CONTINUOUS_GENERATING', 'إنتاج صوتي مستمر (حي)'),
        ('PAUSED', 'متوقف مؤقتاً'),
        ('READY', 'جاهز للمونتاج والتصدير'),
        ('FAILED', 'فشل في المعالجة'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='projects')
    title = models.CharField(max_length=255, default="رواية بدون عنوان")
    author = models.CharField(max_length=255, blank=True, default="مؤلف غير معروف")
    genre = models.CharField(max_length=100, blank=True, default="دراما")
    original_filename = models.CharField(max_length=255, blank=True)
    raw_text = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DRAFT')
    progress_percentage = models.IntegerField(default=0)
    
    # Continuous Long-Form Generation
    target_duration_minutes = models.IntegerField(default=5, help_text="المدة المستهدفة بالدقائق (0 تعني مفتوح)")
    total_duration_seconds = models.FloatField(default=0.0, help_text="إجمالي مدة الصوت المنتج بالثواني")
    current_act = models.IntegerField(default=1, help_text="رقم الفصل الدرامي الحالي")
    story_bible = models.JSONField(default=dict, blank=True, help_text="سجل أحداث القصة وسمات العالم والشخصيات")
    NARRATION_MODE_CHOICES = [
        ('SMART', 'ربط ذكي سينمائي (عند تغير المتحدث)'),
        ('FULL', 'ربط شامل (قبل كل جملة بلا استثناء)'),
        ('NONE', 'حوار مباشر (بدون تقديم الراوي)'),
    ]
    narration_mode = models.CharField(max_length=20, choices=NARRATION_MODE_CHOICES, default='SMART', help_text="نمط تقديم الراوي للشخصيات")

    # Video & Visual Attributes
    PROJECT_TYPE_CHOICES = [
        ('AUDIO_DRAMA', 'دراما صوتية'),
        ('VIDEO_STUDIO', 'استوديو فيديو وسينما'),
    ]
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPE_CHOICES, default='AUDIO_DRAMA')
    VISUAL_STYLE_CHOICES = [
        ('AUTO', 'تلقائي ذكي'),
        ('DOCUMENTARY', 'فيلم وثائقي / أرشيفي واقعي'),
        ('CARTOON', 'كرتون / أنيميشن بيكسار ملون'),
        ('CINEMATIC', 'سينمائي 35mm واقعي'),
        ('MANGA', 'مانجا / كوميك درامي'),
    ]
    visual_style = models.CharField(max_length=30, choices=VISUAL_STYLE_CHOICES, default='AUTO')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_studio_bookproject'
        verbose_name = "مشروع رواية (Book Project)"
        verbose_name_plural = "مشاريع الروايات (Book Projects)"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"


class Character(models.Model):
    ROLE_CHOICES = [
        ('NARRATOR', 'الراوي (Narrator)'),
        ('PROTAGONIST', 'البطل الرئيسي'),
        ('ANTAGONIST', 'الخصم / الشرير'),
        ('SUPPORTING', 'شخصية مساعدة'),
    ]

    GENDER_CHOICES = [
        ('MALE', 'ذكر'),
        ('FEMALE', 'أنثى'),
        ('UNKNOWN', 'غير محدد'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(BookProject, on_delete=models.CASCADE, related_name='characters')
    name = models.CharField(max_length=100)
    role_type = models.CharField(max_length=20, choices=ROLE_CHOICES, default='SUPPORTING')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='MALE')
    description = models.TextField(blank=True)
    assigned_voice = models.CharField(max_length=50, default="Puck")
    speaking_style = models.CharField(max_length=100, blank=True, default="طبيعي وسينمائي")
    sample_audio_url = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = 'ai_studio_character'
        verbose_name = "شخصية (Character)"
        verbose_name_plural = "شخصيات الرواية (Characters)"

    def __str__(self):
        return f"{self.name} ({self.get_role_type_display()}) - صوت: {self.assigned_voice}"


class Chapter(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'بانتظار التنفيذ'),
        ('GENERATING', 'قيد التوليد'),
        ('READY', 'تم التوليد'),
        ('FAILED', 'فشل'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(BookProject, on_delete=models.CASCADE, related_name='chapters')
    number = models.IntegerField(default=1)
    title = models.CharField(max_length=255, default="الفصل الأول")
    summary = models.TextField(blank=True)
    raw_text = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    scenes_count = models.IntegerField(default=0)
    total_duration_seconds = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_studio_chapter'
        verbose_name = "فصل رواية (Chapter)"
        verbose_name_plural = "فصول الرواية (Chapters)"
        ordering = ['number']
        unique_together = ('project', 'number')

    def __str__(self):
        return f"{self.project.title} - الفصل {self.number}: {self.title}"
