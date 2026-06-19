"""Agent Mediator — formal Mediator pattern for inter-agent communication.

Replaces raw publish/subscribe on SharedContext with typed messages
routed through a central mediator.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agentic_pipeline.agents.base_agent import Agent


@dataclass
class AgentMessage:
    """Typed message exchanged between agents via Mediator."""

    sender: str
    topic: str
    payload: Any
    correlation_id: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class PerceptionResult:
    """Payload for perception.completed topic."""

    raw: str
    intent: dict
    entities: list
    slots: dict
    confidence: float


@dataclass
class ReasoningResult:
    """Payload for reasoning.completed topic."""

    goal_id: str
    goal_description: str
    subtasks: list[dict]
    verification_criteria: list[str]


@dataclass
class ExecutionResult:
    """Payload for execution.completed topic."""

    files: list[dict]
    errors: list[str]


@dataclass
class ValidationResult:
    """Payload for validation.completed topic."""

    all_passed: bool
    criteria_checks: list[dict]
    total_criteria: int
    passed_criteria: int


class IAgentMediator(ABC):
    """Interface for the Mediator — agents only know this interface."""

    @abstractmethod
    def register(self, agent: Agent) -> None: ...

    @abstractmethod
    def send(self, message: AgentMessage) -> None: ...

    @abstractmethod
    def request(self, message: AgentMessage, timeout: float = 30.0) -> Any: ...


class AgentMediator(IAgentMediator):
    """Concrete mediator: routes messages between agents without them knowing each other."""

    def __init__(self, event_bus=None):
        self._event_bus = event_bus
        self._agents: dict[str, Agent] = {}
        self._subscriptions: dict[str, list[str]] = {}

    def register(self, agent: Agent) -> None:
        self._agents[agent.name] = agent
        if hasattr(agent, "subscriptions"):
            for topic in agent.subscriptions:
                self._subscriptions.setdefault(topic, []).append(agent.name)

    def send(self, message: AgentMessage) -> None:
        self._route(message.topic, message)

    def request(self, message: AgentMessage, timeout: float = 30.0) -> Any:
        self.send(message)
        return None

    def _route(self, topic: str, data: AgentMessage) -> None:
        for agent_name in self._subscriptions.get(topic, []):
            agent = self._agents.get(agent_name)
            if agent and hasattr(agent, "on_message"):
                agent.on_message(data)
