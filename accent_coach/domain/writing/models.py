"""
Writing Evaluation domain models
"""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class CEFRMetrics:
    """CEFR evaluation metrics."""
    cefr_level: str  # A2, B1-B2, C1-C2
    variety_score: int  # 0-10


@dataclass
class VocabularyExpansion:
    """Vocabulary expansion suggestion."""
    word: str
    ipa: str
    replaces_simple_word: str
    meaning_context: str


@dataclass
class WritingEvaluation:
    """Result of writing evaluation."""
    corrected: str
    improvements: List[str]
    questions: List[str]
    expansion_words: List[VocabularyExpansion]
    metrics: CEFRMetrics

    def __post_init__(self):
        if self.improvements is None:
            self.improvements = []
        if self.questions is None:
            self.questions = []
        if self.expansion_words is None:
            self.expansion_words = []
