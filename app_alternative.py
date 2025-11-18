#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Accent Coach AI - Alternative Implementation
Uses file upload instead of real-time recording to avoid browser compatibility issues
"""

import os
import io
import re
import tempfile
from datetime import datetime
from typing import List, Tuple, Dict, Optional
import json

import streamlit as st
import numpy as np
import pandas as pd
import torch
import torchaudio
import plotly.graph_objects as go
import plotly.express as px

from transformers import AutoProcessor, AutoModelForCTC
from phonemizer.punctuation import Punctuation
from sequence_align.pairwise import needleman_wunsch

try:
    from groq import Groq
    _HAS_GROQ = True
except Exception:
    _HAS_GROQ = False

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

PRACTICE_TEXTS = {
    "Beginner": [
        "The quick brown fox jumps over the lazy dog.",
        "How much wood would a woodchuck chuck if a woodchuck could chuck wood?",
        "She sells seashells by the seashore.",
        "A big black bug bit a big black dog on his big black nose.",
        "I saw a kitten eating chicken in the kitchen.",
    ],
    "Intermediate": [
        "Peter Piper picked a peck of pickled peppers.",
        "I scream, you scream, we all scream for ice cream.",
        "Six thick thistle sticks. Six thick thistles stick.",
        "Fuzzy Wuzzy was a bear. Fuzzy Wuzzy had no hair.",
        "How can a clam cram in a clean cream can?",
    ],
    "Advanced": [
        "The sixth sick sheikh's sixth sheep's sick.",
        "Pad kid poured curd pulled cod.",
        "Can you can a can as a canner can can a can?",
        "Red lorry, yellow lorry, red lorry, yellow lorry.",
        "Unique New York, you need New York, you know you need unique New York.",
    ],
    "Common Phrases": [
        "Could you please repeat that?",
        "I would like to make a reservation.",
        "What time does the meeting start?",
        "Thank you very much for your help.",
        "I'm sorry, I didn't understand.",
    ]
}

MODEL_OPTIONS = {
    "Wav2Vec2 Base (Fast, Cloud-Friendly)": "facebook/wav2vec2-base-960h",
    "Wav2Vec2 Large (Better Accuracy, Needs More RAM)": "facebook/wav2vec2-large-960h",
    "Wav2Vec2 XLSR (Phonetic)": "mrrubino/wav2vec2-large-xlsr-53-l2-arctic-phoneme",
}

# Default model - use Base for cloud deployments (smaller, faster)
DEFAULT_MODEL = "facebook/wav2vec2-base-960h"

# ============================================================================
# AUDIO PROCESSING FUNCTIONS
# ============================================================================

def load_audio_from_file(uploaded_file, target_sr: int = 16000) -> Tuple[np.ndarray, int]:
    """Load audio from uploaded file"""
    try:
        import soundfile as sf
        waveform, sr = sf.read(uploaded_file, dtype='float32')

        # Convert to mono if stereo
        if waveform.ndim > 1 and waveform.shape[1] > 1:
            waveform = waveform.mean(axis=1)

        # Resample if necessary
        if sr != target_sr:
            import librosa
            waveform = librosa.resample(waveform, orig_sr=sr, target_sr=target_sr)

        if waveform.ndim > 1:
            waveform = waveform.flatten()

        return waveform.astype(np.float32), target_sr
    except Exception as e:
        st.error(f"Failed to load audio: {e}")
        return None, None


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
# CACHED MODEL LOADING
# ============================================================================

@st.cache_resource
def load_asr_model(model_name: str, hf_token: Optional[str] = None):
    """Load and cache ASR model"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    kwargs = {}
    if hf_token:
        kwargs["token"] = hf_token

    with st.spinner(f"Loading model {model_name}..."):
        processor = AutoProcessor.from_pretrained(model_name, **kwargs)
        model = AutoModelForCTC.from_pretrained(model_name, **kwargs).to(device)

    return processor, model, device


# ============================================================================
# TRANSCRIPTION & ANALYSIS PIPELINE
# ============================================================================

def transcribe_audio(audio: np.ndarray, sr: int, processor, model, device,
                     use_g2p: bool = True, lang: str = "en-us") -> Tuple[str, str]:
    """Transcribe audio using ASR model"""
    inputs = processor(audio, sampling_rate=sr, return_tensors="pt", padding=True)

    with torch.no_grad():
        logits = model(inputs["input_values"].to(device)).logits

    ids = torch.argmax(logits, dim=-1)
    decoded = processor.batch_decode(ids)[0]

    recorded_phoneme_str = decoded

    # Apply G2P if needed
    if use_g2p:
        try:
            from gruut import sentences
            is_mostly_ascii = bool(re.match(r"^[\x00-\x7f\s\w\.,'\"\-]+$", decoded))

            if is_mostly_ascii:
                ph_parts = []
                for sent in sentences(decoded, lang=lang):
                    for w in sent:
                        try:
                            ph_parts.append(" ".join(w.phonemes))
                        except Exception:
                            ph_parts.append(w.text)

                recorded_phoneme_str = " ".join(ph_parts)
        except Exception as e:
            st.warning(f"G2P conversion failed: {e}")

    return decoded, recorded_phoneme_str


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

    total_phonemes = 0
    correct_phonemes = 0
    substitutions = 0
    insertions = 0
    deletions = 0

    for item in per_word_comparison:
        ref = item['ref_phonemes']
        rec = item['rec_phonemes']

        ref_chars = list(ref) if ref else []
        rec_chars = list(rec) if rec else []

        total_phonemes += len(ref_chars)

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


def process_audio_pipeline(uploaded_file, reference_text: str,
                           processor, model, device, use_g2p: bool,
                           use_llm: bool, groq_api_key: str, lang: str = "en-us") -> Dict:
    """Complete analysis pipeline"""
    # Load audio
    audio, sr = load_audio_from_file(uploaded_file)
    if audio is None:
        return None

    # Transcribe
    with st.spinner("Transcribing audio..."):
        raw_decoded, recorded_phoneme_str = transcribe_audio(
            audio, sr, processor, model, device, use_g2p, lang
        )

    # Generate reference
    with st.spinner("Generating reference phonemes..."):
        lexicon, ref_words = generate_reference_phonemes(reference_text, lang)

    # Align
    with st.spinner("Aligning sequences..."):
        rec_tokens = tokenize_phonemes(recorded_phoneme_str)
        per_word_ref, per_word_rec = align_per_word(lexicon, rec_tokens)

    # Build comparison
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

    # Calculate metrics
    metrics = calculate_metrics(per_word_comparison)

    # Get LLM feedback
    llm_feedback = None
    if use_llm and groq_api_key:
        with st.spinner("Getting AI coach feedback..."):
            llm_feedback = get_llm_feedback(reference_text, per_word_comparison, groq_api_key)

    # Save audio data
    uploaded_file.seek(0)
    audio_bytes = uploaded_file.read()

    return {
        'timestamp': datetime.now(),
        'audio_data': audio_bytes,
        'audio_array': audio,
        'sample_rate': sr,
        'reference_text': reference_text,
        'raw_decoded': raw_decoded,
        'recorded_phoneme_str': recorded_phoneme_str,
        'per_word_comparison': per_word_comparison,
        'llm_feedback': llm_feedback,
        'metrics': metrics,
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


# ============================================================================
# STREAMLIT APP
# ============================================================================

def init_session_state():
    """Initialize session state variables"""
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = []
    if 'current_result' not in st.session_state:
        st.session_state.current_result = None
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

    init_session_state()

    # Title
    st.title("🎙️ Accent Coach AI")
    st.markdown("Practice your American English pronunciation with AI-powered feedback")

    # Sidebar
    with st.sidebar:
        st.header("🎯 Practice Text Selection")

        category = st.selectbox("Category", list(PRACTICE_TEXTS.keys()))
        text_option = st.selectbox("Select a phrase", PRACTICE_TEXTS[category])

        use_custom = st.checkbox("Use custom text")
        if use_custom:
            custom_text = st.text_area("Enter your text:", value=text_option, height=100)
            reference_text = custom_text
        else:
            reference_text = text_option

        st.divider()

        with st.expander("⚙️ Advanced Settings"):
            model_choice = st.selectbox("ASR Model", list(MODEL_OPTIONS.keys()))
            st.session_state.config['model_name'] = MODEL_OPTIONS[model_choice]

            st.session_state.config['use_g2p'] = st.checkbox("Use G2P (Grapheme-to-Phoneme)", value=True)
            st.session_state.config['use_llm'] = st.checkbox("Enable LLM Feedback", value=True)
            st.session_state.config['lang'] = st.selectbox("Language", ["en-us"], index=0)

        st.divider()

        st.header("📊 System Info")

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

    # Main panel
    st.header("📝 Reference Text")
    st.markdown(f"### {reference_text}")
    st.caption(f"Length: {len(reference_text.split())} words")

    st.divider()

    # Upload section
    st.header("🎙️ Upload Your Audio Recording")

    st.info("""
    **How to record audio on your device:**

    - **Windows**: Use Voice Recorder app (built-in) or Audacity
    - **Mac**: Use QuickTime Player or Voice Memos
    - **Mobile**: Use your phone's voice recorder app
    - **Online**: Use https://online-voice-recorder.com/

    Upload the audio file (.wav, .mp3, .m4a, .flac, .ogg) below.
    """)

    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=['wav', 'mp3', 'm4a', 'flac', 'ogg', 'webm'],
        help="Upload your pronunciation recording"
    )

    if uploaded_file:
        st.success(f"✓ File uploaded: {uploaded_file.name}")
        st.audio(uploaded_file, format=f"audio/{uploaded_file.name.split('.')[-1]}")

        file_size = uploaded_file.size / 1024  # KB
        st.caption(f"File size: {file_size:.1f} KB")

        # Analysis button
        if st.button("🚀 Analyze Pronunciation", type="primary", use_container_width=True):
            processor, model, device = load_asr_model(
                st.session_state.config['model_name'],
                hf_token
            )

            result = process_audio_pipeline(
                uploaded_file,
                reference_text,
                processor,
                model,
                device,
                st.session_state.config['use_g2p'],
                st.session_state.config['use_llm'],
                groq_api_key,
                st.session_state.config['lang']
            )

            if result:
                st.session_state.current_result = result
                st.session_state.analysis_history.append(result)
                st.success("Analysis complete!")
                st.rerun()

    # Results display
    if st.session_state.current_result:
        st.divider()
        st.header("📊 Analysis Results")

        result = st.session_state.current_result

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

            metrics = result['metrics']
            col1, col2, col3 = st.columns(3)
            col1.metric("Word Accuracy", f"{metrics['word_accuracy']:.1f}%")
            col2.metric("Correct Words", f"{metrics['correct_words']}/{metrics['total_words']}")
            col3.metric("Phoneme Accuracy", f"{metrics['phoneme_accuracy']:.1f}%")

        with tab2:
            st.subheader("AI Coach Feedback")

            if result['llm_feedback']:
                st.markdown(result['llm_feedback'])

                if st.button("📋 Copy Feedback"):
                    st.code(result['llm_feedback'])
            else:
                st.info("LLM feedback is disabled. Enable it in Advanced Settings.")

        with tab3:
            st.subheader("Technical Analysis")

            st.markdown("#### Metrics")
            metrics = result['metrics']

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Word Accuracy", f"{metrics['word_accuracy']:.1f}%")
            col2.metric("Phoneme Accuracy", f"{metrics['phoneme_accuracy']:.1f}%")
            col3.metric("Phoneme Error Rate", f"{metrics['phoneme_error_rate']:.1f}%")
            col4.metric("Total Errors", metrics['substitutions'] + metrics['insertions'] + metrics['deletions'])

            st.markdown("#### Error Distribution")
            fig = plot_error_distribution(metrics)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### Audio Waveform")
            fig_wave = plot_waveform(result['audio_array'], result['sample_rate'])
            st.plotly_chart(fig_wave, use_container_width=True)

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

                        st.audio(hist_result['audio_data'])

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
                st.info("No analysis history yet. Upload and analyze your first recording!")


if __name__ == "__main__":
    main()
