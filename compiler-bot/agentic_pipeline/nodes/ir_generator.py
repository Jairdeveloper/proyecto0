"""IR Generator stage — builds IR tree and serializes output."""

from __future__ import annotations

import logging
from typing import Any

from ..base_stage import PipelineStage
from ..state_models import ActionPlan, AnalysisResult, StageContext, StageOutput
from .ir_builder import IRBuilder
from .ir_serializer import get_serializer
from .ir_nodes import IRNode

logger = logging.getLogger(__name__)


class IRGenerator(PipelineStage):
    """Stage 6: builds validated IR tree and serializes to multiple formats."""

    name = "ir_generator"

    def __init__(self, context: StageContext) -> None:
        super().__init__(context)
        self._input_ir: dict[str, Any] | None = None
        self._builder: IRBuilder | None = None
        self._built_root: IRNode | None = None

    def receive_mission(self, input_data: object) -> None:
        if isinstance(input_data, dict):
            ast = input_data.get("ast", input_data)
            if isinstance(ast, dict):
                self._input_ir = ast
                return
        self._input_ir = {"node_type": "project", "children": []}
        logger.warning("IRGenerator received non-dict input, using empty IR")

    def analyze(self) -> AnalysisResult:
        node_count = len(self._input_ir.get("children", [])) if self._input_ir else 0
        return AnalysisResult(
            observations=[f"IR nodes to process: {node_count}"],
            detected_patterns=[],
            risks=[],
            complexity_score=0.35,
        )

    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan:
        return ActionPlan(
            steps=[
                {"action": "build_ir_tree"},
                {"action": "validate_graph"},
                {"action": "serialize_output"},
            ],
            strategy="deterministic",
        )

    def act(self, plan: ActionPlan) -> StageOutput:
        self._builder = IRBuilder()
        self._built_root = self._builder.build(self._input_ir)

        errors = self._builder.validate()
        dep_order = self._builder.dep_graph.resolve()

        json_ser = get_serializer("json")
        yaml_ser = get_serializer("yaml")
        dot_ser = get_serializer("dot")

        return StageOutput(
            stage=self.context.stage,
            output_data={
                "ir_tree": self._built_root,
                "ir_json": json_ser.serialize(self._built_root),
                "ir_yaml": yaml_ser.serialize(self._built_root),
                "ir_dot": dot_ser.serialize(self._built_root),
                "validation_errors": errors,
                "dependency_order": dep_order,
                "node_count": len(self._built_root.children),
            },
            metrics={
                "node_count": len(self._built_root.children),
                "error_count": len(errors),
                "has_cycle": self._builder.dep_graph.has_cycle(),
            },
            success=len(errors) == 0,
        )

    def learn_and_improve(self, feedback: object) -> None:
        pass
