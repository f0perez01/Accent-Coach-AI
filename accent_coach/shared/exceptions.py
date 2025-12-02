"""
Custom Exceptions

Domain-specific exceptions for better error handling.
"""


class AccentCoachException(Exception):
    """Base exception for Accent Coach AI."""
    pass


class AudioValidationError(AccentCoachException):
    """Raised when audio validation fails."""
    pass


class TranscriptionError(AccentCoachException):
    """Raised when transcription fails."""
    pass


class AuthenticationError(AccentCoachException):
    """Raised when authentication fails."""
    pass


class RegistrationError(AccentCoachException):
    """Raised when user registration fails."""
    pass


class RepositoryError(AccentCoachException):
    """Raised when repository operations fail."""
    pass
