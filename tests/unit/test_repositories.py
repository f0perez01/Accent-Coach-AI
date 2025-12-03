"""
Unit tests for Repository Pattern

Testing in-memory implementations (fast, no Firebase needed).
"""

import pytest
from datetime import datetime
from accent_coach.infrastructure.persistence.in_memory_repositories import (
    InMemoryPronunciationRepository,
    InMemoryConversationRepository,
    InMemoryWritingRepository,
    InMemoryActivityRepository,
)
from accent_coach.infrastructure.activity.models import ActivityLog, ActivityType


# Mock data classes for testing
class MockPronunciationMetrics:
    def __init__(self):
        self.word_accuracy = 85.0
        self.phoneme_accuracy = 90.0
        self.phoneme_error_rate = 10.0
        self.correct_words = 8
        self.total_words = 10
        self.substitutions = 2
        self.insertions = 1
        self.deletions = 1


class MockWordComparison:
    def __init__(self, word, match=True):
        self.word = word
        self.ref_phonemes = "test"
        self.rec_phonemes = "test" if match else "tst"
        self.match = match
        self.phoneme_accuracy = 100.0 if match else 75.0


class MockPronunciationAnalysis:
    def __init__(self):
        self.metrics = MockPronunciationMetrics()
        self.per_word_comparison = [
            MockWordComparison("hello", True),
            MockWordComparison("world", False),
        ]


class MockPracticeResult:
    def __init__(self):
        self.analysis = MockPronunciationAnalysis()
        self.llm_feedback = "Great job!"
        self.raw_decoded = "hello world"
        self.recorded_phoneme_str = "hɛloʊ wɜrld"


class MockTurnResult:
    def __init__(self):
        self.user_transcript = "Hello, how are you?"
        self.correction = None
        self.improved_version = None
        self.explanation = None
        self.errors_detected = []
        self.follow_up_question = "What do you like to do?"


class MockCEFRMetrics:
    def __init__(self):
        self.cefr_level = "B2"
        self.variety_score = 7


class MockVocabularyExpansion:
    def __init__(self):
        self.word = "furthermore"
        self.ipa = "ˈfɜrðərˌmɔr"
        self.replaces_simple_word = "also"
        self.meaning_context = "formal transition"


class MockWritingEvaluation:
    def __init__(self):
        self.corrected = "This is a corrected version."
        self.improvements = ["Use more varied vocabulary"]
        self.questions = ["Can you elaborate on X?"]
        self.metrics = MockCEFRMetrics()
        self.expansion_words = [MockVocabularyExpansion()]


# ============================================================================
# PRONUNCIATION REPOSITORY TESTS
# ============================================================================


@pytest.mark.unit
class TestInMemoryPronunciationRepository:
    """Test InMemoryPronunciationRepository."""

    def test_save_and_retrieve_analysis(self):
        """Test saving and retrieving pronunciation analysis."""
        # Given
        repo = InMemoryPronunciationRepository()
        user_id = "user123"
        reference_text = "hello world"
        analysis = MockPracticeResult()

        # When
        doc_id = repo.save_analysis(user_id, reference_text, analysis)

        # Then
        assert doc_id == "doc_1"
        history = repo.get_user_history(user_id)
        assert len(history) == 1
        assert history[0] == analysis

    def test_get_history_empty_user(self):
        """Test retrieving history for user with no data."""
        # Given
        repo = InMemoryPronunciationRepository()

        # When
        history = repo.get_user_history("nonexistent_user")

        # Then
        assert history == []

    def test_get_history_respects_limit(self):
        """Test that get_user_history respects limit parameter."""
        # Given
        repo = InMemoryPronunciationRepository()
        user_id = "user123"

        # Save 10 analyses
        for i in range(10):
            repo.save_analysis(user_id, f"text_{i}", MockPracticeResult())

        # When
        history = repo.get_user_history(user_id, limit=5)

        # Then
        assert len(history) == 5

    def test_clear_removes_all_data(self):
        """Test that clear() removes all data."""
        # Given
        repo = InMemoryPronunciationRepository()
        repo.save_analysis("user1", "text1", MockPracticeResult())
        repo.save_analysis("user2", "text2", MockPracticeResult())

        # When
        repo.clear()

        # Then
        assert repo.get_user_history("user1") == []
        assert repo.get_user_history("user2") == []


# ============================================================================
# CONVERSATION REPOSITORY TESTS
# ============================================================================


@pytest.mark.unit
class TestInMemoryConversationRepository:
    """Test InMemoryConversationRepository."""

    def test_save_and_retrieve_turn(self):
        """Test saving and retrieving conversation turn."""
        # Given
        repo = InMemoryConversationRepository()
        session_id = "session_123"
        turn = MockTurnResult()

        # When
        repo.save_turn(session_id, turn)

        # Then
        history = repo.get_session_history(session_id)
        assert len(history) == 1
        assert history[0] == turn

    def test_get_session_history_empty(self):
        """Test retrieving history for nonexistent session."""
        # Given
        repo = InMemoryConversationRepository()

        # When
        history = repo.get_session_history("nonexistent_session")

        # Then
        assert history == []

    def test_multiple_turns_same_session(self):
        """Test saving multiple turns to same session."""
        # Given
        repo = InMemoryConversationRepository()
        session_id = "session_123"

        # When
        for i in range(3):
            repo.save_turn(session_id, MockTurnResult())

        # Then
        history = repo.get_session_history(session_id)
        assert len(history) == 3


# ============================================================================
# WRITING REPOSITORY TESTS
# ============================================================================


@pytest.mark.unit
class TestInMemoryWritingRepository:
    """Test InMemoryWritingRepository."""

    def test_save_and_retrieve_evaluation(self):
        """Test saving writing evaluation."""
        # Given
        repo = InMemoryWritingRepository()
        user_id = "user123"
        text = "This is my essay."
        evaluation = MockWritingEvaluation()

        # When
        doc_id = repo.save_evaluation(user_id, text, evaluation)

        # Then
        assert doc_id == "doc_1"
        # Note: WritingRepository doesn't have get_history method yet
        # This is just testing save functionality


# ============================================================================
# ACTIVITY REPOSITORY TESTS
# ============================================================================


@pytest.mark.unit
class TestInMemoryActivityRepository:
    """Test InMemoryActivityRepository."""

    def test_log_and_retrieve_activity(self):
        """Test logging and retrieving activities."""
        # Given
        repo = InMemoryActivityRepository()
        activity = ActivityLog(
            user_id="user123",
            activity_type=ActivityType.PRONUNCIATION,
            timestamp=datetime.now(),
            score=50,
            metadata={"word_count": 10},
        )

        # When
        repo.log_activity(activity)

        # Then
        today_activities = repo.get_today_activities("user123", datetime.now())
        assert len(today_activities) == 1
        assert today_activities[0] == activity

    def test_get_activities_filters_by_user(self):
        """Test that get_today_activities filters by user_id."""
        # Given
        repo = InMemoryActivityRepository()
        activity1 = ActivityLog(
            user_id="user1",
            activity_type=ActivityType.PRONUNCIATION,
            timestamp=datetime.now(),
            score=50,
            metadata={},
        )
        activity2 = ActivityLog(
            user_id="user2",
            activity_type=ActivityType.CONVERSATION,
            timestamp=datetime.now(),
            score=30,
            metadata={},
        )

        repo.log_activity(activity1)
        repo.log_activity(activity2)

        # When
        user1_activities = repo.get_today_activities("user1", datetime.now())

        # Then
        assert len(user1_activities) == 1
        assert user1_activities[0].user_id == "user1"

    def test_get_activities_filters_by_date(self):
        """Test that get_today_activities filters by date."""
        # Given
        repo = InMemoryActivityRepository()
        today = datetime.now()
        yesterday = datetime(today.year, today.month, today.day - 1, 12, 0, 0)

        activity_today = ActivityLog(
            user_id="user123",
            activity_type=ActivityType.WRITING,
            timestamp=today,
            score=20,
            metadata={},
        )
        activity_yesterday = ActivityLog(
            user_id="user123",
            activity_type=ActivityType.PRONUNCIATION,
            timestamp=yesterday,
            score=10,
            metadata={},
        )

        repo.log_activity(activity_today)
        repo.log_activity(activity_yesterday)

        # When
        today_activities = repo.get_today_activities("user123", today)

        # Then
        assert len(today_activities) == 1
        assert today_activities[0].timestamp.date() == today.date()
