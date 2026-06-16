"""PipelineOrchestrator — StateGraph integration for RECPL v2.0."""

from __future__ import annotations

import logging
from typing import Any, Callable

from langgraph.graph import END, StateGraph

from .base_stage import PipelineStage
from .error_guard import ErrorGuard
from .nodes.intent_stage import IntentStage
from .nodes.ir_generator import IRGenerator
from .nodes.lexer import Lexer
from .nodes.parser import ParserGLR
from .nodes.planner import HybridPlanner
from .nodes.preprocessor import Preprocessor
from .nodes.semantic_analyzer import SemanticAnalyzer
from .nodes.synthesis import SynthesisOrchestrator
from .nodes.ui_generator import UIGenerator
from .nodes.validator import ValidatorPipeline
from .state_models import Stage, StageContext, StageOutput

logger = logging.getLogger(__name__)

NODE_MAP: dict[Stage, type[PipelineStage]] = {
    Stage.INTENT: IntentStage,
    Stage.PREPROCESSOR: Preprocessor,
    Stage.LEXER: Lexer,
    Stage.PARSER: ParserGLR,
    Stage.SEMANTIC_ANALYZER: SemanticAnalyzer,
    Stage.IR_GENERATOR: IRGenerator,
    Stage.PLANNER: HybridPlanner,
    Stage.SYNTHESIS: SynthesisOrchestrator,
    Stage.UI_GENERATOR: UIGenerator,
    Stage.VALIDATOR: ValidatorPipeline,
}

StreamCallback = Callable[[str, StageOutput], None]


class PipelineOrchestrator:
    """StateGraph-based pipeline orchestrator for RECPL v2.0."""

    def __init__(
        self,
        stream_callback: StreamCallback | None = None,
        output_dir: str = "modules",
    ) -> None:
        self._stream_callback = stream_callback
        self._output_dir = output_dir
        self.graph = StateGraph(StageContext)
        self._build()

    def _make_node(self, stage: Stage) -> Callable[[StageContext], dict[str, Any]]:
        cls = NODE_MAP[stage]

        def node_fn(ctx: StageContext) -> dict[str, Any]:
            ctx.stage = stage
            ctx.config_overrides["output_dir"] = self._output_dir
            instance = cls(ctx)
            output = instance.execute(ctx.input_data)
            if self._stream_callback:
                self._stream_callback(stage.value, output)
            updated: dict[str, Any] = {"input_data": output.output_data}
            if not output.success:
                ctx.last_error = output.error
                logger.warning(
                    "Stage %s reported failure: %s",
                    stage.value,
                    output.error,
                )
            else:
                ctx.last_error = None
            return updated

        return node_fn

    def _build(self) -> None:
        stages = list(NODE_MAP.keys())
        self.graph.set_entry_point(stages[0].value)
        for stage in stages:
            self.graph.add_node(stage.value, self._make_node(stage))
        for i in range(len(stages) - 1):
            current = stages[i].value
            next_stage = stages[i + 1].value
            self.graph.add_conditional_edges(
                current,
                ErrorGuard.should_continue,
                {"continue": next_stage, "abort": END},
            )
        self.graph.set_finish_point(stages[-1].value)
        self.compiled = self.graph.compile()

    async def run(self, user_input: str) -> dict[str, Any]:
        ctx = StageContext(stage=Stage.INTENT, input_data=user_input)
        logger.info("PipelineOrchestrator starting with input: %.100s", user_input)
        result: dict[str, Any] = await self.compiled.ainvoke(ctx)
        logger.info("PipelineOrchestrator finished")
        output = result.get("input_data", {})
        return {
            "output": output,
            "success": True,
        }
