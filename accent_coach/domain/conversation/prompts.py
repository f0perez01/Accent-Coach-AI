"""
Conversation Tutor Prompt Builder

Provides structured prompts for LLM-based conversation tutoring.
Migrated from prompt_templates.py to follow DDD architecture.
"""

from typing import List, Optional, Dict
from .models import ConversationTurn, ConversationConfig, ConversationMode


class PromptBuilder:
    """
    Builds prompts for conversation tutor LLM interactions.
    Supports different modes (practice, exam) and customization.
    """

    # Base system prompt for practice mode
    PRACTICE_MODE_SYSTEM = """You are a friendly and supportive ESL conversation tutor.

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

    # Exam mode system prompt
    EXAM_MODE_SYSTEM = """You are an ESL examiner assessing a {user_level} student.

Your role:
- Record errors but DO NOT provide corrections yet
- Ask natural follow-up questions to continue the conversation
- Keep the student talking naturally
- Do not mention errors or corrections

Output format:

[ERRORS FOUND]: List of errors (internal note, not shown to student)
[FOLLOW UP QUESTION]: Natural question to continue conversation"""

    # Topic focus addition
    TOPIC_ADDITION = """

Conversation topic: {topic}

Guide the student to practice vocabulary and structures related to this topic.
Ask questions that encourage them to use relevant vocabulary."""

    # Focus area addition
    FOCUS_AREA_ADDITION = """

Focus area: {focus_area}

Pay special attention to errors related to: {focus_area}
Provide targeted practice in this area through your questions."""

    @classmethod
    def build_prompt(
        cls,
        user_transcript: str,
        conversation_history: List[ConversationTurn],
        config: ConversationConfig,
    ) -> Dict[str, str]:
        """
        Build complete prompt for conversation tutor.

        Args:
            user_transcript: What the user just said
            conversation_history: Previous conversation turns
            config: Conversation configuration

        Returns:
            Dict with 'system' and 'user' prompt sections
        """
        # Build system prompt based on mode
        if config.mode == ConversationMode.PRACTICE:
            system_prompt = cls.PRACTICE_MODE_SYSTEM.format(user_level=config.user_level)
        else:  # EXAM mode
            system_prompt = cls.EXAM_MODE_SYSTEM.format(user_level=config.user_level)

        # Add topic if specified
        if config.topic:
            system_prompt += cls.TOPIC_ADDITION.format(topic=config.topic)

        # Add focus area if specified
        if config.focus_area:
            system_prompt += cls.FOCUS_AREA_ADDITION.format(focus_area=config.focus_area)

        # Build user prompt with conversation history
        user_prompt = cls._build_user_prompt(user_transcript, conversation_history, config)

        return {
            "system": system_prompt,
            "user": user_prompt,
        }

    @classmethod
    def _build_user_prompt(
        cls,
        user_transcript: str,
        conversation_history: List[ConversationTurn],
        config: ConversationConfig,
    ) -> str:
        """
        Build user prompt with conversation context.

        Args:
            user_transcript: Current user input
            conversation_history: Previous turns
            config: Configuration

        Returns:
            Formatted user prompt
        """
        parts = []

        # Add conversation history (last N turns for context)
        if conversation_history:
            parts.append("Recent conversation context:")

            # Get last N turns based on config
            recent_turns = conversation_history[-config.max_history_turns:]

            for turn in recent_turns:
                parts.append(f"Student: {turn.user_transcript}")
                # Only include follow-up question from tutor response
                if turn.tutor_response.follow_up_question:
                    parts.append(f"Tutor: {turn.tutor_response.follow_up_question}")

            parts.append("")  # Blank line

        # Add current user input
        parts.append("Student's current message:")
        parts.append(f'"{user_transcript}"')
        parts.append("")
        parts.append("Please analyze and respond following the format above.")

        return "\n".join(parts)

    @classmethod
    def parse_llm_response(cls, llm_text: str) -> Dict[str, str]:
        """
        Parse LLM output into structured fields.

        Expected format:
        [CORRECTION]: ...
        [EXPLANATION]: ...
        [IMPROVED VERSION]: ...
        [FOLLOW UP QUESTION]: ...

        Args:
            llm_text: Raw LLM output

        Returns:
            Parsed dict with structured fields
        """
        result = {
            "correction": "",
            "explanation": "",
            "improved_version": "",
            "follow_up_question": "",
            "errors_detected": [],
        }

        # Define section markers
        sections = {
            "[CORRECTION]": "correction",
            "[EXPLANATION]": "explanation",
            "[IMPROVED VERSION]": "improved_version",
            "[FOLLOW UP QUESTION]": "follow_up_question",
            "[ERRORS FOUND]": "errors_found",  # For exam mode
        }

        # Parse each section
        for marker, key in sections.items():
            if marker in llm_text:
                # Extract text after marker until next marker or end
                start = llm_text.find(marker) + len(marker)
                end = len(llm_text)

                # Find next marker
                for other_marker in sections.keys():
                    if other_marker != marker:
                        next_pos = llm_text.find(other_marker, start)
                        if next_pos != -1 and next_pos < end:
                            end = next_pos

                value = llm_text[start:end].strip()

                # Remove leading colon if present (e.g., "[FOLLOW UP QUESTION]: text")
                if value.startswith(":"):
                    value = value[1:].strip()

                result[key] = value

        # Build full assistant response
        response_parts = []

        if result.get("correction"):
            response_parts.append(result["correction"])

        if result.get("explanation"):
            response_parts.append(result["explanation"])

        if result.get("improved_version"):
            response_parts.append(f"Better way: {result['improved_version']}")

        if result.get("follow_up_question"):
            response_parts.append(result["follow_up_question"])

        result["assistant_response"] = "\n\n".join(response_parts)

        # Extract errors if mentioned
        if "error" in result.get("correction", "").lower() or "mistake" in result.get("correction", "").lower():
            result["errors_detected"].append(result["correction"])

        # Handle exam mode errors
        if result.get("errors_found"):
            result["errors_detected"].append(result["errors_found"])

        return result
