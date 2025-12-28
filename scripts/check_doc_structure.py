#!/usr/bin/env python3
"""
Documentation Structure Validator (Pre-commit Hook)
===================================================
Validates that documentation follows SSOT_REGISTRY.md structure.

Usage:
    python scripts/check_doc_structure.py [--fix]

Returns:
    0 if valid, 1 if errors found
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict
from datetime import datetime

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_ROOT = PROJECT_ROOT / "docs"

# Allowed files in docs/ root (from SSOT_REGISTRY.md)
ALLOWED_ROOT_FILES = {
    "README.md",
    "CURRENT.md",
    "SSOT_REGISTRY.md",
    "glossary.md",
    "FINAL_DOCUMENTATION_STRUCTURE.md",
    "openapi.yaml",
}

# Required folders (from SSOT_REGISTRY.md)
REQUIRED_FOLDERS = {
    "architecture",
    "features",
    "guides",
    "sessions",
    "analysis",
    "decisions",
    "proposals",
    "templates",
    "PRDs",
}

# Feature subfolders
FEATURE_SUBFOLDERS = {
    "kanban",
    "time-tracking",
    "uncertainty",
    "gi-ck",
    "obsidian",
    "ai-collaboration",
    "quality",
    "udo",
}

# Link pattern for markdown
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


class DocumentationValidator:
    """Validates documentation structure and links."""

    def __init__(self, docs_root: Path):
        self.docs_root = docs_root
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all(self) -> bool:
        """Run all validations."""
        print("=" * 60)
        print("Documentation Structure Validator")
        print("=" * 60)

        self._validate_root_files()
        self._validate_required_folders()
        self._validate_feature_folders()
        self._validate_links()
        self._validate_naming_conventions()

        # Print results
        if self.warnings:
            print(f"\n{len(self.warnings)} Warnings:")
            for w in self.warnings:
                print(f"  - {w}")

        if self.errors:
            print(f"\n{len(self.errors)} Errors:")
            for e in self.errors:
                print(f"  - {e}")
            print("\nValidation FAILED")
            return False
        else:
            print("\nValidation PASSED")
            return True

    def _validate_root_files(self):
        """Check only allowed files in docs/ root."""
        print("\n[1/5] Checking root files...")

        for item in self.docs_root.iterdir():
            if item.is_file():
                if item.name not in ALLOWED_ROOT_FILES:
                    self.errors.append(f"Unexpected file in docs/ root: {item.name} " f"(should be in a subfolder)")
                else:
                    print(f"  OK: {item.name}")

    def _validate_required_folders(self):
        """Check required folders exist."""
        print("\n[2/5] Checking required folders...")

        for folder in REQUIRED_FOLDERS:
            folder_path = self.docs_root / folder
            if not folder_path.exists():
                self.errors.append(f"Missing required folder: docs/{folder}/")
            else:
                file_count = len(list(folder_path.rglob("*")))
                print(f"  OK: {folder}/ ({file_count} items)")

    def _validate_feature_folders(self):
        """Check feature subfolders."""
        print("\n[3/5] Checking feature folders...")

        features_path = self.docs_root / "features"
        if not features_path.exists():
            return

        for subfolder in FEATURE_SUBFOLDERS:
            subfolder_path = features_path / subfolder
            if not subfolder_path.exists():
                self.warnings.append(f"Missing feature folder: features/{subfolder}/")
            else:
                file_count = len(list(subfolder_path.glob("*.md")))
                print(f"  OK: features/{subfolder}/ ({file_count} docs)")

    def _validate_links(self):
        """Check internal links are valid."""
        print("\n[4/5] Checking internal links...")

        broken_links = []
        checked_count = 0

        for md_file in self.docs_root.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
            except Exception:
                continue

            for match in LINK_PATTERN.finditer(content):
                link_text, link_path = match.groups()

                # Skip external links
                if link_path.startswith(("http://", "https://", "mailto:", "#")):
                    continue

                # Check relative link
                if link_path.startswith("../"):
                    target = (md_file.parent / link_path).resolve()
                else:
                    target = (md_file.parent / link_path).resolve()

                checked_count += 1

                if not target.exists():
                    broken_links.append(
                        {"file": str(md_file.relative_to(self.docs_root)), "link": link_path, "text": link_text}
                    )

        if broken_links:
            for bl in broken_links[:10]:  # Show first 10
                self.warnings.append(f"Broken link in {bl['file']}: [{bl['text']}]({bl['link']})")
            if len(broken_links) > 10:
                self.warnings.append(f"  ... and {len(broken_links) - 10} more")

        print(f"  Checked {checked_count} links, {len(broken_links)} broken")

    def _validate_naming_conventions(self):
        """Check file naming follows conventions."""
        print("\n[5/5] Checking naming conventions...")

        issues = []

        for md_file in self.docs_root.rglob("*.md"):
            name = md_file.stem

            # Check for spaces (should use underscores or hyphens)
            if " " in name:
                issues.append(f"Space in filename: {md_file.name}")

            # Check for lowercase requirement in some folders
            rel_path = md_file.relative_to(self.docs_root)
            if str(rel_path).startswith("templates/"):
                if name != name.lower().replace("_", "-"):
                    self.warnings.append(f"Template should use lowercase: {md_file.name}")

        if issues:
            for issue in issues:
                self.warnings.append(issue)

        print(f"  Found {len(issues)} naming issues")


def main():
    """Main entry point."""
    fix_mode = "--fix" in sys.argv

    validator = DocumentationValidator(DOCS_ROOT)
    success = validator.validate_all()

    if fix_mode and not success:
        print("\n[--fix mode] Attempting auto-fixes...")
        # Future: implement auto-fix logic
        print("  Auto-fix not yet implemented")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
