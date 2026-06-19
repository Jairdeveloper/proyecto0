"""DebugObserver — StageObserver que invoca un callback de debug por evento."""

from __future__ import annotations

from collections.abc import Callable

from agentic_pipeline.prompt_chain.observer_base import StageEvent


class DebugObserver:
    """StageObserver que invoca un callback de debug por evento."""

    def __init__(
        self,
        callback: Callable[[str, dict], None] | None = None,
    ) -> None:
        self._callback = callback

    def on_event(self, event: StageEvent) -> None:
        if self._callback:
            self._callback(event.stage, event.output)
