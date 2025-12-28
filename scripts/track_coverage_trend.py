#!/usr/bin/env python3
"""
Coverage Trend Tracker - Week 0 Day 4

Purpose: Track test coverage trends over time and detect regressions

Usage:
    python scripts/track_coverage_trend.py --record
    python scripts/track_coverage_trend.py --report
    python scripts/track_coverage_trend.py --check-regression

Author: VibeCoding Team
Date: 2025-12-07 (Week 0 Day 4)
"""

import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def get_storage_dir() -> Path:
    """Get UDO storage directory"""
    import os

    env_dir = os.environ.get("UDO_STORAGE_DIR") or os.environ.get("UDO_HOME")
    base_dir = Path(env_dir).expanduser() if env_dir else Path.home() / ".udo"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def run_coverage_test() -> Tuple[float, Dict[str, float]]:
    """
    Run pytest with coverage and extract total coverage percentage

    Returns:
        tuple: (total_coverage_percent, module_coverage_dict)
    """
    try:
        import sys

        # Run pytest with coverage using current Python executable
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "backend/tests/",
                "tests/",
                "--cov=backend",
                "--cov=src",
                "--cov-report=term",
                "-q",
                "--tb=line",
                "--disable-warnings",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
            cwd=Path.cwd(),
        )

        # Parse coverage output
        total_coverage = 0.0
        module_coverage = {}

        for line in result.stdout.split("\n"):
            if "TOTAL" in line:
                # Extract total coverage percentage
                parts = line.split()
                for part in parts:
                    if "%" in part:
                        total_coverage = float(part.replace("%", ""))
                        break
            elif line.strip() and not line.startswith("=") and not line.startswith("-"):
                # Extract module-specific coverage
                parts = line.split()
                if len(parts) >= 4 and parts[-1].endswith("%"):
                    module_name = parts[0]
                    coverage_pct = float(parts[-1].replace("%", ""))
                    module_coverage[module_name] = coverage_pct

        return total_coverage, module_coverage

    except subprocess.TimeoutExpired:
        print("Coverage test timed out after 5 minutes")
        return 0.0, {}
    except Exception as e:
        print(f"Error running coverage test: {e}")
        return 0.0, {}


def record_coverage(total_coverage: float, module_coverage: Dict[str, float]) -> None:
    """
    Record coverage snapshot to trend log

    Args:
        total_coverage: Overall coverage percentage
        module_coverage: Module-specific coverage percentages
    """
    storage_dir = get_storage_dir()
    trend_file = storage_dir / "coverage_trend.jsonl"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "total_coverage": total_coverage,
        "module_coverage": module_coverage,
        "metadata": {
            "total_modules": len(module_coverage),
            "modules_above_80": sum(1 for cov in module_coverage.values() if cov >= 80),
            "modules_below_50": sum(1 for cov in module_coverage.values() if cov < 50),
        },
    }

    with open(trend_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    print(f"Coverage recorded: {total_coverage:.1f}%")
    print(f"  Modules: {len(module_coverage)}")
    print(f"  Above 80%: {entry['metadata']['modules_above_80']}")
    print(f"  Below 50%: {entry['metadata']['modules_below_50']}")


def load_coverage_history() -> List[Dict]:
    """Load all coverage history from trend log"""
    storage_dir = get_storage_dir()
    trend_file = storage_dir / "coverage_trend.jsonl"

    if not trend_file.exists():
        return []

    history = []
    with open(trend_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                history.append(json.loads(line))

    return history


def generate_coverage_report() -> str:
    """
    Generate human-readable coverage trend report

    Returns:
        str: Formatted report
    """
    history = load_coverage_history()

    if not history:
        return "No coverage history available. Run with --record first."

    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("COVERAGE TREND REPORT - Week 0 Foundation")
    report_lines.append("=" * 70)
    report_lines.append("")

    # Overall trend
    first_entry = history[0]
    latest_entry = history[-1]

    first_coverage = first_entry["total_coverage"]
    latest_coverage = latest_entry["total_coverage"]
    trend_delta = latest_coverage - first_coverage

    report_lines.append(f"Total Snapshots: {len(history)}")
    report_lines.append(f"First Measurement: {first_entry['timestamp'][:10]}")
    report_lines.append(f"Latest Measurement: {latest_entry['timestamp'][:10]}")
    report_lines.append("")

    report_lines.append("OVERALL COVERAGE TREND:")
    report_lines.append(f"  First:  {first_coverage:.1f}%")
    report_lines.append(f"  Latest: {latest_coverage:.1f}%")

    if trend_delta > 0:
        report_lines.append(f"  Change: +{trend_delta:.1f}% (IMPROVING)")
    elif trend_delta < 0:
        report_lines.append(f"  Change: {trend_delta:.1f}% (REGRESSION)")
    else:
        report_lines.append(f"  Change: {trend_delta:.1f}% (STABLE)")

    report_lines.append("")

    # Module-level trends
    report_lines.append("MODULE-LEVEL TRENDS:")

    first_modules = first_entry.get("module_coverage", {})
    latest_modules = latest_entry.get("module_coverage", {})

    # Find modules with significant changes
    changes = []
    for module, latest_cov in latest_modules.items():
        if module in first_modules:
            first_cov = first_modules[module]
            delta = latest_cov - first_cov
            if abs(delta) >= 5.0:  # Significant change threshold: 5%
                changes.append((module, first_cov, latest_cov, delta))

    changes.sort(key=lambda x: abs(x[3]), reverse=True)

    if changes:
        report_lines.append("")
        report_lines.append("  Significant Changes (>=5%):")
        for module, first_cov, latest_cov, delta in changes[:10]:
            direction = "+" if delta > 0 else ""
            module_short = module.split("/")[-1] if "/" in module else module
            report_lines.append(
                f"    {module_short:40s}: {first_cov:5.1f}% -> {latest_cov:5.1f}% " f"({direction}{delta:.1f}%)"
            )
    else:
        report_lines.append("  No significant module changes detected")

    report_lines.append("")

    # Quality breakdown
    latest_meta = latest_entry.get("metadata", {})
    report_lines.append("QUALITY BREAKDOWN (Latest):")
    report_lines.append(f"  Total Modules: {latest_meta.get('total_modules', 0)}")
    report_lines.append(f"  Above 80%: {latest_meta.get('modules_above_80', 0)}")
    report_lines.append(f"  Below 50%: {latest_meta.get('modules_below_50', 0)}")
    report_lines.append("")

    # Targets
    report_lines.append("TARGETS:")
    report_lines.append(f"  Week 0 Baseline: {latest_coverage:.1f}%")
    report_lines.append(f"  Prototype Target: 65%")
    report_lines.append(f"  Beta Target: 75%")
    report_lines.append(f"  Production Target: 85%")
    report_lines.append("")

    report_lines.append("=" * 70)

    return "\n".join(report_lines)


def check_regression(threshold: float = 2.0) -> bool:
    """
    Check if coverage has regressed from last measurement

    Args:
        threshold: Regression threshold in percentage points (default 2%)

    Returns:
        bool: True if regression detected, False otherwise
    """
    history = load_coverage_history()

    if len(history) < 2:
        print("Need at least 2 measurements to detect regression")
        return False

    prev_coverage = history[-2]["total_coverage"]
    current_coverage = history[-1]["total_coverage"]

    delta = current_coverage - prev_coverage

    if delta < -threshold:
        print(f"REGRESSION DETECTED!")
        print(f"  Previous: {prev_coverage:.1f}%")
        print(f"  Current:  {current_coverage:.1f}%")
        print(f"  Change:   {delta:.1f}% (threshold: -{threshold}%)")
        return True
    else:
        print(f"No regression detected")
        print(f"  Previous: {prev_coverage:.1f}%")
        print(f"  Current:  {current_coverage:.1f}%")
        print(f"  Change:   {delta:+.1f}%")
        return False


def main():
    parser = argparse.ArgumentParser(description="Coverage Trend Tracker for UDO Platform")
    parser.add_argument("--record", action="store_true", help="Run coverage test and record snapshot")
    parser.add_argument("--report", action="store_true", help="Generate coverage trend report")
    parser.add_argument("--check-regression", action="store_true", help="Check for coverage regression from last measurement")
    parser.add_argument("--threshold", type=float, default=2.0, help="Regression threshold in percentage points (default 2%)")

    args = parser.parse_args()

    if args.record:
        print("Running coverage test...")
        total_coverage, module_coverage = run_coverage_test()

        if total_coverage > 0:
            record_coverage(total_coverage, module_coverage)
        else:
            print("Failed to measure coverage")
            return 1

    if args.report:
        report = generate_coverage_report()
        print(report)

        # Save report to file
        storage_dir = get_storage_dir()
        report_file = storage_dir / f"coverage_report_{datetime.now():%Y%m%d_%H%M%S}.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\nReport saved to: {report_file}")

    if args.check_regression:
        has_regression = check_regression(threshold=args.threshold)
        return 1 if has_regression else 0

    if not (args.record or args.report or args.check_regression):
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
