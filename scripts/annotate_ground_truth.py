#!/usr/bin/env python3
"""
Ground Truth Annotation Tool - Week 0 Day 3

Purpose: Interactive CLI for manual annotation of prediction ground truth

Usage:
    python scripts/annotate_ground_truth.py --date 2025-12-06
    python scripts/annotate_ground_truth.py --last-24h
    python scripts/annotate_ground_truth.py --all

Author: VibeCoding Team
Date: 2025-12-07 (Week 0 Day 3)
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional


def get_storage_dir() -> Path:
    """Get UDO storage directory"""
    import os  # noqa: E402

    env_dir = os.environ.get("UDO_STORAGE_DIR") or os.environ.get("UDO_HOME")
    base_dir = Path(env_dir).expanduser() if env_dir else Path.home() / ".udo"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def determine_trend(prev_level: float, current_level: float, threshold: float = 0.05) -> str:
    """
    Determine actual trend from observed levels

    Args:
        prev_level: Uncertainty level at prediction time
        current_level: Uncertainty level now (actual)
        threshold: Minimum change to classify as increasing/decreasing (default 5%)

    Returns:
        str: "increasing" | "decreasing" | "stable"
    """
    delta = current_level - prev_level

    if delta > threshold:
        return "increasing"
    elif delta < -threshold:
        return "decreasing"
    else:
        return "stable"


def level_to_state(level: float) -> str:
    """Convert uncertainty level (0-1) to state classification"""
    if level < 0.10:
        return "DETERMINISTIC"
    elif level < 0.30:
        return "PROBABILISTIC"
    elif level < 0.60:
        return "QUANTUM"
    elif level < 0.90:
        return "CHAOTIC"
    else:
        return "VOID"


def annotate_prediction(prediction_entry: Dict) -> Optional[Dict]:
    """
    Interactive annotation of a single prediction

    Args:
        prediction_entry: Prediction log entry from predictions_log.jsonl

    Returns:
        dict: Annotated entry with actual observations, or None if skipped
    """
    print(f"\n{'='*70}")
    print(f"[*] Prediction made at: {prediction_entry['prediction_timestamp']}")
    print(f"[PREDICT] global uncertainty: {prediction_entry['predicted_global_level']:.1%}")
    print(f"[PREDICT] trend: {prediction_entry['predicted_global_trend']}")
    print(f"[PREDICT] state: {prediction_entry['predicted_global_state']}")
    print(f"[*] Hours ahead: {prediction_entry['hours_ahead']}h")
    print(f"[OK] Validation time: {prediction_entry['validation_timestamp']}")
    print(f"{'='*70}\n")

    # Ask annotator to observe actual uncertainty
    print("[INFO] Based on what happened in the last 24 hours:\n")

    print("1. Did unexpected blockers occur? [y/n/s(kip)]")
    blockers_input = input("> ").lower()
    if blockers_input == "s":
        return None
    blockers = blockers_input == "y"

    print("2. Did estimates match actual time? [y/n]")
    estimates_matched = input("> ").lower() == "y"

    print("3. Did all tests pass first try? [y/n]")
    tests_passed = input("> ").lower() == "y"

    print("4. Were there scope changes? [y/n]")
    scope_changes = input("> ").lower() == "y"

    print("5. Did dependencies fail? [y/n]")
    dependencies_failed = input("> ").lower() == "y"

    # Calculate actual uncertainty based on observations
    base = 0.30  # Normal baseline
    actual_level = base
    actual_level += 0.1 if blockers else 0
    actual_level += -0.1 if estimates_matched else 0
    actual_level += -0.1 if tests_passed else 0.1
    actual_level += 0.15 if scope_changes else 0
    actual_level += 0.2 if dependencies_failed else 0

    # Clamp to 0-1 range
    actual_level = max(0.0, min(1.0, actual_level))

    print(f"\n[CALC] actual uncertainty: {actual_level:.1%}")
    print("Confirm this value? [y/n] or enter custom value [0-1]:")
    confirm = input("> ")

    if confirm.lower() != "y":
        try:
            actual_level = float(confirm)
            if not (0 <= actual_level <= 1):
                print("[WARN]  Value out of range, using calculated value")
                actual_level = max(0.0, min(1.0, actual_level))
        except ValueError:
            print("[WARN]  Invalid input, using calculated value")

    # Determine actual trend
    prev_level = prediction_entry.get("previous_level", 0.30)
    actual_trend = determine_trend(prev_level, actual_level)

    actual_state = level_to_state(actual_level)

    print("\n[*] Annotation Summary:")
    print(f"   Actual level: {actual_level:.1%}")
    print(f"   Actual trend: {actual_trend}")
    print(f"   Actual state: {actual_state}")

    print("\nAnnotator confidence level [high/medium/low]:")
    confidence = input("> ").lower()
    if confidence not in ["high", "medium", "low"]:
        confidence = "medium"

    return {
        **prediction_entry,
        "actual_global_level": actual_level,
        "actual_global_trend": actual_trend,
        "actual_global_state": actual_state,
        "annotation_timestamp": datetime.now().isoformat(),
        "annotator_confidence": confidence,
        "observations": {
            "blockers": blockers,
            "estimates_matched": estimates_matched,
            "tests_passed": tests_passed,
            "scope_changes": scope_changes,
            "dependencies_failed": dependencies_failed,
        },
    }


def load_predictions_to_annotate(date: Optional[datetime] = None, last_24h: bool = False, limit: int = 10) -> List[Dict]:
    """
    Load predictions that need annotation

    Args:
        date: Specific date to annotate (defaults to 24 hours ago)
        last_24h: Annotate predictions from last 24 hours
        limit: Maximum predictions to return (default 10)

    Returns:
        List of prediction entries to annotate
    """
    storage_dir = get_storage_dir()
    predictions_file = storage_dir / "predictions_log.jsonl"

    if not predictions_file.exists():
        print(f"[FAIL] No predictions log found at: {predictions_file}")
        print("Run UDO with predictions first to generate data.")
        return []

    # Load all predictions
    with open(predictions_file, encoding="utf-8") as f:
        predictions = [json.loads(line) for line in f if line.strip()]

    # Load already annotated predictions
    ground_truth_file = storage_dir / "prediction_ground_truth.jsonl"
    annotated_timestamps = set()
    if ground_truth_file.exists():
        with open(ground_truth_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    annotated_timestamps.add(entry["prediction_timestamp"])

    # Filter predictions
    if date is None:
        target_date = datetime.now() - timedelta(hours=24)
    else:
        target_date = date

    # Find unannotated predictions from target timeframe
    candidates = []
    for pred in predictions:
        # Skip already annotated
        if pred["prediction_timestamp"] in annotated_timestamps:
            continue

        pred_time = datetime.fromisoformat(pred["prediction_timestamp"])
        val_time = datetime.fromisoformat(pred["validation_timestamp"])

        # Check if validation time has passed (24h ahead)
        if val_time > datetime.now():
            continue  # Too early to validate

        # Check if prediction matches target date (within 1 hour window)
        if last_24h:
            # Annotate all predictions from last 24h that are ready
            if (datetime.now() - pred_time).total_seconds() < 86400:
                candidates.append(pred)
        else:
            # Annotate predictions from specific date
            if abs((pred_time - target_date).total_seconds()) < 3600:
                candidates.append(pred)

    # Sort by prediction time (oldest first)
    candidates.sort(key=lambda p: p["prediction_timestamp"])

    return candidates[:limit]


def main():
    parser = argparse.ArgumentParser(description="Ground Truth Annotation Tool for UDO Predictions")
    parser.add_argument("--date", type=str, help="Specific date to annotate (YYYY-MM-DD)")
    parser.add_argument("--last-24h", action="store_true", help="Annotate predictions from last 24 hours")
    parser.add_argument("--all", action="store_true", help="Annotate all unannotated predictions")
    parser.add_argument("--limit", type=int, default=10, help="Maximum predictions to annotate (default 10)")

    args = parser.parse_args()

    # Determine target date
    target_date = None
    if args.date:
        try:
            target_date = datetime.fromisoformat(args.date)
        except ValueError:
            print(f"[FAIL] Invalid date format: {args.date}")
            print("Use YYYY-MM-DD format")
            return

    # Load predictions to annotate
    if args.all:
        limit = 1000  # Large number to get all
    else:
        limit = args.limit

    predictions = load_predictions_to_annotate(date=target_date, last_24h=args.last_24h, limit=limit)

    if not predictions:
        print("[OK] No predictions to annotate!")
        print("\nPossible reasons:")
        print("  - All predictions are already annotated")
        print("  - Validation time hasn't passed yet (need to wait 24h)")
        print("  - No predictions logged yet")
        return

    print(f"[*] Found {len(predictions)} predictions to annotate\n")

    # Annotate each
    ground_truth = []
    for i, pred in enumerate(predictions, 1):
        print(f"\n{'#'*70}")
        print(f"[*] Annotation {i}/{len(predictions)}")
        print(f"{'#'*70}")

        annotated = annotate_prediction(pred)

        if annotated is None:
            print("[*]  Skipped")
            continue

        ground_truth.append(annotated)
        print("[OK] Saved")

    # Save ground truth
    if ground_truth:
        storage_dir = get_storage_dir()
        output_file = storage_dir / "prediction_ground_truth.jsonl"

        with open(output_file, "a", encoding="utf-8") as f:
            for entry in ground_truth:
                f.write(json.dumps(entry) + "\n")

        print(f"\n{'='*70}")
        print(f"[OK] Saved {len(ground_truth)} ground truth annotations")
        print(f"[*] Location: {output_file}")
        print(f"{'='*70}\n")
    else:
        print("\n[WARN]  No annotations saved (all skipped)")


if __name__ == "__main__":
    main()
