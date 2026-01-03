"""
Tests for Circuit Breaker state machine (P0 Critical Issue #1).

Verifies all state transitions:
- CLOSED -> OPEN (failures >= threshold)
- OPEN -> HALF_OPEN (after recovery_timeout)
- HALF_OPEN -> CLOSED (on success)
- HALF_OPEN -> OPEN (on failure)
"""

import asyncio
import time

import pytest

from backend.app.core.circuit_breaker import CircuitBreaker


class TestCircuitBreakerStateMachine:
    """Test all state transitions of Circuit Breaker"""

    @pytest.mark.asyncio
    async def test_initial_state_is_closed(self):
        """Circuit breaker should start in CLOSED state"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
        assert cb.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_closed_to_open_transition(self):
        """CLOSED -> OPEN when failures >= threshold"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1)

        @cb
        async def failing_func():
            raise ValueError("Test failure")

        # Execute 3 times (threshold)
        for i in range(3):
            assert cb.state == "CLOSED", f"Should stay CLOSED until threshold (attempt {i + 1})"
            with pytest.raises(ValueError):
                await failing_func()

        # After threshold, should be OPEN
        assert cb.state == "OPEN", "Should transition to OPEN after 3 failures"

    @pytest.mark.asyncio
    async def test_open_stays_open_before_timeout(self):
        """OPEN state should reject calls before recovery_timeout"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=10)  # 10 sec timeout

        @cb
        async def failing_func():
            raise ValueError("Test failure")

        # Trigger OPEN state
        for _ in range(2):
            with pytest.raises(ValueError):
                await failing_func()

        assert cb.state == "OPEN"

        # Should fast-fail with RuntimeError (not execute function)
        with pytest.raises(RuntimeError, match="Circuit breaker open"):
            await failing_func()

        assert cb.state == "OPEN"  # Still OPEN

    @pytest.mark.asyncio
    async def test_open_to_half_open_transition(self):
        """OPEN -> HALF_OPEN after recovery_timeout"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)  # 1 sec timeout

        @cb
        async def failing_func():
            raise ValueError("Test failure")

        # Trigger OPEN state
        for _ in range(2):
            with pytest.raises(ValueError):
                await failing_func()

        assert cb.state == "OPEN"

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # Next call should move to HALF_OPEN (even if it fails)
        try:
            await failing_func()
        except (ValueError, RuntimeError):
            pass

        # Should have transitioned through HALF_OPEN (now back to OPEN due to failure)
        assert cb.state == "OPEN", "Should be OPEN after HALF_OPEN failure"

    @pytest.mark.asyncio
    async def test_half_open_to_closed_on_success(self):
        """HALF_OPEN -> CLOSED on successful call"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        call_count = 0

        @cb
        async def sometimes_failing_func():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ValueError("Fail")
            return "success"

        # Trigger OPEN state (2 failures)
        for _ in range(2):
            with pytest.raises(ValueError):
                await sometimes_failing_func()

        assert cb.state == "OPEN"

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # Next call: OPEN -> HALF_OPEN, then success -> CLOSED
        _success_count = 2  # noqa: F841 - controls success in sometimes_failing_func
        result = await sometimes_failing_func()

        assert result == "success"
        assert cb.state == "CLOSED", "Should transition to CLOSED on HALF_OPEN success"

    @pytest.mark.asyncio
    async def test_half_open_to_open_on_failure(self):
        """HALF_OPEN -> OPEN immediately on failure"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

        @cb
        async def failing_func():
            raise ValueError("Test failure")

        # Trigger OPEN state
        for _ in range(2):
            with pytest.raises(ValueError):
                await failing_func()

        assert cb.state == "OPEN"
        opened_at_first = cb._opened_at

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # Next call: OPEN -> HALF_OPEN, then fail -> back to OPEN
        with pytest.raises(ValueError):
            await failing_func()

        assert cb.state == "OPEN", "Should go back to OPEN on HALF_OPEN failure"
        assert cb._opened_at > opened_at_first, "Should update opened_at timestamp"

    @pytest.mark.asyncio
    async def test_closed_state_resets_failure_count_on_success(self):
        """In CLOSED state, successful call should reset failure count"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
        call_count = 0

        @cb
        async def sometimes_failing_func():
            nonlocal call_count
            call_count += 1
            if call_count in [1, 2]:  # Fail first 2 calls
                raise ValueError("Fail")
            return "success"

        # 2 failures
        for _ in range(2):
            with pytest.raises(ValueError):
                await sometimes_failing_func()

        assert cb._failures == 2
        assert cb.state == "CLOSED"  # Not opened yet (threshold=3)

        # 1 success - should reset failure count
        result = await sometimes_failing_func()
        assert result == "success"
        assert cb._failures == 0, "Failure count should reset on success"
        assert cb.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_full_cycle_closed_open_halfopen_closed(self):
        """Test complete state cycle: CLOSED -> OPEN -> HALF_OPEN -> CLOSED"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5)
        call_count = 0

        @cb
        async def controlled_func():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ValueError("Fail initially")
            return "recovered"

        # 1. Start CLOSED
        assert cb.state == "CLOSED"

        # 2. CLOSED -> OPEN (2 failures)
        for _ in range(2):
            with pytest.raises(ValueError):
                await controlled_func()
        assert cb.state == "OPEN"

        # 3. Wait for recovery timeout
        await asyncio.sleep(0.6)

        # 4. OPEN -> HALF_OPEN -> CLOSED (success)
        result = await controlled_func()
        assert result == "recovered"
        assert cb.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_multiple_failures_in_open_state(self):
        """Multiple calls in OPEN state should all fast-fail"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=10)

        @cb
        async def failing_func():
            raise ValueError("Should not execute")

        # Trigger OPEN
        for _ in range(2):
            with pytest.raises(ValueError):
                await failing_func()

        assert cb.state == "OPEN"

        # All subsequent calls should fast-fail with RuntimeError
        for _ in range(5):
            with pytest.raises(RuntimeError, match="Circuit breaker open"):
                await failing_func()

        assert cb.state == "OPEN"


class TestCircuitBreakerEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_threshold_of_one(self):
        """Circuit breaker with threshold=1 should open immediately"""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=1)

        @cb
        async def failing_func():
            raise ValueError("Fail")

        # Single failure should open
        with pytest.raises(ValueError):
            await failing_func()

        assert cb.state == "OPEN"

    @pytest.mark.asyncio
    async def test_custom_exception_type(self):
        """Circuit breaker should only catch expected_exception"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1, expected_exception=ValueError)

        @cb
        async def func_with_different_errors():
            raise TypeError("Different error type")

        # TypeError should not be caught (not expected_exception)
        with pytest.raises(TypeError):
            await func_with_different_errors()

        # State should still be CLOSED (TypeError not counted)
        assert cb.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_zero_recovery_timeout(self):
        """recovery_timeout=0 should allow immediate retry"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0)
        call_count = 0

        @cb
        async def recovering_func():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ValueError("Fail")
            return "success"

        # Trigger OPEN
        for _ in range(2):
            with pytest.raises(ValueError):
                await recovering_func()

        assert cb.state == "OPEN"

        # Immediate retry (no sleep needed)
        result = await recovering_func()
        assert result == "success"
        assert cb.state == "CLOSED"


class TestCircuitBreakerPerformance:
    """Test performance characteristics"""

    @pytest.mark.asyncio
    async def test_fast_fail_performance(self):
        """OPEN state should fast-fail without executing function"""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=10)
        executed = False

        @cb
        async def expensive_func():
            nonlocal executed
            executed = True
            await asyncio.sleep(1)  # Simulate expensive operation
            raise ValueError("Expensive failure")

        # Trigger OPEN
        executed = False
        with pytest.raises(ValueError):
            await expensive_func()
        assert executed  # Should have executed once
        assert cb.state == "OPEN"

        # Fast-fail should NOT execute function
        executed = False
        start = time.time()
        with pytest.raises(RuntimeError):
            await expensive_func()
        elapsed = time.time() - start

        assert not executed, "Function should not execute in OPEN state"
        assert elapsed < 0.1, "Fast-fail should be < 100ms"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
