"""
Results Visualizers

Charts, graphs, waveforms - pure visualization.
"""

import streamlit as st
import plotly.graph_objects as go


class ResultsVisualizer:
    """
    Pure visualization components.

    NO business logic - only charts and graphs.
    """

    @staticmethod
    def plot_waveform(audio, sr, title="Audio Waveform"):
        """
        Plot audio waveform.

        Args:
            audio: Audio waveform array
            sr: Sample rate
            title: Chart title

        Returns:
            Plotly figure
        """
        # TODO: Migrate from results_visualizer.py in Sprint 7
        st.info("To be migrated in Sprint 7")

    @staticmethod
    def plot_error_distribution(metrics):
        """
        Plot error distribution chart.

        Args:
            metrics: Pronunciation metrics

        Returns:
            Plotly figure
        """
        # TODO: Migrate from results_visualizer.py in Sprint 7
        st.info("To be migrated in Sprint 7")
