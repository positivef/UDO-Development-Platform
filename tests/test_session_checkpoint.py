"""
Unit tests for SessionCheckpoint - Session Lifecycle Validation

Tests:
1. Session start validation
2. Periodic checkpoint functionality
3. Session end reporting
4. Statistics tracking
5. Warning and error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import time

# Import the module to test
from scripts.session_checkpoint import SessionCheckpoint, CheckpointResult, get_checkpoint, session_checkpoint


class TestCheckpointResult:
    """Test suite for CheckpointResult dataclass"""

    def test_initialization(self):
        """Test CheckpointResult initializes correctly"""
        result = CheckpointResult(success=True, timestamp=datetime.now())

        assert result.success is True
        assert isinstance(result.timestamp, datetime)
        assert result.checks == {}
        assert result.warnings == []
        assert result.errors == []
        assert result.statistics == {}

    def test_with_data(self):
        """Test CheckpointResult with full data"""
        now = datetime.now()
        result = CheckpointResult(
            success=False,
            timestamp=now,
            checks={"test_check": True},
            warnings=["Warning message"],
            errors=["Error message"],
            statistics={"rate": 0.95},
        )

        assert result.success is False
        assert result.checks["test_check"] is True
        assert len(result.warnings) == 1
        assert len(result.errors) == 1
        assert result.statistics["rate"] == 0.95


class TestSessionCheckpoint:
    """Test suite for SessionCheckpoint class"""

    def setup_method(self):
        """Setup fresh checkpoint for each test"""
        self.checkpoint = SessionCheckpoint()

    def test_initialization(self):
        """Test checkpoint initializes correctly"""
        assert self.checkpoint.session_start_time is None
        assert self.checkpoint.last_checkpoint_time is None
        assert self.checkpoint.checkpoint_interval == timedelta(minutes=30)
        assert len(self.checkpoint.required_components) == 3
        assert self.checkpoint.session_stats["total_errors_encountered"] == 0

    @patch("scripts.session_checkpoint.get_wrapper")
    def test_session_start_success(self, mock_get_wrapper):
        """Test successful session start"""
        # Mock wrapper
        mock_wrapper = Mock()
        mock_wrapper.is_enabled.return_value = True
        mock_wrapper.get_statistics.return_value = {"circuit_breaker_state": "CLOSED"}
        mock_get_wrapper.return_value = mock_wrapper

        result = self.checkpoint.session_start()

        assert result.success is True
        assert self.checkpoint.session_start_time is not None
        assert result.checks.get("auto_3tier_wrapper_enabled") is True
        assert result.checks.get("circuit_breaker_ok") is True
        assert self.checkpoint.session_stats["checkpoints_passed"] == 1

    @patch("scripts.session_checkpoint.get_wrapper")
    def test_session_start_wrapper_disabled(self, mock_get_wrapper):
        """Test session start with wrapper disabled (warning)"""
        mock_wrapper = Mock()
        mock_wrapper.is_enabled.return_value = False
        mock_wrapper.get_statistics.return_value = {"circuit_breaker_state": "CLOSED"}
        mock_get_wrapper.return_value = mock_wrapper

        result = self.checkpoint.session_start()

        # Still succeeds but with warning
        assert result.success is True
        assert result.checks.get("auto_3tier_wrapper_enabled") is False
        assert len(result.warnings) > 0
        assert any("DISABLED" in w for w in result.warnings)

    @patch("scripts.session_checkpoint.get_wrapper")
    def test_session_start_circuit_breaker_open(self, mock_get_wrapper):
        """Test session start with circuit breaker OPEN"""
        mock_wrapper = Mock()
        mock_wrapper.is_enabled.return_value = True
        mock_wrapper.get_statistics.return_value = {"circuit_breaker_state": "OPEN"}
        mock_get_wrapper.return_value = mock_wrapper

        result = self.checkpoint.session_start()

        assert result.success is True  # Not critical, just warning
        assert result.checks.get("circuit_breaker_ok") is False
        assert len(result.warnings) > 0

    @patch("scripts.session_checkpoint.get_wrapper")
    def test_session_start_import_error(self, mock_get_wrapper):
        """Test session start with import error (critical failure)"""
        mock_get_wrapper.side_effect = ImportError("Module not found")

        with pytest.raises(RuntimeError) as exc_info:
            self.checkpoint.session_start()

        assert "Session start failed" in str(exc_info.value)
        assert self.checkpoint.session_stats["checkpoints_failed"] == 1

    @patch("scripts.session_checkpoint.get_wrapper")
    def test_periodic_check_not_due(self, mock_get_wrapper):
        """Test periodic check when not due yet"""
        # Set last checkpoint to 1 minute ago (< 30min interval)
        self.checkpoint.last_checkpoint_time = datetime.now() - timedelta(minutes=1)

        result = self.checkpoint.periodic_check()

        # Should skip and return success
        assert result.success is True
        assert len(result.statistics) == 0  # No stats collected

    @patch("scripts.session_checkpoint.get_wrapper")
    def test_periodic_check_due(self, mock_get_wrapper):
        """Test periodic check when due"""
        # Set last checkpoint to 31 minutes ago (> 30min interval)
        self.checkpoint.last_checkpoint_time = datetime.now() - timedelta(minutes=31)

        mock_wrapper = Mock()
        mock_wrapper.get_statistics.return_value = {
            "automation_rate": 0.92,
            "total_errors": 10,
            "tier1_hits": 7,
            "tier2_auto": 2,
            "tier3_escalations": 1,
            "time_saved_minutes": 45.5,
            "circuit_breaker_state": "CLOSED",
        }
        mock_get_wrapper.return_value = mock_wrapper

        result = self.checkpoint.periodic_check()

        assert result.success is True
        assert result.checks.get("statistics_available") is True
        assert result.statistics["automation_rate"] == 0.92
        assert len(result.warnings) == 0  # Above 90% threshold
        assert self.checkpoint.session_stats["checkpoints_passed"] == 1

    @patch("scripts.session_checkpoint.get_wrapper")
    def test_periodic_check_low_automation_rate(self, mock_get_wrapper):
        """Test periodic check warns on low automation rate"""
        self.checkpoint.last_checkpoint_time = datetime.now() - timedelta(minutes=31)

        mock_wrapper = Mock()
        mock_wrapper.get_statistics.return_value = {
            "automation_rate": 0.75,  # Below 90% threshold
            "total_errors": 20,
            "tier1_hits": 10,
            "tier2_auto": 5,
            "tier3_escalations": 5,
            "circuit_breaker_state": "CLOSED",
        }
        mock_get_wrapper.return_value = mock_wrapper

        result = self.checkpoint.periodic_check()

        assert result.success is True
        assert len(result.warnings) > 0
        assert any("75.0%" in w for w in result.warnings)
        assert self.checkpoint.session_stats["warnings_issued"] > 0

    @patch("scripts.session_checkpoint.get_wrapper")
    def test_session_end_success(self, mock_get_wrapper):
        """Test successful session end"""
        # Setup session
        self.checkpoint.session_start_time = datetime.now() - timedelta(minutes=60)

        mock_wrapper = Mock()
        mock_wrapper.get_statistics.return_value = {
            "automation_rate": 0.95,
            "total_errors": 20,
            "tier1_hits": 14,
            "tier2_auto": 5,
            "tier2_confirmed": 0,
            "tier3_escalations": 1,
            "time_saved_minutes": 120.0,
            "auto_recoveries": 19,
            "failed_recoveries": 0,
            "circuit_breaker_state": "CLOSED",
        }
        mock_get_wrapper.return_value = mock_wrapper

        result = self.checkpoint.session_end()

        assert result.success is True
        assert result.checks.get("automation_rate_ok") is True
        assert result.checks.get("circuit_breaker_ok") is True
        assert len(result.warnings) == 0  # 95% meets target
        assert result.statistics["automation_rate"] == 0.95

    @patch("scripts.session_checkpoint.get_wrapper")
    def test_session_end_no_errors(self, mock_get_wrapper):
        """Test session end with no errors encountered (warning)"""
        self.checkpoint.session_start_time = datetime.now() - timedelta(minutes=30)

        mock_wrapper = Mock()
        mock_wrapper.get_statistics.return_value = {
            "automation_rate": 0.0,
            "total_errors": 0,  # No errors encountered
            "tier1_hits": 0,
            "tier2_auto": 0,
            "tier3_escalations": 0,
            "circuit_breaker_state": "CLOSED",
        }
        mock_get_wrapper.return_value = mock_wrapper

        result = self.checkpoint.session_end()

        assert result.success is True
        assert len(result.warnings) > 0
        assert any("No errors encountered" in w for w in result.warnings)

    @patch("scripts.session_checkpoint.get_wrapper")
    def test_session_end_low_automation(self, mock_get_wrapper):
        """Test session end with low automation rate"""
        self.checkpoint.session_start_time = datetime.now() - timedelta(minutes=60)

        mock_wrapper = Mock()
        mock_wrapper.get_statistics.return_value = {
            "automation_rate": 0.65,  # Below 90% target
            "total_errors": 20,
            "tier1_hits": 8,
            "tier2_auto": 5,
            "tier3_escalations": 7,  # Too many Tier 3
            "failed_recoveries": 2,
            "circuit_breaker_state": "CLOSED",
        }
        mock_get_wrapper.return_value = mock_wrapper

        result = self.checkpoint.session_end()

        assert result.success is True
        assert len(result.warnings) > 0
        assert any("65.0%" in w and "below 90%" in w for w in result.warnings)
        assert self.checkpoint.session_stats["warnings_issued"] > 0

    def test_get_session_stats(self):
        """Test getting session statistics"""
        self.checkpoint.session_start_time = datetime.now()
        self.checkpoint.session_stats["warnings_issued"] = 3

        stats = self.checkpoint.get_session_stats()

        assert "session_start" in stats
        assert stats["warnings_issued"] == 3
        assert "last_checkpoint" in stats


class TestGlobalFunctions:
    """Test suite for module-level singleton functions"""

    def test_get_checkpoint_singleton(self):
        """Test get_checkpoint returns singleton"""
        checkpoint1 = get_checkpoint()
        checkpoint2 = get_checkpoint()

        assert checkpoint1 is checkpoint2

    def test_session_checkpoint_singleton(self):
        """Test session_checkpoint is available"""
        assert session_checkpoint is not None
        assert isinstance(session_checkpoint, SessionCheckpoint)


@pytest.fixture
def mock_wrapper_stats():
    """Fixture for mocked wrapper statistics"""
    return {
        "automation_rate": 0.93,
        "total_errors": 15,
        "tier1_hits": 10,
        "tier2_auto": 4,
        "tier2_confirmed": 0,
        "tier3_escalations": 1,
        "time_saved_minutes": 75.0,
        "auto_recoveries": 14,
        "failed_recoveries": 0,
        "circuit_breaker_state": "CLOSED",
    }


def test_integration_full_session(mock_wrapper_stats):
    """Integration test showing full session lifecycle"""
    checkpoint = SessionCheckpoint()

    with patch("scripts.session_checkpoint.get_wrapper") as mock_get_wrapper:
        mock_wrapper = Mock()
        mock_wrapper.is_enabled.return_value = True
        mock_wrapper.get_statistics.return_value = mock_wrapper_stats
        mock_get_wrapper.return_value = mock_wrapper

        # 1. Session start
        start_result = checkpoint.session_start()
        assert start_result.success is True

        # 2. Simulate work (force checkpoint to be due)
        checkpoint.last_checkpoint_time = datetime.now() - timedelta(minutes=31)

        # 3. Periodic check
        periodic_result = checkpoint.periodic_check()
        assert periodic_result.success is True
        assert periodic_result.statistics["automation_rate"] == 0.93

        # 4. Session end
        end_result = checkpoint.session_end()
        assert end_result.success is True
        assert end_result.checks.get("automation_rate_ok") is True

        # 5. Verify session stats
        stats = checkpoint.get_session_stats()
        assert stats["checkpoints_passed"] >= 3  # start, periodic, end


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
