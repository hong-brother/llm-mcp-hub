"""Tests for Health API endpoints"""
import pytest


class TestHealthEndpoints:
    """Test /health endpoints"""

    @pytest.mark.asyncio
    async def test_basic_health_check(self, client):
        """GET /health - Basic health check"""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_detailed_health_check(self, client):
        """GET /health/detailed - Detailed health with components"""
        response = await client.get("/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "version" in data
        assert "components" in data

        # Check provider components
        components = data["components"]
        assert "claude" in components
        assert "gemini" in components

        # Each component should have status
        for name, component in components.items():
            assert "status" in component

    @pytest.mark.asyncio
    async def test_token_health_check(self, client):
        """GET /health/tokens - Token status check"""
        response = await client.get("/health/tokens")

        assert response.status_code == 200
        data = response.json()

        # Should have claude and gemini token status
        assert "claude" in data or "gemini" in data

        # Each provider should have valid field
        for provider, status in data.items():
            if status:
                assert "valid" in status
