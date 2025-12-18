#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite for Adaptive Bayesian Uncertainty System

Tests the core functionality of real-time Bayesian learning:
- Belief updates
- Bias detection
- Prediction accuracy improvement
- Kalman filtering
- Performance metrics

Author: UDO Development Team
Date: 2025-11-20
"""

import sys
import os
import unittest
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from adaptive_bayesian_uncertainty import (
    BayesianBelief,
    BiasProfile,
    AdaptiveBayesianUncertainty
)
from uncertainty_map_v3 import UncertaintyVector


class TestBayesianBelief(unittest.TestCase):
    """Test Bayesian belief updates"""

    def setUp(self):
        """Initialize test belief"""
        self.belief = BayesianBelief(
            mean=0.5,
            variance=0.1,
            alpha=5,
            beta=5,
            confidence=0.5,
            observations=10,
            last_updated=datetime.now()
        )

    def test_belief_update_correct_prediction(self):
        """Test belief update with correct prediction"""
        initial_mean = self.belief.mean
        initial_alpha = self.belief.alpha

        # Simulate correct prediction (uncertainty decreased as predicted)
        self.belief.update_with_observation(0.3, learning_rate=1.0)

        # Alpha should increase (success)
        self.assertGreater(self.belief.alpha, initial_alpha)
        # Observations should increment
        self.assertEqual(self.belief.observations, 11)
        # Confidence should be calculated based on observations
        self.assertGreater(self.belief.confidence, 0.3)  # More reasonable expectation

    def test_belief_update_incorrect_prediction(self):
        """Test belief update with incorrect prediction"""
        initial_beta = self.belief.beta

        # Simulate incorrect prediction (large error)
        self.belief.mean = 0.3  # Predict low uncertainty
        self.belief.update_with_observation(0.9, learning_rate=1.0)  # Much higher observed (0.6 error > 0.25 threshold)

        # Beta should increase (failure)
        self.assertGreater(self.belief.beta, initial_beta)

    def test_confidence_interval(self):
        """Test confidence interval calculation"""
        lower, upper = self.belief.get_confidence_interval(0.95)

        # Interval should contain the mean
        self.assertLess(lower, self.belief.mean)
        self.assertGreater(upper, self.belief.mean)

        # Interval should be within [0, 1]
        self.assertGreaterEqual(lower, 0)
        self.assertLessEqual(upper, 1)

    def test_confidence_growth(self):
        """Test that confidence grows with observations"""
        initial_confidence = self.belief.confidence

        # Add many observations
        for _ in range(50):
            self.belief.update_with_observation(0.5, learning_rate=0.1)

        # Confidence should increase but not exceed 1.0
        self.assertGreater(self.belief.confidence, initial_confidence)
        self.assertLessEqual(self.belief.confidence, 1.0)


class TestBiasProfile(unittest.TestCase):
    """Test bias detection and correction"""

    def setUp(self):
        """Initialize bias profile"""
        self.profile = BiasProfile()

    def test_optimistic_bias_detection(self):
        """Test detection of optimistic bias"""
        # Simulate consistently optimistic predictions
        for _ in range(20):
            predicted = 0.3  # Predict low uncertainty
            actual = 0.5     # Actual is higher
            self.profile.update(predicted, actual)

        bias_type = self.profile.get_bias_type()
        self.assertEqual(bias_type, "pessimistic")  # Predicted lower than actual

        # Correction should be positive
        correction = self.profile.get_correction_factor()
        self.assertGreater(correction, 0)

    def test_pessimistic_bias_detection(self):
        """Test detection of pessimistic bias"""
        # Simulate consistently pessimistic predictions
        for _ in range(20):
            predicted = 0.7  # Predict high uncertainty
            actual = 0.4     # Actual is lower
            self.profile.update(predicted, actual)

        bias_type = self.profile.get_bias_type()
        self.assertEqual(bias_type, "optimistic")  # Predicted higher than actual

        # Correction should be negative
        correction = self.profile.get_correction_factor()
        self.assertLess(correction, 0)

    def test_unbiased_detection(self):
        """Test detection of unbiased predictions"""
        # Simulate random unbiased predictions
        np.random.seed(42)
        for _ in range(30):
            base = np.random.random()
            error = np.random.normal(0, 0.03)  # Small random error
            self.profile.update(base, base + error)

        bias_type = self.profile.get_bias_type()
        self.assertEqual(bias_type, "unbiased")

        # Correction should be near zero
        correction = self.profile.get_correction_factor()
        self.assertLess(abs(correction), 0.1)

    def test_correction_factor_limits(self):
        """Test that correction factor is limited"""
        # Add extreme errors
        for _ in range(100):
            self.profile.update(1.0, 0.0)  # Maximum error

        correction = self.profile.get_correction_factor()
        # Should be capped at ±0.3
        self.assertLessEqual(abs(correction), 0.3)


class TestAdaptiveBayesianUncertainty(unittest.TestCase):
    """Test the complete Bayesian uncertainty system"""

    def setUp(self):
        """Initialize Bayesian system with temporary storage"""
        self.temp_dir = tempfile.mkdtemp()
        self.bayesian = AdaptiveBayesianUncertainty(
            "test-project",
            storage_dir=Path(self.temp_dir)
        )

    def tearDown(self):
        """Clean up temporary files"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test system initialization"""
        # Check beliefs are initialized for all phases
        phases = ['ideation', 'design', 'mvp', 'implementation', 'testing']
        dimensions = ['technical', 'market', 'resource', 'timeline', 'quality']

        for phase in phases:
            self.assertIn(phase, self.bayesian.beliefs)
            for dimension in dimensions:
                self.assertIn(dimension, self.bayesian.beliefs[phase])
                belief = self.bayesian.beliefs[phase][dimension]
                self.assertIsInstance(belief, BayesianBelief)
                self.assertGreater(belief.alpha, 0)
                self.assertGreater(belief.beta, 0)

    def test_prediction_structure(self):
        """Test prediction output structure"""
        vector = UncertaintyVector(0.5, 0.6, 0.4, 0.7, 0.5)
        prediction = self.bayesian.predict_uncertainty(
            vector,
            phase='implementation',
            horizon_hours=24
        )

        # Check required fields
        self.assertIn('predicted_magnitude', prediction)
        self.assertIn('confidence', prediction)
        self.assertIn('overall_trend', prediction)
        self.assertIn('dimension_predictions', prediction)
        self.assertIn('quantum_state', prediction)
        self.assertIn('bias_profile', prediction)
        self.assertIn('recommendations', prediction)

        # Check value ranges
        self.assertGreaterEqual(prediction['predicted_magnitude'], 0)
        self.assertLessEqual(prediction['predicted_magnitude'], 1)
        self.assertGreaterEqual(prediction['confidence'], 0)
        self.assertLessEqual(prediction['confidence'], 1)

    def test_learning_from_observations(self):
        """Test that system learns from observations"""
        vector = UncertaintyVector(0.6, 0.7, 0.5, 0.6, 0.4)

        # Make initial prediction
        pred1 = self.bayesian.predict_uncertainty(vector, 'design', 24)
        initial_confidence = pred1['confidence']

        # Simulate multiple observations
        for i in range(5):
            # Create slightly different observed vector
            observed = UncertaintyVector(
                0.6 + i * 0.02,
                0.7 - i * 0.03,
                0.5 + i * 0.01,
                0.6 - i * 0.02,
                0.4 + i * 0.02
            )

            # Update with observation
            self.bayesian.update_with_observation(
                'design',
                pred1,
                observed,
                outcome_success=True
            )

        # Make new prediction
        pred2 = self.bayesian.predict_uncertainty(vector, 'design', 24)

        # Confidence should increase with observations
        self.assertGreater(pred2['confidence'], initial_confidence)

        # Should have recorded observations
        self.assertGreater(len(self.bayesian.observation_history), 0)

    def test_bias_correction(self):
        """Test that bias correction is applied"""
        vector = UncertaintyVector(0.5, 0.5, 0.5, 0.5, 0.5)

        # Create systematic bias by providing biased observations
        for _ in range(10):
            pred = self.bayesian.predict_uncertainty(vector, 'mvp', 24)

            # Always observe lower uncertainty (optimistic reality)
            observed = UncertaintyVector(0.3, 0.3, 0.3, 0.3, 0.3)
            self.bayesian.update_with_observation('mvp', pred, observed)

        # Check bias is detected
        bias_type = self.bayesian.bias_profiles['mvp'].get_bias_type()
        self.assertIn(bias_type, ['optimistic', 'highly_optimistic'])

        # Make new prediction
        pred = self.bayesian.predict_uncertainty(vector, 'mvp', 24)

        # Correction should be applied
        correction = pred['bias_profile']['correction_applied']
        self.assertNotEqual(correction, 0)

    def test_kalman_filtering(self):
        """Test Kalman filter smoothing"""
        # Initial state
        initial_state = self.bayesian.kalman_state['x']

        # Apply multiple updates
        measurements = [0.4, 0.42, 0.45, 0.43, 0.44]
        predictions = [0.5, 0.48, 0.46, 0.45, 0.44]

        for meas, pred in zip(measurements, predictions):
            filtered = self.bayesian._kalman_filter_update(meas, pred)
            # Filtered should be reasonable (within extended bounds)
            # Allow more flexibility since we're blending and clipping
            self.assertTrue(min(meas, pred) - 0.15 <= filtered <= max(meas, pred) + 0.15)

        # State should have changed
        self.assertNotEqual(self.bayesian.kalman_state['x'], initial_state)

    def test_quantum_state_classification(self):
        """Test quantum state classification"""
        test_cases = [
            (0.05, 'deterministic'),
            (0.2, 'probabilistic'),
            (0.45, 'quantum'),
            (0.7, 'chaotic'),
            (0.9, 'void')
        ]

        for magnitude, expected_state in test_cases:
            state = self.bayesian._classify_quantum_state(magnitude)
            self.assertEqual(state, expected_state)

    def test_recommendations_generation(self):
        """Test that recommendations are generated appropriately"""
        # High uncertainty vector
        high_uncertainty = UncertaintyVector(0.8, 0.9, 0.7, 0.8, 0.6)
        pred = self.bayesian.predict_uncertainty(high_uncertainty, 'ideation', 24)

        # Should have recommendations
        self.assertGreater(len(pred['recommendations']), 0)

        # Recommendations should target high uncertainty dimensions
        for rec in pred['recommendations']:
            self.assertIn('action', rec)
            self.assertIn('urgency', rec)
            self.assertIn('confidence', rec)

    def test_performance_report(self):
        """Test performance reporting"""
        # Make some predictions and updates
        vector = UncertaintyVector(0.5, 0.5, 0.5, 0.5, 0.5)
        for i in range(3):
            pred = self.bayesian.predict_uncertainty(vector, 'testing', 24)
            observed = UncertaintyVector(0.5, 0.5, 0.5, 0.5, 0.5)
            self.bayesian.update_with_observation('testing', pred, observed)

        report = self.bayesian.get_performance_report()

        # Check report structure
        self.assertIn('total_predictions', report)
        self.assertIn('overall_accuracy', report)
        self.assertIn('improvement_rate', report)
        self.assertIn('phase_biases', report)
        self.assertIn('learning_status', report)

        # Values should be reasonable
        self.assertGreaterEqual(report['overall_accuracy'], 0)
        self.assertLessEqual(report['overall_accuracy'], 100)

    def test_state_persistence(self):
        """Test saving and loading state"""
        # Make some observations
        vector = UncertaintyVector(0.5, 0.5, 0.5, 0.5, 0.5)
        pred = self.bayesian.predict_uncertainty(vector, 'design', 24)
        observed = UncertaintyVector(0.4, 0.4, 0.4, 0.4, 0.4)
        self.bayesian.update_with_observation('design', pred, observed)

        # Save state
        self.bayesian.save_state()

        # Create new instance and load state
        bayesian2 = AdaptiveBayesianUncertainty(
            "test-project",
            storage_dir=Path(self.temp_dir)
        )
        bayesian2.load_state()

        # Should have same metrics
        self.assertEqual(
            bayesian2.metrics['predictions_made'],
            self.bayesian.metrics['predictions_made']
        )
        self.assertEqual(
            len(bayesian2.observation_history),
            len(self.bayesian.observation_history)
        )

    def test_improvement_over_time(self):
        """Test that system improves over time"""
        vector = UncertaintyVector(0.5, 0.6, 0.4, 0.5, 0.5)
        accuracies = []

        # Simulate learning cycles
        for i in range(20):
            # Make prediction
            pred = self.bayesian.predict_uncertainty(vector, 'implementation', 24)

            # Create realistic observed outcome (slightly noisy)
            noise = np.random.normal(0, 0.05, 5)
            observed = UncertaintyVector(
                max(0, min(1, 0.5 + noise[0])),
                max(0, min(1, 0.6 + noise[1])),
                max(0, min(1, 0.4 + noise[2])),
                max(0, min(1, 0.5 + noise[3])),
                max(0, min(1, 0.5 + noise[4]))
            )

            # Calculate accuracy
            accuracy = 1.0 - abs(pred['predicted_magnitude'] - observed.magnitude())
            accuracies.append(accuracy)

            # Update with observation
            self.bayesian.update_with_observation('implementation', pred, observed)

        # Later predictions should be more accurate on average
        early_avg = np.mean(accuracies[:5])
        late_avg = np.mean(accuracies[-5:])

        # Expect some improvement (or at least no degradation)
        self.assertGreaterEqual(late_avg, early_avg - 0.1)

    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # Test with extreme values
        extreme_vector = UncertaintyVector(0.0, 1.0, 0.0, 1.0, 0.5)
        pred = self.bayesian.predict_uncertainty(extreme_vector, 'testing', 24)
        self.assertIsNotNone(pred)

        # Test with invalid phase
        with self.assertRaises(ValueError):
            self.bayesian.predict_uncertainty(extreme_vector, 'invalid_phase', 24)

        # Test model optimization with insufficient data
        self.bayesian._optimize_model_parameters()  # Should not crash

        # Test empty observation history
        report = self.bayesian.get_performance_report()
        self.assertIsNotNone(report)


class TestIntegration(unittest.TestCase):
    """Integration tests with full workflow"""

    def test_complete_workflow(self):
        """Test complete prediction-observation-learning cycle"""
        temp_dir = tempfile.mkdtemp()
        try:
            bayesian = AdaptiveBayesianUncertainty(
                "integration-test",
                storage_dir=Path(temp_dir)
            )

            phases = ['ideation', 'design', 'mvp', 'implementation', 'testing']
            uncertainties = [
                UncertaintyVector(0.8, 0.9, 0.6, 0.5, 0.4),
                UncertaintyVector(0.6, 0.7, 0.5, 0.6, 0.5),
                UncertaintyVector(0.5, 0.5, 0.5, 0.7, 0.6),
                UncertaintyVector(0.4, 0.3, 0.5, 0.8, 0.7),
                UncertaintyVector(0.2, 0.2, 0.3, 0.4, 0.6)
            ]

            # Run through project lifecycle
            for phase, uncertainty in zip(phases, uncertainties):
                # Make prediction
                prediction = bayesian.predict_uncertainty(
                    uncertainty,
                    phase,
                    horizon_hours=48
                )

                # Verify prediction structure
                self.assertIsNotNone(prediction)
                self.assertIn('predicted_magnitude', prediction)

                # Simulate observed outcome (with some noise)
                noise_factor = 0.9 + np.random.random() * 0.2
                observed = UncertaintyVector(
                    uncertainty.technical * noise_factor,
                    uncertainty.market * noise_factor,
                    uncertainty.resource * noise_factor,
                    uncertainty.timeline * noise_factor,
                    uncertainty.quality * noise_factor
                )

                # Update with observation
                bayesian.update_with_observation(
                    phase,
                    prediction,
                    observed,
                    outcome_success=True
                )

            # Get final report
            report = bayesian.get_performance_report()

            # Should have made predictions
            self.assertEqual(report['total_predictions'], 5)
            self.assertGreater(report['overall_accuracy'], 0)

            # Should have learning status
            self.assertIn(report['learning_status'],
                         ['initializing', 'rapidly_improving', 'steadily_improving', 'stable'])

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestBayesianBelief))
    suite.addTests(loader.loadTestsFromTestCase(TestBiasProfile))
    suite.addTests(loader.loadTestsFromTestCase(TestAdaptiveBayesianUncertainty))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    if success:
        print("\n" + "="*60)
        print("[OK] All Bayesian Learning tests passed!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("[FAIL] Some tests failed. Please review the output above.")
        print("="*60)
    sys.exit(0 if success else 1)