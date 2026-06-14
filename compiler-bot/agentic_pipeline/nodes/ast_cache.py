"""ASTCache — LRU dict cache for parsed ASTs and IR trees."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ASTCache:
    """LRU cache for AST/IR trees to avoid redundant generation."""

    def __init__(self, maxsize: int = 128) -> None:
        self._maxsize = maxsize
        self._cache: dict[str, Any] = {}
        self._order: list[str] = []
        self.hits = 0
        self.misses = 0

    def _make_key(self, obj: object) -> str:
        raw = str(obj)
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, key: str) -> Any | None:
        if key in self._cache:
            self.hits += 1
            self._order.remove(key)
            self._order.append(key)
            return self._cache[key]
        self.misses += 1
        return None

    def set(self, key: str, value: Any) -> None:
        if key in self._cache:
            self._order.remove(key)
        elif len(self._cache) >= self._maxsize:
            oldest = self._order.pop(0)
            del self._cache[oldest]
        self._cache[key] = value
        self._order.append(key)

    def get_or_compute(
        self,
        key: str,
        compute: callable,
    ) -> Any:
        cached = self.get(key)
        if cached is not None:
            logger.debug("AST cache HIT for %s", key[:16])
            return cached
        logger.debug("AST cache MISS for %s", key[:16])
        result = compute()
        self.set(key, result)
        return result

    def clear(self) -> None:
        self._cache.clear()
        self._order.clear()
        self.hits = 0
        self.misses = 0

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    def stats(self) -> dict[str, Any]:
        return {
            "size": self.size,
            "maxsize": self._maxsize,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hit_rate,
        }
