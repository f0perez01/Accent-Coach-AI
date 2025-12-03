"""
Unit tests for Writing Service (BC7)

Testing with mocks (no actual LLM API calls).
"""

import pytest
import json
from unittest.mock import Mock
from accent_coach.domain.writing.service import WritingService
from accent_coach.domain.writing.models import (
    WritingConfig,
    WritingEvaluation,
    CEFRMetrics,
    VocabularyExpansion,
    InterviewQuestion,
    QuestionCategory,
    QuestionDifficulty,
)
from accent_coach.infrastructure.llm.models import LLMResponse


@pytest.mark.unit
class TestWritingService:
    """Test WritingService with mocked LLM service."""

    def test_evaluate_writing_success(self):
        """Test successful writing evaluation."""
        # Given
        mock_llm = Mock()
        mock_llm.generate_writing_feedback.return_value = json.dumps({
            "metrics": {
                "cefr_level": "B2",
                "variety_score": 7
            },
            "corrected": "I have extensive experience in software development.",
            "improvements": [
                "Use 'extensive' instead of basic 'a lot of'",
                "Add specific examples to support claims"
            ],
            "questions": [
                "Can you describe a specific project?",
                "What technologies did you use?"
            ],
            "expansion_words": [
                {
                    "word": "extensive",
                    "ipa": "/ɪkˈstɛnsɪv/",
                    "replaces_simple_word": "a lot of",
                    "meaning_context": "Shows depth and breadth of experience"
                },
                {
                    "word": "proficient",
                    "ipa": "/prəˈfɪʃənt/",
                    "replaces_simple_word": "good at",
                    "meaning_context": "Professional level of skill"
                }
            ]
        })

        service = WritingService(llm_service=mock_llm)

        # When
        evaluation = service.evaluate_writing(
            text="I have experience in software development.",
            config=WritingConfig()
        )

        # Then
        assert isinstance(evaluation, WritingEvaluation)
        assert evaluation.metrics.cefr_level == "B2"
        assert evaluation.metrics.variety_score == 7
        assert "extensive experience" in evaluation.corrected
        assert len(evaluation.improvements) == 2
        assert len(evaluation.questions) == 2
        assert len(evaluation.expansion_words) == 2
        assert evaluation.expansion_words[0].word == "extensive"

        # Verify LLM was called correctly
        mock_llm.generate_writing_feedback.assert_called_once()
        call_args = mock_llm.generate_writing_feedback.call_args
        assert call_args.kwargs["text"] == "I have experience in software development."
        assert call_args.kwargs["model"] == "llama-3.1-8b-instant"
        assert call_args.kwargs["temperature"] == 0.1

    def test_evaluate_writing_empty_text(self):
        """Test that empty text raises ValueError."""
        # Given
        mock_llm = Mock()
        service = WritingService(llm_service=mock_llm)

        # When/Then
        with pytest.raises(ValueError, match="Text cannot be empty"):
            service.evaluate_writing(text="", config=WritingConfig())

        # LLM should not be called
        mock_llm.generate_writing_feedback.assert_not_called()

    def test_evaluate_writing_whitespace_only(self):
        """Test that whitespace-only text raises ValueError."""
        # Given
        mock_llm = Mock()
        service = WritingService(llm_service=mock_llm)

        # When/Then
        with pytest.raises(ValueError, match="Text cannot be empty"):
            service.evaluate_writing(text="   \n  \t  ", config=WritingConfig())

    def test_evaluate_writing_invalid_json_response(self):
        """Test that invalid JSON response raises RuntimeError."""
        # Given
        mock_llm = Mock()
        mock_llm.generate_writing_feedback.return_value = "Not valid JSON {{"

        service = WritingService(llm_service=mock_llm)

        # When/Then
        with pytest.raises(RuntimeError, match="Failed to parse LLM response as JSON"):
            service.evaluate_writing(
                text="Some text",
                config=WritingConfig()
            )

    def test_evaluate_writing_minimal_json_response(self):
        """Test that minimal JSON response is handled gracefully."""
        # Given
        mock_llm = Mock()
        mock_llm.generate_writing_feedback.return_value = json.dumps({
            "metrics": {},
            "corrected": "Corrected text",
            "improvements": [],
            "questions": [],
            "expansion_words": []
        })

        service = WritingService(llm_service=mock_llm)

        # When
        evaluation = service.evaluate_writing(
            text="Original text",
            config=WritingConfig()
        )

        # Then
        assert evaluation.metrics.cefr_level == "B1"  # Default
        assert evaluation.metrics.variety_score == 5  # Default
        assert evaluation.corrected == "Corrected text"
        assert len(evaluation.improvements) == 0
        assert len(evaluation.questions) == 0
        assert len(evaluation.expansion_words) == 0

    def test_evaluate_writing_custom_config(self):
        """Test evaluation with custom configuration."""
        # Given
        mock_llm = Mock()
        mock_llm.generate_writing_feedback.return_value = json.dumps({
            "metrics": {"cefr_level": "C1", "variety_score": 9},
            "corrected": "Advanced text",
            "improvements": [],
            "questions": [],
            "expansion_words": []
        })

        service = WritingService(llm_service=mock_llm)

        custom_config = WritingConfig(
            model="llama-3.1-70b-versatile",
            temperature=0.2,
            max_tokens=1000
        )

        # When
        evaluation = service.evaluate_writing(
            text="Some advanced text",
            config=custom_config
        )

        # Then
        assert evaluation.metrics.cefr_level == "C1"

        # Verify custom config was used
        call_args = mock_llm.generate_writing_feedback.call_args
        assert call_args.kwargs["model"] == "llama-3.1-70b-versatile"
        assert call_args.kwargs["temperature"] == 0.2

    def test_generate_teacher_feedback(self):
        """Test teacher feedback generation."""
        # Given
        mock_llm = Mock()
        mock_llm.generate_teacher_feedback.return_value = (
            "Great work! Your answer shows good understanding. "
            "To make it even stronger, try adding specific examples..."
        )

        service = WritingService(llm_service=mock_llm)

        evaluation = WritingEvaluation(
            corrected="Professional version",
            improvements=["Add examples", "Use stronger verbs"],
            questions=["What project?"],
            expansion_words=[
                VocabularyExpansion(
                    word="implement",
                    ipa="/ˈɪmpləˌmɛnt/",
                    replaces_simple_word="do",
                    meaning_context="Technical execution"
                )
            ],
            metrics=CEFRMetrics(cefr_level="B2", variety_score=7)
        )

        original_text = "I do software projects."

        # When
        feedback = service.generate_teacher_feedback(
            evaluation=evaluation,
            original_text=original_text,
            config=WritingConfig()
        )

        # Then
        assert "Great work" in feedback
        assert "specific examples" in feedback

        # Verify LLM was called correctly
        mock_llm.generate_teacher_feedback.assert_called_once()
        call_args = mock_llm.generate_teacher_feedback.call_args

        # Verify analysis_data is valid JSON
        analysis_data = call_args.kwargs["analysis_data"]
        parsed = json.loads(analysis_data)
        assert parsed["metrics"]["cefr_level"] == "B2"
        assert parsed["corrected"] == "Professional version"

        # Verify original text was passed
        assert call_args.kwargs["original_text"] == original_text

        # Verify temperature is higher (warmth)
        assert call_args.kwargs["temperature"] == 0.4

    def test_compute_variety_score_high_variety(self):
        """Test variety score calculation with high vocabulary variety."""
        # Given
        service = WritingService(llm_service=Mock())
        text = "I leverage comprehensive methodologies to orchestrate scalable solutions."

        # When
        score = service.compute_variety_score(text)

        # Then
        # All words are unique (9/9 = 1.0 ratio)
        assert score >= 9  # Should be very high

    def test_compute_variety_score_low_variety(self):
        """Test variety score calculation with low vocabulary variety."""
        # Given
        service = WritingService(llm_service=Mock())
        text = "I do things and I do them well and I do them fast."

        # When
        score = service.compute_variety_score(text)

        # Then
        # Many repeated words ("I" x3, "do" x3, "them" x3, "and" x2)
        # 8 unique out of 14 total = 0.57 ratio
        assert score <= 6  # Should be medium-low

    def test_compute_variety_score_empty_text(self):
        """Test variety score with empty text."""
        # Given
        service = WritingService(llm_service=Mock())

        # When
        score = service.compute_variety_score("")

        # Then
        assert score == 1  # Minimum score

    def test_compute_variety_score_single_word(self):
        """Test variety score with single word."""
        # Given
        service = WritingService(llm_service=Mock())

        # When
        score = service.compute_variety_score("Hello")

        # Then
        assert score == 10  # Perfect uniqueness

    def test_get_question_by_category_behavioral(self):
        """Test getting behavioral question."""
        # Given
        service = WritingService(llm_service=Mock())

        # When
        question = service.get_question_by_category(QuestionCategory.BEHAVIORAL)

        # Then
        assert question is not None
        assert isinstance(question, InterviewQuestion)
        assert question.category == QuestionCategory.BEHAVIORAL

    def test_get_question_by_category_technical(self):
        """Test getting technical question."""
        # Given
        service = WritingService(llm_service=Mock())

        # When
        question = service.get_question_by_category(QuestionCategory.TECHNICAL)

        # Then
        assert question is not None
        assert question.category == QuestionCategory.TECHNICAL

    def test_get_question_by_category_with_difficulty(self):
        """Test getting question filtered by difficulty."""
        # Given
        service = WritingService(llm_service=Mock())

        # When
        question = service.get_question_by_category(
            category=QuestionCategory.BEHAVIORAL,
            difficulty=QuestionDifficulty.HARD
        )

        # Then
        assert question is not None
        assert question.category == QuestionCategory.BEHAVIORAL
        assert question.difficulty == QuestionDifficulty.HARD

    def test_get_all_questions(self):
        """Test getting all questions from question bank."""
        # Given
        service = WritingService(llm_service=Mock())

        # When
        questions = service.get_all_questions()

        # Then
        assert len(questions) > 0
        assert all(isinstance(q, InterviewQuestion) for q in questions)

        # Verify we have questions from all categories
        categories = {q.category for q in questions}
        assert QuestionCategory.BEHAVIORAL in categories
        assert QuestionCategory.TECHNICAL in categories
        assert QuestionCategory.REMOTE_WORK in categories

        # Verify we have questions at all difficulty levels
        difficulties = {q.difficulty for q in questions}
        assert QuestionDifficulty.EASY in difficulties
        assert QuestionDifficulty.MEDIUM in difficulties
        assert QuestionDifficulty.HARD in difficulties

    def test_question_xp_values(self):
        """Test that questions have correct XP values."""
        # Given
        service = WritingService(llm_service=Mock())

        # When
        easy_q = service.get_question_by_category(
            QuestionCategory.BEHAVIORAL,
            QuestionDifficulty.EASY
        )
        medium_q = service.get_question_by_category(
            QuestionCategory.TECHNICAL,
            QuestionDifficulty.MEDIUM
        )
        hard_q = service.get_question_by_category(
            QuestionCategory.REMOTE_WORK,
            QuestionDifficulty.HARD
        )

        # Then
        assert easy_q.get_xp_value() == 10
        assert medium_q.get_xp_value() == 20
        assert hard_q.get_xp_value() == 40


@pytest.mark.unit
class TestWritingServiceIntegration:
    """Integration tests for WritingService with realistic scenarios."""

    def test_complete_evaluation_workflow(self):
        """Test complete evaluation workflow from text to feedback."""
        # Given
        mock_llm = Mock()

        # Mock writing evaluation
        mock_llm.generate_writing_feedback.return_value = json.dumps({
            "metrics": {"cefr_level": "B2", "variety_score": 7},
            "corrected": "I have extensive experience developing scalable web applications.",
            "improvements": [
                "Quantify your experience with specific numbers",
                "Mention technologies you're proficient in"
            ],
            "questions": [
                "How many years of experience do you have?",
                "What frameworks have you used?"
            ],
            "expansion_words": [
                {
                    "word": "scalable",
                    "ipa": "/ˈskeɪləbəl/",
                    "replaces_simple_word": "big",
                    "meaning_context": "Technical term for systems that grow"
                }
            ]
        })

        # Mock teacher feedback
        mock_llm.generate_teacher_feedback.return_value = (
            "Nice work! Your answer demonstrates solid experience. "
            "To make it even stronger for interviews, consider adding "
            "specific metrics like '5 years' or '10+ projects'. "
            "Keep practicing!"
        )

        service = WritingService(llm_service=mock_llm)

        original_text = "I have experience building websites."

        # When
        # Step 1: Evaluate writing
        evaluation = service.evaluate_writing(
            text=original_text,
            config=WritingConfig()
        )

        # Step 2: Generate teacher feedback
        feedback = service.generate_teacher_feedback(
            evaluation=evaluation,
            original_text=original_text
        )

        # Then
        # Verify evaluation
        assert evaluation.metrics.cefr_level == "B2"
        assert "extensive experience" in evaluation.corrected
        assert len(evaluation.improvements) == 2
        assert len(evaluation.expansion_words) == 1

        # Verify feedback
        assert "Nice work" in feedback
        assert "Keep practicing" in feedback

        # Verify both LLM methods were called
        assert mock_llm.generate_writing_feedback.call_count == 1
        assert mock_llm.generate_teacher_feedback.call_count == 1

    def test_interview_practice_session(self):
        """Test realistic interview practice session."""
        # Given
        mock_llm = Mock()
        mock_llm.generate_writing_feedback.return_value = json.dumps({
            "metrics": {"cefr_level": "C1", "variety_score": 8},
            "corrected": "Polished answer",
            "improvements": ["Add STAR method"],
            "questions": ["Follow-up?"],
            "expansion_words": []
        })

        service = WritingService(llm_service=mock_llm)

        # When
        # Step 1: Get a practice question
        question = service.get_question_by_category(
            category=QuestionCategory.BEHAVIORAL,
            difficulty=QuestionDifficulty.MEDIUM
        )

        # Step 2: Student writes answer
        student_answer = "I worked on a challenging project last year..."

        # Step 3: Evaluate answer
        evaluation = service.evaluate_writing(
            text=student_answer,
            config=WritingConfig()
        )

        # Then
        assert question is not None
        assert question.get_xp_value() == 20  # Medium difficulty
        assert evaluation.metrics.cefr_level == "C1"
        assert isinstance(evaluation, WritingEvaluation)
