"""Integration tests for F1 — full pipeline end-to-end.

Tests the fast-path: project.initialized -> adaptation -> requirements -> code.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import pytest

from pdca_sdlc.agents.adaptation_agent import AdaptationAgent
from pdca_sdlc.agents.coder_agent import CoderAgent
from pdca_sdlc.agents.requirements_analyst import RequirementsAnalystAgent
from pdca_sdlc.core.base_agent import AgentContext
from pdca_sdlc.core.capability_registry import CapabilityRegistry
from pdca_sdlc.core.event_bus import AsyncEventBus, Event
from pdca_sdlc.core.knowledge_graph import KnowledgeGraph, NodeType
from pdca_sdlc.core.llm_client import LLMClient


def _make_agents() -> tuple[
    AsyncEventBus,
    KnowledgeGraph,
    list[AdaptationAgent | RequirementsAnalystAgent | CoderAgent],
]:
    """Create shared infrastructure and agents with proper per-agent contexts."""
    bus = AsyncEventBus()
    kg = KnowledgeGraph()
    registry = CapabilityRegistry()
    llm = LLMClient()

    agents: list[AdaptationAgent | RequirementsAnalystAgent | CoderAgent] = [
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
        ),
    ]
    return bus, kg, agents


@pytest.mark.asyncio
async def test_fast_path_complete() -> None:
    """Full pipeline: "CRUD productos con API REST" -> goal + reqs + code."""
    bus, kg, agents = _make_agents()

    for a in agents:
        await a.start()

    with tempfile.TemporaryDirectory() as tmp:
        agents[2]._output_base = Path(tmp)

        await bus.publish(
            Event(
                topic="project.initialized",
                source="test",
                project_id="p-int-01",
                data={
                    "description": "CRUD de productos con API REST y autenticacion JWT",
                    "project_id": "p-int-01",
                },
            ),
        )

        await asyncio.sleep(3)

        # 1) KG tiene nodo goal
        goal = kg.get_node("goal-p-int-01")
        assert goal is not None, "KG debe contener nodo goal"
        assert goal.node_type == NodeType.goal
        assert goal.properties.get("complexity") in ("simple", "moderate", "complex")

        # 2) KG tiene nodos requirement
        reqs = kg.query(node_type=NodeType.requirement)
        assert len(reqs) >= 1, "KG debe contener al menos 1 requisito"

        # 3) KG tiene nodos artifact (codigo generado)
        artifacts = kg.query(node_type=NodeType.artifact)
        assert len(artifacts) >= 1, "KG debe contener al menos 1 artifact"

        # 4) Al menos un artifact tiene status committed
        committed = [a for a in artifacts if a.properties.get("status") == "committed"]
        assert len(committed) >= 1, "Al menos un artifact debe estar committed"

    for a in agents:
        await a.stop()


@pytest.mark.asyncio
async def test_fast_path_traceability() -> None:
    """Traceability: goal -> requirements -> artifacts."""
    bus, kg, agents = _make_agents()

    for a in agents:
        await a.start()

    with tempfile.TemporaryDirectory() as tmp:
        agents[2]._output_base = Path(tmp)

        await bus.publish(
            Event(
                topic="project.initialized",
                source="test",
                project_id="p-int-02",
                data={
                    "description": "Entidad Product con API REST",
                    "project_id": "p-int-02",
                },
            ),
        )

        await asyncio.sleep(3)

        # goal existe
        goal = kg.get_node("goal-p-int-02")
        assert goal is not None

        # requirements existen
        reqs = kg.query(node_type=NodeType.requirement)
        assert len(reqs) >= 1

        # artifacts existen
        artifacts = kg.query(node_type=NodeType.artifact)
        assert len(artifacts) >= 1

        # artifacts tienen project_id en properties
        for art in artifacts:
            assert art.properties.get("project_id") == "p-int-02", (
                f"Artifact {art.id} debe referenciar al proyecto"
            )

    for a in agents:
        await a.stop()


@pytest.mark.asyncio
async def test_sequential_processing() -> None:
    """Events emitted in correct order: adaptation -> requirement -> code."""
    bus, kg, agents = _make_agents()

    order: list[str] = []

    async def record_adaptation(topic: str, data: object) -> None:
        if isinstance(data, Event) and data.source != "test":
            order.append("adaptation.complete")

    async def record_requirement(topic: str, data: object) -> None:
        if isinstance(data, Event) and data.source != "test":
            order.append("requirement.created")

    async def record_code(topic: str, data: object) -> None:
        if isinstance(data, Event) and data.source != "test":
            order.append("code.committed")

    await bus.subscribe("adaptation.complete", record_adaptation)
    await bus.subscribe("requirement.created", record_requirement)
    await bus.subscribe("code.committed", record_code)

    for a in agents:
        await a.start()

    with tempfile.TemporaryDirectory() as tmp:
        agents[2]._output_base = Path(tmp)

        await bus.publish(
            Event(
                topic="project.initialized",
                source="test",
                project_id="p-int-03",
                data={
                    "description": "CRUD con login y base de datos",
                    "project_id": "p-int-03",
                },
            ),
        )

        await asyncio.sleep(3)

        # The events must appear in order: adaptation -> requirement -> code
        assert "adaptation.complete" in order, "Debe emitirse adaptation.complete"
        assert "requirement.created" in order, "Debe emitirse requirement.created"
        assert "code.committed" in order, "Debe emitirse code.committed"

        def _first_index(items: list[str], target: str) -> int:
            for i, e in enumerate(items):
                if e == target:
                    return i
            return -1

        adaptation_idx = _first_index(order, "adaptation.complete")
        requirement_idx = _first_index(order, "requirement.created")
        code_idx = _first_index(order, "code.committed")

        assert adaptation_idx < requirement_idx, (
            "adaptation.complete debe emitirse antes de requirement.created"
        )
        assert requirement_idx < code_idx, (
            "requirement.created debe emitirse antes de code.committed"
        )

    for a in agents:
        await a.stop()


@pytest.mark.asyncio
async def test_error_handling_empty_description() -> None:
    """Empty description is handled gracefully — no crash, no goal node."""
    bus, kg, agents = _make_agents()

    for a in agents:
        await a.start()

    await bus.publish(
        Event(
            topic="project.initialized",
            source="test",
            project_id="p-int-04",
            data={"description": "", "project_id": "p-int-04"},
        ),
    )

    await asyncio.sleep(2)

    # No goal node should be created
    goal = kg.get_node("goal-p-int-04")
    assert goal is None, "Descripcion vacia no debe crear goal node"

    # No requirements
    reqs = kg.query(node_type=NodeType.requirement)
    assert len(reqs) == 0, "Sin goal no deben crearse requisitos"

    # No artifacts
    artifacts = kg.query(node_type=NodeType.artifact)
    assert len(artifacts) == 0, "Sin requisitos no deben crearse artifacts"

    for a in agents:
        await a.stop()


@pytest.mark.asyncio
async def test_pipeline_with_complex_project() -> None:
    """Complex project triggers multi-target code generation."""
    bus, kg, agents = _make_agents()

    for a in agents:
        await a.start()

    with tempfile.TemporaryDirectory() as tmp:
        agents[2]._output_base = Path(tmp)

        await bus.publish(
            Event(
                topic="project.initialized",
                source="test",
                project_id="p-int-05",
                data={
                    "description": (
                        "Sistema multi-tenant con microservicios. "
                        "API REST de productos. Entidad Usuario. "
                        "Contenedores Docker para despliegue."
                    ),
                    "project_id": "p-int-05",
                },
            ),
        )

        await asyncio.sleep(4)

        # Goal with complex classification
        goal = kg.get_node("goal-p-int-05")
        assert goal is not None
        assert goal.properties.get("complexity") == "complex"

        # Multiple requirements
        reqs = kg.query(node_type=NodeType.requirement)
        assert len(reqs) >= 3

        # At least one artifact committed
        artifacts = kg.query(node_type=NodeType.artifact)
        committed = [a for a in artifacts if a.properties.get("status") == "committed"]
        assert len(committed) >= 1

    for a in agents:
        await a.stop()


@pytest.mark.asyncio
async def test_concurrent_projects() -> None:
    """Two independent projects do not interfere."""
    bus, kg, agents = _make_agents()

    for a in agents:
        await a.start()

    with tempfile.TemporaryDirectory() as tmp:
        agents[2]._output_base = Path(tmp)

        await bus.publish(
            Event(
                topic="project.initialized",
                source="test",
                project_id="p-alpha",
                data={
                    "description": "CRUD de productos",
                    "project_id": "p-alpha",
                },
            ),
        )
        await bus.publish(
            Event(
                topic="project.initialized",
                source="test",
                project_id="p-beta",
                data={
                    "description": "Sistema de autenticacion con JWT",
                    "project_id": "p-beta",
                },
            ),
        )

        await asyncio.sleep(4)

        # Both projects have goal nodes
        goal_alpha = kg.get_node("goal-p-alpha")
        goal_beta = kg.get_node("goal-p-beta")
        assert goal_alpha is not None, "Proyecto alpha debe tener goal"
        assert goal_beta is not None, "Proyecto beta debe tener goal"

        # Artifacts reference correct project
        for art in kg.query(node_type=NodeType.artifact):
            pid = art.properties.get("project_id")
            assert pid in ("p-alpha", "p-beta"), (
                f"Artifact {art.id} debe referenciar p-alpha o p-beta, obtuvo {pid}"
            )

    for a in agents:
        await a.stop()
