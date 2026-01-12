"""Health check endpoints"""
import logging
from datetime import datetime

from fastapi import APIRouter, Request

from llm_mcp_hub.core.config import get_settings
from .schemas import (
    HealthResponse,
    DetailedHealthResponse,
    ComponentHealth,
    TokenHealthResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check"""
    settings = get_settings()

    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
    )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(request: Request):
    """Detailed health check with component status"""
    settings = get_settings()
    components: dict[str, ComponentHealth] = {}

    # Check Redis
    try:
        session_store = request.app.state.session_store
        if hasattr(session_store, "health_check"):
            redis_health = await session_store.health_check()
            components["redis"] = ComponentHealth(
                status=redis_health.get("status", "unknown"),
                latency_ms=redis_health.get("latency_ms"),
                error=redis_health.get("error"),
            )
        else:
            components["redis"] = ComponentHealth(status="healthy")
    except Exception as e:
        components["redis"] = ComponentHealth(status="unhealthy", error=str(e))

    # Check providers
    providers = getattr(request.app.state, "providers", {})

    for name, adapter in providers.items():
        try:
            health = await adapter.health_check()
            components[name] = ComponentHealth(
                status=health.get("status", "unknown"),
                supported_models=health.get("supported_models"),
                error=health.get("error"),
            )
        except Exception as e:
            components[name] = ComponentHealth(status="unhealthy", error=str(e))

    # Determine overall status
    unhealthy_count = sum(1 for c in components.values() if c.status == "unhealthy")
    if unhealthy_count == 0:
        overall_status = "healthy"
    elif unhealthy_count < len(components):
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return DetailedHealthResponse(
        status=overall_status,
        version=settings.app_version,
        components=components,
    )


@router.get("/health/tokens", response_model=TokenHealthResponse)
async def token_health_check(request: Request):
    """Check OAuth token status"""
    result = {}

    providers = getattr(request.app.state, "providers", {})

    for name, adapter in providers.items():
        try:
            health = await adapter.health_check()
            if health.get("status") == "healthy":
                result[name] = {
                    "valid": True,
                    "status": "active",
                }
            else:
                result[name] = {
                    "valid": False,
                    "error": health.get("error", "Unknown error"),
                }
        except Exception as e:
            result[name] = {
                "valid": False,
                "error": str(e),
            }

    return TokenHealthResponse(**result)
