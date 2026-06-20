"""Entrypoint for PDCA-sdlc — wires agents and orchestrates ISO 12207 pipeline.

Usage::

    python -m pdca_sdlc.main "CRUD de productos con API REST" -v
    python -m pdca_sdlc.main --project-id p-custom "Sistema multi-tenant con OAuth2"
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from pdca_sdlc.agents.adaptation_agent import AdaptationAgent
from pdca_sdlc.agents.coder_agent import CoderAgent
from pdca_sdlc.agents.requirements_analyst import RequirementsAnalystAgent
from pdca_sdlc.core.base_agent import AgentContext
from pdca_sdlc.core.capability_registry import CapabilityRegistry
from pdca_sdlc.core.event_bus import AsyncEventBus, Event
from pdca_sdlc.core.knowledge_graph import KnowledgeGraph
from pdca_sdlc.core.llm_client import LLMClient

logger = logging.getLogger(__name__)


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


async def main() -> None:
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

    agents = [
        AdaptationAgent(
            AgentContext(
                event_bus=bus,
                knowledge_graph=kg,
                capability_registry=registry,
                agent_id="adaptation-agent",
            ),
            llm_client=llm,
        ),
        RequirementsAnalystAgent(
            AgentContext(
                event_bus=bus,
                knowledge_graph=kg,
                capability_registry=registry,
                agent_id="requirements-analyst",
            ),
            llm_client=llm,
        ),
        CoderAgent(
            AgentContext(
                event_bus=bus,
                knowledge_graph=kg,
                capability_registry=registry,
                agent_id="coder-agent",
            ),
        ),
    ]

    for agent in agents:
        await agent.start()
        logger.info("Agente iniciado: %s", agent._ctx.agent_id)

    await bus.publish(
        Event(
            topic="project.initialized",
            source="cli",
            project_id=project_id,
            data={"description": description, "project_id": project_id},
        ),
    )
    logger.info("Evento project.initialized publicado para %s", project_id)

    await asyncio.sleep(5)

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


if __name__ == "__main__":
    asyncio.run(main())
