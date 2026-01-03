#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Emoji Detection for Staged Files
Checks only files that are staged for commit (git diff --cached)
"""

import re
import subprocess
import sys


def get_staged_python_files():
    """Get list of staged Python files"""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"], capture_output=True, text=True, check=True
        )
        files = result.stdout.strip().split("\n")
        # Filter only Python files
        py_files = [f for f in files if f.endswith(".py") and f]
        return py_files
    except subprocess.CalledProcessError:
        return []


def check_emoji_in_file(file_path):
    """Check for emoji in a single file"""
    # Comprehensive emoji pattern
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "\u2600-\u26FF"  # misc symbols (warning, checkmark, etc)
        "]+",
        flags=re.UNICODE,
    )

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        matches = emoji_pattern.findall(content)
        if matches:
            lines_with_emoji = []
            for line_num, line in enumerate(content.split("\n"), 1):
                if emoji_pattern.search(line):
                    lines_with_emoji.append(line_num)
            return lines_with_emoji
        return []
    except Exception as e:
        print(f"[WARN] Cannot read {file_path}: {e}")
        return []


def main():
    """Main function"""
    staged_files = get_staged_python_files()

    if not staged_files:
        # No Python files staged
        return 0

    print(f"[INFO] Checking {len(staged_files)} staged Python file(s)...")

    files_with_emoji = []

    for file_path in staged_files:
        lines = check_emoji_in_file(file_path)
        if lines:
            files_with_emoji.append({"file": file_path, "lines": lines})

    if not files_with_emoji:
        print("[OK] No emoji found in staged files")
        return 0

    # Report files with emoji
    print(f"\n[FAIL] Found emoji in {len(files_with_emoji)} file(s):\n")

    for file_info in files_with_emoji:
        print(f"  File: {file_info['file']}")
        line_count = len(file_info["lines"])
        print(f"    Lines with emoji: {line_count}")
        if line_count <= 5:
            print(f"    Line numbers: {', '.join(map(str, file_info['lines']))}")
        else:
            print(f"    Line numbers: {', '.join(map(str, file_info['lines'][:5]))} (and {line_count - 5} more)")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
