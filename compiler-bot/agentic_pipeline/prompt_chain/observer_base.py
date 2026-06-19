"""Observer Pattern base — StageSubject, StageObserver, StageEvent.

Implementa el bus de eventos para el pipeline RECPL. Los PipelineStage
y PromptHandler publican StageEvent via StageSubject, y los observers
concretos (MetricsObserver, DebugObserver, etc.) reaccionan sin
acoplamiento directo.

StageSubject integra EventBus como bus global de eventos para unificar
el mecanismo pub/sub del pipeline (observer_base) con el sistema
multi-agente (agents/event_bus.py).
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from agentic_pipeline.agents.event_bus import EventBus


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


class StageObserver(ABC):
    """Interface que deben implementar los observers del pipeline.

    Cualquier clase que quiera recibir eventos de PipelineStage o
    PromptHandler debe implementar on_event().
    """

    @abstractmethod
    def on_event(self, event: StageEvent) -> None: ...


class StageSubject:
    """Sujeto del patron Observer — mantiene lista de observers y los notifica.

    Los PipelineStage y PromptHandler usan una instancia compartida
    de StageSubject para publicar eventos sin conocer a los observers.

    Thread-safe: attach/detach usan un lock; notify itera sobre una
    copia congelada para evitar RuntimeError por modificacion concurrente.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._observers: list[StageObserver] = []
        self._bus = EventBus()

    def attach(self, observer: StageObserver) -> None:
        """Registra un observer para recibir eventos futuros."""
        with self._lock:
            self._observers.append(observer)

    def detach(self, observer: StageObserver) -> None:
        """Elimina un observer registrado previamente."""
        with self._lock:
            self._observers.remove(observer)

    def notify(self, event: StageEvent) -> None:
        """Notifica a observers locales y publica en el EventBus global.

        Itera sobre copia congelada de _observers para seguridad
        ante modificaciones concurrentes desde otros hilos.
        """
        with self._lock:
            snapshot = list(self._observers)
        for observer in snapshot:
            observer.on_event(event)
        self._bus.publish(event.stage, event)

    @property
    def observer_count(self) -> int:
        """Cantidad de observers registrados actualmente."""
        return len(self._observers)
