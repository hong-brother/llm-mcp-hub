"""Tests for Session API endpoints"""
import pytest


class TestSessionEndpoints:
    """Test /v1/sessions endpoints"""

    @pytest.mark.asyncio
    async def test_create_session_claude(self, client):
        """POST /v1/sessions - Create Claude session"""
        response = await client.post(
            "/v1/sessions",
            json={
                "provider": "claude",
                "model": "claude-sonnet-4-5-20250929",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["provider"] == "claude"
        assert data["model"] == "claude-sonnet-4-5-20250929"
        assert data["status"] == "active"
        assert "supported_models" in data
        assert "created_at" in data
        assert "expires_at" in data

    @pytest.mark.asyncio
    async def test_create_session_gemini(self, client):
        """POST /v1/sessions - Create Gemini session"""
        response = await client.post(
            "/v1/sessions",
            json={
                "provider": "gemini",
                "model": "gemini-2.5-pro",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "gemini"
        assert data["model"] == "gemini-2.5-pro"

    @pytest.mark.asyncio
    async def test_create_session_with_default_model(self, client):
        """POST /v1/sessions - Create session with default model"""
        response = await client.post(
            "/v1/sessions",
            json={"provider": "claude"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "claude"
        assert data["model"] == "claude-sonnet-4-5-20250929"  # default

    @pytest.mark.asyncio
    async def test_create_session_with_alias(self, client):
        """POST /v1/sessions - Create session with model alias"""
        response = await client.post(
            "/v1/sessions",
            json={
                "provider": "claude",
                "model": "sonnet",  # alias
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "claude-sonnet-4-5-20250929"

    @pytest.mark.asyncio
    async def test_create_session_with_context(self, client):
        """POST /v1/sessions - Create session with context injection"""
        response = await client.post(
            "/v1/sessions",
            json={
                "provider": "claude",
                "system_prompt": "You are a Python expert.",
                "context": {
                    "memory": "# Project Rules\n- Use type hints",
                    "previous_summary": "Previous session discussed FastAPI.",
                    "files": [{"name": "main.py", "content": "print('hello')"}]
                },
                "ttl": 7200,
                "metadata": {"project": "test"}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "claude"

    @pytest.mark.asyncio
    async def test_create_session_invalid_provider(self, client):
        """POST /v1/sessions - Invalid provider"""
        response = await client.post(
            "/v1/sessions",
            json={"provider": "openai"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data["detail"] or "message" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_session_invalid_model(self, client):
        """POST /v1/sessions - Invalid model"""
        response = await client.post(
            "/v1/sessions",
            json={
                "provider": "claude",
                "model": "gpt-4"  # Invalid for Claude
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "INVALID_MODEL"

    @pytest.mark.asyncio
    async def test_get_session(self, client):
        """GET /v1/sessions/{session_id} - Get session info"""
        # First create a session
        create_response = await client.post(
            "/v1/sessions",
            json={"provider": "claude"}
        )
        session_id = create_response.json()["session_id"]

        # Get session
        response = await client.get(f"/v1/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["provider"] == "claude"
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, client):
        """GET /v1/sessions/{session_id} - Session not found"""
        response = await client.get("/v1/sessions/nonexistent-id")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "SESSION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_delete_session(self, client):
        """DELETE /v1/sessions/{session_id} - Delete session"""
        # First create a session
        create_response = await client.post(
            "/v1/sessions",
            json={"provider": "claude"}
        )
        session_id = create_response.json()["session_id"]

        # Delete session
        response = await client.delete(f"/v1/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["session_id"] == session_id

        # Verify session is deleted
        get_response = await client.get(f"/v1/sessions/{session_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self, client):
        """DELETE /v1/sessions/{session_id} - Session not found"""
        response = await client.delete("/v1/sessions/nonexistent-id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_close_session(self, client):
        """POST /v1/sessions/{session_id}/close - Close session with memory"""
        # First create a session
        create_response = await client.post(
            "/v1/sessions",
            json={"provider": "claude"}
        )
        session_id = create_response.json()["session_id"]

        # Close session
        response = await client.post(
            f"/v1/sessions/{session_id}/close",
            json={
                "compression": "none",
                "provider": "claude"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["session_id"] == session_id
        assert data["status"] == "closed"
        assert "compressed_memory" in data

    @pytest.mark.asyncio
    async def test_close_session_with_compression(self, client):
        """POST /v1/sessions/{session_id}/close - Close with compression"""
        # Create session
        create_response = await client.post(
            "/v1/sessions",
            json={"provider": "claude"}
        )
        session_id = create_response.json()["session_id"]

        # Close with different compression levels
        for compression in ["none", "low", "medium", "high"]:
            # Create new session for each test
            create_response = await client.post(
                "/v1/sessions",
                json={"provider": "claude"}
            )
            session_id = create_response.json()["session_id"]

            response = await client.post(
                f"/v1/sessions/{session_id}/close",
                json={"compression": compression}
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_session_memory(self, client):
        """GET /v1/sessions/{session_id}/memory - Export session memory"""
        # Create session
        create_response = await client.post(
            "/v1/sessions",
            json={"provider": "claude"}
        )
        session_id = create_response.json()["session_id"]

        # Get memory
        response = await client.get(f"/v1/sessions/{session_id}/memory")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["compression"] == "medium"  # default
        assert data["format"] == "markdown"  # default
        assert "metadata" in data

    @pytest.mark.asyncio
    async def test_get_session_memory_with_params(self, client):
        """GET /v1/sessions/{session_id}/memory - With query params"""
        # Create session
        create_response = await client.post(
            "/v1/sessions",
            json={"provider": "claude"}
        )
        session_id = create_response.json()["session_id"]

        # Get memory with params
        response = await client.get(
            f"/v1/sessions/{session_id}/memory",
            params={
                "compression": "none",
                "format": "json",
                "provider": "claude"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["compression"] == "none"
        assert data["format"] == "json"

    @pytest.mark.asyncio
    async def test_get_memory_nonexistent_session(self, client):
        """GET /v1/sessions/{session_id}/memory - Session not found"""
        response = await client.get("/v1/sessions/nonexistent-id/memory")

        assert response.status_code == 404
