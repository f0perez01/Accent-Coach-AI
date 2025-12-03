"""
In-Memory Repository Implementations

For fast testing without external dependencies.
"""

from typing import List, Dict
from datetime import datetime
from .repositories import (
    PronunciationRepository,
    ConversationRepository,
    WritingRepository,
    ActivityRepository,
)


class InMemoryPronunciationRepository(PronunciationRepository):
    """
    In-memory implementation for testing.

    Fast, no external dependencies, perfect for unit tests.
    """

    def __init__(self):
        self._storage: Dict[str, List] = {}
        self._counter = 0

    def save_analysis(
        self, user_id: str, reference_text: str, analysis
    ) -> str:
        """Save pronunciation analysis to in-memory storage."""
        if user_id not in self._storage:
            self._storage[user_id] = []

        self._counter += 1
        doc_id = f"doc_{self._counter}"

        # Store as dict for easy retrieval
        self._storage[user_id].append({
            "doc_id": doc_id,
            "reference_text": reference_text,
            "analysis": analysis,
            "timestamp": datetime.now(),
        })

        return doc_id

    def get_user_history(self, user_id: str, limit: int = 50) -> List:
        """Get user history from in-memory storage."""
        if user_id not in self._storage:
            return []

        # Return most recent first
        history = self._storage[user_id][-limit:]
        return [item["analysis"] for item in reversed(history)]

    def clear(self):
        """Clear all data (useful for test cleanup)."""
        self._storage.clear()
        self._counter = 0


class InMemoryConversationRepository(ConversationRepository):
    """In-memory implementation for testing."""

    def __init__(self):
        self._sessions: Dict[str, List] = {}

    def save_turn(self, session_id: str, turn) -> None:
        """Save conversation turn to in-memory storage."""
        if session_id not in self._sessions:
            self._sessions[session_id] = []

        self._sessions[session_id].append({
            "turn": turn,
            "timestamp": datetime.now(),
        })

    def get_session_history(self, session_id: str) -> List:
        """Get session history from in-memory storage."""
        if session_id not in self._sessions:
            return []

        return [item["turn"] for item in self._sessions[session_id]]

    def clear(self):
        """Clear all data."""
        self._sessions.clear()


class InMemoryWritingRepository(WritingRepository):
    """In-memory implementation for testing."""

    def __init__(self):
        self._storage: Dict[str, List] = {}
        self._counter = 0

    def save_evaluation(
        self, user_id: str, text: str, evaluation
    ) -> str:
        """Save writing evaluation to in-memory storage."""
        if user_id not in self._storage:
            self._storage[user_id] = []

        self._counter += 1
        doc_id = f"doc_{self._counter}"

        self._storage[user_id].append({
            "doc_id": doc_id,
            "text": text,
            "evaluation": evaluation,
            "timestamp": datetime.now(),
        })

        return doc_id

    def clear(self):
        """Clear all data."""
        self._storage.clear()
        self._counter = 0


class InMemoryActivityRepository(ActivityRepository):
    """In-memory implementation for testing."""

    def __init__(self):
        self._activities: List = []

    def log_activity(self, activity) -> None:
        """Log activity to in-memory storage."""
        self._activities.append(activity)

    def get_today_activities(self, user_id: str, date: datetime) -> List:
        """Get activities for specific date from in-memory storage."""
        # Filter by user_id and date (same day)
        return [
            activity
            for activity in self._activities
            if activity.user_id == user_id
            and activity.timestamp.date() == date.date()
        ]

    def clear(self):
        """Clear all data."""
        self._activities.clear()
