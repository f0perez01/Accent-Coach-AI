"""
Conversation Starters

Pre-defined conversation starters organized by topic and proficiency level.
Migrated from prompt_templates.py to follow DDD architecture.
"""

from typing import List
import random


class ConversationStarters:
    """
    Provides conversation starters by topic and level.
    Helps initiate natural conversation practice sessions.
    """

    STARTERS_BY_TOPIC = {
        "Daily Routine": {
            "B1-B2": [
                "Tell me about your typical morning routine.",
                "What do you usually do on weekends?",
                "How do you usually spend your evenings?",
            ],
            "A2": [
                "What time do you wake up?",
                "What do you eat for breakfast?",
                "Do you like mornings or evenings?",
            ],
        },
        "Travel": {
            "B1-B2": [
                "What's the most memorable trip you've ever taken?",
                "If you could visit any country, where would you go and why?",
                "Do you prefer city trips or nature vacations?",
            ],
            "A2": [
                "Do you like traveling?",
                "What countries have you visited?",
                "What's your favorite place?",
            ],
        },
        "Food & Cooking": {
            "B1-B2": [
                "What's your favorite dish to cook? Can you describe how to make it?",
                "What do you think about trying new cuisines?",
                "Do you prefer eating out or cooking at home?",
            ],
            "A2": [
                "What's your favorite food?",
                "Can you cook?",
                "What did you eat today?",
            ],
        },
        "Work & Career": {
            "B1-B2": [
                "What do you find most challenging about your work or studies?",
                "Where do you see yourself professionally in five years?",
                "What skills would you like to develop?",
            ],
            "A2": [
                "What is your job?",
                "Do you like your work?",
                "What do you study?",
            ],
        },
        "Hobbies & Interests": {
            "B1-B2": [
                "What hobbies help you relax after a stressful day?",
                "Have you picked up any new interests recently?",
                "If you had unlimited free time, what would you do?",
            ],
            "A2": [
                "What do you like to do for fun?",
                "Do you play any sports?",
                "What's your hobby?",
            ],
        },
        "Technology": {
            "B1-B2": [
                "How has technology changed the way you communicate?",
                "What's your opinion on social media?",
                "Do you think AI will change our daily lives? How?",
            ],
            "A2": [
                "Do you use social media?",
                "What apps do you use?",
                "Do you like technology?",
            ],
        },
        "Health & Fitness": {
            "B1-B2": [
                "How do you stay active and healthy?",
                "What's your approach to maintaining work-life balance?",
                "Have you ever tried changing a health habit? How did it go?",
            ],
            "A2": [
                "Do you exercise?",
                "What sports do you like?",
                "How do you stay healthy?",
            ],
        },
        "General Conversation": {
            "B1-B2": [
                "What's been the highlight of your week so far?",
                "Is there anything you've been learning or working on lately?",
                "What are you looking forward to this month?",
            ],
            "A2": [
                "How are you today?",
                "What did you do yesterday?",
                "What are your plans for tomorrow?",
            ],
        },
    }

    @classmethod
    def get_starter(cls, topic: str, level: str = "B1-B2") -> str:
        """
        Get a random conversation starter for a topic and level.

        Args:
            topic: Conversation topic
            level: User's proficiency level (e.g., "A2", "B1-B2")

        Returns:
            Conversation starter question
        """
        # Get topic starters, default to General Conversation
        topic_starters = cls.STARTERS_BY_TOPIC.get(
            topic, cls.STARTERS_BY_TOPIC["General Conversation"]
        )

        # Get level starters, default to B1-B2
        level_starters = topic_starters.get(level, topic_starters.get("B1-B2", []))

        if not level_starters:
            return "Tell me about your day."

        return random.choice(level_starters)

    @classmethod
    def get_topics(cls) -> List[str]:
        """
        Get list of available conversation topics.

        Returns:
            List of topic names
        """
        return list(cls.STARTERS_BY_TOPIC.keys())

    @classmethod
    def get_levels(cls) -> List[str]:
        """
        Get list of supported proficiency levels.

        Returns:
            List of level codes
        """
        return ["A2", "B1-B2"]
