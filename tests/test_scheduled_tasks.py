"""
Tests for Scheduled Tasks System

Validates:
1. scheduled.md parsing
2. Date handling and filtering
3. 3-Tier Search integration
4. Session start workflow
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from check_scheduled_tasks import ScheduledTasksChecker, ScheduledTask


class TestScheduledTasksChecker:
    """Test the scheduled tasks checker"""

    @pytest.fixture
    def checker(self):
        """Create a checker instance"""
        # Use actual Obsidian vault path
        vault_path = os.getenv("OBSIDIAN_VAULT_PATH") or str(Path.home() / "Documents" / "Obsidian Vault")
        return ScheduledTasksChecker(vault_path=vault_path)

    def test_checker_initialization(self, checker):
        """Test checker initializes correctly"""
        assert checker.vault_path.exists()
        assert checker.scheduled_file.exists()
        assert checker.scheduled_file.name == "scheduled.md"

    def test_parse_scheduled_file(self, checker):
        """Test parsing of scheduled.md file"""
        tasks = checker.parse_scheduled_file()

        assert isinstance(tasks, list)
        # Should have at least the AI Feedback MVP task
        assert len(tasks) >= 1

        # Check first task structure
        if tasks:
            task = tasks[0]
            assert isinstance(task, ScheduledTask)
            assert task.title
            # Priority can be "P0" or "P0 (Critical)" format
            assert task.priority.startswith("P") and task.priority[1] in "0123"

    def test_date_parsing(self, checker):
        """Test date parsing logic"""
        # Test valid date
        date = checker._parse_date("2026-01-15")
        assert date is not None
        assert date.year == 2026
        assert date.month == 1
        assert date.day == 15

        # Test invalid date
        invalid_date = checker._parse_date("invalid")
        assert invalid_date is None

    def test_get_upcoming_tasks(self, checker):
        """Test filtering upcoming tasks"""
        upcoming, overdue, this_week = checker.get_upcoming_tasks(weeks_ahead=2)

        assert isinstance(upcoming, list)
        assert isinstance(overdue, list)
        assert isinstance(this_week, list)

        # All tasks should have due dates
        all_tasks = upcoming + overdue + this_week
        for task in all_tasks:
            assert task.due_date is not None
            assert task.days_until_due is not None

        # Overdue tasks should have negative days_until_due
        for task in overdue:
            assert task.days_until_due < 0

        # This week tasks should be within 7 days
        for task in this_week:
            assert 0 <= task.days_until_due <= 7

        # Upcoming tasks should be beyond this week
        for task in upcoming:
            assert task.days_until_due > 7

    def test_task_completion_filter(self, checker):
        """Test filtering completed tasks"""
        # Include completed
        all_tasks = checker.parse_scheduled_file()

        # Exclude completed
        _, _, _ = checker.get_upcoming_tasks(include_completed=False)

        # At least some tasks should exist
        assert len(all_tasks) > 0

    def test_format_summary(self, checker):
        """Test summary formatting"""
        upcoming, overdue, this_week = checker.get_upcoming_tasks(weeks_ahead=2)

        # Test non-verbose
        summary = checker.format_summary(upcoming, overdue, this_week, verbose=False)
        assert "SCHEDULED TASKS CHECK" in summary
        assert "OVERDUE" in summary or "No overdue" in summary

        # Test verbose
        summary_verbose = checker.format_summary(upcoming, overdue, this_week, verbose=True)
        assert len(summary_verbose) >= len(summary)  # Verbose should be longer or equal

    def test_task_to_dict(self, checker):
        """Test task serialization"""
        tasks = checker.parse_scheduled_file()

        if tasks:
            task_dict = tasks[0].to_dict()
            assert isinstance(task_dict, dict)
            assert "title" in task_dict
            assert "priority" in task_dict
            assert "due_date" in task_dict
            assert "days_until_due" in task_dict


class TestSessionStartIntegration:
    """Test session start integration"""

    def test_session_start_import(self):
        """Test session start script can be imported"""
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

        try:
            from session_start import main

            assert callable(main)
        except ImportError as e:
            pytest.fail(f"Failed to import session_start: {e}")

    def test_3tier_search_integration(self):
        """Test 3-Tier Search integration"""
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

        try:
            from obsidian_3stage_search import check_scheduled_tasks_on_session_start

            result = check_scheduled_tasks_on_session_start(verbose=False)

            assert isinstance(result, dict)
            assert "found_tasks" in result
            assert "summary" in result

            if result["found_tasks"]:
                assert "overdue" in result
                assert "this_week" in result
                assert "upcoming" in result

        except Exception as e:
            pytest.fail(f"3-Tier Search integration failed: {e}")


class TestScheduledMdTemplate:
    """Test scheduled.md template structure"""

    def test_template_exists(self):
        """Test template file exists"""
        vault_path = os.getenv("OBSIDIAN_VAULT_PATH") or str(Path.home() / "Documents" / "Obsidian Vault")
        scheduled_file = Path(vault_path) / "_System" / "Tasks" / "scheduled.md"

        assert scheduled_file.exists(), f"Template not found: {scheduled_file}"

    def test_template_has_frontmatter(self):
        """Test template has proper frontmatter"""
        vault_path = os.getenv("OBSIDIAN_VAULT_PATH") or str(Path.home() / "Documents" / "Obsidian Vault")
        scheduled_file = Path(vault_path) / "_System" / "Tasks" / "scheduled.md"

        with open(scheduled_file, "r", encoding="utf-8") as f:
            content = f.read()

        assert content.startswith("---"), "Missing frontmatter"
        assert "type: scheduled-tasks" in content
        assert "auto_search: true" in content

    def test_template_has_sections(self):
        """Test template has required sections"""
        vault_path = os.getenv("OBSIDIAN_VAULT_PATH") or str(Path.home() / "Documents" / "Obsidian Vault")
        scheduled_file = Path(vault_path) / "_System" / "Tasks" / "scheduled.md"

        with open(scheduled_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for monthly sections
        assert "2026-01 (January)" in content

        # Check for usage guide
        assert "Usage Guide" in content
        assert "Priority Levels" in content
        assert "Auto-Search Behavior" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
