import json
import os
import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth.models import User
from ai_studio.services.motion_service import (
    generate_word_timestamps,
    build_motion_props,
    render_motion_video,
    save_uploaded_video,
    ingest_video_url,
    probe_video_metadata,
    generate_viral_script,
    synthesize_motion_speech,
    SUPPORTED_TEMPLATES,
    SUPPORTED_ASPECT_RATIOS,
    SUPPORTED_FONTS,
    SUPPORTED_ENTRY_ANIMATIONS,
    SUPPORTED_BGM_PRESETS,
)


class MotionServiceTestCase(TestCase):
    def test_generate_word_timestamps_default(self):
        words = generate_word_timestamps()
        self.assertIsInstance(words, list)
        self.assertGreater(len(words), 0)
        for w in words:
            self.assertIn("word", w)
            self.assertIn("start", w)
            self.assertIn("end", w)
            self.assertGreaterEqual(w["end"], w["start"])

    def test_generate_word_timestamps_custom_text(self):
        text = "هذا اختبار لتزامن كلمات الموشن جرافيكس"
        words = generate_word_timestamps(text, duration_seconds=4.0)
        self.assertEqual(len(words), 6)
        self.assertEqual(words[0]["word"], "هذا")
        self.assertEqual(words[-1]["word"], "جرافيكس")
        # Ensure sequential timing
        for i in range(len(words) - 1):
            self.assertLessEqual(words[i]["start"], words[i + 1]["start"])
            self.assertLessEqual(words[i]["end"], 4.0)

    def test_build_motion_props(self):
        props = build_motion_props(
            text="تحريك نصوص سينمائية ذكية",
            title="اختبار الموشن",
            subtitle="فرعي",
            speaker_name="المتحدث",
            template_id="tiktok_kinetic",
            aspect_ratio="9:16",
            duration_seconds=3.5,
        )
        self.assertEqual(props["title"], "اختبار الموشن")
        self.assertEqual(props["subtitle"], "فرعي")
        self.assertEqual(props["speakerName"], "المتحدث")
        self.assertEqual(props["templateId"], "tiktok_kinetic")
        self.assertEqual(props["aspectRatio"], "9:16")
        self.assertEqual(props["durationInSeconds"], 3.5)
        self.assertEqual(len(props["words"]), 4)

    def test_build_motion_props_fallback_invalid_template(self):
        props = build_motion_props(template_id="invalid_template", aspect_ratio="invalid_ratio")
        self.assertEqual(props["templateId"], "dark_neon")
        self.assertEqual(props["aspectRatio"], "9:16")

    @patch("ai_studio.services.motion_service.subprocess.run")
    @patch("ai_studio.services.motion_service.upload_bytes")
    def test_render_motion_video_success(self, mock_upload, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        mock_upload.return_value = "https://hexmedia-assets.test/motion/test.mp4"

        # Mock os.path.exists and os.path.getsize for output file
        orig_exists = os.path.exists
        orig_getsize = os.path.getsize

        def fake_exists(path):
            if path.endswith(".mp4") or "rendered.mp4" in path:
                return True
            return orig_exists(path)

        def fake_getsize(path):
            if path.endswith(".mp4") or "rendered.mp4" in path:
                return 1024
            return orig_getsize(path)

        with patch("os.path.exists", side_effect=fake_exists), \
             patch("os.path.getsize", side_effect=fake_getsize), \
             patch("builtins.open", unittest.mock.mock_open(read_data=b"fake-mp4-bytes")):
            props = build_motion_props(text="اختبار ريندر")
            result = render_motion_video(props)

            self.assertTrue(result["success"])
            self.assertEqual(result["video_url"], "https://hexmedia-assets.test/motion/test.mp4")
            self.assertEqual(result["download_url"], "https://hexmedia-assets.test/motion/test.mp4")
            self.assertIn("motion_", result["s3_key"])

    def test_generate_word_timestamps_edge_case_durations(self):
        """Verifies no inverted start/end timestamps even for tiny or boundary durations."""
        test_durations = [0.1, 0.3, 0.5, 0.8, 1.0, 15.0]
        for dur in test_durations:
            words = generate_word_timestamps("كلمة واحدة كلمة ثانية اختبار", duration_seconds=dur)
            self.assertGreater(len(words), 0)
            for w in words:
                self.assertGreaterEqual(
                    w["end"],
                    w["start"],
                    f"Timestamp inversion detected at dur={dur}: {w}"
                )

    @patch("ai_studio.services.motion_service.subprocess.run")
    @patch("ai_studio.services.motion_service.upload_bytes")
    def test_render_motion_video_snake_case_normalization(self, mock_upload, mock_run):
        """Verifies props with snake_case keys are normalized and properly passed to Remotion."""
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        mock_upload.return_value = "https://hexmedia-assets.test/motion/test_snake.mp4"

        with patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=2048), \
             patch("builtins.open", unittest.mock.mock_open(read_data=b"fake-bytes")):
            props = {
                "text": "فيديو تجريبي بتنسيق سنيك كيس",
                "aspect_ratio": "16:9",
                "template_id": "clean_corporate",
                "duration_seconds": 3.5,
            }
            result = render_motion_video(props)
            self.assertTrue(result["success"])
            self.assertEqual(result["aspect_ratio"], "16:9")
            self.assertEqual(result["template_id"], "clean_corporate")
            self.assertEqual(result["duration_seconds"], 3.5)
            self.assertEqual(result["composition_id"], "MotionStudio-Dynamic-16-9")

    @patch("ai_studio.services.motion_service.subprocess.run")
    def test_render_motion_video_cli_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Node syntax error")
        props = build_motion_props(text="اختبار فشل")
        result = render_motion_video(props)
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_build_motion_props_with_video_and_transitions(self):
        props = build_motion_props(
            text="نصوص فوق فيديو",
            background_url="https://assets.test/sample.mp4",
            video_start_offset=2.5,
            video_volume=0.20,
            video_muted=True,
            transition_effect="whip_pan",
        )
        self.assertEqual(props["backgroundType"], "video")
        self.assertEqual(props["videoStartOffset"], 2.5)
        self.assertEqual(props["videoVolume"], 0.20)
        self.assertTrue(props["videoMuted"])
        self.assertEqual(props["transitionEffect"], "whip_pan")

    def test_save_uploaded_video_invalid_format(self):
        fake_file = MagicMock()
        fake_file.name = "audio.mp3"
        fake_file.size = 1024
        result = save_uploaded_video(fake_file)
        self.assertFalse(result["success"])
        self.assertIn("غير مدعومة", result["error"])

    @patch("ai_studio.services.motion_service.probe_video_metadata")
    @patch("ai_studio.services.motion_service.upload_bytes")
    def test_save_uploaded_video_success(self, mock_upload, mock_probe):
        mock_probe.return_value = {"duration": 12.4, "width": 1080, "height": 1920, "has_audio": True}
        mock_upload.return_value = "https://assets.test/motion/videos/uploaded.mp4"

        fake_file = MagicMock()
        fake_file.name = "my_story.mp4"
        fake_file.size = 2048
        fake_file.read.return_value = b"fake-video-content"

        result = save_uploaded_video(fake_file)
        self.assertTrue(result["success"])
        self.assertEqual(result["duration"], 12.4)
        self.assertEqual(result["width"], 1080)
        self.assertEqual(result["height"], 1920)
        self.assertTrue(result["has_audio"])
        self.assertIn("https://assets.test/motion/videos/uploaded.mp4", result["url"])

    def test_ingest_video_url_invalid_url(self):
        result = ingest_video_url("ftp://invalid-domain.com/vid.mp4")
        self.assertFalse(result["success"])
        self.assertIn("غير صالح", result["error"])

    @patch("ai_studio.services.motion_service.probe_video_metadata")
    @patch("ai_studio.services.motion_service.upload_bytes")
    @patch("requests.get")
    def test_ingest_video_url_direct_video(self, mock_get, mock_upload, mock_probe):
        mock_resp = MagicMock()
        mock_resp.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value.__enter__.return_value = mock_resp

        mock_probe.return_value = {"duration": 8.0, "width": 1920, "height": 1080, "has_audio": False}
        mock_upload.return_value = "https://assets.test/motion/videos/direct.mp4"

        result = ingest_video_url("https://example.com/clips/nature.mp4")
        self.assertTrue(result["success"])
        self.assertEqual(result["duration"], 8.0)
        self.assertEqual(result["url"], "https://assets.test/motion/videos/direct.mp4")

    @patch("ai_studio.services.motion_service.get_gemini_client")
    def test_generate_viral_script_gemini(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "title": "أسرار الفيروسية",
            "hook": "هل تعلم هذا السر؟",
            "body": "الذكاء الاصطناعي يغير كل شيء في ثوانٍ",
            "call_to_action": "تابعنا للمزيد",
            "full_script": "هل تعلم هذا السر؟ الذكاء الاصطناعي يغير كل شيء في ثوانٍ. تابعنا للمزيد!",
            "estimated_duration": 6.5
        })
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_config = MagicMock()
        mock_config.llm_model = "gemini-3.8-flash"
        mock_get_client.return_value = (mock_client, mock_config)

        result = generate_viral_script(topic="الذكاء الاصطناعي في 2026", tone="viral")
        self.assertTrue(result["success"])
        self.assertEqual(result["title"], "أسرار الفيروسية")
        self.assertIn("الذكاء الاصطناعي", result["script"])
        self.assertEqual(result["estimated_duration"], 6.5)

    @patch("ai_studio.services.motion_service.get_gemini_client")
    def test_generate_viral_script_fallback(self, mock_get_client):
        mock_get_client.return_value = (None, None)
        result = generate_viral_script(topic="إدارة الوقت والإنتاجية", tone="educational")
        self.assertTrue(result["success"])
        self.assertIn("إدارة الوقت والإنتاجية", result["script"])
        self.assertGreater(result["estimated_duration"], 0)

    @patch("ai_studio.services.motion_service.get_gemini_client")
    def test_generate_viral_script_gemini_markdown_with_commentary(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.text = (
            "Here is the generated script:\n```json\n"
            + json.dumps({
                "title": "ذكاء خارق",
                "subtitle": "حصري",
                "hook": "هل جربت هذا بعد؟",
                "body": "التغيير بدأ الآن بالفعل",
                "call_to_action": "تابعنا",
                "full_script": "هل جربت هذا بعد؟ التغيير بدأ الآن بالفعل تابعنا",
                "estimated_duration": 5.0,
            })
            + "\n```\nHope you find this engaging!"
        )
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_config = MagicMock()
        mock_config.llm_model = "gemini-3.8-flash"
        mock_get_client.return_value = (mock_client, mock_config)

        result = generate_viral_script(topic="الذكاء في العمل")
        self.assertTrue(result["success"])
        self.assertEqual(result["title"], "ذكاء خارق")
        self.assertEqual(result["estimated_duration"], 5.0)

    @patch("ai_studio.services.motion_service.get_gemini_client")
    def test_generate_viral_script_empty_topic(self, mock_get_client):
        mock_get_client.return_value = (None, None)
        result = generate_viral_script(topic="   ")
        self.assertTrue(result["success"])
        self.assertIn("الذكاء الاصطناعي", result["topic"])

    @patch("ai_studio.services.motion_service.generate_voice_audio")
    @patch("tts.services.audio_stitcher.convert_to_mp3")
    @patch("ai_studio.services.motion_service.upload_bytes")
    def test_synthesize_motion_speech(self, mock_upload, mock_convert, mock_voice_gen):
        # 44-byte minimal valid WAV header
        mock_voice_gen.return_value = b"RIFF\x28\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x04\x00\x00\x00\x00\x00\x00\x00"
        mock_convert.return_value = b"fake-mp3-bytes"
        mock_upload.return_value = "https://assets.test/motion/audio/tts_sample.mp3"

        result = synthesize_motion_speech(text="مرحبا بكم في أستوديو هيكس ميديا", voice_profile="alloy")
        self.assertTrue(result["success"])
        self.assertEqual(result["audio_url"], "https://assets.test/motion/audio/tts_sample.mp3")
        self.assertGreater(result["duration"], 0)
        self.assertEqual(result["voice_id"], "alloy")

    def test_synthesize_motion_speech_empty_text(self):
        result = synthesize_motion_speech(text="   ")
        self.assertFalse(result["success"])
        self.assertIn("فارغ", result["error"])

    def test_build_motion_props_continuous_caption_positions(self):
        for pos in [15, 25, 42, 50, 68, 75, 85]:
            props = build_motion_props(caption_position_percent=pos)
            self.assertEqual(props["captionPositionPercent"], float(pos))

    def test_build_motion_props_all_enhancements(self):
        props = build_motion_props(
            text="نصوص متطورة مع مؤثرات وموسيقى خلفية وتكبير ديناميكي",
            font_family="Cairo",
            entry_animation="bounce",
            smart_emojis_enabled=True,
            word_glow_box=True,
            sfx_enabled=True,
            sfx_volume=0.75,
            bgm_preset="cinematic_warm",
            bgm_url="https://assets.test/bgm.mp3",
            bgm_volume=0.35,
            smart_ducking=True,
            dynamic_zoom=True,
            caption_position_percent=75,
            export_format="gif",
            scenes=[{"url": "https://assets.test/s1.mp4", "duration": 4.0}],
            pip_url="https://assets.test/pip.mp4",
            pip_position="bottom-left",
            pip_scale=0.3,
            pip_muted=False,
        )
        self.assertEqual(props["fontFamily"], "Cairo")
        self.assertEqual(props["entryAnimation"], "bounce")
        self.assertTrue(props["smartEmojisEnabled"])
        self.assertTrue(props["wordGlowBox"])
        self.assertTrue(props["sfxEnabled"])
        self.assertEqual(props["sfxVolume"], 0.75)
        self.assertEqual(props["bgmPreset"], "cinematic_warm")
        self.assertEqual(props["bgmUrl"], "https://assets.test/bgm.mp3")
        self.assertEqual(props["bgmVolume"], 0.35)
        self.assertTrue(props["smartDucking"])
        self.assertTrue(props["dynamicZoom"])
        self.assertEqual(props["captionPositionPercent"], 75)
        self.assertEqual(props["exportFormat"], "gif")
        self.assertEqual(len(props["scenes"]), 1)
        self.assertEqual(props["pipUrl"], "https://assets.test/pip.mp4")
        self.assertEqual(props["pipPosition"], "bottom-left")
        self.assertEqual(props["pipScale"], 0.3)
        self.assertFalse(props["pipMuted"])

    @patch("ai_studio.services.motion_service.subprocess.run")
    @patch("ai_studio.services.motion_service.upload_bytes")
    def test_render_motion_video_with_60fps(self, mock_upload, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        mock_upload.return_value = "https://hexmedia-assets.test/motion/test_60fps.mp4"

        with patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=4096), \
             patch("builtins.open", unittest.mock.mock_open(read_data=b"fake-bytes")):
            props = build_motion_props(text="اختبار 60 إطار بالثانية")
            result = render_motion_video(props, fps=60)
            self.assertTrue(result["success"])
            self.assertEqual(result["fps"], 60)
            # Check CLI command contains 60 fps props
            args, kwargs = mock_run.call_args
            cmd_str = " ".join(args[0])
            self.assertIn("props.json", cmd_str)

    @patch("ai_studio.services.motion_service.subprocess.run")
    @patch("ai_studio.services.motion_service.upload_bytes")
    def test_render_motion_video_gif_export(self, mock_upload, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        mock_upload.return_value = "https://hexmedia-assets.test/motion/test_animated.gif"

        with patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=8192), \
             patch("builtins.open", unittest.mock.mock_open(read_data=b"fake-gif-bytes")):
            props = build_motion_props(text="اختبار تصدير صورة متحركة", export_format="gif")
            result = render_motion_video(props, export_format="gif")
            self.assertTrue(result["success"])
            self.assertEqual(result["format"], "gif")
            self.assertTrue(result["video_url"].endswith(".gif"))
            # Ensure upload was called with image/gif content type
            upload_kwargs = mock_upload.call_args[1]
            self.assertEqual(upload_kwargs.get("content_type"), "image/gif")


class MotionApiTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_motion_templates_endpoint(self):
        res = self.client.get("/api/motion/templates")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("templates", data)
        self.assertIn("aspect_ratios", data)
        self.assertIn("default_sample_words", data)
        tpl_ids = [t["id"] for t in data["templates"]]
        self.assertIn("dark_neon", tpl_ids)
        self.assertIn("tiktok_kinetic", tpl_ids)
        self.assertIn("cinematic_narrative", tpl_ids)
        self.assertIn("clean_corporate", tpl_ids)

    def test_generate_motion_config_endpoint(self):
        payload = {
            "text": "فيديو تفاعلي سريع ومبهر",
            "title": "HexMedia Studio",
            "template_id": "clean_corporate",
            "aspect_ratio": "16:9",
            "duration_seconds": 3.0,
        }
        res = self.client.post(
            "/api/motion/config",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["aspect_ratio"], "16:9")
        self.assertEqual(data["template_id"], "clean_corporate")
        self.assertEqual(data["word_count"], 4)
        self.assertEqual(data["props"]["templateId"], "clean_corporate")
        self.assertEqual(data["props"]["aspectRatio"], "16:9")

    @patch("ai_studio.services.motion_service.render_motion_video")
    def test_render_motion_endpoint_mock(self, mock_render):
        mock_render.return_value = {
            "success": True,
            "video_url": "https://hexmedia-assets.test/motion/rendered_video.mp4",
            "download_url": "https://hexmedia-assets.test/motion/rendered_video.mp4",
            "duration_seconds": 4.0,
            "aspect_ratio": "9:16",
            "template_id": "dark_neon",
            "file_size": 204800,
        }
        payload = {
            "text": "تجربة تصدير الريندر",
            "template_id": "dark_neon",
            "aspect_ratio": "9:16",
        }
        res = self.client.post(
            "/api/motion/render",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["video_url"], "https://hexmedia-assets.test/motion/rendered_video.mp4")
        self.assertEqual(data["download_url"], "https://hexmedia-assets.test/motion/rendered_video.mp4")

    @patch("ai_studio.services.motion_service.render_motion_video")
    def test_render_motion_endpoint_error_handling(self, mock_render):
        mock_render.return_value = {
            "success": False,
            "error": "Render process crashed"
        }
        payload = {"text": "فشل"}
        res = self.client.post(
            "/api/motion/render",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 500)

    @patch("ai_studio.services.motion_service.save_uploaded_video")
    def test_upload_motion_video_endpoint(self, mock_save):
        mock_save.return_value = {
            "success": True,
            "url": "https://assets.test/motion/videos/uploaded_file.mp4",
            "duration": 15.0,
            "width": 1080,
            "height": 1920,
            "has_audio": True,
        }
        from django.core.files.uploadedfile import SimpleUploadedFile
        fake_video = SimpleUploadedFile("reel.mp4", b"dummy-bytes", content_type="video/mp4")
        res = self.client.post("/api/motion/upload-video", {"file": fake_video})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["duration"], 15.0)
        self.assertEqual(data["url"], "https://assets.test/motion/videos/uploaded_file.mp4")

    @patch("ai_studio.services.motion_service.ingest_video_url")
    def test_fetch_motion_video_url_endpoint(self, mock_ingest):
        mock_ingest.return_value = {
            "success": True,
            "url": "https://assets.test/motion/videos/fetched_yt.mp4",
            "title": "Amazing Motion Graphics",
            "duration": 20.0,
            "width": 1920,
            "height": 1080,
        }
        res = self.client.post(
            "/api/motion/fetch-video-url",
            data=json.dumps({"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["duration"], 20.0)
        self.assertEqual(data["title"], "Amazing Motion Graphics")

    @patch("ai_studio.services.motion_service.generate_viral_script")
    def test_generate_script_endpoint(self, mock_script_gen):
        mock_script_gen.return_value = {
            "success": True,
            "title": "3 نصائح لرواد الأعمال",
            "hook": "كيف تبدأ مشروعك بنجاح؟",
            "body": "الخطوة الأولى هي التخطيط الذكي",
            "call_to_action": "اشترك لمزيد من النصائح",
            "script": "كيف تبدأ مشروعك بنجاح؟ الخطوة الأولى هي التخطيط الذكي. اشترك لمزيد من النصائح!",
            "estimated_duration": 5.5,
        }
        res = self.client.post(
            "/api/motion/generate-script",
            data=json.dumps({"topic": "ريادة الأعمال", "tone": "viral", "estimated_duration": 5.5}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["title"], "3 نصائح لرواد الأعمال")
        self.assertIn("التخطيط الذكي", data["script"])
        self.assertEqual(data["estimated_duration"], 5.5)

    def test_get_motion_voices_endpoint(self):
        res = self.client.get("/api/motion/voices")
        self.assertEqual(res.status_code, 200)
        voices = res.json()
        self.assertIsInstance(voices, list)
        self.assertGreater(len(voices), 0)
        v_ids = [v["id"] for v in voices]
        self.assertIn("alloy", v_ids)
        self.assertIn("echo", v_ids)

    @patch("ai_studio.services.motion_service.synthesize_motion_speech")
    def test_motion_tts_endpoint(self, mock_tts):
        mock_tts.return_value = {
            "success": True,
            "audio_url": "https://assets.test/motion/audio/tts_gen.mp3",
            "duration": 4.8,
            "voice_id": "onyx",
        }
        res = self.client.post(
            "/api/motion/tts",
            data=json.dumps({"text": "تجربة تحويل النص إلى صوت", "voice_id": "onyx", "speed": 1.0}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["audio_url"], "https://assets.test/motion/audio/tts_gen.mp3")
        self.assertEqual(data["duration"], 4.8)
        self.assertEqual(data["voice_id"], "onyx")

    def test_generate_motion_config_with_all_enhancements(self):
        payload = {
            "text": "نصوص تجريبية مع تحسينات شاملة",
            "font_family": "Cairo",
            "entry_animation": "bounce",
            "smart_emojis_enabled": True,
            "word_glow_box": True,
            "sfx_enabled": True,
            "bgm_preset": "cyber_ambient",
            "smart_ducking": True,
            "dynamic_zoom": True,
            "caption_position_percent": 75,
            "export_format": "gif",
        }
        res = self.client.post(
            "/api/motion/config",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        props = data["props"]
        self.assertEqual(props["fontFamily"], "Cairo")
        self.assertEqual(props["entryAnimation"], "bounce")
        self.assertTrue(props["smartEmojisEnabled"])
        self.assertTrue(props["wordGlowBox"])
        self.assertTrue(props["sfxEnabled"])
        self.assertEqual(props["bgmPreset"], "cyber_ambient")
        self.assertTrue(props["smartDucking"])
        self.assertTrue(props["dynamicZoom"])
        self.assertEqual(props["captionPositionPercent"], 75)
        self.assertEqual(props["exportFormat"], "gif")

    @patch("ai_studio.services.motion_service.render_motion_video")
    def test_render_motion_endpoint_with_fps_and_gif(self, mock_render):
        mock_render.return_value = {
            "success": True,
            "video_url": "https://hexmedia-assets.test/motion/rendered_gif.gif",
            "download_url": "https://hexmedia-assets.test/motion/rendered_gif.gif",
            "duration_seconds": 3.0,
            "aspect_ratio": "9:16",
            "template_id": "tiktok_kinetic",
            "format": "gif",
            "fps": 60,
        }
        payload = {
            "template_id": "tiktok_kinetic",
            "aspect_ratio": "9:16",
            "fps": 60,
            "export_format": "gif",
            "props": {"text": "تصدير GIF بدقة 60 إطار"},
        }
        res = self.client.post(
            "/api/motion/render",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["fps"], 60)
        self.assertEqual(data["format"], "gif")
        self.assertEqual(data["video_url"], "https://hexmedia-assets.test/motion/rendered_gif.gif")


class MotionUiTestCase(TestCase):
    def setUp(self):
        with open("backend/templates/chat/index.html", "r", encoding="utf-8") as f:
            self.html = f.read()

    def test_tools_menu_has_motion_studio_button(self):
        """toolsMenu should include the Motion Studio trigger button."""
        self.assertIn("openMotionStudioModal()", self.html)
        self.assertIn("أستوديو الموشن جرافيكس", self.html)

    def test_motion_studio_modal_elements_exist(self):
        """motionStudioModal should contain all required controls and preview elements."""
        self.assertIn('id="motionStudioModal"', self.html)
        self.assertIn('id="motionTextInput"', self.html)
        self.assertIn('id="motionTitleInput"', self.html)
        self.assertIn('id="motionSubtitleInput"', self.html)
        self.assertIn('id="motionSpeakerInput"', self.html)
        # Template cards
        self.assertIn('id="tplCard_dark_neon"', self.html)
        self.assertIn('id="tplCard_tiktok_kinetic"', self.html)
        self.assertIn('id="tplCard_cinematic_narrative"', self.html)
        self.assertIn('id="tplCard_clean_corporate"', self.html)
        # Aspect ratios 9:16 and 16:9
        self.assertIn('id="aspectBtn_9_16"', self.html)
        self.assertIn('id="aspectBtn_16_9"', self.html)
        # Live preview container and stage
        self.assertIn('id="motionPreviewContainer"', self.html)
        self.assertIn('id="motionPreviewStage"', self.html)
        self.assertIn('id="motionWordsBox"', self.html)
        # Export elements
        self.assertIn('id="motionExportMP4Btn"', self.html)
        self.assertIn('id="motionResultVideo"', self.html)
        self.assertIn('id="motionResultImg"', self.html)
        self.assertIn('id="motionDownloadLink"', self.html)
        # Video ingestion & montage elements
        self.assertIn('id="motionVideoFileInput"', self.html)
        self.assertIn('id="motionVideoUrlInput"', self.html)
        self.assertIn('id="motionFetchUrlBtn"', self.html)
        self.assertIn('id="motionAttachedVideoCard"', self.html)
        self.assertIn('id="motionMontageControls"', self.html)
        self.assertIn('id="motionTrimSlider"', self.html)
        self.assertIn('id="stageBgVideo"', self.html)
        # Transition FX elements
        self.assertIn('id="motionFx_zoom_in"', self.html)
        self.assertIn('id="motionFx_whip_pan"', self.html)
        self.assertIn('id="motionFx_glitch"', self.html)
        self.assertIn('id="motionFx_dissolve"', self.html)
        # Enhanced Kinetic Typography, Audio & TTS controls
        self.assertIn('id="motionAiScriptBox"', self.html)
        self.assertIn('id="motionAiTopicInput"', self.html)
        self.assertIn('id="motionRunAiScriptBtn"', self.html)
        self.assertIn('id="motionFontSelect"', self.html)
        self.assertIn('id="motionEntryAnimationSelect"', self.html)
        self.assertIn('id="motionSmartEmojisToggle"', self.html)
        self.assertIn('id="motionWordGlowToggle"', self.html)
        self.assertIn('id="motionDynamicZoomToggle"', self.html)
        self.assertIn('id="motionSfxToggle"', self.html)
        self.assertIn('id="motionCaptionPosSlider"', self.html)
        self.assertIn('id="motionTtsVoiceSelect"', self.html)
        self.assertIn('id="motionGenerateTtsBtn"', self.html)
        self.assertIn('id="motionBgmSelect"', self.html)
        self.assertIn('id="motionSmartDuckingToggle"', self.html)
        self.assertIn('id="motionFps_30"', self.html)
        self.assertIn('id="motionFps_60"', self.html)
        self.assertIn('id="motionFormat_mp4"', self.html)
        self.assertIn('id="motionFormat_gif"', self.html)

    def test_motion_studio_javascript_functions_exist(self):
        """index.html must define the controller functions for Motion Studio."""
        self.assertIn("function openMotionStudioModal()", self.html)
        self.assertIn("function closeMotionStudioModal()", self.html)
        self.assertIn("function selectMotionTemplate(", self.html)
        self.assertIn("function selectMotionAspectRatio(", self.html)
        self.assertIn("function selectMotionVideoSource(", self.html)
        self.assertIn("function handleMotionVideoFileSelected(", self.html)
        self.assertIn("function fetchMotionVideoFromUrl(", self.html)
        self.assertIn("function handleMotionTrimChange(", self.html)
        self.assertIn("function selectMotionAudioMode(", self.html)
        self.assertIn("function selectMotionTransitionFx(", self.html)
        self.assertIn("function syncMotionConfigFromInputs()", self.html)
        self.assertIn("function exportMotionVideoMP4()", self.html)
        self.assertIn("function sendMotionVideoToChat()", self.html)
        self.assertIn("function toggleMotionAiScriptBox()", self.html)
        self.assertIn("function generateMotionAiScript()", self.html)
        self.assertIn("function loadMotionVoices()", self.html)
        self.assertIn("function synthesizeMotionTTS()", self.html)
        self.assertIn("function handleMotionFontChange(", self.html)
        self.assertIn("function handleMotionEntryAnimationChange(", self.html)
        self.assertIn("function handleMotionToggleChange()", self.html)
        self.assertIn("function selectMotionCaptionPosPreset(", self.html)
        self.assertIn("function handleMotionCaptionPosSlider(", self.html)
        self.assertIn("function handleMotionBgmChange(", self.html)
        self.assertIn("function selectMotionFps(", self.html)
        self.assertIn("function selectMotionExportFormat(", self.html)
        self.assertIn("MOTION_STUDIO_CARD", self.html)

