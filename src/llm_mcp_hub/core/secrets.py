"""Hierarchical secret provider for LLM MCP Hub"""
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class SecretProvider(ABC):
    """Abstract base class for secret providers"""

    @abstractmethod
    def get(self, key: str) -> str | None:
        """Get secret value by key"""
        pass


class EnvSecretProvider(SecretProvider):
    """Load secrets from environment variables"""

    def get(self, key: str) -> str | None:
        return os.environ.get(key)


class FileSecretProvider(SecretProvider):
    """Load secrets from files (Docker Secrets compatible)"""

    def __init__(self, base_path: str = "/run/secrets"):
        self.base_path = Path(base_path)

    def get(self, key: str) -> str | Any | None:
        # Check if file path is specified via environment variable
        file_path_env = os.environ.get(f"{key}_FILE")
        if file_path_env:
            path = Path(file_path_env)
        else:
            # Default: /run/secrets/<key_lowercase>
            path = self.base_path / key.lower()

        if path.exists():
            content = path.read_text().strip()
            # Parse JSON if file has .json extension
            if path.suffix == ".json":
                return json.loads(content)
            return content
        return None


class ChainedSecretProvider(SecretProvider):
    """Chain multiple secret providers, try in order"""

    def __init__(self, providers: list[SecretProvider]):
        self.providers = providers

    def get(self, key: str) -> str | Any | None:
        for provider in self.providers:
            value = provider.get(key)
            if value is not None:
                return value
        return None


def create_secret_provider() -> SecretProvider:
    """Create appropriate secret provider based on environment"""
    providers: list[SecretProvider] = []

    # Priority 1: Docker Secrets
    if Path("/run/secrets").exists():
        providers.append(FileSecretProvider("/run/secrets"))

    # Priority 2: Custom secrets path
    secrets_path = os.environ.get("SECRETS_PATH")
    if secrets_path and Path(secrets_path).exists():
        providers.append(FileSecretProvider(secrets_path))

    # Priority 3: Environment variables (fallback)
    providers.append(EnvSecretProvider())

    return ChainedSecretProvider(providers)
