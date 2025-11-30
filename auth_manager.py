import os
import requests
from datetime import datetime
from typing import Optional, List
import streamlit as st

try:
    import firebase_admin
    from firebase_admin import credentials, firestore, auth
    _HAS_FIREBASE = True
except Exception:
    firebase_admin = None
    credentials = None
    firestore = None
    auth = None
    _HAS_FIREBASE = False

class AuthManager:
    """Encapsulate authentication and Firestore operations."""
    def __init__(self, secrets: Optional[dict] = None):
        # Accept Streamlit secrets dict or None
        self.secrets = secrets or (st.secrets if hasattr(st, 'secrets') else {})
        self._db = None

    def init_firebase(self):
        """Initialize Firebase Admin SDK if available and not already initialized."""
        if not _HAS_FIREBASE:
            return
        if not firebase_admin._apps:
            try:
                if "FIREBASE" in self.secrets:
                    cred_dict = dict(self.secrets["FIREBASE"])
                    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
            except Exception as e:
                st.error(f"Firebase Init Error: {e}")

    def get_db(self):
        """Return Firestore client or None."""
        if not _HAS_FIREBASE or not firebase_admin._apps:
            return None
        if self._db is None:
            self._db = firestore.client()
        return self._db

    def login_user(self, email: str, password: str) -> dict:
        """Login user using Firebase REST API (Identity Toolkit)."""
        api_key = self.secrets.get("FIREBASE_WEB_API_KEY") or os.environ.get("FIREBASE_WEB_API_KEY")
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        try:
            resp = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
            return resp.json() if resp.status_code == 200 else {"error": resp.json().get("error", {}).get("message", "Error")}
        except Exception as e:
            return {"error": str(e)}

    def register_user(self, email: str, password: str) -> dict:
        """Register user using Firebase REST API (Identity Toolkit)."""
        api_key = self.secrets.get("FIREBASE_WEB_API_KEY") or os.environ.get("FIREBASE_WEB_API_KEY")
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
        try:
            resp = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
            return resp.json() if resp.status_code == 200 else {"error": resp.json().get("error", {}).get("message", "Error")}
        except Exception as e:
            return {"error": str(e)}

    def save_analysis_to_firestore(self, user_id: str, reference_text: str, result: dict):
        """Save pronunciation analysis to Firestore collection `accent_coach_analyses`.
        If Firestore not available, this is a no-op.
        """
        db = self.get_db()
        if not db:
            return

        doc = {
            "user_id": user_id,
            "reference_text": reference_text,
            "raw_decoded": result.get("raw_decoded", ""),
            "metrics": result.get("metrics", {}),
            "per_word_comparison": result.get("per_word_comparison", []),
            "llm_feedback": result.get("llm_feedback", ""),
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        try:
            db.collection("accent_coach_analyses").add(doc)
            try:
                st.toast("Analysis saved to cloud! ☁️")
            except Exception:
                pass
        except Exception as e:
            print(f"Firestore Error: {e}")

    def get_user_analyses(self, user_id: str) -> List[dict]:
        """Query user's analyses from `english_analyses_cv` collection and return list sorted by timestamp desc."""
        db = self.get_db()
        if not db:
            return []
        try:
            docs = db.collection("english_analyses_cv").where("user_id", "==", user_id).stream()
            data = [{"id": d.id, **d.to_dict()} for d in docs]
            # Sort by timestamp descending
            data.sort(
                key=lambda x: x.get('timestamp', datetime.min) if isinstance(x.get('timestamp'), datetime) else datetime.min,
                reverse=True
            )
            return data
        except Exception as e:
            print(f"Firestore Query Error: {e}")
            return []

    def save_writing_analysis_to_firestore(self, user_id: str, original_text: str, result: dict):
        """Save writing coach analysis to Firestore collection `english_analyses_cv`.

        This method stores interview writing practice results with complete analysis data.

        Args:
            user_id: User identifier
            original_text: Student's original written answer
            result: Analysis result from WritingCoachManager containing:
                - corrected: Polished version
                - improvements: List of improvement suggestions
                - questions: Follow-up interview questions
                - expansion_words: Vocabulary expansion items
                - metrics: {cefr_level, variety_score}
        """
        db = self.get_db()
        if not db:
            return

        doc = {
            "user_id": user_id,
            "original_text": original_text,
            "corrected": result.get("corrected", ""),
            "improvements": result.get("improvements", []),
            "questions": result.get("questions", []),
            "expansion_words": result.get("expansion_words", []),
            "metrics": result.get("metrics", {}),
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        try:
            db.collection("english_analyses_cv").add(doc)
            try:
                st.toast("Writing analysis saved to cloud! ☁️")
            except Exception:
                pass
        except Exception as e:
            print(f"Firestore Error (Writing Coach): {e}")

    def get_user_writing_analyses(self, user_id: str) -> List[dict]:
        """Query user's writing analyses from `english_analyses_cv` collection.

        Args:
            user_id: User identifier

        Returns:
            List of writing analysis dicts sorted by timestamp descending
        """
        db = self.get_db()
        if not db:
            return []
        try:
            docs = db.collection("english_analyses_cv").where("user_id", "==", user_id).stream()
            data = [{"id": d.id, **d.to_dict()} for d in docs]
            # Sort by timestamp descending
            data.sort(
                key=lambda x: x.get('timestamp', datetime.min) if isinstance(x.get('timestamp'), datetime) else datetime.min,
                reverse=True
            )
            return data
        except Exception as e:
            print(f"Firestore Query Error (Writing Coach): {e}")
            return []

    def log_activity(self, activity_data: dict):
        """Log user activity to Firestore collection `user_activities`.

        This method stores activity logs for heatmap visualization and progress tracking.

        Args:
            activity_data: Activity log dict from ActivityLogger containing:
                - user_id: User identifier
                - activity_type: Type of activity (pronunciation, writing, conversation)
                - content_length: Length of content
                - weight: Calculated weight for progress tracking
                - metadata: Additional activity-specific data
                - timestamp: Activity timestamp
                - date: Date string (YYYY-MM-DD) for heatmap grouping
        """
        db = self.get_db()
        if not db:
            return

        # Convert datetime to Firestore timestamp for storage
        doc = {**activity_data}
        if 'timestamp' in doc and isinstance(doc['timestamp'], datetime):
            # Only use SERVER_TIMESTAMP if firestore is available
            if _HAS_FIREBASE and firestore is not None:
                doc['timestamp'] = firestore.SERVER_TIMESTAMP
            else:
                # Fallback to ISO string if Firebase not available
                doc['timestamp'] = doc['timestamp'].isoformat()

        try:
            db.collection("user_activities").add(doc)
        except Exception as e:
            print(f"Firestore Error (Activity Log): {e}")

    def get_user_activities(self, user_id: str, days: int = 365) -> List[dict]:
        """Query user's activity logs for heatmap visualization.

        Args:
            user_id: User identifier
            days: Number of days to retrieve (default 365 for yearly heatmap)

        Returns:
            List of activity log dicts sorted by timestamp descending
        """
        db = self.get_db()
        if not db:
            return []
        try:
            # Calculate cutoff date
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            # Query activities from the last N days
            docs = db.collection("user_activities") \
                .where("user_id", "==", user_id) \
                .where("date", ">=", cutoff_date) \
                .stream()

            data = [{"id": d.id, **d.to_dict()} for d in docs]

            # Sort by timestamp descending
            data.sort(
                key=lambda x: x.get('timestamp', datetime.min) if isinstance(x.get('timestamp'), datetime) else datetime.min,
                reverse=True
            )
            return data
        except Exception as e:
            print(f"Firestore Query Error (Activities): {e}")
            return []

    def get_today_activities(self, user_id: str) -> List[dict]:
        """Query user's activity logs for today only.

        Optimized query for daily goal tracking.

        Args:
            user_id: User identifier

        Returns:
            List of activity log dicts for today
        """
        db = self.get_db()
        if not db:
            return []
        try:
            today_date = datetime.now().strftime("%Y-%m-%d")

            # Query only today's activities
            docs = db.collection("user_activities") \
                .where("user_id", "==", user_id) \
                .where("date", "==", today_date) \
                .stream()

            data = [{"id": d.id, **d.to_dict()} for d in docs]
            return data
        except Exception as e:
            print(f"Firestore Query Error (Today's Activities): {e}")
            return []

    def save_user_registration(self, user_id: str, email: str):
        """Save new user registration to Firestore collection `users`.

        This method stores user registration data for tracking and analytics.

        Args:
            user_id: User identifier from Firebase Auth
            email: User's email address
        """
        db = self.get_db()
        if not db:
            return

        doc = {
            "user_id": user_id,
            "email": email,
            "registration_timestamp": firestore.SERVER_TIMESTAMP if (_HAS_FIREBASE and firestore) else datetime.now().isoformat(),
            "registration_date": datetime.now().strftime("%Y-%m-%d"),
            "total_activities": 0,
            "daily_goal": 100,
            "profile": {
                "language_level": "unknown",
                "learning_goals": [],
                "preferred_practice_mode": "pronunciation"
            }
        }

        try:
            # Use user_id as document ID for easy lookups
            db.collection("users").document(user_id).set(doc)
            print(f"User registration saved: {email}")
        except Exception as e:
            print(f"Firestore Error (User Registration): {e}")
