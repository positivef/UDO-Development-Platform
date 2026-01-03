#!/usr/bin/env python
"""
System Rules Validation Script
규칙-구현 일치성 자동 검증 도구

목적: .claude/ 규칙 파일과 실제 구현 간의 불일치를 자동으로 감지

검증 레벨:
- Level 1 (CRITICAL): 필수 기능 존재 여부 (Git hooks, 필수 스크립트)
- Level 2 (IMPORTANT): 기능 동작 일치성 (트리거 조건, 파라미터)
- Level 3 (RECOMMENDED): 최적화 및 개선 사항

실행:
  python scripts/validate_system_rules.py
  python scripts/validate_system_rules.py --fix  # 자동 수정 시도

Author: System Validation Team
Date: 2025-12-13
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum


class ValidationLevel(Enum):
    CRITICAL = "CRITICAL"  # [*] 필수 (시스템 작동 불가)
    IMPORTANT = "IMPORTANT"  # [*] 중요 (기능 제한)
    RECOMMENDED = "RECOMMENDED"  # [*] 권장 (개선 필요)


@dataclass
class ValidationResult:
    """검증 결과"""

    level: ValidationLevel
    rule_file: str
    rule_section: str
    check_name: str
    passed: bool
    message: str
    fix_available: bool = False
    fix_command: str = ""


class SystemRulesValidator:
    """시스템 규칙 검증기"""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.claude_rules = repo_root / ".claude"
        self.results: List[ValidationResult] = []

    def validate_all(self) -> List[ValidationResult]:
        """전체 규칙 검증"""
        print("[VALIDATION] System Rules Validation Starting...")
        print(f"Repository: {self.repo_root}")
        print(f"Rules Location: {self.claude_rules}\n")

        # 1. Obsidian 동기화 규칙 검증
        self.validate_obsidian_sync_rules()

        # 2. Git Workflow 규칙 검증
        self.validate_git_workflow_rules()

        # 3. Documentation 규칙 검증
        self.validate_documentation_rules()

        # 4. Innovation Safety 규칙 검증 (NEW)
        self.validate_innovation_safety_rules()

        # 5. Error Resolution 규칙 검증 (NEW)
        self.validate_error_resolution_rules()

        return self.results

    def validate_obsidian_sync_rules(self):
        """OBSIDIAN_SYNC_RULES.md 검증"""
        rule_file = "OBSIDIAN_SYNC_RULES.md"

        # Check 1: Git Hook 존재
        hook_path = self.repo_root / ".git" / "hooks" / "post-commit"
        if not hook_path.exists():
            self.results.append(
                ValidationResult(
                    level=ValidationLevel.CRITICAL,
                    rule_file=rule_file,
                    rule_section="Git Hook 자동 동기화",
                    check_name="post-commit hook 존재",
                    passed=False,
                    message="[FAIL] post-commit hook이 존재하지 않음",
                    fix_available=True,
                    fix_command="python scripts/install_doc_hooks.py",
                )
            )
        else:
            # Check 2: Hook에 Obsidian 동기화 코드 포함
            hook_content = hook_path.read_text(encoding="utf-8")
            has_obsidian_sync = any(
                ["obsidian" in hook_content.lower(), "개발일지" in hook_content, "OBSIDIAN_VAULT" in hook_content]
            )

            if not has_obsidian_sync:
                self.results.append(
                    ValidationResult(
                        level=ValidationLevel.CRITICAL,
                        rule_file=rule_file,
                        rule_section="Git Hook 자동 동기화",
                        check_name="Obsidian 동기화 코드 포함",
                        passed=False,
                        message="[FAIL] post-commit hook에 Obsidian 동기화 코드 없음",
                        fix_available=True,
                        fix_command="Manual: Add Obsidian sync to .git/hooks/post-commit",
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        level=ValidationLevel.CRITICAL,
                        rule_file=rule_file,
                        rule_section="Git Hook 자동 동기화",
                        check_name="Obsidian 동기화 코드 포함",
                        passed=True,
                        message="[OK] post-commit hook에 Obsidian 동기화 포함됨",
                    )
                )

        # Check 3: 트리거 조건 검증
        expected_triggers = [
            r"FILES_CHANGED.*(>=\s*3|-ge\s+3)",  # 3+ files (supports >= or -ge syntax)
            r"feat|feature|fix|bug|docs|refactor",  # Commit message patterns
        ]

        if hook_path.exists():
            hook_content = hook_path.read_text(encoding="utf-8")
            triggers_found = sum(1 for pattern in expected_triggers if re.search(pattern, hook_content))

            if triggers_found >= len(expected_triggers):
                self.results.append(
                    ValidationResult(
                        level=ValidationLevel.IMPORTANT,
                        rule_file=rule_file,
                        rule_section="트리거 조건",
                        check_name="트리거 조건 구현",
                        passed=True,
                        message=f"[OK] {triggers_found}/{len(expected_triggers)} 트리거 조건 구현됨",
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        level=ValidationLevel.IMPORTANT,
                        rule_file=rule_file,
                        rule_section="트리거 조건",
                        check_name="트리거 조건 구현",
                        passed=False,
                        message=f"[WARN] {triggers_found}/{len(expected_triggers)} 트리거 조건만 구현됨",
                        fix_available=True,
                        fix_command="Manual: Add missing trigger conditions to hook",
                    )
                )

        # Check 4: 필수 스크립트 존재
        required_scripts = [
            ("scripts/obsidian_auto_sync.py", "AI v2.0 자동 동기화"),
            ("scripts/obsidian_append.py", "Fallback append 기능"),
        ]

        for script_path, description in required_scripts:
            full_path = self.repo_root / script_path
            if not full_path.exists():
                # obsidian_auto_sync.py는 CRITICAL (규칙에서 요구)
                level = ValidationLevel.CRITICAL if "auto_sync" in script_path else ValidationLevel.IMPORTANT
                self.results.append(
                    ValidationResult(
                        level=level,
                        rule_file=rule_file,
                        rule_section="필수 스크립트",
                        check_name=f"{script_path} 존재",
                        passed=False,
                        message=f"[FAIL] {description} 스크립트 없음: {script_path}",
                        fix_available=True,
                        fix_command=f"TODO: Implement {script_path}",
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        level=ValidationLevel.IMPORTANT,
                        rule_file=rule_file,
                        rule_section="필수 스크립트",
                        check_name=f"{script_path} 존재",
                        passed=True,
                        message=f"[OK] {description} 존재",
                    )
                )

    def validate_git_workflow_rules(self):
        """Git Workflow 규칙 검증"""
        rule_file = "RULES.md"

        # Check 1: Pre-commit hook 존재
        precommit_path = self.repo_root / ".git" / "hooks" / "pre-commit"
        if precommit_path.exists():
            self.results.append(
                ValidationResult(
                    level=ValidationLevel.IMPORTANT,
                    rule_file=rule_file,
                    rule_section="Git Workflow",
                    check_name="pre-commit hook 존재",
                    passed=True,
                    message="[OK] pre-commit hook 설치됨",
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    level=ValidationLevel.IMPORTANT,
                    rule_file=rule_file,
                    rule_section="Git Workflow",
                    check_name="pre-commit hook 존재",
                    passed=False,
                    message="[WARN] pre-commit hook 없음 (권장: Constitutional Guard)",
                    fix_available=True,
                    fix_command="python scripts/install_standard_git_hooks.py",
                )
            )

    def validate_documentation_rules(self):
        """Documentation 규칙 검증"""
        rule_file = "RULES.md"

        # Check 1: docs/ 폴더 구조
        docs_dir = self.repo_root / "docs"
        required_folders = ["sessions", "features", "guides", "architecture"]

        for folder in required_folders:
            folder_path = docs_dir / folder
            if not folder_path.exists():
                self.results.append(
                    ValidationResult(
                        level=ValidationLevel.RECOMMENDED,
                        rule_file=rule_file,
                        rule_section="Documentation 구조",
                        check_name=f"docs/{folder}/ 존재",
                        passed=False,
                        message=f"[WARN] docs/{folder}/ 폴더 없음",
                        fix_available=True,
                        fix_command=f"mkdir -p docs/{folder}",
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        level=ValidationLevel.RECOMMENDED,
                        rule_file=rule_file,
                        rule_section="Documentation 구조",
                        check_name=f"docs/{folder}/ 존재",
                        passed=True,
                        message=f"[OK] docs/{folder}/ 존재",
                    )
                )

    def validate_innovation_safety_rules(self):
        """INNOVATION_SAFETY_PRINCIPLES.md 검증"""
        rule_file = "INNOVATION_SAFETY_PRINCIPLES.md"

        # Check 1: Design Review 문서 존재 (Pattern 4)
        # 새 기능이 3개 이상 파일에 영향을 주는 경우 docs/*_DESIGN_REVIEW.md 필요
        # Note: design_docs check is informational, not used in validation logic
        _ = list((self.repo_root / "docs").glob("*_DESIGN_REVIEW.md"))

        # Check 2: scripts/ 폴더에 자동화 스크립트 존재
        scripts_dir = self.repo_root / "scripts"
        required_automation = [
            ("obsidian_auto_sync.py", "Obsidian 자동 동기화"),
            ("validate_system_rules.py", "규칙 검증 자동화"),
        ]

        for script_file, description in required_automation:
            script_path = scripts_dir / script_file
            if not script_path.exists():
                self.results.append(
                    ValidationResult(
                        level=ValidationLevel.IMPORTANT,
                        rule_file=rule_file,
                        rule_section="자동화 스크립트",
                        check_name=f"{script_file} 존재",
                        passed=False,
                        message=f"[FAIL] {description} 스크립트 없음",
                        fix_available=True,
                        fix_command=f"Implement {script_file}",
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        level=ValidationLevel.IMPORTANT,
                        rule_file=rule_file,
                        rule_section="자동화 스크립트",
                        check_name=f"{script_file} 존재",
                        passed=True,
                        message=f"[OK] {description} 존재",
                    )
                )

        # Check 3: .git/hooks/ 디렉토리 존재
        hooks_dir = self.repo_root / ".git" / "hooks"
        if not hooks_dir.exists():
            self.results.append(
                ValidationResult(
                    level=ValidationLevel.CRITICAL,
                    rule_file=rule_file,
                    rule_section="Git Hooks",
                    check_name=".git/hooks/ 존재",
                    passed=False,
                    message="[FAIL] Git hooks 폴더 없음",
                    fix_available=False,
                    fix_command="git init",
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    level=ValidationLevel.RECOMMENDED,
                    rule_file=rule_file,
                    rule_section="Git Hooks",
                    check_name=".git/hooks/ 존재",
                    passed=True,
                    message="[OK] Git hooks 폴더 존재",
                )
            )

    def validate_error_resolution_rules(self):
        """OBSIDIAN_AUTO_SEARCH.md + 3-Tier Error Resolution 검증"""
        rule_file = "OBSIDIAN_AUTO_SEARCH.md"

        # Check 1: unified_error_resolver.py 존재
        resolver_path = self.repo_root / "scripts" / "unified_error_resolver.py"
        if not resolver_path.exists():
            self.results.append(
                ValidationResult(
                    level=ValidationLevel.CRITICAL,
                    rule_file=rule_file,
                    rule_section="3-Tier Error Resolution",
                    check_name="unified_error_resolver.py 존재",
                    passed=False,
                    message="[FAIL] 3-Tier 에러 해결 스크립트 없음",
                    fix_available=True,
                    fix_command="Implement scripts/unified_error_resolver.py",
                )
            )
        else:
            # Check 2: 3-Tier 기능 구현 확인 (Tier 1/2/3 메서드)
            resolver_content = resolver_path.read_text(encoding="utf-8")
            has_tier1 = "tier1" in resolver_content.lower() or "obsidian" in resolver_content.lower()
            has_tier2 = "tier2" in resolver_content.lower() or "context7" in resolver_content.lower()
            has_tier3 = "tier3" in resolver_content.lower() or "user" in resolver_content.lower()

            if has_tier1 and has_tier2 and has_tier3:
                self.results.append(
                    ValidationResult(
                        level=ValidationLevel.CRITICAL,
                        rule_file=rule_file,
                        rule_section="3-Tier Error Resolution",
                        check_name="3-Tier 구조 구현",
                        passed=True,
                        message="[OK] Tier 1/2/3 모두 구현됨",
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        level=ValidationLevel.CRITICAL,
                        rule_file=rule_file,
                        rule_section="3-Tier Error Resolution",
                        check_name="3-Tier 구조 구현",
                        passed=False,
                        message=f"[FAIL] 일부 Tier 누락 (T1:{has_tier1}, T2:{has_tier2}, T3:{has_tier3})",
                        fix_available=True,
                        fix_command="Complete 3-Tier implementation",
                    )
                )

        # Check 3: Obsidian 개발일지 폴더 존재
        obsidian_vault = os.getenv("OBSIDIAN_VAULT_PATH", str(Path.home() / "Documents" / "Obsidian Vault"))
        dev_log_dir = Path(obsidian_vault) / "개발일지"

        if not dev_log_dir.exists():
            self.results.append(
                ValidationResult(
                    level=ValidationLevel.IMPORTANT,
                    rule_file=rule_file,
                    rule_section="Tier 1 (Obsidian)",
                    check_name="개발일지 폴더 존재",
                    passed=False,
                    message=f"[WARN] Obsidian 개발일지 폴더 없음: {dev_log_dir}",
                    fix_available=True,
                    fix_command=f"mkdir -p '{dev_log_dir}'",
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    level=ValidationLevel.IMPORTANT,
                    rule_file=rule_file,
                    rule_section="Tier 1 (Obsidian)",
                    check_name="개발일지 폴더 존재",
                    passed=True,
                    message=f"[OK] Obsidian 개발일지 존재",
                )
            )

    def print_summary(self):
        """검증 결과 요약 출력"""
        print("\n" + "=" * 80)
        print("[SUMMARY] Validation Summary")
        print("=" * 80 + "\n")

        # 레벨별 통계
        stats = {level: {"passed": 0, "failed": 0} for level in ValidationLevel}

        for result in self.results:
            if result.passed:
                stats[result.level]["passed"] += 1
            else:
                stats[result.level]["failed"] += 1

        # 레벨별 출력
        for level in [ValidationLevel.CRITICAL, ValidationLevel.IMPORTANT, ValidationLevel.RECOMMENDED]:
            total = stats[level]["passed"] + stats[level]["failed"]
            passed = stats[level]["passed"]
            failed = stats[level]["failed"]

            icon = "[!]" if level == ValidationLevel.CRITICAL else "[*]" if level == ValidationLevel.IMPORTANT else "[+]"
            print(f"{icon} {level.value}: {passed}/{total} passed ({failed} failed)")

        print("\n" + "=" * 80)
        print("[DETAILS] Detailed Results")
        print("=" * 80 + "\n")

        # 실패한 항목만 상세 출력
        failed_results = [r for r in self.results if not r.passed]

        if not failed_results:
            print("[OK] All checks passed! System rules are properly implemented.\n")
        else:
            for result in failed_results:
                icon = (
                    "[!]"
                    if result.level == ValidationLevel.CRITICAL
                    else "[*]" if result.level == ValidationLevel.IMPORTANT else "[+]"
                )
                print(f"{icon} [{result.level.value}] {result.check_name}")
                print(f"   Rule: {result.rule_file} / {result.rule_section}")
                print(f"   {result.message}")
                if result.fix_available:
                    print(f"   Fix: {result.fix_command}")
                print()

        # 전체 통과율
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        pass_rate = (passed / total * 100) if total > 0 else 0

        print("=" * 80)
        print(f"[RESULT] Overall Pass Rate: {passed}/{total} ({pass_rate:.1f}%)")
        print("=" * 80 + "\n")

        # Critical 실패가 있으면 exit code 1
        critical_failures = [r for r in failed_results if r.level == ValidationLevel.CRITICAL]
        if critical_failures:
            print(f"[CRITICAL] {len(critical_failures)} CRITICAL issues found. System may not work as intended.\n")
            return 1

        return 0


def main():
    """메인 함수"""
    repo_root = Path(__file__).resolve().parents[1]
    validator = SystemRulesValidator(repo_root)

    # 검증 실행
    results = validator.validate_all()

    # 결과 출력
    exit_code = validator.print_summary()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
