"""
Obsidian Task Files Cleanup Script

DELETES meaningless timestamp-format files:
- YYYY-MM-DD_HHMMSS_*.md (timestamp format)
- YYYY-MM-DD_task_*.md (UUID task format)
- Event- *.md (backup events)

KEEPS meaningful commit-message format files:
- feat(*)- *.md
- fix(*)- *.md / fix- *.md
- refactor(*)- *.md
- docs(*)- *.md
- *-Daily-Summary-Consolidated.md
- Multi-Agent-*.md
"""

import argparse
import os
import re
from pathlib import Path

# Obsidian vault path from environment or user home fallback
OBSIDIAN_VAULT = os.getenv("OBSIDIAN_VAULT_PATH") or str(Path.home() / "Documents" / "Obsidian Vault")

DEV_LOG_DIR = Path(OBSIDIAN_VAULT) / "개발일지"

# Patterns to DELETE (meaningless files)
DELETE_PATTERNS = [
    r"^\d{4}-\d{2}-\d{2}_\d{6}_.*\.md$",  # YYYY-MM-DD_HHMMSS_*.md
    r"^\d{4}-\d{2}-\d{2}_task_[a-f0-9-]+\.md$",  # YYYY-MM-DD_task_UUID.md
    r"^Event-.*\.md$",  # Event- *.md
]

# Patterns to KEEP (meaningful files)
KEEP_PATTERNS = [
    r"^feat\(.*\)-.*\.md$",  # feat(*)- *.md
    r"^fix\(.*\)-.*\.md$",  # fix(*)- *.md
    r"^fix-.*\.md$",  # fix- *.md
    r"^refactor\(.*\)-.*\.md$",  # refactor(*)- *.md
    r"^docs\(.*\)-.*\.md$",  # docs(*)- *.md
    r"^docs-.*\.md$",  # docs- *.md
    r"^test\(.*\)-.*\.md$",  # test(*)- *.md
    r"^archive\(.*\)-.*\.md$",  # archive(*)- *.md (kanban archive)
    r"^.*-Daily-Summary-Consolidated\.md$",  # Daily summaries
    r"^Multi-Agent-.*\.md$",  # Multi-Agent files
]


def should_delete(filename: str) -> bool:
    """Check if file should be deleted."""
    # First check if it matches KEEP patterns
    for pattern in KEEP_PATTERNS:
        if re.match(pattern, filename):
            return False

    # Then check if it matches DELETE patterns
    for pattern in DELETE_PATTERNS:
        if re.match(pattern, filename):
            return True

    return False


def cleanup_folder(folder_path: Path, dry_run: bool = True) -> tuple:
    """Clean up a single folder. Returns (deleted_count, kept_count)."""
    if not folder_path.exists():
        return 0, 0

    deleted = 0
    kept = 0

    for item in folder_path.iterdir():
        if item.is_file() and item.suffix == ".md":
            if should_delete(item.name):
                if dry_run:
                    print(f"  [DELETE] {item.name}")
                else:
                    item.unlink()
                    print(f"  [DELETED] {item.name}")
                deleted += 1
            else:
                print(f"  [KEEP] {item.name}")
                kept += 1

    return deleted, kept


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Cleanup Obsidian task files")
    parser.add_argument("--execute", action="store_true", help="Actually delete files (default: dry run)")
    parser.add_argument("--month", type=str, default="2025-12", help="Month to clean (format: YYYY-MM)")
    args = parser.parse_args()

    dry_run = not args.execute

    print("=" * 70)
    if dry_run:
        print("DRY RUN MODE - No files will be deleted")
        print("Use --execute to actually delete files")
    else:
        print("EXECUTE MODE - Files will be permanently deleted!")
    print("=" * 70)
    print(f"\n[INFO] Working directory: {DEV_LOG_DIR}")
    print(f"[INFO] Target month: {args.month}\n")

    total_deleted = 0
    total_kept = 0

    # Find all date folders for the specified month
    if DEV_LOG_DIR.exists():
        for folder in sorted(DEV_LOG_DIR.iterdir()):
            if folder.is_dir() and folder.name.startswith(args.month):
                print(f"\n[{folder.name}]")
                deleted, kept = cleanup_folder(folder, dry_run)
                total_deleted += deleted
                total_kept += kept
    else:
        print(f"[ERROR] Devlog directory not found: {DEV_LOG_DIR}")
        return

    print("\n" + "=" * 70)
    print(f"SUMMARY: {total_deleted} files to delete, {total_kept} files to keep")
    if dry_run:
        print("Run with --execute to delete these files")
    else:
        print(f"Successfully deleted {total_deleted} files")
    print("=" * 70)


if __name__ == "__main__":
    main()
