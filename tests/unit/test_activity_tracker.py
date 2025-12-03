"""
Unit tests for Activity Tracker
"""

import pytest
from datetime import datetime
from accent_coach.infrastructure.activity.tracker import ActivityTracker
from accent_coach.infrastructure.activity.models import ActivityType
from accent_coach.infrastructure.persistence.in_memory_repositories import (
    InMemoryActivityRepository,
)


@pytest.mark.unit
class TestActivityTracker:
    """Test ActivityTracker with in-memory repository."""

    def test_log_pronunciation_activity(self):
        """Test logging pronunciation activity."""
        # Given
        repo = InMemoryActivityRepository()
        tracker = ActivityTracker(repo)

        # When
        log = tracker.log_pronunciation(
            user_id="user123",
            audio_duration=15.5,
            word_count=10,
            error_count=2,
        )

        # Then
        assert log.user_id == "user123"
        assert log.activity_type == ActivityType.PRONUNCIATION
        assert log.score > 0  # Should calculate score

        # Verify it was saved to repository
        activities = repo.get_today_activities("user123", datetime.now())
        assert len(activities) == 1

    def test_pronunciation_score_calculation(self):
        """Test pronunciation score calculation logic."""
        # Given
        repo = InMemoryActivityRepository()
        tracker = ActivityTracker(repo)

        # When: 10 words, 0 errors, 15 seconds
        log = tracker.log_pronunciation(
            user_id="user123", audio_duration=15.0, word_count=10, error_count=0
        )

        # Then
        # Base: 10 words * 10 = 100
        # Penalty: 0 errors * 2 = 0
        # Bonus: 15 seconds / 10 = 1
        # Total: 100 - 0 + 1 = 101
        assert log.score == 101

    def test_pronunciation_score_with_errors(self):
        """Test that errors reduce score."""
        # Given
        repo = InMemoryActivityRepository()
        tracker = ActivityTracker(repo)

        # When: 10 words, 5 errors
        log = tracker.log_pronunciation(
            user_id="user123", audio_duration=10.0, word_count=10, error_count=5
        )

        # Then
        # Base: 10 * 10 = 100
        # Penalty: 5 * 2 = 10
        # Bonus: 10 / 10 = 1
        # Total: 100 - 10 + 1 = 91
        assert log.score == 91

    def test_get_daily_progress_no_activities(self):
        """Test daily progress with no activities."""
        # Given
        repo = InMemoryActivityRepository()
        tracker = ActivityTracker(repo)

        # When
        progress = tracker.get_daily_progress("user123", daily_goal=100)

        # Then
        assert progress["score"] == 0
        assert progress["goal"] == 100
        assert progress["progress_percentage"] == 0
        assert progress["exceeded"] is False

    def test_get_daily_progress_partial(self):
        """Test daily progress at 50%."""
        # Given
        repo = InMemoryActivityRepository()
        tracker = ActivityTracker(repo)

        # Log activity worth 50 points
        tracker.log_pronunciation(
            user_id="user123", audio_duration=0, word_count=5, error_count=0
        )

        # When
        progress = tracker.get_daily_progress("user123", daily_goal=100)

        # Then
        assert progress["score"] == 50
        assert progress["goal"] == 100
        assert progress["progress_percentage"] == 50
        assert progress["exceeded"] is False

    def test_get_daily_progress_exceeded(self):
        """Test daily progress when goal is exceeded."""
        # Given
        repo = InMemoryActivityRepository()
        tracker = ActivityTracker(repo)

        # Log activities worth 120 points total
        tracker.log_pronunciation(
            user_id="user123", audio_duration=0, word_count=12, error_count=0
        )

        # When
        progress = tracker.get_daily_progress("user123", daily_goal=100)

        # Then
        assert progress["score"] == 120
        assert progress["goal"] == 100
        assert progress["progress_percentage"] == 100  # Capped at 100
        assert progress["exceeded"] is True

    def test_metadata_stored_correctly(self):
        """Test that metadata is stored correctly."""
        # Given
        repo = InMemoryActivityRepository()
        tracker = ActivityTracker(repo)

        # When
        log = tracker.log_pronunciation(
            user_id="user123",
            audio_duration=12.5,
            word_count=8,
            error_count=3,
        )

        # Then
        assert log.metadata["audio_duration"] == 12.5
        assert log.metadata["word_count"] == 8
        assert log.metadata["error_count"] == 3
