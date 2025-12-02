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
    audio_config: AudioConfig = None
    asr_config: ASRConfig = None

    def __post_init__(self):
        if self.audio_config is None:
            self.audio_config = AudioConfig()
        if self.asr_config is None:
            self.asr_config = ASRConfig()


@dataclass
class PracticeResult:
    """Result of pronunciation practice analysis."""
    analysis: PronunciationAnalysis
    llm_feedback: Optional[str]
    raw_decoded: str
    recorded_phoneme_str: str
    audio_array: np.ndarray
    sample_rate: int
    timestamp: datetime
