"""
Kanban Task Service - Core Task Management

Implements Week 2 Day 3-4: Tasks CRUD operations with mock data pattern.
Follows Q1-Q8 decisions from KANBAN_INTEGRATION_STRATEGY.md.
"""

from typing import List, Optional, Dict
from uuid import UUID, uuid4
from datetime import datetime
import logging

from backend.app.models.kanban_task import (
    Task,
    TaskCreate,
    TaskUpdate,
    TaskStatus,
    TaskPriority,
    TaskFilters,
    PaginationMeta,
    TaskListResponse,
    PhaseChangeRequest,
    StatusChangeRequest,
    PriorityChangeRequest,
    CompletenessUpdateRequest,
    QualityGateResult,
    QualityGateCheck,
    ArchiveRequest,
    TaskArchive,
    TaskNotFoundError,
)

logger = logging.getLogger(__name__)


class KanbanTaskService:
    """
    Service for managing Kanban tasks.

    Mock implementation for Week 2 (will be replaced with database later).
    Provides all CRUD operations with pagination and filtering.
    """

    def __init__(self, db_session=None):
        """
        Initialize service with database session.

        Args:
            db_session: Database session (optional for testing with mock data)
        """
        self.db = db_session
        # In-memory storage for testing (will be replaced by DB)
        self._mock_tasks: Dict[UUID, Task] = {}
        self._mock_archived: Dict[UUID, TaskArchive] = {}

        # Create some test tasks for development
        self._create_test_tasks()

    def _create_test_tasks(self):
        """Create test tasks for development"""
        test_phases = [
            {"phase_id": uuid4(), "phase_name": "ideation"},
            {"phase_id": uuid4(), "phase_name": "design"},
            {"phase_id": uuid4(), "phase_name": "implementation"},
        ]

        for i, phase in enumerate(test_phases):
            task = Task(
                task_id=uuid4(),
                title=f"Test Task {i+1}",
                description=f"Test task in {phase['phase_name']} phase",
                phase_id=phase["phase_id"],
                phase_name=phase["phase_name"],
                status=TaskStatus.PENDING if i == 0 else TaskStatus.IN_PROGRESS,
                priority=TaskPriority.HIGH if i == 0 else TaskPriority.MEDIUM,
                completeness=0 if i == 0 else 50,
                estimated_hours=8.0,
                actual_hours=0.0 if i == 0 else 4.0,
            )
            self._mock_tasks[task.task_id] = task

        logger.info(f"Created {len(self._mock_tasks)} test tasks")

    # ========================================================================
    # CRUD Operations
    # ========================================================================

    async def create_task(self, task_data: TaskCreate) -> Task:
        """
        Create new task.

        Args:
            task_data: Task creation data

        Returns:
            Created task

        Raises:
            TaskValidationError: If validation fails
        """
        task = Task(
            task_id=uuid4(),
            title=task_data.title,
            description=task_data.description,
            phase_id=task_data.phase_id,
            phase_name=task_data.phase_name,
            status=task_data.status,
            priority=task_data.priority,
            completeness=task_data.completeness,
            estimated_hours=task_data.estimated_hours,
            actual_hours=task_data.actual_hours,
            ai_suggested=task_data.ai_suggested,
            ai_confidence=task_data.ai_confidence,
        )

        if self.db:
            # Database implementation (when DB is available)
            pass
        else:
            # Mock implementation
            self._mock_tasks[task.task_id] = task

        logger.info(f"Created task: {task.task_id} - {task.title}")
        return task

    async def get_task(self, task_id: UUID) -> Task:
        """
        Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task

        Raises:
            TaskNotFoundError: If task not found
        """
        if self.db:
            # Database implementation
            pass
        else:
            # Mock implementation
            task = self._mock_tasks.get(task_id)
            if not task:
                raise TaskNotFoundError(task_id)
            return task

    async def list_tasks(
        self,
        filters: Optional[TaskFilters] = None,
        page: int = 1,
        per_page: int = 50,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> TaskListResponse:
        """
        List tasks with filtering, sorting, and pagination.

        Args:
            filters: Optional filters
            page: Page number (1-indexed)
            per_page: Items per page (default 50)
            sort_by: Sort field
            sort_desc: Sort descending (default True)

        Returns:
            Paginated task list
        """
        # Start with all tasks
        tasks = list(self._mock_tasks.values())

        # Apply filters
        if filters:
            if filters.phase:
                tasks = [t for t in tasks if t.phase_name == filters.phase]
            if filters.status:
                tasks = [t for t in tasks if t.status == filters.status]
            if filters.priority:
                tasks = [t for t in tasks if t.priority == filters.priority]
            if filters.min_completeness is not None:
                tasks = [t for t in tasks if t.completeness >= filters.min_completeness]
            if filters.max_completeness is not None:
                tasks = [t for t in tasks if t.completeness <= filters.max_completeness]
            if filters.ai_suggested is not None:
                tasks = [t for t in tasks if t.ai_suggested == filters.ai_suggested]
            if filters.quality_gate_passed is not None:
                tasks = [t for t in tasks if t.quality_gate_passed == filters.quality_gate_passed]

        # Sort tasks
        if sort_by == "created_at":
            tasks.sort(key=lambda t: t.created_at, reverse=sort_desc)
        elif sort_by == "updated_at":
            tasks.sort(key=lambda t: t.updated_at, reverse=sort_desc)
        elif sort_by == "priority":
            priority_order = {
                TaskPriority.CRITICAL: 4,
                TaskPriority.HIGH: 3,
                TaskPriority.MEDIUM: 2,
                TaskPriority.LOW: 1,
            }
            tasks.sort(
                key=lambda t: priority_order.get(t.priority, 0),
                reverse=sort_desc
            )
        elif sort_by == "completeness":
            tasks.sort(key=lambda t: t.completeness, reverse=sort_desc)

        # Calculate pagination
        total = len(tasks)
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_tasks = tasks[start_idx:end_idx]

        # Build response
        pagination = PaginationMeta(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

        logger.info(
            f"Listed {len(paginated_tasks)}/{total} tasks "
            f"(page {page}/{total_pages})"
        )

        return TaskListResponse(data=paginated_tasks, pagination=pagination)

    async def update_task(
        self,
        task_id: UUID,
        task_update: TaskUpdate
    ) -> Task:
        """
        Update task.

        Args:
            task_id: Task ID
            task_update: Update data

        Returns:
            Updated task

        Raises:
            TaskNotFoundError: If task not found
        """
        task = await self.get_task(task_id)

        # Apply updates (only non-None fields)
        if task_update.title is not None:
            task.title = task_update.title
        if task_update.description is not None:
            task.description = task_update.description
        if task_update.status is not None:
            task.status = task_update.status
        if task_update.priority is not None:
            task.priority = task_update.priority
        if task_update.completeness is not None:
            task.completeness = task_update.completeness
        if task_update.estimated_hours is not None:
            task.estimated_hours = task_update.estimated_hours
        if task_update.actual_hours is not None:
            task.actual_hours = task_update.actual_hours
        if task_update.quality_score is not None:
            task.quality_score = task_update.quality_score

        task.updated_at = datetime.utcnow()

        # Mark as completed if completeness is 100%
        if task.completeness == 100 and task.status != TaskStatus.COMPLETED:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()

        if self.db:
            # Database implementation
            pass
        else:
            # Mock implementation (already updated)
            pass

        logger.info(f"Updated task: {task_id}")
        return task

    async def delete_task(self, task_id: UUID) -> bool:
        """
        Delete task (soft delete).

        Args:
            task_id: Task ID

        Returns:
            True if deleted

        Raises:
            TaskNotFoundError: If task not found
        """
        task = await self.get_task(task_id)

        if self.db:
            # Database implementation (soft delete)
            pass
        else:
            # Mock implementation (hard delete for now)
            del self._mock_tasks[task_id]

        logger.info(f"Deleted task: {task_id}")
        return True

    # ========================================================================
    # Phase Operations
    # ========================================================================

    async def change_phase(
        self,
        task_id: UUID,
        phase_request: PhaseChangeRequest
    ) -> Task:
        """
        Move task to different phase.

        Args:
            task_id: Task ID
            phase_request: Phase change data

        Returns:
            Updated task
        """
        task = await self.get_task(task_id)

        task.phase_id = phase_request.new_phase_id
        task.phase_name = phase_request.new_phase_name
        task.updated_at = datetime.utcnow()

        logger.info(
            f"Moved task {task_id} to phase: {phase_request.new_phase_name}"
        )
        return task

    # ========================================================================
    # Status & Priority Operations
    # ========================================================================

    async def change_status(
        self,
        task_id: UUID,
        status_request: StatusChangeRequest
    ) -> Task:
        """
        Change task status.

        Args:
            task_id: Task ID
            status_request: Status change data

        Returns:
            Updated task
        """
        task = await self.get_task(task_id)

        task.status = status_request.new_status
        task.updated_at = datetime.utcnow()

        # Set completed_at if status is COMPLETED
        if status_request.new_status == TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()

        logger.info(f"Changed task {task_id} status to: {status_request.new_status}")
        return task

    async def change_priority(
        self,
        task_id: UUID,
        priority_request: PriorityChangeRequest
    ) -> Task:
        """
        Change task priority.

        Args:
            task_id: Task ID
            priority_request: Priority change data

        Returns:
            Updated task
        """
        task = await self.get_task(task_id)

        task.priority = priority_request.new_priority
        task.updated_at = datetime.utcnow()

        logger.info(
            f"Changed task {task_id} priority to: {priority_request.new_priority}"
        )
        return task

    async def update_completeness(
        self,
        task_id: UUID,
        completeness_request: CompletenessUpdateRequest
    ) -> Task:
        """
        Update task completeness percentage.

        Args:
            task_id: Task ID
            completeness_request: Completeness update data

        Returns:
            Updated task
        """
        task = await self.get_task(task_id)

        task.completeness = completeness_request.completeness
        task.updated_at = datetime.utcnow()

        # Auto-mark as completed if 100%
        if completeness_request.completeness == 100:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()

        logger.info(
            f"Updated task {task_id} completeness to: "
            f"{completeness_request.completeness}%"
        )
        return task

    # ========================================================================
    # Quality Gate Operations (Q3)
    # ========================================================================

    async def run_quality_gates(self, task_id: UUID) -> QualityGateResult:
        """
        Run quality gate checks on task (Q3: Hybrid completion).

        Checks:
        1. Constitutional compliance (P1-P17)
        2. Code quality standards
        3. Test coverage
        4. Documentation completeness

        Args:
            task_id: Task ID

        Returns:
            Quality gate result
        """
        task = await self.get_task(task_id)
        start_time = datetime.utcnow()

        # Mock quality checks (will integrate with quality_service later)
        checks = [
            QualityGateCheck(
                check_name="Constitutional Compliance",
                passed=True,
                message="All constitutional articles satisfied",
                article=None
            ),
            QualityGateCheck(
                check_name="Code Quality",
                passed=True,
                message="Code quality score: 85/100",
                article=None
            ),
            QualityGateCheck(
                check_name="Test Coverage",
                passed=True,
                message="Test coverage: 80%",
                article=None
            ),
        ]

        # Calculate results
        passed_checks = [c for c in checks if c.passed]
        quality_score = int((len(passed_checks) / len(checks)) * 100)
        quality_gate_passed = len(passed_checks) == len(checks)
        violated_articles = [c.article for c in checks if not c.passed and c.article]

        # Update task
        task.quality_gate_passed = quality_gate_passed
        task.quality_score = quality_score
        task.constitutional_compliant = len(violated_articles) == 0
        task.violated_articles = violated_articles

        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        result = QualityGateResult(
            task_id=task_id,
            quality_gate_passed=quality_gate_passed,
            quality_score=quality_score,
            constitutional_compliant=len(violated_articles) == 0,
            violated_articles=violated_articles,
            checks=checks,
            timestamp=datetime.utcnow(),
            execution_time_ms=execution_time,
        )

        logger.info(
            f"Quality gate for task {task_id}: "
            f"{'PASSED' if quality_gate_passed else 'FAILED'} "
            f"(score: {quality_score}/100)"
        )

        return result

    async def get_quality_gates(self, task_id: UUID) -> QualityGateResult:
        """
        Get quality gate status for task.

        Args:
            task_id: Task ID

        Returns:
            Quality gate result (cached from last run)
        """
        task = await self.get_task(task_id)

        # Return cached result
        result = QualityGateResult(
            task_id=task_id,
            quality_gate_passed=task.quality_gate_passed,
            quality_score=task.quality_score or 0,
            constitutional_compliant=task.constitutional_compliant,
            violated_articles=task.violated_articles,
            checks=[],
            timestamp=task.updated_at,
            execution_time_ms=0.0,
        )

        return result

    # ========================================================================
    # Archive Operations (Q6)
    # ========================================================================

    async def archive_task(
        self,
        task_id: UUID,
        archive_request: ArchiveRequest
    ) -> TaskArchive:
        """
        Archive task to Done-End (Q6: Done-End + AI → Obsidian).

        Args:
            task_id: Task ID
            archive_request: Archive request data

        Returns:
            Task archive
        """
        task = await self.get_task(task_id)

        # Generate AI summary if requested (mock for now)
        ai_summary = None
        if archive_request.generate_ai_summary:
            ai_summary = (
                f"Task '{task.title}' completed in {task.phase_name} phase. "
                f"Completeness: {task.completeness}%. "
                f"Estimated: {task.estimated_hours}h, "
                f"Actual: {task.actual_hours}h."
            )

        # Create archive
        archive = TaskArchive(
            task_id=task_id,
            task_data=task,
            ai_summary=ai_summary,
            archived_at=datetime.utcnow(),
            archived_by=archive_request.archived_by,
            obsidian_synced=False,  # Will be synced by obsidian_service
        )

        # Update task status
        task.status = TaskStatus.DONE_END
        task.archived_at = datetime.utcnow()

        if self.db:
            # Database implementation
            pass
        else:
            # Mock implementation
            self._mock_archived[task_id] = archive

        logger.info(f"Archived task: {task_id}")
        return archive


# ============================================================================
# Singleton Instance
# ============================================================================

kanban_task_service = KanbanTaskService()
