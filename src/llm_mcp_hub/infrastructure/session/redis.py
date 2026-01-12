"""Redis session store for production"""
import json
import logging
from datetime import timedelta

import redis.asyncio as redis

from llm_mcp_hub.domain import Session
from .base import SessionStore

logger = logging.getLogger(__name__)


class RedisSessionStore(SessionStore):
    """Redis-based session store implementation"""

    KEY_PREFIX = "llm_hub:session:"

    def __init__(self, redis_url: str, ttl: int = 3600):
        self._redis_url = redis_url
        self._ttl = ttl
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        """Connect to Redis"""
        if self._client is None:
            self._client = redis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await self._client.ping()
            logger.info("Connected to Redis")

    async def _ensure_connected(self) -> redis.Redis:
        """Ensure Redis connection is established"""
        if self._client is None:
            await self.connect()
        return self._client  # type: ignore

    def _key(self, session_id: str) -> str:
        """Generate Redis key for session"""
        return f"{self.KEY_PREFIX}{session_id}"

    async def create(self, session: Session) -> Session:
        """Create a new session"""
        client = await self._ensure_connected()

        # Calculate TTL
        ttl = self._ttl
        if session.expires_at:
            from datetime import datetime

            delta = session.expires_at - datetime.utcnow()
            ttl = max(int(delta.total_seconds()), 1)
        else:
            from datetime import datetime

            session.expires_at = datetime.utcnow() + timedelta(seconds=self._ttl)

        # Store session
        key = self._key(session.id)
        await client.setex(key, ttl, json.dumps(session.to_dict()))

        logger.debug(f"Created session: {session.id}, TTL: {ttl}s")
        return session

    async def get(self, session_id: str) -> Session | None:
        """Get session by ID"""
        client = await self._ensure_connected()

        key = self._key(session_id)
        data = await client.get(key)

        if data is None:
            return None

        return Session.from_dict(json.loads(data))

    async def update(self, session: Session) -> Session:
        """Update existing session"""
        client = await self._ensure_connected()

        from datetime import datetime

        session.updated_at = datetime.utcnow()

        key = self._key(session.id)

        # Get remaining TTL
        ttl = await client.ttl(key)
        if ttl <= 0:
            ttl = self._ttl

        await client.setex(key, ttl, json.dumps(session.to_dict()))

        logger.debug(f"Updated session: {session.id}")
        return session

    async def delete(self, session_id: str) -> bool:
        """Delete session by ID"""
        client = await self._ensure_connected()

        key = self._key(session_id)
        result = await client.delete(key)

        logger.debug(f"Deleted session: {session_id}, success: {result > 0}")
        return result > 0

    async def exists(self, session_id: str) -> bool:
        """Check if session exists"""
        client = await self._ensure_connected()

        key = self._key(session_id)
        return await client.exists(key) > 0

    async def list_sessions(self, limit: int = 100, offset: int = 0) -> list[Session]:
        """List sessions with pagination"""
        client = await self._ensure_connected()

        # Get all session keys
        pattern = f"{self.KEY_PREFIX}*"
        keys = []
        async for key in client.scan_iter(match=pattern, count=100):
            keys.append(key)

        # Sort and paginate
        keys.sort(reverse=True)
        paginated_keys = keys[offset : offset + limit]

        # Get sessions
        sessions = []
        for key in paginated_keys:
            data = await client.get(key)
            if data:
                sessions.append(Session.from_dict(json.loads(data)))

        return sessions

    async def close(self) -> None:
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Redis connection closed")

    async def health_check(self) -> dict:
        """Check Redis health"""
        try:
            client = await self._ensure_connected()
            await client.ping()
            return {"status": "healthy", "latency_ms": 0}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
