"""Tests for CircuitBreaker and ExponentialBackoff (M2.1)."""

from __future__ import annotations

import time

import pytest

from agentic_pipeline.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitBreakerState,
    ExponentialBackoff,
)


class TestCircuitBreaker:
    def test_initial_state_closed(self) -> None:
        cb = CircuitBreaker(threshold=3, timeout=30.0)
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0

    def test_opens_after_threshold_failures(self) -> None:
        cb = CircuitBreaker(threshold=3, timeout=30.0)

        for _ in range(3):
            try:
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass

        assert cb.state == CircuitBreakerState.OPEN
        assert cb.failure_count == 3

    def test_raises_open_error_when_open(self) -> None:
        cb = CircuitBreaker(threshold=2, timeout=3600.0)

        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
            except RuntimeError:
                pass

        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "should not reach")

    def test_half_open_transition_on_timeout(self) -> None:
        cb = CircuitBreaker(threshold=1, timeout=0.01)

        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        assert cb.state == CircuitBreakerState.OPEN

        time.sleep(0.02)

        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("still fail")))
        except ValueError:
            pass

        assert cb.state == CircuitBreakerState.OPEN

    def test_half_open_success_closes(self) -> None:
        cb = CircuitBreaker(threshold=1, timeout=0.01)

        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        time.sleep(0.02)

        success = cb.call(lambda: "ok")
        assert success == "ok"
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0

    def test_half_open_failure_reopens(self) -> None:
        cb = CircuitBreaker(threshold=1, timeout=0.01)

        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        time.sleep(0.02)

        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("still fail")))
        except ValueError:
            pass

        assert cb.state == CircuitBreakerState.OPEN

    def test_successful_call_resets_failures(self) -> None:
        cb = CircuitBreaker(threshold=3, timeout=30.0)

        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        assert cb.failure_count == 1

        cb.call(lambda: "ok")
        assert cb.failure_count == 0
        assert cb.state == CircuitBreakerState.CLOSED

    def test_reset(self) -> None:
        cb = CircuitBreaker(threshold=1, timeout=30.0)

        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        assert cb.state == CircuitBreakerState.OPEN

        cb.reset()
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_call_async_success(self) -> None:
        cb = CircuitBreaker(threshold=3, timeout=30.0)

        async def ok() -> str:
            return "hello"

        result = await cb.call_async(ok)
        assert result == "hello"
        assert cb.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_call_async_opens_on_failure(self) -> None:
        cb = CircuitBreaker(threshold=2, timeout=30.0)

        async def fail() -> str:
            raise ValueError("async fail")

        for _ in range(2):
            try:
                await cb.call_async(fail)
            except ValueError:
                pass

        assert cb.state == CircuitBreakerState.OPEN

    @pytest.mark.asyncio
    async def test_call_async_raises_open_error(self) -> None:
        cb = CircuitBreaker(threshold=1, timeout=3600.0)

        async def fail() -> str:
            raise ValueError("async fail")

        try:
            await cb.call_async(fail)
        except ValueError:
            pass

        with pytest.raises(CircuitBreakerOpenError):
            await cb.call_async(fail)


class TestExponentialBackoff:
    def test_delay_increases_with_attempts(self) -> None:
        b = ExponentialBackoff(min_backoff=1.0, max_backoff=60.0, factor=2.0, jitter=0.0)

        d0 = b.delay(0)
        d1 = b.delay(1)
        d2 = b.delay(2)

        assert d0 == 1.0
        assert d1 == 2.0
        assert d2 == 4.0

    def test_delay_bounded_by_max(self) -> None:
        b = ExponentialBackoff(min_backoff=1.0, max_backoff=10.0, factor=10.0, jitter=0.0)

        d_large = b.delay(5)
        assert d_large == 10.0

    def test_jitter_makes_delay_variable(self) -> None:
        b = ExponentialBackoff(min_backoff=1.0, max_backoff=60.0, factor=2.0, jitter=0.5)

        delays = [b.delay(0) for _ in range(10)]
        assert all(1.0 <= d <= 1.5 for d in delays)
        assert len(set(delays)) > 1

    def test_repr(self) -> None:
        b = ExponentialBackoff(min_backoff=1.0, max_backoff=60.0, factor=2.0, jitter=0.1)
        r = repr(b)
        assert "ExponentialBackoff" in r
        assert "min=1.0" in r
        assert "max=60.0" in r
        assert "factor=2.0" in r
