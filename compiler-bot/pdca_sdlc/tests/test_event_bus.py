"""Tests for core/event_bus.py."""

from unittest.mock import Mock

from pdca_sdlc.core.event_bus import (
    AsyncEventBus,
    Event,
    TopicMatcher,
)


class TestTopicMatcher:
    """Tests for TopicMatcher static methods."""

    def test_exact_match(self) -> None:
        assert TopicMatcher.matches(
            "proyecto.p-01.requirement.created",
            "proyecto.p-01.requirement.created",
        )

    def test_exact_mismatch(self) -> None:
        assert not TopicMatcher.matches(
            "proyecto.p-01.requirement.created",
            "proyecto.p-01.requirement.updated",
        )

    def test_single_level_wildcard(self) -> None:
        assert TopicMatcher.matches(
            "proyecto.*.requirement.created",
            "proyecto.p-01.requirement.created",
        )

    def test_single_level_wildcard_mismatch_depth(self) -> None:
        assert not TopicMatcher.matches(
            "proyecto.*.requirement.created",
            "proyecto.p-01.sub.requirement.created",
        )

    def test_subtree_wildcard(self) -> None:
        assert TopicMatcher.matches(
            "proyecto.p-01.>",
            "proyecto.p-01.requirement.created",
        )

    def test_subtree_wildcard_deep(self) -> None:
        assert TopicMatcher.matches(
            "proyecto.p-01.>",
            "proyecto.p-01.requirement.functional.created",
        )

    def test_subtree_wildcard_mismatch(self) -> None:
        assert not TopicMatcher.matches(
            "proyecto.p-01.>",
            "proyecto.p-02.requirement.created",
        )

    def test_catch_all_wildcard(self) -> None:
        assert TopicMatcher.matches(">", "anything.here.is.fine")

    def test_wildcard_with_glob(self) -> None:
        assert TopicMatcher.matches(
            "proyecto.p-??.requirement.created",
            "proyecto.p-01.requirement.created",
        )


class TestEvent:
    """Tests for Event dataclass."""

    def test_event_creation(self) -> None:
        event = Event(
            topic="test.topic",
            source="test",
            project_id="p-01",
            data={"key": "value"},
        )
        assert event.topic == "test.topic"
        assert event.source == "test"
        assert event.project_id == "p-01"
        assert event.data == {"key": "value"}
        assert event.sequence == 0
        assert event.id is not None
        assert event.timestamp > 0


class TestAsyncEventBus:
    """Tests for AsyncEventBus."""

    async def test_publish_subscribe(self) -> None:
        bus = AsyncEventBus()
        handler = Mock()
        await bus.subscribe("proyecto.p-01.created", handler)
        event = Event(topic="proyecto.p-01.created", source="test", project_id="p-01", data={})
        await bus.publish(event)
        handler.assert_called_once()
        args, _ = handler.call_args
        assert args[0] == "proyecto.p-01.created"
        assert args[1].sequence > 0

    async def test_publish_async_handler(self) -> None:
        bus = AsyncEventBus()
        results = []

        async def async_handler(topic: str, data: object) -> None:
            results.append((topic, data))

        await bus.subscribe("proyecto.p-01.updated", async_handler)
        event = Event(
            topic="proyecto.p-01.updated", source="test", project_id="p-01", data={"x": 1}
        )
        await bus.publish(event)
        assert len(results) == 1
        assert results[0][0] == "proyecto.p-01.updated"

    async def test_sequence_numbers(self) -> None:
        bus = AsyncEventBus()
        e1 = Event(topic="t.1", source="test", project_id="p-01", data={})
        e2 = Event(topic="t.2", source="test", project_id="p-01", data={})
        e3 = Event(topic="t.1", source="test", project_id="p-02", data={})
        await bus.publish(e1)
        await bus.publish(e2)
        await bus.publish(e3)
        assert e1.sequence == 1
        assert e2.sequence == 2
        assert e3.sequence == 1  # different project, resets

    async def test_replay_events(self) -> None:
        bus = AsyncEventBus()
        events = [
            Event(topic=f"t.{i}", source="test", project_id="p-01", data={"i": i}) for i in range(5)
        ]
        for e in events:
            await bus.publish(e)
        replayed = bus.replay("p-01", since_sequence=2)
        assert len(replayed) == 3
        assert [e.sequence for e in replayed] == [3, 4, 5]

    async def test_replay_empty(self) -> None:
        bus = AsyncEventBus()
        assert bus.replay("p-99") == []

    async def test_wildcard_subscription(self) -> None:
        bus = AsyncEventBus()
        handler = Mock()
        await bus.subscribe("proyecto.*.created", handler)
        e1 = Event(topic="proyecto.p-01.created", source="test", project_id="p-01", data={})
        e2 = Event(topic="proyecto.p-02.created", source="test", project_id="p-02", data={})
        e3 = Event(topic="proyecto.p-01.updated", source="test", project_id="p-01", data={})
        await bus.publish(e1)
        await bus.publish(e2)
        await bus.publish(e3)
        assert handler.call_count == 2

    async def test_has_subscribers(self) -> None:
        bus = AsyncEventBus()
        handler = Mock()
        assert not bus.has_subscribers("test.topic")
        await bus.subscribe("test.topic", handler)
        assert bus.has_subscribers("test.topic")

    async def test_clear(self) -> None:
        bus = AsyncEventBus()
        handler = Mock()
        await bus.subscribe("test.topic", handler)
        await bus.publish(Event(topic="test.topic", source="test", project_id="p-01", data={}))
        bus.clear()
        assert not bus.has_subscribers("test.topic")
        assert bus.replay("p-01") == []

    async def test_unsubscribe(self) -> None:
        bus = AsyncEventBus()
        handler = Mock()
        await bus.subscribe("test.topic", handler)
        await bus.unsubscribe("test.topic", handler)
        await bus.publish(Event(topic="test.topic", source="test", project_id="p-01", data={}))
        handler.assert_not_called()
