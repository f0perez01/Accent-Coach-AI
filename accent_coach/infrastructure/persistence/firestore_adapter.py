"""
Firestore Repository Implementations

Concrete implementations using Firebase Firestore.
"""

from typing import List
from datetime import datetime
from .repositories import (
    PronunciationRepository,
    ConversationRepository,
    WritingRepository,
    ActivityRepository,
)


class FirestorePronunciationRepository(PronunciationRepository):
    """Firestore implementation of PronunciationRepository."""

    def __init__(self, db):
        """
        Args:
            db: Firestore database client
        """
        self._db = db

    def save_analysis(
        self, user_id: str, reference_text: str, analysis: "PracticeResult"
    ) -> str:
        """Save pronunciation analysis to Firestore."""
        # TODO: Implementation in Sprint 1
        raise NotImplementedError("To be implemented in Sprint 1")

    def get_user_history(
        self, user_id: str, limit: int = 50
    ) -> List["PracticeResult"]:
        """Get user history from Firestore."""
        # TODO: Implementation in Sprint 1
        raise NotImplementedError("To be implemented in Sprint 1")


class FirestoreConversationRepository(ConversationRepository):
    """Firestore implementation of ConversationRepository."""

    def __init__(self, db):
        self._db = db

    def save_turn(self, session_id: str, turn: "TurnResult") -> None:
        """Save conversation turn to Firestore."""
        # TODO: Implementation in Sprint 1
        raise NotImplementedError("To be implemented in Sprint 1")

    def get_session_history(self, session_id: str) -> List["TurnResult"]:
        """Get session history from Firestore."""
        # TODO: Implementation in Sprint 1
        raise NotImplementedError("To be implemented in Sprint 1")


class FirestoreWritingRepository(WritingRepository):
    """Firestore implementation of WritingRepository."""

    def __init__(self, db):
        self._db = db

    def save_evaluation(
        self, user_id: str, text: str, evaluation: "WritingEvaluation"
    ) -> str:
        """Save writing evaluation to Firestore."""
        # TODO: Implementation in Sprint 1
        raise NotImplementedError("To be implemented in Sprint 1")


class FirestoreActivityRepository(ActivityRepository):
    """Firestore implementation of ActivityRepository."""

    def __init__(self, db):
        self._db = db

    def log_activity(self, activity: "ActivityLog") -> None:
        """Log activity to Firestore."""
        # TODO: Implementation in Sprint 1
        raise NotImplementedError("To be implemented in Sprint 1")

    def get_today_activities(
        self, user_id: str, date: datetime
    ) -> List["ActivityLog"]:
        """Get today's activities from Firestore."""
        # TODO: Implementation in Sprint 1
        raise NotImplementedError("To be implemented in Sprint 1")
