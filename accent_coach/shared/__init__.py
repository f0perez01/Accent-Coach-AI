"""
Shared Layer

Common models and exceptions used across layers.
"""

from .exceptions import (
    AccentCoachException,
    AudioValidationError,
    TranscriptionError,
    AuthenticationError,
)

__all__ = [
    "AccentCoachException",
    "AudioValidationError",
    "TranscriptionError",
    "AuthenticationError",
]
