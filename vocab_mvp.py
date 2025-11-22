import streamlit as st
import os
import io
import json  # Agregamos JSON para robustez
from gtts import gTTS

# --- Configuración Mobile-First ---
st.set_page_config(
    page_title="Pocket English Coach",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS Pulido ---
st.markdown("""
    <style>
    .stTextArea textarea { font-size: 16px !important; }
    .stButton button { width: 100%; border-radius: 20px; font-weight: bold; }
    
    /* Estilo IPA / Diccionario */
    .ipa-text {
        font-family: 'Lucida Sans Unicode', 'Arial Unicode MS', sans-serif;
        color: #555;
        font-size: 0.9rem;
        background-color: #f0f2f6;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 8px;
    }
    .vocab-card {
        border-left: 3px solid #FF4B4B;
        padding-left: 10px;
        margin-bottom: 15px;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- Lógica Backend Robusta ---

def get_full_analysis(text: str, api_key: str) -> dict:
    """
    Usa JSON mode para garantizar que todas las secciones (Tabs)
    reciban datos estructurados correctamente.
    """
    if not api_key:
        return {"corrected": text, "explanation": "⚠️ No API Key", "questions": [], "vocab": []}

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        
        # Prompt optimizado para JSON structure
        # Esto evita que el LLM rompa el formato con texto introductorio
        prompt = (
            f"Analyze this English student text: '{text}'. "
            f"Return a valid JSON object with exactly these keys:\n"
            f"- 'corrected': The corrected version of the text (string).\n"
            f"- 'improvements': A list of 3 short strings explaining grammar/vocab changes.\n"
            f"- 'questions': A list of 2 follow-up questions (strings).\n"
            f"- 'vocab': A list of 3 objects, each with keys: 'word', 'ipa', 'definition' (5 words max).\n"
            f"Focus on interesting or complex words for the vocab section."
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful ESL teacher. Output only JSON."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.1,
            response_format={"type": "json_object"} # Forzamos modo JSON
        )
        
        response_content = chat_completion.choices[0].message.content
        data = json.loads(response_content)

        # Validación de campos (Fallback por si algún campo viene vacío)
        return {
            "corrected": data.get("corrected", text), # Si falla, devuelve original
            "explanation": "\n\n".join([f"• {i}" for i in data.get("improvements", [])]),
            "questions": data.get("questions", []),
            "vocab": data.get("vocab", [])
        }

    except Exception as e:
        # En caso de error extremo, devolvemos estructura vacía segura
        return {
            "corrected": text, 
            "explanation": f"Error analyzing text. Try again. ({str(e)})", 
            "questions": [], 
            "vocab": []
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
    st.title("🎓 Pocket English Coach")
    
    user_text = st.text_area("Your Text", height=100, placeholder="Write here (e.g. I go to school yesterday...)")

    if st.button("✨ Analyze", type="primary"):
        if not user_text.strip():
            st.toast("Please write something!")
        else:
            with st.spinner("Thinking..."):
                api_key = st.secrets.get('GROQ_API_KEY', os.environ.get('GROQ_API_KEY'))
                result = get_full_analysis(user_text, api_key)
                
                # Guardamos en session state
                st.session_state['result'] = result
                st.session_state['original'] = user_text

    if 'result' in st.session_state:
        res = st.session_state['result']
        st.markdown("---")
        
        # TABS
        t1, t2, t3, t4 = st.tabs(["✅ Fix", "💡 Why", "🗣️ Chat", "📖 Vocab"])
        
        with t1:
            st.subheader("Native Version")
            st.success(res['corrected'])
            # Audio y Copiar
            audio = text_to_speech(res['corrected'])
            if audio: st.audio(audio, format="audio/mp3")
            st.caption("Copy text:")
            st.code(res['corrected'], language=None)

        with t2:
            st.subheader("Improvements")
            # Si explanation viene vacía, mostramos mensaje default
            if res['explanation']:
                st.markdown(res['explanation'])
            else:
                st.info("No specific improvements needed.")
            st.markdown("---")
            st.caption("Original:")
            st.text(st.session_state['original'])

        with t3:
            st.subheader("Deep Dive")
            if res['questions']:
                for q in res['questions']:
                    st.info(f"❓ {q}")
            else:
                st.write("Write more text to generate discussion questions.")

        with t4:
            st.subheader("Oxford Style Vocab")
            vocab = res.get('vocab', [])
            
            if vocab:
                for item in vocab:
                    # Renderizado HTML seguro
                    html_content = f"""
                    <div class="vocab-card">
                        <strong>{item.get('word', '')}</strong> 
                        <span class="ipa-text">{item.get('ipa', '')}</span>
                        <br>
                        <em style="font-size:0.9rem; color:#666;">{item.get('definition', '')}</em>
                    </div>
                    """
                    st.markdown(html_content, unsafe_allow_html=True)
                    
                    # Audio individual por palabra
                    col_a, col_b = st.columns([1, 4])
                    with col_a:
                        word_audio = text_to_speech(item.get('word', ''))
                        if word_audio:
                            st.audio(word_audio, format="audio/mp3")
                    
                    st.markdown("---")
            else:
                st.write("No complex vocabulary found in this text.")

if __name__ == "__main__":
    main()