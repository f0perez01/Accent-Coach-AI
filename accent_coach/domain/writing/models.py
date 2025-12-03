"""
Writing Evaluation domain models
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class QuestionDifficulty(Enum):
    """Interview question difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionCategory(Enum):
    """Interview question categories."""
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    REMOTE_WORK = "remote_work"


@dataclass
class InterviewQuestion:
    """Interview practice question."""
    text: str
    category: QuestionCategory
    difficulty: QuestionDifficulty

    def get_xp_value(self) -> int:
        """Calculate XP points for this question."""
        xp_map = {
            QuestionDifficulty.EASY: 10,
            QuestionDifficulty.MEDIUM: 20,
            QuestionDifficulty.HARD: 40,
        }
        return xp_map[self.difficulty]


@dataclass
class WritingConfig:
    """Configuration for writing evaluation."""
    model: str = "llama-3.1-8b-instant"
    temperature: float = 0.1
    max_tokens: int = 800
    generate_teacher_feedback: bool = True


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
