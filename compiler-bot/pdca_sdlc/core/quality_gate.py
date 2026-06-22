"""QualityGate — Puntos de Control de Calidad para el pipeline SDLC.

Implementa gates de validacion que se ejecutan en puntos de control
del flujo SDLC. Cada gate es una funcion que recibe
``(kg, project_id, context)`` y retorna ``True`` (OK) o un ``str`` con
el mensaje de error.

Uso::

    qg = QualityGate(event_bus, kg)
    qg.register_gate("req_tienen_aceptacion", gate_requisitos_tienen_aceptacion)
    result = await qg.evaluate("req_tienen_aceptacion", "p-01", {})
    assert result == GateResult.PASSED
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from enum import StrEnum
from typing import Any

from agentic_pipeline.prompt_chain.observer_base import StageEvent, StageSubject

from pdca_sdlc.core.event_bus import AsyncEventBus, Event
from pdca_sdlc.core.knowledge_graph import EdgeType, KnowledgeGraph, Node, NodeType

logger = logging.getLogger(__name__)


class GateResult(StrEnum):
    """Resultado de la evaluacion de un gate de calidad."""

    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


# ── Gates predefinidos ──────────────────────────────────────────────────────


def gate_requisitos_tienen_aceptacion(
    kg: KnowledgeGraph,
    project_id: str,
    context: dict[str, Any],  # noqa: ARG001
) -> bool | str:
    """CHECK: todos los requisitos deben tener ``acceptance_criteria``.

    Args:
        kg: Knowledge Graph a consultar.
        project_id: Identificador del proyecto.
        context: Contexto adicional (no usado).

    Returns:
        ``True`` si todos los requisitos tienen criterios,
        o un ``str`` con el mensaje de error.
    """
    reqs: list[Node] = kg.query(node_type=NodeType.requirement)
    for req in reqs:
        ac = req.properties.get("acceptance_criteria", [])
        if not ac:
            return f"Requisito {req.id} sin criterios de aceptacion"
    return True


def gate_componentes_tienen_trazabilidad(
    kg: KnowledgeGraph,
    project_id: str,
    context: dict[str, Any],  # noqa: ARG001
) -> bool | str:
    """CHECK: cada componente traza a al menos un requisito via IMPLEMENTS.

    Args:
        kg: Knowledge Graph a consultar.
        project_id: Identificador del proyecto.
        context: Contexto adicional (no usado).

    Returns:
        ``True`` si todos los componentes tienen trazabilidad,
        o un ``str`` con el mensaje de error.
    """
    comps: list[Node] = kg.query(node_type=NodeType.component)
    for comp in comps:
        traces = kg.get_outgoing(comp.id)
        implements_edges = [e for e in traces if e.edge_type == EdgeType.implements]
        if not implements_edges:
            return f"Componente {comp.id} sin trazabilidad a requisitos"
    return True


def gate_modulos_tienen_trazabilidad(
    kg: KnowledgeGraph,
    project_id: str,
    context: dict[str, Any],  # noqa: ARG001
) -> bool | str:
    """CHECK: cada modulo traza a al menos un componente via IMPLEMENTS.

    Args:
        kg: Knowledge Graph a consultar.
        project_id: Identificador del proyecto.
        context: Contexto adicional (no usado).

    Returns:
        ``True`` si todos los modulos tienen trazabilidad,
        o un ``str`` con el mensaje de error.
    """
    mods: list[Node] = kg.query(node_type=NodeType.code_module)
    for mod in mods:
        traces = kg.get_outgoing(mod.id)
        implements_edges = [e for e in traces if e.edge_type == EdgeType.implements]
        if not implements_edges:
            return f"Modulo {mod.id} sin trazabilidad a componente"
    return True


# ── QualityGate ─────────────────────────────────────────────────────────────


class QualityGate:
    """Registro y evaluacion de gates de calidad.

    Cada gate es una funcion ``(kg, project_id, context) -> True | str``
    registrada con un nombre. ``evaluate()`` ejecuta el gate, retorna
    el resultado y, en caso de fallo, publica un evento en el bus y
    notifica a los observers via ``StageSubject``.
    """

    def __init__(
        self,
        event_bus: AsyncEventBus,
        kg: KnowledgeGraph,
    ) -> None:
        """Inicializar QualityGate.

        Args:
            event_bus: Bus de eventos para publicar fallos.
            kg: Knowledge Graph para consultas.
        """
        self._gates: dict[str, Callable[..., bool | str]] = {}
        self._event_bus = event_bus
        self._kg = kg
        self._subject = StageSubject()

    def register_gate(self, name: str, fn: Callable[..., bool | str]) -> None:
        """Registrar una funcion como gate de calidad.

        Args:
            name: Nombre del gate.
            fn: Funcion ``(kg, project_id, context) -> True | str(error)``.
        """
        self._gates[name] = fn
        logger.debug("Gate '%s' registered", name)

    @property
    def subject(self) -> StageSubject:
        """StageSubject para attach/detach de observers.

        Los observers reciben ``StageEvent`` cuando un gate falla.
        """
        return self._subject

    @property
    def gate_names(self) -> list[str]:
        """Nombres de todos los gates registrados."""
        return list(self._gates.keys())

    async def evaluate(
        self,
        name: str,
        project_id: str,
        context: dict[str, Any] | None = None,
    ) -> GateResult:
        """Evaluar un gate por nombre.

        Args:
            name: Nombre del gate a evaluar.
            project_id: Proyecto en evaluacion.
            context: Contexto adicional para el gate.

        Returns:
            ``GateResult.PASSED`` si el gate pasa,
            ``GateResult.FAILED`` si falla.
        """
        fn = self._gates.get(name)
        if fn is None:
            logger.debug("Gate '%s' not found — returning PASSED", name)
            return GateResult.PASSED

        result = fn(self._kg, project_id, context or {})

        if result is True:
            return GateResult.PASSED

        reason = str(result)
        logger.warning("Gate '%s' FAILED for %s: %s", name, project_id, reason)

        await self._event_bus.publish(
            Event(
                topic=f"proyecto.{project_id}.quality.gate.failed",
                source="quality-gate",
                project_id=project_id,
                data={
                    "gate": name,
                    "reason": reason,
                },
            ),
        )

        self._subject.notify(
            StageEvent(
                stage=f"gate.{name}",
                duration=0.0,
                success=False,
                error=reason,
                metadata={
                    "project_id": project_id,
                    "gate": name,
                },
            ),
        )

        return GateResult.FAILED
