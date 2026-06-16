"""GlobalFeedbackLoop — weight adjustment and metric aggregation across stages."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from .config import config
from .metrics_store import MetricsStore

logger = logging.getLogger(__name__)


class FeedbackLoop:
    """Legacy file-based feedback loop for persisting stage metrics."""

    def __init__(self, memory_dir: str | None = None) -> None:
        self._memory_dir = memory_dir or config.memory_dir
        os.makedirs(self._memory_dir, exist_ok=True)

    def _stage_path(self, stage: str) -> str:
        return os.path.join(self._memory_dir, f"{stage}.json")

    def record(self, stage: str, metrics: dict[str, Any]) -> None:
        path = self._stage_path(stage)
        entries: list[dict[str, Any]] = []
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
    ) -> list[dict[str, Any]]:
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
        self._adjustments: dict[str, dict[str, Any]] = {}

    def record_stage(self, stage: str, metrics: dict[str, Any]) -> None:
        self._store.record(stage, metrics)
        self._legacy.record(stage, metrics)
        self._adjust_lexer_weights(stage, metrics)

    def get_adjustments(self, stage: str) -> dict[str, Any]:
        return self._adjustments.get(stage, {})

    def _adjust_lexer_weights(
        self,
        stage: str,
        metrics: dict[str, Any],
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

    def get_lexer_adjustments(self) -> dict[str, Any]:
        return self._adjustments.get("lexer", {})

    def summary(self) -> dict[str, Any]:
        return self._store.summary()

    def get_recent(self, stage: str, limit: int = 10) -> list[dict[str, Any]]:
        return self._store.get_recent(stage, limit)


_global_feedback: GlobalFeedbackLoop | None = None


def get_global_feedback() -> GlobalFeedbackLoop:
    global _global_feedback
    if _global_feedback is None:
        _global_feedback = GlobalFeedbackLoop()
    return _global_feedback
