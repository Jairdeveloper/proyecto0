"""AuditObserver — registra cada compilacion en un archivo JSON append-only."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from agentic_pipeline.prompt_chain.observer_base import StageEvent, StageObserver


class AuditObserver(StageObserver):
    """Registra cada compilacion en un archivo JSON append-only."""

    def __init__(self, log_path: str = ".recpl_audit.log") -> None:
        self._log_path = log_path

    def on_event(self, event: StageEvent) -> None:
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "stage": event.stage,
            "success": event.success,
            "duration": event.duration,
        }
        with open(self._log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
