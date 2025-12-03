"""
Transcription Service (BC2)
"""

from typing import Optional
from ..audio.models import ProcessedAudio
from .models import ASRConfig, Transcription
from .asr_manager import ASRModelManager


class TranscriptionError(Exception):
    """Raised when transcription fails."""
    pass


class TranscriptionService:
    """
    BC2: Speech Recognition

    Responsibilities:
    - Transcribe audio to text
    - Manage ASR model lifecycle

    Dependencies:
    - Audio Service (through ProcessedAudio interface)
    """

    def __init__(self, asr_manager: Optional[ASRModelManager] = None):
        """
        Args:
            asr_manager: ASRModelManager instance (optional, lazy-loaded)
        """
        self._asr = asr_manager

    def transcribe(
        self,
        audio: ProcessedAudio,
        config: ASRConfig
    ) -> Transcription:
        """
        Transcribe audio to text.

        Args:
            audio: Processed audio from AudioService
            config: ASR configuration

        Returns:
            Transcription with text and confidence

        Raises:
            TranscriptionError: If transcription fails
        """
        if self._asr is None:
            raise TranscriptionError("ASR manager not initialized")

        try:
            # Ensure model is loaded
            if not self._asr.is_loaded():
                self._asr.load_model(config.model_name, config.hf_token)

            # Transcribe
            text, phonemes = self._asr.transcribe(
                audio=audio.waveform,
                sr=audio.sample_rate,
                use_g2p=config.use_g2p,
                lang=config.language
            )

            # Return transcription
            return Transcription(
                text=text,
                phonemes=phonemes,
                confidence=1.0,  # ASR models don't provide confidence scores
                language=config.language
            )

        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {e}")
