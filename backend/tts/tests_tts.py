import io
import wave
from django.test import TestCase, Client
from django.contrib.auth.models import User
from tts.services.chunker import split_text_into_chunks
from tts.services.audio_stitcher import stitch_wav_buffers
from tts.models import TTSJob
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
        self.assertIn('id="ttsAutoDiacritizeToggle"', content)
        self.assertIn("renderTTSAudioCard", content)

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
        """Catalog supports 25+ world languages and 16 Arabic dialects without cartoon emojis."""
        from tts.services.tts_options import LANGUAGES
        self.assertGreaterEqual(len(LANGUAGES), 25)

        # Check Arabic dialects
        ar_entry = next(l for l in LANGUAGES if l["code"] == "ar")
        self.assertGreaterEqual(len(ar_entry["dialects"]), 15)
        ar_dialect_codes = {d["code"] for d in ar_entry["dialects"]}
        self.assertIn("msa", ar_dialect_codes)
        self.assertIn("egyptian", ar_dialect_codes)
        self.assertIn("saudi", ar_dialect_codes)
        self.assertIn("gulf", ar_dialect_codes)
        self.assertIn("moroccan", ar_dialect_codes)
        self.assertIn("syrian", ar_dialect_codes)
        self.assertIn("iraqi", ar_dialect_codes)

        # Check that no dialect or language name has cartoon emoji or flag
        for lang in LANGUAGES:
            self.assertFalse(any(ord(char) > 0x1F000 for char in lang["name"]))
            for dialect in lang.get("dialects", []):
                self.assertFalse(any(ord(char) > 0x1F000 for char in dialect["name"]))

    def test_emotions_and_delivery_styles_richness_and_cleanliness(self):
        """EMOTIONS and DELIVERY_STYLES have rich spectra with zero emojis."""
        from tts.services.tts_options import EMOTIONS, DELIVERY_STYLES
        self.assertGreaterEqual(len(EMOTIONS), 16)
        self.assertGreaterEqual(len(DELIVERY_STYLES), 16)

        emotion_codes = {e["code"] for e in EMOTIONS}
        self.assertIn("neutral", emotion_codes)
        self.assertIn("calm", emotion_codes)
        self.assertIn("epic", emotion_codes)
        self.assertIn("mysterious", emotion_codes)
        self.assertIn("whispering", emotion_codes)
        self.assertIn("urgent", emotion_codes)

        style_codes = {s["code"] for s in DELIVERY_STYLES}
        self.assertIn("documentary", style_codes)
        self.assertIn("storyteller", style_codes)
        self.assertIn("audiobook", style_codes)
        self.assertIn("trailer", style_codes)
        self.assertIn("podcast", style_codes)
        self.assertIn("motivational", style_codes)

        # Ensure no emojis in metadata
        for e in EMOTIONS:
            self.assertNotIn("icon", e)
            self.assertFalse(any(ord(char) > 0x1F000 for char in e["name"]))

        for s in DELIVERY_STYLES:
            self.assertFalse(any(ord(char) > 0x1F000 for char in s["name"]))

    def test_generate_tts_with_various_voices_and_styles(self):
        """POST /api/tts/generate succeeds with newly added Gemini voices and styles."""
        import json
        payload = {
            "text": "The stars in the deep night reveal the history of our ancient cosmos.",
            "title": "Cosmic Narration",
            "voice_profile": "Zephyr",
            "language": "en",
            "dialect": "us",
            "emotion": "mysterious",
            "delivery_style": "trailer"
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
        self.assertIn("audio_url", data)

    def test_tts_modal_theme_and_no_garish_emojis(self):
        """Frontend ttsConfigModal matches obsidian/limeAccent and has no vulgar emojis."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        content = res.content.decode("utf-8")
        
        # Modal markup exists and uses limeAccent theme
        self.assertIn('id="ttsConfigModal"', content)
        self.assertIn('peer-checked:bg-limeAccent', content)
        self.assertIn('text-limeAccent', content)
        self.assertNotIn('peer-checked:bg-cyan-500', content)
        
        # Check that ttsConfigModal does not contain emojis
        modal_start = content.find('id="ttsConfigModal"')
        modal_end = content.find('<!-- MINIMAL STATUS NOTIFICATION', modal_start)
        modal_html = content[modal_start:modal_end]
        
        # Ensure no cartoon emojis inside modal
        for emoji_char in ["🎙️", "👨‍💼", "⚔️", "🔥", "🌧️", "🤫"]:
            self.assertNotIn(emoji_char, modal_html)


