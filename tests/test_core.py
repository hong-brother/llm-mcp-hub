"""Tests for core module"""
import pytest
from llm_mcp_hub.core.config import Settings
from llm_mcp_hub.core.exceptions import (
    LLMHubError,
    ProviderError,
    ProviderTimeoutError,
    InvalidModelError,
    SessionNotFoundError,
    ProviderMismatchError,
)
from llm_mcp_hub.core.secrets import EnvSecretProvider, ChainedSecretProvider


class TestExceptions:
    def test_llm_hub_error(self):
        error = LLMHubError("Test error", code="TEST_ERROR", details={"key": "value"})
        assert error.message == "Test error"
        assert error.code == "TEST_ERROR"
        assert error.details == {"key": "value"}

        error_dict = error.to_dict()
        assert error_dict["error"]["code"] == "TEST_ERROR"
        assert error_dict["error"]["message"] == "Test error"

    def test_provider_error(self):
        error = ProviderError("Provider failed", provider="claude")
        assert error.code == "PROVIDER_ERROR"
        assert error.details["provider"] == "claude"

    def test_provider_timeout_error(self):
        error = ProviderTimeoutError("claude", 120.0)
        assert error.code == "PROVIDER_TIMEOUT"
        assert "120" in error.message

    def test_invalid_model_error(self):
        error = InvalidModelError("gpt-4", provider="claude", supported_models=["sonnet"])
        assert error.code == "INVALID_MODEL"
        assert error.details["requested_model"] == "gpt-4"

    def test_session_not_found_error(self):
        error = SessionNotFoundError("sess_123")
        assert error.code == "SESSION_NOT_FOUND"
        assert "sess_123" in error.message

    def test_provider_mismatch_error(self):
        error = ProviderMismatchError("gemini", "claude")
        assert error.code == "PROVIDER_MISMATCH"
        assert error.details["session_provider"] == "gemini"
        assert error.details["requested_provider"] == "claude"


class TestSecrets:
    def test_env_secret_provider(self, monkeypatch):
        monkeypatch.setenv("TEST_SECRET", "test_value")
        provider = EnvSecretProvider()
        assert provider.get("TEST_SECRET") == "test_value"
        assert provider.get("NONEXISTENT") is None

    def test_chained_secret_provider(self, monkeypatch):
        monkeypatch.setenv("CHAIN_TEST", "from_env")

        provider1 = EnvSecretProvider()
        provider2 = EnvSecretProvider()

        chained = ChainedSecretProvider([provider1, provider2])
        assert chained.get("CHAIN_TEST") == "from_env"


class TestConfig:
    def test_default_settings(self, monkeypatch):
        # Clear any existing env vars
        monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
        monkeypatch.delenv("GEMINI_AUTH_PATH", raising=False)

        settings = Settings()
        assert settings.app_name == "LLM MCP Hub"
        assert settings.session_ttl == 3600
        assert settings.claude_default_model == "claude-sonnet-4-5-20250929"
        assert settings.gemini_default_model == "gemini-2.5-pro"

    def test_settings_from_env(self, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("SESSION_TTL", "7200")

        settings = Settings()
        assert settings.log_level == "DEBUG"
        assert settings.session_ttl == 7200
