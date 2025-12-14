"""
Kanban Archive API Router

Week 3 Day 4-5: Archive View + AI Summarization.
Implements Q6: Done-End archive with GPT-4o summarization and Obsidian sync.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from backend.app.core.security import require_role, UserRole, get_current_user
from backend.app.services.kanban_archive_service import kanban_archive_service
from backend.app.models.kanban_archive import (
    ArchiveTaskRequest,
    ArchiveTaskResponse,
    ArchiveListResponse,
    ArchivedTaskWithMetrics,
    ArchiveFilters,
    TaskNotArchivableError,
    AISummaryGenerationError,
    ObsidianSyncError,
)

router = APIRouter(prefix="/api/kanban/archive", tags=["Kanban Archive"])


# ============================================================================
# Error Response Helper
# ============================================================================

def error_response(code: str, message: str, status_code: int, details: dict = None):
    """Standard error response format"""
    from datetime import datetime, UTC
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "timestamp": datetime.now(UTC).isoformat() + "Z"
            }
        }
    )


# ============================================================================
# 1. Archive Task (Q6: Done-End + AI Summarization)
# ============================================================================

@router.post(
    "",
    response_model=ArchiveTaskResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Archive completed task",
    description="Archive completed task with AI summarization and Obsidian sync (Q6: Done-End)"
)
async def archive_task(
    request: ArchiveTaskRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Archive a completed Kanban task with AI summarization and knowledge extraction.

    **RBAC**: Requires `developer` role or higher.
    **Q6**: Done-End archive with GPT-4o AI summarization → Obsidian knowledge base.

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
    try:
        # Set archived_by from current user
        request.archived_by = current_user.get("username", current_user.get("email"))

        # Archive task
        response = await kanban_archive_service.archive_task(request)

        return response

    except TaskNotArchivableError as e:
        return error_response(
            code="TASK_NOT_ARCHIVABLE",
            message=str(e),
            status_code=status.HTTP_409_CONFLICT,
            details={"task_id": str(request.task_id)}
        )
    except Exception as e:
        return error_response(
            code="ARCHIVE_FAILED",
            message=f"Failed to archive task: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"task_id": str(request.task_id)}
        )


# ============================================================================
# 2. Get Archive List
# ============================================================================

@router.get(
    "",
    response_model=ArchiveListResponse,
    dependencies=[Depends(require_role(UserRole.VIEWER))],
    summary="Get archived tasks list",
    description="Get paginated list of archived tasks with filtering and ROI statistics"
)
async def get_archive_list(
    phase: Optional[str] = Query(None, description="Filter by phase"),
    archived_by: Optional[str] = Query(None, description="Filter by archiver"),
    ai_suggested: Optional[bool] = Query(None, description="Filter by AI suggestion"),
    obsidian_synced: Optional[bool] = Query(None, description="Filter by Obsidian sync status"),
    min_quality_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum quality score"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    current_user: dict = Depends(get_current_user)
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
            min_quality_score=min_quality_score
        )

        response = await kanban_archive_service.get_archive_list(
            filters=filters,
            page=page,
            per_page=per_page
        )

        return response

    except Exception as e:
        return error_response(
            code="ARCHIVE_LIST_FAILED",
            message=f"Failed to retrieve archive list: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# 3. Get Specific Archived Task
# ============================================================================

@router.get(
    "/{task_id}",
    response_model=ArchivedTaskWithMetrics,
    dependencies=[Depends(require_role(UserRole.VIEWER))],
    summary="Get specific archived task",
    description="Get detailed information about a specific archived task"
)
async def get_archived_task(
    task_id: UUID,
    current_user: dict = Depends(get_current_user)
):
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
                details={"task_id": str(task_id)}
            )

        return archived_task

    except Exception as e:
        return error_response(
            code="ARCHIVED_TASK_RETRIEVAL_FAILED",
            message=f"Failed to retrieve archived task: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"task_id": str(task_id)}
        )


# ============================================================================
# 4. Get ROI Statistics (Optional Endpoint)
# ============================================================================

@router.get(
    "/statistics/roi",
    dependencies=[Depends(require_role(UserRole.VIEWER))],
    summary="Get ROI statistics",
    description="Get aggregated ROI statistics across all archived tasks"
)
async def get_roi_statistics(
    phase: Optional[str] = Query(None, description="Filter by phase"),
    current_user: dict = Depends(get_current_user)
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
            filters=filters,
            page=1,
            per_page=1000  # Get all for statistics
        )

        return response.roi_statistics

    except Exception as e:
        return error_response(
            code="ROI_STATISTICS_FAILED",
            message=f"Failed to calculate ROI statistics: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
