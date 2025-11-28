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
