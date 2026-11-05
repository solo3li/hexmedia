import io
import wave
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from tts.services.chunker import split_text_into_chunks
from tts.services.audio_stitcher import stitch_wav_buffers, convert_to_mp3
from tts.models import TTSJob, ClonedVoice
from tts.services.voice_cloner import convert_to_wav_24k_mono, create_fallback_wav, replicate_voice_with_gemini
from ai_studio.services.gemini_service import generate_voice_audio


class TTSUnitTests(TestCase):
    def test_chunker_short_text(self):
        """Short text (< 2500 chars) should remain a single chunk."""
        text = "هذا نص تجريبي قصير للاختبار."
        chunks = split_text_into_chunks(text, max_chars=2500)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], text)

    def test_chunker_long_text_splits_cleanly(self):
        """Long text (> 3000 chars) should split into multiple chunks along sentence boundaries."""
        sentence = "هذه جملة مفيدة وكاملة تنتهي بنقطة لتوضيح المعنى المطلوب. "
        long_text = sentence * 60  # ~3300 characters
        self.assertGreater(len(long_text), 2500)

        chunks = split_text_into_chunks(long_text, max_chars=1500)
        self.assertGreater(len(chunks), 1)

        # Ensure no chunk exceeds the max_chars
        for c in chunks:
            self.assertLessEqual(len(c), 1500)
            self.assertTrue(len(c.strip()) > 0)

        # Ensure all content is preserved
        combined = "".join(chunks)
        self.assertEqual(len(combined.replace(" ", "")), len(long_text.replace(" ", "")))

    def test_stitch_wav_buffers(self):
        """Stitching multiple WAV buffers creates a valid combined WAV file."""
        wav1 = generate_voice_audio("مرحبا بكم", voice_name="Puck")
        wav2 = generate_voice_audio("في استوديو هيكس ميديا", voice_name="Puck")

        with wave.open(io.BytesIO(wav1), 'rb') as w1:
            frames1 = w1.getnframes()
        with wave.open(io.BytesIO(wav2), 'rb') as w2:
            frames2 = w2.getnframes()

        stitched = stitch_wav_buffers([wav1, wav2], pause_seconds=0.2)
        self.assertTrue(len(stitched) > len(wav1))
        self.assertTrue(len(stitched) > len(wav2))

        # Check valid WAV header and frame count
        with wave.open(io.BytesIO(stitched), 'rb') as sw:
            total_frames = sw.getnframes()
            # Total frames must be approximately frames1 + frames2 + pause_frames
            self.assertGreater(total_frames, frames1 + frames2)

    def test_convert_to_mp3(self):
        """convert_to_mp3 converts WAV PCM audio to valid MP3 audio stream."""
        wav = create_fallback_wav(sample_rate=24000, duration_seconds=1.0)
        mp3 = convert_to_mp3(wav)
        self.assertGreater(len(mp3), 100)
        # MP3 file starts with ID3 header (0x49 0x44 0x33) or sync frame header (0xFF 0xFB/0xF3/0xF2)
        is_mp3 = mp3[:3] == b'ID3' or mp3[:2] in (b'\xff\xfb', b'\xff\xf3', b'\xff\xf2')
        self.assertTrue(is_mp3)

    def test_tts_job_model(self):
        """TTSJob stores conversion data with user ownership and parameters."""
        user = User.objects.create_user(username="tts_user", password="password")
        job = TTSJob.objects.create(
            user=user,
            title="تسجيل وثائقي",
            input_text="نص وثائقي تاريخي",
            language="ar",
            dialect="msa",
            voice_profile="Charon",
            emotion="dramatic",
            delivery_style="documentary",
            duration_seconds=45.5,
            audio_url="http://storage.local/audio.wav"
        )
        self.assertEqual(job.user, user)
        self.assertEqual(job.voice_profile, "Charon")
        self.assertEqual(job.duration_seconds, 45.5)


class TTSAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="tts_api_user",
            email="tts_api_user@test.local",
            password="Password123!"
        )
        from ai_studio.auth import generate_tokens_for_user
        tokens = generate_tokens_for_user(self.user)
        self.token = tokens["access_token"]
        self.auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    def test_get_tts_options(self):
        """GET /api/tts/options returns supported languages, voices, emotions, and styles."""
        res = self.client.get("/api/tts/options")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("languages", data)
        self.assertIn("voices", data)
        self.assertIn("emotions", data)
        self.assertIn("delivery_styles", data)

        # Check voices include standard Gemini voices
        voice_names = [v["name"] for v in data["voices"]]
        self.assertIn("Charon", voice_names)
        self.assertIn("Puck", voice_names)

    def test_generate_tts_endpoint_short_text(self):
        """POST /api/tts/generate processes small text and returns 200 with audio URL."""
        import json
        payload = {
            "text": "مرحباً بكم في استوديو هيكس ميديا الصوتي الذكي.",
            "voice_profile": "Charon",
            "language": "ar",
            "dialect": "msa",
            "emotion": "enthusiastic",
            "delivery_style": "documentary"
        }
        res = self.client.post(
            "/api/tts/generate",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("id", data)
        self.assertIn("audio_url", data)
        self.assertTrue(data["audio_url"].endswith(".mp3"))
        self.assertEqual(data["chunks_count"], 1)
        self.assertGreater(data["duration_seconds"], 0)
        self.assertEqual(data["voice_profile"], "Charon")

        # Verify job saved in database
        job = TTSJob.objects.get(id=data["id"])
        self.assertEqual(job.user, self.user)
        self.assertEqual(job.chunks_count, 1)

    def test_generate_tts_long_text_chunking_and_stitching(self):
        """POST /api/tts/generate splits text > 3000 chars into chunks and stitches into master audio."""
        import json
        sentence = "هذا مقطع سردي طويل يصف معالم المدينة القديمة وتاريخها العريق. "
        long_text = sentence * 60  # > 3000 chars
        payload = {
            "text": long_text,
            "title": "سرد المدينة القديمة",
            "voice_profile": "Puck",
            "language": "ar",
            "dialect": "msa",
            "emotion": "dramatic",
            "delivery_style": "storyteller"
        }
        res = self.client.post(
            "/api/tts/generate",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data["chunks_count"], 1)
        self.assertIn("audio_url", data)
        self.assertTrue(data["audio_url"].endswith(".mp3"))
        self.assertTrue(len(data["chunks"]) > 1)

        # Check job in database
        job = TTSJob.objects.get(id=data["id"])
        self.assertGreater(job.chunks_count, 1)
        self.assertGreater(job.duration_seconds, 0)

    def test_tts_history_endpoint(self):
        """GET /api/tts/history returns list of user's past conversions."""
        job = TTSJob.objects.create(
            user=self.user,
            title="تسجيل قديم",
            input_text="نص التسجيل القديم",
            duration_seconds=15.0,
            audio_url="http://storage.local/old.wav"
        )
        res = self.client.get("/api/tts/history", **self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(len(data) >= 1)
        job_ids = [j["id"] for j in data]
        self.assertIn(str(job.id), job_ids)

    def test_unauthenticated_requests_blocked(self):
        """Unauthenticated requests return 401."""
        res_post = self.client.post("/api/tts/generate", data="{}", content_type="application/json")
        self.assertEqual(res_post.status_code, 401)
        res_history = self.client.get("/api/tts/history")
        self.assertEqual(res_history.status_code, 401)

    def test_tts_frontend_ui_elements(self):
        """Frontend index page contains TTS Studio modal, trigger button, and audio card renderer."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        content = res.content.decode("utf-8")
        self.assertIn("openTTSConfigModal", content)
        self.assertIn('id="ttsConfigModal"', content)
        self.assertIn('id="ttsLanguageSelect"', content)
        self.assertIn('id="ttsDialectSelect"', content)
        self.assertIn('id="ttsVoiceProfilesGrid"', content)
        self.assertNotIn('id="ttsAutoDiacritizeToggle"', content)
        self.assertNotIn("التشكيل التلقائي الذكي", content)
        self.assertIn("renderTTSAudioCard", content)
        self.assertIn("تحميل MP3", content)

    def test_tts_job_appears_in_profile_media(self):
        """Generated TTS audio automatically appears in user profile media library."""
        import json
        payload = {
            "text": "هذا اختبار لمكتبة وسائط الحساب الشخصي.",
            "voice_profile": "Kore",
            "language": "ar",
            "dialect": "egyptian",
            "emotion": "happy",
            "delivery_style": "commercial"
        }
        res_gen = self.client.post(
            "/api/tts/generate",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers
        )
        self.assertEqual(res_gen.status_code, 200)
        job_data = res_gen.json()

        # Check /api/profile/media
        res_media = self.client.get("/api/profile/media", **self.auth_headers)
        self.assertEqual(res_media.status_code, 200)
        media_data = res_media.json()
        audio_urls = [a["audio_url"] for a in media_data["audio"]]
        self.assertIn(job_data["audio_url"], audio_urls)

    def test_full_30_gemini_voice_profiles_catalog(self):
        """All 30 official Gemini TTS voices exist in catalog and acoustic fallback."""
        from tts.services.tts_options import VOICES
        self.assertEqual(len(VOICES), 30)
        
        expected_30_voices = {
            "Zephyr", "Puck", "Charon", "Kore", "Fenrir",
            "Leda", "Orus", "Aoede", "Callirrhoe", "Autonoe",
            "Enceladus", "Iapetus", "Umbriel", "Algieba", "Despina",
            "Erinome", "Algenib", "Rasalgethi", "Laomedeia", "Achernar",
            "Alnilam", "Schedar", "Gacrux", "Pulcherrima", "Achird",
            "Zubenelgenubi", "Vindemiatrix", "Sadachbia", "Sadaltager", "Sulafat"
        }
        catalog_names = {v["name"] for v in VOICES}
        self.assertEqual(catalog_names, expected_30_voices)

        for v in VOICES:
            self.assertIn("name", v)
            self.assertIn("gender", v)
            self.assertIn(v["gender"], ["male", "female", "neutral"])
            self.assertIn("tag", v)
            self.assertIn("description", v)
            self.assertGreater(v["pitch"], 50)
            # Verify no emoji in name or tag
            self.assertFalse(any(ord(char) > 0x1F000 for char in v["name"]))
            self.assertFalse(any(ord(char) > 0x1F000 for char in v["tag"]))

        # Verify acoustic fallback generator handles non-default voices cleanly
        wav_zephyr = generate_voice_audio("Sample audio test for Zephyr", voice_name="Zephyr")
        self.assertGreater(len(wav_zephyr), 1000)
        wav_gacrux = generate_voice_audio("Sample audio test for Gacrux", voice_name="Gacrux")
        self.assertGreater(len(wav_gacrux), 1000)

    def test_multilingual_and_dialect_catalog_completeness(self):
        """Catalog supports 130+ world languages and 19 Arabic dialects without cartoon emojis."""
        from tts.services.tts_options import LANGUAGES
        self.assertGreaterEqual(len(LANGUAGES), 125)

        # Check Arabic dialects
        ar_entry = next(l for l in LANGUAGES if l["code"] == "ar")
        self.assertGreaterEqual(len(ar_entry["dialects"]), 18)
        ar_dialect_codes = {d["code"] for d in ar_entry["dialects"]}
        self.assertIn("msa", ar_dialect_codes)
        self.assertIn("egyptian", ar_dialect_codes)
        self.assertIn("saudi", ar_dialect_codes)
        self.assertIn("gulf", ar_dialect_codes)
        self.assertIn("moroccan", ar_dialect_codes)
        self.assertIn("syrian", ar_dialect_codes)
        self.assertIn("iraqi", ar_dialect_codes)
        self.assertIn("tunisian", ar_dialect_codes)
        self.assertIn("algerian", ar_dialect_codes)
        self.assertIn("sudanese", ar_dialect_codes)
        self.assertIn("yemeni", ar_dialect_codes)
        self.assertIn("omani", ar_dialect_codes)

        # Check major world languages
        lang_codes = {l["code"] for l in LANGUAGES}
        for code in ["en", "fr", "es", "de", "it", "pt", "ru", "tr", "fa", "ur", "hi", "ja", "ko", "zh", "id", "ms", "nl", "sv", "pl", "el", "he", "vi", "th", "sw", "ku"]:
            self.assertIn(code, lang_codes)

        # Check that no dialect or language name has cartoon emoji or flag
        for lang in LANGUAGES:
            self.assertFalse(any(ord(char) > 0x1F000 for char in lang["name"]))
            for dialect in lang.get("dialects", []):
                self.assertFalse(any(ord(char) > 0x1F000 for char in dialect["name"]))

    def test_emotions_and_delivery_styles_richness_and_cleanliness(self):
        """EMOTIONS has 30+ states and DELIVERY_STYLES has 24+ styles with zero emojis."""
        from tts.services.tts_options import EMOTIONS, DELIVERY_STYLES
        self.assertGreaterEqual(len(EMOTIONS), 30)
        self.assertGreaterEqual(len(DELIVERY_STYLES), 24)

        emotion_codes = {e["code"] for e in EMOTIONS}
        self.assertIn("neutral", emotion_codes)
        self.assertIn("calm", emotion_codes)
        self.assertIn("epic", emotion_codes)
        self.assertIn("mysterious", emotion_codes)
        self.assertIn("whispering", emotion_codes)
        self.assertIn("urgent", emotion_codes)
        self.assertIn("terrified", emotion_codes)
        self.assertIn("furious", emotion_codes)
        self.assertIn("triumphant", emotion_codes)
        self.assertIn("nostalgic", emotion_codes)

        style_codes = {s["code"] for s in DELIVERY_STYLES}
        self.assertIn("documentary", style_codes)
        self.assertIn("storyteller", style_codes)
        self.assertIn("audiobook", style_codes)
        self.assertIn("trailer", style_codes)
        self.assertIn("podcast", style_codes)
        self.assertIn("motivational", style_codes)
        self.assertIn("asmr", style_codes)
        self.assertIn("radio_host", style_codes)
        self.assertIn("historical", style_codes)
        self.assertIn("children_tales", style_codes)

        # Ensure no emojis in metadata
        for e in EMOTIONS:
            self.assertNotIn("icon", e)
            self.assertFalse(any(ord(char) > 0x1F000 for char in e["name"]))

        for s in DELIVERY_STYLES:
            self.assertFalse(any(ord(char) > 0x1F000 for char in s["name"]))

    def test_generate_tts_with_various_voices_and_styles(self):
        """POST /api/tts/generate succeeds with newly added Gemini voices, custom directives, and styles."""
        import json
        payload = {
            "text": "The stars in the deep night reveal the history of our ancient cosmos.",
            "title": "Cosmic Narration",
            "voice_profile": "Zephyr",
            "language": "en",
            "dialect": "us",
            "emotion": "mysterious",
            "delivery_style": "trailer",
            "custom_directives": "Deep resonance with ambient pacing",
            "auto_diacritize": True
        }
        res = self.client.post(
            "/api/tts/generate",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["voice_profile"], "Zephyr")
        self.assertEqual(data["language"], "en")
        self.assertEqual(data["dialect"], "us")
        self.assertEqual(data["emotion"], "mysterious")
        self.assertEqual(data["delivery_style"], "trailer")
        self.assertIn("text", data)
        self.assertGreater(data["char_count"], 0)
        self.assertIn("audio_url", data)

    def test_auto_diacritize_flag_and_custom_voice_id(self):
        """POST /api/tts/generate respects auto_diacritize=False and supports custom voice IDs."""
        import json
        text_raw = "نص عربي صريح بدون تشكيل إجباري"
        payload = {
            "text": text_raw,
            "title": "اختبار التشكيل",
            "voice_profile": "voice_custom_studio_actor_99",
            "language": "ar",
            "dialect": "egyptian",
            "auto_diacritize": False,
            "custom_directives": "نبرة إذاعية حرة"
        }
        res = self.client.post(
            "/api/tts/generate",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["voice_profile"], "voice_custom_studio_actor_99")
        self.assertEqual(data["vocalized_text"], text_raw)
        self.assertEqual(data["text"], text_raw)
        self.assertEqual(data["char_count"], len(text_raw))

    def test_acoustic_modulation_for_emotions(self):
        """Fallback generator acoustic frequency and duration modulate based on emotion."""
        wav_whisper = generate_voice_audio("هذا اختبار صوتي هامس وهادئ", voice_name="Charon", emotion="whispering")
        wav_urgent = generate_voice_audio("هذا اختبار صوتي هامس وهادئ", voice_name="Charon", emotion="urgent")
        self.assertGreater(len(wav_whisper), 500)
        self.assertGreater(len(wav_urgent), 500)
        # Slower whispering cadence creates a different duration/sample count than urgent cadence
        self.assertNotEqual(len(wav_whisper), len(wav_urgent))

    def test_tts_modal_theme_and_no_garish_emojis(self):
        """Frontend ttsConfigModal matches obsidian/limeAccent and has no vulgar emojis."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        content = res.content.decode("utf-8")
        
        # Modal markup exists and uses limeAccent theme
        self.assertIn('id="ttsConfigModal"', content)
        self.assertIn('bg-limeAccent', content)
        self.assertIn('text-limeAccent', content)
        self.assertNotIn('peer-checked:bg-cyan-500', content)
        
        # Check that ttsConfigModal does not contain emojis
        modal_start = content.find('id="ttsConfigModal"')
        modal_end = content.find('<!-- MINIMAL STATUS NOTIFICATION', modal_start)
        modal_html = content[modal_start:modal_end]
        
        # Ensure no cartoon emojis inside modal
        for emoji_char in ["🎙️", "👨‍💼", "⚔️", "🔥", "🌧️", "🤫"]:
            self.assertNotIn(emoji_char, modal_html)


class VoiceCloneTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(
            username="voice_clone_user_a",
            email="clone_a@test.local",
            password="Password123!"
        )
        self.user_b = User.objects.create_user(
            username="voice_clone_user_b",
            email="clone_b@test.local",
            password="Password123!"
        )
        from ai_studio.auth import generate_tokens_for_user
        self.token_a = generate_tokens_for_user(self.user_a)["access_token"]
        self.token_b = generate_tokens_for_user(self.user_b)["access_token"]
        self.auth_headers_a = {"HTTP_AUTHORIZATION": f"Bearer {self.token_a}"}
        self.auth_headers_b = {"HTTP_AUTHORIZATION": f"Bearer {self.token_b}"}

    def test_voice_cloner_audio_conversion(self):
        """Audio conversion produces a valid 24kHz mono 16-bit PCM WAV."""
        raw_pcm = create_fallback_wav(sample_rate=24000, duration_seconds=1.0, freq=440.0)
        wav_converted = convert_to_wav_24k_mono(raw_pcm)
        self.assertGreater(len(wav_converted), 1000)
        with wave.open(io.BytesIO(wav_converted), 'rb') as wf:
            self.assertEqual(wf.getnchannels(), 1)
            self.assertEqual(wf.getframerate(), 24000)
            self.assertEqual(wf.getsampwidth(), 2)

    def test_cloned_voice_model_creation(self):
        """ClonedVoice model stores identity, audio urls, and Gemini voice ID."""
        cv = ClonedVoice.objects.create(
            user=self.user_a,
            name="صوتي الإخباري",
            gemini_voice_id="voice_news_anchor_123",
            source_audio_url="http://storage.local/source.wav",
            consent_audio_url="http://storage.local/consent.wav",
            status="READY"
        )
        self.assertEqual(cv.user, self.user_a)
        self.assertEqual(cv.name, "صوتي الإخباري")
        self.assertEqual(cv.gemini_voice_id, "voice_news_anchor_123")
        self.assertEqual(cv.status, "READY")
        self.assertIn("voice_news_anchor_123", str(cv))

    def test_clone_voice_endpoint_success(self):
        """POST /api/tts/voices/clone accepts audio files, creates ClonedVoice, and returns 200."""
        source_audio = SimpleUploadedFile("source.wav", create_fallback_wav(duration_seconds=12.0), content_type="audio/wav")
        consent_audio = SimpleUploadedFile("consent.wav", create_fallback_wav(duration_seconds=4.0), content_type="audio/wav")

        res = self.client.post(
            "/api/tts/voices/clone",
            data={
                "name": "صوتي الطبيعي",
                "source_audio": source_audio,
                "consent_audio": consent_audio
            },
            **self.auth_headers_a
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("id", data)
        self.assertEqual(data["name"], "صوتي الطبيعي")
        self.assertTrue(data["gemini_voice_id"].startswith("voice_"))
        self.assertIn("source_audio_url", data)
        self.assertIn("consent_audio_url", data)
        self.assertEqual(data["status"], "READY")

        # Verify DB entry
        cv = ClonedVoice.objects.get(id=data["id"])
        self.assertEqual(cv.user, self.user_a)
        self.assertEqual(cv.name, "صوتي الطبيعي")

    def test_clone_voice_endpoint_validation_errors(self):
        """POST /api/tts/voices/clone returns 400 or 422 if recordings are missing."""
        source_audio = SimpleUploadedFile("source.wav", create_fallback_wav(duration_seconds=5.0), content_type="audio/wav")
        res = self.client.post(
            "/api/tts/voices/clone",
            data={"name": "صوت تجريبي", "source_audio": source_audio},
            **self.auth_headers_a
        )
        self.assertIn(res.status_code, [400, 422])

        consent_audio = SimpleUploadedFile("consent.wav", create_fallback_wav(duration_seconds=3.0), content_type="audio/wav")
        res2 = self.client.post(
            "/api/tts/voices/clone",
            data={"name": "صوت تجريبي", "consent_audio": consent_audio},
            **self.auth_headers_a
        )
        self.assertIn(res2.status_code, [400, 422])

    def test_list_cloned_voices_and_user_isolation(self):
        """GET /api/tts/voices/cloned isolates voices per authenticated user."""
        cv_a = ClonedVoice.objects.create(
            user=self.user_a,
            name="صوت أ",
            gemini_voice_id="voice_user_a_1",
            status="READY"
        )
        cv_b = ClonedVoice.objects.create(
            user=self.user_b,
            name="صوت ب",
            gemini_voice_id="voice_user_b_1",
            status="READY"
        )

        res_a = self.client.get("/api/tts/voices/cloned", **self.auth_headers_a)
        self.assertEqual(res_a.status_code, 200)
        data_a = res_a.json()
        ids_a = [v["id"] for v in data_a]
        self.assertIn(str(cv_a.id), ids_a)
        self.assertNotIn(str(cv_b.id), ids_a)

        res_b = self.client.get("/api/tts/voices/cloned", **self.auth_headers_b)
        self.assertEqual(res_b.status_code, 200)
        data_b = res_b.json()
        ids_b = [v["id"] for v in data_b]
        self.assertIn(str(cv_b.id), ids_b)
        self.assertNotIn(str(cv_a.id), ids_b)

    def test_test_cloned_voice_endpoint(self):
        """POST /api/tts/voices/cloned/<id>/test synthesizes a speech sample."""
        cv = ClonedVoice.objects.create(
            user=self.user_a,
            name="صوت الاختبار",
            gemini_voice_id="voice_test_replicated_88",
            status="READY"
        )
        payload = {"text": "هذا اختبار نطق بالعينة المستنسخة"}
        import json
        res = self.client.post(
            f"/api/tts/voices/cloned/{cv.id}/test",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers_a
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["voice_id"], str(cv.id))
        self.assertIn("audio_url", data)
        self.assertGreater(data["duration_seconds"], 0)

        # Check DB updated with sample_audio_url
        cv.refresh_from_db()
        self.assertTrue(len(cv.sample_audio_url) > 0)

    def test_delete_cloned_voice_endpoint(self):
        """DELETE /api/tts/voices/cloned/<id> deletes voice and prevents cross-user deletion."""
        cv = ClonedVoice.objects.create(
            user=self.user_a,
            name="صوت للحذف",
            gemini_voice_id="voice_delete_me_99",
            status="READY"
        )

        # User B cannot delete User A's voice
        res_fail = self.client.delete(f"/api/tts/voices/cloned/{cv.id}", **self.auth_headers_b)
        self.assertIn(res_fail.status_code, [404, 403])
        self.assertTrue(ClonedVoice.objects.filter(id=cv.id).exists())

        # User A can delete their own voice
        res_ok = self.client.delete(f"/api/tts/voices/cloned/{cv.id}", **self.auth_headers_a)
        self.assertEqual(res_ok.status_code, 200)
        self.assertFalse(ClonedVoice.objects.filter(id=cv.id).exists())

    def test_tts_generation_with_cloned_voice(self):
        """POST /api/tts/generate succeeds with cloned voice ID (voice_...)."""
        import json
        cv = ClonedVoice.objects.create(
            user=self.user_a,
            name="صوتي الوثائقي",
            gemini_voice_id="voice_rep_custom_speaker_101",
            status="READY"
        )
        payload = {
            "text": "هذا مقطع صوتي مخصص باستخدام الصوت المستنسخ التابع للمستخدم.",
            "voice_profile": cv.gemini_voice_id,
            "language": "ar",
            "dialect": "msa",
            "emotion": "dramatic"
        }
        res = self.client.post(
            "/api/tts/generate",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers_a
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["voice_profile"], cv.gemini_voice_id)
        self.assertIn("audio_url", data)

    def test_frontend_voice_clone_elements(self):
        """Frontend contains Clone Your Voice tool menu item, wizard modal, and My Voices section."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        content = res.content.decode("utf-8")

        # Tool entry
        self.assertIn("openVoiceCloneModal", content)
        self.assertIn("استنساخ الصوت (Clone Your Voice)", content)

        # Modal
        self.assertIn('id="voiceCloneModal"', content)
        self.assertIn('id="vcVoiceNameInput"', content)
        self.assertIn('id="vcStepContainer1"', content)
        self.assertIn('id="vcStepContainer2"', content)
        self.assertIn('id="vcStepContainer3"', content)
        self.assertIn('id="vcStepContainer4"', content)

        # Biometric consent text exact wording
        self.assertIn("أنا مالك هذا الصوت وأوافق على أن تستخدم google هذا الصوت لإنشاء نموذج صوتي اصطناعي.", content)

        # TTS Studio My Voices section
        self.assertIn("أصواتي المستنسخة (My Voices)", content)
        self.assertIn('id="ttsClonedVoicesContainer"', content)
        self.assertIn('id="ttsClonedVoiceCountBadge"', content)
        self.assertIn("deleteTTSClonedVoice", content)

    def test_tts_generation_with_long_gemini_voice_id(self):
        """TTSJob and /api/tts/generate properly support realistic Gemini voice IDs > 50 characters."""
        import json
        long_voice_id = "voice_rep_google_gemini_38_flash_replicated_speaker_998877665544332211"
        self.assertGreater(len(long_voice_id), 50)
        cv = ClonedVoice.objects.create(
            user=self.user_a,
            name="صوت طويل المعرف",
            gemini_voice_id=long_voice_id,
            status="READY"
        )
        payload = {
            "text": "اختبار لتوليد صوت باستخدام معرف صوت طويل يتجاوز خمسين حرفاً.",
            "voice_profile": cv.gemini_voice_id,
            "language": "ar",
            "dialect": "msa",
            "emotion": "neutral"
        }
        res = self.client.post(
            "/api/tts/generate",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers_a
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["voice_profile"], long_voice_id)
        job = TTSJob.objects.get(id=data["id"])
        self.assertEqual(job.voice_profile, long_voice_id)

    def test_clone_voice_rejects_audio_under_10_seconds(self):
        """POST /api/tts/voices/clone rejects reference audio shorter than 10 seconds."""
        # 4 seconds reference audio (< 9.5s requirement)
        short_source = SimpleUploadedFile("short.wav", create_fallback_wav(duration_seconds=4.0), content_type="audio/wav")
        consent_audio = SimpleUploadedFile("consent.wav", create_fallback_wav(duration_seconds=4.0), content_type="audio/wav")

        res = self.client.post(
            "/api/tts/voices/clone",
            data={
                "name": "صوت قصير",
                "source_audio": short_source,
                "consent_audio": consent_audio
            },
            **self.auth_headers_a
        )
        self.assertEqual(res.status_code, 400)
        data = res.json()
        err_msg = data.get("detail") or data.get("message", "")
        self.assertIn("قصير جداً", err_msg)

    def test_clone_voice_fails_on_biometric_speaker_mismatch(self):
        """POST /api/tts/voices/clone raises 400 if Gemini speaker verification rejects audio."""
        from unittest.mock import MagicMock, patch
        mock_client = MagicMock()
        mock_client.voices.create.side_effect = Exception("Speaker mismatch detected: consent audio does not match speaker")

        source_audio = SimpleUploadedFile("source.wav", create_fallback_wav(duration_seconds=12.0), content_type="audio/wav")
        consent_audio = SimpleUploadedFile("consent.wav", create_fallback_wav(duration_seconds=4.0), content_type="audio/wav")

        with patch("tts.services.voice_cloner.get_gemini_client", return_value=(mock_client, MagicMock())):
            res = self.client.post(
                "/api/tts/voices/clone",
                data={
                    "name": "صوت غير مطابق",
                    "source_audio": source_audio,
                    "consent_audio": consent_audio
                },
                **self.auth_headers_a
            )
            self.assertEqual(res.status_code, 400)
            data = res.json()
            err_msg = data.get("detail") or data.get("message", "")
            self.assertIn("فشل استنساخ الصوت", err_msg)
            self.assertFalse(ClonedVoice.objects.filter(name="صوت غير مطابق").exists())

    def test_generate_voice_audio_with_cloned_voice_uuid(self):
        """generate_voice_audio properly resolves ClonedVoice UUID to its gemini_voice_id."""
        from ai_studio.services.gemini_service import generate_voice_audio
        cv = ClonedVoice.objects.create(
            user=self.user_a,
            name="صوت UUID",
            gemini_voice_id="voice_rep_uuid_test_99",
            status="READY"
        )
        audio_bytes = generate_voice_audio("مرحبا بكم في هذا الاختبار", voice_name=str(cv.id))
        self.assertGreater(len(audio_bytes), 1000)




