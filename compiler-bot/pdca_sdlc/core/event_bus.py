"""AsyncEventBus — adapter over existing EventBus with hierarchical topics.

Adds: hierarchical topics (dot-separated), wildcards (`>` for subtree,
`*` for single level), sequence numbers, event log for replay,
query engine with filters/pagination, event aggregations, SSE callbacks.
"""

from __future__ import annotations

import asyncio
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
      - Indexed query engine with filters and pagination
      - Topic/source aggregation and timeline
      - SSE (Server-Sent Events) callbacks for live streaming
    """

    def __init__(self) -> None:
        self._bus = _EventBus()
        self._sequences: dict[str, int] = {}
        self._event_log: list[Event] = []
        self._by_project: dict[str, list[Event]] = {}
        self._by_id: dict[str, Event] = {}
        self._max_log_size: int = 10000
        self._wildcard_handlers: list[tuple[str, Callable]] = []
        self._sse_callbacks: dict[str, list[Callable[[Event], None]]] = {}

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

        Assigns a sequence number, logs the event, maintains indices,
        notifies matching subscribers (both exact and wildcard),
        and invokes SSE callbacks for live streaming.
        """
        event.sequence = self._next_sequence(event.project_id)
        self._event_log.append(event)
        self._by_project.setdefault(event.project_id, []).append(event)
        self._by_id[event.id] = event
        if len(self._event_log) > self._max_log_size:
            removed = self._event_log.pop(0)
            if removed.id in self._by_id:
                del self._by_id[removed.id]
            proj_events = self._by_project.get(removed.project_id, [])
            if proj_events and proj_events[0].id == removed.id:
                proj_events.pop(0)
        for pattern, handler in self._wildcard_handlers:
            if TopicMatcher.matches(pattern, event.topic):
                if asyncio.iscoroutinefunction(handler):
                    await handler(event.topic, event)
                else:
                    handler(event.topic, event)
        for cb in self._sse_callbacks.get(event.project_id, []):
            cb(event)
        for cb in self._sse_callbacks.get("_all", []):
            cb(event)
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

    def query_events(
        self,
        project_id: str | None = None,
        topic_pattern: str | None = None,
        source: str | None = None,
        since_sequence: int = 0,
        since_time: float | None = None,
        until_time: float | None = None,
        search_text: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Event], int]:
        """Query events with filters, pagination, and total count.

        Args:
            project_id: Filter by project. None = all projects.
            topic_pattern: Topic wildcard pattern (supports ``*`` and ``>``).
            source: Exact source filter.
            since_sequence: Minimum sequence number (exclusive).
            since_time: Minimum timestamp (inclusive).
            until_time: Maximum timestamp (inclusive).
            search_text: Case-insensitive search in ``str(event.data)``.
            limit: Max events to return.
            offset: Number of events to skip.

        Returns:
            Tuple of (filtered_events, total_count_before_pagination).
        """
        candidates: list[Event] = []
        if project_id and project_id in self._by_project:
            candidates = self._by_project[project_id]
        elif project_id is None:
            candidates = list(self._event_log)
        else:
            candidates = []

        filtered = [
            e
            for e in candidates
            if e.sequence > since_sequence
            and (topic_pattern is None or TopicMatcher.matches(topic_pattern, e.topic))
            and (source is None or e.source == source)
            and (since_time is None or e.timestamp >= since_time)
            and (until_time is None or e.timestamp <= until_time)
            and (search_text is None or search_text.lower() in str(e.data).lower())
        ]

        total = len(filtered)
        paginated = filtered[offset : offset + limit]
        return paginated, total

    def get_event(self, event_id: str) -> Event | None:
        """Retrieve a single event by its ID, or None if not found."""
        return self._by_id.get(event_id)

    def get_topic_distribution(self, project_id: str) -> dict[str, int]:
        """Return count of events per topic for a given project."""
        dist: dict[str, int] = {}
        for e in self._by_project.get(project_id, []):
            dist[e.topic] = dist.get(e.topic, 0) + 1
        return dist

    def get_timeline(
        self,
        project_id: str,
        granularity: str = "1m",
    ) -> list[dict[str, object]]:
        """Bucket events into time windows.

        Args:
            project_id: Project to analyze.
            granularity: Window size — ``1s``, ``1m`` (default), or ``1h``.

        Returns:
            Sorted list of ``{"time": unix_ts, "count": int}`` buckets.
        """
        window = {"1s": 1, "1m": 60, "1h": 3600}.get(granularity, 60)
        buckets: dict[int, int] = {}
        for e in self._by_project.get(project_id, []):
            bucket = int(e.timestamp / window) * window
            buckets[bucket] = buckets.get(bucket, 0) + 1
        return sorted(
            [{"time": t, "count": c} for t, c in buckets.items()],
            key=lambda x: x["time"],  # type: ignore[arg-type]
        )

    def get_topics(self) -> list[dict[str, object]]:
        """Return all unique topics with count and last_seen timestamp."""
        topic_data: dict[str, dict] = {}
        for e in self._event_log:
            if e.topic not in topic_data:
                topic_data[e.topic] = {
                    "topic": e.topic,
                    "count": 0,
                    "last_seen": 0.0,
                }
            topic_data[e.topic]["count"] += 1
            if e.timestamp > topic_data[e.topic]["last_seen"]:
                topic_data[e.topic]["last_seen"] = e.timestamp
        return sorted(
            list(topic_data.values()),
            key=lambda x: x["count"],
            reverse=True,
        )

    def get_sources(self) -> list[dict[str, object]]:
        """Return all unique sources with count and topics used."""
        source_data: dict[str, dict] = {}
        for e in self._event_log:
            if e.source not in source_data:
                source_data[e.source] = {
                    "source": e.source,
                    "count": 0,
                    "topics": set(),
                }
            source_data[e.source]["count"] += 1
            source_data[e.source]["topics"].add(e.topic)
        result: list[dict[str, object]] = []
        for src_name, data in source_data.items():
            result.append(
                {
                    "source": src_name,
                    "count": data["count"],
                    "topics": sorted(data["topics"]),
                }
            )
        return sorted(
            result,
            key=lambda x: x["count"],
            reverse=True,
        )

    def get_stats(self) -> dict[str, object]:
        """Return event bus health metrics."""
        unique_sources: set[str] = set()
        unique_topics: set[str] = set()
        for e in self._event_log:
            unique_sources.add(e.source)
            unique_topics.add(e.topic)
        return {
            "total_events": len(self._event_log),
            "total_projects": len(self._by_project),
            "capacity": self._max_log_size,
            "usage_pct": round(len(self._event_log) / self._max_log_size * 100, 1),
            "unique_sources": len(unique_sources),
            "unique_topics": len(unique_topics),
        }

    def get_subscribers(self) -> list[dict[str, object]]:
        """Return all registered subscribers (exact and wildcard).

        Introspects the inner EventBus for exact-topic subscribers
        and combines with wildcard handlers.
        """
        subs: list[dict[str, object]] = []
        if hasattr(self._bus, "_subscribers"):
            for topic, handlers in self._bus._subscribers.items():
                for handler in handlers:
                    subs.append(
                        {
                            "pattern": topic,
                            "handler": getattr(handler, "__name__", str(handler)),
                            "type": "exact",
                        },
                    )
        for pattern, handler in self._wildcard_handlers:
            subs.append(
                {
                    "pattern": pattern,
                    "handler": getattr(handler, "__name__", str(handler)),
                    "type": "wildcard",
                },
            )
        return subs

    def register_sse_callback(
        self,
        project_id: str,
        callback: Callable[[Event], None],
    ) -> None:
        """Register a callback to receive events in real-time for SSE."""
        self._sse_callbacks.setdefault(project_id, []).append(callback)

    def unregister_sse_callback(
        self,
        project_id: str,
        callback: Callable[[Event], None],
    ) -> None:
        """Remove a previously registered SSE callback."""
        cbs = self._sse_callbacks.get(project_id, [])
        if callback in cbs:
            cbs.remove(callback)

    def clear(self) -> None:
        """Remove all subscribers, SSE callbacks, and clear event data."""
        self._bus.clear()
        self._wildcard_handlers.clear()
        self._event_log.clear()
        self._by_project.clear()
        self._by_id.clear()
        self._sequences.clear()
        self._sse_callbacks.clear()
