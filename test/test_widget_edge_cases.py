"""
Test edge cases for the widget to ensure it doesn't crash in Streamlit Cloud
"""

import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Mock streamlit before importing the widget
class MockStreamlit:
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

sys.modules['streamlit'] = MockStreamlit()
sys.modules['streamlit.components'] = type(sys)('streamlit.components')
sys.modules['streamlit.components.v1'] = type(sys)('streamlit.components.v1')

class MockComponents:
    @staticmethod
    def html(html_code, height=300, scrolling=True):
        print(f"✓ HTML component rendered ({len(html_code)} chars)")

sys.modules['streamlit.components.v1'].html = MockComponents.html

# Now import the widget
from st_pronunciation_widget import streamlit_pronunciation_widget

print("=" * 70)
print("Testing Widget Edge Cases")
print("=" * 70)

# Test 1: Normal case with all data
print("\n[Test 1] Normal case with word_timings and syllable_timings")
try:
    streamlit_pronunciation_widget(
        reference_text="hello world",
        phoneme_text="h ɛ l oʊ w ɜː r l d",
        b64_audio="data:audio/mp3;base64,",
        word_timings=[
            {"word": "hello", "phonemes": "h ɛ l oʊ", "start": 0.0, "end": 0.5},
            {"word": "world", "phonemes": "w ɜː r l d", "start": 0.5, "end": 1.0}
        ],
        syllable_timings=[
            {"syllable": "hɛ", "start": 0.0, "end": 0.25},
            {"syllable": "loʊ", "start": 0.25, "end": 0.5},
            {"syllable": "wɜːrld", "start": 0.5, "end": 1.0}
        ]
    )
    print("✅ Test 1 PASSED")
except Exception as e:
    print(f"❌ Test 1 FAILED: {e}")

# Test 2: syllable_timings is None
print("\n[Test 2] syllable_timings is None")
try:
    streamlit_pronunciation_widget(
        reference_text="hello world",
        phoneme_text="h ɛ l oʊ w ɜː r l d",
        b64_audio="data:audio/mp3;base64,",
        word_timings=[
            {"word": "hello", "phonemes": "h ɛ l oʊ", "start": 0.0, "end": 0.5},
            {"word": "world", "phonemes": "w ɜː r l d", "start": 0.5, "end": 1.0}
        ],
        syllable_timings=None
    )
    print("✅ Test 2 PASSED")
except Exception as e:
    print(f"❌ Test 2 FAILED: {e}")

# Test 3: syllable_timings is empty list
print("\n[Test 3] syllable_timings is empty list")
try:
    streamlit_pronunciation_widget(
        reference_text="hello world",
        phoneme_text="h ɛ l oʊ w ɜː r l d",
        b64_audio="data:audio/mp3;base64,",
        word_timings=[
            {"word": "hello", "phonemes": "h ɛ l oʊ", "start": 0.0, "end": 0.5},
            {"word": "world", "phonemes": "w ɜː r l d", "start": 0.5, "end": 1.0}
        ],
        syllable_timings=[]
    )
    print("✅ Test 3 PASSED")
except Exception as e:
    print(f"❌ Test 3 FAILED: {e}")

# Test 4: syllable_timings with strings (not dicts)
print("\n[Test 4] syllable_timings with strings (legacy format)")
try:
    streamlit_pronunciation_widget(
        reference_text="hello world",
        phoneme_text="h ɛ l oʊ w ɜː r l d",
        b64_audio="data:audio/mp3;base64,",
        word_timings=[
            {"word": "hello", "phonemes": "h ɛ l oʊ", "start": 0.0, "end": 0.5},
            {"word": "world", "phonemes": "w ɜː r l d", "start": 0.5, "end": 1.0}
        ],
        syllable_timings=["hɛ", "loʊ", "wɜːrld"]
    )
    print("✅ Test 4 PASSED")
except Exception as e:
    print(f"❌ Test 4 FAILED: {e}")

# Test 5: word_timings is None
print("\n[Test 5] word_timings is None")
try:
    streamlit_pronunciation_widget(
        reference_text="hello world",
        phoneme_text="h ɛ l oʊ w ɜː r l d",
        b64_audio="data:audio/mp3;base64,",
        word_timings=None,
        syllable_timings=None
    )
    print("✅ Test 5 PASSED")
except Exception as e:
    print(f"❌ Test 5 FAILED: {e}")

# Test 6: All parameters None (minimal case)
print("\n[Test 6] All optional parameters None")
try:
    streamlit_pronunciation_widget(
        reference_text="hello",
        phoneme_text="h ɛ l oʊ",
        b64_audio="data:audio/mp3;base64,"
    )
    print("✅ Test 6 PASSED")
except Exception as e:
    print(f"❌ Test 6 FAILED: {e}")

# Test 7: Empty strings
print("\n[Test 7] Empty strings")
try:
    streamlit_pronunciation_widget(
        reference_text="",
        phoneme_text="",
        b64_audio="data:audio/mp3;base64,",
        word_timings=[],
        syllable_timings=[]
    )
    print("✅ Test 7 PASSED")
except Exception as e:
    print(f"❌ Test 7 FAILED: {e}")

print("\n" + "=" * 70)
print("All edge case tests completed!")
print("=" * 70)
