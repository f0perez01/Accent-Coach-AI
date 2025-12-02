"""
Controllers

Thin layer between UI and domain services.
Handles UI events and delegates to services.
"""

from .pronunciation_controller import PronunciationController
from .conversation_controller import ConversationController
from .writing_controller import WritingController

__all__ = [
    "PronunciationController",
    "ConversationController",
    "WritingController",
]
