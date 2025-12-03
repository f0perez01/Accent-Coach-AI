"""
Unit tests for Audio Service

Testing with mocks and sample audio data.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from accent_coach.domain.audio import (
    AudioService,
    AudioValidationError,
    AudioConfig,
    ProcessedAudio,
    AudioProcessor,
    TTSGenerator,
)


@pytest.mark.unit
class TestAudioProcessor:
    """Test AudioProcessor utilities."""

    def test_normalize_audio(self):
        """Test audio normalization."""
        # Given
        waveform = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)

        # When
        normalized = AudioProcessor.normalize_audio(waveform, target_level=1.0)

        # Then
        assert normalized.max() == pytest.approx(1.0)
        assert normalized.min() == pytest.approx(0.2)

    def test_normalize_audio_silent(self):
        """Test normalization of silent audio."""
        # Given
        waveform = np.zeros(100, dtype=np.float32)

        # When
        normalized = AudioProcessor.normalize_audio(waveform)

        # Then
        assert np.all(normalized == 0)


@pytest.mark.unit
class TestTTSGenerator:
    """Test TTS Generator."""

    @patch("gtts.gTTS")
    def test_generate_audio_success(self, mock_gtts_class):
        """Test successful TTS generation."""
        # Given
        mock_tts = Mock()
        mock_gtts_class.return_value = mock_tts

        # Mock the write_to_fp to write some bytes
        def write_mock(fp):
            fp.write(b"fake_audio_data")

        mock_tts.write_to_fp.side_effect = write_mock

        generator = TTSGenerator()

        # When
        result = generator.generate_audio("hello world", "en")

        # Then
        assert result is not None
        assert b"fake_audio_data" in result
        mock_gtts_class.assert_called_once_with(text="hello world", lang="en", slow=False)

    @patch("gtts.gTTS")
    def test_generate_slow_audio(self, mock_gtts_class):
        """Test slow TTS generation for practice."""
        # Given
        mock_tts = Mock()
        mock_gtts_class.return_value = mock_tts

        def write_mock(fp):
            fp.write(b"slow_audio_data")

        mock_tts.write_to_fp.side_effect = write_mock

        generator = TTSGenerator()

        # When
        result = generator.generate_slow_audio("practice", "en")

        # Then
        assert result is not None
        assert b"slow_audio_data" in result
        mock_gtts_class.assert_called_once_with(text="practice", lang="en", slow=True)

    @patch("gtts.gTTS")
    def test_generate_audio_failure(self, mock_gtts_class):
        """Test TTS generation failure handling."""
        # Given
        mock_gtts_class.side_effect = Exception("API error")

        generator = TTSGenerator()

        # When
        result = generator.generate_audio("test", "en")

        # Then
        assert result is None


@pytest.mark.unit
class TestAudioService:
    """Test AudioService with mocked components."""

    def test_process_recording_success(self):
        """Test successful audio processing."""
        # Given
        service = AudioService()

        # Create fake audio bytes (minimal WAV header + data)
        fake_wav = self._create_fake_wav()

        config = AudioConfig(sample_rate=16000, normalize=True)

        # Mock the processor to return valid data
        with patch.object(
            service._processor, "load_from_bytes", return_value=(np.random.randn(16000).astype(np.float32) * 0.5, 16000)
        ):
            # When
            result = service.process_recording(fake_wav, config)

            # Then
            assert isinstance(result, ProcessedAudio)
            assert result.sample_rate == 16000
            assert result.duration_seconds == pytest.approx(1.0)
            assert result.waveform is not None

    def test_process_recording_invalid_audio(self):
        """Test processing with invalid audio."""
        # Given
        service = AudioService()
        config = AudioConfig()

        # Mock processor to return None (failed load)
        with patch.object(service._processor, "load_from_bytes", return_value=(None, None)):
            # When/Then
            with pytest.raises(AudioValidationError, match="Invalid audio"):
                service.process_recording(b"invalid", config)

    def test_process_recording_silent_audio(self):
        """Test processing with silent audio."""
        # Given
        service = AudioService()
        config = AudioConfig()

        # Mock processor to return silent audio
        silent_audio = np.zeros(16000, dtype=np.float32)
        with patch.object(service._processor, "load_from_bytes", return_value=(silent_audio, 16000)):
            # When/Then
            with pytest.raises(AudioValidationError, match="silent"):
                service.process_recording(b"silent", config)

    def test_process_recording_too_short(self):
        """Test processing audio that's too short."""
        # Given
        service = AudioService()
        config = AudioConfig()

        # Mock processor to return very short audio (< 0.1 seconds)
        short_audio = np.random.randn(100).astype(np.float32)  # 100 samples at 16000 Hz = 0.00625s
        with patch.object(service._processor, "load_from_bytes", return_value=(short_audio, 16000)):
            # When/Then
            with pytest.raises(AudioValidationError, match="too short"):
                service.process_recording(b"short", config)

    def test_generate_tts_normal(self):
        """Test normal TTS generation."""
        # Given
        mock_tts = Mock()
        mock_tts.generate_audio.return_value = b"audio_data"

        service = AudioService(tts_generator=mock_tts)

        # When
        result = service.generate_tts("hello", "en", slow=False)

        # Then
        assert result == b"audio_data"
        mock_tts.generate_audio.assert_called_once_with("hello", "en")

    def test_generate_tts_slow(self):
        """Test slow TTS generation."""
        # Given
        mock_tts = Mock()
        mock_tts.generate_slow_audio.return_value = b"slow_audio_data"

        service = AudioService(tts_generator=mock_tts)

        # When
        result = service.generate_tts("practice", "en", slow=True)

        # Then
        assert result == b"slow_audio_data"
        mock_tts.generate_slow_audio.assert_called_once_with("practice", "en")

    def test_normalization_applied(self):
        """Test that normalization is applied when configured."""
        # Given
        service = AudioService()
        config = AudioConfig(normalize=True)

        # Create audio that needs normalization (max = 0.5)
        audio = np.random.randn(16000).astype(np.float32) * 0.5

        with patch.object(service._processor, "load_from_bytes", return_value=(audio, 16000)):
            # When
            result = service.process_recording(b"audio", config)

            # Then
            # After normalization, max should be close to 0.95 (default target)
            assert np.abs(result.waveform).max() > 0.9

    def test_normalization_skipped(self):
        """Test that normalization is skipped when not configured."""
        # Given
        service = AudioService()
        config = AudioConfig(normalize=False)

        # Create deterministic audio with known max value
        audio = np.linspace(-0.5, 0.5, 16000).astype(np.float32)

        with patch.object(service._processor, "load_from_bytes", return_value=(audio, 16000)):
            # When
            result = service.process_recording(b"audio", config)

            # Then
            # Without normalization, waveform should be unchanged
            assert np.allclose(result.waveform, audio)

    @staticmethod
    def _create_fake_wav():
        """Create minimal fake WAV file bytes for testing."""
        # Simplified - in real tests, you'd use a proper WAV file
        return b"RIFF" + b"\x00" * 100
