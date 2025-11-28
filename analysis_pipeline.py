from typing import Dict, List, Tuple, Optional
from datetime import datetime
import streamlit as st
import numpy as np

from metrics_calculator import MetricsCalculator


class AnalysisPipeline:
    """Orchestrates the complete pronunciation analysis workflow.
    
    Responsibilities:
    - Coordinate audio loading → transcription → alignment → metrics → feedback
    - Manage dependencies between ASRManager, GroqManager, and calculator
    - Return complete analysis result dict with all components
    - Handle error states gracefully
    
    Flow:
    1. Load audio from bytes
    2. Transcribe using ASR model
    3. Generate reference phonemes
    4. Align reference & recorded phonemes per word
    5. Calculate metrics
    6. Get LLM feedback (optional)
    7. Return complete result
    """

    def __init__(self, asr_manager, groq_manager, audio_processor, ipa_defs_manager):
        """
        Args:
            asr_manager: ASRModelManager instance (for transcription)
            groq_manager: GroqManager instance (for LLM feedback)
            audio_processor: AudioProcessor instance (for loading/validating audio)
            ipa_defs_manager: IPADefinitionsManager instance (for phoneme definitions)
        """
        self.asr_manager = asr_manager
        self.groq_manager = groq_manager
        self.audio_processor = audio_processor
        self.ipa_defs_manager = ipa_defs_manager

    def _load_audio(self, audio_bytes: bytes) -> Tuple[Optional[np.ndarray], Optional[int]]:
        """Load audio from bytes. Returns (audio_array, sample_rate) or (None, None) on error."""
        try:
            audio, sr = self.audio_processor.load_from_bytes(audio_bytes)
            if audio is None:
                st.error("❌ Failed to load audio. Check file format.")
                return None, None
            return audio, sr
        except Exception as e:
            st.error(f"Audio loading error: {e}")
            return None, None

    def _transcribe_audio(self, audio: np.ndarray, sr: int, use_g2p: bool, lang: str) -> Tuple[str, str]:
        """Transcribe audio using ASR. Returns (raw_decoded, recorded_phoneme_str)."""
        try:
            with st.spinner("🎤 Transcribing audio..."):
                raw_decoded, recorded_phoneme_str = self.asr_manager.transcribe(
                    audio, sr,
                    use_g2p=use_g2p,
                    lang=lang
                )
            return raw_decoded, recorded_phoneme_str
        except Exception as e:
            st.error(f"Transcription error: {e}")
            return "", ""

    def _generate_reference_phonemes(self, reference_text: str, lang: str) -> Tuple[List[Tuple[str, str]], List[str]]:
        """Generate reference phonemes from text. Returns (lexicon, words) or ([], []) on error."""
        try:
            from gruut import sentences
            from phonemizer.punctuation import Punctuation
            
            with st.spinner("📖 Generating reference phonemes..."):
                clean = Punctuation(";:,.!\"?()").remove(reference_text)
                lexicon, words = [], []

                for sent in sentences(clean, lang=lang):
                    for w in sent:
                        t = w.text.strip().lower()
                        if not t:
                            continue
                        words.append(t)
                        try:
                            phon = " ".join(w.phonemes)
                        except:
                            phon = t
                        lexicon.append((t, phon))

                return lexicon, words
        except Exception as e:
            st.error(f"Reference phoneme generation error: {e}")
            return [], []

    def _tokenize_phonemes(self, s: str) -> List[str]:
        """Tokenize phoneme string into individual tokens."""
        import re
        s = s.strip()
        if " " in s:
            return s.split()
        tok = re.findall(r"[a-zA-Zʰɪʌɒəɜɑɔɛʊʏœøɯɨɫɹːˈˌ˞̃͜͡d͡ʒ]+|[^\s]", s)
        return [t for t in tok if t]

    def _align_sequences(self, a: List[str], b: List[str]) -> Tuple[List[str], List[str]]:
        """Align two sequences using Needleman-Wunsch algorithm."""
        from sequence_align.pairwise import needleman_wunsch
        return needleman_wunsch(a, b, match_score=2, mismatch_score=-1, indel_score=-1, gap="_")

    def _align_per_word(self, lexicon: List[Tuple[str, str]], rec_tokens: List[str]):
        """Align recorded tokens to reference phonemes word by word."""
        ref_all = []
        word_lens = []
        for word, phon in lexicon:
            parts = phon.split()
            word_lens.append(len(parts))
            if parts:
                ref_all.extend(parts)

        if not ref_all:
            return ["" for _ in lexicon], ["" for _ in lexicon]

        aligned_ref, aligned_rec = self._align_sequences(ref_all, rec_tokens)

        per_word_ref = []
        per_word_rec = []

        ref_token_count = 0
        for wlen, (word, phon) in zip(word_lens, lexicon):
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

    def _build_comparison(self, ref_words: List[str], per_word_ref: List[str], per_word_rec: List[str]) -> List[Dict]:
        """Build per-word comparison list."""
        per_word_comparison = []
        for i, word in enumerate(ref_words):
            ref_ph = per_word_ref[i]
            rec_ph = per_word_rec[i]
            match = ref_ph == rec_ph
            per_word_comparison.append({
                'word': word,
                'ref_phonemes': ref_ph,
                'rec_phonemes': rec_ph,
                'match': match
            })
        return per_word_comparison

    def _get_llm_feedback(self, reference_text: str, per_word_comparison: List[Dict]) -> Optional[str]:
        """Get LLM feedback from Groq manager."""
        try:
            with st.spinner("🧠 Getting AI coach feedback..."):
                feedback = self.groq_manager.get_feedback(reference_text, per_word_comparison)
            return feedback
        except Exception as e:
            st.warning(f"LLM feedback unavailable: {e}")
            return None

    def run(self, audio_bytes: bytes, reference_text: str,
            use_g2p: bool = True, use_llm: bool = True, lang: str = "en-us") -> Optional[Dict]:
        """
        Execute the complete analysis pipeline.
        
        Args:
            audio_bytes: Raw audio data (WAV/MP3/etc)
            reference_text: Text to compare pronunciation against
            use_g2p: Whether to apply grapheme-to-phoneme conversion
            use_llm: Whether to get LLM coaching feedback
            lang: Language code (default 'en-us')
            
        Returns:
            Dict with keys:
            - timestamp: datetime
            - audio_data: bytes
            - audio_array: np.ndarray
            - sample_rate: int
            - reference_text: str
            - raw_decoded: str (ASR output)
            - recorded_phoneme_str: str
            - lexicon: List[Tuple[str, str]]
            - per_word_comparison: List[Dict]
            - llm_feedback: Optional[str]
            - metrics: Dict (from MetricsCalculator)
            
            Returns None if any critical step fails.
        """
        # Step 1: Load audio
        audio, sr = self._load_audio(audio_bytes)
        if audio is None:
            return None

        # Step 2: Transcribe
        raw_decoded, recorded_phoneme_str = self._transcribe_audio(audio, sr, use_g2p, lang)
        if not raw_decoded:
            st.error("Transcription failed.")
            return None

        # Step 3: Generate reference phonemes
        lexicon, ref_words = self._generate_reference_phonemes(reference_text, lang)
        if not lexicon:
            st.error("Could not generate reference phonemes.")
            return None

        # Step 4: Align sequences
        try:
            with st.spinner("🔗 Aligning phonemes..."):
                rec_tokens = self._tokenize_phonemes(recorded_phoneme_str)
                per_word_ref, per_word_rec = self._align_per_word(lexicon, rec_tokens)
        except Exception as e:
            st.error(f"Alignment error: {e}")
            return None

        # Step 5: Build comparison
        per_word_comparison = self._build_comparison(ref_words, per_word_ref, per_word_rec)

        # Step 6: Calculate metrics
        metrics = MetricsCalculator.calculate(per_word_comparison)

        # Step 7: Get LLM feedback (optional)
        llm_feedback = None
        if use_llm:
            llm_feedback = self._get_llm_feedback(reference_text, per_word_comparison)

        # Step 8: Return complete result
        result = {
            'timestamp': datetime.now(),
            'audio_data': audio_bytes,
            'audio_array': audio,
            'sample_rate': sr,
            'reference_text': reference_text,
            'raw_decoded': raw_decoded,
            'recorded_phoneme_str': recorded_phoneme_str,
            'lexicon': lexicon,
            'per_word_comparison': per_word_comparison,
            'llm_feedback': llm_feedback,
            'metrics': metrics,
        }

        st.success("✅ Analysis complete!")
        return result
