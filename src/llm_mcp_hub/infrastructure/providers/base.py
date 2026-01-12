"""Abstract base class for LLM provider adapters"""
from abc import ABC, abstractmethod
from typing import AsyncIterator


class ProviderAdapter(ABC):
    """Abstract LLM provider adapter interface"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass

    @property
    @abstractmethod
    def supported_models(self) -> list[str]:
        """List of supported models"""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model"""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider (called at server startup)"""
        pass

    @abstractmethod
    async def chat(
        self,
        prompt: str,
        model: str | None = None,
        system_prompt: str | None = None,
        conversation: list[dict[str, str]] | None = None,
        timeout: float = 120.0,
    ) -> str:
        """Send chat request and get response"""
        pass

    @abstractmethod
    async def chat_stream(
        self,
        prompt: str,
        model: str | None = None,
        system_prompt: str | None = None,
        conversation: list[dict[str, str]] | None = None,
    ) -> AsyncIterator[str]:
        """Send chat request and stream response"""
        pass

    @abstractmethod
    async def health_check(self) -> dict:
        """Check provider health status"""
        pass

    def is_model_supported(self, model: str) -> bool:
        """Check if model is supported"""
        return model in self.supported_models

    def resolve_model(self, model: str | None) -> str:
        """Resolve model name (handle aliases)"""
        return model if model else self.default_model
