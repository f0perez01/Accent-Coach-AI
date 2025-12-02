"""
Conversation Tutor Service (BC5)
"""

from typing import List, Dict
from .models import ConversationMode, TurnResult


class ConversationTutorService:
    """
    BC5: Conversation Tutoring

    Responsibilities:
    - Process conversation turns
    - Generate feedback (grammar, fluency)
    - Generate follow-up questions

    Dependencies:
    - TranscriptionService (BC2)
    - AudioService (BC1) for TTS
    - LLMService (BC6)
    - ConversationRepository (Infrastructure)
    """

    def __init__(
        self, transcription_service, audio_service, llm_service, repository
    ):
        """
        Args:
            transcription_service: TranscriptionService instance
            audio_service: AudioService instance
            llm_service: LLMService instance
            repository: ConversationRepository instance
        """
        self._transcription = transcription_service
        self._audio = audio_service
        self._llm = llm_service
        self._repo = repository

    def process_turn(
        self,
        session_id: str,
        audio_bytes: bytes,
        conversation_history: List[Dict],
        user_level: str,
        mode: ConversationMode,
    ) -> TurnResult:
        """
        Process one conversation turn.

        Args:
            session_id: Conversation session identifier
            audio_bytes: User's audio response
            conversation_history: Previous turns
            user_level: CEFR level (A2, B1-B2, C1-C2)
            mode: Practice (immediate) or Exam (deferred feedback)

        Returns:
            Turn result with feedback and follow-up
        """
        # TODO: Implementation in Sprint 5
        # 1. Transcribe user speech
        # 2. Generate feedback using LLM
        # 3. Generate TTS for follow-up
        # 4. Save turn
        raise NotImplementedError("To be implemented in Sprint 5")
