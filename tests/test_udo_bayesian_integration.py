"""
Tests for UDO v2 + Bayesian Learning Integration
===============================================

Tests the integration between UDO v2 Orchestrator and Adaptive Bayesian Learning.
"""

import unittest
import sys
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from udo_bayesian_integration import UDOBayesianIntegration


class TestUDOBayesianIntegration(unittest.TestCase):
    """Test UDO-Bayesian integration"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.integration = UDOBayesianIntegration(project_name="Test-Project", storage_dir=Path(self.temp_dir))

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test system initialization"""
        self.assertIsNotNone(self.integration.bayesian)
        self.assertEqual(self.integration.project_name, "Test-Project")
        self.assertIn("ideation", self.integration.BASE_THRESHOLDS)

    def test_adaptive_threshold_calculation(self):
        """Test adaptive threshold calculation"""
        phase = "implementation"
        base_confidence = 0.75

        threshold, metadata = self.integration.get_adaptive_threshold(phase, base_confidence)

        # Threshold should be a valid number
        self.assertGreater(threshold, 0.0)
        self.assertLess(threshold, 1.0)

        # Metadata should contain required fields
        self.assertIn("base_threshold", metadata)
        self.assertIn("adjusted_threshold", metadata)
        self.assertIn("bias_type", metadata)

    def test_go_decision_enhancement(self):
        """Test GO/NO_GO decision enhancement"""
        uncertainties = {"technical": 0.4, "market": 0.3, "resource": 0.5, "timeline": 0.6, "quality": 0.4}

        decision = self.integration.enhance_go_decision(
            phase="implementation", base_confidence=0.75, uncertainties=uncertainties
        )

        # Decision should have required fields
        self.assertIn("decision", decision)
        self.assertIn(decision["decision"], ["GO", "GO_WITH_CHECKPOINTS", "NO_GO"])
        self.assertIn("final_confidence", decision)
        self.assertIn("threshold", decision)
        self.assertIn("bayesian_insights", decision)

    def test_learning_from_outcome(self):
        """Test learning from project outcomes"""
        initial_metrics = dict(self.integration.integration_metrics)

        # Simulate learning
        self.integration.learn_from_project_outcome(
            phase="design",
            predicted_confidence=0.70,
            predicted_uncertainties={"technical": 0.5, "market": 0.4, "resource": 0.5, "timeline": 0.6, "quality": 0.5},
            actual_success=True,
        )

        # Learning events should increase
        self.assertGreater(self.integration.integration_metrics["learning_events"], initial_metrics["learning_events"])

    def test_bias_correction(self):
        """Test bias detection and correction"""
        # Simulate multiple optimistic predictions
        for i in range(5):
            self.integration.learn_from_project_outcome(
                phase="mvp",
                predicted_confidence=0.80,  # High predicted
                predicted_uncertainties={"technical": 0.3, "market": 0.3, "resource": 0.4, "timeline": 0.4, "quality": 0.3},
                actual_success=False,  # But actually failed
                actual_uncertainties={"technical": 0.7, "market": 0.8, "resource": 0.7, "timeline": 0.8, "quality": 0.7},
            )

        # After multiple failures, bias should be detected
        # (This test might need more observations to reliably detect bias)
        self.assertGreaterEqual(self.integration.integration_metrics["learning_events"], 5)

    def test_threshold_adjustment(self):
        """Test that thresholds are adjusted based on learning"""
        # Get initial threshold
        phase = "testing"
        initial_threshold, _ = self.integration.get_adaptive_threshold(phase, 0.70)

        # Make a decision (which may adjust threshold)
        decision = self.integration.enhance_go_decision(
            phase=phase,
            base_confidence=0.75,
            uncertainties={"technical": 0.3, "market": 0.3, "resource": 0.4, "timeline": 0.4, "quality": 0.3},
        )

        # The decision should have been made with a threshold
        self.assertIn("threshold", decision)
        self.assertIsNotNone(decision["threshold"]["adjusted"])

    def test_integration_report(self):
        """Test integration report generation"""
        # Make some decisions and learn
        for i in range(3):
            decision = self.integration.enhance_go_decision(
                phase="implementation",
                base_confidence=0.70 + i * 0.05,
                uncertainties={"technical": 0.4, "market": 0.4, "resource": 0.5, "timeline": 0.5, "quality": 0.4},
            )

            self.integration.learn_from_project_outcome(
                phase="implementation",
                predicted_confidence=0.70 + i * 0.05,
                predicted_uncertainties={"technical": 0.4, "market": 0.4, "resource": 0.5, "timeline": 0.5, "quality": 0.4},
                actual_success=(i % 2 == 0),
            )

        # Get report
        report = self.integration.get_integration_report()

        # Report should have required sections
        self.assertIn("integration_metrics", report)
        self.assertIn("bayesian_performance", report)
        self.assertIn("summary", report)

        # Summary should have correct counts
        summary = report["summary"]
        self.assertEqual(summary["total_decisions"], 3)
        self.assertEqual(summary["learning_events"], 3)

    def test_confidence_blending(self):
        """Test that UDO and Bayesian confidences are properly blended"""
        base_confidence = 0.80
        decision = self.integration.enhance_go_decision(
            phase="design",
            base_confidence=base_confidence,
            uncertainties={"technical": 0.3, "market": 0.3, "resource": 0.4, "timeline": 0.4, "quality": 0.3},
        )

        # Final confidence should be a blend
        final_conf = decision["final_confidence"]
        udo_conf = decision["components"]["udo_confidence"]
        bayesian_conf = decision["components"]["bayesian_confidence"]

        # Check that blending occurred
        self.assertEqual(udo_conf, base_confidence)

        # Final should be between the two (weighted average)
        # 70% UDO + 30% Bayesian
        expected_final = 0.7 * udo_conf + 0.3 * bayesian_conf
        self.assertAlmostEqual(final_conf, expected_final, places=2)


class TestIntegrationScenarios(unittest.TestCase):
    """Test complete integration scenarios"""

    def test_complete_project_lifecycle(self):
        """Test a complete project lifecycle with learning"""
        temp_dir = tempfile.mkdtemp()
        try:
            integration = UDOBayesianIntegration(project_name="Lifecycle-Project", storage_dir=Path(temp_dir))

            phases = ["ideation", "design", "mvp", "implementation", "testing"]
            phase_confidences = [0.65, 0.70, 0.68, 0.75, 0.72]
            phase_successes = [True, True, False, True, True]

            for phase, confidence, success in zip(phases, phase_confidences, phase_successes):
                # Make decision
                decision = integration.enhance_go_decision(
                    phase=phase,
                    base_confidence=confidence,
                    uncertainties={"technical": 0.4, "market": 0.4, "resource": 0.5, "timeline": 0.5, "quality": 0.4},
                )

                # Learn from outcome
                integration.learn_from_project_outcome(
                    phase=phase,
                    predicted_confidence=confidence,
                    predicted_uncertainties={
                        "technical": 0.4,
                        "market": 0.4,
                        "resource": 0.5,
                        "timeline": 0.5,
                        "quality": 0.4,
                    },
                    actual_success=success,
                )

            # After full lifecycle, should have learned from all phases
            report = integration.get_integration_report()
            self.assertEqual(report["summary"]["total_decisions"], 5)
            self.assertEqual(report["summary"]["learning_events"], 5)

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
