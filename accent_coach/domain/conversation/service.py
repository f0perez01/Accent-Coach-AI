"""
Conversation Tutor Service (BC5)

Orchestrates conversation practice flow:
Audio → ASR → LLM Feedback → TTS → Save
"""

from typing import Optional
from datetime import datetime

from ..audio.models import AudioConfig, ProcessedAudio
from ..transcription.models import ASRConfig, Transcription
from ...infrastructure.llm.service import LLMService
from .models import (
    ConversationTurn,
    TutorResponse,
    ConversationConfig,
    ConversationSession,
)
from .prompts import PromptBuilder


class ConversationError(Exception):
    """Raised when conversation processing fails."""
    pass


class ConversationService:
    """
    BC5: Conversation Tutoring

    Responsibilities:
    - Process conversation turns (audio → transcript → feedback → audio)
    - Generate tutor feedback using LLM
    - Manage conversation flow
    - Track conversation history

    Dependencies:
    - BC1 (AudioService) - Audio processing and TTS
    - BC2 (TranscriptionService) - Speech-to-text
    - BC6 (LLMService) - Feedback generation
    - Repository (optional) - Persistence
    """

    def __init__(
        self,
        audio_service,
        transcription_service,
        llm_service: LLMService,
        repository=None,
    ):
        """
        Initialize ConversationService with required dependencies.

        Args:
            audio_service: AudioService instance (BC1)
            transcription_service: TranscriptionService instance (BC2)
            llm_service: LLMService instance (BC6)
            repository: Optional ConversationRepository for persistence
        """
        self._audio = audio_service
        self._transcription = transcription_service
        self._llm = llm_service
        self._repo = repository

    def process_turn(
        self,
        audio_bytes: bytes,
        session: ConversationSession,
        config: ConversationConfig,
    ) -> ConversationTurn:
        """
        Process one conversation turn.

        Pipeline:
        1. Audio → ASR (transcription)
        2. Transcript + History → LLM (feedback)
        3. Follow-up question → TTS (audio)
        4. Save turn (optional)

        Args:
            audio_bytes: User's recorded audio
            session: Current conversation session
            config: Conversation configuration

        Returns:
            ConversationTurn with transcript, feedback, and follow-up audio

        Raises:
            ConversationError: If any step fails
        """
        try:
            # Step 1: Transcribe user speech
            user_transcript = self._transcribe_audio(audio_bytes, config)

            if not user_transcript or user_transcript.strip() == "":
                raise ConversationError("Could not transcribe audio. Please try again.")

            # Step 2: Generate tutor feedback using LLM
            tutor_response = self._generate_feedback(
                user_transcript,
                session.get_recent_history(config.max_history_turns),
                config,
            )

            # Step 3: Generate TTS for follow-up question
            follow_up_audio = None
            if config.generate_audio and tutor_response.follow_up_question:
                follow_up_audio = self._generate_follow_up_audio(
                    tutor_response.follow_up_question
                )

            # Step 4: Create conversation turn
            turn = ConversationTurn(
                user_transcript=user_transcript,
                tutor_response=tutor_response,
                follow_up_audio=follow_up_audio,
                timestamp=datetime.now(),
            )

            # Step 5: Add to session
            session.add_turn(turn)

            # Step 6: Save to repository (optional)
            if self._repo:
                self._repo.save_turn(session.session_id, session.user_id, turn)

            return turn

        except Exception as e:
            raise ConversationError(f"Failed to process conversation turn: {str(e)}")

    def _transcribe_audio(self, audio_bytes: bytes, config: ConversationConfig) -> str:
        """
        Transcribe user's audio to text.

        Args:
            audio_bytes: Raw audio bytes
            config: Configuration with ASR settings

        Returns:
            Transcribed text

        Raises:
            ConversationError: If transcription fails
        """
        try:
            # Process audio
            audio_config = AudioConfig(
                sample_rate=config.sample_rate,
                normalize=True,
            )
            processed_audio = self._audio.process_recording(audio_bytes, audio_config)

            # Transcribe (no G2P needed for conversation)
            asr_config = ASRConfig(
                model_name=config.asr_model,
                use_g2p=False,  # We only need text, not phonemes
                language="en",
            )
            transcription = self._transcription.transcribe(processed_audio, asr_config)

            return transcription.text.strip()

        except Exception as e:
            raise ConversationError(f"Transcription failed: {str(e)}")

    def _generate_feedback(
        self,
        user_transcript: str,
        conversation_history: list,
        config: ConversationConfig,
    ) -> TutorResponse:
        """
        Generate tutor feedback using LLM.

        Args:
            user_transcript: What the user said
            conversation_history: Previous turns for context
            config: Configuration with LLM settings

        Returns:
            TutorResponse with corrections and follow-up

        Raises:
            ConversationError: If LLM call fails
        """
        try:
            # Build prompt
            prompt = PromptBuilder.build_prompt(
                user_transcript,
                conversation_history,
                config,
            )

            # Call LLM
            llm_output = self._llm.generate_conversation_feedback(
                system_prompt=prompt["system"],
                user_message=prompt["user"],
                model=config.llm_model,
                temperature=0.3,
                max_tokens=500,
            )

            # Parse response
            parsed = PromptBuilder.parse_llm_response(llm_output)

            # Build TutorResponse
            return TutorResponse(
                correction=parsed.get("correction", ""),
                explanation=parsed.get("explanation", ""),
                improved_version=parsed.get("improved_version", ""),
                follow_up_question=parsed.get("follow_up_question", "Could you tell me more?"),
                errors_detected=parsed.get("errors_detected", []),
                assistant_response=parsed.get("assistant_response", ""),
            )

        except Exception as e:
            # Fallback response if LLM fails
            return TutorResponse(
                correction="",
                explanation=f"Error getting feedback: {str(e)}",
                improved_version=user_transcript,
                follow_up_question="Could you tell me more about that?",
                errors_detected=[],
                assistant_response=f"I heard: '{user_transcript}'. Could you tell me more?",
            )

    def _generate_follow_up_audio(self, text: str) -> Optional[bytes]:
        """
        Generate TTS audio for follow-up question.

        Args:
            text: Follow-up question text

        Returns:
            Audio bytes or None if generation fails
        """
        try:
            return self._audio.generate_audio(text)
        except Exception:
            # Non-fatal: user can still read the text
            return None

    def create_session(
        self,
        user_id: str,
        config: ConversationConfig,
    ) -> ConversationSession:
        """
        Create a new conversation session.

        Args:
            user_id: User identifier
            config: Conversation configuration

        Returns:
            New ConversationSession
        """
        session_id = f"conv_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            topic=config.topic or "General Conversation",
            level=config.user_level,
            mode=config.mode,
            started_at=datetime.now(),
        )

        # Save to repository if available
        if self._repo:
            self._repo.create_session(session)

        return session

    def close_session(self, session: ConversationSession):
        """
        Mark a session as completed.

        Args:
            session: Session to close
        """
        session.status = "completed"

        if self._repo:
            self._repo.update_session(session)
