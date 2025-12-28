#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korean Preservation Check (Pre-commit Hook)

Checks that Korean text has not been accidentally replaced with [EMOJI] placeholders.
This prevents the same issue that broke obsidian_auto_sync.py from happening again.

Usage:
  python scripts/check_korean_preservation.py
  python scripts/check_korean_preservation.py --all  # Check all files, not just staged

Exit codes:
  0 - All checks passed
  1 - [EMOJI] placeholders found (critical error)
  2 - Warnings found (can proceed with caution)
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def get_staged_python_files() -> List[Path]:
    """Get list of staged Python files from git"""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            check=True,
        )
        files = [
            Path(f) for f in result.stdout.strip().split('\n')
            if f and f.endswith('.py')
        ]
        return files
    except subprocess.CalledProcessError:
        return []


def get_all_python_files() -> List[Path]:
    """Get all Python files in the repository"""
    base_path = Path(".")
    files = []
    for dir_name in ["backend", "src", "scripts", "tests"]:
        dir_path = base_path / dir_name
        if dir_path.exists():
            for py_file in dir_path.rglob("*.py"):
                if ".venv" not in str(py_file) and "node_modules" not in str(py_file):
                    files.append(py_file)
    return files


def check_file_for_emoji_placeholders(file_path: Path) -> Tuple[bool, List[int], List[str]]:
    """
    Check if a file contains [EMOJI] placeholders.

    Returns:
        (has_placeholders, line_numbers, sample_lines)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        line_numbers = []
        sample_lines = []

        for i, line in enumerate(lines, 1):
            if "[EMOJI]" in line:
                line_numbers.append(i)
                # Store sample (first 5 occurrences)
                if len(sample_lines) < 5:
                    sample_lines.append(f"  Line {i}: {line.strip()[:80]}")

        return len(line_numbers) > 0, line_numbers, sample_lines

    except Exception as e:
        print(f"[WARN] Could not read {file_path}: {e}")
        return False, [], []


def check_file_for_critical_korean_paths(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Check if a file contains critical Korean folder paths like "개발일지".

    These paths MUST contain Korean text, not [EMOJI].

    Returns:
        (is_correct, warnings)
    """
    critical_paths = [
        ("개발일지", "dev_log_dir", "Obsidian development log folder"),
        ("분석", "analysis", "Analysis folder"),
        ("결정", "decisions", "Decisions folder"),
    ]

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        warnings = []

        for korean_name, var_name, description in critical_paths:
            # Check if the file should have this path
            if var_name in content or description.lower() in file_path.name.lower():
                # Make sure it has Korean text, not [EMOJI]
                if korean_name not in content and "[EMOJI]" in content:
                    warnings.append(
                        f"  [WARN] {file_path}: Missing '{korean_name}' but has [EMOJI] - "
                        f"Korean text may have been replaced!"
                    )

        return len(warnings) == 0, warnings

    except Exception as e:
        return True, []  # If we can't read, don't fail


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Check for Korean text preservation")
    parser.add_argument("--all", action="store_true", help="Check all files instead of just staged")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("[SAFETY CHECK] Korean Text Preservation Verification")
    print("="*60 + "\n")

    # Get files to check
    if args.all:
        files = get_all_python_files()
        print(f"[INFO] Checking all Python files ({len(files)} files)...")
    else:
        files = get_staged_python_files()
        if not files:
            print("[OK] No Python files staged for commit")
            return 0
        print(f"[INFO] Checking {len(files)} staged Python file(s)...")

    # Check each file
    files_with_emoji = []
    files_with_warnings = []

    for file_path in files:
        # Check for [EMOJI] placeholders
        has_emoji, line_numbers, sample_lines = check_file_for_emoji_placeholders(file_path)

        if has_emoji:
            files_with_emoji.append((file_path, line_numbers, sample_lines))

        # Check for critical Korean paths
        is_correct, warnings = check_file_for_critical_korean_paths(file_path)

        if not is_correct:
            files_with_warnings.extend(warnings)

    # Report results
    print("\n" + "="*60)

    if files_with_emoji:
        print("[CRITICAL ERROR] [EMOJI] placeholders found!\n")
        print("The following files contain [EMOJI] instead of Korean text:")
        print("This indicates Korean characters were mistakenly replaced.\n")

        for file_path, line_numbers, sample_lines in files_with_emoji:
            print(f"[FAIL] {file_path}")
            print(f"  Found [EMOJI] on {len(line_numbers)} line(s): {line_numbers[:10]}")
            if len(line_numbers) > 10:
                print(f"  ... and {len(line_numbers) - 10} more lines")
            print("\n  Sample occurrences:")
            for sample in sample_lines:
                print(sample)
            print()

        print("[ACTION REQUIRED]")
        print("1. Review the files listed above")
        print("2. Restore Korean text from backup (.bak files)")
        print("3. OR restore from git: git show HEAD:<file> > <file>")
        print("\n[ERROR] Commit blocked to prevent Korean text loss")
        return 1

    if files_with_warnings:
        print("[WARNING] Potential Korean text issues detected:\n")
        for warning in files_with_warnings:
            print(warning)
        print("\n[WARN] Please review these files carefully")
        print("[INFO] Proceeding with commit (non-blocking warning)")
        return 2

    print("[SUCCESS] All Korean text preservation checks passed!")
    print("[OK] No [EMOJI] placeholders found")
    print("[OK] Critical Korean paths verified")
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
