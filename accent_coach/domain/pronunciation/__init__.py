"""
BC4: Pronunciation Practice

Responsibilities:
- Orchestrate practice flow (study → record → analyze → feedback)
- Manage practice sessions
- Drilling selective word practice
- Track practice history

Dependencies: BC1 (Audio), BC2 (Transcription), BC3 (Phonetic), BC6 (LLM)
"""

from .service import PronunciationPracticeService
from .models import PracticeConfig, PracticeResult

__all__ = ["PronunciationPracticeService", "PracticeConfig", "PracticeResult"]
