"""Semantic analyzer with Visitor pattern, SymbolTable, and TypeRegistry."""

from __future__ import annotations

import logging
from typing import Any

from agentic_pipeline.base_stage import PipelineStage
from agentic_pipeline.nodes.ast_nodes import (
    ActionNode,
    ComponentNode,
    EntityNode,
    InfraNode,
    PageNode,
    ProjectNode,
)
from agentic_pipeline.nodes.ast_visitor import IASTVisitor
from agentic_pipeline.nodes.symbol_table import SymbolTable
from agentic_pipeline.nodes.type_systems import TypeRegistry, get_default_registry
from agentic_pipeline.state_models import ActionPlan, AnalysisResult, StageContext, StageOutput

logger = logging.getLogger(__name__)


# ============================================================================
# SemanticAnalysisVisitor — walks ASTNode tree using IASTVisitor
# ============================================================================


class SemanticAnalysisVisitor(IASTVisitor):
    """Visitor that walks ASTNode objects and collects semantic information.

    Replaces the dict-based SemanticVisitor with a typed visitor
    that operates on ASTNode instances via accept().
    """

    def __init__(
        self,
        symbol_table: SymbolTable,
        registry: TypeRegistry | None = None,
    ) -> None:
        self.symbols = symbol_table
        self.registry = registry or get_default_registry()
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def visit_project(self, node: ProjectNode) -> Any:
        self.symbols.define("$project", {"type": "project", "name": node.name})
        for child in node.children:
            child.accept(self)

    def visit_page(self, node: PageNode) -> Any:
        self.symbols.enter_scope()
        self.symbols.define(node.name, {"type": "page", "name": node.name})
        errs = self.registry.validate("ui", "page", {"name": node.name})
        self.errors.extend(errs)
        for child in node.children:
            child.accept(self)
        self.symbols.exit_scope()

    def visit_component(self, node: ComponentNode) -> Any:
        self.symbols.define(
            node.name,
            {"type": "component", "component_type": node.component_type},
        )
        errs = self.registry.validate(
            "ui",
            "component",
            {"name": node.name, "component_type": node.component_type},
        )
        self.errors.extend(errs)

    def visit_action(self, node: ActionNode) -> Any:
        if not node.target:
            self.errors.append(f"Action '{node.name}' missing target")
        self.symbols.define(
            f"action:{node.name}",
            {"type": "action", "action_type": node.action_type, "target": node.target},
        )

    def visit_entity(self, node: EntityNode) -> Any:
        self.symbols.define(node.name, {"type": "entity", "attributes": node.attributes})
        errs = self.registry.validate("data", "entity", {"name": node.name})
        self.errors.extend(errs)

    def visit_infra(self, node: InfraNode) -> Any:
        self.symbols.define(
            node.name,
            {"type": "infra", "infra_type": node.infra_type},
        )
        errs = self.registry.validate(
            "infra",
            "resource",
            {"name": node.name, "infra_type": node.infra_type},
        )
        self.errors.extend(errs)

    def get_results(self) -> dict[str, Any]:
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "symbol_count": self.symbols.scope_depth(),
            "scope_depth": self.symbols.scope_depth(),
        }


# ============================================================================
# SemanticVisitor — walks IR dict tree using string-dispatch Visitor pattern
# ============================================================================


class SemanticVisitor:
    """Visitor that walks an IR tree and collects semantic information.

    For each node type ``foo``, calls ``visit_foo(node)`` before children
    and ``exit_foo(node)`` after children.
    """

    def __init__(
        self,
        symbol_table: SymbolTable,
        registry: TypeRegistry | None = None,
    ) -> None:
        self.symbols = symbol_table
        self.registry = registry or get_default_registry()
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def visit(self, ir_node: dict[str, Any]) -> None:
        node_type = ir_node.get("node_type", "")
        visitor = getattr(self, f"visit_{node_type}", None)
        if visitor is not None:
            visitor(ir_node)
        else:
            self.warnings.append(f"Unknown node type: '{node_type}'")
        for child in ir_node.get("children", []):
            if isinstance(child, dict):
                self.visit(child)
        exit_visitor = getattr(self, f"exit_{node_type}", None)
        if exit_visitor is not None:
            exit_visitor(ir_node)

    def visit_project(self, node: dict[str, Any]) -> None:
        self.symbols.define("$project", {"type": "project", "node": node})

    def visit_page(self, node: dict[str, Any]) -> None:
        name = node.get("name", "")
        self.symbols.enter_scope()
        self.symbols.define(name, {"type": "page", "node": node})
        errs = self.registry.validate("ui", "page", node)
        self.errors.extend(errs)

    def exit_page(self, node: dict[str, Any]) -> None:
        self.symbols.exit_scope()

    def visit_component(self, node: dict[str, Any]) -> None:
        name = node.get("name", "")
        comp_type = node.get("component_type", "component")
        self.symbols.define(name, {"type": "component", "component_type": comp_type})
        errs = self.registry.validate("ui", "component", node)
        self.errors.extend(errs)

    def visit_entity(self, node: dict[str, Any]) -> None:
        name = node.get("name", "")
        self.symbols.define(name, {"type": "entity", "node": node})
        errs = self.registry.validate("data", "entity", node)
        self.errors.extend(errs)

    def visit_action(self, node: dict[str, Any]) -> None:
        target = node.get("target", "")
        value = node.get("name", node.get("value", ""))
        if not target:
            self.warnings.append(f"Action '{value}' has no target")
        self.symbols.define(f"$action_{value}", {
            "type": "action",
            "target": target,
            "node": node,
        })

    def exit_action(self, node: dict[str, Any]) -> None:
        pass

    def visit_infra(self, node: dict[str, Any]) -> None:
        name = node.get("name", "")
        infra_type = node.get("infra_type", "resource")
        self.symbols.define(name, {"type": "infra", "infra_type": infra_type})
        errs = self.registry.validate("infra", "resource", node)
        self.errors.extend(errs)

    def get_results(self) -> dict[str, Any]:
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "symbol_count": self.symbols.scope_depth(),
            "scope_depth": self.symbols.scope_depth(),
        }


# ============================================================================
# SemanticAnalyzer Stage
# ============================================================================


class SemanticAnalyzer(PipelineStage):
    """Stage 5: semantic analysis with type checking and symbol resolution."""

    name = "semantic_analyzer"

    def __init__(self, context: StageContext) -> None:
        super().__init__(context)
        self._input_ir: dict[str, Any] | None = None
        self._symbol_table = SymbolTable()
        self._visitor: SemanticVisitor | None = None
        self._enriched: dict = {}

    def receive_mission(self, input_data: object) -> None:
        if isinstance(input_data, dict):
            ast = input_data.get("ast", input_data)
            if isinstance(ast, dict):
                self._input_ir = ast
            else:
                self._input_ir = {"node_type": "project", "children": []}
            self._enriched = input_data.get("enriched", {}) or {}
        else:
            self._input_ir = {"node_type": "project", "children": []}
            self._enriched = {}
            logger.warning("SemanticAnalyzer received non-dict input, using empty IR")

    def analyze(self) -> AnalysisResult:
        node_count = len(self._input_ir.get("children", [])) if self._input_ir else 0
        return AnalysisResult(
            observations=[f"IR nodes to analyze: {node_count}"],
            detected_patterns=[],
            risks=[],
            complexity_score=0.4,
        )

    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan:
        return ActionPlan(
            steps=[
                {"action": "visit_ir"},
                {"action": "resolve_symbols"},
                {"action": "validate_types"},
            ],
            strategy="deterministic",
        )

    def act(self, plan: ActionPlan) -> StageOutput:
        self._symbol_table = SymbolTable()
        self._visitor = SemanticVisitor(self._symbol_table)
        self._visitor.visit(self._input_ir)
        results = self._visitor.get_results()
        snapshot = self._symbol_table.memento_save()
        return StageOutput(
            stage=self.context.stage,
            output_data={
                "ast": self._input_ir,
                "semantic_errors": results["errors"],
                "warnings": results["warnings"],
                "symbol_table_snapshot": snapshot,
                "scope_depth": results["scope_depth"],
                "enriched": self._enriched or None,
            },
            metrics={
                "error_count": len(results["errors"]),
                "warning_count": len(results["warnings"]),
                "scope_depth": results["scope_depth"],
            },
            success=len(results["errors"]) == 0,
        )

    def learn_and_improve(self, feedback: object) -> None:
        pass
