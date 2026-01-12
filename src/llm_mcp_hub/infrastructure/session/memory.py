"""In-memory session store for development and testing"""
import asyncio
from datetime import datetime, timedelta

from llm_mcp_hub.domain import Session, SessionStatus
from .base import SessionStore


class MemorySessionStore(SessionStore):
    """In-memory session store implementation"""

    def __init__(self, ttl: int = 3600):
        self._sessions: dict[str, Session] = {}
        self._ttl = ttl
        self._lock = asyncio.Lock()

    async def create(self, session: Session) -> Session:
        """Create a new session"""
        async with self._lock:
            # Set expiration if not already set
            if not session.expires_at:
                session.expires_at = datetime.utcnow() + timedelta(seconds=self._ttl)

            self._sessions[session.id] = session
            return session

    async def get(self, session_id: str) -> Session | None:
        """Get session by ID"""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None

            # Check expiration
            if session.expires_at and datetime.utcnow() > session.expires_at:
                session.status = SessionStatus.EXPIRED
                return session

            return session

    async def update(self, session: Session) -> Session:
        """Update existing session"""
        async with self._lock:
            session.updated_at = datetime.utcnow()
            self._sessions[session.id] = session
            return session

    async def delete(self, session_id: str) -> bool:
        """Delete session by ID"""
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    async def exists(self, session_id: str) -> bool:
        """Check if session exists"""
        async with self._lock:
            return session_id in self._sessions

    async def list_sessions(self, limit: int = 100, offset: int = 0) -> list[Session]:
        """List sessions with pagination"""
        async with self._lock:
            sessions = list(self._sessions.values())
            # Sort by created_at descending
            sessions.sort(key=lambda s: s.created_at, reverse=True)
            return sessions[offset : offset + limit]

    async def close(self) -> None:
        """Clear all sessions"""
        async with self._lock:
            self._sessions.clear()

    async def cleanup_expired(self) -> int:
        """Remove expired sessions, return count of removed sessions"""
        async with self._lock:
            now = datetime.utcnow()
            expired_ids = [
                sid
                for sid, session in self._sessions.items()
                if session.expires_at and now > session.expires_at
            ]
            for sid in expired_ids:
                del self._sessions[sid]
            return len(expired_ids)
