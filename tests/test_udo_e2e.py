#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Integration Tests for UDO v2
Tests the complete workflow from project initialization to AI collaboration
"""

import os
from pathlib import Path
import pytest

# Ensure src is on the path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in os.sys.path:
    os.sys.path.append(str(SRC_DIR))

import unified_development_orchestrator_v2 as udo_module  # noqa: E402
import uncertainty_map_v3 as umap_module  # noqa: E402
import three_ai_collaboration_bridge as bridge_module  # noqa: E402
from unified_development_orchestrator_v2 import ProjectContext, UnifiedDevelopmentOrchestratorV2  # noqa: E402
from uncertainty_map_v3 import UncertaintyMapV3, UncertaintyVector, UncertaintyState  # noqa: E402


def _prepare_storage(monkeypatch, tmp_path):
    """Prepare isolated storage directory for testing"""
    storage_dir = tmp_path / "udo_storage"
    storage_dir.mkdir()
    monkeypatch.setenv("UDO_STORAGE_DIR", str(storage_dir))
    monkeypatch.setenv("UDO_HOME", str(storage_dir))
    udo_module.DEFAULT_STORAGE_DIR = storage_dir
    umap_module.DEFAULT_STORAGE_DIR = storage_dir
    bridge_module.DEFAULT_STORAGE_DIR = storage_dir
    bridge_module.GEMINI_USAGE_FILE = storage_dir / "gemini_usage.json"
    return storage_dir


def _build_test_project_context(phase="design") -> ProjectContext:
    """Build a test project context for E2E testing"""
    return ProjectContext(
        project_name="E2E_Test_Project",
        goal="Test complete UDO v2 workflow with phase-aware decision making",
        team_size=3,
        timeline_weeks=8,
        budget=30000,
        tech_stack=["python", "fastapi", "react"],
        constraints=["time-critical", "quality-focused"],
        success_metrics=["test_coverage > 80%", "performance < 200ms"],
        current_phase=phase,
        files=["src/main.py", "src/api.py", "tests/test_main.py"],
    )


class TestUDOv2EndToEnd:
    """End-to-End tests for UDO v2 complete workflow"""

    def test_e2e_ideation_phase_workflow(self, monkeypatch, tmp_path):
        """Test complete workflow in ideation phase"""
        _prepare_storage(monkeypatch, tmp_path)
        context = _build_test_project_context(phase="ideation")

        # Initialize UDO v2
        orchestrator = UnifiedDevelopmentOrchestratorV2(context)

        # Execute complete development cycle
        result = orchestrator.start_development_cycle("Design a new AI-powered feature for automated code review")

        # Verify execution plan structure
        assert "system" in result
        assert "confidence" in result
        assert "decision" in result
        assert result["decision"] in ["GO", "GO_WITH_MONITORING", "PROTOTYPE_FIRST", "NEED_MORE_INFO"]

        # Verify phase-aware confidence
        assert 0.0 <= result["confidence"] <= 1.0

        print("[OK] Ideation phase E2E test passed")
        print(f"   Decision: {result['decision']}")
        print(f"   Confidence: {result['confidence']:.2%}")
        print(f"   System: {result['system']}")

    def test_e2e_design_phase_workflow(self, monkeypatch, tmp_path):
        """Test complete workflow in design phase"""
        _prepare_storage(monkeypatch, tmp_path)
        context = _build_test_project_context(phase="design")

        orchestrator = UnifiedDevelopmentOrchestratorV2(context)

        # Design phase request
        result = orchestrator.start_development_cycle("Create system architecture for microservices backend")

        assert "system" in result
        assert "decision" in result
        assert result["decision"] in ["GO", "GO_WITH_MONITORING", "PROTOTYPE_FIRST", "NEED_MORE_INFO"]
        assert "confidence" in result

        print("[OK] Design phase E2E test passed")
        print(f"   Decision: {result['decision']}")
        print(f"   Confidence: {result['confidence']:.2%}")

    def test_e2e_mvp_phase_workflow(self, monkeypatch, tmp_path):
        """Test MVP phase with time-critical constraints"""
        _prepare_storage(monkeypatch, tmp_path)
        context = _build_test_project_context(phase="mvp")

        orchestrator = UnifiedDevelopmentOrchestratorV2(context)

        result = orchestrator.start_development_cycle("Build minimal viable product with core authentication and API")

        assert "system" in result
        assert "decision" in result
        assert "confidence" in result

        # MVP should have moderate confidence requirements
        assert 0.0 <= result["confidence"] <= 1.0

        print("[OK] MVP phase E2E test passed")
        print(f"   Confidence: {result['confidence']:.2%}")

    def test_e2e_implementation_phase_workflow(self, monkeypatch, tmp_path):
        """Test implementation phase with quality metrics"""
        _prepare_storage(monkeypatch, tmp_path)
        context = _build_test_project_context(phase="implementation")

        orchestrator = UnifiedDevelopmentOrchestratorV2(context)

        result = orchestrator.start_development_cycle("Implement user authentication with JWT and refresh tokens")

        assert "system" in result
        assert "decision" in result
        assert "confidence" in result

        # Implementation phase should have higher quality requirements
        print("[OK] Implementation phase E2E test passed")
        print(f"   Decision: {result['decision']}")

    def test_e2e_testing_phase_workflow(self, monkeypatch, tmp_path):
        """Test testing phase with coverage requirements"""
        _prepare_storage(monkeypatch, tmp_path)
        context = _build_test_project_context(phase="testing")

        # Add more test files for testing phase
        context.files = [
            "src/main.py",
            "src/api.py",
            "tests/test_main.py",
            "tests/test_api.py",
            "tests/test_integration.py",
        ]

        orchestrator = UnifiedDevelopmentOrchestratorV2(context)

        result = orchestrator.start_development_cycle("Write comprehensive E2E tests with 80% coverage")

        assert "system" in result
        assert "decision" in result
        assert "confidence" in result

        print("[OK] Testing phase E2E test passed")
        print(f"   Decision: {result['decision']}")

    def test_e2e_uncertainty_prediction_workflow(self, monkeypatch, tmp_path):
        """Test uncertainty prediction and evolution workflow"""
        _prepare_storage(monkeypatch, tmp_path)
        context = _build_test_project_context(phase="mvp")

        # Initialize uncertainty map
        umap = UncertaintyMapV3("E2E_Test_Project")

        # Step 1: Analyze context and get uncertainty vector
        vector, state = umap.analyze_context(
            {
                "phase": "mvp",
                "files": context.files,
                "team_size": context.team_size,
                "timeline_weeks": context.timeline_weeks,
                "market_validation": 0.4,  # Low market validation
            }
        )

        assert isinstance(vector, UncertaintyVector)
        assert isinstance(state, UncertaintyState)

        # Step 2: Add observation for learning
        umap.add_observation(phase="mvp", vector=vector, outcome=True)  # Successful outcome

        # Step 3: Classify uncertainty state
        magnitude = vector.magnitude()
        classified_state = umap.classify_state(magnitude)

        assert classified_state in [
            UncertaintyState.DETERMINISTIC,
            UncertaintyState.PROBABILISTIC,
            UncertaintyState.QUANTUM,
            UncertaintyState.CHAOTIC,
            UncertaintyState.VOID,
        ]

        # Step 4: Predict evolution
        prediction = umap.predict_evolution(vector=vector, phase="mvp", hours=24)

        assert prediction is not None
        assert hasattr(prediction, "trend")

        print("[OK] Uncertainty prediction E2E test passed")
        print(f"   State: {classified_state}")
        print(f"   Magnitude: {magnitude:.2f}")
        print(f"   Trend: {prediction.trend}")

    def test_e2e_config_based_phase_weights(self, monkeypatch, tmp_path):
        """Test that phase-specific weights from config.yaml are applied"""
        _prepare_storage(monkeypatch, tmp_path)

        # Test ideation phase
        ideation_context = _build_test_project_context(phase="ideation")
        ideation_udo = UnifiedDevelopmentOrchestratorV2(ideation_context)

        # Test design phase
        design_context = _build_test_project_context(phase="design")
        design_udo = UnifiedDevelopmentOrchestratorV2(design_context)

        # Calculate confidence with same inputs
        system_score = 0.6
        uncertainty_score = 0.5

        ideation_confidence = ideation_udo.calculate_weighted_confidence(system_score, uncertainty_score, "ideation")

        design_confidence = design_udo.calculate_weighted_confidence(system_score, uncertainty_score, "design")

        # Different phases should produce different confidence scores
        assert ideation_confidence != design_confidence, "Phase-specific weights should produce different confidence scores"

        print("[OK] Config-based phase weights test passed")
        print(f"   Ideation confidence: {ideation_confidence:.2%}")
        print(f"   Design confidence: {design_confidence:.2%}")

    def test_e2e_full_lifecycle(self, monkeypatch, tmp_path):
        """Test complete project lifecycle through all phases"""
        _prepare_storage(monkeypatch, tmp_path)

        phases = ["ideation", "design", "mvp", "implementation", "testing"]
        results = []

        for phase in phases:
            context = _build_test_project_context(phase=phase)
            orchestrator = UnifiedDevelopmentOrchestratorV2(context)

            result = orchestrator.start_development_cycle(
                f"Execute {phase} phase tasks for AI-powered project management system"
            )

            results.append({"phase": phase, "decision": result["decision"], "confidence": result.get("confidence", 0.0)})

            assert "system" in result
            assert "decision" in result
            assert result["decision"] in ["GO", "GO_WITH_MONITORING", "PROTOTYPE_FIRST", "NEED_MORE_INFO"]

        print("[OK] Full lifecycle E2E test passed")
        print(f"   Tested {len(phases)} phases successfully")
        for result in results:
            print(f"   - {result['phase']}: {result['decision']} (confidence: {result['confidence']:.2%})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
