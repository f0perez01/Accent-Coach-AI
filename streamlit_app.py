"""
Accent Coach AI - Main Entry Point

This file delegates to the refactored modular application.
Run with: streamlit run streamlit_app.py
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from accent_coach.presentation.streamlit_app import main

if __name__ == "__main__":
    main()
