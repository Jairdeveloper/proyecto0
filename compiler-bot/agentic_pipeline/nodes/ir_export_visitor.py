"""IR Export Visitor — serializes AST to IR dict (replaces node.to_ir())."""

from typing import Any

from agentic_pipeline.nodes.ast_nodes import (
    ComponentNode,
    EntityNode,
    InfraNode,
    PageNode,
    ProjectNode,
)
from agentic_pipeline.nodes.ast_visitor import IASTVisitor


class IRExportVisitor(IASTVisitor):
    """Visitor that serializes AST to canonical IR dict.

    Separates serialization responsibility from AST nodes.
    Create a new visitor for each export format (YAML, DOT, JSON Schema).
    """

    def visit_project(self, node: ProjectNode) -> Any:
        children = [child.accept(self) for child in node.children]
        return {"node_type": "project", "name": node.name, "children": children}

    def visit_page(self, node: PageNode) -> Any:
        children = [child.accept(self) for child in node.children]
        return {"node_type": "page", "name": node.name, "children": children}

    def visit_component(self, node: ComponentNode) -> Any:
        return {
            "node_type": "component",
            "name": node.name,
            "component_type": node.component_type,
        }

    def visit_entity(self, node: EntityNode) -> Any:
        return {
            "node_type": "entity",
            "name": node.name,
            "attributes": node.attributes,
        }

    def visit_infra(self, node: InfraNode) -> Any:
        return {
            "node_type": "infra",
            "name": node.name,
            "infra_type": node.infra_type,
            "resources": node.resources,
        }
