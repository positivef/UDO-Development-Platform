#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Safe Emoji Replacement Script

Verifies that Korean text is preserved while emoji are replaced.
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from replace_emoji_safe import (  # noqa: E402
    is_korean_char,
    is_safe_char,
    replace_emoji_in_text,
)


def test_is_korean_char():
    """Test Korean character detection"""
    # Hangul Syllables
    assert is_korean_char("가") is True
    assert is_korean_char("개") is True
    assert is_korean_char("발") is True
    assert is_korean_char("일") is True
    assert is_korean_char("지") is True
    assert is_korean_char("한") is True
    assert is_korean_char("글") is True

    # Hangul Compatibility Jamo
    assert is_korean_char("ㄱ") is True
    assert is_korean_char("ㅏ") is True

    # NOT Korean
    assert is_korean_char("a") is False
    assert is_korean_char("A") is False
    assert is_korean_char("1") is False
    assert is_korean_char("[OK]") is False
    assert is_korean_char("[*]") is False
    assert is_korean_char("日") is False  # Japanese/Chinese

    print("[OK] test_is_korean_char passed")


def test_is_safe_char():
    """Test safe character detection"""
    # ASCII
    assert is_safe_char("a") is True
    assert is_safe_char("Z") is True
    assert is_safe_char("0") is True
    assert is_safe_char(" ") is True
    assert is_safe_char("\n") is True

    # Korean
    assert is_safe_char("개") is True
    assert is_safe_char("발") is True
    assert is_safe_char("일") is True
    assert is_safe_char("지") is True

    # CJK/Japanese
    assert is_safe_char("日") is True
    assert is_safe_char("本") is True
    assert is_safe_char("発") is True

    # Emoji (NOT safe, should be replaced)
    assert is_safe_char("[OK]") is False
    assert is_safe_char("[*]") is False
    assert is_safe_char("[FAIL]") is False

    print("[OK] test_is_safe_char passed")


def test_korean_text_preservation():
    """CRITICAL: Test that Korean text is preserved"""
    test_cases = [
        # (input, expected_output, description)
        ("개발일지", "개발일지", "Folder name"),
        ("자동으로 분석", "자동으로 분석", "Korean sentence"),
        ("트리거 조건", "트리거 조건", "Technical term"),
        ("시간대별 작업", "시간대별 작업", "Work description"),
        ("[OK] 테스트 통과", "[OK] 테스트 통과", "Emoji + Korean"),
        ("[*] 프로젝트 시작", "[ROCKET] 프로젝트 시작", "Emoji + Korean"),
        ("개발일지/2025-12-25/", "개발일지/2025-12-25/", "Path with Korean"),
        ("AI 인사이트 자동 생성", "AI 인사이트 자동 생성", "Mixed text"),
    ]

    for input_text, expected, description in test_cases:
        result, changes = replace_emoji_in_text(input_text)
        assert result == expected, f"FAILED: {description}\n  Input: {input_text}\n  Expected: {expected}\n  Got: {result}"
        print(f"[OK] {description}: '{input_text}' -> '{result}'")

    print("[OK] test_korean_text_preservation passed")


def test_emoji_replacement():
    """Test that emoji are correctly replaced"""
    test_cases = [
        ("[OK] Success", "[OK] Success", "Check mark"),
        ("[FAIL] Failed", "[FAIL] Failed", "Cross mark"),
        ("[WARN] Warning", "[WARN] Warning", "Warning sign"),
        ("[*] Launch", "[ROCKET] Launch", "Rocket"),
        ("[*] Fix", "[TOOL] Fix", "Wrench"),
        ("-> Arrow", "-> Arrow", "Arrow"),
    ]

    for input_text, expected, description in test_cases:
        result, changes = replace_emoji_in_text(input_text)
        assert result == expected, f"FAILED: {description}\n  Expected: {expected}\n  Got: {result}"
        print(f"[OK] {description}: '{input_text}' -> '{result}'")

    print("[OK] test_emoji_replacement passed")


def test_mixed_content():
    """Test mixed Korean + emoji content"""
    test_cases = [
        ("[OK] 개발일지 생성 완료 [*]", "[OK] 개발일지 생성 완료 [ROCKET]", "Start/end emoji with Korean"),
        ("트리거 [OK] 조건 [*] 자동", "트리거 [OK] 조건 [TOOL] 자동", "Interspersed emoji/Korean"),
        ("# [OK] 완료\n## [*] 시작\n개발일지", "# [OK] 완료\n## [ROCKET] 시작\n개발일지", "Markdown with Korean"),
    ]

    for input_text, expected, description in test_cases:
        result, changes = replace_emoji_in_text(input_text)
        assert result == expected, f"FAILED: {description}\n  Expected: {expected}\n  Got: {result}"
        print(f"[OK] {description}")

    print("[OK] test_mixed_content passed")


def test_no_replacement_needed():
    """Test that pure Korean/ASCII text is unchanged"""
    test_cases = [
        "개발일지",
        "자동으로 Git commit 정보를 분석하여 Obsidian 개발일지를 생성합니다.",
        "Hello World",
        "print('Hello')",
        "def create_dev_log():",
    ]

    for input_text in test_cases:
        result, changes = replace_emoji_in_text(input_text)
        assert result == input_text, f"FAILED: Text was modified unexpectedly\n  Input: {input_text}\n  Got: {result}"
        assert len(changes) == 0, f"FAILED: Changes reported but shouldn't be\n  Input: {input_text}\n  Changes: {changes}"

    print("[OK] test_no_replacement_needed passed")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Testing Safe Emoji Replacement (Korean Preservation)")
    print("=" * 60 + "\n")

    tests = [
        test_is_korean_char,
        test_is_safe_char,
        test_korean_text_preservation,
        test_emoji_replacement,
        test_mixed_content,
        test_no_replacement_needed,
    ]

    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    if failed == 0:
        print("[SUCCESS] All tests passed! [OK]")
        print("Korean text preservation: VERIFIED")
        return 0
    else:
        print(f"[FAILURE] {failed} test(s) failed [FAIL]")
        return 1


if __name__ == "__main__":
    exit(main())
