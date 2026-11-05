"""TTS Services package."""
from .chunker import split_text_into_chunks
from .audio_stitcher import stitch_wav_buffers, convert_to_mp3

__all__ = ['split_text_into_chunks', 'stitch_wav_buffers', 'convert_to_mp3']
