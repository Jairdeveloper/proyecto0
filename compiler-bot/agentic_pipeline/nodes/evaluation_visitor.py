"""Evaluation visitor — replaces evaluate() in ASTNode."""

from typing import Any

from agentic_pipeline.nodes.ast_nodes import (
    ComponentNode,
    EntityNode,
    InfraNode,
    PageNode,
    ProjectNode,
)
from agentic_pipeline.nodes.ast_visitor import TreeWalkingVisitor


class EvaluationVisitor(TreeWalkingVisitor):
    """Walks AST and produces evaluation dict (replaces node.evaluate())."""

    def __init__(self):
        super().__init__()
        self._result: dict = {}

    def visit_project(self, node: ProjectNode) -> Any:
        pages = []
        for child in node.children:
            result = child.accept(self)
            if result:
                pages.append(result)
        self._result = {"type": "project", "name": node.name, "pages": pages}
        return self._result

    def visit_page(self, node: PageNode) -> Any:
        components = []
        for child in node.children:
            result = child.accept(self)
            if result:
                components.append(result)
        return {"type": "page", "name": node.name, "components": components}

    def visit_component(self, node: ComponentNode) -> Any:
        return {
            "type": "component",
            "name": node.name,
            "component_type": node.component_type,
        }

    def visit_entity(self, node: EntityNode) -> Any:
        return {
            "type": "entity",
            "name": node.name,
            "attributes": node.attributes,
        }

    def visit_infra(self, node: InfraNode) -> Any:
        return {
            "type": "infra",
            "name": node.name,
            "infra_type": node.infra_type,
        }
