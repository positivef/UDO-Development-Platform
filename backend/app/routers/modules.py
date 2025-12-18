"""
Module Management API Router

Standard [EMOJI] [EMOJI] [EMOJI] [EMOJI] API
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.services.module_ownership_manager import (
    get_module_manager,
    ModuleStatus,
    CompletionCriteria
)
from app.services.session_manager_v2 import get_session_manager

router = APIRouter(
    prefix="/api/modules",
    tags=["modules"]
)


# ========================
# Request/Response Models
# ========================

class ClaimModuleRequest(BaseModel):
    """[EMOJI] [EMOJI] [EMOJI]"""
    module_id: str = Field(..., description="[EMOJI] ID ([EMOJI]: auth/login)")
    session_id: str = Field(..., description="[EMOJI] ID")
    developer_name: str = Field(..., description="[EMOJI] [EMOJI]")
    estimated_hours: Optional[float] = Field(None, description="[EMOJI] [EMOJI] [EMOJI]")


class UpdateModuleStatusRequest(BaseModel):
    """[EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
    session_id: str = Field(..., description="[EMOJI] ID")
    new_status: str = Field(..., description="[EMOJI] [EMOJI]")
    progress: Optional[int] = Field(None, ge=0, le=100, description="[EMOJI]")
    commit_hash: Optional[str] = Field(None, description="[EMOJI] [EMOJI]")


class ReleaseModuleRequest(BaseModel):
    """[EMOJI] [EMOJI] [EMOJI]"""
    session_id: str = Field(..., description="[EMOJI] ID")
    reason: Optional[str] = Field(None, description="[EMOJI] [EMOJI]")


class ModuleAvailabilityResponse(BaseModel):
    """[EMOJI] [EMOJI] [EMOJI]"""
    available: bool
    reason: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = None
    estimated_available: Optional[datetime] = None
    alternatives: List[str] = []
    warnings: List[str] = []
    can_override: bool = False


class ModuleOwnershipResponse(BaseModel):
    """[EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
    module_id: str
    owner_session: str
    developer_name: str
    status: str
    started_at: datetime
    estimated_completion: datetime
    actual_completion: Optional[datetime] = None
    completion_criteria: List[str] = []
    blockers: List[str] = []
    warnings: List[str] = []
    progress: int = 0
    commits: List[str] = []


class ModuleStatusBoardResponse(BaseModel):
    """[EMOJI] [EMOJI] [EMOJI]"""
    active: List[Dict[str, Any]]
    available: List[Dict[str, Any]]
    blocked: List[Dict[str, Any]]
    completed: List[Dict[str, Any]]


# ========================
# API Endpoints
# ========================

@router.get("/status-board", response_model=ModuleStatusBoardResponse)
async def get_module_status_board():
    """
    [EMOJI] [EMOJI] [EMOJI]

    [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI].
    """
    try:
        manager = await get_module_manager()
        board = await manager.get_module_status_board()
        return ModuleStatusBoardResponse(**board)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{module_id:path}/availability", response_model=ModuleAvailabilityResponse)
async def check_module_availability(
    module_id: str,
    session_id: str = Query(..., description="[EMOJI] ID"),
    developer_name: str = Query(..., description="[EMOJI] [EMOJI]")
):
    """
    [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]

    [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI].
    [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] false[EMOJI] [EMOJI].
    """
    try:
        manager = await get_module_manager()
        availability = await manager.check_module_availability(
            module_id=module_id,
            session_id=session_id,
            developer_name=developer_name
        )

        return ModuleAvailabilityResponse(
            available=availability.available,
            reason=availability.reason,
            owner=availability.owner,
            status=availability.status.value if availability.status else None,
            estimated_available=availability.estimated_available,
            alternatives=availability.alternatives,
            warnings=availability.warnings,
            can_override=availability.can_override
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{module_id:path}/claim", response_model=ModuleOwnershipResponse)
async def claim_module(
    module_id: str,
    request: ClaimModuleRequest
):
    """
    [EMOJI] [EMOJI]

    [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI].
    Standard [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI].
    """
    try:
        manager = await get_module_manager()

        # [EMOJI] ID [EMOJI]
        if request.module_id != module_id:
            raise ValueError("Module ID mismatch")

        success, ownership = await manager.claim_module(
            module_id=module_id,
            session_id=request.session_id,
            developer_name=request.developer_name,
            estimated_hours=request.estimated_hours
        )

        if not success:
            raise HTTPException(status_code=409, detail="Module claim failed")

        return ModuleOwnershipResponse(
            module_id=ownership.module_id,
            owner_session=ownership.owner_session,
            developer_name=ownership.developer_name,
            status=ownership.status.value,
            started_at=ownership.started_at,
            estimated_completion=ownership.estimated_completion,
            actual_completion=ownership.actual_completion,
            completion_criteria=[c.value for c in ownership.completion_criteria],
            blockers=ownership.blockers,
            warnings=ownership.warnings,
            progress=ownership.progress,
            commits=ownership.commits
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{module_id:path}/status")
async def update_module_status(
    module_id: str,
    request: UpdateModuleStatusRequest
):
    """
    [EMOJI] [EMOJI] [EMOJI]

    [EMOJI] [EMOJI] [EMOJI] [EMOJI].
    (planning -> coding -> testing -> review -> completed)
    """
    try:
        manager = await get_module_manager()

        # [EMOJI] [EMOJI] Enum[EMOJI] [EMOJI]
        new_status = ModuleStatus(request.new_status)

        success = await manager.update_module_status(
            module_id=module_id,
            session_id=request.session_id,
            new_status=new_status,
            progress=request.progress,
            commit_hash=request.commit_hash
        )

        if not success:
            raise HTTPException(status_code=404, detail="Module not found or not owned")

        return {"success": True, "message": f"Module status updated to {new_status.value}"}

    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{module_id:path}/release")
async def release_module(
    module_id: str,
    request: ReleaseModuleRequest
):
    """
    [EMOJI] [EMOJI] [EMOJI]

    [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI].
    """
    try:
        manager = await get_module_manager()

        success = await manager.release_module(
            module_id=module_id,
            session_id=request.session_id,
            reason=request.reason
        )

        if not success:
            raise HTTPException(status_code=404, detail="Module not found or not owned")

        return {"success": True, "message": "Module released successfully"}

    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{module_id:path}/ownership", response_model=Optional[ModuleOwnershipResponse])
async def get_module_ownership(module_id: str):
    """
    [EMOJI] [EMOJI] [EMOJI] [EMOJI]

    [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI].
    """
    try:
        manager = await get_module_manager()

        if module_id not in manager.active_ownerships:
            return None

        ownership = manager.active_ownerships[module_id]

        return ModuleOwnershipResponse(
            module_id=ownership.module_id,
            owner_session=ownership.owner_session,
            developer_name=ownership.developer_name,
            status=ownership.status.value,
            started_at=ownership.started_at,
            estimated_completion=ownership.estimated_completion,
            actual_completion=ownership.actual_completion,
            completion_criteria=[c.value for c in ownership.completion_criteria],
            blockers=ownership.blockers,
            warnings=ownership.warnings,
            progress=ownership.progress,
            commits=ownership.commits
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active", response_model=List[ModuleOwnershipResponse])
async def get_active_modules():
    """
    [EMOJI] [EMOJI] [EMOJI]

    [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI].
    """
    try:
        manager = await get_module_manager()

        active_modules = []
        for module_id, ownership in manager.active_ownerships.items():
            active_modules.append(ModuleOwnershipResponse(
                module_id=ownership.module_id,
                owner_session=ownership.owner_session,
                developer_name=ownership.developer_name,
                status=ownership.status.value,
                started_at=ownership.started_at,
                estimated_completion=ownership.estimated_completion,
                actual_completion=ownership.actual_completion,
                completion_criteria=[c.value for c in ownership.completion_criteria],
                blockers=ownership.blockers,
                warnings=ownership.warnings,
                progress=ownership.progress,
                commits=ownership.commits
            ))

        return active_modules

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-rules")
async def check_standard_rules(
    action: str = Query(..., description="[EMOJI] [EMOJI]"),
    context: Dict[str, Any] = {}
):
    """
    Standard [EMOJI] [EMOJI] [EMOJI]

    [EMOJI] [EMOJI] Standard [EMOJI] [EMOJI] [EMOJI] [EMOJI].
    """
    try:
        manager = await get_module_manager()

        allowed, warnings = await manager.check_standard_rules(action, context)

        return {
            "allowed": allowed,
            "warnings": warnings,
            "level": "Standard"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))