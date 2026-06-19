"""BanditScanner — scans generated files for blocked patterns."""

from __future__ import annotations

from pathlib import Path

from agentic_pipeline.prompt_chain.observer_base import StageEvent
from agentic_pipeline.security.policies import BLOCKED_PATTERNS


class BanditScanner:
    """Inspects generated files for dangerous patterns.

    Attaches to StageSubject and scans every file emitted by the synthesis
    stage against BLOCKED_PATTERNS (eval, exec, os.system, etc.).
    Alerts are recorded in event.metadata["security_alert"].
    """

    def on_event(self, event: StageEvent) -> None:
        if event.stage != "synthesis":
            return
        for filepath in event.output.get("generated_files", []):
            try:
                content = Path(filepath).read_text()
            except (OSError, UnicodeDecodeError):
                continue
            for pattern in BLOCKED_PATTERNS:
                if pattern.search(content):
                    event.metadata["security_alert"] = f"Blocked pattern in {filepath}"
