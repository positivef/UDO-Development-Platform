# scripts/obsidian_tag_enforcer.py
"""Utility to automatically add standardized tags to Obsidian markdown files.

The goal is to make the *Training‑free* knowledge‑reuse mechanism fast:
- Search for a set of target files (e.g., docs/OBSIDIAN_LOG_*.md, docs/Development_History.md)
- Insert one or more tags (``#success``, ``#failure``, ``#insight``) if they are missing.

The script can be invoked from the command line or imported by other
automation scripts (e.g., ``obsidian_knowledge_sync.py``).
"""

import pathlib
import re
from typing import List

# ---------------------------------------------------------------------------
# Configuration – adjust paths/tags here if the project structure changes.
# ---------------------------------------------------------------------------
BASE_DIR = pathlib.Path(__file__).resolve().parents[2]  # project root
DOCS_DIR = BASE_DIR / "docs"
TARGET_GLOBS = ["OBSIDIAN_LOG_*.md", "Development_History.md", "Refactoring_Validation_Summary.md"]
DEFAULT_TAGS = ["#success", "#failure", "#insight"]


def _load_file(path: pathlib.Path) -> str:
    """Read a markdown file and return its content as a string."""
    return path.read_text(encoding="utf-8")


def _save_file(path: pathlib.Path, content: str) -> None:
    """Write ``content`` back to ``path`` using UTF‑8 encoding."""
    path.write_text(content, encoding="utf-8")


def _ensure_tags(content: str, tags: List[str]) -> str:
    """Add any missing ``tags`` to the top of the markdown document.

    The function looks for a YAML front‑matter block (``---``) – if present,
    tags are inserted after the closing ``---`` line.  If no front‑matter is
    found, tags are added as the first line of the file.
    """
    # Normalise line endings for easier processing
    lines = content.splitlines()
    # Detect front‑matter block
    if lines and lines[0].strip() == "---":
        # Find closing ``---``
        try:
            end_idx = lines[1:].index("---") + 1
        except ValueError:
            # No closing delimiter – treat whole file as body
            end_idx = -1
        # Insert tags after the front‑matter block
        insertion_point = end_idx + 1 if end_idx != -1 else len(lines)
    else:
        insertion_point = 0

    # Build a tag line – ensure each tag appears only once
    existing = set(re.findall(r"#\w+", "\n".join(lines)))
    new_tags = [t for t in tags if t not in existing]
    if not new_tags:
        return content  # nothing to add
    tag_line = " ".join(new_tags)
    # Insert the tag line
    lines.insert(insertion_point, tag_line)
    return "\n".join(lines) + "\n"


def process_file(path: pathlib.Path, tags: List[str] = None) -> bool:
    """Add missing tags to ``path``.

    Returns ``True`` if the file was modified, ``False`` otherwise.
    """
    if tags is None:
        tags = DEFAULT_TAGS
    original = _load_file(path)
    updated = _ensure_tags(original, tags)
    if updated != original:
        _save_file(path, updated)
        return True
    return False


def main() -> None:
    """Entry point for command‑line usage.

    Example::
        python -m scripts.obsidian_tag_enforcer
    """
    modified_files = []
    for pattern in TARGET_GLOBS:
        for file_path in DOCS_DIR.glob(pattern):
            if process_file(file_path):
                modified_files.append(str(file_path))
    if modified_files:
        print("Added tags to:")
        for f in modified_files:
            print(f"  - {f}")
    else:
        print("All target files already contain the required tags.")


if __name__ == "__main__":
    main()
