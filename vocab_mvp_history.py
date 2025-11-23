import streamlit as st
import os
import io
import json
import re
import requests
import firebase_admin
from firebase_admin import credentials, firestore, auth
from gtts import gTTS
import streamlit.components.v1 as components
import extra_streamlit_components as stx
import time
from datetime import datetime, timedelta

# --- Configuración Mobile-First ---
st.set_page_config(
    page_title="Pocket English Coach - Strategic MVP",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS Pulido ---
st.markdown("""
    <style>
    .stTextArea textarea { font-size: 16px !important; }
    .stButton button { width: 100%; border-radius: 20px; font-weight: bold; }

    .ipa-text {
        font-family: 'Lucida Sans Unicode', 'Arial Unicode MS', sans-serif;
        color: #555;
        font-size: 0.85rem;
        background-color: #f0f2f6;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 6px;
    }

    .vocab-card {
        border-left: 4px solid #4CAF50;
        padding-left: 12px;
        margin-bottom: 16px;
        background-color: #fafafa;
        padding-top: 8px;
        padding-bottom: 8px;
        border-radius: 0 8px 8px 0;
    }

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

# --- Data Model: History Topics ---
TOPICS = {
    "1ero Básico": [
        {"id": "h1_1", "title": "Mi familia y mi pueblo", "stage": "Época Colonial", "desc": "Vocabulario básico: familia, casa, pueblo. Escribir una descripción corta."},
        {"id": "h1_2", "title": "Fiestas y tradiciones", "stage": "República temprana", "desc": "Actividades sobre costumbres locales y vocabulario cultural."}
    ],
    "8vo Básico": [
        {"id": "h8_1", "title": "Independencia de Chile", "stage": "Independencia", "desc": "Resumen en inglés de hechos clave: causas y consecuencias."},
        {"id": "h8_2", "title": "Personajes relevantes", "stage": "Independencia", "desc": "Biografías cortas en inglés sobre figuras históricas."}
    ],
    "1ero Medio": [
        {"id": "m1_1", "title": "La industrialización", "stage": "Siglo XIX", "desc": "Impacto en la sociedad: redactar un párrafo argumentativo."},
        {"id": "m1_2", "title": "Siglo XX y cambios sociales", "stage": "Siglo XX", "desc": "Analizar cómo cambió la vida cotidiana."}
    ]
}

STAGES = [
    "Prehistoria",
    "Época Colonial",
    "Independencia",
    "República temprana",
    "Siglo XIX",
    "Siglo XX",
    "Siglo XXI"
]

# --- Utilities ---

def compute_variety_score(text: str) -> int:
    words = re.findall(r"\w+", text.lower())
    if not words:
        return 0
    total = len(words)
    unique = len(set(words))
    ttr = unique / total
    score = int(round(1 + ttr * 9))
    return max(1, min(score, 10))

def parse_json_safe(raw: str) -> dict:
    try:
        start = raw.index('{')
        end = raw.rindex('}')
        candidate = raw[start:end+1]
        return json.loads(candidate)
    except Exception:
        try:
            return json.loads(raw)
        except Exception:
            return {}

# --- Firebase Integration ---

def init_firebase():
    if not firebase_admin._apps:
        try:
            if "FIREBASE" in st.secrets:
                cred_dict = dict(st.secrets["FIREBASE"])
                if "private_key" in cred_dict:
                    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Firebase Init Error: {e}")

def get_db():
    if firebase_admin._apps:
        return firestore.client()
    return None

def login_user(email, password):
    api_key = st.secrets.get("FIREBASE_WEB_API_KEY")
    if not api_key:
        return {"localId": email, "email": email}

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    try:
        resp = requests.post(url, json=payload)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": resp.json().get("error", {}).get("message", "Unknown error")}
    except Exception as e:
        return {"error": str(e)}

def register_user(email, password):
    """
    Registers a new user via Firebase REST API.
    """
    api_key = st.secrets.get("FIREBASE_WEB_API_KEY")
    if not api_key:
        return {"error": "Missing FIREBASE_WEB_API_KEY"}

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    try:
        resp = requests.post(url, json=payload)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": resp.json().get("error", {}).get("message", "Unknown error")}
    except Exception as e:
        return {"error": str(e)}

# --- Cookie Manager ---
def get_manager():
    return stx.CookieManager(key="auth_cookies")

def save_analysis_to_firestore(user_id, original_text, result):
    db = get_db()
    if not db:
        return
    
    doc = {
        "user_id": user_id,
        "original_text": original_text,
        "metrics": result.get("metrics", {}),
        "corrected": result.get("corrected", ""),
        "improvements": result.get("improvements", []),
        "expansion_words": result.get("expansion_words", []),
        "questions": result.get("questions", []),
        "timestamp": firestore.SERVER_TIMESTAMP
    }
    try:
        db.collection("english_analyses").add(doc)
        st.toast("Progress saved to cloud! ☁️")
    except Exception as e:
        st.error(f"Error saving to DB: {e}")

def get_user_analyses(user_id):
    db = get_db()
    if not db:
        return []
    try:
        docs = db.collection("english_analyses").where("user_id", "==", user_id).stream()
        data = []
        for doc in docs:
            d = doc.to_dict()
            d['id'] = doc.id
            data.append(d)
        
        # Sort by timestamp descending (handle missing timestamps)
        def get_ts(x):
            ts = x.get('timestamp')
            if isinstance(ts, datetime):
                return ts
            return datetime.min
            
        data.sort(key=get_ts, reverse=True)
        return data
    except Exception as e:
        st.error(f"Error fetching history: {e}")
        return []

# --- Lógica Backend estratégico (Groq) ---
def get_full_analysis(text: str, api_key: str) -> dict:
    # Estructura por defecto si falla
    default_result = {
        "corrected": text,
        "improvements": [],
        "questions": [],
        "expansion_words": [],
        "metrics": {"cefr_level": "N/A", "variety_score": compute_variety_score(text)}
    }

    if not api_key:
        return default_result

    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        # --- PROMPT CORREGIDO: Definición estricta de claves JSON ---
        prompt = f"""
        Role: Strict Lexical Coach. Goal: Increase vocabulary sophistication.
        Input Text: "{text}"

        INSTRUCTIONS:
        Analyze the text and return a valid JSON object.
        
        REQUIRED JSON STRUCTURE (Do not deviate):
        {{
            "metrics": {{
                "cefr_level": "String (e.g., A2, B2, C1)",
                "variety_score": Integer (1-10 based on lexical diversity)
            }},
            "corrected": "String (Native-like version of the text)",
            "improvements": ["String", "String", "String"],
            "questions": ["String", "String"],
            "expansion_words": [
                {{
                    "word": "String (Advanced word)",
                    "ipa": "String (IPA pronunciation)",
                    "replaces_simple_word": "String (The simple word from text it replaces)",
                    "meaning_context": "String (Short definition fitting the context)"
                }},
                ... (Total 3 items)
            ]
        }}
        """

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You represent a backend API. Output ONLY valid JSON. No markdown, no intro."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.1, # Baja temperatura para estructura consistente
            response_format={"type": "json_object"}
        )

        raw = chat_completion.choices[0].message.content
        
        # Parseo seguro
        data = parse_json_safe(raw)

        if not data:
            print("Error: Empty JSON received") # Debug en consola server
            return default_result

        # Mapeo de respuesta con fallbacks seguros
        return {
            "corrected": data.get('corrected', text),
            "improvements": data.get('improvements', []),
            "questions": data.get('questions', []),
            "expansion_words": data.get('expansion_words', []),
            "metrics": data.get("metrics", default_result["metrics"])
        }

    except Exception as e:
        st.error(f"AI Error: {e}") # Mostrar error en UI para depurar si es necesario
        return default_result

# --- Audio ---
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


# ================================
#          MAIN APP
# ================================

def main():
    st.title("🚀 Pocket English Coach")
    st.caption("Strategic Vocabulary Expansion")

    init_firebase()
    cookie_manager = get_manager()

    # --- Session User ---
    if "user" not in st.session_state:
        st.session_state["user"] = None

    # --- Check Cookies for Persistence ---
    if not st.session_state["user"]:
        # Try to get token from cookies
        # Note: get() might return None initially, then trigger rerun
        token = cookie_manager.get(cookie="auth_token")
        if token:
            try:
                # Verify token with Firebase Admin
                decoded_token = auth.verify_id_token(token)
                # Reconstruct user object
                st.session_state["user"] = {
                    "localId": decoded_token["uid"],
                    "email": decoded_token.get("email", ""),
                    "idToken": token
                }
                st.toast(f"Welcome back, {decoded_token.get('email')}!")
            except Exception as e:
                # Token invalid or expired
                # cookie_manager.delete("auth_token") # Optional: auto-clear
                pass

    # --- AUTH NOT LOGGED ---
    if not st.session_state["user"]:
        st.subheader("Welcome")
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login")
                if submitted:
                    user_data = login_user(email, password)
                    if "error" in user_data:
                        st.error(user_data["error"])
                    else:
                        st.session_state["user"] = user_data
                        # Save token to cookie (expires in 7 days)
                        if "idToken" in user_data:
                            expires = datetime.now() + timedelta(days=7)
                            cookie_manager.set("auth_token", user_data["idToken"], expires_at=expires)
                            time.sleep(1) # Allow cookie to be set before rerun
                        st.rerun()
        
        with tab2:
            with st.form("register_form"):
                new_email = st.text_input("Email")
                new_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                submitted_reg = st.form_submit_button("Register")
                if submitted_reg:
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        user_data = register_user(new_email, new_password)
                        if "error" in user_data:
                            st.error(user_data["error"])
                        else:
                            st.success("Account created successfully! Logging in...")
                            st.session_state["user"] = user_data
                            if "idToken" in user_data:
                                expires = datetime.now() + timedelta(days=7)
                                cookie_manager.set("auth_token", user_data["idToken"], expires_at=expires)
                                time.sleep(1) # Allow cookie to be set before rerun
                            st.rerun()

        return  # end auth

    # --- LOGGED IN UI ---
    user_email = st.session_state["user"].get("email", "User")
    user_id = st.session_state["user"].get("localId", user_email)

    with st.sidebar:
        st.write(f"Logged as **{user_email}**")
        if st.button("Logout"):
            st.session_state["user"] = None
            cookie_manager.delete("auth_token")
            st.rerun()
        
        st.markdown("---")
        st.subheader("📜 History")
        history = get_user_analyses(user_id)
        
        if history:
            def format_option(doc):
                ts = doc.get('timestamp')
                date_str = ts.strftime('%d/%m %H:%M') if isinstance(ts, datetime) else "No Date"
                text_preview = doc.get('original_text', '')[:25].replace("\n", " ")
                return f"{date_str} - {text_preview}..."
            
            options = {format_option(h): h for h in history}
            selection = st.selectbox("Load Analysis", ["New Analysis"] + list(options.keys()))
            
            if selection == "New Analysis":
                if st.session_state.get("current_doc_id") is not None:
                    st.session_state["current_doc_id"] = None
                    st.session_state["user_text_input"] = ""
                    if "result" in st.session_state: del st.session_state["result"]
                    if "original" in st.session_state: del st.session_state["original"]
                    st.rerun()
            else:
                doc = options[selection]
                if st.session_state.get("current_doc_id") != doc['id']:
                    st.session_state["current_doc_id"] = doc['id']
                    st.session_state["user_text_input"] = doc.get('original_text', '')
                    st.session_state["original"] = doc.get('original_text', '')
                    st.session_state["result"] = {
                        "metrics": doc.get("metrics", {}),
                        "corrected": doc.get("corrected", ""),
                        "improvements": doc.get("improvements", []),
                        "expansion_words": doc.get("expansion_words", []),
                        "questions": doc.get("questions", [])
                    }
                    st.rerun()

    # --- TOPIC SELECTION ---
    st.subheader("📚 History Topics")
    nav_mode = st.radio("Browse by:", ["Course", "Stage"], horizontal=True)
    
    selected_topic_text = ""

    if nav_mode == "Course":
        curso = st.selectbox("Select Course:", list(TOPICS.keys()))
        topics = TOPICS.get(curso, [])
        
        # Topic Cards
        for t in topics:
            with st.container():
                st.markdown(f"""
                <div class="vocab-card" style="border-left-color: #2196F3;">
                    <div style="display:flex; justify-content:space-between;">
                        <strong>{t['title']}</strong>
                        <span class="ipa-text">{t['stage']}</span>
                    </div>
                    <div style="font-size:0.9rem; color:#666; margin-top:4px;">
                        {t['desc']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Select: {t['title']}", key=t['id']):
                    selected_topic_text = f"Topic: {t['title']}\n\n"
    else:
        etapa = st.selectbox("Select Stage:", STAGES)
        for curso, topics in TOPICS.items():
            for t in topics:
                if t['stage'] == etapa:
                    with st.container():
                        st.markdown(f"""
                        <div class="vocab-card" style="border-left-color: #FF9800;">
                            <div style="display:flex; justify-content:space-between;">
                                <strong>{t['title']}</strong>
                                <span class="ipa-text">{curso}</span>
                            </div>
                            <div style="font-size:0.9rem; color:#666; margin-top:4px;">
                                {t['desc']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"Select: {t['title']}", key=f"stg_{t['id']}"):
                            selected_topic_text = f"Topic: {t['title']}\n\n"

    if selected_topic_text:
        st.session_state["user_text_input"] = selected_topic_text
        st.rerun()

    if "user_text_input" not in st.session_state:
        st.session_state["user_text_input"] = ""

    user_text = st.text_area("Write your story:", height=100, key="user_text_input")

    if st.button("✨ Analyze & Expand"):
        if not user_text.strip():
            st.toast("Please write something!")
        else:
            with st.spinner("Analyzing..."):
                api_key = st.secrets.get("GROQ_API_KEY")
                result = get_full_analysis(user_text, api_key)
                st.session_state["result"] = result
                st.session_state["original"] = user_text

                # Save to Firestore
                user_id = st.session_state["user"].get("localId", user_email)
                save_analysis_to_firestore(user_id, user_text, result)

    # Render results
    if "result" in st.session_state:
        res = st.session_state["result"]
        metrics = res.get("metrics", {})

        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-box">
                <div class="metric-val">{metrics.get('cefr_level')}</div>
                <div class="metric-label">Level Est.</div>
            </div>
            <div class="metric-box">
                <div class="metric-val">{metrics.get('variety_score')}/10</div>
                <div class="metric-label">Lexical Score</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        t1, t2, t3, t4 = st.tabs(["✅ Fix", "💡 Why", "🗣️ Chat", "🚀 Grow"])

        with t1:
            st.success(res.get("corrected", ""))
            audio = text_to_speech(res.get("corrected", ""))
            if audio:
                st.audio(audio, format="audio/mp3")

        with t2:
            st.info("Grammar Fixes")
            for imp in res.get("improvements", []):
                st.markdown(f"- {imp}")
            st.markdown("---")
            st.caption("Original:")
            st.text(st.session_state.get("original", ""))

        with t3:
            st.warning("Deepen the Topic")
            for q in res.get("questions", []):
                st.markdown(f"**❓ {q}**")

        with t4:
            st.subheader("Level Up Words")
            for item in res.get("expansion_words", []):
                st.markdown(f"""
                <div class="vocab-card">
                    <strong>{item.get('word')}</strong>
                    <span class="ipa-text">{item.get('ipa')}</span>
                    <div style="font-size:0.8rem; color:#666;">
                        Instead of: <em>{item.get('replaces_simple_word')}</em>
                    </div>
                    <div>{item.get('meaning_context')}</div>
                </div>
                """, unsafe_allow_html=True)

                col_a, _ = st.columns([1, 4])
                with col_a:
                    audio = text_to_speech(item.get("word", ""))
                    if audio:
                        st.audio(audio, format="audio/mp3")


if __name__ == "__main__":
    main()
