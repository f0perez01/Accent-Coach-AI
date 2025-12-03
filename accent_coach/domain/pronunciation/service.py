"""
Pronunciation Practice Service (BC4)
"""

from datetime import datetime
from typing import Optional
from .models import PracticeConfig, PracticeResult
from ..audio.models import AudioConfig
from ..transcription.models import ASRConfig


class PronunciationError(Exception):
    """Raised when pronunciation practice fails."""
    pass


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
        llm_service=None,
        repository=None,
    ):
        """
        Dependency Injection - NO globals!

        Args:
            audio_service: AudioService instance
            transcription_service: TranscriptionService instance
            phonetic_service: PhoneticAnalysisService instance
            llm_service: LLMService instance (optional)
            repository: PronunciationRepository instance (optional)
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

        Raises:
            PronunciationError: If any step in the pipeline fails

        Example:
            >>> service = PronunciationPracticeService(...)
            >>> result = service.analyze_recording(
            ...     audio_bytes=audio,
            ...     reference_text="hello world",
            ...     user_id="user123",
            ...     config=PracticeConfig()
            ... )
            >>> assert result.analysis.metrics.word_accuracy >= 0
        """
        try:
            # Step 1: Process audio (AudioService)
            audio_config = AudioConfig(
                sample_rate=config.sample_rate,
                normalize=config.normalize_audio,
            )
            processed_audio = self._audio.process_recording(audio_bytes, audio_config)

            # Step 2: Transcribe (TranscriptionService)
            asr_config = ASRConfig(
                model_name=config.asr_model,
                use_g2p=config.use_g2p,
                language=config.language,
            )
            transcription = self._transcription.transcribe(processed_audio, asr_config)

            # Step 3: Phonetic analysis (PhoneticAnalysisService)
            analysis = self._phonetic.analyze_pronunciation(
                reference_text=reference_text,
                recorded_phonemes=transcription.phonemes,
                lang=config.language
            )

            # Step 4: LLM feedback (optional)
            llm_feedback = None
            if config.use_llm_feedback and self._llm:
                llm_feedback = self._get_llm_feedback(
                    reference_text=reference_text,
                    analysis=analysis
                )

            # Step 5: Build result
            result = PracticeResult(
                analysis=analysis,
                llm_feedback=llm_feedback,
                raw_decoded=transcription.text,
                recorded_phoneme_str=transcription.phonemes,
            )

            # Step 6: Save to repository (optional)
            if self._repo:
                self._repo.save_analysis(user_id, reference_text, result)

            return result

        except Exception as e:
            raise PronunciationError(f"Pronunciation analysis failed: {e}")

    def _get_llm_feedback(self, reference_text: str, analysis) -> Optional[str]:
        """
        Get LLM feedback for pronunciation mistakes.

        Args:
            reference_text: Expected text
            analysis: Phonetic analysis result

        Returns:
            LLM feedback text or None on failure
        """
        try:
            # Convert WordComparison objects to dicts for LLM service
            per_word_comparison = [
                {
                    'word': wc.word,
                    'match': wc.match,
                }
                for wc in analysis.per_word_comparison
            ]

            feedback = self._llm.generate_pronunciation_feedback(
                reference_text=reference_text,
                per_word_comparison=per_word_comparison
            )

            return feedback

        except Exception:
            # LLM feedback is optional - don't fail the whole flow
            return None
