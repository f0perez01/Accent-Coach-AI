"""
Groq LLM Provider Implementation
"""

from typing import Dict, Any
from .service import LLMService
from .models import LLMConfig, LLMResponse


class GroqLLMService(LLMService):
    """Groq implementation of LLM service."""

    def __init__(self, api_key: str):
        """
        Args:
            api_key: Groq API key
        """
        self._api_key = api_key
        self._client = None  # Lazy initialization

    def generate(
        self, prompt: str, context: Dict[str, Any], config: LLMConfig
    ) -> LLMResponse:
        """
        Generate text using Groq API.

        Args:
            prompt: Prompt text
            context: Additional context (can be used to enrich prompt)
            config: LLM configuration

        Returns:
            LLM response with text and metadata
        """
        # Ensure client is initialized
        self._ensure_client()

        # Build messages
        messages = [{"role": "user", "content": prompt}]

        # Add system message if context provided
        if context.get("system_message"):
            messages.insert(0, {"role": "system", "content": context["system_message"]})

        try:
            # Call Groq API
            completion = self._client.chat.completions.create(
                messages=messages,
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )

            # Extract response
            text = completion.choices[0].message.content
            tokens_used = completion.usage.total_tokens if completion.usage else 0

            # Estimate cost (Groq pricing as of 2025)
            # llama-3.1-70b: $0.64 per 1M tokens
            cost_per_million = 0.64 if "70b" in config.model else 0.10
            cost_usd = (tokens_used / 1_000_000) * cost_per_million

            return LLMResponse(
                text=text,
                tokens_used=tokens_used,
                cost_usd=cost_usd,
            )

        except Exception as e:
            # Re-raise with more context
            raise RuntimeError(f"Groq API call failed: {str(e)}") from e

    def _ensure_client(self):
        """Lazy initialization of Groq client."""
        if self._client is None:
            try:
                from groq import Groq

                self._client = Groq(api_key=self._api_key)
            except ImportError:
                raise ImportError("groq package not installed. Run: pip install groq")
