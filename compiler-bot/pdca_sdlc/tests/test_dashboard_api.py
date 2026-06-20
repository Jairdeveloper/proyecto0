"""Tests for dashboard API — verifies all endpoints return correct data."""

from __future__ import annotations

import asyncio
import json
import tempfile
import threading
import time
from http.server import HTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from pdca_sdlc.agents.adaptation_agent import AdaptationAgent
from pdca_sdlc.agents.coder_agent import CoderAgent
from pdca_sdlc.agents.requirements_analyst import RequirementsAnalystAgent
from pdca_sdlc.core.base_agent import AgentContext
from pdca_sdlc.core.capability_registry import CapabilityRegistry
from pdca_sdlc.core.event_bus import AsyncEventBus, Event
from pdca_sdlc.core.knowledge_graph import KnowledgeGraph
from pdca_sdlc.core.llm_client import LLMClient
from pdca_sdlc.dashboard import SdlcDashboardService, create_server

DASHBOARD_PORT = 18764
DASHBOARD_URL = f"http://127.0.0.1:{DASHBOARD_PORT}"


def _fetch(path: str) -> tuple[int, dict]:
    """GET a dashboard API endpoint and return (status, parsed_json).

    Handles HTTP errors by reading the error response body.
    """
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
    """Start a dashboard server with a populated pipeline state.

    Uses asyncio.run() for synchronous test module setup.
    """
    bus = AsyncEventBus()
    kg = KnowledgeGraph()
    registry = CapabilityRegistry()
    llm = LLMClient()

    async def _setup():
        tmpdir = tempfile.mkdtemp()
        agents = [
            AdaptationAgent(
                AgentContext(bus, kg, registry, "adaptation-agent"),
                llm_client=llm,
            ),
            RequirementsAnalystAgent(
                AgentContext(bus, kg, registry, "requirements-analyst"),
                llm_client=llm,
            ),
            CoderAgent(
                AgentContext(bus, kg, registry, "coder-agent"),
                output_base=Path(tmpdir),
            ),
        ]
        for a in agents:
            await a.start()

        await bus.publish(
            Event(
                topic="project.initialized",
                source="test",
                project_id="p-dash-01",
                data={
                    "description": "API REST de productos con autenticacion",
                    "project_id": "p-dash-01",
                },
            ),
        )
        await asyncio.sleep(3)
        return agents

    agents = asyncio.run(_setup())

    service = SdlcDashboardService(kg, bus, registry)
    server: HTTPServer = create_server(
        host="127.0.0.1",
        port=DASHBOARD_PORT,
        service=service,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    time.sleep(0.2)

    yield service

    server.shutdown()
    asyncio.run(_teardown(agents))


async def _teardown(agents):
    for a in agents:
        await a.stop()


class TestDashboardAPI:
    def test_health(self, dashboard_server) -> None:
        status, data = _fetch("/api/health")
        assert status == 200
        assert data["status"] == "ok"
        assert "timestamp" in data

    def test_projects(self, dashboard_server) -> None:
        status, data = _fetch("/api/projects")
        assert status == 200
        assert "projects" in data
        assert len(data["projects"]) >= 1

    def test_project_detail(self, dashboard_server) -> None:
        status, data = _fetch("/api/projects/p-dash-01")
        assert status == 200
        assert data["project_id"] == "p-dash-01"
        assert "goal" in data
        assert "requirements" in data
        assert "artifacts" in data
        assert "event_count" in data

    def test_project_detail_not_found(self, dashboard_server) -> None:
        status, data = _fetch("/api/projects/ghost")
        assert status == 404
        assert "error" in data

    def test_trace(self, dashboard_server) -> None:
        status, data = _fetch("/api/projects/p-dash-01/trace")
        assert status == 200
        assert "trace" in data
        assert len(data["trace"]) >= 1

    def test_trace_not_found(self, dashboard_server) -> None:
        status, data = _fetch("/api/projects/ghost/trace")
        assert status == 404

    def test_agents(self, dashboard_server) -> None:
        status, data = _fetch("/api/agents")
        assert status == 200
        assert "agents" in data
        assert data["total"] >= 1

    def test_events(self, dashboard_server) -> None:
        status, data = _fetch("/api/events?project=p-dash-01")
        assert status == 200
        assert data["project_id"] == "p-dash-01"
        assert data["count"] >= 1

    def test_events_missing_project_param(self, dashboard_server) -> None:
        status, data = _fetch("/api/events")
        assert status == 400

    def test_health_returns_timestamp(self, dashboard_server) -> None:
        _, data = _fetch("/api/health")
        assert isinstance(data["timestamp"], (int, float))

    def test_projects_structure(self, dashboard_server) -> None:
        _, data = _fetch("/api/projects")
        for p in data["projects"]:
            assert "project_id" in p
            assert "complexity" in p
            assert "requirement_count" in p
            assert "artifact_count" in p
            assert "event_count" in p

    def test_static_html(self, dashboard_server) -> None:
        req = Request(f"{DASHBOARD_URL}/")
        with urlopen(req, timeout=5) as resp:
            html = resp.read().decode("utf-8")
        assert resp.status == 200
        assert "PDCA-sdlc Dashboard" in html
        assert "text/html" in resp.headers["Content-Type"]
