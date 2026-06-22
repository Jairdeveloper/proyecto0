"""Integration tests for F2 — Deep-Path pipeline end-to-end.

Tests the deep-path with ArchitectAgent, QualityGate, VerificationAgent,
SwarmDetector, and ProjectTracker wired together through the event bus.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from pdca_sdlc.agents.adaptation_agent import AdaptationAgent
from pdca_sdlc.agents.architect_agent import ArchitectAgent
from pdca_sdlc.agents.coder_agent import CoderAgent
from pdca_sdlc.agents.project_tracker import ProjectTracker
from pdca_sdlc.agents.requirements_analyst import RequirementsAnalystAgent
from pdca_sdlc.agents.verification_agent import VerificationAgent
from pdca_sdlc.core.base_agent import AgentContext
from pdca_sdlc.core.capability_registry import CapabilityRegistry
from pdca_sdlc.core.event_bus import AsyncEventBus, Event
from pdca_sdlc.core.knowledge_graph import EdgeType, KnowledgeGraph, Node, NodeType
from pdca_sdlc.core.llm_client import LLMClient
from pdca_sdlc.core.quality_gate import (
    QualityGate,
    gate_componentes_tienen_trazabilidad,
    gate_modulos_tienen_trazabilidad,
    gate_requisitos_tienen_aceptacion,
)
from pdca_sdlc.core.swarm_coordinator import SwarmDetector


def _make_f2_pipeline(
    bus: AsyncEventBus,
    kg: KnowledgeGraph,
    registry: CapabilityRegistry,
    llm: LLMClient | None = None,
    tracker_report_interval: int = 10,
) -> tuple[
    QualityGate,
    SwarmDetector,
    list[Any],
]:
    """Create all F1 + F2 infrastructure and agents.

    Args:
        bus: Event bus.
        kg: Knowledge graph.
        registry: Capability registry.
        llm: Optional LLM client (default: mock).
        tracker_report_interval: ProjectTracker report interval (default: 10).

    Returns:
        Tuple of (quality_gate, swarm_detector, agent_list).
    """
    llm = llm or LLMClient()

    qg = QualityGate(bus, kg)
    for name, fn in [
        ("requisitos_tienen_aceptacion", gate_requisitos_tienen_aceptacion),
        ("componentes_tienen_trazabilidad", gate_componentes_tienen_trazabilidad),
        ("modulos_tienen_trazabilidad", gate_modulos_tienen_trazabilidad),
    ]:
        qg.register_gate(name, fn)

    swarm = SwarmDetector(bus, kg)

    agents: list[Any] = [
        AdaptationAgent(
            AgentContext(bus, kg, registry, "adaptation-agent"),
            llm_client=llm,
        ),
        RequirementsAnalystAgent(
            AgentContext(bus, kg, registry, "requirements-analyst"),
            llm_client=llm,
        ),
        CoderAgent(AgentContext(bus, kg, registry, "coder-agent")),
        ArchitectAgent(
            AgentContext(bus, kg, registry, "architect-agent"),
            llm_client=llm,
        ),
        VerificationAgent(
            AgentContext(bus, kg, registry, "verification-agent"),
            llm_client=llm,
            quality_gate=qg,
        ),
        ProjectTracker(
            AgentContext(bus, kg, registry, "project-tracker"),
            report_interval=tracker_report_interval,
        ),
    ]

    return qg, swarm, agents


@pytest.mark.asyncio
async def test_deep_path_complete() -> None:
    """Proyecto COMPLEX -> architect + verification + quality gates -> flujo completo."""
    bus = AsyncEventBus()
    kg = KnowledgeGraph()
    registry = CapabilityRegistry()
    llm = LLMClient()

    qg, swarm, agents = _make_f2_pipeline(bus, kg, registry, llm)

    # Wire swarm to bus
    async def _swarm_handler(topic: str, data: object) -> None:
        if isinstance(data, Event):
            await swarm.on_event(data)

    await bus.subscribe(">", _swarm_handler)

    # Collect events
    events: list[Event] = []

    async def collector(topic: str, data: object) -> None:
        if isinstance(data, Event):
            events.append(data)

    for topic in [
        "architecture.proposed",
        "design.detailed.complete",
        "verification.complete",
        "code.committed",
    ]:
        await bus.subscribe(topic, collector)

    for agent in agents:
        await agent.start()

    await bus.publish(
        Event(
            topic="project.initialized",
            source="test",
            project_id="p-f2-01",
            data={
                "description": ("Sistema multi-tenant con microservicios y API REST de productos"),
                "project_id": "p-f2-01",
            },
        ),
    )

    await asyncio.sleep(5)

    # Deep-Path events must have been emitted
    topics_found = {e.topic for e in events}
    assert "architecture.proposed" in topics_found, (
        "COMPLEX project must emit architecture.proposed"
    )
    assert "design.detailed.complete" in topics_found, (
        "COMPLEX project must emit design.detailed.complete"
    )
    assert "code.committed" in topics_found, "Pipeline must emit code.committed"
    assert "verification.complete" in topics_found, "Pipeline must emit verification.complete"

    # KG must have traceability nodes
    reqs = kg.query(node_type=NodeType.requirement)
    assert len(reqs) >= 1, "KG must contain requirements"

    components = kg.query(node_type=NodeType.component)
    assert len(components) >= 1, "KG must contain components (ArchitectAgent fallback)"

    for agent in agents:
        await agent.stop()


@pytest.mark.asyncio
async def test_quality_gate_blocks_flow() -> None:
    """Code module sin trazabilidad -> quality.gate.failed + risk.identified."""
    bus = AsyncEventBus()
    kg = KnowledgeGraph()
    registry = CapabilityRegistry()
    llm = LLMClient()

    qg, swarm, agents = _make_f2_pipeline(bus, kg, registry, llm)

    # Seed KG: code module without traceability (no IMPLEMENTS edges)
    kg.add_node(
        Node(
            id="mod-orphan-p01",
            node_type=NodeType.code_module,
            properties={"name": "orphan.module"},
        ),
    )

    # Collect quality.gate.failed and risk.identified
    gate_events: list[Event] = []
    risk_events: list[Event] = []

    async def gate_collector(topic: str, data: object) -> None:
        if isinstance(data, Event):
            gate_events.append(data)

    async def risk_collector(topic: str, data: object) -> None:
        if isinstance(data, Event):
            risk_events.append(data)

    await bus.subscribe("proyecto.p-01.quality.gate.failed", gate_collector)
    await bus.subscribe("proyecto.p-01.risk.identified", risk_collector)

    for agent in agents:
        await agent.start()

    await asyncio.sleep(0.5)

    # Fire code.committed for orphan module
    await bus.publish(
        Event(
            topic="code.committed",
            source="coder-agent",
            project_id="p-01",
            data={
                "module_id": "mod-orphan-p01",
                "component": "orphan",
                "files": [],
                "tests_passed": True,
            },
        ),
    )

    await asyncio.sleep(2)

    # Quality gates should fire (module without traceability fails the gate)
    assert len(gate_events) >= 1, "Quality gate must fire for orphan module"
    payload = gate_events[0].data
    assert "gate" in payload, "Gate event must name the failing gate"

    for agent in agents:
        await agent.stop()


@pytest.mark.asyncio
async def test_fast_path_bypasses_architect() -> None:
    """Proyecto SIMPLE -> Coder directo, Architect no interviene."""
    bus = AsyncEventBus()
    kg = KnowledgeGraph()
    registry = CapabilityRegistry()
    llm = LLMClient()

    qg, swarm, agents = _make_f2_pipeline(bus, kg, registry, llm)

    arch_events: list[Event] = []

    async def arch_collector(topic: str, data: object) -> None:
        if isinstance(data, Event):
            arch_events.append(data)

    await bus.subscribe("architecture.proposed", arch_collector)

    for agent in agents:
        await agent.start()

    await bus.publish(
        Event(
            topic="project.initialized",
            source="test",
            project_id="p-f2-03",
            data={
                "description": "Hola mundo simple",
                "project_id": "p-f2-03",
            },
        ),
    )

    await asyncio.sleep(4)

    # SIMPLE project must NOT emit architecture.proposed
    assert len(arch_events) == 0, "SIMPLE project must not emit architecture.proposed"

    # But code must still be generated
    code_events = kg.query(node_type=NodeType.artifact)
    assert len(code_events) >= 1, "SIMPLE project must still generate code"

    for agent in agents:
        await agent.stop()


@pytest.mark.asyncio
async def test_traceability_chain() -> None:
    """Cadena module -> component -> requirement -> goal en KG."""
    bus = AsyncEventBus()
    kg = KnowledgeGraph()
    registry = CapabilityRegistry()
    llm = LLMClient()

    qg, swarm, agents = _make_f2_pipeline(bus, kg, registry, llm)

    async def _swarm_handler(topic: str, data: object) -> None:
        if isinstance(data, Event):
            await swarm.on_event(data)

    await bus.subscribe(">", _swarm_handler)

    for agent in agents:
        await agent.start()

    await bus.publish(
        Event(
            topic="project.initialized",
            source="test",
            project_id="p-f2-04",
            data={
                "description": ("Sistema multi-tenant con microservicios y autenticacion OAuth2"),
                "project_id": "p-f2-04",
            },
        ),
    )

    await asyncio.sleep(5)

    # Goal node exists
    goal = kg.get_node("goal-p-f2-04")
    assert goal is not None, "Goal node must exist"

    # Requirements exist
    reqs = kg.query(node_type=NodeType.requirement)
    assert len(reqs) >= 1, "Requirements must exist"

    # Components exist (from ArchitectAgent fallback)
    comps = kg.query(node_type=NodeType.component)
    assert len(comps) >= 1, "Components must exist"

    # Each component should have IMPLEMENTS edges to requirements
    chain_ok = False
    for comp in comps:
        outgoing = kg.get_outgoing(comp.id)
        implements = [e for e in outgoing if e.edge_type == EdgeType.implements]
        if implements:
            # At least one target is a requirement
            targets = {e.target_id for e in implements}
            req_ids = {r.id for r in reqs}
            if targets & req_ids:
                chain_ok = True
                break
    assert chain_ok, "At least one component must implement a requirement"

    # Artifacts exist (from CoderAgent)
    artifacts = kg.query(node_type=NodeType.artifact)
    assert len(artifacts) >= 1, "Artifacts must exist"

    for agent in agents:
        await agent.stop()


@pytest.mark.asyncio
async def test_swarm_design_complete() -> None:
    """architecture.proposed + security.review -> design.complete via swarm."""
    bus = AsyncEventBus()
    kg = KnowledgeGraph()
    registry = CapabilityRegistry()
    llm = LLMClient()

    qg, swarm, agents = _make_f2_pipeline(bus, kg, registry, llm)

    # Wire swarm to bus
    async def _swarm_handler(topic: str, data: object) -> None:
        if isinstance(data, Event):
            await swarm.on_event(data)

    await bus.subscribe(">", _swarm_handler)

    # Register swarm expectation
    swarm.expect(
        "req-swarm-01",
        ["architecture.proposed", "security.review.completed"],
        "design.complete",
        timeout=30.0,
    )

    # Subscribe to design.complete
    design_events: list[Event] = []

    async def design_collector(topic: str, data: object) -> None:
        if isinstance(data, Event):
            design_events.append(data)

    await bus.subscribe("design.complete", design_collector)

    for agent in agents:
        await agent.start()

    await asyncio.sleep(0.5)

    # Send first event — still incomplete
    await bus.publish(
        Event(
            topic="architecture.proposed",
            source="architect",
            project_id="p-01",
            data={"requirement_id": "req-swarm-01"},
        ),
    )
    await asyncio.sleep(0.2)
    assert len(design_events) == 0, "1/2 events must not trigger completion"

    # Send second event — completion
    await bus.publish(
        Event(
            topic="security.review.completed",
            source="security",
            project_id="p-01",
            data={"requirement_id": "req-swarm-01"},
        ),
    )
    await asyncio.sleep(0.2)

    assert len(design_events) == 1, "2/2 events must trigger design.complete"
    assert design_events[0].data["req_id"] == "req-swarm-01"

    for agent in agents:
        await agent.stop()


@pytest.mark.asyncio
async def test_tracker_reports_during_flow() -> None:
    """Durante flujo deep-path, tracker emite reportes."""
    bus = AsyncEventBus()
    kg = KnowledgeGraph()
    registry = CapabilityRegistry()
    llm = LLMClient()

    qg, swarm, agents = _make_f2_pipeline(
        bus,
        kg,
        registry,
        llm,
        tracker_report_interval=3,
    )

    # Wire swarm
    async def _swarm_handler(topic: str, data: object) -> None:
        if isinstance(data, Event):
            await swarm.on_event(data)

    await bus.subscribe(">", _swarm_handler)

    # Subscribe to progress reports
    reports: list[Event] = []

    async def report_collector(topic: str, data: object) -> None:
        if isinstance(data, Event):
            reports.append(data)

    await bus.subscribe("project.progress.report", report_collector)

    for agent in agents:
        await agent.start()

    await bus.publish(
        Event(
            topic="project.initialized",
            source="test",
            project_id="p-f2-06",
            data={
                "description": ("Sistema multi-tenant con microservicios y autenticacion OAuth2"),
                "project_id": "p-f2-06",
            },
        ),
    )

    await asyncio.sleep(5)

    # ProjectTracker must have emitted at least one progress report
    assert len(reports) >= 1, "ProjectTracker must emit at least one progress report"
    first = reports[0].data
    assert first["project_id"] == "p-f2-06"
    assert "total_events" in first
    assert "counters" in first

    for agent in agents:
        await agent.stop()


@pytest.mark.asyncio
async def test_design_detailed_after_architecture() -> None:
    """design.detailed.complete no causa crash sin architecture.proposed previo."""
    bus = AsyncEventBus()
    kg = KnowledgeGraph()
    registry = CapabilityRegistry()
    llm = LLMClient()

    qg, swarm, agents = _make_f2_pipeline(bus, kg, registry, llm)

    async def _swarm_handler(topic: str, data: object) -> None:
        if isinstance(data, Event):
            await swarm.on_event(data)

    await bus.subscribe(">", _swarm_handler)

    for agent in agents:
        await agent.start()

    await bus.publish(
        Event(
            topic="design.detailed.complete",
            source="architect",
            project_id="p-f2-edge",
            data={
                "component_ids": ["comp-001"],
                "requirement_ids": ["r-001"],
            },
        ),
    )

    await asyncio.sleep(2)

    kg_components = kg.query(node_type=NodeType.component)
    assert isinstance(kg_components, list)

    for agent in agents:
        await agent.stop()
