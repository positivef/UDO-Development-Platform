"""
Utility script to append a markdown snippet to today's Obsidian daily log.

Usage (Windows PowerShell):
  set PYTHONPATH=C:\Users\user\Documents\GitHub\UDO-Development-Platform
  python scripts\obsidian_append.py --vault "C:\Users\user\Documents\Obsidian Vault" --file tmp\obsidian_append.txt

This script:
- Creates the daily note under <vault>/개발일지/YYYY-MM-DD.md if missing
- Appends the given file content
"""

from pathlib import Path
from datetime import datetime
import argparse
import sys


def append_to_daily(vault_path: Path, content_path: Path) -> Path:
    vault_path = vault_path.resolve()
    daily_dir = vault_path / "개발일지"
    daily_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    note_path = daily_dir / f"{today}.md"
    if not note_path.exists():
        note_path.write_text(f"# Daily Log {today}\n\n", encoding="utf-8")

    if not content_path.exists():
        raise FileNotFoundError(f"Content file not found: {content_path}")

    text = content_path.read_text(encoding="utf-8")
    with open(note_path, "a", encoding="utf-8") as f:
        f.write("\n" + text + "\n")

    return note_path


def main():
    parser = argparse.ArgumentParser(description="Append content to today's Obsidian daily note.")
    parser.add_argument("--vault", required=True, help="Path to Obsidian Vault")
    parser.add_argument("--file", required=True, help="Path to markdown snippet to append")
    args = parser.parse_args()

    try:
        note_path = append_to_daily(Path(args.vault), Path(args.file))
        print(f"Appended to {note_path}")
    except Exception as e:
        print(f"Failed to append: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
