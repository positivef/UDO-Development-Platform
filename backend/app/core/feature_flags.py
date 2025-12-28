"""
Feature Flags Module for Kanban-UDO Integration

Provides runtime feature flag management for Tier 1 rollback strategy.
Allows instant disable of features without deployment (<10 seconds).

Usage:
    from app.core.feature_flags import is_feature_enabled, feature_flags_manager

    if is_feature_enabled("kanban_ai_suggest"):
        # AI suggestion logic
        pass

Author: Claude Code
Date: 2025-12-16
"""

import logging
import os
import threading
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class FeatureFlag(str, Enum):
    """Available feature flags for Kanban-UDO integration."""

    KANBAN_BOARD = "kanban_board"
    KANBAN_AI_SUGGEST = "kanban_ai_suggest"
    KANBAN_ARCHIVE = "kanban_archive"
    KANBAN_DEPENDENCIES = "kanban_dependencies"
    KANBAN_MULTI_PROJECT = "kanban_multi_project"
    KANBAN_OBSIDIAN_SYNC = "kanban_obsidian_sync"
    KANBAN_QUALITY_GATES = "kanban_quality_gates"
    KANBAN_TIME_TRACKING = "kanban_time_tracking"


class FeatureFlagState(BaseModel):
    """State of a feature flag with metadata."""

    enabled: bool
    last_changed: datetime
    changed_by: Optional[str] = None
    reason: Optional[str] = None


class FeatureFlagChangeEvent(BaseModel):
    """Event emitted when a feature flag changes."""

    flag: str
    old_value: bool
    new_value: bool
    changed_at: datetime
    changed_by: Optional[str] = None
    reason: Optional[str] = None


class FeatureFlagsManager:
    """
    Thread-safe feature flag manager with runtime toggle support.

    Features:
    - Thread-safe flag operations
    - Environment variable overrides
    - Change history tracking
    - Event callbacks for flag changes
    - Production-safe defaults (conservative)
    """

    # Production-safe defaults (conservative start)
    DEFAULT_FLAGS: dict[str, bool] = {
        FeatureFlag.KANBAN_BOARD.value: True,  # Core functionality
        FeatureFlag.KANBAN_AI_SUGGEST.value: False,  # Enable after validation
        FeatureFlag.KANBAN_ARCHIVE.value: True,  # Core functionality
        FeatureFlag.KANBAN_DEPENDENCIES.value: True,  # Core functionality
        FeatureFlag.KANBAN_MULTI_PROJECT.value: False,  # Enable after testing
        FeatureFlag.KANBAN_OBSIDIAN_SYNC.value: False,  # Enable after Obsidian setup
        FeatureFlag.KANBAN_QUALITY_GATES.value: True,  # Core functionality
        FeatureFlag.KANBAN_TIME_TRACKING.value: True,  # Core functionality
    }

    def __init__(self) -> None:
        """Initialize feature flags manager."""
        self._lock = threading.RLock()
        self._flags: dict[str, FeatureFlagState] = {}
        self._change_history: list[FeatureFlagChangeEvent] = []
        self._callbacks: list[Callable[[FeatureFlagChangeEvent], None]] = []
        self._max_history_size = 100

        # Initialize with defaults
        self._initialize_flags()

        logger.info("FeatureFlagsManager initialized with %d flags", len(self._flags))

    def _initialize_flags(self) -> None:
        """Initialize flags from defaults and environment variables."""
        now = datetime.utcnow()

        for flag_name, default_value in self.DEFAULT_FLAGS.items():
            # Check for environment variable override
            env_key = f"FEATURE_{flag_name.upper()}"
            env_value = os.getenv(env_key)

            if env_value is not None:
                value = env_value.lower() in ("true", "1", "yes", "on")
                logger.info(
                    "Flag '%s' overridden by env %s=%s", flag_name, env_key, value
                )
            else:
                value = default_value

            self._flags[flag_name] = FeatureFlagState(
                enabled=value,
                last_changed=now,
                changed_by="system",
                reason="Initial configuration",
            )

    def is_enabled(self, flag: str | FeatureFlag) -> bool:
        """
        Check if a feature flag is enabled.

        Args:
            flag: Feature flag name or enum

        Returns:
            True if enabled, False otherwise
        """
        flag_name = flag.value if isinstance(flag, FeatureFlag) else flag

        with self._lock:
            state = self._flags.get(flag_name)
            if state is None:
                logger.warning("Unknown feature flag: %s (returning False)", flag_name)
                return False
            return state.enabled

    def set_flag(
        self,
        flag: str | FeatureFlag,
        enabled: bool,
        changed_by: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Set a feature flag value.

        Args:
            flag: Feature flag name or enum
            enabled: New value
            changed_by: Who made the change
            reason: Reason for the change

        Returns:
            True if changed, False if flag doesn't exist
        """
        flag_name = flag.value if isinstance(flag, FeatureFlag) else flag

        with self._lock:
            if flag_name not in self._flags:
                logger.error("Cannot set unknown feature flag: %s", flag_name)
                return False

            old_state = self._flags[flag_name]
            old_value = old_state.enabled

            if old_value == enabled:
                logger.debug("Flag '%s' already set to %s", flag_name, enabled)
                return True

            now = datetime.utcnow()

            # Update flag state
            self._flags[flag_name] = FeatureFlagState(
                enabled=enabled, last_changed=now, changed_by=changed_by, reason=reason
            )

            # Record change event
            event = FeatureFlagChangeEvent(
                flag=flag_name,
                old_value=old_value,
                new_value=enabled,
                changed_at=now,
                changed_by=changed_by,
                reason=reason,
            )
            self._record_change(event)

            # Notify callbacks
            self._notify_callbacks(event)

            logger.warning(
                "Feature flag '%s' changed: %s -> %s (by: %s, reason: %s)",
                flag_name,
                old_value,
                enabled,
                changed_by,
                reason,
            )

            return True

    def toggle_flag(
        self,
        flag: str | FeatureFlag,
        changed_by: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Toggle a feature flag.

        Args:
            flag: Feature flag name or enum
            changed_by: Who made the change
            reason: Reason for the change

        Returns:
            New value of the flag
        """
        flag_name = flag.value if isinstance(flag, FeatureFlag) else flag

        with self._lock:
            current = self.is_enabled(flag_name)
            self.set_flag(flag_name, not current, changed_by, reason)
            return not current

    def get_all_flags(self) -> dict[str, dict[str, Any]]:
        """
        Get all feature flags with their states.

        Returns:
            Dictionary of flag names to their states
        """
        with self._lock:
            return {
                name: {
                    "enabled": state.enabled,
                    "last_changed": state.last_changed.isoformat(),
                    "changed_by": state.changed_by,
                    "reason": state.reason,
                }
                for name, state in self._flags.items()
            }

    def get_change_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        Get recent change history.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of change events (most recent first)
        """
        with self._lock:
            events = self._change_history[-limit:][::-1]
            return [
                {
                    "flag": e.flag,
                    "old_value": e.old_value,
                    "new_value": e.new_value,
                    "changed_at": e.changed_at.isoformat(),
                    "changed_by": e.changed_by,
                    "reason": e.reason,
                }
                for e in events
            ]

    def register_callback(
        self, callback: Callable[[FeatureFlagChangeEvent], None]
    ) -> None:
        """
        Register a callback for flag change events.

        Args:
            callback: Function to call when a flag changes
        """
        with self._lock:
            self._callbacks.append(callback)
            logger.debug("Registered feature flag change callback")

    def reset_to_defaults(self, changed_by: Optional[str] = None) -> None:
        """
        Reset all flags to their default values.

        Args:
            changed_by: Who triggered the reset
        """
        with self._lock:
            for flag_name, default_value in self.DEFAULT_FLAGS.items():
                self.set_flag(
                    flag_name,
                    default_value,
                    changed_by=changed_by,
                    reason="Reset to defaults",
                )
            logger.warning("All feature flags reset to defaults by %s", changed_by)

    def enable_all(self, changed_by: Optional[str] = None) -> None:
        """
        Enable all feature flags (use with caution).

        Args:
            changed_by: Who triggered the change
        """
        with self._lock:
            for flag_name in self._flags:
                self.set_flag(
                    flag_name, True, changed_by=changed_by, reason="Enable all flags"
                )
            logger.warning("All feature flags enabled by %s", changed_by)

    def disable_all(self, changed_by: Optional[str] = None) -> None:
        """
        Disable all feature flags (emergency shutdown).

        Args:
            changed_by: Who triggered the change
        """
        with self._lock:
            for flag_name in self._flags:
                self.set_flag(
                    flag_name,
                    False,
                    changed_by=changed_by,
                    reason="Emergency disable all",
                )
            logger.warning("All feature flags DISABLED by %s (emergency)", changed_by)

    def _record_change(self, event: FeatureFlagChangeEvent) -> None:
        """Record a change event in history."""
        self._change_history.append(event)

        # Trim history if too large
        if len(self._change_history) > self._max_history_size:
            self._change_history = self._change_history[-self._max_history_size :]

    def _notify_callbacks(self, event: FeatureFlagChangeEvent) -> None:
        """Notify all registered callbacks of a change."""
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error("Error in feature flag callback: %s", e)


# Global singleton instance
feature_flags_manager = FeatureFlagsManager()


def is_feature_enabled(flag: str | FeatureFlag) -> bool:
    """
    Convenience function to check if a feature is enabled.

    Args:
        flag: Feature flag name or enum

    Returns:
        True if enabled, False otherwise

    Example:
        if is_feature_enabled("kanban_ai_suggest"):
            # AI suggestion logic
            pass

        if is_feature_enabled(FeatureFlag.KANBAN_OBSIDIAN_SYNC):
            # Obsidian sync logic
            pass
    """
    return feature_flags_manager.is_enabled(flag)


def require_feature(flag: str | FeatureFlag) -> Callable:
    """
    Decorator to require a feature flag to be enabled.

    Raises HTTPException 503 if feature is disabled.

    Example:
        @require_feature("kanban_ai_suggest")
        async def suggest_tasks():
            # Only runs if AI suggest is enabled
            pass
    """
    from functools import wraps

    from fastapi import HTTPException

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not is_feature_enabled(flag):
                flag_name = flag.value if isinstance(flag, FeatureFlag) else flag
                raise HTTPException(
                    status_code=503,
                    detail=f"Feature '{flag_name}' is currently disabled",
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Export all public items
__all__ = [
    "FeatureFlag",
    "FeatureFlagState",
    "FeatureFlagChangeEvent",
    "FeatureFlagsManager",
    "feature_flags_manager",
    "is_feature_enabled",
    "require_feature",
]
