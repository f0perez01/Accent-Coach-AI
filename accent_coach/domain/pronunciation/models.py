"""
Pronunciation Practice domain models
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import numpy as np

from ..audio.models import AudioConfig
from ..transcription.models import ASRConfig
from ..phonetic.models import PronunciationAnalysis


@dataclass
class PracticeConfig:
    """Configuration for pronunciation practice."""
    use_llm_feedback: bool = True
    llm_model: str = "llama-3.1-70b-versatile"
    sample_rate: int = 16000
    normalize_audio: bool = True
    asr_model: str = "facebook/wav2vec2-base-960h"
    use_g2p: bool = True
    language: str = "en-us"


@dataclass
class PracticeResult:
    """Result of pronunciation practice analysis."""
    analysis: PronunciationAnalysis
    llm_feedback: Optional[str]
    raw_decoded: str
    recorded_phoneme_str: str
