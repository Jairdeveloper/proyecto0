"""Tests for core/knowledge_graph.py."""

from pdca_sdlc.core.knowledge_graph import (
    Edge,
    EdgeType,
    KnowledgeGraph,
    Node,
    NodeType,
)


class TestKnowledgeGraph:
    def test_add_and_get_node(self) -> None:
        kg = KnowledgeGraph()
        node = Node(id="n1", node_type=NodeType.goal, properties={"desc": "Build app"})
        kg.add_node(node)
        retrieved = kg.get_node("n1")
        assert retrieved is not None
        assert retrieved.id == "n1"
        assert retrieved.node_type == NodeType.goal
        assert retrieved.properties["desc"] == "Build app"

    def test_get_nonexistent_node(self) -> None:
        kg = KnowledgeGraph()
        assert kg.get_node("ghost") is None

    def test_update_node(self) -> None:
        kg = KnowledgeGraph()
        kg.add_node(Node(id="n1", node_type=NodeType.requirement, properties={"status": "new"}))
        assert kg.update_node("n1", properties={"status": "approved"})
        node = kg.get_node("n1")
        assert node is not None
        assert node.properties["status"] == "approved"

    def test_update_nonexistent_node(self) -> None:
        kg = KnowledgeGraph()
        assert not kg.update_node("ghost", properties={"x": 1})

    def test_remove_node(self) -> None:
        kg = KnowledgeGraph()
        kg.add_node(Node(id="n1", node_type=NodeType.task))
        assert kg.remove_node("n1")
        assert kg.get_node("n1") is None

    def test_add_and_query_edges(self) -> None:
        kg = KnowledgeGraph()
        kg.add_node(Node(id="req1", node_type=NodeType.requirement))
        kg.add_node(Node(id="mod1", node_type=NodeType.code_module))
        kg.add_edge(Edge(source_id="req1", target_id="mod1", edge_type=EdgeType.implements))
        outgoing = kg.get_outgoing("req1")
        assert len(outgoing) == 1
        assert outgoing[0].target_id == "mod1"
        assert outgoing[0].edge_type == EdgeType.implements
        incoming = kg.get_incoming("mod1")
        assert len(incoming) == 1
        assert incoming[0].source_id == "req1"

    def test_get_trace_bfs(self) -> None:
        kg = KnowledgeGraph()
        for nid in ("g1", "r1", "r2", "c1", "c2"):
            kg.add_node(Node(id=nid, node_type=NodeType.requirement))
        kg.add_edge(Edge("g1", "r1", EdgeType.satisfies))
        kg.add_edge(Edge("g1", "r2", EdgeType.satisfies))
        kg.add_edge(Edge("r1", "c1", EdgeType.implements))
        kg.add_edge(Edge("r2", "c2", EdgeType.implements))
        trace = kg.get_trace("g1")
        assert len(trace) == 5
        assert trace[0].id == "g1"

    def test_get_trace_filtered(self) -> None:
        kg = KnowledgeGraph()
        kg.add_node(Node(id="g1", node_type=NodeType.goal))
        kg.add_node(Node(id="r1", node_type=NodeType.requirement))
        kg.add_node(Node(id="c1", node_type=NodeType.code_module))
        kg.add_edge(Edge("g1", "r1", EdgeType.satisfies))
        kg.add_edge(Edge("r1", "c1", EdgeType.implements))
        trace = kg.get_trace("g1", edge_types={EdgeType.satisfies})
        assert len(trace) == 2
        assert {n.id for n in trace} == {"g1", "r1"}

    def test_get_trace_nonexistent(self) -> None:
        kg = KnowledgeGraph()
        assert kg.get_trace("ghost") == []

    def test_query_by_type(self) -> None:
        kg = KnowledgeGraph()
        kg.add_node(Node(id="g1", node_type=NodeType.goal))
        kg.add_node(Node(id="r1", node_type=NodeType.requirement))
        kg.add_node(Node(id="r2", node_type=NodeType.requirement))
        reqs = kg.query(node_type=NodeType.requirement)
        assert len(reqs) == 2

    def test_query_by_status(self) -> None:
        kg = KnowledgeGraph()
        kg.add_node(
            Node(id="r1", node_type=NodeType.requirement, properties={"status": "approved"})
        )
        kg.add_node(Node(id="r2", node_type=NodeType.requirement, properties={"status": "draft"}))
        approved = kg.query(node_type=NodeType.requirement, status="approved")
        assert len(approved) == 1
        assert approved[0].id == "r1"

    def test_query_by_properties(self) -> None:
        kg = KnowledgeGraph()
        kg.add_node(
            Node(
                id="r1",
                node_type=NodeType.requirement,
                properties={"priority": "high", "status": "approved"},
            )
        )
        kg.add_node(Node(id="r2", node_type=NodeType.requirement, properties={"priority": "low"}))
        high = kg.query(node_type=NodeType.requirement, priority="high")
        assert len(high) == 1
        assert high[0].id == "r1"

    def test_all_nodes(self) -> None:
        kg = KnowledgeGraph()
        kg.add_node(Node(id="a", node_type=NodeType.task))
        kg.add_node(Node(id="b", node_type=NodeType.task))
        nodes = list(kg.all_nodes())
        assert len(nodes) == 2

    def test_counts(self) -> None:
        kg = KnowledgeGraph()
        assert kg.node_count() == 0
        assert kg.edge_count() == 0
        kg.add_node(Node(id="n1", node_type=NodeType.task))
        kg.add_node(Node(id="n2", node_type=NodeType.task))
        kg.add_edge(Edge("n1", "n2", EdgeType.precedes))
        assert kg.node_count() == 2
        assert kg.edge_count() == 1

    def test_clear(self) -> None:
        kg = KnowledgeGraph()
        kg.add_node(Node(id="n1", node_type=NodeType.task))
        kg.clear()
        assert kg.node_count() == 0
