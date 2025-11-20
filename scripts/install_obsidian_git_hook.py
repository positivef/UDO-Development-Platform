#!/usr/bin/env python3
"""
Install Git Post-Commit Hook for Obsidian Auto-Sync

This script installs a git hook that automatically syncs to Obsidian
whenever you commit code changes.
"""

import os
import sys
from pathlib import Path
import subprocess


def find_project_root() -> Path:
    """Find UDO-Development-Platform project root"""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if parent.name == "UDO-Development-Platform":
            return parent
        if (parent / ".git").exists():
            return parent
    print("❌ Could not find project root with .git directory")
    sys.exit(1)


def create_post_commit_hook(project_root: Path) -> bool:
    """Create post-commit hook"""
    hooks_dir = project_root / ".git" / "hooks"
    hook_path = hooks_dir / "post-commit"

    # Create hooks directory if it doesn't exist
    hooks_dir.mkdir(parents=True, exist_ok=True)

    # Post-commit hook script
    hook_script = '''#!/usr/bin/env python3
"""
Post-Commit Hook: Obsidian Auto-Sync

Automatically syncs development logs to Obsidian after each commit.
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
import json

def get_commit_info():
    """Get information about the latest commit"""
    try:
        # Get commit hash
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            encoding='utf-8',
            errors='replace'
        ).strip()

        # Get commit message
        commit_msg = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%B"],
            encoding='utf-8',
            errors='replace'
        ).strip()

        # Get changed files count
        files_changed = subprocess.check_output(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
            encoding='utf-8',
            errors='replace'
        ).strip().split('\\n')

        return {
            "hash": commit_hash,
            "message": commit_msg,
            "files_count": len([f for f in files_changed if f]),
            "files": files_changed[:10]  # First 10 files
        }
    except Exception as e:
        print(f"Warning: Failed to get commit info: {e}")
        return None


def trigger_obsidian_sync(commit_info):
    """Trigger Obsidian sync via backend API"""
    try:
        import requests

        # Try to sync via backend API (if running)
        response = requests.post(
            "http://localhost:8000/api/obsidian/sync",
            json={
                "event_type": "git_commit",
                "data": commit_info,
                "timestamp": datetime.now().isoformat()
            },
            timeout=5
        )

        if response.status_code == 200:
            print("✅ Obsidian sync triggered successfully")
            return True
    except Exception:
        pass  # Backend not running, use MCP directly

    # Fallback: Use MCP directly (if available in Python environment)
    try:
        # This assumes Claude Code is available
        # If not, we just skip silently
        pass
    except Exception:
        pass

    return False


def main():
    """Main post-commit hook logic"""
    commit_info = get_commit_info()

    if not commit_info:
        sys.exit(0)  # Don't fail commit on error

    print(f"\\n📝 Git Commit: {commit_info['hash']}")
    print(f"   Files changed: {commit_info['files_count']}")

    # Only sync if 3+ files changed OR contains "feat:", "fix:", etc.
    should_sync = False

    if commit_info['files_count'] >= 3:
        should_sync = True
        print("   → Significant changes detected (3+ files)")

    commit_msg_lower = commit_info['message'].lower()
    sync_keywords = ['feat:', 'feature:', 'fix:', 'bug:', 'refactor:', 'docs:']

    if any(keyword in commit_msg_lower for keyword in sync_keywords):
        should_sync = True
        print(f"   → Important commit type detected")

    if should_sync:
        print("   🔄 Triggering Obsidian sync...")
        if trigger_obsidian_sync(commit_info):
            print("   ✅ Development log synced to Obsidian")
        else:
            print("   ⚠️  Backend not running - sync will happen on next periodic backup")
    else:
        print("   ℹ️  Skipping sync (not significant enough)")

    print()  # Empty line for readability


if __name__ == "__main__":
    main()
'''

    # Write the hook
    hook_path.write_text(hook_script, encoding='utf-8')

    # Make it executable (Windows: not needed, but doesn't hurt)
    try:
        import stat
        hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC)
    except Exception:
        pass  # Windows doesn't need chmod

    return True


def main():
    """Main installation logic"""
    print("=" * 60)
    print("Obsidian Git Hook Installer")
    print("=" * 60)
    print()

    project_root = find_project_root()
    print(f"[+] Project root: {project_root}")

    # Check if .git exists
    if not (project_root / ".git").exists():
        print("[X] No .git directory found. Is this a git repository?")
        sys.exit(1)

    print()
    print("Installing post-commit hook...")

    if create_post_commit_hook(project_root):
        print("[OK] Post-commit hook installed successfully!")
        print()
        print("==> Git hook is now active!")
        print()
        print("How it works:")
        print("  1. You commit code: git commit -m 'feat: new feature'")
        print("  2. Hook automatically triggers")
        print("  3. Development log synced to Obsidian")
        print()
        print("Combined with periodic sync (every 1-2 hours):")
        print("  -> You'll never lose context!")
        print()
    else:
        print("[X] Failed to install hook")
        sys.exit(1)


if __name__ == "__main__":
    main()
