#!/usr/bin/env python3
"""
Session Automation System (v2.0 - With Recovery)
=================================================
Automates session lifecycle with crash recovery.

Features:
1. Auto-update CURRENT.md on session start/end
2. Generate session handoff documents
3. Sync with Obsidian knowledge base
4. Track session metrics
5. **NEW: Crash recovery for orphaned sessions**
6. **NEW: Auto-detection of incomplete sessions**

Usage:
    python scripts/session_automation.py start
    python scripts/session_automation.py checkpoint --notes "Work done"
    python scripts/session_automation.py end --summary "Work completed"
    python scripts/session_automation.py recover  # NEW: Recover orphaned session
    python scripts/session_automation.py status

Exception Handling:
    - Computer crash: Recoverable via 'recover' command
    - CMD window closed: Recoverable via 'recover' command
    - Claude session ended: Recoverable via 'recover' command
    - Context limit reached: Auto-detected on next 'start'

Environment:
    OBSIDIAN_VAULT_PATH: Path to Obsidian vault (optional)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import subprocess
import re

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_ROOT = PROJECT_ROOT / "docs"
CURRENT_MD = DOCS_ROOT / "CURRENT.md"
SESSIONS_DIR = DOCS_ROOT / "sessions"
WORKLOGS_DIR = SESSIONS_DIR / "worklogs"
STATE_FILE = PROJECT_ROOT / ".udo" / "session_state.json"

# Obsidian path (from environment or user home fallback)
OBSIDIAN_VAULT = Path(os.environ.get("OBSIDIAN_VAULT_PATH") or str(Path.home() / "Documents" / "Obsidian Vault"))

# Recovery settings
ORPHAN_THRESHOLD_HOURS = 12  # Sessions older than this are considered orphaned
AUTO_CHECKPOINT_MINUTES = 30  # Recommended checkpoint interval


class SessionManager:
    """Manages AI session lifecycle with recovery support."""

    def __init__(self):
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Load session state from file."""
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return self._empty_state()

    def _empty_state(self) -> Dict[str, Any]:
        """Return empty state structure."""
        return {
            "active": False,
            "start_time": None,
            "last_checkpoint": None,
            "checkpoints": [],
            "files_modified": [],
            "tests_run": [],
            "recovery_info": None,
        }

    def _save_state(self):
        """Save session state to file."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.state["last_checkpoint"] = datetime.now().isoformat()
        STATE_FILE.write_text(json.dumps(self.state, indent=2, default=str), encoding="utf-8")

    def _check_orphaned_session(self) -> Tuple[bool, Optional[str]]:
        """
        Check if there's an orphaned session from a previous crash.

        Returns:
            (is_orphaned, reason)
        """
        if not self.state.get("active"):
            return False, None

        start_time_str = self.state.get("start_time")
        if not start_time_str:
            return False, None

        try:
            start_time = datetime.fromisoformat(start_time_str)
            elapsed = datetime.now() - start_time

            if elapsed > timedelta(hours=ORPHAN_THRESHOLD_HOURS):
                return True, f"Session started {elapsed} ago (>{ORPHAN_THRESHOLD_HOURS}h threshold)"

            # Check last checkpoint
            last_cp = self.state.get("last_checkpoint")
            if last_cp:
                last_cp_time = datetime.fromisoformat(last_cp)
                since_checkpoint = datetime.now() - last_cp_time
                if since_checkpoint > timedelta(hours=2):
                    return True, f"No activity for {since_checkpoint} (last checkpoint: {last_cp_time})"

        except Exception:
            pass

        return False, None

    def start_session(self, force: bool = False) -> str:
        """
        Start a new session.

        Args:
            force: If True, skip orphan check and force new session
        """
        # Check for orphaned session
        is_orphaned, reason = self._check_orphaned_session()

        if is_orphaned and not force:
            return (
                f"⚠️  ORPHANED SESSION DETECTED\n"
                f"    Reason: {reason}\n"
                f"\n"
                f"    Options:\n"
                f"    1. Recover: python scripts/session_automation.py recover\n"
                f"    2. Force new: python scripts/session_automation.py start --force\n"
                f"\n"
                f"    Recovery will generate handoff from saved checkpoints."
            )

        if self.state.get("active") and not force:
            return (
                f"⚠️  Session already active (started: {self.state.get('start_time')})\n"
                f"    Use 'checkpoint' to save progress or 'end' to finish."
            )

        now = datetime.now()

        self.state = {
            "active": True,
            "start_time": now.isoformat(),
            "last_checkpoint": now.isoformat(),
            "checkpoints": [],
            "files_modified": [],
            "tests_run": [],
            "recovery_info": {
                "started_by": "session_automation.py",
                "hostname": os.environ.get("COMPUTERNAME", "unknown"),
                "pid": os.getpid(),
            },
        }
        self._save_state()

        # Update CURRENT.md
        self._update_current_md(status="Session Started", notes=f"New session started at {now.strftime('%Y-%m-%d %H:%M')}")

        return (
            f"✅ Session started at {now.strftime('%Y-%m-%d %H:%M')}\n"
            f"\n"
            f"   Remember to:\n"
            f"   - Run 'checkpoint' periodically (every {AUTO_CHECKPOINT_MINUTES}min)\n"
            f"   - Run 'end' when finished\n"
            f"\n"
            f"   If session is interrupted unexpectedly, run 'recover'"
        )

    def checkpoint(self, notes: str = "") -> str:
        """Create a checkpoint (crash recovery point)."""
        if not self.state.get("active"):
            return "⚠️  No active session. Run 'start' first."

        now = datetime.now()

        # Get current git status for recovery
        git_status = self._get_git_status()

        checkpoint = {
            "time": now.isoformat(),
            "notes": notes,
            "git_status": git_status,
            "recent_commits": self._get_recent_commits(3),
        }

        self.state["checkpoints"].append(checkpoint)
        self._save_state()

        checkpoint_count = len(self.state["checkpoints"])

        return (
            f"✅ Checkpoint #{checkpoint_count} created at {now.strftime('%H:%M')}\n"
            f"   Notes: {notes if notes else '(none)'}\n"
            f"   Git status saved for recovery"
        )

    def end_session(self, summary: str = "") -> str:
        """End session and generate handoff."""
        if not self.state.get("active"):
            return "⚠️  No active session to end."

        now = datetime.now()
        start_time = datetime.fromisoformat(self.state["start_time"])
        duration = now - start_time

        # Generate handoff document
        handoff_path = self._generate_handoff(summary, duration, is_recovery=False)

        # Update CURRENT.md
        self._update_current_md(status="Session Ended", notes=f"Session ended. Handoff: {handoff_path.name}")

        # Sync to Obsidian
        self._sync_to_obsidian(handoff_path)

        # Reset state
        self.state = self._empty_state()
        self._save_state()

        return (
            f"✅ Session ended successfully\n"
            f"   Duration: {duration}\n"
            f"   Handoff: {handoff_path.name}\n"
            f"   Synced to Obsidian"
        )

    def recover_session(self) -> str:
        """
        Recover an orphaned session from crash/interruption.

        This generates an emergency handoff from saved checkpoints.
        """
        if not self.state.get("active"):
            return "ℹ️  No orphaned session to recover."

        if not self.state.get("checkpoints"):
            # No checkpoints, but session was active - generate minimal handoff
            start_time_str = self.state.get("start_time", datetime.now().isoformat())
            start_time = datetime.fromisoformat(start_time_str)
            duration = datetime.now() - start_time

            handoff_path = self._generate_handoff(
                summary="[EMERGENCY RECOVERY] Session interrupted without checkpoints", duration=duration, is_recovery=True
            )
        else:
            # Has checkpoints - generate recovery handoff
            last_checkpoint = self.state["checkpoints"][-1]
            start_time_str = self.state.get("start_time", datetime.now().isoformat())
            start_time = datetime.fromisoformat(start_time_str)
            duration = datetime.now() - start_time

            # Use notes from last checkpoint as summary
            last_notes = last_checkpoint.get("notes", "No notes")

            handoff_path = self._generate_handoff(
                summary=f"[RECOVERY] Last checkpoint: {last_notes}", duration=duration, is_recovery=True
            )

        # Update CURRENT.md
        self._update_current_md(status="Session Recovered", notes=f"Orphaned session recovered. Handoff: {handoff_path.name}")

        # Sync to Obsidian
        self._sync_to_obsidian(handoff_path)

        # Reset state
        checkpoint_count = len(self.state.get("checkpoints", []))
        self.state = self._empty_state()
        self._save_state()

        return (
            f"✅ Session recovered successfully\n"
            f"   Checkpoints recovered: {checkpoint_count}\n"
            f"   Emergency handoff: {handoff_path.name}\n"
            f"   Synced to Obsidian\n"
            f"\n"
            f"   You can now start a new session with 'start'"
        )

    def get_status(self) -> str:
        """Get current session status with recovery info."""
        is_orphaned, reason = self._check_orphaned_session()

        if not self.state.get("active"):
            return "ℹ️  No active session"

        start_time = datetime.fromisoformat(self.state["start_time"])
        duration = datetime.now() - start_time
        checkpoint_count = len(self.state.get("checkpoints", []))

        status_lines = [
            f"📊 Session Status",
            f"   Active: Yes",
            f"   Duration: {duration}",
            f"   Checkpoints: {checkpoint_count}",
        ]

        if is_orphaned:
            status_lines.extend(
                [
                    f"",
                    f"   ⚠️  WARNING: Session may be orphaned",
                    f"   Reason: {reason}",
                    f"   Run 'recover' to generate emergency handoff",
                ]
            )

        last_cp = self.state.get("last_checkpoint")
        if last_cp:
            last_cp_time = datetime.fromisoformat(last_cp)
            since_cp = datetime.now() - last_cp_time
            status_lines.append(f"   Last checkpoint: {since_cp} ago")

            if since_cp > timedelta(minutes=AUTO_CHECKPOINT_MINUTES):
                status_lines.append(f"   💡 Recommendation: Create a checkpoint now")

        return "\n".join(status_lines)

    def _update_current_md(self, status: str, notes: str):
        """Update CURRENT.md with session info."""
        if not CURRENT_MD.exists():
            return

        try:
            content = CURRENT_MD.read_text(encoding="utf-8")
        except Exception:
            return

        now = datetime.now()

        # Update Last Updated line
        content = re.sub(r"\*\*Last Updated\*\*: .*", f'**Last Updated**: {now.strftime("%Y-%m-%d")}', content)

        # Update change log (add entry)
        changelog_entry = f"| {now.strftime('%Y-%m-%d')} | {status}: {notes[:50]} | @claude-code |"

        # Find Change Log section and add entry
        if "## Change Log" in content:
            lines = content.split("\n")
            new_lines = []
            found_changelog = False
            found_table = False

            for i, line in enumerate(lines):
                new_lines.append(line)
                if "## Change Log" in line:
                    found_changelog = True
                elif found_changelog and line.startswith("|") and "Date" in line:
                    found_table = True
                elif found_changelog and found_table and line.startswith("|---"):
                    new_lines.append(changelog_entry)
                    found_table = False

            content = "\n".join(new_lines)

        try:
            CURRENT_MD.write_text(content, encoding="utf-8")
        except Exception:
            pass

    def _generate_handoff(self, summary: str, duration, is_recovery: bool = False) -> Path:
        """Generate session handoff document."""
        now = datetime.now()
        prefix = "RECOVERY_" if is_recovery else ""
        filename = f"{prefix}{now.strftime('%Y-%m-%d')}_{now.strftime('%H%M')}_handoff.md"
        handoff_path = WORKLOGS_DIR / filename

        WORKLOGS_DIR.mkdir(parents=True, exist_ok=True)

        # Get git changes
        git_status = self._get_git_status()
        recent_commits = self._get_recent_commits()

        # Recovery-specific header
        recovery_notice = ""
        if is_recovery:
            recovery_notice = """
> ⚠️ **RECOVERY HANDOFF**
> This handoff was generated from saved checkpoints after session interruption.
> Some information may be incomplete.

"""

        content = f"""# Session Handoff - {now.strftime('%Y-%m-%d %H:%M')}

**Duration**: {duration}
**Author**: @claude-code
**Type**: {'Recovery' if is_recovery else 'Normal'}

---
{recovery_notice}
## Summary

{summary if summary else "No summary provided."}

## Session Metrics

- **Start Time**: {self.state.get('start_time', 'Unknown')}
- **End Time**: {now.isoformat()}
- **Checkpoints**: {len(self.state.get('checkpoints', []))}
- **Recovery**: {'Yes' if is_recovery else 'No'}

## Files Modified

```
{git_status}
```

## Recent Commits

```
{recent_commits}
```

## Checkpoints

{self._format_checkpoints()}

## Recovery Information

{self._format_recovery_info()}

## Next Session Recommendations

1. Review this handoff for context
2. Check `docs/CURRENT.md` for active work items
3. Run tests: `.venv\\Scripts\\python.exe -m pytest tests/ -v`
4. Start new session: `python scripts/session_automation.py start`

---

*Generated by session_automation.py v2.0*
"""

        handoff_path.write_text(content, encoding="utf-8")
        return handoff_path

    def _format_checkpoints(self) -> str:
        """Format checkpoints for handoff."""
        if not self.state.get("checkpoints"):
            return "No checkpoints recorded."

        lines = []
        for i, cp in enumerate(self.state["checkpoints"], 1):
            try:
                time = datetime.fromisoformat(cp["time"]).strftime("%H:%M")
            except Exception:
                time = "unknown"
            notes = cp.get("notes", "No notes")
            lines.append(f"{i}. **{time}**: {notes}")

        return "\n".join(lines)

    def _format_recovery_info(self) -> str:
        """Format recovery information."""
        info = self.state.get("recovery_info", {})
        if not info:
            return "No recovery information available."

        lines = [
            f"- **Started by**: {info.get('started_by', 'unknown')}",
            f"- **Hostname**: {info.get('hostname', 'unknown')}",
            f"- **Process ID**: {info.get('pid', 'unknown')}",
        ]
        return "\n".join(lines)

    def _get_git_status(self) -> str:
        """Get current git status."""
        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=PROJECT_ROOT,
            )
            return result.stdout.strip() or "No changes"
        except Exception:
            return "Unable to get git status"

    def _get_recent_commits(self, count: int = 5) -> str:
        """Get recent commits."""
        try:
            result = subprocess.run(
                ["git", "log", f"-{count}", "--oneline"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=PROJECT_ROOT,
            )
            return result.stdout.strip() or "No recent commits"
        except Exception:
            return "Unable to get commits"

    def _sync_to_obsidian(self, handoff_path: Path):
        """Sync handoff to Obsidian vault."""
        if not OBSIDIAN_VAULT.exists():
            print(f"  [INFO] Obsidian vault not found: {OBSIDIAN_VAULT}")
            return

        obsidian_devlog = OBSIDIAN_VAULT / "개발일지"
        obsidian_target = obsidian_devlog / handoff_path.name

        try:
            obsidian_devlog.mkdir(parents=True, exist_ok=True)
            obsidian_target.write_text(handoff_path.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"  [OK] Synced to Obsidian: {obsidian_target.name}")
        except Exception as e:
            print(f"  [WARN] Obsidian sync failed: {e}")


def safe_print(text: str):
    """Print text with fallback for encoding issues."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Remove emojis and special characters for Windows console
        import re

        clean_text = re.sub(r"[^\x00-\x7F]+", "", text)
        clean_text = clean_text.replace("✅", "[OK]")
        clean_text = clean_text.replace("⚠️", "[WARN]")
        clean_text = clean_text.replace("ℹ️", "[INFO]")
        clean_text = clean_text.replace("📊", "[STATUS]")
        clean_text = clean_text.replace("💡", "[TIP]")
        print(clean_text)


def main():
    parser = argparse.ArgumentParser(
        description="Session Automation System v2.0 (with Recovery)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s start                    Start new session
  %(prog)s start --force            Force new session (discard orphaned)
  %(prog)s checkpoint -n "Done X"   Create checkpoint with notes
  %(prog)s end -s "Completed Y"     End session with summary
  %(prog)s recover                  Recover orphaned session
  %(prog)s status                   Show session status

Recovery Scenarios:
  - Computer crash     → Run 'recover' on restart
  - CMD window closed  → Run 'recover' in new window
  - Claude terminated  → Run 'recover' in next session
  - Context limit      → Auto-detected on next 'start'
        """,
    )
    parser.add_argument("action", choices=["start", "checkpoint", "end", "status", "recover"], help="Session action")
    parser.add_argument("--summary", "-s", default="", help="Session summary (for end action)")
    parser.add_argument("--notes", "-n", default="", help="Checkpoint notes (for checkpoint action)")
    parser.add_argument("--force", "-f", action="store_true", help="Force action (skip checks)")

    args = parser.parse_args()
    manager = SessionManager()

    if args.action == "start":
        safe_print(manager.start_session(force=args.force))
    elif args.action == "checkpoint":
        safe_print(manager.checkpoint(args.notes))
    elif args.action == "end":
        safe_print(manager.end_session(args.summary))
    elif args.action == "recover":
        safe_print(manager.recover_session())
    elif args.action == "status":
        safe_print(manager.get_status())


if __name__ == "__main__":
    main()
