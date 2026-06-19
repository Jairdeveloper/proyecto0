"""LLMCache — AST-level cache for LLM responses (F5.3).

NO cachea texto crudo — cachea el hash del prompt normalizado + schema,
para que variaciones cosmeticas no invaliden el cache.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class LLMCache:
    """Cache AST-level de respuestas del LLM.

    Almacena respuestas indexadas por hash(prompt_normalizado + schema).
    Soporta backend en memoria o SQLite.
    """

    def __init__(self, backend: str = "memory", db_path: str | None = None) -> None:
        self._backend = backend
        self._store: dict[str, dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0
        if backend == "sqlite":
            self._init_sqlite(db_path)

    def _init_sqlite(self, db_path: str | None) -> None:
        try:
            import sqlite3

            self._sqlite_path = Path(db_path or "/tmp/agentic_llm_cache.db")
            self._sqlite_conn = sqlite3.connect(str(self._sqlite_path))
            self._sqlite_conn.execute("""
                CREATE TABLE IF NOT EXISTS llm_cache (
                    key TEXT PRIMARY KEY,
                    response TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)
            self._sqlite_conn.commit()
        except Exception as exc:
            logger.warning("SQLite LLM cache init failed: %s", exc)
            self._backend = "memory"

    @staticmethod
    def _make_key(prompt: str, schema: str) -> str:
        """Hash deterministico del prompt normalizado + schema."""
        normalized = " ".join(prompt.lower().split())
        raw = f"{normalized}||{schema}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def get(self, prompt: str, schema: str) -> dict[str, Any] | None:
        """Retorna respuesta cacheada o None."""
        key = self._make_key(prompt, schema)
        if self._backend == "sqlite":
            return self._get_sqlite(key)
        cached = self._store.get(key)
        if cached is not None:
            self._hits += 1
            return cached.get("response")
        self._misses += 1
        return None

    async def set(
        self,
        prompt: str,
        schema: str,
        response: dict[str, Any],
    ) -> None:
        """Almacena respuesta en cache."""
        key = self._make_key(prompt, schema)
        entry = {"response": response, "created_at": time.time()}
        if self._backend == "sqlite":
            self._set_sqlite(key, entry)
        else:
            self._store[key] = entry

    def _get_sqlite(self, key: str) -> dict[str, Any] | None:
        try:
            row = self._sqlite_conn.execute(
                "SELECT response FROM llm_cache WHERE key = ?",
                (key,),
            ).fetchone()
            if row:
                self._hits += 1
                return json.loads(row[0])
        except Exception:
            pass
        self._misses += 1
        return None

    def _set_sqlite(self, key: str, entry: dict[str, Any]) -> None:
        try:
            self._sqlite_conn.execute(
                "INSERT OR REPLACE INTO llm_cache (key, response, created_at) VALUES (?, ?, ?)",
                (key, json.dumps(entry["response"]), entry["created_at"]),
            )
            self._sqlite_conn.commit()
        except Exception as exc:
            logger.warning("SQLite LLM cache set failed: %s", exc)

    def stats(self) -> dict[str, Any]:
        """Estadisticas de cache: hits, misses, hit_rate."""
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total * 100, 1) if total > 0 else 0.0,
            "size": len(self._store) if self._backend == "memory" else -1,
            "backend": self._backend,
        }

    def clear(self) -> None:
        """Limpia todo el cache."""
        self._store.clear()
        self._hits = 0
        self._misses = 0
        if self._backend == "sqlite":
            try:
                self._sqlite_conn.execute("DELETE FROM llm_cache")
                self._sqlite_conn.commit()
            except Exception:
                pass
