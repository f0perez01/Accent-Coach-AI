"""
Unit tests for Language Query Service (BC8)

Testing with mocks (no actual LLM API calls).
"""

import pytest
from unittest.mock import Mock
from accent_coach.domain.language_query.service import LanguageQueryService
from accent_coach.domain.language_query.models import (
    QueryResult,
    QueryConfig,
    QueryCategory,
)


@pytest.mark.unit
class TestLanguageQueryService:
    """Test LanguageQueryService with mocked LLM service."""

    def test_process_query_success(self):
        """Test successful query processing."""
        # Given
        mock_llm = Mock()
        mock_llm.generate_language_query_response.return_value = (
            "The expression 'touch base' is commonly used in American English, "
            "especially in business contexts. Example: 'Let's touch base next week.'"
        )

        service = LanguageQueryService(llm_service=mock_llm)

        # When
        result = service.process_query(
            user_query="Is 'touch base' commonly used?",
            conversation_history=[],
            config=QueryConfig()
        )

        # Then
        assert isinstance(result, QueryResult)
        assert result.user_query == "Is 'touch base' commonly used?"
        assert "commonly used" in result.llm_response
        assert result.category == QueryCategory.EXPRESSION
        assert result.timestamp is not None

        # Verify LLM was called correctly
        mock_llm.generate_language_query_response.assert_called_once()
        call_args = mock_llm.generate_language_query_response.call_args
        assert call_args.kwargs["user_query"] == "Is 'touch base' commonly used?"
        assert call_args.kwargs["conversation_history"] == []
        assert call_args.kwargs["model"] == "llama-3.1-8b-instant"
        assert call_args.kwargs["temperature"] == 0.25

    def test_process_query_with_conversation_history(self):
        """Test query processing with conversation history."""
        # Given
        mock_llm = Mock()
        mock_llm.generate_language_query_response.return_value = (
            "Yes, it's commonly used in professional emails."
        )

        service = LanguageQueryService(llm_service=mock_llm)

        conversation_history = [
            {
                "user_query": "What does 'touch base' mean?",
                "llm_response": "It means to contact someone briefly."
            }
        ]

        # When
        result = service.process_query(
            user_query="Is it commonly used?",
            conversation_history=conversation_history
        )

        # Then
        assert result.user_query == "Is it commonly used?"
        assert "commonly used" in result.llm_response

        # Verify history was passed to LLM
        call_args = mock_llm.generate_language_query_response.call_args
        assert call_args.kwargs["conversation_history"] == conversation_history

    def test_process_query_empty_query(self):
        """Test that empty query raises ValueError."""
        # Given
        mock_llm = Mock()
        service = LanguageQueryService(llm_service=mock_llm)

        # When/Then
        with pytest.raises(ValueError, match="User query cannot be empty"):
            service.process_query(user_query="", conversation_history=[])

        # LLM should not be called
        mock_llm.generate_language_query_response.assert_not_called()

    def test_process_query_whitespace_only(self):
        """Test that whitespace-only query raises ValueError."""
        # Given
        mock_llm = Mock()
        service = LanguageQueryService(llm_service=mock_llm)

        # When/Then
        with pytest.raises(ValueError, match="User query cannot be empty"):
            service.process_query(user_query="   \n  \t  ")

    def test_process_query_with_custom_config(self):
        """Test query processing with custom configuration."""
        # Given
        mock_llm = Mock()
        mock_llm.generate_language_query_response.return_value = "Response"

        service = LanguageQueryService(llm_service=mock_llm)

        custom_config = QueryConfig(
            model="llama-3.1-70b-versatile",
            temperature=0.3,
            max_tokens=600
        )

        # When
        result = service.process_query(
            user_query="Test query",
            config=custom_config
        )

        # Then
        assert result.llm_response == "Response"

        # Verify custom config was used
        call_args = mock_llm.generate_language_query_response.call_args
        assert call_args.kwargs["model"] == "llama-3.1-70b-versatile"
        assert call_args.kwargs["temperature"] == 0.3

    def test_process_query_default_config(self):
        """Test query processing with default configuration."""
        # Given
        mock_llm = Mock()
        mock_llm.generate_language_query_response.return_value = "Response"

        service = LanguageQueryService(llm_service=mock_llm)

        # When
        result = service.process_query(user_query="Test query")

        # Then
        # Verify defaults were used
        call_args = mock_llm.generate_language_query_response.call_args
        assert call_args.kwargs["model"] == "llama-3.1-8b-instant"
        assert call_args.kwargs["temperature"] == 0.25
        assert call_args.kwargs["conversation_history"] == []

    def test_process_query_llm_error_handling(self):
        """Test that LLM errors are handled gracefully."""
        # Given
        mock_llm = Mock()
        mock_llm.generate_language_query_response.side_effect = Exception("API Error")

        service = LanguageQueryService(llm_service=mock_llm)

        # When
        result = service.process_query(user_query="Test query")

        # Then
        assert result.category == QueryCategory.ERROR
        assert "Error processing query" in result.llm_response
        assert "API Error" in result.llm_response

    def test_detect_category_phrasal_verb(self):
        """Test category detection for phrasal verbs."""
        # Given
        mock_llm = Mock()
        mock_llm.generate_language_query_response.return_value = "Response"

        service = LanguageQueryService(llm_service=mock_llm)

        # When
        result = service.process_query(
            user_query="What does the phrasal verb 'give up' mean?"
        )

        # Then
        assert result.category == QueryCategory.PHRASAL_VERB

    def test_detect_category_idiom(self):
        """Test category detection for idioms."""
        # Given
        mock_llm = Mock()
        mock_llm.generate_language_query_response.return_value = "Response"

        service = LanguageQueryService(llm_service=mock_llm)

        # When
        result = service.process_query(
            user_query="Is 'kick the bucket' an idiom?"
        )

        # Then
        assert result.category == QueryCategory.IDIOM

    def test_detect_category_slang(self):
        """Test category detection for slang."""
        # Given
        mock_llm = Mock()
        mock_llm.generate_language_query_response.return_value = "Response"

        service = LanguageQueryService(llm_service=mock_llm)

        # When
        result = service.process_query(
            user_query="What does the slang word 'lit' mean?"
        )

        # Then
        assert result.category == QueryCategory.SLANG

    def test_detect_category_grammar(self):
        """Test category detection for grammar questions."""
        # Given
        mock_llm = Mock()
        mock_llm.generate_language_query_response.return_value = "Response"

        service = LanguageQueryService(llm_service=mock_llm)

        # When
        result = service.process_query(
            user_query="What's the difference between past and present tense?"
        )

        # Then
        assert result.category == QueryCategory.GRAMMAR

    def test_detect_category_vocabulary(self):
        """Test category detection for vocabulary questions."""
        # Given
        mock_llm = Mock()
        mock_llm.generate_language_query_response.return_value = "Response"

        service = LanguageQueryService(llm_service=mock_llm)

        # When
        result = service.process_query(
            user_query="What's the meaning of 'ubiquitous'?"
        )

        # Then
        assert result.category == QueryCategory.VOCABULARY

    def test_detect_category_default_expression(self):
        """Test that default category is EXPRESSION."""
        # Given
        mock_llm = Mock()
        mock_llm.generate_language_query_response.return_value = "Response"

        service = LanguageQueryService(llm_service=mock_llm)

        # When
        result = service.process_query(
            user_query="Is 'I am good' natural?"
        )

        # Then
        assert result.category == QueryCategory.EXPRESSION

    def test_get_category_description(self):
        """Test category description retrieval."""
        # Given
        service = LanguageQueryService(llm_service=Mock())

        # When/Then
        assert service.get_category_description(QueryCategory.IDIOM) == "idiomatic expression"
        assert service.get_category_description(QueryCategory.PHRASAL_VERB) == "phrasal verb"
        assert service.get_category_description(QueryCategory.EXPRESSION) == "common expression"
        assert service.get_category_description(QueryCategory.SLANG) == "slang or informal language"
        assert service.get_category_description(QueryCategory.GRAMMAR) == "grammar question"
        assert service.get_category_description(QueryCategory.VOCABULARY) == "vocabulary or word meaning"
        assert service.get_category_description(QueryCategory.ERROR) == "error"


@pytest.mark.unit
class TestLanguageQueryServiceIntegration:
    """Integration tests for LanguageQueryService with realistic scenarios."""

    def test_complete_query_workflow(self):
        """Test complete query workflow."""
        # Given
        mock_llm = Mock()
        mock_llm.generate_language_query_response.return_value = (
            "The expression 'touch base' is commonly used in American business English. "
            "It means to briefly make contact with someone to check status or coordinate. "
            "Examples:\n"
            "1. 'Let's touch base next week about the project.'\n"
            "2. 'I'll touch base with you after the meeting.'\n"
            "3. 'Touch base with me if you need any help.'\n"
            "This is informal but professional, commonly used in workplace communication."
        )

        service = LanguageQueryService(llm_service=mock_llm)

        # When
        result = service.process_query(
            user_query="Is 'touch base' commonly used in American English?",
            conversation_history=[]
        )

        # Then
        assert result.user_query == "Is 'touch base' commonly used in American English?"
        assert "commonly used" in result.llm_response
        assert "Examples:" in result.llm_response
        assert result.category == QueryCategory.EXPRESSION
        assert result.timestamp is not None

    def test_multi_turn_conversation(self):
        """Test multi-turn conversation with context."""
        # Given
        mock_llm = Mock()

        # First turn
        mock_llm.generate_language_query_response.return_value = (
            "'Touch base' means to make brief contact with someone."
        )

        service = LanguageQueryService(llm_service=mock_llm)

        result1 = service.process_query(
            user_query="What does 'touch base' mean?",
            conversation_history=[]
        )

        # Second turn with history
        mock_llm.generate_language_query_response.return_value = (
            "Yes, it's very commonly used in professional settings."
        )

        conversation_history = [
            {
                "user_query": result1.user_query,
                "llm_response": result1.llm_response
            }
        ]

        result2 = service.process_query(
            user_query="Is it commonly used?",
            conversation_history=conversation_history
        )

        # Then
        assert result1.category == QueryCategory.EXPRESSION
        assert result2.category == QueryCategory.EXPRESSION
        assert "commonly used" in result2.llm_response

        # Verify history was passed
        assert mock_llm.generate_language_query_response.call_count == 2

    def test_different_query_types(self):
        """Test processing different types of queries."""
        # Given
        mock_llm = Mock()
        mock_llm.generate_language_query_response.return_value = "Response"

        service = LanguageQueryService(llm_service=mock_llm)

        # When - Test multiple query types
        queries = [
            ("What's a phrasal verb?", QueryCategory.PHRASAL_VERB),
            ("Explain this idiom", QueryCategory.IDIOM),
            ("Is this slang?", QueryCategory.SLANG),
            ("Grammar question here", QueryCategory.GRAMMAR),
            ("What's the meaning?", QueryCategory.VOCABULARY),
            ("Is this natural?", QueryCategory.EXPRESSION),
        ]

        for query_text, expected_category in queries:
            result = service.process_query(user_query=query_text)
            assert result.category == expected_category
