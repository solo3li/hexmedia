import io
import uuid
import wave
import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from stt.models import STTJob
from stt.services.stt_engine import (
    format_seconds_to_srt,
    build_srt_from_segments,
    estimate_audio_duration,
    generate_fallback_transcript,
    process_stt_transcription
)
from core.models import ChatThread, ChatMessage


def make_dummy_wav(duration_sec=2.0, sample_rate=8000) -> bytes:
    """Generate minimal valid PCM WAV bytes."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        total_frames = int(duration_sec * sample_rate)
        wf.writeframes(b'\x00\x00' * total_frames)
    return buf.getvalue()


@pytest.mark.django_db
class STTUnitTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="stt_user_1", password="password123")
        self.user2 = User.objects.create_user(username="stt_user_2", password="password123")
        self.client1 = Client()
        self.client1.force_login(self.user1)
        self.client2 = Client()
        self.client2.force_login(self.user2)

    def test_format_seconds_to_srt(self):
        self.assertEqual(format_seconds_to_srt(0.0), "00:00:00,000")
        self.assertEqual(format_seconds_to_srt(65.45), "00:01:05,450")
        self.assertEqual(format_seconds_to_srt(3661.123), "01:01:01,123")

    def test_build_srt_from_segments(self):
        segments = [
            {"speaker": "متحدث 1", "start": 0.0, "end": 4.5, "text": "مرحباً بكم في هيكس ميديا"},
            {"speaker": "متحدث 2", "start": 4.5, "end": 9.0, "text": "استوديو تفريغ الصوت والترجمة"}
        ]
        srt = build_srt_from_segments(segments)
        self.assertIn("1\n00:00:00,000 --> 00:00:04,500\nمتحدث 1: مرحباً بكم في هيكس ميديا", srt)
        self.assertIn("2\n00:00:04,500 --> 00:00:09,000\nمتحدث 2: استوديو تفريغ الصوت والترجمة", srt)

    def test_estimate_audio_duration(self):
        wav_bytes = make_dummy_wav(3.0)
        dur = estimate_audio_duration(wav_bytes, "test.wav")
        self.assertAlmostEqual(dur, 3.0, places=1)

    def test_generate_fallback_transcript(self):
        res = generate_fallback_transcript(
            duration=12.0,
            language="ar",
            target_language="",
            diarization=True,
            timestamps=True
        )
        self.assertIn("transcript_text", res)
        self.assertIn("srt_content", res)
        self.assertTrue(len(res["diarization_data"]) > 0)
        self.assertIn("متحدث 1", res["transcript_text"])
        self.assertIn("00:00:00", res["srt_content"])

    def test_process_stt_transcription(self):
        wav_bytes = make_dummy_wav(2.0)
        res = process_stt_transcription(
            audio_bytes=wav_bytes,
            filename="meeting.wav",
            content_type="audio/wav",
            language="ar",
            target_language="en",
            diarization=True,
            timestamps=True
        )
        self.assertTrue(res["duration_seconds"] > 0)
        self.assertTrue(bool(res["transcript_text"]))
        self.assertTrue(bool(res["srt_content"]))
        self.assertTrue(res["audio_url"].startswith("/media/") or "http" in res["audio_url"])

    def test_stt_job_model(self):
        job = STTJob.objects.create(
            user=self.user1,
            title="جلسة حوارية",
            audio_url="/media/test.wav",
            language="ar",
            target_language="en",
            transcript_text="نص مفرغ",
            srt_content="1\n00:00:00,000 --> 00:00:02,000\nنص مفرغ",
            duration_seconds=2.0,
            has_diarization=True,
            has_timestamps=True
        )
        self.assertEqual(str(job), f"[stt_user_1] جلسة حوارية (2.0s)")
        self.assertEqual(job.status, "READY")

    def test_stt_options_endpoint(self):
        res = self.client1.get("/api/stt/options")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["model"], "gemini-3.5-transcribe")
        self.assertTrue(any(l["code"] == "ar" for l in data["languages"]))
        self.assertTrue(any(l["code"] == "auto" for l in data["languages"]))
        self.assertTrue(any(l["code"] == "en" for l in data["target_languages"]))

    def test_stt_transcribe_endpoint(self):
        wav_bytes = make_dummy_wav(2.5)
        file = SimpleUploadedFile("interview.wav", wav_bytes, content_type="audio/wav")
        payload = {
            "audio_file": file,
            "title": "مقابلة حصرية",
            "language": "ar",
            "target_language": "en",
            "diarization": "true",
            "timestamps": "true"
        }
        res = self.client1.post("/api/stt/transcribe", payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["title"], "مقابلة حصرية")
        self.assertTrue(data["duration_seconds"] > 0)
        self.assertTrue(data["has_diarization"])
        self.assertTrue(data["has_timestamps"])
        self.assertTrue(len(data["transcript_text"]) > 0)
        self.assertTrue(len(data["srt_content"]) > 0)

        # Database record created
        db_job = STTJob.objects.get(id=data["id"])
        self.assertEqual(db_job.user, self.user1)

    def test_stt_history_user_isolation(self):
        STTJob.objects.create(
            user=self.user1,
            title="ملف سري للمستخدم 1",
            audio_url="/media/u1.wav",
            transcript_text="بيانات المستخدم الأول"
        )
        STTJob.objects.create(
            user=self.user2,
            title="ملف سري للمستخدم 2",
            audio_url="/media/u2.wav",
            transcript_text="بيانات المستخدم الثاني"
        )

        # User 1 history
        res1 = self.client1.get("/api/stt/history")
        self.assertEqual(res1.status_code, 200)
        data1 = res1.json()
        self.assertEqual(len(data1), 1)
        self.assertEqual(data1[0]["title"], "ملف سري للمستخدم 1")

        # User 2 history
        res2 = self.client2.get("/api/stt/history")
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertEqual(len(data2), 1)
        self.assertEqual(data2[0]["title"], "ملف سري للمستخدم 2")

    def test_voice_chat_endpoint(self):
        wav_bytes = make_dummy_wav(1.5)
        file = SimpleUploadedFile("mic.webm", wav_bytes, content_type="audio/webm")
        res = self.client1.post("/api/voice-chat", {"audio_file": file})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("response", data)
        self.assertIn("user_transcript", data)
        self.assertIn("audio_url", data)
        self.assertIn("thread_id", data)

        # Verify chat thread and messages
        thread = ChatThread.objects.get(id=data["thread_id"])
        self.assertEqual(thread.user, self.user1)
        messages = thread.messages.order_by("created_at")
        self.assertEqual(messages.count(), 2)
        user_msg = messages.first()
        asst_msg = messages.last()
        self.assertEqual(user_msg.role, "USER")
        self.assertTrue(user_msg.metadata.get("is_voice_message"))
        self.assertEqual(asst_msg.role, "ASSISTANT")

    def test_frontend_ui_elements(self):
        res = self.client1.get("/")
        self.assertEqual(res.status_code, 200)
        content = res.content.decode("utf-8")

        # Voice input dock button and status
        self.assertIn('id="voiceRecordBtn"', content)
        self.assertIn('id="voiceRecordStatusPill"', content)
        self.assertIn('toggleQuickVoiceRecord()', content)

        # Tool 5 in Tools menu
        self.assertIn('openSTTConfigModal()', content)
        self.assertIn('تفريغ الصوت والترجمة (STT Studio)', content)

        # STT Modal elements
        self.assertIn('id="sttConfigModal"', content)
        self.assertIn('id="sttSourceLanguageSelect"', content)
        self.assertIn('id="sttTargetLanguageSelect"', content)
        self.assertIn('id="sttDiarizationToggle"', content)
        self.assertIn('id="sttTimestampsToggle"', content)
        self.assertIn('confirmSTTTranscription()', content)

        # JS functions
        self.assertIn('renderSTTAudioCard', content)
        self.assertIn('renderUserAudioBubble', content)
        self.assertIn('copySTTTranscript', content)
        self.assertIn('downloadSTTFile', content)
