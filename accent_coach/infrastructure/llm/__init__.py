"""
BC6: LLM Orchestration

Abstract interface for LLM providers.
Allows switching between Groq, OpenAI, Claude, local models.
"""

from .service import LLMService
from .groq_provider import GroqLLMService
from .models import LLMConfig, LLMResponse

__all__ = ["LLMService", "GroqLLMService", "LLMConfig", "LLMResponse"]
