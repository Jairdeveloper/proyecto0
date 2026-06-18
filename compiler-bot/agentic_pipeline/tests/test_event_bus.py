from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agentic_pipeline.agents.event_bus import EventBus


class TestEventBus:
    """Tests for EventBus publish/subscribe."""

    def test_publish_subscribe(self):
        bus = EventBus()
        callback = MagicMock()
        bus.subscribe("test_topic", callback)
        bus.publish("test_topic", {"data": 42})
        callback.assert_called_once_with("test_topic", {"data": 42})

    def test_multiple_subscribers(self):
        bus = EventBus()
        cb1 = MagicMock()
        cb2 = MagicMock()
        bus.subscribe("topic", cb1)
        bus.subscribe("topic", cb2)
        bus.publish("topic", "hello")
        cb1.assert_called_once_with("topic", "hello")
        cb2.assert_called_once_with("topic", "hello")

    def test_unsubscribe(self):
        bus = EventBus()
        callback = MagicMock()
        bus.subscribe("topic", callback)
        bus.unsubscribe("topic", callback)
        bus.publish("topic", "data")
        callback.assert_not_called()

    def test_no_subscribers_no_error(self):
        bus = EventBus()
        bus.publish("empty_topic", "data")

    def test_has_subscribers(self):
        bus = EventBus()
        assert bus.has_subscribers("topic") is False
        bus.subscribe("topic", lambda t, d: None)
        assert bus.has_subscribers("topic") is True

    def test_subscriber_count(self):
        bus = EventBus()
        assert bus.subscriber_count("topic") == 0
        bus.subscribe("topic", lambda t, d: None)
        bus.subscribe("topic", lambda t, d: None)
        assert bus.subscriber_count("topic") == 2

    def test_clear(self):
        bus = EventBus()
        bus.subscribe("a", lambda t, d: None)
        bus.subscribe("b", lambda t, d: None)
        bus.clear()
        assert bus.subscriber_count("a") == 0
        assert bus.subscriber_count("b") == 0

    @pytest.mark.asyncio
    async def test_publish_async_with_async_callback(self):
        bus = EventBus()
        callback = MagicMock()

        async def async_cb(topic, data):
            callback(topic, data)

        bus.subscribe("topic", async_cb)
        await bus.publish_async("topic", {"val": 1})
        callback.assert_called_once_with("topic", {"val": 1})

    @pytest.mark.asyncio
    async def test_publish_async_with_sync_callback(self):
        bus = EventBus()
        callback = MagicMock()
        bus.subscribe("topic", callback)
        await bus.publish_async("topic", "data")
        callback.assert_called_once_with("topic", "data")

    def test_event_bus_in_shared_context(self):
        from agentic_pipeline.agents.base_agent import SharedContext

        ctx = SharedContext()
        assert ctx.event_bus is not None
        callback = MagicMock()
        ctx.event_bus.subscribe("topic", callback)
        ctx.event_bus.publish("topic", "via_bus")
        callback.assert_called_once()
