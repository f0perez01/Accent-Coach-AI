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
    page_title="Professional Interview Coach - Tech Edition",
    page_icon="💼",
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
        border-left: 4px solid #2196F3;
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

# --- Data Model: Interview Topics ---
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
    "Intro",
    "Teamwork",
    "Self-Awareness",
    "System Design",
    "Performance",
    "Decision Making",
    "Communication",
    "Productivity"
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
    return stx.CookieManager(key="auth_cookies_cv") # Changed key to avoid conflict

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
        "timestamp": firestore.SERVER_TIMESTAMP,
        "type": "interview_prep" # Tagging as interview prep
    }
    try:
        db.collection("english_analyses_cv").add(doc) # Separate collection or same? Let's use a new one for clarity or just tag it. Using new one for safety.
        st.toast("Progress saved to cloud! ☁️")
    except Exception as e:
        st.error(f"Error saving to DB: {e}")

def get_user_analyses(user_id):
    db = get_db()
    if not db:
        return []
    try:
        docs = db.collection("english_analyses_cv").where("user_id", "==", user_id).stream()
        data = []
        for doc in docs:
            d = doc.to_dict()
            d['id'] = doc.id
            data.append(d)
        
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

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You represent a backend API. Output ONLY valid JSON. No markdown, no intro."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        raw = chat_completion.choices[0].message.content
        data = parse_json_safe(raw)

        if not data:
            print("Error: Empty JSON received")
            return default_result

        return {
            "corrected": data.get('corrected', text),
            "improvements": data.get('improvements', []),
            "questions": data.get('questions', []),
            "expansion_words": data.get('expansion_words', []),
            "metrics": data.get("metrics", default_result["metrics"])
        }

    except Exception as e:
        st.error(f"AI Error: {e}")
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
    st.title("💼 Professional Interview Coach")
    st.caption("Ace your Remote Software Engineering Interview")

    init_firebase()
    cookie_manager = get_manager()

    if "user" not in st.session_state:
        st.session_state["user"] = None

    if not st.session_state["user"]:
        token = cookie_manager.get(cookie="auth_token")
        if token:
            try:
                decoded_token = auth.verify_id_token(token)
                st.session_state["user"] = {
                    "localId": decoded_token["uid"],
                    "email": decoded_token.get("email", ""),
                    "idToken": token
                }
                st.toast(f"Welcome back, {decoded_token.get('email')}!")
            except Exception as e:
                pass

    if not st.session_state["user"]:
        st.subheader("Welcome Professional")
        
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
                        if "idToken" in user_data:
                            expires = datetime.now() + timedelta(days=7)
                            cookie_manager.set("auth_token", user_data["idToken"], expires_at=expires)
                            time.sleep(1)
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
                                time.sleep(1)
                            st.rerun()

        return

    user_email = st.session_state["user"].get("email", "User")
    user_id = st.session_state["user"].get("localId", user_email)

    with st.sidebar:
        st.write(f"Logged as **{user_email}**")
        if st.button("Logout"):
            st.session_state["user"] = None
            cookie_manager.delete("auth_token")
            st.rerun()
        
        st.markdown("---")
        st.subheader("📜 Interview History")
        history = get_user_analyses(user_id)
        
        if history:
            def format_option(doc):
                ts = doc.get('timestamp')
                date_str = ts.strftime('%d/%m %H:%M') if isinstance(ts, datetime) else "No Date"
                text_preview = doc.get('original_text', '')[:25].replace("\n", " ")
                return f"{date_str} - {text_preview}..."
            
            options = {format_option(h): h for h in history}
            selection = st.selectbox("Load Session", ["New Session"] + list(options.keys()))
            
            if selection == "New Session":
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

    st.subheader("🎯 Interview Preparation")
    nav_mode = st.radio("Browse by:", ["Topic", "Category"], horizontal=True)
    
    selected_topic_text = ""

    if nav_mode == "Topic":
        group = st.selectbox("Select Topic Group:", list(TOPICS.keys()))
        topics = TOPICS.get(group, [])
        
        for t in topics:
            with st.container():
                st.markdown(f"""
                <div class="vocab-card" style="border-left-color: #2196F3;">
                    <div style="display:flex; justify-content:space-between;">
                        <strong>{t['title']}</strong>
                        <span class="ipa-text">{t['category']}</span>
                    </div>
                    <div style="font-size:0.9rem; color:#666; margin-top:4px;">
                        {t['desc']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Practice: {t['title']}", key=t['id']):
                    selected_topic_text = f"Interview Question: {t['title']}\n\nMy Answer:\n"
    else:
        cat = st.selectbox("Select Category:", CATEGORIES)
        for group, topics in TOPICS.items():
            for t in topics:
                if t['category'] == cat:
                    with st.container():
                        st.markdown(f"""
                        <div class="vocab-card" style="border-left-color: #FF9800;">
                            <div style="display:flex; justify-content:space-between;">
                                <strong>{t['title']}</strong>
                                <span class="ipa-text">{group}</span>
                            </div>
                            <div style="font-size:0.9rem; color:#666; margin-top:4px;">
                                {t['desc']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"Practice: {t['title']}", key=f"cat_{t['id']}"):
                            selected_topic_text = f"Interview Question: {t['title']}\n\nMy Answer:\n"

    if selected_topic_text:
        st.session_state["user_text_input"] = selected_topic_text
        st.rerun()

    if "user_text_input" not in st.session_state:
        st.session_state["user_text_input"] = ""

    user_text = st.text_area("Draft your answer:", height=150, key="user_text_input", placeholder="I believe my greatest strength is...")

    if st.button("✨ Analyze & Polish"):
        if not user_text.strip():
            st.toast("Please write something!")
        else:
            with st.spinner("Analyzing..."):
                api_key = st.secrets.get("GROQ_API_KEY")
                result = get_full_analysis(user_text, api_key)
                st.session_state["result"] = result
                st.session_state["original"] = user_text

                user_id = st.session_state["user"].get("localId", user_email)
                save_analysis_to_firestore(user_id, user_text, result)

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
                <div class="metric-label">Professional Score</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        t1, t2, t3, t4 = st.tabs(["✅ Polished", "💡 Feedback", "🗣️ Follow-up", "🚀 Power Words"])

        with t1:
            st.success(res.get("corrected", ""))
            audio = text_to_speech(res.get("corrected", ""))
            if audio:
                st.audio(audio, format="audio/mp3")

        with t2:
            st.info("Coaching Tips")
            for imp in res.get("improvements", []):
                st.markdown(f"- {imp}")
            st.markdown("---")
            st.caption("Original Draft:")
            st.text(st.session_state.get("original", ""))

        with t3:
            st.warning("Prepare for these questions:")
            for q in res.get("questions", []):
                st.markdown(f"**❓ {q}**")

        with t4:
            st.subheader("Industry Terminology")
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
