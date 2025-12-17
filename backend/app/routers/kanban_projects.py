"""
Kanban Multi-Project API Router

Week 2 Day 3-4: 5 API endpoints for multi-project management.
Implements Q5 (1 Primary + max 3 Related projects per task).
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from backend.app.core.security import require_role, UserRole, get_current_user
from backend.app.services.kanban_project_service import kanban_project_service
from backend.app.models.kanban_task_project import (
    TaskProject,
    TaskProjectSummary,
    SetPrimaryProjectRequest,
    AddRelatedProjectRequest,
    RemoveRelatedProjectRequest,
    MaxRelatedProjectsError,
    NoPrimaryProjectError,
    MultiplePrimaryProjectsError,
)

router = APIRouter(prefix="/api/kanban/projects", tags=["Kanban Multi-Project"])


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
# 1. Project Management Operations (3 endpoints)
# ============================================================================

@router.post(
    "/set-primary",
    response_model=TaskProject,
    # DEV_MODE: RBAC disabled for development

    # TODO: Re-enable RBAC in Week 5 Day 2 (see UNCERTAINTY_MAP_WEEK5_ANALYSIS.md P0-1)

    # dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Set primary project for task",
    description="Set task's primary project (Q5: 1 Primary required)"
)
async def set_primary_project(
    request: SetPrimaryProjectRequest,
    # DEV_MODE: Auth disabled

    # current_user: dict = Depends(get_current_user)
):
    """
    Set primary project for a task (atomic operation).

    **RBAC**: Requires `developer` role or higher.
    **Q5**: Exactly 1 primary project required per task.
    **Atomicity**: Removes existing primary, sets new primary, validates.

    Process:
    1. Remove existing primary (if any)
    2. If new primary is in related projects, remove it from related
    3. Set new primary
    4. Validate exactly 1 primary exists
    """
    try:
        task_project = await kanban_project_service.set_primary_project(
            request.task_id,
            request.project_id
        )
        return task_project

    except MultiplePrimaryProjectsError as e:
        return error_response(
            code="MULTIPLE_PRIMARY_PROJECTS",
            message=str(e),
            status_code=status.HTTP_409_CONFLICT,
            details={"task_id": str(request.task_id)}
        )
    except Exception as e:
        return error_response(
            code="SET_PRIMARY_FAILED",
            message=f"Failed to set primary project: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post(
    "/add-related",
    response_model=TaskProject,
    # DEV_MODE: RBAC disabled for development

    # TODO: Re-enable RBAC in Week 5 Day 2 (see UNCERTAINTY_MAP_WEEK5_ANALYSIS.md P0-1)

    # dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Add related project to task",
    description="Add related project (Q5: max 3 related projects)"
)
async def add_related_project(
    request: AddRelatedProjectRequest,
    # DEV_MODE: Auth disabled

    # current_user: dict = Depends(get_current_user)
):
    """
    Add related project to task.

    **RBAC**: Requires `developer` role or higher.
    **Q5**: Maximum 3 related projects per task.
    **Validation**: Cannot be same as primary, no duplicates.
    """
    try:
        task_project = await kanban_project_service.add_related_project(
            request.task_id,
            request.project_id
        )
        return task_project

    except MaxRelatedProjectsError as e:
        return error_response(
            code="MAX_RELATED_PROJECTS",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"task_id": str(request.task_id), "max_related": 3}
        )
    except ValueError as e:
        return error_response(
            code="INVALID_RELATED_PROJECT",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"task_id": str(request.task_id), "project_id": str(request.project_id)}
        )
    except Exception as e:
        return error_response(
            code="ADD_RELATED_FAILED",
            message=f"Failed to add related project: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete(
    "/remove-related",
    status_code=status.HTTP_204_NO_CONTENT,
    # DEV_MODE: RBAC disabled for development

    # TODO: Re-enable RBAC in Week 5 Day 2 (see UNCERTAINTY_MAP_WEEK5_ANALYSIS.md P0-1)

    # dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Remove related project from task",
    description="Remove related project (cannot remove primary)"
)
async def remove_related_project(
    request: RemoveRelatedProjectRequest,
    # DEV_MODE: Auth disabled

    # current_user: dict = Depends(get_current_user)
):
    """
    Remove related project from task.

    **RBAC**: Requires `developer` role or higher.
    **Q5**: Cannot remove primary project (use set-primary to change it).
    """
    try:
        removed = await kanban_project_service.remove_related_project(
            request.task_id,
            request.project_id
        )

        if not removed:
            return error_response(
                code="RELATED_PROJECT_NOT_FOUND",
                message=f"Related project {request.project_id} not found for task {request.task_id}",
                status_code=status.HTTP_404_NOT_FOUND,
                details={"task_id": str(request.task_id), "project_id": str(request.project_id)}
            )

        return None

    except ValueError as e:
        return error_response(
            code="CANNOT_REMOVE_PRIMARY",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
            details={
                "task_id": str(request.task_id),
                "project_id": str(request.project_id),
                "suggestion": "Use /set-primary to change the primary project"
            }
        )
    except Exception as e:
        return error_response(
            code="REMOVE_RELATED_FAILED",
            message=f"Failed to remove related project: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# 2. Query Operations (2 endpoints)
# ============================================================================

@router.get(
    "/tasks/{task_id}/projects",
    response_model=TaskProjectSummary,
    # DEV_MODE: RBAC disabled for development

    # TODO: Re-enable RBAC in Week 5 Day 2 (see UNCERTAINTY_MAP_WEEK5_ANALYSIS.md P0-1)

    # dependencies=[Depends(require_role(UserRole.VIEWER))],
    summary="Get task's project relationships",
    description="Get primary and related projects for task (Q5 summary)"
)
async def get_task_projects(
    task_id: UUID,
    # DEV_MODE: Auth disabled

    # current_user: dict = Depends(get_current_user)
):
    """
    Get all project relationships for a task.

    **RBAC**: Requires `viewer` role or higher.
    **Returns**: Primary project + related projects (max 3).
    **Q5**: 1 Primary + max 3 Related.
    """
    try:
        summary = await kanban_project_service.get_task_projects(task_id)
        return summary

    except Exception as e:
        return error_response(
            code="GET_PROJECTS_FAILED",
            message=f"Failed to get task projects: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/tasks/{task_id}/projects/validate",
    # DEV_MODE: RBAC disabled for development

    # TODO: Re-enable RBAC in Week 5 Day 2 (see UNCERTAINTY_MAP_WEEK5_ANALYSIS.md P0-1)

    # dependencies=[Depends(require_role(UserRole.VIEWER))],
    summary="Validate task's project constraints",
    description="Validate Q5 constraints (1 Primary + max 3 Related)"
)
async def validate_task_projects(
    task_id: UUID,
    # DEV_MODE: Auth disabled

    # current_user: dict = Depends(get_current_user)
):
    """
    Validate all multi-project constraints for a task.

    **RBAC**: Requires `viewer` role or higher.
    **Q5 Constraints**:
    - Exactly 1 primary project
    - Maximum 3 related projects
    - No duplicate project IDs
    - Primary not in related projects

    Returns:
        Validation result with status and errors (if any)
    """
    try:
        validation_result = await kanban_project_service.validate_constraints(task_id)
        return validation_result

    except Exception as e:
        return error_response(
            code="VALIDATION_FAILED",
            message=f"Failed to validate task projects: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
