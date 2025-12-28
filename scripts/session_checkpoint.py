"""
Session Checkpoint System - 3-Tier Validation at Session Boundaries

Ensures 3-Tier automated resolution system is active and working:
- Session Start: Verify all components enabled
- Session End: Validate automation rate achieved
- Periodic Checkpoints: Monitor progress during session

Goal: Prevent manual debugging regression, enforce 95% automation

Usage:
    from scripts.session_checkpoint import session_checkpoint

    # At session start
    session_checkpoint.session_start()

    # During work (optional, every 30min)
    session_checkpoint.periodic_check()

    # At session end
    report = session_checkpoint.session_end()
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CheckpointResult:
    """Result of a checkpoint validation"""

    success: bool
    timestamp: datetime
    checks: Dict[str, bool] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)


class SessionCheckpoint:
    """
    Session lifecycle validator for 3-Tier automated resolution

    Enforces mandatory usage of:
    - Auto3TierWrapper for error detection
    - UnifiedErrorResolver for resolution
    - Obsidian auto-search for past solutions
    """

    def __init__(self):
        self.session_start_time: Optional[datetime] = None
        self.last_checkpoint_time: Optional[datetime] = None
        self.checkpoint_interval = timedelta(minutes=30)

        # Components to validate
        self.required_components = {
            "auto_3tier_wrapper": "scripts.auto_3tier_wrapper",
            "unified_error_resolver": "scripts.unified_error_resolver",
            "obsidian_auto_search": "scripts.auto_obsidian_context",
        }

        # Statistics tracking
        self.session_stats = {
            "total_errors_encountered": 0,
            "automation_checks": 0,
            "warnings_issued": 0,
            "checkpoints_passed": 0,
            "checkpoints_failed": 0,
        }

    def session_start(self) -> CheckpointResult:
        """
        Validate system at session start

        Checks:
        1. Auto3TierWrapper available and enabled
        2. UnifiedErrorResolver available
        3. Obsidian auto-search configured
        4. Circuit breaker in CLOSED state

        Returns:
            CheckpointResult with validation status

        Raises:
            RuntimeError if critical components unavailable
        """
        logger.info("=" * 60)
        logger.info("[EMOJI] SESSION START CHECKPOINT")
        logger.info("=" * 60)

        self.session_start_time = datetime.now()
        self.last_checkpoint_time = datetime.now()

        result = CheckpointResult(success=True, timestamp=self.session_start_time)

        # Check 1: Auto3TierWrapper
        try:
            from scripts.auto_3tier_wrapper import get_wrapper

            wrapper = get_wrapper()

            result.checks["auto_3tier_wrapper_available"] = True

            if wrapper.is_enabled():
                result.checks["auto_3tier_wrapper_enabled"] = True
                logger.info("[OK] Auto3TierWrapper: ENABLED")
            else:
                result.checks["auto_3tier_wrapper_enabled"] = False
                result.warnings.append("Auto3TierWrapper is DISABLED")
                logger.warning("[WARN]  Auto3TierWrapper: DISABLED")

            # Check circuit breaker
            stats = wrapper.get_statistics()
            cb_state = stats.get("circuit_breaker_state", "UNKNOWN")

            if cb_state == "CLOSED":
                result.checks["circuit_breaker_ok"] = True
                logger.info(f"[OK] Circuit Breaker: {cb_state}")
            else:
                result.checks["circuit_breaker_ok"] = False
                result.warnings.append(f"Circuit breaker: {cb_state}")
                logger.warning(f"[WARN]  Circuit Breaker: {cb_state}")

        except ImportError as e:
            result.checks["auto_3tier_wrapper_available"] = False
            result.errors.append(f"Auto3TierWrapper import failed: {e}")
            logger.error(f"[FAIL] Auto3TierWrapper: UNAVAILABLE - {e}")
            result.success = False

        # Check 2: UnifiedErrorResolver
        try:
            from scripts.unified_error_resolver import UnifiedErrorResolver

            resolver = UnifiedErrorResolver()

            result.checks["unified_error_resolver_available"] = True
            logger.info("[OK] UnifiedErrorResolver: AVAILABLE")

        except ImportError as e:
            result.checks["unified_error_resolver_available"] = False
            result.errors.append(f"UnifiedErrorResolver import failed: {e}")
            logger.error(f"[FAIL] UnifiedErrorResolver: UNAVAILABLE - {e}")
            result.success = False

        # Check 3: Obsidian auto-search (optional, just warn)
        try:
            from scripts.auto_obsidian_context import AutoObsidianContext

            auto_ctx = AutoObsidianContext()

            result.checks["obsidian_auto_search_available"] = True
            logger.info("[OK] Obsidian Auto-Search: AVAILABLE")

        except ImportError as e:
            result.checks["obsidian_auto_search_available"] = False
            result.warnings.append(f"Obsidian auto-search not available: {e}")
            logger.warning(f"[WARN]  Obsidian Auto-Search: UNAVAILABLE - {e}")

        # Summary
        logger.info("")
        logger.info("[EMOJI] Checkpoint Summary:")
        logger.info(f"  Total Checks: {len(result.checks)}")
        logger.info(f"  Passed: {sum(result.checks.values())}")
        logger.info(f"  Warnings: {len(result.warnings)}")
        logger.info(f"  Errors: {len(result.errors)}")

        if result.success:
            self.session_stats["checkpoints_passed"] += 1
            logger.info("")
            logger.info("[OK] SESSION START: All critical systems operational")
            logger.info("=" * 60)
        else:
            self.session_stats["checkpoints_failed"] += 1
            logger.error("")
            logger.error("[FAIL] SESSION START: Critical systems missing!")
            logger.error("=" * 60)
            raise RuntimeError(
                f"Session start failed: {len(result.errors)} critical errors. " f"Fix issues before proceeding."
            )

        return result

    def periodic_check(self) -> CheckpointResult:
        """
        Periodic checkpoint during session (every 30 minutes)

        Checks:
        1. Automation rate progress
        2. Time since last checkpoint
        3. Circuit breaker health

        Returns:
            CheckpointResult with progress status
        """
        now = datetime.now()

        # Check if checkpoint is due
        if self.last_checkpoint_time:
            elapsed = now - self.last_checkpoint_time
            if elapsed < self.checkpoint_interval:
                logger.debug(f"⏭  Checkpoint not due yet ({elapsed.seconds}s < {self.checkpoint_interval.seconds}s)")
                return CheckpointResult(success=True, timestamp=now)

        logger.info("=" * 60)
        logger.info("[EMOJI] PERIODIC CHECKPOINT")
        logger.info("=" * 60)

        self.last_checkpoint_time = now

        result = CheckpointResult(success=True, timestamp=now)

        # Get statistics from Auto3TierWrapper
        try:
            from scripts.auto_3tier_wrapper import get_wrapper

            wrapper = get_wrapper()
            stats = wrapper.get_statistics()

            result.statistics = stats
            result.checks["statistics_available"] = True

            # Check automation rate
            automation_rate = stats.get("automation_rate", 0.0)
            total_errors = stats.get("total_errors", 0)

            logger.info(f"[EMOJI] Progress Report:")
            logger.info(f"  Total Errors: {total_errors}")
            logger.info(f"  Automation Rate: {automation_rate * 100:.1f}%")
            logger.info(f"  Tier 1 Hits: {stats.get('tier1_hits', 0)}")
            logger.info(f"  Tier 2 Auto: {stats.get('tier2_auto', 0)}")
            logger.info(f"  Tier 3 Escalations: {stats.get('tier3_escalations', 0)}")
            logger.info(f"  Time Saved: {stats.get('time_saved_minutes', 0):.1f} minutes")

            # Warn if automation rate below target
            if total_errors >= 5 and automation_rate < 0.90:
                warning = f"[WARN]  Automation rate {automation_rate * 100:.1f}% below 90% target"
                result.warnings.append(warning)
                logger.warning(warning)
                self.session_stats["warnings_issued"] += 1

            # Check circuit breaker
            cb_state = stats.get("circuit_breaker_state", "UNKNOWN")
            if cb_state != "CLOSED":
                warning = f"[WARN]  Circuit breaker: {cb_state}"
                result.warnings.append(warning)
                logger.warning(warning)

            self.session_stats["checkpoints_passed"] += 1

        except Exception as e:
            result.checks["statistics_available"] = False
            result.errors.append(f"Statistics retrieval failed: {e}")
            logger.error(f"[FAIL] Failed to get statistics: {e}")
            result.success = False
            self.session_stats["checkpoints_failed"] += 1

        logger.info("=" * 60)
        return result

    def session_end(self) -> CheckpointResult:
        """
        Validate system at session end

        Checks:
        1. Final automation rate achieved
        2. Total time saved
        3. Circuit breaker health

        Returns:
            CheckpointResult with final statistics

        Warnings if:
        - Automation rate < 90% (target: 95%)
        - Zero errors encountered (system not tested)
        """
        logger.info("=" * 60)
        logger.info("[EMOJI] SESSION END CHECKPOINT")
        logger.info("=" * 60)

        now = datetime.now()
        session_duration = (now - self.session_start_time).seconds / 60 if self.session_start_time else 0

        result = CheckpointResult(success=True, timestamp=now)

        # Get final statistics
        try:
            from scripts.auto_3tier_wrapper import get_wrapper

            wrapper = get_wrapper()
            stats = wrapper.get_statistics()

            result.statistics = stats
            result.checks["statistics_available"] = True

            automation_rate = stats.get("automation_rate", 0.0)
            total_errors = stats.get("total_errors", 0)
            time_saved = stats.get("time_saved_minutes", 0.0)

            logger.info("")
            logger.info("[EMOJI] FINAL SESSION REPORT:")
            logger.info(f"  Session Duration: {session_duration:.1f} minutes")
            logger.info(f"  Total Errors: {total_errors}")
            logger.info(f"  Automation Rate: {automation_rate * 100:.1f}%")
            logger.info("")
            logger.info("  3-Tier Breakdown:")
            logger.info(f"    Tier 1 (Obsidian): {stats.get('tier1_hits', 0)} hits")
            logger.info(f"    Tier 2 (Context7 AUTO): {stats.get('tier2_auto', 0)} hits")
            logger.info(f"    Tier 2 (Context7 CONFIRMED): {stats.get('tier2_confirmed', 0)} hits")
            logger.info(f"    Tier 3 (User): {stats.get('tier3_escalations', 0)} escalations")
            logger.info("")
            logger.info(f"  Time Saved: {time_saved:.1f} minutes")
            logger.info(f"  Auto Recoveries: {stats.get('auto_recoveries', 0)}")
            logger.info(f"  Failed Recoveries: {stats.get('failed_recoveries', 0)}")
            logger.info("")

            # Validation: Automation rate
            if total_errors == 0:
                warning = "[WARN]  No errors encountered - system not tested this session"
                result.warnings.append(warning)
                logger.warning(warning)
                self.session_stats["warnings_issued"] += 1
            elif automation_rate < 0.90:
                warning = f"[WARN]  Automation rate {automation_rate * 100:.1f}% below 90% target (Goal: 95%)"
                result.warnings.append(warning)
                logger.warning(warning)
                self.session_stats["warnings_issued"] += 1

                # Provide remediation suggestions
                logger.warning("")
                logger.warning("[EMOJI] Remediation Suggestions:")
                if stats.get("tier3_escalations", 0) > total_errors * 0.1:
                    logger.warning("  - Too many Tier 3 escalations: Review Obsidian documentation coverage")
                if stats.get("failed_recoveries", 0) > 0:
                    logger.warning("  - Failed recoveries detected: Review solution accuracy")
                logger.warning("  - Target: 70% Tier 1, 25% Tier 2, 5% Tier 3")
            else:
                logger.info(f"[OK] Automation rate {automation_rate * 100:.1f}% meets target!")
                result.checks["automation_rate_ok"] = True

            # Circuit breaker check
            cb_state = stats.get("circuit_breaker_state", "UNKNOWN")
            if cb_state == "CLOSED":
                result.checks["circuit_breaker_ok"] = True
                logger.info(f"[OK] Circuit Breaker: {cb_state}")
            else:
                result.warnings.append(f"Circuit breaker: {cb_state}")
                logger.warning(f"[WARN]  Circuit Breaker: {cb_state}")

            self.session_stats["checkpoints_passed"] += 1

        except Exception as e:
            result.errors.append(f"Failed to get final statistics: {e}")
            logger.error(f"[FAIL] Session end validation failed: {e}")
            result.success = False
            self.session_stats["checkpoints_failed"] += 1

        # Session summary
        logger.info("")
        logger.info("[EMOJI] Session Summary:")
        logger.info(f"  Automation Checks: {self.session_stats['automation_checks']}")
        logger.info(f"  Warnings Issued: {self.session_stats['warnings_issued']}")
        logger.info(f"  Checkpoints Passed: {self.session_stats['checkpoints_passed']}")
        logger.info(f"  Checkpoints Failed: {self.session_stats['checkpoints_failed']}")

        if result.success and not result.warnings:
            logger.info("")
            logger.info("[OK] SESSION END: All targets met! Excellent automation.")
        elif result.success and result.warnings:
            logger.info("")
            logger.info("[WARN]  SESSION END: Completed with warnings. Review above.")
        else:
            logger.error("")
            logger.error("[FAIL] SESSION END: Failed validation. Review errors.")

        logger.info("=" * 60)

        return result

    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        return {
            **self.session_stats,
            "session_start": self.session_start_time.isoformat() if self.session_start_time else None,
            "last_checkpoint": self.last_checkpoint_time.isoformat() if self.last_checkpoint_time else None,
        }


# Global singleton instance
_checkpoint_instance: Optional[SessionCheckpoint] = None


def get_checkpoint() -> SessionCheckpoint:
    """Get or create global SessionCheckpoint instance"""
    global _checkpoint_instance
    if _checkpoint_instance is None:
        _checkpoint_instance = SessionCheckpoint()
        logger.info("[EMOJI] SessionCheckpoint initialized")
    return _checkpoint_instance


# Convenience singleton
session_checkpoint = get_checkpoint()


if __name__ == "__main__":
    # Self-test
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    print("\n" + "=" * 60)
    print("Testing SessionCheckpoint System")
    print("=" * 60 + "\n")

    # Test session start
    try:
        result = session_checkpoint.session_start()
        print(f"\n[OK] Session start: {result.success}")
        print(f"Checks passed: {sum(result.checks.values())}/{len(result.checks)}")
        print(f"Warnings: {len(result.warnings)}")
    except RuntimeError as e:
        print(f"\n[FAIL] Session start failed: {e}")

    # Simulate some work
    print("\n... simulating work for 5 seconds ...\n")
    time.sleep(5)

    # Test periodic check
    result = session_checkpoint.periodic_check()
    print(f"\n[OK] Periodic check: {result.success}")

    # Test session end
    result = session_checkpoint.session_end()
    print(f"\n[OK] Session end: {result.success}")
    print(f"Final automation rate: {result.statistics.get('automation_rate', 0) * 100:.1f}%")

    print("\n" + "=" * 60)
    print("SessionCheckpoint Test Complete")
    print("=" * 60)
