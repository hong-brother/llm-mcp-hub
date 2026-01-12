"""Gemini CLI adapter using PTY wrapper"""
import asyncio
import logging
import os
import re
from pathlib import Path
from typing import AsyncIterator

from llm_mcp_hub.core.exceptions import (
    InvalidModelError,
    ProviderError,
    ProviderTimeoutError,
)
from .base import ProviderAdapter

logger = logging.getLogger(__name__)


class GeminiAdapter(ProviderAdapter):
    """Gemini CLI adapter using PTY wrapper for TTY requirement"""

    # ANSI escape code pattern
    ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    # Hardcoded model list (CLI parsing is unstable)
    SUPPORTED_MODELS = [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ]

    def __init__(self, auth_path: str | None = None, default_model: str | None = None):
        self._auth_path = auth_path
        self._default_model = default_model or self.SUPPORTED_MODELS[0]
        self._supported_models: list[str] = []
        self._initialized = False

    @property
    def name(self) -> str:
        return "gemini"

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
        logger.info(f"Gemini initialized with models: {self._supported_models}")

    def _get_env(self) -> dict[str, str]:
        """Get environment variables for PTY process"""
        env = os.environ.copy()
        # Set HOME for OAuth credentials lookup
        if self._auth_path:
            # Set parent directory of auth file as HOME for gemini CLI
            auth_dir = Path(self._auth_path).parent.parent
            env["HOME"] = str(auth_dir)
        env["TERM"] = "dumb"  # Minimize ANSI codes
        return env

    def _clean_ansi(self, text: str) -> str:
        """Remove ANSI escape codes from text"""
        return self.ANSI_ESCAPE.sub("", text)

    def _sync_chat(self, prompt: str, model: str, timeout: float) -> str:
        """Synchronous PTY chat execution"""
        from ptyprocess import PtyProcess
        import time

        cmd = ["gemini", "-p", prompt, "-m", model]

        proc = PtyProcess.spawn(
            cmd,
            env=self._get_env(),
            dimensions=(24, 200),  # Terminal size
        )

        output = []
        start_time = time.time()

        while proc.isalive():
            if time.time() - start_time > timeout:
                proc.terminate(force=True)
                raise TimeoutError(f"Gemini response timeout ({timeout}s)")

            try:
                chunk = proc.read(1024)
                if chunk:
                    output.append(chunk.decode("utf-8", errors="ignore"))
            except EOFError:
                break
            except Exception:
                break

        proc.close()

        raw_output = "".join(output)
        return self._parse_response(raw_output)

    def _parse_response(self, raw: str) -> str:
        """Parse and clean Gemini CLI response"""
        clean = self._clean_ansi(raw)
        # Additional parsing may be needed based on CLI output format
        return clean.strip()

    async def chat(
        self,
        prompt: str,
        model: str | None = None,
        system_prompt: str | None = None,
        conversation: list[dict[str, str]] | None = None,
        timeout: float = 120.0,
    ) -> str:
        """Send chat request using Gemini CLI via PTY"""
        effective_model = model or self._default_model

        if effective_model not in self._supported_models:
            raise InvalidModelError(
                effective_model,
                provider="gemini",
                supported_models=self._supported_models,
            )

        # Prepend system prompt to user prompt if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        logger.debug(f"Executing Gemini CLI: gemini -p '...' -m {effective_model}")

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(self._sync_chat, full_prompt, effective_model, timeout),
                timeout=timeout + 5,  # Extra buffer for thread overhead
            )
            return result
        except TimeoutError:
            raise ProviderTimeoutError("gemini", timeout)
        except asyncio.TimeoutError:
            raise ProviderTimeoutError("gemini", timeout)
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            raise ProviderError(f"Gemini CLI failed: {e}", provider="gemini")

    async def chat_stream(
        self,
        prompt: str,
        model: str | None = None,
        system_prompt: str | None = None,
        conversation: list[dict[str, str]] | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream chat response.

        Note: Gemini CLI doesn't support native streaming, so we simulate
        by yielding chunks from the PTY output.
        """
        effective_model = model or self._default_model

        if effective_model not in self._supported_models:
            raise InvalidModelError(
                effective_model,
                provider="gemini",
                supported_models=self._supported_models,
            )

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # For streaming, we need to read from PTY in real-time
        from ptyprocess import PtyProcess

        cmd = ["gemini", "-p", full_prompt, "-m", effective_model]

        def _create_process():
            return PtyProcess.spawn(
                cmd,
                env=self._get_env(),
                dimensions=(24, 200),
            )

        proc = await asyncio.to_thread(_create_process)

        try:
            while True:
                try:
                    chunk = await asyncio.to_thread(proc.read, 256)
                    if chunk:
                        clean_chunk = self._clean_ansi(chunk.decode("utf-8", errors="ignore"))
                        if clean_chunk:
                            yield clean_chunk
                    if not proc.isalive():
                        break
                except EOFError:
                    break
                except Exception:
                    break
        finally:
            await asyncio.to_thread(proc.close)

    async def health_check(self) -> dict:
        """Check Gemini provider health"""
        try:
            import shutil

            # Check if gemini CLI is installed
            gemini_path = shutil.which("gemini")
            if not gemini_path:
                return {
                    "status": "unhealthy",
                    "error": "Gemini CLI not found",
                }

            # Check OAuth credentials
            if self._auth_path:
                if not Path(self._auth_path).exists():
                    return {
                        "status": "unhealthy",
                        "error": f"OAuth credentials not found: {self._auth_path}",
                    }
            else:
                # Check default path
                default_path = Path.home() / ".gemini" / "oauth_creds.json"
                if not default_path.exists():
                    return {
                        "status": "unhealthy",
                        "error": "OAuth credentials not found at default path",
                    }

            return {
                "status": "healthy",
                "supported_models": self._supported_models,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }
