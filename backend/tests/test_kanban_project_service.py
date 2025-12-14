"""
Tests for Kanban Project Service - Multi-Project Management (P0 Critical Issue #3).

Verifies Q5 decision implementation:
- Exactly 1 primary project per task
- Maximum 3 related projects per task
- Atomic primary switching
- Constraint validation
"""

import pytest
from uuid import uuid4
from backend.app.services.kanban_project_service import KanbanProjectService
from backend.app.models.kanban_task_project import (
    MaxRelatedProjectsError,
    NoPrimaryProjectError,
    MultiplePrimaryProjectsError,
)


class TestPrimaryProjectManagement:
    """Test primary project operations"""

    @pytest.mark.asyncio
    async def test_set_primary_project(self):
        """Should set primary project for task"""
        service = KanbanProjectService()
        task_id = uuid4()
        project_id = uuid4()

        result = await service.set_primary_project(task_id, project_id)

        assert result.task_id == task_id
        assert result.project_id == project_id
        assert result.is_primary is True

    @pytest.mark.asyncio
    async def test_change_primary_project(self):
        """Should atomically switch primary project"""
        service = KanbanProjectService()
        task_id = uuid4()
        project1_id = uuid4()
        project2_id = uuid4()

        # Set first primary
        await service.set_primary_project(task_id, project1_id)

        # Change to second primary (atomic)
        await service.set_primary_project(task_id, project2_id)

        # Verify only one primary exists
        summary = await service.get_task_projects(task_id)
        assert summary.primary_project.project_id == project2_id

        # Verify old primary was removed
        validation = await service.validate_constraints(task_id)
        assert validation["valid"] is True

    @pytest.mark.asyncio
    async def test_exactly_one_primary_constraint(self):
        """Should enforce exactly 1 primary project"""
        service = KanbanProjectService()
        task_id = uuid4()
        project1_id = uuid4()
        project2_id = uuid4()

        # Set primary
        await service.set_primary_project(task_id, project1_id)

        # Try to manually add second primary (simulating constraint violation)
        # This should be prevented by set_primary_project logic
        await service.set_primary_project(task_id, project2_id)

        # Verify only one primary
        summary = await service.get_task_projects(task_id)
        assert summary.primary_project.project_id == project2_id
        assert len([p for p in summary.related_projects if p.is_primary]) == 0


class TestRelatedProjectManagement:
    """Test related project operations"""

    @pytest.mark.asyncio
    async def test_add_related_project(self):
        """Should add related project"""
        service = KanbanProjectService()
        task_id = uuid4()
        primary_id = uuid4()
        related_id = uuid4()

        # Must have primary first
        await service.set_primary_project(task_id, primary_id)

        # Add related
        result = await service.add_related_project(task_id, related_id)

        assert result.task_id == task_id
        assert result.project_id == related_id
        assert result.is_primary is False

    @pytest.mark.asyncio
    async def test_add_multiple_related_projects(self):
        """Should allow up to 3 related projects"""
        service = KanbanProjectService()
        task_id = uuid4()
        primary_id = uuid4()
        related_ids = [uuid4() for _ in range(3)]

        await service.set_primary_project(task_id, primary_id)

        # Add 3 related projects
        for related_id in related_ids:
            await service.add_related_project(task_id, related_id)

        # Verify all 3 added
        summary = await service.get_task_projects(task_id)
        assert len(summary.related_projects) == 3

    @pytest.mark.asyncio
    async def test_max_3_related_projects_constraint(self):
        """Should enforce max 3 related projects"""
        service = KanbanProjectService()
        task_id = uuid4()
        primary_id = uuid4()
        related_ids = [uuid4() for _ in range(4)]

        await service.set_primary_project(task_id, primary_id)

        # Add 3 related projects
        for i in range(3):
            await service.add_related_project(task_id, related_ids[i])

        # Try to add 4th - should fail
        with pytest.raises(MaxRelatedProjectsError):
            await service.add_related_project(task_id, related_ids[3])

    @pytest.mark.asyncio
    async def test_cannot_add_primary_as_related(self):
        """Should prevent adding primary project as related"""
        service = KanbanProjectService()
        task_id = uuid4()
        project_id = uuid4()

        await service.set_primary_project(task_id, project_id)

        # Try to add same project as related
        with pytest.raises(ValueError, match="already the primary project"):
            await service.add_related_project(task_id, project_id)

    @pytest.mark.asyncio
    async def test_cannot_add_duplicate_related(self):
        """Should prevent duplicate related projects"""
        service = KanbanProjectService()
        task_id = uuid4()
        primary_id = uuid4()
        related_id = uuid4()

        await service.set_primary_project(task_id, primary_id)
        await service.add_related_project(task_id, related_id)

        # Try to add same related project again
        with pytest.raises(ValueError, match="already a related project"):
            await service.add_related_project(task_id, related_id)

    @pytest.mark.asyncio
    async def test_remove_related_project(self):
        """Should remove related project"""
        service = KanbanProjectService()
        task_id = uuid4()
        primary_id = uuid4()
        related_id = uuid4()

        await service.set_primary_project(task_id, primary_id)
        await service.add_related_project(task_id, related_id)

        # Remove related
        removed = await service.remove_related_project(task_id, related_id)
        assert removed is True

        # Verify removed
        summary = await service.get_task_projects(task_id)
        assert len(summary.related_projects) == 0

    @pytest.mark.asyncio
    async def test_cannot_remove_primary_as_related(self):
        """Should prevent removing primary project via remove_related"""
        service = KanbanProjectService()
        task_id = uuid4()
        primary_id = uuid4()

        await service.set_primary_project(task_id, primary_id)

        # Try to remove primary via remove_related
        with pytest.raises(ValueError, match="Cannot remove primary project"):
            await service.remove_related_project(task_id, primary_id)


class TestConstraintValidation:
    """Test constraint validation"""

    @pytest.mark.asyncio
    async def test_validate_valid_configuration(self):
        """Should validate correct configuration"""
        service = KanbanProjectService()
        task_id = uuid4()
        primary_id = uuid4()
        related_ids = [uuid4() for _ in range(2)]

        await service.set_primary_project(task_id, primary_id)
        for related_id in related_ids:
            await service.add_related_project(task_id, related_id)

        # Validate
        result = await service.validate_constraints(task_id)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_no_primary(self):
        """Should detect missing primary project"""
        service = KanbanProjectService()
        task_id = uuid4()

        # No primary set
        result = await service.validate_constraints(task_id)

        assert result["valid"] is False
        assert any("must have exactly 1 primary" in error for error in result["errors"])

    @pytest.mark.asyncio
    async def test_get_task_projects_summary(self):
        """Should return complete project summary"""
        service = KanbanProjectService()
        task_id = uuid4()
        primary_id = uuid4()
        related_ids = [uuid4() for _ in range(2)]

        await service.set_primary_project(task_id, primary_id)
        for related_id in related_ids:
            await service.add_related_project(task_id, related_id)

        # Get summary
        summary = await service.get_task_projects(task_id)

        assert summary.task_id == task_id
        assert summary.primary_project.project_id == primary_id
        assert len(summary.related_projects) == 2
        assert summary.total_projects == 3


class TestAtomicOperations:
    """Test atomic operations and race conditions"""

    @pytest.mark.asyncio
    async def test_atomic_primary_switch_from_related(self):
        """Should atomically move related project to primary"""
        service = KanbanProjectService()
        task_id = uuid4()
        project1_id = uuid4()
        project2_id = uuid4()

        # Setup: project1 = primary, project2 = related
        await service.set_primary_project(task_id, project1_id)
        await service.add_related_project(task_id, project2_id)

        # Switch: make project2 primary (should remove from related first)
        await service.set_primary_project(task_id, project2_id)

        # Verify
        summary = await service.get_task_projects(task_id)
        assert summary.primary_project.project_id == project2_id
        assert project2_id not in [p.project_id for p in summary.related_projects]

        # Validation should pass
        validation = await service.validate_constraints(task_id)
        assert validation["valid"] is True


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_empty_task_projects(self):
        """Should handle task with no projects"""
        service = KanbanProjectService()
        task_id = uuid4()

        summary = await service.get_task_projects(task_id)

        assert summary.task_id == task_id
        assert summary.primary_project is None
        assert len(summary.related_projects) == 0
        assert summary.total_projects == 0

    @pytest.mark.asyncio
    async def test_remove_nonexistent_related(self):
        """Should handle removing non-existent related project"""
        service = KanbanProjectService()
        task_id = uuid4()
        primary_id = uuid4()
        nonexistent_id = uuid4()

        await service.set_primary_project(task_id, primary_id)

        # Try to remove non-existent related
        removed = await service.remove_related_project(task_id, nonexistent_id)
        assert removed is False  # Not found

    @pytest.mark.asyncio
    async def test_q5_full_workflow(self):
        """Test complete Q5 workflow: 1 Primary + 3 Related"""
        service = KanbanProjectService()
        task_id = uuid4()
        primary_id = uuid4()
        related_ids = [uuid4() for _ in range(3)]

        # 1. Set primary
        await service.set_primary_project(task_id, primary_id)

        # 2. Add 3 related projects
        for related_id in related_ids:
            await service.add_related_project(task_id, related_id)

        # 3. Verify configuration
        summary = await service.get_task_projects(task_id)
        assert summary.primary_project.project_id == primary_id
        assert len(summary.related_projects) == 3
        assert summary.total_projects == 4

        # 4. Validate constraints
        validation = await service.validate_constraints(task_id)
        assert validation["valid"] is True

        # 5. Cannot add 4th related
        with pytest.raises(MaxRelatedProjectsError):
            await service.add_related_project(task_id, uuid4())

        # 6. Change primary
        new_primary_id = uuid4()
        await service.set_primary_project(task_id, new_primary_id)

        # 7. Verify still valid
        validation = await service.validate_constraints(task_id)
        assert validation["valid"] is True


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
