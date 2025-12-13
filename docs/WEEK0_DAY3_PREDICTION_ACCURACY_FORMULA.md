# Week 0 Day 3: Prediction Accuracy Formula Definition

**Date**: 2025-12-07
**Purpose**: Define objective formula for validating UDO's predictive uncertainty modeling
**Status**: Foundation Phase - Critical Metric Baseline
**Target**: ≥80% prediction accuracy (Prototype), ≥85% (Production)

---

## Executive Summary

**Problem**: UDO v3 makes 24-hour ahead uncertainty predictions, but we have no validation method.

**Solution**: Multi-dimensional prediction accuracy formula with ground truth validation.

**Formula**:
```
prediction_accuracy = (
    0.50 × level_accuracy +
    0.30 × trend_accuracy +
    0.20 × state_accuracy
)
```

**Measurement**: 100 manual ground truth annotations over 10 days (10 predictions/day).

**Targets**:
- **Week 0 Baseline**: Measure current accuracy (expected ~50-60%)
- **Prototype (Week 4-5)**: ≥55% prediction accuracy
- **Beta (Week 6-8)**: ≥65% prediction accuracy
- **Production (Week 9-10)**: ≥80% prediction accuracy

---

## Prediction Types (What UDO Predicts)

UDO v3's `predict(hours_ahead)` returns:

```python
{
    "global": {
        "level": 0.45,        # Uncertainty level (0-1)
        "trend": "increasing" # Direction (increasing/decreasing/stable)
    },
    "technical": {"level": 0.30, "trend": "stable"},
    "market": {"level": 0.60, "trend": "decreasing"},
    "resource": {"level": 0.25, "trend": "stable"},
    "timeline": {"level": 0.50, "trend": "increasing"},
    "quality": {"level": 0.35, "trend": "stable"}
}
```

**Three Validation Dimensions**:
1. **Level Accuracy**: How close predicted `level` is to actual observed level
2. **Trend Accuracy**: How often `trend` direction is correct
3. **State Accuracy**: How often predicted uncertainty state matches actual

---

## Component 1: Level Accuracy (50% weight)

### Formula

```python
def calculate_level_accuracy(predictions, actuals):
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
```

### Example Calculation

```python
# Scenario: 24-hour ahead predictions for global uncertainty
predictions = [
    ("2025-12-07 00:00", 0.45),  # Predicted: 45% uncertainty
    ("2025-12-07 01:00", 0.50),
    ("2025-12-07 02:00", 0.48),
]

actuals = [
    ("2025-12-07 00:00", 0.42),  # Actual: 42% uncertainty (observed)
    ("2025-12-07 01:00", 0.55),
    ("2025-12-07 02:00", 0.46),
]

# Calculation:
# APE_1 = |0.45 - 0.42| / 0.42 = 0.03 / 0.42 = 0.071 (7.1%)
# APE_2 = |0.50 - 0.55| / 0.55 = 0.05 / 0.55 = 0.091 (9.1%)
# APE_3 = |0.48 - 0.46| / 0.46 = 0.02 / 0.46 = 0.043 (4.3%)
# MAPE = (0.071 + 0.091 + 0.043) / 3 = 0.0683 (6.83%)
# Level Accuracy = (1 - 0.0683) × 100 = 93.17%
```

### Ground Truth Annotation (How to Measure "Actual")

**Method**: Manual observation of actual uncertainty 24 hours later.

**Annotation Guide** (`data/prediction_ground_truth_template.yaml`):
```yaml
# Prediction made at: 2025-12-07 10:00
# Validation time: 2025-12-08 10:00 (24 hours later)

prediction:
  timestamp: "2025-12-07 10:00:00"
  hours_ahead: 24
  predicted_global_level: 0.45  # UDO predicted 45% uncertainty

actual:
  timestamp: "2025-12-08 10:00:00"
  observed_global_level: 0.42  # Actual: 42% uncertainty

  # How to determine "actual" uncertainty:
  observation_criteria:
    - "Did unexpected blockers occur? (+0.1 per blocker)"
    - "Did estimates match actual time? (No mismatch: -0.1)"
    - "Did all tests pass first try? (Yes: -0.1)"
    - "Were there scope changes? (+0.15 per change)"
    - "Did dependencies fail? (+0.2 per dependency)"

  # Example calculation:
  base_uncertainty: 0.30  # Normal baseline
  blockers: 1             # +0.1
  scope_changes: 0        # +0.0
  test_failures: 1        # +0.1 (tests didn't pass first try)
  dependency_issues: 0    # +0.0

  total_observed: 0.30 + 0.1 + 0.1 = 0.50  # Actual: 50%

annotator: "Developer Name"
confidence: "high"  # high/medium/low (annotator's confidence in ground truth)
```

**Validation**: 100 samples (10 predictions/day × 10 days).

---

## Component 2: Trend Accuracy (30% weight)

### Formula

```python
def calculate_trend_accuracy(predictions, actuals):
    """
    Trend accuracy based on direction match percentage

    Args:
        predictions: List[(timestamp, predicted_trend)]  # "increasing"/"decreasing"/"stable"
        actuals: List[(timestamp, actual_trend)]

    Returns:
        float: Trend accuracy percentage (0-100%)
    """
    if len(predictions) != len(actuals):
        raise ValueError("Predictions and actuals must have same length")

    correct_trends = 0
    for (pred_ts, pred_trend), (actual_ts, actual_trend) in zip(predictions, actuals):
        if pred_ts != actual_ts:
            raise ValueError(f"Timestamp mismatch: {pred_ts} != {actual_ts}")

        if pred_trend == actual_trend:
            correct_trends += 1

    trend_accuracy = (correct_trends / len(predictions)) * 100
    return trend_accuracy
```

### Trend Determination (Ground Truth)

**Method**: Compare current vs future uncertainty level.

```python
def determine_actual_trend(current_level, future_level, threshold=0.05):
    """
    Determine actual trend from observed levels

    Args:
        current_level: Uncertainty level at prediction time
        future_level: Uncertainty level 24 hours later (actual)
        threshold: Minimum change to classify as increasing/decreasing (default 5%)

    Returns:
        str: "increasing" | "decreasing" | "stable"
    """
    delta = future_level - current_level

    if delta > threshold:
        return "increasing"
    elif delta < -threshold:
        return "decreasing"
    else:
        return "stable"
```

### Example Calculation

```python
predictions = [
    ("2025-12-07 00:00", "increasing"),
    ("2025-12-07 01:00", "stable"),
    ("2025-12-07 02:00", "decreasing"),
]

# Ground truth annotation:
# At 2025-12-07 00:00, level was 0.40
# At 2025-12-08 00:00, level was 0.52 (+0.12 > 0.05 threshold)
# → Actual trend: "increasing" ✅ Match!

actuals = [
    ("2025-12-07 00:00", "increasing"),   # ✅ Correct
    ("2025-12-07 01:00", "increasing"),   # ❌ Wrong (predicted stable)
    ("2025-12-07 02:00", "decreasing"),   # ✅ Correct
]

# Calculation:
# Correct: 2/3
# Trend Accuracy = (2 / 3) × 100 = 66.67%
```

---

## Component 3: State Accuracy (20% weight)

### Formula

```python
def calculate_state_accuracy(predictions, actuals):
    """
    State accuracy based on uncertainty state classification match

    UncertaintyState:
        DETERMINISTIC: <10% uncertainty
        PROBABILISTIC: 10-30%
        QUANTUM: 30-60%
        CHAOTIC: 60-90%
        VOID: >90%

    Args:
        predictions: List[(timestamp, predicted_state)]
        actuals: List[(timestamp, actual_state)]

    Returns:
        float: State accuracy percentage (0-100%)
    """
    if len(predictions) != len(actuals):
        raise ValueError("Predictions and actuals must have same length")

    correct_states = 0
    for (pred_ts, pred_state), (actual_ts, actual_state) in zip(predictions, actuals):
        if pred_ts != actual_ts:
            raise ValueError(f"Timestamp mismatch: {pred_ts} != {actual_ts}")

        if pred_state == actual_state:
            correct_states += 1

    state_accuracy = (correct_states / len(predictions)) * 100
    return state_accuracy

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
```

### Example Calculation

```python
# Predictions with levels converted to states
predictions = [
    ("2025-12-07 00:00", 0.25, "PROBABILISTIC"),  # 25% → PROBABILISTIC
    ("2025-12-07 01:00", 0.45, "QUANTUM"),        # 45% → QUANTUM
    ("2025-12-07 02:00", 0.08, "DETERMINISTIC"),  # 8% → DETERMINISTIC
]

# Actuals (observed levels converted to states)
actuals = [
    ("2025-12-07 00:00", 0.28, "PROBABILISTIC"),  # 28% → PROBABILISTIC ✅
    ("2025-12-07 01:00", 0.55, "QUANTUM"),        # 55% → QUANTUM ✅
    ("2025-12-07 02:00", 0.15, "PROBABILISTIC"),  # 15% → PROBABILISTIC ❌
]

# Calculation:
# Correct: 2/3 (PROBABILISTIC match, QUANTUM match, DETERMINISTIC mismatch)
# State Accuracy = (2 / 3) × 100 = 66.67%
```

---

## Overall Prediction Accuracy Formula

### Weighted Composite

```python
def calculate_prediction_accuracy(
    predictions: List[Dict],
    actuals: List[Dict]
) -> Dict[str, float]:
    """
    Calculate overall prediction accuracy with weighted components

    Args:
        predictions: List of prediction dicts with keys:
            - timestamp: str
            - level: float
            - trend: str
            - state: str

        actuals: List of actual observation dicts (same structure)

    Returns:
        dict: {
            "overall": float,
            "components": {
                "level_accuracy": float,
                "trend_accuracy": float,
                "state_accuracy": float
            }
        }
    """
    # Extract components
    pred_levels = [(p["timestamp"], p["level"]) for p in predictions]
    actual_levels = [(a["timestamp"], a["level"]) for a in actuals]

    pred_trends = [(p["timestamp"], p["trend"]) for p in predictions]
    actual_trends = [(a["timestamp"], a["trend"]) for a in actuals]

    pred_states = [(p["timestamp"], p["state"]) for p in predictions]
    actual_states = [(a["timestamp"], a["state"]) for a in actuals]

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

    return {
        "overall": overall_accuracy,
        "components": {
            "level_accuracy": level_acc,
            "trend_accuracy": trend_acc,
            "state_accuracy": state_acc
        }
    }
```

### Example: Full Calculation

```python
predictions = [
    {
        "timestamp": "2025-12-07 10:00",
        "level": 0.45,
        "trend": "increasing",
        "state": "QUANTUM"
    },
    {
        "timestamp": "2025-12-07 11:00",
        "level": 0.28,
        "trend": "stable",
        "state": "PROBABILISTIC"
    }
]

actuals = [
    {
        "timestamp": "2025-12-07 10:00",
        "level": 0.42,      # 7% error → 93% level accuracy
        "trend": "increasing",  # ✅ Match
        "state": "QUANTUM"      # ✅ Match
    },
    {
        "timestamp": "2025-12-07 11:00",
        "level": 0.35,      # 25% error → 75% level accuracy
        "trend": "increasing",  # ❌ Wrong
        "state": "QUANTUM"      # ❌ Wrong (35% → QUANTUM, not PROBABILISTIC)
    }
]

# Component Calculations:
# Level Accuracy = ((1 - 0.07) + (1 - 0.25)) / 2 × 100 = 84%
# Trend Accuracy = 1/2 × 100 = 50%
# State Accuracy = 1/2 × 100 = 50%

# Overall:
# Prediction Accuracy = 0.50×84 + 0.30×50 + 0.20×50
#                     = 42 + 15 + 10
#                     = 67%
```

---

## Ground Truth Annotation Process

### Step 1: Prediction Logging

**Automated**: Every prediction call logs to `data/predictions_log.jsonl`.

```python
# In src/uncertainty_map_v3.py predict() method
import json
from pathlib import Path

def predict(self, hours_ahead: int) -> Dict[str, Any]:
    result = self._generate_prediction(hours_ahead)

    # Log prediction for future validation
    log_entry = {
        "prediction_timestamp": datetime.now().isoformat(),
        "hours_ahead": hours_ahead,
        "validation_timestamp": (datetime.now() + timedelta(hours=hours_ahead)).isoformat(),
        "predicted_global_level": result["global"]["level"],
        "predicted_global_trend": result["global"]["trend"],
        "predicted_global_state": self._level_to_state(result["global"]["level"])
    }

    log_file = Path("data/predictions_log.jsonl")
    log_file.parent.mkdir(exist_ok=True)

    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return result
```

### Step 2: Manual Annotation

**Daily Task** (10 minutes/day): Annotate 10 predictions from 24 hours ago.

**Tool**: `scripts/annotate_ground_truth.py` (interactive CLI)

```python
#!/usr/bin/env python3
"""
Ground Truth Annotation Tool - Week 0 Day 3

Usage:
    python scripts/annotate_ground_truth.py --date 2025-12-06
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

def annotate_prediction(prediction_entry):
    """Interactive annotation of a single prediction"""
    print(f"\n{'='*60}")
    print(f"Prediction made at: {prediction_entry['prediction_timestamp']}")
    print(f"Predicted global uncertainty: {prediction_entry['predicted_global_level']:.2%}")
    print(f"Predicted trend: {prediction_entry['predicted_global_trend']}")
    print(f"Predicted state: {prediction_entry['predicted_global_state']}")
    print(f"{'='*60}\n")

    # Ask annotator to observe actual uncertainty
    print("Based on what happened in the last 24 hours:")
    print("1. Did unexpected blockers occur? [y/n]")
    blockers = input("> ").lower() == 'y'

    print("2. Did estimates match actual time? [y/n]")
    estimates_matched = input("> ").lower() == 'y'

    print("3. Did all tests pass first try? [y/n]")
    tests_passed = input("> ").lower() == 'y'

    print("4. Were there scope changes? [y/n]")
    scope_changes = input("> ").lower() == 'y'

    print("5. Did dependencies fail? [y/n]")
    dependencies_failed = input("> ").lower() == 'y'

    # Calculate actual uncertainty
    base = 0.30
    actual_level = base
    actual_level += 0.1 if blockers else 0
    actual_level += -0.1 if estimates_matched else 0
    actual_level += -0.1 if tests_passed else 0.1
    actual_level += 0.15 if scope_changes else 0
    actual_level += 0.2 if dependencies_failed else 0

    print(f"\n→ Calculated actual uncertainty: {actual_level:.2%}")
    print("Confirm this value? [y/n] or enter custom value [0-1]:")
    confirm = input("> ")

    if confirm.lower() != 'y':
        try:
            actual_level = float(confirm)
        except ValueError:
            print("Invalid input, using calculated value")

    # Determine actual trend
    prev_level = prediction_entry.get("previous_level", 0.30)
    actual_trend = determine_trend(prev_level, actual_level)

    actual_state = level_to_state(actual_level)

    return {
        **prediction_entry,
        "actual_global_level": actual_level,
        "actual_global_trend": actual_trend,
        "actual_global_state": actual_state,
        "annotation_timestamp": datetime.now().isoformat(),
        "annotator_confidence": "high"  # Could make this interactive
    }

def main():
    # Load predictions from 24 hours ago
    target_date = datetime.now() - timedelta(hours=24)

    predictions_file = Path("data/predictions_log.jsonl")
    if not predictions_file.exists():
        print("No predictions log found. Run UDO first to generate predictions.")
        return

    # Filter predictions from target date
    with open(predictions_file) as f:
        predictions = [json.loads(line) for line in f]

    target_predictions = [
        p for p in predictions
        if abs((datetime.fromisoformat(p["prediction_timestamp"]) - target_date).total_seconds()) < 3600
    ]

    print(f"Found {len(target_predictions)} predictions to annotate")

    # Annotate each
    ground_truth = []
    for pred in target_predictions[:10]:  # Limit to 10/day
        annotated = annotate_prediction(pred)
        ground_truth.append(annotated)

    # Save ground truth
    output_file = Path("data/prediction_ground_truth.jsonl")
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "a") as f:
        for entry in ground_truth:
            f.write(json.dumps(entry) + "\n")

    print(f"\n✅ Saved {len(ground_truth)} ground truth annotations")

if __name__ == "__main__":
    main()
```

### Step 3: Validation

**Automated**: After 100 samples, calculate prediction accuracy.

```bash
# Week 0 Day 4-5: After collecting 100 samples
python scripts/calculate_prediction_accuracy.py --samples 100
```

---

## Implementation Plan (Week 0 Day 3-4)

### Day 3 (Today - 2 hours)

1. **Create prediction logging** (30 min):
   - Add logging to `src/uncertainty_map_v3.py predict()` method
   - Test with 5 sample predictions

2. **Create annotation tool** (60 min):
   - Implement `scripts/annotate_ground_truth.py`
   - Test interactive workflow
   - Create sample ground truth (5 samples)

3. **Create accuracy calculator** (30 min):
   - Implement `scripts/calculate_prediction_accuracy.py`
   - Test with sample data
   - Validate formula correctness

### Day 4 (Ongoing - 10 min/day for 10 days)

4. **Collect ground truth** (10 min/day × 10 days):
   - Annotate 10 predictions/day
   - Target: 100 total samples
   - Timeline: Days 4-13

5. **Measure baseline** (Day 14):
   - Calculate Week 0 baseline accuracy
   - Document in `WEEK0_DAY4_PREDICTION_BASELINE.md`
   - Expected: 50-60% accuracy (before optimization)

---

## Success Criteria

**Week 0 Day 3**:
- [x] Formula defined ✅ (this document)
- [ ] Prediction logging implemented
- [ ] Annotation tool created
- [ ] Accuracy calculator created
- [ ] 5 sample ground truth annotations collected

**Week 0 Day 4-13** (ongoing):
- [ ] 100 ground truth annotations (10/day × 10 days)

**Week 0 Day 14**:
- [ ] Baseline prediction accuracy measured
- [ ] Report: `WEEK0_DAY4_PREDICTION_BASELINE.md`

**Targets by Phase**:
- Week 0: Baseline measurement (50-60% expected)
- Prototype (Week 4-5): ≥55%
- Beta (Week 6-8): ≥65%
- Production (Week 9-10): ≥80%

---

## Example: Full 100-Sample Report

```yaml
# data/prediction_accuracy_week0_baseline.yaml

measurement_period:
  start: "2025-12-07"
  end: "2025-12-17"
  total_samples: 100

overall_accuracy: 58.3%

components:
  level_accuracy: 67.2%  # MAPE-based
  trend_accuracy: 52.0%  # Direction match
  state_accuracy: 48.0%  # Classification match

breakdown_by_dimension:
  global:
    level_accuracy: 67.2%
    trend_accuracy: 52.0%
    state_accuracy: 48.0%

  technical:
    level_accuracy: 72.1%
    trend_accuracy: 60.0%
    state_accuracy: 55.0%

  market:
    level_accuracy: 45.3%  # ← Low: Market unpredictable
    trend_accuracy: 40.0%
    state_accuracy: 38.0%

common_errors:
  - "Market dimension: 60% false positives (predicted high, actual low)"
  - "Trend: 48% missed 'stable' → 'increasing' transitions"
  - "State: Confused QUANTUM (30-60%) with PROBABILISTIC (10-30%) in 30% of cases"

improvement_recommendations:
  - "Add market volatility features to model"
  - "Lower trend threshold from 5% to 3% for better stability detection"
  - "Refine state boundaries: PROBABILISTIC should be 10-25%, not 10-30%"
```

---

## Appendix: Alternative Formulas (Considered but Rejected)

### Alternative A: Simple Binary (Too Coarse)

```python
# ❌ Rejected: Loss of granularity
def simple_accuracy(predictions, actuals):
    correct = sum(1 for p, a in zip(predictions, actuals) if abs(p - a) < 0.1)
    return correct / len(predictions) * 100
```

**Why Rejected**: Doesn't differentiate between 9% error and 1% error (both counted as "correct").

### Alternative B: RMSE (Root Mean Square Error)

```python
# ❌ Rejected: Hard to interpret
def rmse_accuracy(predictions, actuals):
    squared_errors = [(p - a)**2 for p, a in zip(predictions, actuals)]
    rmse = math.sqrt(sum(squared_errors) / len(squared_errors))
    return (1 - rmse) * 100  # Convert to accuracy
```

**Why Rejected**: RMSE penalizes large errors quadratically, but we want linear penalty. Also harder to explain to stakeholders.

### Alternative C: R² (Coefficient of Determination)

```python
# ❌ Rejected: Not suitable for time series
def r_squared(predictions, actuals):
    mean_actual = sum(actuals) / len(actuals)
    ss_total = sum((a - mean_actual)**2 for a in actuals)
    ss_residual = sum((a - p)**2 for a, p in zip(actuals, predictions))
    return (1 - ss_residual / ss_total) * 100
```

**Why Rejected**: R² measures variance explained, not prediction accuracy. Can be negative if predictions are worse than mean baseline.

**Why We Chose MAPE**:
- ✅ Easy to interpret (percentage error)
- ✅ Scale-independent (works for 0-1 range)
- ✅ Linear penalty (proportional to error size)
- ✅ Industry standard for forecasting

---

## Next Steps

1. **Implement prediction logging** in `src/uncertainty_map_v3.py`
2. **Create annotation tool** `scripts/annotate_ground_truth.py`
3. **Create accuracy calculator** `scripts/calculate_prediction_accuracy.py`
4. **Collect 5 sample annotations** (proof of concept)
5. **Start 10-day ground truth collection** (100 samples total)

**Status**: Week 0 Day 3 - Prediction Accuracy Formula Defined ✅
**Next**: Implement logging + annotation tools
**Timeline**: Day 3 (2 hours) + Day 4-13 (10 min/day × 10 days)

---

*Generated with [Claude Code](https://claude.com/claude-code)*
*Week 0 Foundation Phase - Day 3 of 5*
*Co-Authored-By: Claude <noreply@anthropic.com>*
