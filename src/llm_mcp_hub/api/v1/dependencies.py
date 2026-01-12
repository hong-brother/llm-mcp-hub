"""API dependencies"""
from typing import Annotated

from fastapi import Depends, Header, Request

from llm_mcp_hub.services import ChatService, SessionService, MemoryService


def get_session_service(request: Request) -> SessionService:
    """Get session service from app state"""
    return request.app.state.session_service


def get_chat_service(request: Request) -> ChatService:
    """Get chat service from app state"""
    return request.app.state.chat_service


def get_memory_service(request: Request) -> MemoryService:
    """Get memory service from app state"""
    return request.app.state.memory_service


def get_session_id(x_session_id: Annotated[str | None, Header()] = None) -> str | None:
    """Get session ID from X-Session-ID header"""
    return x_session_id


# Type aliases for dependency injection
SessionServiceDep = Annotated[SessionService, Depends(get_session_service)]
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
MemoryServiceDep = Annotated[MemoryService, Depends(get_memory_service)]
SessionIdDep = Annotated[str | None, Depends(get_session_id)]
