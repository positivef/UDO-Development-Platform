"""
Tool Wrappers - 3-Tier Auto-Recovery for Core Development Tools

Provides wrapped versions of common tools with automatic error resolution:
- bash_with_recovery(): Bash command with 3-Tier cascade
- read_with_recovery(): File reading with auto-recovery
- edit_with_recovery(): File editing with auto-recovery
- write_with_recovery(): File writing with auto-recovery

Each tool automatically triggers 3-Tier resolution on errors:
- Tier 1 (Obsidian): Search past solutions (<10ms)
- Tier 2 (Context7): Query official docs (<500ms)
- Tier 3 (User): Escalate if both fail

Usage:
    from scripts.tool_wrappers import bash_with_recovery, read_with_recovery

    # Instead of subprocess.run()
    result = bash_with_recovery("pip install pandas")
    # -> Auto-resolves ModuleNotFoundError via 3-Tier system

    # Instead of open(file).read()
    content = read_with_recovery("/path/to/file.py")
    # -> Auto-resolves PermissionError, FileNotFoundError
"""

import subprocess
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from scripts.auto_3tier_wrapper import auto_3tier

logger = logging.getLogger(__name__)


# =============================================================================
# Bash Command Wrapper
# =============================================================================


@auto_3tier
def bash_with_recovery(
    cmd: str,
    cwd: Optional[str] = None,
    shell: bool = False,
    timeout: Optional[int] = 120,
    check: bool = False,
    capture_output: bool = True,
) -> Dict[str, Any]:
    """
    Execute bash command with automatic 3-Tier error recovery

    Args:
        cmd: Command string to execute
        cwd: Working directory (optional)
        shell: Use shell execution (default: False for security)
        timeout: Command timeout in seconds (default: 120)
        check: Raise exception on non-zero exit code
        capture_output: Capture stdout/stderr (default: True)

    Returns:
        {
            "exit_code": int,
            "stdout": str,
            "stderr": str,
            "success": bool
        }

    Examples:
        >>> result = bash_with_recovery("pip install pandas")
        >>> # ModuleNotFoundError -> Tier 1 (Obsidian) -> Auto-fixed!

        >>> result = bash_with_recovery("chmod +x script.sh")
        >>> # PermissionError -> Tier 2 (Context7) -> chmod applied

        >>> result = bash_with_recovery("nonexistent-command")
        >>> # Command not found -> Tier 3 (User) -> Escalated
    """
    try:
        logger.info(f"[RUN]: {cmd[:100]}")

        # For security, split command unless shell=True explicitly requested
        if shell:
            cmd_list = cmd
        else:
            cmd_list = cmd.split()

        process = subprocess.run(
            cmd_list, cwd=cwd, shell=shell, timeout=timeout, check=check, capture_output=capture_output, text=True
        )

        result = {
            "exit_code": process.returncode,
            "stdout": process.stdout if capture_output else "",
            "stderr": process.stderr if capture_output else "",
            "success": process.returncode == 0,
        }

        if result["success"]:
            logger.info(f"[OK] Command successful: {cmd[:50]}")
        else:
            logger.warning(f"[WARN]  Command failed (exit={result['exit_code']}): {cmd[:50]}")

        return result

    except subprocess.TimeoutExpired as e:
        logger.error(f"[FAIL] Command timeout: {cmd[:100]}")
        return {"exit_code": -1, "stdout": "", "stderr": f"Timeout after {timeout}s", "success": False, "error": str(e)}

    except FileNotFoundError as e:
        logger.error(f"[FAIL] Command not found: {cmd[:100]}")
        return {"exit_code": 127, "stdout": "", "stderr": f"Command not found: {e}", "success": False, "error": str(e)}

    except Exception as e:
        logger.error(f"[FAIL] Command exception: {e}")
        return {"exit_code": -1, "stdout": "", "stderr": str(e), "success": False, "error": str(e)}


# =============================================================================
# File Read Wrapper
# =============================================================================


@auto_3tier
def read_with_recovery(file_path: str, encoding: str = "utf-8", errors: str = "strict") -> Dict[str, Any]:
    """
    Read file with automatic 3-Tier error recovery

    Args:
        file_path: Absolute path to file
        encoding: File encoding (default: utf-8)
        errors: Error handling strategy (strict, ignore, replace)

    Returns:
        {
            "success": bool,
            "content": str,
            "file_path": str,
            "size_bytes": int,
            "error": Optional[str]
        }

    Examples:
        >>> result = read_with_recovery("/path/to/file.py")
        >>> # FileNotFoundError -> Tier 1 -> Past solution found

        >>> result = read_with_recovery("/restricted/file.log")
        >>> # PermissionError -> Tier 2 -> chmod +r applied

        >>> result = read_with_recovery("/binary/file.dat")
        >>> # UnicodeDecodeError -> Tier 2 -> encoding=latin-1 suggested
    """
    try:
        logger.info(f"[READ]: {file_path}")

        path = Path(file_path)

        if not path.exists():
            logger.error(f"[FAIL] File not found: {file_path}")
            return {
                "success": False,
                "content": "",
                "file_path": file_path,
                "size_bytes": 0,
                "error": f"FileNotFoundError: {file_path}",
            }

        if not path.is_file():
            logger.error(f"[FAIL] Not a file: {file_path}")
            return {
                "success": False,
                "content": "",
                "file_path": file_path,
                "size_bytes": 0,
                "error": f"Not a file: {file_path}",
            }

        with open(file_path, "r", encoding=encoding, errors=errors) as f:
            content = f.read()

        size_bytes = path.stat().st_size

        logger.info(f"[OK] Read {size_bytes} bytes from {path.name}")

        return {"success": True, "content": content, "file_path": file_path, "size_bytes": size_bytes}

    except PermissionError as e:
        logger.error(f"[FAIL] Permission denied: {file_path}")
        return {"success": False, "content": "", "file_path": file_path, "size_bytes": 0, "error": f"PermissionError: {e}"}

    except UnicodeDecodeError as e:
        logger.error(f"[FAIL] Encoding error: {file_path}")
        return {
            "success": False,
            "content": "",
            "file_path": file_path,
            "size_bytes": 0,
            "error": f"UnicodeDecodeError: Try encoding='latin-1' or errors='ignore'",
        }

    except Exception as e:
        logger.error(f"[FAIL] Read error: {e}")
        return {"success": False, "content": "", "file_path": file_path, "size_bytes": 0, "error": str(e)}


# =============================================================================
# File Edit Wrapper
# =============================================================================


@auto_3tier
def edit_with_recovery(
    file_path: str, old_string: str, new_string: str, replace_all: bool = False, encoding: str = "utf-8", backup: bool = True
) -> Dict[str, Any]:
    """
    Edit file with automatic 3-Tier error recovery

    Args:
        file_path: Absolute path to file
        old_string: String to replace
        new_string: Replacement string
        replace_all: Replace all occurrences (default: False)
        encoding: File encoding (default: utf-8)
        backup: Create .bak backup (default: True)

    Returns:
        {
            "success": bool,
            "file_path": str,
            "replacements": int,
            "backup_path": Optional[str],
            "error": Optional[str]
        }

    Examples:
        >>> result = edit_with_recovery(
        ...     "/path/to/file.py",
        ...     "old_function()",
        ...     "new_function()"
        ... )
        >>> # PermissionError -> Tier 2 -> chmod +w applied

        >>> result = edit_with_recovery(
        ...     "/readonly/file.txt",
        ...     "search",
        ...     "replace"
        ... )
        >>> # Read-only filesystem -> Tier 3 -> User escalation
    """
    try:
        logger.info(f"[*]  Editing: {file_path}")

        path = Path(file_path)

        if not path.exists():
            return {"success": False, "file_path": file_path, "replacements": 0, "error": f"FileNotFoundError: {file_path}"}

        # Read original content
        with open(file_path, "r", encoding=encoding) as f:
            original = f.read()

        # Count occurrences
        count = original.count(old_string)

        if count == 0:
            logger.warning(f"[WARN]  String not found in {path.name}")
            return {
                "success": False,
                "file_path": file_path,
                "replacements": 0,
                "error": f"String not found: '{old_string[:50]}...'",
            }

        # Replace
        if replace_all:
            modified = original.replace(old_string, new_string)
            replacements = count
        else:
            if count > 1:
                return {
                    "success": False,
                    "file_path": file_path,
                    "replacements": 0,
                    "error": f"Multiple occurrences ({count}) found. Use replace_all=True",
                }
            modified = original.replace(old_string, new_string, 1)
            replacements = 1

        # Create backup
        backup_path = None
        if backup:
            backup_path = str(path) + ".bak"
            with open(backup_path, "w", encoding=encoding) as f:
                f.write(original)

        # Write modified content
        with open(file_path, "w", encoding=encoding) as f:
            f.write(modified)

        logger.info(f"[OK] Edited {path.name} ({replacements} replacement{'s' if replacements > 1 else ''})")

        return {"success": True, "file_path": file_path, "replacements": replacements, "backup_path": backup_path}

    except PermissionError as e:
        logger.error(f"[FAIL] Permission denied: {file_path}")
        return {"success": False, "file_path": file_path, "replacements": 0, "error": f"PermissionError: {e}"}

    except Exception as e:
        logger.error(f"[FAIL] Edit error: {e}")
        return {"success": False, "file_path": file_path, "replacements": 0, "error": str(e)}


# =============================================================================
# File Write Wrapper
# =============================================================================


@auto_3tier
def write_with_recovery(
    file_path: str, content: str, encoding: str = "utf-8", create_dirs: bool = True, backup_if_exists: bool = True
) -> Dict[str, Any]:
    """
    Write file with automatic 3-Tier error recovery

    Args:
        file_path: Absolute path to file
        content: Content to write
        encoding: File encoding (default: utf-8)
        create_dirs: Create parent directories if needed
        backup_if_exists: Backup existing file before overwriting

    Returns:
        {
            "success": bool,
            "file_path": str,
            "size_bytes": int,
            "backup_path": Optional[str],
            "error": Optional[str]
        }

    Examples:
        >>> result = write_with_recovery(
        ...     "/new/path/file.py",
        ...     "print('hello')"
        ... )
        >>> # Parent dir doesn't exist -> create_dirs=True -> Created

        >>> result = write_with_recovery(
        ...     "/readonly/file.txt",
        ...     "content"
        ... )
        >>> # PermissionError -> Tier 2 -> mkdir/chmod suggested
    """
    try:
        logger.info(f"[WRITE]: {file_path}")

        path = Path(file_path)

        # Create parent directories if needed
        if create_dirs and not path.parent.exists():
            logger.info(f"[CREATE] directory: {path.parent}")
            path.parent.mkdir(parents=True, exist_ok=True)

        # Backup existing file
        backup_path = None
        if backup_if_exists and path.exists():
            backup_path = str(path) + ".bak"
            with open(file_path, "r", encoding=encoding) as f:
                original = f.read()
            with open(backup_path, "w", encoding=encoding) as f:
                f.write(original)
            logger.info(f"[*] Backup created: {Path(backup_path).name}")

        # Write content
        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)

        size_bytes = len(content.encode(encoding))

        logger.info(f"[OK] Wrote {size_bytes} bytes to {path.name}")

        return {"success": True, "file_path": file_path, "size_bytes": size_bytes, "backup_path": backup_path}

    except PermissionError as e:
        logger.error(f"[FAIL] Permission denied: {file_path}")
        return {"success": False, "file_path": file_path, "size_bytes": 0, "error": f"PermissionError: {e}"}

    except OSError as e:
        logger.error(f"[FAIL] OS error: {e}")
        return {"success": False, "file_path": file_path, "size_bytes": 0, "error": f"OSError: {e}"}

    except Exception as e:
        logger.error(f"[FAIL] Write error: {e}")
        return {"success": False, "file_path": file_path, "size_bytes": 0, "error": str(e)}


# =============================================================================
# Utility Functions
# =============================================================================


def get_wrapper_statistics() -> Dict[str, Any]:
    """
    Get statistics from Auto3TierWrapper

    Returns all tool wrapper usage statistics including:
    - Total calls and errors
    - Tier distribution (1/2/3)
    - Automation rate
    - Time saved
    """
    from scripts.auto_3tier_wrapper import get_statistics

    return get_statistics()


def reset_wrapper_statistics():
    """Reset all tool wrapper statistics"""
    from scripts.auto_3tier_wrapper import reset_statistics

    reset_statistics()


def print_wrapper_report():
    """Print formatted statistics report"""
    stats = get_wrapper_statistics()

    print("\n" + "=" * 60)
    print("[*] Tool Wrapper Statistics")
    print("=" * 60)
    print(f"Total Calls: {stats['total_calls']}")
    print(f"Total Errors: {stats['total_errors']}")
    print("")
    print("3-Tier Distribution:")
    print(f"  Tier 1 (Obsidian):       {stats['tier1_hits']} hits")
    print(f"  Tier 2 (Context7 AUTO):  {stats['tier2_auto']} hits")
    print(f"  Tier 2 (Context7 CONFIRM): {stats['tier2_confirmed']} hits")
    print(f"  Tier 3 (User):           {stats['tier3_escalations']} escalations")
    print("")
    print(f"Automation Rate: {stats['automation_rate'] * 100:.1f}%")
    print(f"Time Saved: {stats['time_saved_minutes']:.1f} minutes")
    print(f"Circuit Breaker: {stats['circuit_breaker_state']}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    # Self-test
    logging.basicConfig(level=logging.INFO)

    print("\n" + "=" * 60)
    print("Testing Tool Wrappers with 3-Tier Auto-Recovery")
    print("=" * 60 + "\n")

    # Test 1: Successful bash command
    print("Test 1: Successful bash command")
    result = bash_with_recovery("echo Hello World")
    print(f"Result: {result}")
    assert result["success"] is True

    # Test 2: Failed bash command (will trigger 3-Tier, but no solution)
    print("\nTest 2: Failed bash command")
    result = bash_with_recovery("nonexistent-command-test")
    print(f"Result: {result}")
    assert result["success"] is False

    # Test 3: Read existing file (self)
    print("\nTest 3: Read existing file")
    result = read_with_recovery(__file__)
    print(f"Result: success={result['success']}, size={result['size_bytes']} bytes")
    assert result["success"] is True

    # Test 4: Read non-existent file
    print("\nTest 4: Read non-existent file")
    result = read_with_recovery("/nonexistent/file.txt")
    print(f"Result: {result}")
    assert result["success"] is False

    # Print statistics
    print_wrapper_report()

    print("[OK] All self-tests passed!")
