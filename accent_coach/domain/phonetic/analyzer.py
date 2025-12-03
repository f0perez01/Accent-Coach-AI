"""
Phonetic Analyzer Implementation

Migrated from metrics_calculator.py and analysis_pipeline.py with improvements.
"""

import re
from typing import List, Tuple, Dict
from gruut import sentences
from phonemizer.punctuation import Punctuation


class PhonemeTokenizer:
    """Tokenizes phoneme strings into individual phoneme units."""

    @staticmethod
    def tokenize(phoneme_str: str) -> List[str]:
        """
        Tokenize a phoneme string into individual phoneme tokens.

        Args:
            phoneme_str: String containing phonemes (space-separated or concatenated)

        Returns:
            List of individual phoneme tokens

        Examples:
            >>> PhonemeTokenizer.tokenize("h ɛ l oʊ")
            ['h', 'ɛ', 'l', 'oʊ']
            >>> PhonemeTokenizer.tokenize("hɛloʊ")
            ['h', 'ɛ', 'l', 'oʊ']
        """
        s = phoneme_str.strip()
        if not s:
            return []

        # If already space-separated, just split
        if " " in s:
            return s.split()

        # Otherwise, use regex to split IPA characters
        pattern = r"[a-zA-Zʰɪʌɒəɜɑɔɛʊʏœøɯɨɫɹːˈˌ˞̃͜͡d͡ʒ]+|[^\s]"
        tokens = re.findall(pattern, s)
        return [t for t in tokens if t]


class SequenceAligner:
    """Performs sequence alignment using Needleman-Wunsch algorithm."""

    @staticmethod
    def align(seq_a: List[str], seq_b: List[str],
              match_score: int = 2,
              mismatch_score: int = -1,
              indel_score: int = -1,
              gap: str = "_") -> Tuple[List[str], List[str]]:
        """
        Align two sequences using Needleman-Wunsch algorithm.

        Args:
            seq_a: First sequence
            seq_b: Second sequence
            match_score: Score for matching elements
            mismatch_score: Score for mismatching elements
            indel_score: Score for insertions/deletions
            gap: Symbol to use for gaps

        Returns:
            Tuple of (aligned_seq_a, aligned_seq_b)
        """
        from sequence_align.pairwise import needleman_wunsch
        return needleman_wunsch(
            seq_a, seq_b,
            match_score=match_score,
            mismatch_score=mismatch_score,
            indel_score=indel_score,
            gap=gap
        )


class G2PConverter:
    """Grapheme-to-phoneme conversion utilities."""

    @staticmethod
    def text_to_phonemes(text: str, lang: str = "en-us") -> Tuple[List[Tuple[str, str]], List[str]]:
        """
        Convert text to phonemes using gruut.

        Args:
            text: Input text to convert
            lang: Language code (default: "en-us")

        Returns:
            Tuple of (lexicon, words) where:
            - lexicon: List of (word, phonemes) tuples
            - words: List of words

        Example:
            >>> lexicon, words = G2PConverter.text_to_phonemes("hello world")
            >>> lexicon
            [('hello', 'h ɛ l oʊ'), ('world', 'w ɜr l d')]
            >>> words
            ['hello', 'world']
        """
        # Remove punctuation
        clean = Punctuation(";:,.!\"?()").remove(text)
        lexicon = []
        words = []

        for sent in sentences(clean, lang=lang):
            for w in sent:
                word_text = w.text.strip().lower()
                if not word_text:
                    continue

                words.append(word_text)

                try:
                    phonemes = " ".join(w.phonemes)
                except Exception:
                    # Fallback to word text if phoneme conversion fails
                    phonemes = word_text

                lexicon.append((word_text, phonemes))

        return lexicon, words


class PhonemeAligner:
    """Aligns phonemes per word for pronunciation comparison."""

    @staticmethod
    def align_per_word(
        lexicon: List[Tuple[str, str]],
        recorded_tokens: List[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Align recorded phoneme tokens to reference phonemes word by word.

        Args:
            lexicon: List of (word, phonemes) tuples from reference
            recorded_tokens: List of phoneme tokens from recorded audio

        Returns:
            Tuple of (per_word_ref, per_word_rec) where each is a list of
            phoneme strings aligned per word

        Example:
            >>> lexicon = [('hello', 'h ɛ l oʊ'), ('world', 'w ɜr l d')]
            >>> recorded = ['h', 'ɛ', 'l', 'oʊ', 'w', 'ɜr', 'l', 'd']
            >>> ref, rec = PhonemeAligner.align_per_word(lexicon, recorded)
            >>> ref
            ['hɛloʊ', 'wɜrld']
            >>> rec
            ['hɛloʊ', 'wɜrld']
        """
        # Build complete reference phoneme list
        ref_all = []
        word_lens = []

        for word, phonemes in lexicon:
            parts = phonemes.split()
            word_lens.append(len(parts))
            if parts:
                ref_all.extend(parts)

        if not ref_all:
            return ["" for _ in lexicon], ["" for _ in lexicon]

        # Align the full sequences
        aligned_ref, aligned_rec = SequenceAligner.align(ref_all, recorded_tokens)

        # Split aligned sequences back into per-word chunks
        per_word_ref = []
        per_word_rec = []

        ref_token_count = 0
        for wlen, (word, phonemes) in zip(word_lens, lexicon):
            if wlen == 0:
                per_word_ref.append("")
                per_word_rec.append("")
                continue

            start = ref_token_count
            end = start + wlen

            ref_buf = []
            rec_buf = []

            non_gap_idx = 0
            for a_r, a_p in zip(aligned_ref, aligned_rec):
                if a_r != "_":
                    if start <= non_gap_idx < end:
                        ref_buf.append(a_r)
                        if a_p != "_":
                            rec_buf.append(a_p)
                    non_gap_idx += 1

            per_word_ref.append("".join(ref_buf))
            per_word_rec.append("".join(rec_buf))

            ref_token_count = end

        return per_word_ref, per_word_rec


class MetricsCalculator:
    """Calculates pronunciation accuracy metrics."""

    @staticmethod
    def calculate_metrics(per_word_comparison: List[Dict]) -> Dict:
        """
        Calculate pronunciation accuracy metrics from per-word comparison.

        Args:
            per_word_comparison: List of dicts with keys:
                - word: str
                - ref_phonemes: str
                - rec_phonemes: str
                - match: bool

        Returns:
            Dict with metrics:
            - word_accuracy: float (%)
            - phoneme_accuracy: float (%)
            - phoneme_error_rate: float (%)
            - correct_words: int
            - total_words: int
            - correct_phonemes: int
            - total_phonemes: int
            - substitutions: int (S)
            - insertions: int (I)
            - deletions: int (D)

        Example:
            >>> comparison = [
            ...     {'word': 'hello', 'ref_phonemes': 'hɛloʊ', 'rec_phonemes': 'hɛloʊ', 'match': True},
            ...     {'word': 'world', 'ref_phonemes': 'wɜrld', 'rec_phonemes': 'wɜld', 'match': False},
            ... ]
            >>> metrics = MetricsCalculator.calculate_metrics(comparison)
            >>> metrics['word_accuracy']
            50.0
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

            # Character-level comparison
            ref_chars = list(ref) if ref else []
            rec_chars = list(rec) if rec else []

            total_phonemes += len(ref_chars)

            # If exact match, count all as correct
            if ref == rec:
                correct_phonemes += len(ref_chars)
            else:
                # Align at character level for detailed error counting
                aligned_ref, aligned_rec = SequenceAligner.align(ref_chars, rec_chars)

                for r, p in zip(aligned_ref, aligned_rec):
                    if r == p and r != "_":
                        correct_phonemes += 1
                    elif r != "_" and p == "_":
                        deletions += 1
                    elif r == "_" and p != "_":
                        insertions += 1
                    elif r != p and r != "_" and p != "_":
                        substitutions += 1

        # Calculate percentages
        word_accuracy = (correct_words / total_words * 100) if total_words > 0 else 0
        phoneme_accuracy = (correct_phonemes / total_phonemes * 100) if total_phonemes > 0 else 0
        phoneme_error_rate = 100 - phoneme_accuracy

        return {
            'word_accuracy': word_accuracy,
            'phoneme_accuracy': phoneme_accuracy,
            'phoneme_error_rate': phoneme_error_rate,
            'correct_words': correct_words,
            'total_words': total_words,
            'correct_phonemes': correct_phonemes,
            'total_phonemes': total_phonemes,
            'substitutions': substitutions,
            'insertions': insertions,
            'deletions': deletions,
        }
