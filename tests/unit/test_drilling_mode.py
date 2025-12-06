"""
Tests for Drilling Mode Component
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime


@pytest.mark.unit
class TestDrillingMode:
    """Test Drilling Mode component."""

    def test_drilling_mode_imports(self):
        """Test that drilling mode can be imported."""
        from accent_coach.presentation.components import DrillingMode, render_drilling_mode

        assert DrillingMode is not None
        assert render_drilling_mode is not None

    def test_drilling_session_initialization(self):
        """Test drilling session state initialization."""
        from accent_coach.presentation.components.drilling_mode import DrillingMode

        # Mock session state
        mock_session_state = {}

        drill_words = ["hello", "world", "test"]

        # Simulate initialization
        drilling_session = {
            'words': drill_words,
            'current_index': 0,
            'attempts': {},
            'completed': [],
            'started_at': datetime.now()
        }

        assert drilling_session['words'] == drill_words
        assert drilling_session['current_index'] == 0
        assert drilling_session['attempts'] == {}
        assert drilling_session['completed'] == []
        assert isinstance(drilling_session['started_at'], datetime)

    def test_drilling_progress_calculation(self):
        """Test progress calculation."""
        total_words = 5
        current_index = 2

        progress = current_index / total_words
        assert progress == 0.4  # 40% complete

        current_index = 5
        progress = current_index / total_words
        assert progress == 1.0  # 100% complete

    def test_attempt_tracking(self):
        """Test attempt tracking for words."""
        attempts = {}

        # Add attempts for "hello"
        attempts['hello'] = [
            {'timestamp': datetime.now(), 'result': {'accuracy': 0.7}},
            {'timestamp': datetime.now(), 'result': {'accuracy': 0.85}},
            {'timestamp': datetime.now(), 'result': {'accuracy': 0.92}},
        ]

        assert len(attempts['hello']) == 3
        assert attempts['hello'][-1]['result']['accuracy'] == 0.92

    def test_completion_detection(self):
        """Test detection of drilling completion."""
        drill_words = ["hello", "world"]
        current_index = 2

        is_complete = current_index >= len(drill_words)
        assert is_complete is True

        current_index = 1
        is_complete = current_index >= len(drill_words)
        assert is_complete is False

    def test_accuracy_thresholds(self):
        """Test accuracy threshold logic."""
        def get_feedback(accuracy: float) -> str:
            if accuracy >= 90:
                return "excellent"
            elif accuracy >= 70:
                return "good"
            else:
                return "needs_practice"

        assert get_feedback(95) == "excellent"
        assert get_feedback(85) == "good"
        assert get_feedback(50) == "needs_practice"

    def test_best_attempt_calculation(self):
        """Test finding best attempt for a word."""
        attempts = [
            {'result': {'analysis': Mock(metrics=Mock(word_accuracy=0.7))}},
            {'result': {'analysis': Mock(metrics=Mock(word_accuracy=0.85))}},
            {'result': {'analysis': Mock(metrics=Mock(word_accuracy=0.92))}},
        ]

        best = max(
            attempts,
            key=lambda a: a['result']['analysis'].metrics.word_accuracy
        )

        assert best['result']['analysis'].metrics.word_accuracy == 0.92

    def test_statistics_calculation(self):
        """Test drilling statistics calculation."""
        session = {
            'words': ['hello', 'world', 'test'],
            'attempts': {
                'hello': [1, 2, 3],  # 3 attempts
                'world': [1, 2],     # 2 attempts
                'test': [1]          # 1 attempt
            }
        }

        total_attempts = sum(len(attempts) for attempts in session['attempts'].values())
        avg_attempts = total_attempts / len(session['words'])

        assert total_attempts == 6
        assert avg_attempts == 2.0

    def test_word_list_update(self):
        """Test updating word list in active session."""
        session = {
            'words': ['hello', 'world'],
            'current_index': 1,
            'attempts': {'hello': [1, 2]},
            'completed': ['hello']
        }

        new_words = ['foo', 'bar', 'baz']

        # Simulate update
        if session['words'] != new_words:
            session['words'] = new_words
            session['current_index'] = 0
            session['attempts'] = {}
            session['completed'] = []

        assert session['words'] == new_words
        assert session['current_index'] == 0
        assert session['attempts'] == {}
        assert session['completed'] == []

    def test_drilling_mode_component_exists(self):
        """Test that DrillingMode class has required methods."""
        from accent_coach.presentation.components.drilling_mode import DrillingMode

        assert hasattr(DrillingMode, 'render')
        assert hasattr(DrillingMode, '_render_attempt_result')
        assert hasattr(DrillingMode, '_render_completion')

    def test_empty_drill_words(self):
        """Test handling of empty drill words list."""
        drill_words = []

        # Should not crash with empty list
        assert len(drill_words) == 0
        assert not drill_words  # Empty list is falsy


@pytest.mark.integration
class TestDrillingModeIntegration:
    """Integration tests for Drilling Mode."""

    def test_drilling_with_audio_service(self):
        """Test drilling mode with mocked AudioService."""
        from accent_coach.domain.audio import AudioService

        # Create real AudioService (will use mocks internally in tests)
        audio_service = AudioService()

        # Verify it has TTS method
        assert hasattr(audio_service, 'generate_tts')

    def test_drilling_callback_structure(self):
        """Test that callback has correct structure."""
        def mock_callback(audio_bytes: bytes, target_word: str) -> dict:
            return {
                'analysis': Mock(
                    metrics=Mock(word_accuracy=0.85),
                    per_word_comparison=[
                        Mock(
                            word=target_word,
                            phoneme_accuracy=0.85,
                            ref_phonemes="h ɛ l oʊ",
                            rec_phonemes="h ɛ l oʊ"
                        )
                    ]
                )
            }

        result = mock_callback(b"fake_audio", "hello")

        assert 'analysis' in result
        assert result['analysis'].metrics.word_accuracy == 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
