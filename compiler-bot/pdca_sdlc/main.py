"""Entrypoint for PDCA-sdlc — wires agents and orchestrates ISO 12207 pipeline.

Usage::

    python -m pdca_sdlc.main "CRUD de productos con API REST" -v
    python -m pdca_sdlc.main --project-id p-custom "Sistema multi-tenant con OAuth2"
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import threading
from typing import Any

from pdca_sdlc.agents.adaptation_agent import AdaptationAgent
from pdca_sdlc.agents.architect_agent import ArchitectAgent
from pdca_sdlc.agents.coder_agent import CoderAgent
from pdca_sdlc.agents.project_tracker import ProjectTracker
from pdca_sdlc.agents.requirements_analyst import RequirementsAnalystAgent
from pdca_sdlc.agents.verification_agent import VerificationAgent
from pdca_sdlc.core.base_agent import AgentContext
from pdca_sdlc.core.capability_registry import CapabilityRegistry
from pdca_sdlc.core.event_bus import AsyncEventBus, Event
from pdca_sdlc.core.knowledge_graph import KnowledgeGraph
from pdca_sdlc.core.llm_client import LLMClient
from pdca_sdlc.core.quality_gate import (
    QualityGate,
    gate_componentes_tienen_trazabilidad,
    gate_modulos_tienen_trazabilidad,
    gate_requisitos_tienen_aceptacion,
)
from pdca_sdlc.core.swarm_coordinator import SwarmDetector

logger = logging.getLogger(__name__)


def _setup_logging(verbose: bool = False) -> None:
    """Configure logging level and format based on verbosity flag."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


async def main() -> None:
    """Run the PDCA-sdlc pipeline from the command line.

    Parses args, creates infrastructure and agents, publishes
    ``project.initialized``, waits for async processing,
    and prints a Knowledge Graph summary.
    """
    parser = argparse.ArgumentParser(
        description="PDCA-sdlc: SDLC orquestador ISO 12207 reactivo",
    )
    parser.add_argument(
        "description",
        nargs="?",
        default="",
        help="Descripcion del proyecto en lenguaje natural",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Logging verbose (DEBUG level)",
    )
    parser.add_argument(
        "--project-id",
        default=None,
        help="ID del proyecto (auto-generado si no se especifica)",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Iniciar servidor dashboard HTTP tras el pipeline",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8764,
        help="Puerto para el dashboard (default: 8764)",
    )
    args = parser.parse_args()

    _setup_logging(args.verbose)

    description = args.description.strip()
    if not description:
        logger.error("No se proporciono descripcion del proyecto")
        print("Uso: python -m pdca_sdlc.main 'descripcion del proyecto'")
        return

    project_id = args.project_id or "p-001"

    bus = AsyncEventBus()
    kg = KnowledgeGraph()
    registry = CapabilityRegistry()
    llm = LLMClient()

    qg = QualityGate(bus, kg)
    for name, gate_fn in [
        ("requisitos_tienen_aceptacion", gate_requisitos_tienen_aceptacion),
        ("componentes_tienen_trazabilidad", gate_componentes_tienen_trazabilidad),
        ("modulos_tienen_trazabilidad", gate_modulos_tienen_trazabilidad),
    ]:
        qg.register_gate(name, gate_fn)

    swarm = SwarmDetector(bus, kg)

    def _make_ctx(agent_id: str) -> AgentContext:
        return AgentContext(bus, kg, registry, agent_id)

    agents: list[Any] = [
        AdaptationAgent(_make_ctx("adaptation-agent"), llm_client=llm),
        RequirementsAnalystAgent(_make_ctx("requirements-analyst"), llm_client=llm),
        CoderAgent(_make_ctx("coder-agent")),
        ArchitectAgent(_make_ctx("architect-agent"), llm_client=llm),
        VerificationAgent(_make_ctx("verification-agent"), llm_client=llm, quality_gate=qg),
        ProjectTracker(_make_ctx("project-tracker")),
    ]

    for agent in agents:
        await agent.start()
        logger.info("Agente iniciado: %s", agent._ctx.agent_id)

    async def _swarm_handler(topic: str, data: object) -> None:
        if isinstance(data, Event):
            await swarm.on_event(data)

    await bus.subscribe(">", _swarm_handler)

    await bus.publish(
        Event(
            topic="project.initialized",
            source="cli",
            project_id=project_id,
            data={"description": description, "project_id": project_id},
        ),
    )
    logger.info("Evento project.initialized publicado para %s", project_id)

    for _ in range(5):
        await asyncio.sleep(1)
        await swarm.check_timeouts()

    print("\n===== Knowledge Graph Summary =====")
    print(f"Total nodos: {kg.node_count()}, aristas: {kg.edge_count()}")
    for node in kg.all_nodes():
        props = node.properties
        print(f"  [{node.node_type.value}] {node.id}")
        if "description" in props:
            desc = str(props["description"])[:80]
            print(f"    description: {desc}")
        if "complexity" in props:
            print(f"    complexity: {props['complexity']}")
        if "paths" in props:
            print(f"    files: {len(props['paths'])} generados")
        if "status" in props:
            print(f"    status: {props['status']}")
    print("=" * 40)

    for agent in agents:
        await agent.stop()
    logger.info("Pipeline completado para %s", project_id)

    if args.dashboard:
        _start_dashboard(bus, kg, registry, args.port)


def _start_dashboard(
    bus: AsyncEventBus,
    kg: KnowledgeGraph,
    registry: CapabilityRegistry,
    port: int,
) -> None:
    """Start the dashboard HTTP server in a daemon thread."""
    from pdca_sdlc.dashboard import SdlcDashboardService, run_server

    service = SdlcDashboardService(kg, bus, registry)
    thread = threading.Thread(
        target=run_server,
        kwargs={
            "host": "127.0.0.1",
            "port": port,
            "service": service,
            "bus": bus,
        },
        daemon=True,
    )
    thread.start()
    logger.info("Dashboard en segundo plano en http://127.0.0.1:%d", port)
    print(f"\nDashboard: http://127.0.0.1:{port}")
    print("Presiona Ctrl+C para detener el servidor.")
    try:
        thread.join()
    except KeyboardInterrupt:
        logger.info("Dashboard detenido por el usuario")


if __name__ == "__main__":
    asyncio.run(main())
