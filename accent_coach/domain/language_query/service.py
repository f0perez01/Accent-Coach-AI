"""
Language Query Service (BC9)
"""

from typing import List, Dict
from .models import QueryResult


class LanguageQueryService:
    """
    BC9: Language Query Assistant

    Responsibilities:
    - Answer language questions
    - Provide explanations (idioms, phrasal verbs, grammar)

    Dependencies:
    - LLMService (BC6)
    - LanguageQueryRepository (Infrastructure)
    """

    def __init__(self, llm_service, repository):
        """
        Args:
            llm_service: LLMService instance
            repository: LanguageQueryRepository instance
        """
        self._llm = llm_service
        self._repo = repository

    def process_query(
        self, user_query: str, conversation_history: List[Dict], user_id: str
    ) -> QueryResult:
        """
        Process language query.

        Args:
            user_query: User's question
            conversation_history: Previous queries
            user_id: User identifier

        Returns:
            Query result with LLM response
        """
        # TODO: Implementation in Sprint 6
        # 1. Generate LLM response
        # 2. Create QueryResult
        # 3. Save to repository
        raise NotImplementedError("To be implemented in Sprint 6")
