import json
import logging
from datetime import datetime
from pathlib import Path

from .config import config

logger = logging.getLogger(__name__)


class FeedbackLoop:
    def __init__(self):
        self.log_path = Path(config.memory_dir) / "feedback"
        self.log_path.mkdir(parents=True, exist_ok=True)

    def record(self, stage: str, metrics: dict) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "metrics": metrics,
        }
        log_file = self.log_path / f"{stage}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
        logger.debug(f"Feedback recorded for {stage}: {metrics}")

    def get_recent(self, stage: str, limit: int = 10) -> list[dict]:
        log_file = self.log_path / f"{stage}.jsonl"
        if not log_file.exists():
            return []
        with open(log_file) as f:
            lines = f.readlines()[-limit:]
        return [json.loads(line) for line in lines]
