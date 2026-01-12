"""Tests for domain models"""
import pytest
from datetime import datetime, timedelta
from llm_mcp_hub.domain import Message, MessageRole, Session, SessionContext, SessionStatus


class TestMessage:
    def test_create_user_message(self):
        msg = Message.user("Hello")
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"
        assert isinstance(msg.timestamp, datetime)

    def test_create_assistant_message(self):
        msg = Message.assistant("Hi there!")
        assert msg.role == MessageRole.ASSISTANT
        assert msg.content == "Hi there!"

    def test_create_system_message(self):
        msg = Message.system("You are a helpful assistant")
        assert msg.role == MessageRole.SYSTEM
        assert msg.content == "You are a helpful assistant"

    def test_message_to_dict(self):
        msg = Message.user("Test")
        data = msg.to_dict()
        assert data["role"] == "user"
        assert data["content"] == "Test"
        assert "timestamp" in data

    def test_message_from_dict(self):
        data = {
            "role": "assistant",
            "content": "Response",
            "timestamp": "2024-01-01T00:00:00",
        }
        msg = Message.from_dict(data)
        assert msg.role == MessageRole.ASSISTANT
        assert msg.content == "Response"


class TestSessionContext:
    def test_empty_context(self):
        ctx = SessionContext()
        assert ctx.to_system_prompt() is None

    def test_context_with_memory(self):
        ctx = SessionContext(memory="# Project Rules\n- Rule 1")
        prompt = ctx.to_system_prompt()
        assert "Project Rules" in prompt
        assert "Rule 1" in prompt

    def test_context_with_all_fields(self):
        ctx = SessionContext(
            memory="# Memory",
            previous_summary="Previous session summary",
            files=[{"name": "file.py", "content": "code"}],
        )
        prompt = ctx.to_system_prompt()
        assert "Memory" in prompt
        assert "Previous session summary" in prompt
        assert "file.py" in prompt


class TestSession:
    def test_create_session(self):
        session = Session(
            provider="claude",
            model="claude-sonnet-4-5-20250929",
        )
        assert session.provider == "claude"
        assert session.model == "claude-sonnet-4-5-20250929"
        assert session.status == SessionStatus.ACTIVE
        assert len(session.messages) == 0

    def test_add_messages(self):
        session = Session(provider="claude", model="sonnet")
        session.add_user_message("Hello")
        session.add_assistant_message("Hi!")

        assert len(session.messages) == 2
        assert session.messages[0].role == MessageRole.USER
        assert session.messages[1].role == MessageRole.ASSISTANT

    def test_session_is_active(self):
        session = Session(
            provider="claude",
            model="sonnet",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        assert session.is_active() is True

    def test_session_expired(self):
        session = Session(
            provider="claude",
            model="sonnet",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        assert session.is_active() is False

    def test_close_session(self):
        session = Session(provider="claude", model="sonnet")
        session.close()
        assert session.status == SessionStatus.CLOSED
        assert session.is_active() is False

    def test_session_to_dict(self):
        session = Session(provider="claude", model="sonnet")
        session.add_user_message("Test")
        data = session.to_dict()

        assert data["provider"] == "claude"
        assert data["model"] == "sonnet"
        assert len(data["messages"]) == 1

    def test_session_from_dict(self):
        data = {
            "id": "sess_123",
            "provider": "gemini",
            "model": "gemini-2.5-pro",
            "status": "active",
            "messages": [{"role": "user", "content": "Hi", "timestamp": "2024-01-01T00:00:00"}],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        session = Session.from_dict(data)
        assert session.id == "sess_123"
        assert session.provider == "gemini"
        assert len(session.messages) == 1

    def test_get_conversation_for_llm(self):
        session = Session(
            provider="claude",
            model="sonnet",
            system_prompt="You are helpful",
        )
        session.add_user_message("Question")
        session.add_assistant_message("Answer")

        conv = session.get_conversation_for_llm()
        assert conv[0]["role"] == "system"
        assert conv[1]["role"] == "user"
        assert conv[2]["role"] == "assistant"
