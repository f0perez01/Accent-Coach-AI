"""
BC5: Conversation Tutoring

Responsibilities:
- Manage conversation sessions
- Process conversation turns (audio → transcript → feedback → audio)
- Generate tutor feedback with error correction
- Provide contextual follow-up questions
- Support practice vs exam modes

Dependencies: BC1 (Audio), BC2 (Transcription), BC6 (LLM)
"""

from .service import ConversationService, ConversationError
from .models import (
    ConversationMode,
    ConversationConfig,
    ConversationSession,
    ConversationTurn,
    TutorResponse,
)
from .prompts import PromptBuilder
from .starters import ConversationStarters

__all__ = [
    "ConversationService",
    "ConversationError",
    "ConversationMode",
    "ConversationConfig",
    "ConversationSession",
    "ConversationTurn",
    "TutorResponse",
    "PromptBuilder",
    "ConversationStarters",
]
