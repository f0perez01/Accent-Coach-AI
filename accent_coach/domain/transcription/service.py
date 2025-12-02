"""
Transcription Service (BC2)
"""

from ..audio.models import ProcessedAudio
from .models import ASRConfig, Transcription


class TranscriptionService:
    """
    BC2: Speech Recognition

    Responsibilities:
    - Transcribe audio to text
    - Manage ASR model lifecycle

    Dependencies:
    - Audio Service (through ProcessedAudio interface)
    """

    def __init__(self, asr_manager):
        """
        Args:
            asr_manager: ASRModelManager instance
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
        # TODO: Implementation
        # 1. Ensure model is loaded
        # 2. Transcribe waveform
        # 3. Return Transcription
        raise NotImplementedError("To be implemented in Sprint 2")
