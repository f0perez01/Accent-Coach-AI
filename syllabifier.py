"""
Syllabifier: Automatic syllable detection from IPA phoneme sequences.

No deep learning required. Fast, offline, robust for American English.

Algorithm:
1. Normalize phoneme sequence (handle diphthongs, affricates, syllabic consonants)
2. Detect vowel nuclei (monophthongs, diphthongs, syllabic consonants)
3. Build syllables by attaching consonants before/after nuclei
4. Fix invalid onsets using English phonotactics
5. Optionally compute syllable timings from phoneme timings

Usage:
    phonemes = normalize_phoneme_sequence("h aʊ m ʌ t͡ʃ")
    syllables = syllabify_phonemes(phonemes)
    # With timings:
    syllables_with_timing = syllabify_phonemes(
        phonemes,
        phoneme_timings=[
            {"phoneme": "h", "start": 0.0, "end": 0.1},
            ...
        ]
    )
"""

import re
from typing import List, Dict, Optional, Tuple

# ============================================================================
# PHONEME CLASSIFICATION
# ============================================================================

IPA_VOWELS = {
    "i", "ɪ", "e", "ɛ", "æ", "ʌ", "ə", "o", "ʊ", "u", "ɑ", "ɔ",
    "ɚ", "ɝ",  # rhotacized vowels
    "ɨ", "ʉ",  # central vowels (rarer)
}

DIPHTHONGS = {"aɪ", "aʊ", "eɪ", "oʊ", "ɔɪ"}

SYLLABIC_CONSONANTS = {"n̩", "l̩", "ɫ̩", "m̩", "r̩"}

AFFRICATES = {"t͡ʃ", "d͡ʒ"}

# Valid English onsets (CCV, C clusters)
# Includes: stops, fricatives, nasals, liquids, glides, and common clusters
VALID_ONSETS = {
    # Single consonants
    "p", "t", "k", "b", "d", "g",
    "f", "v", "θ", "ð", "s", "z", "ʃ", "ʒ",
    "h", "m", "n", "ŋ", "l", "r", "w", "j",
    # Stop + liquid
    "pl", "pr", "bl", "br", "tr", "dr", "kl", "kr", "gl", "gr",
    # Fricative + liquid or glide
    "fl", "fr", "sl", "sm", "sn", "sp", "st", "sk", "sw",
    # Three-consonant clusters (rare but valid)
    "spr", "str", "skr", "spl", "skw",
}

# ============================================================================
# UTILITIES
# ============================================================================

def is_vowel(phoneme: str) -> bool:
    """Check if a phoneme is a vowel nucleus (monophthong, diphthong, or syllabic consonant)."""
    return phoneme in IPA_VOWELS or phoneme in DIPHTHONGS or phoneme in SYLLABIC_CONSONANTS


def is_consonant(phoneme: str) -> bool:
    """Check if a phoneme is a consonant."""
    return not is_vowel(phoneme)


def normalize_phoneme_sequence(text: str) -> List[str]:
    """
    Convert a space-separated IPA string into a list of correctly tokenized phonemes.
    
    Handles:
    - Affricates (t͡ʃ, d͡ʒ)
    - Diphthongs (aɪ, aʊ, eɪ, oʊ, ɔɪ)
    - Syllabic consonants (n̩, l̩, ɫ̩)
    
    Args:
        text: Space-separated IPA string (e.g., "h aʊ m ʌ t͡ʃ")
    
    Returns:
        List of phoneme tokens
    """
    tokens = text.strip().split()
    merged = []
    i = 0

    while i < len(tokens):
        tok = tokens[i]

        # Check for affricates (two consecutive tokens forming one phoneme)
        if i + 1 < len(tokens):
            potential_affricate = tok + tokens[i + 1]
            if potential_affricate in AFFRICATES:
                merged.append(potential_affricate)
                i += 2
                continue

        # Regular token
        merged.append(tok)
        i += 1

    return merged


def syllabify_phonemes(
    phonemes: List[str],
    phoneme_timings: Optional[List[Dict]] = None
) -> List[Dict]:
    """
    Syllabify a phoneme sequence.
    
    Args:
        phonemes: List of phoneme tokens (e.g., ["h", "aʊ", "m", "ʌ", "t͡ʃ"])
        phoneme_timings: Optional list of {"phoneme": str, "start": float, "end": float}
    
    Returns:
        List of syllable dicts:
        [
            {
                "syllable": "haʊ",
                "phonemes": ["h", "aʊ"],
                "start": 0.0,
                "end": 0.35
            },
            ...
        ]
    """
    if not phonemes:
        return []

    # Step 1: Group consonants and vowels
    syllable_groups = []
    current_group = []

    for phoneme in phonemes:
        if is_vowel(phoneme):
            if current_group:
                syllable_groups.append(current_group)
            current_group = [phoneme]
        else:
            current_group.append(phoneme)

    if current_group:
        syllable_groups.append(current_group)

    # Step 2: Fix invalid onsets (distribute consonants between syllables)
    syllable_groups = _fix_onsets(syllable_groups)

    # Step 3: Build output with timings
    result = []
    phoneme_timing_map = {}

    if phoneme_timings:
        for pt in phoneme_timings:
            phoneme_timing_map[pt["phoneme"]] = (pt["start"], pt["end"])

    for group in syllable_groups:
        syllable_str = "".join(group)

        # Compute timing if available
        start_time = None
        end_time = None

        if phoneme_timing_map:
            starts = []
            ends = []
            for phon in group:
                if phon in phoneme_timing_map:
                    s, e = phoneme_timing_map[phon]
                    starts.append(s)
                    ends.append(e)

            if starts and ends:
                start_time = min(starts)
                end_time = max(ends)

        result.append({
            "syllable": syllable_str,
            "phonemes": group,
            "start": start_time,
            "end": end_time
        })

    return result


def _fix_onsets(syllable_groups: List[List[str]]) -> List[List[str]]:
    """
    Adjust syllable boundaries to respect valid English onsets.
    
    If a syllable starts with an invalid onset cluster, move consonants
    to the previous syllable's coda until the onset is valid.
    
    Examples:
        ["h", "aɪ"], ["m", "oʊ"] → no change (both valid onsets)
        ["k", "t", "aɪ"] → move "k" to previous coda
    """
    if not syllable_groups or len(syllable_groups) < 2:
        return syllable_groups

    fixed = [syllable_groups[0]]

    for current_group in syllable_groups[1:]:
        # Find how many leading consonants form a valid onset
        consonant_count = 0
        for phoneme in current_group:
            if is_consonant(phoneme):
                consonant_count += 1
            else:
                break

        # Move excess consonants to previous syllable's coda
        if consonant_count > 0:
            onset = "".join(current_group[:consonant_count])

            # If onset is invalid, move consonants back one by one
            while consonant_count > 0 and onset not in VALID_ONSETS:
                c = current_group.pop(0)
                fixed[-1].append(c)
                consonant_count -= 1
                onset = "".join(current_group[:consonant_count])

        fixed.append(current_group)

    return fixed


def phonemes_to_syllables_with_fallback(
    phoneme_str: str,
    phoneme_timings: Optional[List[Dict]] = None
) -> List[Dict]:
    """
    Convenience function: convert a space-separated IPA string to syllables.
    
    Falls back gracefully if parsing fails.
    
    Args:
        phoneme_str: Space-separated IPA string
        phoneme_timings: Optional phoneme timing list
    
    Returns:
        List of syllable dicts, or empty list if parsing fails
    """
    try:
        phonemes = normalize_phoneme_sequence(phoneme_str)
        return syllabify_phonemes(phonemes, phoneme_timings)
    except Exception as e:
        # If syllabification fails, return empty list (caller should handle fallback)
        print(f"Warning: syllabification failed: {e}")
        return []


# ============================================================================
# EXAMPLE USAGE (for testing)
# ============================================================================

if __name__ == "__main__":
    # Example 1: Simple
    text1 = "h aʊ m ʌ t͡ʃ"
    print(f"Input: {text1}")
    phonemes1 = normalize_phoneme_sequence(text1)
    print(f"Normalized: {phonemes1}")
    syllables1 = syllabify_phonemes(phonemes1)
    print(f"Syllables: {syllables1}\n")

    # Example 2: With timings
    text2 = "h aʊ m ʌ t͡ʃ"
    phonemes2 = normalize_phoneme_sequence(text2)
    timings2 = [
        {"phoneme": "h", "start": 0.00, "end": 0.10},
        {"phoneme": "aʊ", "start": 0.10, "end": 0.35},
        {"phoneme": "m", "start": 0.35, "end": 0.45},
        {"phoneme": "ʌ", "start": 0.45, "end": 0.65},
        {"phoneme": "t͡ʃ", "start": 0.65, "end": 0.90},
    ]
    syllables2 = syllabify_phonemes(phonemes2, timings2)
    print(f"With timings:")
    for s in syllables2:
        print(f"  {s}")
