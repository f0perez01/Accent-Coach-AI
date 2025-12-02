"""
Pronunciation Practice Service (BC4)
"""

from datetime import datetime
from .models import PracticeConfig, PracticeResult


class PronunciationPracticeService:
    """
    BC4: Pronunciation Practice Orchestration

    Responsibilities:
    - Orchestrate full practice flow
    - Generate LLM feedback
    - Save results to repository

    Dependencies:
    - AudioService (BC1)
    - TranscriptionService (BC2)
    - PhoneticAnalysisService (BC3)
    - LLMService (BC6)
    - PronunciationRepository (Infrastructure)
    """

    def __init__(
        self,
        audio_service,
        transcription_service,
        phonetic_service,
        llm_service,
        repository,
    ):
        """
        Dependency Injection - NO globals!

        Args:
            audio_service: AudioService instance
            transcription_service: TranscriptionService instance
            phonetic_service: PhoneticAnalysisService instance
            llm_service: LLMService instance
            repository: PronunciationRepository instance
        """
        self._audio = audio_service
        self._transcription = transcription_service
        self._phonetic = phonetic_service
        self._llm = llm_service
        self._repo = repository

    def analyze_recording(
        self,
        audio_bytes: bytes,
        reference_text: str,
        user_id: str,
        config: PracticeConfig,
    ) -> PracticeResult:
        """
        Full orchestration: audio → ASR → phonetic → LLM → save.

        This is the ONLY place where the full flow is orchestrated.

        Args:
            audio_bytes: User's recorded audio
            reference_text: Expected pronunciation
            user_id: User identifier
            config: Practice configuration

        Returns:
            Complete practice result

        Example:
            >>> service = PronunciationPracticeService(...)
            >>> result = service.analyze_recording(
            ...     audio_bytes=audio,
            ...     reference_text="hello world",
            ...     user_id="user123",
            ...     config=PracticeConfig()
            ... )
            >>> assert result.analysis.metrics.word_accuracy > 0
        """
        # TODO: Implementation in Sprint 4
        # 1. Process audio (AudioService)
        # 2. Transcribe (TranscriptionService)
        # 3. Phonetic analysis (PhoneticAnalysisService)
        # 4. LLM feedback (optional)
        # 5. Build result
        # 6. Save to repository
        raise NotImplementedError("To be implemented in Sprint 4")
