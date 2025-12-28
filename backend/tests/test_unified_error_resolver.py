"""
Tests for UnifiedErrorResolver - 3-Tier Error Resolution System

Validates:
1. Knowledge reuse tracking (Tier 1, 2, 3 statistics)
2. Pattern-based solution matching (HIGH confidence auto-apply)
3. Confidence scoring (≥95% auto, 70-95% confirm, <70% escalate)
4. Statistics calculation (automation rate, knowledge reuse rate)

Author: VibeCoding Team
Date: 2025-12-07 (Week 0 Day 2)
"""

import tempfile
from pathlib import Path

import pytest

from backend.app.services.unified_error_resolver import (ErrorContext,
                                                         ResolutionResult,
                                                         UnifiedErrorResolver)


class TestKnowledgeReuseTracking:
    """Test Tier 1 (Obsidian) knowledge reuse tracking"""

    def test_statistics_initialization(self):
        """Resolver initializes with zero statistics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            stats = resolver.get_statistics()
            assert stats["total"] == 0
            assert stats["tier1"] == 0
            assert stats["tier2"] == 0
            assert stats["tier3"] == 0
            assert stats["automation_rate"] == 0.0
            assert stats["knowledge_reuse_rate"] == 0.0

    def test_knowledge_reuse_rate_calculation(self):
        """Knowledge reuse rate = (tier1_hits / total_attempts) × 100%"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            # Simulate 10 attempts with 7 Tier 1 hits
            resolver.stats["total_attempts"] = 10
            resolver.stats["tier1_hits"] = 7

            rate = resolver.get_knowledge_reuse_rate()
            assert rate == 70.0  # 7/10 = 70%

    def test_automation_rate_calculation(self):
        """Automation rate = (tier1 + tier2_auto) / total"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            # Simulate: 10 total, 5 Tier 1, 3 Tier 2 auto, 2 Tier 3
            resolver.stats["total_attempts"] = 10
            resolver.stats["tier1_hits"] = 5
            resolver.stats["tier2_auto_applied"] = 3
            resolver.stats["tier3_escalations"] = 2

            stats = resolver.get_statistics()
            assert stats["automation_rate"] == 0.8  # (5+3)/10 = 80%


class TestPatternBasedSolutions:
    """Test Tier 2 pattern-based solution matching"""

    def test_module_not_found_high_confidence(self):
        """ModuleNotFoundError -> pip install (95% confidence)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            result = resolver.resolve_error(
                error_message="ModuleNotFoundError: No module named 'pandas'",
                context={"tool": "Python", "script": "analyzer.py"},
            )

            # Should return Tier 2 solution (Obsidian not integrated yet)
            assert result.tier == 2
            assert result.solution == "pip install pandas"
            assert result.confidence >= 0.95  # HIGH confidence
            assert result.source == "context7"

    def test_permission_denied_write_high_confidence(self):
        """PermissionError (write) -> chmod +w (95% confidence)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            result = resolver.resolve_error(
                error_message="PermissionError: [Errno 13] Permission denied: 'scripts/deploy.sh'",
                context={"tool": "Write", "file": "scripts/deploy.sh"},
            )

            assert result.tier == 2
            assert result.solution == "chmod +w scripts/deploy.sh"
            assert result.confidence >= 0.95

    def test_permission_denied_execute_high_confidence(self):
        """PermissionError (execute) -> chmod +x (95% confidence)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            result = resolver.resolve_error(
                error_message="Permission denied when executing 'tests/smoke_test.sh'",
                context={"tool": "Bash", "command": "bash tests/smoke_test.sh"},
            )

            assert result.tier == 2
            assert "chmod +x" in result.solution
            assert result.confidence >= 0.95

    def test_file_not_found_medium_confidence(self):
        """FileNotFoundError -> None (70% confidence, user confirmation)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            result = resolver.resolve_error(
                error_message="FileNotFoundError: [Errno 2] No such file or directory: 'config.yaml'",
                context={"tool": "Read"},
            )

            # MEDIUM confidence patterns return None (user confirmation needed)
            assert result.solution is None
            assert result.tier == 3  # Escalates to user

    def test_unknown_error_escalates(self):
        """Unknown errors escalate to Tier 3 (user)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            result = resolver.resolve_error(
                error_message="CustomBusinessLogicError: Payment method not supported",
                context={"tool": "Python"},
            )

            assert result.tier == 3
            assert result.solution is None
            assert result.source == "none"


class TestConfidenceScoring:
    """Test confidence-based decision making"""

    def test_high_confidence_auto_apply(self):
        """≥95% confidence -> auto-apply (Tier 2)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            result = resolver.resolve_error(
                error_message="ModuleNotFoundError: No module named 'requests'",
                context={"tool": "Python"},
            )

            # HIGH confidence -> auto-applied
            assert result.confidence >= 0.95
            stats = resolver.get_statistics()
            assert stats["tier2_auto"] == 1  # Auto-applied

    def test_medium_confidence_user_confirmation(self):
        """70-95% confidence -> return for user confirmation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            # File not found is MEDIUM confidence (70%)
            result = resolver.resolve_error(
                error_message="No such file or directory: 'missing.txt'",
                context={"tool": "Read"},
            )

            # MEDIUM confidence -> not auto-applied, escalates
            assert result.tier == 3  # No auto-apply
            stats = resolver.get_statistics()
            assert stats["tier2_auto"] == 0

    def test_low_confidence_escalates(self):
        """<70% confidence -> escalate to user (Tier 3)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            result = resolver.resolve_error(
                error_message="UnknownError: Something went wrong",
                context={"tool": "Unknown"},
            )

            assert result.tier == 3
            assert result.confidence == 0.0


class TestStatisticsPersistence:
    """Test statistics saving and loading"""

    def test_save_and_load_statistics(self):
        """Statistics persist across resolver instances"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"

            # Instance 1: Record some resolutions
            resolver1 = UnifiedErrorResolver(stats_file=stats_file)
            resolver1.resolve_error("ModuleNotFoundError: No module named 'pandas'")
            resolver1.resolve_error("ModuleNotFoundError: No module named 'numpy'")

            stats1 = resolver1.get_statistics()
            assert stats1["total"] == 2

            # Instance 2: Load from same file
            resolver2 = UnifiedErrorResolver(stats_file=stats_file)
            stats2 = resolver2.get_statistics()

            # Should have same statistics
            assert stats2["total"] == 2
            assert stats2["tier2_auto"] == 2

    def test_resolution_history_tracking(self):
        """Resolution history tracks last 100 resolutions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            for i in range(105):
                resolver.resolve_error(
                    error_message=f"ModuleNotFoundError: No module named 'lib{i}'",
                    context={"tool": "Python"},
                )

            # Should keep only last 100
            assert len(resolver.stats["resolution_history"]) == 100
            assert resolver.stats["total_attempts"] == 105


class TestUserSolutionSaving:
    """Test user solution saving for future Tier 1 hits"""

    def test_save_user_solution(self):
        """User solutions are recorded with 100% confidence"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            resolver.save_user_solution(
                error_message="CustomError: API key missing",
                user_solution="export API_KEY=your_key_here",
                context={"tool": "Bash", "command": "run_api.sh"},
            )

            # Should be recorded in history
            assert len(resolver.stats["resolution_history"]) == 1
            history = resolver.stats["resolution_history"][0]
            assert history["tier"] == 3
            assert history["source"] == "user"
            assert history["confidence"] == 1.0


class TestErrorKeywordExtraction:
    """Test keyword extraction from error messages"""

    def test_extract_error_type(self):
        """Extracts error type (e.g., ModuleNotFoundError)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            keywords = resolver._extract_error_keywords(
                "ModuleNotFoundError: No module named 'pandas'"
            )
            assert "ModuleNotFoundError" in keywords

    def test_extract_module_name(self):
        """Extracts module name from ModuleNotFoundError"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            keywords = resolver._extract_error_keywords("No module named 'requests'")
            assert "requests" in keywords

    def test_extract_error_code(self):
        """Extracts HTTP error codes (401, 404, 500)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            keywords = resolver._extract_error_keywords("HTTPError: 404 Not Found")
            assert "404" in keywords

    def test_extract_file_path(self):
        """Extracts file names from error messages"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            keywords = resolver._extract_error_keywords("No such file: 'config.yaml'")
            assert "config.yaml" in keywords


class TestRealWorldScenarios:
    """Test real-world error resolution scenarios"""

    def test_pandas_import_error(self):
        """Real scenario: Missing pandas dependency"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            result = resolver.resolve_error(
                error_message="""
                Traceback (most recent call last):
                  File "analysis.py", line 3, in <module>
                    import pandas as pd
                ModuleNotFoundError: No module named 'pandas'
                """,
                context={"tool": "Python", "file": "analysis.py"},
            )

            assert result.solution == "pip install pandas"
            assert result.confidence >= 0.95
            assert resolver.get_statistics()["tier2_auto"] == 1

    def test_permission_error_chmod(self):
        """Real scenario: Permission denied when running script"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            result = resolver.resolve_error(
                error_message="bash: ./deploy.sh: Permission denied",
                context={"tool": "Bash", "command": "./deploy.sh"},
            )

            assert (
                result.solution is not None
            ), "Solution should not be None for permission denied"
            assert "chmod +x" in result.solution
            assert result.confidence >= 0.95

    def test_accumulate_statistics(self):
        """Real scenario: Multiple errors accumulate statistics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            # 5 pandas errors (same error -> should reuse knowledge if Tier 1 worked)
            for _ in range(5):
                resolver.resolve_error("ModuleNotFoundError: No module named 'pandas'")

            # 3 numpy errors
            for _ in range(3):
                resolver.resolve_error("ModuleNotFoundError: No module named 'numpy'")

            # 2 permission errors
            for _ in range(2):
                resolver.resolve_error(
                    "Permission denied: 'script.sh'", context={"tool": "Bash"}
                )

            stats = resolver.get_statistics()
            assert stats["total"] == 10
            assert stats["tier2_auto"] == 10  # All HIGH confidence
            assert stats["automation_rate"] == 1.0  # 100% automated


class TestResetStatistics:
    """Test statistics reset functionality"""

    def test_reset_clears_all_stats(self):
        """Reset clears all statistics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "test_stats.json"
            resolver = UnifiedErrorResolver(stats_file=stats_file)

            # Record some data
            resolver.resolve_error("ModuleNotFoundError: No module named 'test'")
            assert resolver.get_statistics()["total"] > 0

            # Reset
            resolver.reset_statistics()

            # Should be zero
            stats = resolver.get_statistics()
            assert stats["total"] == 0
            assert stats["tier1"] == 0
            assert stats["tier2"] == 0
            assert len(resolver.stats["resolution_history"]) == 0


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
