"""
Conversation Tutoring domain models
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class ConversationMode(Enum):
    """Conversation mode: immediate vs deferred feedback."""
    PRACTICE = "practice"  # Immediate feedback
    EXAM = "exam"  # Feedback at end


@dataclass
class TurnResult:
    """Result of one conversation turn."""
    user_transcript: str
    correction: Optional[str]
    improved_version: Optional[str]
    explanation: Optional[str]
    errors_detected: List[str]
    follow_up_question: str
    follow_up_audio: bytes

    def __post_init__(self):
        if self.errors_detected is None:
            self.errors_detected = []
