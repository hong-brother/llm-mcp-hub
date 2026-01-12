"""Abstract base class for session storage"""
from abc import ABC, abstractmethod

from llm_mcp_hub.domain import Session


class SessionStore(ABC):
    """Abstract session store interface"""

    @abstractmethod
    async def create(self, session: Session) -> Session:
        """Create a new session"""
        pass

    @abstractmethod
    async def get(self, session_id: str) -> Session | None:
        """Get session by ID"""
        pass

    @abstractmethod
    async def update(self, session: Session) -> Session:
        """Update existing session"""
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """Delete session by ID"""
        pass

    @abstractmethod
    async def exists(self, session_id: str) -> bool:
        """Check if session exists"""
        pass

    @abstractmethod
    async def list_sessions(self, limit: int = 100, offset: int = 0) -> list[Session]:
        """List sessions with pagination"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connection/cleanup resources"""
        pass
