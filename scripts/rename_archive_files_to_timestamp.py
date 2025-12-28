"""
Rename existing UUID-based archive files to timestamp format

Converts:
  FROM: 2025-12-25_task_82fa87c4-7ba0-4328-9ab6-8026175cbfc0.md
  TO:   2025-12-25_143052_Implement-user-authentication.md

Extracts:
  - Title from file content (frontmatter or first heading)
  - Timestamp from file modification time
"""

import os
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Obsidian vault path
OBSIDIAN_VAULT = os.getenv(
    "OBSIDIAN_VAULT_PATH",
    r"C:\Users\user\Documents\Obsidian Vault"
)

DEV_LOG_DIR = Path(OBSIDIAN_VAULT) / "개발일지"


def extract_title_from_file(file_path: Path) -> str:
    """
    Extract task title from Obsidian note content.

    Tries:
    1. YAML frontmatter 'topic' field
    2. First markdown heading (# Title)
    3. Filename as fallback
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Try YAML frontmatter: topic: XXX
        frontmatter_match = re.search(r'^topic:\s*(.+)$', content, re.MULTILINE)
        if frontmatter_match:
            return frontmatter_match.group(1).strip()

        # Try first markdown heading: # Title
        heading_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if heading_match:
            return heading_match.group(1).strip()

        # Fallback: use filename
        return file_path.stem

    except Exception as e:
        print(f"   [WARN] Could not read {file_path.name}: {e}")
        return file_path.stem


def sanitize_title_for_filename(title: str) -> str:
    """Sanitize title for use in filename"""
    # Remove special characters
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', title)
    # Replace spaces with hyphens
    safe = re.sub(r'\s+', '-', safe.strip())
    # Limit length
    return safe[:80]


def find_uuid_files() -> dict:
    """
    Find all UUID-based archive files.

    Pattern: YYYY-MM-DD_task_<uuid>.md

    Returns:
        dict mapping date -> list of (file_path, uuid) tuples
    """
    uuid_files = defaultdict(list)

    if not DEV_LOG_DIR.exists():
        print(f"[ERROR] Directory not found: {DEV_LOG_DIR}")
        return {}

    # Pattern: YYYY-MM-DD_task_<uuid>.md
    pattern = re.compile(r"^(\d{4}-\d{2}-\d{2})_task_([a-f0-9\-]+)\.md$")

    # Search in date folders
    for date_dir in DEV_LOG_DIR.iterdir():
        if date_dir.is_dir() and re.match(r"\d{4}-\d{2}-\d{2}", date_dir.name):
            for file_path in date_dir.iterdir():
                if file_path.is_file():
                    match = pattern.match(file_path.name)
                    if match:
                        date_str = match.group(1)
                        uuid = match.group(2)
                        uuid_files[date_str].append((file_path, uuid))

    return uuid_files


def rename_files(dry_run: bool = True) -> dict:
    """
    Rename UUID files to timestamp format.

    Args:
        dry_run: If True, only show what would be renamed

    Returns:
        dict with statistics
    """
    uuid_files = find_uuid_files()

    if not uuid_files:
        print("[OK] No UUID-based files found!")
        return {"renamed": 0, "errors": [], "skipped": 0}

    stats = {"renamed": 0, "errors": [], "skipped": 0}

    total_files = sum(len(files) for files in uuid_files.values())
    print(f"\n[INFO] Found {total_files} UUID-based files across {len(uuid_files)} dates\n")

    # Track used filenames to handle collisions
    used_filenames = set()

    for date_str, files in sorted(uuid_files.items()):
        print(f"[DATE] {date_str}: {len(files)} files")

        for file_path, uuid in files:
            try:
                # Extract title from file content
                title = extract_title_from_file(file_path)
                safe_title = sanitize_title_for_filename(title)

                # Get file modification time for timestamp
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                time_str = mtime.strftime('%H%M%S')

                # Base filename: YYYY-MM-DD_HHMMSS_Title.md
                base_filename = f"{date_str}_{time_str}_{safe_title}"
                new_filename = f"{base_filename}.md"
                new_path = file_path.parent / new_filename

                # Handle collisions by adding counter suffix
                counter = 2
                while new_filename in used_filenames or (new_path.exists() and new_path != file_path):
                    new_filename = f"{base_filename}-{counter}.md"
                    new_path = file_path.parent / new_filename
                    counter += 1

                # Track this filename as used
                used_filenames.add(new_filename)

                if dry_run:
                    print(f"   [DRY RUN] Would rename:")
                    print(f"      FROM: {file_path.name}")
                    print(f"      TO:   {new_filename}")
                    stats["renamed"] += 1  # Count for dry run
                else:
                    file_path.rename(new_path)
                    print(f"   [OK] Renamed:")
                    print(f"      FROM: {file_path.name}")
                    print(f"      TO:   {new_filename}")
                    stats["renamed"] += 1

            except Exception as e:
                error_msg = f"Failed to rename {file_path.name}: {str(e)}"
                print(f"   [ERROR] {error_msg}")
                stats["errors"].append(error_msg)

        print()  # Blank line between dates

    return stats


def main():
    """Main execution function"""
    import sys

    # Check for --execute flag (non-interactive mode)
    execute_mode = "--execute" in sys.argv or "-e" in sys.argv

    print("=" * 70)
    print("Rename UUID Archive Files to Timestamp Format")
    print("=" * 70)
    print(f"\n[INFO] Working directory: {DEV_LOG_DIR}\n")

    # First, dry run to show what would be renamed
    print("[DRY RUN] Checking files to rename...\n")
    stats_dry = rename_files(dry_run=True)

    # Ask for confirmation
    print("\n" + "=" * 70)
    total = stats_dry["renamed"] + stats_dry["skipped"]
    print(f"\n[SUMMARY] Found {total} files")
    print(f"  - Would rename: {stats_dry['renamed']}")
    print(f"  - Would skip (target exists): {stats_dry['skipped']}")
    print(f"  - Errors: {len(stats_dry['errors'])}")

    if stats_dry["errors"]:
        print("\n[ERRORS]:")
        for error in stats_dry["errors"][:5]:  # Show first 5 errors
            print(f"  - {error}")
        if len(stats_dry["errors"]) > 5:
            print(f"  ... and {len(stats_dry['errors']) - 5} more errors")

    # Non-interactive mode: proceed without confirmation
    if execute_mode:
        print("\n[AUTO] --execute flag detected, proceeding without confirmation...")
    else:
        try:
            response = input("\n[CONFIRM] Proceed with renaming? (yes/no): ").strip().lower()
            if response != "yes":
                print("\n[CANCELLED] Operation cancelled.")
                return
        except EOFError:
            print("\n[INFO] No interactive input available. Use --execute flag for non-interactive mode.")
            return

    # Perform actual rename
    print("\n[STARTING] Renaming files...\n")
    stats = rename_files(dry_run=False)

    # Final report
    print("\n" + "=" * 70)
    print("[COMPLETE] RENAME COMPLETE")
    print("=" * 70)
    print(f"\n[STATS] Statistics:")
    print(f"   - Files renamed: {stats['renamed']}")
    print(f"   - Files skipped: {stats['skipped']}")
    print(f"   - Errors: {len(stats['errors'])}")

    if stats["errors"]:
        print("\n[ERRORS] Errors encountered:")
        for error in stats["errors"]:
            print(f"   - {error}")

    print("\n[SUCCESS] All UUID files have been renamed to timestamp format!")
    print(f"   Format: YYYY-MM-DD_HHMMSS_TaskTitle.md")


if __name__ == "__main__":
    main()
