import json
import html
import streamlit as st
import streamlit.components.v1 as components
from typing import List, Optional, Dict

# Import syllabifier functions from dedicated module
from syllabifier import (
    normalize_phoneme_sequence,
    syllabify_phonemes,
    phonemes_to_syllables_with_fallback as _phonemes_to_syllables
)

# ---------------------------------------------------------------------------
# Helper: JSON safe dump for embedding in HTML
# ---------------------------------------------------------------------------

def _safe_json(obj):
    return json.dumps(obj, ensure_ascii=False)


def phonemes_to_syllables_with_fallback(phoneme_str: str, phoneme_timings: Optional[List[Dict]] = None) -> List[Dict]:
    """
    Wrapper around syllabifier function with Streamlit-specific error handling.
    """
    try:
        return _phonemes_to_syllables(phoneme_str, phoneme_timings)
    except Exception as e:
        # safe fallback with Streamlit warning
        st.warning(f"Syllabification failed: {e}")
        return []


# ---------------------------------------------------------------------------
# Main Streamlit widget (integrated): st_pronunciation_widget
# ---------------------------------------------------------------------------

def streamlit_pronunciation_widget(
    reference_text: str,
    phoneme_text: str,
    b64_audio: str,
    *,
    word_timings: Optional[List[dict]] = None,
    phoneme_timings: Optional[List[dict]] = None,
    syllable_timings: Optional[List[dict]] = None,
    height: int = 300,
    title: Optional[str] = None
):
    """
    Inserta en Streamlit un widget de pronunciación avanzado con soporte para sílabas.

    - NO cambia la firma.
    - Si no recibe syllable_timings intentará inferir sílabas desde phoneme_text
      y phoneme_timings usando el syllabifier implementado arriba.

    Priority for display timings (front-end logic expects):
        1. word_timings (if provided)
        2. syllable_timings (if provided or inferred)
        3. phoneme_timings (if provided)
        4. fallback: equal partitions computed client-side
    """

    # Normalize audio src
    if b64_audio.strip().startswith("data:"):
        src = b64_audio.strip()
    else:
        src = f"data:audio/mp3;base64,{b64_audio.strip()}"

    # Prepare tokens
    words = [html.escape(w) for w in reference_text.strip().split()] if reference_text else []
    phonemes = normalize_phoneme_sequence(phoneme_text) if phoneme_text else []
    phonemes_escaped = [html.escape(p) for p in phonemes]

    # Prepare word-to-phoneme mapping for display
    word_phoneme_pairs = []
    if word_timings:
        for wt in word_timings:
            word_phoneme_pairs.append({
                "word": html.escape(wt.get("word", "")),
                "phonemes": html.escape(wt.get("phonemes", "")),
                "start": wt.get("start"),
                "end": wt.get("end")
            })
    else:
        # Fallback: try to partition phonemes equally across words
        # This is a best-effort when word_timings aren't provided
        if words and phonemes:
            phonemes_per_word = len(phonemes) // len(words) if len(words) > 0 else 0
            for i, word in enumerate(words):
                start_idx = i * phonemes_per_word
                end_idx = start_idx + phonemes_per_word if i < len(words) - 1 else len(phonemes)
                phon_slice = phonemes[start_idx:end_idx]
                word_phoneme_pairs.append({
                    "word": word,
                    "phonemes": " ".join(phon_slice),
                    "start": None,
                    "end": None
                })

    # If syllable_timings not provided, infer syllables from phoneme_text (+ timings if available)
    inferred_syllables = None
    if syllable_timings and len(syllable_timings) > 0:
        # accept user-provided syllable timings (ensure format)
        inferred_syllables = []
        for s in syllable_timings:
            if isinstance(s, dict):
                inferred_syllables.append({
                    "syllable": s.get("syllable", ""),
                    "start": s.get("start"),
                    "end": s.get("end")
                })
            else:
                # s is a string
                inferred_syllables.append({
                    "syllable": str(s),
                    "start": None,
                    "end": None
                })
    else:
        # try inference
        try:
            inferred_syllables = phonemes_to_syllables_with_fallback(phoneme_text, phoneme_timings)
            # if inference returns empty and we have phonemes but no timings, still produce syllable strings
            if not inferred_syllables and phonemes:
                inferred_syllables = [{"syllable": "".join(pgroup), "phonemes": pgroup, "start": None, "end": None}
                                       for pgroup in syllabify_phonemes(phonemes)]
        except Exception as e:
            # Log the error but don't crash
            print(f"Syllabification error: {e}")
            inferred_syllables = []

    # Prepare arrays for payload (escape syllable text)
    syllable_texts = []
    if inferred_syllables:
        for s in inferred_syllables:
            if isinstance(s, dict):
                syllable_texts.append(html.escape(s.get("syllable", "")))
            else:
                syllable_texts.append(html.escape(str(s)))

    # Ensure timings objects are lists of dicts in expected format
    payload_word_timings = word_timings if word_timings is not None else []
    payload_phoneme_timings = phoneme_timings if phoneme_timings is not None else []

    # syllable timings: if inferred_syllables have timing info, map them to expected dicts
    payload_syllable_timings = []
    if inferred_syllables:
        for s in inferred_syllables:
            if isinstance(s, dict):
                payload_syllable_timings.append({
                    "syllable": s.get("syllable", ""),
                    "start": s.get("start"),
                    "end": s.get("end")
                })
            else:
                payload_syllable_timings.append({
                    "syllable": str(s),
                    "start": None,
                    "end": None
                })

    payload = {
        "words": words,
        "phonemes": phonemes_escaped,
        "syllables": syllable_texts,
        "word_timings": payload_word_timings,
        "phoneme_timings": payload_phoneme_timings,
        "syllable_timings": payload_syllable_timings,
        "word_phoneme_pairs": word_phoneme_pairs,
        "audio_src": src,
        "title": title or "",
    }

    # Debug: Show in Streamlit UI (optional - can be commented out in production)
    # if word_phoneme_pairs:
    #     st.info(f"✓ Prepared {len(word_phoneme_pairs)} word-phoneme mappings")
    # elif word_timings:
    #     st.warning(f"⚠️ word_timings provided ({len(word_timings)} items) but word_phoneme_pairs is empty")
    # else:
    #     st.warning("⚠️ No word_timings provided to widget")

    # HTML + JS UI (fixed timing-priority and using syllables correctly)
    html_code = f"""
    <div id="st-pron-widget" style="font-family: Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; max-width:900px; margin: 6px auto;">
<style>
        /* Card and layout */
        .pp-card {{ background:#ffffff; border:1px solid #d0d7e3; border-radius:8px; padding:18px; box-shadow:0 2px 5px rgba(0,0,0,0.06); }}
        .pp-header {{ display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:12px; }}
        .pp-title {{ font-weight:700; font-size:16px; color:#2b2b2b; font-family:"Calibri","Segoe UI",sans-serif; }}
        .pp-controls {{ display:flex; gap:8px; align-items:center; }}
        .pp-select {{ padding:6px 10px; border-radius:6px; border:1px solid #c8d0db; background:#f6f8fa; font-size:14px; font-family:"Calibri","Segoe UI",sans-serif; }}

        /* Token rows - unify chip appearance by default using .pp-word */
        .pp-text, .pp-phonemes, .pp-syllables {{ display:flex; flex-wrap:wrap; gap:6px; justify-content:center; padding:6px 4px; }}
        .pp-word {{
            padding:6px 12px;
            border-radius:999px;
            font-size:16px;
            transition: background-color 120ms ease, color 120ms ease, transform 120ms ease;
            color:#1f3b57;
            background:#f2f4f7;
            font-family:"Calibri","Segoe UI",sans-serif;
            display:inline-flex;
            align-items:center;
            justify-content:center;
        }}

        /* Phoneme / syllable inherit chip style but change monospace font */
        .pp-phon {{ font-family:'Courier New', monospace; color:#8a1d1d; font-size:15px; }}
        .pp-syll {{ font-family:'Courier New', monospace; color:#8a1d1d; font-size:15px; }}

        /* Active variants */
        .pp-syll.active {{ background:#ffd7d7; color:#2b2b2b; box-shadow:0 2px 5px rgba(180,50,50,0.12); transform:translateY(-2px); }}
        .pp-word.active {{ background:#ffe7a6; color:#2b2b2b; box-shadow:0 2px 6px rgba(230,160,40,0.14); transform:translateY(-2px); }}
        .pp-phon.active {{ background:#ffd7d7; color:#2b2b2b; box-shadow:0 2px 5px rgba(180,50,50,0.12); transform:translateY(-2px); }}

        /* Buttons & meta */
        .pp-button {{ padding:10px 18px; border-radius:8px; border:1px solid #1b6cff; cursor:pointer; font-weight:600; font-size:15px; background:#1b6cff; color:white; font-family:"Calibri","Segoe UI",sans-serif; box-shadow:0 3px 8px rgba(27,108,255,0.16); }}
        .pp-button.pause {{ background:#4a5568; border-color:#4a5568; }}
        .pp-meta {{ margin-top:10px; font-size:12px; color:#4b5c70; text-align:center; font-family:"Calibri","Segoe UI",sans-serif; }}

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

        .pp-chip-word.active {{
          background:#ffe7a6;
          transform:translateY(-2px);
          box-shadow:0 2px 6px rgba(230,160,40,0.14);
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

        .pp-chip-syll.active {{
          background:#ffd7d7;
          transform:translateY(-2px);
          box-shadow:0 2px 5px rgba(180,50,50,0.12);
        }}
</style>


      <div class="pp-card">
        <div class="pp-header">
          <div class="pp-title">Pronunciation Trainer {html.escape(payload['title'])}</div>
          <div class="pp-controls">
            <select id="pp-speed" class="pp-select" onchange="ppChangeSpeed()" title="Playback speed">
              <option value="0.5">0.5x</option>
              <option value="0.75">0.75x</option>
              <option value="1.0" selected>1.0x</option>
              <option value="1.25">1.25x</option>
              <option value="1.5">1.5x</option>
            </select>
            <button id="pp-play" class="pp-button" onclick="ppTogglePlay()" aria-pressed="false">▶ Play</button>
          </div>
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

        <audio id="pp-audio" preload="metadata" style="display:none">
          <source src="{payload['audio_src']}" type="audio/mp3">
          Your browser does not support the audio element.
        </audio>
      </div>

      <script>
        (function() {{
          const payload = {_safe_json(payload)};
          const audio = document.getElementById('pp-audio');
          const playBtn = document.getElementById('pp-play');
          const speedSelect = document.getElementById('pp-speed');

          // Render horizontal viewer with words and syllables
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

            // Debug: log payload data
            console.log('Rendering horizontal viewer');
            console.log('payload.word_timings:', payload.word_timings);
            console.log('payload.syllable_timings:', payload.syllable_timings);

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
                wordText.textContent = wt.word || wt.text || '?';

                const ipaText = document.createElement('div');
                ipaText.className = 'pp-chip-word-ipa';
                ipaText.textContent = '/' + (wt.phonemes || wt.ipa || '?') + '/';

                chip.appendChild(wordText);
                chip.appendChild(ipaText);
                wordsRow.appendChild(chip);
              }});
            }} else {{
              const msg = document.createElement('div');
              msg.style.cssText = 'padding:8px; color:#e53e3e; font-weight:600;';
              msg.textContent = '⚠️ No word data available';
              wordsRow.appendChild(msg);
            }}

            // Render syllables with timing data
            if (payload.syllable_timings && payload.syllable_timings.length) {{
              payload.syllable_timings.forEach((st, i) => {{
                const chip = document.createElement('div');
                chip.className = 'pp-chip-syll';
                chip.dataset.index = i;
                chip.dataset.start = st.start ?? 0;
                chip.dataset.end = st.end ?? 0;
                chip.textContent = st.syllable || st;
                syllRow.appendChild(chip);
              }});
            }} else if (payload.syllables && payload.syllables.length) {{
              // Fallback to syllables without timings
              payload.syllables.forEach((syl, i) => {{
                const chip = document.createElement('div');
                chip.className = 'pp-chip-syll';
                chip.dataset.index = i;
                chip.textContent = syl;
                syllRow.appendChild(chip);
              }});
            }} else {{
              const msg = document.createElement('div');
              msg.style.cssText = 'padding:8px; color:#718096; font-style:italic;';
              msg.textContent = 'No syllable data available';
              syllRow.appendChild(msg);
            }}
          }}

          // Highlight and auto-scroll based on current time (karaoke mode)
          function highlightByTime(currentTime) {{
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
          }}

          // Simple audio playback controls
          function togglePlay() {{
            if (audio.paused) {{
              audio.play().catch(()=>{{}}); // ignore play promise rejections in restricted contexts
              playBtn.textContent = '⏸ Pause';
              playBtn.classList.add('pause');
              playBtn.setAttribute('aria-pressed', 'true');
            }} else {{
              audio.pause();
              playBtn.textContent = '▶ Resume';
              playBtn.classList.remove('pause');
              playBtn.setAttribute('aria-pressed', 'false');
            }}
          }}

          audio.onended = function() {{
            playBtn.textContent = '▶ Replay';
            playBtn.classList.remove('pause');
            playBtn.setAttribute('aria-pressed', 'false');
            audio.currentTime = 0;
          }};

          audio.onloadedmetadata = function() {{
            // enable controls when audio is ready
            playBtn.disabled = false;
            speedSelect.disabled = false;
          }};

          // Sync highlighting with audio time (karaoke mode)
          audio.addEventListener('timeupdate', function() {{
            highlightByTime(audio.currentTime);
          }});

          // hookup global functions for Streamlit calls
          window.ppChangeSpeed = function() {{ audio.playbackRate = parseFloat(speedSelect.value); }};
          window.ppTogglePlay = function() {{ togglePlay(); }};

          // initial render of horizontal viewer
          renderHorizontalViewer();

          // defensive: hide play until metadata loaded (prevents weird behavior)
          playBtn.disabled = true;
          speedSelect.disabled = true;
        }})();
      </script>
    </div>
    """

    components.html(html_code, height=height, scrolling=True)
