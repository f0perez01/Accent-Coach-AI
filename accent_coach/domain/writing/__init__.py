"""
BC7: Writing Evaluation

Responsibilities:
- Evaluate written texts
- Generate polished versions
- Calculate CEFR metrics
- Suggest vocabulary expansion

Dependencies: BC6 (LLM), BC1 (Audio for TTS)
"""

from .service import WritingService
from .models import (
    WritingEvaluation,
    CEFRMetrics,
    VocabularyExpansion,
    WritingConfig,
    InterviewQuestion,
    QuestionCategory,
    QuestionDifficulty,
)

__all__ = [
    "WritingService",
    "WritingEvaluation",
    "CEFRMetrics",
    "VocabularyExpansion",
    "WritingConfig",
    "InterviewQuestion",
    "QuestionCategory",
    "QuestionDifficulty",
]
