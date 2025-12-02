"""
LLM infrastructure models
"""

from dataclasses import dataclass


@dataclass
class LLMConfig:
    """Configuration for LLM generation."""
    model: str = "llama-3.1-70b-versatile"
    temperature: float = 0.0
    max_tokens: int = 500


@dataclass
class LLMResponse:
    """Response from LLM."""
    text: str
    tokens_used: int = 0
    cost_usd: float = 0.0
