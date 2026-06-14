"""IR Builder — constructs IRNode tree from semantic analyzer output."""

from __future__ import annotations

import logging
from graphlib import TopologicalSorter
from typing import Any

from .ir_nodes import (
    IRAPI,
    IRComponent,
    IRConfig,
    IREntity,
    IRInfra,
    IRNode,
    IRPage,
    IRProject,
)

logger = logging.getLogger(__name__)


# ============================================================================
# DependencyGraph — topological sort for planner
# ============================================================================


class DependencyGraph:
    """Dependency graph with cycle detection and topological sort."""

    def __init__(self) -> None:
        self._nodes: dict[str, IRNode] = {}
        self._edges: dict[str, set[str]] = {}

    def add_node(self, node: IRNode) -> None:
        self._nodes[node.name] = node
        if node.name not in self._edges:
            self._edges[node.name] = set()

    def add_dependency(self, node_name: str, depends_on: str) -> None:
        if node_name not in self._edges:
            self._edges[node_name] = set()
        self._edges[node_name].add(depends_on)

    def resolve(self) -> list[str]:
        try:
            sorter = TopologicalSorter(self._edges)
            return list(sorter.static_order())
        except ValueError as e:
            logger.error("Cycle detected in dependency graph: %s", e)
            return []

    def has_cycle(self) -> bool:
        try:
            list(TopologicalSorter(self._edges).static_order())
            return False
        except ValueError as e:
            logger.debug("has_cycle caught: %s", e)
            return True

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.has_cycle():
            errors.append("Dependency graph contains a cycle")
        for name, deps in self._edges.items():
            for dep in deps:
                if dep not in self._nodes:
                    errors.append(f"Node '{name}' depends on unknown node '{dep}'")
        return errors


# ============================================================================
# IRBuilder
# ============================================================================


class IRBuilder:
    """Builds IRNode tree from the semantic analyzer output dict."""

    def __init__(self) -> None:
        self._project: IRProject | None = None
        self._config: IRConfig | None = None
        self._deps = DependencyGraph()

    @property
    def root(self) -> IRNode | None:
        return self._project

    @property
    def dep_graph(self) -> DependencyGraph:
        return self._deps

    def build(self, ir_dict: dict[str, Any]) -> IRNode:
        self._project = IRProject("project")
        children = ir_dict.get("children", [])

        for child in children:
            node_type = child.get("node_type", "")
            node = self._build_node(child, node_type)
            if node is not None:
                self._project.add(node)
                self._deps.add_node(node)

        return self._project

    def _build_node(
        self,
        data: dict[str, Any],
        node_type: str,
    ) -> IRNode | None:
        name = data.get("name", "unnamed")

        if node_type == "page":
            return self._build_page(data, name)
        if node_type == "component":
            comp_type = data.get("component_type", "component")
            return IRComponent(name, comp_type)
        if node_type == "entity":
            attrs = data.get("attributes", [])
            ent = IREntity(name, attrs)
            # Auto-register dependency: page using this entity
            return ent
        if node_type == "infra":
            infra_type = data.get("infra_type", "resource")
            resources = data.get("resources", [])
            return IRInfra(name, infra_type, resources)
        if node_type == "api":
            methods = data.get("methods", ["GET"])
            return IRAPI(name, methods)
        if node_type == "config":
            settings = data.get("settings", {})
            self._config = IRConfig(name, settings)
            return self._config

        logger.warning("Unknown IR node type: %s", node_type)
        return None

    def _build_page(
        self,
        data: dict[str, Any],
        name: str,
    ) -> IRPage:
        page = IRPage(name)
        for child in data.get("children", []):
            child_node = self._build_node(child, child.get("node_type", ""))
            if child_node is not None:
                page.add(child_node)
                self._deps.add_node(child_node)
                self._deps.add_dependency(name, child_node.name)
        return page

    def build_with_config(
        self,
        ir_dict: dict[str, Any],
        config_settings: dict[str, Any] | None = None,
    ) -> IRNode:
        root = self.build(ir_dict)
        if config_settings:
            cfg = IRConfig("config", config_settings)
            self._config = cfg
            self._project.add(cfg)
            self._deps.add_node(cfg)
        return root

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self._project is not None:
            errors.extend(self._project.validate())
        errors.extend(self._deps.validate())
        return [e for e in errors if e]
