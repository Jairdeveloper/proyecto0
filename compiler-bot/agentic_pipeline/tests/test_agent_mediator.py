"""Tests for Agent Mediator pattern."""

from agentic_pipeline.agents.agent_mediator import (
    AgentMediator,
    AgentMessage,
    ExecutionResult,
    IAgentMediator,
    PerceptionResult,
    ReasoningResult,
    ValidationResult,
)


class _MockAgent:
    name: str = ""
    subscriptions: list[str] = []
    received: list[AgentMessage] = []

    def __init__(self, name: str, subscriptions: list[str] | None = None):
        self.name = name
        self.subscriptions = subscriptions or []
        self.received = []

    def on_message(self, msg: AgentMessage) -> None:
        self.received.append(msg)


class TestAgentMediator:
    def test_register_agent(self):
        m = AgentMediator()
        agent = _MockAgent("test_agent", ["topic.a"])
        m.register(agent)
        assert "test_agent" in m._agents

    def test_send_message(self):
        m = AgentMediator()
        agent = _MockAgent("receiver", ["topic.a"])
        m.register(agent)
        msg = AgentMessage(sender="sender", topic="topic.a", payload={})
        m.send(msg)
        assert len(agent.received) == 1
        assert agent.received[0].topic == "topic.a"

    def test_routing_by_topic(self):
        m = AgentMediator()
        a1 = _MockAgent("agent1", ["topic.a"])
        a2 = _MockAgent("agent2", ["topic.b"])
        m.register(a1)
        m.register(a2)
        m.send(AgentMessage(sender="s", topic="topic.a", payload={}))
        assert len(a1.received) == 1
        assert len(a2.received) == 0

    def test_typed_message_payload(self):
        payload = PerceptionResult(
            raw="crea modulo",
            intent={"intent": "CREATE"},
            entities=["modulo"],
            slots={},
            confidence=0.95,
        )
        msg = AgentMessage(
            sender="perception", topic="perception.completed", payload=payload
        )
        assert isinstance(msg.payload, PerceptionResult)
        assert msg.payload.raw == "crea modulo"
        assert msg.payload.confidence == 0.95

    def test_on_message_called(self):
        m = AgentMediator()
        agent = _MockAgent("receiver", ["test.topic"])
        m.register(agent)
        m.send(AgentMessage(sender="s", topic="test.topic", payload={"key": "val"}))
        assert len(agent.received) == 1

    def test_correlation_id_propagated(self):
        m = AgentMediator()
        agent = _MockAgent("receiver", ["test.topic"])
        m.register(agent)
        m.send(
            AgentMessage(
                sender="s",
                topic="test.topic",
                payload={},
                correlation_id="corr-123",
            )
        )
        assert agent.received[0].correlation_id == "corr-123"

    def test_no_subscriber_no_error(self):
        m = AgentMediator()
        m.send(AgentMessage(sender="s", topic="nonexistent", payload={}))

    def test_multiple_subscribers(self):
        m = AgentMediator()
        a1 = _MockAgent("sub1", ["topic.a"])
        a2 = _MockAgent("sub2", ["topic.a"])
        m.register(a1)
        m.register(a2)
        m.send(AgentMessage(sender="s", topic="topic.a", payload={}))
        assert len(a1.received) == 1
        assert len(a2.received) == 1

    def test_interface_cannot_instantiate(self):
        try:
            IAgentMediator()
            assert False, "should raise TypeError"
        except TypeError:
            pass

    def test_reasoning_result_dataclass(self):
        r = ReasoningResult(
            goal_id="g-1",
            goal_description="test",
            subtasks=[{"id": "s1", "description": "do something"}],
            verification_criteria=["check 1"],
        )
        assert r.goal_id == "g-1"
        assert len(r.subtasks) == 1

    def test_execution_result_dataclass(self):
        e = ExecutionResult(files=[{"path": "test.py"}], errors=[])
        assert len(e.files) == 1
        assert e.errors == []

    def test_validation_result_dataclass(self):
        v = ValidationResult(
            all_passed=True,
            criteria_checks=[{"criterion": "check 1", "passed": True}],
            total_criteria=1,
            passed_criteria=1,
        )
        assert v.all_passed is True
