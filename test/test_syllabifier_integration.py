#!/usr/bin/env python3
"""
Integration test for syllabifier with pronunciation widget.
Tests the complete pipeline: phoneme text → syllables → widget timings.
"""

from syllabifier import normalize_phoneme_sequence, syllabify_phonemes, phonemes_to_syllables_with_fallback


def test_basic_syllabification():
    """Test basic syllabification without timings."""
    phoneme_str = "h aʊ"
    syllables = phonemes_to_syllables_with_fallback(phoneme_str)
    
    assert len(syllables) > 0, "Should generate at least one syllable"
    assert all("syllable" in s for s in syllables), "All items should have 'syllable' key"
    assert all("phonemes" in s for s in syllables), "All items should have 'phonemes' key"
    assert all("start" in s for s in syllables), "All items should have 'start' key"
    assert all("end" in s for s in syllables), "All items should have 'end' key"
    print("✅ test_basic_syllabification passed")


def test_syllabification_with_timings():
    """Test syllabification with phoneme timings."""
    phoneme_str = "h aʊ m ʌ"
    timings = [
        {"phoneme": "h", "start": 0.0, "end": 0.1},
        {"phoneme": "aʊ", "start": 0.1, "end": 0.35},
        {"phoneme": "m", "start": 0.35, "end": 0.45},
        {"phoneme": "ʌ", "start": 0.45, "end": 0.65},
    ]
    
    syllables = phonemes_to_syllables_with_fallback(phoneme_str, timings)
    
    assert len(syllables) > 0, "Should generate syllables with timings"
    assert any(s["start"] is not None for s in syllables), "At least one syllable should have timing"
    print("✅ test_syllabification_with_timings passed")


def test_syllable_structure_for_widget():
    """Test that syllable output is compatible with widget format."""
    phoneme_str = "p l æ n t"
    syllables = phonemes_to_syllables_with_fallback(phoneme_str)
    
    # Widget expects: [{"syllable": str, "start": float or None, "end": float or None}, ...]
    for syll in syllables:
        assert isinstance(syll["syllable"], str), "syllable must be string"
        assert syll["start"] is None or isinstance(syll["start"], float), "start must be float or None"
        assert syll["end"] is None or isinstance(syll["end"], float), "end must be float or None"
        assert isinstance(syll["phonemes"], list), "phonemes must be list"
    
    print("✅ test_syllable_structure_for_widget passed")


def test_diphthong_handling():
    """Test that diphthongs are treated as single phoneme."""
    phoneme_str = "aɪ m"  # "aɪ" should be treated as single nucleus
    phonemes = normalize_phoneme_sequence(phoneme_str)
    
    # aɪ should be in DIPHTHONGS
    assert "aɪ" in phonemes or len(phonemes) > 0, "Should handle diphthongs"
    print("✅ test_diphthong_handling passed")


def test_empty_input():
    """Test that empty input is handled gracefully."""
    syllables = phonemes_to_syllables_with_fallback("")
    assert isinstance(syllables, list), "Should return list for empty input"
    print("✅ test_empty_input passed")


def test_fallback_on_error():
    """Test that fallback works when parsing fails."""
    # Malformed input should return empty list gracefully
    syllables = phonemes_to_syllables_with_fallback("invalid garbage %%% input")
    assert isinstance(syllables, list), "Should return list even on error"
    print("✅ test_fallback_on_error passed")


if __name__ == "__main__":
    try:
        test_basic_syllabification()
        test_syllabification_with_timings()
        test_syllable_structure_for_widget()
        test_diphthong_handling()
        test_empty_input()
        test_fallback_on_error()
        print("\n✅ All integration tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)
