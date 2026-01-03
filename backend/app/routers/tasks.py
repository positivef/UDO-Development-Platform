"""
Task Management Router

작업(Task) 관리 관련 엔드포인트를 제공합니다.
CLI 통합을 위한 컨텍스트 정보도 제공합니다.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
import logging

from app.services.task_service import task_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/tasks",
    tags=["Tasks"],
    responses={404: {"description": "Task not found"}, 500: {"description": "Internal server error"}},
)


# Request/Response models
class TaskSummary(BaseModel):
    """작업 요약 정보"""

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
    """TODO 그룹"""

    id: str
    title: str
    status: str
    order: int
    items: List[Dict[str, Any]]


class TaskDetail(BaseModel):
    """작업 상세 정보"""

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
    """작업 컨텍스트 (CLI 연동용)"""

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
    """작업 생성 요청"""

    title: str = Field(..., description="작업 제목")
    description: str = Field(..., description="작업 설명")
    project: str = Field(..., description="프로젝트 이름")
    project_id: str = Field(..., description="프로젝트 ID")
    phase: str = Field("planning", description="개발 단계")
    estimated_hours: float = Field(8, description="예상 시간")
    git_branch: Optional[str] = Field(None, description="Git 브랜치")


class UpdateProgressRequest(BaseModel):
    """진행 상황 업데이트 요청"""

    status: Optional[str] = Field(None, description="작업 상태")
    completeness: Optional[int] = Field(None, description="완성도 (0-100)")
    actual_hours: Optional[float] = Field(None, description="실제 소요 시간")
    current_step: Optional[Dict[str, Any]] = Field(None, description="현재 단계")
    todo_update: Optional[Dict[str, Any]] = Field(None, description="TODO 업데이트")


class SaveContextRequest(BaseModel):
    """컨텍스트 저장 요청"""

    files: Optional[List[str]] = Field(None, description="관련 파일 목록")
    prompt_history: Optional[List[str]] = Field(None, description="프롬프트 히스토리")
    checkpoint: Optional[Dict[str, Any]] = Field(None, description="체크포인트")
    git_branch: Optional[str] = Field(None, description="Git 브랜치")


@router.get("/", response_model=List[TaskSummary])
async def list_tasks(
    project_id: Optional[str] = Query(None, description="프로젝트 ID로 필터링"),
    status: Optional[str] = Query(None, description="상태로 필터링"),
    phase: Optional[str] = Query(None, description="단계로 필터링"),
):
    """
    작업 목록 조회

    개발 중인 모든 작업을 목록으로 반환합니다.
    프로젝트, 상태, 단계별로 필터링할 수 있습니다.
    """
    try:
        tasks = await task_service.list_tasks(project_id=project_id, status=status, phase=phase)

        # TaskSummary 형태로 변환
        summaries = []
        for task in tasks:
            summaries.append(
                TaskSummary(
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
                    updated_at=task["updated_at"],
                )
            )

        logger.info(f"Listed {len(summaries)} tasks")
        return summaries

    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve tasks")


@router.get("/{task_id}", response_model=TaskDetail)
async def get_task(task_id: str):
    """
    작업 상세 정보 조회

    특정 작업의 상세 정보를 반환합니다.
    TODO 리스트, 진행 상황 등 모든 정보를 포함합니다.
    """
    try:
        task = await task_service.get_task(task_id)

        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found")

        return TaskDetail(**task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve task")


@router.get("/{task_id}/context", response_model=TaskContext)
async def get_task_context(task_id: str):
    """
    작업 컨텍스트 조회 (CLI 연동용)

    CLI에서 작업을 계속하기 위한 컨텍스트 정보를 반환합니다.
    현재 진행 중인 TODO, 관련 파일, Git 브랜치, 프롬프트 히스토리 등을 포함합니다.
    """
    try:
        context = await task_service.get_task_context(task_id)

        if not context:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found")

        return TaskContext(**context)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task context {task_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve task context")


@router.post("/", response_model=Dict[str, str])
async def create_task(request: CreateTaskRequest):
    """
    새 작업 생성

    새로운 개발 작업을 생성합니다.
    """
    try:
        task_data = request.dict(exclude_none=True)

        # 기본 TODO 그룹 생성
        if "todo_groups" not in task_data:
            task_data["todo_groups"] = [
                {"id": "group-planning", "title": "1. Planning", "status": "pending", "order": 1, "items": []},
                {"id": "group-implementation", "title": "2. Implementation", "status": "pending", "order": 2, "items": []},
                {"id": "group-testing", "title": "3. Testing", "status": "pending", "order": 3, "items": []},
            ]

        task_id = await task_service.create_task(task_data)

        logger.info(f"Created new task: {task_id}")
        return {"task_id": task_id, "message": "Task created successfully"}

    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create task")


@router.put("/{task_id}/progress")
async def update_task_progress(task_id: str, request: UpdateProgressRequest):
    """
    작업 진행 상황 업데이트

    작업의 진행 상황, TODO 상태 등을 업데이트합니다.
    """
    try:
        progress = request.dict(exclude_none=True)

        success = await task_service.update_task_progress(task_id, progress)

        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found")

        # 완성도 재계산
        completeness = await task_service.calculate_completeness(task_id)
        await task_service.update_task_progress(task_id, {"completeness": completeness})

        return {"message": "Task progress updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update task progress {task_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update task progress")


@router.put("/{task_id}/context")
async def save_task_context(task_id: str, request: SaveContextRequest):
    """
    작업 컨텍스트 저장

    CLI 작업 종료 시 컨텍스트를 저장하여 나중에 이어서 작업할 수 있도록 합니다.
    """
    try:
        context = request.dict(exclude_none=True)

        success = await task_service.save_task_context(task_id, context)

        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found")

        return {"message": "Task context saved successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save task context {task_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save task context")


@router.get("/stats/summary")
async def get_task_statistics():
    """
    작업 통계 요약

    전체 작업 통계를 반환합니다.
    """
    try:
        tasks = await task_service.list_tasks()

        stats = {
            "total": len(tasks),
            "by_status": {},
            "by_phase": {},
            "active_count": task_service.get_active_task_count(),
            "blocked_count": task_service.get_blocked_task_count(),
        }

        # 상태별 집계
        for task in tasks:
            status = task.get("status", "unknown")
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

            phase = task.get("phase", "unknown")
            stats["by_phase"][phase] = stats["by_phase"].get(phase, 0) + 1

        return stats

    except Exception as e:
        logger.error(f"Failed to get task statistics: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve task statistics")


# Export router
__all__ = ["router"]
