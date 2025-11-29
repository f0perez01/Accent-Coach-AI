"""
Visual test for the horizontal widget layout.
This generates a standalone HTML file to verify the widget renders correctly.
"""

import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import html

# Sample data (same as test_full_widget_flow.py output)
word_phoneme_pairs = [
    {"word": "the", "phonemes": "ð ə", "start": None, "end": None},
    {"word": "quick", "phonemes": "k w ˈɪ k", "start": None, "end": None},
    {"word": "brown", "phonemes": "b ɹ ˈaʊ n", "start": None, "end": None},
    {"word": "fox", "phonemes": "f ˈɑ k s", "start": None, "end": None},
    {"word": "jumps", "phonemes": "d͡ʒ ˈʌ m p s", "start": None, "end": None},
    {"word": "over", "phonemes": "ˈoʊ v ɚ", "start": None, "end": None},
    {"word": "the", "phonemes": "ð ə", "start": None, "end": None},
    {"word": "lazy", "phonemes": "l ˈeɪ z i", "start": None, "end": None},
    {"word": "dog", "phonemes": "d ˈɔ ɡ", "start": None, "end": None},
]

syllables = ["ðə", "kwɪk", "bɹaʊn", "fɑks", "d͡ʒʌmps", "oʊ", "vɚ", "ðə", "leɪ", "zi", "dɔɡ"]

payload = {
    "word_phoneme_pairs": word_phoneme_pairs,
    "syllables": syllables,
    "audio_src": "data:audio/mp3;base64,",  # Empty audio for testing
}

# Generate HTML
html_output = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Widget Visual Test</title>
</head>
<body style="padding:20px; background:#f0f0f0; font-family:sans-serif;">

<h1>Horizontal Widget Visual Test</h1>
<p>Testing the new horizontal layout with words and syllables.</p>

<div id="st-pron-widget" style="font-family: Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; max-width:900px; margin: 6px auto;">
<style>
    /* Card and layout */
    .pp-card {{ background:#ffffff; border:1px solid #d0d7e3; border-radius:8px; padding:18px; box-shadow:0 2px 5px rgba(0,0,0,0.06); }}
    .pp-header {{ display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:12px; }}
    .pp-title {{ font-weight:700; font-size:16px; color:#2b2b2b; font-family:"Calibri","Segoe UI",sans-serif; }}

    /* Horizontal viewer styles */
    .pp-row-label {{
        font-size:14px;
        font-weight:600;
        color:#4a5568;
        margin-bottom:6px;
        font-family:"Calibri","Segoe UI",sans-serif;
    }}

    /* Scrollable horizontal chips */
    .pp-chip-row {{
        display:flex;
        gap:8px;
        overflow-x:auto;
        padding:6px 4px;
        scroll-behavior:smooth;
    }}

    /* Word chips with IPA below */
    .pp-chip-word {{
        padding:10px 16px;
        background:#f2f4f7;
        color:#1f3b57;
        border-radius:20px;
        white-space:nowrap;
        font-size:16px;
        font-family:"Calibri","Segoe UI",sans-serif;
        transition:all .15s ease;
        display:flex;
        flex-direction:column;
        align-items:center;
        gap:4px;
    }}

    .pp-chip-word-text {{
        font-weight:600;
    }}

    .pp-chip-word-ipa {{
        font-family:'Courier New', monospace;
        font-size:13px;
        color:#8a1d1d;
    }}

    .pp-chip-word:hover {{
        background:#e8ecf0;
        transform:translateY(-2px);
        box-shadow:0 2px 6px rgba(100,120,140,0.14);
    }}

    /* Syllable chips */
    .pp-chip-syll {{
        padding:6px 12px;
        background:#f6e3e3;
        border-radius:16px;
        white-space:nowrap;
        font-family:'Courier New', monospace;
        color:#8a1d1d;
        font-size:15px;
        transition:all .15s ease;
    }}

    .pp-chip-syll:hover {{
        background:#ffd7d7;
        transform:translateY(-2px);
        box-shadow:0 2px 5px rgba(180,50,50,0.12);
    }}
</style>

<div class="pp-card">
    <div class="pp-header">
        <div class="pp-title">Pronunciation Trainer - Visual Test</div>
    </div>

    <!-- Horizontal Word & Syllable Viewer -->
    <div id="pp-horizontal-viewer" style="margin-top:16px; margin-bottom:16px;">

        <!-- Words row -->
        <div class="pp-row-label">Words & IPA</div>
        <div id="pp-words-row" class="pp-chip-row"></div>

        <!-- Syllables row -->
        <div class="pp-row-label" style="margin-top:12px;">Syllables</div>
        <div id="pp-syllables-row" class="pp-chip-row"></div>

    </div>
</div>

<script>
(function() {{
    const payload = {json.dumps(payload, ensure_ascii=False)};

    function renderHorizontalViewer() {{
        const wordsRow = document.getElementById('pp-words-row');
        const syllRow = document.getElementById('pp-syllables-row');

        if (!wordsRow || !syllRow) {{
            console.warn('Horizontal viewer containers not found');
            return;
        }}

        // Clear rows
        wordsRow.innerHTML = '';
        syllRow.innerHTML = '';

        console.log('Rendering horizontal viewer');
        console.log('word_phoneme_pairs:', payload.word_phoneme_pairs);
        console.log('syllables:', payload.syllables);

        // Render words with IPA
        if (payload.word_phoneme_pairs && payload.word_phoneme_pairs.length) {{
            payload.word_phoneme_pairs.forEach(pair => {{
                const chip = document.createElement('div');
                chip.className = 'pp-chip-word';

                const wordText = document.createElement('div');
                wordText.className = 'pp-chip-word-text';
                wordText.textContent = pair.word;

                const ipaText = document.createElement('div');
                ipaText.className = 'pp-chip-word-ipa';
                ipaText.textContent = '/' + pair.phonemes + '/';

                chip.appendChild(wordText);
                chip.appendChild(ipaText);
                wordsRow.appendChild(chip);
            }});
        }}

        // Render syllables
        if (payload.syllables && payload.syllables.length) {{
            payload.syllables.forEach(syl => {{
                const chip = document.createElement('div');
                chip.className = 'pp-chip-syll';
                chip.textContent = syl;
                syllRow.appendChild(chip);
            }});
        }}
    }}

    // Render on load
    renderHorizontalViewer();
}})();
</script>

</div>

<div style="margin-top:20px; padding:12px; background:#ffffff; border-radius:8px; max-width:900px; margin:20px auto;">
    <h2>Expected Output:</h2>
    <ul>
        <li>✅ Words row should show 9 word chips with IPA below each word</li>
        <li>✅ Syllables row should show 11 syllable chips</li>
        <li>✅ Both rows should be horizontally scrollable</li>
        <li>✅ Hover effects should work (translateY and color change)</li>
    </ul>
</div>

</body>
</html>
"""

# Write to file
output_file = "widget_visual_test.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_output)

print("=" * 70)
print("Visual test HTML generated successfully!")
print("=" * 70)
print(f"\nOutput file: {output_file}")
print("\nOpen this file in your browser to see the horizontal widget layout.")
print("\nExpected:")
print("  - 9 word chips (the, quick, brown, fox, jumps, over, the, lazy, dog)")
print("  - Each word chip shows the word above and IPA phonemes below")
print("  - 11 syllable chips in monospace font")
print("  - Both rows are horizontally scrollable")
print("=" * 70)
