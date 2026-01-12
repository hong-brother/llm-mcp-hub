"""Session API endpoints"""
import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from llm_mcp_hub.core.exceptions import LLMHubError
from llm_mcp_hub.services.memory import CompressionLevel
from .dependencies import SessionServiceDep, MemoryServiceDep
from .schemas import (
    CreateSessionRequest,
    SessionResponse,
    CloseSessionRequest,
    CloseSessionResponse,
    SessionMemoryResponse,
    SessionListItem,
    SessionListResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    session_service: SessionServiceDep,
    limit: int = Query(default=50, le=100, ge=1),
    offset: int = Query(default=0, ge=0),
):
    """
    List all active sessions.

    Returns paginated list of sessions with basic information.
    """
    try:
        sessions = await session_service.list_sessions(limit=limit, offset=offset)

        session_items = [
            SessionListItem(
                session_id=s.id,
                provider=s.provider,
                model=s.model,
                status=s.status.value,
                created_at=s.created_at,
                expires_at=s.expires_at,
                message_count=len(s.messages),
            )
            for s in sessions
        ]

        return SessionListResponse(
            sessions=session_items,
            total=len(session_items),
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        logger.exception("Unexpected session list error")
        raise HTTPException(status_code=500, detail={"code": "INTERNAL_ERROR", "message": str(e)})


@router.post("", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    session_service: SessionServiceDep,
):
    """
    Create a new session with optional context injection.

    Use this to start a conversation with persistent context.
    """
    try:
        context = None
        if request.context:
            context = {
                "memory": request.context.memory,
                "previous_summary": request.context.previous_summary,
                "files": request.context.files,
            }

        session = await session_service.create_session(
            provider=request.provider,
            model=request.model,
            system_prompt=request.system_prompt,
            context=context,
            ttl=request.ttl,
            metadata=request.metadata,
        )

        # Get supported models for this provider
        provider = session_service.get_provider(session.provider)
        supported_models = provider.supported_models if provider else []

        return SessionResponse(
            session_id=session.id,
            provider=session.provider,
            model=session.model,
            status=session.status.value,
            supported_models=supported_models,
            created_at=session.created_at,
            expires_at=session.expires_at,
        )

    except LLMHubError as e:
        logger.error(f"Session create error: {e.code} - {e.message}")
        raise HTTPException(
            status_code=_error_to_status(e.code),
            detail=e.to_dict()["error"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"code": "INVALID_REQUEST", "message": str(e)})
    except Exception as e:
        logger.exception("Unexpected session create error")
        raise HTTPException(status_code=500, detail={"code": "INTERNAL_ERROR", "message": str(e)})


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    session_service: SessionServiceDep,
):
    """Get session information"""
    try:
        session = await session_service.get_session(session_id)

        provider = session_service.get_provider(session.provider)
        supported_models = provider.supported_models if provider else []

        return SessionResponse(
            session_id=session.id,
            provider=session.provider,
            model=session.model,
            status=session.status.value,
            supported_models=supported_models,
            created_at=session.created_at,
            expires_at=session.expires_at,
        )

    except LLMHubError as e:
        raise HTTPException(
            status_code=_error_to_status(e.code),
            detail=e.to_dict()["error"],
        )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    session_service: SessionServiceDep,
):
    """Delete a session"""
    try:
        deleted = await session_service.delete_session(session_id)
        if not deleted:
            raise HTTPException(status_code=404, detail={"code": "SESSION_NOT_FOUND", "message": f"Session not found: {session_id}"})

        return {"success": True, "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected session delete error")
        raise HTTPException(status_code=500, detail={"code": "INTERNAL_ERROR", "message": str(e)})


@router.post("/{session_id}/close", response_model=CloseSessionResponse)
async def close_session(
    session_id: str,
    request: CloseSessionRequest,
    memory_service: MemoryServiceDep,
):
    """
    Close session and generate compressed memory.

    Use this when ending a conversation to export context for future sessions.
    """
    try:
        compression = CompressionLevel(request.compression)

        result = await memory_service.close_session_with_memory(
            session_id=session_id,
            compression=compression,
            provider=request.provider,
        )

        return CloseSessionResponse(
            success=result["success"],
            session_id=result["session_id"],
            status=result["status"],
            compressed_memory=result["compressed_memory"],
        )

    except LLMHubError as e:
        raise HTTPException(
            status_code=_error_to_status(e.code),
            detail=e.to_dict()["error"],
        )


@router.get("/{session_id}/memory", response_model=SessionMemoryResponse)
async def get_session_memory(
    session_id: str,
    memory_service: MemoryServiceDep,
    compression: Literal["none", "low", "medium", "high"] = Query(default="medium"),
    provider: str = Query(default="claude"),
    format: Literal["markdown", "json"] = Query(default="markdown"),
):
    """
    Export session memory with optional compression.

    Use this to:
    - Export conversation for backup
    - Generate compressed context for new sessions
    - Create documentation from conversations
    """
    try:
        compression_level = CompressionLevel(compression)

        result = await memory_service.export_memory(
            session_id=session_id,
            compression=compression_level,
            provider=provider,
            format=format,
        )

        return SessionMemoryResponse(
            session_id=result["session_id"],
            compression=result["compression"],
            format=result["format"],
            content=result.get("content"),
            compressed_memory=result.get("compressed_memory"),
            metadata=result["metadata"],
        )

    except LLMHubError as e:
        raise HTTPException(
            status_code=_error_to_status(e.code),
            detail=e.to_dict()["error"],
        )


def _error_to_status(code: str) -> int:
    """Map error code to HTTP status"""
    status_map = {
        "PROVIDER_MISMATCH": 400,
        "INVALID_MODEL": 400,
        "SESSION_NOT_FOUND": 404,
        "SESSION_EXPIRED": 410,
        "PROVIDER_ERROR": 502,
        "PROVIDER_TIMEOUT": 504,
        "TOKEN_EXPIRED": 401,
    }
    return status_map.get(code, 500)
