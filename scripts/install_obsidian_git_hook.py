"""
Install a non-blocking Git hook to append commit context to Obsidian daily notes.

Balanced mode:
- Opt-in per developer
- Best-effort: hook never blocks commit on failure
- Explicit vault/path configuration via env or defaults

Usage (PowerShell/cmd from repo root):
  python scripts\install_obsidian_git_hook.py --vault "C:\Users\user\Documents\Obsidian Vault"

Uninstall:
  delete .git/hooks/post-commit (if created by this script)
"""

import argparse
import os
from pathlib import Path

HOOK_NAME = "post-commit"

TEMPLATE = """#!/usr/bin/env python
import sys
from pathlib import Path
from datetime import datetime

# Config
VAULT = Path(r"{vault}")
DAILY_DIR = VAULT / "개발일지"
REPO_ROOT = Path("{repo_root}")
APPEND_FILE = REPO_ROOT / "tmp" / "obsidian_append.txt"

def main():
    try:
        DAILY_DIR.mkdir(parents=True, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        note = DAILY_DIR / f"{today}.md"
        if not note.exists():
            note.write_text(f"# Daily Log {today}\\n\\n", encoding="utf-8")

        if not APPEND_FILE.exists():
            return 0  # nothing to append

        text = APPEND_FILE.read_text(encoding="utf-8")
        with open(note, "a", encoding="utf-8") as f:
            f.write("\\n" + text + "\\n")
    except Exception as e:
        # Best-effort: never block commit
        sys.stderr.write(f"[obsidian-hook] skipped: {e}\\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""


def install_hook(repo_root: Path, vault_path: Path):
    hooks_dir = repo_root / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hooks_dir / HOOK_NAME

    content = TEMPLATE.format(vault=str(vault_path), repo_root=str(repo_root))
    hook_path.write_text(content, encoding="utf-8")
    hook_path.chmod(0o755)
    print(f"Installed hook: {hook_path}")
    print("Best-effort: hook will not block commits on failure.")


def main():
    parser = argparse.ArgumentParser(description="Install a best-effort Obsidian post-commit hook.")
    parser.add_argument("--vault", required=True, help="Path to Obsidian Vault (absolute)")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    vault_path = Path(args.vault).resolve()

    install_hook(repo_root, vault_path)


if __name__ == "__main__":
    main()
