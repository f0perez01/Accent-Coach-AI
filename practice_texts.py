#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Practice Texts Configuration
Contains predefined practice texts organized by difficulty level
"""

from typing import Dict, List


class PracticeTextManager:
    """Manages practice texts for pronunciation training"""

    # Practice texts organized by difficulty level
    TEXTS: Dict[str, List[str]] = {
        "Beginner": [
            "The quick brown fox jumps over the lazy dog.",
            "How much wood would a woodchuck chuck if a woodchuck could chuck wood?",
            "She sells seashells by the seashore.",
            "A big black bug bit a big black dog on his big black nose.",
            "I saw a kitten eating chicken in the kitchen.",
        ],
        "Intermediate": [
            "Peter Piper picked a peck of pickled peppers.",
            "I scream, you scream, we all scream for ice cream.",
            "Six thick thistle sticks. Six thick thistles stick.",
            "Fuzzy Wuzzy was a bear. Fuzzy Wuzzy had no hair.",
            "How can a clam cram in a clean cream can?",
        ],
        "Advanced": [
            "The sixth sick sheikh's sixth sheep's sick.",
            "Pad kid poured curd pulled cod.",
            "Can you can a can as a canner can can a can?",
            "Red lorry, yellow lorry, red lorry, yellow lorry.",
            "Unique New York, you need New York, you know you need unique New York.",
        ],
        "Common Phrases": [
            "Could you please repeat that?",
            "I would like to make a reservation.",
            "What time does the meeting start?",
            "Thank you very much for your help.",
            "I'm sorry, I didn't understand.",
        ]
    }

    @classmethod
    def get_categories(cls) -> List[str]:
        """Get all available practice text categories"""
        return list(cls.TEXTS.keys())

    @classmethod
    def get_texts_for_category(cls, category: str) -> List[str]:
        """Get all texts for a specific category"""
        return cls.TEXTS.get(category, [])

    @classmethod
    def get_all_texts(cls) -> Dict[str, List[str]]:
        """Get all practice texts"""
        return cls.TEXTS.copy()
