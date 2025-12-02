"""
Transcription domain models
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ASRConfig:
    """Configuration for ASR (Automatic Speech Recognition)."""
    model_name: str = "facebook/wav2vec2-base-960h"
    device: str = "cpu"  # or "cuda"
    use_lm: bool = False  # language model for better accuracy


@dataclass
class Transcription:
    """Result of speech recognition."""
    text: str
    confidence: float
    word_timestamps: Optional[list] = None
