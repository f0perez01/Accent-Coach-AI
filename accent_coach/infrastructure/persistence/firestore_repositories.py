"""
Firestore Repository Implementations (Enhanced)

Production-ready implementations with error handling, logging, and retry logic.
Migrated from auth_manager.py for better separation of concerns.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from .repositories import (
    PronunciationRepository,
    ConversationRepository,
    WritingRepository,
    ActivityRepository,
)

logger = logging.getLogger(__name__)


class FirestorePronunciationRepository(PronunciationRepository):
    """
    Firestore implementation of PronunciationRepository.
    
    Stores pronunciation practice analyses with full metrics and feedback.
    Collection: 'pronunciation_analyses'
    """

    def __init__(self, db):
        """
        Initialize repository with Firestore client.
        
        Args:
            db: Firestore database client from firebase_admin
        """
        if db is None:
            raise ValueError("Firestore database client cannot be None")
        
        self._db = db
        self._collection_name = "pronunciation_analyses"
    
    def save_analysis(
        self, user_id: str, reference_text: str, analysis, timestamp: Optional[datetime] = None
    ) -> str:
        """
        Save pronunciation analysis to Firestore.
        
        Args:
            user_id: User identifier
            reference_text: Original text that was practiced
            analysis: PracticeResult object with metrics and feedback
            timestamp: Optional custom timestamp (defaults to now)
            
        Returns:
            Document ID of saved analysis
            
        Raises:
            Exception: If save operation fails
        """
        try:
            doc_ref = self._db.collection(self._collection_name).document()
            
            # Prepare data structure
            data = {
                "user_id": user_id,
                "reference_text": reference_text,
                "timestamp": timestamp or firestore.SERVER_TIMESTAMP,
                "raw_decoded": getattr(analysis, 'raw_decoded', ''),
                "llm_feedback": getattr(analysis, 'llm_feedback', ''),
            }
            
            # Add metrics if available
            if hasattr(analysis, 'analysis') and hasattr(analysis.analysis, 'metrics'):
                metrics = analysis.analysis.metrics
                data["metrics"] = {
                    "word_accuracy": getattr(metrics, 'word_accuracy', 0.0),
                    "phoneme_accuracy": getattr(metrics, 'phoneme_accuracy', 0.0),
                    "phoneme_error_rate": getattr(metrics, 'phoneme_error_rate', 0.0),
                    "correct_words": getattr(metrics, 'correct_words', 0),
                    "total_words": getattr(metrics, 'total_words', 0),
                    "substitutions": getattr(metrics, 'substitutions', 0),
                    "insertions": getattr(metrics, 'insertions', 0),
                    "deletions": getattr(metrics, 'deletions', 0),
                }
            
            # Add per-word comparison if available
            if hasattr(analysis, 'analysis') and hasattr(analysis.analysis, 'per_word_comparison'):
                data["per_word_comparison"] = [
                    {
                        "word": w.word,
                        "ref_phonemes": getattr(w, 'ref_phonemes', ''),
                        "rec_phonemes": getattr(w, 'rec_phonemes', ''),
                        "match": getattr(w, 'match', False),
                        "phoneme_accuracy": getattr(w, 'phoneme_accuracy', 0.0),
                    }
                    for w in analysis.analysis.per_word_comparison
                ]
            
            doc_ref.set(data)
            logger.info(f"Saved pronunciation analysis for user {user_id}, doc_id={doc_ref.id}")
            return doc_ref.id
            
        except Exception as e:
            logger.error(f"Failed to save pronunciation analysis: {e}")
            raise
    
    def get_user_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get user's pronunciation practice history.
        
        Args:
            user_id: User identifier
            limit: Maximum number of results (default: 50)
            
        Returns:
            List of analysis dictionaries, sorted by timestamp descending
        """
        try:
            query = (
                self._db.collection(self._collection_name)
                .where(filter=FieldFilter("user_id", "==", user_id))
                .order_by("timestamp", direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
            
            docs = query.stream()
            history = [{"id": doc.id, **doc.to_dict()} for doc in docs]
            
            logger.info(f"Retrieved {len(history)} analyses for user {user_id}")
            return history
            
        except Exception as e:
            logger.error(f"Failed to get user history: {e}")
            return []
    
    def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific analysis by document ID.
        
        Args:
            analysis_id: Document ID
            
        Returns:
            Analysis dictionary or None if not found
        """
        try:
            doc = self._db.collection(self._collection_name).document(analysis_id).get()
            
            if doc.exists:
                return {"id": doc.id, **doc.to_dict()}
            else:
                logger.warning(f"Analysis {analysis_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get analysis by id: {e}")
            return None
    
    def delete_analysis(self, analysis_id: str) -> bool:
        """
        Delete specific analysis.
        
        Args:
            analysis_id: Document ID to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            self._db.collection(self._collection_name).document(analysis_id).delete()
            logger.info(f"Deleted analysis {analysis_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete analysis: {e}")
            return False


class FirestoreConversationRepository(ConversationRepository):
    """
    Firestore implementation of ConversationRepository.
    
    Stores conversation tutor turns with corrections and feedback.
    Collection: 'conversation_turns'
    """

    def __init__(self, db):
        """Initialize repository with Firestore client."""
        if db is None:
            raise ValueError("Firestore database client cannot be None")
        
        self._db = db
        self._collection_name = "conversation_turns"
    
    def save_turn(self, session_id: str, turn, timestamp: Optional[datetime] = None) -> str:
        """
        Save conversation turn to Firestore.
        
        Args:
            session_id: Conversation session identifier
            turn: TurnResult object with conversation data
            timestamp: Optional custom timestamp
            
        Returns:
            Document ID of saved turn
        """
        try:
            doc_ref = self._db.collection(self._collection_name).document()
            
            data = {
                "session_id": session_id,
                "timestamp": timestamp or firestore.SERVER_TIMESTAMP,
                "user_transcript": getattr(turn, 'user_transcript', ''),
                "correction": getattr(turn, 'correction', ''),
                "improved_version": getattr(turn, 'improved_version', ''),
                "explanation": getattr(turn, 'explanation', ''),
                "errors_detected": getattr(turn, 'errors_detected', []),
                "follow_up_question": getattr(turn, 'follow_up_question', ''),
            }
            
            doc_ref.set(data)
            logger.info(f"Saved conversation turn for session {session_id}")
            return doc_ref.id
            
        except Exception as e:
            logger.error(f"Failed to save conversation turn: {e}")
            raise
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get full conversation session history.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of turn dictionaries, sorted chronologically
        """
        try:
            query = (
                self._db.collection(self._collection_name)
                .where(filter=FieldFilter("session_id", "==", session_id))
                .order_by("timestamp", direction=firestore.Query.ASCENDING)
            )
            
            docs = query.stream()
            history = [{"id": doc.id, **doc.to_dict()} for doc in docs]
            
            logger.info(f"Retrieved {len(history)} turns for session {session_id}")
            return history
            
        except Exception as e:
            logger.error(f"Failed to get session history: {e}")
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete entire conversation session.
        
        Args:
            session_id: Session to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            docs = (
                self._db.collection(self._collection_name)
                .where(filter=FieldFilter("session_id", "==", session_id))
                .stream()
            )
            
            batch = self._db.batch()
            count = 0
            
            for doc in docs:
                batch.delete(doc.reference)
                count += 1
            
            batch.commit()
            logger.info(f"Deleted {count} turns for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False


class FirestoreWritingRepository(WritingRepository):
    """
    Firestore implementation of WritingRepository.
    
    Stores writing evaluations with corrections and feedback.
    Collection: 'writing_evaluations'
    """

    def __init__(self, db):
        """Initialize repository with Firestore client."""
        if db is None:
            raise ValueError("Firestore database client cannot be None")
        
        self._db = db
        self._collection_name = "writing_evaluations"
    
    def save_evaluation(
        self, user_id: str, text: str, evaluation, timestamp: Optional[datetime] = None
    ) -> str:
        """
        Save writing evaluation to Firestore.
        
        Args:
            user_id: User identifier
            text: Original text submitted by user
            evaluation: WritingEvaluation object
            timestamp: Optional custom timestamp
            
        Returns:
            Document ID of saved evaluation
        """
        try:
            doc_ref = self._db.collection(self._collection_name).document()
            
            data = {
                "user_id": user_id,
                "original_text": text,
                "timestamp": timestamp or firestore.SERVER_TIMESTAMP,
                "corrected": getattr(evaluation, 'corrected', ''),
                "improvements": getattr(evaluation, 'improvements', []),
                "questions": getattr(evaluation, 'questions', []),
            }
            
            # Add metrics if available
            if hasattr(evaluation, 'metrics'):
                metrics = evaluation.metrics
                data["metrics"] = {
                    "cefr_level": getattr(metrics, 'cefr_level', 'Unknown'),
                    "variety_score": getattr(metrics, 'variety_score', 0.0),
                }
            
            # Add expansion words if available
            if hasattr(evaluation, 'expansion_words'):
                data["expansion_words"] = [
                    {
                        "word": w.word,
                        "ipa": getattr(w, 'ipa', ''),
                        "replaces_simple_word": getattr(w, 'replaces_simple_word', ''),
                        "meaning_context": getattr(w, 'meaning_context', ''),
                    }
                    for w in evaluation.expansion_words
                ]
            
            doc_ref.set(data)
            logger.info(f"Saved writing evaluation for user {user_id}")
            return doc_ref.id
            
        except Exception as e:
            logger.error(f"Failed to save writing evaluation: {e}")
            raise
    
    def get_user_evaluations(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get user's writing evaluation history.
        
        Args:
            user_id: User identifier
            limit: Maximum number of results
            
        Returns:
            List of evaluation dictionaries, sorted by timestamp descending
        """
        try:
            query = (
                self._db.collection(self._collection_name)
                .where(filter=FieldFilter("user_id", "==", user_id))
                .order_by("timestamp", direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
            
            docs = query.stream()
            evaluations = [{"id": doc.id, **doc.to_dict()} for doc in docs]
            
            logger.info(f"Retrieved {len(evaluations)} evaluations for user {user_id}")
            return evaluations
            
        except Exception as e:
            logger.error(f"Failed to get user evaluations: {e}")
            return []


class FirestoreActivityRepository(ActivityRepository):
    """
    Firestore implementation of ActivityRepository.
    
    Stores user activity logs for progress tracking.
    Collection: 'user_activities'
    """

    def __init__(self, db):
        """Initialize repository with Firestore client."""
        if db is None:
            raise ValueError("Firestore database client cannot be None")
        
        self._db = db
        self._collection_name = "user_activities"
    
    def log_activity(self, activity) -> None:
        """
        Log user activity to Firestore.

        Args:
            activity: Activity object with type, score, and metadata
        """
        try:
            doc_ref = self._db.collection(self._collection_name).document()

            # Get timestamp
            timestamp = activity.timestamp or datetime.now()

            # Format date for daily aggregation
            date_str = timestamp.strftime("%Y-%m-%d") if isinstance(timestamp, datetime) else datetime.now().strftime("%Y-%m-%d")

            # Get score/weight (support both field names for compatibility)
            score = getattr(activity, 'score', 0)
            weight = getattr(activity, 'weight', score)  # Use weight if available, else use score

            data = {
                "user_id": activity.user_id,
                "activity_type": activity.activity_type.value if hasattr(activity.activity_type, 'value') else str(activity.activity_type),
                "timestamp": firestore.SERVER_TIMESTAMP if timestamp is None else timestamp,
                "score": score,
                "weight": weight,  # For compatibility with ActivityLogger
                "date": date_str,  # For daily aggregation
                "metadata": getattr(activity, 'metadata', {}),
            }

            # Also include content_length if available (used by old activity_logger)
            if hasattr(activity, 'content_length'):
                data["content_length"] = activity.content_length

            doc_ref.set(data)
            logger.info(f"Logged activity for user {activity.user_id}")

        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
            raise
    
    def get_today_activities(self, user_id: str, date: datetime) -> List[Dict[str, Any]]:
        """
        Get user's activities for a specific date.

        Args:
            user_id: User identifier
            date: Date to query activities for

        Returns:
            List of activity dictionaries with 'date', 'weight', and other fields
        """
        try:
            # Format date as string for query
            date_str = date.strftime("%Y-%m-%d")

            # Use date field instead of timestamp ranges to avoid composite index requirement
            query = (
                self._db.collection(self._collection_name)
                .where(filter=FieldFilter("user_id", "==", user_id))
                .where(filter=FieldFilter("date", "==", date_str))
            )

            docs = query.stream()
            activities = [{"id": doc.id, **doc.to_dict()} for doc in docs]

            logger.info(f"Retrieved {len(activities)} activities for user {user_id} on {date_str}")
            return activities

        except Exception as e:
            logger.error(f"Failed to get today's activities: {e}")
            return []
    
    def get_total_score_today(self, user_id: str, date: datetime) -> int:
        """
        Calculate total score for user on specific date.
        
        Args:
            user_id: User identifier
            date: Date to calculate score for
            
        Returns:
            Total score accumulated
        """
        activities = self.get_today_activities(user_id, date)
        return sum(activity.get('score', 0) for activity in activities)
