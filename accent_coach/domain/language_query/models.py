"""
Language Query domain models
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class QueryCategory(Enum):
    """Language query categories."""
    IDIOM = "idiom"
    PHRASAL_VERB = "phrasal_verb"
    EXPRESSION = "expression"
    SLANG = "slang"
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"
    ERROR = "error"


@dataclass
class QueryConfig:
    """Configuration for language query processing."""
    model: str = "llama-3.1-8b-instant"
    temperature: float = 0.25
    max_tokens: int = 450


@dataclass
class QueryResult:
    """Result of language query."""
    user_query: str
    llm_response: str
    category: QueryCategory
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
