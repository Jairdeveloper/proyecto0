"""Tests for dashboard API v2 — query, distribution, timeline, SSE, etc."""

from __future__ import annotations

import asyncio
import json
import threading
import time
from http.server import HTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from pdca_sdlc.core.capability_registry import CapabilityRegistry
from pdca_sdlc.core.event_bus import AsyncEventBus, Event
from pdca_sdlc.core.knowledge_graph import KnowledgeGraph
from pdca_sdlc.dashboard import SdlcDashboardService, create_server

DASHBOARD_PORT = 18765
DASHBOARD_URL = f"http://127.0.0.1:{DASHBOARD_PORT}"


def _fetch(path: str) -> tuple[int, dict]:
    """GET a dashboard API endpoint and return (status, parsed_json)."""
    url = f"{DASHBOARD_URL}{path}"
    req = Request(url)
    try:
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return resp.status, data
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        data = json.loads(body) if body else {"error": str(exc)}
        return exc.code, data


@pytest.fixture(scope="module")
def dashboard_server():
    """Start a dashboard server with pre-populated events for testing.

    Publishes events on multiple topics and sources to exercise
    query filters, distribution, timeline, topics, and sources.
    """
    bus = AsyncEventBus()
    kg = KnowledgeGraph()
    registry = CapabilityRegistry()

    async def _setup():
        # Publish events for p-v2-01
        topics_sources = [
            ("project.initialized", "cli"),
            ("adaptation.complete", "adaptation-agent"),
            ("requirement.created", "requirements-analyst"),
            ("code.committed", "coder-agent"),
            ("code.committed", "coder-agent"),
            ("adaptation.complete", "adaptation-agent"),
        ]
        for topic, source in topics_sources:
            await bus.publish(
                Event(
                    topic=topic,
                    source=source,
                    project_id="p-v2-01",
                    data={"key": topic.split(".")[-1]},
                ),
            )
        # Publish events for p-v2-02 (fewer)
        await bus.publish(
            Event(
                topic="project.initialized",
                source="cli",
                project_id="p-v2-02",
                data={"key": "init"},
            ),
        )
        return bus

    asyncio.run(_setup())

    service = SdlcDashboardService(kg, bus, registry)
    server: HTTPServer = create_server(
        host="127.0.0.1",
        port=DASHBOARD_PORT,
        service=service,
        bus=bus,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)

    yield service

    server.shutdown()


class TestQueryEventsV2:
    """Tests for the extended /api/events endpoint with filters."""

    def test_events_query_default(self, dashboard_server) -> None:
        status, data = _fetch("/api/events?project=p-v2-01")
        assert status == 200
        assert "events" in data
        assert data["total"] >= 6

    def test_events_query_with_topic_filter(self, dashboard_server) -> None:
        status, data = _fetch(
            "/api/events?project=p-v2-01&topic=code.committed",
        )
        assert status == 200
        assert data["total"] == 2
        for e in data["events"]:
            assert e["topic"] == "code.committed"

    def test_events_query_with_source_filter(self, dashboard_server) -> None:
        status, data = _fetch(
            "/api/events?project=p-v2-01&source=coder-agent",
        )
        assert status == 200
        assert data["total"] == 2
        for e in data["events"]:
            assert e["source"] == "coder-agent"

    def test_events_query_pagination(self, dashboard_server) -> None:
        status, data = _fetch("/api/events?project=p-v2-01&limit=2&offset=1")
        assert status == 200
        assert len(data["events"]) == 2
        assert data["total"] >= 6
        assert data["limit"] == 2
        assert data["offset"] == 1

    def test_events_query_search(self, dashboard_server) -> None:
        status, data = _fetch(
            "/api/events?project=p-v2-01&search=committed",
        )
        assert status == 200
        assert data["total"] == 2

    def test_events_query_no_match(self, dashboard_server) -> None:
        status, data = _fetch(
            "/api/events?project=p-v2-01&source=nonexistent",
        )
        assert status == 200
        assert data["total"] == 0

    def test_events_query_missing_project(self, dashboard_server) -> None:
        status, data = _fetch("/api/events")
        assert status == 200  # Sin filtro devuelve todos los proyectos

    def test_events_query_all_projects(self, dashboard_server) -> None:
        status, data = _fetch("/api/events?project=_all")
        assert status == 200
        assert data["total"] >= 7

    def test_events_query_limit_validation(self, dashboard_server) -> None:
        status, data = _fetch(
            "/api/events?project=p-v2-01&limit=invalid",
        )
        assert status == 200
        # Falls back to default limit=20
        assert data["limit"] == 20


class TestEventDetail:
    """Tests for GET /api/events/:id."""

    def test_event_detail_by_id(self, dashboard_server) -> None:
        # First get a known event from the list
        _, list_data = _fetch("/api/events?project=p-v2-01&limit=1")
        assert list_data["total"] >= 1
        event_id = list_data["events"][0]["id"]

        status, data = _fetch(f"/api/events/{event_id}")
        assert status == 200
        assert data["id"] == event_id
        assert "topic" in data
        assert "source" in data
        assert "sequence" in data
        assert "timestamp" in data
        assert "data" in data

    def test_event_detail_not_found(self, dashboard_server) -> None:
        status, data = _fetch("/api/events/nonexistent123")
        assert status == 404


class TestEventDistribution:
    """Tests for GET /api/events/distribution."""

    def test_event_distribution(self, dashboard_server) -> None:
        status, data = _fetch("/api/events/distribution?project=p-v2-01")
        assert status == 200
        assert "distribution" in data
        assert data["total"] >= 6
        # Should have code.committed=2
        assert data["distribution"].get("code.committed", 0) >= 2

    def test_event_distribution_missing_project(self, dashboard_server) -> None:
        status, data = _fetch("/api/events/distribution")
        assert status == 400


class TestEventTimeline:
    """Tests for GET /api/events/timeline."""

    def test_timeline_basic(self, dashboard_server) -> None:
        status, data = _fetch("/api/events/timeline?project=p-v2-01")
        assert status == 200
        assert "buckets" in data
        assert len(data["buckets"]) >= 1
        assert data["granularity"] == "1m"

    def test_timeline_with_granularity(self, dashboard_server) -> None:
        status, data = _fetch(
            "/api/events/timeline?project=p-v2-01&granularity=1h",
        )
        assert status == 200
        assert data["granularity"] == "1h"

    def test_timeline_missing_project(self, dashboard_server) -> None:
        status, data = _fetch("/api/events/timeline")
        assert status == 400


class TestTopics:
    """Tests for GET /api/topics."""

    def test_topics_endpoint(self, dashboard_server) -> None:
        status, data = _fetch("/api/topics")
        assert status == 200
        assert "topics" in data
        assert len(data["topics"]) >= 1


class TestSources:
    """Tests for GET /api/sources."""

    def test_sources_endpoint(self, dashboard_server) -> None:
        status, data = _fetch("/api/sources")
        assert status == 200
        assert "sources" in data
        assert len(data["sources"]) >= 1


class TestSubscriptions:
    """Tests for GET /api/subscriptions."""

    def test_subscriptions_endpoint(self, dashboard_server) -> None:
        status, data = _fetch("/api/subscriptions")
        assert status == 200
        assert "subscriptions" in data
        assert "total" in data


class TestMetrics:
    """Tests for GET /api/health/metrics."""

    def test_metrics_endpoint(self, dashboard_server) -> None:
        status, data = _fetch("/api/health/metrics")
        assert status == 200
        assert data["status"] == "ok"
        assert "timestamp" in data
        assert "total_events" in data
        assert "total_projects" in data
        assert "capacity" in data
        assert "usage_pct" in data
        assert "unique_sources" in data
        assert "unique_topics" in data

    def test_health_still_works(self, dashboard_server) -> None:
        status, data = _fetch("/api/health")
        assert status == 200
        assert data["status"] == "ok"


class Test404:
    """Tests for unknown routes."""

    def test_unknown_route(self, dashboard_server) -> None:
        status, data = _fetch("/api/nonexistent")
        assert status == 404
