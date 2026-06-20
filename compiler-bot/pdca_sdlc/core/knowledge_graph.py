"""Knowledge Graph — NetworkX wrapper for traceability and querying.

Stores nodes (requirements, components, code modules, etc.) and edges
(traceability links) using NetworkX as the backend (Fase 1). Migrates
to Neo4j in Fase 3.
"""

from __future__ import annotations

import time
from collections.abc import Generator
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import networkx as nx


class NodeType(StrEnum):
    requirement = "requirement"
    component = "component"
    code_module = "code_module"
    architecture_decision = "architecture_decision"
    goal = "goal"
    risk = "risk"
    artifact = "artifact"
    task = "task"
    milestone = "milestone"


class EdgeType(StrEnum):
    satisfies = "satisfies"
    implements = "implements"
    verifies = "verifies"
    affects = "affects"
    depends_on = "depends_on"
    generates = "generates"
    documents = "documents"
    precedes = "precedes"


@dataclass
class Node:
    id: str
    node_type: NodeType
    properties: dict[str, Any] = field(default_factory=dict)
    created_by: str = "system"
    created_at: float = field(default_factory=time.time)


@dataclass
class Edge:
    source_id: str
    target_id: str
    edge_type: EdgeType
    properties: dict[str, Any] = field(default_factory=dict)


class KnowledgeGraph:
    """In-memory knowledge graph backed by NetworkX.

    Provides CRUD for nodes and edges, BFS traceability queries,
    and filtering by type / status / properties.
    """

    def __init__(self) -> None:
        import networkx as nx

        self._graph: nx.DiGraph = nx.DiGraph()

    def add_node(self, node: Node) -> None:
        self._graph.add_node(
            node.id,
            node_type=node.node_type,
            properties=node.properties,
            created_by=node.created_by,
            created_at=node.created_at,
        )

    def get_node(self, node_id: str) -> Node | None:
        if node_id not in self._graph:
            return None
        data = self._graph.nodes[node_id]
        return Node(
            id=node_id,
            node_type=NodeType(data["node_type"]),
            properties=dict(data.get("properties", {})),
            created_by=data.get("created_by", "system"),
            created_at=data.get("created_at", 0.0),
        )

    def update_node(self, node_id: str, **updates: Any) -> bool:
        if node_id not in self._graph:
            return False
        for key, value in updates.items():
            if key == "node_type":
                self._graph.nodes[node_id]["node_type"] = NodeType(value).value
            elif key == "properties":
                self._graph.nodes[node_id]["properties"].update(value)
            else:
                self._graph.nodes[node_id][key] = value
        return True

    def remove_node(self, node_id: str) -> bool:
        if node_id not in self._graph:
            return False
        self._graph.remove_node(node_id)
        return True

    def add_edge(self, edge: Edge) -> None:
        self._graph.add_edge(
            edge.source_id,
            edge.target_id,
            edge_type=edge.edge_type,
            properties=edge.properties,
        )

    def get_outgoing(self, node_id: str) -> list[Edge]:
        if node_id not in self._graph:
            return []
        result: list[Edge] = []
        for _, target, data in self._graph.out_edges(node_id, data=True):
            result.append(
                Edge(
                    source_id=node_id,
                    target_id=target,
                    edge_type=EdgeType(data["edge_type"]),
                    properties=dict(data.get("properties", {})),
                )
            )
        return result

    def get_incoming(self, node_id: str) -> list[Edge]:
        if node_id not in self._graph:
            return []
        result: list[Edge] = []
        for source, _, data in self._graph.in_edges(node_id, data=True):
            result.append(
                Edge(
                    source_id=source,
                    target_id=node_id,
                    edge_type=EdgeType(data["edge_type"]),
                    properties=dict(data.get("properties", {})),
                )
            )
        return result

    def get_trace(self, start_id: str, edge_types: set[EdgeType] | None = None) -> list[Node]:
        """BFS traversal from start_id following edges.

        Args:
            start_id: Starting node id.
            edge_types: Optional set of EdgeTypes to follow.
                        If None, follows all edges.

        Returns:
            List of reachable Node objects in BFS order.
        """
        if start_id not in self._graph:
            return []
        visited: set[str] = set()
        result: list[Node] = []
        queue: list[str] = [start_id]
        visited.add(start_id)
        while queue:
            current = queue.pop(0)
            node = self.get_node(current)
            if node is not None:
                result.append(node)
            for _, target, data in self._graph.out_edges(current, data=True):
                if target in visited:
                    continue
                if edge_types is not None:
                    edge_type = EdgeType(data["edge_type"])
                    if edge_type not in edge_types:
                        continue
                visited.add(target)
                queue.append(target)
        return result

    def query(
        self,
        node_type: NodeType | None = None,
        status: str | None = None,
        **properties: Any,
    ) -> list[Node]:
        """Query nodes by type, status, and/or properties.

        All criteria are AND-combined. Property filters check exact match.
        """
        result: list[Node] = []
        for node_id, data in self._graph.nodes(data=True):
            if node_type is not None and data.get("node_type") != node_type.value:
                continue
            props = data.get("properties", {})
            if status is not None and props.get("status") != status:
                continue
            if properties:
                match = all(props.get(key) == value for key, value in properties.items())
                if not match:
                    continue
            result.append(
                Node(
                    id=node_id,
                    node_type=NodeType(data["node_type"]),
                    properties=dict(props),
                    created_by=data.get("created_by", "system"),
                    created_at=data.get("created_at", 0.0),
                )
            )
        return result

    def all_nodes(self) -> Generator[Node, None, None]:
        for node_id in self._graph.nodes:
            node = self.get_node(node_id)
            if node is not None:
                yield node

    def node_count(self) -> int:
        return self._graph.number_of_nodes()

    def edge_count(self) -> int:
        return self._graph.number_of_edges()

    def clear(self) -> None:
        self._graph.clear()
