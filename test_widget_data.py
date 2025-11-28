"""
Test to verify word_phoneme_pairs generation in the widget
"""

import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import html
from typing import List, Optional, Dict

# Simulate the widget's logic
def prepare_word_phoneme_pairs(word_timings: Optional[List[dict]]) -> List[Dict]:
    """Simulate what the widget does"""
    word_phoneme_pairs = []

    print(f"Input word_timings: {word_timings}")
    print(f"Type: {type(word_timings)}")

    if word_timings:
        print(f"word_timings has {len(word_timings)} items")
        for i, wt in enumerate(word_timings):
            print(f"  [{i}] {wt}")
            word_phoneme_pairs.append({
                "word": html.escape(wt.get("word", "")),
                "phonemes": html.escape(wt.get("phonemes", "")),
                "start": wt.get("start"),
                "end": wt.get("end")
            })
    else:
        print("word_timings is None or empty!")

    return word_phoneme_pairs


# Test with sample data
test_word_timings = [
    {"word": "the", "phonemes": "ð ə", "start": None, "end": None},
    {"word": "quick", "phonemes": "k w ˈɪ k", "start": None, "end": None},
    {"word": "brown", "phonemes": "b ɹ ˈaʊ n", "start": None, "end": None},
]

print("=" * 70)
print("Testing word_phoneme_pairs generation")
print("=" * 70)
print()

pairs = prepare_word_phoneme_pairs(test_word_timings)

print()
print("Result:")
print("-" * 70)
for pair in pairs:
    print(f"  {pair['word']:12} → /{pair['phonemes']}/")

print()
print("=" * 70)
print(f"✓ Generated {len(pairs)} word-phoneme pairs")
print("=" * 70)
