import streamlit as st
import os
import io
from gtts import gTTS
import sys

# --- Configuración de Página Mobile-First ---
st.set_page_config(
    page_title="Pocket English Coach",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Estilos CSS (Mantiene botones grandes para dedos) ---
st.markdown("""
    <style>
    .stTextArea textarea { font-size: 16px !important; }
    .stButton button { width: 100%; border-radius: 20px; font-weight: bold; }
    h1 { font-size: 1.8rem !important; text-align: center; }
    /* Ocultar menú hamburguesa para look más 'app' */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- Lógica Backend Simplificada ---

def get_full_analysis(text: str, api_key: str) -> dict:
    """
    Una sola llamada a la API para obtener:
    1. Texto corregido
    2. Explicación breve
    3. Preguntas de seguimiento
    """
    # Fallback si no hay API key
    if not api_key:
        return {
            "corrected": text, 
            "explanation": "⚠️ API Key missing.",
            "questions": ["Is the API key configured?"]
        }

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        
        # PROMPT ACTUALIZADO: Pide 3 secciones separadas por "|||"
        prompt = (
            f"Act as an ESL English teacher. Analyze this student text: '{text}'.\n"
            f"1. Correct the text to sound natural.\n"
            f"2. Provide 3 bullet points explaining key grammar/vocab changes.\n"
            f"3. Ask 2 interesting follow-up questions related to the topic to encourage conversation.\n"
            f"STRICT OUPUT FORMAT: [Corrected Text] ||| [Explanation Bullets] ||| [Questions]\n"
            f"Do not add intro text."
        )

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.2,
        )
        response = chat_completion.choices[0].message.content
        
        # Parsing robusto (divide por el separador mágico)
        parts = response.split("|||")
        
        # Asegurar que tenemos 3 partes, si falla rellenamos
        corrected = parts[0].strip() if len(parts) > 0 else text
        explanation = parts[1].strip() if len(parts) > 1 else "Improvements applied."
        questions_raw = parts[2].strip() if len(parts) > 2 else "What else can you say about this?"
        
        # Formatear preguntas como lista
        questions = [q.strip() for q in questions_raw.split('\n') if '?' in q]

        return {
            "corrected": corrected, 
            "explanation": explanation,
            "questions": questions
        }

    except Exception as e:
        return {
            "corrected": text, 
            "explanation": "Error connecting to AI.",
            "questions": []
        }

def text_to_speech(text: str):
    """Genera audio en memoria"""
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return mp3_fp
    except Exception:
        return None

# --- Interfaz de Usuario (Frontend) ---

def main():
    st.title("🎓 Pocket English Coach")
    
    # Input Limpio
    user_text = st.text_area(
        "Your Text", 
        height=120, 
        placeholder="Write here (e.g., My hobby is play soccer...)"
    )

    # Botón Mágico
    if st.button("✨ Improve & Analyze", type="primary"):
        if not user_text.strip():
            st.toast("Please write something!", icon="✍️")
        else:
            with st.spinner("Thinking..."):
                # Obtener key
                api_key = st.secrets.get('GROQ_API_KEY', os.environ.get('GROQ_API_KEY'))
                
                # Procesar
                result = get_full_analysis(user_text, api_key)
                st.session_state['result'] = result
                st.session_state['original'] = user_text

    # Resultados con Tabs para mantener la pantalla limpia
    if 'result' in st.session_state:
        res = st.session_state['result']
        st.markdown("---")
        
        # TABS: Dividimos la información para no hacer scroll infinito
        tab1, tab2, tab3 = st.tabs(["✅ Fix", "💡 Why?", "🗣️ Discuss"])
        
        # TAB 1: Resultado Inmediato (Lo que el usuario busca primero)
        with tab1:
            st.subheader("Native Version")
            st.success(res['corrected'])
            
            # Audio
            audio = text_to_speech(res['corrected'])
            if audio:
                st.audio(audio, format="audio/mp3")

            st.caption("Original text:")
            st.text(st.session_state['original'])

        # TAB 2: Explicación (Aprendizaje pasivo)
        with tab2:
            st.subheader("Changes Made")
            st.markdown(res['explanation'])
            st.markdown("---")
            st.caption("Copy to clipboard 👇")
            st.code(res['corrected'], language=None)

        # TAB 3: Profundización (Aprendizaje activo / Nuevo feature)
        with tab3:
            st.subheader("Keep Talking!")
            st.info("Answer these questions to practice more:")
            
            if res['questions']:
                for q in res['questions']:
                    st.markdown(f"**❓ {q}**")
            else:
                st.write("Try writing a longer text to get discussion questions!")

if __name__ == "__main__":
    main()