"""
Admin API Router for Feature Flag Management

Provides endpoints for Tier 1 rollback operations:
- Toggle feature flags at runtime (<10 seconds)
- View flag status and change history
- Emergency disable all features

Security: All endpoints require admin authentication.

Author: Claude Code
Date: 2025-12-16
"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.feature_flags import (
    FeatureFlag,
    feature_flags_manager,
    is_feature_enabled,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# Admin key from environment (required for all admin operations)
ADMIN_KEY = os.getenv("ADMIN_KEY", "dev-admin-key-change-in-production")


class FeatureFlagToggleRequest(BaseModel):
    """Request to toggle a feature flag."""

    enabled: bool = Field(..., description="New value for the flag")
    reason: Optional[str] = Field(None, description="Reason for the change")


class FeatureFlagResponse(BaseModel):
    """Response after toggling a feature flag."""

    flag: str
    enabled: bool
    message: str


class AllFlagsResponse(BaseModel):
    """Response with all feature flags."""

    flags: dict
    total: int


class ChangeHistoryResponse(BaseModel):
    """Response with change history."""

    history: list
    total: int


def verify_admin_key(admin_key: str = Header(..., alias="X-Admin-Key")) -> str:
    """
    Verify admin key from request header.

    Raises:
        HTTPException: If admin key is invalid
    """
    if admin_key != ADMIN_KEY:
        logger.warning("Unauthorized admin access attempt")
        raise HTTPException(status_code=403, detail="Unauthorized: Invalid admin key")
    return admin_key


# ============================================================
# IMPORTANT: Route ordering matters in FastAPI!
# Specific routes MUST come before parameterized routes.
# Otherwise /feature-flags/reset would match /{flag} with flag="reset"
# ============================================================


# Public endpoint (no auth required) for health check
@router.get("/health")
async def admin_health():
    """
    Health check for admin service.

    No authentication required.
    """
    return {
        "status": "healthy",
        "service": "admin",
        "feature_flags_active": True,
        "total_flags": len(feature_flags_manager.get_all_flags()),
    }


@router.get("/feature-flags", response_model=AllFlagsResponse)
async def get_all_feature_flags(admin_key: str = Header(..., alias="X-Admin-Key")) -> AllFlagsResponse:
    """
    Get all feature flags and their states.

    Requires admin authentication via X-Admin-Key header.
    """
    verify_admin_key(admin_key)

    flags = feature_flags_manager.get_all_flags()
    return AllFlagsResponse(flags=flags, total=len(flags))


# SPECIFIC routes BEFORE parameterized routes
@router.get("/feature-flags/history", response_model=ChangeHistoryResponse)
async def get_change_history(limit: int = 20, admin_key: str = Header(..., alias="X-Admin-Key")) -> ChangeHistoryResponse:
    """
    Get feature flag change history.

    Args:
        limit: Maximum number of events to return (default: 20, max: 100)
    """
    verify_admin_key(admin_key)

    if limit > 100:
        limit = 100

    history = feature_flags_manager.get_change_history(limit=limit)
    return ChangeHistoryResponse(history=history, total=len(history))


@router.post("/feature-flags/reset", response_model=AllFlagsResponse)
async def reset_all_flags(admin_key: str = Header(..., alias="X-Admin-Key")) -> AllFlagsResponse:
    """
    Reset all feature flags to their default values.

    Use this to restore production-safe configuration.
    """
    verify_admin_key(admin_key)

    feature_flags_manager.reset_to_defaults(changed_by="admin")

    logger.warning("Admin reset all feature flags to defaults")

    flags = feature_flags_manager.get_all_flags()
    return AllFlagsResponse(flags=flags, total=len(flags))


@router.post("/feature-flags/disable-all", response_model=AllFlagsResponse)
async def emergency_disable_all(admin_key: str = Header(..., alias="X-Admin-Key")) -> AllFlagsResponse:
    """
    Emergency: Disable ALL feature flags.

    Use this only in critical situations requiring immediate rollback.
    All Kanban features will be disabled.
    """
    verify_admin_key(admin_key)

    feature_flags_manager.disable_all(changed_by="admin-emergency")

    logger.critical("EMERGENCY: Admin disabled ALL feature flags")

    flags = feature_flags_manager.get_all_flags()
    return AllFlagsResponse(flags=flags, total=len(flags))


# PARAMETERIZED routes AFTER specific routes
@router.get("/feature-flags/{flag}", response_model=FeatureFlagResponse)
async def get_feature_flag(flag: str, admin_key: str = Header(..., alias="X-Admin-Key")) -> FeatureFlagResponse:
    """
    Get a specific feature flag status.

    Args:
        flag: Feature flag name (e.g., kanban_ai_suggest)
    """
    verify_admin_key(admin_key)

    # Validate flag exists
    try:
        FeatureFlag(flag)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Unknown feature flag: {flag}")

    enabled = is_feature_enabled(flag)
    return FeatureFlagResponse(
        flag=flag,
        enabled=enabled,
        message=f"Feature '{flag}' is {'enabled' if enabled else 'disabled'}",
    )


@router.post("/feature-flags/{flag}", response_model=FeatureFlagResponse)
async def toggle_feature_flag(
    flag: str,
    request: FeatureFlagToggleRequest,
    admin_key: str = Header(..., alias="X-Admin-Key"),
) -> FeatureFlagResponse:
    """
    Toggle a feature flag at runtime.

    This is the primary Tier 1 rollback mechanism (<10 seconds).

    Args:
        flag: Feature flag name (e.g., kanban_ai_suggest)
        request: Toggle request with enabled value and optional reason

    Example:
        curl -X POST "http://localhost:8000/api/admin/feature-flags/kanban_ai_suggest" \\
             -H "X-Admin-Key: your-admin-key" \\
             -H "Content-Type: application/json" \\
             -d '{"enabled": false, "reason": "Performance issue detected"}'
    """
    verify_admin_key(admin_key)

    # Validate flag exists
    try:
        FeatureFlag(flag)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Unknown feature flag: {flag}")

    success = feature_flags_manager.set_flag(flag=flag, enabled=request.enabled, changed_by="admin", reason=request.reason)

    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to update feature flag: {flag}")

    action = "enabled" if request.enabled else "disabled"
    logger.warning("Admin %s feature flag '%s' (reason: %s)", action, flag, request.reason)

    return FeatureFlagResponse(
        flag=flag,
        enabled=request.enabled,
        message=f"Feature '{flag}' has been {action}",
    )
