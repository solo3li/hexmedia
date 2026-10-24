"""TTS Options and Metadata catalog for HexMedia Studio.

Contains official Gemini TTS voice profiles (30 prebuilt studio voices),
comprehensive multi-lingual support covering over 130+ languages supported by Gemini 3.8 Flash TTS,
full regional Arabic and international dialects,
an expanded cinematic/psychological emotion spectrum (32 distinct states),
and professional broadcast/narrative delivery styles (25 distinct styles).
All labels use clean, professional typography without vulgar emojis.
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
            {"code": "qatari_bahraini", "name": "لهجة قطرية وبحرينية (Qatari & Bahraini Arabic)"},
            {"code": "syrian", "name": "لهجة شامية سورية (Syrian Levantine)"},
            {"code": "lebanese", "name": "لهجة شامية لبنانية (Lebanese Levantine)"},
            {"code": "palestinian", "name": "لهجة فلسطينية (Palestinian Arabic)"},
            {"code": "jordanian", "name": "لهجة أردنية (Jordanian Arabic)"},
            {"code": "iraqi", "name": "لهجة عراقية بغدادية وجنوبية (Iraqi Arabic)"},
            {"code": "moroccan", "name": "دارجة مغربية (Moroccan Darija)"},
            {"code": "algerian", "name": "دارجة جزائرية (Algerian Arabic)"},
            {"code": "tunisian", "name": "لهجة تونسية (Tunisian Arabic)"},
            {"code": "libyan", "name": "لهجة ليبية (Libyan Arabic)"},
            {"code": "sudanese", "name": "لهجة سودانية (Sudanese Arabic)"},
            {"code": "yemeni", "name": "لهجة يمنية (Yemeni Arabic)"},
            {"code": "omani", "name": "لهجة عمانية (Omani Arabic)"},
            {"code": "mauritanian", "name": "لهجة حسانية موريتانية (Mauritanian Arabic)"},
        ]
    },
    {
        "code": "en",
        "name": "English (الإنجليزية)",
        "dialects": [
            {"code": "us", "name": "American English (US General)"},
            {"code": "uk", "name": "British English (UK - Received Pronunciation)"},
            {"code": "uk_north", "name": "British English (Northern / Cockney)"},
            {"code": "au", "name": "Australian English (AU)"},
            {"code": "ca", "name": "Canadian English (CA)"},
            {"code": "in", "name": "Indian English (IN)"},
            {"code": "ie", "name": "Irish English (IE)"},
            {"code": "sct", "name": "Scottish English (SCT)"},
            {"code": "za", "name": "South African English (ZA)"},
            {"code": "nz", "name": "New Zealand English (NZ)"},
            {"code": "sg", "name": "Singaporean English (SG)"},
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
            {"code": "fr_af", "name": "Français d'Afrique (Sénégal, Côte d'Ivoire)"},
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
            {"code": "pt_ao", "name": "Português de Angola"},
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
            {"code": "fa_af", "name": "فارسی دری (أفغانستان)"},
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
        "name": "Bahasa Indonesia (الإندونيسية)",
        "dialects": [
            {"code": "id_standard", "name": "Bahasa Indonesia Baku"},
        ]
    },
    {
        "code": "ms",
        "name": "Bahasa Melayu (الملايو)",
        "dialects": [
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
            {"code": "he_standard", "name": "עברית מودرنية (Modern Hebrew)"},
        ]
    },
    {
        "code": "vi",
        "name": "Tiếng Việt (الفيتنامية)",
        "dialects": [
            {"code": "vi_standard", "name": "Tiếng Việt chuẩn (Hà Nội)"},
            {"code": "vi_south", "name": "Tiếng Việt miền Nam (Sài Gòn)"},
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
    # Additional official languages supported by Gemini 3.8 Flash TTS
    {"code": "ace", "name": "Acehnese (الأتشيهية)", "dialects": [{"code": "ace_standard", "name": "Acehnese Standard"}]},
    {"code": "af", "name": "Afrikaans (الأفريكانية)", "dialects": [{"code": "af_standard", "name": "Afrikaans Standaard"}]},
    {"code": "ak", "name": "Akan (الأكانية)", "dialects": [{"code": "ak_standard", "name": "Akan Standard"}]},
    {"code": "am", "name": "Amharic (الأمهرية)", "dialects": [{"code": "am_standard", "name": "አማርኛ (Standard Amharic)"}]},
    {"code": "hy", "name": "Armenian (الأرمنية)", "dialects": [{"code": "hy_standard", "name": "Հայերեն (Standard Armenian)"}]},
    {"code": "as", "name": "Assamese (الأسامية)", "dialects": [{"code": "as_standard", "name": "অসমীয়া (Standard Assamese)"}]},
    {"code": "awa", "name": "Awadhi (الأودهية)", "dialects": [{"code": "awa_standard", "name": "अवधी (Standard Awadhi)"}]},
    {"code": "ban", "name": "Balinese (البالية)", "dialects": [{"code": "ban_standard", "name": "Balinese Standard"}]},
    {"code": "bn", "name": "Bangla / Bengali (البنغالية)", "dialects": [{"code": "bn_bd", "name": "বাংলা (Bangladesh)"}, {"code": "bn_in", "name": "বাংলা (India)"}]},
    {"code": "bjn", "name": "Banjar (البنجارية)", "dialects": [{"code": "bjn_standard", "name": "Bahasa Banjar"}]},
    {"code": "ba", "name": "Bashkir (الباشكيرية)", "dialects": [{"code": "ba_standard", "name": "Башҡортса"}]},
    {"code": "eu", "name": "Basque (الباسكية)", "dialects": [{"code": "eu_standard", "name": "Euskara Batua"}]},
    {"code": "be", "name": "Belarusian (البيلاروسية)", "dialects": [{"code": "be_standard", "name": "Беларуская"}]},
    {"code": "bem", "name": "Bemba (البيمبا)", "dialects": [{"code": "bem_standard", "name": "Ichibemba"}]},
    {"code": "bho", "name": "Bhojpuri (البوجبورية)", "dialects": [{"code": "bho_standard", "name": "भोजपुरी"}]},
    {"code": "bs", "name": "Bosnian (البوسنية)", "dialects": [{"code": "bs_standard", "name": "Bosanski jezik"}]},
    {"code": "bug", "name": "Buginese (البوجية)", "dialects": [{"code": "bug_standard", "name": "Basa Ugi"}]},
    {"code": "bg", "name": "Bulgarian (البلغارية)", "dialects": [{"code": "bg_standard", "name": "Български"}]},
    {"code": "my", "name": "Burmese (البورمية)", "dialects": [{"code": "my_standard", "name": "မြန်မာစာ"}]},
    {"code": "ca", "name": "Catalan (الكتالونية)", "dialects": [{"code": "ca_standard", "name": "Català Estàndard"}]},
    {"code": "ceb", "name": "Cebuano (السيبوانية)", "dialects": [{"code": "ceb_standard", "name": "Sinugboanon"}]},
    {"code": "hne", "name": "Chhattisgarhi (التشهاتيسغارية)", "dialects": [{"code": "hne_standard", "name": "छत्तीसगढ़ी"}]},
    {"code": "crh", "name": "Crimean Tatar (تتار القرم)", "dialects": [{"code": "crh_standard", "name": "Qırımtatar tili"}]},
    {"code": "hr", "name": "Croatian (الكرواتية)", "dialects": [{"code": "hr_standard", "name": "Hrvatski standardni"}]},
    {"code": "cs", "name": "Czech (التشيكية)", "dialects": [{"code": "cs_standard", "name": "Čeština"}]},
    {"code": "da", "name": "Danish (الدنماركية)", "dialects": [{"code": "da_standard", "name": "Dansk standard"}]},
    {"code": "dyu", "name": "Dyula (الديولية)", "dialects": [{"code": "dyu_standard", "name": "Julakan"}]},
    {"code": "dz", "name": "Dzongkha (الدزونغخية)", "dialects": [{"code": "dz_standard", "name": "རྫོང་ཁ"}]},
    {"code": "et", "name": "Estonian (الإستونية)", "dialects": [{"code": "et_standard", "name": "Eesti keel"}]},
    {"code": "fil", "name": "Filipino / Tagalog (الفلبينية)", "dialects": [{"code": "fil_standard", "name": "Wikang Filipino"}]},
    {"code": "fi", "name": "Finnish (الفنلندية)", "dialects": [{"code": "fi_standard", "name": "Suomi"}]},
    {"code": "gl", "name": "Galician (الجليقية)", "dialects": [{"code": "gl_standard", "name": "Galego"}]},
    {"code": "lg", "name": "Ganda / Luganda (اللوغاندية)", "dialects": [{"code": "lg_standard", "name": "Oluganda"}]},
    {"code": "ka", "name": "Georgian (الجورجية)", "dialects": [{"code": "ka_standard", "name": "ქართული"}]},
    {"code": "gn", "name": "Guarani (الغوارانية)", "dialects": [{"code": "gn_standard", "name": "Avañe'ẽ"}]},
    {"code": "gu", "name": "Gujarati (الغوجاراتية)", "dialects": [{"code": "gu_standard", "name": "ગુજરાતી"}]},
    {"code": "ht", "name": "Haitian Creole (الكريولية الهايتية)", "dialects": [{"code": "ht_standard", "name": "Kreyòl Ayisyen"}]},
    {"code": "mn", "name": "Halh Mongolian (المنغولية)", "dialects": [{"code": "mn_standard", "name": "Монгол хэл"}]},
    {"code": "ha", "name": "Hausa (الهوساوية)", "dialects": [{"code": "ha_standard", "name": "Harshen Hausa"}]},
    {"code": "hu", "name": "Hungarian (المجرية)", "dialects": [{"code": "hu_standard", "name": "Magyar"}]},
    {"code": "is", "name": "Icelandic (الآيسلندية)", "dialects": [{"code": "is_standard", "name": "Íslenska"}]},
    {"code": "ig", "name": "Igbo (الإيغبو)", "dialects": [{"code": "ig_standard", "name": "Asụsụ Igbo"}]},
    {"code": "ilo", "name": "Iloko (الإيلوكو)", "dialects": [{"code": "ilo_standard", "name": "Pagsasao nga Ilokano"}]},
    {"code": "jv", "name": "Javanese (الجاوية)", "dialects": [{"code": "jv_standard", "name": "Basa Jawa"}]},
    {"code": "kab", "name": "Kabyle (القبائلية)", "dialects": [{"code": "kab_standard", "name": "Taqbaylit"}]},
    {"code": "kam", "name": "Kamba (الكامبا)", "dialects": [{"code": "kam_standard", "name": "Kikamba"}]},
    {"code": "kn", "name": "Kannada (الكانادا)", "dialects": [{"code": "kn_standard", "name": "ಕನ್ನಡ"}]},
    {"code": "ks", "name": "Kashmiri (الكشميرية)", "dialects": [{"code": "ks_standard", "name": "کٲشُر / कश्मीरी"}]},
    {"code": "kk", "name": "Kazakh (الكازاخية)", "dialects": [{"code": "kk_standard", "name": "Қазақ тілі"}]},
    {"code": "km", "name": "Khmer (الخميرية)", "dialects": [{"code": "km_standard", "name": "ភាសាខ្មែរ"}]},
    {"code": "ki", "name": "Kikuyu (الكيكويو)", "dialects": [{"code": "ki_standard", "name": "Gĩkũyũ"}]},
    {"code": "rw", "name": "Kinyarwanda (الكينيارواندية)", "dialects": [{"code": "rw_standard", "name": "Ikinyarwanda"}]},
    {"code": "kg", "name": "Kongo (الكونغوية)", "dialects": [{"code": "kg_standard", "name": "Kikongo"}]},
    {"code": "ky", "name": "Kyrgyz (القيرغيزية)", "dialects": [{"code": "ky_standard", "name": "Кыргызча"}]},
    {"code": "lo", "name": "Lao (اللاوية)", "dialects": [{"code": "lo_standard", "name": "ພາສາລາວ"}]},
    {"code": "ltg", "name": "Latgalian (اللاتغالية)", "dialects": [{"code": "ltg_standard", "name": "Latgalīšu volūda"}]},
    {"code": "lv", "name": "Latvian (اللاتفية)", "dialects": [{"code": "lv_standard", "name": "Latviešu valoda"}]},
    {"code": "ln", "name": "Lingala (اللينغالا)", "dialects": [{"code": "ln_standard", "name": "Lingála"}]},
    {"code": "lt", "name": "Lithuanian (الليتوانية)", "dialects": [{"code": "lt_standard", "name": "Lietuvių kalba"}]},
    {"code": "lb", "name": "Luxembourgish (اللوكسمبورغية)", "dialects": [{"code": "lb_standard", "name": "Lëtzebuergesch"}]},
    {"code": "mk", "name": "Macedonian (المقدونية)", "dialects": [{"code": "mk_standard", "name": "Македонски"}]},
    {"code": "mag", "name": "Magahi (الماغاهية)", "dialects": [{"code": "mag_standard", "name": "मगही"}]},
    {"code": "mai", "name": "Maithili (المايثيلية)", "dialects": [{"code": "mai_standard", "name": "मैथिली"}]},
    {"code": "ml", "name": "Malayalam (المالايالامية)", "dialects": [{"code": "ml_standard", "name": "മലയാളം"}]},
    {"code": "mt", "name": "Maltese (المالطية)", "dialects": [{"code": "mt_standard", "name": "Malti"}]},
    {"code": "mni", "name": "Manipuri (المانيبورية)", "dialects": [{"code": "mni_standard", "name": "মৈতৈলোন্"}]},
    {"code": "mr", "name": "Marathi (المراثية)", "dialects": [{"code": "mr_standard", "name": "मराठी"}]},
    {"code": "min", "name": "Minangkabau (المينانغكاباو)", "dialects": [{"code": "min_standard", "name": "Baso Minangkabau"}]},
    {"code": "lus", "name": "Mizo (الميزو)", "dialects": [{"code": "lus_standard", "name": "Mizo ṭawng"}]},
    {"code": "ne", "name": "Nepali (النيبالية)", "dialects": [{"code": "ne_standard", "name": "नेपाली"}]},
    {"code": "fuv", "name": "Nigerian Fulfulde (الفولانية النيجيرية)", "dialects": [{"code": "fuv_standard", "name": "Fulfulde"}]},
    {"code": "az", "name": "North Azerbaijani (الأذربيجانية الشمالية)", "dialects": [{"code": "az_standard", "name": "Azərbaycan dili"}]},
    {"code": "nso", "name": "Northern Sotho (السوتو الشمالية)", "dialects": [{"code": "nso_standard", "name": "Sesotho sa Leboa"}]},
    {"code": "uz", "name": "Northern Uzbek (الأوزبكية)", "dialects": [{"code": "uz_standard", "name": "Oʻzbekcha"}]},
    {"code": "nb", "name": "Norwegian Bokmål (النرويجية البوكمول)", "dialects": [{"code": "nb_standard", "name": "Norsk Bokmål"}]},
    {"code": "nn", "name": "Norwegian Nynorsk (النرويجية النينوشك)", "dialects": [{"code": "nn_standard", "name": "Norsk Nynorsk"}]},
    {"code": "ny", "name": "Nyanja / Chewa (النيانجا)", "dialects": [{"code": "ny_standard", "name": "Chinyanja"}]},
    {"code": "oc", "name": "Occitan (الأوكيتانية)", "dialects": [{"code": "oc_standard", "name": "Occitan"}]},
    {"code": "or", "name": "Odia (الأوديا)", "dialects": [{"code": "or_standard", "name": "ଓଡ଼ିଆ"}]},
    {"code": "pag", "name": "Pangasinan (البانغاسينانية)", "dialects": [{"code": "pag_standard", "name": "Salitan Pangasinan"}]},
    {"code": "ps", "name": "Pashto (البشتوية)", "dialects": [{"code": "ps_standard", "name": "پښتو"}]},
    {"code": "pa", "name": "Punjabi (البنجابية)", "dialects": [{"code": "pa_standard", "name": "ਪੰਜਾਬੀ / پنجابی"}]},
    {"code": "ro", "name": "Romanian (الرومانية)", "dialects": [{"code": "ro_standard", "name": "Română"}]},
    {"code": "sat", "name": "Santali (السانتالية)", "dialects": [{"code": "sat_standard", "name": "ᱥᱟᱱᱛᱟᱲᱤ"}]},
    {"code": "sr", "name": "Serbian (الصربية)", "dialects": [{"code": "sr_standard", "name": "Српски / Srpski"}]},
    {"code": "sd", "name": "Sindhi (السندية)", "dialects": [{"code": "sd_standard", "name": "سنڌي"}]},
    {"code": "si", "name": "Sinhala (السنهالية)", "dialects": [{"code": "si_standard", "name": "සිංහල"}]},
    {"code": "sk", "name": "Slovak (السلوفاكية)", "dialects": [{"code": "sk_standard", "name": "Slovenčina"}]},
    {"code": "sl", "name": "Slovenian (السلوفينية)", "dialects": [{"code": "sl_standard", "name": "Slovenščina"}]},
    {"code": "so", "name": "Somali (الصومالية)", "dialects": [{"code": "so_standard", "name": "Af Soomaali"}]},
    {"code": "azb", "name": "South Azerbaijani (الأذربيجانية الجنوبية)", "dialects": [{"code": "azb_standard", "name": "تورکجه"}]},
    {"code": "st", "name": "Southern Sotho (السوتو الجنوبية)", "dialects": [{"code": "st_standard", "name": "Sesotho"}]},
    {"code": "ss", "name": "Swati (السواتية)", "dialects": [{"code": "ss_standard", "name": "SiSwati"}]},
    {"code": "tg", "name": "Tajik (الطاجيكية)", "dialects": [{"code": "tg_standard", "name": "Тоҷикӣ"}]},
    {"code": "ta", "name": "Tamil (التاميلية)", "dialects": [{"code": "ta_standard", "name": "தமிழ்"}]},
    {"code": "te", "name": "Telugu (التيلوغوية)", "dialects": [{"code": "te_standard", "name": "తెలుగు"}]},
    {"code": "ti", "name": "Tigrinya (التغرينية)", "dialects": [{"code": "ti_standard", "name": "ትግርኛ"}]},
    {"code": "sq", "name": "Tosk Albanian (الألبانية)", "dialects": [{"code": "sq_standard", "name": "Shqip"}]},
    {"code": "uk", "name": "Ukrainian (الأوكرانية)", "dialects": [{"code": "uk_standard", "name": "Українська"}]},
    {"code": "ug", "name": "Uyghur (الأويغورية)", "dialects": [{"code": "ug_standard", "name": "ئۇيغۇرچە"}]},
    {"code": "cy", "name": "Welsh (الويلزية)", "dialects": [{"code": "cy_standard", "name": "Cymraeg"}]},
    {"code": "wo", "name": "Wolof (الولوفية)", "dialects": [{"code": "wo_standard", "name": "Wolof"}]},
    {"code": "xh", "name": "Xhosa (الخوسية)", "dialects": [{"code": "xh_standard", "name": "isiXhosa"}]},
    {"code": "yo", "name": "Yoruba (اليوروبية)", "dialects": [{"code": "yo_standard", "name": "Èdè Yorùbá"}]},
    {"code": "zu", "name": "Zulu (الزولية)", "dialects": [{"code": "zu_standard", "name": "isiZulu"}]},
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

# Expanded psychological, literary, and cinematic emotion spectrum (32 distinct states, No vulgar emojis)
EMOTIONS = [
    {"code": "neutral", "name": "طبيعي ورصين (Neutral & Balanced)"},
    {"code": "calm", "name": "هادئ ومريح وسكينة (Calm & Serene)"},
    {"code": "warm", "name": "دافئ وحميمي مقرب (Warm & Intimate)"},
    {"code": "enthusiastic", "name": "حماسي ومحفز ملهم (Enthusiastic & Inspiring)"},
    {"code": "cheerful", "name": "مبتهج وسعيد مشرق (Cheerful & Joyful)"},
    {"code": "dramatic", "name": "درامي وتراجيدي جاد (Dramatic & Serious)"},
    {"code": "epic", "name": "ملحمي ومهيب بطولي (Epic & Majestic)"},
    {"code": "mysterious", "name": "غامض ومثير للفضول والتشويق (Mysterious & Suspenseful)"},
    {"code": "melancholic", "name": "حزين ومؤثر شجي (Melancholic & Reflective)"},
    {"code": "somber", "name": "وقور وحزين متزن (Somber & Solemn)"},
    {"code": "whispering", "name": "هامس وسري خافت (Whispering & Secretive)"},
    {"code": "urgent", "name": "متوتر وملح متسارع (Urgent & Tense)"},
    {"code": "fearful", "name": "خائف ومرتعد مضطرب (Fearful & Anxious)"},
    {"code": "terrified", "name": "مذعور ومفزوع هلع (Terrified & Horrified)"},
    {"code": "angry", "name": "غاضب وصارم حاد (Angry & Stern)"},
    {"code": "furious", "name": "حنق وثائر هادر (Furious & Enraged)"},
    {"code": "confident", "name": "واثق وحاسم جازم (Confident & Authoritative)"},
    {"code": "affectionate", "name": "عطوف وحنون رقيق (Affectionate & Tender)"},
    {"code": "sarcastic", "name": "ساخر ومتهكم لاذع (Sarcastic & Ironic)"},
    {"code": "poetic_emotional", "name": "شاعري ووجداني وجد (Poetic & Soulful)"},
    {"code": "nostalgic", "name": "حنين وشوق نوستالجي (Nostalgic & Yearning)"},
    {"code": "hopeful", "name": "مفعم بالأمل والتفاؤل (Hopeful & Optimistic)"},
    {"code": "despairing", "name": "يائس ومنكسر خافت (Despairing & Hopeless)"},
    {"code": "astonished", "name": "مندهش ومذهول انبهار (Astonished & Amazed)"},
    {"code": "playful", "name": "مرح ومشاغب خفيف (Playful & Teasing)"},
    {"code": "contemplative", "name": "تأملي وفلسفي عميق (Contemplative & Philosophical)"},
    {"code": "exhausted", "name": "مرهق ومجهد متعب (Exhausted & Weary)"},
    {"code": "relieved", "name": "مرتاح ومطمئن سكينة (Relieved & Reassured)"},
    {"code": "romantic", "name": "رومانسي وشغوف عاطفي (Romantic & Passionate)"},
    {"code": "threatening", "name": "متوعد ومهدد مخيف (Threatening & Menacing)"},
    {"code": "somnolent", "name": "نعس وسكون هادئ (Somnolent & Sleepy)"},
    {"code": "triumphant", "name": "منتصر وفخور شموخ (Triumphant & Victorious)"},
]

# Professional broadcast, narrative, and performance delivery styles (25 distinct styles, No vulgar emojis)
DELIVERY_STYLES = [
    {"code": "documentary", "name": "تعليق وثائقي فخم واستقصائي (Documentary Narration)"},
    {"code": "commercial", "name": "إعلان تجاري وترويجي تسويقي (Commercial & Promo)"},
    {"code": "storyteller", "name": "راوي قصص وروايات سردية (Cinematic Storyteller)"},
    {"code": "audiobook", "name": "قراءة كتاب صوتي هادئ ومتصل (Audiobook Narration)"},
    {"code": "news", "name": "نشرة أخبار رسمية وإيجاز صحفي (News Broadcast)"},
    {"code": "poetic", "name": "إلقاء أدبي ونصوص شعرية فصيحة (Poetic Recitation)"},
    {"code": "conversational", "name": "حوار عفوي ومحادثة واقعية (Natural Conversation)"},
    {"code": "podcast", "name": "بودكاست إذاعي تفاعلي وحيوي (Interactive Podcast)"},
    {"code": "educational", "name": "شرح تعليمي وأكاديمي مبسط (Educational & Explainer)"},
    {"code": "corporate", "name": "عرض تقديمي ومؤسسي احترافي (Corporate Presentation)"},
    {"code": "meditation", "name": "تأمل وتنويم واسترخاء ذهني (Guided Meditation)"},
    {"code": "trailer", "name": "إعلان تشويقي وتريلر سينمائي (Movie Trailer)"},
    {"code": "motivational", "name": "خطابي تحفيزي وإلهامي حماسي (Motivational Speech)"},
    {"code": "dramatic_dialogue", "name": "تمثيل مسرحي وحواري درامي (Dramatic Roleplay)"},
    {"code": "investigative", "name": "استقصائي غموض وتحقيق جنائي (Investigative Crime)"},
    {"code": "sports", "name": "تعليق رياضي تفاعلي وحماسي (Sports Commentary)"},
    {"code": "radio_host", "name": "مقدم برامج إذاعية وترفيهية (Radio Host & DJ)"},
    {"code": "asmr", "name": "همس استرخائي حسي (ASMR & Intimate Whispering)"},
    {"code": "historical", "name": "تأريخ ملحمي وسير تاريخية (Historical & Epic Chronicles)"},
    {"code": "children_tales", "name": "حكايات أطفال وخرافات مشوقة (Children's Fairy Tales)"},
    {"code": "tech_tutorial", "name": "دليل تقني وبرمجي دقيق (Tech Tutorial & Screencast)"},
    {"code": "political_speech", "name": "خطاب سياسي وجماهيري حاشد (Political Discourse)"},
    {"code": "spiritual", "name": "ابتهالات ونصوص روحانية وتدبر (Spiritual & Contemplative)"},
    {"code": "satirical", "name": "مونولوج كوميدي وستاند أب ساخر (Satirical Monologue)"},
    {"code": "legal_formal", "name": "قراءة قانونية وبيان رسمي حازم (Legal & Formal Declaration)"},
]
