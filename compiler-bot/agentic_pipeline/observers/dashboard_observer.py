"""DashboardObserver — buffer de eventos recientes para consumo del dashboard."""

from __future__ import annotations

from collections import deque

from agentic_pipeline.prompt_chain.observer_base import StageEvent


class WebSocketClient:
    """Stub para cliente WebSocket."""

    def send_json(self, data: object) -> None: ...


class DashboardObserver:
    """Mantiene un buffer de eventos recientes para consumo del dashboard.

    Almacena los ultimos 1000 eventos en un deque para consumo
    del dashboard en tiempo real. El broadcast a WebSocket clients
    es un stub preparado para integracion futura.
    """

    def __init__(self, max_events: int = 1000) -> None:
        self._recent_events: deque[StageEvent] = deque(maxlen=max_events)
        self._ws_clients: list[WebSocketClient] = []

    def on_event(self, event: StageEvent) -> None:
        self._recent_events.append(event)
        self._broadcast(event)

    def _broadcast(self, event: StageEvent) -> None:
        for ws in self._ws_clients:
            try:
                ws.send_json(
                    {
                        "stage": event.stage,
                        "duration": event.duration,
                        "success": event.success,
                        "timestamp": event.timestamp,
                    }
                )
            except Exception:
                self._ws_clients.remove(ws)

    def get_recent(self, limit: int = 100) -> list[StageEvent]:
        return list(self._recent_events)[-limit:]

    @property
    def event_count(self) -> int:
        return len(self._recent_events)
