"""Tests for core/swarm_coordinator.py."""

from __future__ import annotations

import pytest

from pdca_sdlc.core.event_bus import AsyncEventBus, Event
from pdca_sdlc.core.knowledge_graph import KnowledgeGraph
from pdca_sdlc.core.swarm_coordinator import SwarmDetector


class TestSwarmDetector:
    """Tests para el SwarmDetector — deteccion de completitud."""

    @pytest.fixture
    def event_bus(self) -> AsyncEventBus:
        return AsyncEventBus()

    @pytest.fixture
    def kg(self) -> KnowledgeGraph:
        return KnowledgeGraph()

    @pytest.fixture
    def detector(
        self,
        event_bus: AsyncEventBus,
        kg: KnowledgeGraph,
    ) -> SwarmDetector:
        return SwarmDetector(event_bus, kg)

    # ── test_swarm_completion ───────────────────────────────────────

    async def test_swarm_completion(
        self,
        detector: SwarmDetector,
        event_bus: AsyncEventBus,
    ) -> None:
        """2/2 eventos esperados -> completion emitido."""
        detector.expect(
            "req-001",
            ["architecture.proposed", "security.review.completed"],
            "design.complete",
        )

        received: list[Event] = []

        async def collector(topic: str, data: object) -> None:
            if isinstance(data, Event):
                received.append(data)

        await event_bus.subscribe("design.complete", collector)

        await detector.on_event(
            Event(
                topic="architecture.proposed",
                source="architect",
                project_id="p-01",
                data={"requirement_id": "req-001"},
            ),
        )
        assert len(received) == 0  # Aun no completo

        await detector.on_event(
            Event(
                topic="security.review.completed",
                source="security",
                project_id="p-01",
                data={"requirement_id": "req-001"},
            ),
        )
        assert len(received) == 1
        assert received[0].topic == "design.complete"
        assert received[0].data["req_id"] == "req-001"
        assert "architecture.proposed" in received[0].data["events"]
        assert "security.review.completed" in received[0].data["events"]

    # ── test_swarm_partial ──────────────────────────────────────────

    async def test_swarm_partial(
        self,
        detector: SwarmDetector,
        event_bus: AsyncEventBus,
    ) -> None:
        """1/2 eventos -> completion NO emitido aun."""
        detector.expect(
            "req-002",
            ["architecture.proposed", "ux.review.completed"],
            "design.complete",
        )

        received: list[Event] = []

        async def collector(topic: str, data: object) -> None:
            if isinstance(data, Event):
                received.append(data)

        await event_bus.subscribe("design.complete", collector)

        await detector.on_event(
            Event(
                topic="architecture.proposed",
                source="architect",
                project_id="p-01",
                data={"requirement_id": "req-002"},
            ),
        )
        assert len(received) == 0  # Solo 1/2, no debe emitir

    # ── test_swarm_timeout ──────────────────────────────────────────

    async def test_swarm_timeout(
        self,
        detector: SwarmDetector,
        event_bus: AsyncEventBus,
    ) -> None:
        """Solo 1/2 eventos recibido en timeout -> risk.identified."""
        detector.expect(
            "req-003",
            ["architecture.proposed", "security.review.completed"],
            "design.complete",
            timeout=-1.0,  # Timeout inmediato
        )

        received: list[Event] = []

        async def collector(topic: str, data: object) -> None:
            if isinstance(data, Event):
                received.append(data)

        await event_bus.subscribe("proyecto.p-01.risk.identified", collector)

        await detector.on_event(
            Event(
                topic="architecture.proposed",
                source="architect",
                project_id="p-01",
                data={"requirement_id": "req-003"},
            ),
        )
        assert len(received) == 0  # Timeout aun no evaluado

        await detector.check_timeouts()

        assert len(received) == 1
        payload = received[0].data
        assert payload["type"] == "swarm_timeout"
        assert payload["req_id"] == "req-003"
        assert "security.review.completed" in payload["pending"]

    # ── test_swarm_unrelated_event ──────────────────────────────────

    async def test_swarm_unrelated_event(
        self,
        detector: SwarmDetector,
    ) -> None:
        """Evento no esperado -> ignorado, expectativa intacta."""
        detector.expect(
            "req-004",
            ["architecture.proposed"],
            "design.complete",
        )

        await detector.on_event(
            Event(
                topic="unrelated.event",
                source="some-agent",
                project_id="p-01",
                data={"requirement_id": "req-004"},
            ),
        )

        # La expectativa debe seguir activa con el topic aun pendiente
        exp = detector.active_expectations["req-004"]
        assert exp["expected"]["architecture.proposed"] is False

    # ── test_swarm_multiple_requests ────────────────────────────────

    async def test_swarm_multiple_requests(
        self,
        detector: SwarmDetector,
        event_bus: AsyncEventBus,
    ) -> None:
        """2 reqs independientes -> cada uno completa por separado."""
        detector.expect(
            "req-010",
            ["architecture.proposed"],
            "design.complete.010",
        )
        detector.expect(
            "req-020",
            ["architecture.proposed"],
            "design.complete.020",
        )

        received_010: list[Event] = []
        received_020: list[Event] = []

        async def collector_010(topic: str, data: object) -> None:
            if isinstance(data, Event):
                received_010.append(data)

        async def collector_020(topic: str, data: object) -> None:
            if isinstance(data, Event):
                received_020.append(data)

        await event_bus.subscribe("design.complete.010", collector_010)
        await event_bus.subscribe("design.complete.020", collector_020)

        # Solo req-010 recibe su evento
        await detector.on_event(
            Event(
                topic="architecture.proposed",
                source="architect",
                project_id="p-01",
                data={"requirement_id": "req-010"},
            ),
        )

        assert len(received_010) == 1
        assert received_010[0].data["req_id"] == "req-010"
        assert len(received_020) == 0  # req-020 aun pendiente

        # Ahora req-020 recibe su evento
        await detector.on_event(
            Event(
                topic="architecture.proposed",
                source="architect",
                project_id="p-01",
                data={"requirement_id": "req-020"},
            ),
        )

        assert len(received_020) == 1
        assert received_020[0].data["req_id"] == "req-020"
