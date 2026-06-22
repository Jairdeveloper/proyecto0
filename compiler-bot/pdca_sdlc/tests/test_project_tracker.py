"""Tests for agents/project_tracker.py."""

from __future__ import annotations

import pytest

from pdca_sdlc.agents.project_tracker import ProjectTracker
from pdca_sdlc.core.base_agent import AgentContext
from pdca_sdlc.core.capability_registry import CapabilityRegistry
from pdca_sdlc.core.event_bus import AsyncEventBus, Event
from pdca_sdlc.core.knowledge_graph import KnowledgeGraph


class TestProjectTracker:
    """Tests para el ProjectTracker — monitoreo y metricas."""

    @pytest.fixture
    def context(self) -> AgentContext:
        return AgentContext(
            event_bus=AsyncEventBus(),
            knowledge_graph=KnowledgeGraph(),
            capability_registry=CapabilityRegistry(),
            agent_id="tracker",
        )

    @pytest.fixture
    def tracker(self, context: AgentContext) -> ProjectTracker:
        return ProjectTracker(
            context,
            report_interval=10,
            failure_threshold=3,
            pending_threshold=10,
        )

    # ── test_tracker_classification ─────────────────────────────────

    async def test_tracker_classification(
        self,
        tracker: ProjectTracker,
    ) -> None:
        """Eventos created/completed/failed clasificados correctamente."""
        # Evento created -> pending
        await tracker.handle_event(
            Event(
                topic="proyecto.p-01.requirement.created",
                source="req-analyst",
                project_id="p-01",
                data={"requirement_id": "r-001"},
            ),
        )
        report = await tracker.get_report("p-01")
        assert report is not None
        assert report["counters"]["pending"] == 1

        # Evento complete -> completed
        await tracker.handle_event(
            Event(
                topic="proyecto.p-01.design.complete",
                source="swarm",
                project_id="p-01",
                data={"req_id": "r-001"},
            ),
        )
        report = await tracker.get_report("p-01")
        assert report is not None
        assert report["counters"]["completed"] == 1
        assert report["counters"]["pending"] == 1

        # Evento failed -> failed
        await tracker.handle_event(
            Event(
                topic="proyecto.p-01.quality.gate.failed",
                source="quality-gate",
                project_id="p-01",
                data={"gate": "test", "reason": "error"},
            ),
        )
        report = await tracker.get_report("p-01")
        assert report is not None
        assert report["counters"]["failed"] == 1
        assert report["total_events"] == 3

    # ── test_tracker_report ─────────────────────────────────────────

    async def test_tracker_report(
        self,
        context: AgentContext,
    ) -> None:
        """Tras 10 eventos, reporte emitido con contadores."""
        tracker = ProjectTracker(context, report_interval=10)

        received: list[Event] = []

        async def collector(topic: str, data: object) -> None:
            if isinstance(data, Event):
                received.append(data)

        await context.event_bus.subscribe("project.progress.report", collector)

        for i in range(10):
            await tracker.handle_event(
                Event(
                    topic="proyecto.p-01.event.created"
                    if i < 5
                    else "proyecto.p-01.event.complete",
                    source="test",
                    project_id="p-01",
                    data={"seq": i},
                ),
            )

        # 10 eventos -> reporte emitido en el 10mo
        assert len(received) == 1
        payload = received[0].data
        assert payload["project_id"] == "p-01"
        assert payload["total_events"] == 10
        assert payload["counters"]["pending"] == 5
        assert payload["counters"]["completed"] == 5

    # ── test_risk_high_failure ──────────────────────────────────────

    async def test_risk_high_failure(
        self,
        context: AgentContext,
    ) -> None:
        """4 eventos failed consecutivos -> risk.identified."""
        tracker = ProjectTracker(context, failure_threshold=3)

        received: list[Event] = []

        async def collector(topic: str, data: object) -> None:
            if isinstance(data, Event):
                received.append(data)

        await context.event_bus.subscribe("risk.identified", collector)

        for i in range(4):
            await tracker.handle_event(
                Event(
                    topic="proyecto.p-01.quality.gate.failed",
                    source="test",
                    project_id="p-01",
                    data={"seq": i, "reason": "test failure"},
                ),
            )

        # Solo 1 risk.identified debe emitirse (los 4 failed > threshold=3)
        # En el 4to evento (i=3), failed_count=4 > 3 -> riesgo
        failed_risks = [e for e in received if e.data.get("type") == "high_failure_rate"]
        assert len(failed_risks) == 1
        assert failed_risks[0].data["failed_count"] == 4

    # ── test_risk_timeout ───────────────────────────────────────────

    async def test_risk_timeout(
        self,
        context: AgentContext,
    ) -> None:
        """Evento swarm_timeout -> risk.identified (blocked_task)."""
        tracker = ProjectTracker(context)

        received: list[Event] = []

        async def collector(topic: str, data: object) -> None:
            if isinstance(data, Event):
                received.append(data)

        await context.event_bus.subscribe("risk.identified", collector)

        await tracker.handle_event(
            Event(
                topic="proyecto.p-01.risk.identified",
                source="swarm-coordinator",
                project_id="p-01",
                data={
                    "type": "swarm_timeout",
                    "req_id": "req-003",
                    "pending": ["security.review.completed"],
                },
            ),
        )

        blocked = [e for e in received if e.data.get("type") == "blocked_task"]
        assert len(blocked) == 1
        assert blocked[0].data["req_id"] == "req-003"
        assert "security.review.completed" in blocked[0].data["pending"]

    # ── test_tracker_no_events ──────────────────────────────────────

    async def test_tracker_no_events(
        self,
        tracker: ProjectTracker,
    ) -> None:
        """Sin eventos -> no emite nada."""
        report = await tracker.get_report("p-01")
        assert report is None
