"""GlobalFeedbackLoop — weight adjustment and metric aggregation across stages.

Note: Observers and PromptOptimizer were extracted to agentic_pipeline.observers
and agentic_pipeline.optimizer respectively (SRP refactor). Backward-compatible
re-exports are maintained below.
"""

from __future__ import annotations

import json
import logging
import os

from agentic_pipeline.config import config
from agentic_pipeline.metrics_store import MetricsStore, StageMetrics, SummaryResult

logger = logging.getLogger(__name__)


class FeedbackLoop:
    """Legacy file-based feedback loop for persisting stage metrics."""

    def __init__(self, memory_dir: str | None = None) -> None:
        self._memory_dir = memory_dir or config.memory_dir
        os.makedirs(self._memory_dir, exist_ok=True)

    def _stage_path(self, stage: str) -> str:
        return os.path.join(self._memory_dir, f"{stage}.json")

    def record(self, stage: str, metrics: StageMetrics) -> None:
        path = self._stage_path(stage)
        entries: list[dict[str, object]] = []
        if os.path.exists(path):
            with open(path) as f:
                entries = json.load(f)
        entries.append({"stage": stage, "metrics": metrics})
        with open(path, "w") as f:
            json.dump(entries, f, indent=2)

    def get_recent(
        self,
        stage: str,
        limit: int = 10,
    ) -> list[dict[str, object]]:
        path = self._stage_path(stage)
        if not os.path.exists(path):
            return []
        with open(path) as f:
            entries = json.load(f)
        return entries[-limit:]


class GlobalFeedbackLoop:
    """Aggregates metrics from all stages, adjusts weights, and caches results."""

    def __init__(
        self,
        metrics_store: MetricsStore | None = None,
    ) -> None:
        self._store = metrics_store or MetricsStore()
        self._legacy = FeedbackLoop()
        self._adjustments: dict[str, StageMetrics] = {}

    def record_stage(self, stage: str, metrics: StageMetrics) -> None:
        self._store.record(stage, metrics)
        self._legacy.record(stage, metrics)
        self._adjust_lexer_weights(stage, metrics)

    # -- Prompt chain metrics (F5) -------------------------------------------

    def record_prompt(self, prompt_name: str, metrics: StageMetrics) -> None:
        """Registra metricas de una etapa del prompt chain."""
        self._store.record_prompt(prompt_name, metrics)

    def get_prompt_success_rate(self, prompt_name: str, n: int = 20) -> float:
        """Tasa de exito del prompt en las ultimas N ejecuciones."""
        return self._store.get_prompt_success_rate(prompt_name, n)

    def get_prompt_avg_duration(self, prompt_name: str, n: int = 20) -> float:
        """Duracion promedio del prompt en segundos."""
        return self._store.get_prompt_avg_duration(prompt_name, n)

    def get_prompt_fallback_rate(self, prompt_name: str, n: int = 20) -> float:
        """Tasa de fallback del prompt."""
        return self._store.get_prompt_fallback_rate(prompt_name, n)

    def prompt_chain_summary(self) -> SummaryResult:
        """Resumen agregado de todas las etapas del prompt chain."""
        return self._store.get_prompt_chain_summary()

    # -- Existing API ---------------------------------------------------------

    def get_adjustments(self, stage: str) -> StageMetrics:
        return self._adjustments.get(stage, {})

    def _adjust_lexer_weights(
        self,
        stage: str,
        metrics: StageMetrics,
    ) -> None:
        if stage != "lexer":
            return
        task_count = metrics.get("task_count", 0)
        error_count = metrics.get("errors", 0)
        node_count = metrics.get("node_count", 0)

        if error_count > 0 and task_count > 0:
            ratio = error_count / max(task_count, 1)
            if ratio > 0.5:
                self._adjustments[stage] = {
                    "action": "reduce_complexity",
                    "reason": f"error_rate={ratio:.2f}",
                }
                logger.info(
                    "Lexer weight adjusted: reduce_complexity (error_rate=%.2f)",
                    ratio,
                )

        if node_count > 50:
            self._adjustments[stage] = {
                "action": "increase_threshold",
                "reason": f"high_node_count={node_count}",
            }
            logger.info(
                "Lexer threshold increased: node_count=%d",
                node_count,
            )

    def get_lexer_adjustments(self) -> StageMetrics:
        return self._adjustments.get("lexer", {})

    def summary(self) -> dict[str, object]:
        return self._store.summary()

    def get_recent(self, stage: str, limit: int = 10) -> list[dict[str, object]]:
        return self._store.get_recent(stage, limit)


_global_feedback: GlobalFeedbackLoop | None = None


def get_global_feedback() -> GlobalFeedbackLoop:
    global _global_feedback
    if _global_feedback is None:
        _global_feedback = GlobalFeedbackLoop()
    return _global_feedback


# ── SRP refactor: Observers moved to agentic_pipeline.observers ────────────
# ── SRP refactor: PromptOptimizer moved to agentic_pipeline.optimizer ──────
# Backward-compat re-exports were removed to avoid circular imports.
# Update imports to use the new locations:
#   from agentic_pipeline.observers import MetricsObserver
#   from agentic_pipeline.optimizer import PromptOptimizer
