"""
Session Start Script

Automatically runs at the beginning of each Claude Code session to:
1. Check for scheduled tasks from Obsidian
2. Alert about overdue or upcoming tasks
3. Provide context for the session

Usage:
    python scripts/session_start.py
    python scripts/session_start.py --verbose
"""

import sys
from pathlib import Path
from typing import List  # noqa: F401 - may be used in type annotations

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from obsidian_3stage_search import check_scheduled_tasks_on_session_start  # noqa: E402


def main():
    """Main entry point"""
    import argparse

    # Fix Windows console encoding
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Session start checks")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--silent", action="store_true", help="Silent mode (only show if tasks found)")

    args = parser.parse_args()

    # Check scheduled tasks
    result = check_scheduled_tasks_on_session_start(verbose=args.verbose)

    # Silent mode: only output if tasks found
    if args.silent and not result.get("found_tasks"):
        return 0

    # Print summary
    if "summary" in result:
        print(result["summary"])

    # Return exit code
    if result.get("found_tasks"):
        # Check priority
        if result.get("overdue"):
            return 2  # Overdue tasks (highest priority)
        elif result.get("this_week"):
            return 1  # This week tasks
        else:
            return 0  # Just upcoming
    else:
        return 0


if __name__ == "__main__":
    exit(main())
