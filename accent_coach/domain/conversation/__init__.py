"""
BC5: Conversation Tutoring

Responsibilities:
- Manage conversation sessions
- Generate contextual follow-up questions
- Evaluate user responses
- Provide feedback (practice vs exam mode)

Dependencies: BC2 (Transcription), BC6 (LLM), BC1 (Audio for TTS)
"""

from .service import ConversationTutorService
from .models import ConversationMode, TurnResult

__all__ = ["ConversationTutorService", "ConversationMode", "TurnResult"]
