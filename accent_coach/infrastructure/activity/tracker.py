"""
Activity Tracker
"""

from datetime import datetime
from typing import Dict
from .models import ActivityLog, ActivityType


class ActivityTracker:
    """
    Track user activities across all domains.

    Responsibilities:
    - Log activities with scores
    - Calculate daily progress
    - Aggregate statistics

    Dependencies:
    - ActivityRepository (Infrastructure)
    """

    def __init__(self, repository):
        """
        Args:
            repository: ActivityRepository instance
        """
        self._repo = repository

    def log_pronunciation(
        self, user_id: str, audio_duration: float, word_count: int, error_count: int
    ) -> ActivityLog:
        """
        Log pronunciation activity.

        Args:
            user_id: User identifier
            audio_duration: Duration of audio in seconds
            word_count: Number of words practiced
            error_count: Number of errors detected

        Returns:
            Activity log entry
        """
        score = self._calculate_pronunciation_score(
            audio_duration, word_count, error_count
        )

        log = ActivityLog(
            user_id=user_id,
            activity_type=ActivityType.PRONUNCIATION,
            timestamp=datetime.now(),
            score=score,
            metadata={
                "audio_duration": audio_duration,
                "word_count": word_count,
                "error_count": error_count,
            },
        )

        self._repo.log_activity(log)
        return log

    def get_daily_progress(
        self, user_id: str, daily_goal: int = 100
    ) -> Dict:
        """
        Calculate daily progress.

        Args:
            user_id: User identifier
            daily_goal: Daily score goal

        Returns:
            Progress dict with score, goal, percentage, exceeded
        """
        today_activities = self._repo.get_today_activities(user_id, datetime.now())

        total_score = sum(a.score for a in today_activities)
        progress = min(100, (total_score / daily_goal) * 100)

        return {
            "score": total_score,
            "goal": daily_goal,
            "progress_percentage": progress,
            "exceeded": total_score > daily_goal,
        }

    def _calculate_pronunciation_score(
        self, audio_duration: float, word_count: int, error_count: int
    ) -> int:
        """Calculate score for pronunciation activity."""
        # Base score: 10 points per word
        base_score = word_count * 10

        # Penalty for errors: -2 points per error
        error_penalty = error_count * 2

        # Bonus for longer practice: +1 point per 10 seconds
        duration_bonus = int(audio_duration / 10)

        return max(0, base_score - error_penalty + duration_bonus)
