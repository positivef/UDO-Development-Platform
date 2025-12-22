#!/usr/bin/env python3
"""
Session Automation System (v3.0 - Enhanced Context)
====================================================
Automates session lifecycle with crash recovery and smart context restoration.

Features:
1. Auto-update CURRENT.md on session start/end
2. Generate session handoff documents
3. Sync with Obsidian knowledge base
4. Track session metrics
5. Crash recovery for orphaned sessions
6. Auto-detection of incomplete sessions
7. **NEW v3.0: Pending todos collection from worklogs**
8. **NEW v3.0: Suggested next actions based on context**
9. **NEW v3.0: Recent errors summary for quick reference**

Usage:
    python scripts/session_automation.py start
    python scripts/session_automation.py start --context    # NEW: With full context
    python scripts/session_automation.py checkpoint --notes "Work done"
    python scripts/session_automation.py end --summary "Work completed"
    python scripts/session_automation.py recover
    python scripts/session_automation.py status
    python scripts/session_automation.py context           # NEW: Show context only

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
CLAUDEDOCS_ROOT = PROJECT_ROOT / "claudedocs"
CLAUDEDOCS_WORKLOG = CLAUDEDOCS_ROOT / "worklog"
CLAUDEDOCS_COMPLETION = CLAUDEDOCS_ROOT / "completion"
STATE_FILE = PROJECT_ROOT / ".udo" / "session_state.json"

# Obsidian path (from environment or default)
OBSIDIAN_VAULT = Path(os.environ.get(
    "OBSIDIAN_VAULT_PATH",
    "C:/Users/user/Documents/Obsidian Vault"
))

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
            "recovery_info": None
        }

    # ========== NEW v3.0: Context Collection Methods ==========

    def collect_pending_todos(self) -> list:
        """
        Collect pending todos from recent worklogs and CURRENT.md.

        Scans:
        - claudedocs/worklog/*.md for unchecked items (- [ ])
        - docs/CURRENT.md for active work items

        Returns:
            List of pending todo strings
        """
        pending = []

        # 1. Scan claudedocs/worklog for recent files (last 3 days)
        if CLAUDEDOCS_WORKLOG.exists():
            worklog_files = sorted(
                CLAUDEDOCS_WORKLOG.glob("*.md"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )[:5]  # Last 5 worklogs

            for wf in worklog_files:
                try:
                    content = wf.read_text(encoding="utf-8")
                    # Find unchecked items: - [ ] task
                    unchecked = re.findall(r'- \[ \] (.+)', content)
                    for item in unchecked:
                        pending.append(f"[{wf.stem}] {item.strip()}")
                except Exception:
                    pass

        # 2. Scan CURRENT.md for active work
        if CURRENT_MD.exists():
            try:
                content = CURRENT_MD.read_text(encoding="utf-8")
                # Find pending items in "Upcoming Milestones" or similar sections
                unchecked = re.findall(r'- \[ \] (.+)', content)
                for item in unchecked:
                    if item.strip() not in [p.split('] ')[-1] for p in pending]:
                        pending.append(f"[CURRENT] {item.strip()}")
            except Exception:
                pass

        return pending[:10]  # Limit to top 10

    def get_recent_errors(self, days: int = 3) -> list:
        """
        Get recent errors from Obsidian knowledge base.

        Scans Debug-*.md files for recent error resolutions.

        Returns:
            List of recent error summaries
        """
        errors = []

        # Check Obsidian vault for Debug files
        if OBSIDIAN_VAULT.exists():
            debug_dir = OBSIDIAN_VAULT / "3-Areas" / "UDO" / "Errors"
            if debug_dir.exists():
                for df in sorted(debug_dir.glob("Debug-*.md"), reverse=True)[:5]:
                    try:
                        content = df.read_text(encoding="utf-8")
                        # Extract error type from filename
                        error_type = df.stem.replace("Debug-", "").replace("-", " ")
                        errors.append(f"[RESOLVED] {error_type}")
                    except Exception:
                        pass

        return errors[:5]

    def suggest_next_actions(self) -> list:
        """
        Suggest next actions based on current context.

        Analyzes:
        - Git status (uncommitted changes)
        - Test status (if tests are failing)
        - Recent worklogs (incomplete work)
        - CURRENT.md (upcoming milestones)

        Returns:
            List of suggested action strings
        """
        suggestions = []

        # 1. Check git status
        git_status = self._get_git_status()
        if git_status and git_status != "No changes":
            modified_count = len([l for l in git_status.split('\n') if l.strip()])
            if modified_count > 0:
                suggestions.append(f"[GIT] {modified_count} uncommitted changes - consider committing")

        # 2. Check for pending todos
        pending = self.collect_pending_todos()
        if pending:
            suggestions.append(f"[TODO] {len(pending)} pending tasks from previous sessions")

        # 3. Check CURRENT.md for active work
        if CURRENT_MD.exists():
            try:
                content = CURRENT_MD.read_text(encoding="utf-8")
                # Look for "Active Work" or "This Week's Focus" section
                if "in_progress" in content.lower() or "active work" in content.lower():
                    suggestions.append("[CONTINUE] Active work detected in CURRENT.md")
            except Exception:
                pass

        # 4. Check for recent completion reports
        if CLAUDEDOCS_COMPLETION.exists():
            recent_completions = sorted(
                CLAUDEDOCS_COMPLETION.glob("*.md"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )[:1]
            if recent_completions:
                last_completion = recent_completions[0].stem
                suggestions.append(f"[LAST] Completed: {last_completion}")

        # 5. Default suggestion if nothing else
        if not suggestions:
            suggestions.append("[START] No pending work - ready for new tasks")

        return suggestions

    def generate_session_context(self) -> Dict[str, Any]:
        """
        Generate comprehensive session context for quick restoration.

        Returns:
            Dictionary with all context information
        """
        return {
            "last_session": self._get_last_session_summary(),
            "pending_todos": self.collect_pending_todos(),
            "recent_errors": self.get_recent_errors(),
            "git_status": self._get_git_status(),
            "suggested_next": self.suggest_next_actions(),
            "generated_at": datetime.now().isoformat()
        }

    def _get_last_session_summary(self) -> Dict[str, Any]:
        """Get summary of last session from handoff or state."""
        summary = {
            "exists": False,
            "summary": "No previous session found",
            "duration": None,
            "checkpoints": 0
        }

        # Check for recent handoff files
        if WORKLOGS_DIR.exists():
            handoffs = sorted(
                WORKLOGS_DIR.glob("*_handoff.md"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )[:1]

            if handoffs:
                try:
                    content = handoffs[0].read_text(encoding="utf-8")
                    # Extract summary section
                    summary_match = re.search(r'## Summary\s+(.+?)(?=\n##|\Z)', content, re.DOTALL)
                    if summary_match:
                        summary["exists"] = True
                        summary["summary"] = summary_match.group(1).strip()[:200]
                        summary["file"] = handoffs[0].name
                except Exception:
                    pass

        return summary

    def display_context(self) -> str:
        """
        Display formatted session context.

        Returns:
            Formatted context string for display
        """
        ctx = self.generate_session_context()

        lines = [
            "=" * 60,
            "  SESSION CONTEXT (Auto-Generated)",
            "=" * 60,
            ""
        ]

        # Last Session
        last = ctx.get("last_session", {})
        if last.get("exists"):
            lines.extend([
                "[LAST SESSION]",
                f"  File: {last.get('file', 'Unknown')}",
                f"  Summary: {last.get('summary', 'N/A')[:100]}...",
                ""
            ])

        # Pending Todos
        todos = ctx.get("pending_todos", [])
        if todos:
            lines.extend([
                f"[PENDING TODOS] ({len(todos)} items)",
            ])
            for todo in todos[:5]:
                lines.append(f"  - {todo}")
            if len(todos) > 5:
                lines.append(f"  ... and {len(todos) - 5} more")
            lines.append("")

        # Suggested Actions
        suggestions = ctx.get("suggested_next", [])
        if suggestions:
            lines.extend([
                "[SUGGESTED ACTIONS]",
            ])
            for s in suggestions:
                lines.append(f"  > {s}")
            lines.append("")

        # Git Status
        git = ctx.get("git_status", "")
        if git and git != "No changes":
            lines.extend([
                "[GIT STATUS]",
                f"  {git[:200]}",
                ""
            ])

        lines.extend([
            "=" * 60,
            f"  Generated: {ctx.get('generated_at', 'Unknown')}",
            "=" * 60,
        ])

        return "\n".join(lines)

    # ========== END v3.0 Methods ==========

    def _save_state(self):
        """Save session state to file."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.state["last_checkpoint"] = datetime.now().isoformat()
        STATE_FILE.write_text(
            json.dumps(self.state, indent=2, default=str),
            encoding="utf-8"
        )

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
                f"[WARN]  ORPHANED SESSION DETECTED\n"
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
                f"[WARN]  Session already active (started: {self.state.get('start_time')})\n"
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
                "pid": os.getpid()
            }
        }
        self._save_state()

        # Update CURRENT.md
        self._update_current_md(
            status="Session Started",
            notes=f"New session started at {now.strftime('%Y-%m-%d %H:%M')}"
        )

        return (
            f"[OK] Session started at {now.strftime('%Y-%m-%d %H:%M')}\n"
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
            return "[WARN]  No active session. Run 'start' first."

        now = datetime.now()

        # Get current git status for recovery
        git_status = self._get_git_status()

        checkpoint = {
            "time": now.isoformat(),
            "notes": notes,
            "git_status": git_status,
            "recent_commits": self._get_recent_commits(3)
        }

        self.state["checkpoints"].append(checkpoint)
        self._save_state()

        checkpoint_count = len(self.state["checkpoints"])

        return (
            f"[OK] Checkpoint #{checkpoint_count} created at {now.strftime('%H:%M')}\n"
            f"   Notes: {notes if notes else '(none)'}\n"
            f"   Git status saved for recovery"
        )

    def end_session(self, summary: str = "") -> str:
        """End session and generate handoff."""
        if not self.state.get("active"):
            return "[WARN]  No active session to end."

        now = datetime.now()
        start_time = datetime.fromisoformat(self.state["start_time"])
        duration = now - start_time

        # Generate handoff document
        handoff_path = self._generate_handoff(summary, duration, is_recovery=False)

        # Update CURRENT.md
        self._update_current_md(
            status="Session Ended",
            notes=f"Session ended. Handoff: {handoff_path.name}"
        )

        # Sync to Obsidian
        self._sync_to_obsidian(handoff_path)

        # Reset state
        self.state = self._empty_state()
        self._save_state()

        return (
            f"[OK] Session ended successfully\n"
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
            return "ℹ  No orphaned session to recover."

        if not self.state.get("checkpoints"):
            # No checkpoints, but session was active - generate minimal handoff
            start_time_str = self.state.get("start_time", datetime.now().isoformat())
            start_time = datetime.fromisoformat(start_time_str)
            duration = datetime.now() - start_time

            handoff_path = self._generate_handoff(
                summary="[EMERGENCY RECOVERY] Session interrupted without checkpoints",
                duration=duration,
                is_recovery=True
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
                summary=f"[RECOVERY] Last checkpoint: {last_notes}",
                duration=duration,
                is_recovery=True
            )

        # Update CURRENT.md
        self._update_current_md(
            status="Session Recovered",
            notes=f"Orphaned session recovered. Handoff: {handoff_path.name}"
        )

        # Sync to Obsidian
        self._sync_to_obsidian(handoff_path)

        # Reset state
        checkpoint_count = len(self.state.get("checkpoints", []))
        self.state = self._empty_state()
        self._save_state()

        return (
            f"[OK] Session recovered successfully\n"
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
            return "ℹ  No active session"

        start_time = datetime.fromisoformat(self.state["start_time"])
        duration = datetime.now() - start_time
        checkpoint_count = len(self.state.get("checkpoints", []))

        status_lines = [
            f"[EMOJI] Session Status",
            f"   Active: Yes",
            f"   Duration: {duration}",
            f"   Checkpoints: {checkpoint_count}",
        ]

        if is_orphaned:
            status_lines.extend([
                f"",
                f"   [WARN]  WARNING: Session may be orphaned",
                f"   Reason: {reason}",
                f"   Run 'recover' to generate emergency handoff"
            ])

        last_cp = self.state.get("last_checkpoint")
        if last_cp:
            last_cp_time = datetime.fromisoformat(last_cp)
            since_cp = datetime.now() - last_cp_time
            status_lines.append(f"   Last checkpoint: {since_cp} ago")

            if since_cp > timedelta(minutes=AUTO_CHECKPOINT_MINUTES):
                status_lines.append(f"   [EMOJI] Recommendation: Create a checkpoint now")

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
        content = re.sub(
            r'\*\*Last Updated\*\*: .*',
            f'**Last Updated**: {now.strftime("%Y-%m-%d")}',
            content
        )

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
> [WARN] **RECOVERY HANDOFF**
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
            f"- **Process ID**: {info.get('pid', 'unknown')}"
        ]
        return "\n".join(lines)

    def _get_git_status(self) -> str:
        """Get current git status."""
        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=PROJECT_ROOT
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
                encoding='utf-8',
                errors='replace',
                cwd=PROJECT_ROOT
            )
            return result.stdout.strip() or "No recent commits"
        except Exception:
            return "Unable to get commits"

    def _sync_to_obsidian(self, handoff_path: Path):
        """Sync handoff to Obsidian vault."""
        if not OBSIDIAN_VAULT.exists():
            print(f"  [INFO] Obsidian vault not found: {OBSIDIAN_VAULT}")
            return

        obsidian_devlog = OBSIDIAN_VAULT / "[EMOJI]"
        obsidian_target = obsidian_devlog / handoff_path.name

        try:
            obsidian_devlog.mkdir(parents=True, exist_ok=True)
            obsidian_target.write_text(
                handoff_path.read_text(encoding="utf-8"),
                encoding="utf-8"
            )
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
        clean_text = re.sub(r'[^\x00-\x7F]+', '', text)
        clean_text = clean_text.replace('[OK]', '[OK]')
        clean_text = clean_text.replace('[WARN]', '[WARN]')
        clean_text = clean_text.replace('ℹ', '[INFO]')
        clean_text = clean_text.replace('[EMOJI]', '[STATUS]')
        clean_text = clean_text.replace('[EMOJI]', '[TIP]')
        print(clean_text)


def main():
    parser = argparse.ArgumentParser(
        description="Session Automation System v3.0 (with Recovery + Context)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s start                    Start new session
  %(prog)s start --context          Start with full context display
  %(prog)s start --force            Force new session (discard orphaned)
  %(prog)s checkpoint -n "Done X"   Create checkpoint with notes
  %(prog)s end -s "Completed Y"     End session with summary
  %(prog)s recover                  Recover orphaned session
  %(prog)s status                   Show session status
  %(prog)s context                  Show session context only (NEW v3.0)

Recovery Scenarios:
  - Computer crash     -> Run 'recover' on restart
  - CMD window closed  -> Run 'recover' in new window
  - Claude terminated  -> Run 'recover' in next session
  - Context limit      -> Auto-detected on next 'start'

Context Features (v3.0):
  - Pending todos from worklogs and CURRENT.md
  - Suggested next actions based on git status
  - Recent errors from Obsidian knowledge base
  - Last session summary for quick reference
        """
    )
    parser.add_argument(
        "action",
        choices=["start", "checkpoint", "end", "status", "recover", "context"],
        help="Session action"
    )
    parser.add_argument(
        "--summary", "-s",
        default="",
        help="Session summary (for end action)"
    )
    parser.add_argument(
        "--notes", "-n",
        default="",
        help="Checkpoint notes (for checkpoint action)"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force action (skip checks)"
    )
    parser.add_argument(
        "--context", "-c",
        action="store_true",
        help="Show context on start (v3.0)"
    )

    args = parser.parse_args()
    manager = SessionManager()

    if args.action == "start":
        result = manager.start_session(force=args.force)
        safe_print(result)
        # Show context if requested or if this is a successful start
        if args.context and "[OK]" in result:
            safe_print("")
            safe_print(manager.display_context())
    elif args.action == "checkpoint":
        safe_print(manager.checkpoint(args.notes))
    elif args.action == "end":
        safe_print(manager.end_session(args.summary))
    elif args.action == "recover":
        safe_print(manager.recover_session())
    elif args.action == "status":
        safe_print(manager.get_status())
    elif args.action == "context":
        safe_print(manager.display_context())


if __name__ == "__main__":
    main()
