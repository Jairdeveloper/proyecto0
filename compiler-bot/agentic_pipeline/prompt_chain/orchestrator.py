"""ChainOrchestrator — orquestador del prompt chain con Chain of Responsibility.

Flujo:
    preprocess → intent → plan → generate → verify [→ retry → generate] → format
                                ↑          │
                                └── retry ──┘  (si should_retry y attempts < max_retries)
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from agentic_pipeline.feedback_loop import DebugObserver
from agentic_pipeline.prompt_chain.chain_context import ChainContext
from agentic_pipeline.prompt_chain.handler_base import (
    PromptHandler,
    PromptRequest,
)
from agentic_pipeline.prompt_chain.llm_backend import LLMBackend, build_llm_backend
from agentic_pipeline.prompt_chain.observer_base import StageSubject
from agentic_pipeline.prompt_chain.prompts.format import FormatHandler
from agentic_pipeline.prompt_chain.prompts.generate import GenerateHandler
from agentic_pipeline.prompt_chain.prompts.intent import IntentHandler
from agentic_pipeline.prompt_chain.prompts.plan import PlanHandler
from agentic_pipeline.prompt_chain.prompts.preprocess import PreprocessHandler
from agentic_pipeline.prompt_chain.prompts.verify import VerifyHandler

logger = logging.getLogger(__name__)

_PROMOTES_REGISTERED: bool = False


def _ensure_prompts_registered() -> None:
    """Ensure all 6 prompt templates are registered in PromptRegistry.

    Idempotent — solo ejecuta la importacion una vez.
    """
    global _PROMOTES_REGISTERED
    if _PROMOTES_REGISTERED:
        return
    from agentic_pipeline.prompt_chain import prompts as _pkg

    _ = _pkg
    _PROMOTES_REGISTERED = True


class ChainOrchestrator:
    """Orquestador del prompt chain con Chain of Responsibility + Observer.

    Construye una cadena de 6 PromptHandler y ejecuta el flujo
    completo con soporte de reintentos post-verificacion.

    Cada handler publica StageEvent en un StageSubject interno que
    tiene un DebugObserver adjunto, reemplazando el debug_callback
    directo de versiones anteriores.
    """

    def __init__(
        self,
        llm: LLMBackend | None = None,
        debug_callback: Callable[[str, dict], None] | None = None,
        max_retries: int = 3,
    ) -> None:
        _ensure_prompts_registered()
        self._llm = llm or build_llm_backend()
        self._debug_callback = debug_callback
        self._max_retries = max_retries
        self._subject = StageSubject()
        if debug_callback:
            self._subject.attach(DebugObserver(debug_callback))
        self._chain = self._build_main_chain()
        self._gen_handler: PromptHandler = GenerateHandler(
            self._llm,
            subject=self._subject,
        )
        self._ver_handler: PromptHandler = VerifyHandler(
            self._llm,
            subject=self._subject,
        )

    async def run(self, raw_input: str) -> dict:
        """Ejecuta el prompt chain completo.

        Args:
            raw_input: Texto del usuario (ej: "crea un modulo de pagos").

        Returns:
            Dict con output final del prompt FORMAT (OutputContract).
        """
        ctx = ChainContext()
        request = PromptRequest(
            raw_input=raw_input,
            debug_callback=self._debug_callback,
        )

        # pre → intent → plan → gen → verify
        await self._chain.handle(request, ctx)

        # Retry loop: gen → verify
        # Main chain's generate counts as attempt 1
        attempt = 1
        while attempt < self._max_retries:
            all_outputs = ctx.get_all_outputs()
            verify_output = all_outputs.get("verify", {})
            if not verify_output.get("should_retry", False):
                break
            attempt += 1
            logger.info("Retry attempt %d/%d", attempt, self._max_retries)
            self._gen_handler.set_next(self._ver_handler)
            await self._gen_handler.handle(request, ctx)

        # Format (always runs once at the end)
        fmt = FormatHandler(self._llm, subject=self._subject)
        result = await fmt.handle(request, ctx)

        return result.output

    def _build_main_chain(self) -> PromptHandler:
        """Construye la cadena principal: pre → intent → plan → gen → verify."""
        pre = PreprocessHandler(self._llm, subject=self._subject)
        intent = IntentHandler(self._llm, subject=self._subject)
        plan = PlanHandler(self._llm, subject=self._subject)
        gen = GenerateHandler(self._llm, subject=self._subject)
        verify = VerifyHandler(self._llm, subject=self._subject)
        pre.set_next(intent).set_next(plan).set_next(gen).set_next(verify)
        return pre
