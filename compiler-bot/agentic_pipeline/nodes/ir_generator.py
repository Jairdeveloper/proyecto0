"""IR Generator stage — construye el arbol IR canonico y lo serializa. El IR es el producto central del compilador."""

from __future__ import annotations

import logging
from typing import Any

from agentic_pipeline.base_stage import PipelineStage
from agentic_pipeline.nodes.ast_nodes import ASTNode
from agentic_pipeline.nodes.ir_builder import IRBuilder
from agentic_pipeline.nodes.ir_export_visitor import IRExportVisitor
from agentic_pipeline.nodes.ir_nodes import IRNode
from agentic_pipeline.nodes.ir_serializer import get_serializer
from agentic_pipeline.state_models import ActionPlan, AnalysisResult, StageContext, StageOutput

logger = logging.getLogger(__name__)


class IRGenerator(PipelineStage):
    """Stage 6: construye el arbol IR validado y lo serializa a multiples formatos. El IR es independiente de tecnologia."""

    name = "ir_generator"

    def __init__(self, context: StageContext) -> None:
        super().__init__(context)
        self._input_ir: dict[str, Any] | None = None
        self._builder: IRBuilder | None = None
        self._built_root: IRNode | None = None
        self._enriched: dict = {}
        self._ast_node: ASTNode | None = None

    def receive_mission(self, input_data: object) -> None:
        if isinstance(input_data, ASTNode):
            self._ast_node = input_data
            self._input_ir = input_data.accept(IRExportVisitor())
            self._enriched = {}
        elif isinstance(input_data, dict):
            ast = input_data.get("ast", input_data)
            if isinstance(ast, dict):
                self._input_ir = ast
            else:
                self._input_ir = {"node_type": "project", "children": []}
            self._enriched = input_data.get("enriched", {}) or {}
        else:
            self._input_ir = {"node_type": "project", "children": []}
            self._enriched = {}
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
                "enriched": self._enriched or None,
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
