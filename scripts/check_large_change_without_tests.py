#!/usr/bin/env python3
"""
Simple Large Change Warning Hook

5개 이상 파일 변경 시 테스트 파일이 없으면 경고.
Vibe coding flow를 방해하지 않고 인식만 시켜줌.

850줄 Adaptive Governance System 대신 30줄로 동일 효과.

Usage:
    python scripts/check_large_change_without_tests.py

Author: Claude Code
Date: 2026-01-17
"""

import subprocess
import sys

THRESHOLD = 5  # 이 이상 파일 변경 시 체크
TEST_PATTERNS = ["test_", "_test.py", ".spec.", ".test."]


def get_staged_files():
    """Get list of staged files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
    )
    return [f for f in result.stdout.strip().split("\n") if f]


def has_test_files(files):
    """Check if any file looks like a test file."""
    for f in files:
        if any(pattern in f for pattern in TEST_PATTERNS):
            return True
    return False


def main():
    staged = get_staged_files()

    if len(staged) >= THRESHOLD and not has_test_files(staged):
        print(f"\n[INFO] {len(staged)}개 파일 변경, 테스트 파일 없음")
        print("       (--no-verify로 스킵 가능)\n")
        # 경고만, 차단하지 않음 (exit 0)

    return 0


if __name__ == "__main__":
    sys.exit(main())
