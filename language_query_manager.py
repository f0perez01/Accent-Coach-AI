#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Language Query Manager (Refactored for Expression Naturalness Checking)
Evaluates whether expressions are commonly used in American English.
"""

from typing import Dict, List, Optional
from datetime import datetime


class LanguageQueryManager:
    """
    Manages language consultation chat with LLM, now specialized in:
    - Checking if an expression is natural/common in American English
    - Explaining how native speakers actually use the expression
    - Detecting unnatural or incorrect phrasing
    - Suggesting more natural alternatives
    - Giving short examples with context

    All method signatures have been preserved.
    """

    QUERY_CATEGORIES = {
        "idiom": "idiomatic expression",
        "phrasal_verb": "phrasal verb",
        "expression": "common expression",
        "slang": "slang or informal language",
        "grammar": "grammar question",
        "vocabulary": "vocabulary or word meaning"
    }

    def __init__(self, groq_manager):
        self.groq_manager = groq_manager

    # ----------------------------------------------------------------------
    # Main Query Processing
    # ----------------------------------------------------------------------
    def process_query(self, user_query: str, conversation_history: List[Dict] = None) -> Dict:
        """
        Process user query through the LLM.

        Returns:
            Dict with user_query, llm_response, timestamp, category
        """
        if not self.groq_manager or not self.groq_manager.api_key:
            return {
                "user_query": user_query,
                "llm_response": "LLM is not available. Please check your API configuration.",
                "timestamp": datetime.now(),
                "category": "error"
            }

        try:
            from groq import Groq
            client = Groq(api_key=self.groq_manager.api_key)

            messages = self._build_messages(user_query, conversation_history)

            completion = client.chat.completions.create(
                messages=messages,
                model=self.groq_manager.model or "llama-3.1-8b-instant",
                temperature=0.25,  # precise and consistent
                max_tokens=450
            )

            llm_response = completion.choices[0].message.content.strip()
            category = self._detect_category(user_query)

            return {
                "user_query": user_query,
                "llm_response": llm_response,
                "timestamp": datetime.now(),
                "category": category
            }

        except Exception as e:
            print(f"Language query error: {e}")
            return {
                "user_query": user_query,
                "llm_response": f"Error processing query: {str(e)}",
                "timestamp": datetime.now(),
                "category": "error"
            }

    # ----------------------------------------------------------------------
    # Build messages for LLM
    # ----------------------------------------------------------------------
    def _build_messages(self, user_query: str, conversation_history: List[Dict] = None) -> List[Dict]:
        """
        Build messages with an optimized system prompt specialized in:
        - Naturalness evaluation
        - Colloquial frequency in American English
        - Register analysis (formal/informal)
        - Better alternatives
        """

        messages = [
            {
                "role": "system",
                "content": """
You are a highly specialized assistant that evaluates how natural an English expression sounds to a native American speaker.

Your goals for each user question:
1. Determine if the expression is **commonly used**, **rare**, **unnatural**, or **incorrect**.
2. Explain *how* and *when* native speakers actually use it.
3. Give 2–3 short real-life examples.
4. If the expression is unnatural, provide the closest **native alternatives**.
5. Keep explanations concise, clear, and friendly.
6. Avoid academic grammar terms unless absolutely necessary.

Focus strongly on:
- naturalness
- real-life usage
- colloquial vs. formal English
- incorrect or unnatural phrasing patterns
"""
            }
        ]

        if conversation_history:
            # keep last 6 pairs
            for msg in conversation_history[-6:]:
                messages.append({"role": "user", "content": msg.get("user_query", "")})
                messages.append({"role": "assistant", "content": msg.get("llm_response", "")})

        messages.append({"role": "user", "content": user_query})
        return messages

    # ----------------------------------------------------------------------
    # Category detection (preserved)
    # ----------------------------------------------------------------------
    def _detect_category(self, query: str) -> str:
        """
        Simple keyword-based category detection.
        """
        query_lower = query.lower()

        if any(word in query_lower for word in ["phrasal", "phrasal verb"]):
            return "phrasal_verb"
        if any(word in query_lower for word in ["idiom", "idiomatic"]):
            return "idiom"
        if any(word in query_lower for word in ["slang", "informal", "casual"]):
            return "slang"
        if any(word in query_lower for word in ["grammar", "tense"]):
            return "grammar"
        if any(word in query_lower for word in ["meaning", "definition"]):
            return "vocabulary"

        # default case → expressions / naturalness
        return "expression"

    # ----------------------------------------------------------------------
    # Formatting (unchanged)
    # ----------------------------------------------------------------------
    @staticmethod
    def format_chat_message(message: Dict, is_user: bool = True) -> str:
        return message.get("user_query" if is_user else "llm_response", "")

    # ----------------------------------------------------------------------
    # Quick example prompts (updated)
    # ----------------------------------------------------------------------
    @staticmethod
    def get_quick_examples() -> List[str]:
        """
        Get quick example queries to help users get started.

        (Now intentionally left empty because you requested to remove example questions)
        """
        return []
