"""
Unit tests for Conversation Service (BC5)

Testing conversation turn processing, prompt building, and session management.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from accent_coach.domain.conversation import (
    ConversationService,
    ConversationError,
    ConversationMode,
    ConversationConfig,
    ConversationSession,
    ConversationTurn,
    TutorResponse,
)
from accent_coach.domain.conversation.prompts import PromptBuilder
from accent_coach.domain.conversation.starters import ConversationStarters
from accent_coach.domain.audio.models import ProcessedAudio
from accent_coach.domain.transcription.models import Transcription


@pytest.mark.unit
class TestPromptBuilder:
    """Test prompt building logic."""

    def test_build_practice_mode_prompt(self):
        """Test building prompt for practice mode."""
        # Given
        user_transcript = "I go to school yesterday"
        conversation_history = []
        config = ConversationConfig(
            mode=ConversationMode.PRACTICE,
            user_level="B1-B2",
        )

        # When
        prompt = PromptBuilder.build_prompt(user_transcript, conversation_history, config)

        # Then
        assert "system" in prompt
        assert "user" in prompt
        assert "B1-B2" in prompt["system"]
        assert "[CORRECTION]" in prompt["system"]
        assert user_transcript in prompt["user"]

    def test_build_prompt_with_history(self):
        """Test prompt building with conversation history."""
        # Given
        user_transcript = "What about you?"

        # Create mock history
        turn1 = ConversationTurn(
            user_transcript="I like reading",
            tutor_response=TutorResponse(
                correction="Great!",
                explanation="",
                improved_version="I like reading",
                follow_up_question="What do you like to read?",
            ),
        )

        config = ConversationConfig(mode=ConversationMode.PRACTICE, max_history_turns=3)

        # When
        prompt = PromptBuilder.build_prompt(user_transcript, [turn1], config)

        # Then
        assert "I like reading" in prompt["user"]
        assert "What do you like to read?" in prompt["user"]
        assert "What about you?" in prompt["user"]

    def test_build_exam_mode_prompt(self):
        """Test building prompt for exam mode."""
        # Given
        config = ConversationConfig(mode=ConversationMode.EXAM, user_level="A2")

        # When
        prompt = PromptBuilder.build_prompt("Hello", [], config)

        # Then
        assert "examiner" in prompt["system"].lower()
        assert "[ERRORS FOUND]" in prompt["system"]

    def test_parse_llm_response(self):
        """Test parsing structured LLM output."""
        # Given
        llm_output = """
[CORRECTION]: You should say "went" instead of "go" for past tense.
[EXPLANATION]: We use past tense for actions that happened yesterday.
[IMPROVED VERSION]: I went to school yesterday.
[FOLLOW UP QUESTION]: What did you do at school?
"""

        # When
        parsed = PromptBuilder.parse_llm_response(llm_output)

        # Then
        assert "went" in parsed["correction"]
        assert "past tense" in parsed["explanation"]
        assert "I went to school yesterday" in parsed["improved_version"]
        assert "What did you do at school?" in parsed["follow_up_question"]


@pytest.mark.unit
class TestConversationStarters:
    """Test conversation starters."""

    def test_get_starter_by_topic(self):
        """Test getting starter for specific topic."""
        # Given
        topic = "Travel"
        level = "B1-B2"

        # When
        starter = ConversationStarters.get_starter(topic, level)

        # Then
        assert isinstance(starter, str)
        assert len(starter) > 0

    def test_get_starter_defaults_to_general(self):
        """Test that unknown topics default to general conversation."""
        # Given
        topic = "Unknown Topic"

        # When
        starter = ConversationStarters.get_starter(topic)

        # Then
        assert isinstance(starter, str)

    def test_get_topics(self):
        """Test getting list of available topics."""
        # When
        topics = ConversationStarters.get_topics()

        # Then
        assert isinstance(topics, list)
        assert "Travel" in topics
        assert "General Conversation" in topics


@pytest.mark.unit
class TestConversationSession:
    """Test conversation session management."""

    def test_create_session(self):
        """Test creating a new session."""
        # Given
        session_id = "test_session_123"
        user_id = "user_456"

        # When
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            topic="Travel",
            level="B1-B2",
            mode=ConversationMode.PRACTICE,
        )

        # Then
        assert session.session_id == session_id
        assert session.user_id == user_id
        assert session.topic == "Travel"
        assert len(session.history) == 0
        assert session.status == "active"

    def test_add_turn_to_session(self):
        """Test adding a turn to session history."""
        # Given
        session = ConversationSession(
            session_id="test", user_id="user", topic="Travel", level="B1-B2", mode=ConversationMode.PRACTICE
        )

        turn = ConversationTurn(
            user_transcript="I like traveling",
            tutor_response=TutorResponse(
                correction="Great!",
                explanation="",
                improved_version="I like traveling",
                follow_up_question="Where have you been?",
            ),
        )

        # When
        session.add_turn(turn)

        # Then
        assert len(session.history) == 1
        assert session.history[0] == turn

    def test_get_recent_history(self):
        """Test getting recent conversation history."""
        # Given
        session = ConversationSession(
            session_id="test", user_id="user", topic="Travel", level="B1-B2", mode=ConversationMode.PRACTICE
        )

        # Add 10 turns
        for i in range(10):
            turn = ConversationTurn(
                user_transcript=f"Message {i}",
                tutor_response=TutorResponse(
                    correction="", explanation="", improved_version="", follow_up_question=""
                ),
            )
            session.add_turn(turn)

        # When
        recent = session.get_recent_history(max_turns=5)

        # Then
        assert len(recent) == 5
        assert recent[0].user_transcript == "Message 5"
        assert recent[-1].user_transcript == "Message 9"

    def test_session_stats(self):
        """Test session statistics calculation."""
        # Given
        session = ConversationSession(
            session_id="test", user_id="user", topic="Travel", level="B1-B2", mode=ConversationMode.PRACTICE
        )

        # Add turns with errors
        turn1 = ConversationTurn(
            user_transcript="I go yesterday",
            tutor_response=TutorResponse(
                correction="Error",
                explanation="",
                improved_version="I went yesterday",
                follow_up_question="",
                errors_detected=["past tense error"],
            ),
        )
        session.add_turn(turn1)

        # When
        stats = session.get_stats()

        # Then
        assert stats["total_turns"] == 1
        assert stats["total_errors"] == 1
        assert stats["topic"] == "Travel"

    def test_session_to_dict(self):
        """Test converting session to dict for storage."""
        # Given
        session = ConversationSession(
            session_id="test123",
            user_id="user456",
            topic="Travel",
            level="B1-B2",
            mode=ConversationMode.PRACTICE,
        )

        # When
        session_dict = session.to_dict()

        # Then
        assert session_dict["session_id"] == "test123"
        assert session_dict["user_id"] == "user456"
        assert session_dict["topic"] == "Travel"
        assert session_dict["mode"] == "practice"
        assert "stats" in session_dict


@pytest.mark.unit
class TestConversationService:
    """Test ConversationService."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        audio_service = Mock()
        transcription_service = Mock()
        llm_service = Mock()
        repository = Mock()

        return {
            "audio": audio_service,
            "transcription": transcription_service,
            "llm": llm_service,
            "repository": repository,
        }

    @pytest.fixture
    def conversation_service(self, mock_services):
        """Create ConversationService with mocked dependencies."""
        return ConversationService(
            audio_service=mock_services["audio"],
            transcription_service=mock_services["transcription"],
            llm_service=mock_services["llm"],
            repository=mock_services["repository"],
        )

    def test_create_session(self, conversation_service):
        """Test creating a new conversation session."""
        # Given
        user_id = "user123"
        config = ConversationConfig(
            mode=ConversationMode.PRACTICE,
            topic="Travel",
            user_level="B1-B2",
        )

        # When
        session = conversation_service.create_session(user_id, config)

        # Then
        assert session.user_id == user_id
        assert session.topic == "Travel"
        assert session.level == "B1-B2"
        assert session.mode == ConversationMode.PRACTICE
        assert "conv_" in session.session_id

    def test_process_turn_success(self, conversation_service, mock_services):
        """Test successful conversation turn processing."""
        # Given
        audio_bytes = b"fake_audio_data"
        session = ConversationSession(
            session_id="test", user_id="user", topic="Travel", level="B1-B2", mode=ConversationMode.PRACTICE
        )
        config = ConversationConfig()

        # Mock audio processing
        mock_services["audio"].process_recording.return_value = ProcessedAudio(
            waveform=np.zeros(16000, dtype=np.float32),
            sample_rate=16000,
            duration_seconds=1.0,
        )

        # Mock transcription
        mock_services["transcription"].transcribe.return_value = Transcription(
            text="I like traveling",
            phonemes="",
            confidence=0.9,
        )

        # Mock LLM feedback
        mock_services["llm"].generate_conversation_feedback.return_value = """
[CORRECTION]: Great! No errors.
[EXPLANATION]: Perfect grammar and vocabulary.
[IMPROVED VERSION]: I like traveling.
[FOLLOW UP QUESTION]: Where have you traveled?
"""

        # Mock TTS
        mock_services["audio"].generate_audio.return_value = b"fake_tts_audio"

        # When
        turn = conversation_service.process_turn(audio_bytes, session, config)

        # Then
        assert turn.user_transcript == "I like traveling"
        assert turn.tutor_response.follow_up_question == "Where have you traveled?"
        assert turn.follow_up_audio == b"fake_tts_audio"
        assert len(session.history) == 1

        # Verify dependencies were called
        mock_services["audio"].process_recording.assert_called_once()
        mock_services["transcription"].transcribe.assert_called_once()
        mock_services["llm"].generate_conversation_feedback.assert_called_once()

    def test_process_turn_empty_transcript(self, conversation_service, mock_services):
        """Test handling of empty transcription."""
        # Given
        audio_bytes = b"fake_audio"
        session = ConversationSession(
            session_id="test", user_id="user", topic="Test", level="B1-B2", mode=ConversationMode.PRACTICE
        )
        config = ConversationConfig()

        # Mock empty transcription
        mock_services["audio"].process_recording.return_value = ProcessedAudio(
            waveform=np.zeros(16000, dtype=np.float32), sample_rate=16000, duration_seconds=1.0
        )
        mock_services["transcription"].transcribe.return_value = Transcription(
            text="", phonemes="", confidence=0.0
        )

        # When/Then
        with pytest.raises(ConversationError, match="Could not transcribe"):
            conversation_service.process_turn(audio_bytes, session, config)

    def test_process_turn_llm_failure_fallback(self, conversation_service, mock_services):
        """Test fallback when LLM fails."""
        # Given
        audio_bytes = b"fake_audio"
        session = ConversationSession(
            session_id="test", user_id="user", topic="Test", level="B1-B2", mode=ConversationMode.PRACTICE
        )
        config = ConversationConfig()

        # Mock audio and transcription success
        mock_services["audio"].process_recording.return_value = ProcessedAudio(
            waveform=np.zeros(16000, dtype=np.float32), sample_rate=16000, duration_seconds=1.0
        )
        mock_services["transcription"].transcribe.return_value = Transcription(
            text="Hello", phonemes="", confidence=0.9
        )

        # Mock LLM failure
        mock_services["llm"].generate_conversation_feedback.side_effect = Exception("LLM error")

        # Mock TTS (won't be called due to error)
        mock_services["audio"].generate_audio.return_value = None

        # When
        turn = conversation_service.process_turn(audio_bytes, session, config)

        # Then - should have fallback response
        assert turn.user_transcript == "Hello"
        assert "Error getting feedback" in turn.tutor_response.explanation
        assert turn.tutor_response.follow_up_question == "Could you tell me more about that?"

    def test_close_session(self, conversation_service, mock_services):
        """Test closing a conversation session."""
        # Given
        session = ConversationSession(
            session_id="test", user_id="user", topic="Test", level="B1-B2", mode=ConversationMode.PRACTICE
        )

        # When
        conversation_service.close_session(session)

        # Then
        assert session.status == "completed"
        mock_services["repository"].update_session.assert_called_once_with(session)
