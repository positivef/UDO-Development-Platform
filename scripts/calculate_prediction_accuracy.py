#!/usr/bin/env python3
"""
Prediction Accuracy Calculator - Week 0 Day 3

Purpose: Calculate prediction accuracy from ground truth annotations

Usage:
    python scripts/calculate_prediction_accuracy.py --samples 100
    python scripts/calculate_prediction_accuracy.py --all
    python scripts/calculate_prediction_accuracy.py --report

Author: VibeCoding Team
Date: 2025-12-07 (Week 0 Day 3)
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime


def get_storage_dir() -> Path:
    """Get UDO storage directory"""
    import os
    env_dir = os.environ.get('UDO_STORAGE_DIR') or os.environ.get('UDO_HOME')
    base_dir = Path(env_dir).expanduser() if env_dir else Path.home() / '.udo'
    return base_dir


def calculate_level_accuracy(
    predictions: List[Tuple[str, float]],
    actuals: List[Tuple[str, float]]
) -> float:
    """
    Level accuracy based on Mean Absolute Percentage Error (MAPE)

    Args:
        predictions: List[(timestamp, predicted_level)]
        actuals: List[(timestamp, actual_level)]

    Returns:
        float: Level accuracy percentage (0-100%)
    """
    if len(predictions) != len(actuals):
        raise ValueError("Predictions and actuals must have same length")

    if not predictions:
        return 0.0

    absolute_errors = []
    for (pred_ts, pred_level), (actual_ts, actual_level) in zip(predictions, actuals):
        if pred_ts != actual_ts:
            raise ValueError(f"Timestamp mismatch: {pred_ts} != {actual_ts}")

        # Absolute Percentage Error
        # Handle zero actual values (use absolute error instead)
        if actual_level == 0:
            ape = abs(pred_level - actual_level)
        else:
            ape = abs(pred_level - actual_level) / actual_level

        absolute_errors.append(ape)

    # Mean APE
    mape = sum(absolute_errors) / len(absolute_errors)

    # Convert to accuracy (1 - error)
    # Cap at 100% (negative errors impossible with APE)
    level_accuracy = max(0, min(100, (1 - mape) * 100))

    return level_accuracy


def calculate_trend_accuracy(
    predictions: List[Tuple[str, str]],
    actuals: List[Tuple[str, str]]
) -> float:
    """
    Trend accuracy based on direction match percentage

    Args:
        predictions: List[(timestamp, predicted_trend)]
        actuals: List[(timestamp, actual_trend)]

    Returns:
        float: Trend accuracy percentage (0-100%)
    """
    if len(predictions) != len(actuals):
        raise ValueError("Predictions and actuals must have same length")

    if not predictions:
        return 0.0

    correct_trends = 0
    for (pred_ts, pred_trend), (actual_ts, actual_trend) in zip(predictions, actuals):
        if pred_ts != actual_ts:
            raise ValueError(f"Timestamp mismatch: {pred_ts} != {actual_ts}")

        if pred_trend == actual_trend:
            correct_trends += 1

    trend_accuracy = (correct_trends / len(predictions)) * 100
    return trend_accuracy


def calculate_state_accuracy(
    predictions: List[Tuple[str, str]],
    actuals: List[Tuple[str, str]]
) -> float:
    """
    State accuracy based on uncertainty state classification match

    Args:
        predictions: List[(timestamp, predicted_state)]
        actuals: List[(timestamp, actual_state)]

    Returns:
        float: State accuracy percentage (0-100%)
    """
    if len(predictions) != len(actuals):
        raise ValueError("Predictions and actuals must have same length")

    if not predictions:
        return 0.0

    correct_states = 0
    for (pred_ts, pred_state), (actual_ts, actual_state) in zip(predictions, actuals):
        if pred_ts != actual_ts:
            raise ValueError(f"Timestamp mismatch: {pred_ts} != {actual_ts}")

        if pred_state == actual_state:
            correct_states += 1

    state_accuracy = (correct_states / len(predictions)) * 100
    return state_accuracy


def calculate_prediction_accuracy(
    ground_truth_entries: List[Dict]
) -> Dict[str, any]:
    """
    Calculate overall prediction accuracy with weighted components

    Args:
        ground_truth_entries: List of annotated predictions

    Returns:
        dict: {
            "overall": float,
            "components": {...},
            "sample_size": int,
            "confidence_breakdown": {...}
        }
    """
    if not ground_truth_entries:
        return {
            "overall": 0.0,
            "components": {
                "level_accuracy": 0.0,
                "trend_accuracy": 0.0,
                "state_accuracy": 0.0
            },
            "sample_size": 0
        }

    # Extract components
    pred_levels = []
    actual_levels = []
    pred_trends = []
    actual_trends = []
    pred_states = []
    actual_states = []

    for entry in ground_truth_entries:
        ts = entry["prediction_timestamp"]
        pred_levels.append((ts, entry["predicted_global_level"]))
        actual_levels.append((ts, entry["actual_global_level"]))
        pred_trends.append((ts, entry["predicted_global_trend"]))
        actual_trends.append((ts, entry["actual_global_trend"]))
        pred_states.append((ts, entry["predicted_global_state"]))
        actual_states.append((ts, entry["actual_global_state"]))

    # Calculate component accuracies
    level_acc = calculate_level_accuracy(pred_levels, actual_levels)
    trend_acc = calculate_trend_accuracy(pred_trends, actual_trends)
    state_acc = calculate_state_accuracy(pred_states, actual_states)

    # Weighted composite (50% level, 30% trend, 20% state)
    overall_accuracy = (
        0.50 * level_acc +
        0.30 * trend_acc +
        0.20 * state_acc
    )

    # Confidence breakdown
    confidence_counts = {"high": 0, "medium": 0, "low": 0}
    for entry in ground_truth_entries:
        conf = entry.get("annotator_confidence", "medium")
        confidence_counts[conf] = confidence_counts.get(conf, 0) + 1

    return {
        "overall": overall_accuracy,
        "components": {
            "level_accuracy": level_acc,
            "trend_accuracy": trend_acc,
            "state_accuracy": state_acc
        },
        "sample_size": len(ground_truth_entries),
        "confidence_breakdown": confidence_counts,
        "measurement_period": {
            "start": min(e["prediction_timestamp"] for e in ground_truth_entries),
            "end": max(e["prediction_timestamp"] for e in ground_truth_entries)
        }
    }


def analyze_errors(ground_truth_entries: List[Dict]) -> Dict[str, any]:
    """
    Analyze common error patterns

    Args:
        ground_truth_entries: List of annotated predictions

    Returns:
        dict: Error pattern analysis
    """
    level_errors = []
    trend_mismatches = []
    state_mismatches = []

    for entry in ground_truth_entries:
        # Level errors
        pred_level = entry["predicted_global_level"]
        actual_level = entry["actual_global_level"]
        level_error = abs(pred_level - actual_level)
        level_errors.append({
            "timestamp": entry["prediction_timestamp"],
            "predicted": pred_level,
            "actual": actual_level,
            "error": level_error
        })

        # Trend mismatches
        if entry["predicted_global_trend"] != entry["actual_global_trend"]:
            trend_mismatches.append({
                "timestamp": entry["prediction_timestamp"],
                "predicted": entry["predicted_global_trend"],
                "actual": entry["actual_global_trend"]
            })

        # State mismatches
        if entry["predicted_global_state"] != entry["actual_global_state"]:
            state_mismatches.append({
                "timestamp": entry["prediction_timestamp"],
                "predicted": entry["predicted_global_state"],
                "actual": entry["actual_global_state"]
            })

    # Sort by error magnitude
    level_errors.sort(key=lambda x: x["error"], reverse=True)

    return {
        "worst_level_errors": level_errors[:5],  # Top 5 worst
        "trend_mismatches": len(trend_mismatches),
        "trend_mismatch_examples": trend_mismatches[:5],
        "state_mismatches": len(state_mismatches),
        "state_mismatch_examples": state_mismatches[:5]
    }


def generate_report(accuracy_results: Dict, error_analysis: Dict) -> str:
    """Generate human-readable report"""
    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("[EMOJI] PREDICTION ACCURACY REPORT - Week 0 Baseline")
    report_lines.append("=" * 70)
    report_lines.append("")

    # Overall
    overall = accuracy_results["overall"]
    report_lines.append(f"[EMOJI] Overall Accuracy: {overall:.1f}%")
    report_lines.append("")

    # Components
    components = accuracy_results["components"]
    report_lines.append("[EMOJI] Component Breakdown:")
    report_lines.append(f"   Level Accuracy (50% weight):  {components['level_accuracy']:.1f}%")
    report_lines.append(f"   Trend Accuracy (30% weight):  {components['trend_accuracy']:.1f}%")
    report_lines.append(f"   State Accuracy (20% weight):  {components['state_accuracy']:.1f}%")
    report_lines.append("")

    # Sample size
    sample_size = accuracy_results["sample_size"]
    report_lines.append(f"[EMOJI] Sample Size: {sample_size} predictions")
    report_lines.append("")

    # Confidence
    conf = accuracy_results["confidence_breakdown"]
    report_lines.append("[EMOJI] Annotator Confidence:")
    report_lines.append(f"   High:   {conf.get('high', 0)}")
    report_lines.append(f"   Medium: {conf.get('medium', 0)}")
    report_lines.append(f"   Low:    {conf.get('low', 0)}")
    report_lines.append("")

    # Period
    period = accuracy_results["measurement_period"]
    report_lines.append("[EMOJI] Measurement Period:")
    report_lines.append(f"   Start: {period['start'][:10]}")
    report_lines.append(f"   End:   {period['end'][:10]}")
    report_lines.append("")

    # Errors
    report_lines.append("[WARN]  Error Analysis:")
    report_lines.append(f"   Trend mismatches:  {error_analysis['trend_mismatches']}")
    report_lines.append(f"   State mismatches:  {error_analysis['state_mismatches']}")
    report_lines.append("")

    # Worst errors
    if error_analysis["worst_level_errors"]:
        report_lines.append("[EMOJI] Top 5 Worst Level Errors:")
        for i, error in enumerate(error_analysis["worst_level_errors"], 1):
            report_lines.append(
                f"   {i}. {error['timestamp'][:10]}: "
                f"Predicted {error['predicted']:.1%}, "
                f"Actual {error['actual']:.1%} "
                f"(Error: {error['error']:.1%})"
            )
        report_lines.append("")

    # Targets
    report_lines.append("[EMOJI] Target Comparison:")
    report_lines.append(f"   Week 0 Baseline:  {overall:.1f}% (expected: 50-60%)")
    report_lines.append(f"   Prototype Target: 55%")
    report_lines.append(f"   Beta Target:      65%")
    report_lines.append(f"   Production Target: 80%")
    report_lines.append("")

    report_lines.append("=" * 70)

    return "\n".join(report_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Calculate Prediction Accuracy from Ground Truth"
    )
    parser.add_argument(
        "--samples",
        type=int,
        help="Calculate accuracy for first N samples"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Calculate accuracy for all annotations"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate detailed report"
    )
    parser.add_argument(
        "--min-confidence",
        type=str,
        choices=["high", "medium", "low"],
        default="low",
        help="Minimum annotator confidence to include (default: low = all)"
    )

    args = parser.parse_args()

    # Load ground truth
    storage_dir = get_storage_dir()
    ground_truth_file = storage_dir / "prediction_ground_truth.jsonl"

    if not ground_truth_file.exists():
        print(f"[FAIL] No ground truth annotations found at: {ground_truth_file}")
        print("\nRun annotation tool first:")
        print("  python scripts/annotate_ground_truth.py --last-24h")
        return

    # Load annotations
    with open(ground_truth_file, encoding="utf-8") as f:
        all_entries = [json.loads(line) for line in f if line.strip()]

    # Filter by confidence
    confidence_levels = {"high": 3, "medium": 2, "low": 1}
    min_conf_level = confidence_levels[args.min_confidence]

    filtered_entries = [
        entry for entry in all_entries
        if confidence_levels.get(entry.get("annotator_confidence", "low"), 1) >= min_conf_level
    ]

    # Limit samples
    if args.samples:
        entries = filtered_entries[:args.samples]
    else:
        entries = filtered_entries

    if not entries:
        print("[FAIL] No annotations match criteria")
        return

    print(f"[EMOJI] Calculating accuracy for {len(entries)} annotations...")
    print(f"   (Total available: {len(all_entries)})")
    print("")

    # Calculate accuracy
    accuracy_results = calculate_prediction_accuracy(entries)
    error_analysis = analyze_errors(entries)

    # Output
    if args.report:
        report = generate_report(accuracy_results, error_analysis)
        print(report)

        # Save report
        report_file = storage_dir / f"prediction_accuracy_report_{datetime.now():%Y%m%d_%H%M%S}.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n[EMOJI] Report saved to: {report_file}")

    else:
        # Simple output
        print(f"[EMOJI] Overall Accuracy: {accuracy_results['overall']:.1f}%")
        print(f"\nComponents:")
        print(f"  Level:  {accuracy_results['components']['level_accuracy']:.1f}%")
        print(f"  Trend:  {accuracy_results['components']['trend_accuracy']:.1f}%")
        print(f"  State:  {accuracy_results['components']['state_accuracy']:.1f}%")
        print(f"\nSample Size: {accuracy_results['sample_size']}")

    # Save JSON results
    results_file = storage_dir / f"prediction_accuracy_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump({
            "accuracy": accuracy_results,
            "errors": error_analysis
        }, f, indent=2)

    print(f"\n[EMOJI] Results saved to: {results_file}")


if __name__ == "__main__":
    main()
