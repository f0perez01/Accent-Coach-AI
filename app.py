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
from typing import List, Dict, Optional
import json
import base64
from st_pronunciation_widget import streamlit_pronunciation_widget
from syllabifier import phonemes_to_syllables_with_fallback
import streamlit.components.v1 as components

import streamlit as st
import numpy as np
import pandas as pd
import torch
import plotly.graph_objects as go
import plotly.express as px
import requests
import extra_streamlit_components as stx

# NOTE: Punctuation and needleman_wunsch imports removed - now handled by PhonemeProcessor and AnalysisPipeline
from asr_model import ASRModelManager
from practice_texts import PracticeTextManager
from ipa_definitions import IPADefinitionsManager
from audio_processor import AudioProcessor, TTSGenerator, AudioValidator
from auth_manager import AuthManager
from groq_manager import GroqManager
from session_manager import SessionManager
from metrics_calculator import MetricsCalculator
from results_visualizer import ResultsVisualizer
from analysis_pipeline import AnalysisPipeline
from conversation_tutor import ConversationTutor, ConversationSession
from conversation_manager import ConversationManager
from prompt_templates import ConversationPromptTemplate, ConversationStarters
from phoneme_processor import PhonemeProcessor

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

# Initialize Auth Manager (global instance)
auth_manager = AuthManager(st.secrets if hasattr(st, 'secrets') else None)

# Initialize Groq/LLM manager
groq_manager = GroqManager()

# NOTE: SessionManager will be instantiated in main() after functions are defined

# ============================================================================
# FIREBASE AUTHENTICATION & DATABASE
# ============================================================================

# NOTE: The following functions now delegate to manager classes:
# - login_user() -> delegates to auth_manager
# - register_user() -> delegates to auth_manager
# - get_user_analyses() -> delegates to auth_manager
# - save_analysis_to_firestore() -> delegates to auth_manager
# - calculate_metrics() -> delegates to MetricsCalculator
# - plot_waveform(), display_comparison_table(), plot_error_distribution(), render_ipa_guide_component()
#   -> use ResultsVisualizer static methods

def init_firebase():
    """Initialize Firebase Admin SDK (delegates to AuthManager)"""
    try:
        auth_manager.init_firebase()
    except Exception:
        # If initialization fails or firebase not available, ignore gracefully
        pass

def get_db():
    """Get Firestore database client (delegates to AuthManager)"""
    return auth_manager.get_db()

def login_user(email: str, password: str) -> dict:
    """Login user with Firebase Authentication (delegates to AuthManager)"""
    return auth_manager.login_user(email, password)

def register_user(email: str, password: str) -> dict:
    """Register new user with Firebase Authentication (delegates to AuthManager)"""
    return auth_manager.register_user(email, password)

def save_analysis_to_firestore(user_id: str, reference_text: str, result: dict):
    """Save pronunciation analysis to Firestore (delegates to AuthManager)"""
    return auth_manager.save_analysis_to_firestore(user_id, reference_text, result)

def get_user_analyses(user_id: str) -> list:
    """Get user's pronunciation analysis history from Firestore (delegates to AuthManager)"""
    return auth_manager.get_user_analyses(user_id)


# NOTE: align_sequences and align_per_word have been moved to AnalysisPipeline
# These functions are no longer needed in app.py as they are duplicates


# ============================================================================
# TRANSCRIPTION & ANALYSIS PIPELINE
# ============================================================================

# NOTE: generate_reference_phonemes and prepare_pronunciation_widget_data
# have been moved to PhonemeProcessor class for better separation of concerns


def get_llm_feedback(reference_text: str, per_word_comparison: List[Dict],
                     groq_api_key: str) -> Optional[str]:
    """Get accent coaching feedback via `groq_manager` wrapper.

    This function keeps the original signature for backwards compatibility
    but delegates the actual LLM work to `groq_manager`.
    """
    try:
        if groq_api_key:
            groq_manager.set_api_key(groq_api_key)
        return groq_manager.get_feedback(reference_text, per_word_comparison)
    except Exception as e:
        st.error(f"LLM feedback failed: {e}")
        return None


def calculate_metrics(per_word_comparison: List[Dict]) -> Dict:
    """Calculate pronunciation accuracy metrics (delegates to MetricsCalculator)"""
    return MetricsCalculator.calculate(per_word_comparison)


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def plot_waveform(audio: np.ndarray, sr: int, title: str = "Audio Waveform"):
    """Plot audio waveform using plotly (delegates to ResultsVisualizer)"""
    return ResultsVisualizer.plot_waveform(audio, sr, title)


def display_comparison_table(per_word_comparison: List[Dict], show_only_errors: bool = False):
    """Display word-by-word comparison table (delegates to ResultsVisualizer)"""
    return ResultsVisualizer.display_comparison_table(per_word_comparison, show_only_errors)


def plot_error_distribution(metrics: Dict):
    """Plot error type distribution (delegates to ResultsVisualizer)"""
    return ResultsVisualizer.plot_error_distribution(metrics)

# NOTE: render_ipa_guide_component has been moved to ResultsVisualizer.render_ipa_guide
# Data preparation moved to PhonemeProcessor.create_ipa_guide_data


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
            'lang': 'en-us',
            # Audio enhancement settings
            'enable_enhancement': True,
            'enable_vad': True,
            'enable_denoising': True,
            'show_quality_metrics': False
        }
    # Conversation tutor state
    if 'conversation_session' not in st.session_state:
        st.session_state.conversation_session = None
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'conversation_mode' not in st.session_state:
        st.session_state.conversation_mode = 'practice'  # 'practice' or 'exam'


def render_conversation_tutor(user: dict, groq_api_key: str):
    """
    Render the Conversation Tutor interface for voice-based ESL practice.

    Args:
        user: User dict from authentication
        groq_api_key: Groq API key for LLM
    """
    st.header("🗣️ Conversation Practice Tutor")
    st.markdown("Practice natural English conversation with AI-powered feedback and guidance")

    # Initialize managers
    conversation_manager = ConversationManager(auth_manager)
    conversation_tutor = ConversationTutor(groq_manager, asr_manager, AudioProcessor)

    # Session setup
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        topic = st.selectbox(
            "📚 Conversation Topic",
            ConversationStarters.get_topics(),
            help="Choose a topic to practice"
        )

    with col2:
        level = st.selectbox(
            "🎯 Your Level",
            ["A2", "B1-B2", "C1-C2"],
            index=1,
            help="Your current English proficiency level"
        )

    with col3:
        mode = st.selectbox(
            "Mode",
            ["Practice", "Exam"],
            help="Practice: Get immediate feedback | Exam: Feedback at the end"
        )
        st.session_state.conversation_mode = mode.lower()

    st.divider()

    # New Session / Continue
    if st.session_state.conversation_session is None:
        st.info("🎬 Start a new conversation session")

        # Show conversation starter
        starter_question = ConversationStarters.get_starter(topic, level)
        st.markdown(f"**Tutor:** {starter_question}")

        # Play TTS for starter
        try:
            starter_audio = TTSGenerator.generate_audio(starter_question)
            if starter_audio:
                st.audio(starter_audio, format="audio/mp3")
        except:
            pass

        if st.button("🚀 Start Conversation", type="primary"):
            # Create session
            session_id = f"conv_{user['localId']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.session_state.conversation_session = ConversationSession(
                session_id=session_id,
                user_id=user['localId'],
                topic=topic
            )
            st.session_state.conversation_history = []
            st.rerun()

    else:
        # Active conversation session
        session = st.session_state.conversation_session

        st.success(f"📖 Active Session: {session.topic}")

        # Display conversation history using ResultsVisualizer (pure UI, no logic)
        ResultsVisualizer.render_conversation_history(
            st.session_state.conversation_history,
            st.session_state.conversation_mode,
            TTSGenerator
        )

        # Recording section
        st.subheader("🎙️ Your Turn")
        st.caption("Speak naturally. Answer the tutor's question or continue the conversation.")

        audio_bytes = st.audio_input("Record your response")

        if audio_bytes:
            st.success("✓ Recording captured!")

            # Show playback
            audio_data = audio_bytes.getvalue() if hasattr(audio_bytes, "getvalue") else audio_bytes
            st.audio(audio_data, format="audio/wav")

            if st.button("🚀 Send & Get Feedback", type="primary", use_container_width=True):
                with st.spinner("🧠 Analyzing your speech..."):
                    # Load ASR model if needed
                    try:
                        hf_token = st.secrets.get("HF_API_TOKEN", os.environ.get("HF_API_TOKEN"))
                        asr_manager.load_model(
                            st.session_state.config['model_name'],
                            hf_token
                        )
                    except Exception as e:
                        st.error(f"Failed to load ASR model: {e}")
                        st.stop()

                    # Process speech
                    result = conversation_tutor.process_user_speech(
                        audio_data=audio_data,
                        conversation_history=st.session_state.conversation_history,
                        user_level=level
                    )

                    if 'error' in result:
                        st.error(result['error'])
                    else:
                        # Record turn atomically (session state + session object + Firestore)
                        conversation_manager.record_turn(
                            session=session,
                            turn_data=result,
                            user_id=user['localId']
                        )

                        # Show response
                        st.success("✅ Response received!")

                        # Display feedback
                        if st.session_state.conversation_mode == 'practice':
                            st.markdown("### 📝 Feedback")

                            col1, col2 = st.columns(2)

                            with col1:
                                st.markdown(f"**You said:** {result['user_transcript']}")
                                if result.get('correction'):
                                    st.markdown(f"**Correction:** {result['correction']}")
                                if result.get('improved_version'):
                                    st.info(f"✅ Better: {result['improved_version']}")

                            with col2:
                                if result.get('explanation'):
                                    st.markdown(f"**Explanation:**\n{result['explanation']}")

                        # Show tutor's follow-up
                        if result.get('follow_up_question'):
                            st.markdown("---")
                            st.markdown(f"### 🤖 Tutor's Next Question")

                            # Display question with audio player
                            st.info(f"**{result['follow_up_question']}**")

                            # Play TTS - prioritize dedicated follow_up_audio
                            follow_up_audio = result.get('follow_up_audio')
                            audio_response = result.get('audio_response')

                            if follow_up_audio is not None and len(follow_up_audio) > 0:
                                try:
                                    st.audio(follow_up_audio, format="audio/mp3")
                                except Exception as e:
                                    st.caption(f"🔊 Audio playback error: {e}")
                            elif audio_response is not None and len(audio_response) > 0:
                                try:
                                    st.audio(audio_response, format="audio/mp3")
                                except Exception as e:
                                    st.caption(f"🔊 Audio playback error: {e}")
                            else:
                                st.caption("🔊 Audio not available")

                        st.rerun()

        # Session controls
        st.divider()
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📊 Session Stats"):
                stats = session.get_session_stats()
                st.json(stats)

        with col2:
            if st.button("💾 Export Session"):
                transcript = conversation_manager.export_session_to_text(session.session_id)
                st.download_button(
                    label="Download Transcript",
                    data=transcript,
                    file_name=f"conversation_{session.session_id}.txt",
                    mime="text/plain"
                )

        with col3:
            if st.button("🔚 End Session", type="secondary"):
                conversation_manager.close_session(session.session_id)
                st.session_state.conversation_session = None
                st.session_state.conversation_history = []
                st.success("Session ended!")
                st.rerun()


def main():
    st.set_page_config(
        page_title="Accent Coach AI",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    init_firebase()
    init_session_state()

    # Initialize SessionManager with callbacks (including save_analysis)
    session_mgr = SessionManager(
        login_user,
        register_user,
        get_user_analyses,
        save_analysis_callback=save_analysis_to_firestore
    )

    # Initialize AnalysisPipeline with manager dependencies
    analysis_pipeline = AnalysisPipeline(
        asr_manager=asr_manager,
        groq_manager=groq_manager,
        audio_processor=AudioProcessor,
        ipa_defs_manager=IPADefinitionsManager
    )

    # --- AUTH FLOW ---
    should_return, _ = session_mgr.render_login_ui()
    if should_return:
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

        # Use SessionManager to render history selector
        reference_text, selected_history = session_mgr.render_user_info_and_history(user)

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
            st.markdown("**Audio Enhancement**")
            st.session_state.config['enable_enhancement'] = st.checkbox(
                "Enable Audio Enhancement",
                value=True,
                help="Improves ASR accuracy with denoising and VAD"
            )
            if st.session_state.config['enable_enhancement']:
                st.session_state.config['enable_vad'] = st.checkbox(
                    "Voice Activity Detection",
                    value=True,
                    help="Trim silence from audio"
                )
                st.session_state.config['enable_denoising'] = st.checkbox(
                    "Noise Reduction",
                    value=True,
                    help="Remove background noise"
                )
                st.session_state.config['show_quality_metrics'] = st.checkbox(
                    "Show Quality Metrics",
                    value=False,
                    help="Display audio quality analysis"
                )

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

        # Configure Groq manager with key if available
        if groq_api_key and _HAS_GROQ:
            groq_manager.set_api_key(groq_api_key)
            st.success("✓ Groq API Connected")
        else:
            st.warning("⚠ Groq API Not Available")

        # LLM controls
        with st.expander("🧠 LLM / Groq Settings", expanded=False):
            llm_model = st.selectbox("LLM Model", [groq_manager.model, "llama-3.1-8b-instant", "gpt-4o-mini"], index=0 if groq_manager.model else 1)
            llm_temp = st.slider("Temperature", min_value=0.0, max_value=1.0, value=float(groq_manager.temperature or 0.0), step=0.05)
            groq_manager.model = llm_model
            groq_manager.temperature = float(llm_temp)

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
                    st.error(f"❌ Model download failed! Error: {str(e)[:300]}")
                    st.warning("💡 Try Clear cache (button below), Use 'Wav2Vec2 Base' model, Check your internet connection")

        # Clear cache button
        if st.button("🗑️ Clear Model Cache", help="Clear cached models to free up space"):
            st.cache_resource.clear()
            st.success("✓ Cache cleared! Page will reload.")
            st.rerun()

        st.divider()

        # Use SessionManager for logout
        session_mgr.render_logout_button()

    # Main panel - Add tabs for different modes
    main_tab1, main_tab2 = st.tabs(["🎯 Pronunciation Practice", "🗣️ Conversation Tutor"])

    with main_tab1:
        # PRONUNCIATION PRACTICE MODE
        st.header("📝 Reference Text")
        st.markdown(f"### {reference_text}")
        st.caption(f"Length: {len(reference_text.split())} words")

        # --- STUDY PHASE ---
        # 1. Generate Data using PhonemeProcessor
        with st.spinner("Preparing study materials..."):
            # Use PhonemeProcessor for all phoneme-related operations
            lexicon, _ = PhonemeProcessor.generate_reference_phonemes(
                reference_text, st.session_state.config['lang']
            )
            widget_data = PhonemeProcessor.prepare_widget_data(reference_text, lexicon)
            phoneme_text = widget_data["phoneme_text"]
            word_timings = widget_data["word_timings"]
            tts_audio = TTSGenerator.generate_audio(reference_text)

        # 2. Render Karaoke Player
        if tts_audio:
            b64_audio = base64.b64encode(tts_audio).decode()

            # Generate syllables automatically from phoneme text
            syllable_timings = None
            try:
                syllables = phonemes_to_syllables_with_fallback(phoneme_text)
                if syllables:
                    syllable_timings = syllables
            except Exception as e:
                st.warning(f"Could not generate syllables: {e}")

            streamlit_pronunciation_widget(
                reference_text,
                phoneme_text,
                b64_audio,
                word_timings=word_timings,
                syllable_timings=syllable_timings
            )

            # === IPA GUIDE (using new architecture) ===
            st.markdown("---")

            # Generate IPA guide data using PhonemeProcessor
            breakdown_data, unique_symbols = PhonemeProcessor.create_ipa_guide_data(
                reference_text, st.session_state.config['lang']
            )

            # Render using ResultsVisualizer (pure UI, no logic)
            ResultsVisualizer.render_ipa_guide(breakdown_data, unique_symbols, IPADefinitionsManager)
            # ==========================================

        else:
            st.info(f"**IPA:** /{phoneme_text}/")
            st.warning("Audio generation failed.")
    
        st.divider()
    
        # Recording section
        st.header("🎙️ Record Your Pronunciation")
    
        st.markdown("**Click below to record your pronunciation**")
        st.caption(f"{reference_text}")
            
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
                # Step 1: Load ASR model
                try:
                    asr_manager.load_model(
                        st.session_state.config['model_name'],
                        hf_token
                    )
                except Exception as e:
                    st.error(f"Failed to load ASR model: {e}")
                    st.stop()
    
                # Convert audio_bytes to bytes if it's a file-like object
                audio_data = audio_bytes.getvalue() if hasattr(audio_bytes, 'getvalue') else audio_bytes
    
                # Step 2: Use AnalysisPipeline to orchestrate the entire workflow
                result = analysis_pipeline.run(
                    audio_data,
                    reference_text,
                    use_g2p=st.session_state.config['use_g2p'],
                    use_llm=st.session_state.config['use_llm'],
                    lang=st.session_state.config['lang']
                )

                # Step 3: Save analysis using SessionManager (encapsulates state + persistence)
                if result:
                    session_mgr.save_analysis(user['localId'], reference_text, result)
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
    
    

    with main_tab2:
        # CONVERSATION TUTOR MODE
        render_conversation_tutor(user, groq_api_key)

if __name__ == "__main__":
    main()
