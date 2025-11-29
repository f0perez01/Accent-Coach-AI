#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prompt Templates for Conversation Tutor
Educational prompts for ESL/L2 conversation practice
"""

from typing import List, Dict, Optional


class ConversationPromptTemplate:
    """
    Template manager for LLM prompts in conversation tutoring.
    Provides structured prompts for different teaching scenarios.
    """

    # Base system prompt for conversation tutor
    SYSTEM_PROMPT_BASE = """You are a friendly and supportive ESL conversation tutor.

Your role:
- Help students practice natural English conversation
- Correct grammar and vocabulary mistakes gently
- Explain errors using simple, clear language
- Keep the conversation flowing naturally
- Adapt to the student's proficiency level

Student level: {user_level}

Guidelines:
1. ALWAYS correct errors, but kindly
2. Provide brief explanations (1-2 sentences max)
3. Give a natural, improved version of what they said
4. Ask ONE follow-up question to continue the conversation
5. Stay on topic unless the student changes it
6. Be encouraging and motivating

Output format (MUST follow exactly):

[CORRECTION]: Brief correction of the error (or "Great! No errors." if perfect)
[EXPLANATION]: Simple explanation of the grammar/vocabulary rule
[IMPROVED VERSION]: Natural way to say what they meant
[FOLLOW UP QUESTION]: One question to continue the conversation

Keep your total response under 100 words."""

    # Prompt for topic-based conversations
    TOPIC_PROMPT = """Conversation topic: {topic}

Guide the student to practice vocabulary and structures related to this topic.
Ask questions that encourage them to use relevant vocabulary."""

    # Prompt for error-focused practice
    ERROR_FOCUS_PROMPT = """Focus area: {focus_area}

Pay special attention to errors related to: {focus_area}
Provide targeted practice in this area through your questions."""

    @classmethod
    def build_tutor_prompt(
        cls,
        user_transcript: str,
        conversation_history: List[Dict],
        user_level: str = "B1-B2",
        topic: Optional[str] = None,
        focus_area: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Build complete prompt for conversation tutor.

        Args:
            user_transcript: What the user just said
            conversation_history: Previous conversation turns
            user_level: User's proficiency level
            topic: Optional conversation topic
            focus_area: Optional grammar/vocab focus area

        Returns:
            Dict with 'system' and 'user' prompt sections
        """

        # Build system prompt
        system_prompt = cls.SYSTEM_PROMPT_BASE.format(user_level=user_level)

        if topic:
            system_prompt += "\n\n" + cls.TOPIC_PROMPT.format(topic=topic)

        if focus_area:
            system_prompt += "\n\n" + cls.ERROR_FOCUS_PROMPT.format(focus_area=focus_area)

        # Build user prompt with context
        user_prompt_parts = []

        # Add conversation history for context (last 3 turns)
        if conversation_history:
            user_prompt_parts.append("Recent conversation context:")
            for turn in conversation_history[-3:]:
                user_msg = turn.get('user_transcript', '')
                assistant_msg = turn.get('assistant_response', '')
                if user_msg:
                    user_prompt_parts.append(f"Student: {user_msg}")
                if assistant_msg:
                    # Only include the follow-up question from previous turns
                    follow_up = turn.get('follow_up_question', '')
                    if follow_up:
                        user_prompt_parts.append(f"Tutor: {follow_up}")

            user_prompt_parts.append("")  # Blank line

        # Add current user input
        user_prompt_parts.append(f"Student's current message:")
        user_prompt_parts.append(f'"{user_transcript}"')
        user_prompt_parts.append("")
        user_prompt_parts.append("Please analyze and respond following the format above.")

        user_prompt = "\n".join(user_prompt_parts)

        return {
            "system": system_prompt,
            "user": user_prompt
        }

    @classmethod
    def build_exam_mode_prompt(cls, user_transcript: str, user_level: str = "B1-B2") -> Dict[str, str]:
        """
        Build prompt for exam/assessment mode (no immediate feedback).

        Args:
            user_transcript: User's speech
            user_level: Proficiency level

        Returns:
            Dict with 'system' and 'user' prompts
        """

        system_prompt = f"""You are an ESL examiner assessing a {user_level} student.

Your role:
- Record errors but DO NOT provide corrections yet
- Ask natural follow-up questions to continue the conversation
- Keep the student talking naturally
- Do not mention errors or corrections

Output format:

[ERRORS FOUND]: List of errors (internal note, not shown to student)
[FOLLOW UP QUESTION]: Natural question to continue conversation"""

        user_prompt = f'Student said: "{user_transcript}"\n\nProvide a natural follow-up question.'

        return {
            "system": system_prompt,
            "user": user_prompt
        }

    @classmethod
    def build_topic_suggestion_prompt(
        cls,
        conversation_history: List[Dict],
        user_level: str = "B1-B2"
    ) -> Dict[str, str]:
        """
        Generate topic suggestions based on conversation history.

        Args:
            conversation_history: Previous conversation turns
            user_level: User's proficiency level

        Returns:
            Dict with prompt for suggesting new topics
        """

        system_prompt = f"""You are an ESL curriculum advisor for {user_level} students.

Based on the student's conversation history, suggest 3 relevant topics for practice.

Consider:
- Topics they've discussed
- Vocabulary they've used
- Errors they've made (suggest topics to practice those areas)

Output format:

[TOPIC 1]: Topic name - Brief reason why this would help
[TOPIC 2]: Topic name - Brief reason why this would help
[TOPIC 3]: Topic name - Brief reason why this would help"""

        # Summarize history
        history_summary = []
        for turn in conversation_history[-5:]:
            user_msg = turn.get('user_transcript', '')
            if user_msg:
                history_summary.append(f"- {user_msg}")

        user_prompt = "Recent conversation:\n" + "\n".join(history_summary)
        user_prompt += "\n\nSuggest 3 new topics for practice."

        return {
            "system": system_prompt,
            "user": user_prompt
        }


class ConversationStarters:
    """
    Pre-defined conversation starters by topic and level.
    """

    STARTERS_BY_TOPIC = {
        "Daily Routine": {
            "B1-B2": [
                "Tell me about your typical morning routine.",
                "What do you usually do on weekends?",
                "How do you usually spend your evenings?"
            ],
            "A2": [
                "What time do you wake up?",
                "What do you eat for breakfast?",
                "Do you like mornings or evenings?"
            ]
        },
        "Travel": {
            "B1-B2": [
                "What's the most memorable trip you've ever taken?",
                "If you could visit any country, where would you go and why?",
                "Do you prefer city trips or nature vacations?"
            ],
            "A2": [
                "Do you like traveling?",
                "What countries have you visited?",
                "What's your favorite place?"
            ]
        },
        "Food & Cooking": {
            "B1-B2": [
                "What's your favorite dish to cook? Can you describe how to make it?",
                "What do you think about trying new cuisines?",
                "Do you prefer eating out or cooking at home?"
            ],
            "A2": [
                "What's your favorite food?",
                "Can you cook?",
                "What did you eat today?"
            ]
        },
        "Work & Career": {
            "B1-B2": [
                "What do you find most challenging about your work or studies?",
                "Where do you see yourself professionally in five years?",
                "What skills would you like to develop?"
            ],
            "A2": [
                "What is your job?",
                "Do you like your work?",
                "What do you study?"
            ]
        },
        "Hobbies & Interests": {
            "B1-B2": [
                "What hobbies help you relax after a stressful day?",
                "Have you picked up any new interests recently?",
                "If you had unlimited free time, what would you do?"
            ],
            "A2": [
                "What do you like to do for fun?",
                "Do you play any sports?",
                "What's your hobby?"
            ]
        },
        "Technology": {
            "B1-B2": [
                "How has technology changed the way you communicate?",
                "What's your opinion on social media?",
                "Do you think AI will change our daily lives? How?"
            ],
            "A2": [
                "Do you use social media?",
                "What apps do you use?",
                "Do you like technology?"
            ]
        },
        "Health & Fitness": {
            "B1-B2": [
                "How do you stay active and healthy?",
                "What's your approach to maintaining work-life balance?",
                "Have you ever tried changing a health habit? How did it go?"
            ],
            "A2": [
                "Do you exercise?",
                "What sports do you like?",
                "How do you stay healthy?"
            ]
        },
        "General Conversation": {
            "B1-B2": [
                "What's been the highlight of your week so far?",
                "Is there anything you've been learning or working on lately?",
                "What are you looking forward to this month?"
            ],
            "A2": [
                "How are you today?",
                "What did you do yesterday?",
                "What are your plans for tomorrow?"
            ]
        }
    }

    @classmethod
    def get_starter(cls, topic: str, level: str = "B1-B2") -> str:
        """
        Get a random conversation starter for a topic and level.

        Args:
            topic: Conversation topic
            level: User's proficiency level

        Returns:
            Conversation starter question
        """
        import random

        topic_starters = cls.STARTERS_BY_TOPIC.get(topic, cls.STARTERS_BY_TOPIC["General Conversation"])
        level_starters = topic_starters.get(level, topic_starters.get("B1-B2", []))

        if not level_starters:
            return "Tell me about your day."

        return random.choice(level_starters)

    @classmethod
    def get_topics(cls) -> List[str]:
        """Get list of available topics."""
        return list(cls.STARTERS_BY_TOPIC.keys())
