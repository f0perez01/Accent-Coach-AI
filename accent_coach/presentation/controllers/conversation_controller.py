"""
Conversation Tutor Controller
"""

import streamlit as st


class ConversationController:
    """
    Controller: UI → ConversationTutorService

    Responsibilities:
    - Handle conversation turns
    - Manage session state
    - Update UI

    NO business logic here!
    """

    def __init__(self, tutor_service, activity_tracker):
        """
        Args:
            tutor_service: ConversationTutorService instance
            activity_tracker: ActivityTracker instance
        """
        self._service = tutor_service
        self._tracker = activity_tracker

    def handle_turn(self, audio_bytes: bytes, session_id: str, user_id: str):
        """
        Handle conversation turn.

        Args:
            audio_bytes: User's audio response
            session_id: Conversation session ID
            user_id: User identifier
        """
        # TODO: Implementation in Sprint 5
        st.info("To be implemented in Sprint 5")
