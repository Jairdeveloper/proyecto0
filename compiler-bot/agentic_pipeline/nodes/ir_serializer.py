"""IR Serializer — Bridge pattern for JSON, YAML, DOT output."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from .ir_nodes import IRNode


# ============================================================================
# Serializer interface (Bridge Implementor)
# ============================================================================


class IRSerializer(ABC):
    """Abstract serializer — Bridge Implementor."""

    @abstractmethod
    def serialize(self, node: IRNode) -> str: ...

    @abstractmethod
    def mime_type(self) -> str: ...


# ============================================================================
# JSON Serializer
# ============================================================================


class JSONSerializer(IRSerializer):
    """Serializes IR to JSON."""

    def serialize(self, node: IRNode) -> str:
        data = self._to_dict(node)
        return json.dumps(data, indent=2, ensure_ascii=False)

    def mime_type(self) -> str:
        return "application/json"

    def _to_dict(self, node: IRNode) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": node.name,
            "type": type(node).__name__,
        }
        if hasattr(node, "component_type") and node.component_type:
            result["component_type"] = node.component_type
        if hasattr(node, "infra_type") and node.infra_type:
            result["infra_type"] = node.infra_type
        if hasattr(node, "attributes") and node.attributes:
            result["attributes"] = node.attributes
        if hasattr(node, "resources") and node.resources:
            result["resources"] = node.resources
        if hasattr(node, "methods") and node.methods:
            result["methods"] = node.methods
        if hasattr(node, "settings") and node.settings:
            result["settings"] = node.settings
        if node.children:
            result["children"] = [self._to_dict(c) for c in node.children]
        return result


# ============================================================================
# YAML Serializer
# ============================================================================


class YAMLSerializer(IRSerializer):
    """Serializes IR to YAML."""

    def serialize(self, node: IRNode) -> str:
        try:
            import yaml as pyyaml  # type: ignore[import-untyped]

            data = self._to_dict(node)
            return pyyaml.dump(data, default_flow_style=False, allow_unicode=True)
        except ImportError:
            return (
                "# yaml library not available; falling back to JSON\n"
                + JSONSerializer().serialize(node)
            )

    def mime_type(self) -> str:
        return "text/yaml"

    def _to_dict(self, node: IRNode) -> dict[str, Any]:
        ser = JSONSerializer()
        return ser._to_dict(node)


# ============================================================================
# DOT Serializer (Graphviz)
# ============================================================================


class DOTSerializer(IRSerializer):
    """Serializes IR to Graphviz DOT format."""

    def serialize(self, node: IRNode) -> str:
        lines: list[str] = ["digraph IR {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box, style=rounded];")
        self._render_node(node, lines, set())
        lines.append("}")
        return "\n".join(lines)

    def mime_type(self) -> str:
        return "text/vnd.graphviz"

    def _render_node(
        self,
        node: IRNode,
        lines: list[str],
        visited: set[str],
    ) -> None:
        node_id = id(node)
        if node_id in visited:
            return
        visited.add(node_id)

        label = node.name.replace('"', '\\"')
        node_type = type(node).__name__
        lines.append(f'  n{node_id} [label="{label}\\n({node_type})"];')

        for child in node.children:
            child_id = id(child)
            lines.append(f"  n{node_id} -> n{child_id};")
            self._render_node(child, lines, visited)


# ============================================================================
# Serializer factory
# ============================================================================


def get_serializer(fmt: str = "json") -> IRSerializer:
    if fmt == "yaml":
        return YAMLSerializer()
    if fmt == "dot":
        return DOTSerializer()
    return JSONSerializer()
