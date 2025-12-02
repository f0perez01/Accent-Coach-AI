"""
Audio domain models
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class AudioConfig:
    """Configuration for audio processing."""
    enable_enhancement: bool = True
    enable_vad: bool = True
    enable_denoising: bool = True
    target_sample_rate: int = 16000


@dataclass
class ProcessedAudio:
    """Result of audio processing."""
    waveform: np.ndarray
    sample_rate: int
    duration: float
    quality_metrics: Optional[dict] = None
