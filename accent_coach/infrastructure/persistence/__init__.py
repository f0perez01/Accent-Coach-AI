"""
Persistence Layer

Repository Pattern for data access.
Provides abstraction over database (Firestore, PostgreSQL, in-memory).
"""

from .repositories import (
    PronunciationRepository,
    ConversationRepository,
    WritingRepository,
    ActivityRepository,
)

from .firestore_repositories import (
    FirestorePronunciationRepository,
    FirestoreConversationRepository,
    FirestoreWritingRepository,
    FirestoreActivityRepository,
)

from .in_memory_repositories import (
    InMemoryPronunciationRepository,
    InMemoryConversationRepository,
    InMemoryWritingRepository,
)

__all__ = [
    # Abstract interfaces
    "PronunciationRepository",
    "ConversationRepository",
    "WritingRepository",
    "ActivityRepository",
    # Firestore implementations
    "FirestorePronunciationRepository",
    "FirestoreConversationRepository",
    "FirestoreWritingRepository",
    "FirestoreActivityRepository",
    # In-memory implementations
    "InMemoryPronunciationRepository",
    "InMemoryConversationRepository",
    "InMemoryWritingRepository",
]
