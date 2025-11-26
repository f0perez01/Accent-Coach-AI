import streamlit as st
import io
import json
import re
import requests
import time
from datetime import datetime, timedelta
import extra_streamlit_components as stx

# Intentar importar librerías opcionales con manejo de errores
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, auth
except ImportError:
    firebase_admin = None

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

try:
    from groq import Groq
except ImportError:
    Groq = None

# ==========================================
# 1. CONFIGURACIÓN & ESTILOS
# ==========================================
st.set_page_config(
    page_title="Professional Interview Coach - Pro",
    page_icon="💼",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    /* Estilos Globales */
    .stTextArea textarea { font-size: 16px !important; }
    .stButton button { width: 100%; border-radius: 12px; font-weight: 600; }
    
    /* Tarjetas de Selección */
    .selection-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        background-color: white;
        transition: transform 0.2s, box-shadow 0.2s;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .selection-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    .selection-card.selected {
        border: 2px solid #2196F3;
        background-color: #e3f2fd;
    }
    
    /* Métricas */
    .metric-container {
        display: flex;
        justify-content: space-around;
        margin-bottom: 20px;
        background: #f8f9fa;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #dee2e6;
    }
    .metric-box { text-align: center; }
    .metric-val { font-size: 1.4rem; font-weight: bold; color: #2196F3; }
    .metric-label { font-size: 0.8rem; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MODELO DE DATOS
# ==========================================
TOPICS = {
    "Behavioral Questions": [
        {"id": "beh_1", "title": "Tell me about yourself", "category": "Intro", "desc": "Craft a compelling professional summary highlighting your experience.", "difficulty": "easy"},
        {"id": "beh_2", "title": "Conflict Resolution", "category": "Teamwork", "desc": "Describe a time you had a disagreement with a colleague.", "difficulty": "medium"},
        {"id": "beh_3", "title": "Greatest Weakness", "category": "Self-Awareness", "desc": "Discuss a real weakness and steps to improve it.", "difficulty": "medium"}
    ],
    "Technical Experience": [
        {"id": "tech_1", "title": "Project Deep Dive", "category": "System Design", "desc": "Explain a complex project focusing on architecture.", "difficulty": "hard"},
        {"id": "tech_2", "title": "Scaling Challenges", "category": "Performance", "desc": "Optimize code or infrastructure for scale.", "difficulty": "hard"},
        {"id": "tech_3", "title": "Tech Stack Choice", "category": "Decision Making", "desc": "Why did you choose a specific technology? Pros/Cons.", "difficulty": "medium"}
    ],
    "Remote Work & Soft Skills": [
        {"id": "rem_1", "title": "Remote Collaboration", "category": "Communication", "desc": "Ensuring effective communication in distributed teams.", "difficulty": "easy"},
        {"id": "rem_2", "title": "Time Management", "category": "Productivity", "desc": "Prioritizing tasks without supervision.", "difficulty": "easy"}
    ]
}

CATEGORIES = ["Intro", "Teamwork", "Self-Awareness", "System Design", "Performance", "Decision Making", "Communication", "Productivity"]

# ==========================================
# 3. BACKEND & UTILIDADES (Auth, DB, AI)
# ==========================================

# --- Init Firebase ---
def init_firebase():
    if not firebase_admin: return
    if not firebase_admin._apps:
        try:
            if "FIREBASE" in st.secrets:
                cred_dict = dict(st.secrets["FIREBASE"])
                cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Firebase Init Error: {e}")

def get_db():
    return firestore.client() if firebase_admin and firebase_admin._apps else None

# --- Auth ---
def login_user(email, password):
    api_key = st.secrets.get("FIREBASE_WEB_API_KEY")
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    try:
        resp = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
        return resp.json() if resp.status_code == 200 else {"error": resp.json().get("error", {}).get("message", "Error")}
    except Exception as e: return {"error": str(e)}

def register_user(email, password):
    api_key = st.secrets.get("FIREBASE_WEB_API_KEY")
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
    try:
        resp = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
        return resp.json() if resp.status_code == 200 else {"error": resp.json().get("error", {}).get("message", "Error")}
    except Exception as e: return {"error": str(e)}

# --- Send Email
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_gmail(to_email: str, subject: str, body: str):
    """Send email using Gmail + App Password."""
    gmail_user = st.secrets["GMAIL"]["EMAIL"]
    gmail_password = st.secrets["GMAIL"]["APP_PASSWORD"]

    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, to_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Email error: {e}")
        return False


# --- Firestore Logic ---
def save_analysis_to_firestore(user_id, original_text, result):
    db = get_db()
    if not db: return
    
    # Calcular XP ganado en esta sesión
    xp_gained = st.session_state.get("last_xp_gained", 0)
    
    doc = {
        "user_id": user_id,
        "original_text": original_text,
        "metrics": result.get("metrics", {}),
        "corrected": result.get("corrected", ""),
        "improvements": result.get("improvements", []),
        "expansion_words": result.get("expansion_words", []),
        "questions": result.get("questions", []),
        "xp_earned": xp_gained,
        "timestamp": firestore.SERVER_TIMESTAMP
    }
    try:
        db.collection("english_analyses_cv").add(doc)
        st.toast("Analysis saved to cloud! ☁️")
    except Exception as e:
        print(f"DB Error: {e}")

def get_user_analyses(user_id):
    db = get_db()
    if not db: return []
    try:
        docs = db.collection("english_analyses_cv").where("user_id", "==", user_id).stream()
        data = [{"id": d.id, **d.to_dict()} for d in docs]
        data.sort(key=lambda x: x.get('timestamp', datetime.min) if isinstance(x.get('timestamp'), datetime) else datetime.min, reverse=True)
        return data
    except: return []

# --- AI Logic (Groq) ---
def compute_variety_score(text: str) -> int:
    words = re.findall(r"\w+", text.lower())
    if not words: return 0
    unique = len(set(words))
    score = int(round(1 + (unique / len(words)) * 9))
    return max(1, min(score, 10))

def parse_json_safe(raw: str) -> dict:
    try:
        start = raw.index('{')
        end = raw.rindex('}')
        return json.loads(raw[start:end+1])
    except: return {}

@st.cache_data(show_spinner=False)
def get_full_analysis(text: str) -> dict:
    # PROMPT ORIGINAL RESTAURADO
    api_key = st.secrets.get("GROQ_API_KEY")
    default_res = {"corrected": text, "improvements": [], "questions": [], "expansion_words": [], "metrics": {"cefr_level": "N/A", "variety_score": compute_variety_score(text)}}
    
    if not api_key or not Groq: return default_res

    try:
        client = Groq(api_key=api_key)
        prompt = f"""
        Role: Senior Tech Recruiter & Communication Coach for US Companies.
        Goal: Optimize the candidate's answer for clarity, professionalism, and impact in a remote software engineering interview context.
        Input Text: "{text}"

        INSTRUCTIONS:
        Analyze the text and return a valid JSON object.
        
        REQUIRED JSON STRUCTURE (Do not deviate):
        {{
            "metrics": {{
                "cefr_level": "String (e.g., B2, C1, C2)",
                "variety_score": Integer (1-10 based on professional vocabulary)
            }},
            "corrected": "String (Polished, professional version suitable for a job interview)",
            "improvements": ["String (Specific advice on tone, clarity, or STAR method)", "String", "String"],
            "questions": ["String (Follow-up interview question)", "String (Technical or behavioral probe)"],
            "expansion_words": [
                {{
                    "word": "String (Power verb or industry term)",
                    "ipa": "String (IPA pronunciation)",
                    "replaces_simple_word": "String (The weaker word used)",
                    "meaning_context": "String (Why this word is better for interviews)"
                }},
                ... (Total 3 items)
            ]
        }}
        """

        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You represent a backend API. Output ONLY valid JSON. No markdown."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        data = parse_json_safe(completion.choices[0].message.content)
        return {**default_res, **data} if data else default_res

    except Exception as e:
        st.error(f"AI Error: {e}")
        return default_res

@st.cache_data(show_spinner=False)
def synthesize_tts(text: str):
    if not gTTS: return None
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except: return None

## --- Second LLM call
def get_teacher_feedback(analysis: dict, original_text: str) -> str:
    """
    Second LLM call: rewrite feedback in English-teacher tone.
    Returns a friendly email body.
    """
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key or not Groq:
        return "Your feedback is ready, but the AI model is offline."

    try:
        client = Groq(api_key=api_key)

        prompt = f"""
        You are a friendly English teacher who helps ESL students.
        Rewrite the following analysis as warm, constructive feedback.
        Tone: kind, supportive, motivating.
        Format: an email addressed directly to the student.

        Student's original answer:
        {original_text}

        Analysis data:
        {json.dumps(analysis, indent=2)}

        Produce ONLY the email body. No JSON, no explanation, no greeting lines like "Here is your email".
        """

        chat = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You write clear, warm English teacher feedback."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.4
        )

        return chat.choices[0].message.content.strip()

    except Exception as e:
        st.error(f"Feedback LLM error: {e}")
        return "We couldn't generate feedback due to an AI issue."

# ==========================================
# 4. LÓGICA DE ESTADO Y GAMIFICATION
# ==========================================

def init_state():
    if "user" not in st.session_state: st.session_state["user"] = None
    if "answered_ids" not in st.session_state: st.session_state["answered_ids"] = set()
    if "selected_ids" not in st.session_state: st.session_state["selected_ids"] = set()
    if "current_batch_ids" not in st.session_state: st.session_state["current_batch_ids"] = []
    if "xp" not in st.session_state: st.session_state["xp"] = 0
    if "last_xp_gained" not in st.session_state: st.session_state["last_xp_gained"] = 0

DIFFICULTY_XP = {"easy": 10, "medium": 20, "hard": 40}

def calculate_xp_potential(ids):
    total = 0
    for qid in ids:
        for group in TOPICS.values():
            for q in group:
                if q["id"] == qid:
                    total += DIFFICULTY_XP.get(q.get("difficulty", "easy"), 10)
    return total

def commit_xp(ids):
    gained = calculate_xp_potential(ids)
    st.session_state["xp"] += gained
    st.session_state["last_xp_gained"] = gained
    return gained

def compute_level(xp):
    return 1 + (xp // 500)

# ==========================================
# 5. UI COMPONENTS
# ==========================================

def selection_ui():
    st.subheader("🎯 Preparación de Entrevista")
    
    # Filtros y Auto-select
    c_filter, c_auto = st.columns([3, 1])
    with c_filter:
        group = st.selectbox("Topic Group", list(TOPICS.keys()), label_visibility="collapsed")
    with c_auto:
        if st.button("🎲 Auto-Fill"):
            # Lógica simple de auto-fill (3 preguntas aleatorias no contestadas)
            all_q = [q for t in TOPICS.values() for q in t if q['id'] not in st.session_state["answered_ids"]]
            import random
            picks = random.sample(all_q, min(3, len(all_q))) if all_q else []
            for p in picks: st.session_state["selected_ids"].add(p['id'])
            st.toast(f"Auto-selected {len(picks)} questions!")
            st.rerun()

    candidates = TOPICS.get(group, [])
    
    # Grid de Tarjetas (Responsive)
    cols = st.columns(3)
    for idx, t in enumerate(candidates):
        is_selected = t["id"] in st.session_state["selected_ids"]
        is_done = t["id"] in st.session_state["answered_ids"]
        
        with cols[idx % 3]:
            # Botón invisible full-width para la tarjeta
            if st.button(f"{'✅' if is_selected else '⬜'} {t['title']}", key=f"btn_{t['id']}", use_container_width=True):
                if is_selected: st.session_state["selected_ids"].discard(t['id'])
                else: st.session_state["selected_ids"].add(t['id'])
                st.rerun()
            
            # Decoración visual debajo del botón
            status_color = "#4CAF50" if is_done else ("#2196F3" if is_selected else "#e0e0e0")
            bg_color = "#e8f5e9" if is_done else ("#e3f2fd" if is_selected else "#ffffff")
            
            st.markdown(f"""
            <div style="margin-top:-5px; margin-bottom:15px; padding:10px; border-radius:8px; border-left:4px solid {status_color}; background-color:{bg_color}; font-size:0.85rem; color:#555;">
                {t['desc']}
                <div style="margin-top:5px; font-size:0.7rem; color:#888;">XP: {DIFFICULTY_XP.get(t.get('difficulty'), 10)}</div>
            </div>
            """, unsafe_allow_html=True)

    # Action Bar Sticky
    count = len(st.session_state["selected_ids"])
    if count > 0:
        st.markdown("---")
        xp_pot = calculate_xp_potential(st.session_state["selected_ids"])
        if st.button(f"📝 Start Session ({count} Questions) - Pot. XP: +{xp_pot}", type="primary"):
            # Generar prompt
            chosen = []
            for g in TOPICS.values():
                for q in g:
                    if q["id"] in st.session_state["selected_ids"]: chosen.append(q)
            
            intro = "Interview Questions Selected:\n" + "\n".join([f"- {q['title']}" for q in chosen])
            st.session_state["user_text_input"] = f"{intro}\n\nMy Integrated Answer:\n"
            st.session_state["current_batch_ids"] = list(st.session_state["selected_ids"])
            # Limpiar selección visual pero mantener batch en memoria
            st.session_state["selected_ids"].clear()
            st.rerun()

# ==========================================
# 6. MAIN APP FLOW
# ==========================================

def main():
    init_firebase()
    init_state()
    cookie_manager = stx.CookieManager(key="auth_cookies_v2")

    # --- Auth Flow ---
    if not st.session_state["user"]:
        token = cookie_manager.get(cookie="auth_token")
        if token:
            try:
                decoded = auth.verify_id_token(token)
                st.session_state["user"] = {"localId": decoded["uid"], "email": decoded.get("email", "")}
            except: pass

    if not st.session_state["user"]:
        st.title("🔐 Professional Coach Login")
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            with st.form("login"):
                email, pwd = st.text_input("Email"), st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    data = login_user(email, pwd)
                    if "error" in data: st.error(data["error"])
                    else:
                        st.session_state["user"] = data
                        cookie_manager.set("auth_token", data["idToken"], expires_at=datetime.now() + timedelta(days=7))
                        st.rerun()
        return

    # --- Logged In View ---
    user = st.session_state["user"]
    
    # Sidebar
    with st.sidebar:
        st.write(f"👤 **{user['email']}**")
        
        # Gamification Stats
        curr_xp = st.session_state["xp"]
        curr_lvl = compute_level(curr_xp)
        st.metric("Level", f"{curr_lvl}", f"{curr_xp} XP")
        st.progress(min(1.0, (curr_xp % 500) / 500))
        
        st.divider()
        
        # History Loader
        history = get_user_analyses(user['localId'])
        options = {f"{h.get('timestamp').strftime('%d/%m') if h.get('timestamp') else ''} - {h.get('original_text', '')[:15]}...": h for h in history}
        sel = st.selectbox("📜 History", ["New Session"] + list(options.keys()))
        
        if sel != "New Session":
            doc = options[sel]
            if st.session_state.get("current_doc_id") != doc['id']:
                st.session_state["current_doc_id"] = doc['id']
                st.session_state["user_text_input"] = doc.get('original_text', '')
                st.session_state["original"] = doc.get('original_text', '')
                st.session_state["result"] = doc
                st.rerun()
        elif st.session_state.get("current_doc_id"):
            # Reset to new session
            st.session_state["current_doc_id"] = None
            st.session_state["user_text_input"] = ""
            st.session_state.pop("result", None)
            st.rerun()

        if st.button("Logout"):
            st.session_state["user"] = None
            cookie_manager.delete("auth_token")
            st.rerun()

    # Main Content
    st.title("💼 Interview Coach Pro")
    
    # Render UI
    selection_ui()

    # Input Area
    if "user_text_input" not in st.session_state: st.session_state["user_text_input"] = ""
    user_text = st.text_area("Draft your answer:", height=200, key="user_text_input", placeholder="Start typing here...")

    # Botón Análisis
    if st.button("✨ Analyze & Polish", type="primary"):
        if not user_text.strip():
            st.toast("Please write something!")
        else:
            with st.spinner("Analyzing with AI..."):
                # Llamada al LLM Real
                res = get_full_analysis(user_text)
                
                # Update Gamification (Confirmar Batch)
                if st.session_state["current_batch_ids"]:
                    xp_gained = commit_xp(st.session_state["current_batch_ids"])
                    st.session_state["answered_ids"].update(st.session_state["current_batch_ids"])
                    st.session_state["current_batch_ids"] = [] # Clear batch
                    st.toast(f"Analysis Done! +{xp_gained} XP Earned! 🚀")
                
                # Save to State & DB
                st.session_state["result"] = res
                st.session_state["original"] = user_text
                save_analysis_to_firestore(user['localId'], user_text, res)

    # Resultados
    if "result" in st.session_state:
        r = st.session_state["result"]
        m = r.get("metrics", {})
        
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-box"><div class="metric-val">{m.get('cefr_level', 'N/A')}</div><div class="metric-label">Level</div></div>
            <div class="metric-box"><div class="metric-val">{m.get('variety_score', 0)}/10</div><div class="metric-label">Variety</div></div>
            <div class="metric-box"><div class="metric-val">+{st.session_state.get('last_xp_gained', 0)}</div><div class="metric-label">XP Gained</div></div>
        </div>
        """, unsafe_allow_html=True)

        t1, t2, t3, t4 = st.tabs(["✅ Polished", "💡 Tips", "🗣️ Follow-up", "🚀 Vocab"])
        
        with t1:
            st.success(r.get("corrected"))
            aud = synthesize_tts(r.get("corrected"))
            if aud: st.audio(aud, format="audio/mp3")
        with t2:
            for i in r.get("improvements", []): st.info(f"• {i}")
            with st.expander("Show Original Text"): st.text(st.session_state["original"])
        with t3:
            for q in r.get("questions", []): st.warning(f"❓ {q}")
        with t4:
            for w in r.get("expansion_words", []):
                st.markdown(f"**{w.get('word')}** `/{w.get('ipa','')}/`")
                st.caption(f"Replace: {w.get('replaces_simple_word', '')} | Context: {w.get('meaning_context', '')}")
                aud = synthesize_tts(w.get('word'))
                if aud: st.audio(aud, format="audio/mp3")

    # === BUTTON: TRIGGER SECOND LLM CALL ===
    if "result" in st.session_state:
        st.markdown("### 📧 Teacher Feedback Email")

        if st.button("Send Teacher Feedback to My Email"):
            with st.spinner("Generating teacher-style feedback..."):
                email_body = get_teacher_feedback(
                    analysis=st.session_state["result"],
                    original_text=st.session_state["user_text_input"]
                )

            with st.spinner(f"Sending email to {user['email']}..."):
                ok = send_email_gmail(
                    to_email=user["email"],
                    subject="Your English Feedback from Interview Coach",
                    body=email_body
                )

            if ok:
                st.success("Feedback sent! Check your inbox 📬")
            else:
                st.error("Could not send the email.")

if __name__ == '__main__':
    main()