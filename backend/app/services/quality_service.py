"""
Quality Metrics Service

Collects code quality metrics using Pylint, ESLint, and pytest-cov.
"""

import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class QualityMetricsService:
    """Service for collecting and analyzing code quality metrics"""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize Quality Metrics Service

        Args:
            project_root: Root directory of the project (defaults to current working directory)
        """
        self.project_root = project_root or Path.cwd()
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "web-dashboard"

    def get_pylint_metrics(self, target_dir: Optional[Path] = None) -> Dict:
        """
        Run Pylint on Python code and collect metrics

        Args:
            target_dir: Directory to analyze (defaults to backend/app)

        Returns:
            Dict containing Pylint metrics
        """
        target = target_dir or (self.backend_dir / "app")

        try:
            # Run Pylint with JSON output
            result = subprocess.run(
                ["pylint", str(target), "--output-format=json"],
                capture_output=True,
                text=True,
                cwd=str(self.backend_dir)
            )

            # Parse Pylint score from stdout
            score_match = re.search(r"Your code has been rated at ([\d.]+)/10", result.stdout)
            score = float(score_match.group(1)) if score_match else 0.0

            # Parse JSON messages
            messages = []
            if result.stdout.strip():
                try:
                    messages = json.loads(result.stdout)
                except json.JSONDecodeError:
                    # If JSON parsing fails, look for messages in stderr
                    pass

            # Count issues by type
            issues_by_type = {
                "convention": 0,
                "refactor": 0,
                "warning": 0,
                "error": 0,
                "fatal": 0
            }

            for msg in messages:
                msg_type = msg.get("type", "").lower()
                if msg_type in issues_by_type:
                    issues_by_type[msg_type] += 1

            return {
                "score": score,
                "total_issues": len(messages),
                "issues_by_type": issues_by_type,
                "messages": messages[:10],  # Only keep first 10 for performance
                "analyzed_at": datetime.now().isoformat()
            }

        except FileNotFoundError:
            logger.warning("Pylint not found. Install with: pip install pylint")
            return {
                "score": 0.0,
                "total_issues": 0,
                "issues_by_type": {},
                "messages": [],
                "analyzed_at": datetime.now().isoformat(),
                "error": "Pylint not installed"
            }
        except Exception as e:
            logger.error(f"Error running Pylint: {e}")
            return {
                "score": 0.0,
                "total_issues": 0,
                "issues_by_type": {},
                "messages": [],
                "analyzed_at": datetime.now().isoformat(),
                "error": str(e)
            }

    def get_eslint_metrics(self, target_dir: Optional[Path] = None) -> Dict:
        """
        Run ESLint on TypeScript/JavaScript code and collect metrics

        Args:
            target_dir: Directory to analyze (defaults to web-dashboard)

        Returns:
            Dict containing ESLint metrics
        """
        target = target_dir or self.frontend_dir

        try:
            # Run ESLint with JSON output
            result = subprocess.run(
                ["npx", "eslint", ".", "--format=json"],
                capture_output=True,
                text=True,
                cwd=str(target),
                shell=True  # Required for npx on Windows
            )

            # Parse JSON output
            eslint_results = json.loads(result.stdout) if result.stdout.strip() else []

            # Aggregate metrics
            total_errors = 0
            total_warnings = 0
            total_files = len(eslint_results)
            all_messages = []

            for file_result in eslint_results:
                total_errors += file_result.get("errorCount", 0)
                total_warnings += file_result.get("warningCount", 0)
                all_messages.extend(file_result.get("messages", []))

            # Calculate score (10 if no issues, decreases with errors/warnings)
            total_issues = total_errors + total_warnings
            score = max(0.0, 10.0 - (total_errors * 0.5) - (total_warnings * 0.1))
            score = min(10.0, score)  # Cap at 10.0

            return {
                "score": round(score, 2),
                "total_files": total_files,
                "total_errors": total_errors,
                "total_warnings": total_warnings,
                "total_issues": total_issues,
                "messages": all_messages[:10],  # Only keep first 10
                "analyzed_at": datetime.now().isoformat()
            }

        except FileNotFoundError:
            logger.warning("ESLint not found. Install with: npm install eslint")
            return {
                "score": 0.0,
                "total_files": 0,
                "total_errors": 0,
                "total_warnings": 0,
                "total_issues": 0,
                "messages": [],
                "analyzed_at": datetime.now().isoformat(),
                "error": "ESLint not installed"
            }
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing ESLint JSON output: {e}")
            return {
                "score": 0.0,
                "total_files": 0,
                "total_errors": 0,
                "total_warnings": 0,
                "total_issues": 0,
                "messages": [],
                "analyzed_at": datetime.now().isoformat(),
                "error": f"JSON parsing error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error running ESLint: {e}")
            return {
                "score": 0.0,
                "total_files": 0,
                "total_errors": 0,
                "total_warnings": 0,
                "total_issues": 0,
                "messages": [],
                "analyzed_at": datetime.now().isoformat(),
                "error": str(e)
            }

    def get_test_coverage_metrics(self) -> Dict:
        """
        Run pytest with coverage and collect metrics

        Returns:
            Dict containing test coverage metrics
        """
        try:
            # Run pytest with coverage
            result = subprocess.run(
                ["pytest", "--cov=app", "--cov-report=json", "--cov-report=term"],
                capture_output=True,
                text=True,
                cwd=str(self.backend_dir)
            )

            # Try to read coverage JSON report
            coverage_file = self.backend_dir / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)

                total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0.0)

                # Count test results from output
                test_match = re.search(r"(\d+) passed", result.stdout)
                failed_match = re.search(r"(\d+) failed", result.stdout)

                tests_passed = int(test_match.group(1)) if test_match else 0
                tests_failed = int(failed_match.group(1)) if failed_match else 0
                tests_total = tests_passed + tests_failed

                return {
                    "coverage_percentage": round(total_coverage, 2),
                    "tests_total": tests_total,
                    "tests_passed": tests_passed,
                    "tests_failed": tests_failed,
                    "success_rate": round((tests_passed / tests_total * 100) if tests_total > 0 else 0, 2),
                    "files_covered": len(coverage_data.get("files", {})),
                    "analyzed_at": datetime.now().isoformat()
                }
            else:
                # Fallback: parse from stdout
                coverage_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", result.stdout)
                coverage = float(coverage_match.group(1)) if coverage_match else 0.0

                test_match = re.search(r"(\d+) passed", result.stdout)
                tests_passed = int(test_match.group(1)) if test_match else 0

                return {
                    "coverage_percentage": coverage,
                    "tests_total": tests_passed,
                    "tests_passed": tests_passed,
                    "tests_failed": 0,
                    "success_rate": 100.0 if tests_passed > 0 else 0.0,
                    "analyzed_at": datetime.now().isoformat()
                }

        except FileNotFoundError:
            logger.warning("pytest not found. Install with: pip install pytest pytest-cov")
            return {
                "coverage_percentage": 0.0,
                "tests_total": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "success_rate": 0.0,
                "analyzed_at": datetime.now().isoformat(),
                "error": "pytest not installed"
            }
        except Exception as e:
            logger.error(f"Error running pytest coverage: {e}")
            return {
                "coverage_percentage": 0.0,
                "tests_total": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "success_rate": 0.0,
                "analyzed_at": datetime.now().isoformat(),
                "error": str(e)
            }

    def get_all_metrics(self) -> Dict:
        """
        Collect all quality metrics

        Returns:
            Dict containing all quality metrics
        """
        logger.info("Collecting quality metrics...")

        # Collect all metrics
        pylint_metrics = self.get_pylint_metrics()
        eslint_metrics = self.get_eslint_metrics()
        coverage_metrics = self.get_test_coverage_metrics()

        # Calculate overall score (weighted average)
        # Pylint: 30%, ESLint: 30%, Coverage: 40%
        pylint_score = pylint_metrics.get("score", 0.0)
        eslint_score = eslint_metrics.get("score", 0.0)
        coverage_score = coverage_metrics.get("coverage_percentage", 0.0) / 10.0  # Convert to 0-10 scale

        overall_score = (
            (pylint_score * 0.3) +
            (eslint_score * 0.3) +
            (coverage_score * 0.4)
        )

        return {
            "overall_score": round(overall_score, 2),
            "code_quality": {
                "python": pylint_metrics,
                "typescript": eslint_metrics
            },
            "test_metrics": coverage_metrics,
            "collected_at": datetime.now().isoformat()
        }


# Create singleton instance
quality_service = QualityMetricsService()
