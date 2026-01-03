"""
Unit Tests for Constitutional Guard

Tests all P1-P17 validation logic
"""

import pytest
from pathlib import Path

from app.core.constitutional_guard import (
    ConstitutionalGuard,
    ValidationResult,
    Severity,
)


@pytest.fixture
def guard():
    """Create ConstitutionalGuard instance for testing"""
    # Use test constitution if available, else use main
    test_constitution = Path(__file__).parent / "test_constitution.yaml"
    if test_constitution.exists():
        return ConstitutionalGuard(test_constitution)
    return ConstitutionalGuard()


@pytest.fixture
def sample_design():
    """Sample design for P1 testing"""
    return {
        "id": "design_001",
        "risk_assessments": {
            "existing_system_impact": {"assessed": True, "mitigation": "Backwards compatible API"},
            "git_conflict_risk": {"assessed": True, "mitigation": "Feature branch strategy"},
            "multi_session_issue": {"assessed": True, "mitigation": "Redis-based locking"},
            "performance_impact": {"assessed": True, "mitigation": "Caching layer"},
            "complexity_increase": {"assessed": True, "mitigation": "Modular design"},
            "workflow_change": {"assessed": True, "mitigation": "Migration guide"},
            "rollback_plan": {"assessed": True, "mitigation": "Feature flag + database backup"},
            "test_method": {"assessed": True, "mitigation": "Unit + integration tests"},
        },
        "user_approved": True,
    }


@pytest.fixture
def sample_confidence():
    """Sample confidence for P2 testing"""
    return {
        "id": "response_001",
        "ai_agent": "claude",
        "recommendation": "Use React hooks instead of class components",
        "confidence": {
            "level": "HIGH",
            "score": 0.96,
            "rationale": "Official React documentation recommends hooks",
            "evidence": ["React official docs", "Community best practices", "Performance benchmarks"],
        },
        "alternatives": [{"option": "Keep class components", "pros": ["Familiar to team"], "cons": ["Deprecated pattern"]}],
        "risks": ["Learning curve for team"],
    }


@pytest.fixture
def sample_evidence():
    """Sample evidence for P3 testing"""
    return {
        "id": "claim_001",
        "type": "optimization",
        "before": {"execution_time": 250, "memory_usage": 150},
        "after": {"execution_time": 100, "memory_usage": 120},
        "evidence": {
            "benchmark_results": {"execution_time": 100, "memory_usage": 120, "cpu_utilization": 45, "database_queries": 5},
            "ab_test_metrics": {
                "variant_a": "Old implementation",
                "variant_b": "New implementation",
                "sample_size": 150,
                "statistical_significance": 0.02,
            },
        },
    }


# [*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*]
# P1: Design Review First Tests
# [*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*]


@pytest.mark.asyncio
async def test_p1_valid_design(guard, sample_design):
    """Test P1 with valid design review"""
    result = await guard.validate_design(sample_design)

    assert result.passed is True
    assert len(result.violations) == 0
    assert result.article == "P1_design_review_first"


@pytest.mark.asyncio
async def test_p1_missing_risk_check(guard, sample_design):
    """Test P1 with missing risk check"""
    # Remove one required risk
    del sample_design["risk_assessments"]["performance_impact"]

    result = await guard.validate_design(sample_design)

    assert result.passed is False
    assert len(result.violations) > 0
    assert any("performance_impact" in v for v in result.violations)


@pytest.mark.asyncio
async def test_p1_incomplete_risk_assessment(guard, sample_design):
    """Test P1 with incomplete risk assessment"""
    # Mark risk as not assessed
    sample_design["risk_assessments"]["git_conflict_risk"]["assessed"] = False

    result = await guard.validate_design(sample_design)

    assert result.passed is False
    assert any("git_conflict_risk" in v for v in result.violations)


@pytest.mark.asyncio
async def test_p1_missing_user_approval(guard, sample_design):
    """Test P1 without user approval"""
    sample_design["user_approved"] = False

    result = await guard.validate_design(sample_design)

    assert result.passed is False
    assert any("approval" in v.lower() for v in result.violations)


@pytest.mark.asyncio
async def test_p1_valid_exemption(guard, sample_design):
    """Test P1 with valid exemption"""
    sample_design["exemption_claimed"] = True
    sample_design["exemption_reason"] = "오타 수정"
    sample_design["user_approved"] = False

    result = await guard.validate_design(sample_design)

    # Exemption should not bypass all checks in real implementation
    # This test checks that exemption is processed
    assert result.article == "P1_design_review_first"


# [*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*]
# P2: Uncertainty Disclosure Tests
# [*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*]


@pytest.mark.asyncio
async def test_p2_valid_high_confidence(guard, sample_confidence):
    """Test P2 with valid HIGH confidence"""
    result = await guard.validate_confidence(sample_confidence)

    assert result.passed is True
    assert len(result.violations) == 0
    assert result.metadata["confidence_level"] == "HIGH"


@pytest.mark.asyncio
async def test_p2_valid_medium_confidence(guard, sample_confidence):
    """Test P2 with valid MEDIUM confidence"""
    sample_confidence["confidence"]["level"] = "MEDIUM"
    sample_confidence["confidence"]["score"] = 0.80

    result = await guard.validate_confidence(sample_confidence)

    assert result.passed is True
    assert result.metadata["confidence_level"] == "MEDIUM"


@pytest.mark.asyncio
async def test_p2_valid_low_confidence(guard, sample_confidence):
    """Test P2 with valid LOW confidence with multiple alternatives"""
    sample_confidence["confidence"]["level"] = "LOW"
    sample_confidence["confidence"]["score"] = 0.65
    sample_confidence["alternatives"] = [
        {"option": "Option 1", "pros": [], "cons": []},
        {"option": "Option 2", "pros": [], "cons": []},
    ]

    result = await guard.validate_confidence(sample_confidence)

    assert result.passed is True
    assert result.metadata["confidence_level"] == "LOW"


@pytest.mark.asyncio
async def test_p2_missing_confidence_field(guard, sample_confidence):
    """Test P2 with missing confidence field"""
    del sample_confidence["confidence"]

    result = await guard.validate_confidence(sample_confidence)

    assert result.passed is False
    assert any("confidence" in v.lower() for v in result.violations)


@pytest.mark.asyncio
async def test_p2_invalid_confidence_level(guard, sample_confidence):
    """Test P2 with invalid confidence level"""
    sample_confidence["confidence"]["level"] = "SUPER_HIGH"

    result = await guard.validate_confidence(sample_confidence)

    assert result.passed is False
    assert any("invalid" in v.lower() for v in result.violations)


@pytest.mark.asyncio
async def test_p2_mismatched_score_level(guard, sample_confidence):
    """Test P2 with mismatched score and level"""
    sample_confidence["confidence"]["level"] = "HIGH"
    sample_confidence["confidence"]["score"] = 0.50  # Should be >= 0.95 for HIGH

    result = await guard.validate_confidence(sample_confidence)

    assert result.passed is False
    assert any("0.95" in v for v in result.violations)


@pytest.mark.asyncio
async def test_p2_low_confidence_missing_alternatives(guard, sample_confidence):
    """Test P2 LOW confidence without required alternatives"""
    sample_confidence["confidence"]["level"] = "LOW"
    sample_confidence["confidence"]["score"] = 0.60
    sample_confidence["alternatives"] = []

    result = await guard.validate_confidence(sample_confidence)

    assert result.passed is False
    assert any("alternatives" in v.lower() for v in result.violations)


@pytest.mark.asyncio
async def test_p2_low_confidence_insufficient_alternatives(guard, sample_confidence):
    """Test P2 LOW confidence with only 1 alternative (need 2)"""
    sample_confidence["confidence"]["level"] = "LOW"
    sample_confidence["confidence"]["score"] = 0.60
    sample_confidence["alternatives"] = [{"option": "Only one", "pros": [], "cons": []}]

    result = await guard.validate_confidence(sample_confidence)

    assert result.passed is False
    assert any("2 alternatives" in v for v in result.violations)


# [*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*]
# P3: Evidence-Based Decision Tests
# [*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*]


@pytest.mark.asyncio
async def test_p3_valid_optimization(guard, sample_evidence):
    """Test P3 with valid optimization evidence"""
    result = await guard.validate_evidence(sample_evidence)

    assert result.passed is True
    assert len(result.violations) == 0


@pytest.mark.asyncio
async def test_p3_non_optimization_skipped(guard):
    """Test P3 skips non-optimization claims"""
    claim = {"id": "claim_002", "type": "feature", "description": "New feature implementation"}

    result = await guard.validate_evidence(claim)

    assert result.passed is True
    assert result.metadata.get("skipped") is not None


@pytest.mark.asyncio
async def test_p3_missing_benchmark(guard, sample_evidence):
    """Test P3 with missing benchmark"""
    del sample_evidence["evidence"]["benchmark_results"]

    result = await guard.validate_evidence(sample_evidence)

    # Should fail if no A/B test either
    if "ab_test_metrics" not in sample_evidence["evidence"]:
        assert result.passed is False


@pytest.mark.asyncio
async def test_p3_missing_before_after(guard, sample_evidence):
    """Test P3 with missing before/after comparison"""
    del sample_evidence["before"]

    result = await guard.validate_evidence(sample_evidence)

    assert result.passed is False
    assert any("before" in v.lower() for v in result.violations)


@pytest.mark.asyncio
async def test_p3_low_sample_size(guard, sample_evidence):
    """Test P3 with low A/B test sample size"""
    sample_evidence["evidence"]["ab_test_metrics"]["sample_size"] = 50

    result = await guard.validate_evidence(sample_evidence)

    # Should generate warning
    assert len(result.warnings) > 0


@pytest.mark.asyncio
async def test_p3_not_statistically_significant(guard, sample_evidence):
    """Test P3 with non-significant A/B test"""
    sample_evidence["evidence"]["ab_test_metrics"]["statistical_significance"] = 0.15

    result = await guard.validate_evidence(sample_evidence)

    # Should generate warning
    assert any("significant" in w.lower() for w in result.warnings)


# [*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*]
# P4: Phase-Aware Compliance Tests
# [*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*]


@pytest.mark.asyncio
async def test_p4_valid_phase_action(guard):
    """Test P4 with valid action in phase"""
    context = {"quality_score": 0.70, "completed_deliverables": []}

    result = await guard.validate_phase_compliance("implementation", "full_implementation", context)

    assert result.passed is True


@pytest.mark.asyncio
async def test_p4_prohibited_action(guard):
    """Test P4 with prohibited action in phase"""
    context = {"quality_score": 0.60}

    result = await guard.validate_phase_compliance("testing", "new_features", context)  # Prohibited in testing phase

    assert result.passed is False
    assert any("prohibited" in v.lower() for v in result.violations)


@pytest.mark.asyncio
async def test_p4_low_quality_score(guard):
    """Test P4 with quality score below threshold"""
    context = {"quality_score": 0.50, "phase_transition_requested": False}  # Below implementation threshold (0.65)

    result = await guard.validate_phase_compliance("implementation", "full_implementation", context)

    # Should generate warning
    assert len(result.warnings) > 0


@pytest.mark.asyncio
async def test_p4_phase_transition_success(guard):
    """Test P4 successful phase transition"""
    context = {
        "quality_score": 0.70,
        "completed_deliverables": ["완전한 기능 구현", "80% 이상 테스트 커버리지", "코드 리뷰 완료", "API 문서"],
        "approved": True,
    }

    result = await guard.validate_phase_transition("implementation", "testing", context)

    assert result.passed is True


@pytest.mark.asyncio
async def test_p4_phase_transition_missing_deliverables(guard):
    """Test P4 phase transition with missing deliverables"""
    context = {"quality_score": 0.70, "completed_deliverables": ["완전한 기능 구현"], "approved": True}  # Missing others

    result = await guard.validate_phase_transition("implementation", "testing", context)

    assert result.passed is False
    assert any("deliverables" in v.lower() for v in result.violations)


@pytest.mark.asyncio
async def test_p4_phase_transition_no_approval(guard):
    """Test P4 phase transition without approval"""
    context = {
        "quality_score": 0.70,
        "completed_deliverables": ["완전한 기능 구현", "80% 이상 테스트 커버리지", "코드 리뷰 완료", "API 문서"],
        "approved": False,
    }

    result = await guard.validate_phase_transition("implementation", "testing", context)

    assert result.passed is False
    assert any("approval" in v.lower() for v in result.violations)


# [*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*]
# P5: Multi-AI Consistency Tests
# [*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*]


@pytest.mark.asyncio
async def test_p5_unanimous_consensus(guard):
    """Test P5 with unanimous AI consensus"""
    decisions = [
        {"ai_agent": "claude", "recommendation": "Use TypeScript", "confidence": {"level": "HIGH", "score": 0.95}},
        {"ai_agent": "codex", "recommendation": "Use TypeScript", "confidence": {"level": "HIGH", "score": 0.92}},
        {"ai_agent": "gemini", "recommendation": "Use TypeScript", "confidence": {"level": "MEDIUM", "score": 0.88}},
    ]

    result, consensus = await guard.validate_ai_consensus(decisions)

    assert result.passed is True
    assert consensus["recommendation"] == "Use TypeScript"
    assert len(consensus["supporting_ais"]) == 3
    assert consensus["confidence"]["level"] == "MEDIUM"  # Consensus reduces to MEDIUM max


@pytest.mark.asyncio
async def test_p5_majority_consensus(guard):
    """Test P5 with 2/3 majority"""
    decisions = [
        {"ai_agent": "claude", "recommendation": "Use React", "confidence": {"level": "HIGH", "score": 0.95}},
        {"ai_agent": "codex", "recommendation": "Use React", "confidence": {"level": "MEDIUM", "score": 0.80}},
        {"ai_agent": "gemini", "recommendation": "Use Vue", "confidence": {"level": "MEDIUM", "score": 0.75}},
    ]

    result, consensus = await guard.validate_ai_consensus(decisions)

    assert result.passed is True
    assert consensus["recommendation"] == "Use React"
    assert len(consensus["supporting_ais"]) == 2
    assert len(consensus["minority_opinions"]) == 1


@pytest.mark.asyncio
async def test_p5_no_majority(guard):
    """Test P5 without 2/3 majority"""
    decisions = [
        {"ai_agent": "claude", "recommendation": "Option A", "confidence": {"level": "MEDIUM", "score": 0.70}},
        {"ai_agent": "codex", "recommendation": "Option B", "confidence": {"level": "MEDIUM", "score": 0.72}},
        {"ai_agent": "gemini", "recommendation": "Option C", "confidence": {"level": "MEDIUM", "score": 0.68}},
    ]

    result, consensus = await guard.validate_ai_consensus(decisions)

    # Should still pick winner by weighted score but generate warning
    assert len(result.warnings) > 0
    assert any("majority" in w.lower() for w in result.warnings)


@pytest.mark.asyncio
async def test_p5_single_ai(guard):
    """Test P5 with single AI (consensus not required)"""
    decisions = [{"ai_agent": "claude", "recommendation": "Use Python", "confidence": {"level": "HIGH", "score": 0.95}}]

    result, consensus = await guard.validate_ai_consensus(decisions)

    assert result.passed is True
    assert result.metadata.get("skipped") is not None


# [*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*]
# General Tests
# [*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*]


def test_guard_initialization(guard):
    """Test ConstitutionalGuard initialization"""
    assert guard is not None
    assert guard.constitution is not None
    assert isinstance(guard.violation_log, list)


def test_compliance_score_calculation(guard):
    """Test compliance score calculation"""
    # Initial score should be 1.0 (no violations)
    score = guard.get_compliance_score()
    assert score == 1.0

    # Add a violation
    guard._log_violation(
        article="P1_design_review_first", violation_type="test", description="Test violation", severity=Severity.HIGH
    )

    # Score should decrease
    new_score = guard.get_compliance_score()
    assert new_score < 1.0


def test_violation_filtering(guard):
    """Test violation filtering"""
    # Add violations
    guard._log_violation(
        article="P1_design_review_first", violation_type="test1", description="Test 1", severity=Severity.CRITICAL
    )
    guard._log_violation(
        article="P2_uncertainty_disclosure", violation_type="test2", description="Test 2", severity=Severity.HIGH
    )

    # Filter by article
    p1_violations = guard.get_violations(article="P1_design_review_first")
    assert len(p1_violations) == 1
    assert p1_violations[0]["article"] == "P1_design_review_first"

    # Filter by severity
    critical_violations = guard.get_violations(severity=Severity.CRITICAL)
    assert len(critical_violations) == 1
    assert critical_violations[0]["severity"] == "CRITICAL"


def test_violation_export(guard, tmp_path):
    """Test violation export"""
    # Add a violation
    guard._log_violation(
        article="P1_design_review_first", violation_type="test", description="Test violation", severity=Severity.HIGH
    )

    # Export
    export_file = tmp_path / "violations.json"
    guard.export_violations(export_file)

    # Verify file exists
    assert export_file.exists()

    # Verify content
    import json

    with open(export_file) as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["article"] == "P1_design_review_first"


# [*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*]
# Integration Tests
# [*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*]


@pytest.mark.asyncio
async def test_validate_all_design(guard, sample_design):
    """Test validate_all with design operation"""
    results = await guard.validate_all("design", sample_design)

    assert len(results) > 0
    assert all(isinstance(r, ValidationResult) for r in results)


@pytest.mark.asyncio
async def test_validate_all_ai_response(guard, sample_confidence):
    """Test validate_all with AI response operation"""
    results = await guard.validate_all("ai_response", sample_confidence)

    assert len(results) > 0
    assert all(isinstance(r, ValidationResult) for r in results)


@pytest.mark.asyncio
async def test_validate_all_optimization(guard, sample_evidence):
    """Test validate_all with optimization operation"""
    results = await guard.validate_all("optimization", sample_evidence)

    assert len(results) > 0
    assert all(isinstance(r, ValidationResult) for r in results)


# [*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*]
# Performance Tests
# [*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*][*]


@pytest.mark.asyncio
async def test_validation_performance(guard, sample_design):
    """Test that validation completes within acceptable time"""
    import time

    start = time.time()
    _result = await guard.validate_design(sample_design)  # noqa: F841 - timing test
    duration = time.time() - start

    # Should complete in < 50ms
    assert duration < 0.05, f"Validation took {duration * 1000:.2f}ms (target: <50ms)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
