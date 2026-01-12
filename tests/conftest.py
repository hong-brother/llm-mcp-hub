"""Pytest fixtures for API testing"""
import pytest
from typing import AsyncIterator
from unittest.mock import AsyncMock

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from llm_mcp_hub.core.config import Settings
from llm_mcp_hub.infrastructure.session import MemorySessionStore
from llm_mcp_hub.infrastructure.providers.base import ProviderAdapter
from llm_mcp_hub.services import ChatService, SessionService, MemoryService
from llm_mcp_hub.api.v1 import router as api_v1_router
from llm_mcp_hub.api.v1.health import router as health_router


class MockClaudeAdapter(ProviderAdapter):
    """Mock Claude adapter for testing"""

    SUPPORTED_MODELS = [
        "claude-sonnet-4-5-20250929",
        "claude-opus-4-5-20251101",
        "claude-haiku-4-5-20251001",
    ]

    MODEL_ALIASES = {
        "sonnet": "claude-sonnet-4-5-20250929",
        "opus": "claude-opus-4-5-20251101",
        "haiku": "claude-haiku-4-5-20251001",
    }

    def __init__(self):
        self._supported_models = self.SUPPORTED_MODELS.copy()
        self._default_model = self.SUPPORTED_MODELS[0]

    @property
    def name(self) -> str:
        return "claude"

    @property
    def supported_models(self) -> list[str]:
        return self._supported_models

    @property
    def default_model(self) -> str:
        return self._default_model

    async def initialize(self) -> None:
        pass

    def resolve_model(self, model: str | None) -> str:
        if model is None:
            return self._default_model
        if model in self.MODEL_ALIASES:
            return self.MODEL_ALIASES[model]
        return model

    async def chat(
        self,
        prompt: str,
        model: str | None = None,
        system_prompt: str | None = None,
        conversation: list[dict[str, str]] | None = None,
        timeout: float = 120.0,
    ) -> str:
        from llm_mcp_hub.core.exceptions import InvalidModelError
        effective_model = self.resolve_model(model)
        if effective_model not in self._supported_models:
            raise InvalidModelError(effective_model, provider="claude", supported_models=self._supported_models)
        return f"Mock Claude response to: {prompt}"

    async def chat_stream(
        self,
        prompt: str,
        model: str | None = None,
        system_prompt: str | None = None,
        conversation: list[dict[str, str]] | None = None,
    ) -> AsyncIterator[str]:
        chunks = ["Mock ", "Claude ", "streaming ", "response"]
        for chunk in chunks:
            yield chunk

    async def health_check(self) -> dict:
        return {
            "status": "healthy",
            "supported_models": self._supported_models,
        }


class MockGeminiAdapter(ProviderAdapter):
    """Mock Gemini adapter for testing"""

    SUPPORTED_MODELS = [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ]

    def __init__(self):
        self._supported_models = self.SUPPORTED_MODELS.copy()
        self._default_model = self.SUPPORTED_MODELS[0]

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def supported_models(self) -> list[str]:
        return self._supported_models

    @property
    def default_model(self) -> str:
        return self._default_model

    async def initialize(self) -> None:
        pass

    async def chat(
        self,
        prompt: str,
        model: str | None = None,
        system_prompt: str | None = None,
        conversation: list[dict[str, str]] | None = None,
        timeout: float = 120.0,
    ) -> str:
        return f"Mock Gemini response to: {prompt}"

    async def chat_stream(
        self,
        prompt: str,
        model: str | None = None,
        system_prompt: str | None = None,
        conversation: list[dict[str, str]] | None = None,
    ) -> AsyncIterator[str]:
        chunks = ["Mock ", "Gemini ", "streaming ", "response"]
        for chunk in chunks:
            yield chunk

    async def health_check(self) -> dict:
        return {
            "status": "healthy",
            "supported_models": self._supported_models,
        }


def create_test_app() -> FastAPI:
    """Create test FastAPI application with mock providers"""
    app = FastAPI(title="LLM MCP Hub Test")

    # Include routers
    app.include_router(api_v1_router)
    app.include_router(health_router)

    return app


@pytest.fixture
def mock_settings():
    """Create mock settings"""
    return Settings(
        app_name="LLM MCP Hub Test",
        app_version="0.1.0-test",
        debug=True,
        redis_url="redis://localhost:6379",
        session_ttl=3600,
    )


@pytest.fixture
def session_store():
    """Create in-memory session store"""
    return MemorySessionStore(ttl=3600)


@pytest.fixture
def mock_providers():
    """Create mock providers"""
    return {
        "claude": MockClaudeAdapter(),
        "gemini": MockGeminiAdapter(),
    }


@pytest.fixture
def session_service(session_store, mock_providers):
    """Create session service with mock providers"""
    return SessionService(
        session_store=session_store,
        providers=mock_providers,
        default_ttl=3600,
    )


@pytest.fixture
def chat_service(mock_providers, session_service):
    """Create chat service with mock providers"""
    return ChatService(
        providers=mock_providers,
        session_service=session_service,
    )


@pytest.fixture
def memory_service(session_service, chat_service):
    """Create memory service"""
    return MemoryService(
        session_service=session_service,
        chat_service=chat_service,
    )


@pytest.fixture
def test_app(mock_settings, session_store, mock_providers, session_service, chat_service, memory_service):
    """Create test application with all services"""
    app = create_test_app()

    # Set app state
    app.state.settings = mock_settings
    app.state.session_store = session_store
    app.state.providers = mock_providers
    app.state.session_service = session_service
    app.state.chat_service = chat_service
    app.state.memory_service = memory_service

    return app


@pytest.fixture
async def client(test_app):
    """Create async test client"""
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test"
    ) as ac:
        yield ac
