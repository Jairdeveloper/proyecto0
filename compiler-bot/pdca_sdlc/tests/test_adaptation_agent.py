"""Tests for agents/adaptation_agent.py."""

import pytest

from pdca_sdlc.agents.adaptation_agent import AdaptationAgent
from pdca_sdlc.core.base_agent import AgentContext
from pdca_sdlc.core.capability_registry import CapabilityRegistry
from pdca_sdlc.core.event_bus import AsyncEventBus, Event
from pdca_sdlc.core.knowledge_graph import KnowledgeGraph
from pdca_sdlc.core.llm_client import LLMClient


class TestAdaptationAgent:
    @pytest.fixture
    def context(self) -> AgentContext:
        return AgentContext(
            event_bus=AsyncEventBus(),
            knowledge_graph=KnowledgeGraph(),
            capability_registry=CapabilityRegistry(),
            agent_id="adaptation-agent",
        )

    @pytest.fixture
    def agent(self, context: AgentContext) -> AdaptationAgent:
        return AdaptationAgent(context, llm_client=LLMClient({"model": "mock"}))

    def test_fallback_classifies_simple(self) -> None:
        agent = AdaptationAgent(
            AgentContext(
                event_bus=AsyncEventBus(),
                knowledge_graph=KnowledgeGraph(),
                capability_registry=CapabilityRegistry(),
                agent_id="test",
            ),
        )
        assert agent._fallback_classify("CRUD de productos") == "simple"
        assert agent._fallback_classify("Listar usuarios con filtros") == "simple"

    def test_fallback_classifies_moderate(self) -> None:
        agent = AdaptationAgent(
            AgentContext(
                event_bus=AsyncEventBus(),
                knowledge_graph=KnowledgeGraph(),
                capability_registry=CapabilityRegistry(),
                agent_id="test",
            ),
        )
        assert agent._fallback_classify("API REST con autenticacion JWT") == "moderate"
        assert agent._fallback_classify("Dashboard con roles y permisos") == "moderate"

    def test_fallback_classifies_complex(self) -> None:
        agent = AdaptationAgent(
            AgentContext(
                event_bus=AsyncEventBus(),
                knowledge_graph=KnowledgeGraph(),
                capability_registry=CapabilityRegistry(),
                agent_id="test",
            ),
        )
        desc = "Sistema multi-tenant con OAuth2 y microservicios"
        assert agent._fallback_classify(desc) == "complex"

    def test_select_template_simple(self) -> None:
        agent = AdaptationAgent(
            AgentContext(
                event_bus=AsyncEventBus(),
                knowledge_graph=KnowledgeGraph(),
                capability_registry=CapabilityRegistry(),
                agent_id="test",
            ),
        )
        template = agent._select_template("simple")
        assert template["lifecycle"] == "fast_track"
        assert len(template["activities"]) == 3

    def test_select_template_complex(self) -> None:
        agent = AdaptationAgent(
            AgentContext(
                event_bus=AsyncEventBus(),
                knowledge_graph=KnowledgeGraph(),
                capability_registry=CapabilityRegistry(),
                agent_id="test",
            ),
        )
        template = agent._select_template("complex")
        assert template["lifecycle"] == "agile"
        assert len(template["activities"]) == 9

    def test_estimate_effort(self) -> None:
        effort = AdaptationAgent._estimate_effort({"activities": ["a", "b", "c"]})
        assert effort["activity_count"] == 3
        assert effort["estimated_hours"] == 24
        assert effort["estimated_days"] == 4

    async def test_handle_event_writes_goal_node(self, agent: AdaptationAgent) -> None:
        await agent.start()
        event = Event(
            topic="project.initialized",
            source="cli",
            project_id="p-01",
            data={"description": "CRUD de productos"},
        )
        await agent._handle_event_wrapper("project.initialized", event)
        node = agent.read_graph("goal-p-01")
        assert node is not None
        assert node.node_type.value == "goal"
        assert node.properties["complexity"] == "simple"
        await agent.stop()

    async def test_handle_event_emits_expected_events(
        self,
        agent: AdaptationAgent,
    ) -> None:
        received: list[str] = []

        async def collector(topic: str, data: object) -> None:
            received.append(topic)

        await agent._ctx.event_bus.subscribe("adaptation.complete", collector)
        await agent._ctx.event_bus.subscribe("complexity.classified", collector)
        await agent._ctx.event_bus.subscribe("lifecycle.proposed", collector)
        await agent.start()
        event = Event(
            topic="project.initialized",
            source="cli",
            project_id="p-01",
            data={"description": "CRUD"},
        )
        await agent._handle_event_wrapper("project.initialized", event)
        assert "complexity.classified" in received
        assert "lifecycle.proposed" in received
        assert "adaptation.complete" in received
        await agent.stop()

    async def test_manifest_has_correct_triggers(self, agent: AdaptationAgent) -> None:
        assert "project.initialized" in agent.manifest.triggers

    async def test_empty_description_does_nothing(self, agent: AdaptationAgent) -> None:
        await agent.start()
        event = Event(
            topic="project.initialized",
            source="cli",
            project_id="p-01",
            data={"description": ""},
        )
        await agent._handle_event_wrapper("project.initialized", event)
        assert agent.read_graph("goal-p-01") is None
        await agent.stop()
