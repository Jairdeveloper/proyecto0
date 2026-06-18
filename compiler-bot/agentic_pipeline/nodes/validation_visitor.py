"""Validation visitor — replaces validate() in ASTNode."""

from typing import Any

from agentic_pipeline.nodes.ast_nodes import (
    ComponentNode,
    EntityNode,
    PageNode,
)
from agentic_pipeline.nodes.ast_visitor import TreeWalkingVisitor


class ValidationVisitor(TreeWalkingVisitor):
    """Walks AST and collects validation errors."""

    def __init__(self):
        super().__init__()
        self.errors: list[str] = []

    def visit_page(self, node: PageNode) -> Any:
        if not node.children:
            self.errors.append(f"Page '{node.name}' has no components")
        super().visit_page(node)
        return self

    def visit_entity(self, node: EntityNode) -> Any:
        if not node.attributes:
            self.errors.append(f"Entity '{node.name}' has no attributes")
        super().visit_entity(node)
        return self

    def visit_component(self, node: ComponentNode) -> Any:
        if not node.name:
            self.errors.append("Component has no name")
        super().visit_component(node)
        return self
