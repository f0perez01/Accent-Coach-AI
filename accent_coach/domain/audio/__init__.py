"""
BC1: Audio Processing & Enhancement

Responsibilities:
- Validate audio input
- Enhance audio quality (denoising, VAD)
- Convert audio formats
- Generate TTS audio

Dependencies: NONE (pure processing)
"""

from .service import AudioService, AudioValidationError
from .models import AudioConfig, ProcessedAudio
from .audio_processor import AudioProcessor, TTSGenerator, AudioValidator

__all__ = [
    "AudioService",
    "AudioValidationError",
    "AudioConfig",
    "ProcessedAudio",
    "AudioProcessor",
    "TTSGenerator",
    "AudioValidator",
]
