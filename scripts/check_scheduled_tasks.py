"""
Scheduled Tasks Checker - Session Start Auto-Search

Automatically searches Obsidian vault for upcoming scheduled tasks at session start.
Integrates with 3-Tier Search system for reliability.

Usage:
    python scripts/check_scheduled_tasks.py
    python scripts/check_scheduled_tasks.py --verbose
    python scripts/check_scheduled_tasks.py --weeks-ahead 2
"""

import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json


@dataclass
class ScheduledTask:
    """Represents a scheduled task from Obsidian"""

    title: str
    priority: str
    due_date: Optional[datetime]
    context: str
    prerequisites: List[str]
    related_links: List[str]
    estimated_time: str
    notes: str
    line_number: int
    is_completed: bool
    days_until_due: Optional[int] = None

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "priority": self.priority,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "context": self.context,
            "prerequisites": self.prerequisites,
            "related_links": self.related_links,
            "estimated_time": self.estimated_time,
            "notes": self.notes,
            "line_number": self.line_number,
            "is_completed": self.is_completed,
            "days_until_due": self.days_until_due,
        }


class ScheduledTasksChecker:
    """Checks for upcoming scheduled tasks in Obsidian vault"""

    def __init__(self, vault_path: Optional[str] = None):
        """
        Initialize checker

        Args:
            vault_path: Path to Obsidian vault (uses env var or default if None)
        """
        if vault_path is None:
            vault_path = os.getenv("OBSIDIAN_VAULT_PATH")
            if not vault_path:
                vault_path = str(Path.home() / "Documents" / "Obsidian Vault")

        self.vault_path = Path(vault_path)
        self.scheduled_file = self.vault_path / "_System" / "Tasks" / "scheduled.md"

        if not self.scheduled_file.exists():
            raise FileNotFoundError(
                f"Scheduled tasks file not found: {self.scheduled_file}\n" "Please create it using the template."
            )

    def parse_scheduled_file(self) -> List[ScheduledTask]:
        """
        Parse scheduled.md file and extract tasks

        Returns:
            List of ScheduledTask objects
        """
        tasks = []

        with open(self.scheduled_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        current_task = None
        task_data = {}
        line_num = 0

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Task start: - [ ] or - [x]
            if stripped.startswith("- [ ]") or stripped.startswith("- [x]"):
                # Save previous task if exists
                if current_task:
                    tasks.append(self._create_task(task_data, line_num - 1))

                # Start new task
                is_completed = stripped.startswith("- [x]")
                title = stripped[6:].strip()

                # Extract bold title if present
                title_match = re.match(r"\*\*(.+?)\*\*", title)
                if title_match:
                    title = title_match.group(1)

                task_data = {
                    "title": title,
                    "is_completed": is_completed,
                    "line_number": line_num,
                    "priority": "P2",  # Default
                    "due_date": None,
                    "context": "",
                    "prerequisites": [],
                    "related_links": [],
                    "estimated_time": "",
                    "notes": "",
                }
                current_task = True

            # Task metadata lines
            elif current_task and stripped.startswith("- **"):
                key_match = re.match(r"- \*\*(\w+)\*\*:\s*(.+)", stripped)
                if key_match:
                    key = key_match.group(1).lower()
                    value = key_match.group(2).strip()

                    if key == "priority":
                        task_data["priority"] = value
                    elif key == "due":
                        task_data["due_date"] = self._parse_date(value)
                    elif key == "context":
                        task_data["context"] = value
                    elif key == "prerequisites":
                        task_data["prerequisites"] = [v.strip() for v in value.split(",")]
                    elif key == "related":
                        # Extract [[links]]
                        task_data["related_links"] = re.findall(r"\[\[(.+?)\]\]", value)
                    elif key == "estimated":
                        task_data["estimated_time"] = value
                    elif key == "notes":
                        task_data["notes"] = value

            # End of task (empty line or section header)
            elif current_task and (not stripped or stripped.startswith("#")):
                if task_data:
                    tasks.append(self._create_task(task_data, line_num))
                current_task = None
                task_data = {}

        # Save last task if exists
        if current_task and task_data:
            tasks.append(self._create_task(task_data, line_num))

        return tasks

    def _create_task(self, data: Dict, line_number: int) -> ScheduledTask:
        """Create ScheduledTask from parsed data"""
        due_date = data.get("due_date")
        days_until_due = None

        if due_date:
            delta = (due_date - datetime.now()).days
            days_until_due = delta

        return ScheduledTask(
            title=data.get("title", ""),
            priority=data.get("priority", "P2"),
            due_date=due_date,
            context=data.get("context", ""),
            prerequisites=data.get("prerequisites", []),
            related_links=data.get("related_links", []),
            estimated_time=data.get("estimated_time", ""),
            notes=data.get("notes", ""),
            line_number=line_number,
            is_completed=data.get("is_completed", False),
            days_until_due=days_until_due,
        )

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string in YYYY-MM-DD format"""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None

    def get_upcoming_tasks(
        self, weeks_ahead: int = 2, include_completed: bool = False
    ) -> Tuple[List[ScheduledTask], List[ScheduledTask], List[ScheduledTask]]:
        """
        Get upcoming, overdue, and this-week tasks

        Args:
            weeks_ahead: Number of weeks to look ahead
            include_completed: Include completed tasks

        Returns:
            Tuple of (upcoming_tasks, overdue_tasks, this_week_tasks)
        """
        all_tasks = self.parse_scheduled_file()

        if not include_completed:
            all_tasks = [t for t in all_tasks if not t.is_completed]

        now = datetime.now()
        end_date = now + timedelta(weeks=weeks_ahead)
        week_end = now + timedelta(days=7)

        upcoming_tasks = []
        overdue_tasks = []
        this_week_tasks = []

        for task in all_tasks:
            if task.due_date is None:
                continue

            if task.due_date < now:
                overdue_tasks.append(task)
            elif task.due_date <= week_end:
                this_week_tasks.append(task)
            elif task.due_date <= end_date:
                upcoming_tasks.append(task)

        # Sort by due date
        overdue_tasks.sort(key=lambda t: t.due_date if t.due_date else datetime.max)
        this_week_tasks.sort(key=lambda t: t.due_date if t.due_date else datetime.max)
        upcoming_tasks.sort(key=lambda t: t.due_date if t.due_date else datetime.max)

        return upcoming_tasks, overdue_tasks, this_week_tasks

    def format_summary(
        self,
        upcoming: List[ScheduledTask],
        overdue: List[ScheduledTask],
        this_week: List[ScheduledTask],
        verbose: bool = False,
    ) -> str:
        """
        Format tasks into a readable summary

        Args:
            upcoming: Upcoming tasks
            overdue: Overdue tasks
            this_week: This week tasks
            verbose: Include detailed info

        Returns:
            Formatted summary string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("[*] SCHEDULED TASKS CHECK")
        lines.append(f"Checked: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 60)

        # Overdue tasks (critical)
        if overdue:
            lines.append("\n[*] OVERDUE TASKS:")
            lines.append("-" * 60)
            for task in overdue:
                days_late = abs(task.days_until_due) if task.days_until_due else 0
                lines.append(f"  [{task.priority}] {task.title}")
                lines.append(f"      Due: {task.due_date.strftime('%Y-%m-%d')} ({days_late} days late)")
                if verbose and task.context:
                    lines.append(f"      Context: {task.context}")
                lines.append("")
        else:
            lines.append("\n[OK] No overdue tasks")

        # This week tasks
        if this_week:
            lines.append("\n[*] THIS WEEK (7 days):")
            lines.append("-" * 60)
            for task in this_week:
                days_left = task.days_until_due if task.days_until_due else 0
                lines.append(f"  [{task.priority}] {task.title}")
                lines.append(f"      Due: {task.due_date.strftime('%Y-%m-%d')} (in {days_left} days)")
                if verbose:
                    if task.context:
                        lines.append(f"      Context: {task.context}")
                    if task.estimated_time:
                        lines.append(f"      Estimated: {task.estimated_time}")
                lines.append("")
        else:
            lines.append("\n[OK] No tasks due this week")

        # Upcoming tasks
        if upcoming:
            lines.append("\n[*] UPCOMING (next 2 weeks):")
            lines.append("-" * 60)
            for task in upcoming:
                days_left = task.days_until_due if task.days_until_due else 0
                lines.append(f"  [{task.priority}] {task.title}")
                lines.append(f"      Due: {task.due_date.strftime('%Y-%m-%d')} (in {days_left} days)")
                if verbose and task.context:
                    lines.append(f"      Context: {task.context}")
                lines.append("")

        # Summary stats
        lines.append("\n" + "=" * 60)
        lines.append(f"Total: {len(overdue)} overdue, {len(this_week)} this week, {len(upcoming)} upcoming")
        lines.append("=" * 60)

        return "\n".join(lines)


def main():
    """Main entry point for CLI usage"""
    import argparse
    import sys

    # Fix Windows console encoding
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Check scheduled tasks in Obsidian")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--weeks-ahead", type=int, default=2, help="Weeks to look ahead (default: 2)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    try:
        checker = ScheduledTasksChecker()
        upcoming, overdue, this_week = checker.get_upcoming_tasks(weeks_ahead=args.weeks_ahead)

        if args.json:
            output = {
                "overdue": [t.to_dict() for t in overdue],
                "this_week": [t.to_dict() for t in this_week],
                "upcoming": [t.to_dict() for t in upcoming],
                "summary": {"total_overdue": len(overdue), "total_this_week": len(this_week), "total_upcoming": len(upcoming)},
            }
            print(json.dumps(output, indent=2))
        else:
            summary = checker.format_summary(upcoming, overdue, this_week, verbose=args.verbose)
            print(summary)

        # Exit code: 2 if overdue, 1 if this week, 0 otherwise
        if overdue:
            return 2
        elif this_week:
            return 1
        else:
            return 0

    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
