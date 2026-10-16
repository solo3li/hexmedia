import uuid
from django.db import models

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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
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
        verbose_name = "فصل رواية (Chapter)"
        verbose_name_plural = "فصول الرواية (Chapters)"
        ordering = ['number']
        unique_together = ('project', 'number')

    def __str__(self):
        return f"{self.project.title} - الفصل {self.number}: {self.title}"


class Scene(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'معلق'),
        ('GENERATING', 'قيد التوليد'),
        ('GENERATED', 'تم التوليد'),
        ('FAILED', 'فشل'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(BookProject, on_delete=models.CASCADE, related_name='scenes')
    order = models.IntegerField(default=0)
    chapter = models.IntegerField(default=1)
    chapter_obj = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, blank=True, related_name='scenes')
    speaker = models.ForeignKey(Character, on_delete=models.SET_NULL, null=True, blank=True, related_name='scenes')
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

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "مشهد / حوار (Scene)"
        verbose_name_plural = "المشاهد والحوارات (Scenes)"
        ordering = ['order']

    def __str__(self):
        return f"مشهد #{self.order}: {self.speaker_name} ({self.duration_seconds}s)"


class TimelineState(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(BookProject, on_delete=models.CASCADE, related_name='timeline')
    designcombo_json = models.JSONField(default=dict, blank=True)
    total_duration = models.FloatField(default=0.0)
    exported_audio_url = models.CharField(max_length=500, blank=True)
    exported_video_url = models.CharField(max_length=500, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "شريط التايم لاين (Timeline State)"
        verbose_name_plural = "أشرطة التايم لاين (Timeline States)"

    def __str__(self):
        return f"تايم لاين: {self.project.title} ({self.total_duration}s)"


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
    project = models.ForeignKey(BookProject, on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='ASSISTANT')
    content = models.TextField()
    msg_type = models.CharField(max_length=30, choices=MSG_TYPE_CHOICES, default='TEXT')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "رسالة شات (Chat Message)"
        verbose_name_plural = "سجل الشات (Chat Messages)"
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.get_role_display()}] {self.content[:40]}..."
