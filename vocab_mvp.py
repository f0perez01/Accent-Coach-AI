import streamlit as st
import json
import os
from typing import List, Dict, Optional
import sys
from lexical.metrics import compute_metrics_for_text, load_basic_wordlists
from lexical.suggester import SuggestionEngine
from db.models import init_db, add_text_for_user, get_user_stats

try:
    from groq import Groq
    _HAS_GROQ = True
except Exception:
    _HAS_GROQ = False


def get_groq_suggestions_for_words(problem_words: List[str], groq_api_key: str) -> Optional[Dict[str, str]]:
    """Ask Groq LLM to propose replacement suggestions for a list of problem words.

    Returns a mapping original_word -> suggestion, or None on failure.
    """
    if not _HAS_GROQ:
        st.warning("Groq client not available (package missing)")
        return None

    if not groq_api_key:
        st.warning("GROQ API key not provided")
        return None

    try:
        client = Groq(api_key=groq_api_key)

        system_message = (
            "You are a helpful English writing assistant. "
            "Given a short list of words that a student used, propose a single-word or short-phrase replacement that is more native-like, precise, or varied. "
            "Return a JSON object mapping each original word to a suggested replacement. "
            "If no good replacement exists, return the original word as the suggestion."
        )

        user_prompt = (
            f"Words: {problem_words}\n\n"
            "Respond ONLY with a JSON object (no extra text). Wrap the JSON between <JSON> and </JSON> markers. "
            "Example: <JSON>{\"word\": \"suggestion\"}</JSON>"
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt},
            ],
            model="llama-3.1-8b-instant",
            temperature=0.0,
        )

        raw = chat_completion.choices[0].message.content
        try:
            st.session_state['groq_raw_suggestions'] = raw
        except Exception:
            pass

        # Extract JSON between markers if provided
        start = raw.find('<JSON>')
        end = raw.find('</JSON>')
        if start != -1 and end != -1 and end > start:
            json_blob = raw[start + len('<JSON>'):end].strip()
        else:
            json_blob = raw

        try:
            suggestions = json.loads(json_blob)
            return {str(k): str(v) for k, v in suggestions.items()}
        except Exception:
            # Fallback: simple line parsing like "word: suggestion"
            out = {}
            for line in raw.splitlines():
                if ':' in line:
                    k, v = line.split(':', 1)
                    out[k.strip().strip('"')] = v.strip().strip('"')
            return out if out else None

    except Exception as e:
        st.error(f"Groq suggestions failed: {e}")
        return None


def get_groq_rewrite(original_text: str, suggestions: Dict[str, str], groq_api_key: str) -> Optional[str]:
    """Ask Groq LLM to rewrite the original text incorporating the provided suggestions.

    `suggestions` should be a mapping from original_word -> replacement_word.
    """
    if not _HAS_GROQ or not groq_api_key:
        return None

    try:
        client = Groq(api_key=groq_api_key)

        system_message = (
            "You are an expert editor. Rewrite the following student text applying the provided replacement suggestions. "
            "Keep the meaning and level (tone) similar, but incorporate the suggested words/phrases naturally. "
            "Return only the rewritten text."
        )

        sug_lines = []
        for k, v in (suggestions or {}).items():
            sug_lines.append(f"Replace '{k}' -> '{v}'")

        # Ask for rewritten text only, and include the suggestions. Use markers for easy extraction.
        user_prompt = (
            f"Original text:\n{original_text}\n\n"
            f"Suggestions:\n{chr(10).join(sug_lines)}\n\n"
            "Respond ONLY with the rewritten text. Wrap the rewritten text between <REWRITE> and </REWRITE> markers."
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt},
            ],
            model="llama-3.1-8b-instant",
            temperature=0.0,
        )

        rewritten = chat_completion.choices[0].message.content
        try:
            st.session_state['groq_raw_rewrite'] = rewritten
        except Exception:
            pass

        # Extract between markers if present
        s = rewritten.find('<REWRITE>')
        e = rewritten.find('</REWRITE>')
        if s != -1 and e != -1 and e > s:
            return rewritten[s + len('<REWRITE>'):e].strip()
        return rewritten.strip()

    except Exception as e:
        st.error(f"Groq rewrite failed: {e}")
        return None


def main():
    st.title("Vocabulary Coach — MVP")
    st.markdown("Upload or paste student text to analyze lexical variety and get contextual suggestions.")

    # Environment debug info to help diagnose missing package issues
    with st.sidebar.expander("🧪 Environment Debug", expanded=False):
        try:
            st.write(f"Python executable: `{sys.executable}`")
            st.write(f"Python version: `{sys.version.splitlines()[0]}`")
        except Exception:
            pass

        try:
            if _HAS_GROQ:
                import groq as _groq_mod
                groq_path = getattr(_groq_mod, '__file__', 'unknown')
                groq_ver = getattr(_groq_mod, '__version__', 'unknown')
                st.success(f"Groq client available: {groq_ver}")
                st.write(f"Groq module path: `{groq_path}`")
            else:
                st.warning("Groq client not available in this Python environment.")
        except Exception as e:
            st.error(f"Error inspecting groq module: {e}")

    init_db()
    user = st.text_input("Student ID", value="student_1")

    st.header("Input")
    text = st.text_area("Paste student text here", height=200)
    uploaded = st.file_uploader("Or upload a .txt file", type=["txt"])
    if uploaded and not text:
        text = uploaded.read().decode("utf-8")

    if st.button("Analyze") and text.strip():
        # Persist analysis results in session state so UI can survive reruns
        add_text_for_user(user, text)
        wordlists = load_basic_wordlists()
        metrics = compute_metrics_for_text(text, wordlists=wordlists)

        st.session_state['analysis_done'] = True
        st.session_state['analyzed_text'] = text
        st.session_state['metrics'] = metrics

        sugg_engine = SuggestionEngine()
        st.session_state['suggestions'] = sugg_engine.suggest(text, top_k=15)
        # reset groq-related session state for fresh flow
        st.session_state['groq_suggestions'] = None
        st.session_state['groq_rewrite'] = None

    # Render results if analysis has been performed (persisted in session_state)
    if st.session_state.get('analysis_done'):
        metrics = st.session_state.get('metrics', {})

        st.sidebar.header("Metrics")
        for k, v in metrics.items():
            st.sidebar.write(f"**{k}**: {v}")

        st.header("Suggestions")
        suggestions = st.session_state.get('suggestions', []) or []

        for idx, s in enumerate(suggestions, 1):
            st.markdown(f"**{idx}. {s['word']}** — {s.get('reason','')}")
            st.write(s.get('example',''))
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Accept {s['word']}", key=f"accept-{idx}"):
                    st.success(f"Accepted {s['word']}")
            with col2:
                if st.button(f"Reject {s['word']}", key=f"reject-{idx}"):
                    st.error(f"Rejected {s['word']}")

        # --- Groq integration: suggestions + rewrite ---
        st.markdown("---")
        st.markdown("#### ✍️ Rewrite Student Text with Groq Suggestions")

        # problematic words fallback: use top suggested words (those engine returned)
        suggested_words = [s['word'] for s in suggestions]

        # Decide whether Groq is available in this environment
        groq_api_key = None
        try:
            groq_api_key = st.secrets.get('GROQ_API_KEY', os.environ.get('GROQ_API_KEY'))
        except Exception:
            groq_api_key = os.environ.get('GROQ_API_KEY')

        col1, col2 = st.columns([1, 1])

        if not _HAS_GROQ:
            # Groq client not installed — show actionable instructions and local fallback button
            with col1:
                st.warning("Groq client not available (package missing). Install the Python client in your environment to enable LLM suggestions.")
                st.code('pip install groq', language='bash')
                st.caption("If you're running Streamlit from a different virtualenv, make sure to install the package there.")

            with col2:
                if st.button("🔧 Apply Local Rewrite Now"):
                    # Ensure suggestions exist (use existing or basic heuristic fallback)
                    suggestions_map = st.session_state.get('groq_suggestions')
                    if not suggestions_map:
                        fallback = {}
                        for w in suggested_words[:25]:
                            lw = w.lower()
                            if lw == 'according':
                                fallback[w] = 'according to'
                            elif lw in ('technics', 'technic'):
                                fallback[w] = 'techniques'
                            elif lw == 'helps':
                                fallback[w] = 'help'
                            elif lw == 'theirs':
                                fallback[w] = 'their'
                            elif lw in ('skils', 'skils.'):
                                fallback[w] = 'skills'
                            else:
                                fallback[w] = w
                        st.session_state['groq_suggestions'] = fallback
                    # Apply local rewrite immediately
                    txt = st.session_state.get('analyzed_text', '')
                    s = st.session_state.get('groq_suggestions', {}) or {}
                    for orig, rep in s.items():
                        txt = txt.replace(orig, rep)
                        txt = txt.replace(orig.capitalize(), rep.capitalize())
                    st.session_state['groq_rewrite'] = txt
                    st.success('Local rewrite applied and saved to session.')

        else:
            # Groq client is installed — show Groq buttons
            with col1:
                if st.button("🔍 Get Groq Suggestions"):
                    gr_sugs = get_groq_suggestions_for_words(suggested_words[:25], groq_api_key)
                    if gr_sugs:
                        st.session_state['groq_suggestions'] = gr_sugs
                        st.success("Groq suggestions fetched and saved to session.")
                    else:
                        st.warning("No suggestions returned from Groq. Using local fallback suggestions.")
                        # Local fallback
                        fallback = {}
                        for w in suggested_words[:25]:
                            lw = w.lower()
                            if lw == 'according':
                                fallback[w] = 'according to'
                            elif lw in ('technics', 'technic'):
                                fallback[w] = 'techniques'
                            elif lw == 'helps':
                                fallback[w] = 'help'
                            elif lw == 'theirs':
                                fallback[w] = 'their'
                            elif lw in ('skils', 'skils.'):
                                fallback[w] = 'skills'
                            else:
                                fallback[w] = w
                        st.session_state['groq_suggestions'] = fallback
                        st.info("Fallback suggestions ready.")

            with col2:
                if st.button("✍️ Rewrite Text Using Groq"):
                    existing_sugs = st.session_state.get('groq_suggestions', {})
                    rewritten = get_groq_rewrite(st.session_state.get('analyzed_text', ''), existing_sugs or {}, groq_api_key)

                    # Accept parsed rewrite if present
                    if rewritten and rewritten.strip():
                        st.session_state['groq_rewrite'] = rewritten.strip()
                        st.success("Rewritten text saved to session.")
                    else:
                        # If parsed rewrite is empty, check raw response and accept it if non-empty
                        raw_rewrite = st.session_state.get('groq_raw_rewrite', '')
                        if raw_rewrite and raw_rewrite.strip():
                            st.session_state['groq_rewrite'] = raw_rewrite.strip()
                            st.success("Rewritten text (raw) saved to session.")
                        else:
                            st.warning("Groq did not return a rewritten text. Using local fallback rewrite.")
                            # Simple local rewrite fallback using replacements
                            txt = st.session_state.get('analyzed_text', '')
                            s = existing_sugs or {}
                            for orig, rep in s.items():
                                txt = txt.replace(orig, rep)
                                txt = txt.replace(orig.capitalize(), rep.capitalize())
                            st.session_state['groq_rewrite'] = txt
                            st.info("Local fallback rewrite applied.")

        if st.session_state.get('groq_suggestions'):
            st.markdown("**Groq Suggestions**")
            for k, v in st.session_state['groq_suggestions'].items():
                st.write(f"- **{k}** → {v}")

        # Debug: show raw Groq suggestions if available
        if st.session_state.get('groq_raw_suggestions'):
            with st.expander("🔎 Raw Groq suggestions (debug)", expanded=False):
                try:
                    st.code(st.session_state.get('groq_raw_suggestions', ''), language='')
                except Exception:
                    st.write(st.session_state.get('groq_raw_suggestions', ''))

        if st.session_state.get('groq_rewrite'):
            st.markdown("**Rewritten Text**")
            new_text = st.text_area("Rewritten text (Groq)", value=st.session_state['groq_rewrite'], height=180)
            if st.button("💾 Save Rewritten Text as New Entry"):
                add_text_for_user(user, new_text)
                st.success("Rewritten text saved to the student's history.")

        # Debug: show raw Groq rewrite if available
        if st.session_state.get('groq_raw_rewrite'):
            with st.expander("🔎 Raw Groq rewrite (debug)", expanded=False):
                try:
                    st.code(st.session_state.get('groq_raw_rewrite', ''), language='')
                except Exception:
                    st.write(st.session_state.get('groq_raw_rewrite', ''))

        st.header("Student History")
        stats = get_user_stats(user)
        st.write(stats)


if __name__ == "__main__":
    main()
