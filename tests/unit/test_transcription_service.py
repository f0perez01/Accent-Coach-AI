"""
Unit tests for Transcription Service

Testing with mocked ASR manager (no actual model loading).
"""

import pytest
import numpy as np
from unittest.mock import Mock
from accent_coach.domain.transcription import (
    TranscriptionService,
    TranscriptionError,
    ASRConfig,
    Transcription,
    ASRModelManager,
)
from accent_coach.domain.audio import ProcessedAudio


@pytest.mark.unit
class TestTranscriptionService:
    """Test TranscriptionService with mocked ASR manager."""

    def test_transcribe_success(self):
        """Test successful transcription."""
        # Given
        mock_asr = Mock(spec=ASRModelManager)
        mock_asr.is_loaded.return_value = True
        mock_asr.transcribe.return_value = ("hello world", "h ɛ l oʊ w ɜr l d")

        service = TranscriptionService(asr_manager=mock_asr)

        audio = ProcessedAudio(
            waveform=np.random.randn(16000).astype(np.float32),
            sample_rate=16000,
            duration_seconds=1.0,
        )

        config = ASRConfig(model_name="facebook/wav2vec2-base-960h")

        # When
        result = service.transcribe(audio, config)

        # Then
        assert isinstance(result, Transcription)
        assert result.text == "hello world"
        assert result.phonemes == "h ɛ l oʊ w ɜr l d"
        assert result.confidence == 1.0
        assert result.language == "en-us"

        # Verify ASR manager was called correctly
        mock_asr.transcribe.assert_called_once()
        call_args = mock_asr.transcribe.call_args
        assert call_args.kwargs["sr"] == 16000
        assert call_args.kwargs["use_g2p"] is True
        assert call_args.kwargs["lang"] == "en-us"

    def test_transcribe_loads_model_if_needed(self):
        """Test that model is loaded if not already loaded."""
        # Given
        mock_asr = Mock(spec=ASRModelManager)
        mock_asr.is_loaded.return_value = False
        mock_asr.transcribe.return_value = ("test", "t ɛ s t")

        service = TranscriptionService(asr_manager=mock_asr)

        audio = ProcessedAudio(
            waveform=np.random.randn(16000).astype(np.float32),
            sample_rate=16000,
            duration_seconds=1.0,
        )

        config = ASRConfig(model_name="facebook/wav2vec2-base-960h", hf_token="test_token")

        # When
        service.transcribe(audio, config)

        # Then
        # Should have called load_model with correct parameters
        mock_asr.load_model.assert_called_once_with("facebook/wav2vec2-base-960h", "test_token")

    def test_transcribe_no_asr_manager(self):
        """Test transcription fails without ASR manager."""
        # Given
        service = TranscriptionService(asr_manager=None)

        audio = ProcessedAudio(
            waveform=np.random.randn(16000).astype(np.float32),
            sample_rate=16000,
            duration_seconds=1.0,
        )

        config = ASRConfig()

        # When/Then
        with pytest.raises(TranscriptionError, match="ASR manager not initialized"):
            service.transcribe(audio, config)

    def test_transcribe_asr_failure(self):
        """Test handling of ASR transcription failure."""
        # Given
        mock_asr = Mock(spec=ASRModelManager)
        mock_asr.is_loaded.return_value = True
        mock_asr.transcribe.side_effect = RuntimeError("Model error")

        service = TranscriptionService(asr_manager=mock_asr)

        audio = ProcessedAudio(
            waveform=np.random.randn(16000).astype(np.float32),
            sample_rate=16000,
            duration_seconds=1.0,
        )

        config = ASRConfig()

        # When/Then
        with pytest.raises(TranscriptionError, match="Transcription failed"):
            service.transcribe(audio, config)

    def test_transcribe_with_custom_language(self):
        """Test transcription with custom language configuration."""
        # Given
        mock_asr = Mock(spec=ASRModelManager)
        mock_asr.is_loaded.return_value = True
        mock_asr.transcribe.return_value = ("hola mundo", "o l a m u n d o")

        service = TranscriptionService(asr_manager=mock_asr)

        audio = ProcessedAudio(
            waveform=np.random.randn(16000).astype(np.float32),
            sample_rate=16000,
            duration_seconds=1.0,
        )

        config = ASRConfig(language="es-es", use_g2p=True)

        # When
        result = service.transcribe(audio, config)

        # Then
        assert result.language == "es-es"

        # Verify correct language was passed to ASR
        call_args = mock_asr.transcribe.call_args
        assert call_args.kwargs["lang"] == "es-es"

    def test_transcribe_without_g2p(self):
        """Test transcription with G2P disabled."""
        # Given
        mock_asr = Mock(spec=ASRModelManager)
        mock_asr.is_loaded.return_value = True
        mock_asr.transcribe.return_value = ("hello", "hello")

        service = TranscriptionService(asr_manager=mock_asr)

        audio = ProcessedAudio(
            waveform=np.random.randn(16000).astype(np.float32),
            sample_rate=16000,
            duration_seconds=1.0,
        )

        config = ASRConfig(use_g2p=False)

        # When
        result = service.transcribe(audio, config)

        # Then
        call_args = mock_asr.transcribe.call_args
        assert call_args.kwargs["use_g2p"] is False


@pytest.mark.unit
class TestASRModelManager:
    """Test ASRModelManager basic functionality."""

    def test_initialization(self):
        """Test ASR manager initialization."""
        # Given/When
        manager = ASRModelManager(
            default_model="facebook/wav2vec2-base-960h",
            model_options={"base": "facebook/wav2vec2-base-960h"},
        )

        # Then
        assert manager.default_model == "facebook/wav2vec2-base-960h"
        assert manager.device in ["cpu", "cuda"]
        assert manager.processor is None
        assert manager.model is None
        assert not manager.is_loaded()

    def test_is_loaded_returns_false_initially(self):
        """Test that is_loaded returns False before loading."""
        # Given
        manager = ASRModelManager(
            default_model="test",
            model_options={},
        )

        # When/Then
        assert not manager.is_loaded()

    def test_is_phoneme_model_returns_false_without_processor(self):
        """Test _is_phoneme_model returns False without processor."""
        # Given
        manager = ASRModelManager(
            default_model="test",
            model_options={},
        )

        # When/Then
        assert not manager._is_phoneme_model()
