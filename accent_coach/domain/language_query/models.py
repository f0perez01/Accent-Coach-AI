"""
Language Query domain models
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class QueryResult:
    """Result of language query."""
    user_query: str
    llm_response: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
