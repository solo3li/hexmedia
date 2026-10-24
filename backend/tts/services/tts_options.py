"""TTS Options and Metadata catalog."""

LANGUAGES = [
    {
        "code": "ar",
        "name": "العربية (Arabic)",
        "dialects": [
            {"code": "msa", "name": "فصحى معيارية سينمائية (Modern Standard)", "flag": "🇸🇦"},
            {"code": "egyptian", "name": "لهجة مصرية عفوية (Egyptian)", "flag": "🇪🇬"},
            {"code": "gulf", "name": "لهجة خليجية / سعودية (Gulf)", "flag": "🇦🇪"},
            {"code": "levantine", "name": "لهجة شامية (Levantine)", "flag": "🇱🇧"},
            {"code": "maghrebi", "name": "لهجة مغاربية (Maghrebi)", "flag": "🇲🇦"},
        ]
    },
    {
        "code": "en",
        "name": "English (الإنجليزية)",
        "dialects": [
            {"code": "us", "name": "American English (US)", "flag": "🇺🇸"},
            {"code": "uk", "name": "British English (UK)", "flag": "🇬🇧"},
        ]
    },
    {
        "code": "fr",
        "name": "Français (الفرنسية)",
        "dialects": [
            {"code": "fr_standard", "name": "Français Standard", "flag": "🇫🇷"},
        ]
    },
    {
        "code": "es",
        "name": "Español (الإسبانية)",
        "dialects": [
            {"code": "es_standard", "name": "Español Castellano", "flag": "🇪🇸"},
        ]
    },
]

VOICES = [
    {"name": "Charon", "gender": "male", "pitch": 95, "description": "صوت جهوري عميق وقور ورزين (مثالي للوثائقيات والراوي)"},
    {"name": "Puck", "gender": "male", "pitch": 130, "description": "صوت شبابي حيوي واضح ومشرق (مثالي للإعلانات والشات)"},
    {"name": "Kore", "gender": "female", "pitch": 220, "description": "صوت نسائي دافئ وناعم مهدئ (مناسب للقصص والروايات)"},
    {"name": "Fenrir", "gender": "male", "pitch": 110, "description": "صوت خشن وقوي حازم (للشخصيات الصارمة والمشاهد الملحمية)"},
    {"name": "Aoede", "gender": "female", "pitch": 260, "description": "صوت نسائي تعبيري درامي مفعم بالحياة والتأثير"},
]

EMOTIONS = [
    {"code": "neutral", "name": "طبيعي / متزن (Neutral)", "icon": "🎙️"},
    {"code": "enthusiastic", "name": "حماسي ومحفز (Enthusiastic)", "icon": "🔥"},
    {"code": "dramatic", "name": "درامي وجاد (Dramatic)", "icon": "🎭"},
    {"code": "happy", "name": "فرح ومتفائل (Happy)", "icon": "✨"},
    {"code": "sad", "name": "حزين ومؤثر (Melancholic)", "icon": "🌧️"},
    {"code": "whisper", "name": "هادئ وهمس (Whispering)", "icon": "🤫"},
]

DELIVERY_STYLES = [
    {"code": "documentary", "name": "تعليق وثائقي فخم (Documentary)"},
    {"code": "commercial", "name": "إعلان ترويجي وتسويقي (Commercial)"},
    {"code": "storyteller", "name": "راوي قصص وروايات (Storyteller)"},
    {"code": "news", "name": "نشرة أخبار رسمية (News Broadcast)"},
    {"code": "poetic", "name": "إلقاء أدبي وشعري (Poetic)"},
    {"code": "conversational", "name": "محادثة عفوية (Conversational)"},
]
