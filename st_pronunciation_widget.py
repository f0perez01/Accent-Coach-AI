# st_pronunciation_widget.py
import json
import html
import streamlit as st
import streamlit.components.v1 as components
from typing import List, Optional

def _safe_json(obj):
    return json.dumps(obj, ensure_ascii=False)

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

    Args:
      reference_text: texto normal (string).
      phoneme_text: transcripción IPA u otra (string).
      b64_audio: audio mp3 en Base64 (sin prefijo "data:..."), o con prefijo.
      word_timings: optional list of { "word": str, "start": float, "end": float }
      phoneme_timings: optional list of { "phoneme": str, "start": float, "end": float }
      syllable_timings: optional list of { "syllable": str, "start": float, "end": float }
      height: altura del iframe html.
      title: título opcional que aparece arriba.
    
    Priority order:
      1. word_timings (if provided)
      2. syllable_timings (if provided, auto-generated or user-supplied)
      3. phoneme_timings (if provided)
      4. Fallback: compute equal partitions at client-side
    """

    # Normalize audio src (allow user to pass either raw base64 or data URI)
    if b64_audio.strip().startswith("data:"):
        src = b64_audio.strip()
    else:
        src = f"data:audio/mp3;base64,{b64_audio.strip()}"

    # Split words and phonemes into arrays for markup
    # Keep HTML-escaped text to avoid injection
    words = [html.escape(w) for w in reference_text.strip().split()]
    phonemes = [html.escape(p) for p in phoneme_text.strip().split()]
    
    # Prepare syllables (escape and deduplicate from phoneme_text)
    syllables = []
    if syllable_timings:
        syllables = [html.escape(s["syllable"]) for s in syllable_timings]

    payload = {
        "words": words,
        "phonemes": phonemes,
        "syllables": syllables,
        "word_timings": word_timings or [],
        "phoneme_timings": phoneme_timings or [],
        "syllable_timings": syllable_timings or [],
        "audio_src": src,
        "title": title or ""
    }

    html_code = f"""
    <div id="st-pron-widget" style="font-family: Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; max-width:900px; margin: 6px auto;">
      <style>
        /* Card */
        .pp-card {{
          background: linear-gradient(180deg, #ffffff, #fbfdff);
          border: 1px solid #e6eef6;
          border-radius: 14px;
          padding: 18px;
          box-shadow: 0 6px 18px rgba(30, 62, 95, 0.06);
        }}
        .pp-header {{ display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:12px; }}
        .pp-title {{ font-weight:700; font-size:16px; color:#102a43; }}
        .pp-controls {{ display:flex; gap:8px; align-items:center; }}

        /* Speed select */
        .pp-select {{
          padding:6px 10px; border-radius:8px; border:1px solid #d9e6f2; background:#f7fbff; font-size:14px;
        }}

        /* Text areas */
        .pp-text, .pp-phonemes {{
          display:flex; flex-wrap:wrap; gap:6px; justify-content:center; padding:6px 4px;
        }}
        .pp-word, .pp-phon {{
          padding:6px 10px; border-radius:999px; font-size:16px; transition: background-color 120ms ease, color 120ms ease, transform 120ms ease;
          color:#184e6c; background:transparent;
        }}
        .pp-phon {{ font-family: 'Courier New', monospace; color:#9b2c2c; font-size:15px; }}

        .pp-syll {{ 
          padding:8px 12px; border-radius:8px; font-size:16px; font-family: 'Courier New', monospace;
          color:#1b4965; background:#e8f4f8; transition: background-color 120ms ease, color 120ms ease, transform 120ms ease;
        }}

        .pp-syll.active {{
          background: linear-gradient(90deg, #66bb6a, #52c41a);
          color:#fff; transform: scale(1.05);
          box-shadow: 0 6px 14px rgba(82,196,26,0.2);
        }}

        .pp-word.active {{
          background: linear-gradient(90deg,#ffd36b,#ffc16a);
          color:#2b2b2b; transform: translateY(-3px);
          box-shadow: 0 6px 14px rgba(255,178,74,0.14);
        }}

        .pp-phon.active {{
          background: linear-gradient(90deg,#ffb3b3,#ff8f8f);
          color:#2b2b2b; transform: translateY(-2px);
          box-shadow: 0 6px 14px rgba(255,102,102,0.12);
        }}

        /* Play button */
        .pp-button {{
          padding:10px 18px; border-radius:12px; border:none; cursor:pointer; font-weight:600; font-size:15px;
          background:#1b6cff; color:white; box-shadow: 0 8px 20px rgba(27,108,255,0.12);
        }}
        .pp-button.pause {{ background:#334155; }}

        /* Footer small notes */
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

        <!-- Text, syllables, and phonemes -->
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
          const payload = { _safe_json(payload) };
          const words = payload.words;
          const phonemes = payload.phonemes;
          const userWordTimings = payload.word_timings || [];
          const userPhTimings = payload.phoneme_timings || [];
          const audio = document.getElementById('pp-audio');
          const textArea = document.getElementById('pp-text-area');
          const phonArea = document.getElementById('pp-phon-area');
          const playBtn = document.getElementById('pp-play');
          const speedSelect = document.getElementById('pp-speed');

          // Render spans with data-index
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
            
            // Render syllables if available
            const syllArea = document.getElementById('pp-syll-area');
            if (phonemes.length > 0 && payload.syllables && payload.syllables.length > 0) {{
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

          // When audio metadata loads, if no timings provided, compute equal partitions
          function computeTimingsIfMissing() {{
            const duration = audio.duration || 0.0;
            
            // Priority 1: word timings
            let wTimings = userWordTimings && userWordTimings.length ? userWordTimings : null;
            
            // Priority 2: syllable timings (generate equal partitions if not available)
            let sTimings = userPhTimings && userPhTimings.length ? userPhTimings : null;
            if (payload.syllable_timings && payload.syllable_timings.length) {{
              sTimings = payload.syllable_timings;
            }}
            
            // Priority 3: phoneme timings
            let pTimings = userPhTimings && userPhTimings.length ? userPhTimings : null;

            // Fallback: compute equal partitions
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

          // Keep active indices for fast lookup
          function findActiveIndices(t, timings) {{
            // timings: array of objects with start/end
            // Binary search could be used but arrays are small, linear OK
            const active = [];
            for (let i = 0; i < timings.length; i++) {{
              const it = timings[i];
              if (t >= it.start && t < it.end) active.push(i);
            }}
            return active;
          }}

          function clearActive() {{
            document.querySelectorAll('.pp-word.active, .pp-phon.active').forEach(el => {{
              el.classList.remove('active');
            }});
          }}

          let timings = null;
          let rafId = null;

          function syncFrame() {{
            const t = audio.currentTime;
            // words
            const activeWords = findActiveIndices(t, timings.wTimings);
            const activeSylls = timings.sTimings ? findActiveIndices(t, timings.sTimings) : [];
            const activePh = findActiveIndices(t, timings.pTimings);

            // clear previous
            document.querySelectorAll('.pp-word.active').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.pp-syll.active').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.pp-phon.active').forEach(el => el.classList.remove('active'));

            // set current
            activeWords.forEach(i => {{
              const el = textArea.querySelector('.pp-word[data-index=\"' + i + '\"]');
              if (el) el.classList.add('active');
            }});
            activeSylls.forEach(i => {{
              const el = document.getElementById('pp-syll-area').querySelector('.pp-syll[data-index=\"' + i + '\"]');
              if (el) el.classList.add('active');
            }});
            activePh.forEach(i => {{
              const el = phonArea.querySelector('.pp-phon[data-index=\"' + i + '\"]');
              if (el) el.classList.add('active');
            }});

            rafId = window.requestAnimationFrame(syncFrame);
          }}

          // Play/pause control
          function togglePlay() {{
            if (audio.paused) {{
              audio.play();
              playBtn.textContent = '⏸ Pause';
              playBtn.classList.add('pause');
              // start RAF
              if (rafId) window.cancelAnimationFrame(rafId);
              rafId = window.requestAnimationFrame(syncFrame);
            }} else {{
              audio.pause();
              playBtn.textContent = '▶ Resume';
              playBtn.classList.remove('pause');
              if (rafId) window.cancelAnimationFrame(rafId);
            }}
          }}

          // Pause behavior: keep current highlight (we don't reset)
          // On ended, set to Replay state and reset highlights
          audio.onended = function() {{
            playBtn.textContent = '▶ Replay';
            playBtn.classList.remove('pause');
            if (rafId) window.cancelAnimationFrame(rafId);
            // set time to end to highlight final token briefly, then reset after 400ms
            setTimeout(() => {{ audio.currentTime = 0; clearActive(); }}, 450);
          }};

          audio.onloadedmetadata = function() {{
            timings = computeTimingsIfMissing();
            // update any data attributes: embed start/end in spans (optional)
            // (Not strictly necessary for runtime, but useful for debugging)
            timings.wTimings.forEach((it, i) => {{
              const el = textArea.querySelector('.pp-word[data-index=\"' + i + '\"]');
              if (el) {{
                el.dataset.start = it.start; el.dataset.end = it.end;
                el.title = el.textContent + ' [' + it.start + ' - ' + it.end + 's]';
              }}
            }});
            if (timings.sTimings) {{
              timings.sTimings.forEach((it, i) => {{
                const el = document.getElementById('pp-syll-area').querySelector('.pp-syll[data-index=\"' + i + '\"]');
                if (el) {{
                  el.dataset.start = it.start; el.dataset.end = it.end;
                  el.title = el.textContent + ' [' + it.start + ' - ' + it.end + 's]';
                }}
              }});
            }}
            timings.pTimings.forEach((it, i) => {{
              const el = phonArea.querySelector('.pp-phon[data-index=\"' + i + '\"]');
              if (el) {{
                el.dataset.start = it.start; el.dataset.end = it.end;
                el.title = el.textContent + ' [' + it.start + ' - ' + it.end + 's]';
              }}
            }});
          }};

          // Speed control
          window.ppChangeSpeed = function() {{
            audio.playbackRate = parseFloat(speedSelect.value);
          }};

          window.ppTogglePlay = function() {{
            togglePlay();
          }};

          // Initialize UI
          renderSpans();
          // auto compute timings when audio metadata arrives (audio.onloadedmetadata above)

          // expose minor debug API (optional)
          window._pp_widget = {{
            audio, getTimings: () => timings, words, phonemes
          }};
        }})();
      </script>
    </div>
    """

    # Render the HTML in Streamlit
    components.html(html_code, height=height, scrolling=True)
