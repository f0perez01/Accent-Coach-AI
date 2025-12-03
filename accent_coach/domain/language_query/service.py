"""
Language Query Service (BC8)

Evaluates English expression naturalness for American speakers.
"""

from typing import List, Dict, Optional
from .models import QueryResult, QueryConfig, QueryCategory
from ...infrastructure.llm.service import LLMService


class LanguageQueryService:
    """
    BC8: Language Query Assistant

    Responsibilities:
    - Evaluate expression naturalness (common/rare/unnatural/incorrect)
    - Explain how native speakers use expressions
    - Provide real-life usage examples
    - Suggest native alternatives for unnatural expressions
    - Detect query categories (idiom, phrasal verb, slang, etc.)

    Specialized in American English naturalness evaluation.
    """

    # Category detection keywords
    CATEGORY_KEYWORDS = {
        QueryCategory.PHRASAL_VERB: ["phrasal", "phrasal verb"],
        QueryCategory.IDIOM: ["idiom", "idiomatic"],
        QueryCategory.SLANG: ["slang", "informal", "casual"],
        QueryCategory.GRAMMAR: ["grammar", "tense"],
        QueryCategory.VOCABULARY: ["meaning", "definition"],
    }

    def __init__(self, llm_service: LLMService):
        """
        Initialize Language Query Service.

        Args:
            llm_service: LLM service for generating responses
        """
        self._llm = llm_service

    def process_query(
        self,
        user_query: str,
        conversation_history: Optional[List[Dict]] = None,
        config: Optional[QueryConfig] = None,
    ) -> QueryResult:
        """
        Process language query about English expressions.

        Args:
            user_query: User's question about English language
            conversation_history: Previous Q&A pairs for context (optional)
            config: Optional configuration (defaults used if None)

        Returns:
            QueryResult with LLM response and detected category

        Raises:
            ValueError: If user_query is empty
            RuntimeError: If LLM call fails
        """
        if not user_query or not user_query.strip():
            raise ValueError("User query cannot be empty")

        config = config or QueryConfig()
        conversation_history = conversation_history or []

        try:
            # Call LLM service with query and history
            llm_response = self._llm.generate_language_query_response(
                user_query=user_query,
                conversation_history=conversation_history,
                model=config.model,
                temperature=config.temperature,
            )

            # Detect category based on query keywords
            category = self._detect_category(user_query)

            # Create QueryResult
            result = QueryResult(
                user_query=user_query,
                llm_response=llm_response,
                category=category,
            )

            return result

        except Exception as e:
            # Handle errors gracefully with ERROR category
            return QueryResult(
                user_query=user_query,
                llm_response=f"Error processing query: {str(e)}",
                category=QueryCategory.ERROR,
            )

    def _detect_category(self, query: str) -> QueryCategory:
        """
        Detect query category based on keywords.

        Args:
            query: User's query text

        Returns:
            Detected QueryCategory
        """
        query_lower = query.lower()

        # Check each category's keywords
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword in query_lower for keyword in keywords):
                return category

        # Default to EXPRESSION (naturalness check)
        return QueryCategory.EXPRESSION

    def get_category_description(self, category: QueryCategory) -> str:
        """
        Get human-readable description for a category.

        Args:
            category: QueryCategory enum

        Returns:
            Description string
        """
        descriptions = {
            QueryCategory.IDIOM: "idiomatic expression",
            QueryCategory.PHRASAL_VERB: "phrasal verb",
            QueryCategory.EXPRESSION: "common expression",
            QueryCategory.SLANG: "slang or informal language",
            QueryCategory.GRAMMAR: "grammar question",
            QueryCategory.VOCABULARY: "vocabulary or word meaning",
            QueryCategory.ERROR: "error",
        }
        return descriptions.get(category, "unknown")
