"""
Firestore Repository Implementations

Concrete implementations using Firebase Firestore.
"""

from typing import List
from datetime import datetime
from .repositories import (
    PronunciationRepository,
    ConversationRepository,
    WritingRepository,
    ActivityRepository,
)


class FirestorePronunciationRepository(PronunciationRepository):
    """Firestore implementation of PronunciationRepository."""

    def __init__(self, db):
        """
        Args:
            db: Firestore database client
        """
        self._db = db
        self._collection = "pronunciation_analyses"

    def save_analysis(
        self, user_id: str, reference_text: str, analysis
    ) -> str:
        """Save pronunciation analysis to Firestore."""
        doc_ref = self._db.collection(self._collection).document()

        # Convert analysis to dict for Firestore
        data = {
            "user_id": user_id,
            "reference_text": reference_text,
            "timestamp": datetime.now(),
            # Store metrics
            "metrics": {
                "word_accuracy": analysis.analysis.metrics.word_accuracy,
                "phoneme_accuracy": analysis.analysis.metrics.phoneme_accuracy,
                "phoneme_error_rate": analysis.analysis.metrics.phoneme_error_rate,
                "correct_words": analysis.analysis.metrics.correct_words,
                "total_words": analysis.analysis.metrics.total_words,
                "substitutions": analysis.analysis.metrics.substitutions,
                "insertions": analysis.analysis.metrics.insertions,
                "deletions": analysis.analysis.metrics.deletions,
            },
            # Store per-word comparison
            "per_word_comparison": [
                {
                    "word": w.word,
                    "ref_phonemes": w.ref_phonemes,
                    "rec_phonemes": w.rec_phonemes,
                    "match": w.match,
                    "phoneme_accuracy": w.phoneme_accuracy,
                }
                for w in analysis.analysis.per_word_comparison
            ],
            # Store LLM feedback if available
            "llm_feedback": analysis.llm_feedback,
            "raw_decoded": analysis.raw_decoded,
        }

        doc_ref.set(data)
        return doc_ref.id

    def get_user_history(self, user_id: str, limit: int = 50) -> List:
        """Get user history from Firestore."""
        query = (
            self._db.collection(self._collection)
            .where("user_id", "==", user_id)
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
        )

        docs = query.stream()

        # Return raw dicts (can be converted to objects by service layer)
        return [doc.to_dict() for doc in docs]


class FirestoreConversationRepository(ConversationRepository):
    """Firestore implementation of ConversationRepository."""

    def __init__(self, db):
        self._db = db
        self._collection = "conversation_turns"

    def save_turn(self, session_id: str, turn) -> None:
        """Save conversation turn to Firestore."""
        doc_ref = self._db.collection(self._collection).document()

        data = {
            "session_id": session_id,
            "timestamp": datetime.now(),
            "user_transcript": turn.user_transcript,
            "correction": turn.correction,
            "improved_version": turn.improved_version,
            "explanation": turn.explanation,
            "errors_detected": turn.errors_detected,
            "follow_up_question": turn.follow_up_question,
        }

        doc_ref.set(data)

    def get_session_history(self, session_id: str) -> List:
        """Get session history from Firestore."""
        query = (
            self._db.collection(self._collection)
            .where("session_id", "==", session_id)
            .order_by("timestamp", direction="ASCENDING")
        )

        docs = query.stream()
        return [doc.to_dict() for doc in docs]


class FirestoreWritingRepository(WritingRepository):
    """Firestore implementation of WritingRepository."""

    def __init__(self, db):
        self._db = db
        self._collection = "writing_evaluations"

    def save_evaluation(
        self, user_id: str, text: str, evaluation
    ) -> str:
        """Save writing evaluation to Firestore."""
        doc_ref = self._db.collection(self._collection).document()

        data = {
            "user_id": user_id,
            "text": text,
            "timestamp": datetime.now(),
            "corrected": evaluation.corrected,
            "improvements": evaluation.improvements,
            "questions": evaluation.questions,
            "metrics": {
                "cefr_level": evaluation.metrics.cefr_level,
                "variety_score": evaluation.metrics.variety_score,
            },
            "expansion_words": [
                {
                    "word": w.word,
                    "ipa": w.ipa,
                    "replaces_simple_word": w.replaces_simple_word,
                    "meaning_context": w.meaning_context,
                }
                for w in evaluation.expansion_words
            ],
        }

        doc_ref.set(data)
        return doc_ref.id


class FirestoreActivityRepository(ActivityRepository):
    """Firestore implementation of ActivityRepository."""

    def __init__(self, db):
        self._db = db
        self._collection = "user_activities"

    def log_activity(self, activity) -> None:
        """Log activity to Firestore."""
        doc_ref = self._db.collection(self._collection).document()

        data = {
            "user_id": activity.user_id,
            "activity_type": activity.activity_type.value,  # Enum to string
            "timestamp": activity.timestamp,
            "score": activity.score,
            "metadata": activity.metadata,
        }

        doc_ref.set(data)

    def get_today_activities(self, user_id: str, date: datetime) -> List:
        """Get today's activities from Firestore."""
        # Get start and end of day
        start_of_day = datetime(date.year, date.month, date.day, 0, 0, 0)
        end_of_day = datetime(date.year, date.month, date.day, 23, 59, 59)

        query = (
            self._db.collection(self._collection)
            .where("user_id", "==", user_id)
            .where("timestamp", ">=", start_of_day)
            .where("timestamp", "<=", end_of_day)
            .order_by("timestamp", direction="DESCENDING")
        )

        docs = query.stream()
        return [doc.to_dict() for doc in docs]
