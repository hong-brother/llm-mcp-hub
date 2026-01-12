"""API v1 router - aggregates all endpoint routers"""
from fastapi import APIRouter

from .chat import router as chat_router
from .sessions import router as sessions_router
from .providers import router as providers_router
from .health import router as health_router

router = APIRouter(prefix="/v1")

# Include all sub-routers
router.include_router(chat_router)
router.include_router(sessions_router)
router.include_router(providers_router)

# Health router without /v1 prefix (mounted separately)
__all__ = ["router", "health_router"]
