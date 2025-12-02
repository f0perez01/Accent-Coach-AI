"""
Phonetic Analysis Service (BC3)
"""

from typing import List
from .models import (
    PronunciationAnalysis,
    PronunciationMetrics,
    WordComparison,
    IPABreakdown,
)


class PhoneticAnalysisService:
    """
    BC3: Phonetic Analysis & IPA

    Responsibilities:
    - G2P (Grapheme-to-Phoneme) conversion
    - Phoneme alignment (Needleman-Wunsch)
    - Pronunciation metrics calculation
    - IPA educational data generation
    - Drill word suggestion (business logic)

    Dependencies: NONE (pure logic, 100% testable)
    """

    def __init__(
        self,
        phoneme_processor,
        ipa_definitions_manager,
        syllabifier,
        metrics_calculator,
    ):
        """
        Args:
            phoneme_processor: PhonemeProcessor instance
            ipa_definitions_manager: IPADefinitionsManager instance
            syllabifier: Syllabifier instance
            metrics_calculator: MetricsCalculator instance
        """
        self._processor = phoneme_processor
        self._ipa_defs = ipa_definitions_manager
        self._syllabifier = syllabifier
        self._metrics = metrics_calculator

    def analyze_pronunciation(
        self, reference_text: str, recorded_text: str, lang: str = "en-us"
    ) -> PronunciationAnalysis:
        """
        Analyze pronunciation quality.

        Args:
            reference_text: Expected text
            recorded_text: What was actually said (from ASR)
            lang: Language code

        Returns:
            Complete pronunciation analysis

        Example:
            >>> service = PhoneticAnalysisService(...)
            >>> analysis = service.analyze_pronunciation(
            ...     reference_text="hello world",
            ...     recorded_text="halo world"
            ... )
            >>> assert "hello" in analysis.suggested_drill_words
        """
        # TODO: Implementation in Sprint 3
        # 1. Generate phonemes (G2P)
        # 2. Align phonemes (Needleman-Wunsch)
        # 3. Calculate metrics
        # 4. Generate IPA breakdown
        # 5. Suggest drill words
        raise NotImplementedError("To be implemented in Sprint 3")

    def _suggest_drill_words(self, alignment: List[WordComparison]) -> List[str]:
        """
        Business logic: Which words need practice?

        Criteria:
        - Word doesn't match exactly, OR
        - Phoneme accuracy < 80%

        Args:
            alignment: Per-word comparison results

        Returns:
            List of words that need practice
        """
        drill_words = []
        for word_data in alignment:
            if not word_data.match or word_data.phoneme_accuracy < 80:
                drill_words.append(word_data.word)
        return drill_words
