"""
Writing Coach Service (BC7)

Provides writing evaluation and feedback for job interview practice.
"""

import json
import re
from typing import Optional, List
from .models import (
    WritingConfig,
    WritingEvaluation,
    CEFRMetrics,
    VocabularyExpansion,
    InterviewQuestion,
    QuestionCategory,
    QuestionDifficulty,
)
from ...infrastructure.llm.service import LLMService


class WritingService:
    """
    BC7: Writing Coach - Domain Service

    Responsibilities:
    - Evaluate written answers for job interview preparation
    - Calculate vocabulary variety and CEFR level
    - Generate professional corrections and improvements
    - Provide warm teacher-style feedback
    - Manage interview question bank
    """

    def __init__(self, llm_service: LLMService):
        """
        Initialize Writing Service.

        Args:
            llm_service: LLM service for generating feedback
        """
        self._llm = llm_service
        self._question_bank = self._initialize_question_bank()

    def evaluate_writing(
        self,
        text: str,
        config: Optional[WritingConfig] = None,
    ) -> WritingEvaluation:
        """
        Evaluate written text for job interview context.

        Args:
            text: Student's written answer
            config: Optional configuration (defaults used if None)

        Returns:
            WritingEvaluation with corrections, improvements, and metrics

        Raises:
            ValueError: If text is empty
            RuntimeError: If LLM call fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        config = config or WritingConfig()

        # Call LLM for evaluation
        llm_response = self._llm.generate_writing_feedback(
            text=text,
            model=config.model,
            temperature=config.temperature,
        )

        # Parse JSON response
        try:
            evaluation_data = json.loads(llm_response)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse LLM response as JSON: {e}")

        # Extract and validate fields
        metrics_data = evaluation_data.get("metrics", {})
        expansion_data = evaluation_data.get("expansion_words", [])

        # Build CEFRMetrics
        metrics = CEFRMetrics(
            cefr_level=metrics_data.get("cefr_level", "B1"),
            variety_score=metrics_data.get("variety_score", 5),
        )

        # Build VocabularyExpansion list
        expansion_words = [
            VocabularyExpansion(
                word=item.get("word", ""),
                ipa=item.get("ipa", ""),
                replaces_simple_word=item.get("replaces_simple_word", ""),
                meaning_context=item.get("meaning_context", ""),
            )
            for item in expansion_data
        ]

        # Build WritingEvaluation
        evaluation = WritingEvaluation(
            corrected=evaluation_data.get("corrected", text),
            improvements=evaluation_data.get("improvements", []),
            questions=evaluation_data.get("questions", []),
            expansion_words=expansion_words,
            metrics=metrics,
        )

        return evaluation

    def generate_teacher_feedback(
        self,
        evaluation: WritingEvaluation,
        original_text: str,
        config: Optional[WritingConfig] = None,
    ) -> str:
        """
        Generate warm teacher-style feedback email.

        Args:
            evaluation: WritingEvaluation result
            original_text: Student's original text
            config: Optional configuration

        Returns:
            Friendly feedback email body
        """
        config = config or WritingConfig()

        # Convert evaluation back to JSON for LLM
        analysis_data = json.dumps(
            {
                "metrics": {
                    "cefr_level": evaluation.metrics.cefr_level,
                    "variety_score": evaluation.metrics.variety_score,
                },
                "corrected": evaluation.corrected,
                "improvements": evaluation.improvements,
                "questions": evaluation.questions,
                "expansion_words": [
                    {
                        "word": exp.word,
                        "ipa": exp.ipa,
                        "replaces_simple_word": exp.replaces_simple_word,
                        "meaning_context": exp.meaning_context,
                    }
                    for exp in evaluation.expansion_words
                ],
            },
            indent=2,
        )

        # Call LLM for teacher feedback
        feedback = self._llm.generate_teacher_feedback(
            analysis_data=analysis_data,
            original_text=original_text,
            model=config.model,
            temperature=0.4,  # Higher temperature for warmth
        )

        return feedback

    def compute_variety_score(self, text: str) -> int:
        """
        Compute vocabulary variety score (1-10).

        Uses unique word ratio as a simple metric:
        - Split text into words
        - Calculate unique_words / total_words ratio
        - Map to 1-10 scale

        Args:
            text: Text to analyze

        Returns:
            Variety score from 1 to 10
        """
        if not text or not text.strip():
            return 1

        # Normalize and tokenize
        words = re.findall(r'\b\w+\b', text.lower())

        if len(words) == 0:
            return 1

        # Calculate uniqueness ratio
        unique_words = set(words)
        ratio = len(unique_words) / len(words)

        # Map to 1-10 scale
        # ratio=1.0 (all unique) � 10
        # ratio=0.5 (half repeated) � 5
        # ratio=0.1 (highly repetitive) � 1
        score = max(1, min(10, int(ratio * 10)))
        return score

    def get_question_by_category(
        self,
        category: QuestionCategory,
        difficulty: Optional[QuestionDifficulty] = None,
    ) -> Optional[InterviewQuestion]:
        """
        Get a random question from question bank.

        Args:
            category: Question category
            difficulty: Optional difficulty filter

        Returns:
            InterviewQuestion or None if no match
        """
        import random

        # Filter by category
        candidates = [
            q for q in self._question_bank if q.category == category
        ]

        # Filter by difficulty if specified
        if difficulty:
            candidates = [q for q in candidates if q.difficulty == difficulty]

        if not candidates:
            return None

        return random.choice(candidates)

    def get_all_questions(self) -> List[InterviewQuestion]:
        """Get all questions from question bank."""
        return list(self._question_bank)

    def _initialize_question_bank(self) -> List[InterviewQuestion]:
        """
        Initialize interview question bank.

        Migrated from writing_coach_manager.py TOPICS dict.
        """
        questions = []

        # Behavioral questions (Easy)
        behavioral_easy = [
            "Tell me about yourself and your background in software engineering.",
            "Why are you interested in this position?",
            "What are your greatest strengths as a developer?",
            "Describe your ideal work environment.",
            "How do you stay updated with new technologies?",
        ]
        for text in behavioral_easy:
            questions.append(
                InterviewQuestion(
                    text=text,
                    category=QuestionCategory.BEHAVIORAL,
                    difficulty=QuestionDifficulty.EASY,
                )
            )

        # Behavioral questions (Medium)
        behavioral_medium = [
            "Tell me about a challenging project you worked on. What was your role?",
            "Describe a time when you had to learn a new technology quickly.",
            "How do you handle disagreements with team members?",
            "Tell me about a time you failed. What did you learn?",
            "Describe a situation where you had to meet a tight deadline.",
        ]
        for text in behavioral_medium:
            questions.append(
                InterviewQuestion(
                    text=text,
                    category=QuestionCategory.BEHAVIORAL,
                    difficulty=QuestionDifficulty.MEDIUM,
                )
            )

        # Behavioral questions (Hard)
        behavioral_hard = [
            "Describe a time when you had to make a difficult technical decision with incomplete information.",
            "Tell me about a project where you had to balance technical debt with feature delivery.",
            "How have you influenced technical direction or architecture decisions in your previous roles?",
        ]
        for text in behavioral_hard:
            questions.append(
                InterviewQuestion(
                    text=text,
                    category=QuestionCategory.BEHAVIORAL,
                    difficulty=QuestionDifficulty.HARD,
                )
            )

        # Technical questions (Easy)
        technical_easy = [
            "What programming languages are you most comfortable with?",
            "Explain the difference between a class and an object.",
            "What is version control and why is it important?",
            "What is the difference between frontend and backend development?",
            "What is an API and how have you used them?",
        ]
        for text in technical_easy:
            questions.append(
                InterviewQuestion(
                    text=text,
                    category=QuestionCategory.TECHNICAL,
                    difficulty=QuestionDifficulty.EASY,
                )
            )

        # Technical questions (Medium)
        technical_medium = [
            "Explain how you would optimize a slow database query.",
            "What is your approach to debugging a production issue?",
            "Describe your experience with automated testing.",
            "How do you ensure code quality in your projects?",
            "Explain the concept of technical debt and how you manage it.",
        ]
        for text in technical_medium:
            questions.append(
                InterviewQuestion(
                    text=text,
                    category=QuestionCategory.TECHNICAL,
                    difficulty=QuestionDifficulty.MEDIUM,
                )
            )

        # Technical questions (Hard)
        technical_hard = [
            "Design a system to handle 1 million concurrent users. Walk me through your architecture decisions.",
            "How would you approach migrating a legacy monolith to microservices?",
            "Explain how you would implement a real-time collaborative editing feature like Google Docs.",
        ]
        for text in technical_hard:
            questions.append(
                InterviewQuestion(
                    text=text,
                    category=QuestionCategory.TECHNICAL,
                    difficulty=QuestionDifficulty.HARD,
                )
            )

        # Remote work questions (Easy)
        remote_easy = [
            "Do you have experience working remotely?",
            "What tools do you use for remote collaboration?",
            "How do you manage your time when working from home?",
        ]
        for text in remote_easy:
            questions.append(
                InterviewQuestion(
                    text=text,
                    category=QuestionCategory.REMOTE_WORK,
                    difficulty=QuestionDifficulty.EASY,
                )
            )

        # Remote work questions (Medium)
        remote_medium = [
            "How do you stay connected with your team in a remote setting?",
            "Describe your home office setup and how it supports productivity.",
            "How do you handle timezone differences when working with distributed teams?",
        ]
        for text in remote_medium:
            questions.append(
                InterviewQuestion(
                    text=text,
                    category=QuestionCategory.REMOTE_WORK,
                    difficulty=QuestionDifficulty.MEDIUM,
                )
            )

        # Remote work questions (Hard)
        remote_hard = [
            "How do you build trust and rapport with team members you've never met in person?",
            "Describe how you would onboard a new team member in a fully remote environment.",
        ]
        for text in remote_hard:
            questions.append(
                InterviewQuestion(
                    text=text,
                    category=QuestionCategory.REMOTE_WORK,
                    difficulty=QuestionDifficulty.HARD,
                )
            )

        return questions
