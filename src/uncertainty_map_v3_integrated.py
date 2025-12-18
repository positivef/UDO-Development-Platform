"""
Integrated Uncertainty Map v3 with Adaptive Bayesian Learning
=============================================================

This module integrates the existing UncertaintyMapV3 with the new
AdaptiveBayesianUncertainty system for real-time learning and improvement.

Key Enhancements:
1. Real-time Bayesian belief updates
2. Systematic bias detection and correction
3. Kalman filtering for smooth predictions
4. Performance tracking and reporting
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.uncertainty_map_v3 import (
    UncertaintyMapV3,
    UncertaintyVector,
    UncertaintyState,
    PredictiveModel,
    MitigationStrategy
)
from src.adaptive_bayesian_uncertainty import AdaptiveBayesianUncertainty


class IntegratedUncertaintyMapV3:
    """
    Enhanced Uncertainty Map with Adaptive Bayesian Learning

    This class wraps the existing UncertaintyMapV3 and enhances it with
    real-time learning capabilities from the AdaptiveBayesianUncertainty system.
    """

    def __init__(self, project_path: str = ".",
                 data_dir: str = "data/uncertainty_learning"):
        """
        Initialize integrated uncertainty system

        Args:
            project_path: Path to project directory
            data_dir: Directory for storing learning data
        """
        # Initialize original uncertainty map
        self.original_map = UncertaintyMapV3(project_path)

        # Initialize Bayesian learning system
        self.bayesian_system = AdaptiveBayesianUncertainty(
            project_name="UDO-Platform",
            storage_dir=Path(data_dir)
        )

        # Track integration metrics
        self.metrics = {
            "predictions_made": 0,
            "bayesian_corrections": 0,
            "accuracy_improvements": [],
            "bias_corrections": []
        }

        print("[OK] Integrated Uncertainty Map v3 initialized with Bayesian Learning")

    def predict(self, phase: str = "implementation", hours_ahead: int = 24) -> Dict[str, Any]:
        """
        Enhanced prediction with Bayesian learning

        Args:
            phase: Development phase
            hours_ahead: Hours to predict ahead

        Returns:
            Enhanced prediction with Bayesian corrections
        """
        # Analyze current context
        context = {
            "phase": phase,
            "has_code": True,
            "team_size": 5,
            "timeline_weeks": 4
        }
        current_vector, state = self.original_map.analyze_context(context)

        # Get original prediction using predict_evolution
        predictive_model = self.original_map.predict_evolution(current_vector, phase, hours_ahead)

        # Calculate predicted magnitude using the predictive model
        predicted_magnitude = predictive_model.predict_future(hours_ahead)

        # Structure original prediction in expected format
        original_prediction = {
            "current_uncertainty": {
                "technical": current_vector.technical,
                "resource": current_vector.resource,
                "timeline": current_vector.timeline,
                "market": current_vector.market,
                "quality": current_vector.quality,
                "magnitude": current_vector.magnitude
            },
            "prediction": {
                "technical": current_vector.technical * 0.9,  # Simulated prediction
                "resource": current_vector.resource * 0.95,
                "timeline": current_vector.timeline * 1.05,
                "market": current_vector.market * 0.9,
                "quality": current_vector.quality * 0.92,
                "predicted_magnitude": predicted_magnitude,
                "quantum_state": self.original_map.classify_state(predicted_magnitude).value,
                "trend": predictive_model.trend
            },
            "phase": phase
        }

        # Get current uncertainty vector
        current_vector = self._extract_current_vector(original_prediction)

        # Get Bayesian-enhanced prediction
        bayesian_prediction = self.bayesian_system.predict(
            current_uncertainty=current_vector,
            hours_ahead=hours_ahead,
            phase=phase
        )

        # Merge predictions intelligently
        enhanced_prediction = self._merge_predictions(
            original_prediction,
            bayesian_prediction
        )

        # Track metrics
        self.metrics["predictions_made"] += 1

        # Add learning metadata
        enhanced_prediction["learning_metadata"] = {
            "bayesian_confidence": bayesian_prediction.get("confidence", 0),
            "bias_detected": bayesian_prediction.get("bias_profile", {}).get("type", "unbiased"),
            "correction_applied": bayesian_prediction.get("correction_factor", 0),
            "learning_enabled": True,
            "predictions_count": self.metrics["predictions_made"]
        }

        print(f"🧠 Bayesian Enhancement Applied:")
        print(f"   - Confidence: {bayesian_prediction.get('confidence', 0):.1%}")
        print(f"   - Bias: {bayesian_prediction.get('bias_profile', {}).get('type', 'unbiased')}")
        print(f"   - Correction: {bayesian_prediction.get('correction_factor', 0):+.3f}")

        return enhanced_prediction

    def learn_from_outcome(self, predicted: Dict[str, Any], actual: Dict[str, float]):
        """
        Learn from actual outcomes to improve future predictions

        Args:
            predicted: The prediction that was made
            actual: The actual observed values
        """
        # Extract predicted vector
        pred_vector = self._extract_predicted_vector(predicted)

        # Learn from the observation
        self.bayesian_system.learn_from_observation(pred_vector, actual)

        # Calculate improvement
        error_before = abs(pred_vector.get("magnitude", 0.5) - actual.get("magnitude", 0.5))

        # Get corrected prediction
        corrected = self.bayesian_system.predict(
            current_uncertainty=actual,
            hours_ahead=0,  # Current state
            phase=predicted.get("phase", "implementation")
        )

        error_after = abs(corrected.get("predicted_magnitude", 0.5) - actual.get("magnitude", 0.5))
        improvement = (error_before - error_after) / max(error_before, 0.001) * 100

        self.metrics["accuracy_improvements"].append(improvement)

        print(f"[EMOJI] Learning Complete:")
        print(f"   - Error reduction: {improvement:.1f}%")
        print(f"   - Total observations: {len(self.metrics['accuracy_improvements'])}")
        print(f"   - Average improvement: {sum(self.metrics['accuracy_improvements'])/max(len(self.metrics['accuracy_improvements']), 1):.1f}%")

    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get comprehensive performance report

        Returns:
            Performance metrics and learning statistics
        """
        # Get Bayesian performance
        bayesian_perf = self.bayesian_system.get_performance_report()

        # Add integration metrics
        report = {
            "integration_metrics": self.metrics,
            "bayesian_performance": bayesian_perf,
            "summary": {
                "total_predictions": self.metrics["predictions_made"],
                "learning_enabled": True,
                "average_confidence": bayesian_perf.get("average_confidence", 0),
                "bias_profile": bayesian_perf.get("bias_profile", {}),
                "accuracy_trend": "improving" if len(self.metrics["accuracy_improvements"]) > 0 and
                                 sum(self.metrics["accuracy_improvements"][-5:]) > 0 else "stable"
            }
        }

        return report

    def visualize(self, save_path: str = None):
        """
        Visualize uncertainty with Bayesian enhancements

        Args:
            save_path: Optional path to save visualization
        """
        # Use original visualization
        self.original_map.visualize(save_path)

        # Add Bayesian metrics overlay (would need matplotlib in real implementation)
        print("\n[EMOJI] Bayesian Learning Overlay:")
        perf = self.get_performance_report()
        print(f"   - Predictions made: {perf['summary']['total_predictions']}")
        print(f"   - Average confidence: {perf['summary']['average_confidence']:.1%}")
        print(f"   - Accuracy trend: {perf['summary']['accuracy_trend']}")

    def _extract_current_vector(self, prediction: Dict[str, Any]) -> Dict[str, float]:
        """Extract current uncertainty vector from prediction"""
        return {
            "technical": prediction.get("current_uncertainty", {}).get("technical", 0.5),
            "resource": prediction.get("current_uncertainty", {}).get("resource", 0.5),
            "timeline": prediction.get("current_uncertainty", {}).get("timeline", 0.5),
            "market": prediction.get("current_uncertainty", {}).get("market", 0.5),
            "quality": prediction.get("current_uncertainty", {}).get("quality", 0.5),
            "magnitude": prediction.get("current_uncertainty", {}).get("magnitude", 0.5)
        }

    def _extract_predicted_vector(self, prediction: Dict[str, Any]) -> Dict[str, float]:
        """Extract predicted uncertainty vector from prediction"""
        return {
            "technical": prediction.get("prediction", {}).get("technical", 0.5),
            "resource": prediction.get("prediction", {}).get("resource", 0.5),
            "timeline": prediction.get("prediction", {}).get("timeline", 0.5),
            "market": prediction.get("prediction", {}).get("market", 0.5),
            "quality": prediction.get("prediction", {}).get("quality", 0.5),
            "magnitude": prediction.get("prediction", {}).get("predicted_magnitude", 0.5)
        }

    def _merge_predictions(self, original: Dict[str, Any],
                          bayesian: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligently merge original and Bayesian predictions

        Uses confidence-weighted averaging
        """
        # Start with original
        merged = original.copy()

        # Get confidence weights
        original_confidence = 0.3  # Base confidence for original ML model
        bayesian_confidence = bayesian.get("confidence", 0.5)

        # Normalize weights
        total_weight = original_confidence + bayesian_confidence
        orig_weight = original_confidence / total_weight
        bayes_weight = bayesian_confidence / total_weight

        # Merge predicted values
        if "prediction" in merged and "dimensions" in bayesian:
            for dim in bayesian["dimensions"]:
                if dim in merged["prediction"] and dim in bayesian["dimensions"]:
                    orig_val = merged["prediction"][dim]
                    bayes_val = bayesian["dimensions"][dim]["predicted"]
                    merged["prediction"][dim] = orig_weight * orig_val + bayes_weight * bayes_val

        # Update magnitude
        if "predicted_magnitude" in bayesian:
            orig_mag = merged.get("prediction", {}).get("predicted_magnitude", 0.5)
            bayes_mag = bayesian["predicted_magnitude"]
            merged["prediction"]["predicted_magnitude"] = orig_weight * orig_mag + bayes_weight * bayes_mag

        # Apply bias correction if significant
        if abs(bayesian.get("correction_factor", 0)) > 0.05:
            correction = bayesian["correction_factor"]
            merged["prediction"]["predicted_magnitude"] += correction
            self.metrics["bayesian_corrections"] += 1
            self.metrics["bias_corrections"].append(correction)

        return merged

    def save_state(self):
        """Save learning state for persistence"""
        self.bayesian_system.save_state()
        print("[EMOJI] Learning state saved")

    def load_state(self):
        """Load previous learning state"""
        self.bayesian_system.load_state()
        print("[EMOJI] Learning state loaded")


def demo_integration():
    """
    Demonstrate the integrated system
    """
    print("=" * 60)
    print("INTEGRATED UNCERTAINTY MAP V3 WITH BAYESIAN LEARNING")
    print("=" * 60)

    # Initialize integrated system
    integrated = IntegratedUncertaintyMapV3()

    # Make initial prediction
    print("\n1⃣ Making Initial Prediction...")
    prediction1 = integrated.predict(phase="implementation", hours_ahead=24)
    print(f"   - Predicted magnitude: {prediction1['prediction']['predicted_magnitude']:.3f}")
    print(f"   - Quantum state: {prediction1['prediction']['quantum_state']}")

    # Simulate actual outcome
    print("\n2⃣ Simulating Actual Outcome...")
    actual = {
        "technical": 0.4,
        "resource": 0.3,
        "timeline": 0.5,
        "market": 0.35,
        "quality": 0.45,
        "magnitude": 0.37
    }
    print(f"   - Actual magnitude: {actual['magnitude']:.3f}")

    # Learn from outcome
    print("\n3⃣ Learning from Outcome...")
    integrated.learn_from_outcome(prediction1, actual)

    # Make improved prediction
    print("\n4⃣ Making Improved Prediction...")
    prediction2 = integrated.predict(phase="implementation", hours_ahead=24)
    print(f"   - Predicted magnitude: {prediction2['prediction']['predicted_magnitude']:.3f}")
    print(f"   - Learning confidence: {prediction2['learning_metadata']['bayesian_confidence']:.1%}")

    # Show performance report
    print("\n5⃣ Performance Report:")
    report = integrated.get_performance_report()
    print(f"   - Total predictions: {report['summary']['total_predictions']}")
    print(f"   - Accuracy trend: {report['summary']['accuracy_trend']}")
    print(f"   - Bias detected: {report['bayesian_performance'].get('bias_profile', {}).get('type', 'unbiased')}")

    # Save state
    print("\n6⃣ Saving Learning State...")
    integrated.save_state()

    print("\n" + "=" * 60)
    print("[OK] INTEGRATION DEMONSTRATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    demo_integration()