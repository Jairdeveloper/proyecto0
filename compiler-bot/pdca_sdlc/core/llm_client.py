"""LLMClient — generic LLM client with fallback, retry, and timeout.

In Fase 1 the client operates in mock mode (no external API calls).
Future phases will add OpenRouter and LiteLLM backends.
"""

from __future__ import annotations

import json
import logging
import random
import time
from typing import Any

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base exception for LLM client errors."""


class LLMClient:
    """Generic LLM client with configurable backends and fallback chain.

    Args:
        config: Dict with profile config (model, temperature, max_tokens).
                Falls back to defaults if not provided.

    Usage::

        client = LLMClient({"model": "mock", "temperature": 0.3})
        response = client.complete("Hola", max_tokens=512)
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = config or {}
        self._model: str = self._config.get("model", "mock")
        self._temperature: float = float(self._config.get("temperature", 0.3))
        self._max_tokens: int = int(self._config.get("max_tokens", 4096))
        self._timeout: int = int(self._config.get("timeout", 30))
        self._max_retries: int = int(self._config.get("max_retries", 3))

    def complete(
        self,
        prompt: str,
        max_tokens: int | None = None,
        response_format: str | None = None,
    ) -> str:
        """Send a prompt to the LLM and return the text response.

        Args:
            prompt: Input text.
            max_tokens: Max tokens in response (overrides config default).
            response_format: Optional format hint ("json", "text").

        Returns:
            Response text.

        Raises:
            LLMError: If all backends fail after retries.
        """
        effective_max = max_tokens or self._max_tokens
        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                return self._try_backend(prompt, effective_max, response_format)
            except LLMError as e:
                last_error = e
                if attempt < self._max_retries:
                    delay = 2**attempt + random.uniform(0, 1)
                    logger.debug("LLM retry %d after %0.2fs: %s", attempt + 1, delay, e)
                    time.sleep(delay)
        if last_error is not None:
            raise last_error
        raise LLMError("No backend available")

    def _try_backend(
        self,
        prompt: str,
        max_tokens: int,
        response_format: str | None,
    ) -> str:
        """Try the current backend. Raises LLMError on failure."""
        if self._model == "mock":
            return self._mock_complete(prompt, max_tokens, response_format)
        if self._model == "flash" or self._model == "pro":
            return self._mock_complete(prompt, max_tokens, response_format)
        msg = f"Unknown model backend: {self._model}"
        raise LLMError(msg)

    def _mock_complete(
        self,
        prompt: str,
        max_tokens: int,
        response_format: str | None,
    ) -> str:
        """Mock backend for testing — returns structured JSON or echo."""
        if response_format == "json":
            return json.dumps({"response": prompt[:max_tokens]})
        return f"Mock response to: {prompt[:max_tokens]}"

    @property
    def model(self) -> str:
        return self._model

    @property
    def temperature(self) -> float:
        return self._temperature

    @property
    def config(self) -> dict[str, Any]:
        return {
            "model": self._model,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "timeout": self._timeout,
            "max_retries": self._max_retries,
        }
