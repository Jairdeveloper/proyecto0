"""PromptOptimizerObserver — registra metricas de prompts en MetricsStore."""

from __future__ import annotations

from agentic_pipeline.metrics_store import MetricsStore
from agentic_pipeline.prompt_chain.observer_base import StageEvent


class PromptOptimizerObserver:
    """StageObserver que registra metricas de prompts en MetricsStore."""

    def __init__(self, store: MetricsStore | None = None) -> None:
        self._store = store or MetricsStore()

    def on_event(self, event: StageEvent) -> None:
        prompt_stages = {
            "preprocess",
            "intent",
            "plan",
            "generate",
            "verify",
            "format",
        }
        if event.stage not in prompt_stages:
            return
        self._store.record_prompt(
            event.stage,
            {
                "success": event.success,
                "duration": event.duration,
                "error": event.error,
                "fallback_used": event.metadata.get("fallback_used", False),
            },
        )
