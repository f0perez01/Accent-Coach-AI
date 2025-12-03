"""
BC3: Phonetic Analysis & IPA

Responsibilities:
- Convert text to phonemes (G2P)
- Align phonemes (Needleman-Wunsch)
- Calculate pronunciation metrics
- Generate IPA educational data
- Suggest drill words

Dependencies: NONE (pure logic)
"""

from .service import PhoneticAnalysisService
from .models import PronunciationAnalysis, PronunciationMetrics, WordComparison
from .analyzer import (
    G2PConverter,
    PhonemeTokenizer,
    PhonemeAligner,
    SequenceAligner,
    MetricsCalculator,
)

__all__ = [
    "PhoneticAnalysisService",
    "PronunciationAnalysis",
    "PronunciationMetrics",
    "WordComparison",
    "G2PConverter",
    "PhonemeTokenizer",
    "PhonemeAligner",
    "SequenceAligner",
    "MetricsCalculator",
]
