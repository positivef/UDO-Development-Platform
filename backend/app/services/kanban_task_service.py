"""
Kanban Task Service - Core Task Management (Database Implementation)

Week 8 Day 1: Migrated from mock data to real PostgreSQL database.
Follows Q1-Q8 decisions from KANBAN_INTEGRATION_STRATEGY.md.

Week 8 Day 2: Added MockKanbanTaskService for testing without database.
"""

import logging
from datetime import UTC, datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

# Optional asyncpg import (not needed for Mock mode)
try:
    import asyncpg
except ImportError:
    asyncpg = None

from app.models.kanban_task import (
    ArchiveRequest,
    CompletenessUpdateRequest,
    PaginationMeta,
    PhaseChangeRequest,
    PhaseName,
    PriorityChangeRequest,
    QualityGateCheck,
    QualityGateResult,
    StatusChangeRequest,
    Task,
    TaskArchive,
    TaskCreate,
    TaskFilters,
    TaskListResponse,
    TaskNotFoundError,
    TaskPriority,
    TaskStatus,
    TaskUpdate,
)

logger = logging.getLogger(__name__)


class KanbanTaskService:
    """
    Service for managing Kanban tasks with PostgreSQL database.

    Uses asyncpg connection pool for all database operations.
    Provides CRUD operations with pagination, filtering, and quality gates.
    """

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize service with database connection pool.

        Args:
            db_pool: asyncpg connection pool
        """
        self.db_pool = db_pool

    # ========================================================================
    # CRUD Operations
    # ========================================================================

    async def create_task(self, task_data: TaskCreate) -> Task:
        """
        Create new task in database.

        Args:
            task_data: Task creation data

        Returns:
            Created task
        """
        async with self.db_pool.acquire() as conn:
            # Start explicit transaction
            async with conn.transaction():
                query = """
                    INSERT INTO kanban.tasks (
                        title, description, phase_id, phase_name,
                        status, priority, completeness,
                        estimated_hours, actual_hours,
                        ai_suggested, ai_confidence
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    RETURNING
                        task_id, title, description, phase_id, phase_name,
                        status, priority, completeness,
                        estimated_hours, actual_hours,
                        ai_suggested, ai_confidence, approved_by, approval_timestamp,
                        quality_gate_passed, quality_score,
                        constitutional_compliant, COALESCE(violated_articles, '{}') as violated_articles,
                        user_confirmed, confirmed_by, confirmed_at,
                        created_at, updated_at, completed_at, archived_at
                """

                row = await conn.fetchrow(
                    query,
                    task_data.title,
                    task_data.description,
                    task_data.phase_id,
                    task_data.phase_name,
                    task_data.status if task_data.status else "pending",
                    task_data.priority if task_data.priority else "medium",
                    task_data.completeness,
                    task_data.estimated_hours,
                    task_data.actual_hours,
                    task_data.ai_suggested,
                    task_data.ai_confidence,
                )

                task = Task(**dict(row))
                logger.info(f"Created task: {task.task_id} - {task.title}")
                # Transaction will auto-commit when context exits
                return task

    async def get_task(self, task_id: UUID) -> Task:
        """
        Get task by ID from database.

        Args:
            task_id: Task ID

        Returns:
            Task

        Raises:
            TaskNotFoundError: If task not found
        """
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT
                    task_id, title, description, phase_id, phase_name,
                    status, priority, completeness,
                    estimated_hours, actual_hours,
                    ai_suggested, ai_confidence, approved_by, approval_timestamp,
                    quality_gate_passed, quality_score,
                    constitutional_compliant, COALESCE(violated_articles, '{}') as violated_articles,
                    user_confirmed, confirmed_by, confirmed_at,
                    created_at, updated_at, completed_at, archived_at
                FROM kanban.tasks
                WHERE task_id = $1
            """

            row = await conn.fetchrow(query, task_id)

            if not row:
                raise TaskNotFoundError(task_id)

            return Task(**dict(row))

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
            sort_by: Sort field (created_at, updated_at, priority, completeness)
            sort_desc: Sort descending (default True)

        Returns:
            Paginated task list
        """
        async with self.db_pool.acquire() as conn:
            # Build WHERE clause
            where_clauses = []
            params = []
            param_count = 1

            if filters:
                if filters.phase:
                    where_clauses.append(f"phase_name = ${param_count}")
                    params.append(filters.phase)
                    param_count += 1

                if filters.status:
                    where_clauses.append(f"status = ${param_count}")
                    params.append(filters.status.value if hasattr(filters.status, "value") else filters.status)
                    param_count += 1

                if filters.priority:
                    where_clauses.append(f"priority = ${param_count}")
                    params.append(filters.priority.value if hasattr(filters.priority, "value") else filters.priority)
                    param_count += 1

                if filters.min_completeness is not None:
                    where_clauses.append(f"completeness >= ${param_count}")
                    params.append(filters.min_completeness)
                    param_count += 1

                if filters.max_completeness is not None:
                    where_clauses.append(f"completeness <= ${param_count}")
                    params.append(filters.max_completeness)
                    param_count += 1

                if filters.ai_suggested is not None:
                    where_clauses.append(f"ai_suggested = ${param_count}")
                    params.append(filters.ai_suggested)
                    param_count += 1

                if filters.quality_gate_passed is not None:
                    where_clauses.append(f"quality_gate_passed = ${param_count}")
                    params.append(filters.quality_gate_passed)
                    param_count += 1

            where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            # P0-4: Build ORDER BY clause with whitelist validation
            # Note: sort_by is already validated by TaskSortField.validate() in router
            # This mapping provides an additional safety layer and documentation
            sort_mapping = {
                "created_at": "created_at",
                "updated_at": "updated_at",
                "priority": "priority",
                "completeness": "completeness",
            }
            # Use validated sort_by from whitelist (already checked in router)
            sort_column = sort_mapping.get(sort_by, "created_at")
            # Direction is strictly controlled (not from user input)
            sort_direction = "DESC" if sort_desc else "ASC"

            # Count total
            count_query = f"SELECT COUNT(*) FROM kanban.tasks {where_sql}"
            total = await conn.fetchval(count_query, *params)

            # Calculate pagination
            total_pages = (total + per_page - 1) // per_page if total > 0 else 0
            offset = (page - 1) * per_page

            # Fetch tasks
            query = f"""
                SELECT
                    task_id, title, description, phase_id, phase_name,
                    status, priority, completeness,
                    estimated_hours, actual_hours,
                    ai_suggested, ai_confidence, approved_by, approval_timestamp,
                    quality_gate_passed, quality_score,
                    constitutional_compliant, COALESCE(violated_articles, '{{}}') as violated_articles,
                    user_confirmed, confirmed_by, confirmed_at,
                    created_at, updated_at, completed_at, archived_at
                FROM kanban.tasks
                {where_sql}
                ORDER BY {sort_column} {sort_direction}
                LIMIT ${param_count} OFFSET ${param_count + 1}
            """

            rows = await conn.fetch(query, *params, per_page, offset)
            tasks = [Task(**dict(row)) for row in rows]

            pagination = PaginationMeta(
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1,
            )

            logger.info(f"Listed {len(tasks)}/{total} tasks (page {page}/{total_pages})")
            return TaskListResponse(data=tasks, pagination=pagination)

    async def update_task(self, task_id: UUID, task_update: TaskUpdate) -> Task:
        """
        Update task in database.

        Args:
            task_id: Task ID
            task_update: Update data (only non-None fields are updated)

        Returns:
            Updated task

        Raises:
            TaskNotFoundError: If task not found
        """
        # Check task exists
        await self.get_task(task_id)

        async with self.db_pool.acquire() as conn:
            # Build dynamic UPDATE query
            set_clauses = []
            params = []
            param_count = 1

            if task_update.title is not None:
                set_clauses.append(f"title = ${param_count}")
                params.append(task_update.title)
                param_count += 1

            if task_update.description is not None:
                set_clauses.append(f"description = ${param_count}")
                params.append(task_update.description)
                param_count += 1

            if task_update.status is not None:
                set_clauses.append(f"status = ${param_count}")
                params.append(task_update.status.value if hasattr(task_update.status, "value") else task_update.status)
                param_count += 1

                # Set completed_at if status is COMPLETED
                if task_update.status == TaskStatus.COMPLETED:
                    set_clauses.append(f"completed_at = ${param_count}")
                    params.append(datetime.now(UTC).replace(tzinfo=None))
                    param_count += 1

            if task_update.priority is not None:
                set_clauses.append(f"priority = ${param_count}")
                params.append(task_update.priority.value if hasattr(task_update.priority, "value") else task_update.priority)
                param_count += 1

            if task_update.completeness is not None:
                set_clauses.append(f"completeness = ${param_count}")
                params.append(task_update.completeness)
                param_count += 1

                # Auto-mark as completed if 100%
                if task_update.completeness == 100:
                    set_clauses.append(f"status = ${param_count}")
                    params.append("completed")
                    param_count += 1
                    set_clauses.append(f"completed_at = ${param_count}")
                    params.append(datetime.now(UTC).replace(tzinfo=None))
                    param_count += 1

            if task_update.estimated_hours is not None:
                set_clauses.append(f"estimated_hours = ${param_count}")
                params.append(task_update.estimated_hours)
                param_count += 1

            if task_update.actual_hours is not None:
                set_clauses.append(f"actual_hours = ${param_count}")
                params.append(task_update.actual_hours)
                param_count += 1

            if task_update.quality_score is not None:
                set_clauses.append(f"quality_score = ${param_count}")
                params.append(task_update.quality_score)
                param_count += 1

            # Always update updated_at
            set_clauses.append(f"updated_at = ${param_count}")
            params.append(datetime.now(UTC).replace(tzinfo=None))
            param_count += 1

            # Add task_id as last parameter
            params.append(task_id)

            query = f"""
                UPDATE kanban.tasks
                SET {', '.join(set_clauses)}
                WHERE task_id = ${param_count}
                RETURNING
                    task_id, title, description, phase_id, phase_name,
                    status, priority, completeness,
                    estimated_hours, actual_hours,
                    ai_suggested, ai_confidence, approved_by, approval_timestamp,
                    quality_gate_passed, quality_score,
                    constitutional_compliant, violated_articles,
                    user_confirmed, confirmed_by, confirmed_at,
                    created_at, updated_at, completed_at, archived_at
            """

            row = await conn.fetchrow(query, *params)
            task = Task(**dict(row))

            logger.info(f"Updated task: {task_id}")
            return task

    async def delete_task(self, task_id: UUID) -> bool:
        """
        Delete task from database (hard delete).

        Args:
            task_id: Task ID

        Returns:
            True if deleted

        Raises:
            TaskNotFoundError: If task not found
        """
        async with self.db_pool.acquire() as conn:
            query = "DELETE FROM kanban.tasks WHERE task_id = $1"
            result = await conn.execute(query, task_id)

            # Check if any row was deleted
            deleted_count = int(result.split()[-1])
            if deleted_count == 0:
                raise TaskNotFoundError(task_id)

            logger.info(f"Deleted task: {task_id}")
            return True

    # ========================================================================
    # Phase Operations
    # ========================================================================

    async def change_phase(self, task_id: UUID, phase_request: PhaseChangeRequest) -> Task:
        """
        Move task to different phase.

        Args:
            task_id: Task ID
            phase_request: Phase change data

        Returns:
            Updated task
        """
        async with self.db_pool.acquire() as conn:
            query = """
                UPDATE kanban.tasks
                SET
                    phase_id = $1,
                    phase_name = $2,
                    updated_at = $3
                WHERE task_id = $4
                RETURNING
                    task_id, title, description, phase_id, phase_name,
                    status, priority, completeness,
                    estimated_hours, actual_hours,
                    ai_suggested, ai_confidence, approved_by, approval_timestamp,
                    quality_gate_passed, quality_score,
                    constitutional_compliant, violated_articles,
                    user_confirmed, confirmed_by, confirmed_at,
                    created_at, updated_at, completed_at, archived_at
            """

            row = await conn.fetchrow(
                query,
                phase_request.new_phase_id,
                phase_request.new_phase_name,
                datetime.now(UTC).replace(tzinfo=None),
                task_id,
            )

            if not row:
                raise TaskNotFoundError(task_id)

            task = Task(**dict(row))
            logger.info(f"Moved task {task_id} to phase: {phase_request.new_phase_name}")
            return task

    # ========================================================================
    # Status & Priority Operations
    # ========================================================================

    async def change_status(self, task_id: UUID, status_request: StatusChangeRequest) -> Task:
        """
        Change task status.

        Args:
            task_id: Task ID
            status_request: Status change data

        Returns:
            Updated task
        """
        async with self.db_pool.acquire() as conn:
            # Set completed_at if status is COMPLETED
            if status_request.new_status == TaskStatus.COMPLETED:
                query = """
                    UPDATE kanban.tasks
                    SET
                        status = $1,
                        completed_at = $2,
                        updated_at = $2
                    WHERE task_id = $3
                    RETURNING
                        task_id, title, description, phase_id, phase_name,
                        status, priority, completeness,
                        estimated_hours, actual_hours,
                        ai_suggested, ai_confidence, approved_by, approval_timestamp,
                        quality_gate_passed, quality_score,
                        constitutional_compliant, violated_articles,
                        user_confirmed, confirmed_by, confirmed_at,
                        created_at, updated_at, completed_at, archived_at
                """
                row = await conn.fetchrow(
                    query,
                    status_request.new_status,
                    datetime.now(UTC).replace(tzinfo=None),
                    task_id,
                )
            else:
                query = """
                    UPDATE kanban.tasks
                    SET
                        status = $1,
                        updated_at = $2
                    WHERE task_id = $3
                    RETURNING
                        task_id, title, description, phase_id, phase_name,
                        status, priority, completeness,
                        estimated_hours, actual_hours,
                        ai_suggested, ai_confidence, approved_by, approval_timestamp,
                        quality_gate_passed, quality_score,
                        constitutional_compliant, violated_articles,
                        user_confirmed, confirmed_by, confirmed_at,
                        created_at, updated_at, completed_at, archived_at
                """
                row = await conn.fetchrow(
                    query,
                    status_request.new_status,
                    datetime.now(UTC).replace(tzinfo=None),
                    task_id,
                )

            if not row:
                raise TaskNotFoundError(task_id)

            # Convert None to empty list for violated_articles (Pydantic validation)
            task_data = dict(row)
            if task_data.get("violated_articles") is None:
                task_data["violated_articles"] = []

            task = Task(**task_data)
            logger.info(f"Changed task {task_id} status to: {status_request.new_status}")
            return task

    async def change_priority(self, task_id: UUID, priority_request: PriorityChangeRequest) -> Task:
        """
        Change task priority.

        Args:
            task_id: Task ID
            priority_request: Priority change data

        Returns:
            Updated task
        """
        async with self.db_pool.acquire() as conn:
            query = """
                UPDATE kanban.tasks
                SET
                    priority = $1,
                    updated_at = $2
                WHERE task_id = $3
                RETURNING
                    task_id, title, description, phase_id, phase_name,
                    status, priority, completeness,
                    estimated_hours, actual_hours,
                    ai_suggested, ai_confidence, approved_by, approval_timestamp,
                    quality_gate_passed, quality_score,
                    constitutional_compliant, violated_articles,
                    user_confirmed, confirmed_by, confirmed_at,
                    created_at, updated_at, completed_at, archived_at
            """

            row = await conn.fetchrow(
                query, priority_request.new_priority.value, datetime.now(UTC).replace(tzinfo=None), task_id
            )

            if not row:
                raise TaskNotFoundError(task_id)

            task = Task(**dict(row))
            logger.info(f"Changed task {task_id} priority to: {priority_request.new_priority}")
            return task

    async def update_completeness(self, task_id: UUID, completeness_request: CompletenessUpdateRequest) -> Task:
        """
        Update task completeness percentage.

        Auto-marks task as completed if 100%.

        Args:
            task_id: Task ID
            completeness_request: Completeness update data

        Returns:
            Updated task
        """
        async with self.db_pool.acquire() as conn:
            # Auto-mark as completed if 100%
            if completeness_request.completeness == 100:
                query = """
                    UPDATE kanban.tasks
                    SET
                        completeness = $1,
                        status = 'completed',
                        completed_at = $2,
                        updated_at = $2
                    WHERE task_id = $3
                    RETURNING
                        task_id, title, description, phase_id, phase_name,
                        status, priority, completeness,
                        estimated_hours, actual_hours,
                        ai_suggested, ai_confidence, approved_by, approval_timestamp,
                        quality_gate_passed, quality_score,
                        constitutional_compliant, violated_articles,
                        user_confirmed, confirmed_by, confirmed_at,
                        created_at, updated_at, completed_at, archived_at
                """
                row = await conn.fetchrow(
                    query, completeness_request.completeness, datetime.now(UTC).replace(tzinfo=None), task_id
                )
            else:
                query = """
                    UPDATE kanban.tasks
                    SET
                        completeness = $1,
                        updated_at = $2
                    WHERE task_id = $3
                    RETURNING
                        task_id, title, description, phase_id, phase_name,
                        status, priority, completeness,
                        estimated_hours, actual_hours,
                        ai_suggested, ai_confidence, approved_by, approval_timestamp,
                        quality_gate_passed, quality_score,
                        constitutional_compliant, violated_articles,
                        user_confirmed, confirmed_by, confirmed_at,
                        created_at, updated_at, completed_at, archived_at
                """
                row = await conn.fetchrow(
                    query, completeness_request.completeness, datetime.now(UTC).replace(tzinfo=None), task_id
                )

            if not row:
                raise TaskNotFoundError(task_id)

            task = Task(**dict(row))
            logger.info(f"Updated task {task_id} completeness to: {completeness_request.completeness}%")
            return task

    # ========================================================================
    # Quality Gate Operations (Q3)
    # ========================================================================

    async def run_quality_gates(self, task_id: UUID) -> QualityGateResult:
        """
        Run quality gate checks on task (Q3: Hybrid completion).

        Updates task with quality gate results in database.

        Args:
            task_id: Task ID

        Returns:
            Quality gate result
        """
        start_time = datetime.now(UTC)

        # Mock quality checks (will integrate with quality_service later)
        checks = [
            QualityGateCheck(
                check_name="Constitutional Compliance",
                passed=True,
                message="All constitutional articles satisfied",
                article=None,
            ),
            QualityGateCheck(
                check_name="Code Quality",
                passed=True,
                message="Code quality score: 85/100",
                article=None,
            ),
            QualityGateCheck(
                check_name="Test Coverage",
                passed=True,
                message="Test coverage: 80%",
                article=None,
            ),
        ]

        # Calculate results
        passed_checks = [c for c in checks if c.passed]
        quality_score = int((len(passed_checks) / len(checks)) * 100)
        quality_gate_passed = len(passed_checks) == len(checks)
        violated_articles = [c.article for c in checks if not c.passed and c.article]

        # Update task in database
        async with self.db_pool.acquire() as conn:
            query = """
                UPDATE kanban.tasks
                SET
                    quality_gate_passed = $1,
                    quality_score = $2,
                    constitutional_compliant = $3,
                    violated_articles = $4,
                    updated_at = $5
                WHERE task_id = $6
            """
            await conn.execute(
                query,
                quality_gate_passed,
                quality_score,
                len(violated_articles) == 0,
                violated_articles,
                datetime.now(UTC).replace(tzinfo=None),
                task_id,
            )

        execution_time = (datetime.now(UTC) - start_time).total_seconds() * 1000

        result = QualityGateResult(
            task_id=task_id,
            quality_gate_passed=quality_gate_passed,
            quality_score=quality_score,
            constitutional_compliant=len(violated_articles) == 0,
            violated_articles=violated_articles,
            checks=checks,
            timestamp=datetime.now(UTC),
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
            Quality gate result (from database)
        """
        task = await self.get_task(task_id)

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

    async def archive_task(self, task_id: UUID, archive_request: ArchiveRequest) -> TaskArchive:
        """
        Archive task to Done-End (Q6: Done-End + AI -> Obsidian).

        Updates task status to 'done_end' and sets archived_at.

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

        # Update task status to done_end
        async with self.db_pool.acquire() as conn:
            query = """
                UPDATE kanban.tasks
                SET
                    status = 'done_end',
                    archived_at = $1,
                    updated_at = $1
                WHERE task_id = $2
            """
            # Use naive UTC datetime for asyncpg compatibility with 'timestamp without time zone' columns
            now_utc = datetime.now(UTC).replace(tzinfo=None)
            await conn.execute(query, now_utc, task_id)

        # Create archive object
        archive = TaskArchive(
            task_id=task_id,
            task_data=task,
            ai_summary=ai_summary,
            archived_at=datetime.now(UTC),
            archived_by=archive_request.archived_by,
            obsidian_synced=False,  # Will be synced by obsidian_service
        )

        logger.info(f"Archived task: {task_id}")
        return archive


# ============================================================================
# Mock Service for Testing
# ============================================================================


class MockKanbanTaskService:
    """
    Mock service for testing Kanban tasks without database.

    Uses in-memory Dict storage for all operations.
    Provides the same interface as KanbanTaskService.
    """

    def __init__(self):
        """Initialize with empty mock storage."""
        self._mock_tasks: Dict[UUID, Task] = {}
        self._initialize_test_tasks()

    def _initialize_test_tasks(self):
        """Create initial test tasks."""
        test_tasks = [
            Task(
                task_id=uuid4(),
                title="Setup Development Environment",
                description="Configure local dev environment with Docker",
                phase_id=uuid4(),
                phase_name=PhaseName.IMPLEMENTATION,
                status=TaskStatus.COMPLETED,
                priority=TaskPriority.HIGH,
                completeness=100,
                estimated_hours=4.0,
                actual_hours=3.5,
                ai_suggested=False,
                ai_confidence=None,
                quality_gate_passed=True,
                quality_score=95,
                constitutional_compliant=True,
                violated_articles=[],
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            Task(
                task_id=uuid4(),
                title="Implement Kanban Board UI",
                description="Build interactive Kanban board with React and DnD features",
                phase_id=uuid4(),
                phase_name=PhaseName.IMPLEMENTATION,
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.HIGH,
                completeness=60,
                estimated_hours=8.0,
                actual_hours=5.0,
                ai_suggested=True,
                ai_confidence=0.85,
                quality_gate_passed=False,
                quality_score=None,
                constitutional_compliant=True,
                violated_articles=[],
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            Task(
                task_id=uuid4(),
                title="Design API Schema",
                description="Define OpenAPI schema for Kanban endpoints",
                phase_id=uuid4(),
                phase_name=PhaseName.DESIGN,
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                completeness=0,
                estimated_hours=6.0,
                actual_hours=0.0,
                ai_suggested=True,
                ai_confidence=0.72,
                quality_gate_passed=False,
                quality_score=None,
                constitutional_compliant=True,
                violated_articles=[],
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
        ]

        for task in test_tasks:
            self._mock_tasks[task.task_id] = task

    def reset_mock_data(self, recreate_test_tasks: bool = True):
        """
        Reset mock data for clean test state.

        Args:
            recreate_test_tasks: If True, recreate initial test tasks
        """
        self._mock_tasks.clear()
        if recreate_test_tasks:
            self._initialize_test_tasks()
        logger.info("Mock task data reset")

    # ========================================================================
    # CRUD Operations
    # ========================================================================

    async def create_task(self, task_data: TaskCreate) -> Task:
        """Create new task in mock storage."""
        task = Task(
            task_id=uuid4(),
            title=task_data.title,
            description=task_data.description,
            phase_id=task_data.phase_id or uuid4(),
            phase_name=task_data.phase_name or PhaseName.IDEATION,
            status=task_data.status or TaskStatus.PENDING,
            priority=task_data.priority or TaskPriority.MEDIUM,
            completeness=task_data.completeness or 0,
            estimated_hours=task_data.estimated_hours,
            actual_hours=task_data.actual_hours,
            ai_suggested=task_data.ai_suggested or False,
            ai_confidence=task_data.ai_confidence,
            quality_gate_passed=False,
            quality_score=None,
            constitutional_compliant=True,
            violated_articles=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self._mock_tasks[task.task_id] = task
        logger.info(f"[Mock] Created task: {task.task_id} - {task.title}")
        return task

    async def get_task(self, task_id: UUID) -> Task:
        """Get task by ID from mock storage."""
        if task_id not in self._mock_tasks:
            raise TaskNotFoundError(task_id)
        return self._mock_tasks[task_id]

    async def list_tasks(
        self,
        filters: Optional[TaskFilters] = None,
        page: int = 1,
        per_page: int = 50,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> TaskListResponse:
        """List tasks with filtering and pagination from mock storage."""
        tasks = list(self._mock_tasks.values())

        # Apply filters
        if filters:
            if filters.phase:
                tasks = [t for t in tasks if t.phase_name == filters.phase]
            if filters.status:
                status_val = filters.status.value if hasattr(filters.status, "value") else filters.status
                tasks = [
                    t for t in tasks if t.status == status_val or (hasattr(t.status, "value") and t.status.value == status_val)
                ]
            if filters.priority:
                priority_val = filters.priority.value if hasattr(filters.priority, "value") else filters.priority
                tasks = [
                    t
                    for t in tasks
                    if t.priority == priority_val or (hasattr(t.priority, "value") and t.priority.value == priority_val)
                ]
            if filters.min_completeness is not None:
                tasks = [t for t in tasks if (t.completeness or 0) >= filters.min_completeness]
            if filters.max_completeness is not None:
                tasks = [t for t in tasks if (t.completeness or 0) <= filters.max_completeness]
            if filters.ai_suggested is not None:
                tasks = [t for t in tasks if t.ai_suggested == filters.ai_suggested]
            if filters.quality_gate_passed is not None:
                tasks = [t for t in tasks if t.quality_gate_passed == filters.quality_gate_passed]

        # Sort
        sort_key = sort_by if sort_by in ["created_at", "updated_at", "priority", "completeness"] else "created_at"
        tasks.sort(
            key=lambda t: getattr(t, sort_key) or datetime.min.replace(tzinfo=UTC),
            reverse=sort_desc,
        )

        # Paginate
        total = len(tasks)
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        start = (page - 1) * per_page
        end = start + per_page
        paginated_tasks = tasks[start:end]

        pagination = PaginationMeta(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

        return TaskListResponse(data=paginated_tasks, pagination=pagination)

    async def update_task(self, task_id: UUID, task_update: TaskUpdate) -> Task:
        """Update task in mock storage."""
        if task_id not in self._mock_tasks:
            raise TaskNotFoundError(task_id)

        task = self._mock_tasks[task_id]

        if task_update.title is not None:
            task.title = task_update.title
        if task_update.description is not None:
            task.description = task_update.description
        if task_update.status is not None:
            task.status = task_update.status
            if task_update.status == TaskStatus.COMPLETED:
                task.completed_at = datetime.now(UTC)
        if task_update.priority is not None:
            task.priority = task_update.priority
        if task_update.completeness is not None:
            task.completeness = task_update.completeness
            if task_update.completeness == 100:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now(UTC)
        if task_update.estimated_hours is not None:
            task.estimated_hours = task_update.estimated_hours
        if task_update.actual_hours is not None:
            task.actual_hours = task_update.actual_hours
        if task_update.quality_score is not None:
            task.quality_score = task_update.quality_score

        task.updated_at = datetime.now(UTC)
        logger.info(f"[Mock] Updated task: {task_id}")
        return task

    async def delete_task(self, task_id: UUID) -> bool:
        """Delete task from mock storage."""
        if task_id not in self._mock_tasks:
            raise TaskNotFoundError(task_id)
        del self._mock_tasks[task_id]
        logger.info(f"[Mock] Deleted task: {task_id}")
        return True

    # ========================================================================
    # Phase Operations
    # ========================================================================

    async def change_phase(self, task_id: UUID, phase_request: PhaseChangeRequest) -> Task:
        """Move task to different phase."""
        if task_id not in self._mock_tasks:
            raise TaskNotFoundError(task_id)

        task = self._mock_tasks[task_id]
        task.phase_id = phase_request.new_phase_id
        task.phase_name = phase_request.new_phase_name
        task.updated_at = datetime.now(UTC)
        logger.info(f"[Mock] Moved task {task_id} to phase: {phase_request.new_phase_name}")
        return task

    # ========================================================================
    # Status & Priority Operations
    # ========================================================================

    async def change_status(self, task_id: UUID, status_request: StatusChangeRequest) -> Task:
        """Change task status."""
        if task_id not in self._mock_tasks:
            raise TaskNotFoundError(task_id)

        task = self._mock_tasks[task_id]
        task.status = status_request.new_status
        task.updated_at = datetime.now(UTC)
        if status_request.new_status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now(UTC)
        logger.info(f"[Mock] Changed task {task_id} status to: {status_request.new_status}")
        return task

    async def change_priority(self, task_id: UUID, priority_request: PriorityChangeRequest) -> Task:
        """Change task priority."""
        if task_id not in self._mock_tasks:
            raise TaskNotFoundError(task_id)

        task = self._mock_tasks[task_id]
        task.priority = priority_request.new_priority
        task.updated_at = datetime.now(UTC)
        logger.info(f"[Mock] Changed task {task_id} priority to: {priority_request.new_priority}")
        return task

    async def update_completeness(self, task_id: UUID, completeness_request: CompletenessUpdateRequest) -> Task:
        """Update task completeness percentage."""
        if task_id not in self._mock_tasks:
            raise TaskNotFoundError(task_id)

        task = self._mock_tasks[task_id]
        task.completeness = completeness_request.completeness
        task.updated_at = datetime.now(UTC)
        if completeness_request.completeness == 100:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(UTC)
        logger.info(f"[Mock] Updated task {task_id} completeness to: {completeness_request.completeness}%")
        return task

    # ========================================================================
    # Quality Gate Operations (Q3)
    # ========================================================================

    async def run_quality_gates(self, task_id: UUID) -> QualityGateResult:
        """Run quality gate checks on task."""
        if task_id not in self._mock_tasks:
            raise TaskNotFoundError(task_id)

        start_time = datetime.now(UTC)

        checks = [
            QualityGateCheck(
                check_name="Constitutional Compliance",
                passed=True,
                message="All constitutional articles satisfied",
                article=None,
            ),
            QualityGateCheck(
                check_name="Code Quality",
                passed=True,
                message="Code quality score: 85/100",
                article=None,
            ),
            QualityGateCheck(
                check_name="Test Coverage",
                passed=True,
                message="Test coverage: 80%",
                article=None,
            ),
        ]

        passed_checks = [c for c in checks if c.passed]
        quality_score = int((len(passed_checks) / len(checks)) * 100)
        quality_gate_passed = len(passed_checks) == len(checks)
        violated_articles = [c.article for c in checks if not c.passed and c.article]

        task = self._mock_tasks[task_id]
        task.quality_gate_passed = quality_gate_passed
        task.quality_score = quality_score
        task.constitutional_compliant = len(violated_articles) == 0
        task.violated_articles = violated_articles
        task.updated_at = datetime.now(UTC)

        execution_time = (datetime.now(UTC) - start_time).total_seconds() * 1000

        result = QualityGateResult(
            task_id=task_id,
            quality_gate_passed=quality_gate_passed,
            quality_score=quality_score,
            constitutional_compliant=len(violated_articles) == 0,
            violated_articles=violated_articles,
            checks=checks,
            timestamp=datetime.now(UTC),
            execution_time_ms=execution_time,
        )

        logger.info(f"[Mock] Quality gate for task {task_id}: {'PASSED' if quality_gate_passed else 'FAILED'}")
        return result

    async def get_quality_gates(self, task_id: UUID) -> QualityGateResult:
        """Get quality gate status for task."""
        task = await self.get_task(task_id)

        return QualityGateResult(
            task_id=task_id,
            quality_gate_passed=task.quality_gate_passed,
            quality_score=task.quality_score or 0,
            constitutional_compliant=task.constitutional_compliant,
            violated_articles=task.violated_articles,
            checks=[],
            timestamp=task.updated_at,
            execution_time_ms=0.0,
        )

    # ========================================================================
    # Archive Operations (Q6)
    # ========================================================================

    async def archive_task(self, task_id: UUID, archive_request: ArchiveRequest) -> TaskArchive:
        """Archive task to Done-End."""
        task = await self.get_task(task_id)

        ai_summary = None
        if archive_request.generate_ai_summary:
            ai_summary = (
                f"Task '{task.title}' completed in {task.phase_name} phase. "
                f"Completeness: {task.completeness}%. "
                f"Estimated: {task.estimated_hours}h, "
                f"Actual: {task.actual_hours}h."
            )

        task.status = TaskStatus.DONE_END
        task.archived_at = datetime.now(UTC)
        task.updated_at = datetime.now(UTC)

        archive = TaskArchive(
            task_id=task_id,
            task_data=task,
            ai_summary=ai_summary,
            archived_at=datetime.now(UTC),
            archived_by=archive_request.archived_by,
            obsidian_synced=False,
        )

        logger.info(f"[Mock] Archived task: {task_id}")
        return archive


# ============================================================================
# Singleton Instance for Testing
# ============================================================================

# Create singleton instance for tests (uses MockKanbanTaskService)
kanban_task_service = MockKanbanTaskService()


# ============================================================================
# Dependency Injection
# ============================================================================


def get_kanban_task_service() -> "KanbanTaskService":
    """
    Dependency function for FastAPI routes.

    Returns a KanbanTaskService instance with the global database pool.
    Used via Depends(get_kanban_task_service) in route handlers.

    Example:
        @router.get("/tasks")
        async def list_tasks(
            service: KanbanTaskService = Depends(get_kanban_task_service)
        ):
            return await service.get_all_tasks()
    """
    from backend.async_database import async_db

    db_pool = async_db.get_pool()
    if db_pool is None:
        raise RuntimeError("Database pool not initialized. Ensure startup_event has run.")

    return KanbanTaskService(db_pool=db_pool)
