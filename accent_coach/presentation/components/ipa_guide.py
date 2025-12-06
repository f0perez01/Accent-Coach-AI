"""
IPA Guide Component

Interactive phonetic alphabet guide for the sidebar.
Provides quick reference to IPA symbols with filters by category.
"""

import streamlit as st
from typing import Dict, List, Optional
from ipa_definitions import IPADefinitionsManager


class IPAGuideComponent:
    """
    IPA phonetic alphabet guide component for sidebar.
    
    Displays IPA symbols organized by category (vowels, diphthongs, consonants)
    with educational descriptions.
    """
    
    @staticmethod
    def render():
        """
        Render the IPA guide in an expander with category filters.
        
        Displays:
        - Filter options (All, Vowels, Diphthongs, Consonants, Stress)
        - Symbol cards with definitions
        - Search functionality
        """
        with st.expander("📖 IPA Quick Reference", expanded=False):
            st.markdown("**International Phonetic Alphabet Guide**")
            st.caption("Reference for American English pronunciation symbols")
            
            # Filter selector
            filter_options = [
                "All Symbols",
                "Vowels",
                "Diphthongs", 
                "Consonants",
                "Stress Markers"
            ]
            
            selected_filter = st.selectbox(
                "Category:",
                options=filter_options,
                key="ipa_guide_filter",
                label_visibility="collapsed"
            )
            
            # Get filtered symbols
            symbols = IPAGuideComponent._get_filtered_symbols(selected_filter)
            
            # Display count
            st.caption(f"Showing {len(symbols)} symbols")
            
            st.divider()
            
            # Display symbols in a clean layout
            IPAGuideComponent._render_symbols(symbols)
    
    @staticmethod
    def _get_filtered_symbols(filter_type: str) -> Dict[str, str]:
        """
        Get symbols filtered by category.
        
        Args:
            filter_type: Category filter selected by user
            
        Returns:
            Dictionary of filtered IPA symbols and definitions
        """
        if filter_type == "Vowels":
            return IPADefinitionsManager.get_vowels()
        elif filter_type == "Diphthongs":
            return IPADefinitionsManager.get_diphthongs()
        elif filter_type == "Consonants":
            return IPADefinitionsManager.get_consonants()
        elif filter_type == "Stress Markers":
            return {
                "ˈ": "Acento principal (sílaba fuerte)",
                "ˌ": "Acento secundario"
            }
        else:  # All Symbols
            return IPADefinitionsManager.get_all_definitions()
    
    @staticmethod
    def _render_symbols(symbols: Dict[str, str]):
        """
        Render IPA symbols in a clean card layout.
        
        Args:
            symbols: Dictionary of IPA symbols and their definitions
        """
        if not symbols:
            st.info("No symbols found for this category")
            return
        
        # Render each symbol as a clean info card
        for symbol, definition in symbols.items():
            # Use container for better spacing
            col1, col2 = st.columns([1, 4])
            
            with col1:
                # Large symbol display
                st.markdown(f"### {symbol}")
            
            with col2:
                # Definition with subtle styling
                st.markdown(f"**{definition}**")
            
            # Subtle separator
            st.markdown("<hr style='margin: 8px 0; opacity: 0.1;'>", unsafe_allow_html=True)


def render_ipa_guide():
    """
    Convenience function to render IPA guide component.
    
    Usage:
        from accent_coach.presentation.components.ipa_guide import render_ipa_guide
        render_ipa_guide()
    """
    IPAGuideComponent.render()
