"""
Kanban Tasks API Router

Week 2 Day 3-4: 12 API endpoints for task management.
Implements Q1-Q8 decisions with RBAC protection.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.core.security import UserRole, get_current_user, require_role
from app.models.kanban_task import (
    ArchiveRequest,
    CompletenessUpdateRequest,
    PhaseChangeRequest,
    PriorityChangeRequest,
    QualityGateResult,
    StatusChangeRequest,
    Task,
    TaskArchive,
    TaskCreate,
    TaskFilters,
    TaskListResponse,
    TaskNotFoundError,
    TaskSortField,
    TaskUpdate,
)

# WebSocket support for real-time updates
from app.routers.kanban_websocket import kanban_manager
from app.services.kanban_task_service import KanbanTaskService, MockKanbanTaskService
from backend.async_database import async_db

router = APIRouter(prefix="/api/kanban/tasks", tags=["Kanban Tasks"])


# ============================================================================
# Dependency Injection
# ============================================================================


def get_kanban_service():
    """
    Dependency for KanbanTaskService with database pool.
    Falls back to MockKanbanTaskService when database is unavailable.

    [WARN] CRITICAL: Always provide mock fallback for services requiring database
    This allows E2E tests to run without PostgreSQL running
    See: docs/guides/ERROR_PREVENTION_GUIDE.md#service-fallback-pattern

    Returns:
        KanbanTaskService or MockKanbanTaskService: Service instance
    """
    import logging
    import sys

    logger = logging.getLogger(__name__)
    # Identity logs for debugging
    logger.debug(f"[IDENTITY] async_database module id: {id(sys.modules.get('backend.async_database'))}")
    logger.debug(f"[IDENTITY] async_db object id: {id(async_db)}")
    logger.debug(f"[IDENTITY] async_db._initialized: {async_db._initialized}")
    try:
        db_pool = async_db.get_pool()
        logger.debug(f"[DEBUG] Database pool obtained: {db_pool}")
        return KanbanTaskService(db_pool=db_pool)
    except RuntimeError as e:
        logger.exception("[KANBAN] Database not available, using MockKanbanTaskService")
        return MockKanbanTaskService()


# ============================================================================
# Error Response Helper
# ============================================================================


def error_response(code: str, message: str, status_code: int, details: dict = None):
    """Standard error response format"""
    from datetime import UTC, datetime

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "timestamp": datetime.now(UTC).isoformat() + "Z",
            }
        },
    )


# ============================================================================
# 1. CRUD Operations (5 endpoints)
# ============================================================================


@router.post(
    "",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Create new task",
    description="Create new task (requires developer role or higher)",
)
async def create_task(
    task_data: TaskCreate,
    service: KanbanTaskService = Depends(get_kanban_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Create new task.

    **RBAC**: Requires `developer` role or higher.
    **Q2**: Supports AI-suggested tasks with confidence score.
    **WebSocket**: Broadcasts task_created event to all connected clients.
    """
    try:
        task = await service.create_task(task_data)

        # Broadcast task creation to WebSocket clients
        # TODO(Q5): Use actual project_id when multi-project support is implemented
        project_id = "default"
        await kanban_manager.broadcast_to_project(
            {
                "type": "task_created",
                "task": task.model_dump(),  # Convert Pydantic model to dict
                "created_by": current_user.get("username", current_user.get("email")),
                "timestamp": (task.created_at.isoformat() if hasattr(task, "created_at") else None),
            },
            project_id,
        )

        return task
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        return error_response(
            code="TASK_CREATE_FAILED",
            message=f"Failed to create task: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get(
    "",
    response_model=TaskListResponse,
    dependencies=[Depends(require_role(UserRole.VIEWER))],
    summary="List tasks with filtering and pagination",
    description="List tasks with filters, sorting, and pagination (requires viewer role)",
)
async def list_tasks(
    # Filters (Q1: Phase filtering)
    phase: Optional[str] = Query(None, description="Filter by phase"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    min_completeness: Optional[int] = Query(None, ge=0, le=100, description="Min completeness %"),
    max_completeness: Optional[int] = Query(None, ge=0, le=100, description="Max completeness %"),
    ai_suggested: Optional[bool] = Query(None, description="Filter AI-suggested tasks (Q2)"),
    quality_gate_passed: Optional[bool] = Query(None, description="Filter by quality gate (Q3)"),
    # Pagination
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page (default 50)"),
    # Sorting
    sort_by: str = Query("created_at", description="Sort field"),
    sort_desc: bool = Query(True, description="Sort descending"),
    service: KanbanTaskService = Depends(get_kanban_service, use_cache=False),
    current_user: dict = Depends(get_current_user),
):
    """
    List tasks with filtering, sorting, and pagination.

    **RBAC**: Requires `viewer` role or higher.
    **Pagination**: Default 50 per page, max 100.
    **Q1**: Filter by phase (ideation/design/mvp/implementation/testing).
    **Q2**: Filter AI-suggested tasks.
    **Q3**: Filter by quality gate status.
    **Security (P0-4)**: Sort field validated against whitelist to prevent SQL injection.
    """
    try:
        # P0-4: Validate sort_by against whitelist (SQL injection protection)
        try:
            validated_sort_by = TaskSortField.validate(sort_by)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        # Build filters
        filters = TaskFilters(
            phase=phase,
            status=status_filter,
            priority=priority,
            min_completeness=min_completeness,
            max_completeness=max_completeness,
            ai_suggested=ai_suggested,
            quality_gate_passed=quality_gate_passed,
        )

        result = await service.list_tasks(
            filters=filters,
            page=page,
            per_page=per_page,
            sort_by=validated_sort_by,
            sort_desc=sort_desc,
        )

        return result
    except HTTPException:
        raise  # Re-raise HTTP exceptions (including validation errors)
    except Exception as e:
        return error_response(
            code="TASK_LIST_FAILED",
            message=f"Failed to list tasks: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get(
    "/debug",
    response_model=dict,
    summary="Debug Kanban service",
)
async def debug_service(
    service: KanbanTaskService = Depends(get_kanban_service, use_cache=False),
    current_user: dict = Depends(get_current_user),
):
    return {
        "service_type": type(service).__name__,
        "is_mock": isinstance(service, MockKanbanTaskService),
        "async_db_initialized": async_db._initialized,
        "async_db_pool": str(async_db._pool) if async_db._initialized else None,
    }


@router.get(
    "/{task_id}",
    response_model=Task,
    dependencies=[Depends(require_role(UserRole.VIEWER))],
    summary="Get task details",
    description="Get task by ID (requires viewer role)",
)
async def get_task(
    task_id: UUID,
    service: KanbanTaskService = Depends(get_kanban_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Get task by ID.

    **RBAC**: Requires `viewer` role or higher.
    """
    try:
        task = await service.get_task(task_id)
        return task
    except TaskNotFoundError:
        return error_response(
            code="TASK_NOT_FOUND",
            message=f"Task with ID {task_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"task_id": str(task_id)},
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        return error_response(
            code="TASK_GET_FAILED",
            message=f"Failed to get task: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.put(
    "/{task_id}",
    response_model=Task,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Update task",
    description="Update task (requires developer role or higher)",
)
async def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    service: KanbanTaskService = Depends(get_kanban_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Update task.

    **RBAC**: Requires `developer` role or higher.
    **Note**: Auto-marks as completed if completeness reaches 100%.
    **WebSocket**: Broadcasts task_updated event to all connected clients.
    """
    try:
        task = await service.update_task(task_id, task_update)

        # Broadcast task update to WebSocket clients
        # TODO(Q5): Use actual project_id when multi-project support is implemented
        project_id = "default"
        await kanban_manager.broadcast_to_project(
            {
                "type": "task_updated",
                "task_id": str(task_id),
                "updates": task_update.model_dump(exclude_unset=True),  # Only changed fields
                "task": task.model_dump(),  # Full updated task
                "updated_by": current_user.get("username", current_user.get("email")),
                "timestamp": (task.updated_at.isoformat() if hasattr(task, "updated_at") else None),
            },
            project_id,
        )

        return task
    except TaskNotFoundError:
        return error_response(
            code="TASK_NOT_FOUND",
            message=f"Task with ID {task_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"task_id": str(task_id)},
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        return error_response(
            code="TASK_UPDATE_FAILED",
            message=f"Failed to update task: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Delete task",
    description="Delete task (requires developer role or higher)",
)
async def delete_task(
    task_id: UUID,
    service: KanbanTaskService = Depends(get_kanban_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete task (soft delete).

    **RBAC**: Requires `developer` role or higher.
    **WebSocket**: Broadcasts task_deleted event to all connected clients.
    """
    try:
        await service.delete_task(task_id)

        # Broadcast task deletion to WebSocket clients
        # TODO(Q5): Use actual project_id when multi-project support is implemented
        project_id = "default"
        from datetime import UTC, datetime

        await kanban_manager.broadcast_to_project(
            {
                "type": "task_deleted",
                "task_id": str(task_id),
                "deleted_by": current_user.get("username", current_user.get("email")),
                "timestamp": datetime.now(UTC).isoformat(),
            },
            project_id,
        )

        return None
    except TaskNotFoundError:
        return error_response(
            code="TASK_NOT_FOUND",
            message=f"Task with ID {task_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"task_id": str(task_id)},
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        return error_response(
            code="TASK_DELETE_FAILED",
            message=f"Failed to delete task: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ============================================================================
# 2. Phase Operations (1 endpoint)
# ============================================================================


@router.put(
    "/{task_id}/phase",
    response_model=Task,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Move task to different phase",
    description="Move task to different phase (Q1: Task within Phase)",
)
async def change_phase(
    task_id: UUID,
    phase_request: PhaseChangeRequest,
    service: KanbanTaskService = Depends(get_kanban_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Move task to different phase.

    **RBAC**: Requires `developer` role or higher.
    **Q1**: Task within Phase relationship.
    """
    try:
        task = await service.change_phase(task_id, phase_request)
        return task
    except TaskNotFoundError:
        return error_response(
            code="TASK_NOT_FOUND",
            message=f"Task with ID {task_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"task_id": str(task_id)},
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        return error_response(
            code="PHASE_CHANGE_FAILED",
            message=f"Failed to change phase: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ============================================================================
# 3. Status & Priority Operations (3 endpoints)
# ============================================================================


@router.put(
    "/{task_id}/status",
    response_model=Task,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Change task status",
    description="Change task status",
)
async def change_status(
    task_id: UUID,
    status_request: StatusChangeRequest,
    service: KanbanTaskService = Depends(get_kanban_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Change task status.

    **RBAC**: Requires `developer` role or higher.
    **Note**: Auto-sets completed_at when status becomes COMPLETED.
    """
    try:
        task = await service.change_status(task_id, status_request)
        return task
    except TaskNotFoundError:
        return error_response(
            code="TASK_NOT_FOUND",
            message=f"Task with ID {task_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"task_id": str(task_id)},
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        return error_response(
            code="STATUS_CHANGE_FAILED",
            message=f"Failed to change status: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.put(
    "/{task_id}/priority",
    response_model=Task,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Change task priority",
    description="Change task priority",
)
async def change_priority(
    task_id: UUID,
    priority_request: PriorityChangeRequest,
    service: KanbanTaskService = Depends(get_kanban_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Change task priority.

    **RBAC**: Requires `developer` role or higher.
    """
    try:
        task = await service.change_priority(task_id, priority_request)
        return task
    except TaskNotFoundError:
        return error_response(
            code="TASK_NOT_FOUND",
            message=f"Task with ID {task_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"task_id": str(task_id)},
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        return error_response(
            code="PRIORITY_CHANGE_FAILED",
            message=f"Failed to change priority: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.put(
    "/{task_id}/completeness",
    response_model=Task,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Update task completeness",
    description="Update task completeness percentage (0-100)",
)
async def update_completeness(
    task_id: UUID,
    completeness_request: CompletenessUpdateRequest,
    service: KanbanTaskService = Depends(get_kanban_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Update task completeness percentage.

    **RBAC**: Requires `developer` role or higher.
    **Note**: Auto-marks as COMPLETED when reaching 100%.
    """
    try:
        task = await service.update_completeness(task_id, completeness_request)
        return task
    except TaskNotFoundError:
        return error_response(
            code="TASK_NOT_FOUND",
            message=f"Task with ID {task_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"task_id": str(task_id)},
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        return error_response(
            code="COMPLETENESS_UPDATE_FAILED",
            message=f"Failed to update completeness: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ============================================================================
# 4. Quality Gate Operations (2 endpoints) - Q3
# ============================================================================


@router.get(
    "/{task_id}/quality-gates",
    response_model=QualityGateResult,
    dependencies=[Depends(require_role(UserRole.VIEWER))],
    summary="Get quality gate status",
    description="Get quality gate status for task (Q3: Hybrid completion)",
)
async def get_quality_gates(
    task_id: UUID,
    service: KanbanTaskService = Depends(get_kanban_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Get quality gate status for task.

    **RBAC**: Requires `viewer` role or higher.
    **Q3**: Hybrid completion (Quality gate + User confirmation).
    """
    try:
        result = await service.get_quality_gates(task_id)
        return result
    except TaskNotFoundError:
        return error_response(
            code="TASK_NOT_FOUND",
            message=f"Task with ID {task_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"task_id": str(task_id)},
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        return error_response(
            code="QUALITY_GATE_GET_FAILED",
            message=f"Failed to get quality gate status: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post(
    "/{task_id}/quality-gates",
    response_model=QualityGateResult,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Run quality gate checks",
    description="Run quality gate checks on task (Q3: Hybrid completion)",
)
async def run_quality_gates(
    task_id: UUID,
    service: KanbanTaskService = Depends(get_kanban_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Run quality gate checks on task.

    **RBAC**: Requires `developer` role or higher.
    **Q3**: Hybrid completion - checks constitutional compliance (P1-P17).

    Checks:
    1. Constitutional compliance (P1-P17)
    2. Code quality standards
    3. Test coverage
    4. Documentation completeness
    """
    try:
        result = await service.run_quality_gates(task_id)
        return result
    except TaskNotFoundError:
        return error_response(
            code="TASK_NOT_FOUND",
            message=f"Task with ID {task_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"task_id": str(task_id)},
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        return error_response(
            code="QUALITY_GATE_RUN_FAILED",
            message=f"Failed to run quality gates: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ============================================================================
# 5. Archive Operation (1 endpoint) - Q6
# ============================================================================


@router.post(
    "/{task_id}/archive",
    response_model=TaskArchive,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Archive task to Done-End",
    description="Archive task to Done-End with AI summary (Q6: Done-End archiving)",
)
async def archive_task(
    task_id: UUID,
    archive_request: ArchiveRequest,
    service: KanbanTaskService = Depends(get_kanban_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Archive task to Done-End.

    **RBAC**: Requires `developer` role or higher.
    **Q6**: Done-End archiving with AI summary (GPT-4o) -> Obsidian sync.

    Process:
    1. Generate AI summary (optional, default: True)
    2. Move task to DONE_END status
    3. Save to archive
    4. Sync to Obsidian knowledge base (async)
    """
    try:
        archive = await service.archive_task(task_id, archive_request)
        return archive
    except TaskNotFoundError:
        return error_response(
            code="TASK_NOT_FOUND",
            message=f"Task with ID {task_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"task_id": str(task_id)},
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        return error_response(
            code="ARCHIVE_FAILED",
            message=f"Failed to archive task: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
