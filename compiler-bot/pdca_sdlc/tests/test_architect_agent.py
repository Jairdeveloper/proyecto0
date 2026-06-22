"""Tests for agents/architect_agent.py."""

from __future__ import annotations

import json
from typing import Any

import pytest

from pdca_sdlc.agents.architect_agent import ArchitectAgent
from pdca_sdlc.core.base_agent import AgentContext
from pdca_sdlc.core.capability_registry import CapabilityRegistry
from pdca_sdlc.core.event_bus import AsyncEventBus, Event
from pdca_sdlc.core.knowledge_graph import (
    EdgeType,
    KnowledgeGraph,
    Node,
    NodeType,
)
from pdca_sdlc.core.llm_client import LLMClient


class _FakeLLM(LLMClient):
    """LLM stub that returns a canned architecture response."""

    def __init__(self, components: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> None:
        super().__init__({"model": "mock"})
        self._canned_components = components
        self._canned_decisions = decisions

    def _mock_complete(self, prompt: str, max_tokens: int, response_format: str | None) -> str:
        return json.dumps(
            {
                "components": self._canned_components,
                "decisions": self._canned_decisions,
            },
        )


class _FailingLLM(LLMClient):
    """LLM stub that always raises an exception."""

    def _mock_complete(self, prompt: str, max_tokens: int, response_format: str | None) -> str:
        msg = "LLM unavailable"
        raise RuntimeError(msg)


class _CountingLLM(LLMClient):
    """LLM stub that returns a configurable number of components."""

    def __init__(self, component_count: int) -> None:
        super().__init__({"model": "mock"})
        self._component_count = component_count

    def _mock_complete(self, prompt: str, max_tokens: int, response_format: str | None) -> str:
        components = [
            {
                "name": f"Component{i}",
                "tech_stack": ["generic"],
                "interfaces": ["handle"],
                "implements_requirements": [f"r-{(i % 4) + 1:03d}"],
            }
            for i in range(1, self._component_count + 1)
        ]
        decisions = [
            {
                "title": f"ADR {i}",
                "context": f"Context for decision {i}",
                "decision": f"Decision {i}",
                "consequences": f"Consequences of {i}",
            }
            for i in range(1, 3)
        ]
        return json.dumps({"components": components, "decisions": decisions})


class TestArchitectAgent:
    @pytest.fixture
    def context(self) -> AgentContext:
        return AgentContext(
            event_bus=AsyncEventBus(),
            knowledge_graph=KnowledgeGraph(),
            capability_registry=CapabilityRegistry(),
            agent_id="architect",
        )

    @pytest.fixture
    def agent(self, context: AgentContext) -> ArchitectAgent:
        return ArchitectAgent(context)

    def _seed_goal(
        self,
        agent: ArchitectAgent,
        project_id: str,
        complexity: str,
    ) -> None:
        """Create a goal node with the given complexity."""
        agent.write_graph(
            Node(
                id=f"goal-{project_id}",
                node_type=NodeType.goal,
                properties={
                    "project_id": project_id,
                    "complexity": complexity,
                    "description": f"Project {project_id}",
                },
            ),
        )

    def _seed_requirements(
        self,
        agent: ArchitectAgent,
        requirement_ids: list[str],
    ) -> None:
        """Create requirement nodes with standard properties."""
        texts = [
            "Login con autenticacion OAuth2",
            "Dashboard con reportes en tiempo real",
            "Gestion de usuarios con roles",
            "API REST para integracion externa",
        ]
        for i, rid in enumerate(requirement_ids):
            text = texts[i] if i < len(texts) else f"Requirement {rid}"
            agent.write_graph(
                Node(
                    id=rid,
                    node_type=NodeType.requirement,
                    properties={
                        "id": rid,
                        "text": text,
                        "type": "functional",
                        "priority": "high",
                    },
                ),
            )

    # ── Tests ──────────────────────────────────────────────────────────

    async def test_fast_path_skip(
        self,
        agent: ArchitectAgent,
    ) -> None:
        """SIMPLE project: agent emits nothing (fast-path skip)."""
        self._seed_goal(agent, "p-simple", "simple")
        self._seed_requirements(agent, ["r-001", "r-002"])

        received: list[dict[str, object]] = []

        async def collector(topic: str, data: object) -> None:
            if isinstance(data, Event):
                received.append(data.data)

        await agent._ctx.event_bus.subscribe("architecture.proposed", collector)
        await agent.start()
        event = Event(
            topic="requirement.created",
            source="requirements-analyst",
            project_id="p-simple",
            data={"requirement_ids": ["r-001", "r-002"]},
        )
        await agent._handle_event_wrapper("requirement.created", event)
        assert len(received) == 0
        await agent.stop()

    async def test_fallback_flat(self, agent: ArchitectAgent) -> None:
        """LLM fails -> flat architecture generated deterministically."""
        failing_agent = ArchitectAgent(agent._ctx, llm_client=_FailingLLM())
        self._seed_goal(failing_agent, "p-fallback", "moderate")
        self._seed_requirements(failing_agent, ["r-001", "r-002", "r-003"])

        await failing_agent.start()
        event = Event(
            topic="requirement.created",
            source="requirements-analyst",
            project_id="p-fallback",
            data={"requirement_ids": ["r-001", "r-002", "r-003"]},
        )
        await failing_agent._handle_event_wrapper("requirement.created", event)

        components = failing_agent.query_graph(node_type=NodeType.component)
        # Flat: 1 component per requirement = 3
        assert len(components) == 3
        for comp in components:
            props = comp.properties
            assert "name" in props
            assert "tech_stack" in props
            assert "implements_requirements" in props
        await failing_agent.stop()

    async def test_component_generation(self, agent: ArchitectAgent) -> None:
        """4 requirements produce 2-3 components with valid names."""
        canned = _FakeLLM(
            components=[
                {
                    "name": "AuthComponent",
                    "tech_stack": ["nestjs", "passport"],
                    "interfaces": ["login", "register"],
                    "implements_requirements": ["r-001"],
                },
                {
                    "name": "DashboardComponent",
                    "tech_stack": ["react", "websocket"],
                    "interfaces": ["reports", "realtime"],
                    "implements_requirements": ["r-002", "r-004"],
                },
                {
                    "name": "UserManagementComponent",
                    "tech_stack": ["nestjs", "prisma"],
                    "interfaces": ["crud", "roles"],
                    "implements_requirements": ["r-003"],
                },
            ],
            decisions=[
                {
                    "title": "Use modular architecture",
                    "context": "System has 4 related requirements",
                    "decision": "Separate auth, dashboard, and user management",
                    "consequences": "Clear separation of concerns",
                },
            ],
        )
        llm_agent = ArchitectAgent(agent._ctx, llm_client=canned)
        self._seed_goal(llm_agent, "p-gen", "moderate")
        self._seed_requirements(llm_agent, ["r-001", "r-002", "r-003", "r-004"])

        await llm_agent.start()
        event = Event(
            topic="requirement.created",
            source="requirements-analyst",
            project_id="p-gen",
            data={
                "requirement_ids": [
                    "r-001",
                    "r-002",
                    "r-003",
                    "r-004",
                ],
            },
        )
        await llm_agent._handle_event_wrapper("requirement.created", event)

        components = llm_agent.query_graph(node_type=NodeType.component)
        assert 2 <= len(components) <= 3
        for comp in components:
            assert comp.properties["name"]
            assert len(comp.properties.get("implements_requirements", [])) >= 1
        await llm_agent.stop()

    async def test_traceability_edges(self, agent: ArchitectAgent) -> None:
        """Each component has an IMPLEMENTS edge to at least one requirement."""
        self._seed_goal(agent, "p-trace", "moderate")
        self._seed_requirements(agent, ["r-001", "r-002"])

        await agent.start()
        event = Event(
            topic="requirement.created",
            source="requirements-analyst",
            project_id="p-trace",
            data={"requirement_ids": ["r-001", "r-002"]},
        )
        await agent._handle_event_wrapper("requirement.created", event)

        components = agent.query_graph(node_type=NodeType.component)
        for comp in components:
            edges = agent._ctx.knowledge_graph.get_outgoing(comp.id)
            implements_edges = [e for e in edges if e.edge_type == EdgeType.implements]
            assert len(implements_edges) >= 1
            # Each edge points to an existing requirement
            for edge in implements_edges:
                assert agent.read_graph(edge.target_id) is not None
        await agent.stop()

    async def test_adr_creation(self, agent: ArchitectAgent) -> None:
        """Each ADR has non-empty title, context, decision, consequences."""
        self._seed_goal(agent, "p-adr", "moderate")
        self._seed_requirements(agent, ["r-001", "r-002"])

        await agent.start()
        event = Event(
            topic="requirement.created",
            source="requirements-analyst",
            project_id="p-adr",
            data={"requirement_ids": ["r-001", "r-002"]},
        )
        await agent._handle_event_wrapper("requirement.created", event)

        decisions = agent.query_graph(node_type=NodeType.architecture_decision)
        assert len(decisions) >= 1
        for adr in decisions:
            props = adr.properties
            assert props.get("title")
            assert props.get("context")
            assert props.get("decision")
            assert props.get("consequences")
        await agent.stop()

    async def test_complex_project_architecture(
        self,
        agent: ArchitectAgent,
    ) -> None:
        """COMPLEX project produces more components than MODERATE."""
        moderate_llm = _CountingLLM(component_count=2)
        moderate_agent = ArchitectAgent(agent._ctx, llm_client=moderate_llm)

        complex_llm = _CountingLLM(component_count=4)
        complex_agent = ArchitectAgent(agent._ctx, llm_client=complex_llm)

        # Moderate project
        self._seed_goal(moderate_agent, "p-moderate", "moderate")
        self._seed_requirements(moderate_agent, ["r-001", "r-002", "r-003", "r-004"])
        await moderate_agent.start()
        event = Event(
            topic="requirement.created",
            source="requirements-analyst",
            project_id="p-moderate",
            data={"requirement_ids": ["r-001", "r-002", "r-003", "r-004"]},
        )
        await moderate_agent._handle_event_wrapper("requirement.created", event)

        moderate_count = len(moderate_agent.query_graph(node_type=NodeType.component))

        # Complex project
        self._seed_goal(complex_agent, "p-complex", "complex")
        self._seed_requirements(complex_agent, ["r-001", "r-002", "r-003", "r-004"])
        await complex_agent.start()
        event2 = Event(
            topic="requirement.created",
            source="requirements-analyst",
            project_id="p-complex",
            data={"requirement_ids": ["r-001", "r-002", "r-003", "r-004"]},
        )
        await complex_agent._handle_event_wrapper("requirement.created", event2)

        complex_count = len(complex_agent.query_graph(node_type=NodeType.component))

        assert complex_count > moderate_count
        await moderate_agent.stop()
        await complex_agent.stop()

    async def test_no_duplicate_components(self, agent: ArchitectAgent) -> None:
        """Same requirement does not generate 2 identical components."""
        self._seed_goal(agent, "p-dedup", "moderate")
        # Two requirements with the same text -> fallback derives same name -> dedup
        agent.write_graph(
            Node(
                id="r-001",
                node_type=NodeType.requirement,
                properties={
                    "id": "r-001",
                    "text": "Login con autenticacion",
                    "type": "functional",
                    "priority": "high",
                },
            ),
        )
        agent.write_graph(
            Node(
                id="r-002",
                node_type=NodeType.requirement,
                properties={
                    "id": "r-002",
                    "text": "Login con autenticacion",
                    "type": "functional",
                    "priority": "high",
                },
            ),
        )

        await agent.start()
        event = Event(
            topic="requirement.created",
            source="requirements-analyst",
            project_id="p-dedup",
            data={"requirement_ids": ["r-001", "r-002"]},
        )
        await agent._handle_event_wrapper("requirement.created", event)

        components = agent.query_graph(node_type=NodeType.component)
        # Generated with fallback -> _derive_component_name sees same text
        # and dedup logic renames: "Login" then "Login2"
        assert len(components) == 2
        names = [comp.properties["name"] for comp in components]
        assert len(names) == len(set(names)), f"Duplicate names found: {names}"
        await agent.stop()

    async def test_architecture_proposed_event(
        self,
        agent: ArchitectAgent,
    ) -> None:
        """Architecture.proposed event contains component_ids and decision_ids."""
        self._seed_goal(agent, "p-event", "moderate")
        self._seed_requirements(agent, ["r-001", "r-002"])

        received: list[dict[str, object]] = []

        async def collector(topic: str, data: object) -> None:
            if isinstance(data, Event):
                received.append(data.data)

        await agent._ctx.event_bus.subscribe("architecture.proposed", collector)
        await agent.start()
        event = Event(
            topic="requirement.created",
            source="requirements-analyst",
            project_id="p-event",
            data={"requirement_ids": ["r-001", "r-002"]},
        )
        await agent._handle_event_wrapper("requirement.created", event)

        assert len(received) == 1
        payload = received[0]
        assert "component_ids" in payload
        assert "decision_ids" in payload
        assert "components" in payload
        assert "requirement_ids" in payload
        assert len(payload["component_ids"]) >= 1
        assert len(payload["decision_ids"]) >= 1
        await agent.stop()
