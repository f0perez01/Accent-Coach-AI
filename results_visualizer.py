from typing import List, Dict
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from phonemizer.punctuation import Punctuation


class ResultsVisualizer:
    """Encapsulates all visualization and UI rendering for analysis results.
    
    Responsibilities:
    - Plot audio waveforms
    - Display word-by-word comparison tables with styling
    - Plot error distribution charts
    - Render IPA pronunciation guide with audio
    """

    @staticmethod
    def plot_waveform(audio: np.ndarray, sr: int, title: str = "Audio Waveform"):
        """Plot audio waveform using plotly."""
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

    @staticmethod
    def display_comparison_table(per_word_comparison: List[Dict], show_only_errors: bool = False):
        """Display word-by-word comparison table with color coding."""
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
            idx = row.name
            is_match = df.loc[idx, 'match'] if idx in df.index else False
            if not is_match:
                return ['background-color: #ffebee'] * len(row)
            else:
                return ['background-color: #e8f5e9'] * len(row)

        # Apply styling
        styled_df = display_df.style.apply(highlight_errors, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=400)

    @staticmethod
    def plot_error_distribution(metrics: Dict):
        """Plot error type distribution chart."""
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

    @staticmethod
    def render_ipa_guide(breakdown_data: List[Dict], unique_symbols: set, ipa_defs_manager, tts_generator):
        """
        Renderiza la guía educativa interactiva y permite seleccionar palabras para práctica enfocada.

        Args:
            breakdown_data: List of dicts with {index, word, ipa, hint, audio}
            unique_symbols: Set of unique IPA symbols found in the text
            ipa_defs_manager: IPADefinitionsManager instance for symbol definitions
            tts_generator: TTSGenerator class for creating audio for selected words

        Returns:
            str or None: Cadena con palabras seleccionadas unidas por espacios, o None si no hay selección
        """
        selected_words = []

        with st.expander("📖 Guía de Pronunciación y Práctica Selectiva", expanded=False):

            tab1, tab2 = st.tabs(["🧩 Desglose y Selección", "📚 Glosario de Símbolos"])

            with tab1:
                st.markdown("#### 🕵️‍♀️ Práctica de Drilling Enfocado")
                st.info("✅ Selecciona las palabras difíciles para practicar solo esa combinación.")

                # Headers de la tabla
                h0, h1, h2, h3, h4 = st.columns([0.5, 1.5, 1.5, 2.5, 1.5])
                h0.markdown("**✅**")
                h1.markdown("**Palabra**")
                h2.markdown("**IPA**")
                h3.markdown("**Pista**")
                h4.markdown("**Audio**")

                st.divider()

                # Rows con checkboxes
                if breakdown_data:
                    for i, item in enumerate(breakdown_data):
                        c0, c1, c2, c3, c4 = st.columns([0.5, 1.5, 1.5, 2.5, 1.5])

                        with c0:
                            # Checkbox para seleccionar la palabra
                            if st.checkbox("Select", key=f"sel_word_{i}", label_visibility="collapsed"):
                                selected_words.append(item['word'])

                        with c1:
                            # Resaltar si está seleccionado
                            if item['word'] in selected_words:
                                st.markdown(f"**🎯 {item['word']}**")
                            else:
                                st.markdown(item['word'])

                        with c2:
                            st.code(item['ipa'], language=None)

                        with c3:
                            if item['hint']:
                                st.caption(f"💡 {item['hint']}")
                            else:
                                st.caption("-")

                        with c4:
                            if item['audio']:
                                st.audio(item['audio'], format="audio/mp3")

                        st.markdown("<hr style='margin: 5px 0; opacity: 0.1;'>", unsafe_allow_html=True)
                else:
                    st.warning("No se pudo procesar el desglose fonético.")

                # --- Zona de Acción para la Selección ---
                if selected_words:
                    st.divider()
                    st.markdown("### 🎯 Práctica Enfocada")
                    subset_text = " ".join(selected_words)

                    st.markdown(f"**Objetivo actual:** `{subset_text}`")

                    if st.button("🔊 Escuchar Secuencia Seleccionada", type="primary", use_container_width=True):
                        try:
                            # Generar audio al vuelo para la combinación de palabras
                            combined_audio = tts_generator.generate_audio(subset_text)
                            if combined_audio:
                                st.audio(combined_audio, format="audio/mp3")
                            else:
                                st.warning("No se pudo generar audio para la selección")
                        except Exception as e:
                            st.error(f"Error generando audio: {e}")

                    return subset_text

            with tab2:
                st.markdown("#### 🗝️ Símbolos Clave")
                st.markdown("Glosario de símbolos encontrados en esta frase:")

                cols = st.columns(2)
                for i, sym in enumerate(sorted(unique_symbols)):
                    definition = ipa_defs_manager.get_definition(sym) or "Sonido específico"
                    with cols[i % 2]:
                        st.info(f"**{sym}** : {definition}")

        # Si no hay selección, retornamos None
        return None

    @staticmethod
    def render_conversation_history(conversation_history: List[Dict], conversation_mode: str, tts_generator):
        """
        Render conversation history with feedback and audio playback.

        Args:
            conversation_history: List of conversation turns
            conversation_mode: 'practice' or 'exam'
            tts_generator: TTSGenerator class for audio generation
        """
        if not conversation_history:
            return

        with st.expander("💬 Conversation History", expanded=True):
            for i, turn in enumerate(conversation_history, 1):
                st.markdown(f"**Turn {i}:**")

                col_a, col_b = st.columns([1, 1])

                with col_a:
                    st.markdown(f"🧑 **You:** {turn.get('user_transcript', '')}")

                with col_b:
                    if conversation_mode == 'practice':
                        if turn.get('correction'):
                            st.markdown(f"✏️ **Correction:** {turn.get('correction', '')}")
                        if turn.get('explanation'):
                            st.markdown(f"📚 {turn.get('explanation', '')}")

                if turn.get('follow_up_question'):
                    st.markdown(f"🤖 **Tutor:** {turn.get('follow_up_question', '')}")

                    # Play audio if available
                    follow_up_audio = turn.get('follow_up_audio')
                    if follow_up_audio is not None and len(follow_up_audio) > 0:
                        try:
                            st.audio(follow_up_audio, format="audio/mp3")
                        except Exception:
                            # If audio playback fails, show button to regenerate
                            if st.button("🔊 Listen", key=f"listen_turn_{i}_err", help="Generate audio for question"):
                                try:
                                    question_audio = tts_generator.generate_audio(turn.get('follow_up_question', ''))
                                    if question_audio:
                                        st.audio(question_audio, format="audio/mp3")
                                except Exception as e:
                                    st.warning(f"Could not generate audio: {e}")
                    else:
                        # Fallback: show button to generate on demand
                        if st.button("🔊 Listen", key=f"listen_turn_{i}", help="Listen to tutor's question"):
                            try:
                                question_audio = tts_generator.generate_audio(turn.get('follow_up_question', ''))
                                if question_audio:
                                    st.audio(question_audio, format="audio/mp3")
                            except Exception as e:
                                st.warning(f"Could not generate audio: {e}")

                st.divider()
