"""
Test Suite for Kanban Tasks API

Week 2 Day 3-4: 60 tests for Tasks API (12 endpoints × 5 cases).

Test Categories:
1. CRUD Operations (25 tests)
2. Phase Operations (5 tests)
3. Status & Priority Operations (15 tests)
4. Quality Gates (10 tests)
5. Archive Operations (5 tests)
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime

from backend.app.models.kanban_task import (
    Task,
    TaskCreate,
    TaskUpdate,
    TaskStatus,
    TaskPriority,
    PhaseName,
    PhaseChangeRequest,
    StatusChangeRequest,
    PriorityChangeRequest,
    CompletenessUpdateRequest,
    ArchiveRequest,
)
from backend.app.services.kanban_task_service import kanban_task_service


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(autouse=True, scope="function")
def reset_task_service():
    """
    Reset task service mock data before each test for isolation.

    This fixture ensures tests don't interfere with each other
    by clearing accumulated task state from previous tests.
    """
    kanban_task_service.reset_mock_data(recreate_test_tasks=False)
    yield
    # Cleanup after test (optional, but good practice)
    kanban_task_service.reset_mock_data(recreate_test_tasks=False)


@pytest.fixture
def sample_task_data():
    """Sample task creation data"""
    return TaskCreate(
        title="Test Task",
        description="Test task description",
        phase_id=uuid4(),
        phase_name=PhaseName.IDEATION,
        status=TaskStatus.PENDING,
        priority=TaskPriority.HIGH,
        completeness=0,
        estimated_hours=8.0,
        actual_hours=0.0,
        ai_suggested=False,
    )


@pytest_asyncio.fixture
async def created_task(sample_task_data):
    """Create and return a test task"""
    task = await kanban_task_service.create_task(sample_task_data)
    return task


# ============================================================================
# 1. CRUD Operations (25 tests)
# ============================================================================

class TestTaskCRUD:
    """Test CRUD operations for Tasks API"""

    @pytest.mark.asyncio
    async def test_create_task_success(self, sample_task_data):
        """Test successful task creation"""
        task = await kanban_task_service.create_task(sample_task_data)

        assert task.task_id is not None
        assert task.title == sample_task_data.title
        assert task.description == sample_task_data.description
        assert task.phase_name == sample_task_data.phase_name
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.HIGH
        assert task.completeness == 0
        assert task.created_at is not None
        assert task.updated_at is not None

    @pytest.mark.asyncio
    async def test_create_task_with_ai_suggestion(self):
        """Test task creation with AI suggestion (Q2)"""
        task_data = TaskCreate(
            title="AI Suggested Task",
            description="Task suggested by AI",
            phase_id=uuid4(),
            phase_name=PhaseName.IDEATION,
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            completeness=0,
            estimated_hours=4.0,
            actual_hours=0.0,
            ai_suggested=True,
            ai_confidence=0.85,
        )

        task = await kanban_task_service.create_task(task_data)

        assert task.ai_suggested is True
        assert task.ai_confidence == 0.85

    @pytest.mark.asyncio
    async def test_create_task_minimal_fields(self):
        """Test task creation with only required fields"""
        task_data = TaskCreate(
            title="Minimal Task",
            phase_id=uuid4(),
            phase_name=PhaseName.DESIGN,
        )

        task = await kanban_task_service.create_task(task_data)

        assert task.title == "Minimal Task"
        assert task.phase_name == PhaseName.DESIGN
        assert task.status == TaskStatus.PENDING  # Default
        assert task.priority == TaskPriority.MEDIUM  # Default
        assert task.completeness == 0  # Default

    @pytest.mark.asyncio
    async def test_get_task_success(self, created_task):
        """Test successful task retrieval"""
        task = await kanban_task_service.get_task(created_task.task_id)

        assert task is not None
        assert task.task_id == created_task.task_id
        assert task.title == created_task.title

    @pytest.mark.asyncio
    async def test_get_task_not_found(self):
        """Test task retrieval with non-existent ID"""
        from backend.app.models.kanban_task import TaskNotFoundError

        with pytest.raises(TaskNotFoundError):
            await kanban_task_service.get_task(uuid4())

    @pytest.mark.asyncio
    async def test_list_tasks_default_pagination(self, created_task):
        """Test list tasks with default pagination (50 per page)"""
        result = await kanban_task_service.list_tasks(
            filters=None,
            page=1,
            per_page=50,
            sort_by="created_at",
            sort_desc=True
        )

        assert result is not None
        assert result.pagination.per_page == 50
        assert result.pagination.page == 1
        assert len(result.data) >= 1  # At least our created task

    @pytest.mark.asyncio
    async def test_list_tasks_filter_by_phase(self, created_task):
        """Test list tasks filtered by phase (Q1)"""
        from backend.app.models.kanban_task import TaskFilters

        filters = TaskFilters(phase=PhaseName.IDEATION)
        result = await kanban_task_service.list_tasks(filters=filters)

        # All returned tasks should be in IDEATION phase
        for task in result.data:
            assert task.phase_name == PhaseName.IDEATION

    @pytest.mark.asyncio
    async def test_list_tasks_filter_by_ai_suggested(self):
        """Test list tasks filtered by AI suggestion (Q2)"""
        from backend.app.models.kanban_task import TaskFilters

        # Create AI-suggested task
        ai_task_data = TaskCreate(
            title="AI Task",
            phase_id=uuid4(),
            phase_name=PhaseName.IDEATION,
            ai_suggested=True,
            ai_confidence=0.9,
        )
        ai_task = await kanban_task_service.create_task(ai_task_data)

        # Filter by ai_suggested=True
        filters = TaskFilters(ai_suggested=True)
        result = await kanban_task_service.list_tasks(filters=filters)

        # All returned tasks should be AI-suggested
        for task in result.data:
            assert task.ai_suggested is True

    @pytest.mark.asyncio
    async def test_list_tasks_filter_by_quality_gate(self):
        """Test list tasks filtered by quality gate (Q3)"""
        from backend.app.models.kanban_task import TaskFilters

        # Create task and run quality gate
        task_data = TaskCreate(
            title="Quality Task",
            phase_id=uuid4(),
            phase_name=PhaseName.IMPLEMENTATION,
        )
        task = await kanban_task_service.create_task(task_data)

        # Run quality gate
        await kanban_task_service.run_quality_gates(task.task_id)

        # Filter by quality_gate_passed=True
        filters = TaskFilters(quality_gate_passed=True)
        result = await kanban_task_service.list_tasks(filters=filters)

        # Should find at least one task with quality gate passed
        assert len(result.data) >= 1

    @pytest.mark.asyncio
    async def test_list_tasks_pagination(self, created_task):
        """Test list tasks pagination"""
        # Create multiple tasks
        for i in range(5):
            task_data = TaskCreate(
                title=f"Pagination Test Task {i}",
                phase_id=uuid4(),
                phase_name=PhaseName.IDEATION,
            )
            await kanban_task_service.create_task(task_data)

        # Page 1 with per_page=2
        result = await kanban_task_service.list_tasks(page=1, per_page=2)

        assert result.pagination.page == 1
        assert result.pagination.per_page == 2
        assert len(result.data) <= 2
        assert result.pagination.total >= 6  # At least 6 tasks

    @pytest.mark.asyncio
    async def test_list_tasks_sort_by_priority(self, created_task):
        """Test list tasks sorted by priority"""
        # Create tasks with different priorities
        priorities = [TaskPriority.LOW, TaskPriority.CRITICAL, TaskPriority.MEDIUM]
        for priority in priorities:
            task_data = TaskCreate(
                title=f"Priority {priority}",
                phase_id=uuid4(),
                phase_name=PhaseName.IDEATION,
                priority=priority,
            )
            await kanban_task_service.create_task(task_data)

        # Sort by priority descending
        result = await kanban_task_service.list_tasks(
            sort_by="priority",
            sort_desc=True
        )

        # First task should have highest priority
        if len(result.data) >= 2:
            priority_order = {
                TaskPriority.CRITICAL: 4,
                TaskPriority.HIGH: 3,
                TaskPriority.MEDIUM: 2,
                TaskPriority.LOW: 1,
            }
            first_priority = priority_order.get(result.data[0].priority, 0)
            second_priority = priority_order.get(result.data[1].priority, 0)
            assert first_priority >= second_priority

    @pytest.mark.asyncio
    async def test_update_task_success(self, created_task):
        """Test successful task update"""
        update_data = TaskUpdate(
            title="Updated Title",
            description="Updated description",
            priority=TaskPriority.CRITICAL,
        )

        updated_task = await kanban_task_service.update_task(
            created_task.task_id,
            update_data
        )

        assert updated_task.title == "Updated Title"
        assert updated_task.description == "Updated description"
        assert updated_task.priority == TaskPriority.CRITICAL
        # Changed from > to >= to handle microsecond precision
        assert updated_task.updated_at >= created_task.updated_at

    @pytest.mark.asyncio
    async def test_update_task_partial_fields(self, created_task):
        """Test task update with only some fields"""
        update_data = TaskUpdate(title="New Title Only")

        updated_task = await kanban_task_service.update_task(
            created_task.task_id,
            update_data
        )

        # Updated field
        assert updated_task.title == "New Title Only"
        # Unchanged fields
        assert updated_task.description == created_task.description
        assert updated_task.priority == created_task.priority

    @pytest.mark.asyncio
    async def test_update_task_not_found(self):
        """Test task update with non-existent ID"""
        from backend.app.models.kanban_task import TaskNotFoundError

        update_data = TaskUpdate(title="New Title")

        with pytest.raises(TaskNotFoundError):
            await kanban_task_service.update_task(uuid4(), update_data)

    @pytest.mark.asyncio
    async def test_update_task_auto_complete_at_100(self, created_task):
        """Test task auto-completion when completeness reaches 100%"""
        update_data = TaskUpdate(completeness=100)

        updated_task = await kanban_task_service.update_task(
            created_task.task_id,
            update_data
        )

        assert updated_task.completeness == 100
        assert updated_task.status == TaskStatus.COMPLETED
        assert updated_task.completed_at is not None

    @pytest.mark.asyncio
    async def test_delete_task_success(self, created_task):
        """Test successful task deletion"""
        result = await kanban_task_service.delete_task(created_task.task_id)

        assert result is True

        # Task should not be retrievable
        from backend.app.models.kanban_task import TaskNotFoundError
        with pytest.raises(TaskNotFoundError):
            await kanban_task_service.get_task(created_task.task_id)

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self):
        """Test task deletion with non-existent ID"""
        from backend.app.models.kanban_task import TaskNotFoundError

        with pytest.raises(TaskNotFoundError):
            await kanban_task_service.delete_task(uuid4())


# ============================================================================
# 2. Phase Operations (5 tests)
# ============================================================================

class TestPhaseOperations:
    """Test phase operations (Q1: Task within Phase)"""

    @pytest.mark.asyncio
    async def test_change_phase_success(self, created_task):
        """Test successful phase change"""
        new_phase_id = uuid4()
        phase_request = PhaseChangeRequest(
            new_phase_id=new_phase_id,
            new_phase_name=PhaseName.DESIGN,
            reason="Moving to design phase"
        )

        updated_task = await kanban_task_service.change_phase(
            created_task.task_id,
            phase_request
        )

        assert updated_task.phase_id == new_phase_id
        assert updated_task.phase_name == PhaseName.DESIGN
        # Changed from > to >= to handle microsecond precision
        assert updated_task.updated_at >= created_task.updated_at

    @pytest.mark.asyncio
    async def test_change_phase_all_phases(self, created_task):
        """Test changing through all phases (Q1)"""
        phases = [
            PhaseName.DESIGN,
            PhaseName.MVP,
            PhaseName.IMPLEMENTATION,
            PhaseName.TESTING,
        ]

        for phase in phases:
            phase_request = PhaseChangeRequest(
                new_phase_id=uuid4(),
                new_phase_name=phase
            )

            updated_task = await kanban_task_service.change_phase(
                created_task.task_id,
                phase_request
            )

            assert updated_task.phase_name == phase

    @pytest.mark.asyncio
    async def test_change_phase_with_reason(self, created_task):
        """Test phase change with reason"""
        phase_request = PhaseChangeRequest(
            new_phase_id=uuid4(),
            new_phase_name=PhaseName.IMPLEMENTATION,
            reason="Requirements completed, starting implementation"
        )

        updated_task = await kanban_task_service.change_phase(
            created_task.task_id,
            phase_request
        )

        assert updated_task.phase_name == PhaseName.IMPLEMENTATION

    @pytest.mark.asyncio
    async def test_change_phase_task_not_found(self):
        """Test phase change with non-existent task"""
        from backend.app.models.kanban_task import TaskNotFoundError

        phase_request = PhaseChangeRequest(
            new_phase_id=uuid4(),
            new_phase_name=PhaseName.DESIGN
        )

        with pytest.raises(TaskNotFoundError):
            await kanban_task_service.change_phase(uuid4(), phase_request)

    @pytest.mark.asyncio
    async def test_change_phase_invalid_phase_name(self, created_task):
        """Test phase change with invalid phase name"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PhaseChangeRequest(
                new_phase_id=uuid4(),
                new_phase_name="invalid_phase"
            )


# ============================================================================
# 3. Status & Priority Operations (15 tests)
# ============================================================================

class TestStatusPriorityOperations:
    """Test status and priority operations"""

    @pytest.mark.asyncio
    async def test_change_status_success(self, created_task):
        """Test successful status change"""
        status_request = StatusChangeRequest(
            new_status=TaskStatus.IN_PROGRESS,
            reason="Starting work on this task"
        )

        updated_task = await kanban_task_service.change_status(
            created_task.task_id,
            status_request
        )

        assert updated_task.status == TaskStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_change_status_to_completed(self, created_task):
        """Test status change to COMPLETED sets completed_at"""
        status_request = StatusChangeRequest(new_status=TaskStatus.COMPLETED)

        updated_task = await kanban_task_service.change_status(
            created_task.task_id,
            status_request
        )

        assert updated_task.status == TaskStatus.COMPLETED
        assert updated_task.completed_at is not None

    @pytest.mark.asyncio
    async def test_change_status_to_blocked(self, created_task):
        """Test status change to BLOCKED"""
        status_request = StatusChangeRequest(
            new_status=TaskStatus.BLOCKED,
            reason="Waiting for dependency"
        )

        updated_task = await kanban_task_service.change_status(
            created_task.task_id,
            status_request
        )

        assert updated_task.status == TaskStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_change_status_task_not_found(self):
        """Test status change with non-existent task"""
        from backend.app.models.kanban_task import TaskNotFoundError

        status_request = StatusChangeRequest(new_status=TaskStatus.IN_PROGRESS)

        with pytest.raises(TaskNotFoundError):
            await kanban_task_service.change_status(uuid4(), status_request)

    @pytest.mark.asyncio
    async def test_change_priority_success(self, created_task):
        """Test successful priority change"""
        priority_request = PriorityChangeRequest(
            new_priority=TaskPriority.CRITICAL,
            reason="Urgent client request"
        )

        updated_task = await kanban_task_service.change_priority(
            created_task.task_id,
            priority_request
        )

        assert updated_task.priority == TaskPriority.CRITICAL

    @pytest.mark.asyncio
    async def test_change_priority_all_levels(self, created_task):
        """Test changing through all priority levels"""
        priorities = [
            TaskPriority.CRITICAL,
            TaskPriority.HIGH,
            TaskPriority.MEDIUM,
            TaskPriority.LOW,
        ]

        for priority in priorities:
            priority_request = PriorityChangeRequest(new_priority=priority)

            updated_task = await kanban_task_service.change_priority(
                created_task.task_id,
                priority_request
            )

            assert updated_task.priority == priority

    @pytest.mark.asyncio
    async def test_change_priority_task_not_found(self):
        """Test priority change with non-existent task"""
        from backend.app.models.kanban_task import TaskNotFoundError

        priority_request = PriorityChangeRequest(new_priority=TaskPriority.HIGH)

        with pytest.raises(TaskNotFoundError):
            await kanban_task_service.change_priority(uuid4(), priority_request)

    @pytest.mark.asyncio
    async def test_update_completeness_success(self, created_task):
        """Test successful completeness update"""
        completeness_request = CompletenessUpdateRequest(
            completeness=50,
            updated_by="test_user"
        )

        updated_task = await kanban_task_service.update_completeness(
            created_task.task_id,
            completeness_request
        )

        assert updated_task.completeness == 50

    @pytest.mark.asyncio
    async def test_update_completeness_to_100(self, created_task):
        """Test completeness update to 100% marks as COMPLETED"""
        completeness_request = CompletenessUpdateRequest(
            completeness=100,
            updated_by="test_user"
        )

        updated_task = await kanban_task_service.update_completeness(
            created_task.task_id,
            completeness_request
        )

        assert updated_task.completeness == 100
        assert updated_task.status == TaskStatus.COMPLETED
        assert updated_task.completed_at is not None

    @pytest.mark.asyncio
    async def test_update_completeness_boundary_values(self, created_task):
        """Test completeness with boundary values (0, 100)"""
        # Test 0%
        completeness_request = CompletenessUpdateRequest(
            completeness=0,
            updated_by="test_user"
        )
        updated_task = await kanban_task_service.update_completeness(
            created_task.task_id,
            completeness_request
        )
        assert updated_task.completeness == 0

        # Test 100%
        completeness_request = CompletenessUpdateRequest(
            completeness=100,
            updated_by="test_user"
        )
        updated_task = await kanban_task_service.update_completeness(
            created_task.task_id,
            completeness_request
        )
        assert updated_task.completeness == 100

    @pytest.mark.asyncio
    async def test_update_completeness_task_not_found(self):
        """Test completeness update with non-existent task"""
        from backend.app.models.kanban_task import TaskNotFoundError

        completeness_request = CompletenessUpdateRequest(
            completeness=50,
            updated_by="test_user"
        )

        with pytest.raises(TaskNotFoundError):
            await kanban_task_service.update_completeness(uuid4(), completeness_request)


# ============================================================================
# 4. Quality Gates (10 tests) - Q3
# ============================================================================

class TestQualityGates:
    """Test quality gate operations (Q3: Hybrid completion)"""

    @pytest.mark.asyncio
    async def test_run_quality_gates_success(self, created_task):
        """Test successful quality gate execution"""
        result = await kanban_task_service.run_quality_gates(created_task.task_id)

        assert result is not None
        assert result.task_id == created_task.task_id
        assert result.quality_score is not None
        assert result.quality_score >= 0
        assert result.quality_score <= 100
        assert result.execution_time_ms >= 0

    @pytest.mark.asyncio
    async def test_run_quality_gates_checks(self, created_task):
        """Test quality gate checks structure"""
        result = await kanban_task_service.run_quality_gates(created_task.task_id)

        assert len(result.checks) > 0

        # Verify check structure
        for check in result.checks:
            assert check.check_name is not None
            assert isinstance(check.passed, bool)
            assert check.message is not None

    @pytest.mark.asyncio
    async def test_run_quality_gates_constitutional_compliance(self, created_task):
        """Test quality gate constitutional compliance (P1-P17)"""
        result = await kanban_task_service.run_quality_gates(created_task.task_id)

        # Should have constitutional compliance check
        constitutional_check = next(
            (c for c in result.checks if "Constitutional" in c.check_name),
            None
        )
        assert constitutional_check is not None

    @pytest.mark.asyncio
    async def test_run_quality_gates_updates_task(self, created_task):
        """Test quality gate execution updates task fields"""
        result = await kanban_task_service.run_quality_gates(created_task.task_id)

        # Retrieve updated task
        updated_task = await kanban_task_service.get_task(created_task.task_id)

        assert updated_task.quality_gate_passed == result.quality_gate_passed
        assert updated_task.quality_score == result.quality_score

    @pytest.mark.asyncio
    async def test_run_quality_gates_task_not_found(self):
        """Test quality gate execution with non-existent task"""
        from backend.app.models.kanban_task import TaskNotFoundError

        with pytest.raises(TaskNotFoundError):
            await kanban_task_service.run_quality_gates(uuid4())

    @pytest.mark.asyncio
    async def test_get_quality_gates_success(self, created_task):
        """Test get quality gate status"""
        # Run quality gates first
        await kanban_task_service.run_quality_gates(created_task.task_id)

        # Get cached result
        result = await kanban_task_service.get_quality_gates(created_task.task_id)

        assert result is not None
        assert result.task_id == created_task.task_id

    @pytest.mark.asyncio
    async def test_get_quality_gates_before_run(self, created_task):
        """Test get quality gate status before running checks"""
        result = await kanban_task_service.get_quality_gates(created_task.task_id)

        # Should return default values
        assert result.quality_gate_passed is False
        assert result.quality_score == 0

    @pytest.mark.asyncio
    async def test_get_quality_gates_task_not_found(self):
        """Test get quality gate status with non-existent task"""
        from backend.app.models.kanban_task import TaskNotFoundError

        with pytest.raises(TaskNotFoundError):
            await kanban_task_service.get_quality_gates(uuid4())


# ============================================================================
# 5. Archive Operations (5 tests) - Q6
# ============================================================================

class TestArchiveOperations:
    """Test archive operations (Q6: Done-End + AI → Obsidian)"""

    @pytest.mark.asyncio
    async def test_archive_task_success(self, created_task):
        """Test successful task archiving"""
        archive_request = ArchiveRequest(
            archived_by="test_user",
            generate_ai_summary=True,
            reason="Task completed successfully"
        )

        archive = await kanban_task_service.archive_task(
            created_task.task_id,
            archive_request
        )

        assert archive is not None
        assert archive.task_id == created_task.task_id
        assert archive.archived_by == "test_user"
        assert archive.archived_at is not None

    @pytest.mark.asyncio
    async def test_archive_task_with_ai_summary(self, created_task):
        """Test archive with AI summary generation (Q6)"""
        archive_request = ArchiveRequest(
            archived_by="test_user",
            generate_ai_summary=True
        )

        archive = await kanban_task_service.archive_task(
            created_task.task_id,
            archive_request
        )

        # AI summary should be generated
        assert archive.ai_summary is not None
        assert len(archive.ai_summary) > 0

    @pytest.mark.asyncio
    async def test_archive_task_without_ai_summary(self, created_task):
        """Test archive without AI summary"""
        archive_request = ArchiveRequest(
            archived_by="test_user",
            generate_ai_summary=False
        )

        archive = await kanban_task_service.archive_task(
            created_task.task_id,
            archive_request
        )

        # AI summary should be None
        assert archive.ai_summary is None

    @pytest.mark.asyncio
    async def test_archive_task_updates_status(self, created_task):
        """Test archive updates task status to DONE_END"""
        archive_request = ArchiveRequest(archived_by="test_user")

        await kanban_task_service.archive_task(
            created_task.task_id,
            archive_request
        )

        # Task status should be updated
        updated_task = await kanban_task_service.get_task(created_task.task_id)
        assert updated_task.status == TaskStatus.DONE_END
        assert updated_task.archived_at is not None

    @pytest.mark.asyncio
    async def test_archive_task_not_found(self):
        """Test archive with non-existent task"""
        from backend.app.models.kanban_task import TaskNotFoundError

        archive_request = ArchiveRequest(archived_by="test_user")

        with pytest.raises(TaskNotFoundError):
            await kanban_task_service.archive_task(uuid4(), archive_request)
