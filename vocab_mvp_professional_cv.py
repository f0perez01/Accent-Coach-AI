"""
Streamlit app: Professional Interview Coach - v2
Replaces selection UI with clickable cards, smart auto-fill, XP/gamification, caching and safer async patterns.

USAGE:
  - Put this file in your project
  - Ensure st.secrets contains FIREBASE and GROQ_API_KEY (optional)
  - Run: `streamlit run streamlit_interview_coach_v2.py`

Notes:
  - This is a drop-in replacement for the selection/gamification flows. It keeps many of your original utilities
    but reorganizes state management and avoids per-item checkboxes.
  - Some integrations (Groq client) remain as stubs/fallbacks because keys and client libs differ across envs.

TODOs: adapt Firestore collection names and credentials to your project.
"""

import streamlit as st
import io
import json
import re
import time
from datetime import datetime, timedelta
import functools

# Optional libs used in your original app
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, auth
except Exception:
    firebase_admin = None

try:
    from gtts import gTTS
except Exception:
    gTTS = None

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="Professional Interview Coach - v2", page_icon="💼", layout="centered")

# -------------------------
# DATA (keep your TOPICS / CATEGORIES)
# -------------------------
TOPICS = {
    "Behavioral Questions": [
        {"id": "beh_1", "title": "Tell me about yourself", "category": "Intro", "desc": "Craft a compelling professional summary highlighting your experience and passion.", "difficulty": "easy"},
        {"id": "beh_2", "title": "Conflict Resolution", "category": "Teamwork", "desc": "Describe a time you had a disagreement with a colleague and how you resolved it.", "difficulty": "medium"},
        {"id": "beh_3", "title": "Greatest Weakness", "category": "Self-Awareness", "desc": "Discuss a real weakness and the steps you are taking to improve it.", "difficulty": "medium"}
    ],
    "Technical Experience": [
        {"id": "tech_1", "title": "Project Deep Dive", "category": "System Design", "desc": "Explain a complex project you worked on, focusing on architecture and challenges.", "difficulty": "hard"},
        {"id": "tech_2", "title": "Scaling Challenges", "category": "Performance", "desc": "Describe a situation where you had to optimize code or infrastructure for scale.", "difficulty": "hard"},
        {"id": "tech_3", "title": "Tech Stack Choice", "category": "Decision Making", "desc": "Why did you choose a specific technology for a past project? Pros and cons.", "difficulty": "medium"}
    ],
    "Remote Work & Soft Skills": [
        {"id": "rem_1", "title": "Remote Collaboration", "category": "Communication", "desc": "How do you ensure effective communication in a distributed team?", "difficulty": "easy"},
        {"id": "rem_2", "title": "Time Management", "category": "Productivity", "desc": "How do you prioritize tasks and manage your time without direct supervision?", "difficulty": "easy"}
    ]
}

CATEGORIES = [
    "Intro", "Teamwork", "Self-Awareness", "System Design", 
    "Performance", "Decision Making", "Communication", "Productivity"
]

# -------------------------
# UTIL: Variety Score
# -------------------------
def compute_variety_score(text: str) -> int:
    words = re.findall(r"\w+", text.lower())
    if not words:
        return 0
    unique = len(set(words))
    score = int(round(1 + (unique / len(words)) * 9))
    return max(1, min(score, 10))

# -------------------------
# STATE INIT
# -------------------------
def init_state():
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("answered_ids", set())
    st.session_state.setdefault("selected_ids", set())
    st.session_state.setdefault("current_batch_ids", [])
    st.session_state.setdefault("xp", 0)
    st.session_state.setdefault("streak_days", 0)
    st.session_state.setdefault("last_active", None)
    st.session_state.setdefault("filter_text", "")
    st.session_state.setdefault("auto_batch_size", 3)

init_state()

# -------------------------
# GAMIFICATION
# -------------------------
DIFFICULTY_XP = {"easy": 10, "medium": 20, "hard": 40}

def add_xp_for_questions(ids):
    gained = 0
    for qid in ids:
        # find question
        for group in TOPICS.values():
            for q in group:
                if q["id"] == qid:
                    gained += DIFFICULTY_XP.get(q.get("difficulty", "easy"), 10)
    st.session_state["xp"] += gained
    # update streak
    now = datetime.utcnow().date()
    last = st.session_state.get("last_active")
    if last is None or (now - last).days >= 1:
        # if last is yesterday then streak++ else reset to 1
        if last is not None and (now - last).days == 1:
            st.session_state["streak_days"] = st.session_state.get("streak_days", 0) + 1
        else:
            st.session_state["streak_days"] = 1
    st.session_state["last_active"] = now
    return gained

def compute_level(xp):
    return xp // 500

# -------------------------
# AUDIO: cache TTS to disk-like BytesIO
# -------------------------
@st.cache_data(show_spinner=False)
def synthesize_tts(text: str):
    if not gTTS:
        return None
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception:
        return None

# -------------------------
# AI: get_full_analysis (safe/cached)
# -------------------------
@st.cache_data(show_spinner=False)
def get_full_analysis(text: str) -> dict:
    # This replaces external client call with safe stub OR uses st.secrets['GROQ_API_KEY'] if present
    default_result = {"corrected": text, "improvements": [], "questions": [], "expansion_words": [], "metrics": {"cefr_level": "N/A", "variety_score": compute_variety_score(text)}}
    # Here you would call your LLM; keep it small and safe
    try:
        api_key = st.secrets.get("GROQ_API_KEY") if hasattr(st, "secrets") else None
        if not api_key:
            # simple polish heuristics as fallback
            polished = text.strip().replace('\n\n', '\n')
            default_result.update({"corrected": polished, "improvements": ["Be more specific with numbers/metrics.", "Start with a one-line summary."], "questions": ["Can you quantify the impact?"], "expansion_words": [{"word": "streamline", "ipa": "ˈstriːmˌlaɪn", "meaning_context": "make a process more efficient"}]})
            return default_result
        # If you have a real client, call it here and parse JSON safely. For now return default.
        return default_result
    except Exception:
        return default_result

# -------------------------
# FIRESTORE helpers (optional)
# -------------------------

def init_firebase_from_secrets():
    if not firebase_admin:
        return
    if not firebase_admin._apps:
        try:
            if "FIREBASE" in st.secrets:
                cred_dict = dict(st.secrets["FIREBASE"])
                cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
        except Exception as e:
            st.warning(f"Firebase init failed: {e}")

def save_analysis_to_firestore(user_id, original_text, result):
    if not firebase_admin or not firebase_admin._apps:
        return
    try:
        db = firestore.client()
        doc = {"user_id": user_id, "original_text": original_text, "metrics": result.get("metrics", {}), "corrected": result.get("corrected", ""), "timestamp": firestore.SERVER_TIMESTAMP}
        db.collection("interview_analyses").add(doc)
    except Exception:
        pass

# -------------------------
# UI: Selection (cards) + Auto-fill
# -------------------------

def selection_ui():
    st.subheader("🎯 Interview Preparation")

    c1, c2, c3 = st.columns([3,2,1])
    with c1:
        st.session_state["filter_text"] = st.text_input("Search questions or keywords", key="filter_text", placeholder="e.g. system design, teamwork")
    with c2:
        mode = st.selectbox("Browse by:", ["Topic", "Category"])
    with c3:
        if st.button("Auto-fill"):
            auto_fill()

    # build candidate list
    candidates = []
    if mode == "Topic":
        group = st.selectbox("Select Topic Group", list(TOPICS.keys()))
        candidates = TOPICS.get(group, [])
    else:
        cat = st.selectbox("Select Category", CATEGORIES)
        for g_name, t_list in TOPICS.items():
            for t in t_list:
                if t.get("category") == cat:
                    t_copy = t.copy(); t_copy["group_origin"] = g_name
                    candidates.append(t_copy)

    flt = st.session_state.get("filter_text", "").strip().lower()
    if flt:
        candidates = [t for t in candidates if flt in t["title"].lower() or flt in t["desc"].lower()]

    # responsive grid (3 columns)
    cols = st.columns(3)
    for idx, t in enumerate(candidates):
        col = cols[idx % 3]
        selected = t["id"] in st.session_state["selected_ids"]
        with col:
            btn_label = ("✅ " if selected else "") + t["title"]
            if st.button(btn_label, key=f"card_{t['id']}"):
                if selected:
                    st.session_state["selected_ids"].discard(t["id"])
                else:
                    st.session_state["selected_ids"].add(t["id"])
                st.experimental_rerun()
            # card body
            st.markdown(f"""
                <div style="padding:8px; margin-top:6px; border-radius:8px; border:1px solid #e0e0e0; background:{'#e8f5e9' if selected else '#ffffff'};">
                    <div style="font-weight:600;">{t['title']}</div>
                    <div style="font-size:0.85rem; color:#666;">{t.get('desc')}</div>
                    <div style="font-size:0.75rem; margin-top:6px;">
                        <span style="background:#f0f0f0;padding:3px 6px;border-radius:4px;">{t.get('category')}</span>
                        <span style="float:right; font-size:0.8rem; color:#999;">{t.get('group_origin', '')}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # action bar
    st.markdown("---")
    selected_count = len(st.session_state["selected_ids"])
    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        st.markdown(f"**Selected:** {selected_count}")
    with c2:
        if st.button("Clear Selection"):
            st.session_state["selected_ids"].clear()
    with c3:
        if st.button("Start Mock Interview", type="primary"):
            if selected_count == 0:
                st.toast("Select at least one question first.")
            else:
                st.session_state["current_batch_ids"] = list(st.session_state["selected_ids"])
                # set up user_text_input like before
                chosen = []
                for g in TOPICS.values():
                    for q in g:
                        if q["id"] in st.session_state["current_batch_ids"]:
                            chosen.append(q)
                intro = "Interview Questions Selected:\n" + "\n".join([f"- {q['title']}" for q in chosen])
                st.session_state["user_text_input"] = f"{intro}\n\nMy Integrated Answer:\n"
                # Mark answered as soon as they start so gamification feels immediate
                gained = add_xp_for_questions(st.session_state["current_batch_ids"])
                st.toast(f"+{gained} XP — Good luck! 🚀")
                st.experimental_rerun()

# -------------------------
# Auto-fill logic
# -------------------------

def auto_fill():
    all_questions = [q for topic in TOPICS.values() for q in topic]
    unanswered = [qq for qq in all_questions if qq["id"] not in st.session_state.get("answered_ids", set())]
    pool = unanswered or all_questions
    selected = []
    cats = set()
    for p in pool:
        if len(selected) >= st.session_state.get("auto_batch_size", 3):
            break
        if p["category"] not in cats:
            selected.append(p)
            cats.add(p["category"])
    i = 0
    while len(selected) < st.session_state.get("auto_batch_size", 3) and i < len(pool):
        if pool[i] not in selected:
            selected.append(pool[i])
        i += 1
    for s in selected:
        st.session_state["selected_ids"].add(s["id"])
    st.toast(f"Auto-filled {len(selected)} questions ✅")

# -------------------------
# MAIN: layout + input + analysis
# -------------------------

def main():
    st.title("💼 Professional Interview Coach")
    st.caption("Ace your Remote Software Engineering Interview")

    # left column: selection
    selection_ui()

    # Input area
    if "user_text_input" not in st.session_state:
        st.session_state["user_text_input"] = ""
    user_text = st.text_area("Draft your answer:", height=150, key="user_text_input")

    if st.button("✨ Analyze & Polish"):
        if not user_text.strip():
            st.toast("Write something first!")
        else:
            with st.spinner("Analyzing..."):
                res = get_full_analysis(user_text)
                # mark answered and save xp; here we assume current_batch_ids were the ones
                if st.session_state.get("current_batch_ids"):
                    st.session_state["answered_ids"].update(st.session_state["current_batch_ids"])
                    st.session_state["current_batch_ids"] = []
                st.session_state["result"] = res
                st.session_state["original"] = user_text
                # optional: save to firestore
                # save_analysis_to_firestore(user_id, user_text, res)
                st.toast("Analysis complete — check feedback below!")

    # Results
    if "result" in st.session_state:
        r = st.session_state["result"]
        m = r.get("metrics", {})
        st.markdown(f"**Level:** {m.get('cefr_level')} • **Variety:** {m.get('variety_score')}/10")
        tabs = st.tabs(["✅ Polished", "💡 Feedback", "🗣️ Follow-up", "🚀 Vocab"])
        with tabs[0]:
            st.success(r.get("corrected"))
            audio_bytes = synthesize_tts(r.get("corrected"))
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")
        with tabs[1]:
            for i in r.get("improvements", []):
                st.info(i)
            with st.expander("Show Original"):
                st.text(st.session_state.get("original", ""))
        with tabs[2]:
            for q in r.get("questions", []):
                st.warning(f"❓ {q}")
        with tabs[3]:
            for w in r.get("expansion_words", []):
                st.markdown(f"**{w.get('word')}** `/{w.get('ipa','')}/`: {w.get('meaning_context','')}")
                w_audio = synthesize_tts(w.get('word', ''))
                if w_audio:
                    st.audio(w_audio, format="audio/mp3")

    # Profile / gamification card
    st.sidebar.markdown("## Profile & Gamification")
    st.sidebar.markdown(f"**XP:** {st.session_state.get('xp')} • **Level:** {compute_level(st.session_state.get('xp',0))}")
    st.sidebar.markdown(f"**Streak:** {st.session_state.get('streak_days')} days")
    if st.sidebar.button("Claim daily bonus"):
        st.session_state['xp'] += 5
        st.toast("+5 XP daily bonus!")


if __name__ == '__main__':
    main()

# End of file
