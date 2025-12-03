"""
Audio Processing Service (BC1)
"""

from typing import Optional
from .models import AudioConfig, ProcessedAudio
from .audio_processor import AudioProcessor, TTSGenerator, AudioValidator


class AudioValidationError(Exception):
    """Raised when audio validation fails."""
    pass


class AudioService:
    """
    BC1: Audio Processing & Enhancement

    Responsibilities:
    - Process raw audio for ASR consumption
    - Generate TTS audio

    Dependencies: NONE (pure processing)
    """

    def __init__(self, processor: AudioProcessor = None, tts_generator: TTSGenerator = None):
        """
        Args:
            processor: AudioProcessor instance (defaults to AudioProcessor)
            tts_generator: TTSGenerator instance (defaults to TTSGenerator)
        """
        self._processor = processor or AudioProcessor()
        self._tts = tts_generator or TTSGenerator()

    def process_recording(
        self,
        audio_bytes: bytes,
        config: AudioConfig
    ) -> ProcessedAudio:
        """
        Process raw audio for ASR consumption.

        Args:
            audio_bytes: Raw audio input
            config: Enhancement configuration

        Returns:
            ProcessedAudio with enhanced waveform

        Raises:
            AudioValidationError: If audio is invalid
        """
        # 1. Load audio
        waveform, sr = self._processor.load_from_bytes(audio_bytes, target_sr=config.sample_rate)

        # 2. Validate audio
        is_valid, error_message = AudioValidator.validate_audio_data(waveform, sr)
        if not is_valid:
            raise AudioValidationError(f"Invalid audio: {error_message}")

        # 3. Apply normalization if configured
        if config.normalize:
            waveform = self._processor.normalize_audio(waveform)

        # 4. Return ProcessedAudio
        return ProcessedAudio(
            waveform=waveform,
            sample_rate=sr,
            duration_seconds=len(waveform) / sr
        )

    def generate_tts(self, text: str, lang: str = 'en', slow: bool = False) -> Optional[bytes]:
        """
        Generate speech audio from text.

        Args:
            text: Text to convert to speech
            lang: Language code (default: 'en')
            slow: Whether to generate slow speech for practice

        Returns:
            Audio bytes (MP3 format), or None on failure
        """
        if slow:
            return self._tts.generate_slow_audio(text, lang)
        else:
            return self._tts.generate_audio(text, lang)
