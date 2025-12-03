"""
LLM Service Abstract Interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from .models import LLMConfig, LLMResponse


class LLMService(ABC):
    """
    BC6: LLM Orchestration - ABSTRACTION

    Abstract interface for LLM providers.
    Allows switching between Groq, OpenAI, Claude, local models.
    """

    @abstractmethod
    def generate(
        self, prompt: str, context: Dict[str, Any], config: LLMConfig
    ) -> LLMResponse:
        """
        Generate text from prompt + context.

        Args:
            prompt: Template or direct prompt
            context: Additional context for generation
            config: LLM configuration

        Returns:
            LLM response with text and metadata
        """
        pass

    def generate_pronunciation_feedback(
        self,
        reference_text: str,
        per_word_comparison: List[Dict],
        model: str,
    ) -> str:
        """
        Domain-specific: Generate pronunciation feedback.

        Args:
            reference_text: Expected text
            per_word_comparison: Per-word phoneme comparison
            model: LLM model to use

        Returns:
            Feedback text
        """
        # Build prompt
        prompt = self._build_pronunciation_prompt(
            reference_text, per_word_comparison
        )

        config = LLMConfig(model=model, temperature=0.0)
        response = self.generate(prompt, {}, config)
        return response.text

    def generate_conversation_feedback(
        self,
        system_prompt: str,
        user_message: str,
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 500,
    ) -> str:
        """
        Domain-specific: Generate conversation tutor feedback.

        Args:
            system_prompt: System instructions for the LLM
            user_message: User's message to analyze
            model: LLM model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Feedback text with corrections and follow-up
        """
        # Build combined prompt
        combined_prompt = f"{system_prompt}\n\n{user_message}"

        config = LLMConfig(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        response = self.generate(combined_prompt, {}, config)
        return response.text

    def generate_writing_feedback(
        self,
        text: str,
        model: str,
        temperature: float = 0.1,
    ) -> str:
        """
        Domain-specific: Generate writing evaluation feedback.

        Analyzes written text for job interviews, providing:
        - CEFR level assessment
        - Professional polish
        - Improvement suggestions
        - Vocabulary expansion recommendations

        Args:
            text: Student's written answer
            model: LLM model to use
            temperature: Sampling temperature (default 0.1 for consistency)

        Returns:
            JSON string with evaluation results
        """
        prompt = self._build_writing_prompt(text)
        config = LLMConfig(model=model, temperature=temperature, max_tokens=800)
        response = self.generate(prompt, {}, config)
        return response.text

    def generate_teacher_feedback(
        self,
        analysis_data: str,
        original_text: str,
        model: str,
        temperature: float = 0.4,
    ) -> str:
        """
        Domain-specific: Generate warm teacher-style feedback email.

        Args:
            analysis_data: JSON string of analysis results
            original_text: Student's original text
            model: LLM model to use
            temperature: Sampling temperature (default 0.4 for warmth)

        Returns:
            Friendly feedback email body
        """
        prompt = self._build_teacher_feedback_prompt(analysis_data, original_text)
        config = LLMConfig(model=model, temperature=temperature, max_tokens=600)
        response = self.generate(prompt, {}, config)
        return response.text

    def generate_language_query_response(
        self,
        user_query: str,
        conversation_history: List[Dict],
        model: str,
        temperature: float = 0.25,
    ) -> str:
        """
        Domain-specific: Generate response to language query.

        Evaluates English expressions for naturalness, providing:
        - Commonality assessment (common/rare/unnatural/incorrect)
        - Real-life usage examples
        - Native alternatives if needed
        - Register analysis (formal/informal)

        Args:
            user_query: User's question about English language
            conversation_history: Previous Q&A pairs for context
            model: LLM model to use
            temperature: Sampling temperature (default 0.25 for precision)

        Returns:
            LLM response with explanation and examples
        """
        prompt = self._build_language_query_prompt(user_query, conversation_history)
        config = LLMConfig(model=model, temperature=temperature, max_tokens=450)
        response = self.generate(prompt, {}, config)
        return response.text

    def _build_pronunciation_prompt(
        self, reference_text: str, per_word_comparison: List[Dict]
    ) -> str:
        """Build pronunciation coaching prompt."""
        # TODO: Extract to prompt template
        errors = [w for w in per_word_comparison if not w.get("match", False)]
        prompt = f"""You are a pronunciation coach. The student tried to say: "{reference_text}"

Errors detected:
{errors}

Provide encouraging, specific feedback on how to improve."""
        return prompt

    def _build_writing_prompt(self, text: str) -> str:
        """Build writing evaluation prompt for job interview context."""
        return f"""
Role: Senior Tech Recruiter & Communication Coach for US Companies.
Goal: Optimize the candidate's answer for clarity, professionalism, and impact in a remote software engineering interview context.
Input Text: "{text}"

INSTRUCTIONS:
Analyze the text and return a valid JSON object.

REQUIRED JSON STRUCTURE (Do not deviate):
{{
    "metrics": {{
        "cefr_level": "String (e.g., B2, C1, C2)",
        "variety_score": Integer (1-10 based on professional vocabulary)
    }},
    "corrected": "String (Polished, professional version suitable for a job interview)",
    "improvements": ["String (Specific advice on tone, clarity, or STAR method)", "String", "String"],
    "questions": ["String (Follow-up interview question)", "String (Technical or behavioral probe)"],
    "expansion_words": [
        {{
            "word": "String (Power verb or industry term)",
            "ipa": "String (IPA pronunciation)",
            "replaces_simple_word": "String (The weaker word used)",
            "meaning_context": "String (Why this word is better for interviews)"
        }},
        ... (Total 3 items)
    ]
}}

Output ONLY valid JSON. No markdown, no explanation."""

    def _build_teacher_feedback_prompt(self, analysis_data: str, original_text: str) -> str:
        """Build teacher feedback prompt for warm, supportive email."""
        return f"""
You are a friendly English teacher who helps ESL students.
Rewrite the following analysis as warm, constructive feedback.
Tone: kind, supportive, motivating.
Format: an email addressed directly to the student.

Student's original answer:
{original_text}

Analysis data:
{analysis_data}

Produce ONLY the email body. No JSON, no explanation, no greeting lines like "Here is your email"."""

    def _build_language_query_prompt(self, user_query: str, conversation_history: List[Dict]) -> str:
        """Build language query prompt with conversation context."""
        # Build system prompt
        system_prompt = """
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
- incorrect or unnatural phrasing patterns"""

        # Build context from history (last 3 exchanges)
        context_parts = [system_prompt, "\n\n"]

        if conversation_history:
            context_parts.append("Conversation history:\n")
            for msg in conversation_history[-3:]:  # Last 3 pairs
                user_q = msg.get("user_query", "")
                llm_r = msg.get("llm_response", "")
                if user_q:
                    context_parts.append(f"User: {user_q}\n")
                if llm_r:
                    context_parts.append(f"Assistant: {llm_r}\n")
            context_parts.append("\n")

        context_parts.append(f"Current question: {user_query}")

        return "".join(context_parts)
