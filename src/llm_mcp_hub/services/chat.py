"""Chat service for handling LLM conversations"""
import logging
from typing import AsyncIterator, Any

from llm_mcp_hub.core.exceptions import ProviderError
from llm_mcp_hub.domain import Session, Message
from llm_mcp_hub.infrastructure.providers import ProviderAdapter
from .session import SessionService

logger = logging.getLogger(__name__)


class ChatService:
    """Chat service for handling LLM conversations"""

    def __init__(
        self,
        providers: dict[str, ProviderAdapter],
        session_service: SessionService,
    ):
        self._providers = providers
        self._session_service = session_service

    async def chat(
        self,
        prompt: str,
        provider: str | None = None,
        model: str | None = None,
        session_id: str | None = None,
        system_prompt: str | None = None,
        timeout: float = 120.0,
    ) -> dict[str, Any]:
        """
        Send chat request and get response.

        Returns dict with:
        - response: str - The LLM response
        - session_id: str | None - Session ID if session was used
        - provider: str - Provider used
        - model: str - Model used
        """
        # Get or create context
        session = await self._session_service.get_session_or_none(session_id)

        if session:
            # Validate provider match
            self._session_service.validate_provider_match(session, provider)

            # Resolve model
            effective_model = self._session_service.validate_model(session, model)
            effective_provider = session.provider

            # Get system prompt from session
            effective_system_prompt = session._build_system_prompt() or system_prompt
        else:
            # No session - use provided values
            effective_provider = provider or "claude"
            if effective_provider not in self._providers:
                raise ProviderError(f"Unknown provider: {effective_provider}")

            adapter = self._providers[effective_provider]
            effective_model = adapter.resolve_model(model)
            effective_system_prompt = system_prompt

        # Get adapter
        adapter = self._providers[effective_provider]

        # Add user message to session
        if session:
            session.add_user_message(prompt)

        # Send request
        logger.info(f"Chat request: provider={effective_provider}, model={effective_model}")

        response = await adapter.chat(
            prompt=prompt,
            model=effective_model,
            system_prompt=effective_system_prompt,
            timeout=timeout,
        )

        # Add assistant response to session
        if session:
            session.add_assistant_message(response)
            await self._session_service.update_session(session)

        return {
            "response": response,
            "session_id": session.id if session else None,
            "provider": effective_provider,
            "model": effective_model,
        }

    async def chat_stream(
        self,
        prompt: str,
        provider: str | None = None,
        model: str | None = None,
        session_id: str | None = None,
        system_prompt: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Stream chat response.

        Yields dicts with:
        - type: str - Event type (content, done)
        - text: str - Content text (for content events)
        - session_id: str | None - Session ID
        - provider: str - Provider used
        - model: str - Model used
        """
        # Get or create context
        session = await self._session_service.get_session_or_none(session_id)

        if session:
            self._session_service.validate_provider_match(session, provider)
            effective_model = self._session_service.validate_model(session, model)
            effective_provider = session.provider
            effective_system_prompt = session._build_system_prompt() or system_prompt
        else:
            effective_provider = provider or "claude"
            if effective_provider not in self._providers:
                raise ProviderError(f"Unknown provider: {effective_provider}")

            adapter = self._providers[effective_provider]
            effective_model = adapter.resolve_model(model)
            effective_system_prompt = system_prompt

        adapter = self._providers[effective_provider]

        # Add user message to session
        if session:
            session.add_user_message(prompt)

        logger.info(f"Chat stream: provider={effective_provider}, model={effective_model}")

        # Collect full response for session
        full_response = []

        async for chunk in adapter.chat_stream(
            prompt=prompt,
            model=effective_model,
            system_prompt=effective_system_prompt,
        ):
            full_response.append(chunk)
            yield {
                "type": "content",
                "text": chunk,
                "session_id": session.id if session else None,
                "provider": effective_provider,
                "model": effective_model,
            }

        # Add assistant response to session
        if session:
            session.add_assistant_message("".join(full_response))
            await self._session_service.update_session(session)

        yield {
            "type": "done",
            "session_id": session.id if session else None,
            "provider": effective_provider,
            "model": effective_model,
        }

    async def chat_with_messages(
        self,
        messages: list[dict[str, str]],
        provider: str | None = None,
        model: str | None = None,
        session_id: str | None = None,
        timeout: float = 120.0,
    ) -> dict[str, Any]:
        """
        Chat with message history (OpenAI-compatible format).

        Messages format: [{"role": "user", "content": "..."}, ...]
        """
        # Extract the last user message as the prompt
        user_messages = [m for m in messages if m.get("role") == "user"]
        if not user_messages:
            raise ValueError("No user message found in messages")

        prompt = user_messages[-1]["content"]

        # Extract system prompt if present
        system_messages = [m for m in messages if m.get("role") == "system"]
        system_prompt = system_messages[0]["content"] if system_messages else None

        return await self.chat(
            prompt=prompt,
            provider=provider,
            model=model,
            session_id=session_id,
            system_prompt=system_prompt,
            timeout=timeout,
        )
