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
from .analyzer import (
    G2PConverter,
    PhonemeTokenizer,
    PhonemeAligner,
    MetricsCalculator,
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

    def __init__(self):
        """Initialize phonetic analysis service with default utilities."""
        pass

    def analyze_pronunciation(
        self,
        reference_text: str,
        recorded_phonemes: str,
        lang: str = "en-us"
    ) -> PronunciationAnalysis:
        """
        Analyze pronunciation quality by comparing reference text to recorded phonemes.

        Args:
            reference_text: Expected text (e.g., "hello world")
            recorded_phonemes: Phonemes from ASR transcription (e.g., "h ɛ l oʊ w ɜr l d")
            lang: Language code (default: "en-us")

        Returns:
            Complete pronunciation analysis with metrics and drill suggestions

        Example:
            >>> service = PhoneticAnalysisService()
            >>> analysis = service.analyze_pronunciation(
            ...     reference_text="hello world",
            ...     recorded_phonemes="h ɛ l oʊ w ɜr l d"
            ... )
            >>> assert analysis.metrics.word_accuracy == 100.0
        """
        # Step 1: Generate reference phonemes from text (G2P)
        lexicon, words = G2PConverter.text_to_phonemes(reference_text, lang)

        # Step 2: Tokenize recorded phonemes
        recorded_tokens = PhonemeTokenizer.tokenize(recorded_phonemes)

        # Step 3: Align phonemes per word
        per_word_ref, per_word_rec = PhonemeAligner.align_per_word(lexicon, recorded_tokens)

        # Step 4: Build per-word comparison
        per_word_comparison_dict = []
        per_word_comparison_models = []

        for i, word in enumerate(words):
            ref_ph = per_word_ref[i]
            rec_ph = per_word_rec[i]
            match = ref_ph == rec_ph

            # Calculate per-word phoneme accuracy
            if match:
                phoneme_accuracy = 100.0
            else:
                # Simple character-level accuracy
                ref_chars = list(ref_ph) if ref_ph else []
                rec_chars = list(rec_ph) if rec_ph else []
                if len(ref_chars) > 0:
                    correct = sum(1 for r, p in zip(ref_chars, rec_chars) if r == p)
                    phoneme_accuracy = (correct / len(ref_chars)) * 100
                else:
                    phoneme_accuracy = 0.0

            # For metrics calculation (dict format)
            per_word_comparison_dict.append({
                'word': word,
                'ref_phonemes': ref_ph,
                'rec_phonemes': rec_ph,
                'match': match
            })

            # For model (WordComparison format)
            per_word_comparison_models.append(WordComparison(
                word=word,
                ref_phonemes=ref_ph,
                rec_phonemes=rec_ph,
                match=match,
                phoneme_accuracy=phoneme_accuracy
            ))

        # Step 5: Calculate overall metrics
        metrics_dict = MetricsCalculator.calculate_metrics(per_word_comparison_dict)

        metrics = PronunciationMetrics(
            word_accuracy=metrics_dict['word_accuracy'],
            phoneme_accuracy=metrics_dict['phoneme_accuracy'],
            phoneme_error_rate=metrics_dict['phoneme_error_rate'],
            correct_words=metrics_dict['correct_words'],
            total_words=metrics_dict['total_words'],
            substitutions=metrics_dict['substitutions'],
            insertions=metrics_dict['insertions'],
            deletions=metrics_dict['deletions'],
        )

        # Step 6: Suggest drill words
        drill_words = self._suggest_drill_words(per_word_comparison_models)

        # Step 7: Create IPA breakdown (placeholder - full implementation in future)
        ipa_breakdown = []
        unique_symbols = set()

        return PronunciationAnalysis(
            metrics=metrics,
            per_word_comparison=per_word_comparison_models,
            ipa_breakdown=ipa_breakdown,
            unique_symbols=unique_symbols,
            suggested_drill_words=drill_words,
        )

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
