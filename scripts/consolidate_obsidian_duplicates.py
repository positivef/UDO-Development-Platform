#!/usr/bin/env python3
"""
Obsidian Vault Duplicate Consolidation Script

Identifies and consolidates duplicate files in the Obsidian vault's development log.

Problem: Test runs generate 200+ duplicate files per day with pattern:
    YYYY-MM-DD_HHMMSS_<task-name>.md

Solution: Keep only the LATEST version of each unique task, archive duplicates,
and generate a consolidated daily summary.

Features:
- Dry-run mode (preview without changes)
- Execute mode (perform cleanup with confirmation)
- Consolidated daily summary generation
- Safe archival of duplicates (no deletion)
- Detailed cleanup report

Usage:
    python scripts/consolidate_obsidian_duplicates.py                    # Dry run
    python scripts/consolidate_obsidian_duplicates.py --execute          # Execute
    python scripts/consolidate_obsidian_duplicates.py --execute --yes    # No confirmation
    python scripts/consolidate_obsidian_duplicates.py --date 2025-12-26  # Specific date
    python scripts/consolidate_obsidian_duplicates.py --all-dates        # All dates

Author: UDO Development Platform
Version: 1.0.0
Date: 2025-12-28
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ============================================================================
# Configuration
# ============================================================================

# Default Obsidian vault path (can be overridden via environment or CLI)
DEFAULT_VAULT_PATH = Path(os.getenv("OBSIDIAN_VAULT_PATH", r"C:\Users\user\Documents\Obsidian Vault"))

# Development log subdirectory
DEV_LOG_DIR_NAME = "개발일지"

# Archive subdirectory for duplicates (inside date folder)
ARCHIVE_SUBDIR = "_duplicates"

# File pattern: YYYY-MM-DD_HHMMSS_<task-name>.md
FILE_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})_(\d{6})_(.+)\.md$")

# Alternative patterns to handle edge cases
ALT_PATTERN_NO_TIME = re.compile(r"^(\d{4}-\d{2}-\d{2})_(.+?)(-\d+)?\.md$")


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class TaskFile:
    """Represents a single task file in the vault."""

    path: Path
    date: str
    timestamp: str  # HHMMSS format
    task_name: str
    size_bytes: int
    content_hash: str = ""

    @property
    def datetime_obj(self) -> datetime:
        """Parse date and timestamp into datetime object."""
        dt_str = f"{self.date}_{self.timestamp}"
        return datetime.strptime(dt_str, "%Y-%m-%d_%H%M%S")

    @property
    def display_time(self) -> str:
        """Human-readable time format."""
        return f"{self.timestamp[:2]}:{self.timestamp[2:4]}:{self.timestamp[4:6]}"


@dataclass
class TaskGroup:
    """Group of duplicate files for the same task."""

    task_name: str
    files: List[TaskFile] = field(default_factory=list)

    @property
    def latest_file(self) -> Optional[TaskFile]:
        """Get the most recent file in the group."""
        if not self.files:
            return None
        return max(self.files, key=lambda f: f.datetime_obj)

    @property
    def duplicates(self) -> List[TaskFile]:
        """Get all files except the latest one."""
        if len(self.files) <= 1:
            return []
        latest = self.latest_file
        return [f for f in self.files if f != latest]

    @property
    def duplicate_count(self) -> int:
        """Number of duplicate files."""
        return len(self.duplicates)

    @property
    def total_duplicate_size(self) -> int:
        """Total size of duplicate files in bytes."""
        return sum(f.size_bytes for f in self.duplicates)


@dataclass
class CleanupReport:
    """Report of cleanup operation."""

    date: str
    total_files_scanned: int = 0
    unique_tasks: int = 0
    duplicates_found: int = 0
    duplicates_archived: int = 0
    bytes_archived: int = 0
    errors: List[str] = field(default_factory=list)
    task_groups: Dict[str, TaskGroup] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "date": self.date,
            "total_files_scanned": self.total_files_scanned,
            "unique_tasks": self.unique_tasks,
            "duplicates_found": self.duplicates_found,
            "duplicates_archived": self.duplicates_archived,
            "bytes_archived": self.bytes_archived,
            "bytes_archived_kb": round(self.bytes_archived / 1024, 2),
            "errors": self.errors,
            "task_summary": {
                name: {
                    "total_versions": len(group.files),
                    "duplicates": group.duplicate_count,
                    "latest_time": group.latest_file.display_time if group.latest_file else None,
                }
                for name, group in self.task_groups.items()
            },
        }


# ============================================================================
# Core Functions
# ============================================================================


def parse_filename(filename: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse a task filename into components.

    Args:
        filename: The filename to parse (e.g., "2025-12-26_023929_design-task.md")

    Returns:
        Tuple of (date, timestamp, task_name) or None if not matching
    """
    # Try primary pattern with timestamp
    match = FILE_PATTERN.match(filename)
    if match:
        return match.group(1), match.group(2), match.group(3)

    # Try alternative pattern without timestamp
    match = ALT_PATTERN_NO_TIME.match(filename)
    if match:
        # Use 000000 as placeholder timestamp for files without time
        return match.group(1), "000000", match.group(2)

    return None


def compute_content_hash(filepath: Path) -> str:
    """
    Compute MD5 hash of file content for deduplication verification.

    Args:
        filepath: Path to the file

    Returns:
        MD5 hash string
    """
    try:
        content = filepath.read_bytes()
        return hashlib.md5(content).hexdigest()[:8]
    except Exception:
        return "error"


def scan_date_folder(date_folder: Path) -> Tuple[List[TaskFile], List[Path]]:
    """
    Scan a date folder and categorize files.

    Args:
        date_folder: Path to the YYYY-MM-DD folder

    Returns:
        Tuple of (list of TaskFile objects, list of unmatched files)
    """
    task_files: List[TaskFile] = []
    unmatched_files: List[Path] = []

    if not date_folder.exists():
        return task_files, unmatched_files

    for filepath in date_folder.iterdir():
        # Skip directories (like _duplicates archive)
        if filepath.is_dir():
            continue

        # Skip non-markdown files
        if filepath.suffix.lower() != ".md":
            continue

        parsed = parse_filename(filepath.name)
        if parsed:
            date, timestamp, task_name = parsed
            task_files.append(
                TaskFile(
                    path=filepath,
                    date=date,
                    timestamp=timestamp,
                    task_name=task_name,
                    size_bytes=filepath.stat().st_size,
                    content_hash=compute_content_hash(filepath),
                )
            )
        else:
            unmatched_files.append(filepath)

    return task_files, unmatched_files


def group_by_task(task_files: List[TaskFile]) -> Dict[str, TaskGroup]:
    """
    Group task files by their task name.

    Args:
        task_files: List of TaskFile objects

    Returns:
        Dictionary mapping task name to TaskGroup
    """
    groups: Dict[str, TaskGroup] = {}

    for tf in task_files:
        if tf.task_name not in groups:
            groups[tf.task_name] = TaskGroup(task_name=tf.task_name)
        groups[tf.task_name].files.append(tf)

    # Sort files within each group by timestamp (newest first)
    for group in groups.values():
        group.files.sort(key=lambda f: f.datetime_obj, reverse=True)

    return groups


def archive_duplicates(
    task_groups: Dict[str, TaskGroup], date_folder: Path, dry_run: bool = True
) -> Tuple[int, int, List[str]]:
    """
    Archive duplicate files to the _duplicates subdirectory.

    Args:
        task_groups: Dictionary of task groups
        date_folder: Path to the date folder
        dry_run: If True, only preview without making changes

    Returns:
        Tuple of (files_archived, bytes_archived, errors)
    """
    files_archived = 0
    bytes_archived = 0
    errors: List[str] = []

    archive_dir = date_folder / ARCHIVE_SUBDIR

    for group in task_groups.values():
        for dup_file in group.duplicates:
            try:
                if dry_run:
                    files_archived += 1
                    bytes_archived += dup_file.size_bytes
                else:
                    # Create archive directory if needed
                    archive_dir.mkdir(exist_ok=True)

                    # Move file to archive
                    dest_path = archive_dir / dup_file.path.name

                    # Handle name collision in archive
                    if dest_path.exists():
                        base = dest_path.stem
                        suffix = dest_path.suffix
                        counter = 1
                        while dest_path.exists():
                            dest_path = archive_dir / f"{base}_{counter}{suffix}"
                            counter += 1

                    shutil.move(str(dup_file.path), str(dest_path))
                    files_archived += 1
                    bytes_archived += dup_file.size_bytes

            except Exception as e:
                errors.append(f"Failed to archive {dup_file.path.name}: {str(e)}")

    return files_archived, bytes_archived, errors


def generate_daily_summary(
    task_groups: Dict[str, TaskGroup], date: str, date_folder: Path, dry_run: bool = True
) -> Optional[Path]:
    """
    Generate a consolidated daily summary from all unique tasks.

    Args:
        task_groups: Dictionary of task groups
        date: Date string (YYYY-MM-DD)
        date_folder: Path to the date folder
        dry_run: If True, only preview without making changes

    Returns:
        Path to the generated summary file, or None
    """
    if not task_groups:
        return None

    summary_filename = f"{date}_Daily-Summary-Consolidated.md"
    summary_path = date_folder / summary_filename

    # Collect data from latest version of each task
    tasks_data = []
    total_estimated = 0.0
    total_actual = 0.0

    for group in sorted(task_groups.values(), key=lambda g: g.task_name):
        latest = group.latest_file
        if not latest:
            continue

        # Parse task content for metrics
        try:
            content = latest.path.read_text(encoding="utf-8")
            tasks_data.append(
                {"name": group.task_name, "time": latest.display_time, "versions": len(group.files), "content": content}
            )

            # Extract estimated/actual hours if present
            est_match = re.search(r"\*\*Estimated\*\*:\s*([\d.]+)h", content)
            act_match = re.search(r"\*\*Actual\*\*:\s*([\d.]+)h", content)
            if est_match:
                total_estimated += float(est_match.group(1))
            if act_match:
                total_actual += float(act_match.group(1))

        except Exception:
            tasks_data.append(
                {"name": group.task_name, "time": latest.display_time, "versions": len(group.files), "content": ""}
            )

    # Generate summary content
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    summary_content = f"""---
date: {date}
type: daily-summary
generated: {now}
total_tasks: {len(task_groups)}
total_estimated_hours: {total_estimated:.1f}
total_actual_hours: {total_actual:.1f}
tags: [daily-summary, consolidated, auto-generated]
---

# Daily Summary - {date}

**Generated**: {now}
**Total Unique Tasks**: {len(task_groups)}
**Duplicate Versions Archived**: {sum(g.duplicate_count for g in task_groups.values())}

## Task Overview

| Task | Latest Time | Versions | Status |
|------|-------------|----------|--------|
"""

    for task in tasks_data:
        status = "Consolidated" if task["versions"] > 1 else "Single"
        summary_content += f"| {task['name']} | {task['time']} | {task['versions']} | {status} |\n"

    summary_content += f"""
## Metrics Summary

- **Total Estimated Hours**: {total_estimated:.1f}h
- **Total Actual Hours**: {total_actual:.1f}h
- **Efficiency**: {(total_estimated / total_actual * 100) if total_actual > 0 else 0:.1f}%

## Individual Task Details

"""

    for task in tasks_data:
        summary_content += f"### {task['name']}\n\n"
        summary_content += f"**Latest Version**: {task['time']} ({task['versions']} total versions)\n\n"

        # Extract key learnings if present
        if task["content"]:
            learnings_match = re.search(r"## .* Key Learnings\n\n((?:- .+\n)+)", task["content"])
            if learnings_match:
                summary_content += "**Key Learnings**:\n"
                summary_content += learnings_match.group(1)
                summary_content += "\n"

        summary_content += "---\n\n"

    summary_content += """
## Notes

This summary was automatically generated by the Obsidian duplicate consolidation script.
Original duplicate files have been archived to the `_duplicates` subdirectory.

**Script**: `scripts/consolidate_obsidian_duplicates.py`
"""

    if dry_run:
        return summary_path

    try:
        summary_path.write_text(summary_content, encoding="utf-8")
        return summary_path
    except Exception:
        return None


def process_date(date: str, vault_path: Path, dry_run: bool = True, verbose: bool = False) -> CleanupReport:
    """
    Process a single date folder for duplicate consolidation.

    Args:
        date: Date string (YYYY-MM-DD)
        vault_path: Path to the Obsidian vault
        dry_run: If True, only preview without making changes
        verbose: If True, show detailed output

    Returns:
        CleanupReport with results
    """
    report = CleanupReport(date=date)
    date_folder = vault_path / DEV_LOG_DIR_NAME / date

    if not date_folder.exists():
        report.errors.append(f"Date folder not found: {date_folder}")
        return report

    # Scan folder
    task_files, unmatched = scan_date_folder(date_folder)
    report.total_files_scanned = len(task_files) + len(unmatched)

    if verbose and unmatched:
        print(f"  [INFO] {len(unmatched)} unmatched files (skipped)")

    # Group by task
    task_groups = group_by_task(task_files)
    report.unique_tasks = len(task_groups)
    report.task_groups = task_groups

    # Count duplicates
    total_duplicates = sum(g.duplicate_count for g in task_groups.values())
    report.duplicates_found = total_duplicates

    if total_duplicates == 0:
        if verbose:
            print(f"  [OK] No duplicates found in {date}")
        return report

    # Archive duplicates
    archived, bytes_archived, errors = archive_duplicates(task_groups, date_folder, dry_run)
    report.duplicates_archived = archived
    report.bytes_archived = bytes_archived
    report.errors.extend(errors)

    # Generate daily summary
    if not dry_run:
        summary_path = generate_daily_summary(task_groups, date, date_folder, dry_run)
        if summary_path:
            print(f"  [SUMMARY] Created: {summary_path.name}")

    return report


def get_all_date_folders(vault_path: Path) -> List[str]:
    """
    Get all date folders in the development log directory.

    Args:
        vault_path: Path to the Obsidian vault

    Returns:
        List of date strings (YYYY-MM-DD format)
    """
    dev_log = vault_path / DEV_LOG_DIR_NAME
    if not dev_log.exists():
        return []

    dates = []
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    for item in dev_log.iterdir():
        if item.is_dir() and date_pattern.match(item.name):
            dates.append(item.name)

    return sorted(dates, reverse=True)  # Most recent first


def print_report(report: CleanupReport, dry_run: bool = True) -> None:
    """Print a formatted cleanup report."""
    mode = "DRY RUN" if dry_run else "EXECUTED"

    print(f"\n{'=' * 60}")
    print(f"CLEANUP REPORT - {report.date} [{mode}]")
    print(f"{'=' * 60}")

    print(f"\nFiles scanned:       {report.total_files_scanned}")
    print(f"Unique tasks:        {report.unique_tasks}")
    print(f"Duplicates found:    {report.duplicates_found}")
    print(f"Duplicates archived: {report.duplicates_archived}")
    print(f"Space freed:         {report.bytes_archived / 1024:.1f} KB")

    if report.task_groups:
        print("\nTask Breakdown:")
        print(f"{'Task Name':<40} {'Versions':<10} {'Duplicates':<10} {'Latest'}")
        print("-" * 75)

        for name, group in sorted(report.task_groups.items()):
            latest_time = group.latest_file.display_time if group.latest_file else "N/A"
            print(f"{name:<40} {len(group.files):<10} {group.duplicate_count:<10} {latest_time}")

    if report.errors:
        print(f"\nErrors ({len(report.errors)}):")
        for error in report.errors:
            print(f"  - {error}")

    print()


def save_report_json(reports: List[CleanupReport], output_path: Path) -> None:
    """Save cleanup reports to JSON file."""
    data = {"generated": datetime.now().isoformat(), "reports": [r.to_dict() for r in reports]}

    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ============================================================================
# Main Entry Point
# ============================================================================


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Consolidate duplicate files in Obsidian vault development logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview cleanup for today
  python scripts/consolidate_obsidian_duplicates.py

  # Execute cleanup for today
  python scripts/consolidate_obsidian_duplicates.py --execute

  # Execute cleanup for specific date
  python scripts/consolidate_obsidian_duplicates.py --execute --date 2025-12-26

  # Execute cleanup for all dates
  python scripts/consolidate_obsidian_duplicates.py --execute --all-dates

  # Execute with auto-confirmation (for automation)
  python scripts/consolidate_obsidian_duplicates.py --execute --yes
""",
    )

    parser.add_argument("--execute", action="store_true", help="Execute cleanup (default is dry-run preview)")
    parser.add_argument("--date", type=str, help="Specific date to process (YYYY-MM-DD format)")
    parser.add_argument("--all-dates", action="store_true", help="Process all date folders")
    parser.add_argument("--vault", type=str, help=f"Obsidian vault path (default: {DEFAULT_VAULT_PATH})")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--json-report", type=str, help="Save JSON report to specified path")

    args = parser.parse_args()

    # Determine vault path
    vault_path = Path(args.vault) if args.vault else DEFAULT_VAULT_PATH

    if not vault_path.exists():
        print(f"[ERROR] Vault not found: {vault_path}")
        return 1

    dev_log_path = vault_path / DEV_LOG_DIR_NAME
    if not dev_log_path.exists():
        print(f"[ERROR] Development log directory not found: {dev_log_path}")
        return 1

    # Determine dates to process
    if args.all_dates:
        dates = get_all_date_folders(vault_path)
        if not dates:
            print("[INFO] No date folders found")
            return 0
    elif args.date:
        dates = [args.date]
    else:
        # Default to today
        dates = [datetime.now().strftime("%Y-%m-%d")]

    # Print header
    dry_run = not args.execute
    mode = "DRY RUN" if dry_run else "EXECUTE"

    print("=" * 60)
    print("OBSIDIAN DUPLICATE CONSOLIDATION")
    print("=" * 60)
    print(f"Vault: {vault_path}")
    print(f"Mode: {mode}")
    print(f"Dates to process: {len(dates)}")
    print()

    # Collect reports for preview
    reports: List[CleanupReport] = []
    total_duplicates = 0
    total_bytes = 0

    for date in dates:
        print(f"[SCANNING] {date}...")
        report = process_date(date, vault_path, dry_run=True, verbose=args.verbose)
        reports.append(report)
        total_duplicates += report.duplicates_found
        total_bytes += sum(g.total_duplicate_size for g in report.task_groups.values())

    # Print preview summary
    print()
    print("=" * 60)
    print("PREVIEW SUMMARY")
    print("=" * 60)
    print(f"Total dates: {len(dates)}")
    print(f"Total duplicates found: {total_duplicates}")
    print(f"Total space to free: {total_bytes / 1024:.1f} KB")

    for report in reports:
        if report.duplicates_found > 0:
            print(f"\n  [{report.date}] {report.duplicates_found} duplicates from {report.unique_tasks} tasks")

    if total_duplicates == 0:
        print("\n[OK] No duplicates to archive")
        return 0

    # Confirmation for execute mode
    if args.execute:
        print()

        if not args.yes:
            try:
                confirm = input(f"Archive {total_duplicates} duplicate files? [y/N]: ").strip().lower()
            except EOFError:
                confirm = ""

            if confirm not in ("y", "yes"):
                print("[CANCELLED] No files were modified")
                return 0
        else:
            print("[AUTO] Skipping confirmation (--yes flag)")

        # Execute cleanup
        print("\n[EXECUTING] Archiving duplicates...")

        execution_reports: List[CleanupReport] = []
        for date in dates:
            print(f"\n  [{date}] Processing...")
            report = process_date(date, vault_path, dry_run=False, verbose=args.verbose)
            execution_reports.append(report)

            if report.duplicates_archived > 0:
                print(f"    Archived: {report.duplicates_archived} files ({report.bytes_archived / 1024:.1f} KB)")

            if report.errors:
                for error in report.errors:
                    print(f"    [ERROR] {error}")

        # Final summary
        total_archived = sum(r.duplicates_archived for r in execution_reports)
        total_bytes_archived = sum(r.bytes_archived for r in execution_reports)
        total_errors = sum(len(r.errors) for r in execution_reports)

        print()
        print("=" * 60)
        print("EXECUTION COMPLETE")
        print("=" * 60)
        print(f"Files archived: {total_archived}")
        print(f"Space freed: {total_bytes_archived / 1024:.1f} KB")
        print(f"Errors: {total_errors}")

        # Save JSON report if requested
        if args.json_report:
            report_path = Path(args.json_report)
            save_report_json(execution_reports, report_path)
            print(f"\nJSON report saved: {report_path}")

        reports = execution_reports
    else:
        print()
        print("[PREVIEW] No files were modified")
        print("Run with --execute to archive duplicates")

    # Optional detailed reports
    if args.verbose:
        for report in reports:
            print_report(report, dry_run)

    return 0


if __name__ == "__main__":
    sys.exit(main())
