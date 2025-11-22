import streamlit as st
import os
import io
import json
import re
from gtts import gTTS

# --- Configuración Mobile-First ---
st.set_page_config(
    page_title="Pocket English Coach - Strategic MVP",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS Pulido (Minimalismo + Badges) ---
st.markdown("""
    <style>
    .stTextArea textarea { font-size: 16px !important; }
    .stButton button { width: 100%; border-radius: 20px; font-weight: bold; }
    
    /* Estilo IPA / Diccionario */
    .ipa-text {
        font-family: 'Lucida Sans Unicode', 'Arial Unicode MS', sans-serif;
        color: #555;
        font-size: 0.85rem;
        background-color: #f0f2f6;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 6px;
    }
    
    /* Tarjeta de vocabulario (Expansion) */
    .vocab-card {
        border-left: 4px solid #4CAF50; /* Verde para crecimiento */
        padding-left: 12px;
        margin-bottom: 16px;
        background-color: #fafafa;
        padding-top: 8px;
        padding-bottom: 8px;
        border-radius: 0 8px 8px 0;
    }
    
    /* Métricas Header */
    .metric-container {
        display: flex;
        justify-content: space-around;
        margin-bottom: 20px;
        background: #e8f5e9;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #c8e6c9;
    }
    .metric-box { text-align: center; }
    .metric-val { font-size: 1.2rem; font-weight: bold; color: #2e7d32; }
    .metric-label { font-size: 0.8rem; color: #666; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- Utilities ---

def compute_variety_score(text: str) -> int:
    """Simple heuristic for lexical variety.
    Uses a normalized Type-Token Ratio (TTR) and maps to 1-10.
    """
    words = re.findall(r"\w+", text.lower())
    if not words:
        return 0
    total = len(words)
    unique = len(set(words))
    ttr = unique / total  # between 0 and 1
    # map to 1-10 (avoid extremes)
    score = int(round(1 + ttr * 9))
    return max(1, min(score, 10))


def parse_json_safe(raw: str) -> dict:
    """Try to extract a JSON object from raw text. Returns dict or empty dict on failure."""
    # Quick attempt: find first { and last }
    try:
        start = raw.index('{')
        end = raw.rindex('}')
        candidate = raw[start:end+1]
        return json.loads(candidate)
    except Exception:
        # fallback: try to directly load if already json
        try:
            return json.loads(raw)
        except Exception:
            return {}


# --- Lógica Backend Estratégica ---

def get_full_analysis(text: str, api_key: str) -> dict:
    """
    Analiza el texto buscando CORRECCIÓN (pasado) y EXPANSIÓN (futuro).
    Mejoras aplicadas basadas en el prompt pulido: salida JSON-only, definición CEFR y variety_score.
    """
    # Defaults
    default_result = {
        "corrected": text,
        "improvements": [],
        "questions": [],
        "expansion_words": [],
        "metrics": {"cefr_level": "?", "variety_score": compute_variety_score(text)}
    }

    if not api_key:
        # Keep UI stable: return defaults with a visible warning in UI layer
        return default_result

    try:
        from groq import Groq
        client = Groq(api_key=api_key)

                # --- PROMPT MEJORADO ---
        prompt = f"""Analyze this English student text: "{text}"
            You are a strict but helpful Lexical Coach whose goal is to increase the student's vocabulary sophistication.
                
                REQUIREMENTS:
                1) Output ONLY a single valid JSON object (no extra text) with these exact keys: 
                - "metrics": {{ "cefr_level": "A1|A2|B1|B2|C1|C2", "variety_score": integer 1-10 }}.
                - "corrected": corrected version of the text (natural, native-like English).
                - "improvements": array (up to 3) short strings describing grammar/usage errors corrected.
                - "expansion_words": array of EXACTLY 3 objects: {{ "word": "<word>", "ipa": "/<IPA>/", "meaning_context": "<one short example sentence>", "replaces_simple_word": "<original simple word>" }}.
                - "questions": array of EXACTLY 2 follow-up questions in English.
                
                2) CEFR rule: estimate level from vocabulary range, grammar complexity and sentence structure; choose the nearest single level.
                3) Variety score: approximate lexical diversity on a 1-10 scale (1=very low, 10=excellent).
                4) Expansion words must NOT appear in the original text and must bridge from B2->C1. Provide IPA between slashes.
                5) All strings must be in English. Do not output extra keys or commentary. The JSON must be parseable.
                """

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert Lexical Data Scientist. OUTPUT ONLY A JSON OBJECT. No explanation, no extra characters."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        # Groq SDK may already return structured JSON. Try robust parsing.
        raw = chat_completion.choices[0].message.content
        data = parse_json_safe(raw)

        # Validation & safe defaults
        if not data:
            return default_result

        # Ensure keys exist and are sane
        metrics = data.get('metrics', {})
        cefr = metrics.get('cefr_level', '?')
        variety = metrics.get('variety_score', compute_variety_score(text))
        try:
            variety = int(variety)
        except Exception:
            variety = compute_variety_score(text)

        expansion = data.get('expansion_words', [])
        # Ensure each expansion item contains required fields and IPA enclosed in slashes
        clean_expansion = []
        for item in expansion:
            if not isinstance(item, dict):
                continue
            word = item.get('word', '').strip()
            ipa = item.get('ipa', '').strip()
            meaning_context = item.get('meaning_context', '').strip()
            replaces = item.get('replaces_simple_word', '').strip()
            if word and ipa and meaning_context and replaces:
                # Normalize IPA to be between slashes
                if not (ipa.startswith('/') and ipa.endswith('/')):
                    ipa = f"/{ipa.strip('/')}\/" if ipa else ipa
                clean_expansion.append({
                    'word': word,
                    'ipa': ipa,
                    'meaning_context': meaning_context,
                    'replaces_simple_word': replaces
                })
        # If model returned fewer than 3 expansions, keep what we have (UI handles empty cases)

        return {
            "corrected": data.get('corrected', text),
            "improvements": data.get('improvements', []),
            "questions": data.get('questions', []),
            "expansion_words": clean_expansion,
            "metrics": {"cefr_level": cefr, "variety_score": variety}
        }

    except Exception as e:
        return {
            "corrected": text,
            "improvements": [f"Error: {str(e)}"],
            "questions": [],
            "expansion_words": [],
            "metrics": {"cefr_level": "Error", "variety_score": compute_variety_score(text)}
        }


def text_to_speech(text: str):
    if not text:
        return None
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return mp3_fp
    except Exception:
        return None


# --- UI Principal ---

def main():
    st.title("🚀 Pocket English Coach")
    st.caption("Strategic Vocabulary Expansion")

    user_text = st.text_area("Write your story:", height=100, placeholder="Yesterday I go to work and it was very hard...")

    if st.button("✨ Analyze & Expand", type="primary"):
        if not user_text.strip():
            st.toast("Please write something!")
        else:
            with st.spinner("Measuring lexical density..."):
                api_key = st.secrets.get('GROQ_API_KEY', os.environ.get('GROQ_API_KEY'))
                result = get_full_analysis(user_text, api_key)
                st.session_state['result'] = result
                st.session_state['original'] = user_text

    if 'result' in st.session_state:
        res = st.session_state['result']
        metrics = res.get('metrics', {})

        # --- Dashboard Estratégico (Arriba) ---
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-box">
                <div class="metric-val">{metrics.get('cefr_level', 'N/A')}</div>
                <div class="metric-label">Level Est.</div>
            </div>
            <div class="metric-box">
                <div class="metric-val">{metrics.get('variety_score', 0)}/10</div>
                <div class="metric-label">Lexical Score</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- TABS ---
        t1, t2, t3, t4 = st.tabs(["✅ Fix", "💡 Why", "🗣️ Chat", "🚀 Grow"])

        with t1:
            st.success(res.get('corrected', ''))
            audio = text_to_speech(res.get('corrected', ''))
            if audio:
                st.audio(audio, format="audio/mp3")
            st.caption("Corrected version")

        with t2:
            st.info("Grammar Fixes")
            improvements = res.get('improvements', [])
            if improvements:
                for imp in improvements:
                    st.markdown(f"- {imp}")
            else:
                st.write("No significant grammar corrections suggested.")
            st.markdown("---")
            st.caption("Original:")
            st.text(st.session_state.get('original', ''))

        with t3:
            st.warning("Deepen the Topic")
            if res.get('questions'):
                for q in res.get('questions'):
                    st.markdown(f"**❓ {q}**")
            else:
                st.write("No follow-up questions generated.")

        with t4:
            st.subheader("Level Up Words")
            st.caption("Words you DIDN'T use, but should have:")

            expansion = res.get('expansion_words', [])
            if expansion:
                for item in expansion:
                    html_content = f"""
                    <div class="vocab-card">
                        <div style="display:flex; justify-content:space-between;">
                            <strong>{item.get('word', '')}</strong>
                            <span class="ipa-text">{item.get('ipa', '')}</span>
                        </div>
                        <div style="font-size:0.85rem; color:#666; margin-top:4px;">
                            Instead of: <em>"{item.get('replaces_simple_word', '...')}"</em>
                        </div>
                        <div style="font-size:0.9rem; margin-top:4px;">
                            {item.get('meaning_context', '')}
                        </div>
                    </div>
                    """
                    st.markdown(html_content, unsafe_allow_html=True)

                    # Audio mini
                    col_a, col_b = st.columns([1, 5])
                    with col_a:
                        word_audio = text_to_speech(item.get('word', ''))
                        if word_audio:
                            st.audio(word_audio, format="audio/mp3")
            else:
                st.write("Good variety! No immediate upgrades suggested.")

if __name__ == "__main__":
    main()
