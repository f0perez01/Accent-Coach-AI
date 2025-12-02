"""
Authentication Service
"""

from typing import Dict, Optional


class AuthService:
    """
    Authentication service using Firebase.

    Responsibilities:
    - User login
    - User registration
    - Session management

    DOES NOT handle:
    - Data persistence (use repositories)
    - Activity logging (use ActivityTracker)
    """

    def __init__(self, firebase_adapter):
        """
        Args:
            firebase_adapter: Firebase authentication adapter
        """
        self._firebase = firebase_adapter

    def login_user(self, email: str, password: str) -> Dict:
        """
        Login user with Firebase.

        Args:
            email: User email
            password: User password

        Returns:
            User data dict

        Raises:
            AuthenticationError: If login fails
        """
        # TODO: Implementation in Sprint 1
        raise NotImplementedError("To be implemented in Sprint 1")

    def register_user(self, email: str, password: str) -> Dict:
        """
        Register new user with Firebase.

        Args:
            email: User email
            password: User password

        Returns:
            User data dict

        Raises:
            RegistrationError: If registration fails
        """
        # TODO: Implementation in Sprint 1
        raise NotImplementedError("To be implemented in Sprint 1")
