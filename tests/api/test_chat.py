"""Tests for Chat API endpoints"""
import pytest


class TestChatEndpoints:
    """Test /v1/chat endpoints"""

    @pytest.mark.asyncio
    async def test_chat_completion_basic(self, client):
        """POST /v1/chat/completions - Basic chat completion"""
        response = await client.post(
            "/v1/chat/completions",
            json={
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ],
                "provider": "claude"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["provider"] == "claude"
        assert "model" in data
        assert "Mock Claude response" in data["response"]

    @pytest.mark.asyncio
    async def test_chat_completion_with_gemini(self, client):
        """POST /v1/chat/completions - Chat with Gemini"""
        response = await client.post(
            "/v1/chat/completions",
            json={
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ],
                "provider": "gemini"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "gemini"
        assert "Mock Gemini response" in data["response"]

    @pytest.mark.asyncio
    async def test_chat_completion_with_model(self, client):
        """POST /v1/chat/completions - Specify model"""
        response = await client.post(
            "/v1/chat/completions",
            json={
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ],
                "provider": "claude",
                "model": "claude-opus-4-5-20251101"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "claude-opus-4-5-20251101"

    @pytest.mark.asyncio
    async def test_chat_completion_with_model_alias(self, client):
        """POST /v1/chat/completions - Use model alias"""
        response = await client.post(
            "/v1/chat/completions",
            json={
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ],
                "provider": "claude",
                "model": "haiku"  # alias
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "claude-haiku-4-5-20251001"

    @pytest.mark.asyncio
    async def test_chat_completion_with_system_message(self, client):
        """POST /v1/chat/completions - With system message"""
        response = await client.post(
            "/v1/chat/completions",
            json={
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello!"}
                ],
                "provider": "claude"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data

    @pytest.mark.asyncio
    async def test_chat_completion_with_conversation(self, client):
        """POST /v1/chat/completions - Multi-turn conversation"""
        response = await client.post(
            "/v1/chat/completions",
            json={
                "messages": [
                    {"role": "user", "content": "My name is Alice."},
                    {"role": "assistant", "content": "Nice to meet you, Alice!"},
                    {"role": "user", "content": "What is my name?"}
                ],
                "provider": "claude"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data

    @pytest.mark.asyncio
    async def test_chat_completion_with_session(self, client):
        """POST /v1/chat/completions - With session ID"""
        # First create a session
        session_response = await client.post(
            "/v1/sessions",
            json={"provider": "claude"}
        )
        session_id = session_response.json()["session_id"]

        # Chat with session
        response = await client.post(
            "/v1/chat/completions",
            headers={"X-Session-ID": session_id},
            json={
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["provider"] == "claude"

    @pytest.mark.asyncio
    async def test_chat_completion_session_provider_mismatch(self, client):
        """POST /v1/chat/completions - Provider mismatch with session"""
        # Create Claude session
        session_response = await client.post(
            "/v1/sessions",
            json={"provider": "claude"}
        )
        session_id = session_response.json()["session_id"]

        # Try to chat with Gemini
        response = await client.post(
            "/v1/chat/completions",
            headers={"X-Session-ID": session_id},
            json={
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ],
                "provider": "gemini"  # Mismatch!
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "PROVIDER_MISMATCH"

    @pytest.mark.asyncio
    async def test_chat_completion_session_model_change(self, client):
        """POST /v1/chat/completions - Change model within same provider"""
        # Create Claude session with sonnet
        session_response = await client.post(
            "/v1/sessions",
            json={"provider": "claude", "model": "claude-sonnet-4-5-20250929"}
        )
        session_id = session_response.json()["session_id"]

        # Chat with different model (haiku)
        response = await client.post(
            "/v1/chat/completions",
            headers={"X-Session-ID": session_id},
            json={
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ],
                "model": "claude-haiku-4-5-20251001"  # Different model, same provider
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "claude-haiku-4-5-20251001"

    @pytest.mark.asyncio
    async def test_chat_completion_invalid_model(self, client):
        """POST /v1/chat/completions - Invalid model"""
        response = await client.post(
            "/v1/chat/completions",
            json={
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ],
                "provider": "claude",
                "model": "gpt-4"  # Invalid for Claude
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "INVALID_MODEL"

    @pytest.mark.asyncio
    async def test_chat_completion_no_user_message(self, client):
        """POST /v1/chat/completions - No user message"""
        response = await client.post(
            "/v1/chat/completions",
            json={
                "messages": [
                    {"role": "system", "content": "You are helpful."}
                ],
                "provider": "claude"
            }
        )

        # Should fail - no user message
        assert response.status_code == 400 or response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_completion_empty_messages(self, client):
        """POST /v1/chat/completions - Empty messages"""
        response = await client.post(
            "/v1/chat/completions",
            json={
                "messages": [],
                "provider": "claude"
            }
        )

        # Should fail - empty messages
        assert response.status_code == 400 or response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_completion_default_provider(self, client):
        """POST /v1/chat/completions - Default provider"""
        response = await client.post(
            "/v1/chat/completions",
            json={
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ]
                # No provider specified - should default to claude
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "claude"

    @pytest.mark.asyncio
    async def test_chat_completion_with_timeout(self, client):
        """POST /v1/chat/completions - Custom timeout"""
        response = await client.post(
            "/v1/chat/completions",
            json={
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ],
                "provider": "claude",
                "timeout": 60.0
            }
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_chat_completion_streaming(self, client):
        """POST /v1/chat/completions - Streaming response"""
        response = await client.post(
            "/v1/chat/completions",
            json={
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ],
                "provider": "claude",
                "stream": True
            }
        )

        assert response.status_code == 200
        assert response.headers.get("content-type") == "text/event-stream; charset=utf-8"

        # Read SSE events
        content = response.text
        assert "event: message" in content or "event: done" in content

    @pytest.mark.asyncio
    async def test_chat_session_stores_messages(self, client):
        """POST /v1/chat/completions - Verify session stores messages"""
        # Create session
        session_response = await client.post(
            "/v1/sessions",
            json={"provider": "claude"}
        )
        session_id = session_response.json()["session_id"]

        # First message
        await client.post(
            "/v1/chat/completions",
            headers={"X-Session-ID": session_id},
            json={
                "messages": [{"role": "user", "content": "First message"}]
            }
        )

        # Second message
        await client.post(
            "/v1/chat/completions",
            headers={"X-Session-ID": session_id},
            json={
                "messages": [{"role": "user", "content": "Second message"}]
            }
        )

        # Get session memory to verify messages are stored
        memory_response = await client.get(
            f"/v1/sessions/{session_id}/memory",
            params={"compression": "none"}
        )

        assert memory_response.status_code == 200
        data = memory_response.json()
        # Memory should contain conversation
        assert "content" in data or "compressed_memory" in data
