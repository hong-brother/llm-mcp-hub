"""Claude CLI adapter using claude-code"""
import asyncio
import json
import logging
import os
import subprocess
from typing import AsyncIterator

from llm_mcp_hub.core.exceptions import (
    InvalidModelError,
    ProviderError,
    ProviderTimeoutError,
)
from .base import ProviderAdapter

logger = logging.getLogger(__name__)


class ClaudeAdapter(ProviderAdapter):
    """Claude CLI adapter using claude-code CLI with --output-format json"""

    # Hardcoded model list (CLI doesn't support --list-models)
    SUPPORTED_MODELS = [
        "claude-sonnet-4-5-20250929",
        "claude-opus-4-5-20251101",
        "claude-haiku-4-5-20251001",
    ]

    # Model aliases
    MODEL_ALIASES = {
        "sonnet": "claude-sonnet-4-5-20250929",
        "opus": "claude-opus-4-5-20251101",
        "haiku": "claude-haiku-4-5-20251001",
    }

    def __init__(self, oauth_token: str | None = None, default_model: str | None = None):
        self._oauth_token = oauth_token
        self._default_model = default_model or self.SUPPORTED_MODELS[0]
        self._supported_models: list[str] = []
        self._initialized = False

    @property
    def name(self) -> str:
        return "claude"

    @property
    def supported_models(self) -> list[str]:
        return self._supported_models

    @property
    def default_model(self) -> str:
        return self._default_model

    async def initialize(self) -> None:
        """Initialize provider with hardcoded model list"""
        self._supported_models = self.SUPPORTED_MODELS.copy()

        if self._default_model not in self._supported_models:
            self._default_model = self._supported_models[0]

        self._initialized = True
        logger.info(f"Claude initialized with models: {self._supported_models}")

    def resolve_model(self, model: str | None) -> str:
        """Resolve model name including aliases"""
        if model is None:
            return self._default_model

        # Check alias
        if model in self.MODEL_ALIASES:
            return self.MODEL_ALIASES[model]

        return model

    def _get_env(self) -> dict[str, str]:
        """Get environment variables for subprocess"""
        env = os.environ.copy()
        if self._oauth_token:
            env["CLAUDE_CODE_OAUTH_TOKEN"] = self._oauth_token
        return env

    async def chat(
        self,
        prompt: str,
        model: str | None = None,
        system_prompt: str | None = None,
        conversation: list[dict[str, str]] | None = None,
        timeout: float = 120.0,
    ) -> str:
        """Send chat request using claude-code CLI"""
        effective_model = self.resolve_model(model)

        if effective_model not in self._supported_models:
            raise InvalidModelError(
                effective_model,
                provider="claude",
                supported_models=self._supported_models,
            )

        # Build command
        cmd = ["claude", "-p", prompt, "--output-format", "json", "--model", effective_model]

        # Add system prompt if provided
        if system_prompt:
            cmd.extend(["--system-prompt", system_prompt])

        logger.debug(f"Executing Claude CLI: {' '.join(cmd[:6])}...")

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    capture_output=True,
                    text=True,
                    env=self._get_env(),
                    cwd="/tmp",  # Avoid reading CLAUDE.md from project directory
                ),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            raise ProviderTimeoutError("claude", timeout)

        if result.returncode != 0:
            logger.error(f"Claude CLI error: {result.stderr}")
            raise ProviderError(f"claude-code failed: {result.stderr}", provider="claude")

        try:
            response = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response: {result.stdout}")
            raise ProviderError(f"Invalid JSON response: {e}", provider="claude")

        # Handle error response
        if response.get("is_error"):
            raise ProviderError(
                f"Claude error: {response.get('result', 'Unknown error')}",
                provider="claude",
            )

        return response.get("result", "")

    async def chat_stream(
        self,
        prompt: str,
        model: str | None = None,
        system_prompt: str | None = None,
        conversation: list[dict[str, str]] | None = None,
    ) -> AsyncIterator[str]:
        """Stream chat response using claude-code CLI with --output-format stream-json"""
        effective_model = self.resolve_model(model)

        if effective_model not in self._supported_models:
            raise InvalidModelError(
                effective_model,
                provider="claude",
                supported_models=self._supported_models,
            )

        # Build command (--verbose is required for stream-json)
        cmd = [
            "claude",
            "-p",
            prompt,
            "--output-format",
            "stream-json",
            "--verbose",
            "--model",
            effective_model,
        ]

        if system_prompt:
            cmd.extend(["--system-prompt", system_prompt])

        logger.debug(f"Executing Claude CLI (stream): {' '.join(cmd[:6])}...")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._get_env(),
            cwd="/tmp",  # Avoid reading CLAUDE.md from project directory
        )

        async for line in proc.stdout:  # type: ignore
            if line:
                try:
                    data = json.loads(line.decode())
                    # Extract text from assistant message
                    if data.get("type") == "assistant":
                        message = data.get("message", {})
                        for content in message.get("content", []):
                            if content.get("type") == "text":
                                text = content.get("text", "")
                                if text:
                                    yield text
                except json.JSONDecodeError:
                    continue

        await proc.wait()

        if proc.returncode != 0:
            stderr = await proc.stderr.read() if proc.stderr else b""  # type: ignore
            logger.error(f"Claude CLI stream error: {stderr.decode()}")

    async def health_check(self) -> dict:
        """Check Claude provider health"""
        try:
            # Simple health check - try to run claude with minimal args
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    subprocess.run,
                    ["claude", "--version"],
                    capture_output=True,
                    text=True,
                    env=self._get_env(),
                ),
                timeout=10.0,
            )

            if result.returncode == 0:
                return {
                    "status": "healthy",
                    "supported_models": self._supported_models,
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": result.stderr,
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }
