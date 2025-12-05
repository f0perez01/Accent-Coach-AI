"""
Advanced Settings Component

Provides configuration UI for ASR models, audio enhancement, and other settings.
Migrated from app.py lines 879-927 with improvements.
"""

import streamlit as st
from typing import Dict, Optional


class AdvancedSettings:
    """Component for rendering advanced settings in sidebar."""

    # ASR Model options
    MODEL_OPTIONS = {
        "Wav2Vec2 Base (Fast, Cloud-Friendly)": "facebook/wav2vec2-base-960h",
        "Wav2Vec2 Large (Better Accuracy, Needs More RAM)": "facebook/wav2vec2-large-960h",
        "Wav2Vec2 XLSR (Phonetic)": "mrrubino/wav2vec2-large-xlsr-53-l2-arctic-phoneme",
    }

    # Language options
    LANGUAGE_OPTIONS = ["en-us"]

    @staticmethod
    def render(config: Optional[Dict] = None) -> Dict:
        """
        Render advanced settings UI.

        Args:
            config: Current configuration dict (optional, reads from session_state if None)

        Returns:
            Updated configuration dict
        """
        # Get current config from session_state if not provided
        if config is None:
            if 'config' not in st.session_state:
                st.session_state.config = AdvancedSettings._get_default_config()
            config = st.session_state.config

        with st.expander("⚙️ Advanced Settings", expanded=False):
            st.markdown("### 🎙️ Speech Recognition")

            # ASR Model selection
            current_model_name = config.get('model_name', 'facebook/wav2vec2-base-960h')
            current_model_label = AdvancedSettings._get_model_label(current_model_name)

            model_choice = st.selectbox(
                "ASR Model",
                list(AdvancedSettings.MODEL_OPTIONS.keys()),
                index=list(AdvancedSettings.MODEL_OPTIONS.values()).index(current_model_name)
                if current_model_name in AdvancedSettings.MODEL_OPTIONS.values()
                else 0,
                help="Choose the speech recognition model. Base is faster, Large is more accurate."
            )
            config['model_name'] = AdvancedSettings.MODEL_OPTIONS[model_choice]

            # G2P and LLM options
            col1, col2 = st.columns(2)

            with col1:
                config['use_g2p'] = st.checkbox(
                    "Use G2P",
                    value=config.get('use_g2p', True),
                    help="Grapheme-to-Phoneme conversion for better phonetic analysis"
                )

            with col2:
                config['use_llm'] = st.checkbox(
                    "Enable LLM Feedback",
                    value=config.get('use_llm', True),
                    help="Get AI-powered personalized feedback (requires Groq API)"
                )

            # Language selection
            config['lang'] = st.selectbox(
                "Language",
                AdvancedSettings.LANGUAGE_OPTIONS,
                index=AdvancedSettings.LANGUAGE_OPTIONS.index(config.get('lang', 'en-us'))
                if config.get('lang', 'en-us') in AdvancedSettings.LANGUAGE_OPTIONS
                else 0,
                help="Target language for pronunciation practice"
            )

            st.divider()

            # Audio Enhancement section
            st.markdown("### 🎛️ Audio Enhancement")

            config['enable_enhancement'] = st.checkbox(
                "Enable Audio Enhancement",
                value=config.get('enable_enhancement', True),
                help="Improves ASR accuracy with denoising and Voice Activity Detection"
            )

            # Conditional enhancement options
            if config['enable_enhancement']:
                col1, col2 = st.columns(2)

                with col1:
                    config['enable_vad'] = st.checkbox(
                        "Voice Activity Detection",
                        value=config.get('enable_vad', True),
                        help="Automatically trim silence from audio recordings"
                    )

                    config['show_quality_metrics'] = st.checkbox(
                        "Show Quality Metrics",
                        value=config.get('show_quality_metrics', False),
                        help="Display audio quality analysis (SNR, duration, etc.)"
                    )

                with col2:
                    config['enable_denoising'] = st.checkbox(
                        "Noise Reduction",
                        value=config.get('enable_denoising', True),
                        help="Remove background noise from recordings"
                    )
            else:
                # Set defaults when enhancement is disabled
                config['enable_vad'] = False
                config['enable_denoising'] = False
                config['show_quality_metrics'] = False

            # Info message
            if config['enable_enhancement']:
                st.info("💡 Audio enhancement is active. Your recordings will be automatically improved.")
            else:
                st.warning("⚠️ Audio enhancement is disabled. Raw audio will be used.")

        # Update session state
        st.session_state.config = config

        return config

    @staticmethod
    def _get_default_config() -> Dict:
        """
        Get default configuration.

        Returns:
            Default configuration dict
        """
        return {
            'model_name': 'facebook/wav2vec2-base-960h',
            'use_g2p': True,
            'use_llm': True,
            'lang': 'en-us',
            'enable_enhancement': True,
            'enable_vad': True,
            'enable_denoising': True,
            'show_quality_metrics': False,
        }

    @staticmethod
    def _get_model_label(model_name: str) -> str:
        """
        Get display label for model name.

        Args:
            model_name: Model identifier

        Returns:
            Display label or model name if not found
        """
        for label, name in AdvancedSettings.MODEL_OPTIONS.items():
            if name == model_name:
                return label
        return model_name

    @staticmethod
    def get_model_display_name(model_name: str) -> str:
        """
        Get friendly display name for model.

        Args:
            model_name: Model identifier

        Returns:
            Friendly display name
        """
        model_map = {
            'facebook/wav2vec2-base-960h': 'Wav2Vec2 Base',
            'facebook/wav2vec2-large-960h': 'Wav2Vec2 Large',
            'mrrubino/wav2vec2-large-xlsr-53-l2-arctic-phoneme': 'Wav2Vec2 XLSR (Phonetic)',
        }
        return model_map.get(model_name, model_name.split('/')[-1])


# Convenience function for backward compatibility
def render_advanced_settings(config: Optional[Dict] = None) -> Dict:
    """
    Render advanced settings UI.

    Args:
        config: Current configuration dict (optional)

    Returns:
        Updated configuration dict
    """
    return AdvancedSettings.render(config)
