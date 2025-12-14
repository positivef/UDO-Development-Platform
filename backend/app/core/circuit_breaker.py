"""
Simple circuit breaker and TTL cache utilities for uncertainty endpoints.

Designed to be lightweight and dependency-free to avoid coupling with external cache/queue.
"""

import time
import functools
from typing import Callable, Optional, Any


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
            # Successful call in HALF_OPEN → move to CLOSED
            self._reset()
        elif self._state == "CLOSED":
            # Still closed, just reset failure count
            self._failures = 0

    def _on_failure(self):
        """Handle failed call - increment failures and transition states"""
        if self._state == "HALF_OPEN":
            # Failure in HALF_OPEN → immediately go back to OPEN
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

