"""Metrics module for tracking LLM usage and token counts."""

# Try to import database models, fallback to None if not available
try:
    from ..database.models import ModelUsage, TokenUsage
    _DATABASE_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    _DATABASE_AVAILABLE = False
    ModelUsage = None
    TokenUsage = None

from .database import get_metrics_db
from .token_counter import TokenCounter, TokenCountingCallback

__all__ = [
    "ModelUsage",
    "TokenCounter",
    "TokenCountingCallback",
    "TokenUsage",
    "get_metrics_db",
]
