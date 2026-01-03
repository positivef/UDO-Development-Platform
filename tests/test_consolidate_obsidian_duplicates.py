#!/usr/bin/env python3
"""
Tests for Obsidian Duplicate Consolidation Script

Tests the consolidate_obsidian_duplicates.py script functionality:
- Filename parsing
- Duplicate detection
- Task grouping
- Archive operations
- Summary generation
- Report generation

Author: UDO Development Platform
Version: 1.0.0
Date: 2025-12-28
"""

import json
import shutil
import tempfile
from datetime import datetime  # noqa: F401
from pathlib import Path
from unittest.mock import patch  # noqa: F401

import pytest

# Import the module under test
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from consolidate_obsidian_duplicates import (  # noqa: E402
    parse_filename,
    compute_content_hash,
    scan_date_folder,
    group_by_task,
    archive_duplicates,
    generate_daily_summary,
    process_date,
    get_all_date_folders,
    TaskFile,
    TaskGroup,
    CleanupReport,
    ARCHIVE_SUBDIR,
    DEV_LOG_DIR_NAME,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_vault():
    """Create a temporary vault structure for testing."""
    temp_dir = tempfile.mkdtemp(prefix="obsidian_test_")
    vault_path = Path(temp_dir)

    # Create development log directory
    dev_log = vault_path / DEV_LOG_DIR_NAME
    dev_log.mkdir(parents=True)

    yield vault_path

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_date_folder(temp_vault):
    """Create a sample date folder with duplicate files."""
    date = "2025-12-26"
    date_folder = temp_vault / DEV_LOG_DIR_NAME / date
    date_folder.mkdir(parents=True)

    # Create sample files - 3 versions of each task
    tasks = ["design-task", "testing-task", "mvp-task"]
    times = ["100000", "110000", "120000"]  # Increasing timestamps

    for task in tasks:
        for time in times:
            filename = f"{date}_{time}_{task}.md"
            content = f"""# {task}

#design #medium #kanban-archived

## Task Summary

**Phase**: design
**Archived**: {date} {time[:2]}:{time[2:4]}
**Task ID**: `test-id-{task}-{time}`

## Key Learnings

- Sample learning 1
- Sample learning 2

## ROI Metrics

- **Estimated**: 10.0h
- **Actual**: 9.0h
"""
            (date_folder / filename).write_text(content, encoding="utf-8")

    return date_folder, date


@pytest.fixture
def single_file_folder(temp_vault):
    """Create a folder with only single (non-duplicate) files."""
    date = "2025-12-25"
    date_folder = temp_vault / DEV_LOG_DIR_NAME / date
    date_folder.mkdir(parents=True)

    # One file per task
    tasks = ["task-a", "task-b"]
    for i, task in enumerate(tasks):
        filename = f"{date}_{i:06d}_{task}.md"
        (date_folder / filename).write_text(f"# {task}\n\nContent", encoding="utf-8")

    return date_folder, date


# ============================================================================
# Tests: Filename Parsing
# ============================================================================


class TestParseFilename:
    """Tests for parse_filename function."""

    def test_parse_standard_filename(self):
        """Test parsing standard filename with timestamp."""
        result = parse_filename("2025-12-26_023929_design-task.md")
        assert result is not None
        assert result == ("2025-12-26", "023929", "design-task")

    def test_parse_filename_with_dashes(self):
        """Test parsing filename with multiple dashes in task name."""
        result = parse_filename("2025-12-26_100000_implement-user-auth-system.md")
        assert result is not None
        assert result == ("2025-12-26", "100000", "implement-user-auth-system")

    def test_parse_filename_without_timestamp(self):
        """Test parsing filename without timestamp (alternative pattern)."""
        result = parse_filename("2025-12-26_some-task.md")
        assert result is not None
        assert result == ("2025-12-26", "000000", "some-task")

    def test_parse_invalid_filename(self):
        """Test that invalid filenames return None."""
        assert parse_filename("random-file.md") is None
        assert parse_filename("2025-12-26.md") is None
        assert parse_filename("not-a-date_task.md") is None

    def test_parse_non_markdown_filename(self):
        """Test that non-markdown files are not parsed as valid."""
        # The function only checks the pattern, extension check is in scan
        result = parse_filename("2025-12-26_100000_task.txt")
        assert result is None


# ============================================================================
# Tests: Content Hash
# ============================================================================


class TestComputeContentHash:
    """Tests for compute_content_hash function."""

    def test_hash_consistency(self, temp_vault):
        """Test that same content produces same hash."""
        test_file = temp_vault / "test.md"
        test_file.write_text("Hello, World!", encoding="utf-8")

        hash1 = compute_content_hash(test_file)
        hash2 = compute_content_hash(test_file)

        assert hash1 == hash2
        assert len(hash1) == 8  # Truncated to 8 chars

    def test_different_content_different_hash(self, temp_vault):
        """Test that different content produces different hashes."""
        file1 = temp_vault / "test1.md"
        file2 = temp_vault / "test2.md"

        file1.write_text("Content A", encoding="utf-8")
        file2.write_text("Content B", encoding="utf-8")

        assert compute_content_hash(file1) != compute_content_hash(file2)

    def test_hash_nonexistent_file(self, temp_vault):
        """Test handling of nonexistent file."""
        fake_file = temp_vault / "nonexistent.md"
        assert compute_content_hash(fake_file) == "error"


# ============================================================================
# Tests: Folder Scanning
# ============================================================================


class TestScanDateFolder:
    """Tests for scan_date_folder function."""

    def test_scan_with_duplicates(self, sample_date_folder):
        """Test scanning folder with duplicate files."""
        date_folder, date = sample_date_folder
        task_files, unmatched = scan_date_folder(date_folder)

        assert len(task_files) == 9  # 3 tasks x 3 versions
        assert len(unmatched) == 0

    def test_scan_empty_folder(self, temp_vault):
        """Test scanning empty folder."""
        empty_folder = temp_vault / DEV_LOG_DIR_NAME / "2025-01-01"
        empty_folder.mkdir(parents=True)

        task_files, unmatched = scan_date_folder(empty_folder)

        assert len(task_files) == 0
        assert len(unmatched) == 0

    def test_scan_nonexistent_folder(self, temp_vault):
        """Test scanning nonexistent folder."""
        fake_folder = temp_vault / "nonexistent"
        task_files, unmatched = scan_date_folder(fake_folder)

        assert len(task_files) == 0
        assert len(unmatched) == 0

    def test_scan_skips_directories(self, sample_date_folder):
        """Test that directories are skipped during scan."""
        date_folder, date = sample_date_folder

        # Create a subdirectory
        (date_folder / "subdir").mkdir()

        task_files, unmatched = scan_date_folder(date_folder)

        # Should still only find the files
        assert len(task_files) == 9


# ============================================================================
# Tests: Task Grouping
# ============================================================================


class TestGroupByTask:
    """Tests for group_by_task function."""

    def test_group_duplicates(self, sample_date_folder):
        """Test grouping of duplicate files by task name."""
        date_folder, date = sample_date_folder
        task_files, _ = scan_date_folder(date_folder)
        groups = group_by_task(task_files)

        assert len(groups) == 3  # 3 unique tasks
        assert all(len(g.files) == 3 for g in groups.values())  # 3 versions each

    def test_group_single_files(self, single_file_folder):
        """Test grouping when each task has only one file."""
        date_folder, date = single_file_folder
        task_files, _ = scan_date_folder(date_folder)
        groups = group_by_task(task_files)

        assert len(groups) == 2  # 2 unique tasks
        assert all(g.duplicate_count == 0 for g in groups.values())

    def test_latest_file_selection(self, sample_date_folder):
        """Test that latest file is correctly identified."""
        date_folder, date = sample_date_folder
        task_files, _ = scan_date_folder(date_folder)
        groups = group_by_task(task_files)

        for group in groups.values():
            latest = group.latest_file
            assert latest is not None
            assert latest.timestamp == "120000"  # Latest timestamp


# ============================================================================
# Tests: TaskGroup Dataclass
# ============================================================================


class TestTaskGroup:
    """Tests for TaskGroup dataclass methods."""

    def test_duplicate_count(self):
        """Test duplicate count calculation."""
        group = TaskGroup(task_name="test")
        group.files = [
            TaskFile(Path("a.md"), "2025-01-01", "100000", "test", 100),
            TaskFile(Path("b.md"), "2025-01-01", "110000", "test", 100),
            TaskFile(Path("c.md"), "2025-01-01", "120000", "test", 100),
        ]

        assert group.duplicate_count == 2
        assert len(group.duplicates) == 2

    def test_empty_group(self):
        """Test empty group behavior."""
        group = TaskGroup(task_name="empty")

        assert group.latest_file is None
        assert group.duplicate_count == 0
        assert group.duplicates == []

    def test_single_file_group(self):
        """Test group with single file (no duplicates)."""
        group = TaskGroup(task_name="single")
        group.files = [TaskFile(Path("a.md"), "2025-01-01", "100000", "single", 100)]

        assert group.duplicate_count == 0
        assert group.duplicates == []


# ============================================================================
# Tests: Archive Operations
# ============================================================================


class TestArchiveDuplicates:
    """Tests for archive_duplicates function."""

    def test_archive_dry_run(self, sample_date_folder):
        """Test archive operation in dry-run mode."""
        date_folder, date = sample_date_folder
        task_files, _ = scan_date_folder(date_folder)
        groups = group_by_task(task_files)

        archived, bytes_archived, errors = archive_duplicates(groups, date_folder, dry_run=True)

        # Dry run should count but not move files
        assert archived == 6  # 3 tasks x 2 duplicates each
        assert bytes_archived > 0
        assert len(errors) == 0

        # Files should still exist
        assert len(list(date_folder.glob("*.md"))) == 9

    def test_archive_execute(self, sample_date_folder):
        """Test archive operation in execute mode."""
        date_folder, date = sample_date_folder
        task_files, _ = scan_date_folder(date_folder)
        groups = group_by_task(task_files)

        archived, bytes_archived, errors = archive_duplicates(groups, date_folder, dry_run=False)

        assert archived == 6
        assert len(errors) == 0

        # Archive directory should exist
        archive_dir = date_folder / ARCHIVE_SUBDIR
        assert archive_dir.exists()

        # 6 files should be in archive
        assert len(list(archive_dir.glob("*.md"))) == 6

        # 3 files should remain in main folder
        main_files = [f for f in date_folder.glob("*.md") if f.parent == date_folder]
        assert len(main_files) == 3


# ============================================================================
# Tests: Summary Generation
# ============================================================================


class TestGenerateDailySummary:
    """Tests for generate_daily_summary function."""

    def test_summary_dry_run(self, sample_date_folder):
        """Test summary generation in dry-run mode."""
        date_folder, date = sample_date_folder
        task_files, _ = scan_date_folder(date_folder)
        groups = group_by_task(task_files)

        summary_path = generate_daily_summary(groups, date, date_folder, dry_run=True)

        assert summary_path is not None
        assert "Daily-Summary-Consolidated.md" in summary_path.name
        assert not summary_path.exists()  # Dry run doesn't create file

    def test_summary_execute(self, sample_date_folder):
        """Test summary generation in execute mode."""
        date_folder, date = sample_date_folder
        task_files, _ = scan_date_folder(date_folder)
        groups = group_by_task(task_files)

        summary_path = generate_daily_summary(groups, date, date_folder, dry_run=False)

        assert summary_path is not None
        assert summary_path.exists()

        # Verify content
        content = summary_path.read_text(encoding="utf-8")
        assert "Daily Summary" in content
        assert "design-task" in content
        assert "testing-task" in content
        assert "mvp-task" in content

    def test_summary_empty_groups(self, temp_vault):
        """Test summary generation with no task groups."""
        date_folder = temp_vault / DEV_LOG_DIR_NAME / "2025-01-01"
        date_folder.mkdir(parents=True)

        summary_path = generate_daily_summary({}, "2025-01-01", date_folder, dry_run=False)

        assert summary_path is None


# ============================================================================
# Tests: Full Processing
# ============================================================================


class TestProcessDate:
    """Tests for process_date function."""

    def test_process_with_duplicates(self, sample_date_folder, temp_vault):
        """Test full processing of a date with duplicates."""
        date_folder, date = sample_date_folder
        report = process_date(date, temp_vault, dry_run=True)

        assert report.date == date
        assert report.total_files_scanned == 9
        assert report.unique_tasks == 3
        assert report.duplicates_found == 6

    def test_process_no_duplicates(self, single_file_folder, temp_vault):
        """Test processing when no duplicates exist."""
        date_folder, date = single_file_folder
        report = process_date(date, temp_vault, dry_run=True)

        assert report.duplicates_found == 0
        assert report.unique_tasks == 2

    def test_process_nonexistent_date(self, temp_vault):
        """Test processing nonexistent date folder."""
        report = process_date("2099-01-01", temp_vault, dry_run=True)

        assert len(report.errors) > 0
        assert "not found" in report.errors[0].lower()


# ============================================================================
# Tests: Get All Date Folders
# ============================================================================


class TestGetAllDateFolders:
    """Tests for get_all_date_folders function."""

    def test_get_dates_multiple(self, temp_vault):
        """Test getting multiple date folders."""
        dev_log = temp_vault / DEV_LOG_DIR_NAME

        dates = ["2025-12-26", "2025-12-25", "2025-12-24"]
        for date in dates:
            (dev_log / date).mkdir()

        result = get_all_date_folders(temp_vault)

        assert len(result) == 3
        assert result[0] == "2025-12-26"  # Most recent first
        assert result[-1] == "2025-12-24"

    def test_get_dates_empty(self, temp_vault):
        """Test getting dates from empty vault."""
        result = get_all_date_folders(temp_vault)

        assert result == []

    def test_get_dates_ignores_non_date_folders(self, temp_vault):
        """Test that non-date folders are ignored."""
        dev_log = temp_vault / DEV_LOG_DIR_NAME

        (dev_log / "2025-12-26").mkdir()
        (dev_log / "not-a-date").mkdir()
        (dev_log / "random").mkdir()

        result = get_all_date_folders(temp_vault)

        assert len(result) == 1
        assert result[0] == "2025-12-26"


# ============================================================================
# Tests: Report Serialization
# ============================================================================


class TestCleanupReport:
    """Tests for CleanupReport dataclass."""

    def test_report_to_dict(self):
        """Test report serialization to dictionary."""
        report = CleanupReport(
            date="2025-12-26",
            total_files_scanned=100,
            unique_tasks=10,
            duplicates_found=90,
            duplicates_archived=90,
            bytes_archived=102400,
        )

        data = report.to_dict()

        assert data["date"] == "2025-12-26"
        assert data["total_files_scanned"] == 100
        assert data["bytes_archived_kb"] == 100.0

    def test_report_json_serializable(self):
        """Test that report dict is JSON serializable."""
        report = CleanupReport(date="2025-12-26")
        data = report.to_dict()

        # Should not raise
        json_str = json.dumps(data)
        assert json_str is not None


# ============================================================================
# Tests: TaskFile Dataclass
# ============================================================================


class TestTaskFile:
    """Tests for TaskFile dataclass methods."""

    def test_datetime_obj(self):
        """Test datetime conversion."""
        tf = TaskFile(path=Path("test.md"), date="2025-12-26", timestamp="143022", task_name="test", size_bytes=100)

        dt = tf.datetime_obj
        assert dt.year == 2025
        assert dt.month == 12
        assert dt.day == 26
        assert dt.hour == 14
        assert dt.minute == 30
        assert dt.second == 22

    def test_display_time(self):
        """Test human-readable time format."""
        tf = TaskFile(path=Path("test.md"), date="2025-12-26", timestamp="093045", task_name="test", size_bytes=100)

        assert tf.display_time == "09:30:45"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
