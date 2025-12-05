"""
Practice Text Manager

Manages practice texts for pronunciation training.
Migrated from root practice_texts.py with enhancements.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class PracticeText:
    """Represents a practice text with metadata."""
    text: str
    category: str
    difficulty: Optional[str] = None
    focus: Optional[str] = None
    word_count: Optional[int] = None

    def __post_init__(self):
        """Calculate word count and set defaults if not provided."""
        if self.word_count is None:
            self.word_count = len(self.text.split())
        if self.focus is None:
            self.focus = "General practice"
        if self.difficulty is None:
            # Infer difficulty from category if not set
            difficulty_map = {
                "Beginner": "Easy",
                "Intermediate": "Medium",
                "Advanced": "Hard",
                "Common Phrases": "Easy",
                "Idioms": "Medium",
                "Business English": "Medium",
                "Tongue Twisters": "Hard"
            }
            self.difficulty = difficulty_map.get(self.category, "Medium")


class PracticeTextManager:
    """
    Manages practice texts for pronunciation training.
    
    Provides organized collections of texts by category and difficulty level.
    """

    # Practice texts organized by category
    TEXTS: Dict[str, List[str]] = {
        "Beginner": [
            "The quick brown fox jumps over the lazy dog.",
            "How much wood would a woodchuck chuck if a woodchuck could chuck wood?",
            "She sells seashells by the seashore.",
            "A big black bug bit a big black dog on his big black nose.",
            "I saw a kitten eating chicken in the kitchen.",
            "Hello, my name is Alex. Nice to meet you.",
            "The cat sat on the mat.",
            "I like to eat pizza and ice cream.",
            "Today is a beautiful sunny day.",
            "Can you help me please?",
        ],
        "Intermediate": [
            "Peter Piper picked a peck of pickled peppers.",
            "I scream, you scream, we all scream for ice cream.",
            "Six thick thistle sticks. Six thick thistles stick.",
            "Fuzzy Wuzzy was a bear. Fuzzy Wuzzy had no hair.",
            "How can a clam cram in a clean cream can?",
            "Red leather, yellow leather, red leather, yellow leather.",
            "Betty Botter bought some butter, but she said the butter's bitter.",
            "A proper copper coffee pot.",
            "Which wristwatches are Swiss wristwatches?",
            "Eleven benevolent elephants.",
        ],
        "Advanced": [
            "The sixth sick sheikh's sixth sheep's sick.",
            "Pad kid poured curd pulled cod.",
            "Can you can a can as a canner can can a can?",
            "Red lorry, yellow lorry, red lorry, yellow lorry.",
            "Unique New York, you need New York, you know you need unique New York.",
            "The seething sea ceaseth and thus the seething sea sufficeth us.",
            "I saw Susie sitting in a shoeshine shop.",
            "Imagine an imaginary menagerie manager managing an imaginary menagerie.",
            "Brisk brave brigadiers brandished broad bright blades.",
            "Six sleek swans swam swiftly southwards.",
        ],
        "Common Phrases": [
            "Could you please repeat that?",
            "I would like to make a reservation.",
            "What time does the meeting start?",
            "Thank you very much for your help.",
            "I'm sorry, I didn't understand.",
            "Excuse me, where is the nearest subway station?",
            "How much does this cost?",
            "I need to cancel my appointment.",
            "Could you speak more slowly, please?",
            "What's the weather like today?",
        ],
        "Idioms": [
            "It's raining cats and dogs outside.",
            "Break a leg at your performance tonight!",
            "That costs an arm and a leg.",
            "I'm feeling under the weather today.",
            "Let's call it a day.",
            "The ball is in your court now.",
            "Don't beat around the bush.",
            "That's a piece of cake.",
            "Actions speak louder than words.",
            "Better late than never.",
        ],
        "Business English": [
            "Let's schedule a meeting to discuss the quarterly results.",
            "I'd like to follow up on our previous conversation.",
            "Could you send me the presentation slides?",
            "We need to meet the deadline by Friday.",
            "I appreciate your prompt response.",
            "Let's touch base next week.",
            "I'll keep you in the loop.",
            "Could you please clarify the requirements?",
            "I'm looking forward to our collaboration.",
            "Thank you for taking the time to meet with me.",
        ],
        "Tongue Twisters": [
            "She sells seashells by the seashore.",
            "Peter Piper picked a peck of pickled peppers.",
            "How much wood would a woodchuck chuck?",
            "Rubber baby buggy bumpers.",
            "Toy boat, toy boat, toy boat.",
            "Three free throws.",
            "Red lorry, yellow lorry.",
            "Eleven benevolent elephants.",
            "Specific Pacific.",
            "Irish wristwatch, Swiss wristwatch.",
        ],
    }

    @classmethod
    def get_categories(cls) -> List[str]:
        """
        Get all available practice text categories.
        
        Returns:
            List of category names
        """
        return list(cls.TEXTS.keys())

    @classmethod
    def get_texts_for_category(cls, category: str) -> List[PracticeText]:
        """
        Get all texts for a specific category.
        
        Args:
            category: Category name
            
        Returns:
            List of PracticeText objects for the category
        """
        texts = cls.TEXTS.get(category, [])
        return [
            PracticeText(
                text=text,
                category=category,
                difficulty=None,  # Will be auto-set in __post_init__
                focus=cls._get_focus_for_category(category)
            )
            for text in texts
        ]
    
    @classmethod
    def _get_focus_for_category(cls, category: str) -> str:
        """Get focus area for a category."""
        focus_map = {
            "Beginner": "Basic vocabulary and simple sentences",
            "Intermediate": "Common expressions and conversations",
            "Advanced": "Complex grammar and vocabulary",
            "Common Phrases": "Practical daily phrases",
            "Idioms": "Idiomatic expressions",
            "Business English": "Professional communication",
            "Tongue Twisters": "Pronunciation clarity and speed"
        }
        return focus_map.get(category, "General practice")

    @classmethod
    def get_all_texts(cls) -> Dict[str, List[str]]:
        """
        Get all practice texts organized by category.
        
        Returns:
            Dictionary mapping categories to text lists
        """
        return cls.TEXTS.copy()

    @classmethod
    def get_text_by_index(cls, category: str, index: int) -> Optional[PracticeText]:
        """
        Get a specific text by category and index.
        
        Args:
            category: Category name
            index: Index of text in category
            
        Returns:
            PracticeText object or None if not found
        """
        texts = cls.get_texts_for_category(category)
        if 0 <= index < len(texts):
            return texts[index]
        return None

    @classmethod
    def get_text_metadata(cls, text: str, category: str) -> PracticeText:
        """
        Get metadata for a practice text.
        
        Args:
            text: Practice text
            category: Category name
            
        Returns:
            PracticeText object with metadata
        """
        # Determine difficulty based on category
        difficulty = None
        if category in ["Beginner", "Intermediate", "Advanced"]:
            difficulty = category
        elif category == "Tongue Twisters":
            difficulty = "Advanced"
        elif category == "Common Phrases":
            difficulty = "Beginner"
        elif category in ["Business English", "Idioms"]:
            difficulty = "Intermediate"

        return PracticeText(
            text=text,
            category=category,
            difficulty=difficulty
        )

    @classmethod
    def search_texts(cls, query: str) -> List[PracticeText]:
        """
        Search for texts containing a query string.
        
        Args:
            query: Search query
            
        Returns:
            List of PracticeText objects matching the query
        """
        results = []
        query_lower = query.lower()
        
        for category, texts in cls.TEXTS.items():
            for text in texts:
                if query_lower in text.lower():
                    results.append(
                        PracticeText(
                            text=text,
                            category=category,
                            focus=cls._get_focus_for_category(category)
                        )
                    )
        
        return results

    @classmethod
    def get_random_text(cls, category: Optional[str] = None) -> Optional[PracticeText]:
        """
        Get a random text, optionally from a specific category.
        
        Args:
            category: Optional category name
            
        Returns:
            Random PracticeText object
        """
        import random
        
        if category:
            texts = cls.get_texts_for_category(category)
            return random.choice(texts) if texts else None
        else:
            # Get all texts as PracticeText objects
            all_texts = []
            for cat in cls.get_categories():
                all_texts.extend(cls.get_texts_for_category(cat))
            return random.choice(all_texts) if all_texts else None

    @classmethod
    def get_total_text_count(cls) -> int:
        """
        Get total number of practice texts available.
        
        Returns:
            Total count of texts
        """
        return sum(len(texts) for texts in cls.TEXTS.values())

    @classmethod
    def get_category_info(cls, category: Optional[str] = None) -> Dict[str, any]:
        """
        Get information about category or categories.
        
        Args:
            category: Specific category name, or None for all categories
        
        Returns:
            Dictionary with category stats. If category specified, returns single dict.
            If category is None, returns dict of all categories.
        """
        category_descriptions = {
            "Beginner": "Simple, short sentences perfect for starting learners",
            "Intermediate": "Everyday conversations and common expressions",
            "Advanced": "Complex sentences with sophisticated vocabulary",
            "Common Phrases": "Practical phrases for daily interactions",
            "Idioms": "English idioms and expressions",
            "Business English": "Professional communication phrases",
            "Tongue Twisters": "Challenging phrases for pronunciation practice"
        }
        
        if category:
            # Return info for specific category
            if category not in cls.TEXTS:
                return {}
            texts = cls.TEXTS[category]
            return {
                'count': len(texts),
                'description': category_descriptions.get(category, ""),
                'avg_words': sum(len(text.split()) for text in texts) / len(texts) if texts else 0
            }
        else:
            # Return info for all categories
            info = {}
            for cat, texts in cls.TEXTS.items():
                info[cat] = {
                    'count': len(texts),
                    'description': category_descriptions.get(cat, ""),
                    'avg_words': sum(len(text.split()) for text in texts) / len(texts) if texts else 0
                }
            return info
