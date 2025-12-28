"""
Kanban AI Task Suggestion Models

Week 3 Day 3: AI Task Suggestion Implementation (Q2: AI Hybrid)
Implements Claude Sonnet 4.5 integration for intelligent task generation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class PhaseName(str, Enum):
    """Project phases for task suggestion context"""

    IDEATION = "ideation"
    DESIGN = "design"
    MVP = "mvp"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"


class SuggestionConfidence(str, Enum):
    """Confidence level for AI suggestions"""

    HIGH = "high"  # >90% confidence, minimal risk
    MEDIUM = "medium"  # 70-90% confidence, review recommended
    LOW = "low"  # <70% confidence, careful review required


class TaskSuggestionRequest(BaseModel):
    """
    Request for AI task suggestion generation.

    Q2: AI Hybrid - AI suggests, user approves for Constitutional compliance (P1).
    """

    project_id: Optional[UUID] = Field(None, description="Project context (optional)")
    phase_name: PhaseName = Field(..., description="Target phase for task suggestions")
    context: str = Field(..., min_length=10, max_length=2000, description="Project context and requirements (10-2000 chars)")
    num_suggestions: int = Field(default=3, ge=1, le=5, description="Number of task suggestions to generate (1-5)")
    include_dependencies: bool = Field(default=False, description="Whether to suggest task dependencies")

    @validator("context")
    def validate_context_quality(cls, v):
        """Ensure context provides meaningful information"""
        if len(v.strip()) < 10:
            raise ValueError("Context must contain at least 10 characters of meaningful content")
        return v.strip()


class TaskSuggestion(BaseModel):
    """
    AI-generated task suggestion with confidence scoring.

    Week 3 Day 3: Claude Sonnet 4.5 powered suggestion.
    """

    suggestion_id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., max_length=200, description="Suggested task title")
    description: str = Field(..., max_length=2000, description="Detailed task description")
    phase_name: PhaseName = Field(..., description="Recommended phase")
    priority: str = Field(default="medium", description="Suggested priority (critical/high/medium/low)")
    estimated_hours: Optional[float] = Field(None, ge=0.5, le=100.0, description="Estimated hours to complete (0.5-100)")
    confidence: SuggestionConfidence = Field(..., description="AI confidence level")
    reasoning: str = Field(..., max_length=1000, description="Explanation for this suggestion")
    suggested_dependencies: List[str] = Field(default_factory=list, description="Suggested prerequisite tasks (by title)")
    constitutional_compliance: Dict[str, bool] = Field(default_factory=dict, description="P1-P17 constitutional checks")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional AI-generated metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("priority")
    def validate_priority(cls, v):
        """Ensure priority is valid"""
        valid_priorities = ["critical", "high", "medium", "low"]
        if v.lower() not in valid_priorities:
            raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v.lower()


class TaskSuggestionResponse(BaseModel):
    """
    Response containing multiple AI-generated task suggestions.

    Q2: AI Hybrid - User reviews and approves suggestions.
    """

    request_id: UUID = Field(default_factory=uuid4)
    suggestions: List[TaskSuggestion] = Field(..., description="Generated task suggestions")
    generation_time_ms: float = Field(..., description="Time taken to generate suggestions")
    model_used: str = Field(default="claude-sonnet-4.5", description="AI model identifier")
    context_summary: str = Field(..., description="Summary of input context used")
    remaining_suggestions_today: int = Field(..., description="Rate limit remaining count")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskSuggestionApproval(BaseModel):
    """
    User approval of AI-generated suggestion to create actual task.

    Q2: AI Hybrid - Final approval step for Constitutional compliance.
    """

    suggestion_id: UUID = Field(..., description="ID of suggestion to approve")
    approved_by: str = Field(..., description="User who approved (username/email)")
    modifications: Optional[Dict[str, Any]] = Field(None, description="User modifications to suggestion before approval")
    approval_notes: Optional[str] = Field(None, max_length=500, description="Optional notes about approval decision")


class TaskSuggestionApprovalResponse(BaseModel):
    """Response after approving and creating task from suggestion"""

    task_id: UUID = Field(..., description="Created task ID")
    suggestion_id: UUID = Field(..., description="Approved suggestion ID")
    success: bool = Field(..., description="Whether task was created successfully")
    message: str = Field(..., description="Success or error message")
    created_task: Optional[Dict[str, Any]] = Field(None, description="Created task details")


class RateLimitStatus(BaseModel):
    """Rate limit status for AI suggestions"""

    user_id: str = Field(..., description="User identifier")
    suggestions_used_today: int = Field(..., description="Suggestions used in current period")
    suggestions_remaining: int = Field(..., description="Suggestions remaining")
    limit_per_period: int = Field(default=10, description="Maximum suggestions per period")
    period_reset_at: datetime = Field(..., description="When limit resets")
    is_limited: bool = Field(..., description="Whether user is currently rate limited")


class RateLimitExceededError(Exception):
    """Raised when user exceeds AI suggestion rate limit"""

    def __init__(self, status: RateLimitStatus):
        self.status = status
        super().__init__(
            f"Rate limit exceeded: {status.suggestions_used_today}/{status.limit_per_period} "
            f"suggestions used. Resets at {status.period_reset_at.isoformat()}"
        )


class InvalidSuggestionError(Exception):
    """Raised when suggestion ID is invalid or not found"""

    pass


class ConstitutionalViolationError(Exception):
    """Raised when suggestion violates Constitutional principles (P1-P17)"""

    def __init__(self, violations: List[str]):
        self.violations = violations
        super().__init__(f"Constitutional violations detected: {', '.join(violations)}")
