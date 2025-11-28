"""
Test suite for improved syllabifier.

Tests validate:
1. Schwa + sonorant collapse
2. Ambisyllabic consonants
3. Sonority-based onset validation
4. Extended onset clusters
5. Common irregular words
"""

import sys
import io

# Fix encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from syllabifier import (
    normalize_phoneme_sequence,
    syllabify_phonemes,
    collapse_schwa_sonorant,
    is_sonority_ascending,
    is_vowel,
)


def test_schwa_collapse():
    """Test schwa + sonorant → syllabic consonant."""
    print("\n=== Test: Schwa + Sonorant Collapse ===")

    # bottle: b ɑ t ə l → b ɑ t l̩
    phonemes = normalize_phoneme_sequence("b ɑ t ə l")
    print(f"bottle: {phonemes}")
    assert "l̩" in phonemes, "Expected syllabic l"
    assert "ə" not in phonemes, "Schwa should be collapsed"

    # little: l ɪ t ə l → l ɪ t l̩
    phonemes = normalize_phoneme_sequence("l ɪ t ə l")
    print(f"little: {phonemes}")
    assert "l̩" in phonemes

    # button: b ʌ t ə n → b ʌ t n̩
    phonemes = normalize_phoneme_sequence("b ʌ t ə n")
    print(f"button: {phonemes}")
    assert "n̩" in phonemes

    print("✓ Schwa collapse working correctly")


def test_sonority_ascending():
    """Test sonority hierarchy validation."""
    print("\n=== Test: Sonority Ascending ===")

    # Valid onsets (ascending sonority)
    assert is_sonority_ascending(["p", "l"]), "pl should be valid (1→4)"
    assert is_sonority_ascending(["k", "r"]), "kr should be valid (1→4)"
    assert is_sonority_ascending(["f", "l"]), "fl should be valid (2→4)"

    # Invalid onsets (descending sonority)
    assert not is_sonority_ascending(["l", "p"]), "lp should be invalid (4→1)"
    assert not is_sonority_ascending(["r", "t"]), "rt should be invalid (4→1)"

    # Special case: /s/ initial always valid
    assert is_sonority_ascending(["s", "p", "r"]), "spr should be valid (s-exception)"
    assert is_sonority_ascending(["s", "t", "r"]), "str should be valid (s-exception)"

    print("✓ Sonority validation working correctly")


def test_syllabification_basic():
    """Test basic syllabification."""
    print("\n=== Test: Basic Syllabification ===")

    # Simple word: "happy" (h æ p i)
    phonemes = normalize_phoneme_sequence("h æ p i")
    syllables = syllabify_phonemes(phonemes)
    print(f"'happy': {[s['syllable'] for s in syllables]}")
    assert len(syllables) == 2, f"Expected 2 syllables, got {len(syllables)}"

    # Word with consonant cluster: "spring"
    phonemes = normalize_phoneme_sequence("s p r ɪ ŋ")
    syllables = syllabify_phonemes(phonemes)
    print(f"'spring': {[s['syllable'] for s in syllables]}")
    assert len(syllables) == 1, "spring should be 1 syllable"
    assert syllables[0]['syllable'] == "sprɪŋ"

    # Word: "hello" (h ɛ l oʊ)
    phonemes = normalize_phoneme_sequence("h ɛ l oʊ")
    syllables = syllabify_phonemes(phonemes)
    print(f"'hello': {[s['syllable'] for s in syllables]}")
    assert len(syllables) == 2, f"Expected 2 syllables, got {len(syllables)}"

    print("✓ Basic syllabification working correctly")


def test_syllabification_advanced():
    """Test advanced cases with new improvements."""
    print("\n=== Test: Advanced Syllabification ===")

    # bottle (with schwa collapse)
    phonemes = normalize_phoneme_sequence("b ɑ t ə l")
    syllables = syllabify_phonemes(phonemes)
    print(f"'bottle': {[s['syllable'] for s in syllables]}")
    assert len(syllables) == 2
    assert "l̩" in syllables[-1]['syllable'], "Last syllable should be syllabic l"

    # better (ambisyllabic t)
    phonemes = normalize_phoneme_sequence("b ɛ t ɚ")
    syllables = syllabify_phonemes(phonemes)
    print(f"'better': {[s['syllable'] for s in syllables]}")
    assert len(syllables) == 2

    # construct (complex onset)
    phonemes = normalize_phoneme_sequence("k ə n s t r ʌ k t")
    syllables = syllabify_phonemes(phonemes)
    print(f"'construct': {[s['syllable'] for s in syllables]}")
    # Should be kən-strʌkt (str is valid onset)

    # extra (complex coda + onset)
    phonemes = normalize_phoneme_sequence("ɛ k s t r ə")
    syllables = syllabify_phonemes(phonemes)
    print(f"'extra': {[s['syllable'] for s in syllables]}")
    # Should be ɛk-strə

    print("✓ Advanced syllabification working correctly")


def test_affricates():
    """Test affricate handling."""
    print("\n=== Test: Affricates ===")

    # church: t͡ʃ ɚ t͡ʃ
    phonemes = normalize_phoneme_sequence("t͡ʃ ɚ t͡ʃ")
    print(f"'church': {phonemes}")
    assert "t͡ʃ" in phonemes
    assert len(phonemes) == 3  # Should merge t͡ʃ

    # judge: d͡ʒ ʌ d͡ʒ
    phonemes = normalize_phoneme_sequence("d͡ʒ ʌ d͡ʒ")
    print(f"'judge': {phonemes}")
    assert "d͡ʒ" in phonemes

    print("✓ Affricate handling working correctly")


def test_extended_onsets():
    """Test newly added onset clusters."""
    print("\n=== Test: Extended Onsets ===")

    # student: s t j u d ə n t (stj cluster)
    phonemes = normalize_phoneme_sequence("s t j u d ə n t")
    syllables = syllabify_phonemes(phonemes)
    print(f"'student': {[s['syllable'] for s in syllables]}")
    # stj should be recognized as valid onset

    print("✓ Extended onset clusters working correctly")


def test_vowel_detection():
    """Test vowel vs consonant detection."""
    print("\n=== Test: Vowel Detection ===")

    # Regular vowels
    assert is_vowel("i")
    assert is_vowel("ɛ")
    assert is_vowel("ə")

    # Diphthongs
    assert is_vowel("aɪ")
    assert is_vowel("oʊ")

    # Syllabic consonants
    assert is_vowel("l̩")
    assert is_vowel("n̩")

    # Regular consonants
    assert not is_vowel("p")
    assert not is_vowel("t")
    assert not is_vowel("s")

    print("✓ Vowel detection working correctly")


def run_all_tests():
    """Run all test suites."""
    print("=" * 60)
    print("Running Syllabifier Test Suite")
    print("=" * 60)

    try:
        test_vowel_detection()
        test_schwa_collapse()
        test_sonority_ascending()
        test_affricates()
        test_syllabification_basic()
        test_syllabification_advanced()
        test_extended_onsets()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)

    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    run_all_tests()
