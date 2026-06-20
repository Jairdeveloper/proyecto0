"""AsyncEventBus — adapter over existing EventBus with hierarchical topics.

Adds: hierarchical topics (dot-separated), wildcards (`>` for subtree,
`*` for single level), sequence numbers, event log for replay.
"""

from __future__ import annotations

import fnmatch
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from agentic_pipeline.agents.event_bus import EventBus as _EventBus


class TopicMatcher:
    """Static wildcard matching for hierarchical topics (dot-separated)."""

    @staticmethod
    def matches(pattern: str, topic: str) -> bool:
        """Check if a topic matches a pattern with wildcard support.

        Wildcards:
            *  — matches exactly one level (no dots)
            >  — matches the rest of the topic (subtree, must be at end)
        """
        if pattern == ">":
            return True
        if pattern.endswith(">"):
            prefix = pattern[:-1].rstrip(".")
            if prefix == "":
                return True
            return topic.startswith(prefix + ".")
        if ">" in pattern:
            parts = pattern.split(">", 1)
            return topic.startswith(parts[0].rstrip(".")) and (
                len(parts[0].rstrip(".")) == 0 or topic[len(parts[0].rstrip("."))] == "."
            )
        parts_p = pattern.split(".")
        parts_t = topic.split(".")
        if len(parts_p) != len(parts_t):
            return False
        for p, t in zip(parts_p, parts_t):
            if p == "*":
                continue
            if fnmatch.fnmatch(t, p):
                continue
            if p != t:
                return False
        return True


@dataclass
class Event:
    """A event in the event bus."""

    topic: str
    source: str
    project_id: str
    data: dict[str, Any]
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: float = field(default_factory=time.time)
    sequence: int = 0


class AsyncEventBus:
    """Async event bus with hierarchical topics, wildcards, and replay.

    Wraps the existing synchronous EventBus internally, extending it
    with:
      - Hierarchical topics (dot-separated: ``project.p-01.requirement.created``)
      - Wildcard subscription (``*`` one level, ``>`` subtree)
      - Auto-increment sequence numbers per project
      - Event log for replay
    """

    def __init__(self) -> None:
        self._bus = _EventBus()
        self._sequences: dict[str, int] = {}
        self._event_log: list[Event] = []
        self._max_log_size: int = 10000
        self._wildcard_handlers: list[tuple[str, Callable]] = []

    def set_max_log_size(self, size: int) -> None:
        """Set the maximum number of events kept in the replay log."""
        self._max_log_size = size

    def _next_sequence(self, project_id: str) -> int:
        self._sequences[project_id] = self._sequences.get(project_id, 0) + 1
        return self._sequences[project_id]

    async def subscribe(self, topic: str, handler: Callable) -> None:
        """Subscribe to a topic pattern.

        Supports wildcards:
          - ``"proyecto.*.created"`` — one level wildcard
          - ``"proyecto.>"`` — subtree wildcard (must be at end)
          - ``"proyecto.p-01.requirement.created"`` — exact match
        """
        if "*" in topic or ">" in topic:
            self._wildcard_handlers.append((topic, handler))
            return
        self._bus.subscribe(topic, handler)

    async def unsubscribe(self, topic: str, handler: Callable) -> None:
        """Remove a subscription."""
        if "*" in topic or ">" in topic:
            self._wildcard_handlers = [
                (p, h) for p, h in self._wildcard_handlers if not (p == topic and h == handler)
            ]
            return
        try:
            self._bus.unsubscribe(topic, handler)
        except ValueError:
            pass

    async def publish(self, event: Event) -> None:
        """Publish an event to the bus.

        Assigns a sequence number, logs the event, and notifies
        matching subscribers (both exact and wildcard).
        """
        event.sequence = self._next_sequence(event.project_id)
        self._event_log.append(event)
        if len(self._event_log) > self._max_log_size:
            self._event_log.pop(0)
        for pattern, handler in self._wildcard_handlers:
            if TopicMatcher.matches(pattern, event.topic):
                if hasattr(handler, "_async") or hasattr(handler, "__call__"):
                    pass
                handler(event.topic, event)
        await self._bus.publish_async(event.topic, event)

    def replay(self, project_id: str, since_sequence: int = 0) -> list[Event]:
        """Replay events for a project since a given sequence number."""
        return [
            e for e in self._event_log if e.project_id == project_id and e.sequence > since_sequence
        ]

    def has_subscribers(self, topic: str) -> bool:
        """Check if any subscriber matches this topic."""
        if self._bus.has_subscribers(topic):
            return True
        for pattern, _ in self._wildcard_handlers:
            if TopicMatcher.matches(pattern, topic):
                return True
        return False

    def clear(self) -> None:
        """Remove all subscribers and clear the event log."""
        self._bus.clear()
        self._wildcard_handlers.clear()
        self._event_log.clear()
        self._sequences.clear()
