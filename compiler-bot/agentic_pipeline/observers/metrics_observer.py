"""MetricsObserver — StageObserver que registra metricas en GlobalFeedbackLoop."""

from __future__ import annotations

from typing import Any

from agentic_pipeline.feedback_loop import GlobalFeedbackLoop, get_global_feedback
from agentic_pipeline.prompt_chain.observer_base import StageEvent


class MetricsObserver:
    """StageObserver que registra metricas en GlobalFeedbackLoop.

    Conecta el StageSubject del pipeline con el sistema de metricas
    existente, preservando la funcionalidad de record_stage().
    """

    def __init__(
        self,
        feedback: GlobalFeedbackLoop | None = None,
    ) -> None:
        self._feedback = feedback or get_global_feedback()

    def on_event(self, event: StageEvent) -> None:
        metrics: dict[str, Any] = {
            "duration_seconds": event.duration,
            "success": event.success,
            "error": event.error,
            **event.metadata,
        }
        self._feedback.record_stage(event.stage, metrics)
