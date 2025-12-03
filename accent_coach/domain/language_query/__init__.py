"""
BC8: Language Query Assistant

Responsibilities:
- Evaluate expression naturalness (common/rare/unnatural/incorrect)
- Answer language questions (idioms, grammar, vocabulary)
- Provide real-life usage examples
- Suggest native alternatives

Dependencies: BC6 (LLM)
"""

from .service import LanguageQueryService
from .models import QueryResult, QueryConfig, QueryCategory

__all__ = [
    "LanguageQueryService",
    "QueryResult",
    "QueryConfig",
    "QueryCategory",
]
