"""Tests for session store"""
import pytest
from datetime import datetime, timedelta
from llm_mcp_hub.domain import Session, SessionStatus
from llm_mcp_hub.infrastructure.session import MemorySessionStore


@pytest.fixture
def session_store():
    return MemorySessionStore(ttl=3600)


@pytest.fixture
def sample_session():
    return Session(
        provider="claude",
        model="claude-sonnet-4-5-20250929",
    )


class TestMemorySessionStore:
    @pytest.mark.asyncio
    async def test_create_session(self, session_store, sample_session):
        created = await session_store.create(sample_session)
        assert created.id == sample_session.id
        assert created.expires_at is not None

    @pytest.mark.asyncio
    async def test_get_session(self, session_store, sample_session):
        await session_store.create(sample_session)
        retrieved = await session_store.get(sample_session.id)
        assert retrieved is not None
        assert retrieved.id == sample_session.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, session_store):
        retrieved = await session_store.get("nonexistent")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_update_session(self, session_store, sample_session):
        await session_store.create(sample_session)
        sample_session.add_user_message("Hello")
        updated = await session_store.update(sample_session)
        assert len(updated.messages) == 1

    @pytest.mark.asyncio
    async def test_delete_session(self, session_store, sample_session):
        await session_store.create(sample_session)
        deleted = await session_store.delete(sample_session.id)
        assert deleted is True

        retrieved = await session_store.get(sample_session.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self, session_store):
        deleted = await session_store.delete("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_exists(self, session_store, sample_session):
        await session_store.create(sample_session)
        assert await session_store.exists(sample_session.id) is True
        assert await session_store.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_list_sessions(self, session_store):
        for i in range(5):
            session = Session(provider="claude", model="sonnet")
            await session_store.create(session)

        sessions = await session_store.list_sessions(limit=3)
        assert len(sessions) == 3

    @pytest.mark.asyncio
    async def test_expired_session(self, session_store):
        session = Session(
            provider="claude",
            model="sonnet",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        await session_store.create(session)

        retrieved = await session_store.get(session.id)
        assert retrieved is not None
        assert retrieved.status == SessionStatus.EXPIRED

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, session_store):
        # Create expired session
        expired = Session(
            provider="claude",
            model="sonnet",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        await session_store.create(expired)

        # Create active session
        active = Session(
            provider="claude",
            model="sonnet",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        await session_store.create(active)

        count = await session_store.cleanup_expired()
        assert count == 1

        # Active session should remain
        assert await session_store.exists(active.id) is True
        assert await session_store.exists(expired.id) is False
