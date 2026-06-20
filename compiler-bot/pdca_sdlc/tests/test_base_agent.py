"""Tests for core/base_agent.py."""

import pytest

from pdca_sdlc.core.base_agent import AgentContext, BaseAgent
from pdca_sdlc.core.capability_registry import (
    CapabilityManifest,
    CapabilityRegistry,
)
from pdca_sdlc.core.event_bus import AsyncEventBus, Event
from pdca_sdlc.core.knowledge_graph import KnowledgeGraph, Node, NodeType


class _ConcreteAgent(BaseAgent):
    @property
    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest(
            agent_id="test-agent",
            agent_name="TestAgent",
            description="Agent for testing",
            iso_12207={"process": "test"},
            triggers=["test.topic"],
            output_events=["test.complete"],
        )

    async def handle_event(self, event: Event) -> None:
        self.last_event = event


class _FailingAgent(BaseAgent):
    @property
    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest(
            agent_id="failing-agent",
            agent_name="FailingAgent",
            description="Agent that fails on purpose",
            iso_12207={},
            triggers=["fail.topic"],
            output_events=["risk.identified"],
        )

    async def handle_event(self, event: Event) -> None:
        msg = "Intentional failure"
        raise ValueError(msg)


class TestBaseAgent:
    @pytest.fixture
    def context(self) -> AgentContext:
        return AgentContext(
            event_bus=AsyncEventBus(),
            knowledge_graph=KnowledgeGraph(),
            capability_registry=CapabilityRegistry(),
            agent_id="test-agent",
        )

    @pytest.fixture
    def agent(self, context: AgentContext) -> _ConcreteAgent:
        return _ConcreteAgent(context)

    async def test_start_registers_and_subscribes(self, agent: _ConcreteAgent) -> None:
        assert not agent.is_running
        await agent.start()
        assert agent.is_running
        assert agent.context.capability_registry.count() == 1
        assert agent.context.event_bus.has_subscribers("test.topic")

    async def test_stop_unsubscribes_and_disables(self, agent: _ConcreteAgent) -> None:
        await agent.start()
        await agent.stop()
        assert not agent.is_running
        assert not agent.context.event_bus.has_subscribers("test.topic")
        manifest = agent.context.capability_registry.get("test-agent")
        assert manifest is not None
        assert manifest.status == "disabled"

    async def test_handle_event_wrapper_calls_handle_event(
        self,
        agent: _ConcreteAgent,
    ) -> None:
        await agent.start()
        event = Event(topic="test.topic", source="test", project_id="p-01", data={})
        await agent._handle_event_wrapper("test.topic", event)
        assert agent.last_event is event
        await agent.stop()

    async def test_handle_event_wrapper_ignores_non_event(self, agent: _ConcreteAgent) -> None:
        await agent.start()
        await agent._handle_event_wrapper("test.topic", "not_an_event")
        assert not hasattr(agent, "last_event")
        await agent.stop()

    async def test_wrapper_catches_exception_and_emits_risk(
        self,
        context: AgentContext,
    ) -> None:
        agent = _FailingAgent(context)
        events: list[Event] = []

        async def collector(topic: str, data: object) -> None:
            if isinstance(data, Event):
                events.append(data)

        await context.event_bus.subscribe("risk.identified", collector)
        await agent.start()
        event = Event(topic="fail.topic", source="test", project_id="p-01", data={})
        await agent._handle_event_wrapper("fail.topic", event)
        assert len(events) == 1
        assert events[0].topic == "risk.identified"
        assert events[0].data["severity"] == "medium"
        await agent.stop()

    async def test_emit_creates_event(self, context: AgentContext) -> None:
        agent = _ConcreteAgent(context)
        received: list[Event] = []

        async def collector(topic: str, data: object) -> None:
            if isinstance(data, Event):
                received.append(data)

        await context.event_bus.subscribe("agent.test", collector)
        await agent.start()
        await agent.emit("agent.test", "p-01", {"msg": "hello"})
        assert len(received) == 1
        assert received[0].topic == "agent.test"
        assert received[0].source == "test-agent"
        assert received[0].project_id == "p-01"
        assert received[0].data == {"msg": "hello"}
        await agent.stop()

    async def test_graph_helpers(self, context: AgentContext) -> None:
        agent = _ConcreteAgent(context)
        node = Node(id="n1", node_type=NodeType.goal, properties={"status": "active"})
        agent.write_graph(node)
        retrieved = agent.read_graph("n1")
        assert retrieved is not None
        assert retrieved.id == "n1"
        results = agent.query_graph(node_type=NodeType.goal)
        assert len(results) == 1
        assert results[0].id == "n1"

    async def test_double_start_stop_safe(self, agent: _ConcreteAgent) -> None:
        await agent.start()
        await agent.start()
        assert agent.is_running
        await agent.stop()
        await agent.stop()
        assert not agent.is_running
