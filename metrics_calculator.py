from typing import List, Dict


class MetricsCalculator:
    """Encapsulates pronunciation accuracy metrics calculation.
    
    Responsibilities:
    - Calculate word-level accuracy
    - Calculate phoneme-level accuracy and error rates
    - Count error types (substitutions, insertions, deletions)
    - Pure logic, no I/O or Streamlit dependencies
    """

    @staticmethod
    def align_sequences(a: List[str], b: List[str]) -> tuple:
        """Align two sequences using Needleman-Wunsch algorithm.
        
        This is imported from the main app for now.
        In production, move sequence_align import here.
        """
        from sequence_align.pairwise import needleman_wunsch
        return needleman_wunsch(a, b, match_score=2, mismatch_score=-1, indel_score=-1, gap="_")

    @staticmethod
    def calculate(per_word_comparison: List[Dict]) -> Dict:
        """Calculate pronunciation accuracy metrics.
        
        Args:
            per_word_comparison: List of dicts with keys:
                - word: str
                - ref_phonemes: str
                - rec_phonemes: str
                - match: bool
                
        Returns:
            Dict with keys:
            - word_accuracy (%)
            - phoneme_accuracy (%)
            - phoneme_error_rate (%)
            - total_words, correct_words
            - total_phonemes, correct_phonemes
            - substitutions, insertions, deletions (error counts)
        """
        total_words = len(per_word_comparison)
        correct_words = sum(1 for item in per_word_comparison if item['match'])

        # Calculate phoneme-level metrics
        total_phonemes = 0
        correct_phonemes = 0
        substitutions = 0
        insertions = 0
        deletions = 0

        for item in per_word_comparison:
            ref = item['ref_phonemes']
            rec = item['rec_phonemes']

            # Simple character-level comparison
            ref_chars = list(ref) if ref else []
            rec_chars = list(rec) if rec else []

            total_phonemes += len(ref_chars)

            # Align at character level for detailed metrics
            if ref == rec:
                correct_phonemes += len(ref_chars)
            else:
                aligned_ref, aligned_rec = MetricsCalculator.align_sequences(ref_chars, rec_chars)
                for r, p in zip(aligned_ref, aligned_rec):
                    if r == p and r != "_":
                        correct_phonemes += 1
                    elif r != "_" and p == "_":
                        deletions += 1
                    elif r == "_" and p != "_":
                        insertions += 1
                    elif r != p and r != "_" and p != "_":
                        substitutions += 1

        word_accuracy = (correct_words / total_words * 100) if total_words > 0 else 0
        phoneme_accuracy = (correct_phonemes / total_phonemes * 100) if total_phonemes > 0 else 0
        phoneme_error_rate = 100 - phoneme_accuracy

        return {
            'word_accuracy': word_accuracy,
            'phoneme_accuracy': phoneme_accuracy,
            'phoneme_error_rate': phoneme_error_rate,
            'total_words': total_words,
            'correct_words': correct_words,
            'total_phonemes': total_phonemes,
            'correct_phonemes': correct_phonemes,
            'substitutions': substitutions,
            'insertions': insertions,
            'deletions': deletions,
        }
