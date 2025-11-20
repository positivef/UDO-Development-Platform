#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration tests for GI Formula and C-K Theory services
"""

import pytest
from datetime import datetime
from backend.app.models.gi_formula import GIFormulaRequest, StageType
from backend.app.models.ck_theory import CKTheoryRequest
from backend.app.services.gi_formula_service import GIFormulaService
from backend.app.services.ck_theory_service import CKTheoryService


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
            context={"current_latency": "200ms", "target_latency": "100ms"}
        )

        result = await gi_service.generate_insight(request)

        assert result is not None
        assert result.insight_id is not None
        assert result.problem == request.problem
        assert len(result.stages) == 5
        assert result.final_insight is not None
        assert result.bias_check is not None
        assert result.bias_check.confidence_score > 0
        assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_stage_progression(self, gi_service):
        """Test that stages execute in correct order"""
        request = GIFormulaRequest(
            problem="Improve code quality metrics",
            context={"current_score": 70, "target_score": 90}
        )

        result = await gi_service.generate_insight(request)

        # Verify stage order
        expected_stages = [
            StageType.OBSERVATION,
            StageType.CONNECTION,
            StageType.PATTERN,
            StageType.SYNTHESIS,
            StageType.BIAS_CHECK
        ]

        actual_stages = [stage.stage_type for stage in result.stages]
        assert actual_stages == expected_stages

        # Verify each stage has output
        for stage in result.stages:
            assert stage.output is not None
            assert len(stage.output) > 0

    @pytest.mark.asyncio
    async def test_caching_behavior(self, gi_service):
        """Test that caching improves performance on repeated requests"""
        request = GIFormulaRequest(
            problem="Optimize database queries",
            context={"current_qps": 100, "target_qps": 500}
        )

        # First request (no cache)
        result1 = await gi_service.generate_insight(request)
        time1 = result1.execution_time

        # Second request (should hit cache)
        result2 = await gi_service.generate_insight(request)
        time2 = result2.execution_time

        # Cached request should be faster (or same if very fast)
        assert time2 <= time1
        assert result1.insight_id == result2.insight_id


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
            project_context={"platform": "web", "tech_stack": "FastAPI+React"}
        )

        result = await ck_service.generate_alternatives(request)

        assert result is not None
        assert result.design_id is not None
        assert result.challenge == request.challenge
        assert len(result.alternatives) == 3  # Must generate exactly 3 alternatives
        assert result.tradeoff_analysis is not None
        assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_alternative_uniqueness(self, ck_service):
        """Test that generated alternatives are distinct"""
        request = CKTheoryRequest(
            challenge="Implement caching strategy for high-traffic API",
            constraints={"budget": "medium", "complexity": "moderate"}
        )

        result = await ck_service.generate_alternatives(request)

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
            constraints={"timeline": "3 months", "team_experience": "React"}
        )

        result = await ck_service.generate_alternatives(request)
        analysis = result.tradeoff_analysis

        assert analysis.summary is not None
        assert analysis.recommended_alternative_id in ['A', 'B', 'C']
        assert len(analysis.key_tradeoffs) >= 1
        assert len(analysis.decision_factors) >= 1

    @pytest.mark.asyncio
    async def test_feedback_integration(self, ck_service):
        """Test feedback submission and retrieval"""
        request = CKTheoryRequest(
            challenge="Design CI/CD pipeline",
            constraints={"automation_level": "high"}
        )

        result = await ck_service.generate_alternatives(request)

        # Submit feedback
        feedback_request = {
            "selected_alternative_id": "A",
            "rating": 4,
            "comments": "Good balance between cost and features",
            "outcome": "implemented"
        }

        feedback_result = await ck_service.submit_feedback(
            result.design_id,
            feedback_request
        )

        assert feedback_result["success"] is True
        assert feedback_result["design_id"] == result.design_id


class TestServiceIntegration:
    """Integration tests between GI Formula and C-K Theory"""

    @pytest.mark.asyncio
    async def test_gi_to_ck_workflow(self):
        """Test workflow: GI Formula generates insight → C-K Theory generates alternatives"""
        gi_service = GIFormulaService()
        ck_service = CKTheoryService()

        # Step 1: Generate insight with GI Formula
        gi_request = GIFormulaRequest(
            problem="Need to improve team productivity by 30%",
            context={"current_velocity": 20, "target_velocity": 26}
        )

        gi_result = await gi_service.generate_insight(gi_request)
        assert gi_result.final_insight is not None

        # Step 2: Use insight as context for C-K Theory
        ck_request = CKTheoryRequest(
            challenge="Implement productivity improvement strategy",
            constraints={"budget": "medium", "timeline": "2 months"},
            project_context={
                "gi_insight": gi_result.final_insight,
                "confidence": gi_result.bias_check.confidence_score
            }
        )

        ck_result = await ck_service.generate_alternatives(ck_request)
        assert len(ck_result.alternatives) == 3
        assert ck_result.tradeoff_analysis is not None

    @pytest.mark.asyncio
    async def test_performance_targets(self):
        """Test that both services meet performance targets"""
        gi_service = GIFormulaService()
        ck_service = CKTheoryService()

        # GI Formula should complete in <30 seconds
        gi_request = GIFormulaRequest(
            problem="Optimize resource allocation",
            context={}
        )

        gi_result = await gi_service.generate_insight(gi_request)
        assert gi_result.execution_time < 30.0, f"GI Formula took {gi_result.execution_time}s (target: <30s)"

        # C-K Theory should complete in <45 seconds
        ck_request = CKTheoryRequest(
            challenge="Design scalable architecture",
            constraints={}
        )

        ck_result = await ck_service.generate_alternatives(ck_request)
        assert ck_result.execution_time < 45.0, f"C-K Theory took {ck_result.execution_time}s (target: <45s)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
