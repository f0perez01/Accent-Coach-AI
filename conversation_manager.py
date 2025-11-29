#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversation Manager
Handles session management and persistence for conversation tutor
"""

from typing import Dict, List, Optional
from datetime import datetime
import json


class ConversationManager:
    """
    Manages conversation sessions, including creation, storage, and retrieval.
    Integrates with Firestore for persistence.
    """

    def __init__(self, auth_manager):
        """
        Initialize ConversationManager.

        Args:
            auth_manager: Instance of AuthManager for Firestore access
        """
        self.auth_manager = auth_manager

    def create_session(
        self,
        user_id: str,
        topic: str = "General Conversation",
        level: str = "B1-B2"
    ) -> Dict:
        """
        Create a new conversation session.

        Args:
            user_id: User ID from authentication
            topic: Conversation topic
            level: User's proficiency level

        Returns:
            Session data dict
        """
        session_id = f"conv_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "topic": topic,
            "level": level,
            "started_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "history": [],
            "status": "active"
        }

        return session_data

    def record_turn(
        self,
        session,
        turn_data: Dict,
        user_id: str,
        update_session_state: bool = True
    ) -> bool:
        """
        Record a conversation turn atomically (session state + session object + Firestore).

        This method encapsulates the complete turn recording workflow:
        1. Add to st.session_state.conversation_history (if update_session_state=True)
        2. Add to session object (session.add_turn)
        3. Persist to Firestore

        Args:
            session: ConversationSession instance
            turn_data: Turn data from ConversationTutor
            user_id: User ID for Firestore
            update_session_state: Whether to update st.session_state (default True)

        Returns:
            True if successful, False otherwise
        """
        try:
            import streamlit as st

            # Step 1: Update session state (if requested)
            if update_session_state:
                if 'conversation_history' not in st.session_state:
                    st.session_state.conversation_history = []
                st.session_state.conversation_history.append(turn_data)

            # Step 2: Add to session object
            session.add_turn(turn_data)

            # Step 3: Persist to Firestore
            self.save_conversation_turn(session.session_id, user_id, turn_data)

            return True

        except Exception as e:
            print(f"Error recording turn: {e}")
            return False

    def save_conversation_turn(
        self,
        session_id: str,
        user_id: str,
        turn_data: Dict
    ) -> bool:
        """
        Save a conversation turn to Firestore.

        NOTE: This is a lower-level method. For most use cases, use record_turn() instead,
        which handles session state, session object, and Firestore atomically.

        Args:
            session_id: Session identifier
            user_id: User ID
            turn_data: Turn data from ConversationTutor

        Returns:
            True if successful, False otherwise
        """
        try:
            db = self.auth_manager.get_db()
            if not db:
                return False

            # Prepare turn data for storage
            turn_record = {
                "user_transcript": turn_data.get('user_transcript', ''),
                "correction": turn_data.get('correction', ''),
                "explanation": turn_data.get('explanation', ''),
                "improved_version": turn_data.get('improved_version', ''),
                "follow_up_question": turn_data.get('follow_up_question', ''),
                "errors_count": len(turn_data.get('errors_detected', [])),
                "timestamp": turn_data.get('timestamp', datetime.now()).isoformat()
            }

            # Update session document
            session_ref = db.collection('conversation_sessions').document(session_id)

            # Check if session exists
            session_doc = session_ref.get()

            if session_doc.exists:
                # Append turn to existing session
                session_ref.update({
                    'history': firestore.ArrayUnion([turn_record]),
                    'last_activity': datetime.now().isoformat(),
                    'turn_count': firestore.Increment(1)
                })
            else:
                # Create new session
                session_ref.set({
                    'session_id': session_id,
                    'user_id': user_id,
                    'started_at': datetime.now().isoformat(),
                    'last_activity': datetime.now().isoformat(),
                    'history': [turn_record],
                    'turn_count': 1,
                    'status': 'active'
                })

            return True

        except Exception as e:
            print(f"Error saving conversation turn: {e}")
            return False

    def get_user_sessions(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get user's conversation sessions from Firestore.

        Args:
            user_id: User ID
            limit: Maximum number of sessions to retrieve

        Returns:
            List of session dicts
        """
        try:
            db = self.auth_manager.get_db()
            if not db:
                return []

            sessions_ref = db.collection('conversation_sessions')
            query = sessions_ref.where('user_id', '==', user_id).order_by(
                'last_activity', direction='DESCENDING'
            ).limit(limit)

            sessions = []
            for doc in query.stream():
                session_data = doc.to_dict()
                sessions.append(session_data)

            return sessions

        except Exception as e:
            print(f"Error retrieving sessions: {e}")
            return []

    def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        """
        Get a specific session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session data dict or None
        """
        try:
            db = self.auth_manager.get_db()
            if not db:
                return None

            session_ref = db.collection('conversation_sessions').document(session_id)
            session_doc = session_ref.get()

            if session_doc.exists:
                return session_doc.to_dict()
            else:
                return None

        except Exception as e:
            print(f"Error retrieving session: {e}")
            return None

    def close_session(self, session_id: str) -> bool:
        """
        Mark a session as completed.

        Args:
            session_id: Session identifier

        Returns:
            True if successful, False otherwise
        """
        try:
            db = self.auth_manager.get_db()
            if not db:
                return False

            session_ref = db.collection('conversation_sessions').document(session_id)
            session_ref.update({
                'status': 'completed',
                'completed_at': datetime.now().isoformat()
            })

            return True

        except Exception as e:
            print(f"Error closing session: {e}")
            return False

    def get_session_stats(self, session_id: str) -> Dict:
        """
        Calculate statistics for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dict with session statistics
        """
        session = self.get_session_by_id(session_id)

        if not session:
            return {}

        history = session.get('history', [])

        total_turns = len(history)
        total_errors = sum(turn.get('errors_count', 0) for turn in history)

        # Calculate duration
        started_at = datetime.fromisoformat(session.get('started_at', datetime.now().isoformat()))
        last_activity = datetime.fromisoformat(session.get('last_activity', datetime.now().isoformat()))
        duration_minutes = (last_activity - started_at).total_seconds() / 60

        return {
            "session_id": session_id,
            "total_turns": total_turns,
            "total_errors": total_errors,
            "avg_errors_per_turn": round(total_errors / total_turns, 2) if total_turns > 0 else 0,
            "duration_minutes": round(duration_minutes, 1),
            "topic": session.get('topic', 'General'),
            "level": session.get('level', 'B1-B2'),
            "started_at": session.get('started_at'),
            "status": session.get('status', 'active')
        }

    def export_session_to_text(self, session_id: str) -> str:
        """
        Export session as readable text transcript.

        Args:
            session_id: Session identifier

        Returns:
            Formatted text transcript
        """
        session = self.get_session_by_id(session_id)

        if not session:
            return "Session not found."

        lines = []
        lines.append("=" * 60)
        lines.append(f"CONVERSATION SESSION: {session.get('topic', 'General')}")
        lines.append(f"Level: {session.get('level', 'B1-B2')}")
        lines.append(f"Started: {session.get('started_at', 'Unknown')}")
        lines.append("=" * 60)
        lines.append("")

        history = session.get('history', [])

        for i, turn in enumerate(history, 1):
            lines.append(f"Turn {i}:")
            lines.append(f"Student: {turn.get('user_transcript', '')}")

            if turn.get('correction'):
                lines.append(f"✏️  Correction: {turn.get('correction', '')}")

            if turn.get('explanation'):
                lines.append(f"📚 Explanation: {turn.get('explanation', '')}")

            if turn.get('improved_version'):
                lines.append(f"✅ Better: {turn.get('improved_version', '')}")

            if turn.get('follow_up_question'):
                lines.append(f"Tutor: {turn.get('follow_up_question', '')}")

            lines.append("")

        # Add stats
        stats = self.get_session_stats(session_id)
        lines.append("=" * 60)
        lines.append("SESSION STATISTICS")
        lines.append(f"Total turns: {stats.get('total_turns', 0)}")
        lines.append(f"Total errors: {stats.get('total_errors', 0)}")
        lines.append(f"Duration: {stats.get('duration_minutes', 0)} minutes")
        lines.append("=" * 60)

        return "\n".join(lines)


# Firestore import (conditional)
try:
    from firebase_admin import firestore
except ImportError:
    # Create mock firestore for when Firebase is not available
    class firestore:
        @staticmethod
        def ArrayUnion(items):
            return items

        @staticmethod
        def Increment(value):
            return value
