"""AST nodes with Composite pattern for parser output."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agentic_pipeline.nodes.ast_visitor import IASTVisitor


class ASTNode(ABC):
    """Base AST node with parent-child navigation."""

    def __init__(self, name: str = ""):
        self.name = name
        self.children: list[ASTNode] = []
        self.parent: ASTNode | None = None

    def add(self, child: ASTNode) -> None:
        self.children.append(child)
        child.parent = self

    @abstractmethod
    def accept(self, visitor: IASTVisitor) -> Any: ...


class ProjectNode(ASTNode):
    """Root node representing a project."""

    def accept(self, visitor: IASTVisitor) -> Any:
        return visitor.visit_project(self)


class PageNode(ASTNode):
    """Node representing a page/section."""

    def accept(self, visitor: IASTVisitor) -> Any:
        return visitor.visit_page(self)


class ComponentNode(ASTNode):
    """Node representing a UI/component element."""

    def __init__(self, name: str, component_type: str):
        super().__init__(name)
        self.component_type = component_type

    def accept(self, visitor: IASTVisitor) -> Any:
        return visitor.visit_component(self)


class EntityNode(ASTNode):
    """Node representing a data entity."""

    def __init__(self, name: str):
        super().__init__(name)
        self.attributes: list[dict[str, str]] = []

    def add_attribute(self, attr_name: str, attr_type: str) -> None:
        self.attributes.append({"name": attr_name, "type": attr_type})

    def accept(self, visitor: IASTVisitor) -> Any:
        return visitor.visit_entity(self)


class InfraNode(ASTNode):
    """Node representing infrastructure resource."""

    def __init__(self, name: str, infra_type: str):
        super().__init__(name)
        self.infra_type = infra_type
        self.resources: list[dict[str, Any]] = []

    def add_resource(self, resource: dict[str, Any]) -> None:
        self.resources.append(resource)

    def accept(self, visitor: IASTVisitor) -> Any:
        return visitor.visit_infra(self)
