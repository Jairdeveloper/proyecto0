"""SwarmCoordinator — deteccion de completitud de tareas via eventos.

El SwarmDetector monitorea un conjunto de sub-eventos esperados para
una tarea y emite un evento de completitud cuando todos han llegado.

Uso::

    detector = SwarmDetector(event_bus, kg)
    detector.expect("req-001", ["architecture.proposed", "security.review.completed"],
                    "design.complete", timeout=300.0)

    # Cuando ambos eventos llegan, "design.complete" se emite automaticamente
    await detector.on_event(event)
"""

from __future__ import annotations

import logging
import time
from typing import Any

from pdca_sdlc.core.event_bus import AsyncEventBus, Event
from pdca_sdlc.core.knowledge_graph import KnowledgeGraph

logger = logging.getLogger(__name__)


class SwarmDetector:
    """Detecta cuando un conjunto de sub-eventos forma una tarea completa.

    Registra expectativas para un ``req_id``: lista de topics que deben
    llegar antes de emitir un evento de completitud. Si alguna expira
    por timeout, emite ``risk.identified``.

    Attributes:
        event_bus: Bus de eventos para publicar completitud y riesgos.
        kg: Knowledge Graph (reservado para futura trazabilidad).
    """

    def __init__(
        self,
        event_bus: AsyncEventBus,
        kg: KnowledgeGraph,
    ) -> None:
        """Inicializar SwarmDetector.

        Args:
            event_bus: Bus de eventos para publicar completitud y riesgos.
            kg: Knowledge Graph para futura trazabilidad (no usado actualmente).
        """
        self.event_bus = event_bus
        self.kg = kg
        self._expectations: dict[str, dict[str, Any]] = {}
        # {req_id: {
        #     "expected": {topic: bool},
        #     "completion_topic": str,
        #     "timeout": float,
        #     "started_at": float,
        # }}

    def expect(
        self,
        req_id: str,
        expected_topics: list[str],
        completion_topic: str,
        timeout: float = 300.0,
    ) -> None:
        """Registrar que un ``req_id`` requiere ciertos topics para completarse.

        Args:
            req_id: Identificador del requisito o entidad a monitorear.
            expected_topics: Lista de topics que deben llegar para considerar
                la tarea completa.
            completion_topic: Topic del evento a emitir cuando todos los
                sub-eventos hayan llegado.
            timeout: Tiempo maximo en segundos para esperar (default 300s).
        """
        self._expectations[req_id] = {
            "expected": {topic: False for topic in expected_topics},
            "completion_topic": completion_topic,
            "timeout": timeout,
            "started_at": time.time(),
            "project_id": "",
        }
        logger.debug(
            "Swarm expectation registered for %s: %d topic(s) -> '%s' (timeout=%0.1fs)",
            req_id,
            len(expected_topics),
            completion_topic,
            timeout,
        )

    async def on_event(self, event: Event) -> None:
        """Procesar un evento y evaluar condiciones de swarm.

        Si el evento corresponde a un topic esperado para algun req_id,
        lo marca como recibido. Cuando todos los topics esperados han
        llegado, emite el evento de completitud.

        Args:
            event: Evento entrante del bus.
        """
        req_id = event.data.get("requirement_id") or event.data.get("req_id")
        if not req_id or req_id not in self._expectations:
            return

        exp = self._expectations[req_id]
        if not exp["project_id"]:
            exp["project_id"] = event.project_id
        if event.topic in exp["expected"]:
            exp["expected"][event.topic] = True
            logger.debug(
                "Swarm: %s received for %s (%d/%d)",
                event.topic,
                req_id,
                sum(1 for v in exp["expected"].values() if v),
                len(exp["expected"]),
            )

        if all(exp["expected"].values()):
            logger.info(
                "Swarm complete for %s -> emitting '%s'",
                req_id,
                exp["completion_topic"],
            )
            await self.event_bus.publish(
                Event(
                    topic=exp["completion_topic"],
                    source="swarm-coordinator",
                    project_id=event.project_id,
                    data={
                        "req_id": req_id,
                        "events": list(exp["expected"].keys()),
                    },
                ),
            )
            del self._expectations[req_id]

    async def check_timeouts(self) -> None:
        """Barrer expectativas y emitir ``risk.identified`` si expiraron.

        Recorre todas las expectativas registradas. Si alguna ha superado
        su timeout sin completarse, emite un evento ``risk.identified``
        con los topics pendientes y la elimina.
        """
        now = time.time()
        for req_id, exp in list(self._expectations.items()):
            elapsed = now - exp["started_at"]
            if elapsed > exp["timeout"]:
                pending = [t for t, v in exp["expected"].items() if not v]
                project_id = exp["project_id"] or (
                    req_id.split("-")[0] if "-" in req_id else "unknown"
                )

                logger.warning(
                    "Swarm timeout for %s after %0.1fs — pending: %s",
                    req_id,
                    elapsed,
                    pending,
                )
                await self.event_bus.publish(
                    Event(
                        topic=f"proyecto.{project_id}.risk.identified",
                        source="swarm-coordinator",
                        project_id=project_id,
                        data={
                            "type": "swarm_timeout",
                            "req_id": req_id,
                            "pending": pending,
                        },
                    ),
                )
                del self._expectations[req_id]

    @property
    def active_expectations(self) -> dict[str, dict[str, Any]]:
        """Retornar una copia de las expectativas activas.

        Returns:
            Dict con req_id como clave y sus metadatos de expectativa.
        """
        return dict(self._expectations)

    def clear(self) -> None:
        """Eliminar todas las expectativas activas."""
        count = len(self._expectations)
        self._expectations.clear()
        logger.debug("SwarmDetector cleared %d expectation(s)", count)
