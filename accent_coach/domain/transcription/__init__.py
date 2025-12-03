"""
BC2: Speech Recognition & Transcription

Responsibilities:
- Load and manage ASR models
- Transcribe audio to text
- Optimize GPU/CPU usage

Dependencies: Audio Service (through ProcessedAudio interface)
"""

from .service import TranscriptionService, TranscriptionError
from .models import ASRConfig, Transcription
from .asr_manager import ASRModelManager

__all__ = [
    "TranscriptionService",
    "TranscriptionError",
    "ASRConfig",
    "Transcription",
    "ASRModelManager",
]
