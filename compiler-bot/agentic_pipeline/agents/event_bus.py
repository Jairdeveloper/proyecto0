"""EventBus — publish/subscribe event bus for multi-agent coordination.

Formaliza el patron Observer para el sistema multi-agente. Los agentes
publican eventos en topics y se suscriben a topics de otros agentes,
permitiendo coordinacion desacoplada entre PerceptionAgent,
ReasoningAgent, ExecutionAgent, y ValidatorAgent.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any


class EventBus:
    """Bus de eventos con publish/subscribe por topicos (Observer).

    Los agentes pueden publicar eventos en topics y suscribirse a
    topics de otros agentes. Soporta callbacks sync y async.

    Examples:
        bus = EventBus()
        bus.subscribe("pr_created", security_agent.review_pr)
        bus.subscribe("pr_created", ux_agent.review_design)
        bus.publish("pr_created", {"pr_url": "..."})
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable]] = {}

    def subscribe(self, topic: str, callback: Callable) -> None:
        """Registra un callback para un topic.

        Args:
            topic: Nombre del topic (ej: "pr_created", "stage_completed").
            callback: Funcion que recibe (topic, data) cuando se publica.
        """
        self._subscribers.setdefault(topic, []).append(callback)

    def unsubscribe(self, topic: str, callback: Callable) -> None:
        """Elimina un callback registrado previamente.

        Raises:
            ValueError: Si el callback no estaba registrado en el topic.
        """
        self._subscribers[topic].remove(callback)

    def publish(self, topic: str, data: Any) -> None:
        """Publica un evento en un topic (sync).

        Todos los callbacks registrados reciben (topic, data).
        """
        for cb in self._subscribers.get(topic, []):
            cb(topic, data)

    async def publish_async(self, topic: str, data: Any) -> None:
        """Publica un evento en un topic (async).

        Awatea callbacks async, ejecuta sync directamente.
        """
        for cb in self._subscribers.get(topic, []):
            if inspect.iscoroutinefunction(cb):
                await cb(topic, data)
            else:
                cb(topic, data)

    def has_subscribers(self, topic: str) -> bool:
        """True si al menos un callback esta registrado en el topic."""
        return len(self._subscribers.get(topic, [])) > 0

    def subscriber_count(self, topic: str) -> int:
        """Cantidad de callbacks registrados en un topic."""
        return len(self._subscribers.get(topic, []))

    def clear(self) -> None:
        """Elimina todos los subscriptores de todos los topics."""
        self._subscribers.clear()
