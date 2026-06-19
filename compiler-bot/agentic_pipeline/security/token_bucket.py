"""TokenBucket — thread-safe rate limiter for LLM API calls."""

from __future__ import annotations

import threading
import time


class TokenBucket:
    """Thread-safe token bucket rate limiter.

    Allows bursting up to `capacity` tokens, then refills at `refill_rate`
    tokens per second. Use `consume()` before each API call.
    """

    def __init__(self, capacity: int = 60, refill_rate: float = 1.0) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()
        self._lock = threading.Lock()

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume `tokens` from the bucket.

        Returns True if successful, False if insufficient tokens.
        """
        with self._lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    @property
    def available(self) -> float:
        """Current number of available tokens (approximate)."""
        with self._lock:
            now = time.time()
            elapsed = now - self.last_refill
            return min(self.capacity, self.tokens + elapsed * self.refill_rate)
