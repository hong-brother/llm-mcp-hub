"""Provider API endpoints"""
import logging

from fastapi import APIRouter, HTTPException

from .dependencies import SessionServiceDep
from .schemas import ProviderInfo, ProviderDetailResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/providers", tags=["Providers"])


@router.get("", response_model=list[ProviderInfo])
async def list_providers(session_service: SessionServiceDep):
    """List all available providers"""
    providers = session_service.get_available_providers()
    return [
        ProviderInfo(
            name=p["name"],
            models=p["models"],
            default_model=p["default_model"],
        )
        for p in providers
    ]


@router.get("/{name}", response_model=ProviderDetailResponse)
async def get_provider(name: str, session_service: SessionServiceDep):
    """Get provider details"""
    provider = session_service.get_provider(name)
    if not provider:
        raise HTTPException(
            status_code=404,
            detail={"code": "PROVIDER_NOT_FOUND", "message": f"Provider not found: {name}"},
        )

    return ProviderDetailResponse(
        name=provider.name,
        status="healthy",  # Basic status, detailed health via /health endpoint
        models=provider.supported_models,
        default_model=provider.default_model,
    )


@router.get("/{name}/models", response_model=list[str])
async def get_provider_models(name: str, session_service: SessionServiceDep):
    """Get supported models for a provider"""
    provider = session_service.get_provider(name)
    if not provider:
        raise HTTPException(
            status_code=404,
            detail={"code": "PROVIDER_NOT_FOUND", "message": f"Provider not found: {name}"},
        )

    return provider.supported_models
