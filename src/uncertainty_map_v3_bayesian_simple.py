"""
Simplified Integration of UncertaintyMapV3 with Adaptive Bayesian Learning
==========================================================================

This module provides a simple but effective integration between the existing
UncertaintyMapV3 and the new AdaptiveBayesianUncertainty system.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.adaptive_bayesian_uncertainty import AdaptiveBayesianUncertainty
from src.uncertainty_map_v3 import UncertaintyMapV3, UncertaintyVector


class SimpleBayesianIntegration:
    """Simplified integration of Bayesian learning with UncertaintyMapV3"""

    def __init__(self, project_name: str = "UDO-Platform"):
        """Initialize both systems"""
        self.uncertainty_map = UncertaintyMapV3(project_name)
        self.bayesian_system = AdaptiveBayesianUncertainty(
            project_name=project_name,
            storage_dir=Path.home() / ".udo" / "bayesian_integration",
        )

        print("[OK] Bayesian-Enhanced Uncertainty System Initialized")

    def predict_with_learning(
        self, phase: str = "implementation", hours_ahead: int = 24
    ) -> Dict[str, Any]:
        """
        Make predictions using both systems and combine intelligently

        Returns:
            Combined prediction with Bayesian enhancements
        """
        # Step 1: Get current uncertainty state from UncertaintyMapV3
        context = {
            "phase": phase,
            "has_code": True,
            "team_size": 5,
            "timeline_weeks": 4,
        }
        current_vector, current_state = self.uncertainty_map.analyze_context(context)

        # Step 2: Get predictive model from UncertaintyMapV3
        predictive_model = self.uncertainty_map.predict_evolution(
            current_vector, phase, hours_ahead
        )

        # Step 3: Get Bayesian predictions
        current_dict = {
            "technical": current_vector.technical,
            "resource": current_vector.resource,
            "timeline": current_vector.timeline,
            "market": current_vector.market,
            "quality": current_vector.quality,
            "magnitude": current_vector.magnitude,
        }

        bayesian_pred = self.bayesian_system.predict_uncertainty(
            current_vector=current_vector, phase=phase, horizon_hours=hours_ahead
        )

        # Step 4: Combine predictions intelligently
        # Use Bayesian confidence to weight the predictions
        bayesian_confidence = bayesian_pred.get("confidence", 0.3)
        base_confidence = 0.7

        # Weight average based on confidence
        total_weight = base_confidence + bayesian_confidence
        base_weight = base_confidence / total_weight
        bayes_weight = bayesian_confidence / total_weight

        # Calculate combined predicted magnitude
        base_prediction = predictive_model.predict_future(hours_ahead)
        bayes_prediction = bayesian_pred.get("predicted_magnitude", base_prediction)

        combined_magnitude = (
            base_weight * base_prediction + bayes_weight * bayes_prediction
        )

        # Apply bias correction if available
        if abs(bayesian_pred.get("correction_factor", 0)) > 0.05:
            combined_magnitude += bayesian_pred["correction_factor"]

        # Classify the combined state
        combined_state = self.uncertainty_map.classify_state(combined_magnitude)

        # Step 5: Build comprehensive result
        result = {
            "current_state": {
                "magnitude": current_vector.magnitude,
                "state": current_state.value,
                "dimensions": current_dict,
            },
            "prediction": {
                "magnitude": combined_magnitude,
                "state": combined_state.value,
                "trend": predictive_model.trend,
                "confidence": (base_confidence + bayesian_confidence) / 2,
                "hours_ahead": hours_ahead,
            },
            "bayesian_insights": {
                "confidence": bayesian_confidence,
                "bias_detected": bayesian_pred.get("bias_profile", {}).get(
                    "type", "unbiased"
                ),
                "correction_applied": bayesian_pred.get("correction_factor", 0),
                "recommendations": bayesian_pred.get("recommendations", []),
            },
            "phase": phase,
            "timestamp": datetime.now().isoformat(),
        }

        return result

    def learn_from_outcome(self, prediction: Dict[str, Any], actual_magnitude: float):
        """
        Learn from actual outcomes to improve future predictions

        Args:
            prediction: The prediction that was made
            actual_magnitude: The actual observed magnitude
        """
        # Extract current dimensions
        current_dims = prediction["current_state"]["dimensions"]

        # Scale dimensions based on actual vs predicted magnitude
        scale_factor = (
            actual_magnitude / prediction["prediction"]["magnitude"]
            if prediction["prediction"]["magnitude"] > 0
            else 1.0
        )

        # Create actual observation as UncertaintyVector
        actual_vector = UncertaintyVector(
            technical=current_dims["technical"] * scale_factor,
            market=current_dims["market"] * scale_factor,
            resource=current_dims["resource"] * scale_factor,
            timeline=current_dims["timeline"] * scale_factor,
            quality=current_dims["quality"] * scale_factor,
        )

        # Get the most recent Bayesian prediction for this phase
        # (In a real system, you'd store this from the predict call)
        # For now, make a fresh prediction to get the structure
        bayesian_pred = self.bayesian_system.predict_uncertainty(
            current_vector=actual_vector,
            phase=prediction["phase"],
            horizon_hours=0,  # Current state
        )

        # Update Bayesian system
        self.bayesian_system.update_with_observation(
            phase=prediction["phase"],
            predicted=bayesian_pred,
            observed_vector=actual_vector,
            outcome_success=actual_magnitude
            < prediction["prediction"]["magnitude"],  # Success if uncertainty decreased
        )

        print(
            f"[OK] Learned from outcome: predicted={prediction['prediction']['magnitude']:.3f}, actual={actual_magnitude:.3f}"
        )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from Bayesian system"""
        return self.bayesian_system.get_performance_report()


def demo():
    """Demonstrate the simplified integration"""
    print("\n" + "=" * 60)
    print("SIMPLIFIED BAYESIAN-ENHANCED UNCERTAINTY PREDICTION")
    print("=" * 60)

    # Initialize system
    system = SimpleBayesianIntegration()

    # Phase 1: Make initial predictions
    print("\n[EMOJI] Phase 1: Initial Predictions")
    predictions = []
    phases = ["ideation", "design", "mvp", "implementation", "testing"]

    for phase in phases:
        pred = system.predict_with_learning(phase=phase, hours_ahead=24)
        predictions.append(pred)
        print(
            f"   {phase:15} -> magnitude: {pred['prediction']['magnitude']:.3f}, "
            f"confidence: {pred['prediction']['confidence']:.1%}"
        )

    # Phase 2: Simulate learning from outcomes
    print("\n[EMOJI] Phase 2: Learning from Outcomes")
    for pred in predictions:
        # Simulate actual outcome (slightly different from prediction)
        actual_magnitude = (
            pred["prediction"]["magnitude"] * 0.9
        )  # Actual was 10% better
        system.learn_from_outcome(pred, actual_magnitude)

    # Phase 3: Make improved predictions
    print("\n[EMOJI] Phase 3: Improved Predictions (After Learning)")
    for phase in phases:
        pred = system.predict_with_learning(phase=phase, hours_ahead=24)
        print(
            f"   {phase:15} -> magnitude: {pred['prediction']['magnitude']:.3f}, "
            f"confidence: {pred['prediction']['confidence']:.1%}, "
            f"bias: {pred['bayesian_insights']['bias_detected']}"
        )

    # Phase 4: Show performance metrics
    print("\n[EMOJI] Phase 4: Performance Metrics")
    metrics = system.get_performance_metrics()
    print(f"   Total predictions: {metrics.get('predictions_made', 0)}")
    print(f"   Average confidence: {metrics.get('average_confidence', 0):.1%}")
    print(f"   Bias profile: {metrics.get('bias_profile', {}).get('type', 'unbiased')}")
    print(f"   Accuracy trend: {metrics.get('accuracy_history', [])[-5:]}")

    # Save state for persistence
    system.bayesian_system.save_state()
    print("\n[EMOJI] Learning state saved for future sessions")

    print("\n" + "=" * 60)
    print("[OK] DEMONSTRATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    demo()
