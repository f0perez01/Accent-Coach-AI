"""
BC2: Speech Recognition & Transcription

Responsibilities:
- Load and manage ASR models
- Transcribe audio to text
- Optimize GPU/CPU usage

Dependencies: Audio Service (through ProcessedAudio interface)
"""

from .service import TranscriptionService
from .models import ASRConfig, Transcription

__all__ = ["TranscriptionService", "ASRConfig", "Transcription"]
