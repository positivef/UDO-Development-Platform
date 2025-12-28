"""
Auto 3-Tier Wrapper - Automatic Error Resolution System

Automatically wraps all tool calls to trigger 3-Tier resolution cascade:
- Tier 1 (Obsidian): Past solutions (<10ms, 70% hit rate)
- Tier 2 (Context7): Official docs (<500ms, 25% hit rate)
- Tier 3 (User): Human intervention (5% cases only)

Goal: 95% automation rate

Usage:
    from scripts.auto_3tier_wrapper import auto_3tier, get_wrapper

    # Wrap any tool function
    @auto_3tier
    def my_tool_function(*args, **kwargs):
        # Your implementation
        pass

    # Get statistics
    stats = get_wrapper().get_statistics()
"""

import functools
import logging
import subprocess
import time
from typing import Any, Callable, Dict, Optional, TypeVar, cast
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)

# Type variable for generic function wrapping
F = TypeVar("F", bound=Callable[..., Any])


class Auto3TierWrapper:
    """
    Automatic 3-Tier resolution wrapper for all tool calls

    Detects errors and automatically triggers resolution cascade:
    1. Search Obsidian for past solutions
    2. Query Context7 for official documentation
    3. Escalate to user only if both fail
    """

    def __init__(self):
        self.enabled = True
        self.statistics = {
            "total_calls": 0,
            "total_errors": 0,
            "tier1_hits": 0,  # Obsidian
            "tier2_hits": 0,  # Context7
            "tier2_auto": 0,  # Context7 auto-applied (HIGH confidence)
            "tier2_confirmed": 0,  # Context7 user-confirmed (MEDIUM confidence)
            "tier3_escalations": 0,  # User intervention
            "auto_recoveries": 0,
            "failed_recoveries": 0,
            "total_time_saved": 0.0,  # minutes
        }

        # Circuit breaker for safety
        self.circuit_breaker = {
            "consecutive_failures": 0,
            "threshold": 3,
            "state": "CLOSED",  # CLOSED, OPEN, HALF_OPEN
            "last_failure_time": None,
        }

        # Lazy import to avoid circular dependencies
        self._resolver = None

    @property
    def resolver(self):
        """Lazy load UnifiedErrorResolver to avoid circular imports"""
        if self._resolver is None:
            try:
                from scripts.unified_error_resolver import UnifiedErrorResolver

                self._resolver = UnifiedErrorResolver()
                logger.info("[OK] UnifiedErrorResolver initialized")
            except ImportError as e:
                logger.warning(f"[WARN]  UnifiedErrorResolver not available: {e}")
                self._resolver = None
        return self._resolver

    def is_enabled(self) -> bool:
        """Check if wrapper is enabled and circuit breaker allows operation"""
        if not self.enabled:
            return False

        if self.circuit_breaker["state"] == "OPEN":
            # Check if we should try half-open
            if self.circuit_breaker["last_failure_time"]:
                elapsed = (datetime.now() - self.circuit_breaker["last_failure_time"]).seconds
                if elapsed > 60:  # 1 minute cooldown
                    self.circuit_breaker["state"] = "HALF_OPEN"
                    logger.info("[EMOJI] Circuit breaker: HALF_OPEN (testing recovery)")
                    return True
            return False

        return True

    def _is_error(self, result: Any) -> bool:
        """
        Detect if a result indicates an error

        Checks for:
        - Exception objects
        - Dict with 'error' or 'exit_code' != 0
        - None when expecting data
        - Bash result with stderr and exit_code != 0
        """
        if isinstance(result, Exception):
            return True

        if isinstance(result, dict):
            # Check for explicit error field
            if result.get("error") or result.get("success") is False:
                return True

            # Check for non-zero exit code
            exit_code = result.get("exit_code")
            if exit_code is not None and exit_code != 0:
                return True

            # Check for stderr with non-zero exit code
            if result.get("stderr") and result.get("exit_code", 0) != 0:
                return True

        return False

    def _extract_error_message(self, result: Any) -> str:
        """Extract error message from various result formats"""
        if isinstance(result, Exception):
            return f"{type(result).__name__}: {str(result)}"

        if isinstance(result, dict):
            # Try multiple error fields
            error_msg = result.get("error") or result.get("stderr") or result.get("message") or str(result)
            return str(error_msg)

        return str(result)

    def _apply_and_retry(
        self, solution: str, original_func: Callable, args: tuple, kwargs: dict, context: Dict[str, Any]
    ) -> Any:
        """
        Apply solution and retry original function

        Executes the solution as a bash command, then retries the original function.

        Returns:
            Result of retried function or raises exception
        """
        logger.info(f"[EMOJI] Applying solution: {solution[:100]}")

        # Execute solution as bash command
        try:
            # Run solution command
            result = subprocess.run(solution, shell=True, capture_output=True, text=True, timeout=30)  # 30 second timeout

            if result.returncode == 0:
                logger.info(f"[OK] Solution applied successfully: {result.stdout[:100] if result.stdout else '(no output)'}")
            else:
                logger.warning(f"[WARN]  Solution returned non-zero exit code: {result.returncode}")
                logger.warning(f"stderr: {result.stderr[:200]}")
                # Continue anyway - might still fix the issue

        except subprocess.TimeoutExpired:
            logger.error("[FAIL] Solution execution timed out after 30 seconds")
            self.statistics["failed_recoveries"] += 1
            self._update_circuit_breaker(failed=True)
            raise Exception(f"Solution timeout: {solution}")

        except Exception as e:
            logger.error(f"[FAIL] Failed to execute solution: {e}")
            self.statistics["failed_recoveries"] += 1
            self._update_circuit_breaker(failed=True)
            raise

        # Retry the original function
        try:
            result = original_func(*args, **kwargs)

            if not self._is_error(result):
                logger.info("[OK] Retry successful after applying solution")
                self.statistics["auto_recoveries"] += 1
                self.circuit_breaker["consecutive_failures"] = 0
                return result
            else:
                logger.warning("[WARN]  Solution applied but retry still failed")
                raise Exception(f"Solution didn't work: {self._extract_error_message(result)}")

        except Exception as e:
            logger.error(f"[FAIL] Retry failed: {e}")
            self.statistics["failed_recoveries"] += 1
            self._update_circuit_breaker(failed=True)
            raise

    def _update_circuit_breaker(self, failed: bool = False):
        """Update circuit breaker state based on success/failure"""
        if failed:
            self.circuit_breaker["consecutive_failures"] += 1
            self.circuit_breaker["last_failure_time"] = datetime.now()

            if self.circuit_breaker["consecutive_failures"] >= self.circuit_breaker["threshold"]:
                self.circuit_breaker["state"] = "OPEN"
                logger.error(
                    f"[EMOJI] Circuit breaker OPEN: {self.circuit_breaker['consecutive_failures']} consecutive failures"
                )
        else:
            self.circuit_breaker["consecutive_failures"] = 0
            if self.circuit_breaker["state"] == "HALF_OPEN":
                self.circuit_breaker["state"] = "CLOSED"
                logger.info("[OK] Circuit breaker CLOSED: Recovery successful")

    def wrap_tool(self, func: F) -> F:
        """
        Decorator to wrap any tool function with 3-Tier resolution

        Usage:
            @wrapper.wrap_tool
            def my_tool(*args, **kwargs):
                return result
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.statistics["total_calls"] += 1

            # Skip if disabled or circuit breaker open
            if not self.is_enabled():
                logger.debug(f"⏭  Auto-resolution disabled for {func.__name__}")
                return func(*args, **kwargs)

            try:
                # Execute original function
                result = func(*args, **kwargs)

                # Check if result indicates error
                if self._is_error(result):
                    self.statistics["total_errors"] += 1
                    error_msg = self._extract_error_message(result)
                    logger.warning(f"[WARN]  Error detected in {func.__name__}: {error_msg[:100]}")

                    # Only trigger resolution if resolver is available
                    if self.resolver is None:
                        logger.warning("[WARN]  UnifiedErrorResolver not available, skipping auto-resolution")
                        return result

                    # [EMOJI] AUTOMATIC 3-TIER CASCADE
                    start_time = time.time()

                    context = {
                        "tool": func.__name__,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200],
                        "timestamp": datetime.now().isoformat(),
                    }

                    solution = self.resolver.resolve_error(error_msg, context=context)

                    elapsed = (time.time() - start_time) * 1000  # ms

                    if solution:
                        # Tier 1 or Tier 2 hit!
                        stats = self.resolver.get_statistics()

                        if stats.get("tier1", 0) > 0:
                            # Obsidian hit
                            self.statistics["tier1_hits"] += 1
                            self.statistics["total_time_saved"] += 8.0  # Assume 8min saved vs manual
                            logger.info(f"[OK] Tier 1 (Obsidian) hit in {elapsed:.1f}ms")

                        elif stats.get("tier2_auto", 0) > 0:
                            # Context7 auto-applied (HIGH confidence)
                            self.statistics["tier2_hits"] += 1
                            self.statistics["tier2_auto"] += 1
                            self.statistics["total_time_saved"] += 5.0  # Assume 5min saved
                            logger.info(f"[OK] Tier 2 (Context7 HIGH) auto-applied in {elapsed:.1f}ms")

                        elif stats.get("tier2_confirmed", 0) > 0:
                            # Context7 user-confirmed (MEDIUM confidence)
                            self.statistics["tier2_hits"] += 1
                            self.statistics["tier2_confirmed"] += 1
                            self.statistics["total_time_saved"] += 3.0  # Partial savings
                            logger.info(f"[OK] Tier 2 (Context7 MEDIUM) user-confirmed in {elapsed:.1f}ms")

                        # Apply solution and retry
                        return self._apply_and_retry(solution, func, args, kwargs, context)

                    else:
                        # Tier 3: Escalate to user
                        self.statistics["tier3_escalations"] += 1
                        logger.error(f"[FAIL] Tier 3 escalation: No automated solution for {error_msg[:100]}")

                        # Return original error result for user to handle
                        return result

                # No error, return result as-is
                return result

            except Exception as e:
                # Unexpected exception during wrapping
                self.statistics["total_errors"] += 1
                logger.error(f"[FAIL] Wrapper exception in {func.__name__}: {e}")
                logger.debug(traceback.format_exc())

                # Don't re-wrap exceptions, just propagate
                raise

        return cast(F, wrapper)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current statistics

        Returns:
            {
                "total_calls": int,
                "total_errors": int,
                "tier1_hits": int,
                "tier2_hits": int,
                "tier3_escalations": int,
                "automation_rate": float,  # 0.0 to 1.0
                "time_saved_minutes": float,
                "circuit_breaker_state": str
            }
        """
        total_resolved = self.statistics["tier1_hits"] + self.statistics["tier2_auto"] + self.statistics["tier2_confirmed"]
        total_errors = self.statistics["total_errors"]

        automation_rate = (total_resolved / total_errors) if total_errors > 0 else 0.0

        return {
            **self.statistics,
            "automation_rate": automation_rate,
            "time_saved_minutes": self.statistics["total_time_saved"],
            "circuit_breaker_state": self.circuit_breaker["state"],
            "circuit_breaker_failures": self.circuit_breaker["consecutive_failures"],
        }

    def reset_statistics(self):
        """Reset all statistics counters"""
        for key in self.statistics:
            if isinstance(self.statistics[key], (int, float)):
                self.statistics[key] = 0
        logger.info("[EMOJI] Statistics reset")

    def enable(self):
        """Enable auto-resolution"""
        self.enabled = True
        logger.info("[OK] Auto-resolution ENABLED")

    def disable(self):
        """Disable auto-resolution"""
        self.enabled = False
        logger.info("⏸  Auto-resolution DISABLED")


# Global singleton instance
_wrapper_instance: Optional[Auto3TierWrapper] = None


def get_wrapper() -> Auto3TierWrapper:
    """Get or create global Auto3TierWrapper instance"""
    global _wrapper_instance
    if _wrapper_instance is None:
        _wrapper_instance = Auto3TierWrapper()
        logger.info("[EMOJI] Auto3TierWrapper initialized")
    return _wrapper_instance


def auto_3tier(func: F) -> F:
    """
    Decorator shorthand for wrapping tools with 3-Tier resolution

    Usage:
        from scripts.auto_3tier_wrapper import auto_3tier

        @auto_3tier
        def my_bash_command(cmd: str):
            return subprocess.run(cmd, ...)
    """
    wrapper = get_wrapper()
    return wrapper.wrap_tool(func)


# Convenience functions
def get_statistics() -> Dict[str, Any]:
    """Get global statistics"""
    return get_wrapper().get_statistics()


def reset_statistics():
    """Reset global statistics"""
    get_wrapper().reset_statistics()


def enable_auto_resolution():
    """Enable auto-resolution globally"""
    get_wrapper().enable()


def disable_auto_resolution():
    """Disable auto-resolution globally"""
    get_wrapper().disable()


if __name__ == "__main__":
    # Self-test
    logging.basicConfig(level=logging.INFO)

    @auto_3tier
    def test_tool(should_fail: bool = False):
        """Test tool that can fail"""
        if should_fail:
            return {"error": "Test error", "exit_code": 1}
        return {"success": True, "data": "Test data"}

    print("Testing Auto3TierWrapper...")

    # Test successful call
    result = test_tool(should_fail=False)
    print(f"[OK] Success result: {result}")

    # Test error detection
    result = test_tool(should_fail=True)
    print(f"[FAIL] Error result: {result}")

    # Print statistics
    stats = get_statistics()
    print(f"\n[EMOJI] Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
