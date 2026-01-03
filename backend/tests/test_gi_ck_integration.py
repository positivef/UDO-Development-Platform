#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration tests for GI Formula and C-K Theory services

Updated: 2025-12-13
- Fixed API mismatches with actual service implementations
- GIFormulaResult: insight_id -> id, stages is Dict, execution_time -> total_duration_ms
- CKTheoryResult: design_id -> id, execution_time -> total_duration_ms
- CKTheoryService: generate_alternatives -> generate_design, submit_feedback -> add_feedback
- Removed unsupported CKTheoryRequest fields (project_context)
- Use only allowed constraint keys
"""

from datetime import datetime  # noqa: F401

import pytest

from backend.app.models.ck_theory import CKTheoryRequest
from backend.app.models.gi_formula import GIFormulaRequest, StageType
from backend.app.services.ck_theory_service import CKTheoryService
from backend.app.services.gi_formula_service import GIFormulaService


class TestGIFormulaIntegration:
    """GI Formula service integration tests"""

    @pytest.fixture
    def gi_service(self):
        """Create GI Formula service instance"""
        return GIFormulaService()

    @pytest.mark.asyncio
    async def test_generate_insight_simple(self, gi_service):
        """Test basic insight generation"""
        request = GIFormulaRequest(
            problem="How can we reduce API latency by 50%?",
            context={"current_latency": "200ms", "target_latency": "100ms"},
        )

        result = await gi_service.generate_insight(request)

        assert result is not None
        assert result.id is not None  # Changed from insight_id
        assert result.problem == request.problem
        assert len(result.stages) == 5
        assert result.final_insight is not None
        assert result.bias_check is not None
        assert result.bias_check.confidence_score > 0
        assert result.total_duration_ms >= 0  # Changed from execution_time

    @pytest.mark.asyncio
    async def test_stage_progression(self, gi_service):
        """Test that stages execute in correct order"""
        request = GIFormulaRequest(
            problem="Improve code quality metrics",
            context={"current_score": 70, "target_score": 90},
        )

        result = await gi_service.generate_insight(request)

        # Verify stage order - stages is a Dict[str, StageResult]
        expected_stages = [
            StageType.OBSERVATION,
            StageType.CONNECTION,
            StageType.PATTERN,
            StageType.SYNTHESIS,
            StageType.BIAS_CHECK,
        ]

        # Access stages as dict values
        actual_stages = [stage.stage for stage in result.stages.values()]
        assert actual_stages == expected_stages

        # Verify each stage has content
        for stage in result.stages.values():
            assert stage.content is not None  # Changed from output
            assert len(stage.content) > 0

    @pytest.mark.asyncio
    async def test_caching_behavior(self, gi_service):
        """Test that caching improves performance on repeated requests"""
        request = GIFormulaRequest(
            problem="Optimize database queries",
            context={"current_qps": 100, "target_qps": 500},
        )

        # First request (no cache)
        result1 = await gi_service.generate_insight(request)
        time1 = result1.total_duration_ms  # Changed from execution_time

        # Second request (should hit cache)
        result2 = await gi_service.generate_insight(request)
        time2 = result2.total_duration_ms

        # Cached request should be faster (or same if very fast)
        assert time2 <= time1
        assert result1.id == result2.id  # Changed from insight_id


class TestCKTheoryIntegration:
    """C-K Theory service integration tests"""

    @pytest.fixture
    def ck_service(self):
        """Create C-K Theory service instance"""
        return CKTheoryService()

    @pytest.mark.asyncio
    async def test_generate_design_alternatives(self, ck_service):
        """Test basic design alternative generation"""
        request = CKTheoryRequest(
            challenge="Design authentication system for multi-tenant SaaS",
            constraints={"team_size": 3, "security_requirement": "high"},
            # Removed project_context - not a valid field
        )

        result = await ck_service.generate_design(request)  # Changed from generate_alternatives

        assert result is not None
        assert result.id is not None  # Changed from design_id
        assert result.challenge == request.challenge
        assert len(result.alternatives) == 3  # Must generate exactly 3 alternatives
        assert result.tradeoff_analysis is not None
        assert result.total_duration_ms >= 0  # Changed from execution_time

    @pytest.mark.asyncio
    async def test_alternative_uniqueness(self, ck_service):
        """Test that generated alternatives are distinct"""
        request = CKTheoryRequest(
            challenge="Implement caching strategy for high-traffic API",
            constraints={"budget": "medium", "complexity": "moderate"},
        )

        result = await ck_service.generate_design(request)  # Changed from generate_alternatives

        # Check that all alternatives have unique IDs and titles
        ids = [alt.id for alt in result.alternatives]
        titles = [alt.title for alt in result.alternatives]

        assert len(ids) == len(set(ids))  # All IDs unique
        assert len(titles) == len(set(titles))  # All titles unique

        # Verify RICE scores are calculated
        for alt in result.alternatives:
            assert alt.rice.reach >= 1 and alt.rice.reach <= 10
            assert alt.rice.impact >= 1 and alt.rice.impact <= 10
            assert alt.rice.confidence >= 1 and alt.rice.confidence <= 10
            assert alt.rice.effort >= 1 and alt.rice.effort <= 10
            assert alt.rice.score > 0

    @pytest.mark.asyncio
    async def test_tradeoff_analysis(self, ck_service):
        """Test that trade-off analysis is comprehensive"""
        request = CKTheoryRequest(
            challenge="Choose frontend framework for new project",
            constraints={
                "timeline": "3 months",
                "team_size": 5,
            },  # Fixed: removed team_experience
        )

        result = await ck_service.generate_design(request)  # Changed from generate_alternatives
        analysis = result.tradeoff_analysis

        assert analysis.summary is not None
        # recommendation is a string describing the recommended alternative
        assert analysis.recommendation is not None
        assert any(alt_id in analysis.recommendation for alt_id in ["A", "B", "C"])
        # comparison_matrix and decision_tree instead of key_tradeoffs/decision_factors
        assert analysis.comparison_matrix is not None
        assert analysis.decision_tree is not None
        assert len(analysis.decision_tree) >= 1

    @pytest.mark.asyncio
    async def test_feedback_integration(self, ck_service):
        """Test feedback submission and retrieval"""
        request = CKTheoryRequest(
            challenge="Design CI/CD pipeline for microservices",
            constraints={"complexity": "high"},  # Fixed: changed automation_level to complexity
        )

        result = await ck_service.generate_design(request)  # Changed from generate_alternatives

        # Submit feedback using add_feedback method
        from backend.app.models.ck_theory import DesignFeedback

        feedback = DesignFeedback(
            design_id=result.id,
            selected_alternative_id="A",
            rating=4,
            comments="Good balance between cost and features",
            outcome="success",  # Fixed: must be 'success', 'partial', or 'failure'
        )

        feedback_result = await ck_service.add_feedback(result.id, feedback)  # Changed from submit_feedback

        # add_feedback() returns True on success, not a feedback object
        assert feedback_result is True


class TestServiceIntegration:
    """Integration tests between GI Formula and C-K Theory"""

    @pytest.mark.asyncio
    async def test_gi_to_ck_workflow(self):
        """Test workflow: GI Formula generates insight -> C-K Theory generates alternatives"""
        gi_service = GIFormulaService()
        ck_service = CKTheoryService()

        # Step 1: Generate insight with GI Formula
        gi_request = GIFormulaRequest(
            problem="Need to improve team productivity by 30%",
            context={"current_velocity": 20, "target_velocity": 26},
        )

        gi_result = await gi_service.generate_insight(gi_request)
        assert gi_result.final_insight is not None

        # Step 2: Use insight as context for C-K Theory
        # Note: project_context is not a valid field, use constraints instead
        ck_request = CKTheoryRequest(
            challenge="Implement productivity improvement strategy",
            constraints={"budget": "medium", "timeline": "2 months"},
        )

        ck_result = await ck_service.generate_design(ck_request)  # Changed from generate_alternatives
        assert len(ck_result.alternatives) == 3
        assert ck_result.tradeoff_analysis is not None

    @pytest.mark.asyncio
    async def test_performance_targets(self):
        """Test that both services meet performance targets"""
        gi_service = GIFormulaService()
        ck_service = CKTheoryService()

        # GI Formula should complete in <30 seconds
        gi_request = GIFormulaRequest(problem="Optimize resource allocation", context={})

        gi_result = await gi_service.generate_insight(gi_request)
        gi_time_sec = gi_result.total_duration_ms / 1000  # Convert ms to seconds
        assert gi_time_sec < 30.0, f"GI Formula took {gi_time_sec}s (target: <30s)"

        # C-K Theory should complete in <45 seconds
        ck_request = CKTheoryRequest(challenge="Design scalable architecture", constraints={})

        ck_result = await ck_service.generate_design(ck_request)  # Changed from generate_alternatives
        ck_time_sec = ck_result.total_duration_ms / 1000  # Convert ms to seconds
        assert ck_time_sec < 45.0, f"C-K Theory took {ck_time_sec}s (target: <45s)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
