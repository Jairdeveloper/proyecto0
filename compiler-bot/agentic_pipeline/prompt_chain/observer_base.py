"""StageSubject — thin facade over EventBus, StageEvent payload.

StageSubject mantiene la API attach/detach/notify por compatibilidad
pero delega internamente en EventBus como unico mecanismo pub/sub.
StageObserver se elimino como clase — los observers concretos
implementan on_event(event) sin herencia.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from agentic_pipeline.agents.event_bus import EventBus

STAGE_EVENTS_TOPIC = "stage_event"
"""Topic unico bajo el cual EventBus publica todos los StageEvent."""


@dataclass
class StageEvent:
    """Payload de evento emitido por un stage del pipeline.

    Attributes:
        stage: Nombre del stage que emitio el evento.
        duration: Duracion en segundos.
        success: True si el stage completo sin errores.
        output: Datos de salida del stage.
        error: Mensaje de error si success es False.
        metadata: Metrica adicional especifica del stage.
        timestamp: ISO 8601 de cuando ocurrio el evento.
    """

    stage: str
    duration: float
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
    )


class StageSubject:
    """Sujeto del patron Observer — fachada delgada sobre EventBus.

    Mantiene la API attach/detach/notify/observer_count por
    compatibilidad con PipelineStage y PromptHandler. Internamente
    todo el pub/sub se delega en EventBus.

    attach(observer) suscribe observer.on_event a EventBus.
    detach(observer) cancela la suscripcion.
    notify(event) publica en EventBus bajo STAGE_EVENTS_TOPIC.
    """

    def __init__(self) -> None:
        self._bus = EventBus()
        self._wrappers: dict[int, Callable[[str, Any], None]] = {}

    def attach(self, observer: object) -> None:
        """Suscribe observer.on_event a EventBus via wrapper."""

        def _wrap(topic: str, data: object) -> None:
            observer.on_event(data)  # type: ignore[union-attr]

        self._wrappers[id(observer)] = _wrap
        self._bus.subscribe(STAGE_EVENTS_TOPIC, _wrap)

    def detach(self, observer: object) -> None:
        """Cancela la suscripcion de un observer previamente registrado."""
        wrapper = self._wrappers.pop(id(observer), None)
        if wrapper is not None:
            self._bus.unsubscribe(STAGE_EVENTS_TOPIC, wrapper)

    def notify(self, event: StageEvent) -> None:
        """Publica un StageEvent en EventBus (unico mecanismo de difusion)."""
        self._bus.publish(STAGE_EVENTS_TOPIC, event)

    @property
    def observer_count(self) -> int:
        """Cantidad de observers registrados actualmente."""
        return self._bus.subscriber_count(STAGE_EVENTS_TOPIC)
