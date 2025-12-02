"""
Phonetic Analysis domain models
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PronunciationMetrics:
    """Pronunciation quality metrics."""
    word_accuracy: float
    phoneme_accuracy: float
    phoneme_error_rate: float
    correct_words: int
    total_words: int
    substitutions: int
    insertions: int
    deletions: int


@dataclass
class WordComparison:
    """Word-level phoneme comparison."""
    word: str
    ref_phonemes: str
    rec_phonemes: str
    match: bool
    phoneme_accuracy: float
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


@dataclass
class IPABreakdown:
    """IPA breakdown for educational purposes."""
    index: int
    word: str
    ipa: str
    hint: str
    audio: Optional[bytes] = None


@dataclass
class PronunciationAnalysis:
    """Complete pronunciation analysis result."""
    metrics: PronunciationMetrics
    per_word_comparison: List[WordComparison]
    ipa_breakdown: List[IPABreakdown]
    unique_symbols: set
    suggested_drill_words: List[str]
