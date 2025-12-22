"""
Kanban AI Task Suggestion API Router

Week 3 Day 3: AI Task Suggestion with Claude Sonnet 4.5.
Implements Q2: AI Hybrid (suggest + approve) with Constitutional compliance.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from backend.app.core.security import require_role, UserRole, get_current_user
from backend.app.services.kanban_ai_service import kanban_ai_service
from backend.app.models.kanban_ai import (
    TaskSuggestionRequest,
    TaskSuggestionResponse,
    TaskSuggestionApproval,
    TaskSuggestionApprovalResponse,
    RateLimitStatus,
    RateLimitExceededError,
    InvalidSuggestionError,
    ConstitutionalViolationError,
)

router = APIRouter(prefix="/api/kanban/ai", tags=["Kanban AI"])


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
# 1. AI Task Suggestion Generation (Q2: AI Hybrid)
# ============================================================================

@router.post(
    "/suggest",
    response_model=TaskSuggestionResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Generate AI task suggestions",
    description="Generate intelligent task suggestions using Claude Sonnet 4.5 (Q2: AI Hybrid)"
)
async def suggest_tasks(
    request: TaskSuggestionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate AI-powered task suggestions using Claude Sonnet 4.5.

    **RBAC**: Requires `developer` role or higher.
    **Q2**: AI Hybrid - AI suggests, user approves for Constitutional compliance.
    **Performance**: <3 seconds target.
    **Rate Limit**: 10 suggestions/hour per user.

    Features:
    - Intelligent task generation based on project context
    - Phase-aware suggestions (ideation/design/mvp/implementation/testing)
    - Confidence scoring (high/medium/low)
    - Constitutional compliance validation
    - Dependency suggestions (optional)

    Raises:
        400: Invalid request parameters
        429: Rate limit exceeded (10/hour)
        500: AI service error
    """
    try:
        user_id = current_user.get("username", current_user.get("email"))

        # Generate suggestions
        response = await kanban_ai_service.suggest_tasks(request, user_id)

        return response

    except RateLimitExceededError as e:
        return error_response(
            code="RATE_LIMIT_EXCEEDED",
            message=str(e),
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={
                "suggestions_used": e.status.suggestions_used_today,
                "limit": e.status.limit_per_period,
                "reset_at": e.status.period_reset_at.isoformat() + "Z"
            }
        )
    except ValueError as e:
        return error_response(
            code="INVALID_REQUEST",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            code="SUGGESTION_GENERATION_FAILED",
            message=f"Failed to generate task suggestions: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# 2. AI Suggestion Approval (Q2: AI Hybrid Final Step)
# ============================================================================

@router.post(
    "/approve/{suggestion_id}",
    response_model=TaskSuggestionApprovalResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Approve AI suggestion and create task",
    description="Approve AI-generated suggestion and create actual task (Q2: AI Hybrid)"
)
async def approve_suggestion(
    suggestion_id: UUID,
    approval: TaskSuggestionApproval,
    current_user: dict = Depends(get_current_user)
):
    """
    Approve AI-generated task suggestion and create actual task.

    **RBAC**: Requires `developer` role or higher.
    **Q2**: AI Hybrid - Final approval step for Constitutional compliance (P1-P17).

    Process:
    1. Validate suggestion exists and not expired
    2. Apply user modifications (if any)
    3. Check Constitutional compliance (P1: Design Review First)
    4. Create actual task in system
    5. Return created task details

    Raises:
        400: Suggestion ID mismatch
        404: Suggestion not found or expired
        409: Constitutional violation (P1-P17)
        500: Task creation failed
    """
    try:
        # Validate suggestion_id matches request body
        if approval.suggestion_id != suggestion_id:
            return error_response(
                code="SUGGESTION_ID_MISMATCH",
                message="Suggestion ID in URL does not match request body",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Set approved_by from current user
        approval.approved_by = current_user.get("username", current_user.get("email"))

        # Approve and create task
        user_id = current_user.get("username", current_user.get("email"))
        response = await kanban_ai_service.approve_suggestion(
            suggestion_id,
            approval,
            user_id
        )

        return response

    except InvalidSuggestionError as e:
        return error_response(
            code="SUGGESTION_NOT_FOUND",
            message=str(e),
            status_code=status.HTTP_404_NOT_FOUND,
            details={"suggestion_id": str(suggestion_id)}
        )
    except ConstitutionalViolationError as e:
        return error_response(
            code="CONSTITUTIONAL_VIOLATION",
            message=f"Suggestion violates Constitutional principles: {str(e)}",
            status_code=status.HTTP_409_CONFLICT,
            details={"violations": e.violations}
        )
    except Exception as e:
        return error_response(
            code="APPROVAL_FAILED",
            message=f"Failed to approve suggestion and create task: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# 3. Rate Limit Status (Optional Helper Endpoint)
# ============================================================================

@router.get(
    "/rate-limit",
    response_model=RateLimitStatus,
    dependencies=[Depends(require_role(UserRole.DEVELOPER))],
    summary="Check AI suggestion rate limit status",
    description="Check current rate limit status for AI suggestions (10/hour)"
)
async def get_rate_limit_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Check current rate limit status for AI suggestions.

    **RBAC**: Requires `developer` role or higher.
    **Rate Limit**: 10 suggestions/hour per user.

    Returns:
    - Suggestions used in current period
    - Suggestions remaining
    - When limit resets
    """
    try:
        user_id = current_user.get("username", current_user.get("email"))
        # ⚠️ CRITICAL: Use rate_status (NOT status) to avoid shadowing FastAPI status module
        # Variable named 'status' would make status.HTTP_500_INTERNAL_SERVER_ERROR fail
        # See: docs/guides/ERROR_PREVENTION_GUIDE.md#variable-naming-conventions
        rate_status = kanban_ai_service._check_rate_limit(user_id)
        return rate_status

    except Exception as e:
        return error_response(
            code="RATE_LIMIT_CHECK_FAILED",
            message=f"Failed to check rate limit status: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR  # Requires 'status' not shadowed
        )
