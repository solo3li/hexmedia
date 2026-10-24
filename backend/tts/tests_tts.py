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
