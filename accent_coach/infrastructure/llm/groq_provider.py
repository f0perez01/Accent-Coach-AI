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
            context: Additional context (unused for now)
            config: LLM configuration

        Returns:
            LLM response
        """
        # TODO: Implementation in Sprint 1
        # 1. Initialize Groq client if needed
        # 2. Call API
        # 3. Parse response
        # 4. Return LLMResponse
        raise NotImplementedError("To be implemented in Sprint 1")

    def _ensure_client(self):
        """Lazy initialization of Groq client."""
        if self._client is None:
            try:
                from groq import Groq

                self._client = Groq(api_key=self._api_key)
            except ImportError:
                raise ImportError("groq package not installed. Run: pip install groq")
