import os
from pathlib import Path

import pytest

# Ensure src is on the path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in os.sys.path:
    os.sys.path.append(str(SRC_DIR))

import unified_development_orchestrator_v2 as udo_module
import uncertainty_map_v3 as umap_module
import three_ai_collaboration_bridge as bridge_module
from unified_development_orchestrator_v2 import ProjectContext, UnifiedDevelopmentOrchestratorV2
from uncertainty_map_v3 import UncertaintyMapV3, UncertaintyState
from three_ai_collaboration_bridge import ThreeAICollaborationBridge


def _prepare_storage(monkeypatch, tmp_path):
    storage_dir = tmp_path / "udo_storage"
    storage_dir.mkdir()
    monkeypatch.setenv("UDO_STORAGE_DIR", str(storage_dir))
    monkeypatch.setenv("UDO_HOME", str(storage_dir))
    udo_module.DEFAULT_STORAGE_DIR = storage_dir
    umap_module.DEFAULT_STORAGE_DIR = storage_dir
    bridge_module.DEFAULT_STORAGE_DIR = storage_dir
    bridge_module.GEMINI_USAGE_FILE = storage_dir / "gemini_usage.json"
    return storage_dir


def _build_project_context() -> ProjectContext:
    return ProjectContext(
        project_name="TestProject",
        goal="Validate confidence weighting",
        team_size=4,
        timeline_weeks=12,
        budget=50000,
        tech_stack=["python"],
        constraints=["demo"],
        success_metrics=["quality"],
        current_phase="design",
        files=[],
    )


def test_calculate_weighted_confidence_uses_config(monkeypatch, tmp_path):
    _prepare_storage(monkeypatch, tmp_path)
    orchestrator = UnifiedDevelopmentOrchestratorV2(_build_project_context())
    confidence = orchestrator.calculate_weighted_confidence(0.6, 0.5, "design")
    assert confidence == pytest.approx(0.7, rel=1e-3)


def test_analyze_context_identifies_high_uncertainty(monkeypatch, tmp_path):
    storage_dir = _prepare_storage(monkeypatch, tmp_path)
    umap = UncertaintyMapV3("unit-test")
    vector, state = umap.analyze_context(
        {
            "phase": "ideation",
            "files": [],
            "team_size": 3,
            "timeline_weeks": 6,
            "market_validation": 0.1,
        }
    )
    assert state == UncertaintyState.CHAOTIC
    assert vector.technical >= 0.9
    umap.save_state()
    assert (storage_dir / f"uncertainty_history_{umap.project_name}.json").exists()


def test_collaborate_returns_summary(monkeypatch, tmp_path):
    _prepare_storage(monkeypatch, tmp_path)
    bridge = ThreeAICollaborationBridge()
    result = bridge.collaborate("Implement pipeline", pattern="implementation", max_iterations=1)
    assert result["collaboration_pattern"] == "implementation"
    assert "status" in result
    assert isinstance(result["ai_responses"], list)
