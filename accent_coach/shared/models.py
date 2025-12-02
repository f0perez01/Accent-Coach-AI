"""
Shared Models

Common models used across multiple bounded contexts.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """User model."""
    user_id: str
    email: str
    display_name: Optional[str] = None
