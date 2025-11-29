#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phoneme Processor Module
Encapsulates all linguistic processing (G2P) and study material preparation logic.
"""

from typing import List, Tuple, Dict
from gruut import sentences
from phonemizer.punctuation import Punctuation
from ipa_definitions import IPADefinitionsManager
from audio_processor import TTSGenerator


class PhonemeProcessor:
    """
    Encapsula toda la lógica de procesamiento lingüístico (G2P) y la preparación
    de datos de estudio.

    Responsibilities:
    - Generate reference phonemes from text using gruut
    - Prepare data for pronunciation widgets
    - Create IPA guide data with individual word audio
    - Extract unique phoneme symbols and definitions
    """

    @staticmethod
    def generate_reference_phonemes(text: str, lang: str = "en-us") -> Tuple[List[Tuple[str, str]], List[str]]:
        """
        Genera el léxico (palabra, fonemas) y la lista de palabras.

        Args:
            text: Input text to process
            lang: Language code (default "en-us")

        Returns:
            Tuple of (lexicon, words) where:
            - lexicon: List of (word, phonemes) tuples
            - words: List of words
        """
        clean = Punctuation(";:,.!\"?()").remove(text)
        lexicon, words = [], []

        for sent in sentences(clean, lang=lang):
            for w in sent:
                t = w.text.strip().lower()
                if not t:
                    continue
                words.append(t)
                try:
                    phon = " ".join(w.phonemes)
                except Exception:
                    phon = t  # Fallback to word text if phonemes fail
                lexicon.append((t, phon))

        return lexicon, words

    @staticmethod
    def prepare_widget_data(reference_text: str, lexicon: List[Tuple[str, str]]) -> Dict:
        """
        Prepara los datos en el formato requerido por el widget de Streamlit.

        Args:
            reference_text: Original text string
            lexicon: List of (word, phonemes) tuples from gruut

        Returns:
            Dict with keys:
            - phoneme_text: Space-separated phonemes for all words
            - word_timings: List of dicts with {word, phonemes} for proper alignment
        """
        word_timings = []
        all_phonemes = []

        for word, phonemes in lexicon:
            word_timings.append({
                "word": word,
                "phonemes": phonemes,
                # Note: start/end times would come from ASR alignment
                # For TTS preview, we leave them None and let widget auto-partition
                "start": None,
                "end": None
            })
            all_phonemes.append(phonemes)

        return {
            "phoneme_text": " ".join(all_phonemes),
            "word_timings": word_timings
        }

    @staticmethod
    def create_ipa_guide_data(text: str, lang: str = "en-us") -> Tuple[List[Dict], set]:
        """
        Procesa el texto para generar los datos necesarios para renderizar
        la guía IPA palabra por palabra (incluyendo audio individual).

        Args:
            text: Input text to process
            lang: Language code (default "en-us")

        Returns:
            Tuple of (breakdown_data, unique_symbols) where:
            - breakdown_data: List of dicts with {index, word, ipa, hint, audio}
            - unique_symbols: Set of unique IPA symbols found in the text
        """
        breakdown_data = []
        unique_symbols = set()
        clean_text = Punctuation(';:,.!?"()').remove(text)
        word_counter = 0

        for sent in sentences(clean_text, lang=lang):
            for w in sent:
                word_text = w.text
                if not word_text:
                    continue

                try:
                    phonemes_list = w.phonemes
                    phoneme_str = "".join(phonemes_list)

                    # Recolección de símbolos y generación de hints
                    hints = []
                    for p in phonemes_list:
                        clean_p = p.replace("ˈ", "").replace("ˌ", "")
                        definition = IPADefinitionsManager.get_definition(clean_p)
                        if definition:
                            unique_symbols.add(clean_p)
                            hints.append(definition.split('(')[0].strip())
                        elif IPADefinitionsManager.get_definition(p):
                            unique_symbols.add(p)
                            definition_full = IPADefinitionsManager.get_definition(p)
                            if definition_full:
                                hints.append(definition_full.split('(')[0].strip())

                    hint_str = " + ".join(hints[:3])
                    if len(hints) > 3:
                        hint_str += "..."

                    # Generar audio individual para esta palabra
                    word_audio = TTSGenerator.generate_audio(word_text, lang=lang)

                    breakdown_data.append({
                        "index": word_counter,
                        "word": word_text,
                        "ipa": f"/{phoneme_str}/",
                        "hint": hint_str,
                        "audio": word_audio
                    })
                    word_counter += 1

                except Exception:
                    # Skip words that fail processing
                    continue

        return breakdown_data, unique_symbols
