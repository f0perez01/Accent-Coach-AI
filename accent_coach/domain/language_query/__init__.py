"""
BC9: Language Query Assistant

Responsibilities:
- Answer language questions (idioms, grammar, vocabulary)
- Maintain chat history
- Provide explanations

Dependencies: BC6 (LLM)
"""

from .service import LanguageQueryService
from .models import QueryResult

__all__ = ["LanguageQueryService", "QueryResult"]
