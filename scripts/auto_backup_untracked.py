#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatic Backup System for Untracked Files
Created: 2025-12-23
Purpose: Prevent data loss from git clean or accidental deletion

This script:
1. Detects all untracked files in the Git repository
2. Creates timestamped backups before any dangerous operation
3. Can be run manually or scheduled (every 30 minutes recommended)
4. Preserves file structure in backup directory
"""

import subprocess
import os
import shutil
from pathlib import Path
from datetime import datetime
import json
import sys

# Windows console encoding fix
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configuration
BACKUP_ROOT = Path("D:/git-untracked-backups")  # External drive recommended
MAX_BACKUPS = 50  # Keep last 50 backups
BACKUP_METADATA_FILE = "backup_metadata.json"

# Critical file extensions to always backup
CRITICAL_EXTENSIONS = {
    '.tsx', '.ts', '.jsx', '.js', '.py', '.md',
    '.json', '.yaml', '.yml', '.toml', '.env',
    '.sql', '.sh', '.bat', '.ps1'
}

def get_repo_root():
    """Get the Git repository root directory."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        print("❌ Error: Not a Git repository")
        sys.exit(1)

def get_untracked_files():
    """Get list of untracked files from Git."""
    try:
        result = subprocess.run(
            ['git', 'ls-files', '--others', '--exclude-standard'],
            capture_output=True,
            text=True,
            check=True
        )
        files = [line for line in result.stdout.strip().split('\n') if line]
        return files
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting untracked files: {e}")
        return []

def filter_critical_files(files):
    """Filter files to include only critical ones."""
    critical_files = []
    for file_path in files:
        ext = Path(file_path).suffix.lower()
        if ext in CRITICAL_EXTENSIONS:
            critical_files.append(file_path)
    return critical_files

def create_backup(repo_root, untracked_files):
    """Create a timestamped backup of untracked files."""
    if not untracked_files:
        print("ℹ️  No untracked files to backup")
        return None

    # Create backup directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = BACKUP_ROOT / f"backup_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Backup metadata
    metadata = {
        "timestamp": timestamp,
        "datetime": datetime.now().isoformat(),
        "repo_root": str(repo_root),
        "files": []
    }

    # Copy files
    backed_up_count = 0
    for rel_path in untracked_files:
        src = repo_root / rel_path
        dst = backup_dir / rel_path

        try:
            # Create parent directories
            dst.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(src, dst)

            # Add to metadata
            metadata["files"].append({
                "path": rel_path,
                "size": src.stat().st_size,
                "modified": src.stat().st_mtime
            })

            backed_up_count += 1
            print(f"  ✅ {rel_path}")

        except Exception as e:
            print(f"  ⚠️  Failed to backup {rel_path}: {e}")

    # Save metadata
    with open(backup_dir / BACKUP_METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n✅ Backed up {backed_up_count} files to: {backup_dir}")
    return backup_dir

def cleanup_old_backups():
    """Remove old backups, keeping only the most recent MAX_BACKUPS."""
    if not BACKUP_ROOT.exists():
        return

    # Get all backup directories
    backups = sorted(
        [d for d in BACKUP_ROOT.iterdir() if d.is_dir() and d.name.startswith('backup_')],
        key=lambda x: x.name,
        reverse=True
    )

    # Remove old backups
    if len(backups) > MAX_BACKUPS:
        for old_backup in backups[MAX_BACKUPS:]:
            try:
                shutil.rmtree(old_backup)
                print(f"🗑️  Removed old backup: {old_backup.name}")
            except Exception as e:
                print(f"⚠️  Failed to remove {old_backup.name}: {e}")

def list_backups():
    """List all available backups."""
    if not BACKUP_ROOT.exists():
        print("ℹ️  No backups found")
        return

    backups = sorted(
        [d for d in BACKUP_ROOT.iterdir() if d.is_dir() and d.name.startswith('backup_')],
        key=lambda x: x.name,
        reverse=True
    )

    if not backups:
        print("ℹ️  No backups found")
        return

    print(f"\n📦 Available backups ({len(backups)} total):\n")
    for i, backup in enumerate(backups[:10], 1):  # Show latest 10
        metadata_file = backup / BACKUP_METADATA_FILE
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            file_count = len(metadata.get('files', []))
            dt = metadata.get('datetime', 'Unknown')
        else:
            file_count = '?'
            dt = 'Unknown'

        print(f"{i}. {backup.name}")
        print(f"   Date: {dt}")
        print(f"   Files: {file_count}")
        print()

def restore_backup(backup_name, repo_root):
    """Restore files from a backup."""
    backup_dir = BACKUP_ROOT / backup_name

    if not backup_dir.exists():
        print(f"❌ Backup not found: {backup_name}")
        return

    metadata_file = backup_dir / BACKUP_METADATA_FILE
    if not metadata_file.exists():
        print(f"❌ Backup metadata not found")
        return

    # Load metadata
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    print(f"\n📦 Restoring backup from: {metadata.get('datetime', 'Unknown')}")
    print(f"Files to restore: {len(metadata.get('files', []))}\n")

    # Confirm
    response = input("Continue with restore? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Restore cancelled")
        return

    # Restore files
    restored_count = 0
    for file_info in metadata.get('files', []):
        rel_path = file_info['path']
        src = backup_dir / rel_path
        dst = repo_root / rel_path

        try:
            # Create parent directories
            dst.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(src, dst)
            restored_count += 1
            print(f"  ✅ {rel_path}")

        except Exception as e:
            print(f"  ⚠️  Failed to restore {rel_path}: {e}")

    print(f"\n✅ Restored {restored_count} files")

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Backup untracked Git files')
    parser.add_argument('--backup', action='store_true', help='Create a new backup')
    parser.add_argument('--list', action='store_true', help='List available backups')
    parser.add_argument('--restore', type=str, metavar='NAME', help='Restore a backup')
    parser.add_argument('--all', action='store_true', help='Backup all untracked files (not just critical)')

    args = parser.parse_args()

    repo_root = get_repo_root()

    if args.list:
        list_backups()
        return

    if args.restore:
        restore_backup(args.restore, repo_root)
        return

    if args.backup or len(sys.argv) == 1:  # Default action
        print("🔍 Scanning for untracked files...\n")
        untracked_files = get_untracked_files()

        if not args.all:
            # Filter to critical files only
            untracked_files = filter_critical_files(untracked_files)
            print(f"Found {len(untracked_files)} critical untracked files\n")
        else:
            print(f"Found {len(untracked_files)} untracked files\n")

        if untracked_files:
            create_backup(repo_root, untracked_files)
            cleanup_old_backups()
        else:
            print("✅ No files to backup")

if __name__ == '__main__':
    main()
