"""ChainOrchestrator — orquestador del prompt chain con LangGraph.

Flujo:
    preprocess → intent → plan → generate → verify → format
                                ↑          │
                                └── retry ──┘  (si should_retry y attempts < max_retries)
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TypedDict

from langgraph.graph import StateGraph

from agentic_pipeline.prompt_chain.chain_context import ChainContext
from agentic_pipeline.prompt_chain.llm_backend import LLMBackend, build_llm_backend

logger = logging.getLogger(__name__)

# ── Flag de registro unico de prompts ──
_PROMOTES_REGISTERED: bool = False


def _ensure_prompts_registered() -> None:
    """Ensure all 6 prompt templates are registered in PromptRegistry.

    Idempotent — solo ejecuta la importacion una vez.
    """
    global _PROMOTES_REGISTERED
    if _PROMOTES_REGISTERED:
        return
    # Importar el paquete prompts ejecuta __init__.py, que a su vez
    # importa cada submodulo y ejecuta register_prompt() en cada uno.
    from agentic_pipeline.prompt_chain import prompts as _pkg

    _ = _pkg
    _PROMOTES_REGISTERED = True


# ── Estado del grafo ──


class ChainState(TypedDict):
    """Estado compartido del grafo LangGraph.

    Cada nodo publica su output como campo en el estado.
    ``ctx`` es el bus de datos entre etapas (ChainContext).
    """

    raw_input: str
    ctx: ChainContext
    preprocess_output: dict | None
    intent_output: dict | None
    plan_output: dict | None
    generate_output: dict | None
    verify_output: dict | None
    format_output: dict | None
    final_output: dict | None
    attempt_count: int
    errors: list[str]


# ── Orquestador ──


class ChainOrchestrator:
    """Orquestador del prompt chain con LangGraph.

    Construye un StateGraph con 6 nodos (uno por prompt) y routing
    condicional post-verificacion (retry → generate, abort → END).
    """

    def __init__(
        self,
        llm: LLMBackend | None = None,
        debug_callback: Callable[[str, dict], None] | None = None,
        max_retries: int = 3,
    ) -> None:
        """Inicializa el orquestador.

        Args:
            llm: Backend LLM (se autoconfigura si no se provee).
            debug_callback: Callable(stage_name, output_dict) para debug.
            max_retries: Maximo numero de reintentos en verify→generate.
        """
        _ensure_prompts_registered()
        self._llm = llm or build_llm_backend()
        self._debug_callback = debug_callback
        self._max_retries = max_retries
        self._graph = self._build_graph()

    async def run(self, raw_input: str) -> dict:
        """Ejecuta el prompt chain completo.

        Args:
            raw_input: Texto del usuario (ej: "crea un modulo de pagos").

        Returns:
            Dict con output final del prompt FORMAT (OutputContract).
        """
        ctx = ChainContext()
        state: ChainState = {
            "raw_input": raw_input,
            "ctx": ctx,
            "preprocess_output": None,
            "intent_output": None,
            "plan_output": None,
            "generate_output": None,
            "verify_output": None,
            "format_output": None,
            "final_output": None,
            "attempt_count": 0,
            "errors": [],
        }
        result = await self._graph.ainvoke(state)
        return result.get("final_output", {})

    # ── Construccion del grafo ──

    def _build_graph(self) -> StateGraph:
        """Construye el grafo LangGraph con 6 nodos y routing condicional."""
        graph = StateGraph(ChainState)

        graph.add_node("preprocess", self._node_preprocess)
        graph.add_node("intent", self._node_intent)
        graph.add_node("plan", self._node_plan)
        graph.add_node("generate", self._node_generate)
        graph.add_node("verify", self._node_verify)
        graph.add_node("format", self._node_format)

        graph.set_entry_point("preprocess")
        graph.add_edge("preprocess", "intent")
        graph.add_edge("intent", "plan")
        graph.add_edge("plan", "generate")
        graph.add_edge("generate", "verify")
        graph.add_conditional_edges(
            "verify",
            self._router_verify,
            {
                "retry": "generate",
                "format": "format",
                "abort": "format",
            },
        )
        graph.set_finish_point("format")

        return graph.compile()

    # ── Nodos del grafo ──

    async def _node_preprocess(self, state: ChainState) -> dict:
        """Ejecuta prompt PREPROCESS."""
        from agentic_pipeline.prompt_chain.prompts.preprocess import (
            preprocess_handler,
        )

        try:
            output = await preprocess_handler(
                raw_text=state["raw_input"],
                llm=self._llm,
                ctx=state["ctx"],
            )
            if self._debug_callback:
                self._debug_callback("preprocess", output)
            return {"preprocess_output": output}
        except Exception as exc:
            logger.error("preprocess failed: %s", exc)
            state["errors"].append(f"preprocess: {exc}")
            return {"preprocess_output": None}

    async def _node_intent(self, state: ChainState) -> dict:
        """Ejecuta prompt INTENT."""
        from agentic_pipeline.prompt_chain.prompts.intent import intent_handler

        try:
            pre = state["ctx"].get_fields("preprocess", ["normalized", "domain"])
            output = await intent_handler(
                normalized_text=pre["normalized"],
                domain=pre.get("domain", "backend"),
                llm=self._llm,
                ctx=state["ctx"],
            )
            if self._debug_callback:
                self._debug_callback("intent", output)
            return {"intent_output": output}
        except Exception as exc:
            logger.error("intent failed: %s", exc)
            state["errors"].append(f"intent: {exc}")
            return {"intent_output": None}

    async def _node_plan(self, state: ChainState) -> dict:
        """Ejecuta prompt PLAN."""
        from agentic_pipeline.prompt_chain.prompts.plan import plan_handler

        try:
            intent_data = state["ctx"].get_fields(
                "intent", ["intent", "module", "entity", "tech", "features"],
            )
            output = await plan_handler(
                intent=intent_data["intent"],
                module=intent_data.get("module"),
                entity=intent_data.get("entity"),
                tech=intent_data.get("tech", []),
                features=intent_data.get("features", []),
                llm=self._llm,
                ctx=state["ctx"],
            )
            if self._debug_callback:
                self._debug_callback("plan", output)
            return {"plan_output": output}
        except Exception as exc:
            logger.error("plan failed: %s", exc)
            state["errors"].append(f"plan: {exc}")
            return {"plan_output": None}

    async def _node_generate(self, state: ChainState) -> dict:
        """Ejecuta prompt GENERATE."""
        from agentic_pipeline.prompt_chain.prompts.generate import (
            generate_handler,
        )

        attempt = state["attempt_count"] + 1
        try:
            plan_data = state["ctx"].get_fields("plan", ["tasks"])
            output = await generate_handler(
                tasks=plan_data.get("tasks", []),
                llm=self._llm,
                ctx=state["ctx"],
            )
            if self._debug_callback:
                self._debug_callback("generate", output)
            return {"generate_output": output, "attempt_count": attempt}
        except Exception as exc:
            logger.error("generate failed: %s", exc)
            state["errors"].append(f"generate: {exc}")
            return {"generate_output": None, "attempt_count": attempt}

    async def _node_verify(self, state: ChainState) -> dict:
        """Ejecuta prompt VERIFY."""
        from agentic_pipeline.prompt_chain.prompts.verify import verify_handler

        try:
            intent_data = state["ctx"].get_fields(
                "intent", ["intent", "module", "entity", "tech", "features"],
            )
            generate_data = state["ctx"].get_fields("generate", ["files"])
            output = await verify_handler(
                requirements=intent_data,
                files=generate_data.get("files", []),
                llm=self._llm,
                ctx=state["ctx"],
            )
            if self._debug_callback:
                self._debug_callback("verify", output)
            return {"verify_output": output}
        except Exception as exc:
            logger.error("verify failed: %s", exc)
            state["errors"].append(f"verify: {exc}")
            return {"verify_output": {"valid": False, "should_retry": False,
                                      "checks": [], "suggestions": []}}

    async def _node_format(self, state: ChainState) -> dict:
        """Ejecuta prompt FORMAT y escribe resultado final."""
        from agentic_pipeline.prompt_chain.prompts.format import format_handler

        try:
            plan_data = state["ctx"].get_fields("plan", ["tasks",
                                                          "execution_order"])
            generate_data = state["ctx"].get_fields("generate", ["files"])
            verify_data = state["ctx"].get_fields(
                "verify", ["valid", "checks", "suggestions"],
            )
            output = await format_handler(
                original_request=state["raw_input"],
                plan=plan_data,
                generated_files=generate_data.get("files", []),
                validation=verify_data,
                llm=self._llm,
                ctx=state["ctx"],
            )
            if self._debug_callback:
                self._debug_callback("format", output)
            return {"format_output": output, "final_output": output}
        except Exception as exc:
            logger.error("format failed: %s", exc)
            state["errors"].append(f"format: {exc}")
            error_output = {
                "summary": "Error al generar el resumen final.",
                "files_created": [],
                "warnings": [],
                "next_steps": ["Revisa los logs de error"],
                "success": False,
            }
            return {"format_output": error_output, "final_output": error_output}

    # ── Router condicional ──

    def _router_verify(self, state: ChainState) -> str:
        """Router condicional post-verificacion.

        Returns:
            "retry":  si should_retry y attempt_count < max_retries.
            "format": si valid=True o attempt_count >= max_retries.
            "abort":  si error critico (valid=False sin retry posible).
        """
        verify = state.get("verify_output") or {}
        if verify.get("should_retry") and state["attempt_count"] < self._max_retries:
            return "retry"
        if verify.get("valid", False):
            return "format"
        return "abort"
