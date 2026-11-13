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
    SUPPORTED_TEMPLATES,
    SUPPORTED_ASPECT_RATIOS,
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
        self.assertIn('id="motionDownloadLink"', self.html)

    def test_motion_studio_javascript_functions_exist(self):
        """index.html must define the controller functions for Motion Studio."""
        self.assertIn("function openMotionStudioModal()", self.html)
        self.assertIn("function closeMotionStudioModal()", self.html)
        self.assertIn("function selectMotionTemplate(", self.html)
        self.assertIn("function selectMotionAspectRatio(", self.html)
        self.assertIn("function syncMotionConfigFromInputs()", self.html)
        self.assertIn("function exportMotionVideoMP4()", self.html)
        self.assertIn("function sendMotionVideoToChat()", self.html)
        self.assertIn("MOTION_STUDIO_CARD", self.html)

