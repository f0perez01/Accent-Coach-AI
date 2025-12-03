"""
Audio domain models
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class AudioConfig:
    """Configuration for audio processing."""
    sample_rate: int = 16000  # target sample rate
    normalize: bool = True  # enable normalization
    enable_enhancement: bool = True
    enable_vad: bool = True
    enable_denoising: bool = True


@dataclass
class ProcessedAudio:
    """Result of audio processing."""
    waveform: np.ndarray
    sample_rate: int
    duration_seconds: float  # duration in seconds
    quality_metrics: Optional[dict] = None
