"""ProjectTracker — Monitoreo y Metricas de proyectos SDLC.

Se suscribe a todos los eventos del proyecto (``proyecto.{id}.>``),
clasifica cada evento en categorias (pending, completed, failed),
mantiene contadores por proyecto, emite reportes periodicos y
detecta riesgos.

No orquesta. Solo observa, registra y alerta.

Outputs:
  - ``project.progress.report`` — cada N eventos o bajo demanda
  - ``risk.identified`` — high_failure_rate, too_many_pending, blocked_task
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from pdca_sdlc.core.base_agent import AgentContext, BaseAgent
from pdca_sdlc.core.capability_registry import CapabilityManifest
from pdca_sdlc.core.event_bus import Event

logger = logging.getLogger(__name__)

# Umbrales por defecto
_DEFAULT_REPORT_INTERVAL: int = 10
_DEFAULT_FAILURE_THRESHOLD: int = 3
_DEFAULT_PENDING_THRESHOLD: int = 10


class ProjectTracker(BaseAgent):
    """Monitorea eventos del proyecto y emite reportes de progreso.

    Clasifica eventos en categorias (pending, completed, failed),
    mantiene contadores acumulados y detecta condiciones de riesgo.

    Attributes:
        report_interval: Numero de eventos tras el cual emitir reporte.
        failure_threshold: Maximo de eventos failed antes de alertar.
        pending_threshold: Maximo de eventos pending antes de alertar.
    """

    def __init__(
        self,
        context: AgentContext,
        report_interval: int = _DEFAULT_REPORT_INTERVAL,
        failure_threshold: int = _DEFAULT_FAILURE_THRESHOLD,
        pending_threshold: int = _DEFAULT_PENDING_THRESHOLD,
    ) -> None:
        """Inicializar ProjectTracker.

        Args:
            context: Contexto del agente con event bus, KG y registry.
            report_interval: Eventos tras los cuales emitir reporte (default 10).
            failure_threshold: Eventos failed antes de alertar (default 3).
            pending_threshold: Eventos pending antes de alertar (default 10).
        """
        super().__init__(context)
        self.report_interval = report_interval
        self.failure_threshold = failure_threshold
        self.pending_threshold = pending_threshold

        # {project_id: {category: count}}
        self._counters: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int),
        )
        # {project_id: total_event_count}
        self._total_events: dict[str, int] = defaultdict(int)
        # {project_id: set[risk_type]} — evita duplicados
        self._fired_risks: dict[str, set[str]] = defaultdict(set)

    @property
    def manifest(self) -> CapabilityManifest:
        """Return the capability manifest."""
        return CapabilityManifest(
            agent_id=self._ctx.agent_id,
            agent_name="ProjectTracker",
            description=(
                "Monitors project events, classifies them, emits progress reports and detects risks"
            ),
            iso_12207={"process": "6.4", "activities": ["6.4.9"]},
            triggers=[">"],
            output_events=[
                "project.progress.report",
                "risk.identified",
            ],
        )

    async def handle_event(self, event: Event) -> None:
        """Process an incoming project event.

        Classifies the event, updates counters, detects risks, and
        emits progress reports periodically.

        Args:
            event: The event to process.
        """
        project_id: str = event.project_id
        if not project_id:
            return

        # Classify and count
        category = self._classify_event(event.topic)
        self._counters[project_id][category] += 1
        self._total_events[project_id] += 1

        logger.debug(
            "Tracker: %s -> %s (total=%d, %s)",
            event.topic,
            category,
            self._total_events[project_id],
            dict(self._counters[project_id]),
        )

        # Detect risks
        await self._detect_risks(project_id, event)

        # Emit report periodically
        if self._total_events[project_id] % self.report_interval == 0:
            await self._emit_report(project_id)

    # ── Clasificacion ───────────────────────────────────────────────

    @staticmethod
    def _classify_event(topic: str) -> str:
        """Clasificar un topic de evento en una categoria.

        Args:
            topic: Topic del evento (ej. ``proyecto.p-01.requirement.created``).

        Returns:
            ``"pending"`` para created/proposed,
            ``"completed"`` para passed/complete,
            ``"failed"`` para failed,
            ``"other"`` en cualquier otro caso.
        """
        topic_lower = topic.lower()
        if "created" in topic_lower or "proposed" in topic_lower:
            return "pending"
        if "passed" in topic_lower or "complete" in topic_lower:
            return "completed"
        if "failed" in topic_lower:
            return "failed"
        return "other"

    # ── Deteccion de Riesgos ────────────────────────────────────────

    async def _detect_risks(self, project_id: str, event: Event) -> None:
        """Evaluar condiciones de riesgo y emitir alertas.

        Args:
            project_id: Proyecto a evaluar.
            event: Evento que disparo la evaluacion.
        """
        # High failure rate
        failed_count = self._counters[project_id].get("failed", 0)
        if (
            failed_count > self.failure_threshold
            and "high_failure_rate" not in self._fired_risks[project_id]
        ):
            self._fired_risks[project_id].add("high_failure_rate")
            await self.emit(
                "risk.identified",
                project_id,
                {
                    "type": "high_failure_rate",
                    "failed_count": failed_count,
                    "threshold": self.failure_threshold,
                    "detail": (
                        f"Project {project_id} has {failed_count} "
                        f"failed events (threshold: {self.failure_threshold})"
                    ),
                },
            )
            logger.info("Risk HIGH_FAILURE_RATE detected for %s", project_id)

        # Too many pending
        pending_count = self._counters[project_id].get("pending", 0)
        if (
            pending_count > self.pending_threshold
            and "too_many_pending" not in self._fired_risks[project_id]
        ):
            self._fired_risks[project_id].add("too_many_pending")
            await self.emit(
                "risk.identified",
                project_id,
                {
                    "type": "too_many_pending",
                    "pending_count": pending_count,
                    "threshold": self.pending_threshold,
                    "detail": (
                        f"Project {project_id} has {pending_count} "
                        f"pending events (threshold: {self.pending_threshold})"
                    ),
                },
            )
            logger.info("Risk TOO_MANY_PENDING detected for %s", project_id)

        # Swarm timeout
        event_data: dict[str, Any] = event.data
        if event_data.get("type") == "swarm_timeout":
            req_id = event_data.get("req_id", "unknown")
            blocked_key = f"blocked_task:{req_id}"
            if blocked_key not in self._fired_risks[project_id]:
                self._fired_risks[project_id].add(blocked_key)
                await self.emit(
                    "risk.identified",
                    project_id,
                    {
                        "type": "blocked_task",
                        "req_id": req_id,
                        "pending": event_data.get("pending", []),
                        "detail": (
                            f"Task for requirement {req_id} blocked — "
                            f"pending events: {event_data.get('pending', [])}"
                        ),
                    },
                )
                logger.info(
                    "Risk BLOCKED_TASK detected for %s: %s",
                    project_id,
                    req_id,
                )

    # ── Reportes ────────────────────────────────────────────────────

    async def _emit_report(self, project_id: str) -> None:
        """Emitir un reporte de progreso del proyecto.

        Args:
            project_id: Proyecto del reporte.
        """
        counters = dict(self._counters[project_id])
        total = self._total_events[project_id]
        data: dict[str, object] = {
            "project_id": project_id,
            "total_events": total,
            "counters": counters,
        }
        await self.emit("project.progress.report", project_id, data)
        logger.info(
            "Progress report for %s: total=%d, counters=%s",
            project_id,
            total,
            counters,
        )

    async def get_report(self, project_id: str) -> dict[str, object] | None:
        """Obtener el reporte actual de un proyecto (bajo demanda).

        Args:
            project_id: Proyecto a consultar.

        Returns:
            Dict con contadores y total, o None si no hay datos.
        """
        if project_id not in self._counters:
            return None
        return {
            "project_id": project_id,
            "total_events": self._total_events[project_id],
            "counters": dict(self._counters[project_id]),
        }
