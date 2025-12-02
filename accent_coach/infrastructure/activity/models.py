"""
Activity Tracking models
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict


class ActivityType(Enum):
    """Types of user activities."""
    PRONUNCIATION = "pronunciation"
    CONVERSATION = "conversation"
    WRITING = "writing"
    LANGUAGE_QUERY = "language_query"


@dataclass
class ActivityLog:
    """User activity log entry."""
    user_id: str
    activity_type: ActivityType
    timestamp: datetime
    score: int
    metadata: Dict

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
