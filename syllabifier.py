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
    # Extended clusters with glides (for words like "student", "skewer")
    "spj", "stj", "skj", "sfj",
}

# Ambisyllabic consonants (can belong to both syllables in VCV context)
AMBISYLLABIC = {"t", "d", "s", "z", "n"}

# Sonority hierarchy (higher = more sonorous)
# Used to validate onset clusters (should have ascending sonority)
SONORITY = {
    # Plosives (least sonorous)
    "p": 1, "t": 1, "k": 1, "b": 1, "d": 1, "g": 1,
    # Fricatives
    "f": 2, "v": 2, "θ": 2, "ð": 2, "s": 2, "z": 2, "ʃ": 2, "ʒ": 2, "h": 2,
    # Nasals
    "m": 3, "n": 3, "ŋ": 3,
    # Liquids and glides (most sonorous consonants)
    "l": 4, "r": 4, "w": 4, "j": 4,
}

# Fallback dictionary for common irregular words
# This handles exceptions that don't follow standard phonotactic rules
SYLLABLE_EXCEPTIONS = {
    # Common reductions and irregular patterns
    "little": ["lɪ", "tl̩"],
    "bottle": ["bɑ", "tl̩"],
    "button": ["bʌ", "tn̩"],
    "cotton": ["kɑ", "tn̩"],
    "hidden": ["hɪ", "dn̩"],
    "garden": ["gɑr", "dn̩"],
    "better": ["bɛ", "tɚ"],
    "water": ["wɑ", "tɚ"],
    "letter": ["lɛ", "tɚ"],
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


def is_sonority_ascending(cluster: List[str]) -> bool:
    """
    Check if a consonant cluster has ascending sonority.

    English prefers onset clusters with ascending sonority:
    - "spring" (s=2, p=1, r=4) is invalid by strict rules but /s/ is special
    - "pl" (p=1, l=4) ✓ ascending
    - "lp" (l=4, p=1) ✗ descending

    Special case: /s/ clusters are exempt from sonority rules.

    Args:
        cluster: List of phoneme strings

    Returns:
        True if cluster has valid sonority profile
    """
    if not cluster:
        return True

    # Special case: /s/ initial clusters are always valid in English
    if cluster[0] == "s":
        return True

    sonorities = [SONORITY.get(c, 0) for c in cluster]

    # Check for ascending sonority (allowing plateaus for some cases)
    for i in range(len(sonorities) - 1):
        if sonorities[i] > sonorities[i + 1]:
            return False

    return True


def collapse_schwa_sonorant(phonemes: List[str]) -> List[str]:
    """
    Collapse schwa + sonorant sequences into syllabic consonants.

    Examples:
        ["b", "ɑ", "t", "ə", "l"] → ["b", "ɑ", "t", "l̩"]  (bottle)
        ["l", "ɪ", "t", "ə", "l"] → ["l", "ɪ", "t", "l̩"]  (little)
        ["b", "ʌ", "t", "ə", "n"] → ["b", "ʌ", "t", "n̩"]  (button)

    Args:
        phonemes: List of phoneme tokens

    Returns:
        List with schwa+sonorant collapsed to syllabic consonants
    """
    result = []
    i = 0

    while i < len(phonemes):
        # Check for schwa followed by sonorant (l, r, m, n)
        if (i + 1 < len(phonemes) and
            phonemes[i] == "ə" and
            phonemes[i + 1] in {"l", "r", "m", "n"}):
            # Create syllabic consonant
            result.append(phonemes[i + 1] + "̩")
            i += 2
        else:
            result.append(phonemes[i])
            i += 1

    return result


def normalize_phoneme_sequence(text: str) -> List[str]:
    """
    Convert a space-separated IPA string into a list of correctly tokenized phonemes.

    Handles:
    - Affricates (t͡ʃ, d͡ʒ)
    - Diphthongs (aɪ, aʊ, eɪ, oʊ, ɔɪ)
    - Syllabic consonants (n̩, l̩, ɫ̩)
    - Schwa + sonorant → syllabic consonant (ə + l → l̩)

    Args:
        text: Space-separated IPA string (e.g., "h aʊ m ʌ t͡ʃ")

    Returns:
        List of phoneme tokens
    """
    if not text:
        return []

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

    # Apply schwa + sonorant collapse (bottle, little, button)
    merged = collapse_schwa_sonorant(merged)

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
    # Strategy: Each vowel starts a new syllable, consonants attach to the
    # current syllable being built
    syllable_groups = []
    current_group = []

    for phoneme in phonemes:
        if is_vowel(phoneme):
            # Start a new syllable with this vowel
            # If we have a current group with consonants, save it first
            if current_group and any(is_vowel(p) for p in current_group):
                # Current group already has a vowel, save it and start fresh
                syllable_groups.append(current_group)
                current_group = [phoneme]
            else:
                # Current group is just consonants (onset), add vowel to it
                current_group.append(phoneme)
        else:
            # Consonant: add to current group
            current_group.append(phoneme)

    # Save final group
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

    Uses multiple heuristics:
    1. Prefer valid onsets from VALID_ONSETS
    2. Check sonority sequencing (ascending sonority in onsets)
    3. Handle ambisyllabic consonants in VCV contexts

    If a syllable starts with an invalid onset cluster, move consonants
    to the previous syllable's coda until the onset is valid.

    Examples:
        ["h", "aɪ"], ["m", "oʊ"] → no change (both valid onsets)
        ["k", "t", "aɪ"] → move "k" to previous coda
        ["b", "ɛ"], ["t", "ɚ"] → "better" - 't' is ambisyllabic, prefer onset
    """
    if not syllable_groups or len(syllable_groups) < 2:
        return syllable_groups

    fixed = [list(syllable_groups[0])]

    for current_group in syllable_groups[1:]:
        current_group = list(current_group)

        # Find how many leading consonants exist
        consonant_count = 0
        for phoneme in current_group:
            if is_consonant(phoneme):
                consonant_count += 1
            else:
                break

        # Handle ambisyllabic consonants (VCV pattern with special consonants)
        # If single consonant between vowels and it's ambisyllabic, prefer onset
        if (consonant_count == 1 and
            current_group[0] in AMBISYLLABIC and
            len(fixed[-1]) > 0 and is_vowel(fixed[-1][-1]) and
            len(current_group) > 1 and is_vowel(current_group[1])):
            # Keep consonant as onset (do nothing)
            pass
        elif consonant_count > 0:
            # Try to find maximal valid onset
            onset_phonemes = current_group[:consonant_count]
            onset_str = "".join(onset_phonemes)

            # Check if onset is valid (either in list or has ascending sonority)
            while consonant_count > 0:
                onset_str = "".join(current_group[:consonant_count])

                # Valid if: in VALID_ONSETS OR has ascending sonority
                is_valid = (onset_str in VALID_ONSETS or
                           is_sonority_ascending(current_group[:consonant_count]))

                if is_valid:
                    break

                # Move first consonant to previous coda
                c = current_group.pop(0)
                fixed[-1].append(c)
                consonant_count -= 1

        fixed.append(current_group)

    # Remove any empty groups
    fixed = [g for g in fixed if g]

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
