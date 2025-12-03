"""
Unit tests for LLM Service

Testing with mocks (no actual API calls).
"""

import pytest
from unittest.mock import Mock, patch
from accent_coach.infrastructure.llm.groq_provider import GroqLLMService
from accent_coach.infrastructure.llm.models import LLMConfig, LLMResponse


@pytest.mark.unit
class TestGroqLLMService:
    """Test GroqLLMService with mocked Groq API."""

    def test_generate_calls_groq_api(self):
        """Test that generate() calls Groq API correctly."""
        # Given
        service = GroqLLMService(api_key="test_api_key")

        # Mock the Groq client
        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock(message=Mock(content="Generated text"))]
        mock_completion.usage = Mock(total_tokens=100)
        mock_client.chat.completions.create.return_value = mock_completion

        service._client = mock_client

        config = LLMConfig(model="llama-3.1-70b-versatile", temperature=0.0)

        # When
        response = service.generate("Test prompt", {}, config)

        # Then
        assert isinstance(response, LLMResponse)
        assert response.text == "Generated text"
        assert response.tokens_used == 100
        assert response.cost_usd > 0  # Should calculate cost

        # Verify API was called correctly
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "llama-3.1-70b-versatile"
        assert call_args.kwargs["temperature"] == 0.0

    def test_generate_with_system_message(self):
        """Test that system message is included if provided in context."""
        # Given
        service = GroqLLMService(api_key="test_api_key")

        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock(message=Mock(content="Response"))]
        mock_completion.usage = Mock(total_tokens=50)
        mock_client.chat.completions.create.return_value = mock_completion

        service._client = mock_client

        config = LLMConfig()
        context = {"system_message": "You are a helpful assistant."}

        # When
        response = service.generate("User prompt", context, config)

        # Then
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]

        # Should have system message first, then user message
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful assistant."
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "User prompt"

    def test_cost_calculation_70b_model(self):
        """Test cost calculation for 70b model."""
        # Given
        service = GroqLLMService(api_key="test_api_key")

        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock(message=Mock(content="Text"))]
        mock_completion.usage = Mock(total_tokens=1000)
        mock_client.chat.completions.create.return_value = mock_completion

        service._client = mock_client

        config = LLMConfig(model="llama-3.1-70b-versatile")

        # When
        response = service.generate("Prompt", {}, config)

        # Then
        # 1000 tokens * $0.64 per 1M = $0.00064
        expected_cost = (1000 / 1_000_000) * 0.64
        assert abs(response.cost_usd - expected_cost) < 0.0001

    def test_cost_calculation_8b_model(self):
        """Test cost calculation for 8b model."""
        # Given
        service = GroqLLMService(api_key="test_api_key")

        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock(message=Mock(content="Text"))]
        mock_completion.usage = Mock(total_tokens=1000)
        mock_client.chat.completions.create.return_value = mock_completion

        service._client = mock_client

        config = LLMConfig(model="llama-3.1-8b-instant")

        # When
        response = service.generate("Prompt", {}, config)

        # Then
        # 1000 tokens * $0.10 per 1M = $0.0001
        expected_cost = (1000 / 1_000_000) * 0.10
        assert abs(response.cost_usd - expected_cost) < 0.0001

    def test_api_error_handling(self):
        """Test that API errors are handled properly."""
        # Given
        service = GroqLLMService(api_key="test_api_key")

        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        service._client = mock_client

        config = LLMConfig()

        # When/Then
        with pytest.raises(RuntimeError, match="Groq API call failed"):
            service.generate("Prompt", {}, config)

    def test_lazy_client_initialization(self):
        """Test that Groq client is initialized lazily."""
        # Given
        service = GroqLLMService(api_key="test_api_key")

        # Then
        assert service._client is None  # Should be None initially

        # When
        with patch("groq.Groq") as MockGroq:
            mock_groq_instance = Mock()
            MockGroq.return_value = mock_groq_instance

            service._ensure_client()

            # Then
            assert service._client == mock_groq_instance
            MockGroq.assert_called_once_with(api_key="test_api_key")


@pytest.mark.unit
class TestLLMServiceDomainMethods:
    """Test domain-specific methods in LLMService."""

    def test_generate_pronunciation_feedback(self):
        """Test pronunciation feedback generation."""
        # Given
        service = GroqLLMService(api_key="test_api_key")

        # Mock generate method
        service.generate = Mock(return_value=LLMResponse(
            text="Great job on pronunciation!",
            tokens_used=50,
            cost_usd=0.001
        ))

        per_word_comparison = [
            {"word": "hello", "match": True},
            {"word": "world", "match": False},
        ]

        # When
        feedback = service.generate_pronunciation_feedback(
            reference_text="hello world",
            per_word_comparison=per_word_comparison,
            model="llama-3.1-70b-versatile"
        )

        # Then
        assert feedback == "Great job on pronunciation!"

        # Verify generate was called
        service.generate.assert_called_once()
        call_args = service.generate.call_args

        # Should build a prompt mentioning the errors
        prompt = call_args[0][0]
        assert "hello world" in prompt

    def test_generate_conversation_feedback(self):
        """Test conversation feedback generation."""
        # Given
        service = GroqLLMService(api_key="test_api_key")

        # Mock generate method
        service.generate = Mock(return_value=LLMResponse(
            text="[CORRECTION]: Great! [FOLLOW UP QUESTION]: What else?",
            tokens_used=100,
            cost_usd=0.002
        ))

        # When
        feedback = service.generate_conversation_feedback(
            system_prompt="You are a tutor",
            user_message="I go yesterday",
            model="llama-3.1-70b-versatile",
            temperature=0.3,
            max_tokens=500
        )

        # Then
        assert "[CORRECTION]" in feedback
        assert "[FOLLOW UP QUESTION]" in feedback

        # Verify generate was called with proper config
        service.generate.assert_called_once()

    def test_generate_writing_feedback(self):
        """Test writing evaluation feedback generation."""
        # Given
        service = GroqLLMService(api_key="test_api_key")

        # Mock generate method with JSON response
        service.generate = Mock(return_value=LLMResponse(
            text='{"metrics": {"cefr_level": "B2", "variety_score": 7}, "corrected": "Professional version"}',
            tokens_used=200,
            cost_usd=0.003
        ))

        # When
        feedback = service.generate_writing_feedback(
            text="I have experience in software development.",
            model="llama-3.1-8b-instant",
            temperature=0.1
        )

        # Then
        assert "cefr_level" in feedback
        assert "B2" in feedback

        # Verify prompt includes job interview context
        service.generate.assert_called_once()
        call_args = service.generate.call_args
        prompt = call_args[0][0]
        assert "Tech Recruiter" in prompt
        assert "interview" in prompt.lower()

    def test_generate_teacher_feedback(self):
        """Test teacher-style feedback generation."""
        # Given
        service = GroqLLMService(api_key="test_api_key")

        # Mock generate method
        service.generate = Mock(return_value=LLMResponse(
            text="Great job! Keep practicing your grammar.",
            tokens_used=80,
            cost_usd=0.002
        ))

        analysis_data = '{"metrics": {"cefr_level": "B1"}}'
        original_text = "I like programming"

        # When
        feedback = service.generate_teacher_feedback(
            analysis_data=analysis_data,
            original_text=original_text,
            model="llama-3.1-8b-instant",
            temperature=0.4
        )

        # Then
        assert "Great job" in feedback

        # Verify prompt includes warm tone instructions
        service.generate.assert_called_once()
        call_args = service.generate.call_args
        prompt = call_args[0][0]
        assert "friendly" in prompt.lower() or "warm" in prompt.lower()

    def test_generate_language_query_response(self):
        """Test language query response generation."""
        # Given
        service = GroqLLMService(api_key="test_api_key")

        # Mock generate method
        service.generate = Mock(return_value=LLMResponse(
            text="This expression is commonly used in American English. Example: 'Let's touch base next week.'",
            tokens_used=120,
            cost_usd=0.003
        ))

        conversation_history = [
            {"user_query": "What does 'touch base' mean?", "llm_response": "It means to contact someone briefly."}
        ]

        # When
        response = service.generate_language_query_response(
            user_query="Is 'touch base' commonly used?",
            conversation_history=conversation_history,
            model="llama-3.1-8b-instant",
            temperature=0.25
        )

        # Then
        assert "commonly used" in response

        # Verify prompt includes naturalness evaluation instructions
        service.generate.assert_called_once()
        call_args = service.generate.call_args
        prompt = call_args[0][0]
        assert "natural" in prompt.lower()
        assert "American speaker" in prompt

    def test_generate_language_query_without_history(self):
        """Test language query without conversation history."""
        # Given
        service = GroqLLMService(api_key="test_api_key")

        # Mock generate method
        service.generate = Mock(return_value=LLMResponse(
            text="This is a natural expression.",
            tokens_used=60,
            cost_usd=0.001
        ))

        # When
        response = service.generate_language_query_response(
            user_query="Is 'kick the bucket' common?",
            conversation_history=[],
            model="llama-3.1-8b-instant"
        )

        # Then
        assert response == "This is a natural expression."

        # Should still work without history
        service.generate.assert_called_once()
