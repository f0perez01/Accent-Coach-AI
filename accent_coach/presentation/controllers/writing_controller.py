"""
Writing Coach Controller
"""

import streamlit as st


class WritingController:
    """
    Controller: UI → WritingCoachService

    Responsibilities:
    - Handle writing evaluation requests
    - Update UI state

    NO business logic here!
    """

    def __init__(self, writing_service, activity_tracker):
        """
        Args:
            writing_service: WritingCoachService instance
            activity_tracker: ActivityTracker instance
        """
        self._service = writing_service
        self._tracker = activity_tracker

    def handle_evaluation(self, text: str, user_id: str):
        """
        Handle writing evaluation.

        Args:
            text: User's written text
            user_id: User identifier
        """
        # TODO: Implementation in Sprint 6
        st.info("To be implemented in Sprint 6")
