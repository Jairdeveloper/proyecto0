"""Observer Pattern base — StageSubject, StageObserver, StageEvent.

Implementa el bus de eventos para el pipeline RECPL. Los PipelineStage
y PromptHandler publican StageEvent via StageSubject, y los observers
concretos (MetricsObserver, DebugObserver, etc.) reaccionan sin
acoplamiento directo.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


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
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
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
    """

    def __init__(self) -> None:
        self._observers: list[StageObserver] = []

    def attach(self, observer: StageObserver) -> None:
        """Registra un observer para recibir eventos futuros."""
        self._observers.append(observer)

    def detach(self, observer: StageObserver) -> None:
        """Elimina un observer registrado previamente."""
        self._observers.remove(observer)

    def notify(self, event: StageEvent) -> None:
        """Notifica a todos los observers registrados con un evento."""
        for observer in self._observers:
            observer.on_event(event)

    @property
    def observer_count(self) -> int:
        """Cantidad de observers registrados actualmente."""
        return len(self._observers)
