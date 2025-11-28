#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Accent Coach AI - Streamlit Interface
Interactive pronunciation practice application for American English
"""

import os
import io
import re
import tempfile
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional
import json
import base64
from st_pronunciation_widget import streamlit_pronunciation_widget
import streamlit.components.v1 as components

import streamlit as st
import numpy as np
import pandas as pd
import torch
import plotly.graph_objects as go
import plotly.express as px
import requests
import extra_streamlit_components as stx

from phonemizer.punctuation import Punctuation
from sequence_align.pairwise import needleman_wunsch
from asr_model import ASRModelManager
from practice_texts import PracticeTextManager
from ipa_definitions import IPADefinitionsManager
from audio_processor import AudioProcessor, TTSGenerator, AudioValidator

try:
    from groq import Groq
    _HAS_GROQ = True
except Exception:
    _HAS_GROQ = False

try:
    import firebase_admin
    from firebase_admin import credentials, firestore, auth
    _HAS_FIREBASE = True
except ImportError:
    _HAS_FIREBASE = False

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

MODEL_OPTIONS = {
    "Wav2Vec2 Base (Fast, Cloud-Friendly)": "facebook/wav2vec2-base-960h",
    "Wav2Vec2 Large (Better Accuracy, Needs More RAM)": "facebook/wav2vec2-large-960h",
    "Wav2Vec2 XLSR (Phonetic)": "mrrubino/wav2vec2-large-xlsr-53-l2-arctic-phoneme",
}

# Default model - use Base for cloud deployments (smaller, faster)
DEFAULT_MODEL = "facebook/wav2vec2-base-960h"

# Initialize ASR Model Manager (global instance)
asr_manager = ASRModelManager(DEFAULT_MODEL, MODEL_OPTIONS)

# ============================================================================
# FIREBASE AUTHENTICATION & DATABASE
# ============================================================================

def init_firebase():
    """Initialize Firebase Admin SDK"""
    if not _HAS_FIREBASE:
        return
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
    """Get Firestore database client"""
    return firestore.client() if _HAS_FIREBASE and firebase_admin._apps else None

def login_user(email: str, password: str) -> dict:
    """Login user with Firebase Authentication"""
    api_key = st.secrets.get("FIREBASE_WEB_API_KEY")
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    try:
        resp = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
        return resp.json() if resp.status_code == 200 else {"error": resp.json().get("error", {}).get("message", "Error")}
    except Exception as e:
        return {"error": str(e)}

def register_user(email: str, password: str) -> dict:
    """Register new user with Firebase Authentication"""
    api_key = st.secrets.get("FIREBASE_WEB_API_KEY")
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
    try:
        resp = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
        return resp.json() if resp.status_code == 200 else {"error": resp.json().get("error", {}).get("message", "Error")}
    except Exception as e:
        return {"error": str(e)}

def save_analysis_to_firestore(user_id: str, reference_text: str, result: dict):
    """Save pronunciation analysis to Firestore"""
    db = get_db()
    if not db:
        return

    doc = {
        "user_id": user_id,
        "reference_text": reference_text,
        "raw_decoded": result.get("raw_decoded", ""),
        "metrics": result.get("metrics", {}),
        "per_word_comparison": result.get("per_word_comparison", []),
        "llm_feedback": result.get("llm_feedback", ""),
        "timestamp": firestore.SERVER_TIMESTAMP
    }
    try:
        db.collection("accent_coach_analyses").add(doc)
        st.toast("Analysis saved to cloud! ☁️")
    except Exception as e:
        print(f"Firestore Error: {e}")

def get_user_analyses(user_id: str) -> list:
    """Get user's pronunciation analysis history from Firestore"""
    db = get_db()
    if not db:
        return []
    try:
        docs = db.collection("english_analyses_cv").where("user_id", "==", user_id).stream()
        data = [{"id": d.id, **d.to_dict()} for d in docs]
        # Sort by timestamp descending
        data.sort(
            key=lambda x: x.get('timestamp', datetime.min) if isinstance(x.get('timestamp'), datetime) else datetime.min,
            reverse=True
        )
        return data
    except Exception as e:
        print(f"Firestore Query Error: {e}")
        return []

# ============================================================================
# PHONEME PROCESSING FUNCTIONS
# ============================================================================

def tokenize_phonemes(s: str) -> List[str]:
    """Tokenize phoneme string into individual tokens"""
    s = s.strip()
    if " " in s:
        return s.split()
    tok = re.findall(r"[a-zA-Zʰɪʌɒəɜɑɔɛʊʏœøɯɨɫɹːˈˌ˞̃͜͡d͡ʒ]+|[^\s]", s)
    return [t for t in tok if t]


def align_sequences(a: List[str], b: List[str]) -> Tuple[List[str], List[str]]:
    """Align two sequences using Needleman-Wunsch algorithm"""
    return needleman_wunsch(a, b, match_score=2, mismatch_score=-1, indel_score=-1, gap="_")


def align_per_word(lexicon: List[Tuple[str, str]], rec_tokens: List[str]):
    """Align recorded tokens to reference phonemes word by word"""
    ref_all = []
    word_lens = []
    for word, phon in lexicon:
        parts = phon.split()
        word_lens.append(len(parts))
        if parts:
            ref_all.extend(parts)

    if not ref_all:
        return ["" for _ in lexicon], ["" for _ in lexicon]

    aligned_ref, aligned_rec = align_sequences(ref_all, rec_tokens)

    per_word_ref = []
    per_word_rec = []

    ref_token_count = 0
    for wlen, (word, phon) in zip(word_lens, lexicon):
        if wlen == 0:
            per_word_ref.append("")
            per_word_rec.append("")
            continue

        start = ref_token_count
        end = start + wlen

        ref_buf = []
        rec_buf = []

        non_gap_idx = 0
        for a_r, a_p in zip(aligned_ref, aligned_rec):
            if a_r != "_":
                if start <= non_gap_idx < end:
                    ref_buf.append(a_r)
                    if a_p != "_":
                        rec_buf.append(a_p)
                non_gap_idx += 1

        per_word_ref.append("".join(ref_buf))
        per_word_rec.append("".join(rec_buf))

        ref_token_count = end

    return per_word_ref, per_word_rec


# ============================================================================
# TRANSCRIPTION & ANALYSIS PIPELINE
# ============================================================================

@st.cache_data
def generate_reference_phonemes(text: str, lang: str = "en-us") -> Tuple[List[Tuple[str, str]], List[str]]:
    """Generate reference phonemes from text using gruut"""
    from gruut import sentences

    clean = Punctuation(";:,.!\"?()").remove(text)
    lexicon, words = [], []

    for sent in sentences(clean, lang=lang):
        for w in sent:
            t = w.text.strip().lower()
            if not t:
                continue
            words.append(t)
            try:
                phon = " ".join(w.phonemes)
            except:
                phon = t
            lexicon.append((t, phon))

    return lexicon, words


def get_llm_feedback(reference_text: str, per_word_comparison: List[Dict],
                     groq_api_key: str) -> Optional[str]:
    """Get accent coaching feedback from Groq LLM"""
    if not _HAS_GROQ or not groq_api_key:
        return None

    try:
        client = Groq(api_key=groq_api_key)

        diff = "\n".join(
            f"{item['word']}: expected={item['ref_phonemes']}, produced={item['rec_phonemes']}"
            for item in per_word_comparison
        )

        system_message = """You are an expert dialect/accent coach for American spoken English.
Provide feedback to improve the speaker's American accent.
Use Google pronunciation respelling when giving corrections.
Provide the following sections:
- Overall Impression
- Specific Feedback
- Google Pronunciation Respelling Suggestions
- Additional Tips"""

        user_prompt = f"""Reference Text: {reference_text}

(word, reference_phoneme, recorded_phoneme)
{diff}"""

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt},
            ],
            model="llama-3.1-8b-instant",
            temperature=0
        )

        return chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"LLM feedback failed: {e}")
        return None


def calculate_metrics(per_word_comparison: List[Dict]) -> Dict:
    """Calculate pronunciation accuracy metrics"""
    total_words = len(per_word_comparison)
    correct_words = sum(1 for item in per_word_comparison if item['match'])

    # Calculate phoneme-level metrics
    total_phonemes = 0
    correct_phonemes = 0
    substitutions = 0
    insertions = 0
    deletions = 0

    for item in per_word_comparison:
        ref = item['ref_phonemes']
        rec = item['rec_phonemes']

        # Simple character-level comparison
        ref_chars = list(ref) if ref else []
        rec_chars = list(rec) if rec else []

        total_phonemes += len(ref_chars)

        # Align at character level for detailed metrics
        if ref == rec:
            correct_phonemes += len(ref_chars)
        else:
            aligned_ref, aligned_rec = align_sequences(ref_chars, rec_chars)
            for r, p in zip(aligned_ref, aligned_rec):
                if r == p and r != "_":
                    correct_phonemes += 1
                elif r != "_" and p == "_":
                    deletions += 1
                elif r == "_" and p != "_":
                    insertions += 1
                elif r != p and r != "_" and p != "_":
                    substitutions += 1

    word_accuracy = (correct_words / total_words * 100) if total_words > 0 else 0
    phoneme_accuracy = (correct_phonemes / total_phonemes * 100) if total_phonemes > 0 else 0
    phoneme_error_rate = 100 - phoneme_accuracy

    return {
        'word_accuracy': word_accuracy,
        'phoneme_accuracy': phoneme_accuracy,
        'phoneme_error_rate': phoneme_error_rate,
        'total_words': total_words,
        'correct_words': correct_words,
        'total_phonemes': total_phonemes,
        'correct_phonemes': correct_phonemes,
        'substitutions': substitutions,
        'insertions': insertions,
        'deletions': deletions,
    }


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def plot_waveform(audio: np.ndarray, sr: int, title: str = "Audio Waveform"):
    """Plot audio waveform using plotly"""
    duration = len(audio) / sr
    time = np.linspace(0, duration, len(audio))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time, y=audio, mode='lines', name='Amplitude'))
    fig.update_layout(
        title=title,
        xaxis_title="Time (s)",
        yaxis_title="Amplitude",
        height=200,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    return fig


def display_comparison_table(per_word_comparison: List[Dict], show_only_errors: bool = False):
    """Display word-by-word comparison table"""
    if show_only_errors:
        data = [item for item in per_word_comparison if not item.get('match', False)]
    else:
        data = per_word_comparison

    if not data:
        st.info("No errors found! Perfect pronunciation!")
        return

    # Create DataFrame
    df = pd.DataFrame(data)

    # Ensure all required columns exist
    if 'match' not in df.columns:
        df['match'] = False
    if 'word' not in df.columns:
        df['word'] = ''
    if 'ref_phonemes' not in df.columns:
        df['ref_phonemes'] = ''
    if 'rec_phonemes' not in df.columns:
        df['rec_phonemes'] = ''

    # Add Status column
    df['Status'] = df['match'].apply(lambda x: '✓' if x else '✗')

    # Prepare display dataframe
    display_df = df[['word', 'ref_phonemes', 'rec_phonemes', 'Status']].copy()

    # Color coding function
    def highlight_errors(row):
        # Get the original index to access the 'match' column
        idx = row.name
        is_match = df.loc[idx, 'match'] if idx in df.index else False

        if not is_match:
            return ['background-color: #ffebee'] * len(row)
        else:
            return ['background-color: #e8f5e9'] * len(row)

    # Apply styling
    styled_df = display_df.style.apply(highlight_errors, axis=1)

    st.dataframe(styled_df, use_container_width=True, height=400)


def plot_error_distribution(metrics: Dict):
    """Plot error type distribution"""
    error_types = ['Substitutions', 'Insertions', 'Deletions']
    error_counts = [metrics['substitutions'], metrics['insertions'], metrics['deletions']]

    fig = px.bar(
        x=error_types,
        y=error_counts,
        labels={'x': 'Error Type', 'y': 'Count'},
        title='Phoneme Error Distribution',
        color=error_types,
        color_discrete_sequence=['#EF5350', '#FFA726', '#42A5F5']
    )
    fig.update_layout(showlegend=False, height=300)
    return fig

def render_ipa_guide_component(text: str, lang: str = "en-us"):
    """
    Renderiza una guía educativa con reproductores de audio individuales
    por palabra usando un diseño de filas y columnas (Grid Layout).
    """
    from gruut import sentences
    
    # 1. Procesar texto
    breakdown_data = []
    unique_symbols = set()
    
    clean_text = Punctuation(';:,.!?"()').remove(text)
    
    # Usamos un contador global para evitar IDs duplicados en los reproductores
    word_counter = 0 
    
    for sent in sentences(clean_text, lang=lang):
        for w in sent:
            word_text = w.text
            try:
                phonemes_list = w.phonemes
                phoneme_str = "".join(phonemes_list)
                
                # Recolectar símbolos para glosario
                for p in phonemes_list:
                    clean_p = p.replace("ˈ", "").replace("ˌ", "")
                    if IPADefinitionsManager.get_definition(clean_p):
                        unique_symbols.add(clean_p)
                    elif IPADefinitionsManager.get_definition(p):
                        unique_symbols.add(p)

                # Pistas
                hints = []
                for p in phonemes_list:
                    clean_p = p.replace("ˈ", "").replace("ˌ", "")
                    definition = IPADefinitionsManager.get_definition(clean_p)
                    if definition:
                        desc = definition.split('(')[0].strip()
                        hints.append(desc)
                
                hint_str = " + ".join(hints[:3])
                if len(hints) > 3: hint_str += "..."

                # Generar audio individual para esta palabra
                # Nota: Esto puede tardar un poco si la frase es muy larga
                word_audio = TTSGenerator.generate_audio(word_text, lang=lang)

                breakdown_data.append({
                    "index": word_counter,
                    "word": word_text,
                    "ipa": f"/{phoneme_str}/",
                    "hint": hint_str,
                    "audio": word_audio
                })
                word_counter += 1
                
            except Exception:
                continue

    # 2. Renderizar UI
    with st.expander("📖 Guía de Pronunciación Paso a Paso (Decodificador)", expanded=False):
        
        tab1, tab2 = st.tabs(["🧩 Desglose por Palabra", "📚 Glosario de Símbolos"])
        
        with tab1:
            st.markdown("#### 🕵️‍♀️ Práctica de Drilling")
            st.markdown("Escucha y repite palabra por palabra:")
            
            # --- ENCABEZADOS DE LA TABLA ---
            # Ajustamos los ratios de las columnas para que se vea ordenado
            h1, h2, h3, h4 = st.columns([1.5, 1.5, 2.5, 1.5])
            h1.markdown("**Palabra**")
            h2.markdown("**IPA**")
            h3.markdown("**Pista**")
            h4.markdown("**Audio**")
            
            st.divider() # Línea separadora
            
            # --- FILAS DE DATOS ---
            if breakdown_data:
                for item in breakdown_data:
                    c1, c2, c3, c4 = st.columns([1.5, 1.5, 2.5, 1.5])
                    
                    # Alineación vertical visual usando padding o markdown
                    with c1:
                        st.markdown(f"### {item['word']}")
                    
                    with c2:
                        # Usamos st.code para resaltar el IPA
                        st.code(item['ipa'], language=None)
                        
                    with c3:
                        if item['hint']:
                            st.caption(f"💡 {item['hint']}")
                        else:
                            st.caption("-")
                            
                    with c4:
                        if item['audio']:
                            # key es vital aquí para evitar conflictos
                            st.audio(item['audio'], format="audio/mp3")
                    
                    # Separador ligero entre filas
                    st.markdown("<hr style='margin: 5px 0; opacity: 0.2;'>", unsafe_allow_html=True)
            else:
                st.warning("No se pudo procesar el desglose fonético.")

        with tab2:
            st.markdown("#### 🗝️ Símbolos Clave")
            st.markdown("Glosario de símbolos encontrados en esta frase:")

            cols = st.columns(2)
            for i, sym in enumerate(sorted(unique_symbols)):
                definition = IPADefinitionsManager.get_definition(sym) or "Sonido específico"
                with cols[i % 2]:
                    st.info(f"**{sym}** : {definition}")


# ============================================================================
# STREAMLIT APP
# ============================================================================

def init_session_state():
    """Initialize session state variables"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = []
    if 'current_result' not in st.session_state:
        st.session_state.current_result = None
    if 'current_doc_id' not in st.session_state:
        st.session_state.current_doc_id = None
    if 'config' not in st.session_state:
        st.session_state.config = {
            'model_name': DEFAULT_MODEL,  # Use base model by default (cloud-friendly)
            'use_g2p': True,
            'use_llm': True,
            'lang': 'en-us'
        }


def main():
    st.set_page_config(
        page_title="Accent Coach AI",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    init_firebase()
    init_session_state()

    # Cookie manager for persistent auth
    cookie_manager = stx.CookieManager(key="auth_cookies_accent")

    # --- AUTH FLOW ---
    if not st.session_state.user:
        # Try to restore session from cookie
        token = cookie_manager.get(cookie="auth_token")
        if token and _HAS_FIREBASE:
            try:
                decoded = auth.verify_id_token(token)
                st.session_state.user = {
                    "localId": decoded["uid"],
                    "email": decoded.get("email", "")
                }
            except:
                pass

    # Show login/register if not authenticated
    if not st.session_state.user:
        st.title("🔐 Accent Coach AI - Login")
        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    data = login_user(email, password)
                    if "error" in data:
                        st.error(data["error"])
                    else:
                        st.session_state.user = data
                        cookie_manager.set("auth_token", data["idToken"], expires_at=datetime.now() + timedelta(days=7))
                        st.success("Login successful!")
                        st.rerun()

        with tab2:
            with st.form("register_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                password_confirm = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Register"):
                    if password != password_confirm:
                        st.error("Passwords don't match!")
                    else:
                        data = register_user(email, password)
                        if "error" in data:
                            st.error(data["error"])
                        else:
                            st.success("Registration successful! Please login.")
        return

    # --- LOGGED IN VIEW ---
    user = st.session_state.user

    # Title
    st.title("🎙️ Accent Coach AI")
    st.markdown("Practice your American English pronunciation with AI-powered feedback")

    # Sidebar
    with st.sidebar:
        st.write(f"👤 **{user['email']}**")
        st.divider()

        # --- HISTORY LOADER ---
        st.header("📜 History")
        history = get_user_analyses(user['localId'])

        # Create options for selectbox
        history_options = {}
        if history:
            for h in history:
                timestamp_str = h.get('timestamp').strftime('%d/%m %H:%M') if h.get('timestamp') else 'Unknown'
                # Use 'original_text' which is the field in english_analyses_cv
                text_preview = h.get('original_text', '')[:30] + "..." if len(h.get('original_text', '')) > 30 else h.get('original_text', '')
                label = f"{timestamp_str} - {text_preview}"
                history_options[label] = h

        selected_history = st.selectbox(
            "Select from history or start new",
            ["📝 New Practice Session"] + list(history_options.keys())
        )

        # Initialize reference_text variable
        reference_text = ""

        # Load selected history or start new session
        if selected_history != "📝 New Practice Session":
            doc = history_options[selected_history]
            # Load the text from 'original_text' field (from english_analyses_cv)
            reference_text = doc.get('original_text', '')

            # Reset current_doc_id since we're loading a writing practice text (no previous audio analysis)
            if st.session_state.get("current_doc_id") != doc['id']:
                st.session_state.current_doc_id = doc['id']
                # Don't set previous_result since there's no audio analysis in this collection
                st.session_state.pop("previous_result", None)
                st.session_state.current_result = None
                st.rerun()

            st.info("📖 Practice pronunciation for this text from your writing history!")
            st.caption(f"**Text:** {reference_text[:50]}{'...' if len(reference_text) > 50 else ''}")
        else:
            # New session - reset
            if st.session_state.get("current_doc_id"):
                st.session_state.current_doc_id = None
                st.session_state.pop("previous_result", None)
                st.session_state.current_result = None
                st.rerun()

        st.divider()

        # --- PRACTICE TEXT SELECTION (Only for new sessions) ---
        if selected_history == "📝 New Practice Session":
            st.header("🎯 Practice Text Selection")

            # Category selection
            category = st.selectbox("Category", PracticeTextManager.get_categories())

            # Text selection
            text_option = st.selectbox("Select a phrase", PracticeTextManager.get_texts_for_category(category))

            # Custom text option
            use_custom = st.checkbox("Use custom text")
            if use_custom:
                custom_text = st.text_area("Enter your text:", value=text_option, height=100)
                reference_text = custom_text
            else:
                reference_text = text_option

        st.divider()

        # Advanced settings
        with st.expander("⚙️ Advanced Settings"):
            model_choice = st.selectbox("ASR Model", list(MODEL_OPTIONS.keys()))
            st.session_state.config['model_name'] = MODEL_OPTIONS[model_choice]

            st.session_state.config['use_g2p'] = st.checkbox("Use G2P (Grapheme-to-Phoneme)", value=True)
            st.session_state.config['use_llm'] = st.checkbox("Enable LLM Feedback", value=True)
            st.session_state.config['lang'] = st.selectbox("Language", ["en-us"], index=0)

        st.divider()

        # System info
        st.header("📊 System Info")

        # Get API keys from secrets or environment
        try:
            groq_api_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY"))
            hf_token = st.secrets.get("HF_API_TOKEN", os.environ.get("HF_API_TOKEN"))
        except:
            groq_api_key = os.environ.get("GROQ_API_KEY")
            hf_token = os.environ.get("HF_API_TOKEN")

        if groq_api_key and _HAS_GROQ:
            st.success("✓ Groq API Connected")
        else:
            st.warning("⚠ Groq API Not Available")

        device = "CUDA" if torch.cuda.is_available() else "CPU"
        st.info(f"Device: {device}")
        st.caption(f"Model: {model_choice}")

        # Model verification and cache management
        st.divider()
        st.subheader("🔧 Model Status")

        # Test model load button
        if st.button("✅ Test Model Download", help="Verify that the model can be downloaded"):
            with st.spinner("Testing model download..."):
                try:
                    test_model = st.session_state.config['model_name']
                    asr_manager.load_model(test_model, hf_token)
                    st.success(f"✅ Model loaded successfully!")
                    st.info(f"📦 Model: {test_model}")
                    st.info(f"💻 Device: {asr_manager.device}")
                    try:
                        param_count = sum(p.numel() for p in asr_manager.model.parameters())
                        st.caption(f"Parameters: {param_count:,}")
                    except:
                        pass
                except Exception as e:
                    st.error("❌ Model download failed!")
                    st.error(f"Error: {str(e)[:300]}")
                    st.warning("💡 Try:")
                    st.warning("1. Clear cache (button below)")
                    st.warning("2. Use 'Wav2Vec2 Base' model")
                    st.warning("3. Check your internet connection")

        # Clear cache button
        if st.button("🗑️ Clear Model Cache", help="Clear cached models to free up space"):
            st.cache_resource.clear()
            st.success("✓ Cache cleared! Page will reload.")
            st.rerun()

        st.divider()

        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            cookie_manager.delete("auth_token")
            st.rerun()

    # Main panel
    st.header("📝 Reference Text")
    st.markdown(f"### {reference_text}")
    st.caption(f"Length: {len(reference_text.split())} words")

    # --- STUDY PHASE ---
    # 1. Generate Data
    with st.spinner("Preparing study materials..."):
        lexicon, _ = generate_reference_phonemes(reference_text, st.session_state.config['lang'])
        phoneme_text = " ".join([phon for _, phon in lexicon])
        tts_audio = TTSGenerator.generate_audio(reference_text)

    # 2. Render Karaoke Player
    if tts_audio:
        b64_audio = base64.b64encode(tts_audio).decode()

        streamlit_pronunciation_widget(reference_text, phoneme_text, b64_audio)
        
        # === AQUÍ AGREGAMOS LA NUEVA GUÍA ===
        st.markdown("---") # Separador sutil
        render_ipa_guide_component(reference_text, st.session_state.config['lang'])
        # ====================================
        
    else:
        st.info(f"**IPA:** /{phoneme_text}/")
        st.warning("Audio generation failed.")

    st.divider()

    # Recording section
    st.header("🎙️ Record Your Pronunciation")

    st.markdown("**Click below to record your pronunciation**")
    st.caption("Speak clearly and naturally. The recording will stop automatically when you're done.")

    audio_bytes = st.audio_input("Record your pronunciation")

    if audio_bytes:
        st.success("✓ Recording captured!")

        # Safe extraction
        audio_data = audio_bytes.getvalue() if hasattr(audio_bytes, "getvalue") else audio_bytes

        audio_size = len(audio_data) / 1024  # KB
        st.caption(f"Audio size: {audio_size:.1f} KB")

        # Diagnostics
        with st.expander("🔍 Audio Diagnostics (click to expand)"):
            try:
                import soundfile as sf

                audio_file = io.BytesIO(audio_data)
                waveform, sr = sf.read(audio_file, dtype='float32')

                st.write(f"Sample rate: {sr} Hz")
                st.write(f"Duration: {len(waveform) / sr:.2f} seconds")
                st.write(f"Samples: {len(waveform)}")

            except Exception as e:
                st.error(f"Could not analyze audio: {e}")

        # FIXED PLAYBACK
        try:
            st.audio(audio_data, format="audio/wav")
        except Exception:
            st.warning("⚠️ Retrying audio playback with fallback...")
            try:
                st.audio(bytes(audio_data), format="audio/wav")
            except:
                st.error("❌ Audio playback failed.")


    # Analysis button
    if audio_bytes:
        if st.button("🚀 Analyze Pronunciation", type="primary", use_container_width=True):
            # Load model using ASRModelManager
            asr_manager.load_model(
                st.session_state.config['model_name'],
                hf_token
            )

            # Convert audio_bytes to bytes if it's a file-like object
            audio_data = audio_bytes.getvalue() if hasattr(audio_bytes, 'getvalue') else audio_bytes

            # Transcribe using ASRModelManager
            audio, sr = AudioProcessor.load_from_bytes(audio_data)
            if audio is None:
                st.error("Audio loading failed.")
                return
            raw_decoded, recorded_phoneme_str = asr_manager.transcribe(
                audio, sr,
                use_g2p=st.session_state.config['use_g2p'],
                lang=st.session_state.config['lang']
            )

            # Generate reference
            lexicon, ref_words = generate_reference_phonemes(reference_text, st.session_state.config['lang'])
            rec_tokens = tokenize_phonemes(recorded_phoneme_str)
            per_word_ref, per_word_rec = align_per_word(lexicon, rec_tokens)
            per_word_comparison = []
            for i, word in enumerate(ref_words):
                ref_ph = per_word_ref[i]
                rec_ph = per_word_rec[i]
                match = ref_ph == rec_ph
                per_word_comparison.append({
                    'word': word,
                    'ref_phonemes': ref_ph,
                    'rec_phonemes': rec_ph,
                    'match': match
                })
            metrics = calculate_metrics(per_word_comparison)
            llm_feedback = None
            if st.session_state.config['use_llm'] and groq_api_key:
                with st.spinner("Getting AI coach feedback..."):
                    llm_feedback = get_llm_feedback(reference_text, per_word_comparison, groq_api_key)
            result = {
                'timestamp': datetime.now(),
                'audio_data': audio_data,
                'audio_array': audio,
                'sample_rate': sr,
                'reference_text': reference_text,
                'raw_decoded': raw_decoded,
                'recorded_phoneme_str': recorded_phoneme_str,
                'per_word_comparison': per_word_comparison,
                'llm_feedback': llm_feedback,
                'metrics': metrics,
            }
            st.session_state.current_result = result
            st.session_state.analysis_history.append(result)
            save_analysis_to_firestore(user['localId'], reference_text, result)
            st.success("Analysis complete!")
            st.rerun()

    # Results display
    if st.session_state.current_result:
        # Show current result
        st.divider()
        st.header("📊 Analysis Results")

        result = st.session_state.current_result

        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Word Comparison",
            "🎓 Coach Feedback",
            "🔬 Technical Analysis",
            "📚 History"
        ])

        with tab1:
            st.subheader("Word-by-Word Comparison")

            col1, col2 = st.columns([3, 1])
            with col2:
                show_errors_only = st.checkbox("Show errors only", value=False)

            display_comparison_table(result['per_word_comparison'], show_errors_only)

            # Quick stats
            metrics = result['metrics']
            col1, col2, col3 = st.columns(3)
            col1.metric("Word Accuracy", f"{metrics['word_accuracy']:.1f}%")
            col2.metric("Correct Words", f"{metrics['correct_words']}/{metrics['total_words']}")
            col3.metric("Phoneme Accuracy", f"{metrics['phoneme_accuracy']:.1f}%")

        with tab2:
            st.subheader("AI Coach Feedback")

            if result['llm_feedback']:
                st.markdown(result['llm_feedback'])

                # Copy button
                if st.button("📋 Copy Feedback"):
                    st.code(result['llm_feedback'])
            else:
                st.info("LLM feedback is disabled. Enable it in Advanced Settings.")

        with tab3:
            st.subheader("Technical Analysis")

            # Metrics
            st.markdown("#### Metrics")
            metrics = result['metrics']

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Word Accuracy", f"{metrics['word_accuracy']:.1f}%")
            col2.metric("Phoneme Accuracy", f"{metrics['phoneme_accuracy']:.1f}%")
            col3.metric("Phoneme Error Rate", f"{metrics['phoneme_error_rate']:.1f}%")
            col4.metric("Total Errors", metrics['substitutions'] + metrics['insertions'] + metrics['deletions'])

            # Error distribution
            st.markdown("#### Error Distribution")
            fig = plot_error_distribution(metrics)
            st.plotly_chart(fig, use_container_width=True)

            # Waveform
            st.markdown("#### Audio Waveform")
            fig_wave = plot_waveform(result['audio_array'], result['sample_rate'])
            st.plotly_chart(fig_wave, use_container_width=True)

            # Technical details
            with st.expander("🔍 View Technical Details"):
                st.markdown("**Raw Decoded Text:**")
                st.code(result['raw_decoded'])
                st.markdown("**Phoneme String:**")
                st.code(result['recorded_phoneme_str'])

        with tab4:
            st.subheader("Session History")

            if len(st.session_state.analysis_history) > 0:
                st.info(f"Total attempts: {len(st.session_state.analysis_history)}")

                for i, hist_result in enumerate(reversed(st.session_state.analysis_history)):
                    with st.expander(f"Attempt #{len(st.session_state.analysis_history) - i} - {hist_result['timestamp'].strftime('%H:%M:%S')}"):
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Word Accuracy", f"{hist_result['metrics']['word_accuracy']:.1f}%")
                        col2.metric("Phoneme Accuracy", f"{hist_result['metrics']['phoneme_accuracy']:.1f}%")
                        col3.metric("Errors", hist_result['metrics']['substitutions'] + hist_result['metrics']['insertions'] + hist_result['metrics']['deletions'])

                        st.audio(hist_result['audio_data'], format="audio/wav")

                # Export option
                if st.button("💾 Export History as JSON"):
                    export_data = []
                    for hist_result in st.session_state.analysis_history:
                        export_data.append({
                            'timestamp': hist_result['timestamp'].isoformat(),
                            'reference_text': hist_result['reference_text'],
                            'metrics': hist_result['metrics'],
                            'per_word_comparison': hist_result['per_word_comparison']
                        })

                    json_str = json.dumps(export_data, indent=2)
                    st.download_button(
                        label="Download JSON",
                        data=json_str,
                        file_name=f"accent_coach_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
            else:
                st.info("No analysis history yet. Record and analyze your first pronunciation!")


if __name__ == "__main__":
    main()
