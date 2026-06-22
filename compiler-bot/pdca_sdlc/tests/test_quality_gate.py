"""Tests for core/quality_gate.py."""

from __future__ import annotations

import pytest

from pdca_sdlc.core.event_bus import AsyncEventBus, Event
from pdca_sdlc.core.knowledge_graph import (
    Edge,
    EdgeType,
    KnowledgeGraph,
    Node,
    NodeType,
)
from pdca_sdlc.core.quality_gate import (
    GateResult,
    QualityGate,
    gate_componentes_tienen_trazabilidad,
    gate_modulos_tienen_trazabilidad,
    gate_requisitos_tienen_aceptacion,
)


class TestQualityGate:
    """Tests para la clase QualityGate y sus gates predefinidos."""

    @pytest.fixture
    def event_bus(self) -> AsyncEventBus:
        return AsyncEventBus()

    @pytest.fixture
    def kg(self) -> KnowledgeGraph:
        return KnowledgeGraph()

    @pytest.fixture
    def quality_gate(self, event_bus: AsyncEventBus, kg: KnowledgeGraph) -> QualityGate:
        return QualityGate(event_bus, kg)

    # ── gate_requisitos_tienen_aceptacion ──────────────────────────

    def test_gate_passes(
        self,
        kg: KnowledgeGraph,
        quality_gate: QualityGate,
    ) -> None:
        """Todos los requisitos con acceptance_criteria -> PASSED."""
        kg.add_node(
            Node(
                id="r-001",
                node_type=NodeType.requirement,
                properties={
                    "text": "Login",
                    "acceptance_criteria": ["Usuario puede loguearse"],
                },
            ),
        )
        result = gate_requisitos_tienen_aceptacion(kg, "p-01", {})
        assert result is True

    def test_gate_fails(
        self,
        kg: KnowledgeGraph,
        quality_gate: QualityGate,
    ) -> None:
        """Un requisito sin acceptance_criteria -> FAILED con mensaje."""
        kg.add_node(
            Node(
                id="r-001",
                node_type=NodeType.requirement,
                properties={"text": "Login sin criterios"},
            ),
        )
        result = gate_requisitos_tienen_aceptacion(kg, "p-01", {})
        assert result is not True
        assert isinstance(result, str)
        assert "r-001" in result
        assert "criterios" in result

    def test_gate_empty_criteria_fails(
        self,
        kg: KnowledgeGraph,
        quality_gate: QualityGate,
    ) -> None:
        """Acceptance_criteria vacio tambien cuenta como fallo."""
        kg.add_node(
            Node(
                id="r-001",
                node_type=NodeType.requirement,
                properties={
                    "text": "Login",
                    "acceptance_criteria": [],
                },
            ),
        )
        result = gate_requisitos_tienen_aceptacion(kg, "p-01", {})
        assert result is not True

    # ── gate_not_found ─────────────────────────────────────────────

    async def test_gate_not_found(
        self,
        quality_gate: QualityGate,
    ) -> None:
        """Gate inexistente -> PASSED."""
        result = await quality_gate.evaluate("gate_que_no_existe", "p-01", {})
        assert result == GateResult.PASSED

    # ── gate_componentes_tienen_trazabilidad ───────────────────────

    def test_gate_component_traceability(
        self,
        kg: KnowledgeGraph,
        quality_gate: QualityGate,
    ) -> None:
        """Componente sin aristas IMPLEMENTS -> FAILED."""
        kg.add_node(
            Node(
                id="comp-auth-p01",
                node_type=NodeType.component,
                properties={"name": "AuthComponent"},
            ),
        )
        result = gate_componentes_tienen_trazabilidad(kg, "p-01", {})
        assert result is not True
        assert isinstance(result, str)
        assert "comp-auth-p01" in result

    def test_gate_component_with_trace_passes(
        self,
        kg: KnowledgeGraph,
        quality_gate: QualityGate,
    ) -> None:
        """Componente con arista IMPLEMENTS -> PASSED."""
        kg.add_node(
            Node(
                id="comp-auth-p01",
                node_type=NodeType.component,
                properties={"name": "AuthComponent"},
            ),
        )
        kg.add_node(
            Node(
                id="r-001",
                node_type=NodeType.requirement,
                properties={"text": "Login"},
            ),
        )
        kg.add_edge(
            Edge(
                source_id="comp-auth-p01",
                target_id="r-001",
                edge_type=EdgeType.implements,
            ),
        )
        result = gate_componentes_tienen_trazabilidad(kg, "p-01", {})
        assert result is True

    # ── gate_modulos_tienen_trazabilidad ───────────────────────────

    def test_gate_module_traceability(
        self,
        kg: KnowledgeGraph,
        quality_gate: QualityGate,
    ) -> None:
        """Modulo sin aristas IMPLEMENTS -> FAILED."""
        kg.add_node(
            Node(
                id="mod-auth-p01",
                node_type=NodeType.code_module,
                properties={"name": "auth.module"},
            ),
        )
        result = gate_modulos_tienen_trazabilidad(kg, "p-01", {})
        assert result is not True
        assert isinstance(result, str)
        assert "mod-auth-p01" in result

    def test_gate_module_with_trace_passes(
        self,
        kg: KnowledgeGraph,
        quality_gate: QualityGate,
    ) -> None:
        """Modulo con arista IMPLEMENTS -> PASSED."""
        kg.add_node(
            Node(
                id="mod-auth-p01",
                node_type=NodeType.code_module,
                properties={"name": "auth.module"},
            ),
        )
        kg.add_node(
            Node(
                id="comp-auth-p01",
                node_type=NodeType.component,
                properties={"name": "AuthComponent"},
            ),
        )
        kg.add_edge(
            Edge(
                source_id="mod-auth-p01",
                target_id="comp-auth-p01",
                edge_type=EdgeType.implements,
            ),
        )
        result = gate_modulos_tienen_trazabilidad(kg, "p-01", {})
        assert result is True

    # ── evaluate end-to-end ────────────────────────────────────────

    async def test_gate_evaluate_registered_passes(
        self,
        quality_gate: QualityGate,
        kg: KnowledgeGraph,
    ) -> None:
        """evaluate() con gate registrado que pasa -> PASSED."""
        quality_gate.register_gate(
            "req_tienen_aceptacion",
            gate_requisitos_tienen_aceptacion,
        )
        kg.add_node(
            Node(
                id="r-001",
                node_type=NodeType.requirement,
                properties={
                    "text": "Login",
                    "acceptance_criteria": ["Criterio valido"],
                },
            ),
        )
        result = await quality_gate.evaluate("req_tienen_aceptacion", "p-01", {})
        assert result == GateResult.PASSED

    async def test_gate_evaluate_registered_fails(
        self,
        quality_gate: QualityGate,
        kg: KnowledgeGraph,
    ) -> None:
        """evaluate() con gate registrado que falla -> FAILED."""
        quality_gate.register_gate(
            "req_tienen_aceptacion",
            gate_requisitos_tienen_aceptacion,
        )
        kg.add_node(
            Node(
                id="r-001",
                node_type=NodeType.requirement,
                properties={"text": "Login sin criterios"},
            ),
        )
        result = await quality_gate.evaluate("req_tienen_aceptacion", "p-01", {})
        assert result == GateResult.FAILED

    async def test_gate_event_emitted(
        self,
        quality_gate: QualityGate,
        kg: KnowledgeGraph,
        event_bus: AsyncEventBus,
    ) -> None:
        """Gate fail publicado como evento en el bus."""
        quality_gate.register_gate(
            "req_tienen_aceptacion",
            gate_requisitos_tienen_aceptacion,
        )
        kg.add_node(
            Node(
                id="r-001",
                node_type=NodeType.requirement,
                properties={"text": "Sin criterios"},
            ),
        )

        received: list[dict[str, object]] = []

        async def collector(topic: str, data: object) -> None:
            if isinstance(data, Event):
                received.append(data.data)

        await event_bus.subscribe("proyecto.p-01.quality.gate.failed", collector)
        result = await quality_gate.evaluate("req_tienen_aceptacion", "p-01", {})
        assert result == GateResult.FAILED
        assert len(received) == 1
        assert received[0]["gate"] == "req_tienen_aceptacion"
        assert "reason" in received[0]

    # ── StageSubject observer notification ─────────────────────────

    async def test_gate_notifies_subject(
        self,
        quality_gate: QualityGate,
        kg: KnowledgeGraph,
    ) -> None:
        """Gate fallido notifica al StageSubject."""
        quality_gate.register_gate(
            "req_tienen_aceptacion",
            gate_requisitos_tienen_aceptacion,
        )
        kg.add_node(
            Node(
                id="r-001",
                node_type=NodeType.requirement,
                properties={"text": "Sin criterios"},
            ),
        )

        received_events: list[object] = []

        class CollectorObserver:
            def on_event(self, event: object) -> None:
                received_events.append(event)

        observer = CollectorObserver()
        quality_gate.subject.attach(observer)

        await quality_gate.evaluate("req_tienen_aceptacion", "p-01", {})

        quality_gate.subject.detach(observer)
        assert len(received_events) == 1
        stage_ev = received_events[0]
        assert hasattr(stage_ev, "stage")
        assert stage_ev.stage == "gate.req_tienen_aceptacion"
        assert hasattr(stage_ev, "success")
        assert stage_ev.success is False

    # ── Dia 18: Casos borde ─────────────────────────────────────────

    async def test_quality_gate_multiple_gates(
        self,
        kg: KnowledgeGraph,
        event_bus: AsyncEventBus,
    ) -> None:
        """3 gates registrados, 1 falla -> FAILED, 2 no evaluados."""
        qg = QualityGate(event_bus, kg)
        call_order: list[str] = []

        def gate_a(_kg: object, _pid: str, _ctx: object) -> bool | str:
            call_order.append("gate_a")
            return True

        def gate_b(_kg: object, _pid: str, _ctx: object) -> bool | str:
            call_order.append("gate_b")
            return "Gate B failure"

        def gate_c(_kg: object, _pid: str, _ctx: object) -> bool | str:
            call_order.append("gate_c")
            return True

        qg.register_gate("gate_a", gate_a)
        qg.register_gate("gate_b", gate_b)
        qg.register_gate("gate_c", gate_c)

        # Evaluate gates in sequence — gate_b fails, gate_c must NOT be called
        result_a = await qg.evaluate("gate_a", "p-01")
        assert result_a == GateResult.PASSED

        result_b = await qg.evaluate("gate_b", "p-01")
        assert result_b == GateResult.FAILED

        # gate_c is never evaluated if calling code stops after failure
        assert "gate_c" not in call_order, "Gate C should not be evaluated after gate B failed"
        assert call_order == ["gate_a", "gate_b"], "Only gates A and B should have been called"
