"""
Writing Coach Service (BC7)
"""

from .models import WritingEvaluation


class WritingCoachService:
    """
    BC7: Writing Evaluation

    Responsibilities:
    - Evaluate written texts
    - Generate polished versions
    - Calculate CEFR metrics
    - Suggest vocabulary expansion

    Dependencies:
    - LLMService (BC6)
    - WritingRepository (Infrastructure)
    """

    def __init__(self, llm_service, repository):
        """
        Args:
            llm_service: LLMService instance
            repository: WritingRepository instance
        """
        self._llm = llm_service
        self._repo = repository

    def evaluate_writing(self, text: str, user_id: str) -> WritingEvaluation:
        """
        Evaluate written text.

        Args:
            text: User's written text
            user_id: User identifier

        Returns:
            Writing evaluation with corrections and suggestions
        """
        # TODO: Implementation in Sprint 6
        # 1. Generate LLM evaluation
        # 2. Parse response into WritingEvaluation
        # 3. Save to repository
        raise NotImplementedError("To be implemented in Sprint 6")
