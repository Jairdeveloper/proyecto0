"""Tests for agents/requirements_analyst.py."""

import pytest

from pdca_sdlc.agents.requirements_analyst import RequirementsAnalystAgent
from pdca_sdlc.core.base_agent import AgentContext
from pdca_sdlc.core.capability_registry import CapabilityRegistry
from pdca_sdlc.core.event_bus import AsyncEventBus, Event
from pdca_sdlc.core.knowledge_graph import KnowledgeGraph, Node, NodeType
from pdca_sdlc.core.llm_client import LLMClient


class TestRequirementsAnalystAgent:
    @pytest.fixture
    def context(self) -> AgentContext:
        return AgentContext(
            event_bus=AsyncEventBus(),
            knowledge_graph=KnowledgeGraph(),
            capability_registry=CapabilityRegistry(),
            agent_id="requirements-analyst",
        )

    @pytest.fixture
    def agent(self, context: AgentContext) -> RequirementsAnalystAgent:
        return RequirementsAnalystAgent(
            context,
            llm_client=LLMClient({"model": "mock"}),
        )

    def _seed_goal(
        self, agent: RequirementsAnalystAgent, project_id: str, description: str
    ) -> None:
        agent.write_graph(
            Node(
                id=f"goal-{project_id}",
                node_type=NodeType.goal,
                properties={"description": description},
            ),
        )

    def test_read_project_description(self, agent: RequirementsAnalystAgent) -> None:
        self._seed_goal(agent, "p-01", "Crear login con Google")
        desc = agent._read_project_description("p-01")
        assert desc == "Crear login con Google"

    def test_read_project_description_missing(self, agent: RequirementsAnalystAgent) -> None:
        assert agent._read_project_description("ghost") == ""

    def test_fallback_decompose_returns_requirements(self, agent: RequirementsAnalystAgent) -> None:
        reqs = agent._fallback_decompose("Login con Google. Dashboard de usuarios.")
        assert len(reqs) >= 1
        for r in reqs:
            assert r.text
            assert r.type in ("functional", "business", "user", "non_functional")
            assert r.priority in ("high", "medium", "low")
            assert len(r.acceptance_criteria) >= 1

    def test_fallback_creates_multiple_requirements(self, agent: RequirementsAnalystAgent) -> None:
        reqs = agent._fallback_decompose("Autenticacion. Pagos. Reportes. Notificaciones.")
        assert 2 <= len(reqs) <= 6

    def test_guess_type_functional(self, agent: RequirementsAnalystAgent) -> None:
        assert agent._guess_type("Crear login con Google") == "functional"

    def test_guess_type_non_functional(self, agent: RequirementsAnalystAgent) -> None:
        assert agent._guess_type("El sistema debe ser seguro") == "non_functional"

    def test_guess_priority_high(self, agent: RequirementsAnalystAgent) -> None:
        assert agent._guess_priority("Autenticacion de usuarios") == "high"

    def test_guess_priority_low(self, agent: RequirementsAnalystAgent) -> None:
        assert agent._guess_priority("Mejora cosmética") == "low"

    async def test_handle_event_writes_requirement_nodes(
        self,
        agent: RequirementsAnalystAgent,
    ) -> None:
        self._seed_goal(agent, "p-01", "Login con Google")
        await agent.start()
        event = Event(
            topic="adaptation.complete",
            source="adaptation-agent",
            project_id="p-01",
            data={"complexity": "simple"},
        )
        await agent._handle_event_wrapper("adaptation.complete", event)
        reqs = agent.query_graph(node_type=NodeType.requirement)
        assert len(reqs) >= 1
        for n in reqs:
            assert "text" in n.properties
            assert "type" in n.properties
        await agent.stop()

    async def test_handle_event_emits_requirement_created(
        self,
        agent: RequirementsAnalystAgent,
    ) -> None:
        self._seed_goal(agent, "p-01", "Login con Google")
        received: list[dict[str, object]] = []

        async def collector(topic: str, data: object) -> None:
            if isinstance(data, Event):
                received.append(data.data)

        await agent._ctx.event_bus.subscribe("requirement.created", collector)
        await agent.start()
        event = Event(
            topic="adaptation.complete",
            source="adaptation-agent",
            project_id="p-01",
            data={"complexity": "simple"},
        )
        await agent._handle_event_wrapper("adaptation.complete", event)
        assert len(received) == 1
        assert received[0]["count"] >= 1
        assert len(received[0]["requirement_ids"]) == received[0]["count"]
        await agent.stop()

    async def test_empty_description_does_nothing(self, agent: RequirementsAnalystAgent) -> None:
        self._seed_goal(agent, "p-01", "")
        await agent.start()
        event = Event(
            topic="adaptation.complete",
            source="adaptation-agent",
            project_id="p-01",
            data={},
        )
        await agent._handle_event_wrapper("adaptation.complete", event)
        reqs = agent.query_graph(node_type=NodeType.requirement)
        assert len(reqs) == 0
        await agent.stop()

    async def test_missing_goal_does_nothing(self, agent: RequirementsAnalystAgent) -> None:
        await agent.start()
        event = Event(
            topic="adaptation.complete",
            source="adaptation-agent",
            project_id="no-goal",
            data={},
        )
        await agent._handle_event_wrapper("adaptation.complete", event)
        reqs = agent.query_graph(node_type=NodeType.requirement)
        assert len(reqs) == 0
        await agent.stop()
