"""TTS Options and Metadata catalog for HexMedia Studio.

Contains official Gemini TTS voice profiles (30 prebuilt voices),
comprehensive multi-lingual support with regional dialects,
an expanded cinematic/psychological emotion spectrum,
and professional broadcast/narrative delivery styles.
All labels use clean, professional typography without emojis.
"""

LANGUAGES = [
    {
        "code": "ar",
        "name": "العربية (Arabic)",
        "dialects": [
            {"code": "msa", "name": "فصحى معيارية سينمائية (Modern Standard Arabic)"},
            {"code": "egyptian", "name": "لهجة مصرية عفوية (Egyptian Arabic)"},
            {"code": "saudi", "name": "لهجة سعودية نجدية وحجازية (Saudi Arabic)"},
            {"code": "gulf", "name": "لهجة خليجية وإماراتية (Gulf / UAE Arabic)"},
            {"code": "kuwaiti", "name": "لهجة كويتية (Kuwaiti Arabic)"},
            {"code": "syrian", "name": "لهجة شامية سورية (Syrian Levantine)"},
            {"code": "lebanese", "name": "لهجة شامية لبنانية (Lebanese Levantine)"},
            {"code": "levantine_south", "name": "لهجة فلسطينية وأردنية (Palestinian / Jordanian)"},
            {"code": "iraqi", "name": "لهجة عراقية (Iraqi Arabic)"},
            {"code": "moroccan", "name": "دارجة مغربية (Moroccan Darija)"},
            {"code": "algerian", "name": "دارجة جزائرية (Algerian Arabic)"},
            {"code": "tunisian", "name": "لهجة تونسية (Tunisian Arabic)"},
            {"code": "sudanese", "name": "لهجة سودانية (Sudanese Arabic)"},
            {"code": "yemeni", "name": "لهجة يمنية (Yemeni Arabic)"},
            {"code": "omani", "name": "لهجة عمانية (Omani Arabic)"},
            {"code": "libyan", "name": "لهجة ليبية (Libyan Arabic)"},
        ]
    },
    {
        "code": "en",
        "name": "English (الإنجليزية)",
        "dialects": [
            {"code": "us", "name": "American English (US)"},
            {"code": "uk", "name": "British English (UK - Received Pronunciation)"},
            {"code": "au", "name": "Australian English (AU)"},
            {"code": "ca", "name": "Canadian English (CA)"},
            {"code": "in", "name": "Indian English (IN)"},
            {"code": "ie", "name": "Irish English (IE)"},
            {"code": "sct", "name": "Scottish English (SCT)"},
            {"code": "za", "name": "South African English (ZA)"},
            {"code": "nz", "name": "New Zealand English (NZ)"},
        ]
    },
    {
        "code": "fr",
        "name": "Français (الفرنسية)",
        "dialects": [
            {"code": "fr_standard", "name": "Français Métropolitain (Standard)"},
            {"code": "fr_ca", "name": "Français Canadien (Québécois)"},
            {"code": "fr_be", "name": "Français de Belgique"},
            {"code": "fr_ch", "name": "Français de Suisse"},
            {"code": "fr_af", "name": "Français d'Afrique"},
        ]
    },
    {
        "code": "es",
        "name": "Español (الإسبانية)",
        "dialects": [
            {"code": "es_standard", "name": "Español de España (Castellano)"},
            {"code": "es_mx", "name": "Español Mexicano"},
            {"code": "es_ar", "name": "Español Rioplatense (Argentina & Uruguay)"},
            {"code": "es_co", "name": "Español Colombiano"},
            {"code": "es_cl", "name": "Español Chileno"},
            {"code": "es_latam", "name": "Español Latinoamericano Neutro"},
            {"code": "es_us", "name": "Español de Estados Unidos"},
        ]
    },
    {
        "code": "de",
        "name": "Deutsch (الألمانية)",
        "dialects": [
            {"code": "de_standard", "name": "Standarddeutsch (Hochdeutsch)"},
            {"code": "de_at", "name": "Österreichisches Deutsch"},
            {"code": "de_ch", "name": "Schweizer Hochdeutsch"},
        ]
    },
    {
        "code": "it",
        "name": "Italiano (الإيطالية)",
        "dialects": [
            {"code": "it_standard", "name": "Italiano Standard"},
        ]
    },
    {
        "code": "pt",
        "name": "Português (البرتغالية)",
        "dialects": [
            {"code": "pt_br", "name": "Português do Brasil"},
            {"code": "pt_pt", "name": "Português Europeu (Portugal)"},
        ]
    },
    {
        "code": "ru",
        "name": "Русский (الروسية)",
        "dialects": [
            {"code": "ru_standard", "name": "Русский литературный"},
        ]
    },
    {
        "code": "tr",
        "name": "Türkçe (التركية)",
        "dialects": [
            {"code": "tr_standard", "name": "Standart Türkçe (İstanbul)"},
        ]
    },
    {
        "code": "fa",
        "name": "فارسی (الفارسية)",
        "dialects": [
            {"code": "fa_ir", "name": "فارسی ایرانی (تهرانی)"},
            {"code": "fa_af", "name": "فارسی دری / أفغاني"},
        ]
    },
    {
        "code": "ur",
        "name": "اردو (الأردية)",
        "dialects": [
            {"code": "ur_pk", "name": "اردو معیاری (پاکستان)"},
            {"code": "ur_in", "name": "اردو ہندوستانی (بھارت)"},
        ]
    },
    {
        "code": "hi",
        "name": "हिन्दी (الهندية)",
        "dialects": [
            {"code": "hi_standard", "name": "मानक हिन्दी (Standard Hindi)"},
        ]
    },
    {
        "code": "ja",
        "name": "日本語 (اليابانية)",
        "dialects": [
            {"code": "ja_standard", "name": "標準日本語 (Tokyo Standard)"},
            {"code": "ja_kansai", "name": "関西弁 (Kansai Dialect)"},
        ]
    },
    {
        "code": "ko",
        "name": "한국어 (الكورية)",
        "dialects": [
            {"code": "ko_standard", "name": "표준 한국어 (Seoul Standard)"},
        ]
    },
    {
        "code": "zh",
        "name": "中文 (الصينية)",
        "dialects": [
            {"code": "zh_cmn", "name": "中文 普通话 (Mandarin Simplified)"},
            {"code": "zh_tw", "name": "國語 繁體 (Mandarin Traditional)"},
            {"code": "zh_yue", "name": "粵語 (Cantonese / 广州话)"},
        ]
    },
    {
        "code": "id",
        "name": "Bahasa Indonesia / Melayu (الإندونيسية والملايو)",
        "dialects": [
            {"code": "id_standard", "name": "Bahasa Indonesia Baku"},
            {"code": "ms_standard", "name": "Bahasa Melayu Standard"},
        ]
    },
    {
        "code": "nl",
        "name": "Nederlands (الهولندية)",
        "dialects": [
            {"code": "nl_standard", "name": "Nederlands Standaard"},
            {"code": "nl_be", "name": "Vlaams (Belgisch)"},
        ]
    },
    {
        "code": "sv",
        "name": "Svenska (السويدية)",
        "dialects": [
            {"code": "sv_standard", "name": "Rikssvenska (Standard Swedish)"},
        ]
    },
    {
        "code": "pl",
        "name": "Polski (البولندية)",
        "dialects": [
            {"code": "pl_standard", "name": "Język polski standardowy"},
        ]
    },
    {
        "code": "el",
        "name": "Ελληνικά (اليونانية)",
        "dialects": [
            {"code": "el_standard", "name": "Νέα Ελληνικά (Modern Greek)"},
        ]
    },
    {
        "code": "he",
        "name": "עברית (العبرية)",
        "dialects": [
            {"code": "he_standard", "name": "עברית מודרנית (Modern Hebrew)"},
        ]
    },
    {
        "code": "vi",
        "name": "Tiếng Việt (الفيتنامية)",
        "dialects": [
            {"code": "vi_standard", "name": "Tiếng Việt chuẩn (Giọng Bắc / Nam)"},
        ]
    },
    {
        "code": "th",
        "name": "ไทย (التايلاندية)",
        "dialects": [
            {"code": "th_standard", "name": "ภาษาไทยมาตรฐาน (Standard Thai)"},
        ]
    },
    {
        "code": "sw",
        "name": "Kiswahili (السواحلية)",
        "dialects": [
            {"code": "sw_standard", "name": "Kiswahili Sanifu"},
        ]
    },
    {
        "code": "ku",
        "name": "کوردی (الكردية)",
        "dialects": [
            {"code": "ku_sorani", "name": "کوردی سۆرانی (Central Kurdish)"},
            {"code": "ku_kurmanji", "name": "Kurmancî (Northern Kurdish)"},
        ]
    },
]

# Full 30 official Gemini TTS Studio prebuilt voices with timbre, gender and character persona
VOICES = [
    {
        "name": "Zephyr",
        "gender": "female",
        "tag": "مشرق ومنعش",
        "pitch": 240,
        "description": "صوت شبابي مشرق وخفيف، نبرة متفائلة وإيقاع رشيق يناسب الإعلانات الحديثة والمحتوى التفاعلي"
    },
    {
        "name": "Puck",
        "gender": "male",
        "tag": "حيوي ومتفائل",
        "pitch": 130,
        "description": "صوت شبابي حيوي واضح ومشرق، طاقة متدفقة مثالية للإعلانات والبودكاست والمحادثات الذكية"
    },
    {
        "name": "Charon",
        "gender": "male",
        "tag": "جهوري وقور",
        "pitch": 95,
        "description": "صوت جهوري عميق ورزين، حضور مسرحي مهيب مثالي للوثائقيات والراوي الفخم والسرد التاريخي"
    },
    {
        "name": "Kore",
        "gender": "female",
        "tag": "دافئ وحازم",
        "pitch": 220,
        "description": "صوت نسائي دافئ وناعم مهدئ ومتزن، نبرة مريحة تناسب الروايات الأدبية والقصص الهادفة"
    },
    {
        "name": "Fenrir",
        "gender": "male",
        "tag": "ملحمي وقوي",
        "pitch": 110,
        "description": "صوت خشن وقوي حازم، طاقة ملحمية سينمائية تلائم المشاهد القتالية والتريلرات والشخصيات الصارمة"
    },
    {
        "name": "Leda",
        "gender": "female",
        "tag": "شبابي نضر",
        "pitch": 250,
        "description": "صوت نسائي نضر وناعم، يتميز بالعفوية والوضوح للشروحات التفاعلية والتطبيقات التعليمية"
    },
    {
        "name": "Orus",
        "gender": "male",
        "tag": "قيادي حاسم",
        "pitch": 105,
        "description": "صوت رجالي قوي ورسمي، نبرة موثوقة ومقنعة للخطابات المؤسسية والتقارير الإدارية والتاريخية"
    },
    {
        "name": "Aoede",
        "gender": "female",
        "tag": "تعبيري درامي",
        "pitch": 260,
        "description": "صوت نسائي سينمائي مفعم بالعاطفة والتأثير المسرحي، ممتاز للمشاهد الشعرية والدرامية العميقة"
    },
    {
        "name": "Callirrhoe",
        "gender": "female",
        "tag": "سلس ومريح",
        "pitch": 215,
        "description": "صوت نسائي انسيابي ومقنع، نبرة متزنة ومريحة للأذن للكتب الصوتية والمقالات العلمية"
    },
    {
        "name": "Autonoe",
        "gender": "female",
        "tag": "ناصع ومتألق",
        "pitch": 245,
        "description": "صوت نسائي واضح ولامع، نبرة متفائلة وواثقة مثالية لحملات التوعية والإعلانات الحيوية"
    },
    {
        "name": "Enceladus",
        "gender": "male",
        "tag": "هامس وشاعري",
        "pitch": 120,
        "description": "صوت رجالي ناعم وحميمي بنبرة تنفسية هادئة، مناسب للتأمل والنصوص الوجدانية والشعر"
    },
    {
        "name": "Iapetus",
        "gender": "male",
        "tag": "صافٍ ودقيق",
        "pitch": 115,
        "description": "صوت نقي ومخارج حروف واضحة جداً، راوي مثقف ورصين للأعمال الأكاديمية والوثائقية"
    },
    {
        "name": "Umbriel",
        "gender": "male",
        "tag": "عفوي ومسترخٍ",
        "pitch": 125,
        "description": "نبرة عفوية طبيعية غير متكلفة، تناسب الحوارات اليومية والبودكاست والمحادثات الحرة"
    },
    {
        "name": "Algieba",
        "gender": "female",
        "tag": "مخملي راقٍ",
        "pitch": 230,
        "description": "صوت مخملي دافئ وأنيق، يضفي لمسة من الفخامة والسكينة على الروايات والبرامج الثقافية"
    },
    {
        "name": "Despina",
        "gender": "female",
        "tag": "رقيق وسردي",
        "pitch": 225,
        "description": "صوت سردي ناعم ومتدفق بلطف، ملائم جداً لقصص الأطفال والروايات الرومانسية"
    },
    {
        "name": "Erinome",
        "gender": "female",
        "tag": "بلوري تعليمي",
        "pitch": 235,
        "description": "نبرة بلورية صافية ودقيقة، ممتازة للدورات التدريبية والشروحات التقنية والمقاطع التثقيفية"
    },
    {
        "name": "Algenib",
        "gender": "male",
        "tag": "خشن أجش",
        "pitch": 90,
        "description": "صوت أجش مفعم بالخشونة والرجولة، شخصية سينمائية مميزة للمشاهد الغامضة وأفلام الإثارة"
    },
    {
        "name": "Rasalgethi",
        "gender": "male",
        "tag": "إخباري موثوق",
        "pitch": 118,
        "description": "نبرة إخبارية رصينة وتقريرية، مثالية لنشرات الأخبار والبيانات الرسمية والتقارير الصحفية"
    },
    {
        "name": "Laomedeia",
        "gender": "female",
        "tag": "مبتهج ونشط",
        "pitch": 255,
        "description": "صوت نشط ومبهج يشع بالحيوية، مثالي للألعاب والمحتوى الترفيهي والرسائل الحماسية"
    },
    {
        "name": "Achernar",
        "gender": "female",
        "tag": "ناعم وهادئ",
        "pitch": 210,
        "description": "صوت رقيق وهادئ يدعو للاسترخاء، نبرة متوازنة ومريحة للمحتوى التأملي والإرشادي"
    },
    {
        "name": "Alnilam",
        "gender": "male",
        "tag": "قوي وحازم",
        "pitch": 100,
        "description": "صوت قوي ذو نبرة عسكرية وتوجيهية صارمة، مناسب للإعلانات المؤثرة والتحذيرات والمشاهد الحاسمة"
    },
    {
        "name": "Schedar",
        "gender": "male",
        "tag": "متزن ومحايد",
        "pitch": 128,
        "description": "نبرة متزنة ومحايدة تخلو من الانفعال الزائد، ملائمة للتقارير الإحصائية والمحتوى العلمي"
    },
    {
        "name": "Gacrux",
        "gender": "male",
        "tag": "ناضج وحكيم",
        "pitch": 88,
        "description": "صوت رجالي مسن وحكيم، وقار عالي وتجربة عميقة تناسب الشخصيات التراثية والحكماء"
    },
    {
        "name": "Pulcherrima",
        "gender": "female",
        "tag": "جريء ومندفع",
        "pitch": 248,
        "description": "نبرة جريئة ومندفعة مفعمة بالحماس، صوت إعلاني قوي يبرز العروض التسويقية والمهرجانات"
    },
    {
        "name": "Achird",
        "gender": "male",
        "tag": "ودود وقريب",
        "pitch": 135,
        "description": "نبرة صديق ناصح وودود، تشعر المستمع بالألفة والاهتمام، ممتازة لخدمة العملاء والإرشاد"
    },
    {
        "name": "Zubenelgenubi",
        "gender": "male",
        "tag": "عفوي وبسيط",
        "pitch": 122,
        "description": "صوت مألوف وبسيط دون تكلف، مثالي للمواقف اليومية والروايات الاجتماعية المعاصرة"
    },
    {
        "name": "Vindemiatrix",
        "gender": "female",
        "tag": "لطيف وحنون",
        "pitch": 218,
        "description": "نبرة أمومية حنونة وإنسانية مؤثرة، تلامس المشاعر في الحملات الخيرية والتوعية الإنسانية"
    },
    {
        "name": "Sadachbia",
        "gender": "female",
        "tag": "مفعم بالحياة",
        "pitch": 242,
        "description": "صوت متدفق وحيوي يشد الانتباه، سرد سلس يبقي المستمع متفاعلاً طوال النص"
    },
    {
        "name": "Sadaltager",
        "gender": "male",
        "tag": "خبير ومعرفي",
        "pitch": 112,
        "description": "صوت أكاديمي عميق ونبرة أستاذ خبير، مثالي للمحاضرات والبودكاست الفكري والمقالات التخصصية"
    },
    {
        "name": "Sulafat",
        "gender": "female",
        "tag": "دافئ ومحتضن",
        "pitch": 222,
        "description": "صوت دافئ ومحتضن يفيض بالمشاعر النبيلة، نبرة ملهمة تناسب السير الذاتية والمقالات الأدبية"
    },
]

# Expanded psychological and cinematic emotion spectrum (No vulgar emojis)
EMOTIONS = [
    {"code": "neutral", "name": "طبيعي ورصين (Neutral & Balanced)"},
    {"code": "calm", "name": "هادئ ومريح (Calm & Serene)"},
    {"code": "warm", "name": "دافئ وحميمي (Warm & Intimate)"},
    {"code": "enthusiastic", "name": "حماسي ومحفز ملهم (Enthusiastic & Inspiring)"},
    {"code": "cheerful", "name": "مبتهج وسعيد (Cheerful & Joyful)"},
    {"code": "dramatic", "name": "درامي وتراجيدي جاد (Dramatic & Serious)"},
    {"code": "epic", "name": "ملحمي ومهيب (Epic & Majestic)"},
    {"code": "mysterious", "name": "غامض ومثير للفضول (Mysterious & Suspenseful)"},
    {"code": "melancholic", "name": "حزين ومؤثر شجي (Melancholic & Reflective)"},
    {"code": "somber", "name": "وقور وحزين (Somber & Solemn)"},
    {"code": "whispering", "name": "هامس وسري (Whispering & Secretive)"},
    {"code": "urgent", "name": "متوتر وملح (Urgent & Tense)"},
    {"code": "fearful", "name": "خائف ومرتعد (Fearful & Anxious)"},
    {"code": "angry", "name": "غاضب وصارم (Angry & Stern)"},
    {"code": "confident", "name": "واثق وحاسم (Confident & Authoritative)"},
    {"code": "affectionate", "name": "عطوف وحنون (Affectionate & Tender)"},
    {"code": "sarcastic", "name": "ساخر ومتهكم (Sarcastic & Ironic)"},
    {"code": "poetic_emotional", "name": "شاعري ووجداني (Poetic & Soulful)"},
]

# Professional broadcast, narrative, and cinematic delivery styles (No vulgar emojis)
DELIVERY_STYLES = [
    {"code": "documentary", "name": "تعليق وثائقي فخم واستقصائي (Documentary)"},
    {"code": "commercial", "name": "إعلان تجاري وترويجي تسويقي (Commercial & Promo)"},
    {"code": "storyteller", "name": "راوي قصص وروايات سردية (Cinematic Storyteller)"},
    {"code": "audiobook", "name": "قراءة كتاب صوتي هادئ ومتصل (Audiobook Narration)"},
    {"code": "news", "name": "نشرة أخبار رسمية وإيجاز صحفي (News Broadcast)"},
    {"code": "poetic", "name": "إلقاء أدبي ونصوص شعرية (Poetic Recitation)"},
    {"code": "conversational", "name": "حوار عفوي ومحادثة واقعية (Natural Conversation)"},
    {"code": "podcast", "name": "بودكاست إذاعي تفاعلي (Interactive Podcast)"},
    {"code": "educational", "name": "شرح تعليمي وأكاديمي مبسط (Educational & Explainer)"},
    {"code": "corporate", "name": "عرض تقديمي ومؤسسي احترافي (Corporate Presentation)"},
    {"code": "meditation", "name": "تأمل وتنويم واسترخاء ذهني (Guided Meditation)"},
    {"code": "trailer", "name": "إعلان تشويقي وتريلر سينمائي (Movie Trailer)"},
    {"code": "motivational", "name": "خطابي تحفيزي وإلهامي (Motivational Speech)"},
    {"code": "dramatic_dialogue", "name": "تمثيل مسرحي وحواري درامي (Dramatic Roleplay)"},
    {"code": "investigative", "name": "استقصائي غموض وتحقيق (Investigative Crime)"},
    {"code": "sports", "name": "تعليق رياضي تفاعلي وحماسي (Sports Commentary)"},
]
