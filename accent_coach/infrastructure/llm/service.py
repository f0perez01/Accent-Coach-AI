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
