"""AST nodes with Composite pattern for parser output."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


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
    def evaluate(self) -> dict[str, Any]: ...

    @abstractmethod
    def validate(self) -> list[str]: ...

    @abstractmethod
    def to_ir(self) -> dict[str, Any]: ...


class ProjectNode(ASTNode):
    """Root node representing a project."""

    def evaluate(self) -> dict[str, Any]:
        return {"type": "project", "pages": [c.evaluate() for c in self.children]}

    def validate(self) -> list[str]:
        errors: list[str] = []
        for c in self.children:
            errors.extend(c.validate())
        return errors

    def to_ir(self) -> dict[str, Any]:
        return {"node_type": "project", "children": [c.to_ir() for c in self.children]}


class PageNode(ASTNode):
    """Node representing a page/section."""

    def evaluate(self) -> dict[str, Any]:
        return {
            "type": "page",
            "name": self.name,
            "components": [c.evaluate() for c in self.children],
        }

    def validate(self) -> list[str]:
        if not self.children:
            return [f"Page '{self.name}' has no components"]
        errors: list[str] = []
        for c in self.children:
            errors.extend(c.validate())
        return errors

    def to_ir(self) -> dict[str, Any]:
        return {
            "node_type": "page",
            "name": self.name,
            "children": [c.to_ir() for c in self.children],
        }


class ComponentNode(ASTNode):
    """Node representing a UI/component element."""

    def __init__(self, name: str, component_type: str):
        super().__init__(name)
        self.component_type = component_type

    def evaluate(self) -> dict[str, Any]:
        return {
            "type": "component",
            "name": self.name,
            "component_type": self.component_type,
        }

    def validate(self) -> list[str]:
        return []

    def to_ir(self) -> dict[str, Any]:
        return {
            "node_type": "component",
            "name": self.name,
            "component_type": self.component_type,
        }


class EntityNode(ASTNode):
    """Node representing a data entity."""

    def __init__(self, name: str):
        super().__init__(name)
        self.attributes: list[dict[str, str]] = []

    def add_attribute(self, attr_name: str, attr_type: str) -> None:
        self.attributes.append({"name": attr_name, "type": attr_type})

    def evaluate(self) -> dict[str, Any]:
        return {
            "type": "entity",
            "name": self.name,
            "attributes": self.attributes,
        }

    def validate(self) -> list[str]:
        if not self.attributes:
            return [f"Entity '{self.name}' has no attributes"]
        return []

    def to_ir(self) -> dict[str, Any]:
        return {
            "node_type": "entity",
            "name": self.name,
            "attributes": self.attributes,
        }


class InfraNode(ASTNode):
    """Node representing infrastructure resource."""

    def __init__(self, name: str, infra_type: str):
        super().__init__(name)
        self.infra_type = infra_type
        self.resources: list[dict[str, Any]] = []

    def add_resource(self, resource: dict[str, Any]) -> None:
        self.resources.append(resource)

    def evaluate(self) -> dict[str, Any]:
        return {
            "type": "infra",
            "name": self.name,
            "infra_type": self.infra_type,
            "resources": self.resources,
        }

    def validate(self) -> list[str]:
        return []

    def to_ir(self) -> dict[str, Any]:
        return {
            "node_type": "infra",
            "name": self.name,
            "infra_type": self.infra_type,
            "resources": self.resources,
        }
