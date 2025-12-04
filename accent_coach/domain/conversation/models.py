"""
Conversation Tutoring domain models
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict


class ConversationMode(Enum):
    """Conversation mode: immediate vs deferred feedback."""
    PRACTICE = "practice"  # Immediate feedback
    EXAM = "exam"  # Feedback at end


@dataclass
class ConversationConfig:
    """Configuration for conversation practice."""
    mode: ConversationMode = ConversationMode.PRACTICE
    user_level: str = "B1-B2"
    topic: Optional[str] = None
    focus_area: Optional[str] = None  # e.g., "past tense", "prepositions"
    generate_audio: bool = True
    llm_model: str = "llama-3.1-70b-versatile"
    asr_model: str = "facebook/wav2vec2-base-960h"
    sample_rate: int = 16000
    max_history_turns: int = 5  # Context window for LLM


@dataclass
class TutorResponse:
    """Parsed response from LLM tutor."""
    correction: str
    explanation: str
    improved_version: str
    follow_up_question: str
    errors_detected: List[str] = field(default_factory=list)
    assistant_response: str = ""  # Full response text


@dataclass
class TurnResult:
    """Simplified turn result for UI interactions."""
    user_transcript: str
    correction: Optional[str] = None
    follow_up: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConversationTurn:
    """Single turn in a conversation."""
    user_transcript: str
    tutor_response: TutorResponse
    follow_up_audio: Optional[bytes] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "user_transcript": self.user_transcript,
            "correction": self.tutor_response.correction,
            "explanation": self.tutor_response.explanation,
            "improved_version": self.tutor_response.improved_version,
            "follow_up_question": self.tutor_response.follow_up_question,
            "errors_count": len(self.tutor_response.errors_detected),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ConversationSession:
    """Represents a conversation practice session."""
    session_id: str
    user_id: str
    topic: str
    level: str
    mode: ConversationMode
    history: List[ConversationTurn] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    status: str = "active"  # active, completed

    def add_turn(self, turn: ConversationTurn):
        """Add a turn to the conversation history."""
        self.history.append(turn)
        self.last_activity = datetime.now()

    def get_recent_history(self, max_turns: int = 5) -> List[ConversationTurn]:
        """Get recent conversation history for context."""
        return self.history[-max_turns:] if len(self.history) > max_turns else self.history

    def get_stats(self) -> Dict:
        """Calculate session statistics."""
        total_errors = sum(
            len(turn.tutor_response.errors_detected)
            for turn in self.history
        )

        duration_minutes = (self.last_activity - self.started_at).total_seconds() / 60

        return {
            "session_id": self.session_id,
            "total_turns": len(self.history),
            "total_errors": total_errors,
            "avg_errors_per_turn": round(total_errors / len(self.history), 2) if self.history else 0,
            "duration_minutes": round(duration_minutes, 1),
            "topic": self.topic,
            "level": self.level,
            "started_at": self.started_at.isoformat(),
            "status": self.status,
        }

    def to_dict(self) -> Dict:
        """Export session to dictionary for storage."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "topic": self.topic,
            "level": self.level,
            "mode": self.mode.value,
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "status": self.status,
            "history": [turn.to_dict() for turn in self.history],
            "stats": self.get_stats(),
        }
