"""
BC1: Audio Processing & Enhancement

Responsibilities:
- Validate audio input
- Enhance audio quality (denoising, VAD)
- Convert audio formats
- Generate TTS audio

Dependencies: NONE (pure processing)
"""

from .service import AudioService
from .models import AudioConfig, ProcessedAudio

__all__ = ["AudioService", "AudioConfig", "ProcessedAudio"]
