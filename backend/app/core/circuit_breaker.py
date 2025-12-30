"""
Simple circuit breaker and TTL cache utilities for uncertainty endpoints.

Designed to be lightweight and dependency-free to avoid coupling with external cache/queue.
"""

import functools
import time
from typing import Any, Callable, Optional


class CircuitBreaker:
    """
    Minimal circuit breaker implementation.

    - Opens when failure count exceeds threshold
    - Half-open after recovery_timeout seconds
    - Closes on successful call in half-open state
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self._failures = 0
        self._state = "CLOSED"  # CLOSED | OPEN | HALF_OPEN
        self._opened_at: Optional[float] = None

    def __call__(self, func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Fast-fail if open
            if self._state == "OPEN":
                if self._opened_at and (time.time() - self._opened_at) > self.recovery_timeout:
                    # Move to HALF_OPEN and try once
                    self._state = "HALF_OPEN"
                else:
                    raise RuntimeError("Circuit breaker open")

            try:
                result = await func(*args, **kwargs)
                # Success: reset on HALF_OPEN or CLOSED
                self._on_success()
                return result
            except self.expected_exception:
                self._on_failure()
                raise

        return wrapper

    def _on_success(self):
        """Handle successful call - transition to CLOSED from any state"""
        if self._state == "HALF_OPEN":
            # Successful call in HALF_OPEN -> move to CLOSED
            self._reset()
        elif self._state == "CLOSED":
            # Still closed, just reset failure count
            self._failures = 0

    def _on_failure(self):
        """Handle failed call - increment failures and transition states"""
        if self._state == "HALF_OPEN":
            # Failure in HALF_OPEN -> immediately go back to OPEN
            self._state = "OPEN"
            self._opened_at = time.time()
            # Keep failure count for monitoring
        elif self._state == "CLOSED":
            # Increment failures, open if threshold reached
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._state = "OPEN"
                self._opened_at = time.time()

    def _reset(self):
        """Reset to clean CLOSED state"""
        self._failures = 0
        self._state = "CLOSED"
        self._opened_at = None

    @property
    def state(self) -> str:
        return self._state

    def force_reset(self) -> bool:
        """
        강제로 Circuit Breaker를 CLOSED 상태로 리셋합니다.

        HIGH-04 FIX: 운영자가 수동으로 서비스 복구할 수 있도록 추가 (2025-12-30)

        사용 시나리오:
        - 외부 서비스가 복구되었지만 recovery_timeout 전인 경우
        - 테스트/디버깅 시 강제 리셋 필요한 경우
        - 운영자가 서비스 상태 확인 후 수동 복구

        Returns:
            bool: True if reset was performed (was not already CLOSED), False otherwise
        """
        if self._state == "CLOSED":
            return False  # Already closed, nothing to reset

        previous_state = self._state
        self._reset()
        # Log for audit trail
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Circuit breaker force reset: {previous_state} -> CLOSED")
        return True

    def get_status(self) -> dict:
        """
        Circuit Breaker 현재 상태 정보를 반환합니다.

        Returns:
            dict: 상태, 실패 횟수, 열린 시간 등
        """
        import time

        time_in_open = None
        if self._state == "OPEN" and self._opened_at:
            time_in_open = time.time() - self._opened_at

        return {
            "state": self._state,
            "failures": self._failures,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "opened_at": self._opened_at,
            "time_in_open_seconds": time_in_open,
            "can_force_reset": self._state != "CLOSED",
        }


class SimpleTTLCache:
    """In-memory TTL cache for small payloads (not for large responses)."""

    def __init__(self):
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if not entry:
            return None
        expires_at, value = entry
        if time.time() > expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: int):
        self._store[key] = (time.time() + ttl_seconds, value)
