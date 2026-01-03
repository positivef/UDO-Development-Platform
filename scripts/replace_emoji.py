#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Safe Emoji Replacement Script (v2.0 - Korean Preservation)

Replaces emoji characters with ASCII equivalents for Windows cp949 compatibility.
CRITICALLY PRESERVES Korean (Hangul), Chinese (CJK), and Japanese text.

Version History:
- v1.0 (2025-12-19): Original version (BUGGY - replaced Korean text)
- v2.0 (2025-12-25): Added Korean/CJK preservation logic
"""

import shutil
import unicodedata
from pathlib import Path
from typing import Dict, List, Tuple

# Emoji to ASCII mapping
EMOJI_REPLACEMENTS = {
    # Status indicators
    "\u2705": "[OK]",  # [OK]
    "\u274c": "[FAIL]",  # [FAIL]
    "\u2757": "[!]",  # [!]
    "\u2753": "[?]",  # [?]
    "\u2714": "[OK]",  # [OK]
    "\u2716": "[X]",  # [X]
    # Warnings and alerts
    "\u26a0": "[WARN]",  # [WARN]
    "\ufe0f": "",  # Variation selector (remove)
    "\u2622": "[HAZARD]",  # [HAZARD]
    "\u26d4": "[NO]",  # [NO]
    # Common symbols
    "\ud83d\udcca": "[INFO]",
    "\ud83e\uddea": "[TEST]",
    "\ud83d\udd34": "[RED]",
    "\ud83d\udfe1": "[YELLOW]",
    "\ud83d\udfe2": "[GREEN]",
    "\u2b55": "[O]",  # [O]
    "\u274e": "[X]",  # [X]
    # Development symbols
    "\ud83d\udd27": "[TOOL]",
    "\ud83d\udee0": "[BUILD]",
    "\ud83d\udc1b": "[BUG]",
    "\ud83d\ude80": "[ROCKET]",
    "\u2728": "[NEW]",  # [NEW]
    "\ud83d\udd25": "[HOT]",  # Arrows and directions
    "\u2192": "->",  # ->
    "\u2190": "<-",  # <-
    "\u2191": "^",  # ^
    "\u2193": "v",  # v
    "\u21d2": "=>",  # =>
    "\u21d0": "<=",  # <=
    # Other common
    "\u2022": "*",  # *
    "\u25cf": "*",  # *
    "\u25cb": "o",  # o
    "\u25a0": "[#]",  # [#]
    "\u25a1": "[ ]",  # [ ]
}


def is_korean_char(char: str) -> bool:
    """
    Check if a character is Korean (Hangul).

    Korean Unicode ranges:
    - AC00-D7AF: Hangul Syllables (11,172 characters) - "가" to "힣"
    - 1100-11FF: Hangul Jamo
    - 3130-318F: Hangul Compatibility Jamo - "ㄱ" to "ㅎ", "ㅏ" to "ㅣ"
    - A960-A97F: Hangul Jamo Extended-A
    - D7B0-D7FF: Hangul Jamo Extended-B

    Examples:
    - is_korean_char('가') -> True
    - is_korean_char('개') -> True
    - is_korean_char('발') -> True
    - is_korean_char('일') -> True
    - is_korean_char('지') -> True
    - is_korean_char('[OK]') -> False (emoji)
    """
    if not char:
        return False

    code = ord(char)
    return (
        0xAC00 <= code <= 0xD7AF  # Hangul Syllables
        or 0x1100 <= code <= 0x11FF  # Hangul Jamo
        or 0x3130 <= code <= 0x318F  # Hangul Compatibility Jamo
        or 0xA960 <= code <= 0xA97F  # Hangul Jamo Extended-A
        or 0xD7B0 <= code <= 0xD7FF  # Hangul Jamo Extended-B
    )


def is_safe_char(char: str) -> bool:
    """
    Check if a character should be preserved (not replaced).

    Preserves:
    - ASCII printable characters (0x20-0x7E): a-z, A-Z, 0-9, punctuation
    - Korean (Hangul) characters: All Korean text
    - CJK Unified Ideographs: Chinese characters
    - Japanese Hiragana/Katakana: Japanese text
    - Whitespace and control characters: \\n, \\r, \\t, space

    Examples:
    - is_safe_char('a') -> True (ASCII)
    - is_safe_char('개') -> True (Korean)
    - is_safe_char('発') -> True (Japanese)
    - is_safe_char('日') -> True (CJK)
    - is_safe_char('[OK]') -> False (emoji, should be replaced)
    """
    if not char:
        return True

    # ASCII printable (0x20-0x7E)
    code = ord(char)
    if 0x20 <= code <= 0x7E:
        return True

    # Korean - CRITICAL: Must preserve
    if is_korean_char(char):
        return True

    # CJK Unified Ideographs (Chinese/Japanese characters)
    if 0x4E00 <= code <= 0x9FFF:  # CJK Unified Ideographs
        return True
    if 0x3400 <= code <= 0x4DBF:  # CJK Extension A
        return True

    # Japanese Hiragana/Katakana
    if 0x3040 <= code <= 0x309F:  # Hiragana
        return True
    if 0x30A0 <= code <= 0x30FF:  # Katakana
        return True

    # Common whitespace and control characters
    if char in ["\n", "\r", "\t", " "]:
        return True

    return False


def replace_emoji_in_text(text: str) -> Tuple[str, List[str]]:
    """
    Replace emoji with ASCII equivalents while PRESERVING Korean/CJK text.

    Strategy:
    1. Replace known emoji from EMOJI_REPLACEMENTS dict
    2. For remaining characters, check each one individually
    3. PRESERVE Korean, CJK, Japanese, and ASCII characters
    4. Only replace actual emoji and problematic symbols

    Returns: (modified_text, list_of_changes)

    Example:
    >>> text = "[OK] 개발일지 생성 완료"
    >>> modified, changes = replace_emoji_in_text(text)
    >>> modified
    '[OK] 개발일지 생성 완료'  # Korean preserved!

    >>> text = "[*] 프로젝트 시작"
    >>> modified, changes = replace_emoji_in_text(text)
    >>> modified
    '[ROCKET] 프로젝트 시작'  # Korean preserved!
    """
    changes = []
    modified = text

    # Step 1: Replace known emoji with mappings
    for emoji, replacement in EMOJI_REPLACEMENTS.items():
        if emoji in modified:
            count = modified.count(emoji)
            modified = modified.replace(emoji, replacement)
            if count > 0:
                # Use unicode escape code instead of emoji character in output
                try:
                    emoji_code = emoji.encode("unicode-escape").decode("ascii")
                    changes.append(f"Replaced \\{emoji_code} with {replacement} ({count} times)")
                except Exception:
                    changes.append(f"Replaced emoji with {replacement} ({count} times)")

    # Step 2: Character-by-character check for remaining emoji
    # CRITICAL: This preserves Korean and other important characters
    result = []
    emoji_count = 0

    for char in modified:
        if is_safe_char(char):
            # PRESERVE: Korean, ASCII, CJK, Japanese, whitespace
            result.append(char)
        else:
            # Check if it's actually an emoji/symbol
            category = unicodedata.category(char)

            # Replace emoji and symbols (So=Symbol Other, Sk=Symbol Modifier)
            if category in ["So", "Sk"]:
                result.append("[*]")
                emoji_count += 1
                try:
                    if emoji_count <= 10:  # Limit logging to first 10
                        emoji_name = unicodedata.name(char, "UNKNOWN")
                        emoji_code = char.encode("unicode-escape").decode("ascii")
                        changes.append(f"Replaced \\{emoji_code} ({emoji_name}) with [*]")
                except Exception:
                    pass
            else:
                # PRESERVE: Other valid Unicode characters
                result.append(char)

    if emoji_count > 10:
        changes.append(f"... and {emoji_count - 10} more emoji")

    return "".join(result), changes


def process_file(file_path: Path, create_backup: bool = True) -> Dict:
    """
    Process a single Python file, replacing emoji while preserving Korean text.

    Returns: dict with file path, changes made, and status
    """
    result = {"file": str(file_path), "changes": [], "backup_created": False, "modified": False, "error": None}

    try:
        # Read original content
        with open(file_path, "r", encoding="utf-8") as f:
            original = f.read()

        # Replace emoji (Korean-safe)
        modified, changes = replace_emoji_in_text(original)

        # Check if anything changed
        if original == modified:
            return result

        result["modified"] = True
        result["changes"] = changes

        # Create backup if requested
        if create_backup:
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            shutil.copy2(file_path, backup_path)
            result["backup_created"] = True

        # Write modified content
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(modified)

    except Exception as e:
        result["error"] = str(e)

    return result


def main():
    """Main function"""
    print("[INFO] Starting SAFE emoji replacement (Korean preservation enabled)...")

    # Directories to process
    dirs_to_scan = ["backend", "src", "scripts", "tests"]
    base_path = Path(".")

    total_files = 0
    modified_files = []
    skipped_files = []
    error_files = []

    for dir_name in dirs_to_scan:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            continue

        for py_file in dir_path.rglob("*.py"):
            # Skip virtual environment and node_modules
            if ".venv" in str(py_file) or "node_modules" in str(py_file):
                continue

            total_files += 1
            result = process_file(py_file, create_backup=True)

            if result["error"]:
                error_files.append(result)
            elif result["modified"]:
                modified_files.append(result)
            else:
                skipped_files.append(result)

    # Report results
    print(f"\n[RESULT] Processed {total_files} Python files")
    print(f"[OK] Modified: {len(modified_files)} files")
    print(f"[OK] Unchanged: {len(skipped_files)} files")

    if error_files:
        print(f"[WARN] Errors: {len(error_files)} files")

    # Show details of modified files
    if modified_files:
        print(f"\n[CHANGES] Details of {len(modified_files)} modified files:\n")

        for result in modified_files[:20]:  # Show first 20
            print(f"File: {result['file']}")
            for change in result["changes"][:3]:  # Show first 3 changes per file
                print(f"  - {change}")
            if result["backup_created"]:
                print(f"  - Backup: {result['file']}.bak")
            print()

        if len(modified_files) > 20:
            print(f"... and {len(modified_files) - 20} more files")

    # Show errors if any
    if error_files:
        print("\n[ERROR] Files with errors:\n")
        for result in error_files:
            print(f"File: {result['file']}")
            print(f"  Error: {result['error']}\n")

    print("\n[INFO] Safe emoji replacement complete!")
    print("[INFO] Korean/CJK text PRESERVED")
    print("[INFO] Backups created with .bak extension")

    return 0 if not error_files else 1


if __name__ == "__main__":
    exit(main())
