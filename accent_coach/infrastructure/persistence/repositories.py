"""
Abstract Repository Interfaces

Following Repository Pattern for clean separation of persistence.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime


class PronunciationRepository(ABC):
    """Repository for pronunciation practice data."""

    @abstractmethod
    def save_analysis(
        self, user_id: str, reference_text: str, analysis: "PracticeResult"
    ) -> str:
        """
        Save pronunciation analysis.

        Args:
            user_id: User identifier
            reference_text: Text that was practiced
            analysis: Practice result

        Returns:
            Document ID
        """
        pass

    @abstractmethod
    def get_user_history(
        self, user_id: str, limit: int = 50
    ) -> List["PracticeResult"]:
        """
        Get user's practice history.

        Args:
            user_id: User identifier
            limit: Maximum number of results

        Returns:
            List of practice results
        """
        pass


class ConversationRepository(ABC):
    """Repository for conversation tutor data."""

    @abstractmethod
    def save_turn(self, session_id: str, turn: "TurnResult") -> None:
        """
        Save conversation turn.

        Args:
            session_id: Conversation session ID
            turn: Turn result
        """
        pass

    @abstractmethod
    def get_session_history(self, session_id: str) -> List["TurnResult"]:
        """
        Get full session history.

        Args:
            session_id: Conversation session ID

        Returns:
            List of turns
        """
        pass


class WritingRepository(ABC):
    """Repository for writing evaluations."""

    @abstractmethod
    def save_evaluation(
        self, user_id: str, text: str, evaluation: "WritingEvaluation"
    ) -> str:
        """
        Save writing evaluation.

        Args:
            user_id: User identifier
            text: Original text
            evaluation: Writing evaluation

        Returns:
            Document ID
        """
        pass


class ActivityRepository(ABC):
    """Repository for activity tracking."""

    @abstractmethod
    def log_activity(self, activity: "ActivityLog") -> None:
        """
        Log user activity.

        Args:
            activity: Activity log entry
        """
        pass

    @abstractmethod
    def get_today_activities(
        self, user_id: str, date: datetime
    ) -> List["ActivityLog"]:
        """
        Get activities for specific date.

        Args:
            user_id: User identifier
            date: Date to query

        Returns:
            List of activities
        """
        pass
