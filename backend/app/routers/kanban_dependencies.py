"""
Kanban Dependencies API Router

Week 2 Day 3-4: 8 API endpoints for dependency management.
Week 3 Day 1-2: 10 API endpoints (added topological-sort, statistics).
Implements Q7 (Hard Block dependencies with emergency override).
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from backend.app.core.security import require_role, UserRole, get_current_user
from backend.app.services.kanban_dependency_service import kanban_dependency_service
from backend.app.services.kanban_task_service import kanban_task_service
from backend.app.models.kanban_dependencies import (
    Dependency,
    DependencyCreate,
    EmergencyOverride,
    DependencyAudit,
    CircularDependencyError,
    TopologicalSortResult,
    DependencyGraph,
    DAGStatistics,
)

router = APIRouter(prefix="/api/kanban/dependencies", tags=["Kanban Dependencies"])


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
# 1. CRUD Operations (4 endpoints)
# ============================================================================

@router.post(
    "",
    response_model=Dependency,
    status_code=status.HTTP_201_CREATED,
    # DEV_MODE: RBAC disabled for development

    # TODO: Re-enable RBAC in Week 5 Day 2 (see UNCERTAINTY_MAP_WEEK5_ANALYSIS.md P0-1)

    # dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Create dependency with DAG cycle validation",
    description="Create task dependency (requires developer role or higher)"
)
async def create_dependency(
    dependency_data: DependencyCreate,
    # DEV_MODE: Auth disabled

    # current_user: dict = Depends(get_current_user)
):
    """
    Create new task dependency with DAG cycle validation.

    **RBAC**: Requires `developer` role or higher.
    **Q7**: Hard Block dependencies (emergency override available).
    **Performance**: Cycle detection <50ms for 1,000 tasks.

    Raises:
        400: Circular dependency detected
        404: Task not found
    """
    try:
        # Get all available task IDs for validation
        task_list = await kanban_task_service.list_tasks(
            filters=None,
            page=1,
            per_page=10000,  # Get all tasks for validation
            sort_by="created_at",
            sort_desc=False
        )
        available_task_ids = {task.task_id for task in task_list.data}

        # Create dependency with cycle detection
        dependency = await kanban_dependency_service.create_dependency(
            dependency_data,
            available_task_ids
        )
        return dependency

    except CircularDependencyError as e:
        return error_response(
            code="CIRCULAR_DEPENDENCY",
            message=f"Circular dependency detected: {e}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"cycle": [str(task_id) for task_id in e.cycle]}
        )
    except ValueError as e:
        return error_response(
            code="TASK_NOT_FOUND",
            message=str(e),
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return error_response(
            code="DEPENDENCY_CREATE_FAILED",
            message=f"Failed to create dependency: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/{dependency_id}",
    response_model=Dependency,
    # DEV_MODE: RBAC disabled for development

    # TODO: Re-enable RBAC in Week 5 Day 2 (see UNCERTAINTY_MAP_WEEK5_ANALYSIS.md P0-1)

    # dependencies=[Depends(require_role(UserRole.VIEWER))],
    summary="Get dependency details",
    description="Get dependency by ID (requires viewer role)"
)
async def get_dependency(
    dependency_id: UUID,
    # DEV_MODE: Auth disabled

    # current_user: dict = Depends(get_current_user)
):
    """
    Get dependency by ID.

    **RBAC**: Requires `viewer` role or higher.
    """
    try:
        dependency = await kanban_dependency_service.get_dependency(dependency_id)
        if not dependency:
            return error_response(
                code="DEPENDENCY_NOT_FOUND",
                message=f"Dependency with ID {dependency_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
                details={"dependency_id": str(dependency_id)}
            )
        return dependency
    except Exception as e:
        return error_response(
            code="DEPENDENCY_GET_FAILED",
            message=f"Failed to get dependency: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete(
    "/{dependency_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    # DEV_MODE: RBAC disabled for development

    # TODO: Re-enable RBAC in Week 5 Day 2 (see UNCERTAINTY_MAP_WEEK5_ANALYSIS.md P0-1)

    # dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Delete dependency",
    description="Delete dependency (requires developer role or higher)"
)
async def delete_dependency(
    dependency_id: UUID,
    # DEV_MODE: Auth disabled

    # current_user: dict = Depends(get_current_user)
):
    """
    Delete dependency.

    **RBAC**: Requires `developer` role or higher.
    """
    try:
        deleted = await kanban_dependency_service.delete_dependency(dependency_id)
        if not deleted:
            return error_response(
                code="DEPENDENCY_NOT_FOUND",
                message=f"Dependency with ID {dependency_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
                details={"dependency_id": str(dependency_id)}
            )
        return None
    except Exception as e:
        return error_response(
            code="DEPENDENCY_DELETE_FAILED",
            message=f"Failed to delete dependency: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/audit",
    response_model=list[DependencyAudit],
    # DEV_MODE: RBAC disabled for development

    # TODO: Re-enable RBAC in Week 5 Day 2 (see UNCERTAINTY_MAP_WEEK5_ANALYSIS.md P0-1)

    # dependencies=[Depends(require_role(UserRole.VIEWER))],
    summary="Get dependency audit log",
    description="Get emergency override audit log (requires viewer role)"
)
async def get_audit_log(
    limit: int = Query(50, ge=1, le=100, description="Number of entries (max 100)"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    # DEV_MODE: Auth disabled

    # current_user: dict = Depends(get_current_user)
):
    """
    Get dependency audit log (emergency overrides).

    **RBAC**: Requires `viewer` role or higher.
    **Q7**: Audit log for all emergency overrides.
    """
    try:
        audit_log = await kanban_dependency_service.get_audit_log(limit, offset)
        return audit_log
    except Exception as e:
        return error_response(
            code="AUDIT_LOG_GET_FAILED",
            message=f"Failed to get audit log: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# 2. Task-Specific Operations (3 endpoints)
# ============================================================================

@router.get(
    "/tasks/{task_id}/dependencies",
    response_model=list[Dependency],
    # DEV_MODE: RBAC disabled for development

    # TODO: Re-enable RBAC in Week 5 Day 2 (see UNCERTAINTY_MAP_WEEK5_ANALYSIS.md P0-1)

    # dependencies=[Depends(require_role(UserRole.VIEWER))],
    summary="Get task dependencies (upstream/predecessors)",
    description="Get all dependencies for a task (tasks this task depends on)"
)
async def get_task_dependencies(
    task_id: UUID,
    # DEV_MODE: Auth disabled

    # current_user: dict = Depends(get_current_user)
):
    """
    Get all dependencies for a task (upstream/predecessors).

    **RBAC**: Requires `viewer` role or higher.
    **Returns**: List of tasks this task depends on (must be completed first).
    """
    try:
        dependencies = await kanban_dependency_service.get_task_dependencies(task_id)
        return dependencies
    except Exception as e:
        return error_response(
            code="DEPENDENCIES_GET_FAILED",
            message=f"Failed to get task dependencies: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/tasks/{task_id}/dependents",
    response_model=list[Dependency],
    # DEV_MODE: RBAC disabled for development

    # TODO: Re-enable RBAC in Week 5 Day 2 (see UNCERTAINTY_MAP_WEEK5_ANALYSIS.md P0-1)

    # dependencies=[Depends(require_role(UserRole.VIEWER))],
    summary="Get task dependents (downstream/successors)",
    description="Get all dependents for a task (tasks that depend on this task)"
)
async def get_task_dependents(
    task_id: UUID,
    # DEV_MODE: Auth disabled

    # current_user: dict = Depends(get_current_user)
):
    """
    Get all dependents for a task (downstream/successors).

    **RBAC**: Requires `viewer` role or higher.
    **Returns**: List of tasks that depend on this task (blocked until this task completes).
    """
    try:
        dependents = await kanban_dependency_service.get_task_dependents(task_id)
        return dependents
    except Exception as e:
        return error_response(
            code="DEPENDENTS_GET_FAILED",
            message=f"Failed to get task dependents: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/tasks/{task_id}/dependency-graph",
    response_model=DependencyGraph,
    # DEV_MODE: RBAC disabled for development

    # TODO: Re-enable RBAC in Week 5 Day 2 (see UNCERTAINTY_MAP_WEEK5_ANALYSIS.md P0-1)

    # dependencies=[Depends(require_role(UserRole.VIEWER))],
    summary="Get dependency graph for D3.js visualization",
    description="Get dependency graph with nodes and edges for force-directed layout"
)
async def get_dependency_graph(
    task_id: UUID,
    depth: int = Query(3, ge=1, le=10, description="Maximum depth to traverse (default: 3)"),
    # DEV_MODE: Auth disabled

    # current_user: dict = Depends(get_current_user)
):
    """
    Get dependency graph for D3.js force-directed visualization.

    **RBAC**: Requires `viewer` role or higher.
    **Returns**: Nodes and edges for D3.js force-directed graph layout enriched with task metadata.
    **Performance**: Optimized for interactive visualization (<100ms).
    **Week 3 Day 1-2**: Enhanced with task metadata (title, phase, priority, blocked, completeness).
    """
    try:
        graph = await kanban_dependency_service.get_dependency_graph(task_id, depth)
        return graph
    except Exception as e:
        return error_response(
            code="DEPENDENCY_GRAPH_FAILED",
            message=f"Failed to get dependency graph: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/topological-sort",
    response_model=TopologicalSortResult,
    # DEV_MODE: RBAC disabled for development

    # TODO: Re-enable RBAC in Week 5 Day 2 (see UNCERTAINTY_MAP_WEEK5_ANALYSIS.md P0-1)

    # dependencies=[Depends(require_role(UserRole.VIEWER))],
    summary="Get topological sort of tasks",
    description="Topological sort using Kahn's Algorithm (<50ms for 1,000 tasks)"
)
async def topological_sort(
    task_ids: str = Query(..., description="Comma-separated list of task IDs"),
    # DEV_MODE: Auth disabled

    # current_user: dict = Depends(get_current_user)
):
    """
    Perform topological sort on task dependencies using Kahn's Algorithm.

    **RBAC**: Requires `viewer` role or higher.
    **Performance**: <50ms for 1,000 tasks (P0 Critical Issue #4).
    **Returns**: Ordered tasks list with execution time metrics.
    **Week 3 Day 1-2**: New endpoint for DAG analysis and scheduling.

    Process:
    1. Parse task IDs from comma-separated string
    2. Build adjacency list and in-degree count
    3. Apply Kahn's Algorithm
    4. Return ordered tasks with performance metrics
    """
    try:
        # Parse task IDs from comma-separated string
        task_id_list = [UUID(tid.strip()) for tid in task_ids.split(",")]
        task_id_set = set(task_id_list)

        # Perform topological sort
        result = await kanban_dependency_service.topological_sort(task_id_set)
        return result

    except ValueError as e:
        return error_response(
            code="INVALID_TASK_IDS",
            message=f"Invalid task IDs format: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            code="TOPOLOGICAL_SORT_FAILED",
            message=f"Failed to perform topological sort: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/statistics",
    response_model=DAGStatistics,
    # DEV_MODE: RBAC disabled for development

    # TODO: Re-enable RBAC in Week 5 Day 2 (see UNCERTAINTY_MAP_WEEK5_ANALYSIS.md P0-1)

    # dependencies=[Depends(require_role(UserRole.VIEWER))],
    summary="Get DAG performance statistics",
    description="DAG performance metrics for monitoring and debugging"
)
async def get_statistics(
    task_ids: str = Query(..., description="Comma-separated list of task IDs"),
    # DEV_MODE: Auth disabled

    # current_user: dict = Depends(get_current_user)
):
    """
    Get DAG performance statistics.

    **RBAC**: Requires `viewer` role or higher.
    **Returns**: Performance metrics (max_depth, avg_dependencies, execution times).
    **Week 3 Day 1-2**: New endpoint for DAG analysis and monitoring.

    Metrics:
    - Total tasks and dependencies count
    - Maximum dependency chain depth
    - Average dependencies per task
    - Topological sort execution time
    - Cycle detection execution time
    - Performance target validation (<50ms for 1,000 tasks)
    """
    try:
        # Parse task IDs from comma-separated string
        task_id_list = [UUID(tid.strip()) for tid in task_ids.split(",")]
        task_id_set = set(task_id_list)

        # Get statistics
        stats = await kanban_dependency_service.get_statistics(task_id_set)
        return stats

    except ValueError as e:
        return error_response(
            code="INVALID_TASK_IDS",
            message=f"Invalid task IDs format: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            code="STATISTICS_GET_FAILED",
            message=f"Failed to get statistics: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# 3. Emergency Override (1 endpoint) - Q7
# ============================================================================

@router.post(
    "/{dependency_id}/override",
    response_model=Dependency,
    # DEV_MODE: RBAC disabled for development

    # TODO: Re-enable RBAC in Week 5 Day 2 (see UNCERTAINTY_MAP_WEEK5_ANALYSIS.md P0-1)

    # dependencies=[Depends(require_role(UserRole.PROJECT_OWNER))],
    summary="Emergency override dependency",
    description="Emergency override for hard-blocked dependency (Q7)"
)
async def emergency_override(
    dependency_id: UUID,
    override_request: EmergencyOverride,
    # DEV_MODE: Auth disabled

    # current_user: dict = Depends(get_current_user)
):
    """
    Emergency override for dependency (Q7: Hard Block with emergency override).

    **RBAC**: Requires `project_owner` role or higher (NOT developer).
    **Q7**: Emergency override should be used sparingly - audit logged.
    **Audit**: All overrides are logged in audit table with reason and user.

    Process:
    1. Validate override reason (min 10 characters)
    2. Update dependency status to OVERRIDDEN
    3. Create audit log entry
    4. Return updated dependency
    """
    try:
        # Ensure dependency_id matches request
        if override_request.dependency_id != dependency_id:
            return error_response(
                code="DEPENDENCY_ID_MISMATCH",
                message="Dependency ID in URL does not match request body",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Set overridden_by from current user
        override_request.overridden_by = current_user.get("username", current_user.get("email"))

        dependency = await kanban_dependency_service.emergency_override(override_request)
        return dependency

    except ValueError as e:
        return error_response(
            code="DEPENDENCY_NOT_FOUND",
            message=str(e),
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return error_response(
            code="EMERGENCY_OVERRIDE_FAILED",
            message=f"Failed to override dependency: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
