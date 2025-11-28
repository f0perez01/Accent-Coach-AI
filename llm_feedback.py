#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Feedback Module
Handles AI-powered pronunciation feedback using Groq API
"""

from typing import Optional, List, Dict
import streamlit as st

try:
    from groq import Groq
    _HAS_GROQ = True
except ImportError:
    _HAS_GROQ = False


class LLMFeedbackGenerator:
    """Generates AI-powered accent coaching feedback using LLM"""

    # System prompts for different feedback types
    ACCENT_COACH_PROMPT = """You are an expert dialect/accent coach for American spoken English.
Provide feedback to improve the speaker's American accent.
Use Google pronunciation respelling when giving corrections.
Provide the following sections:
- Overall Impression
- Specific Feedback
- Google Pronunciation Respelling Suggestions
- Additional Tips"""

    PRONUNCIATION_TUTOR_PROMPT = """You are a professional pronunciation tutor for English learners.
Analyze the pronunciation differences and provide constructive feedback.
Focus on:
- Sounds that need improvement
- Common mistakes and how to fix them
- Practice recommendations
Be encouraging and specific."""

    PHONETICS_EXPERT_PROMPT = """You are a phonetics expert analyzing pronunciation patterns.
Provide detailed technical feedback on:
- Phoneme substitutions and their causes
- Articulatory adjustments needed
- IPA-based corrections
- Systematic patterns in errors"""

    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        """
        Initialize LLM Feedback Generator

        Args:
            api_key: Groq API key
            model: Model name to use (default: llama-3.1-8b-instant)
        """
        if not _HAS_GROQ:
            raise ImportError("Groq library not available. Install with: pip install groq")

        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.model = model
        self.client = Groq(api_key=api_key)

    def generate_accent_feedback(
        self,
        reference_text: str,
        per_word_comparison: List[Dict],
        temperature: float = 0.0
    ) -> Optional[str]:
        """
        Generate accent coaching feedback

        Args:
            reference_text: Original reference text
            per_word_comparison: List of word-by-word comparison dicts
            temperature: Model temperature (0.0 = deterministic)

        Returns:
            Feedback text or None on failure
        """
        return self._generate_feedback(
            reference_text,
            per_word_comparison,
            self.ACCENT_COACH_PROMPT,
            temperature
        )

    def generate_pronunciation_feedback(
        self,
        reference_text: str,
        per_word_comparison: List[Dict],
        temperature: float = 0.2
    ) -> Optional[str]:
        """
        Generate pronunciation tutor feedback (more encouraging)

        Args:
            reference_text: Original reference text
            per_word_comparison: List of word-by-word comparison dicts
            temperature: Model temperature

        Returns:
            Feedback text or None on failure
        """
        return self._generate_feedback(
            reference_text,
            per_word_comparison,
            self.PRONUNCIATION_TUTOR_PROMPT,
            temperature
        )

    def generate_phonetics_analysis(
        self,
        reference_text: str,
        per_word_comparison: List[Dict],
        temperature: float = 0.0
    ) -> Optional[str]:
        """
        Generate detailed phonetics analysis

        Args:
            reference_text: Original reference text
            per_word_comparison: List of word-by-word comparison dicts
            temperature: Model temperature

        Returns:
            Analysis text or None on failure
        """
        return self._generate_feedback(
            reference_text,
            per_word_comparison,
            self.PHONETICS_EXPERT_PROMPT,
            temperature
        )

    def _generate_feedback(
        self,
        reference_text: str,
        per_word_comparison: List[Dict],
        system_prompt: str,
        temperature: float
    ) -> Optional[str]:
        """
        Internal method to generate feedback

        Args:
            reference_text: Original reference text
            per_word_comparison: List of word-by-word comparison dicts
            system_prompt: System message for the LLM
            temperature: Model temperature

        Returns:
            Feedback text or None on failure
        """
        try:
            # Build comparison text
            diff = self._format_comparison(per_word_comparison)

            user_prompt = f"""Reference Text: {reference_text}

(word, reference_phoneme, recorded_phoneme)
{diff}"""

            # Call LLM
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model=self.model,
                temperature=temperature
            )

            return chat_completion.choices[0].message.content

        except Exception as e:
            st.error(f"LLM feedback generation failed: {e}")
            return None

    @staticmethod
    def _format_comparison(per_word_comparison: List[Dict]) -> str:
        """
        Format word comparison for LLM prompt

        Args:
            per_word_comparison: List of comparison dicts

        Returns:
            Formatted comparison string
        """
        lines = []
        for item in per_word_comparison:
            word = item.get('word', '')
            ref = item.get('ref_phonemes', '')
            rec = item.get('rec_phonemes', '')
            lines.append(f"{word}: expected={ref}, produced={rec}")

        return "\n".join(lines)

    @staticmethod
    def is_available() -> bool:
        """Check if Groq library is available"""
        return _HAS_GROQ


class FeedbackFormatter:
    """Formats and processes feedback text"""

    @staticmethod
    def extract_sections(feedback: str) -> Dict[str, str]:
        """
        Extract sections from feedback text

        Args:
            feedback: Complete feedback text

        Returns:
            Dictionary with section names as keys
        """
        sections = {}
        current_section = "Introduction"
        current_content = []

        for line in feedback.split('\n'):
            # Check if line is a section header (starts with -, *, or is all caps)
            if line.strip().startswith('-') or line.strip().startswith('*'):
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                    current_content = []

                # Start new section
                current_section = line.strip().lstrip('-*').strip()

            elif line.strip().isupper() and len(line.strip()) > 3:
                # All caps header
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                    current_content = []

                current_section = line.strip()

            else:
                current_content.append(line)

        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

    @staticmethod
    def highlight_corrections(feedback: str) -> str:
        """
        Add markdown highlighting to corrections

        Args:
            feedback: Feedback text

        Returns:
            Feedback with markdown highlighting
        """
        # Highlight phonetic corrections (text in quotes or parentheses)
        import re

        # Highlight quoted text
        feedback = re.sub(r'"([^"]+)"', r'**"\1"**', feedback)

        # Highlight IPA patterns
        feedback = re.sub(r'/([^/]+)/', r'`/\1/`', feedback)

        return feedback

    @staticmethod
    def create_summary(per_word_comparison: List[Dict]) -> str:
        """
        Create a quick summary of the analysis

        Args:
            per_word_comparison: List of comparison dicts

        Returns:
            Summary text
        """
        total = len(per_word_comparison)
        correct = sum(1 for item in per_word_comparison if item.get('match', False))
        errors = total - correct

        if errors == 0:
            return "🎉 Perfect pronunciation! All words match the reference."

        error_rate = (errors / total) * 100

        if error_rate < 10:
            level = "Excellent"
            emoji = "✨"
        elif error_rate < 25:
            level = "Good"
            emoji = "👍"
        elif error_rate < 50:
            level = "Fair"
            emoji = "📝"
        else:
            level = "Needs Practice"
            emoji = "💪"

        return f"{emoji} **{level}** - {correct}/{total} words correct ({error_rate:.1f}% error rate)"


class FeedbackCache:
    """Caches LLM feedback to avoid redundant API calls"""

    def __init__(self):
        if 'llm_feedback_cache' not in st.session_state:
            st.session_state.llm_feedback_cache = {}

    @staticmethod
    def _create_key(reference_text: str, comparison: List[Dict]) -> str:
        """Create cache key from inputs"""
        import hashlib
        import json

        # Create a deterministic hash of the inputs
        data = {
            'text': reference_text,
            'comparison': sorted(
                [(item['word'], item['ref_phonemes'], item['rec_phonemes'])
                 for item in comparison]
            )
        }
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(json_str.encode()).hexdigest()

    def get(self, reference_text: str, comparison: List[Dict]) -> Optional[str]:
        """Get cached feedback if available"""
        key = self._create_key(reference_text, comparison)
        return st.session_state.llm_feedback_cache.get(key)

    def set(self, reference_text: str, comparison: List[Dict], feedback: str):
        """Cache feedback"""
        key = self._create_key(reference_text, comparison)
        st.session_state.llm_feedback_cache[key] = feedback

    def clear(self):
        """Clear all cached feedback"""
        st.session_state.llm_feedback_cache = {}
