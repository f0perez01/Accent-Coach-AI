"""
Streamlit Main Application

Thin UI orchestrator.
Delegates to controllers and services.

This will replace the current monolithic app.py (1,295 lines → ~300 lines)
"""

import streamlit as st


def main():
    """Main Streamlit application entry point."""
    st.set_page_config(
        page_title="Accent Coach AI",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🎙️ Accent Coach AI - Modular Architecture")
    st.markdown("Refactored following Domain-Driven Design principles")

    # TODO: Implementation
    # 1. Initialize services (with DI)
    # 2. Render tabs
    # 3. Delegate to controllers
    st.info("To be implemented in Sprints 4-6")


if __name__ == "__main__":
    main()
