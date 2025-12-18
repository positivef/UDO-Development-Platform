#!/usr/bin/env python
"""
System Rules Validation Script
[EMOJI]-[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]

[EMOJI]: .claude/ [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]

[EMOJI] [EMOJI]:
- Level 1 (CRITICAL): [EMOJI] [EMOJI] [EMOJI] [EMOJI] (Git hooks, [EMOJI] [EMOJI])
- Level 2 (IMPORTANT): [EMOJI] [EMOJI] [EMOJI] ([EMOJI] [EMOJI], [EMOJI])
- Level 3 (RECOMMENDED): [EMOJI] [EMOJI] [EMOJI] [EMOJI]

[EMOJI]:
  python scripts/validate_system_rules.py
  python scripts/validate_system_rules.py --fix  # [EMOJI] [EMOJI] [EMOJI]

Author: System Validation Team
Date: 2025-12-13
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum


class ValidationLevel(Enum):
    CRITICAL = "CRITICAL"    # [EMOJI] [EMOJI] ([EMOJI] [EMOJI] [EMOJI])
    IMPORTANT = "IMPORTANT"  # 🟡 [EMOJI] ([EMOJI] [EMOJI])
    RECOMMENDED = "RECOMMENDED"  # 🟢 [EMOJI] ([EMOJI] [EMOJI])


@dataclass
class ValidationResult:
    """[EMOJI] [EMOJI]"""
    level: ValidationLevel
    rule_file: str
    rule_section: str
    check_name: str
    passed: bool
    message: str
    fix_available: bool = False
    fix_command: str = ""


class SystemRulesValidator:
    """[EMOJI] [EMOJI] [EMOJI]"""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.claude_rules = repo_root / ".claude"
        self.results: List[ValidationResult] = []

    def validate_all(self) -> List[ValidationResult]:
        """[EMOJI] [EMOJI] [EMOJI]"""
        print("[VALIDATION] System Rules Validation Starting...")
        print(f"Repository: {self.repo_root}")
        print(f"Rules Location: {self.claude_rules}\n")

        # 1. Obsidian [EMOJI] [EMOJI] [EMOJI]
        self.validate_obsidian_sync_rules()

        # 2. Git Workflow [EMOJI] [EMOJI]
        self.validate_git_workflow_rules()

        # 3. Documentation [EMOJI] [EMOJI]
        self.validate_documentation_rules()

        # 4. Innovation Safety [EMOJI] [EMOJI] (NEW)
        self.validate_innovation_safety_rules()

        # 5. Error Resolution [EMOJI] [EMOJI] (NEW)
        self.validate_error_resolution_rules()

        return self.results

    def validate_obsidian_sync_rules(self):
        """OBSIDIAN_SYNC_RULES.md [EMOJI]"""
        rule_file = "OBSIDIAN_SYNC_RULES.md"

        # Check 1: Git Hook [EMOJI]
        hook_path = self.repo_root / ".git" / "hooks" / "post-commit"
        if not hook_path.exists():
            self.results.append(ValidationResult(
                level=ValidationLevel.CRITICAL,
                rule_file=rule_file,
                rule_section="Git Hook [EMOJI] [EMOJI]",
                check_name="post-commit hook [EMOJI]",
                passed=False,
                message="[FAIL] post-commit hook[EMOJI] [EMOJI] [EMOJI]",
                fix_available=True,
                fix_command="python scripts/install_doc_hooks.py"
            ))
        else:
            # Check 2: Hook[EMOJI] Obsidian [EMOJI] [EMOJI] [EMOJI]
            hook_content = hook_path.read_text(encoding='utf-8')
            has_obsidian_sync = any([
                "obsidian" in hook_content.lower(),
                "[EMOJI]" in hook_content,
                "OBSIDIAN_VAULT" in hook_content
            ])

            if not has_obsidian_sync:
                self.results.append(ValidationResult(
                    level=ValidationLevel.CRITICAL,
                    rule_file=rule_file,
                    rule_section="Git Hook [EMOJI] [EMOJI]",
                    check_name="Obsidian [EMOJI] [EMOJI] [EMOJI]",
                    passed=False,
                    message="[FAIL] post-commit hook[EMOJI] Obsidian [EMOJI] [EMOJI] [EMOJI]",
                    fix_available=True,
                    fix_command="Manual: Add Obsidian sync to .git/hooks/post-commit"
                ))
            else:
                self.results.append(ValidationResult(
                    level=ValidationLevel.CRITICAL,
                    rule_file=rule_file,
                    rule_section="Git Hook [EMOJI] [EMOJI]",
                    check_name="Obsidian [EMOJI] [EMOJI] [EMOJI]",
                    passed=True,
                    message="[OK] post-commit hook[EMOJI] Obsidian [EMOJI] [EMOJI]"
                ))

        # Check 3: [EMOJI] [EMOJI] [EMOJI]
        expected_triggers = [
            r"FILES_CHANGED.*(>=\s*3|-ge\s+3)",  # 3+ files (supports >= or -ge syntax)
            r"feat|feature|fix|bug|docs|refactor",  # Commit message patterns
        ]

        if hook_path.exists():
            hook_content = hook_path.read_text(encoding='utf-8')
            triggers_found = sum(1 for pattern in expected_triggers if re.search(pattern, hook_content))

            if triggers_found >= len(expected_triggers):
                self.results.append(ValidationResult(
                    level=ValidationLevel.IMPORTANT,
                    rule_file=rule_file,
                    rule_section="[EMOJI] [EMOJI]",
                    check_name="[EMOJI] [EMOJI] [EMOJI]",
                    passed=True,
                    message=f"[OK] {triggers_found}/{len(expected_triggers)} [EMOJI] [EMOJI] [EMOJI]"
                ))
            else:
                self.results.append(ValidationResult(
                    level=ValidationLevel.IMPORTANT,
                    rule_file=rule_file,
                    rule_section="[EMOJI] [EMOJI]",
                    check_name="[EMOJI] [EMOJI] [EMOJI]",
                    passed=False,
                    message=f"[WARN] {triggers_found}/{len(expected_triggers)} [EMOJI] [EMOJI] [EMOJI]",
                    fix_available=True,
                    fix_command="Manual: Add missing trigger conditions to hook"
                ))

        # Check 4: [EMOJI] [EMOJI] [EMOJI]
        required_scripts = [
            ("scripts/obsidian_auto_sync.py", "AI v2.0 [EMOJI] [EMOJI]"),
            ("scripts/obsidian_append.py", "Fallback append [EMOJI]"),
        ]

        for script_path, description in required_scripts:
            full_path = self.repo_root / script_path
            if not full_path.exists():
                # obsidian_auto_sync.py[EMOJI] CRITICAL ([EMOJI] [EMOJI])
                level = ValidationLevel.CRITICAL if "auto_sync" in script_path else ValidationLevel.IMPORTANT
                self.results.append(ValidationResult(
                    level=level,
                    rule_file=rule_file,
                    rule_section="[EMOJI] [EMOJI]",
                    check_name=f"{script_path} [EMOJI]",
                    passed=False,
                    message=f"[FAIL] {description} [EMOJI] [EMOJI]: {script_path}",
                    fix_available=True,
                    fix_command=f"TODO: Implement {script_path}"
                ))
            else:
                self.results.append(ValidationResult(
                    level=ValidationLevel.IMPORTANT,
                    rule_file=rule_file,
                    rule_section="[EMOJI] [EMOJI]",
                    check_name=f"{script_path} [EMOJI]",
                    passed=True,
                    message=f"[OK] {description} [EMOJI]"
                ))

    def validate_git_workflow_rules(self):
        """Git Workflow [EMOJI] [EMOJI]"""
        rule_file = "RULES.md"

        # Check 1: Pre-commit hook [EMOJI]
        precommit_path = self.repo_root / ".git" / "hooks" / "pre-commit"
        if precommit_path.exists():
            self.results.append(ValidationResult(
                level=ValidationLevel.IMPORTANT,
                rule_file=rule_file,
                rule_section="Git Workflow",
                check_name="pre-commit hook [EMOJI]",
                passed=True,
                message="[OK] pre-commit hook [EMOJI]"
            ))
        else:
            self.results.append(ValidationResult(
                level=ValidationLevel.IMPORTANT,
                rule_file=rule_file,
                rule_section="Git Workflow",
                check_name="pre-commit hook [EMOJI]",
                passed=False,
                message="[WARN] pre-commit hook [EMOJI] ([EMOJI]: Constitutional Guard)",
                fix_available=True,
                fix_command="python scripts/install_standard_git_hooks.py"
            ))

    def validate_documentation_rules(self):
        """Documentation [EMOJI] [EMOJI]"""
        rule_file = "RULES.md"

        # Check 1: docs/ [EMOJI] [EMOJI]
        docs_dir = self.repo_root / "docs"
        required_folders = ["sessions", "features", "guides", "architecture"]

        for folder in required_folders:
            folder_path = docs_dir / folder
            if not folder_path.exists():
                self.results.append(ValidationResult(
                    level=ValidationLevel.RECOMMENDED,
                    rule_file=rule_file,
                    rule_section="Documentation [EMOJI]",
                    check_name=f"docs/{folder}/ [EMOJI]",
                    passed=False,
                    message=f"[WARN] docs/{folder}/ [EMOJI] [EMOJI]",
                    fix_available=True,
                    fix_command=f"mkdir -p docs/{folder}"
                ))
            else:
                self.results.append(ValidationResult(
                    level=ValidationLevel.RECOMMENDED,
                    rule_file=rule_file,
                    rule_section="Documentation [EMOJI]",
                    check_name=f"docs/{folder}/ [EMOJI]",
                    passed=True,
                    message=f"[OK] docs/{folder}/ [EMOJI]"
                ))

    def validate_innovation_safety_rules(self):
        """INNOVATION_SAFETY_PRINCIPLES.md [EMOJI]"""
        rule_file = "INNOVATION_SAFETY_PRINCIPLES.md"

        # Check 1: Design Review [EMOJI] [EMOJI] (Pattern 4)
        # [EMOJI] [EMOJI] 3[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] docs/*_DESIGN_REVIEW.md [EMOJI]
        design_docs = list((self.repo_root / "docs").glob("*_DESIGN_REVIEW.md"))

        # Check 2: scripts/ [EMOJI] [EMOJI] [EMOJI] [EMOJI]
        scripts_dir = self.repo_root / "scripts"
        required_automation = [
            ("obsidian_auto_sync.py", "Obsidian [EMOJI] [EMOJI]"),
            ("validate_system_rules.py", "[EMOJI] [EMOJI] [EMOJI]"),
        ]

        for script_file, description in required_automation:
            script_path = scripts_dir / script_file
            if not script_path.exists():
                self.results.append(ValidationResult(
                    level=ValidationLevel.IMPORTANT,
                    rule_file=rule_file,
                    rule_section="[EMOJI] [EMOJI]",
                    check_name=f"{script_file} [EMOJI]",
                    passed=False,
                    message=f"[FAIL] {description} [EMOJI] [EMOJI]",
                    fix_available=True,
                    fix_command=f"Implement {script_file}"
                ))
            else:
                self.results.append(ValidationResult(
                    level=ValidationLevel.IMPORTANT,
                    rule_file=rule_file,
                    rule_section="[EMOJI] [EMOJI]",
                    check_name=f"{script_file} [EMOJI]",
                    passed=True,
                    message=f"[OK] {description} [EMOJI]"
                ))

        # Check 3: .git/hooks/ [EMOJI] [EMOJI]
        hooks_dir = self.repo_root / ".git" / "hooks"
        if not hooks_dir.exists():
            self.results.append(ValidationResult(
                level=ValidationLevel.CRITICAL,
                rule_file=rule_file,
                rule_section="Git Hooks",
                check_name=".git/hooks/ [EMOJI]",
                passed=False,
                message="[FAIL] Git hooks [EMOJI] [EMOJI]",
                fix_available=False,
                fix_command="git init"
            ))
        else:
            self.results.append(ValidationResult(
                level=ValidationLevel.RECOMMENDED,
                rule_file=rule_file,
                rule_section="Git Hooks",
                check_name=".git/hooks/ [EMOJI]",
                passed=True,
                message="[OK] Git hooks [EMOJI] [EMOJI]"
            ))

    def validate_error_resolution_rules(self):
        """OBSIDIAN_AUTO_SEARCH.md + 3-Tier Error Resolution [EMOJI]"""
        rule_file = "OBSIDIAN_AUTO_SEARCH.md"

        # Check 1: unified_error_resolver.py [EMOJI]
        resolver_path = self.repo_root / "scripts" / "unified_error_resolver.py"
        if not resolver_path.exists():
            self.results.append(ValidationResult(
                level=ValidationLevel.CRITICAL,
                rule_file=rule_file,
                rule_section="3-Tier Error Resolution",
                check_name="unified_error_resolver.py [EMOJI]",
                passed=False,
                message="[FAIL] 3-Tier [EMOJI] [EMOJI] [EMOJI] [EMOJI]",
                fix_available=True,
                fix_command="Implement scripts/unified_error_resolver.py"
            ))
        else:
            # Check 2: 3-Tier [EMOJI] [EMOJI] [EMOJI] (Tier 1/2/3 [EMOJI])
            resolver_content = resolver_path.read_text(encoding='utf-8')
            has_tier1 = "tier1" in resolver_content.lower() or "obsidian" in resolver_content.lower()
            has_tier2 = "tier2" in resolver_content.lower() or "context7" in resolver_content.lower()
            has_tier3 = "tier3" in resolver_content.lower() or "user" in resolver_content.lower()

            if has_tier1 and has_tier2 and has_tier3:
                self.results.append(ValidationResult(
                    level=ValidationLevel.CRITICAL,
                    rule_file=rule_file,
                    rule_section="3-Tier Error Resolution",
                    check_name="3-Tier [EMOJI] [EMOJI]",
                    passed=True,
                    message="[OK] Tier 1/2/3 [EMOJI] [EMOJI]"
                ))
            else:
                self.results.append(ValidationResult(
                    level=ValidationLevel.CRITICAL,
                    rule_file=rule_file,
                    rule_section="3-Tier Error Resolution",
                    check_name="3-Tier [EMOJI] [EMOJI]",
                    passed=False,
                    message=f"[FAIL] [EMOJI] Tier [EMOJI] (T1:{has_tier1}, T2:{has_tier2}, T3:{has_tier3})",
                    fix_available=True,
                    fix_command="Complete 3-Tier implementation"
                ))

        # Check 3: Obsidian [EMOJI] [EMOJI] [EMOJI]
        obsidian_vault = os.getenv("OBSIDIAN_VAULT_PATH", str(Path.home() / "Documents" / "Obsidian Vault"))
        dev_log_dir = Path(obsidian_vault) / "[EMOJI]"

        if not dev_log_dir.exists():
            self.results.append(ValidationResult(
                level=ValidationLevel.IMPORTANT,
                rule_file=rule_file,
                rule_section="Tier 1 (Obsidian)",
                check_name="[EMOJI] [EMOJI] [EMOJI]",
                passed=False,
                message=f"[WARN] Obsidian [EMOJI] [EMOJI] [EMOJI]: {dev_log_dir}",
                fix_available=True,
                fix_command=f"mkdir -p '{dev_log_dir}'"
            ))
        else:
            self.results.append(ValidationResult(
                level=ValidationLevel.IMPORTANT,
                rule_file=rule_file,
                rule_section="Tier 1 (Obsidian)",
                check_name="[EMOJI] [EMOJI] [EMOJI]",
                passed=True,
                message=f"[OK] Obsidian [EMOJI] [EMOJI]"
            ))

    def print_summary(self):
        """[EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
        print("\n" + "="*80)
        print("[SUMMARY] Validation Summary")
        print("="*80 + "\n")

        # [EMOJI] [EMOJI]
        stats = {level: {"passed": 0, "failed": 0} for level in ValidationLevel}

        for result in self.results:
            if result.passed:
                stats[result.level]["passed"] += 1
            else:
                stats[result.level]["failed"] += 1

        # [EMOJI] [EMOJI]
        for level in [ValidationLevel.CRITICAL, ValidationLevel.IMPORTANT, ValidationLevel.RECOMMENDED]:
            total = stats[level]["passed"] + stats[level]["failed"]
            passed = stats[level]["passed"]
            failed = stats[level]["failed"]

            icon = "[!]" if level == ValidationLevel.CRITICAL else "[*]" if level == ValidationLevel.IMPORTANT else "[+]"
            print(f"{icon} {level.value}: {passed}/{total} passed ({failed} failed)")

        print("\n" + "="*80)
        print("[DETAILS] Detailed Results")
        print("="*80 + "\n")

        # [EMOJI] [EMOJI] [EMOJI] [EMOJI]
        failed_results = [r for r in self.results if not r.passed]

        if not failed_results:
            print("[OK] All checks passed! System rules are properly implemented.\n")
        else:
            for result in failed_results:
                icon = "[!]" if result.level == ValidationLevel.CRITICAL else "[*]" if result.level == ValidationLevel.IMPORTANT else "[+]"
                print(f"{icon} [{result.level.value}] {result.check_name}")
                print(f"   Rule: {result.rule_file} / {result.rule_section}")
                print(f"   {result.message}")
                if result.fix_available:
                    print(f"   Fix: {result.fix_command}")
                print()

        # [EMOJI] [EMOJI]
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        pass_rate = (passed / total * 100) if total > 0 else 0

        print("="*80)
        print(f"[RESULT] Overall Pass Rate: {passed}/{total} ({pass_rate:.1f}%)")
        print("="*80 + "\n")

        # Critical [EMOJI] [EMOJI] exit code 1
        critical_failures = [r for r in failed_results if r.level == ValidationLevel.CRITICAL]
        if critical_failures:
            print(f"[CRITICAL] {len(critical_failures)} CRITICAL issues found. System may not work as intended.\n")
            return 1

        return 0


def main():
    """[EMOJI] [EMOJI]"""
    repo_root = Path(__file__).resolve().parents[1]
    validator = SystemRulesValidator(repo_root)

    # [EMOJI] [EMOJI]
    results = validator.validate_all()

    # [EMOJI] [EMOJI]
    exit_code = validator.print_summary()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
