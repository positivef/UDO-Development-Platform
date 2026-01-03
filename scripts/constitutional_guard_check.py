#!/usr/bin/env python3
"""
Constitutional Guard Pre-commit Hook

Enforces UDO Constitution before commits.
Validates code changes against P1-P17 articles.

Usage:
    Install as Git hook:
        ln -s ../../scripts/constitutional_guard_check.py .git/hooks/pre-commit

    Or run manually:
        python scripts/constitutional_guard_check.py
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Tuple
import asyncio

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from backend.app.core.constitutional_guard import ConstitutionalGuard  # noqa: E402
except ImportError:
    print("[FAIL] Error: Cannot import ConstitutionalGuard")
    print("   Make sure you're in the UDO-Development-Platform directory")
    sys.exit(1)


class ConstitutionalPreCommitHook:
    """Pre-commit hook for constitutional enforcement"""

    def __init__(self):
        self.guard = ConstitutionalGuard()
        self.violations = []
        self.warnings = []

    def get_staged_files(self) -> List[str]:
        """Get list of staged files"""
        try:
            result = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, check=True)
            return [f.strip() for f in result.stdout.split("\n") if f.strip()]
        except subprocess.CalledProcessError as e:
            print(f"[FAIL] Error getting staged files: {e}")
            return []

    def get_staged_diff(self) -> str:
        """Get diff of staged changes"""
        try:
            result = subprocess.run(["git", "diff", "--cached"], capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"[FAIL] Error getting diff: {e}")
            return ""

    def count_file_changes(self, staged_files: List[str]) -> Tuple[int, int, int]:
        """Count added, modified, deleted files"""
        added = 0
        modified = 0
        deleted = 0

        for file in staged_files:
            try:
                # Check if file exists (not deleted)
                if not Path(file).exists():
                    deleted += 1
                    continue

                # Check if file is new
                result = subprocess.run(["git", "ls-files", "--error-unmatch", file], capture_output=True, text=True)
                if result.returncode != 0:
                    added += 1
                else:
                    modified += 1
            except Exception:
                modified += 1

        return added, modified, deleted

    def analyze_commit_message(self) -> str:
        """Get commit message from COMMIT_EDITMSG"""
        commit_msg_file = Path(".git/COMMIT_EDITMSG")
        if commit_msg_file.exists():
            return commit_msg_file.read_text(encoding="utf-8").strip()
        return ""

    async def check_p1_design_review(self, staged_files: List[str]) -> bool:
        """
        P1: Design Review First

        Check if design review is required and has been completed
        """
        # Exemptions (from P1 constitution)
        exemptions = [
            lambda f: f.endswith(".md"),  # Documentation
            lambda f: any(word in f.lower() for word in ["test", "spec"]),  # Tests
            lambda f: f.endswith(".json") or f.endswith(".yaml"),  # Config
        ]

        # Check if any non-exempt files are being changed
        significant_files = []
        for file in staged_files:
            if not any(exempt(file) for exempt in exemptions):
                significant_files.append(file)

        if not significant_files:
            # Only exempt files, skip P1 check
            return True

        # Check for design review document
        design_docs = [f for f in staged_files if "design" in f.lower() and f.endswith(".md")]

        if len(significant_files) >= 3 and not design_docs:
            self.violations.append(
                "P1 VIOLATION: Design review required for changes affecting 3+ files\n"
                f"   Changed files: {len(significant_files)}\n"
                f"   Missing: Design review document (docs/*_DESIGN_REVIEW.md)\n"
                "   Create design document with 8-Risk Check before committing"
            )
            return False

        return True

    async def check_p7_code_quality(self, staged_files: List[str]) -> bool:
        """
        P7: Code Quality Gates

        Run linting and type checking on staged files
        """
        has_python = any(f.endswith(".py") for f in staged_files)
        has_typescript = any(f.endswith((".ts", ".tsx")) for f in staged_files)

        quality_passed = True

        # Python quality checks
        if has_python:
            python_files = [f for f in staged_files if f.endswith(".py")]

            # Pylint check
            try:
                result = subprocess.run(["python", "-m", "pylint"] + python_files, capture_output=True, text=True)
                if result.returncode != 0:
                    # Check for critical issues
                    if "E:" in result.stdout or "F:" in result.stdout:
                        self.violations.append(
                            f"P7 VIOLATION: Python code quality issues\n"
                            f"   Run: pylint {' '.join(python_files)}\n"
                            "   Fix critical errors (E:, F:) before committing"
                        )
                        quality_passed = False
                    else:
                        self.warnings.append("P7 WARNING: Python code quality warnings (non-critical)")
            except FileNotFoundError:
                self.warnings.append("P7 WARNING: pylint not installed, skipping Python checks")

            # Type checking with mypy
            try:
                result = subprocess.run(["python", "-m", "mypy"] + python_files, capture_output=True, text=True)
                if result.returncode != 0 and "error:" in result.stdout.lower():
                    self.warnings.append("P7 WARNING: Type checking issues detected (mypy)")
            except FileNotFoundError:
                pass  # mypy is optional

        # TypeScript quality checks
        if has_typescript:
            ts_files = [f for f in staged_files if f.endswith((".ts", ".tsx"))]

            # ESLint check
            try:
                result = subprocess.run(
                    ["npx", "eslint"] + ts_files, capture_output=True, text=True, cwd=project_root / "web-dashboard"
                )
                if result.returncode != 0:
                    self.warnings.append("P7 WARNING: TypeScript linting issues (ESLint)")
            except (FileNotFoundError, subprocess.CalledProcessError):
                pass  # ESLint might not be available

        return quality_passed

    async def check_p8_security(self, diff: str) -> bool:
        """
        P8: Security First

        Check for common security issues in diff
        """
        security_patterns = [
            ("password", "Potential hardcoded password"),
            ("secret", "Potential hardcoded secret"),
            ("api_key", "Potential hardcoded API key"),
            ("private_key", "Potential hardcoded private key"),
            ("aws_access_key", "Potential AWS credentials"),
            ("eval(", "Use of eval() - security risk"),
            ("exec(", "Use of exec() - security risk"),
            ("shell=True", "shell=True in subprocess - security risk"),
        ]

        security_issues = []
        for pattern, message in security_patterns:
            if pattern in diff.lower():
                # Check if it's in added lines (starts with +)
                for line in diff.split("\n"):
                    if line.startswith("+") and pattern in line.lower():
                        security_issues.append(f"{message}: {line[:80]}")
                        break

        if security_issues:
            self.violations.append(
                "P8 SECURITY VIOLATION: Potential security issues detected\n"
                + "\n".join(f"   - {issue}" for issue in security_issues)
                + "\n   Review and remove sensitive data before committing"
            )
            return False

        return True

    async def run_checks(self) -> bool:
        """
        Run all constitutional checks

        Returns:
            True if all checks pass, False otherwise
        """
        print("[RUN] Constitutional Guard checks...")

        # Get staged files
        staged_files = self.get_staged_files()
        if not staged_files:
            print("ℹ  No staged files to check")
            return True

        print(f"   Checking {len(staged_files)} staged files")

        # Get diff
        diff = self.get_staged_diff()

        # Count changes
        added, modified, deleted = self.count_file_changes(staged_files)
        print(f"   Changes: +{added} ~{modified} -{deleted}")

        # Run checks
        checks = [
            ("P1: Design Review First", self.check_p1_design_review(staged_files)),
            ("P7: Code Quality Gates", self.check_p7_code_quality(staged_files)),
            ("P8: Security First", self.check_p8_security(diff)),
        ]

        all_passed = True
        for check_name, check_coro in checks:
            try:
                result = await check_coro
                status = "[OK]" if result else "[FAIL]"
                print(f"   {status} {check_name}")
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"   [WARN]  {check_name}: Error - {e}")
                self.warnings.append(f"{check_name}: Check failed with error")

        return all_passed

    def print_results(self):
        """Print violations and warnings"""
        if self.violations:
            print("\n[FAIL] CONSTITUTIONAL VIOLATIONS:")
            for violation in self.violations:
                print(f"\n{violation}")

        if self.warnings:
            print("\n[WARN]  WARNINGS:")
            for warning in self.warnings:
                print(f"   {warning}")

    def get_exit_code(self) -> int:
        """Get exit code based on violations"""
        if self.violations:
            return 1  # Block commit
        return 0  # Allow commit


async def main():
    """Main entry point"""
    print("=" * 60)
    print("UDO Constitutional Guard - Pre-commit Hook")
    print("=" * 60)

    hook = ConstitutionalPreCommitHook()

    # Run checks
    passed = await hook.run_checks()

    # Print results
    hook.print_results()

    # Summary
    print("\n" + "=" * 60)
    if passed and not hook.violations:
        print("[OK] All constitutional checks passed!")
        print("   Commit allowed")
    else:
        print("[FAIL] Constitutional violations detected!")
        print("   Commit blocked - fix violations before committing")
        print("\nTips:")
        print("   - Create design review doc for major changes (P1)")
        print("   - Run linters: pylint, eslint (P7)")
        print("   - Remove hardcoded secrets (P8)")
        print("\nTo bypass (NOT RECOMMENDED):")
        print("   git commit --no-verify")
    print("=" * 60)

    return hook.get_exit_code()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
