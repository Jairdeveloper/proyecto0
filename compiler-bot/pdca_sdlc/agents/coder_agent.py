"""CoderAgent — generates code from requirements using agentic_pipeline generators.

Trigger: ``requirement.created``
Output: ``code.committed`` or ``code.failed``
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from pdca_sdlc.core.base_agent import AgentContext, BaseAgent
from pdca_sdlc.core.capability_registry import CapabilityManifest
from pdca_sdlc.core.event_bus import Event
from pdca_sdlc.core.knowledge_graph import Node, NodeType

logger = logging.getLogger(__name__)


def _generator_factory() -> Any:
    from agentic_pipeline.generators.base_generator import GeneratorFactory

    return GeneratorFactory


def _ir_nodes() -> tuple[Any, Any, Any]:
    from agentic_pipeline.nodes.ir_nodes import IRAPI, IREntity, IRProject

    return IRProject, IRAPI, IREntity


class CoderAgent(BaseAgent):
    """Generates code from requirements using agentic_pipeline generators.

    Maps requirement text to generator targets (nestjs, prisma, docker),
    builds IR node trees, and delegates to GeneratorFactory.
    """

    _TARGET_KEYWORDS: dict[str, list[str]] = {
        "nestjs": [
            "api",
            "controller",
            "servicio",
            "endpoint",
            "rest",
            "module",
            "crud",
            "modulo",
        ],
        "prisma": [
            "entidad",
            "entity",
            "modelo",
            "schema",
            "base de datos",
            "datos",
            "persistencia",
            "bd",
        ],
        "docker": [
            "docker",
            "contenedor",
            "container",
            "despliegue",
            "deploy",
        ],
    }

    _OUTPUT_BASE: Path = Path("output")

    def __init__(
        self,
        context: AgentContext,
        output_base: Path | None = None,
    ) -> None:
        super().__init__(context)
        self._output_base = output_base or self._OUTPUT_BASE

    @property
    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest(
            agent_id=self._ctx.agent_id,
            agent_name="CoderAgent",
            description=("Generates code from requirements using NestJS/Prisma generators"),
            iso_12207={"process": "6.3", "activities": ["6.3.1", "6.3.2"]},
            triggers=["requirement.created"],
            output_events=["code.committed", "code.failed"],
        )

    async def handle_event(self, event: Event) -> None:
        project_id: str = event.project_id
        requirement_ids: list[str] = event.data.get("requirement_ids", [])
        if not requirement_ids:
            logger.warning("No requirement IDs in event for %s", project_id)
            return

        requirements = self._read_requirements(requirement_ids)
        if not requirements:
            logger.warning("No requirements found in KG for %s", project_id)
            return

        targets = self._plan_targets(requirements)
        if not targets:
            logger.warning("No targetable requirements for %s", project_id)
            return

        all_success = True
        committed: list[dict[str, Any]] = []

        for target, reqs in targets.items():
            gen_id = f"gen-{project_id}-{target}"
            try:
                ir_node = self._build_ir(project_id, target, reqs)
                output_dir = self._output_dir(project_id, target)
                gf_cls = _generator_factory()
                generator = gf_cls.get_generator(target)
                paths = generator.generate(ir_node, output_dir)

                self.write_graph(
                    Node(
                        id=gen_id,
                        node_type=NodeType.artifact,
                        properties={
                            "target": target,
                            "paths": [str(p) for p in paths],
                            "status": "committed",
                            "project_id": project_id,
                        },
                    ),
                )
                committed.append(
                    {"target": target, "files": [str(p) for p in paths]},
                )
            except Exception as exc:
                all_success = False
                self.write_graph(
                    Node(
                        id=gen_id,
                        node_type=NodeType.artifact,
                        properties={
                            "target": target,
                            "status": "failed",
                            "error": str(exc),
                            "project_id": project_id,
                        },
                    ),
                )
                await self.emit(
                    "code.failed",
                    project_id,
                    {
                        "module_id": project_id,
                        "component": target,
                        "error": str(exc),
                    },
                )

        if all_success:
            all_files = [f for c in committed for f in c["files"]]
            await self.emit(
                "code.committed",
                project_id,
                {
                    "module_id": project_id,
                    "component": "all",
                    "files": all_files,
                    "tests_passed": False,
                },
            )

    def _read_requirements(
        self,
        requirement_ids: list[str],
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for rid in requirement_ids:
            node = self.read_graph(rid)
            if node is not None:
                result.append(node.properties)
        return result

    def _plan_targets(
        self,
        requirements: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        targets: dict[str, list[dict[str, Any]]] = {}
        for req in requirements:
            text = str(req.get("text", "")).lower()
            assigned = False
            for target, keywords in self._TARGET_KEYWORDS.items():
                if any(kw in text for kw in keywords):
                    targets.setdefault(target, []).append(req)
                    assigned = True
            if not assigned:
                targets.setdefault("nestjs", []).append(req)
        return targets

    def _build_ir(
        self,
        project_id: str,
        target: str,
        requirements: list[dict[str, Any]],
    ) -> Any:
        proj_cls, api_cls, ent_cls = _ir_nodes()
        project = proj_cls(name=project_id)

        if target == "prisma":
            entities = self._extract_entities(requirements)
            for entity_name, attrs in entities:
                entity = ent_cls(name=entity_name, attributes=attrs)
                project.add(entity)

        elif target == "nestjs":
            apis = self._extract_apis(requirements)
            for api_name, methods in apis:
                api = api_cls(name=api_name, methods=methods)
                project.add(api)

        return project

    @staticmethod
    def _extract_entities(
        requirements: list[dict[str, Any]],
    ) -> list[tuple[str, list[dict[str, str]]]]:
        seen: set[str] = set()
        entities: list[tuple[str, list[dict[str, str]]]] = []
        for req in requirements:
            text = str(req.get("text", ""))
            words = re.findall(r"\b[A-Z][a-z]+\b", text)
            for word in words:
                lower = word.lower()
                if lower not in seen:
                    seen.add(lower)
                    entities.append(
                        (
                            word,
                            [
                                {
                                    "name": "id",
                                    "type": "String @id @default(cuid())",
                                },
                            ],
                        ),
                    )
        return entities

    @staticmethod
    def _extract_apis(
        requirements: list[dict[str, Any]],
    ) -> list[tuple[str, list[str]]]:
        seen: set[str] = set()
        apis: list[tuple[str, list[str]]] = []
        for req in requirements:
            text = str(req.get("text", ""))
            words = re.findall(r"\b[A-Z][a-z]+\b", text)
            for word in words:
                name = word.lower()
                if name not in seen:
                    seen.add(name)
                    apis.append((word, ["GET", "POST", "PUT", "DELETE"]))
        return apis

    def _output_dir(self, project_id: str, target: str) -> Path:
        return self._output_base / project_id / target
