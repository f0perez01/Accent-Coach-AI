"""
Pronunciation Practice Controller
"""

import streamlit as st


class PronunciationController:
    """
    Controller: UI → PronunciationPracticeService

    Responsibilities:
    - Handle UI events (button clicks, file uploads)
    - Extract config from session state
    - Call service methods
    - Update UI state

    NO business logic here!
    """

    def __init__(self, practice_service, activity_tracker):
        """
        Args:
            practice_service: PronunciationPracticeService instance
            activity_tracker: ActivityTracker instance
        """
        self._service = practice_service
        self._tracker = activity_tracker

    def handle_recording_analysis(
        self, audio_bytes: bytes, reference_text: str, user_id: str
    ):
        """
        Handle user recording analysis.

        Args:
            audio_bytes: Recorded audio
            reference_text: Text to practice
            user_id: User identifier
        """
        # TODO: Implementation in Sprint 4
        # 1. Get config from session state
        # 2. Call service.analyze_recording()
        # 3. Track activity
        # 4. Update UI state (st.session_state)
        st.info("To be implemented in Sprint 4")
