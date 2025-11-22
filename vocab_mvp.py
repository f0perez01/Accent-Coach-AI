import streamlit as st
import os
import io
import json
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

# --- Lógica Backend Estratégica ---

def get_full_analysis(text: str, api_key: str) -> dict:
    """
    Analiza el texto buscando CORRECCIÓN (Pasado) y EXPANSIÓN (Futuro).
    """
    if not api_key:
        return {"corrected": text, "explanation": "⚠️ No API Key", "questions": [], "expansion": [], "metrics": {}}

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        
        # --- EL PROMPT MAESTRO (Ajustado a la Visión) ---
        prompt = (
            f"Analyze this English student text: '{text}'.\n"
            f"Act as a strict but helpful Lexical Coach. Goal: Increase vocabulary sophistication.\n"
            f"Return a valid JSON object with exactly these keys:\n"
            f"1. 'metrics': Object with 'cefr_level' (e.g. A2, B1, C2) and 'variety_score' (1-10 integer based on lexical diversity).\n"
            f"2. 'corrected': The corrected version of the text (natural & native-like).\n"
            f"3. 'improvements': List of 3 short strings explaining grammar errors corrected.\n"
            f"4. 'expansion_words': List of 3 'Power Words' that the student DID NOT use but fits the context perfectly to replace simple words. "
            f"   (Format: object with 'word', 'ipa', 'meaning_context', 'replaces_simple_word').\n"
            f"5. 'questions': List of 2 follow-up questions to deepen the topic.\n"
            f"Focus: 'expansion_words' must be the bridge to a higher level (B2->C1)."
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert Lexical Data Scientist. Output only JSON."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        data = json.loads(chat_completion.choices[0].message.content)

        # Validación y Fallbacks
        return {
            "corrected": data.get("corrected", text),
            "explanation": "\n\n".join([f"• {i}" for i in data.get("improvements", [])]),
            "questions": data.get("questions", []),
            "expansion": data.get("expansion_words", []), # Nueva clave estratégica
            "metrics": data.get("metrics", {"cefr_level": "?", "variety_score": 0})
        }

    except Exception as e:
        return {
            "corrected": text, 
            "explanation": f"Error: {str(e)}", 
            "questions": [], 
            "expansion": [],
            "metrics": {"cefr_level": "Error", "variety_score": 0}
        }

def text_to_speech(text: str):
    if not text: return None
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
            st.success(res['corrected'])
            audio = text_to_speech(res['corrected'])
            if audio: st.audio(audio, format="audio/mp3")
            st.caption("Corrected version")

        with t2:
            st.info("Grammar Fixes")
            st.markdown(res['explanation'])
            st.markdown("---")
            st.caption("Original:")
            st.text(st.session_state['original'])

        with t3:
            st.warning("Deepen the Topic")
            if res['questions']:
                for q in res['questions']:
                    st.markdown(f"**❓ {q}**")

        with t4:
            st.subheader("Level Up Words")
            st.caption("Words you DIDN'T use, but should have:")
            
            expansion = res.get('expansion', [])
            if expansion:
                for item in expansion:
                    # Tarjeta de Expansión Estratégica
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
                        if word_audio: st.audio(word_audio, format="audio/mp3")
            else:
                st.write("Good variety! No immediate upgrades suggested.")

if __name__ == "__main__":
    main()