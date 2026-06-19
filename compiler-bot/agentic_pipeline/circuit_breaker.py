"""Circuit breaker + exponential backoff for LLM resilience (M2.1)."""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is OPEN and calls are rejected."""


class CircuitBreaker:
    """Circuit breaker pattern with async support.

    States: CLOSED → OPEN (on threshold failures) → HALF_OPEN (after timeout) → CLOSED (on success).
    """

    def __init__(
        self,
        threshold: int = 5,
        timeout: float = 30.0,
    ) -> None:
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.threshold = threshold
        self.timeout = timeout
        self.last_failure_time: float = 0.0

    def call(self, fn: Callable[[], Any]) -> Any:
        """Execute a synchronous call through the circuit breaker."""
        if self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                logger.debug("Circuit breaker HALF_OPEN after timeout")
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")
        try:
            result = fn()
            self.failure_count = 0
            if self.state == CircuitBreakerState.HALF_OPEN:
                logger.debug("Circuit breaker CLOSED after successful probe")
                self.state = CircuitBreakerState.CLOSED
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            logger.debug(
                "Circuit breaker failure %d/%d",
                self.failure_count,
                self.threshold,
            )
            if self.failure_count >= self.threshold:
                logger.warning("Circuit breaker OPEN after %d failures", self.failure_count)
                self.state = CircuitBreakerState.OPEN
            raise e

    async def call_async(self, fn: Callable[[], Any]) -> Any:
        """Execute an async callable through the circuit breaker."""
        if self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                logger.debug("Circuit breaker HALF_OPEN after timeout")
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")
        try:
            result = await fn()
            self.failure_count = 0
            if self.state == CircuitBreakerState.HALF_OPEN:
                logger.debug("Circuit breaker CLOSED after successful probe")
                self.state = CircuitBreakerState.CLOSED
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            logger.debug(
                "Circuit breaker failure %d/%d",
                self.failure_count,
                self.threshold,
            )
            if self.failure_count >= self.threshold:
                logger.warning("Circuit breaker OPEN after %d failures", self.failure_count)
                self.state = CircuitBreakerState.OPEN
            raise e

    def reset(self) -> None:
        """Reset circuit breaker to CLOSED state."""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0


class ExponentialBackoff:
    """Exponential backoff with jitter for retry logic."""

    def __init__(
        self,
        min_backoff: float = 1.0,
        max_backoff: float = 60.0,
        factor: float = 2.0,
        jitter: float = 0.1,
    ) -> None:
        self.min_backoff = min_backoff
        self.max_backoff = max_backoff
        self.factor = factor
        self.jitter = jitter

    def delay(self, attempt: int) -> float:
        """Calculate backoff delay for a given attempt (0-indexed)."""
        backoff = min(self.min_backoff * (self.factor**attempt), self.max_backoff)
        jitter_amount = random.uniform(0, backoff * self.jitter)
        return backoff + jitter_amount

    def __repr__(self) -> str:
        return (
            f"ExponentialBackoff(min={self.min_backoff}, max={self.max_backoff}, "
            f"factor={self.factor}, jitter={self.jitter})"
        )
