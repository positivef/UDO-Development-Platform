#!/usr/bin/env python3
"""
claudedocs/ Retention Cleanup Script

Automatically cleans up expired files based on retention policy:
- whiteboard/: 7 days since last project activity
- worklog/: 30 days since last project activity
- analysis/: 90 days since last project activity
- completion/: PERMANENT (never delete)
- decisions/: PERMANENT (never delete)

IMPORTANT: Retention is calculated from LAST PROJECT ACTIVITY (git commit),
NOT from absolute calendar date. This ensures files remain valid
while project is actively developed.

Archive Strategy (2-stage):
- Stage 1 (in-project): Expired -> claudedocs/_archived/ (14 day grace period)
- Stage 2 (external): Archive expired -> D:/claudedocs-archive/{project}/ (permanent storage)

Usage:
    python scripts/cleanup_claudedocs.py              # Dry run (preview only)
    python scripts/cleanup_claudedocs.py --execute    # Move expired files
    python scripts/cleanup_claudedocs.py --verbose    # Show all files checked
    python scripts/cleanup_claudedocs.py --external   # Also process Stage 2 (external archive)
"""

import sys
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Retention policy (days since LAST PROJECT ACTIVITY) - 0 means permanent
RETENTION_POLICY: Dict[str, int] = {
    "whiteboard": 7,
    "worklog": 30,
    "analysis": 90,
    "completion": 0,  # Permanent
    "decisions": 0,  # Permanent
}

# Stage 1: In-project archive (grace period)
ARCHIVE_FOLDER = "_archived"
ARCHIVE_GRACE_DAYS = 14  # Days before moving to external archive

# Stage 2: External archive (permanent storage, outside project)
EXTERNAL_ARCHIVE_ROOT = Path("D:/claudedocs-archive")


def get_last_project_activity() -> datetime:
    """
    Get the timestamp of last project activity (git commit).

    This is the reference point for retention calculation.
    Files are considered "expired" only if they are older than
    (last_activity - retention_days), NOT from today's date.

    Returns:
        datetime of last git commit, or datetime.now() if not a git repo
    """
    try:
        # Get last commit timestamp
        result = subprocess.run(["git", "log", "-1", "--format=%ct"], capture_output=True, text=True, cwd=get_project_root())

        if result.returncode == 0 and result.stdout.strip():
            timestamp = int(result.stdout.strip())
            return datetime.fromtimestamp(timestamp)

    except (subprocess.SubprocessError, ValueError, FileNotFoundError):
        pass

    # Fallback to current time if git not available
    print("[WARNING] Could not get git commit time, using current time")
    return datetime.now()


def get_project_name() -> str:
    """
    Get project name from git remote or folder name.

    Priority:
    1. Git remote origin URL (e.g., github.com/user/project-name)
    2. Root folder name as fallback
    """
    try:
        # Try to get from git remote
        result = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, cwd=get_project_root())

        if result.returncode == 0 and result.stdout.strip():
            url = result.stdout.strip()
            # Extract project name from URL
            # https://github.com/user/project-name.git -> project-name
            # git@github.com:user/project-name.git -> project-name
            name = url.rstrip("/").rstrip(".git").split("/")[-1]
            if name:
                return name
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    # Fallback to folder name
    return get_project_root().name


def get_external_archive_path() -> Path:
    """Get external archive path for current project."""
    project_name = get_project_name()
    return EXTERNAL_ARCHIVE_ROOT / project_name


def update_archive_index(external_archive: Path, moved_files: List[Tuple[Path, str]]) -> None:
    """
    Update INDEX.md in external archive with newly moved files.

    This file serves as a guide for finding past context when needed.
    """
    index_path = external_archive / "INDEX.md"
    today = datetime.now().strftime("%Y-%m-%d")
    project_name = get_project_name()

    # Read existing index or create new
    if index_path.exists():
        existing_content = index_path.read_text(encoding="utf-8")
    else:
        existing_content = f"""# {project_name} - Archived claudedocs

This archive contains expired documentation from the `claudedocs/` folder.

**Purpose**: Past context reference for AI sessions and development history.

**How to search**:
```bash
# Find files by keyword
grep -r "keyword" D:/claudedocs-archive/{project_name}/

# List all files
find D:/claudedocs-archive/{project_name}/ -name "*.md" | sort
```

---

## Archive History

"""

    # Append new entries
    if moved_files:
        new_entries = f"\n### {today}\n\n"
        for filepath, subfolder in moved_files:
            new_entries += f"- `{subfolder}/{filepath.name}`\n"

        # Append to existing content
        updated_content = existing_content + new_entries

        # Write updated index
        external_archive.mkdir(parents=True, exist_ok=True)
        index_path.write_text(updated_content, encoding="utf-8")
        print(f"  [INDEX] Updated {index_path}")


def get_project_root() -> Path:
    """Get project root directory."""
    script_dir = Path(__file__).parent
    return script_dir.parent


def get_claudedocs_path() -> Path:
    """Find claudedocs/ folder relative to script location."""
    project_root = get_project_root()
    claudedocs = project_root / "claudedocs"

    if not claudedocs.exists():
        print(f"[ERROR] claudedocs/ not found at: {claudedocs}")
        sys.exit(1)

    return claudedocs


def parse_date_from_filename(filename: str) -> Optional[datetime]:
    """
    Extract date from filename patterns:
    - YYYY-MM-DD-*.md
    - YYYY-MM-DD_*.md
    - *_YYYY-MM-DD.md
    """
    import re

    # Pattern: YYYY-MM-DD at start or end
    patterns = [
        r"^(\d{4}-\d{2}-\d{2})",  # Start: 2025-12-15-worklog.md
        r"(\d{4}-\d{2}-\d{2})\.md$",  # End: analysis_2025-12-15.md
        r"_(\d{4}-\d{2}-\d{2})_",  # Middle: foo_2025-12-15_bar.md
    ]

    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                return datetime.strptime(match.group(1), "%Y-%m-%d")
            except ValueError:
                continue

    return None


def get_file_age_days(filepath: Path, reference_time: datetime) -> int:
    """
    Get file age in days relative to reference time (last project activity).

    Args:
        filepath: Path to the file
        reference_time: Reference point (last git commit, not today)

    Returns:
        Number of days between file date and reference_time
    """
    # Try to get date from filename first
    filename_date = parse_date_from_filename(filepath.name)

    if filename_date:
        return (reference_time - filename_date).days

    # Fallback to file modification time
    mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
    return (reference_time - mtime).days


def scan_folder(folder_path: Path, retention_days: int, reference_time: datetime) -> List[Tuple[Path, int, str]]:
    """
    Scan folder and return list of (filepath, age_days, status).

    Args:
        folder_path: Directory to scan
        retention_days: Retention period (0 = permanent)
        reference_time: Reference point for age calculation (last project activity)

    Returns:
        List of (filepath, age_days, status)
        Status: 'expired', 'valid', 'permanent'
    """
    results = []

    if not folder_path.exists():
        return results

    for filepath in folder_path.glob("*.md"):
        if filepath.name.startswith("."):
            continue

        age_days = get_file_age_days(filepath, reference_time)

        if retention_days == 0:
            status = "permanent"
        elif age_days > retention_days:
            status = "expired"
        else:
            status = "valid"

        results.append((filepath, age_days, status))

    return results


def scan_internal_archive(claudedocs: Path, reference_time: datetime) -> List[Tuple[Path, int, str]]:
    """
    Scan in-project _archived/ folder for Stage 2 processing.

    Files older than ARCHIVE_GRACE_DAYS are marked for external archiving.

    Returns:
        List of (filepath, age_days, 'archive_expired' | 'archive_valid')
    """
    results = []
    archive_path = claudedocs / ARCHIVE_FOLDER

    if not archive_path.exists():
        return results

    # Scan all subfolders in _archived/
    for subfolder in archive_path.iterdir():
        if not subfolder.is_dir():
            continue

        for filepath in subfolder.glob("*.md"):
            age_days = get_file_age_days(filepath, reference_time)

            if age_days > ARCHIVE_GRACE_DAYS:
                status = "archive_expired"
            else:
                status = "archive_valid"

            results.append((filepath, age_days, status))

    return results


def cleanup_claudedocs(
    execute: bool = False,
    verbose: bool = False,
    archive: bool = True,
    auto_confirm: bool = False,
    process_external: bool = False,
) -> Dict[str, List[Path]]:
    """
    Main cleanup function with 2-stage archiving.

    Stage 1: Expired files -> claudedocs/_archived/ (in-project, 14 day grace)
    Stage 2: Archive expired -> D:/claudedocs-archive/{project}/ (external, permanent)

    Args:
        execute: If True, process expired files (with confirmation).
        verbose: If True, show all files (not just expired).
        archive: If True, move to _archived instead of deleting.
        auto_confirm: If True, skip confirmation prompt (for automation).
        process_external: If True, also process Stage 2 (external archive).

    Returns:
        Dict with 'deleted' and 'skipped' file lists.
    """
    claudedocs = get_claudedocs_path()
    today = datetime.now().strftime("%Y-%m-%d")
    project_name = get_project_name()
    external_archive = get_external_archive_path()

    # Get last project activity (git commit) as reference point
    last_activity = get_last_project_activity()
    last_activity_str = last_activity.strftime("%Y-%m-%d %H:%M")

    print("=" * 60)
    print(f"claudedocs/ Retention Cleanup - {today}")
    print("=" * 60)
    print(f"Project: {project_name}")
    print(f"Mode: {'EXECUTE' if execute else 'DRY RUN (preview only)'}")
    print(f"Archive: {'Yes' if archive else 'No (permanent delete)'}")
    print(f"Stage 2 (External): {'Yes' if process_external else 'No (use --external)'}")
    print()
    print(f"Reference Point: {last_activity_str} (last git commit)")
    print("  -> Files are aged relative to last project activity,")
    print("    NOT from today's calendar date.")
    print()

    # Print retention policy
    print("Retention Policy:")
    print("  [Stage 1] In-project -> _archived/")
    for folder, days in RETENTION_POLICY.items():
        policy = "PERMANENT" if days == 0 else f"{days} days"
        print(f"    - {folder}/: {policy}")
    print(f"  [Stage 2] _archived/ -> {external_archive}")
    print(f"    - Grace period: {ARCHIVE_GRACE_DAYS} days -> External archive")
    print()

    results = {
        "deleted": [],
        "skipped": [],
        "permanent": [],
        "valid": [],
        "expired": [],  # (filepath, folder_name) tuples for confirmation
    }

    total_expired = 0
    total_size_bytes = 0

    for folder_name, retention_days in RETENTION_POLICY.items():
        folder_path = claudedocs / folder_name

        if not folder_path.exists():
            if verbose:
                print(f"[SKIP] {folder_name}/ - folder does not exist")
            continue

        files = scan_folder(folder_path, retention_days, last_activity)

        if not files:
            if verbose:
                print(f"[EMPTY] {folder_name}/ - no .md files")
            continue

        print(f"\n[{folder_name}/] ({len(files)} files)")

        for filepath, age_days, status in files:
            size_bytes = filepath.stat().st_size
            size_kb = size_bytes / 1024

            if status == "permanent":
                if verbose:
                    print(f"  [PERMANENT] {filepath.name} ({age_days}d old, {size_kb:.1f}KB)")
                results["permanent"].append(filepath)

            elif status == "expired":
                print(f"  [EXPIRED] {filepath.name} ({age_days}d old > {retention_days}d, {size_kb:.1f}KB)")
                total_expired += 1
                total_size_bytes += size_bytes
                # Store for later processing after confirmation
                results["expired"].append((filepath, folder_name))
                results["skipped"].append(filepath)

            else:  # valid
                if verbose:
                    remaining = retention_days - age_days
                    print(f"  [VALID] {filepath.name} ({age_days}d old, {remaining}d remaining)")
                results["valid"].append(filepath)

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Expired files found: {total_expired}")
    print(f"Total size: {total_size_bytes / 1024:.1f} KB")
    print(f"Permanent files: {len(results['permanent'])}")
    print(f"Valid files: {len(results['valid'])}")

    # Interactive confirmation flow
    if total_expired > 0 and execute:
        print()
        print("=" * 60)
        print("FILES TO BE PROCESSED")
        print("=" * 60)

        # Group by folder for clear display
        by_folder: Dict[str, List[Path]] = {}
        for filepath, folder_name in results["expired"]:
            if folder_name not in by_folder:
                by_folder[folder_name] = []
            by_folder[folder_name].append(filepath)

        for folder_name, files in by_folder.items():
            print(f"\n{folder_name}/ ({len(files)} files):")
            for f in files:
                size_kb = f.stat().st_size / 1024
                print(f"  - {f.name} ({size_kb:.1f}KB)")

        print()
        action = "archived to _archived/" if archive else "PERMANENTLY DELETED"
        print(f"Action: These {total_expired} file(s) will be {action}")
        print()

        # User confirmation (skip if auto_confirm)
        if auto_confirm:
            confirm = "y"
            print("[AUTO] Skipping confirmation (--yes flag)")
        else:
            try:
                confirm = input("Proceed? [y/N/list]: ").strip().lower()
            except EOFError:
                confirm = ""

            if confirm == "list":
                # Show full paths
                print("\nFull paths:")
                for filepath, _ in results["expired"]:
                    print(f"  {filepath}")
                try:
                    confirm = input("\nProceed? [y/N]: ").strip().lower()
                except EOFError:
                    confirm = ""

        if confirm in ("y", "yes"):
            print()
            print("Processing...")

            for filepath, folder_name in results["expired"]:
                try:
                    if archive:
                        archive_dir = claudedocs / ARCHIVE_FOLDER / folder_name
                        archive_dir.mkdir(parents=True, exist_ok=True)
                        archive_path = archive_dir / filepath.name
                        filepath.rename(archive_path)
                        print(f"  [ARCHIVED] {filepath.name} -> {archive_path.relative_to(claudedocs)}")
                    else:
                        filepath.unlink()
                        print(f"  [DELETED] {filepath.name}")

                    results["deleted"].append(filepath)
                    results["skipped"].remove(filepath)
                except Exception as e:
                    print(f"  [ERROR] {filepath.name}: {e}")

            print()
            print(f"Completed: {len(results['deleted'])} file(s) {'archived' if archive else 'deleted'}")
        else:
            print()
            print("[CANCELLED] No files were modified.")

    elif total_expired > 0:
        print()
        print("[PREVIEW] No files were modified.")
        print("Run with --execute to process expired files (with confirmation).")

    elif total_expired == 0:
        print()
        print("[OK] No Stage 1 expired files found.")

    # ========================================
    # STAGE 2: In-project archive -> External archive
    # ========================================
    if process_external:
        print()
        print("=" * 60)
        print("STAGE 2: External Archive Processing")
        print("=" * 60)
        print(f"Scanning: {claudedocs / ARCHIVE_FOLDER}")
        print(f"Destination: {external_archive}")
        print()

        archive_files = scan_internal_archive(claudedocs, last_activity)
        archive_expired = [(f, age, stat) for f, age, stat in archive_files if stat == "archive_expired"]
        archive_valid = [(f, age, stat) for f, age, stat in archive_files if stat == "archive_valid"]

        if verbose:
            for filepath, age_days, status in archive_valid:
                remaining = ARCHIVE_GRACE_DAYS - age_days
                print(f"  [VALID] {filepath.name} ({age_days}d old, {remaining}d until external)")

        total_archive_expired = len(archive_expired)
        archive_size_bytes = sum(f.stat().st_size for f, _, _ in archive_expired)

        for filepath, age_days, status in archive_expired:
            size_kb = filepath.stat().st_size / 1024
            print(f"  [EXTERNAL] {filepath.name} ({age_days}d > {ARCHIVE_GRACE_DAYS}d grace, {size_kb:.1f}KB)")

        print()
        print(f"Archive files to move: {total_archive_expired}")
        print(f"Total size: {archive_size_bytes / 1024:.1f} KB")
        print(f"Still in grace period: {len(archive_valid)}")

        if total_archive_expired > 0 and execute:
            print()

            # User confirmation for Stage 2
            if auto_confirm:
                confirm2 = "y"
                print("[AUTO] Skipping confirmation (--yes flag)")
            else:
                try:
                    confirm2 = input(f"Move {total_archive_expired} file(s) to external archive? [y/N]: ").strip().lower()
                except EOFError:
                    confirm2 = ""

            if confirm2 in ("y", "yes"):
                print()
                print("Processing Stage 2...")

                # Ensure D: drive exists
                if not EXTERNAL_ARCHIVE_ROOT.parent.exists():
                    print(f"  [ERROR] Drive not found: {EXTERNAL_ARCHIVE_ROOT.parent}")
                else:
                    moved_files = []  # Track for INDEX.md

                    for filepath, age_days, status in archive_expired:
                        try:
                            # Determine subfolder (worklog, analysis, etc.)
                            subfolder = filepath.parent.name  # e.g., "worklog" from _archived/worklog/
                            dest_dir = external_archive / subfolder
                            dest_dir.mkdir(parents=True, exist_ok=True)
                            dest_path = dest_dir / filepath.name

                            filepath.rename(dest_path)
                            print(f"  [MOVED] {filepath.name} -> {dest_path}")
                            results["deleted"].append(filepath)
                            moved_files.append((dest_path, subfolder))
                        except Exception as e:
                            print(f"  [ERROR] {filepath.name}: {e}")

                    # Update INDEX.md for future reference
                    if moved_files:
                        update_archive_index(external_archive, moved_files)

                    print()
                    print(f"Stage 2 completed: {len(moved_files)} file(s) moved to external archive")
            else:
                print()
                print("[CANCELLED] Stage 2 not executed.")

        elif total_archive_expired > 0:
            print()
            print("[PREVIEW] Stage 2 files identified but not moved.")
            print("Run with --execute --external to move to external archive.")

        else:
            print()
            print("[OK] No Stage 2 files ready for external archive.")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Clean up claudedocs/ based on 2-stage retention policy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview what would be cleaned (Stage 1 only)
  python scripts/cleanup_claudedocs.py --verbose

  # Execute Stage 1 cleanup (move expired -> _archived/)
  python scripts/cleanup_claudedocs.py --execute

  # Execute both Stage 1 and Stage 2 (move to D: drive)
  python scripts/cleanup_claudedocs.py --execute --external

  # Automated/CI mode (no prompts)
  python scripts/cleanup_claudedocs.py --execute --external --yes
""",
    )
    parser.add_argument(
        "--execute", action="store_true", help="Process expired files (shows summary and asks for confirmation)"
    )
    parser.add_argument("--external", "-e", action="store_true", help="Also process Stage 2 (move archived files to D: drive)")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt (for automation/CI)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all files, not just expired ones")
    parser.add_argument("--no-archive", action="store_true", help="Permanently delete instead of archiving (use with caution)")

    args = parser.parse_args()

    cleanup_claudedocs(
        execute=args.execute,
        verbose=args.verbose,
        archive=not args.no_archive,
        auto_confirm=args.yes,
        process_external=args.external,
    )


if __name__ == "__main__":
    main()
