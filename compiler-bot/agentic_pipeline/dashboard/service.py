from __future__ import annotations

from datetime import datetime
from typing import Any

from agentic_pipeline.metrics_store import HAS_SQLITE, MAX_ENTRIES_PER_STAGE, MetricsStore


class DashboardService:
    """View model layer over MetricsStore for dashboard UI/API."""

    def __init__(self, store: MetricsStore | None = None) -> None:
        self._store = store or MetricsStore()

    def get_health(self) -> dict[str, Any]:
        return {
            "backend": "sqlite" if HAS_SQLITE else "json_fallback",
            "timestamp": datetime.now().isoformat(),
        }

    def get_summary(self) -> dict[str, Any]:
        raw = self._store.summary()
        total = raw.get("total_records", 0)
        errors = raw.get("total_errors", 0)
        if total > 0:
            success_rate = round((total - errors) / total * 100, 1)
        else:
            success_rate = 0.0
        return {
            "total_records": total,
            "total_errors": errors,
            "success_rate": success_rate,
        }

    def get_stages(self) -> list[dict[str, Any]]:
        raw = self._store.summary()
        stages_raw = raw.get("stages", {})
        result: list[dict[str, Any]] = []
        for stage_name in sorted(stages_raw):
            runs = stages_raw[stage_name]
            entries = self._store.get_recent(stage_name, MAX_ENTRIES_PER_STAGE)
            errors = sum(
                1
                for e in entries
                if e.get("metrics", {}).get("errors", 0) > 0
                or e.get("metrics", {}).get("success") is False
            )
            success_rate = round((runs - errors) / runs * 100, 1) if runs > 0 else 0.0
            result.append(
                {
                    "name": stage_name,
                    "runs": runs,
                    "errors": errors,
                    "success_rate": success_rate,
                }
            )
        return result

    def get_recent(self, stage: str, limit: int = 20) -> list[dict[str, Any]]:
        clamped = max(1, min(limit, 100))
        return self._store.get_recent(stage, clamped)
