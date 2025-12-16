"""
Tests for Feature Flags Module

Tests the Tier 1 rollback mechanism for Kanban-UDO integration.
Covers feature flag management, admin API, and thread safety.

Author: Claude Code
Date: 2025-12-16
"""

import os
import pytest
from datetime import datetime
from unittest.mock import patch
from fastapi.testclient import TestClient

# Set test admin key before imports
os.environ["ADMIN_KEY"] = "test-admin-key"

from backend.app.core.feature_flags import (
    FeatureFlag,
    FeatureFlagsManager,
    feature_flags_manager,
    is_feature_enabled,
    require_feature,
)
from backend.main import app


# Test client for API tests
client = TestClient(app)

# Admin key header
ADMIN_HEADERS = {"X-Admin-Key": "test-admin-key"}
INVALID_ADMIN_HEADERS = {"X-Admin-Key": "wrong-key"}


class TestFeatureFlagsManager:
    """Tests for the FeatureFlagsManager class."""

    @pytest.fixture(autouse=True)
    def reset_flags(self):
        """Reset feature flags before each test."""
        feature_flags_manager.reset_to_defaults(changed_by="test")
        yield
        feature_flags_manager.reset_to_defaults(changed_by="test")

    def test_default_flags_initialized(self):
        """Test that default flags are properly initialized."""
        flags = feature_flags_manager.get_all_flags()

        # Core functionality should be enabled
        assert flags["kanban_board"]["enabled"] is True
        assert flags["kanban_archive"]["enabled"] is True
        assert flags["kanban_dependencies"]["enabled"] is True

        # Optional features should be disabled by default
        assert flags["kanban_ai_suggest"]["enabled"] is False
        assert flags["kanban_multi_project"]["enabled"] is False
        assert flags["kanban_obsidian_sync"]["enabled"] is False

    def test_is_feature_enabled(self):
        """Test is_feature_enabled function."""
        # By string
        assert is_feature_enabled("kanban_board") is True
        assert is_feature_enabled("kanban_ai_suggest") is False

        # By enum
        assert is_feature_enabled(FeatureFlag.KANBAN_BOARD) is True
        assert is_feature_enabled(FeatureFlag.KANBAN_AI_SUGGEST) is False

    def test_set_flag(self):
        """Test setting a feature flag."""
        # Enable a disabled flag
        result = feature_flags_manager.set_flag(
            "kanban_ai_suggest",
            enabled=True,
            changed_by="test",
            reason="Testing"
        )

        assert result is True
        assert is_feature_enabled("kanban_ai_suggest") is True

        # Disable it again
        result = feature_flags_manager.set_flag(
            "kanban_ai_suggest",
            enabled=False,
            changed_by="test",
            reason="Reverting"
        )

        assert result is True
        assert is_feature_enabled("kanban_ai_suggest") is False

    def test_set_unknown_flag_returns_false(self):
        """Test setting an unknown flag returns False."""
        result = feature_flags_manager.set_flag(
            "nonexistent_flag",
            enabled=True,
            changed_by="test"
        )
        assert result is False

    def test_toggle_flag(self):
        """Test toggling a feature flag."""
        initial = is_feature_enabled("kanban_ai_suggest")

        new_value = feature_flags_manager.toggle_flag(
            "kanban_ai_suggest",
            changed_by="test"
        )

        assert new_value == (not initial)
        assert is_feature_enabled("kanban_ai_suggest") == new_value

    def test_change_history(self):
        """Test that change history is recorded."""
        # Make some changes
        feature_flags_manager.set_flag("kanban_ai_suggest", True, "user1", "Enable AI")
        feature_flags_manager.set_flag("kanban_ai_suggest", False, "user2", "Disable AI")

        history = feature_flags_manager.get_change_history(limit=5)

        assert len(history) >= 2
        # Most recent first
        assert history[0]["flag"] == "kanban_ai_suggest"
        assert history[0]["new_value"] is False
        assert history[0]["changed_by"] == "user2"

    def test_reset_to_defaults(self):
        """Test resetting all flags to defaults."""
        # Change some flags
        feature_flags_manager.set_flag("kanban_ai_suggest", True, "test")
        feature_flags_manager.set_flag("kanban_board", False, "test")

        # Reset
        feature_flags_manager.reset_to_defaults(changed_by="admin")

        # Verify defaults restored
        assert is_feature_enabled("kanban_ai_suggest") is False
        assert is_feature_enabled("kanban_board") is True

    def test_disable_all(self):
        """Test emergency disable all flags."""
        feature_flags_manager.disable_all(changed_by="emergency")

        flags = feature_flags_manager.get_all_flags()
        for flag_name, state in flags.items():
            assert state["enabled"] is False, f"Flag {flag_name} should be disabled"

    def test_enable_all(self):
        """Test enabling all flags."""
        feature_flags_manager.enable_all(changed_by="test")

        flags = feature_flags_manager.get_all_flags()
        for flag_name, state in flags.items():
            assert state["enabled"] is True, f"Flag {flag_name} should be enabled"

    def test_callback_notification(self):
        """Test that callbacks are notified on flag changes."""
        callback_events = []

        def test_callback(event):
            callback_events.append(event)

        feature_flags_manager.register_callback(test_callback)
        feature_flags_manager.set_flag("kanban_ai_suggest", True, "test")

        assert len(callback_events) == 1
        assert callback_events[0].flag == "kanban_ai_suggest"
        assert callback_events[0].new_value is True

    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        # Set environment variable
        with patch.dict(os.environ, {"FEATURE_KANBAN_AI_SUGGEST": "true"}):
            # Create new manager to pick up env var
            manager = FeatureFlagsManager()
            assert manager.is_enabled("kanban_ai_suggest") is True


class TestAdminAPIEndpoints:
    """Tests for Admin API endpoints."""

    @pytest.fixture(autouse=True)
    def reset_flags(self):
        """Reset feature flags before each test."""
        feature_flags_manager.reset_to_defaults(changed_by="test")
        yield
        feature_flags_manager.reset_to_defaults(changed_by="test")

    def test_get_all_flags_requires_auth(self):
        """Test that getting flags requires admin auth."""
        response = client.get("/api/admin/feature-flags")
        assert response.status_code == 422  # Missing header

        response = client.get("/api/admin/feature-flags", headers=INVALID_ADMIN_HEADERS)
        assert response.status_code == 403

    def test_get_all_flags(self):
        """Test getting all feature flags."""
        response = client.get("/api/admin/feature-flags", headers=ADMIN_HEADERS)

        assert response.status_code == 200
        data = response.json()
        assert "flags" in data
        assert "total" in data
        assert data["total"] == 8  # 8 default flags

    def test_get_single_flag(self):
        """Test getting a single feature flag."""
        response = client.get(
            "/api/admin/feature-flags/kanban_board",
            headers=ADMIN_HEADERS
        )

        assert response.status_code == 200
        data = response.json()
        assert data["flag"] == "kanban_board"
        assert data["enabled"] is True

    def test_get_unknown_flag_returns_404(self):
        """Test getting an unknown flag returns 404."""
        response = client.get(
            "/api/admin/feature-flags/nonexistent",
            headers=ADMIN_HEADERS
        )

        assert response.status_code == 404

    def test_toggle_flag(self):
        """Test toggling a feature flag via API."""
        # Enable a disabled flag
        response = client.post(
            "/api/admin/feature-flags/kanban_ai_suggest",
            headers=ADMIN_HEADERS,
            json={"enabled": True, "reason": "Testing API toggle"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["flag"] == "kanban_ai_suggest"
        assert data["enabled"] is True

        # Verify it's actually changed
        assert is_feature_enabled("kanban_ai_suggest") is True

    def test_toggle_unknown_flag_returns_404(self):
        """Test toggling an unknown flag returns 404."""
        response = client.post(
            "/api/admin/feature-flags/nonexistent",
            headers=ADMIN_HEADERS,
            json={"enabled": True}
        )

        assert response.status_code == 404

    def test_reset_all_flags(self):
        """Test resetting all flags via API."""
        # Change some flags first
        feature_flags_manager.set_flag("kanban_ai_suggest", True, "test")

        response = client.post(
            "/api/admin/feature-flags/reset",
            headers=ADMIN_HEADERS
        )

        assert response.status_code == 200
        data = response.json()

        # Verify kanban_ai_suggest is back to default (False)
        assert data["flags"]["kanban_ai_suggest"]["enabled"] is False

    def test_emergency_disable_all(self):
        """Test emergency disable all via API."""
        response = client.post(
            "/api/admin/feature-flags/disable-all",
            headers=ADMIN_HEADERS
        )

        assert response.status_code == 200
        data = response.json()

        # All flags should be disabled
        for flag_name, state in data["flags"].items():
            assert state["enabled"] is False

    def test_get_change_history(self):
        """Test getting change history via API."""
        # Make some changes
        feature_flags_manager.set_flag("kanban_ai_suggest", True, "user1")

        response = client.get(
            "/api/admin/feature-flags/history",
            headers=ADMIN_HEADERS
        )

        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert len(data["history"]) > 0

    def test_health_endpoint_no_auth_required(self):
        """Test that health endpoint doesn't require auth."""
        response = client.get("/api/admin/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["feature_flags_active"] is True


class TestRequireFeatureDecorator:
    """Tests for the require_feature decorator."""

    @pytest.fixture(autouse=True)
    def reset_flags(self):
        """Reset feature flags before each test."""
        feature_flags_manager.reset_to_defaults(changed_by="test")
        yield
        feature_flags_manager.reset_to_defaults(changed_by="test")

    def test_decorator_allows_enabled_feature(self):
        """Test that decorator allows request when feature is enabled."""
        # kanban_board is enabled by default
        @require_feature("kanban_board")
        async def test_endpoint():
            return {"status": "ok"}

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(test_endpoint())
        assert result == {"status": "ok"}

    def test_decorator_blocks_disabled_feature(self):
        """Test that decorator blocks request when feature is disabled."""
        from fastapi import HTTPException

        # kanban_ai_suggest is disabled by default
        @require_feature("kanban_ai_suggest")
        async def test_endpoint():
            return {"status": "ok"}

        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.get_event_loop().run_until_complete(test_endpoint())

        assert exc_info.value.status_code == 503
        assert "kanban_ai_suggest" in exc_info.value.detail


class TestThreadSafety:
    """Tests for thread safety of feature flags."""

    @pytest.fixture(autouse=True)
    def reset_flags(self):
        """Reset feature flags before each test."""
        feature_flags_manager.reset_to_defaults(changed_by="test")
        yield
        feature_flags_manager.reset_to_defaults(changed_by="test")

    def test_concurrent_flag_operations(self):
        """Test that concurrent flag operations are thread-safe."""
        import threading
        import random

        errors = []
        iterations = 100

        def toggle_flag():
            try:
                for _ in range(iterations):
                    flag = random.choice(list(FeatureFlag))
                    feature_flags_manager.toggle_flag(flag, changed_by="thread")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=toggle_flag) for _ in range(10)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread errors: {errors}"

    def test_concurrent_read_write(self):
        """Test concurrent read and write operations."""
        import threading

        errors = []
        iterations = 100

        def reader():
            try:
                for _ in range(iterations):
                    is_feature_enabled("kanban_board")
                    feature_flags_manager.get_all_flags()
            except Exception as e:
                errors.append(e)

        def writer():
            try:
                for _ in range(iterations):
                    feature_flags_manager.toggle_flag("kanban_ai_suggest", changed_by="writer")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=reader) for _ in range(5)]
        threads += [threading.Thread(target=writer) for _ in range(3)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread errors: {errors}"
