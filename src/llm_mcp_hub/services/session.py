"""Session management service"""
import logging
from datetime import datetime, timedelta
from typing import Any

from llm_mcp_hub.core.exceptions import (
    SessionNotFoundError,
    SessionExpiredError,
    ProviderMismatchError,
    InvalidModelError,
)
from llm_mcp_hub.domain import Session, SessionContext, SessionStatus
from llm_mcp_hub.infrastructure.session import SessionStore
from llm_mcp_hub.infrastructure.providers import ProviderAdapter

logger = logging.getLogger(__name__)


class SessionService:
    """Session management service"""

    def __init__(
        self,
        session_store: SessionStore,
        providers: dict[str, ProviderAdapter],
        default_ttl: int = 3600,
    ):
        self._store = session_store
        self._providers = providers
        self._default_ttl = default_ttl

    async def create_session(
        self,
        provider: str,
        model: str | None = None,
        system_prompt: str | None = None,
        context: dict[str, Any] | None = None,
        ttl: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Session:
        """Create a new session"""
        # Validate provider
        if provider not in self._providers:
            raise ValueError(f"Unknown provider: {provider}")

        adapter = self._providers[provider]

        # Resolve model
        effective_model = adapter.resolve_model(model)
        if not adapter.is_model_supported(effective_model):
            raise InvalidModelError(
                effective_model,
                provider=provider,
                supported_models=adapter.supported_models,
            )

        # Build context
        session_context = None
        if context:
            session_context = SessionContext(
                memory=context.get("memory"),
                previous_summary=context.get("previous_summary"),
                files=context.get("files", []),
            )

        # Calculate expiration
        session_ttl = ttl or self._default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=session_ttl)

        # Create session
        session = Session(
            provider=provider,
            model=effective_model,
            system_prompt=system_prompt,
            context=session_context,
            expires_at=expires_at,
            metadata=metadata or {},
        )

        # Store session
        session = await self._store.create(session)

        logger.info(f"Created session: {session.id}, provider: {provider}, model: {effective_model}")
        return session

    async def get_session(self, session_id: str) -> Session:
        """Get session by ID"""
        session = await self._store.get(session_id)

        if session is None:
            raise SessionNotFoundError(session_id)

        if session.status == SessionStatus.EXPIRED:
            raise SessionExpiredError(session_id)

        if not session.is_active():
            raise SessionExpiredError(session_id)

        return session

    async def get_session_or_none(self, session_id: str | None) -> Session | None:
        """Get session by ID, return None if not found or no ID provided"""
        if not session_id:
            return None

        try:
            return await self.get_session(session_id)
        except (SessionNotFoundError, SessionExpiredError):
            return None

    async def update_session(self, session: Session) -> Session:
        """Update session"""
        return await self._store.update(session)

    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        return await self._store.delete(session_id)

    async def close_session(self, session_id: str) -> Session:
        """Close session"""
        session = await self.get_session(session_id)
        session.close()
        return await self._store.update(session)

    async def list_sessions(self, limit: int = 100, offset: int = 0) -> list[Session]:
        """List sessions"""
        return await self._store.list_sessions(limit=limit, offset=offset)

    def validate_provider_match(self, session: Session, requested_provider: str | None) -> None:
        """Validate that requested provider matches session provider"""
        if requested_provider and requested_provider != session.provider:
            raise ProviderMismatchError(session.provider, requested_provider)

    def validate_model(self, session: Session, requested_model: str | None) -> str:
        """Validate and resolve model for session"""
        adapter = self._providers.get(session.provider)
        if not adapter:
            raise ValueError(f"Unknown provider: {session.provider}")

        # Use session's default model if not specified
        effective_model = requested_model or session.model

        # Resolve aliases
        effective_model = adapter.resolve_model(effective_model)

        # Validate model is supported
        if not adapter.is_model_supported(effective_model):
            raise InvalidModelError(
                effective_model,
                provider=session.provider,
                supported_models=adapter.supported_models,
            )

        return effective_model

    def get_provider(self, name: str) -> ProviderAdapter | None:
        """Get provider adapter by name"""
        return self._providers.get(name)

    def get_available_providers(self) -> list[dict[str, Any]]:
        """Get list of available providers with their models"""
        return [
            {
                "name": name,
                "models": adapter.supported_models,
                "default_model": adapter.default_model,
            }
            for name, adapter in self._providers.items()
        ]
