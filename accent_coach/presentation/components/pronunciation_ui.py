"""
Pronunciation Practice UI Components
"""

import streamlit as st


class PronunciationUI:
    """
    Pure UI components for pronunciation practice.

    NO business logic - only rendering.
    """

    @staticmethod
    def render_ipa_guide(breakdown_data, default_selection, on_selection_change):
        """
        Render IPA guide with word selection.

        Args:
            breakdown_data: IPA breakdown data
            default_selection: Pre-selected words
            on_selection_change: Callback when selection changes
        """
        # TODO: Extract from results_visualizer.py in Sprint 7
        # This should be PURE UI - no business logic
        st.info("To be migrated in Sprint 7")

    @staticmethod
    def render_comparison_table(per_word_comparison, show_only_errors=False):
        """
        Render word-by-word comparison table.

        Args:
            per_word_comparison: Per-word comparison data
            show_only_errors: Filter to show only errors
        """
        # TODO: Migrate from results_visualizer.py in Sprint 7
        st.info("To be migrated in Sprint 7")
