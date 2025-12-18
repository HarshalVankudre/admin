"""
RÜKO Admin Dashboard Backend

A FastAPI-based admin dashboard for monitoring chatbot analytics.
"""
from .config import get_settings
from .database import close_pool, init_pool

__all__ = ["get_settings", "init_pool", "close_pool"]
__version__ = "1.0.0"
