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
        "audio_src": src,
        "title": title or "",
    }

    # HTML + JS UI (fixed timing-priority and using syllables correctly)
    html_code = f"""
    <div id="st-pron-widget" style="font-family: Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; max-width:900px; margin: 6px auto;">
      <style>
        .pp-card {{ background: linear-gradient(180deg, #ffffff, #fbfdff); border: 1px solid #e6eef6; border-radius: 14px; padding: 18px; box-shadow: 0 6px 18px rgba(30,62,95,0.06); }}
        .pp-header {{ display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:12px; }}
        .pp-title {{ font-weight:700; font-size:16px; color:#102a43; }}
        .pp-controls {{ display:flex; gap:8px; align-items:center; }}
        .pp-select {{ padding:6px 10px; border-radius:8px; border:1px solid #d9e6f2; background:#f7fbff; font-size:14px; }}
        .pp-text, .pp-phonemes {{ display:flex; flex-wrap:wrap; gap:6px; justify-content:center; padding:6px 4px; }}
        .pp-word, .pp-phon {{ padding:6px 10px; border-radius:999px; font-size:16px; transition: background-color 120ms ease, color 120ms ease, transform 120ms ease; color:#184e6c; background:transparent; }}
        .pp-phon {{ font-family: 'Courier New', monospace; color:#9b2c2c; font-size:15px; }}
        .pp-syll {{ padding:8px 12px; border-radius:8px; font-size:16px; font-family: 'Courier New', monospace; color:#1b4965; background:#e8f4f8; transition: background-color 120ms ease, color 120ms ease, transform 120ms ease; }}
        .pp-syll.active {{ background: linear-gradient(90deg, #66bb6a, #52c41a); color:#fff; transform: scale(1.05); box-shadow: 0 6px 14px rgba(82,196,26,0.2); }}
        .pp-word.active {{ background: linear-gradient(90deg,#ffd36b,#ffc16a); color:#2b2b2b; transform: translateY(-3px); box-shadow: 0 6px 14px rgba(255,178,74,0.14); }}
        .pp-phon.active {{ background: linear-gradient(90deg,#ffb3b3,#ff8f8f); color:#2b2b2b; transform: translateY(-2px); box-shadow: 0 6px 14px rgba(255,102,102,0.12); }}
        .pp-button {{ padding:10px 18px; border-radius:12px; border:none; cursor:pointer; font-weight:600; font-size:15px; background:#1b6cff; color:white; box-shadow: 0 8px 20px rgba(27,108,255,0.12); }}
        .pp-button.pause {{ background:#334155; }}
        .pp-meta {{ margin-top:10px; font-size:12px; color:#627d98; text-align:center; }}
      </style>

      <div class="pp-card">
        <div class="pp-header">
          <div class="pp-title">Pronunciation Trainer {html.escape(payload['title'])}</div>
          <div class="pp-controls">
            <select id="pp-speed" class="pp-select" onchange="ppChangeSpeed()">
              <option value="0.5">0.5x</option>
              <option value="0.75">0.75x</option>
              <option value="1.0" selected>1.0x</option>
              <option value="1.25">1.25x</option>
              <option value="1.5">1.5x</option>
            </select>
            <button id="pp-play" class="pp-button" onclick="ppTogglePlay()">▶ Play</button>
          </div>
        </div>

        <div id="pp-text-area" class="pp-text" aria-hidden="false"></div>
        <div id="pp-syll-area" class="pp-syllables" aria-hidden="false" style="margin-top:6px; display:none;"></div>
        <div id="pp-phon-area" class="pp-phonemes" aria-hidden="false" style="margin-top:6px;"></div>

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

          // Render spans
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

            // syllables
            if (payload.syllables && payload.syllables.length) {{
              syllArea.style.display = 'flex';
              syllArea.innerHTML = '';
              payload.syllables.forEach((s, i) => {{
                const span = document.createElement('span');
                span.className = 'pp-syll';
                span.dataset.index = i;
                span.dataset.syllable = s;
                span.textContent = s;
                syllArea.appendChild(span);
              }});
            }} else {{
              syllArea.style.display = 'none';
            }}

            phonArea.innerHTML = '';
            phonemes.forEach((p, i) => {{
              const span = document.createElement('span');
              span.className = 'pp-phon';
              span.dataset.index = i;
              span.dataset.phoneme = p;
              span.textContent = p;
              phonArea.appendChild(span);
            }});
          }}

          // Compute timings with correct priority
          function computeTimingsIfMissing() {{
            const duration = audio.duration || 0.0;

            // Priority 1: word timings
            let wTimings = (payload.word_timings && payload.word_timings.length) ? payload.word_timings : null;

            // Priority 2: syllable timings
            let sTimings = (payload.syllable_timings && payload.syllable_timings.length) ? payload.syllable_timings : null;

            // Priority 3: phoneme timings
            let pTimings = (payload.phoneme_timings && payload.phoneme_timings.length) ? payload.phoneme_timings : null;

            // Fallbacks
            if (!wTimings) {{
              const n = Math.max(words.length, 1);
              const seg = duration / n;
              wTimings = words.map((w, i) => ({{ word: w, start: +(i * seg).toFixed(3), end: +(((i + 1) * seg)).toFixed(3) }}));
            }}

            if (!sTimings && payload.syllables && payload.syllables.length) {{
              // If there are syllable tokens but no timings, partition audio across syllables
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
            for (let i = 0; i < timings.length; i++) {{
              const it = timings[i];
              if (it.start == null || it.end == null) continue;
              if (t >= it.start && t < it.end) active.push(i);
            }}
            return active;
          }}

          function clearActive() {{
            document.querySelectorAll('.pp-word.active, .pp-syll.active, .pp-phon.active').forEach(el => el.classList.remove('active'));
          }}

          let timings = null;
          let rafId = null;

          function syncFrame() {{
            const t = audio.currentTime;
            const activeWords = timings && timings.wTimings ? findActiveIndices(t, timings.wTimings) : [];
            const activeSylls = timings && timings.sTimings ? findActiveIndices(t, timings.sTimings) : [];
            const activePh = timings && timings.pTimings ? findActiveIndices(t, timings.pTimings) : [];

            clearActive();

            activeWords.forEach(i => {{
              const el = textArea.querySelector('.pp-word[data-index="' + i + '"]');
              if (el) el.classList.add('active');
            }});
            activeSylls.forEach(i => {{
              const el = syllArea.querySelector('.pp-syll[data-index="' + i + '"]');
              if (el) el.classList.add('active');
            }});
            activePh.forEach(i => {{
              const el = phonArea.querySelector('.pp-phon[data-index="' + i + '"]');
              if (el) el.classList.add('active');
            }});

            rafId = window.requestAnimationFrame(syncFrame);
          }}

          function togglePlay() {{
            if (audio.paused) {{
              audio.play();
              playBtn.textContent = '⏸ Pause';
              playBtn.classList.add('pause');
              if (rafId) window.cancelAnimationFrame(rafId);
              rafId = window.requestAnimationFrame(syncFrame);
            }} else {{
              audio.pause();
              playBtn.textContent = '▶ Resume';
              playBtn.classList.remove('pause');
              if (rafId) window.cancelAnimationFrame(rafId);
            }}
          }}

          audio.onended = function() {{
            playBtn.textContent = '▶ Replay';
            playBtn.classList.remove('pause');
            if (rafId) window.cancelAnimationFrame(rafId);
            setTimeout(() => {{ audio.currentTime = 0; clearActive(); }}, 450);
          }};

          audio.onloadedmetadata = function() {{
            timings = computeTimingsIfMissing();

            // attach data attributes
            timings.wTimings.forEach((it, i) => {{
              const el = textArea.querySelector('.pp-word[data-index="' + i + '"]');
              if (el) {{ el.dataset.start = it.start; el.dataset.end = it.end; el.title = el.textContent + ' [' + it.start + ' - ' + it.end + 's]'; }}
            }});
            if (timings.sTimings) {{
              timings.sTimings.forEach((it, i) => {{
                const el = syllArea.querySelector('.pp-syll[data-index="' + i + '"]');
                if (el) {{ el.dataset.start = it.start; el.dataset.end = it.end; el.title = el.textContent + ' [' + it.start + ' - ' + it.end + 's]'; }}
              }});
            }}
            timings.pTimings.forEach((it, i) => {{
              const el = phonArea.querySelector('.pp-phon[data-index="' + i + '"]');
              if (el) {{ el.dataset.start = it.start; el.dataset.end = it.end; el.title = el.textContent + ' [' + it.start + ' - ' + it.end + 's]'; }}
            }});
          }};

          window.ppChangeSpeed = function() {{ audio.playbackRate = parseFloat(speedSelect.value); }};
          window.ppTogglePlay = function() {{ togglePlay(); }};

          renderSpans();

          // debug API
          window._pp_widget = {{ audio, getTimings: () => timings, words, phonemes }};
        }})();
      </script>
    </div>
    """

    components.html(html_code, height=height, scrolling=True)
