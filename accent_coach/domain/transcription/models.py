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
    use_g2p: bool = True  # grapheme-to-phoneme conversion
    language: str = "en-us"  # language code for G2P
    hf_token: Optional[str] = None  # Hugging Face token


@dataclass
class Transcription:
    """Result of speech recognition."""
    text: str
    confidence: float
    phonemes: str = ""  # phoneme representation
    language: str = "en-us"
    word_timestamps: Optional[list] = None
