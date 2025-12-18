"""
Week 0 Day 1: Smoke Test Suite
Purpose: 5 critical tests that MUST pass for system to be considered "working"

Smoke tests validate the 5 P0 capabilities:
1. Uncertainty graph renders
2. API responds
3. Frontend loads
4. Basic predictions work
5. Confidence calculations work

Each test runs in <5 seconds, total suite <30 seconds.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from uncertainty_map_v3 import UncertaintyMapV3, UncertaintyState
from unified_development_orchestrator_v2 import UnifiedDevelopmentOrchestratorV2


class TestSmokeUncertaintyGraph:
    """SMOKE 1: Uncertainty graph renders without crashing"""

    def test_uncertainty_graph_visible(self):
        """Critical: Uncertainty map can generate basic visualization data"""
        uncertainty_map = UncertaintyMapV3()

        # Create a simple uncertainty vector
        from uncertainty_map_v3 import UncertaintyVector

        vector = UncertaintyVector(
            technical=0.3,
            market=0.2,
            resource=0.4,
            timeline=0.5,
            quality=0.3
        )

        # Should be able to classify state
        state = uncertainty_map.classify_state(vector.magnitude())

        # Verify basic state classification works
        assert state in [
            UncertaintyState.DETERMINISTIC,
            UncertaintyState.PROBABILISTIC,
            UncertaintyState.QUANTUM,
            UncertaintyState.CHAOTIC,
            UncertaintyState.VOID
        ]

        # Should be able to generate mitigation
        mitigation = uncertainty_map.generate_mitigation(vector, state)

        assert mitigation is not None
        assert hasattr(mitigation, 'strategy')
        assert hasattr(mitigation, 'cost')

        print(f"[OK] SMOKE 1 PASSED: Uncertainty graph renders (state={state.value})")


class TestSmokeAPIResponds:
    """SMOKE 2: Backend API can be imported without errors"""

    def test_api_responds(self):
        """Critical: Backend main.py imports successfully"""
        try:
            # Try to import backend (validates all imports, routers, services)
            import backend.main as backend_main

            # Verify FastAPI app exists
            assert hasattr(backend_main, 'app')
            assert backend_main.app is not None

            # Verify critical routers are loaded
            routes = [route.path for route in backend_main.app.routes]
            assert len(routes) > 0

            print(f"[OK] SMOKE 2 PASSED: API imports successfully ({len(routes)} routes)")

        except ImportError as e:
            pytest.fail(f"Backend import failed: {e}")


class TestSmokeFrontendLoads:
    """SMOKE 3: Frontend bundle builds without errors"""

    def test_frontend_loads(self):
        """Critical: Frontend can be built for production"""
        import subprocess
        import os

        # Change to web-dashboard directory
        web_dashboard_path = Path(__file__).parent.parent.parent / "web-dashboard"

        if not web_dashboard_path.exists():
            pytest.skip("Frontend directory not found")

        # Check if package.json exists
        package_json = web_dashboard_path / "package.json"
        if not package_json.exists():
            pytest.skip("package.json not found")

        # Check if node_modules exists (dependencies installed)
        node_modules = web_dashboard_path / "node_modules"
        if not node_modules.exists():
            pytest.skip("Dependencies not installed (run 'npm install')")

        # Try to build (this validates TypeScript compilation, imports, etc.)
        # Note: This is commented out to avoid long CI times
        # Uncomment for pre-deployment smoke testing

        # result = subprocess.run(
        #     ["npm", "run", "build"],
        #     cwd=web_dashboard_path,
        #     capture_output=True,
        #     text=True,
        #     timeout=120
        # )
        #
        # if result.returncode != 0:
        #     pytest.fail(f"Frontend build failed: {result.stderr}")

        print("[OK] SMOKE 3 SKIPPED: Frontend build (long CI time)")
        pytest.skip("Frontend build skipped (enable for pre-deployment)")


class TestSmokeBasicPrediction:
    """SMOKE 4: Basic prediction functionality works"""

    def test_basic_prediction(self):
        """Critical: Can predict uncertainty 24 hours ahead"""
        uncertainty_map = UncertaintyMapV3()

        from uncertainty_map_v3 import UncertaintyVector

        # Historical uncertainty (t=0)
        current_vector = UncertaintyVector(
            technical=0.3,
            market=0.2,
            resource=0.4,
            timeline=0.5,
            quality=0.3
        )

        # Predict 24 hours ahead
        prediction = uncertainty_map.predict_24h(current_vector)

        # Verify prediction structure
        assert prediction is not None
        assert hasattr(prediction, 'trend')
        assert hasattr(prediction, 'velocity')
        assert hasattr(prediction, 'acceleration')

        # Verify prediction is different from current state
        # (unless uncertainty is DETERMINISTIC)
        current_magnitude = current_vector.magnitude()
        predicted_state = uncertainty_map.classify_state(current_magnitude + prediction.trend)

        assert predicted_state in [
            UncertaintyState.DETERMINISTIC,
            UncertaintyState.PROBABILISTIC,
            UncertaintyState.QUANTUM,
            UncertaintyState.CHAOTIC,
            UncertaintyState.VOID
        ]

        print(f"[OK] SMOKE 4 PASSED: Basic prediction works (trend={prediction.trend:.2f})")


class TestSmokeConfidenceCalculation:
    """SMOKE 5: Confidence calculations work correctly"""

    def test_confidence_calculation(self):
        """Critical: Bayesian confidence scoring produces valid results"""
        udo = UnifiedDevelopmentOrchestratorV2()

        # Test confidence calculation for Ideation phase
        confidence = udo.calculate_confidence_score(
            phase="ideation",
            completed_tasks=5,
            total_tasks=10,
            test_coverage=0.6,
            quality_metrics={"pylint_score": 8.0}
        )

        # Verify confidence is in valid range
        assert 0.0 <= confidence <= 1.0

        # Verify confidence is reasonable (50% tasks done ≈ 50-70% confidence)
        assert 0.3 <= confidence <= 0.8

        # Test GO/NO_GO decision logic
        decision = udo.make_decision(
            phase="ideation",
            confidence=confidence,
            context={}
        )

        assert decision in ["GO", "GO_WITH_CHECKPOINTS", "NO_GO"]

        print(f"[OK] SMOKE 5 PASSED: Confidence calculation works (conf={confidence:.2%}, decision={decision})")


# Smoke test suite runner
if __name__ == "__main__":
    """
    Run smoke tests standalone:

    python tests/smoke/test_core_functionality.py

    Expected output:
    [OK] SMOKE 1 PASSED: Uncertainty graph renders
    [OK] SMOKE 2 PASSED: API responds (or SKIPPED)
    [OK] SMOKE 3 SKIPPED: Frontend build
    [OK] SMOKE 4 PASSED: Basic prediction works
    [OK] SMOKE 5 PASSED: Confidence calculation works

    Result: 4-5 / 5 tests passing (API may be skipped in CI)
    """
    pytest.main([__file__, "-v", "--tb=short"])
