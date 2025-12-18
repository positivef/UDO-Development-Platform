"""
Project Context Router

API endpoints for project context management and project switching.
"""

import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, Depends, status

from app.models.project_context import (
    ProjectContextCreate,
    ProjectContextUpdate,
    ProjectContextResponse,
    ProjectSwitchRequest,
    ProjectSwitchResponse,
    ProjectsListResponse,
    ProjectListResponse
)
from app.services.project_context_service import get_project_context_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/project-context",
    tags=["Project Context"]
)

projects_router = APIRouter(
    prefix="/api/projects",
    tags=["Projects"]
)


# ============================================================
# Dependency: Get Service
# ============================================================

def get_service():
    """Dependency to get project context service"""
    logger.info(f"[DEBUG] get_service() called")

    service = get_project_context_service()
    logger.info(f"[DEBUG] get_project_context_service() returned: {type(service) if service else 'None'}")

    if not service:
        # Try to enable mock service as fallback
        try:
            logger.info("[DEBUG] Attempting to enable mock service as fallback")
            from app.services.project_context_service import enable_mock_service, _use_mock_service, _mock_service_instance
            logger.info(f"[DEBUG] Before enable: _use_mock_service={_use_mock_service}, _mock_service_instance={type(_mock_service_instance) if _mock_service_instance else 'None'}")

            enable_mock_service()
            service = get_project_context_service()

            logger.info(f"[DEBUG] After enable: service={type(service) if service else 'None'}")
            logger.info("✅ Mock service enabled as fallback")
        except Exception as e:
            logger.error(f"Failed to enable mock service: {e}")
            import traceback
            traceback.print_exc()

        if not service:
            logger.error("Project context service not initialized")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Project context service not initialized"
            )
    return service


# ============================================================
# Project Context Endpoints
# ============================================================

@router.post("/save", response_model=ProjectContextResponse, status_code=status.HTTP_200_OK)
async def save_project_context(
    context_data: ProjectContextCreate,
    service=Depends(get_service)
) -> ProjectContextResponse:
    """
    Save or update project context.

    **Request Body:**
    - project_id: UUID of the project
    - udo_state: UDO system state (decision, confidence, quantum state, etc.)
    - ml_models: ML model paths and configurations
    - recent_executions: List of recent task executions (max 10)
    - ai_preferences: AI service preferences (model, temperature, etc.)
    - editor_state: Editor state (open files, cursor positions, etc.)

    **Response:** Complete saved context with timestamps
    """
    try:
        logger.info(f"💾 Saving context for project {context_data.project_id}")

        result = await service.save_context(
            project_id=context_data.project_id,
            udo_state=context_data.udo_state.model_dump() if context_data.udo_state else None,
            ml_models=context_data.ml_models.model_dump() if context_data.ml_models else None,
            recent_executions=[e.model_dump() for e in context_data.recent_executions] if context_data.recent_executions else None,
            ai_preferences=context_data.ai_preferences.model_dump() if context_data.ai_preferences else None,
            editor_state=context_data.editor_state.model_dump() if context_data.editor_state else None
        )

        return ProjectContextResponse(**result)

    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to save context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save project context: {str(e)}"
        )


@router.get("/load/{project_id}", response_model=ProjectContextResponse)
async def load_project_context(
    project_id: UUID,
    service=Depends(get_service)
) -> ProjectContextResponse:
    """
    Load project context for a specific project.

    Updates the `loaded_at` timestamp when context is retrieved.

    **Path Parameters:**
    - project_id: UUID of the project

    **Response:** Complete project context or 404 if not found
    """
    try:
        logger.info(f"📂 Loading context for project {project_id}")

        result = await service.load_context(project_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No context found for project {project_id}"
            )

        return ProjectContextResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to load context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load project context: {str(e)}"
        )


@router.patch("/update/{project_id}", response_model=ProjectContextResponse)
async def update_project_context(
    project_id: UUID,
    context_update: ProjectContextUpdate,
    service=Depends(get_service)
) -> ProjectContextResponse:
    """
    Partially update project context (merge with existing).

    Only updates the fields provided in the request body.
    Keeps all other fields unchanged.

    **Path Parameters:**
    - project_id: UUID of the project

    **Request Body:** Any subset of context fields to update

    **Response:** Complete updated context
    """
    try:
        logger.info(f"🔄 Updating context for project {project_id}")

        # Prepare partial update
        partial_context = {}

        if context_update.udo_state:
            partial_context["udo_state"] = context_update.udo_state.model_dump()
        if context_update.ml_models:
            partial_context["ml_models"] = context_update.ml_models.model_dump()
        if context_update.recent_executions:
            partial_context["recent_executions"] = [e.model_dump() for e in context_update.recent_executions]
        if context_update.ai_preferences:
            partial_context["ai_preferences"] = context_update.ai_preferences.model_dump()
        if context_update.editor_state:
            partial_context["editor_state"] = context_update.editor_state.model_dump()

        result = await service.merge_context(project_id, partial_context)

        return ProjectContextResponse(**result)

    except Exception as e:
        logger.error(f"❌ Failed to update context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project context: {str(e)}"
        )


@router.delete("/delete/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_context(
    project_id: UUID,
    service=Depends(get_service)
):
    """
    Delete project context.

    **Path Parameters:**
    - project_id: UUID of the project

    **Response:** 204 No Content on success
    """
    try:
        logger.info(f"🗑️ Deleting context for project {project_id}")

        deleted = await service.delete_context(project_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No context found for project {project_id}"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project context: {str(e)}"
        )


@router.post("/switch", response_model=ProjectSwitchResponse)
async def switch_project(
    switch_request: ProjectSwitchRequest,
    service=Depends(get_service)
) -> ProjectSwitchResponse:
    """
    Switch to a different project with context auto-loading.

    **Workflow:**
    1. Optionally save current project context
    2. Load target project context
    3. Update current active project
    4. Return loaded context

    **Request Body:**
    - project_id: Target project UUID
    - auto_save_current: Whether to save current project before switching (default: true)

    **Response:** Switch result with loaded context
    """
    try:
        logger.info(f"🔄 Switching to project {switch_request.project_id}")

        result = await service.switch_project(
            target_project_id=switch_request.project_id,
            auto_save_current=switch_request.auto_save_current
        )

        return ProjectSwitchResponse(**result)

    except ValueError as e:
        logger.error(f"❌ Invalid project: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to switch project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to switch project: {str(e)}"
        )


# ============================================================
# Projects List Endpoints
# ============================================================

@projects_router.get("", response_model=ProjectsListResponse)
async def list_projects(
    include_archived: bool = Query(False, description="Include archived projects"),
    limit: int = Query(50, ge=1, le=100, description="Max projects to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service=Depends(get_service)
) -> ProjectsListResponse:
    """
    List all projects with context availability status.

    **Query Parameters:**
    - include_archived: Include archived projects (default: false)
    - limit: Max number of projects to return (1-100, default: 50)
    - offset: Pagination offset (default: 0)

    **Response:** List of projects sorted by last_active_at (most recent first)
    """
    try:
        logger.info(f"📋 Listing projects (limit={limit}, offset={offset})")

        result = await service.list_projects(
            include_archived=include_archived,
            limit=limit,
            offset=offset
        )

        return ProjectsListResponse(**result)

    except Exception as e:
        logger.error(f"❌ Failed to list projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list projects: {str(e)}"
        )


@projects_router.get("/current", response_model=Optional[ProjectListResponse])
async def get_current_project(
    service=Depends(get_service)
) -> Optional[ProjectListResponse]:
    """
    Get the currently active project.

    **Response:** Current project info or null if no project is active
    """
    try:
        logger.info("📍 Getting current project")

        result = await service.get_current_project()

        if not result:
            return None

        return ProjectListResponse(**result)

    except Exception as e:
        logger.error(f"❌ Failed to get current project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current project: {str(e)}"
        )


# Export routers
__all__ = ["router", "projects_router"]
