#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows Task Scheduler Auto-Backup Setup
Created: 2025-12-23
Purpose: Schedule automatic backup of untracked files every 30 minutes
"""

import subprocess
import sys
from pathlib import Path

# Windows console encoding fix
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")


def setup_windows_task():
    """Windows Task Scheduler에 자동 백업 등록"""

    # Get absolute paths
    repo_root = Path(__file__).parent.parent.absolute()
    script_path = repo_root / "scripts" / "auto_backup_untracked.py"
    python_exe = repo_root / ".venv" / "Scripts" / "python.exe"

    # Verify paths exist
    if not script_path.exists():
        print(f"[FAIL] Error: Backup script not found: {script_path}")
        return False

    if not python_exe.exists():
        print(f"[FAIL] Error: Python executable not found: {python_exe}")
        print("   Make sure virtual environment is activated")
        return False

    print("[*] Git Auto-Backup Setup")
    print("=" * 50)
    print(f"Script: {script_path}")
    print(f"Python: {python_exe}")
    print()

    # Create scheduled task
    task_name = "Git Auto Backup - UDO Platform"

    # Windows schtasks command
    cmd = [
        "schtasks",
        "/create",
        "/tn",
        task_name,
        "/tr",
        f'"{python_exe}" "{script_path}" --backup',
        "/sc",
        "minute",
        "/mo",
        "30",
        "/f",  # Force (overwrites if exists)
    ]

    print("Creating scheduled task...")
    print(f"Command: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            print("[OK] Automatic backup scheduled successfully!")
            print()
            print("Task Details:")
            print(f"  Name: {task_name}")
            print("  Frequency: Every 30 minutes")
            print("  Action: Backup untracked files")
            print("  Location: D:/git-untracked-backups/")
            print()
            print("To verify:")
            print(f'  schtasks /query /tn "{task_name}"')
            print()
            print("To disable:")
            print(f'  schtasks /delete /tn "{task_name}" /f')
            print()
            return True
        else:
            print("Failed to create scheduled task")
            print(f"Error: {result.stderr}")
            print()
            print("Possible causes:")
            print("  - Not running as Administrator")
            print("  - Task Scheduler service not running")
            print()
            print("Try running:")
            print("  1. Open PowerShell as Administrator")
            print("  2. Run: python scripts/setup_auto_backup.py")
            return False

    except Exception as e:
        print(f"[FAIL] Exception occurred: {e}")
        return False


def verify_task():
    """Verify that the scheduled task exists and is enabled"""

    task_name = "Git Auto Backup - UDO Platform"

    cmd = ["schtasks", "/query", "/tn", task_name, "/fo", "LIST"]

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            print("\n[*] Task Status:")
            print(result.stdout)
            return True
        else:
            print(f"\n[WARN]  Task not found: {task_name}")
            return False

    except Exception as e:
        print(f"[FAIL] Error checking task: {e}")
        return False


def main():
    """Main entry point"""

    # Check if running on Windows
    if sys.platform != "win32":
        print("[FAIL] This script is for Windows only")
        print("   On Unix/Mac, use cron instead:")
        print("   crontab -e")
        print("   */30 * * * * cd /path/to/repo && python scripts/auto_backup_untracked.py --backup")
        sys.exit(1)

    # Setup task
    success = setup_windows_task()

    if success:
        # Verify task
        verify_task()

        print("\n[OK] Setup complete!")
        print("\nNext steps:")
        print("  1. Wait 30 minutes or manually run backup:")
        print("     python scripts/auto_backup_untracked.py --backup")
        print("  2. Check backup directory:")
        print("     dir D:\\git-untracked-backups")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
