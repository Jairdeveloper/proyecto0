"""LLMBackend abstraction with OpenAI, Ollama, vLLM, and failover support."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from agentic_pipeline.circuit_breaker import CircuitBreakerOpenError

if TYPE_CHECKING:
    from agentic_pipeline.circuit_breaker import CircuitBreaker, ExponentialBackoff
    from agentic_pipeline.prompt_chain.llm_cache import LLMCache
    from agentic_pipeline.security.token_bucket import TokenBucket

logger = logging.getLogger(__name__)


class LLMResult(BaseModel):
    """Resultado de una llamada al LLM."""

    content: str = ""
    structured: dict | None = None
    provider: str = ""
    model: str = ""
    duration: float = 0.0
    success: bool = False
    error: str | None = None


class LLMBackend(ABC):
    """Abstraccion sobre proveedores de LLM."""

    def __init__(self) -> None:
        self._cache: LLMCache | None = None
        self._circuit_breaker: CircuitBreaker | None = None
        self._backoff: ExponentialBackoff | None = None
        self._rate_limiter: TokenBucket | None = None

    def set_cache(self, cache: LLMCache | None) -> None:
        """Inyecta cache de respuestas LLM."""
        self._cache = cache

    def set_circuit_breaker(
        self,
        cb: CircuitBreaker | None = None,
        backoff: ExponentialBackoff | None = None,
    ) -> None:
        """Inyecta circuit breaker + exponential backoff para resiliencia."""
        self._circuit_breaker = cb
        self._backoff = backoff

    def set_rate_limiter(self, limiter: TokenBucket | None) -> None:
        """Inyecta TokenBucket rate limiter para control de tasa de API."""
        self._rate_limiter = limiter

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResult:
        """Genera texto libre."""

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        system: str = "",
        output_schema: type[BaseModel] | None = None,
        temperature: float = 0.3,
    ) -> LLMResult:
        """Genera output estructurado validado contra schema."""


class OpenAIBackend(LLMBackend):
    """OpenAI backend via langchain-openai ChatOpenAI.

    Config via env vars:
        AGENTIC_OPENAI_API_KEY (str)
        AGENTIC_OPENAI_MODEL (str) — defecto: gpt-4o-mini
        AGENTIC_OPENAI_BASE_URL (str) — opcional (Azure/compatibles)
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        super().__init__()
        self._api_key = api_key or os.getenv("AGENTIC_OPENAI_API_KEY", "")
        self._model = model or os.getenv("AGENTIC_OPENAI_MODEL", "gpt-4o-mini")
        self._base_url = base_url or os.getenv("AGENTIC_OPENAI_BASE_URL")
        self._llm: Any = None

    async def _call_with_retry(
        self,
        fn: Any,
        max_retries: int = 3,
    ) -> Any:
        """Execute fn with circuit breaker, rate limiter, and exponential backoff retry."""
        last_exc: Exception | None = None
        for attempt in range(max_retries):
            try:
                if self._rate_limiter is not None:
                    while not self._rate_limiter.consume():
                        await asyncio.sleep(0.1)
                if self._circuit_breaker is not None:
                    return await self._circuit_breaker.call_async(fn)
                return await fn()
            except CircuitBreakerOpenError:
                raise
            except Exception as e:
                last_exc = e
                if attempt < max_retries - 1:
                    if self._backoff is not None:
                        await asyncio.sleep(self._backoff.delay(attempt))
                    continue
                raise

        raise last_exc  # type: ignore[misc]

    def _ensure_llm(self) -> None:
        if self._llm is not None:
            return
        try:
            from langchain_openai import ChatOpenAI

            kwargs: dict[str, Any] = {
                "model": self._model,
                "api_key": self._api_key,
                "temperature": 0,
            }
            if self._base_url:
                kwargs["base_url"] = self._base_url
            self._llm = ChatOpenAI(**kwargs)
        except ImportError:
            msg = "langchain-openai not installed"
            raise ImportError(msg) from None
        except Exception as exc:
            logger.warning("OpenAI backend init failed: %s", exc)
            self._llm = object()  # non-None sentinel to avoid retry

    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResult:
        # Check cache first
        if self._cache is not None:
            cached = await self._cache.get(prompt, "")
            if cached is not None:
                logger.debug("LLM cache HIT for prompt: %.60s", prompt)
                return LLMResult(**cached)

        self._ensure_llm()
        if not hasattr(self._llm, "ainvoke"):
            return LLMResult(
                provider="openai",
                model=self._model,
                success=False,
                error="OpenAI backend unavailable (init failed)",
            )

        from langchain_core.messages import HumanMessage, SystemMessage

        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))

        t0 = time.time()
        try:
            response = await self._call_with_retry(lambda: self._llm.ainvoke(messages))
            duration = time.time() - t0
            result = LLMResult(
                content=response.content,
                provider="openai",
                model=self._model,
                duration=duration,
                success=True,
            )
            if self._cache is not None:
                await self._cache.set(prompt, "", result.model_dump())
            return result
        except CircuitBreakerOpenError:
            duration = time.time() - t0
            logger.warning("OpenAI generate rejected: circuit breaker OPEN")
            return LLMResult(
                provider="openai",
                model=self._model,
                duration=duration,
                success=False,
                error="Circuit breaker OPEN — LLM temporarily unavailable",
            )
        except Exception as exc:
            duration = time.time() - t0
            logger.warning("OpenAI generate failed: %s", exc)
            return LLMResult(
                provider="openai",
                model=self._model,
                duration=duration,
                success=False,
                error=str(exc),
            )

    async def generate_structured(
        self,
        prompt: str,
        system: str = "",
        output_schema: type[BaseModel] | None = None,
        temperature: float = 0.3,
    ) -> LLMResult:
        # Check cache first (schema-aware)
        schema_name = output_schema.__name__ if output_schema else ""
        if self._cache is not None:
            cached = await self._cache.get(prompt, schema_name)
            if cached is not None:
                logger.debug("LLM cache HIT for structured: %.60s", prompt)
                return LLMResult(**cached)

        self._ensure_llm()
        if not hasattr(self._llm, "ainvoke"):
            return LLMResult(
                provider="openai",
                model=self._model,
                success=False,
                error="OpenAI backend unavailable (init failed)",
            )

        if output_schema is None:
            return await self.generate(prompt, system, temperature)

        from langchain_core.messages import HumanMessage, SystemMessage

        schema_instructions = (
            f"Responde SOLO con JSON valido que cumpla este schema:\n"
            f"{output_schema.model_json_schema()}"
        )
        full_system = f"{system}\n\n{schema_instructions}" if system else schema_instructions
        messages = [
            SystemMessage(content=full_system),
            HumanMessage(content=prompt),
        ]

        t0 = time.time()
        try:
            response = await self._call_with_retry(lambda: self._llm.ainvoke(messages))
            parsed = output_schema.model_validate_json(response.content)
            duration = time.time() - t0
            result = LLMResult(
                content=response.content,
                structured=parsed.model_dump(),
                provider="openai",
                model=self._model,
                duration=duration,
                success=True,
            )
            if self._cache is not None:
                await self._cache.set(prompt, schema_name, result.model_dump())
            return result
        except CircuitBreakerOpenError:
            duration = time.time() - t0
            logger.warning("OpenAI generate_structured rejected: circuit breaker OPEN")
            return LLMResult(
                provider="openai",
                model=self._model,
                duration=duration,
                success=False,
                error="Circuit breaker OPEN — LLM temporarily unavailable",
            )
        except Exception as exc:
            duration = time.time() - t0
            logger.warning("OpenAI generate_structured failed: %s", exc)
            return LLMResult(
                provider="openai",
                model=self._model,
                duration=duration,
                success=False,
                error=str(exc),
            )


class OllamaBackend(LLMBackend):
    """Ollama backend para modelos locales.

    Config via env vars:
        AGENTIC_OLLAMA_URL (str) — defecto: http://localhost:11434
        AGENTIC_OLLAMA_MODEL (str) — defecto: llama3
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        super().__init__()
        self._base_url = (
            base_url or os.getenv("AGENTIC_OLLAMA_URL", "http://localhost:11434")
        ).rstrip("/")
        self._model = model or os.getenv("AGENTIC_OLLAMA_MODEL", "llama3")

    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResult:
        t0 = time.time()
        try:
            import httpx

            payload: dict[str, Any] = {
                "model": self._model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }
            if system:
                payload["system"] = system

            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{self._base_url}/api/generate", json=payload)
                resp.raise_for_status()
                data = resp.json()

            duration = time.time() - t0
            return LLMResult(
                content=data.get("response", ""),
                provider="ollama",
                model=self._model,
                duration=duration,
                success=True,
            )
        except Exception as exc:
            duration = time.time() - t0
            logger.warning("Ollama generate failed: %s", exc)
            return LLMResult(
                provider="ollama",
                model=self._model,
                duration=duration,
                success=False,
                error=str(exc),
            )

    async def generate_structured(
        self,
        prompt: str,
        system: str = "",
        output_schema: type[BaseModel] | None = None,
        temperature: float = 0.3,
    ) -> LLMResult:
        if output_schema is None:
            return await self.generate(prompt, system, temperature)

        schema_instructions = (
            f"Responde SOLO con JSON valido que cumpla este schema:\n"
            f"{output_schema.model_json_schema()}"
        )
        full_system = f"{system}\n\n{schema_instructions}" if system else schema_instructions

        result = await self.generate(prompt, full_system, temperature)
        if not result.success:
            return result

        try:
            parsed = output_schema.model_validate_json(result.content)
            result.structured = parsed.model_dump()
            result.success = True
        except Exception as exc:
            result.success = False
            result.error = f"JSON parse failed: {exc}"

        return result


class VLLMBackend(LLMBackend):
    """vLLM backend (API compatible OpenAI).

    Config via env vars:
        AGENTIC_VLLM_URL (str)
        AGENTIC_VLLM_MODEL (str)
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        super().__init__()
        self._base_url = (
            base_url or os.getenv("AGENTIC_VLLM_URL", "http://localhost:8000")
        ).rstrip("/")
        self._model = model or os.getenv("AGENTIC_VLLM_MODEL", "")

    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResult:
        t0 = time.time()
        try:
            import httpx

            payload: dict[str, Any] = {
                "model": self._model,
                "messages": [],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if system:
                payload["messages"].append({"role": "system", "content": system})
            payload["messages"].append({"role": "user", "content": prompt})

            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{self._base_url}/v1/chat/completions", json=payload)
                resp.raise_for_status()
                data = resp.json()

            content = data["choices"][0]["message"]["content"]
            duration = time.time() - t0
            return LLMResult(
                content=content,
                provider="vllm",
                model=self._model,
                duration=duration,
                success=True,
            )
        except Exception as exc:
            duration = time.time() - t0
            logger.warning("vLLM generate failed: %s", exc)
            return LLMResult(
                provider="vllm",
                model=self._model,
                duration=duration,
                success=False,
                error=str(exc),
            )

    async def generate_structured(
        self,
        prompt: str,
        system: str = "",
        output_schema: type[BaseModel] | None = None,
        temperature: float = 0.3,
    ) -> LLMResult:
        if output_schema is None:
            return await self.generate(prompt, system, temperature)

        schema_instructions = (
            f"Responde SOLO con JSON valido que cumpla este schema:\n"
            f"{output_schema.model_json_schema()}"
        )
        full_system = f"{system}\n\n{schema_instructions}" if system else schema_instructions

        result = await self.generate(prompt, full_system, temperature)
        if not result.success:
            return result

        try:
            parsed = output_schema.model_validate_json(result.content)
            result.structured = parsed.model_dump()
            result.success = True
        except Exception as exc:
            result.success = False
            result.error = f"JSON parse failed: {exc}"

        return result


class FailoverLLMBackend(LLMBackend):
    """Wrapper que intenta multiples backends en orden.

    Si todos fallan, retorna LLMResult con success=False.
    El llamante decide si usar fallback rule-based.
    """

    def __init__(self, backends: list[LLMBackend]) -> None:
        super().__init__()
        if not backends:
            msg = "At least one backend required"
            raise ValueError(msg)
        self._backends = backends

    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResult:
        for backend in self._backends:
            result = await backend.generate(prompt, system, temperature, max_tokens)
            if result.success:
                return result
        return LLMResult(success=False, error="all backends failed")

    async def generate_structured(
        self,
        prompt: str,
        system: str = "",
        output_schema: type[BaseModel] | None = None,
        temperature: float = 0.3,
    ) -> LLMResult:
        for backend in self._backends:
            result = await backend.generate_structured(
                prompt,
                system,
                output_schema,
                temperature,
            )
            if result.success:
                return result
        return LLMResult(success=False, error="all backends failed")


def build_llm_backend() -> LLMBackend:
    """Factory: construye FailoverLLMBackend segun variables de entorno.

    Orden de prioridad:
        1. Proveedor definido en AGENTIC_LLM_PROVIDER
        2. OpenAI (si hay API key)
        3. Ollama (fallback local)
    """
    provider = os.getenv("AGENTIC_LLM_PROVIDER", "").lower()
    backends: list[LLMBackend] = []

    if provider == "openai" or not provider:
        backends.append(OpenAIBackend())
    if provider == "ollama" or not provider:
        backends.append(OllamaBackend())
    if provider == "vllm":
        backends.append(VLLMBackend())

    if not backends:
        backends = [OpenAIBackend(), OllamaBackend()]

    return FailoverLLMBackend(backends)
