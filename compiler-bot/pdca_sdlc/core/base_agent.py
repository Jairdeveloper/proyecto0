"""BaseAgent — abstract base class for all PDCA-sdlc agents.

Defines the lifecycle (start -> handle_event -> stop), agent context,
and helper methods for emitting events and querying the knowledge graph.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from pdca_sdlc.core.capability_registry import (
    CapabilityManifest,
    CapabilityRegistry,
)
from pdca_sdlc.core.event_bus import AsyncEventBus, Event
from pdca_sdlc.core.knowledge_graph import KnowledgeGraph, Node, NodeType

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """Shared context passed to every agent.

    Attributes:
        event_bus: The async event bus for inter-agent communication.
        knowledge_graph: The traceability graph.
        capability_registry: Registry where agents register themselves.
        agent_id: Unique identifier for this agent instance.
    """

    event_bus: AsyncEventBus
    knowledge_graph: KnowledgeGraph
    capability_registry: CapabilityRegistry
    agent_id: str


class BaseAgent(ABC):
    """Abstract base class for PDCA-sdlc agents.

    Subclasses must implement:
      - ``manifest`` (property) — returns CapabilityManifest
      - ``handle_event(event)`` — process an incoming event

    Lifecycle::

        agent = MyAgent(ctx, llm)
        await agent.start()
        # ... event_bus delivers events ...
        await agent.stop()
    """

    def __init__(self, context: AgentContext) -> None:
        self._ctx = context
        self._running: bool = False
        self._subscribed_topics: list[str] = []

    @property
    @abstractmethod
    def manifest(self) -> CapabilityManifest:
        """Return the capability manifest for this agent."""

    async def start(self) -> None:
        """Register the agent and subscribe to trigger topics."""
        log_extra = {"agent_id": self._ctx.agent_id}
        self._ctx.capability_registry.register(self.manifest)
        logger.debug("Agent %s registered", self._ctx.agent_id, extra=log_extra)
        for trigger in self.manifest.triggers:
            await self._ctx.event_bus.subscribe(trigger, self._handle_event_wrapper)
            self._subscribed_topics.append(trigger)
        self._running = True
        logger.info(
            "Agent %s started — subscribed to %d topics",
            self._ctx.agent_id,
            len(self.manifest.triggers),
            extra=log_extra,
        )

    async def stop(self) -> None:
        """Unsubscribe from topics and unregister from the registry."""
        log_extra = {"agent_id": self._ctx.agent_id}
        for topic in self._subscribed_topics:
            await self._ctx.event_bus.unsubscribe(topic, self._handle_event_wrapper)
        self._subscribed_topics.clear()
        self._ctx.capability_registry.update_status(self._ctx.agent_id, "disabled")
        self._running = False
        logger.info("Agent %s stopped", self._ctx.agent_id, extra=log_extra)

    @abstractmethod
    async def handle_event(self, event: Event) -> None:
        """Process an incoming event. Must be implemented by subclasses."""

    async def _handle_event_wrapper(self, topic: str, data: object) -> None:
        """Wrapper that catches exceptions and emits risk.identified."""
        if not isinstance(data, Event):
            logger.warning(
                "Agent %s received non-Event payload on %s",
                self._ctx.agent_id,
                topic,
            )
            return
        try:
            await self.handle_event(data)
        except Exception as exc:
            logger.exception(
                "Agent %s failed handling %s",
                self._ctx.agent_id,
                data.topic,
            )
            await self.emit(
                topic="risk.identified",
                project_id=data.project_id,
                data={
                    "description": f"{self._ctx.agent_id} failed: {exc}",
                    "severity": "medium",
                    "source_event": data.topic,
                },
            )

    async def emit(
        self,
        topic: str,
        project_id: str,
        data: dict[str, Any],
    ) -> None:
        """Publish an event to the bus on behalf of this agent."""
        event = Event(
            topic=topic,
            source=self._ctx.agent_id,
            project_id=project_id,
            data=data,
        )
        await self._ctx.event_bus.publish(event)

    def read_graph(self, node_id: str) -> Node | None:
        """Read a node from the knowledge graph."""
        return self._ctx.knowledge_graph.get_node(node_id)

    def write_graph(self, node: Node) -> None:
        """Write a node to the knowledge graph."""
        self._ctx.knowledge_graph.add_node(node)

    def query_graph(
        self,
        node_type: NodeType | None = None,
        status: str | None = None,
        **properties: Any,
    ) -> list[Node]:
        """Query nodes from the knowledge graph."""
        return self._ctx.knowledge_graph.query(
            node_type=node_type,
            status=status,
            **properties,
        )

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def context(self) -> AgentContext:
        return self._ctx
