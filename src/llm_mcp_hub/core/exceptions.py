"""Custom exceptions for LLM MCP Hub"""
from typing import Any


class LLMHubError(Exception):
    """Base exception for LLM MCP Hub"""

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", details: dict[str, Any] | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class ProviderError(LLMHubError):
    """LLM Provider call failed"""

    def __init__(self, message: str, provider: str | None = None, details: dict[str, Any] | None = None):
        details = details or {}
        if provider:
            details["provider"] = provider
        super().__init__(message, code="PROVIDER_ERROR", details=details)


class ProviderTimeoutError(LLMHubError):
    """LLM Provider response timeout"""

    def __init__(self, provider: str, timeout: float):
        super().__init__(
            message=f"Provider '{provider}' timed out after {timeout}s",
            code="PROVIDER_TIMEOUT",
            details={"provider": provider, "timeout_seconds": timeout},
        )


class InvalidModelError(LLMHubError):
    """Unsupported model requested"""

    def __init__(self, model: str, provider: str | None = None, supported_models: list[str] | None = None):
        details: dict[str, Any] = {"requested_model": model}
        if provider:
            details["provider"] = provider
        if supported_models:
            details["supported_models"] = supported_models
        super().__init__(
            message=f"Unsupported model: {model}",
            code="INVALID_MODEL",
            details=details,
        )


class SessionNotFoundError(LLMHubError):
    """Session not found"""

    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session not found: {session_id}",
            code="SESSION_NOT_FOUND",
            details={"session_id": session_id},
        )


class SessionExpiredError(LLMHubError):
    """Session expired"""

    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session expired: {session_id}",
            code="SESSION_EXPIRED",
            details={"session_id": session_id},
        )


class ProviderMismatchError(LLMHubError):
    """Session provider mismatch"""

    def __init__(self, session_provider: str, requested_provider: str):
        super().__init__(
            message=f"Session uses '{session_provider}' provider, cannot use '{requested_provider}'",
            code="PROVIDER_MISMATCH",
            details={
                "session_provider": session_provider,
                "requested_provider": requested_provider,
            },
        )


class TokenExpiredError(LLMHubError):
    """OAuth token expired"""

    def __init__(self, provider: str):
        super().__init__(
            message=f"OAuth token expired for provider: {provider}",
            code="TOKEN_EXPIRED",
            details={"provider": provider},
        )
