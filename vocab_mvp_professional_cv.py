import streamlit as st
import os
import io
import json
import re
import requests
import firebase_admin
from firebase_admin import credentials, firestore, auth
from gtts import gTTS
import extra_streamlit_components as stx
import time
from datetime import datetime, timedelta

# ================================
# 1. CONFIGURACIÓN & ESTILOS
# ================================

st.set_page_config(
    page_title="Professional Interview Coach - Tech Edition",
    page_icon="💼",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    /* Global Styles */
    .stTextArea textarea { font-size: 16px !important; }
    .stButton button { width: 100%; border-radius: 20px; font-weight: bold; }

    /* Custom Component Styles */
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
        padding: 8px 12px;
        border-radius: 0 4px 4px 0;
        margin-bottom: 0px; /* Streamlit columns handle spacing */
    }

    .metric-container {
        display: flex;
        justify-content: space-around;
        margin-bottom: 20px;
        background: #e3f2fd;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #bbdefb;
    }
    .metric-box { text-align: center; }
    .metric-val { font-size: 1.2rem; font-weight: bold; color: #1565c0; }
    .metric-label { font-size: 0.8rem; color: #666; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ================================
# 2. MODELO DE DATOS
# ================================

TOPICS = {
    "Behavioral Questions": [
        {"id": "beh_1", "title": "Tell me about yourself", "category": "Intro", "desc": "Craft a compelling professional summary highlighting your experience and passion."},
        {"id": "beh_2", "title": "Conflict Resolution", "category": "Teamwork", "desc": "Describe a time you had a disagreement with a colleague and how you resolved it."},
        {"id": "beh_3", "title": "Greatest Weakness", "category": "Self-Awareness", "desc": "Discuss a real weakness and the steps you are taking to improve it."}
    ],
    "Technical Experience": [
        {"id": "tech_1", "title": "Project Deep Dive", "category": "System Design", "desc": "Explain a complex project you worked on, focusing on architecture and challenges."},
        {"id": "tech_2", "title": "Scaling Challenges", "category": "Performance", "desc": "Describe a situation where you had to optimize code or infrastructure for scale."},
        {"id": "tech_3", "title": "Tech Stack Choice", "category": "Decision Making", "desc": "Why did you choose a specific technology for a past project? Pros and cons."}
    ],
    "Remote Work & Soft Skills": [
        {"id": "rem_1", "title": "Remote Collaboration", "category": "Communication", "desc": "How do you ensure effective communication in a distributed team?"},
        {"id": "rem_2", "title": "Time Management", "category": "Productivity", "desc": "How do you prioritize tasks and manage your time without direct supervision?"}
    ]
}

CATEGORIES = [
    "Intro", "Teamwork", "Self-Awareness", "System Design", 
    "Performance", "Decision Making", "Communication", "Productivity"
]

# ================================
# 3. UTILIDADES & BACKEND
# ================================

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
    except:
        return {}

def init_firebase():
    if not firebase_admin._apps:
        try:
            if "FIREBASE" in st.secrets:
                cred_dict = dict(st.secrets["FIREBASE"])
                cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Firebase Error: {e}")

def get_db():
    return firestore.client() if firebase_admin._apps else None

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

def save_analysis_to_firestore(user_id, original_text, result):
    db = get_db()
    if not db: return
    doc = {
        "user_id": user_id, "original_text": original_text, 
        "metrics": result.get("metrics", {}), "corrected": result.get("corrected", ""),
        "improvements": result.get("improvements", []), "expansion_words": result.get("expansion_words", []),
        "questions": result.get("questions", []), "timestamp": firestore.SERVER_TIMESTAMP
    }
    db.collection("english_analyses_cv").add(doc)
    st.toast("Progress saved to cloud! ☁️")

def get_user_analyses(user_id):
    db = get_db()
    if not db: return []
    docs = db.collection("english_analyses_cv").where("user_id", "==", user_id).stream()
    data = [{"id": d.id, **d.to_dict()} for d in docs]
    data.sort(key=lambda x: x.get('timestamp', datetime.min) if isinstance(x.get('timestamp'), datetime) else datetime.min, reverse=True)
    return data

def get_full_analysis(text: str, api_key: str) -> dict:
    default_result = {"corrected": text, "improvements": [], "questions": [], "expansion_words": [], "metrics": {"cefr_level": "N/A", "variety_score": 0}}
    if not api_key: return default_result
    
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        prompt = f"""
        Role: Senior Tech Recruiter. Goal: Optimize answer for clarity/impact.
        Input: "{text}"
        Output JSON only: {{
            "metrics": {{"cefr_level": "B2/C1", "variety_score": 1-10}},
            "corrected": "Polished version",
            "improvements": ["Tip 1", "Tip 2"],
            "questions": ["Follow-up 1", "Follow-up 2"],
            "expansion_words": [{{"word": "X", "ipa": "/x/", "replaces_simple_word": "y", "meaning_context": "z"}}]
        }}
        """
        completion = client.chat.completions.create(
            messages=[{"role": "system", "content": "JSON only."}, {"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant", temperature=0.1, response_format={"type": "json_object"}
        )
        data = parse_json_safe(completion.choices[0].message.content)
        return {**default_result, **data} if data else default_result
    except Exception as e:
        st.error(f"AI Error: {e}")
        return default_result

def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except: return None

# ================================
# 4. MAIN APPLICATION
# ================================

def main():
    st.title("💼 Professional Interview Coach")
    st.caption("Ace your Remote Software Engineering Interview")

    init_firebase()
    cookie_manager = stx.CookieManager(key="auth_cookies_cv")

    # --- AUTHENTICATION FLOW ---
    if "user" not in st.session_state: st.session_state["user"] = None

    if not st.session_state["user"]:
        token = cookie_manager.get(cookie="auth_token")
        if token:
            try:
                decoded = auth.verify_id_token(token)
                st.session_state["user"] = {"localId": decoded["uid"], "email": decoded.get("email", "")}
                st.toast(f"Welcome back!")
            except: pass

    if not st.session_state["user"]:
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
        return # Stop execution if not logged in

    user = st.session_state["user"]
    
    # --- GAMIFICATION STATE ---
    if "answered_ids" not in st.session_state: st.session_state["answered_ids"] = set()
    if "current_batch_ids" not in st.session_state: st.session_state["current_batch_ids"] = []

    # Calculate Progress
    all_q = [q for topic in TOPICS.values() for q in topic]
    completed = len(st.session_state["answered_ids"])
    total = len(all_q)
    pct = (completed / total) * 100 if total > 0 else 0
    
    # Render Dashboard
    st.markdown(f"""
    <div style="display: flex; align-items: center; background: white; padding: 15px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 25px;">
        <div style="position: relative; width: 60px; height: 60px; border-radius: 50%; background: conic-gradient(#4CAF50 {(pct/100)*360}deg, #f0f2f6 0deg); display: flex; align-items: center; justify-content: center; margin-right: 15px;">
            <div style="width: 50px; height: 50px; background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.8rem; color: #333;">{int(pct)}%</div>
        </div>
        <div>
            <div style="font-weight: bold; font-size: 1rem; color: #333;">Tu Progreso de Hoy</div>
            <div style="font-size: 0.85rem; color: #666;">Has dominado <strong>{completed}</strong> de <strong>{total}</strong> preguntas.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- SIDEBAR HISTORY ---
    with st.sidebar:
        st.write(f"👤 **{user['email']}**")
        if st.button("Logout"):
            st.session_state["user"] = None
            cookie_manager.delete("auth_token")
            st.rerun()
        st.markdown("---")
        
        # Load History Logic
        history = get_user_analyses(user['localId'])
        options = {f"{h.get('timestamp').strftime('%d/%m %H:%M') if isinstance(h.get('timestamp'), datetime) else ''} - {h.get('original_text', '')[:20]}...": h for h in history}
        
        sel = st.selectbox("📜 History", ["New Session"] + list(options.keys()))
        if sel == "New Session" and st.session_state.get("current_doc_id"):
            st.session_state["current_doc_id"] = None
            st.session_state["user_text_input"] = ""
            st.session_state.pop("result", None)
            st.rerun()
        elif sel != "New Session":
            doc = options[sel]
            if st.session_state.get("current_doc_id") != doc['id']:
                st.session_state.update({
                    "current_doc_id": doc['id'],
                    "user_text_input": doc.get('original_text', ''),
                    "original": doc.get('original_text', ''),
                    "result": doc
                })
                st.rerun()

    # --- SELECTION INTERFACE ---
    st.subheader("🎯 Interview Preparation")
    nav_mode = st.radio("Browse by:", ["Topic", "Category"], horizontal=True)

    candidates = []
    if nav_mode == "Topic":
        group = st.selectbox("Selecciona el Tópico:", list(TOPICS.keys()))
        candidates = TOPICS.get(group, [])
        default_color = "#2196F3"
    else:
        cat = st.selectbox("Selecciona la Categoría:", CATEGORIES)
        for g_name, t_list in TOPICS.items():
            for t in t_list:
                if t.get('category') == cat:
                    t_copy = t.copy()
                    t_copy['group_origin'] = g_name
                    candidates.append(t_copy)
        default_color = "#FF9800"

    selected_questions = []
    
    with st.container():
        for t in candidates:
            # Check status
            is_done = t['id'] in st.session_state["answered_ids"]
            
            # Dynamic Styling
            border_c = "#4CAF50" if is_done else default_color
            bg_c = "#f1f8e9" if is_done else "#f8f9fa"
            icon = "✅" if is_done else ""
            
            # UX: Vertical Alignment Center (Streamlit 1.37+)
            c1, c2 = st.columns([0.15, 0.85], vertical_alignment="center")
            
            with c1:
                # Key ensures unique ID. Label empty for visual cleaness
                if st.checkbox("", key=f"chk_{t['id']}"):
                    selected_questions.append(t)
            
            with c2:
                meta = t.get('group_origin', t['category'])
                st.markdown(f"""
                <div class="vocab-card" style="border-left: 3px solid {border_c}; background-color: {bg_c};">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <strong style="color:#333;">{t['title']} {icon}</strong>
                        <span style="font-size:0.7rem; background:#e0e0e0; padding:2px 6px; border-radius:4px; color:#555;">{meta}</span>
                    </div>
                    <div style="font-size:0.85rem; color:#666; margin-top:4px; line-height:1.4;">{t['desc']}</div>
                </div>
                """, unsafe_allow_html=True)

    # --- ACTION BAR (Stickyish) ---
    if selected_questions:
        st.markdown("---")
        if st.button(f"📝 Responder estas {len(selected_questions)} preguntas", type="primary", use_container_width=True):
            # 1. Save Batch
            st.session_state["current_batch_ids"] = [q['id'] for q in selected_questions]
            
            # 2. Build Prompt
            intro = "Interview Questions Selected:\n" + "\n".join([f"- {q['title']}" for q in selected_questions])
            st.session_state["user_text_input"] = f"{intro}\n\nMy Integrated Answer:\n"
            
            # 3. Auto-Reset Checkboxes (UX Magic)
            for t in candidates:
                if f"chk_{t['id']}" in st.session_state:
                    st.session_state[f"chk_{t['id']}"] = False
            
            st.rerun()

    # --- INPUT AREA ---
    if "user_text_input" not in st.session_state: st.session_state["user_text_input"] = ""
    
    user_text = st.text_area("Draft your answer:", height=150, key="user_text_input", placeholder="Start typing...")

    if st.button("✨ Analyze & Polish"):
        if not user_text.strip():
            st.toast("Write something first!")
        else:
            with st.spinner("Analyzing..."):
                res = get_full_analysis(user_text, st.secrets.get("GROQ_API_KEY"))
                
                # Update Progress ONLY on successful analysis
                if st.session_state["current_batch_ids"]:
                    st.session_state["answered_ids"].update(st.session_state["current_batch_ids"])
                    st.session_state["current_batch_ids"] = []
                    st.toast("Progress Updated! 🚀")
                
                st.session_state["result"] = res
                st.session_state["original"] = user_text
                save_analysis_to_firestore(user['localId'], user_text, res)

    # --- RESULTS DISPLAY ---
    if "result" in st.session_state:
        r = st.session_state["result"]
        m = r.get("metrics", {})
        
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-box"><div class="metric-val">{m.get('cefr_level')}</div><div class="metric-label">Level</div></div>
            <div class="metric-box"><div class="metric-val">{m.get('variety_score')}/10</div><div class="metric-label">Score</div></div>
        </div>
        """, unsafe_allow_html=True)

        t1, t2, t3, t4 = st.tabs(["✅ Polished", "💡 Feedback", "🗣️ Follow-up", "🚀 Vocab"])
        
        with t1:
            st.success(r.get("corrected"))
            aud = text_to_speech(r.get("corrected"))
            if aud: st.audio(aud, format="audio/mp3")
            
        with t2:
            for i in r.get("improvements", []): st.info(i)
            with st.expander("Show Original"): st.text(st.session_state["original"])
            
        with t3:
            for q in r.get("questions", []): st.warning(f"❓ {q}")
            
        with t4:
            for w in r.get("expansion_words", []):
                st.markdown(f"**{w['word']}** `/{w['ipa']}/`: {w['meaning_context']}")
                aud = text_to_speech(w['word'])
                if aud: st.audio(aud, format="audio/mp3")

if __name__ == "__main__":
    main()