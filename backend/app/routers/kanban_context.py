"""
Kanban Context API Router

Week 2 Day 5: 3 API endpoints for context management.
Implements Q4 (Double-click auto-load, single-click popup)
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from backend.app.core.security import require_role, UserRole, get_current_user
from backend.app.services.kanban_context_service import kanban_context_service
from backend.app.models.kanban_context import (
    ContextMetadata,
    TaskContext,
    ContextUploadRequest,
    ContextLoadRequest,
    ContextUploadResponse,
    ContextLoadResponse,
    ContextNotFoundError,
    ContextSizeLimitExceeded,
    InvalidContextFiles,
)

router = APIRouter(prefix="/api/kanban/context", tags=["Kanban Context"])


# ============================================================================
# Error Response Helper
# ============================================================================

def error_response(code: str, message: str, status_code: int, details: dict = None):
    """Standard error response format"""
    from datetime import datetime
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    )


# ============================================================================
# Context Operations (3 endpoints)
# ============================================================================

@router.get(
    "/{task_id}",
    response_model=ContextMetadata,
    dependencies=[Depends(require_role(UserRole.VIEWER))],
    summary="Get context metadata",
    description="Get context metadata without full files list (Q4: Context info)"
)
async def get_context_metadata(
    task_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get context metadata for task.

    **RBAC**: Requires `viewer` role or higher.
    **Q4**: Returns metadata for single-click popup.
    **Returns**: ContextMetadata without full files array.
    """
    try:
        metadata = await kanban_context_service.get_context_metadata(task_id)

        if not metadata:
            return error_response(
                code="CONTEXT_NOT_FOUND",
                message=f"No context found for task {task_id}",
                status_code=status.HTTP_404_NOT_FOUND,
                details={"task_id": str(task_id)}
            )

        return metadata

    except Exception as e:
        return error_response(
            code="GET_CONTEXT_FAILED",
            message=f"Failed to get context metadata: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post(
    "/{task_id}",
    response_model=ContextUploadResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Upload context as ZIP",
    description="Upload context files as ZIP (<50MB limit)"
)
async def upload_context(
    task_id: UUID,
    upload_request: ContextUploadRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Upload context for task as ZIP file.

    **RBAC**: Requires `developer` role or higher.
    **Q4**: ZIP will be auto-loaded on double-click.
    **Limit**: Max 50MB ZIP size.

    Process:
    1. Validate files list (min 1 file)
    2. Create ZIP from files (mock: estimate size)
    3. Upload to storage (mock: generate URL)
    4. Store metadata in database
    5. Return ZIP URL and checksum
    """
    try:
        upload_response = await kanban_context_service.upload_context(
            task_id, upload_request
        )
        return upload_response

    except ContextSizeLimitExceeded as e:
        return error_response(
            code="CONTEXT_SIZE_LIMIT_EXCEEDED",
            message=str(e),
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            details={"task_id": str(task_id), "limit_bytes": 52428800}
        )

    except InvalidContextFiles as e:
        return error_response(
            code="INVALID_CONTEXT_FILES",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"task_id": str(task_id)}
        )

    except Exception as e:
        return error_response(
            code="UPLOAD_CONTEXT_FAILED",
            message=f"Failed to upload context: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post(
    "/{task_id}/load",
    response_model=ContextLoadResponse,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Track context load (Q4 double-click)",
    description="Track context load event (Q4: load_count, avg_load_time_ms)"
)
async def track_context_load(
    task_id: UUID,
    load_request: ContextLoadRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Track context load event (Q4: Double-click auto-load tracking).

    **RBAC**: Requires `developer` role or higher.
    **Q4**: Increments load_count, updates avg_load_time_ms.

    Process:
    1. Find context for task
    2. Increment load_count
    3. Update avg_load_time_ms: (old_avg * old_count + new_time) / new_count
    4. Update last_loaded_at timestamp
    5. Return updated stats
    """
    try:
        load_response = await kanban_context_service.track_context_load(
            task_id, load_request
        )
        return load_response

    except ContextNotFoundError as e:
        return error_response(
            code="CONTEXT_NOT_FOUND",
            message=str(e),
            status_code=status.HTTP_404_NOT_FOUND,
            details={"task_id": str(task_id)}
        )

    except Exception as e:
        return error_response(
            code="TRACK_LOAD_FAILED",
            message=f"Failed to track context load: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# Additional Endpoint: Get Full Context (with files list)
# ============================================================================

@router.get(
    "/{task_id}/full",
    response_model=TaskContext,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Get full context with files list",
    description="Get complete context including all file paths (developer+ only)"
)
async def get_context_full(
    task_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get full context including files array.

    **RBAC**: Requires `developer` role or higher.
    **Returns**: Full TaskContext with files array.
    **Use case**: Download context for local development.
    """
    try:
        context = await kanban_context_service.get_context_full(task_id)

        if not context:
            return error_response(
                code="CONTEXT_NOT_FOUND",
                message=f"No context found for task {task_id}",
                status_code=status.HTTP_404_NOT_FOUND,
                details={"task_id": str(task_id)}
            )

        return context

    except Exception as e:
        return error_response(
            code="GET_FULL_CONTEXT_FAILED",
            message=f"Failed to get full context: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
