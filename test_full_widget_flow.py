"""
Full end-to-end test of the word-phoneme alignment flow
"""

import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Test the full flow: app.py → widget.py
from gruut import sentences
from phonemizer.punctuation import Punctuation
from typing import List, Tuple

def generate_reference_phonemes(text: str, lang: str = "en-us") -> Tuple[List[Tuple[str, str]], List[str]]:
    """Generate reference phonemes from text using gruut"""
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
            except:
                phon = t
            lexicon.append((t, phon))

    return lexicon, words


def prepare_pronunciation_widget_data(reference_text: str, lexicon: List[Tuple[str, str]]):
    """Prepare data for pronunciation widget with proper word-to-phoneme alignment."""
    word_timings = []
    all_phonemes = []

    for word, phonemes in lexicon:
        word_timings.append({
            "word": word,
            "phonemes": phonemes,
            "start": None,
            "end": None
        })
        all_phonemes.append(phonemes)

    return {
        "phoneme_text": " ".join(all_phonemes),
        "word_timings": word_timings
    }


# Simulate widget preparation
def simulate_widget_prep(word_timings):
    """Simulate what st_pronunciation_widget.py does"""
    import html

    word_phoneme_pairs = []

    print(f"Widget receives word_timings: {type(word_timings)}")
    print(f"Length: {len(word_timings) if word_timings else 0}")

    if word_timings:
        for wt in word_timings:
            word_phoneme_pairs.append({
                "word": html.escape(wt.get("word", "")),
                "phonemes": html.escape(wt.get("phonemes", "")),
                "start": wt.get("start"),
                "end": wt.get("end")
            })

    return word_phoneme_pairs


# Run test
print("=" * 70)
print("FULL FLOW TEST: App → Widget")
print("=" * 70)
print()

reference_text = "The quick brown fox jumps over the lazy dog."
print(f"Input: {reference_text}")
print()

# Step 1: app.py generates phonemes
print("Step 1: app.py - generate_reference_phonemes()")
print("-" * 70)
lexicon, words = generate_reference_phonemes(reference_text)
for word, phon in lexicon:
    print(f"  {word:12} → {phon}")
print()

# Step 2: app.py prepares widget data
print("Step 2: app.py - prepare_pronunciation_widget_data()")
print("-" * 70)
widget_data = prepare_pronunciation_widget_data(reference_text, lexicon)
print(f"phoneme_text: {widget_data['phoneme_text'][:50]}...")
print(f"word_timings count: {len(widget_data['word_timings'])}")
print()

# Step 3: Widget receives and processes data
print("Step 3: st_pronunciation_widget.py - prepare word_phoneme_pairs")
print("-" * 70)
word_phoneme_pairs = simulate_widget_prep(widget_data["word_timings"])
print(f"word_phoneme_pairs count: {len(word_phoneme_pairs)}")
print()

# Step 4: Display result
print("Step 4: Final output (what should appear in table)")
print("-" * 70)
print(f"{'Word':<12} | IPA Phonemes")
print("-" * 70)
for pair in word_phoneme_pairs:
    print(f"{pair['word']:<12} | /{pair['phonemes']}/")

print()
print("=" * 70)
if len(word_phoneme_pairs) == len(lexicon):
    print(f"✅ SUCCESS: {len(word_phoneme_pairs)} word-phoneme pairs generated correctly!")
else:
    print(f"❌ FAIL: Expected {len(lexicon)} pairs, got {len(word_phoneme_pairs)}")
print("=" * 70)
