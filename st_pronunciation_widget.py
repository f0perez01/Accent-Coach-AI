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
        inferred_syllables = [
            {"syllable": s.get("syllable") if isinstance(s, dict) else s, "start": s.get("start"), "end": s.get("end")}
            for s in syllable_timings
        ]
    else:
        # try inference
        try:
            inferred_syllables = phonemes_to_syllables_with_fallback(phoneme_text, phoneme_timings)
            # if inference returns empty and we have phonemes but no timings, still produce syllable strings
            if not inferred_syllables and phonemes:
                inferred_syllables = [{"syllable": "".join(pgroup), "phonemes": pgroup, "start": None, "end": None}
                                       for pgroup in syllabify_phonemes(phonemes)]
        except Exception:
            inferred_syllables = []

    # Prepare arrays for payload (escape syllable text)
    syllable_texts = [html.escape(s.get("syllable") if isinstance(s, dict) else s) for s in inferred_syllables] if inferred_syllables else []

    # Ensure timings objects are lists of dicts in expected format
    payload_word_timings = word_timings or []
    payload_phoneme_timings = phoneme_timings or []
    # syllable timings: if inferred_syllables have timing info, map them to expected dicts
    payload_syllable_timings = []
    if inferred_syllables:
        for s in inferred_syllables:
            start = s.get("start") if isinstance(s, dict) else None
            end = s.get("end") if isinstance(s, dict) else None
            payload_syllable_timings.append({"syllable": s.get("syllable") if isinstance(s, dict) else s, "start": start, "end": end})

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

    # Debug: Show in Streamlit UI
    if word_phoneme_pairs:
        st.info(f"✓ Prepared {len(word_phoneme_pairs)} word-phoneme mappings")
    elif word_timings:
        st.warning(f"⚠️ word_timings provided ({len(word_timings)} items) but word_phoneme_pairs is empty")
    else:
        st.warning("⚠️ No word_timings provided to widget")

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

        <!-- Word-to-Phoneme Mapping Table -->
        <div id="pp-word-phoneme-map" style="margin-top:12px; margin-bottom:12px; max-height:200px; overflow-y:auto;">
          <div style="display:grid; grid-template-columns: minmax(80px, auto) 1fr; gap:4px 8px; font-size:14px; background:#f8f9fb; padding:10px; border-radius:6px; border:1px solid #e3e8ef;">
            <!-- Header -->
            <div style="font-weight:600; color:#4a5568; border-bottom:1px solid #d1d9e4; padding-bottom:4px;">Word</div>
            <div style="font-weight:600; color:#4a5568; border-bottom:1px solid #d1d9e4; padding-bottom:4px;">IPA Phonemes</div>
            <!-- Rows will be inserted by JS -->
          </div>
        </div>

        <div id="pp-text-area" class="pp-text" aria-hidden="false" role="group" aria-label="Words"></div>
        <div id="pp-syll-area" class="pp-syllables" aria-hidden="true" style="margin-top:6px; display:none;" role="group" aria-label="Syllables"></div>
        <div id="pp-phon-area" class="pp-phonemes" aria-hidden="false" style="margin-top:6px;" role="group" aria-label="Phonemes"></div>

        <div class="pp-meta">Velocidad y resaltado sincronizados. Pausa congela la posición.</div>

        <audio id="pp-audio" preload="metadata" style="display:none">
          <source src="{payload['audio_src']}" type="audio/mp3">
          Your browser does not support the audio element.
        </audio>
      </div>

      <script>
        (function() {{
          const payload = {_safe_json(payload)};
          const words = payload.words || [];
          const phonemes = payload.phonemes || [];
          const audio = document.getElementById('pp-audio');
          const textArea = document.getElementById('pp-text-area');
          const phonArea = document.getElementById('pp-phon-area');
          const syllArea = document.getElementById('pp-syll-area');
          const playBtn = document.getElementById('pp-play');
          const speedSelect = document.getElementById('pp-speed');

          // Render spans: each token uses .pp-word to guarantee consistent chip visuals.
          function renderSpans() {{
            textArea.innerHTML = '';
            words.forEach((w, i) => {{
              const span = document.createElement('span');
              span.className = 'pp-word';
              span.dataset.index = i;
              span.dataset.word = w;
              span.textContent = w;
              textArea.appendChild(span);
            }});

            // syllables (use pp-word + pp-syll so they look like chips but with monospace)
            if (payload.syllables && payload.syllables.length) {{
              syllArea.style.display = 'flex';
              syllArea.setAttribute('aria-hidden', 'false');
              syllArea.innerHTML = '';
              payload.syllables.forEach((s, i) => {{
                const span = document.createElement('span');
                span.className = 'pp-word pp-syll';
                span.dataset.index = i;
                span.dataset.syllable = s;
                span.textContent = s;
                syllArea.appendChild(span);
              }});
            }} else {{
              syllArea.style.display = 'none';
              syllArea.setAttribute('aria-hidden', 'true');
            }}

            phonArea.innerHTML = '';
            phonemes.forEach((p, i) => {{
              const span = document.createElement('span');
              span.className = 'pp-word pp-phon';
              span.dataset.index = i;
              span.dataset.phoneme = p;
              span.textContent = p;
              phonArea.appendChild(span);
            }});
          }}

          // Render word-to-phoneme mapping table
          function renderWordPhonemeMap() {{
            const mapContainer = document.getElementById('pp-word-phoneme-map');
            if (!mapContainer) {{
              console.warn('Word-phoneme map container not found');
              return;
            }}

            const grid = mapContainer.querySelector('div');
            if (!grid) {{
              console.warn('Grid element not found');
              return;
            }}

            // Debug: log payload data
            console.log('Rendering word-phoneme map');
            console.log('payload.word_phoneme_pairs:', payload.word_phoneme_pairs);
            console.log('payload.word_timings:', payload.word_timings);

            // Clear existing rows (keep headers)
            while (grid.children.length > 2) {{
              grid.removeChild(grid.lastChild);
            }}

            // Add rows from word_phoneme_pairs
            if (payload.word_phoneme_pairs && payload.word_phoneme_pairs.length) {{
              console.log('Rendering', payload.word_phoneme_pairs.length, 'word-phoneme pairs');
              payload.word_phoneme_pairs.forEach((pair, idx) => {{
                // Word cell
                const wordCell = document.createElement('div');
                wordCell.style.cssText = 'padding:4px 6px; color:#2d3748; background:#ffffff; border-radius:4px;';
                wordCell.textContent = pair.word;
                grid.appendChild(wordCell);

                // Phonemes cell
                const phonCell = document.createElement('div');
                phonCell.style.cssText = "padding:4px 6px; color:#9b2c2c; font-family:'Courier New', monospace; background:#ffffff; border-radius:4px;";
                phonCell.textContent = '/' + pair.phonemes + '/';
                grid.appendChild(phonCell);
              }});
            }} else {{
              // Fallback: show message if no mapping available
              console.warn('No word_phoneme_pairs available');
              const msgCell = document.createElement('div');
              msgCell.style.cssText = 'grid-column: 1 / -1; padding:8px; text-align:center; color:#e53e3e; font-weight:600; background:#fff5f5; border-radius:4px;';
              msgCell.textContent = '⚠️ Word-phoneme mapping not available';
              grid.appendChild(msgCell);

              // Try to use word_timings as fallback
              if (payload.word_timings && payload.word_timings.length) {{
                console.log('Using word_timings as fallback');
                payload.word_timings.forEach((wt, idx) => {{
                  const wordCell = document.createElement('div');
                  wordCell.style.cssText = 'padding:4px 6px; color:#2d3748; background:#fffbeb; border-radius:4px;';
                  wordCell.textContent = wt.word || wt.text || '?';
                  grid.appendChild(wordCell);

                  const phonCell = document.createElement('div');
                  phonCell.style.cssText = "padding:4px 6px; color:#9b2c2c; font-family:'Courier New', monospace; background:#fffbeb; border-radius:4px;";
                  phonCell.textContent = '/' + (wt.phonemes || wt.ipa || '?') + '/';
                  grid.appendChild(phonCell);
                }});
              }}
            }}
          }}

          // Compute timings with correct priority (respecting provided timings)
          function computeTimingsIfMissing() {{
            const duration = audio.duration || 0.0;

            // Priority 1: word timings
            let wTimings = (payload.word_timings && payload.word_timings.length) ? payload.word_timings : null;

            // Priority 2: syllable timings
            let sTimings = (payload.syllable_timings && payload.syllable_timings.length) ? payload.syllable_timings : null;

            // Priority 3: phoneme timings
            let pTimings = (payload.phoneme_timings && payload.phoneme_timings.length) ? payload.phoneme_timings : null;

            // Fallbacks: create uniform partitions when missing
            if (!wTimings) {{
              const n = Math.max(words.length, 1);
              const seg = duration / n;
              wTimings = words.map((w, i) => ({{ word: w, start: +(i * seg).toFixed(3), end: +(((i + 1) * seg)).toFixed(3) }}));
            }}

            if (!sTimings && payload.syllables && payload.syllables.length) {{
              const n = Math.max(payload.syllables.length, 1);
              const seg = duration / n;
              sTimings = payload.syllables.map((s, i) => ({{ syllable: s, start: +(i * seg).toFixed(3), end: +(((i + 1) * seg)).toFixed(3) }}));
            }}

            if (!pTimings) {{
              const n = Math.max(phonemes.length, 1);
              const seg = duration / n;
              pTimings = phonemes.map((p, i) => ({{ phoneme: p, start: +(i * seg).toFixed(3), end: +(((i + 1) * seg)).toFixed(3) }}));
            }}

            return {{ wTimings, sTimings, pTimings }};
          }}

          function findActiveIndices(t, timings) {{
            const active = [];
            if (!timings || !timings.length) return active;
            for (let i = 0; i < timings.length; i++) {{
              const it = timings[i];
              if (it == null) continue;
              const s = it.start, e = it.end;
              if (s == null || e == null) continue;
              // include end when t is very close to duration (to avoid missing final token)
              if (t >= s && t < e) active.push(i);
            }}
            return active;
          }}

          function clearActive() {{
            document.querySelectorAll('.pp-word.active, .pp-syll.active, .pp-phon.active').forEach(el => el.classList.remove('active'));
          }}

          let timings = null;
          let rafId = null;

          // Single RAF loop for sync
          function syncFrame() {{
            const t = audio.currentTime;
            const activeWords = timings && timings.wTimings ? findActiveIndices(t, timings.wTimings) : [];
            const activeSylls = timings && timings.sTimings ? findActiveIndices(t, timings.sTimings) : [];
            const activePh = timings && timings.pTimings ? findActiveIndices(t, timings.pTimings) : [];

            clearActive();

            // apply word highlights (highest priority)
            activeWords.forEach(i => {{
              const el = textArea.querySelector('.pp-word[data-index="' + i + '"]');
              if (el) el.classList.add('active');
            }});

            // apply syllable highlights (second priority)
            activeSylls.forEach(i => {{
              const el = syllArea.querySelector('.pp-word.pp-syll[data-index="' + i + '"]');
              if (el) el.classList.add('active');
            }});

            // apply phoneme highlights (third priority)
            activePh.forEach(i => {{
              const el = phonArea.querySelector('.pp-word.pp-phon[data-index="' + i + '"]');
              if (el) el.classList.add('active');
            }});

            rafId = window.requestAnimationFrame(syncFrame);
          }}

          function startRAF() {{
            if (rafId) window.cancelAnimationFrame(rafId);
            rafId = window.requestAnimationFrame(syncFrame);
          }}

          function stopRAF() {{
            if (rafId) {{
              window.cancelAnimationFrame(rafId);
              rafId = null;
            }}
          }}

          function togglePlay() {{
            if (audio.paused) {{
              audio.play().catch(()=>{{}}); // ignore play promise rejections in restricted contexts
              playBtn.textContent = '⏸ Pause';
              playBtn.classList.add('pause');
              playBtn.setAttribute('aria-pressed', 'true');
              startRAF();
            }} else {{
              audio.pause();
              playBtn.textContent = '▶ Resume';
              playBtn.classList.remove('pause');
              playBtn.setAttribute('aria-pressed', 'false');
              stopRAF();
            }}
          }}

          audio.onended = function() {{
            playBtn.textContent = '▶ Replay';
            playBtn.classList.remove('pause');
            playBtn.setAttribute('aria-pressed', 'false');
            stopRAF();
            setTimeout(() => {{ audio.currentTime = 0; clearActive(); }}, 200);
          }};

          audio.onloadedmetadata = function() {{
            timings = computeTimingsIfMissing();

            // attach data attributes (and ignore items with null timings)
            if (timings && timings.wTimings) {{
              timings.wTimings.forEach((it, i) => {{
                const el = textArea.querySelector('.pp-word[data-index="' + i + '"]');
                if (el && it && it.start != null && it.end != null) {{
                  el.dataset.start = it.start; el.dataset.end = it.end;
                  el.title = el.textContent + ' [' + it.start + ' - ' + it.end + 's]';
                }}
              }});
            }}
            if (timings && timings.sTimings) {{
              timings.sTimings.forEach((it, i) => {{
                const el = syllArea.querySelector('.pp-word.pp-syll[data-index="' + i + '"]');
                if (el && it && it.start != null && it.end != null) {{
                  el.dataset.start = it.start; el.dataset.end = it.end;
                  el.title = el.textContent + ' [' + it.start + ' - ' + it.end + 's]';
                }}
              }});
            }}
            if (timings && timings.pTimings) {{
              timings.pTimings.forEach((it, i) => {{
                const el = phonArea.querySelector('.pp-word.pp-phon[data-index="' + i + '"]');
                if (el && it && it.start != null && it.end != null) {{
                  el.dataset.start = it.start; el.dataset.end = it.end;
                  el.title = el.textContent + ' [' + it.start + ' - ' + it.end + 's]';
                }}
              }});
            }}

            // enable controls if needed
            playBtn.disabled = false;
            speedSelect.disabled = false;
          }};

          // hookup global functions for Streamlit calls
          window.ppChangeSpeed = function() {{ audio.playbackRate = parseFloat(speedSelect.value); }};
          window.ppTogglePlay = function() {{ togglePlay(); }};

          // initial render
          renderSpans();
          renderWordPhonemeMap();

          // debug API
          window._pp_widget = {{ audio, getTimings: () => timings, words, phonemes }};

          // defensive: hide play until metadata loaded (prevents weird behavior)
          playBtn.disabled = true;
          speedSelect.disabled = true;
        }})();
      </script>
    </div>
    """

    components.html(html_code, height=height, scrolling=True)
