"""Chain of Responsibility base for prompt handlers.

PromptHandler is an abstract handler with:
- set_next() for chain linking
- handle() that attempts LLM → fallback → publishes to ctx → delegates
- Default safety-net in handle() so every handler is self-sufficient
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Callable

from pydantic import BaseModel

from agentic_pipeline.prompt_chain.chain_context import ChainContext
from agentic_pipeline.prompt_chain.fallbacks import execute_fallback
from agentic_pipeline.prompt_chain.llm_backend import LLMBackend, build_llm_backend
from agentic_pipeline.prompt_chain.observer_base import (
    StageEvent,
    StageSubject,
)
from agentic_pipeline.prompt_chain.prompt_template import PromptRegistry

logger = logging.getLogger(__name__)


class PromptRequest(BaseModel):
    """Payload que fluye a traves de la cadena CoR."""

    raw_input: str
    debug_callback: Callable[[str, dict], None] | None = None


class PromptResponse(BaseModel):
    """Resultado de un handler en la cadena CoR."""

    success: bool = True
    output: dict[str, Any] = {}
    error: str | None = None


class PromptHandler(ABC):
    """Base abstracta para handlers del prompt chain (Chain of Responsibility).

    Cada handler concreto debe implementar:
      - name: str — nombre del handler (ej: "preprocess")
      - output_contract: type[BaseModel] — contrato Pydantic de salida
      - input_fields: list[str] — campos a extraer de ctx

    Opcionalmente puede sobreescribir _build_prompt_kwargs() para
    personalizar como se construyen los argumentos del prompt.
    """

    name: str = ""
    output_contract: type[BaseModel] | None = None
    input_fields: list[str] = []
    _next_handler: PromptHandler | None = None

    def __init__(
        self,
        llm: LLMBackend | None = None,
        debug_callback: Callable[[str, dict], None] | None = None,
        subject: StageSubject | None = None,
    ) -> None:
        self._llm = llm or build_llm_backend()
        self._debug_callback = debug_callback
        self._subject = subject

    @abstractmethod
    def _build_prompt_kwargs(
        self,
        request: PromptRequest,
        ctx_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Construye kwargs para template.render() y fallback.

        Cada handler concreto define que datos necesita para su prompt.
        """

    def set_next(self, handler: PromptHandler) -> PromptHandler:
        """Encadena el siguiente handler. Retorna el handler para fluent API."""
        self._next_handler = handler
        return handler

    async def handle(
        self,
        request: PromptRequest,
        ctx: ChainContext,
    ) -> PromptResponse:
        """Procesa el request: LLM → fallback → publica en ctx → delega."""
        t0 = time.time()
        try:
            ctx_data = self._get_ctx_data(ctx)
            kwargs = self._build_prompt_kwargs(request, ctx_data)

            template = PromptRegistry.get(self.name)
            prompt = template.render(**kwargs)

            result = await self._llm.generate_structured(
                prompt=prompt,
                system=template.system_prompt,
                output_schema=template.output_schema,
                temperature=template.temperature,
            )

            if not result.success:
                logger.info("LLM %s failed, using fallback", self.name)
                output = execute_fallback(template.fallback_name or "", **kwargs)
            else:
                output = result.structured  # type: ignore[assignment]

            if ctx:
                try:
                    contract = self.output_contract
                    ctx.set_output(self.name, output, contract=contract)
                except Exception as exc:
                    logger.warning("%s ctx.set_output failed: %s", self.name, exc)

            duration = time.time() - t0
            self._notify_observers(output, duration, success=True)

            if self._debug_callback:
                self._debug_callback(self.name, output)

            if self._next_handler is not None:
                return await self._next_handler.handle(request, ctx)

            return PromptResponse(success=True, output=output)

        except Exception as exc:
            duration = time.time() - t0
            logger.error("%s handler failed: %s", self.name, exc)
            self._notify_observers({}, duration, success=False, error=str(exc))
            return PromptResponse(success=False, output={}, error=str(exc))

    def _notify_observers(
        self,
        output: dict,
        duration: float,
        success: bool,
        error: str | None = None,
    ) -> None:
        """Publica un StageEvent en el subject si esta configurado.

        Reemplaza funcionalmente al debug_callback directo, permitiendo
        que multiples observers (MetricsObserver, DebugObserver, etc.)
        reaccionen al mismo evento.
        """
        if self._subject:
            event = StageEvent(
                stage=self.name,
                duration=round(duration, 4),
                success=success,
                output=output,
                error=error,
            )
            self._subject.notify(event)

    def _get_ctx_data(self, ctx: ChainContext) -> dict[str, Any]:
        """Extrae campos del contexto de etapas anteriores."""
        if not self.input_fields:
            return {}
        data: dict[str, Any] = {}
        for field in self.input_fields:
            for stage in ["preprocess", "intent", "plan", "generate", "verify"]:
                try:
                    val = ctx.get_fields(stage, [field])
                    if field in val:
                        data[field] = val[field]
                        break
                except KeyError:
                    continue
        return data
