"""
Unit tests for Pronunciation Practice Service (BC4)

Testing with mocks (no actual audio/ASR processing).
"""

import pytest
import numpy as np
from unittest.mock import Mock
from accent_coach.domain.pronunciation.service import (
    PronunciationPracticeService,
    PronunciationError,
)
from accent_coach.domain.pronunciation.models import PracticeConfig, PracticeResult
from accent_coach.domain.audio.models import ProcessedAudio
from accent_coach.domain.transcription.models import Transcription
from accent_coach.domain.phonetic.models import (
    PronunciationAnalysis,
    PronunciationMetrics,
    WordComparison,
)


@pytest.mark.unit
class TestPronunciationPracticeService:
    """Test PronunciationPracticeService with mocked dependencies."""

    def test_analyze_recording_success(self):
        """Test successful pronunciation analysis workflow."""
        # Given - Mock all dependencies
        mock_audio = Mock()
        mock_transcription = Mock()
        mock_phonetic = Mock()
        mock_llm = Mock()
        mock_repo = Mock()

        # Mock processed audio
        mock_audio.process_recording.return_value = ProcessedAudio(
            waveform=np.array([0.1, 0.2, 0.3]),
            sample_rate=16000,
            duration_seconds=1.0
        )

        # Mock transcription
        mock_transcription.transcribe.return_value = Transcription(
            text="hello world",
            phonemes="həˈloʊ ˈwɝld",
            confidence=0.95,
            language="en-us"
        )

        # Mock phonetic analysis
        mock_phonetic.analyze_pronunciation.return_value = PronunciationAnalysis(
            metrics=PronunciationMetrics(
                word_accuracy=1.0,
                phoneme_accuracy=0.9,
                phoneme_error_rate=0.1,
                correct_words=2,
                total_words=2,
                substitutions=1,
                insertions=0,
                deletions=0
            ),
            per_word_comparison=[
                WordComparison(
                    word="hello",
                    ref_phonemes="həˈloʊ",
                    rec_phonemes="həˈloʊ",
                    match=True,
                    phoneme_accuracy=1.0
                ),
                WordComparison(
                    word="world",
                    ref_phonemes="ˈwɝld",
                    rec_phonemes="ˈwɝld",
                    match=True,
                    phoneme_accuracy=1.0
                )
            ],
            ipa_breakdown=[],
            unique_symbols=set(),
            suggested_drill_words=[]
        )

        # Mock LLM feedback
        mock_llm.generate_pronunciation_feedback.return_value = (
            "Great job! Your pronunciation is excellent."
        )

        service = PronunciationPracticeService(
            audio_service=mock_audio,
            transcription_service=mock_transcription,
            phonetic_service=mock_phonetic,
            llm_service=mock_llm,
            repository=mock_repo
        )

        # When
        result = service.analyze_recording(
            audio_bytes=b"fake_audio_data",
            reference_text="hello world",
            user_id="user123",
            config=PracticeConfig()
        )

        # Then
        assert isinstance(result, PracticeResult)
        assert result.analysis.metrics.phoneme_accuracy == 0.9
        assert result.analysis.metrics.word_accuracy == 1.0
        assert result.llm_feedback == "Great job! Your pronunciation is excellent."
        assert result.raw_decoded == "hello world"
        assert result.recorded_phoneme_str == "həˈloʊ ˈwɝld"

        # Verify all services were called
        mock_audio.process_recording.assert_called_once()
        mock_transcription.transcribe.assert_called_once()
        mock_phonetic.analyze_pronunciation.assert_called_once()
        mock_llm.generate_pronunciation_feedback.assert_called_once()
        mock_repo.save_analysis.assert_called_once_with(
            "user123", "hello world", result
        )

    def test_analyze_recording_without_llm(self):
        """Test pronunciation analysis without LLM feedback."""
        # Given
        mock_audio = Mock()
        mock_transcription = Mock()
        mock_phonetic = Mock()

        mock_audio.process_recording.return_value = ProcessedAudio(
            waveform=np.array([0.1, 0.2]),
            sample_rate=16000,
            duration_seconds=1.0
        )

        mock_transcription.transcribe.return_value = Transcription(
            text="test",
            phonemes="tɛst",
            confidence=0.9,
            language="en-us"
        )

        mock_phonetic.analyze_pronunciation.return_value = PronunciationAnalysis(
            metrics=PronunciationMetrics(
                word_accuracy=1.0,
                phoneme_accuracy=0.85,
                phoneme_error_rate=0.15,
                correct_words=1,
                total_words=1,
                substitutions=1,
                insertions=0,
                deletions=0
            ),
            per_word_comparison=[WordComparison(
                word="test",
                ref_phonemes="tɛst",
                rec_phonemes="tɛst",
                match=True,
                phoneme_accuracy=0.85
            )],
            ipa_breakdown=[],
            unique_symbols=set(),
            suggested_drill_words=[]
        )

        service = PronunciationPracticeService(
            audio_service=mock_audio,
            transcription_service=mock_transcription,
            phonetic_service=mock_phonetic,
            llm_service=None,  # No LLM
            repository=None
        )

        config = PracticeConfig(use_llm_feedback=False)

        # When
        result = service.analyze_recording(
            audio_bytes=b"audio",
            reference_text="test",
            user_id="user123",
            config=config
        )

        # Then
        assert result.llm_feedback is None
        assert result.analysis.metrics.phoneme_accuracy == 0.85

    def test_analyze_recording_with_llm_but_disabled(self):
        """Test that LLM is not called when disabled in config."""
        # Given
        mock_audio = Mock()
        mock_transcription = Mock()
        mock_phonetic = Mock()
        mock_llm = Mock()

        mock_audio.process_recording.return_value = ProcessedAudio(
            waveform=np.array([0.1]),
            sample_rate=16000,
            duration_seconds=1.0
        )

        mock_transcription.transcribe.return_value = Transcription(
            text="test",
            phonemes="tɛst",
            confidence=0.9,
            language="en-us"
        )

        mock_phonetic.analyze_pronunciation.return_value = PronunciationAnalysis(
            metrics=PronunciationMetrics(
                word_accuracy=1.0,
                phoneme_accuracy=0.8,
                phoneme_error_rate=0.2,
                correct_words=1,
                total_words=1,
                substitutions=1,
                insertions=0,
                deletions=0
            ),
            per_word_comparison=[],
            ipa_breakdown=[],
            unique_symbols=set(),
            suggested_drill_words=[]
        )

        service = PronunciationPracticeService(
            audio_service=mock_audio,
            transcription_service=mock_transcription,
            phonetic_service=mock_phonetic,
            llm_service=mock_llm,
            repository=None
        )

        config = PracticeConfig(use_llm_feedback=False)

        # When
        result = service.analyze_recording(
            audio_bytes=b"audio",
            reference_text="test",
            user_id="user123",
            config=config
        )

        # Then
        assert result.llm_feedback is None
        mock_llm.generate_pronunciation_feedback.assert_not_called()

    def test_analyze_recording_audio_failure(self):
        """Test that audio processing failure raises PronunciationError."""
        # Given
        mock_audio = Mock()
        mock_audio.process_recording.side_effect = Exception("Audio processing failed")

        service = PronunciationPracticeService(
            audio_service=mock_audio,
            transcription_service=Mock(),
            phonetic_service=Mock(),
            llm_service=None,
            repository=None
        )

        # When/Then
        with pytest.raises(PronunciationError, match="Pronunciation analysis failed"):
            service.analyze_recording(
                audio_bytes=b"audio",
                reference_text="test",
                user_id="user123",
                config=PracticeConfig()
            )

    def test_analyze_recording_transcription_failure(self):
        """Test that transcription failure raises PronunciationError."""
        # Given
        mock_audio = Mock()
        mock_transcription = Mock()

        mock_audio.process_recording.return_value = ProcessedAudio(
            waveform=np.array([0.1]),
            sample_rate=16000,
            duration_seconds=1.0
        )

        mock_transcription.transcribe.side_effect = Exception("ASR failed")

        service = PronunciationPracticeService(
            audio_service=mock_audio,
            transcription_service=mock_transcription,
            phonetic_service=Mock(),
            llm_service=None,
            repository=None
        )

        # When/Then
        with pytest.raises(PronunciationError, match="Pronunciation analysis failed"):
            service.analyze_recording(
                audio_bytes=b"audio",
                reference_text="test",
                user_id="user123",
                config=PracticeConfig()
            )

    def test_analyze_recording_phonetic_failure(self):
        """Test that phonetic analysis failure raises PronunciationError."""
        # Given
        mock_audio = Mock()
        mock_transcription = Mock()
        mock_phonetic = Mock()

        mock_audio.process_recording.return_value = ProcessedAudio(
            waveform=np.array([0.1]),
            sample_rate=16000,
            duration_seconds=1.0
        )

        mock_transcription.transcribe.return_value = Transcription(
            text="test",
            phonemes="tɛst",
            confidence=0.9,
            language="en-us"
        )

        mock_phonetic.analyze_pronunciation.side_effect = Exception("Phonetic analysis failed")

        service = PronunciationPracticeService(
            audio_service=mock_audio,
            transcription_service=mock_transcription,
            phonetic_service=mock_phonetic,
            llm_service=None,
            repository=None
        )

        # When/Then
        with pytest.raises(PronunciationError, match="Pronunciation analysis failed"):
            service.analyze_recording(
                audio_bytes=b"audio",
                reference_text="test",
                user_id="user123",
                config=PracticeConfig()
            )

    def test_analyze_recording_llm_failure_continues(self):
        """Test that LLM failure doesn't stop the workflow."""
        # Given
        mock_audio = Mock()
        mock_transcription = Mock()
        mock_phonetic = Mock()
        mock_llm = Mock()

        mock_audio.process_recording.return_value = ProcessedAudio(
            waveform=np.array([0.1]),
            sample_rate=16000,
            duration_seconds=1.0
        )

        mock_transcription.transcribe.return_value = Transcription(
            text="test",
            phonemes="tɛst",
            confidence=0.9,
            language="en-us"
        )

        mock_phonetic.analyze_pronunciation.return_value = PronunciationAnalysis(
            metrics=PronunciationMetrics(
                word_accuracy=1.0,
                phoneme_accuracy=0.9,
                phoneme_error_rate=0.1,
                correct_words=1,
                total_words=1,
                substitutions=0,
                insertions=0,
                deletions=0
            ),
            per_word_comparison=[],
            ipa_breakdown=[],
            unique_symbols=set(),
            suggested_drill_words=[]
        )

        # LLM fails
        mock_llm.generate_pronunciation_feedback.side_effect = Exception("LLM API down")

        service = PronunciationPracticeService(
            audio_service=mock_audio,
            transcription_service=mock_transcription,
            phonetic_service=mock_phonetic,
            llm_service=mock_llm,
            repository=None
        )

        # When
        result = service.analyze_recording(
            audio_bytes=b"audio",
            reference_text="test",
            user_id="user123",
            config=PracticeConfig(use_llm_feedback=True)
        )

        # Then - Should succeed with no LLM feedback
        assert result.llm_feedback is None
        assert result.analysis.metrics.phoneme_accuracy == 0.9

    def test_analyze_recording_without_repository(self):
        """Test that analysis works without repository."""
        # Given
        mock_audio = Mock()
        mock_transcription = Mock()
        mock_phonetic = Mock()

        mock_audio.process_recording.return_value = ProcessedAudio(
            waveform=np.array([0.1]),
            sample_rate=16000,
            duration_seconds=1.0
        )

        mock_transcription.transcribe.return_value = Transcription(
            text="test",
            phonemes="tɛst",
            confidence=0.9,
            language="en-us"
        )

        mock_phonetic.analyze_pronunciation.return_value = PronunciationAnalysis(
            metrics=PronunciationMetrics(
                word_accuracy=1.0,
                phoneme_accuracy=0.9,
                phoneme_error_rate=0.1,
                correct_words=1,
                total_words=1,
                substitutions=0,
                insertions=0,
                deletions=0
            ),
            per_word_comparison=[],
            ipa_breakdown=[],
            unique_symbols=set(),
            suggested_drill_words=[]
        )

        service = PronunciationPracticeService(
            audio_service=mock_audio,
            transcription_service=mock_transcription,
            phonetic_service=mock_phonetic,
            llm_service=None,
            repository=None  # No repository
        )

        # When
        result = service.analyze_recording(
            audio_bytes=b"audio",
            reference_text="test",
            user_id="user123",
            config=PracticeConfig(use_llm_feedback=False)
        )

        # Then - Should succeed
        assert isinstance(result, PracticeResult)

    def test_analyze_recording_custom_config(self):
        """Test pronunciation analysis with custom configuration."""
        # Given
        mock_audio = Mock()
        mock_transcription = Mock()
        mock_phonetic = Mock()

        mock_audio.process_recording.return_value = ProcessedAudio(
            waveform=np.array([0.1]),
            sample_rate=48000,  # Custom sample rate
            duration_seconds=1.0
        )

        mock_transcription.transcribe.return_value = Transcription(
            text="test",
            phonemes="tɛst",
            confidence=0.9,
            language="en-gb"  # British English
        )

        mock_phonetic.analyze_pronunciation.return_value = PronunciationAnalysis(
            metrics=PronunciationMetrics(
                word_accuracy=1.0,
                phoneme_accuracy=0.9,
                phoneme_error_rate=0.1,
                correct_words=1,
                total_words=1,
                substitutions=0,
                insertions=0,
                deletions=0
            ),
            per_word_comparison=[],
            ipa_breakdown=[],
            unique_symbols=set(),
            suggested_drill_words=[]
        )

        service = PronunciationPracticeService(
            audio_service=mock_audio,
            transcription_service=mock_transcription,
            phonetic_service=mock_phonetic,
            llm_service=None,
            repository=None
        )

        custom_config = PracticeConfig(
            sample_rate=48000,
            normalize_audio=False,
            use_g2p=False,
            language="en-gb"
        )

        # When
        result = service.analyze_recording(
            audio_bytes=b"audio",
            reference_text="test",
            user_id="user123",
            config=custom_config
        )

        # Then
        assert isinstance(result, PracticeResult)

        # Verify custom config was passed correctly
        audio_call = mock_audio.process_recording.call_args
        assert audio_call[0][1].sample_rate == 48000
        assert audio_call[0][1].normalize is False

        transcription_call = mock_transcription.transcribe.call_args
        assert transcription_call[0][1].language == "en-gb"
        assert transcription_call[0][1].use_g2p is False


@pytest.mark.unit
class TestPronunciationServiceIntegration:
    """Integration tests for PronunciationPracticeService with realistic scenarios."""

    def test_complete_pronunciation_workflow(self):
        """Test complete pronunciation practice workflow."""
        # Given - Set up realistic mock responses
        mock_audio = Mock()
        mock_transcription = Mock()
        mock_phonetic = Mock()
        mock_llm = Mock()
        mock_repo = Mock()

        # User says "hello world" but mispronounces "world"
        mock_audio.process_recording.return_value = ProcessedAudio(
            waveform=np.array([0.1, 0.2, 0.3, 0.4]),
            sample_rate=16000,
            duration_seconds=2.0
        )

        mock_transcription.transcribe.return_value = Transcription(
            text="hello word",  # Transcribed incorrectly
            phonemes="həˈloʊ wɝd",
            confidence=0.88,
            language="en-us"
        )

        mock_phonetic.analyze_pronunciation.return_value = PronunciationAnalysis(
            metrics=PronunciationMetrics(
                word_accuracy=0.5,  # 1 out of 2 words correct
                phoneme_accuracy=0.7,
                phoneme_error_rate=0.3,
                correct_words=1,
                total_words=2,
                substitutions=3,
                insertions=0,
                deletions=0
            ),
            per_word_comparison=[
                WordComparison(
                    word="hello",
                    ref_phonemes="həˈloʊ",
                    rec_phonemes="həˈloʊ",
                    match=True,
                    phoneme_accuracy=1.0
                ),
                WordComparison(
                    word="world",
                    ref_phonemes="ˈwɝld",
                    rec_phonemes="wɝd",
                    match=False,
                    phoneme_accuracy=0.5
                )
            ],
            ipa_breakdown=[],
            unique_symbols=set(),
            suggested_drill_words=[]
        )

        mock_llm.generate_pronunciation_feedback.return_value = (
            "Good start! You pronounced 'hello' perfectly. "
            "For 'world', make sure to emphasize the 'l' sound at the end: 'wɝld'."
        )

        service = PronunciationPracticeService(
            audio_service=mock_audio,
            transcription_service=mock_transcription,
            phonetic_service=mock_phonetic,
            llm_service=mock_llm,
            repository=mock_repo
        )

        # When
        result = service.analyze_recording(
            audio_bytes=b"user_audio_recording",
            reference_text="hello world",
            user_id="student123",
            config=PracticeConfig()
        )

        # Then - Verify complete workflow
        assert result.analysis.metrics.word_accuracy == 0.5
        assert len(result.analysis.per_word_comparison) == 2
        assert result.analysis.per_word_comparison[0].match is True  # hello correct
        assert result.analysis.per_word_comparison[1].match is False  # world wrong
        assert "world" in result.llm_feedback
        assert result.raw_decoded == "hello word"

        # Verify result was saved
        mock_repo.save_analysis.assert_called_once()
