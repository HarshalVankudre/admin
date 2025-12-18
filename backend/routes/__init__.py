"""
Routes package - aggregates all API routers.
"""
from fastapi import APIRouter

from .conversations import router as conversations_router
from .health import router as health_router
from .messages import router as messages_router
from .stats import router as stats_router
from .users import router as users_router

# Create main API router that includes all sub-routers
api_router = APIRouter()

# Include all routers
api_router.include_router(health_router)
api_router.include_router(stats_router)
api_router.include_router(users_router)
api_router.include_router(conversations_router)
api_router.include_router(messages_router)

__all__ = ["api_router"]
