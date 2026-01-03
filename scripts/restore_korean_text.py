#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Restore Korean Text from Git History

Restores files that had Korean text replaced with [*] placeholders.
Uses git history to get the last good version (before commit 648966c).

Usage:
  python scripts/restore_korean_text.py --dry-run  # Preview only
  python scripts/restore_korean_text.py --execute  # Actually restore

Safe Restoration Strategy:
1. Identify files with [*] placeholders
2. For each file, get version from commit 1b2076d (before damage)
3. Verify the restored version has Korean text
4. Create backup of current version (.damaged)
5. Restore the good version

Exit codes:
  0 - All files restored successfully
  1 - Some files could not be restored
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


# Commit before the damage
GOOD_COMMIT = "1b2076d"  # Last commit before 648966c


def has_korean_text(text: str) -> bool:
    """Check if text contains Korean characters"""
    for char in text:
        code = ord(char)
        if (
            0xAC00 <= code <= 0xD7AF or 0x1100 <= code <= 0x11FF or 0x3130 <= code <= 0x318F  # Hangul Syllables  # Hangul Jamo
        ):  # Hangul Compatibility Jamo
            return True
    return False


def get_file_from_commit(file_path: Path, commit: str) -> Tuple[bool, str]:
    """
    Get file content from a specific git commit.

    Returns:
        (success, content)
    """
    try:
        # Convert Windows path to Unix-style for git
        git_path = str(file_path).replace("\\", "/")

        result = subprocess.run(
            ["git", "show", f"{commit}:{git_path}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Error: {e.stderr}"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def restore_file(file_path: Path, dry_run: bool = True) -> Tuple[bool, str]:
    """
    Restore a single file from git history.

    Returns:
        (success, message)
    """
    # Read current content
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            current_content = f.read()
    except Exception as e:
        return False, f"Cannot read current file: {e}"

    # Check if it has [*]
    if "[*]" not in current_content:
        return True, "No [*] found, skipping"

    # Get content from good commit
    success, restored_content = get_file_from_commit(file_path, GOOD_COMMIT)

    if not success:
        return False, f"Cannot get from git: {restored_content}"

    # Verify restored version has Korean text
    if not has_korean_text(restored_content):
        return False, "Restored version has no Korean text (suspicious)"

    # Count how many [*] will be fixed
    emoji_count = current_content.count("[*]")

    if dry_run:
        return True, f"Would restore (fixes {emoji_count} [*] occurrences)"

    # Actually restore
    try:
        # Backup current damaged version
        damaged_path = file_path.with_suffix(file_path.suffix + ".damaged")
        with open(damaged_path, "w", encoding="utf-8") as f:
            f.write(current_content)

        # Write restored version
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(restored_content)

        return True, f"Restored (fixed {emoji_count} [*], backup: {damaged_path.name})"

    except Exception as e:
        return False, f"Failed to write: {e}"


def get_damaged_files() -> List[Path]:
    """Get list of files with [*] placeholders"""
    damaged = []

    for dir_name in ["backend", "src", "scripts", "tests"]:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            continue

        for py_file in dir_path.rglob("*.py"):
            if ".venv" in str(py_file) or "node_modules" in str(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    if "[*]" in f.read():
                        damaged.append(py_file)
            except Exception:
                pass

    return damaged


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Restore Korean text from git history")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, don't actually restore")
    parser.add_argument("--execute", action="store_true", help="Actually restore files")
    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("[ERROR] Must specify either --dry-run or --execute")
        print("Usage: python scripts/restore_korean_text.py --dry-run")
        print("       python scripts/restore_korean_text.py --execute")
        return 1

    mode = "DRY RUN (preview only)" if args.dry_run else "EXECUTE (will modify files)"

    print("\n" + "=" * 60)
    print(f"[RESTORATION] Korean Text Restoration - {mode}")
    print("=" * 60)
    print(f"[INFO] Restoring from commit: {GOOD_COMMIT}")
    print("[INFO] (Before damage in commit 648966c)\n")

    # Get list of damaged files
    print("[INFO] Scanning for damaged files...")
    damaged_files = get_damaged_files()

    if not damaged_files:
        print("[OK] No damaged files found!")
        return 0

    print(f"[INFO] Found {len(damaged_files)} damaged file(s)\n")

    # Restore each file
    restored = []
    failed = []
    skipped = []

    for i, file_path in enumerate(damaged_files, 1):
        print(f"[{i}/{len(damaged_files)}] {file_path}...", end=" ")

        success, message = restore_file(file_path, dry_run=args.dry_run)

        if success:
            if "skipping" in message:
                skipped.append((file_path, message))
                print(f"[SKIP] {message}")
            else:
                restored.append((file_path, message))
                print(f"[OK] {message}")
        else:
            failed.append((file_path, message))
            print(f"[FAIL] {message}")

    # Summary
    print("\n" + "=" * 60)
    print("[SUMMARY]")
    print(f"  Restored: {len(restored)} files")
    print(f"  Skipped: {len(skipped)} files")
    print(f"  Failed: {len(failed)} files")

    if failed:
        print("\n[FAILED FILES]")
        for file_path, message in failed[:10]:
            print(f"  {file_path}: {message}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")

    if args.dry_run:
        print("\n[NEXT STEP] Run with --execute to actually restore files")
        print("  python scripts/restore_korean_text.py --execute")
    else:
        print("\n[SUCCESS] Restoration complete!")
        print("[INFO] Damaged versions backed up with .damaged extension")
        print("[INFO] Run tests to verify: python -m pytest tests/")

    return 0 if len(failed) == 0 else 1


if __name__ == "__main__":
    exit(main())
