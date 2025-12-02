"""
BC7: Writing Evaluation

Responsibilities:
- Evaluate written texts
- Generate polished versions
- Calculate CEFR metrics
- Suggest vocabulary expansion

Dependencies: BC6 (LLM), BC1 (Audio for TTS)
"""

from .service import WritingCoachService
from .models import WritingEvaluation, CEFRMetrics

__all__ = ["WritingCoachService", "WritingEvaluation", "CEFRMetrics"]
