"""API request/response schemas"""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# Chat Schemas
class ChatMessage(BaseModel):
    """Chat message"""

    role: Literal["user", "assistant", "system"]
    content: str


class ChatCompletionRequest(BaseModel):
    """Chat completion request"""

    messages: list[ChatMessage]
    provider: str | None = Field(default=None, description="LLM provider (claude, gemini)")
    model: str | None = Field(default=None, description="Model name or alias")
    stream: bool = Field(default=False, description="Enable streaming response")
    timeout: float = Field(default=120.0, description="Timeout in seconds")


class ChatCompletionResponse(BaseModel):
    """Chat completion response"""

    response: str
    session_id: str | None
    provider: str
    model: str


class StreamEvent(BaseModel):
    """SSE stream event"""

    type: Literal["content", "thinking", "error", "done"]
    text: str | None = None
    session_id: str | None = None
    provider: str | None = None
    model: str | None = None
    error: str | None = None


# Session Schemas
class SessionContextRequest(BaseModel):
    """Session context for creation"""

    memory: str | None = Field(default=None, description="Project memory content")
    previous_summary: str | None = Field(default=None, description="Previous session summary")
    files: list[dict[str, str]] = Field(default_factory=list, description="Reference files")


class CreateSessionRequest(BaseModel):
    """Create session request"""

    provider: str = Field(description="LLM provider (claude, gemini)")
    model: str | None = Field(default=None, description="Default model for session")
    system_prompt: str | None = Field(default=None, description="System prompt")
    context: SessionContextRequest | None = Field(default=None, description="Session context")
    ttl: int = Field(default=3600, description="Session TTL in seconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata")


class SessionResponse(BaseModel):
    """Session response"""

    session_id: str
    provider: str
    model: str
    status: str
    supported_models: list[str]
    created_at: datetime
    expires_at: datetime | None


class CloseSessionRequest(BaseModel):
    """Close session request"""

    compression: Literal["none", "low", "medium", "high"] = Field(
        default="medium",
        description="Compression level for memory export",
    )
    provider: str = Field(
        default="claude",
        description="Provider to use for compression",
    )


class CloseSessionResponse(BaseModel):
    """Close session response"""

    success: bool
    session_id: str
    status: str
    compressed_memory: str


class SessionMemoryResponse(BaseModel):
    """Session memory export response"""

    session_id: str
    compression: str
    format: str
    content: str | None = None
    compressed_memory: str | None = None
    metadata: dict[str, Any]


class SessionListItem(BaseModel):
    """Session list item"""

    session_id: str
    provider: str
    model: str
    status: str
    created_at: datetime
    expires_at: datetime | None
    message_count: int = 0


class SessionListResponse(BaseModel):
    """Session list response"""

    sessions: list[SessionListItem]
    total: int
    limit: int
    offset: int


# Provider Schemas
class ProviderInfo(BaseModel):
    """Provider information"""

    name: str
    models: list[str]
    default_model: str


class ProviderDetailResponse(BaseModel):
    """Provider detail response"""

    name: str
    status: str
    models: list[str]
    default_model: str


# Health Schemas
class HealthResponse(BaseModel):
    """Health check response"""

    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ComponentHealth(BaseModel):
    """Component health status"""

    status: Literal["healthy", "unhealthy"]
    latency_ms: int | None = None
    error: str | None = None
    supported_models: list[str] | None = None
    last_success: datetime | None = None


class DetailedHealthResponse(BaseModel):
    """Detailed health check response"""

    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    components: dict[str, ComponentHealth]


class TokenHealthResponse(BaseModel):
    """Token health response"""

    claude: dict[str, Any] | None = None
    gemini: dict[str, Any] | None = None


# Error Schemas
class ErrorDetail(BaseModel):
    """Error detail"""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response"""

    error: ErrorDetail
