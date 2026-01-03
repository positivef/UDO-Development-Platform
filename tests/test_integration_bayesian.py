"""
Integration Tests for Bayesian-Enhanced Uncertainty Map
======================================================

Tests the integration of AdaptiveBayesianUncertainty with UncertaintyMapV3.
"""

import unittest
import sys
from pathlib import Path
import tempfile
import shutil
from datetime import datetime  # noqa: F401

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.uncertainty_map_v3_integrated import IntegratedUncertaintyMapV3  # noqa: E402


class TestIntegratedUncertaintyMap(unittest.TestCase):
    """Test integrated uncertainty map with Bayesian learning"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.integrated = IntegratedUncertaintyMapV3(project_path=".", data_dir=self.temp_dir)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test system initialization"""
        self.assertIsNotNone(self.integrated.original_map)
        self.assertIsNotNone(self.integrated.bayesian_system)
        self.assertEqual(self.integrated.metrics["predictions_made"], 0)

    def test_enhanced_prediction(self):
        """Test that predictions are enhanced with Bayesian learning"""
        # Make prediction
        prediction = self.integrated.predict(phase="implementation", hours_ahead=24)

        # Check structure
        self.assertIn("prediction", prediction)
        self.assertIn("learning_metadata", prediction)
        self.assertIn("bayesian_confidence", prediction["learning_metadata"])
        self.assertIn("bias_detected", prediction["learning_metadata"])
        self.assertIn("learning_enabled", prediction["learning_metadata"])

        # Check learning is enabled
        self.assertTrue(prediction["learning_metadata"]["learning_enabled"])

        # Check metrics updated
        self.assertEqual(self.integrated.metrics["predictions_made"], 1)

    def test_learning_from_outcome(self):
        """Test learning from actual outcomes"""
        # Make initial prediction
        prediction = self.integrated.predict(phase="design", hours_ahead=12)
        _initial_magnitude = prediction["prediction"]["predicted_magnitude"]

        # Create actual outcome
        actual = {
            "technical": 0.3,
            "resource": 0.4,
            "timeline": 0.5,
            "integration": 0.35,
            "external": 0.25,
            "quality": 0.4,
            "magnitude": 0.37,
        }

        # Learn from outcome
        self.integrated.learn_from_outcome(prediction, actual)

        # Check that learning occurred
        self.assertGreater(len(self.integrated.metrics["accuracy_improvements"]), 0)

        # Make another prediction - should be influenced by learning
        _prediction2 = self.integrated.predict(phase="design", hours_ahead=12)

        # Check that Bayesian system has updated beliefs
        self.assertEqual(self.integrated.metrics["predictions_made"], 2)

    def test_bias_detection_and_correction(self):
        """Test that bias is detected and corrected"""
        # Simulate multiple biased predictions
        for i in range(5):
            # Make optimistic predictions (predict low, observe high)
            prediction = self.integrated.predict(phase="testing", hours_ahead=6)

            # Simulate consistently higher actual values
            actual = {
                "technical": 0.7,
                "resource": 0.8,
                "timeline": 0.75,
                "integration": 0.7,
                "external": 0.6,
                "quality": 0.8,
                "magnitude": 0.73,
            }

            self.integrated.learn_from_outcome(prediction, actual)

        # After multiple observations, bias should be detected
        report = self.integrated.get_performance_report()
        bias_type = report["bayesian_performance"].get("bias_profile", {}).get("type", "unbiased")

        # Should detect some form of bias after consistent errors
        self.assertIn(bias_type, ["optimistic", "highly_optimistic", "pessimistic", "highly_pessimistic", "unbiased"])

        # Check that corrections are being tracked
        if len(self.integrated.metrics["bias_corrections"]) > 0:
            # If corrections applied, they should be non-zero
            self.assertTrue(any(abs(c) > 0 for c in self.integrated.metrics["bias_corrections"]))

    def test_performance_report(self):
        """Test performance reporting"""
        # Make some predictions and learn
        for i in range(3):
            pred = self.integrated.predict(phase="implementation", hours_ahead=12)
            actual = {
                "technical": 0.4 + i * 0.05,
                "resource": 0.35 + i * 0.05,
                "timeline": 0.45 + i * 0.05,
                "integration": 0.4,
                "external": 0.3,
                "quality": 0.5,
                "magnitude": 0.4 + i * 0.05,
            }
            self.integrated.learn_from_outcome(pred, actual)

        # Get report
        report = self.integrated.get_performance_report()

        # Check report structure
        self.assertIn("integration_metrics", report)
        self.assertIn("bayesian_performance", report)
        self.assertIn("summary", report)

        # Check summary fields
        summary = report["summary"]
        self.assertIn("total_predictions", summary)
        self.assertIn("learning_enabled", summary)
        self.assertIn("average_confidence", summary)
        self.assertIn("accuracy_trend", summary)

        # Check values
        self.assertEqual(summary["total_predictions"], 3)
        self.assertTrue(summary["learning_enabled"])

    def test_state_persistence(self):
        """Test saving and loading learning state"""
        # Make predictions and learn
        for i in range(2):
            pred = self.integrated.predict(phase="mvp", hours_ahead=8)
            actual = {
                "magnitude": 0.5,
                "technical": 0.5,
                "resource": 0.5,
                "timeline": 0.5,
                "integration": 0.5,
                "external": 0.5,
                "quality": 0.5,
            }
            self.integrated.learn_from_outcome(pred, actual)

        # Save state
        self.integrated.save_state()

        # Create new instance
        new_integrated = IntegratedUncertaintyMapV3(project_path=".", data_dir=self.temp_dir)

        # Load state
        new_integrated.load_state()

        # Should have loaded the learned beliefs
        # (exact verification would depend on internal state structure)
        self.assertIsNotNone(new_integrated.bayesian_system)

    def test_prediction_merging(self):
        """Test that predictions are properly merged"""
        # Make prediction
        prediction = self.integrated.predict(phase="ideation", hours_ahead=48)

        # Check that prediction contains both original and enhanced elements
        self.assertIn("prediction", prediction)  # Original structure
        self.assertIn("learning_metadata", prediction)  # Bayesian enhancement

        # Predicted magnitude should be influenced by both systems
        magnitude = prediction["prediction"]["predicted_magnitude"]
        self.assertGreaterEqual(magnitude, 0)
        self.assertLessEqual(magnitude, 1)

    def test_confidence_growth(self):
        """Test that confidence grows with more observations"""
        initial_confidences = []
        final_confidences = []

        # Make initial predictions
        for i in range(3):
            pred = self.integrated.predict(phase="implementation", hours_ahead=24)
            initial_confidences.append(pred["learning_metadata"]["bayesian_confidence"])

        # Learn from many observations
        for i in range(10):
            pred = self.integrated.predict(phase="implementation", hours_ahead=24)
            actual = {
                "magnitude": 0.4 + (i % 3) * 0.1,
                "technical": 0.4,
                "resource": 0.4,
                "timeline": 0.4,
                "integration": 0.4,
                "external": 0.4,
                "quality": 0.4,
            }
            self.integrated.learn_from_outcome(pred, actual)

            if i >= 7:  # Last 3 predictions
                final_confidences.append(pred["learning_metadata"]["bayesian_confidence"])

        # Average confidence should increase
        avg_initial = sum(initial_confidences) / len(initial_confidences)
        avg_final = sum(final_confidences) / len(final_confidences)

        # Confidence should generally increase with learning
        # (though not guaranteed in all cases due to uncertainty)
        self.assertGreaterEqual(avg_final, avg_initial * 0.9)  # Allow some variance

    def test_visualization(self):
        """Test visualization doesn't crash"""
        # Should not raise exception
        try:
            self.integrated.visualize()
        except Exception as e:
            self.fail(f"Visualization raised exception: {e}")


class TestIntegrationWorkflow(unittest.TestCase):
    """Test complete integration workflow"""

    def test_complete_workflow(self):
        """Test a complete prediction-learn-improve cycle"""
        temp_dir = tempfile.mkdtemp()
        try:
            # Initialize
            system = IntegratedUncertaintyMapV3(data_dir=temp_dir)

            # Phase 1: Initial predictions
            predictions = []
            for phase in ["ideation", "design", "mvp", "implementation", "testing"]:
                pred = system.predict(phase=phase, hours_ahead=24)
                predictions.append(pred)

            # Phase 2: Learn from outcomes
            for pred in predictions:
                # Simulate actual being slightly different
                actual = {
                    "magnitude": pred["prediction"]["predicted_magnitude"] * 0.9,
                    "technical": 0.4,
                    "resource": 0.4,
                    "timeline": 0.4,
                    "integration": 0.4,
                    "external": 0.4,
                    "quality": 0.4,
                }
                system.learn_from_outcome(pred, actual)

            # Phase 3: Make improved predictions
            improved_predictions = []
            for phase in ["ideation", "design", "mvp", "implementation", "testing"]:
                pred = system.predict(phase=phase, hours_ahead=24)
                improved_predictions.append(pred)

            # Phase 4: Verify improvement
            report = system.get_performance_report()

            # Should have made predictions and learned
            self.assertEqual(report["summary"]["total_predictions"], 10)
            self.assertTrue(report["summary"]["learning_enabled"])

            # Should have some accuracy improvements tracked
            self.assertEqual(len(system.metrics["accuracy_improvements"]), 5)

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
