#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPA (International Phonetic Alphabet) Definitions
Educational dictionary of IPA symbols for American English pronunciation
"""

from typing import Dict, List, Optional


class IPADefinitionsManager:
    """Manages IPA phonetic symbols and their definitions for American English"""

    # Educational dictionary of IPA symbols (General American English)
    DEFINITIONS: Dict[str, str] = {
        # Vowels
        "i": "i larga (see)",
        "iː": "i larga (see)",
        "ɪ": "i corta (sit)",
        "e": "e cerrada (bed)",
        "ɛ": "e abierta (bet)",
        "æ": "a abierta (cat)",
        "ɑ": "a profunda (father)",
        "ɑː": "a profunda (father)",
        "ɔ": "o abierta (thought)",
        "ɔː": "o larga (law)",
        "ʊ": "u corta (good)",
        "u": "u larga (blue)",
        "uː": "u larga (blue)",
        "ʌ": "u corta/seca (cup, up)",
        "ə": "Schwa (sonido neutro débil, 'uh')",
        "ɜ": "er (bird)",
        "ɜː": "er larga (bird)",

        # Diphthongs
        "aɪ": "ai (my)",
        "eɪ": "ei (say)",
        "ɔɪ": "oi (boy)",
        "aʊ": "au (cow)",
        "oʊ": "ou (go)",
        "əʊ": "ou (go)",

        # Special consonants
        "t͡ʃ": "ch (chair)",
        "d͡ʒ": "j (judge)",
        "ʃ": "sh (she)",
        "ʒ": "s suave (measure)",
        "θ": "th (think - z española)",
        "ð": "th (this - d suave)",
        "ŋ": "ng (sing)",
        "j": "y (yes)",
        "ɹ": "r suave inglesa",
        "ʔ": "Glottal stop (parada de aire)",

        # Stress markers
        "ˈ": "Acento principal (sílaba fuerte)",
        "ˌ": "Acento secundario"
    }

    @classmethod
    def get_definition(cls, symbol: str) -> Optional[str]:
        """
        Get the definition for a specific IPA symbol

        Args:
            symbol: IPA symbol to look up

        Returns:
            Definition string if found, None otherwise
        """
        return cls.DEFINITIONS.get(symbol)

    @classmethod
    def get_all_definitions(cls) -> Dict[str, str]:
        """Get all IPA definitions"""
        return cls.DEFINITIONS.copy()

    @classmethod
    def get_vowels(cls) -> Dict[str, str]:
        """Get only vowel definitions"""
        vowel_symbols = [
            "i", "iː", "ɪ", "e", "ɛ", "æ", "ɑ", "ɑː",
            "ɔ", "ɔː", "ʊ", "u", "uː", "ʌ", "ə", "ɜ", "ɜː"
        ]
        return {k: v for k, v in cls.DEFINITIONS.items() if k in vowel_symbols}

    @classmethod
    def get_diphthongs(cls) -> Dict[str, str]:
        """Get only diphthong definitions"""
        diphthong_symbols = ["aɪ", "eɪ", "ɔɪ", "aʊ", "oʊ", "əʊ"]
        return {k: v for k, v in cls.DEFINITIONS.items() if k in diphthong_symbols}

    @classmethod
    def get_consonants(cls) -> Dict[str, str]:
        """Get only special consonant definitions"""
        consonant_symbols = [
            "t͡ʃ", "d͡ʒ", "ʃ", "ʒ", "θ", "ð", "ŋ", "j", "ɹ", "ʔ"
        ]
        return {k: v for k, v in cls.DEFINITIONS.items() if k in consonant_symbols}

    @classmethod
    def get_stress_markers(cls) -> Dict[str, str]:
        """Get stress marker definitions"""
        stress_symbols = ["ˈ", "ˌ"]
        return {k: v for k, v in cls.DEFINITIONS.items() if k in stress_symbols}

    @classmethod
    def extract_symbols_from_text(cls, phonetic_text: str) -> List[str]:
        """
        Extract all IPA symbols found in a phonetic text

        Args:
            phonetic_text: Text containing IPA symbols

        Returns:
            List of unique IPA symbols found
        """
        found_symbols = set()
        for symbol in cls.DEFINITIONS.keys():
            if symbol in phonetic_text:
                found_symbols.add(symbol)
        return sorted(list(found_symbols))

    @classmethod
    def get_definitions_for_symbols(cls, symbols: List[str]) -> Dict[str, str]:
        """
        Get definitions for a list of symbols

        Args:
            symbols: List of IPA symbols

        Returns:
            Dictionary of symbol: definition pairs
        """
        return {symbol: cls.DEFINITIONS.get(symbol, "Unknown") for symbol in symbols}
