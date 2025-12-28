"""
Unit tests for Auto3TierWrapper - 3-Tier Automated Resolution System

Tests:
1. Error detection in various formats
2. Wrapper decoration and error handling
3. Circuit breaker functionality
4. Statistics tracking
5. Integration with UnifiedErrorResolver (mocked)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the module to test
from scripts.auto_3tier_wrapper import (
    Auto3TierWrapper,
    auto_3tier,
    get_wrapper,
    get_statistics,
    reset_statistics,
    enable_auto_resolution,
    disable_auto_resolution,
)


class TestAuto3TierWrapper:
    """Test suite for Auto3TierWrapper class"""

    def setup_method(self):
        """Setup fresh wrapper for each test"""
        self.wrapper = Auto3TierWrapper()
        self.wrapper.reset_statistics()

    def test_initialization(self):
        """Test wrapper initializes correctly"""
        assert self.wrapper.enabled is True
        assert self.wrapper.statistics["total_calls"] == 0
        assert self.wrapper.circuit_breaker["state"] == "CLOSED"

    def test_error_detection_exception(self):
        """Test error detection with Exception objects"""
        error = ValueError("Test error")
        assert self.wrapper._is_error(error) is True

    def test_error_detection_dict_with_error(self):
        """Test error detection with dict containing 'error' field"""
        result = {"error": "Test error message"}
        assert self.wrapper._is_error(result) is True

    def test_error_detection_dict_with_exit_code(self):
        """Test error detection with dict containing non-zero exit_code"""
        result = {"exit_code": 1, "stderr": "Error message"}
        assert self.wrapper._is_error(result) is True

    def test_error_detection_dict_success_false(self):
        """Test error detection with dict containing success: False"""
        result = {"success": False, "message": "Operation failed"}
        assert self.wrapper._is_error(result) is True

    def test_error_detection_success_result(self):
        """Test error detection with successful result"""
        result = {"success": True, "data": "Result data"}
        assert self.wrapper._is_error(result) is False

        result2 = {"exit_code": 0, "stdout": "Success"}
        assert self.wrapper._is_error(result2) is False

    def test_extract_error_message_from_exception(self):
        """Test extracting error message from Exception"""
        error = ValueError("Test error message")
        msg = self.wrapper._extract_error_message(error)
        assert "ValueError" in msg
        assert "Test error message" in msg

    def test_extract_error_message_from_dict(self):
        """Test extracting error message from dict"""
        result = {"stderr": "Command failed"}
        msg = self.wrapper._extract_error_message(result)
        assert "Command failed" in msg

    def test_wrap_tool_successful_call(self):
        """Test wrapping a tool that succeeds"""

        @self.wrapper.wrap_tool
        def successful_tool():
            return {"success": True, "data": "test"}

        result = successful_tool()

        assert result["success"] is True
        assert self.wrapper.statistics["total_calls"] == 1
        assert self.wrapper.statistics["total_errors"] == 0

    @patch("scripts.unified_error_resolver.UnifiedErrorResolver")
    def test_wrap_tool_error_no_resolver(self, mock_resolver_class):
        """Test wrapping a tool that errors when resolver unavailable"""
        # Make import fail to simulate resolver unavailable
        mock_resolver_class.side_effect = ImportError("UnifiedErrorResolver not available")

        # Force resolver property to try initialization
        _ = self.wrapper.resolver  # Will fail and set _resolver to None

        @self.wrapper.wrap_tool
        def failing_tool():
            return {"error": "Test error", "exit_code": 1}

        result = failing_tool()

        # Should return error result as-is (no resolution attempted)
        assert result["error"] == "Test error"
        assert self.wrapper.statistics["total_calls"] == 1
        assert self.wrapper.statistics["total_errors"] == 1

    @patch("scripts.unified_error_resolver.UnifiedErrorResolver")
    def test_wrap_tool_tier1_hit(self, mock_resolver_class):
        """Test Tier 1 (Obsidian) resolution"""
        # Mock resolver
        mock_resolver = Mock()
        mock_resolver.resolve_error.return_value = "pip install pandas"
        mock_resolver.get_statistics.return_value = {"tier1": 1, "tier2_auto": 0}
        mock_resolver_class.return_value = mock_resolver

        self.wrapper._resolver = mock_resolver

        # Create a tool that fails then succeeds
        call_count = [0]

        @self.wrapper.wrap_tool
        def flaky_tool():
            call_count[0] += 1
            if call_count[0] == 1:
                return {"error": "ModuleNotFoundError: pandas", "exit_code": 1}
            else:
                return {"success": True, "data": "Fixed!"}

        # This will trigger error on first call, then auto-retry
        # BUT since we can't actually apply the solution in tests,
        # we need to mock _apply_and_retry
        with patch.object(self.wrapper, "_apply_and_retry") as mock_apply:
            mock_apply.return_value = {"success": True, "data": "Fixed!"}

            result = flaky_tool()

            assert self.wrapper.statistics["total_errors"] == 1
            assert self.wrapper.statistics["tier1_hits"] == 1
            mock_resolver.resolve_error.assert_called_once()

    @patch("scripts.unified_error_resolver.UnifiedErrorResolver")
    def test_wrap_tool_tier2_auto_hit(self, mock_resolver_class):
        """Test Tier 2 (Context7 AUTO) resolution"""
        mock_resolver = Mock()
        mock_resolver.resolve_error.return_value = "chmod +r file.py"
        mock_resolver.get_statistics.return_value = {"tier1": 0, "tier2_auto": 1}
        mock_resolver_class.return_value = mock_resolver

        self.wrapper._resolver = mock_resolver

        @self.wrapper.wrap_tool
        def permission_tool():
            return {"error": "PermissionError", "exit_code": 1}

        with patch.object(self.wrapper, "_apply_and_retry") as mock_apply:
            mock_apply.return_value = {"success": True}

            result = permission_tool()

            assert self.wrapper.statistics["tier2_auto"] == 1
            assert self.wrapper.statistics["tier2_hits"] == 1

    @patch("scripts.unified_error_resolver.UnifiedErrorResolver")
    def test_wrap_tool_tier3_escalation(self, mock_resolver_class):
        """Test Tier 3 (User) escalation when no solution found"""
        mock_resolver = Mock()
        mock_resolver.resolve_error.return_value = None  # No solution
        mock_resolver_class.return_value = mock_resolver

        self.wrapper._resolver = mock_resolver

        @self.wrapper.wrap_tool
        def custom_error_tool():
            return {"error": "CustomBusinessError: Unknown", "exit_code": 1}

        result = custom_error_tool()

        # Should return original error
        assert result["error"] == "CustomBusinessError: Unknown"
        assert self.wrapper.statistics["tier3_escalations"] == 1

    def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after consecutive failures"""
        # Manually trigger failures
        for _ in range(3):
            self.wrapper._update_circuit_breaker(failed=True)

        assert self.wrapper.circuit_breaker["state"] == "OPEN"
        assert self.wrapper.circuit_breaker["consecutive_failures"] == 3

    def test_circuit_breaker_closes_on_success(self):
        """Test circuit breaker closes on successful recovery"""
        # Open circuit breaker
        self.wrapper.circuit_breaker["state"] = "HALF_OPEN"
        self.wrapper.circuit_breaker["consecutive_failures"] = 1

        # Success should close it
        self.wrapper._update_circuit_breaker(failed=False)

        assert self.wrapper.circuit_breaker["state"] == "CLOSED"
        assert self.wrapper.circuit_breaker["consecutive_failures"] == 0

    def test_get_statistics(self):
        """Test statistics retrieval"""
        self.wrapper.statistics["total_calls"] = 10
        self.wrapper.statistics["total_errors"] = 5
        self.wrapper.statistics["tier1_hits"] = 3
        self.wrapper.statistics["tier2_auto"] = 1

        stats = self.wrapper.get_statistics()

        assert stats["total_calls"] == 10
        assert stats["total_errors"] == 5
        assert stats["automation_rate"] == 0.8  # (3 + 1) / 5
        assert "circuit_breaker_state" in stats

    def test_enable_disable(self):
        """Test enabling and disabling wrapper"""
        assert self.wrapper.enabled is True

        self.wrapper.disable()
        assert self.wrapper.enabled is False

        self.wrapper.enable()
        assert self.wrapper.enabled is True

    def test_decorator_shorthand(self):
        """Test @auto_3tier decorator shorthand"""
        # Reset global instance
        import scripts.auto_3tier_wrapper

        scripts.auto_3tier_wrapper._wrapper_instance = None

        @auto_3tier
        def decorated_tool():
            return {"success": True}

        result = decorated_tool()
        assert result["success"] is True

        # Check global statistics
        stats = get_statistics()
        assert stats["total_calls"] >= 1


class TestGlobalFunctions:
    """Test suite for module-level convenience functions"""

    def test_get_wrapper_singleton(self):
        """Test get_wrapper returns singleton"""
        wrapper1 = get_wrapper()
        wrapper2 = get_wrapper()

        assert wrapper1 is wrapper2

    def test_reset_statistics(self):
        """Test global statistics reset"""
        wrapper = get_wrapper()
        wrapper.statistics["total_calls"] = 100

        reset_statistics()

        assert wrapper.statistics["total_calls"] == 0

    def test_enable_disable_auto_resolution(self):
        """Test global enable/disable functions"""
        wrapper = get_wrapper()

        disable_auto_resolution()
        assert wrapper.enabled is False

        enable_auto_resolution()
        assert wrapper.enabled is True


@pytest.fixture
def mock_resolver():
    """Fixture for mocked UnifiedErrorResolver"""
    with patch("scripts.unified_error_resolver.UnifiedErrorResolver") as mock:
        resolver_instance = Mock()
        resolver_instance.resolve_error.return_value = "test solution"
        resolver_instance.get_statistics.return_value = {"tier1": 1}
        mock.return_value = resolver_instance
        yield resolver_instance


def test_integration_example(mock_resolver):
    """Integration test showing typical usage"""
    wrapper = Auto3TierWrapper()
    wrapper._resolver = mock_resolver

    @wrapper.wrap_tool
    def bash_command(cmd: str):
        """Simulate bash command that might fail"""
        if "nonexistent" in cmd:
            return {"exit_code": 1, "stderr": "Command not found"}
        return {"exit_code": 0, "stdout": "Success"}

    # Successful command
    result = bash_command("echo hello")
    assert result["exit_code"] == 0

    # Failing command (will trigger 3-Tier resolution)
    with patch.object(wrapper, "_apply_and_retry") as mock_apply:
        mock_apply.return_value = {"exit_code": 0, "stdout": "Fixed"}

        result = bash_command("nonexistent-command")
        # Resolver would be called
        mock_resolver.resolve_error.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
