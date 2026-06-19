"""AST Visitor pattern — IASTVisitor interface and TreeWalkingVisitor base."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agentic_pipeline.nodes.ast_nodes import (
        ActionNode,
        ComponentNode,
        EntityNode,
        InfraNode,
        PageNode,
        ProjectNode,
    )


class IASTVisitor(ABC):
    """Interface for AST node visitors.

    Each node type has a dedicated visit_* method.
    New operations = new subclasses (OCP compliance).
    """

    @abstractmethod
    def visit_project(self, node: ProjectNode) -> Any: ...

    @abstractmethod
    def visit_page(self, node: PageNode) -> Any: ...

    @abstractmethod
    def visit_component(self, node: ComponentNode) -> Any: ...

    @abstractmethod
    def visit_entity(self, node: EntityNode) -> Any: ...

    @abstractmethod
    def visit_action(self, node: ActionNode) -> Any: ...

    @abstractmethod
    def visit_infra(self, node: InfraNode) -> Any: ...


class TreeWalkingVisitor(IASTVisitor):
    """Base visitor that walks the AST tree recursively.
    Subclasses override specific visit_* methods.
    """

    def visit_project(self, node: ProjectNode) -> Any:
        for child in node.children:
            child.accept(self)
        return self

    def visit_page(self, node: PageNode) -> Any:
        for child in node.children:
            child.accept(self)
        return self

    def visit_component(self, node: ComponentNode) -> Any:
        return self

    def visit_entity(self, node: EntityNode) -> Any:
        return self

    def visit_action(self, node: ActionNode) -> Any:
        return self

    def visit_infra(self, node: InfraNode) -> Any:
        return self
