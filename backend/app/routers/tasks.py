"""
Task Management Router

[EMOJI](Task) [EMOJI] [EMOJI] [EMOJI] [EMOJI].
CLI [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI].
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
import logging

from app.services.task_service import task_service, TaskStatus, TodoStatus

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/tasks",
    tags=["Tasks"],
    responses={
        404: {"description": "Task not found"},
        500: {"description": "Internal server error"}
    }
)


# Request/Response models
class TaskSummary(BaseModel):
    """[EMOJI] [EMOJI] [EMOJI]"""
    id: str
    title: str
    description: str
    project: str
    project_id: str
    phase: str
    status: str
    current_step: Dict[str, Any]
    completeness: int
    estimated_hours: float
    actual_hours: float
    git_branch: str
    updated_at: str


class TodoGroup(BaseModel):
    """TODO [EMOJI]"""
    id: str
    title: str
    status: str
    order: int
    items: List[Dict[str, Any]]


class TaskDetail(BaseModel):
    """[EMOJI] [EMOJI] [EMOJI]"""
    id: str
    title: str
    description: str
    project: str
    project_id: str
    phase: str
    status: str
    todo_groups: List[TodoGroup]
    current_step: Dict[str, Any]
    completeness: int
    estimated_hours: float
    actual_hours: float
    git_branch: str
    last_commit: Optional[str]
    created_at: str
    updated_at: str


class TaskContext(BaseModel):
    """[EMOJI] [EMOJI] (CLI [EMOJI])"""
    task_id: str
    title: str
    description: str
    project: str
    phase: str
    status: str
    current_todo: Optional[Dict[str, Any]]
    git_branch: Optional[str]
    files: List[str]
    prompt_history: List[str]
    checkpoint: Optional[Dict[str, Any]]
    command: str
    updated_at: str


class CreateTaskRequest(BaseModel):
    """[EMOJI] [EMOJI] [EMOJI]"""
    title: str = Field(..., description="[EMOJI] [EMOJI]")
    description: str = Field(..., description="[EMOJI] [EMOJI]")
    project: str = Field(..., description="[EMOJI] [EMOJI]")
    project_id: str = Field(..., description="[EMOJI] ID")
    phase: str = Field("planning", description="[EMOJI] [EMOJI]")
    estimated_hours: float = Field(8, description="[EMOJI] [EMOJI]")
    git_branch: Optional[str] = Field(None, description="Git [EMOJI]")


class UpdateProgressRequest(BaseModel):
    """[EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
    status: Optional[str] = Field(None, description="[EMOJI] [EMOJI]")
    completeness: Optional[int] = Field(None, description="[EMOJI] (0-100)")
    actual_hours: Optional[float] = Field(None, description="[EMOJI] [EMOJI] [EMOJI]")
    current_step: Optional[Dict[str, Any]] = Field(None, description="[EMOJI] [EMOJI]")
    todo_update: Optional[Dict[str, Any]] = Field(None, description="TODO [EMOJI]")


class SaveContextRequest(BaseModel):
    """[EMOJI] [EMOJI] [EMOJI]"""
    files: Optional[List[str]] = Field(None, description="[EMOJI] [EMOJI] [EMOJI]")
    prompt_history: Optional[List[str]] = Field(None, description="[EMOJI] [EMOJI]")
    checkpoint: Optional[Dict[str, Any]] = Field(None, description="[EMOJI]")
    git_branch: Optional[str] = Field(None, description="Git [EMOJI]")


@router.get("/", response_model=List[TaskSummary])
async def list_tasks(
    project_id: Optional[str] = Query(None, description="[EMOJI] ID[EMOJI] [EMOJI]"),
    status: Optional[str] = Query(None, description="[EMOJI] [EMOJI]"),
    phase: Optional[str] = Query(None, description="[EMOJI] [EMOJI]")
):
    """
    [EMOJI] [EMOJI] [EMOJI]

    [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI].
    [EMOJI], [EMOJI], [EMOJI] [EMOJI] [EMOJI] [EMOJI].
    """
    try:
        tasks = await task_service.list_tasks(
            project_id=project_id,
            status=status,
            phase=phase
        )

        # TaskSummary [EMOJI] [EMOJI]
        summaries = []
        for task in tasks:
            summaries.append(TaskSummary(
                id=task["id"],
                title=task["title"],
                description=task["description"],
                project=task["project"],
                project_id=task["project_id"],
                phase=task["phase"],
                status=task["status"],
                current_step=task["current_step"],
                completeness=task["completeness"],
                estimated_hours=task.get("estimated_hours", 0),
                actual_hours=task.get("actual_hours", 0),
                git_branch=task.get("git_branch", ""),
                updated_at=task["updated_at"]
            ))

        logger.info(f"Listed {len(summaries)} tasks")
        return summaries

    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tasks"
        )


@router.get("/{task_id}", response_model=TaskDetail)
async def get_task(task_id: str):
    """
    [EMOJI] [EMOJI] [EMOJI] [EMOJI]

    [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI].
    TODO [EMOJI], [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI].
    """
    try:
        task = await task_service.get_task(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        return TaskDetail(**task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task"
        )


@router.get("/{task_id}/context", response_model=TaskContext)
async def get_task_context(task_id: str):
    """
    [EMOJI] [EMOJI] [EMOJI] (CLI [EMOJI])

    CLI[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI].
    [EMOJI] [EMOJI] [EMOJI] TODO, [EMOJI] [EMOJI], Git [EMOJI], [EMOJI] [EMOJI] [EMOJI] [EMOJI].
    """
    try:
        context = await task_service.get_task_context(task_id)

        if not context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        return TaskContext(**context)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task context {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task context"
        )


@router.post("/", response_model=Dict[str, str])
async def create_task(request: CreateTaskRequest):
    """
    [EMOJI] [EMOJI] [EMOJI]

    [EMOJI] [EMOJI] [EMOJI] [EMOJI].
    """
    try:
        task_data = request.dict(exclude_none=True)

        # [EMOJI] TODO [EMOJI] [EMOJI]
        if "todo_groups" not in task_data:
            task_data["todo_groups"] = [
                {
                    "id": "group-planning",
                    "title": "1. Planning",
                    "status": "pending",
                    "order": 1,
                    "items": []
                },
                {
                    "id": "group-implementation",
                    "title": "2. Implementation",
                    "status": "pending",
                    "order": 2,
                    "items": []
                },
                {
                    "id": "group-testing",
                    "title": "3. Testing",
                    "status": "pending",
                    "order": 3,
                    "items": []
                }
            ]

        task_id = await task_service.create_task(task_data)

        logger.info(f"Created new task: {task_id}")
        return {"task_id": task_id, "message": "Task created successfully"}

    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task"
        )


@router.put("/{task_id}/progress")
async def update_task_progress(
    task_id: str,
    request: UpdateProgressRequest
):
    """
    [EMOJI] [EMOJI] [EMOJI] [EMOJI]

    [EMOJI] [EMOJI] [EMOJI], TODO [EMOJI] [EMOJI] [EMOJI].
    """
    try:
        progress = request.dict(exclude_none=True)

        success = await task_service.update_task_progress(task_id, progress)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        # [EMOJI] [EMOJI]
        completeness = await task_service.calculate_completeness(task_id)
        await task_service.update_task_progress(
            task_id,
            {"completeness": completeness}
        )

        return {"message": "Task progress updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update task progress {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task progress"
        )


@router.put("/{task_id}/context")
async def save_task_context(
    task_id: str,
    request: SaveContextRequest
):
    """
    [EMOJI] [EMOJI] [EMOJI]

    CLI [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI].
    """
    try:
        context = request.dict(exclude_none=True)

        success = await task_service.save_task_context(task_id, context)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        return {"message": "Task context saved successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save task context {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save task context"
        )


@router.get("/stats/summary")
async def get_task_statistics():
    """
    [EMOJI] [EMOJI] [EMOJI]

    [EMOJI] [EMOJI] [EMOJI] [EMOJI].
    """
    try:
        tasks = await task_service.list_tasks()

        stats = {
            "total": len(tasks),
            "by_status": {},
            "by_phase": {},
            "active_count": task_service.get_active_task_count(),
            "blocked_count": task_service.get_blocked_task_count()
        }

        # [EMOJI] [EMOJI]
        for task in tasks:
            status = task.get("status", "unknown")
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

            phase = task.get("phase", "unknown")
            stats["by_phase"][phase] = stats["by_phase"].get(phase, 0) + 1

        return stats

    except Exception as e:
        logger.error(f"Failed to get task statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task statistics"
        )


# Export router
__all__ = ['router']