"""MetricsStore — persistence for stage metrics with SQLite or JSON fallback."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    import sqlite3

    HAS_SQLITE = True
except ModuleNotFoundError:
    HAS_SQLITE = False
    logger.warning("_sqlite3 C module not available; falling back to JSON file store")


MAX_ENTRIES_PER_STAGE = 1000


class MetricsStore:
    """Persistent metrics store using SQLite (preferred) or JSON files."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or Path("/tmp/agentic_metrics.db")
        self._data_dir = self.db_path.parent / f"{self.db_path.stem}_json_fallback"
        if HAS_SQLITE:
            self._init_db_sqlite()
        else:
            os.makedirs(self._data_dir, exist_ok=True)

    def _init_db_sqlite(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stage_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stage TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metrics TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS token_frequencies (
                    token TEXT PRIMARY KEY,
                    count INTEGER NOT NULL DEFAULT 0,
                    weight REAL NOT NULL DEFAULT 1.0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_stats (
                    key TEXT PRIMARY KEY,
                    hits INTEGER NOT NULL DEFAULT 0,
                    misses INTEGER NOT NULL DEFAULT 0
                )
            """)

    # -- JSON fallback helpers ------------------------------------------------

    def _json_path(self, stage: str) -> Path:
        safe = stage.replace("/", "_").replace("\\", "_")
        return self._data_dir / f"{safe}.json"

    def _json_read(self, stage: str) -> list[dict[str, Any]]:
        path = self._json_path(stage)
        if not path.exists():
            return []
        with open(path) as f:
            return json.load(f)

    def _json_write(self, stage: str, entries: list[dict[str, Any]]) -> None:
        with open(self._json_path(stage), "w") as f:
            json.dump(entries, f, indent=2)

    # -- Public API -----------------------------------------------------------

    def record(self, stage: str, metrics: dict[str, Any]) -> None:
        if HAS_SQLITE:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    "INSERT INTO stage_metrics (stage, timestamp, metrics) VALUES (?, ?, ?)",
                    (stage, datetime.now().isoformat(), json.dumps(metrics)),
                )
                conn.execute(
                    "DELETE FROM stage_metrics WHERE id IN ("
                    "SELECT id FROM stage_metrics WHERE stage = ? "
                    "ORDER BY id DESC LIMIT -1 OFFSET ?)",
                    (stage, MAX_ENTRIES_PER_STAGE),
                )
            return
        entries = self._json_read(stage)
        entries.append(
            {
                "stage": stage,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat(),
            }
        )
        if len(entries) > MAX_ENTRIES_PER_STAGE:
            entries = entries[-MAX_ENTRIES_PER_STAGE:]
        self._json_write(stage, entries)

    def get_recent(
        self,
        stage: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        if HAS_SQLITE:
            with sqlite3.connect(str(self.db_path)) as conn:
                rows = conn.execute(
                    "SELECT timestamp, metrics FROM stage_metrics "
                    "WHERE stage = ? ORDER BY id DESC LIMIT ?",
                    (stage, limit),
                ).fetchall()
            return [{"timestamp": row[0], "metrics": json.loads(row[1])} for row in reversed(rows)]
        entries = self._json_read(stage)
        return [
            {"timestamp": e.get("timestamp", ""), "metrics": e.get("metrics", {})}
            for e in entries[-limit:]
        ]

    def summary(self) -> dict[str, Any]:
        if HAS_SQLITE:
            with sqlite3.connect(str(self.db_path)) as conn:
                total = conn.execute("SELECT COUNT(*) FROM stage_metrics").fetchone()[0]
                stages = conn.execute(
                    "SELECT stage, COUNT(*) as cnt FROM stage_metrics "
                    "GROUP BY stage ORDER BY cnt DESC"
                ).fetchall()
                errors = conn.execute(
                    "SELECT COUNT(*) FROM stage_metrics WHERE json_extract(metrics, '$.errors') > 0"
                ).fetchone()[0]
            return {
                "total_records": total,
                "stages": {row[0]: row[1] for row in stages},
                "total_errors": errors,
            }
        stages: dict[str, int] = {}
        total = 0
        errors = 0
        for fname in os.listdir(self._data_dir):
            if not fname.endswith(".json"):
                continue
            stage = fname[: -len(".json")]
            path = self._data_dir / fname
            with open(path) as f:
                entries = json.load(f)
            stages[stage] = len(entries)
            total += len(entries)
            for e in entries:
                m = e.get("metrics", {})
                if m.get("errors", 0) > 0:
                    errors += 1
        return {
            "total_records": total,
            "stages": stages,
            "total_errors": errors,
        }

    def record_token(self, token: str, weight: float = 1.0) -> None:
        if HAS_SQLITE:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    "INSERT INTO token_frequencies (token, count, weight) "
                    "VALUES (?, 1, ?) "
                    "ON CONFLICT(token) DO UPDATE SET "
                    "count = count + 1",
                    (token, weight),
                )
            return
        path = self._data_dir / "token_frequencies.json"
        freqs: dict[str, dict[str, Any]] = {}
        if path.exists():
            with open(path) as f:
                freqs = json.load(f)
        if token in freqs:
            freqs[token]["count"] += 1
        else:
            freqs[token] = {"count": 1, "weight": weight}
        with open(path, "w") as f:
            json.dump(freqs, f, indent=2)

    def get_token_weights(self) -> dict[str, float]:
        if HAS_SQLITE:
            with sqlite3.connect(str(self.db_path)) as conn:
                rows = conn.execute(
                    "SELECT token, weight FROM token_frequencies ORDER BY count DESC"
                ).fetchall()
            return {row[0]: row[1] for row in rows}
        path = self._data_dir / "token_frequencies.json"
        if not path.exists():
            return {}
        with open(path) as f:
            freqs = json.load(f)
        return {t: v["weight"] for t, v in freqs.items()}

    def close(self) -> None:
        pass

    # -- Prompt chain metrics (F5) -------------------------------------------

    def record_prompt(self, prompt_name: str, metrics: dict[str, Any]) -> None:
        """Registra metricas de una etapa del prompt chain.

        Args:
            prompt_name: Nombre del prompt (preprocess, intent, plan, etc.)
            metrics: Dict con success, duration, llm_provider, llm_model,
                     temperature, fallback_used, output_size, tokens_used.
        """
        full_metrics = dict(metrics)
        full_metrics.setdefault("fallback_used", False)
        full_metrics.setdefault("output_size", 0)
        full_metrics.setdefault("tokens_used", 0)
        self.record(f"prompt_chain:{prompt_name}", full_metrics)

    def _get_prompt_entries(
        self,
        prompt_name: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        return self.get_recent(f"prompt_chain:{prompt_name}", limit)

    def get_prompt_success_rate(
        self,
        prompt_name: str,
        n: int = 20,
    ) -> float:
        """Tasa de exito del prompt en las ultimas N ejecuciones (0.0-1.0)."""
        entries = self._get_prompt_entries(prompt_name, n)
        if not entries:
            return 1.0
        successes = sum(1 for e in entries if e.get("metrics", {}).get("success", False))
        return successes / len(entries)

    def get_prompt_avg_duration(
        self,
        prompt_name: str,
        n: int = 20,
    ) -> float:
        """Duracion promedio del prompt en segundos."""
        entries = self._get_prompt_entries(prompt_name, n)
        if not entries:
            return 0.0
        durations = [
            e.get("metrics", {}).get("duration", 0.0)
            for e in entries
            if e.get("metrics", {}).get("duration") is not None
        ]
        if not durations:
            return 0.0
        return sum(durations) / len(durations)

    def get_prompt_fallback_rate(
        self,
        prompt_name: str,
        n: int = 20,
    ) -> float:
        """Tasa de fallback en las ultimas N ejecuciones (0.0-1.0)."""
        entries = self._get_prompt_entries(prompt_name, n)
        if not entries:
            return 0.0
        fallbacks = sum(1 for e in entries if e.get("metrics", {}).get("fallback_used", False))
        return fallbacks / len(entries)

    def get_prompt_chain_summary(self) -> dict[str, Any]:
        """Retorna resumen agregado de todos los prompts del chain.

        Returns:
            Dict con total_records, total_errors, success_rate, cache_hit_rate,
            fallback_rate, y per-stage stats.
        """
        prompt_stages = [
            "preprocess",
            "intent",
            "plan",
            "generate",
            "verify",
            "format",
        ]
        per_stage: dict[str, dict[str, Any]] = {}
        total_records = 0
        total_errors = 0
        total_fallbacks = 0

        for name in prompt_stages:
            stage_key = f"prompt_chain:{name}"
            entries = self.get_recent(stage_key, MAX_ENTRIES_PER_STAGE)
            if not entries:
                continue
            count = len(entries)
            total_records += count
            errors = sum(1 for e in entries if not e.get("metrics", {}).get("success", True))
            fallbacks = sum(1 for e in entries if e.get("metrics", {}).get("fallback_used", False))
            total_errors += errors
            total_fallbacks += fallbacks

            durations = [
                e.get("metrics", {}).get("duration", 0.0)
                for e in entries
                if e.get("metrics", {}).get("duration") is not None
            ]
            avg_duration = sum(durations) / len(durations) if durations else 0.0
            success_rate = (count - errors) / count if count > 0 else 1.0

            per_stage[name] = {
                "calls": count,
                "success_rate": round(success_rate * 100, 1),
                "avg_duration_s": round(avg_duration, 2),
                "errors": errors,
                "fallbacks": fallbacks,
            }

        overall_success_rate = (
            (total_records - total_errors) / total_records if total_records > 0 else 1.0
        )
        fallback_rate = total_fallbacks / total_records if total_records > 0 else 0.0

        return {
            "total_records": total_records,
            "total_errors": total_errors,
            "success_rate": round(overall_success_rate * 100, 1),
            "fallback_rate": round(fallback_rate * 100, 1),
            "per_stage": per_stage,
        }
