"""Tests for event_bus query engine, aggregations, SSE, and indices."""

import time
from unittest.mock import Mock

from pdca_sdlc.core.event_bus import AsyncEventBus, Event


class TestQueryEvents:
    """Tests for AsyncEventBus.query_events()."""

    async def _setup(
        self,
        bus: AsyncEventBus,
        project_id: str = "p-01",
        count: int = 5,
    ) -> list[Event]:
        events = [
            Event(
                topic=f"project.{project_id}.step.{i}",
                source="agent-a",
                project_id=project_id,
                data={"idx": i, "msg": f"event-{i}"},
            )
            for i in range(count)
        ]
        for e in events:
            await bus.publish(e)
        return events

    async def test_query_events_by_project(self) -> None:
        bus = AsyncEventBus()
        await self._setup(bus)
        results, total = bus.query_events(project_id="p-01")
        assert total == 5
        assert len(results) == 5

    async def test_query_events_by_project_empty(self) -> None:
        bus = AsyncEventBus()
        results, total = bus.query_events(project_id="p-99")
        assert total == 0
        assert results == []

    async def test_query_events_all_projects(self) -> None:
        bus = AsyncEventBus()
        await self._setup(bus, "p-01", 3)
        await self._setup(bus, "p-02", 2)
        results, total = bus.query_events()
        assert total == 5
        assert len(results) == 5

    async def test_query_events_by_topic_pattern(self) -> None:
        bus = AsyncEventBus()
        await self._setup(bus)
        results, total = bus.query_events(topic_pattern="project.p-01.step.*")
        assert total == 5

    async def test_query_events_by_topic_exact(self) -> None:
        bus = AsyncEventBus()
        await self._setup(bus)
        e = Event(topic="custom.event", source="test", project_id="p-01", data={})
        await bus.publish(e)
        results, total = bus.query_events(topic_pattern="custom.event")
        assert total == 1

    async def test_query_events_by_source(self) -> None:
        bus = AsyncEventBus()
        await self._setup(bus)
        e = Event(topic="other.event", source="agent-b", project_id="p-01", data={})
        await bus.publish(e)
        results, total = bus.query_events(source="agent-b")
        assert total == 1

    async def test_query_events_by_time_range(self) -> None:
        bus = AsyncEventBus()
        e1 = Event(topic="a", source="s", project_id="p-01", data={})
        await bus.publish(e1)
        time.sleep(0.01)
        mid = time.time()
        time.sleep(0.01)
        e2 = Event(topic="b", source="s", project_id="p-01", data={})
        await bus.publish(e2)
        results, total = bus.query_events(since_time=mid)
        assert total == 1
        assert results[0].topic == "b"

    async def test_query_events_search_text(self) -> None:
        bus = AsyncEventBus()
        await self._setup(bus)
        results, total = bus.query_events(search_text="event-3")
        assert total == 1

    async def test_query_events_search_text_no_match(self) -> None:
        bus = AsyncEventBus()
        await self._setup(bus)
        results, total = bus.query_events(search_text="nonexistent")
        assert total == 0

    async def test_query_events_pagination(self) -> None:
        bus = AsyncEventBus()
        await self._setup(bus)
        results, total = bus.query_events(limit=2, offset=1)
        assert total == 5
        assert len(results) == 2
        assert results[0].data["idx"] == 1

    async def test_query_events_pagination_beyond(self) -> None:
        bus = AsyncEventBus()
        await self._setup(bus)
        results, total = bus.query_events(limit=2, offset=10)
        assert total == 5
        assert results == []

    async def test_query_events_total_count(self) -> None:
        bus = AsyncEventBus()
        await self._setup(bus)
        results, total = bus.query_events(limit=3)
        assert total == 5
        assert len(results) == 3


class TestGetEvent:
    """Tests for AsyncEventBus.get_event()."""

    async def test_get_event_by_id(self) -> None:
        bus = AsyncEventBus()
        event = Event(topic="t", source="s", project_id="p-01", data={})
        await bus.publish(event)
        found = bus.get_event(event.id)
        assert found is not None
        assert found.id == event.id
        assert found.topic == "t"

    async def test_get_event_not_found(self) -> None:
        bus = AsyncEventBus()
        assert bus.get_event("nonexistent") is None


class TestTopicDistribution:
    """Tests for AsyncEventBus.get_topic_distribution()."""

    async def _setup(self, bus: AsyncEventBus) -> None:
        topics = ["a.x", "a.x", "b.y", "a.x", "c.z"]
        for t in topics:
            await bus.publish(Event(topic=t, source="s", project_id="p-01", data={}))

    async def test_topic_distribution(self) -> None:
        bus = AsyncEventBus()
        await self._setup(bus)
        dist = bus.get_topic_distribution("p-01")
        assert dist == {"a.x": 3, "b.y": 1, "c.z": 1}

    async def test_topic_distribution_empty_project(self) -> None:
        bus = AsyncEventBus()
        assert bus.get_topic_distribution("p-99") == {}


class TestTimeline:
    """Tests for AsyncEventBus.get_timeline()."""

    async def _setup(self, bus: AsyncEventBus) -> None:
        for i in range(3):
            await bus.publish(Event(topic="t", source="s", project_id="p-01", data={}))

    async def test_timeline_basic(self) -> None:
        bus = AsyncEventBus()
        await self._setup(bus)
        timeline = bus.get_timeline("p-01", granularity="1h")
        assert len(timeline) >= 1
        for bucket in timeline:
            assert "time" in bucket
            assert "count" in bucket

    async def test_timeline_empty(self) -> None:
        bus = AsyncEventBus()
        assert bus.get_timeline("p-99") == []

    async def test_timeline_granularity_1s(self) -> None:
        bus = AsyncEventBus()
        await self._setup(bus)
        timeline = bus.get_timeline("p-01", granularity="1s")
        assert len(timeline) >= 1

    async def test_timeline_invalid_granularity_defaults_1m(self) -> None:
        bus = AsyncEventBus()
        await self._setup(bus)
        timeline = bus.get_timeline("p-01", granularity="invalid")
        assert len(timeline) >= 1


class TestTopics:
    """Tests for AsyncEventBus.get_topics()."""

    async def test_get_topics(self) -> None:
        bus = AsyncEventBus()
        topics = ["a.b", "a.b", "c.d"]
        for t in topics:
            await bus.publish(Event(topic=t, source="s", project_id="p-01", data={}))
        result = bus.get_topics()
        assert len(result) == 2
        assert result[0]["topic"] == "a.b"
        assert result[0]["count"] == 2
        assert result[1]["topic"] == "c.d"
        assert result[1]["count"] == 1

    async def test_get_topics_empty(self) -> None:
        bus = AsyncEventBus()
        assert bus.get_topics() == []


class TestSources:
    """Tests for AsyncEventBus.get_sources()."""

    async def test_get_sources(self) -> None:
        bus = AsyncEventBus()
        await bus.publish(Event(topic="a", source="src1", project_id="p-01", data={}))
        await bus.publish(Event(topic="b", source="src1", project_id="p-01", data={}))
        await bus.publish(Event(topic="c", source="src2", project_id="p-01", data={}))
        result = bus.get_sources()
        assert len(result) == 2
        assert result[0]["source"] == "src1"
        assert result[0]["count"] == 2
        assert result[1]["source"] == "src2"
        assert result[1]["count"] == 1

    async def test_get_sources_empty(self) -> None:
        bus = AsyncEventBus()
        assert bus.get_sources() == []


class TestStats:
    """Tests for AsyncEventBus.get_stats()."""

    async def test_get_stats(self) -> None:
        bus = AsyncEventBus()
        await bus.publish(Event(topic="a", source="s1", project_id="p-01", data={}))
        await bus.publish(Event(topic="b", source="s2", project_id="p-02", data={}))
        stats = bus.get_stats()
        assert stats["total_events"] == 2
        assert stats["total_projects"] == 2
        assert stats["capacity"] == 10000
        assert 0 <= stats["usage_pct"] < 100  # 2/10000 rounds to 0.0
        assert stats["unique_sources"] == 2
        assert stats["unique_topics"] == 2

    async def test_get_stats_empty(self) -> None:
        bus = AsyncEventBus()
        stats = bus.get_stats()
        assert stats["total_events"] == 0
        assert stats["usage_pct"] == 0.0


class TestSubscribers:
    """Tests for AsyncEventBus.get_subscribers()."""

    async def test_get_subscribers_wildcard(self) -> None:
        bus = AsyncEventBus()

        def handler(topic: str, event: object) -> None:
            pass

        await bus.subscribe("proyecto.*.created", handler)
        subs = bus.get_subscribers()
        wildcard = [s for s in subs if s["type"] == "wildcard"]
        assert len(wildcard) == 1
        assert wildcard[0]["pattern"] == "proyecto.*.created"

    async def test_get_subscribers_exact(self) -> None:
        bus = AsyncEventBus()
        handler = Mock()
        await bus.subscribe("test.topic", handler)
        subs = bus.get_subscribers()
        exact = [s for s in subs if s["type"] == "exact"]
        assert len(exact) >= 1

    async def test_get_subscribers_empty(self) -> None:
        bus = AsyncEventBus()
        assert bus.get_subscribers() == []


class TestSSECallbacks:
    """Tests for SSE callback registration and invocation."""

    async def test_sse_callback_invoked(self) -> None:
        bus = AsyncEventBus()
        results: list[str] = []

        def cb(event: Event) -> None:
            results.append(event.topic)

        bus.register_sse_callback("p-01", cb)
        await bus.publish(Event(topic="test.event", source="s", project_id="p-01", data={}))
        assert results == ["test.event"]

    async def test_sse_callback_multi_project(self) -> None:
        bus = AsyncEventBus()
        results_a: list[str] = []
        results_b: list[str] = []

        def cb_a(event: Event) -> None:
            results_a.append(event.topic)

        def cb_b(event: Event) -> None:
            results_b.append(event.topic)

        bus.register_sse_callback("p-01", cb_a)
        bus.register_sse_callback("p-02", cb_b)
        await bus.publish(Event(topic="event.1", source="s", project_id="p-01", data={}))
        await bus.publish(Event(topic="event.2", source="s", project_id="p-02", data={}))
        assert results_a == ["event.1"]
        assert results_b == ["event.2"]

    async def test_sse_callback_unregister(self) -> None:
        bus = AsyncEventBus()
        results: list[str] = []

        def cb(event: Event) -> None:
            results.append(event.topic)

        bus.register_sse_callback("p-01", cb)
        bus.unregister_sse_callback("p-01", cb)
        await bus.publish(Event(topic="test.event", source="s", project_id="p-01", data={}))
        assert results == []

    async def test_sse_callback_all_projects(self) -> None:
        bus = AsyncEventBus()
        results: list[str] = []

        def cb(event: Event) -> None:
            results.append(event.topic)

        bus.register_sse_callback("_all", cb)
        await bus.publish(Event(topic="a", source="s", project_id="p-01", data={}))
        await bus.publish(Event(topic="b", source="s", project_id="p-02", data={}))
        assert results == ["a", "b"]

    async def test_sse_callback_not_invoked_for_other_project(self) -> None:
        bus = AsyncEventBus()
        results: list[str] = []

        def cb(event: Event) -> None:
            results.append(event.topic)

        bus.register_sse_callback("p-01", cb)
        await bus.publish(Event(topic="event", source="s", project_id="p-02", data={}))
        assert results == []


class TestIndices:
    """Tests for index consistency."""

    async def test_indices_consistent_on_overflow(self) -> None:
        bus = AsyncEventBus()
        bus.set_max_log_size(3)
        events = [
            Event(topic=f"t.{i}", source="s", project_id="p-01", data={"i": i}) for i in range(5)
        ]
        for e in events:
            await bus.publish(e)
        # Only 3 events should remain in the log (indices 2,3,4)
        assert len(bus._event_log) == 3
        assert len(bus._by_project["p-01"]) == 3
        assert len(bus._by_id) == 3
        # The oldest two should have been removed from _by_id
        assert bus.get_event(events[0].id) is None
        assert bus.get_event(events[1].id) is None
        # The newest three should still be accessible
        assert bus.get_event(events[2].id) is not None
        assert bus.get_event(events[3].id) is not None
        assert bus.get_event(events[4].id) is not None

    async def test_indices_clear_resets_everything(self) -> None:
        bus = AsyncEventBus()
        await bus.publish(Event(topic="t", source="s", project_id="p-01", data={}))
        handler = Mock()
        await bus.subscribe("test.topic", handler)
        bus.register_sse_callback("p-01", lambda e: None)
        bus.clear()
        assert bus._event_log == []
        assert bus._by_project == {}
        assert bus._by_id == {}
        assert bus._sequences == {}
        assert bus._wildcard_handlers == []
        assert bus._sse_callbacks == {}
        assert bus.get_subscribers() == []

    async def test_replay_still_works(self) -> None:
        bus = AsyncEventBus()
        for i in range(5):
            await bus.publish(Event(topic=f"t.{i}", source="s", project_id="p-01", data={}))
        replayed = bus.replay("p-01", since_sequence=2)
        assert len(replayed) == 3
        assert [e.sequence for e in replayed] == [3, 4, 5]

    async def test_query_events_since_sequence(self) -> None:
        bus = AsyncEventBus()
        for i in range(5):
            await bus.publish(Event(topic=f"t.{i}", source="s", project_id="p-01", data={}))
        results, total = bus.query_events(project_id="p-01", since_sequence=2)
        assert total == 3
        assert [e.sequence for e in results] == [3, 4, 5]
