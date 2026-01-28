"""
Kanban Archive API Router

Week 3 Day 4-5: Archive View + AI Summarization.
Implements Q6: Done-End archive with GPT-4o summarization and Obsidian sync.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from app.core.security import UserRole, get_current_user, require_role
from app.models.kanban_archive import (
    ArchivedTaskWithMetrics,
    ArchiveFilters,
    ArchiveListResponse,
    ArchiveTaskRequest,
    ArchiveTaskResponse,
    TaskNotArchivableError,
)
from app.services.kanban_archive_service import kanban_archive_service
from app.services.kanban_task_service import (
    KanbanTaskService,
    kanban_task_service as shared_mock_service,
)
from backend.async_database import async_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kanban/archive", tags=["Kanban Archive"])


# ============================================================================
# Dependency Injection for Task Service
# ============================================================================


def get_kanban_service_for_archive():
    """
    Dependency for KanbanTaskService in archive operations.
    Uses same pattern as kanban_tasks.py for consistency.
    """
    try:
        db_pool = async_db.get_pool()
        return KanbanTaskService(db_pool=db_pool)
    except RuntimeError as e:
        logger.warning(f"[ARCHIVE] Database not available: {e}. Using mock service")
        return shared_mock_service


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
# DEBUG: Test Dependency Injection (BEFORE /{task_id} route)
# ============================================================================


@router.get("/test/di")
async def debug_dependency_injection_first(
    task_service: KanbanTaskService = Depends(get_kanban_service_for_archive),
):
    """Debug endpoint to test DI and task lookup"""
    from uuid import UUID

    task_id = UUID("de1a9f24-4ee2-420e-add1-ebafed339efe")

    result = {
        "task_service_type": type(task_service).__name__,
        "has_db_pool": hasattr(task_service, "db_pool"),
        "db_pool_not_none": task_service.db_pool is not None if hasattr(task_service, "db_pool") else False,
    }

    try:
        task = await task_service.get_task(task_id)
        result["task_found"] = True
        result["task_title"] = task.title
        result["task_status"] = str(task.status)
    except Exception as e:
        result["task_found"] = False
        result["error"] = f"{type(e).__name__}: {e}"

    return result


# ============================================================================
# 1. Archive Task (Q6: Done-End + AI Summarization)
# ============================================================================


@router.post(
    "",
    response_model=ArchiveTaskResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Archive completed task",
    description="Archive completed task with AI summarization and Obsidian sync (Q6: Done-End)",
)
async def archive_task(
    request: ArchiveTaskRequest,
    current_user: dict = Depends(get_current_user),
    task_service: KanbanTaskService = Depends(get_kanban_service_for_archive),
):
    """
    Archive a completed Kanban task with AI summarization and knowledge extraction.

    **RBAC**: Requires `developer` role or higher.
    **Q6**: Done-End archive with GPT-4o AI summarization -> Obsidian knowledge base.

    Process:
    1. Validate task is completed
    2. Generate AI summary using GPT-4o (or mock mode)
    3. Calculate ROI metrics (efficiency, quality, time saved)
    4. Sync to Obsidian knowledge base
    5. Mark task as DONE_END in archive

    Features:
    - AI-generated summary with key learnings
    - Technical insights extraction
    - ROI metrics calculation
    - Obsidian knowledge sync
    - Recommendations for future tasks

    Raises:
        400: Invalid request (task not completed)
        404: Task not found
        409: Task already archived
        500: Archive operation failed
    """
    print(f"[ARCHIVE-DEBUG] archive_task endpoint called with task_id={request.task_id}", flush=True)
    try:
        # Set archived_by from current user
        request.archived_by = current_user.get("username", current_user.get("email"))

        print(f"[ARCHIVE-DEBUG] Processing archive request for task_id={request.task_id}", flush=True)
        print(f"[ARCHIVE-DEBUG] task_service type: {type(task_service).__name__}", flush=True)
        print(f"[ARCHIVE-DEBUG] task_service has db_pool: {hasattr(task_service, 'db_pool')}", flush=True)

        logger.info(f"[ARCHIVE] Processing archive request for task_id={request.task_id}")
        logger.info(f"[ARCHIVE] task_service type: {type(task_service).__name__}")
        logger.info(f"[ARCHIVE] task_service has db_pool: {hasattr(task_service, 'db_pool')}")

        # Archive task with injected task service for DB access
        response = await kanban_archive_service.archive_task(request, task_service)

        return response

    except TaskNotArchivableError as e:
        print(f"[ARCHIVE-DEBUG] TaskNotArchivableError: {e}", flush=True)
        return error_response(
            code="TASK_NOT_ARCHIVABLE",
            message=str(e),
            status_code=status.HTTP_409_CONFLICT,
            details={"task_id": str(request.task_id)},
        )
    except Exception as e:
        print(f"[ARCHIVE-DEBUG] Exception caught: {type(e).__name__}: {e}", flush=True)
        return error_response(
            code="ARCHIVE_FAILED",
            message=f"Failed to archive task: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"task_id": str(request.task_id)},
        )


# ============================================================================
# 2. Get Archive List
# ============================================================================


@router.get(
    "",
    response_model=ArchiveListResponse,
    dependencies=[Depends(require_role(UserRole.VIEWER))],
    summary="Get archived tasks list",
    description="Get paginated list of archived tasks with filtering and ROI statistics",
)
async def get_archive_list(
    phase: Optional[str] = Query(None, description="Filter by phase"),
    archived_by: Optional[str] = Query(None, description="Filter by archiver"),
    ai_suggested: Optional[bool] = Query(None, description="Filter by AI suggestion"),
    obsidian_synced: Optional[bool] = Query(None, description="Filter by Obsidian sync status"),
    min_quality_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum quality score"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get paginated list of archived tasks with filtering.

    **RBAC**: Requires `viewer` role or higher.
    **Q6**: View archived tasks with AI summaries and ROI metrics.

    Features:
    - Pagination support
    - Filter by phase, archiver, AI suggestion status
    - Filter by Obsidian sync status
    - Filter by minimum quality score
    - Aggregated ROI statistics
    - Phase breakdown

    Returns:
    - List of archived tasks with full metrics
    - Pagination metadata
    - Aggregated ROI statistics
    """
    try:
        filters = ArchiveFilters(
            phase=phase,
            archived_by=archived_by,
            ai_suggested=ai_suggested,
            obsidian_synced=obsidian_synced,
            min_quality_score=min_quality_score,
        )

        response = await kanban_archive_service.get_archive_list(filters=filters, page=page, per_page=per_page)

        return response

    except Exception as e:
        return error_response(
            code="ARCHIVE_LIST_FAILED",
            message=f"Failed to retrieve archive list: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ============================================================================
# 3. Get Specific Archived Task
# ============================================================================


@router.get(
    "/{task_id}",
    response_model=ArchivedTaskWithMetrics,
    dependencies=[Depends(require_role(UserRole.VIEWER))],
    summary="Get specific archived task",
    description="Get detailed information about a specific archived task",
)
async def get_archived_task(task_id: UUID, current_user: dict = Depends(get_current_user)):
    """
    Get detailed information about a specific archived task.

    **RBAC**: Requires `viewer` role or higher.
    **Q6**: View full archive details with AI summary and ROI metrics.

    Returns:
    - Complete task information
    - AI-generated summary with insights
    - ROI metrics (efficiency, quality, time saved)
    - Obsidian sync status
    - Key learnings and recommendations

    Raises:
        404: Archived task not found
    """
    try:
        # Get from archive storage
        archived_task = kanban_archive_service.archives.get(task_id)

        if not archived_task:
            return error_response(
                code="ARCHIVED_TASK_NOT_FOUND",
                message=f"Archived task {task_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
                details={"task_id": str(task_id)},
            )

        return archived_task

    except Exception as e:
        return error_response(
            code="ARCHIVED_TASK_RETRIEVAL_FAILED",
            message=f"Failed to retrieve archived task: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"task_id": str(task_id)},
        )


# ============================================================================
# 4. Get ROI Statistics (Optional Endpoint)
# ============================================================================


@router.get(
    "/statistics/roi",
    dependencies=[Depends(require_role(UserRole.VIEWER))],
    summary="Get ROI statistics",
    description="Get aggregated ROI statistics across all archived tasks",
)
async def get_roi_statistics(
    phase: Optional[str] = Query(None, description="Filter by phase"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get aggregated ROI statistics across archived tasks.

    **RBAC**: Requires `viewer` role or higher.
    **Q6**: Analyze return on investment for archived tasks.

    Returns:
    - Total tasks archived
    - Total time saved
    - Average efficiency
    - Average quality score
    - Constitutional compliance rate
    - AI suggestion accuracy
    - Phase breakdown
    """
    try:
        filters = ArchiveFilters(phase=phase) if phase else None

        # Get all archives with filter
        response = await kanban_archive_service.get_archive_list(
            filters=filters, page=1, per_page=1000  # Get all for statistics
        )

        return response.roi_statistics

    except Exception as e:
        return error_response(
            code="ROI_STATISTICS_FAILED",
            message=f"Failed to calculate ROI statistics: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
