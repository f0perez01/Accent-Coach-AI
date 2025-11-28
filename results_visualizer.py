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
    def render_ipa_guide(text: str, ipa_defs_manager, tts_generator, lang: str = "en-us"):
        """Render interactive IPA pronunciation guide with word breakdown and audio.
        
        Args:
            text: Reference text to break down
            ipa_defs_manager: IPADefinitionsManager instance
            tts_generator: TTSGenerator instance
            lang: Language code (default 'en-us')
        """
        from gruut import sentences
        
        # 1. Process text
        breakdown_data = []
        unique_symbols = set()
        
        clean_text = Punctuation(';:,.!?"()').remove(text)
        word_counter = 0 
        
        for sent in sentences(clean_text, lang=lang):
            for w in sent:
                word_text = w.text
                try:
                    phonemes_list = w.phonemes
                    phoneme_str = "".join(phonemes_list)
                    
                    # Collect symbols for glossary
                    for p in phonemes_list:
                        clean_p = p.replace("ˈ", "").replace("ˌ", "")
                        if ipa_defs_manager.get_definition(clean_p):
                            unique_symbols.add(clean_p)
                        elif ipa_defs_manager.get_definition(p):
                            unique_symbols.add(p)

                    # Get hints
                    hints = []
                    for p in phonemes_list:
                        clean_p = p.replace("ˈ", "").replace("ˌ", "")
                        definition = ipa_defs_manager.get_definition(clean_p)
                        if definition:
                            desc = definition.split('(')[0].strip()
                            hints.append(desc)
                    
                    hint_str = " + ".join(hints[:3])
                    if len(hints) > 3: hint_str += "..."

                    # Generate audio for word
                    word_audio = tts_generator.generate_audio(word_text, lang=lang)

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

        # 2. Render UI
        with st.expander("📖 Guía de Pronunciación Paso a Paso (Decodificador)", expanded=False):
            
            tab1, tab2 = st.tabs(["🧩 Desglose por Palabra", "📚 Glosario de Símbolos"])
            
            with tab1:
                st.markdown("#### 🕵️‍♀️ Práctica de Drilling")
                st.markdown("Escucha y repite palabra por palabra:")
                
                # Headers
                h1, h2, h3, h4 = st.columns([1.5, 1.5, 2.5, 1.5])
                h1.markdown("**Palabra**")
                h2.markdown("**IPA**")
                h3.markdown("**Pista**")
                h4.markdown("**Audio**")
                
                st.divider()
                
                # Rows
                if breakdown_data:
                    for item in breakdown_data:
                        c1, c2, c3, c4 = st.columns([1.5, 1.5, 2.5, 1.5])
                        
                        with c1:
                            st.markdown(f"### {item['word']}")
                        
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
                        
                        st.markdown("<hr style='margin: 5px 0; opacity: 0.2;'>", unsafe_allow_html=True)
                else:
                    st.warning("No se pudo procesar el desglose fonético.")

            with tab2:
                st.markdown("#### 🗝️ Símbolos Clave")
                st.markdown("Glosario de símbolos encontrados en esta frase:")

                cols = st.columns(2)
                for i, sym in enumerate(sorted(unique_symbols)):
                    definition = ipa_defs_manager.get_definition(sym) or "Sonido específico"
                    with cols[i % 2]:
                        st.info(f"**{sym}** : {definition}")
