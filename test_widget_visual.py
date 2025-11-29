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

# Sample data with simulated timings for karaoke effect
word_timings = [
    {"word": "the", "phonemes": "ð ə", "start": 0.0, "end": 0.5},
    {"word": "quick", "phonemes": "k w ˈɪ k", "start": 0.5, "end": 1.0},
    {"word": "brown", "phonemes": "b ɹ ˈaʊ n", "start": 1.0, "end": 1.5},
    {"word": "fox", "phonemes": "f ˈɑ k s", "start": 1.5, "end": 2.0},
    {"word": "jumps", "phonemes": "d͡ʒ ˈʌ m p s", "start": 2.0, "end": 2.5},
    {"word": "over", "phonemes": "ˈoʊ v ɚ", "start": 2.5, "end": 3.0},
    {"word": "the", "phonemes": "ð ə", "start": 3.0, "end": 3.5},
    {"word": "lazy", "phonemes": "l ˈeɪ z i", "start": 3.5, "end": 4.0},
    {"word": "dog", "phonemes": "d ˈɔ ɡ", "start": 4.0, "end": 4.5},
]

syllable_timings = [
    {"syllable": "ðə", "start": 0.0, "end": 0.5},
    {"syllable": "kwɪk", "start": 0.5, "end": 1.0},
    {"syllable": "bɹaʊn", "start": 1.0, "end": 1.5},
    {"syllable": "fɑks", "start": 1.5, "end": 2.0},
    {"syllable": "d͡ʒʌmps", "start": 2.0, "end": 2.5},
    {"syllable": "oʊ", "start": 2.5, "end": 2.8},
    {"syllable": "vɚ", "start": 2.8, "end": 3.0},
    {"syllable": "ðə", "start": 3.0, "end": 3.5},
    {"syllable": "leɪ", "start": 3.5, "end": 3.8},
    {"syllable": "zi", "start": 3.8, "end": 4.0},
    {"syllable": "dɔɡ", "start": 4.0, "end": 4.5},
]

payload = {
    "word_timings": word_timings,
    "syllable_timings": syllable_timings,
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
        console.log('word_timings:', payload.word_timings);
        console.log('syllable_timings:', payload.syllable_timings);

        // Render words with IPA and timing data
        if (payload.word_timings && payload.word_timings.length) {{
            payload.word_timings.forEach((wt, i) => {{
                const chip = document.createElement('div');
                chip.className = 'pp-chip-word';
                chip.dataset.index = i;
                chip.dataset.start = wt.start ?? 0;
                chip.dataset.end = wt.end ?? 0;

                const wordText = document.createElement('div');
                wordText.className = 'pp-chip-word-text';
                wordText.textContent = wt.word;

                const ipaText = document.createElement('div');
                ipaText.className = 'pp-chip-word-ipa';
                ipaText.textContent = '/' + wt.phonemes + '/';

                chip.appendChild(wordText);
                chip.appendChild(ipaText);
                wordsRow.appendChild(chip);
            }});
        }}

        // Render syllables with timing data
        if (payload.syllable_timings && payload.syllable_timings.length) {{
            payload.syllable_timings.forEach((st, i) => {{
                const chip = document.createElement('div');
                chip.className = 'pp-chip-syll';
                chip.dataset.index = i;
                chip.dataset.start = st.start ?? 0;
                chip.dataset.end = st.end ?? 0;
                chip.textContent = st.syllable;
                syllRow.appendChild(chip);
            }});
        }}
    }}

    // Simulate karaoke highlighting effect
    function simulateKaraoke() {{
        let currentTime = 0;
        const duration = 4.5;
        const interval = 100; // Update every 100ms

        const timer = setInterval(() => {{
            currentTime += interval / 1000;

            // Highlight words
            document.querySelectorAll('.pp-chip-word').forEach(chip => {{
                const start = parseFloat(chip.dataset.start);
                const end = parseFloat(chip.dataset.end);

                if (currentTime >= start && currentTime <= end) {{
                    chip.classList.add('active');
                    chip.scrollIntoView({{ behavior: 'smooth', inline: 'center', block: 'nearest' }});
                }} else {{
                    chip.classList.remove('active');
                }}
            }});

            // Highlight syllables
            document.querySelectorAll('.pp-chip-syll').forEach(chip => {{
                const start = parseFloat(chip.dataset.start);
                const end = parseFloat(chip.dataset.end);

                if (currentTime >= start && currentTime <= end) {{
                    chip.classList.add('active');
                    chip.scrollIntoView({{ behavior: 'smooth', inline: 'center', block: 'nearest' }});
                }} else {{
                    chip.classList.remove('active');
                }}
            }});

            // Stop when done
            if (currentTime >= duration) {{
                clearInterval(timer);
                // Reset all
                document.querySelectorAll('.pp-chip-word, .pp-chip-syll').forEach(chip => {{
                    chip.classList.remove('active');
                }});
            }}
        }}, interval);
    }}

    // Render on load
    renderHorizontalViewer();

    // Add button to test karaoke effect
    window.testKaraoke = simulateKaraoke;
}})();
</script>

</div>

<div style="margin-top:20px; padding:12px; background:#ffffff; border-radius:8px; max-width:900px; margin:20px auto;">
    <h2>Test Karaoke Effect:</h2>
    <button onclick="testKaraoke()" style="padding:10px 20px; background:#1b6cff; color:white; border:none; border-radius:8px; cursor:pointer; font-size:16px; font-weight:600;">
        ▶ Simulate Karaoke Highlighting
    </button>
    <p style="margin-top:8px; color:#666; font-size:14px;">Click to see auto-scroll and highlighting synchronized with simulated audio timing</p>
</div>

<div style="margin-top:20px; padding:12px; background:#ffffff; border-radius:8px; max-width:900px; margin:20px auto;">
    <h2>Expected Output:</h2>
    <ul>
        <li>✅ Words row should show 9 word chips with IPA below each word</li>
        <li>✅ Syllables row should show 11 syllable chips</li>
        <li>✅ Both rows should be horizontally scrollable</li>
        <li>✅ Hover effects should work (translateY and color change)</li>
        <li>✅ Click "Simulate Karaoke" to see synchronized highlighting and auto-scroll</li>
        <li>✅ Active chips should turn yellow (words) or pink (syllables)</li>
        <li>✅ Chips should auto-scroll to center as they become active</li>
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
