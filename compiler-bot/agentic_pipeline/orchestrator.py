"""AgentOrchestrator — StateGraph integration for RECPL v2.0."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from langgraph.graph import END, StateGraph

from agentic_pipeline.agents.agent_stage_adapter import AgentStageAdapter
from agentic_pipeline.agents.base_agent import Agent
from agentic_pipeline.base_stage import PipelineStage
from agentic_pipeline.error_guard import ErrorGuard
from agentic_pipeline.nodes.action_executor import ActionExecutor
from agentic_pipeline.nodes.ir_generator import IRGenerator
from agentic_pipeline.nodes.lexer import Lexer
from agentic_pipeline.nodes.parser import LarkParser
from agentic_pipeline.nodes.perception_unit import PerceptionUnit
from agentic_pipeline.nodes.preprocessor import Preprocessor
from agentic_pipeline.nodes.reasoning_engine import ReasoningEngine
from agentic_pipeline.nodes.semantic_analyzer import SemanticAnalyzer
from agentic_pipeline.nodes.ui_generator import UIGenerator
from agentic_pipeline.nodes.validator import ValidatorPipeline
from agentic_pipeline.prompt_chain.command_base import Command, CommandResult
from agentic_pipeline.stage_executor import StageExecutor
from agentic_pipeline.state_models import ContextWindow, Stage, StageContext, StageOutput

logger = logging.getLogger(__name__)


# ============================================================================
# Context Engineering (N2.2c)
# ============================================================================


def build_context(stage: Stage, full_context: dict, world: object = None) -> ContextWindow:
    """Construye el contexto optimo para cada stage."""
    history = full_context.get("history", [])
    world_snapshot = world.snapshot() if world and hasattr(world, "snapshot") else {}

    if stage in (Stage.INTENT, Stage.PERCEPTION):
        return ContextWindow(
            relevant_history=history[-3:],
            world_snapshot={},
            task_focus="parse user intent and classify",
        )
    if stage in (Stage.PLANNER, Stage.REASONING):
        return ContextWindow(
            relevant_history=[],
            world_snapshot=world_snapshot,
            task_focus="decompose goal with current world state",
        )
    if stage in (Stage.SYNTHESIS, Stage.EXECUTION):
        files_list = world_snapshot.get("files", []) if isinstance(world_snapshot, dict) else []
        return ContextWindow(
            relevant_history=[],
            world_snapshot={"files": files_list},
            task_focus="generate code per plan, avoid overwrites",
        )
    if stage in (Stage.PREPROCESSOR, Stage.LEXER, Stage.PARSER):
        return ContextWindow(
            relevant_history=[],
            world_snapshot={},
            task_focus="syntactic analysis without context bias",
        )
    return ContextWindow(
        relevant_history=history,
        world_snapshot=world_snapshot,
        task_focus="general processing",
    )


NODE_MAP: dict[Stage, type[PipelineStage]] = {
    Stage.INTENT: PerceptionUnit,
    Stage.PREPROCESSOR: Preprocessor,
    Stage.LEXER: Lexer,
    Stage.PARSER: LarkParser,
    Stage.SEMANTIC_ANALYZER: SemanticAnalyzer,
    Stage.IR_GENERATOR: IRGenerator,
    Stage.PLANNER: ReasoningEngine,
    Stage.SYNTHESIS: ActionExecutor,
    Stage.UI_GENERATOR: UIGenerator,
    Stage.VALIDATOR: ValidatorPipeline,
}

StreamCallback = Callable[[str, StageOutput], None]


class AgentOrchestrator:
    """StateGraph-based agent orchestrator for RECPL v2.0."""

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
        executor = StageExecutor()
        cls = NODE_MAP[stage]

        async def node_fn(ctx: StageContext) -> dict[str, Any]:
            ctx.stage = stage
            ctx.config_overrides["output_dir"] = self._output_dir
            instance = cls(ctx)
            output = await executor.execute(instance, ctx.input_data)
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

    def build_from_agents(self, agents: dict[str, Agent]) -> None:
        """Build a StateGraph using AgentStageAdapters.

        Each agent is wrapped as a PipelineStage and connected sequentially.
        The adapter delegates to agent.process() internally.
        """
        agent_order = [
            "perception_agent",
            "reasoning_agent",
            "execution_agent",
            "validator_agent",
        ]
        stages: list[tuple[str, AgentStageAdapter]] = []
        for agent_name in agent_order:
            agent = agents.get(agent_name)
            if not agent:
                continue
            ctx = StageContext(
                stage=Stage.INTENT,
                input_data="",
                config_overrides={"output_dir": self._output_dir},
            )
            adapter = AgentStageAdapter(ctx, agent, agent_name)
            stages.append((agent_name, adapter))

        if not stages:
            return

        self.graph.set_entry_point(stages[0][0])
        for name, adapter in stages:
            self.graph.add_node(name, self._make_adapter_node(adapter))
        for i in range(len(stages) - 1):
            current = stages[i][0]
            next_name = stages[i + 1][0]
            self.graph.add_conditional_edges(
                current,
                ErrorGuard.should_continue,
                {"continue": next_name, "abort": END},
            )
        self.graph.set_finish_point(stages[-1][0])
        self.compiled = self.graph.compile()

    def _make_adapter_node(
        self,
        adapter: AgentStageAdapter,
    ) -> Callable[[StageContext], dict[str, Any]]:
        def node_fn(ctx: StageContext) -> dict[str, Any]:
            ctx.stage = Stage.INTENT
            ctx.config_overrides["output_dir"] = self._output_dir
            output = adapter.execute(ctx.input_data)
            if self._stream_callback:
                self._stream_callback(adapter.name, output)
            updated: dict[str, Any] = {"input_data": output.output_data}
            if not output.success:
                ctx.last_error = output.error
                logger.warning(
                    "Agent adapter %s reported failure: %s",
                    adapter.name,
                    output.error,
                )
            else:
                ctx.last_error = None
            return updated

        return node_fn

    async def run(self, user_input: str) -> dict[str, Any]:
        ctx = StageContext(stage=Stage.INTENT, input_data=user_input)
        logger.info("AgentOrchestrator starting with input: %.100s", user_input)
        result: dict[str, Any] = await self.compiled.ainvoke(ctx)
        logger.info("AgentOrchestrator finished")
        output = result.get("input_data", {})
        return {
            "output": output,
            "success": True,
        }


# Backward compat
PipelineOrchestrator = AgentOrchestrator


class PipelineMacroCommand(Command):
    """MacroCommand que ejecuta el pipeline RECPL completo.

    Encapsula todos los PipelineStage en un solo Command,
    permitiendo su uso con CommandHistory, logging, y replay.
    """

    name = "pipeline"

    def __init__(
        self,
        stages: list[type[PipelineStage]],
        output_dir: str = "modules",
        stream_callback: StreamCallback | None = None,
    ) -> None:
        self._stages = stages
        self._output_dir = output_dir
        self._stream_callback = stream_callback

    async def execute(self) -> CommandResult:
        """Ejecuta todos los stages secuencialmente."""
        from agentic_pipeline.command_base import CommandResult

        t0 = time.time()
        input_data: object = ""
        last_error: str | None = None

        for stage_cls in self._stages:
            stage_enum = self._stage_to_enum(stage_cls)
            ctx = StageContext(
                stage=stage_enum,
                input_data=input_data,
                config_overrides={"output_dir": self._output_dir},
            )
            instance = stage_cls(ctx)
            try:
                output = instance.execute(input_data)
                if self._stream_callback:
                    self._stream_callback(stage_cls.__name__, output)
                if not output.success:
                    last_error = output.error
                    logger.warning(
                        "PipelineMacro stage %s failed: %s",
                        stage_cls.__name__,
                        output.error,
                    )
                    break
                input_data = output.output_data
            except Exception as exc:
                last_error = str(exc)
                logger.error(
                    "PipelineMacro stage %s exception: %s",
                    stage_cls.__name__,
                    exc,
                )
                break

        duration = time.time() - t0
        return CommandResult(
            success=last_error is None,
            data=input_data if isinstance(input_data, dict) else {"output": input_data},
            error=last_error,
            duration=duration,
            command_name=self.name,
        )

    @staticmethod
    def _stage_to_enum(stage_cls: type[PipelineStage]) -> Stage:
        """Mapea clase PipelineStage a su enum Stage."""
        from agentic_pipeline.nodes.action_executor import ActionExecutor
        from agentic_pipeline.nodes.intent_stage import IntentStage
        from agentic_pipeline.nodes.ir_generator import IRGenerator
        from agentic_pipeline.nodes.lexer import Lexer
        from agentic_pipeline.nodes.parser import LarkParser
        from agentic_pipeline.nodes.preprocessor import Preprocessor
        from agentic_pipeline.nodes.reasoning_engine import ReasoningEngine
        from agentic_pipeline.nodes.semantic_analyzer import SemanticAnalyzer
        from agentic_pipeline.nodes.ui_generator import UIGenerator
        from agentic_pipeline.nodes.validator import ValidatorPipeline
        from agentic_pipeline.state_models import Stage

        mapping: dict[type[PipelineStage], Stage] = {
            IntentStage: Stage.INTENT,
            Preprocessor: Stage.PREPROCESSOR,
            Lexer: Stage.LEXER,
            LarkParser: Stage.PARSER,
            SemanticAnalyzer: Stage.SEMANTIC_ANALYZER,
            IRGenerator: Stage.IR_GENERATOR,
            ReasoningEngine: Stage.PLANNER,
            ActionExecutor: Stage.SYNTHESIS,
            UIGenerator: Stage.UI_GENERATOR,
            ValidatorPipeline: Stage.VALIDATOR,
        }
        return mapping.get(stage_cls, Stage.PREPROCESSOR)
