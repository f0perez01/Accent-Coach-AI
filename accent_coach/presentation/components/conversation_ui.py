"""
Conversation Tutor UI Components
"""

import streamlit as st


class ConversationUI:
    """
    Pure UI components for conversation tutor.

    NO business logic - only rendering.
    """

    @staticmethod
    def render_conversation_history(history, mode, tts_generator):
        """
        Render conversation history.

        Args:
            history: List of conversation turns
            mode: practice or exam
            tts_generator: TTS generator for playback
        """
        # TODO: Migrate from results_visualizer.py in Sprint 7
        st.info("To be migrated in Sprint 7")
