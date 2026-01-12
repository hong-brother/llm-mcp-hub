"""Tests for Provider API endpoints"""
import pytest


class TestProviderEndpoints:
    """Test /v1/providers endpoints"""

    @pytest.mark.asyncio
    async def test_list_providers(self, client):
        """GET /v1/providers - List all providers"""
        response = await client.get("/v1/providers")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2  # claude and gemini

        # Check provider structure
        provider_names = [p["name"] for p in data]
        assert "claude" in provider_names
        assert "gemini" in provider_names

        # Each provider should have required fields
        for provider in data:
            assert "name" in provider
            assert "models" in provider
            assert "default_model" in provider
            assert isinstance(provider["models"], list)
            assert len(provider["models"]) > 0

    @pytest.mark.asyncio
    async def test_get_claude_provider(self, client):
        """GET /v1/providers/claude - Get Claude provider details"""
        response = await client.get("/v1/providers/claude")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "claude"
        assert data["status"] == "healthy"
        assert "models" in data
        assert "default_model" in data

        # Check Claude models
        assert "claude-sonnet-4-5-20250929" in data["models"]
        assert "claude-opus-4-5-20251101" in data["models"]
        assert "claude-haiku-4-5-20251001" in data["models"]

    @pytest.mark.asyncio
    async def test_get_gemini_provider(self, client):
        """GET /v1/providers/gemini - Get Gemini provider details"""
        response = await client.get("/v1/providers/gemini")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "gemini"
        assert data["status"] == "healthy"
        assert "models" in data
        assert "default_model" in data

        # Check Gemini models
        assert "gemini-2.5-pro" in data["models"]
        assert "gemini-2.5-flash" in data["models"]
        assert "gemini-2.0-flash" in data["models"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_provider(self, client):
        """GET /v1/providers/unknown - Provider not found"""
        response = await client.get("/v1/providers/unknown")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "PROVIDER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_claude_models(self, client):
        """GET /v1/providers/claude/models - Get Claude model list"""
        response = await client.get("/v1/providers/claude/models")

        assert response.status_code == 200
        models = response.json()
        assert isinstance(models, list)
        assert len(models) == 3
        assert "claude-sonnet-4-5-20250929" in models
        assert "claude-opus-4-5-20251101" in models
        assert "claude-haiku-4-5-20251001" in models

    @pytest.mark.asyncio
    async def test_get_gemini_models(self, client):
        """GET /v1/providers/gemini/models - Get Gemini model list"""
        response = await client.get("/v1/providers/gemini/models")

        assert response.status_code == 200
        models = response.json()
        assert isinstance(models, list)
        assert len(models) == 3
        assert "gemini-2.5-pro" in models
        assert "gemini-2.5-flash" in models
        assert "gemini-2.0-flash" in models

    @pytest.mark.asyncio
    async def test_get_models_nonexistent_provider(self, client):
        """GET /v1/providers/unknown/models - Provider not found"""
        response = await client.get("/v1/providers/unknown/models")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "PROVIDER_NOT_FOUND"
