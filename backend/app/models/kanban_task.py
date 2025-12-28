"""
Kanban Task Models

Core task management models for Kanban-UDO integration.
Implements Q1-Q8 decisions from KANBAN_INTEGRATION_STRATEGY.md.

Security improvements (MED-02):
- Input sanitization for text fields
- XSS/SQL injection pattern checks
- Length constraints on all string fields
"""

import re
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# MED-02: Security Validation Patterns (inline to avoid circular imports)
# ============================================================================

# SQL injection patterns (OWASP)
_SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE)\b)",
    r"(--|\||;|\/\*|\*\/|@@|@)",
    r"(xp_|sp_|0x)",
    r"(\bEXEC\b|\bEXECUTE\b)",
]

# XSS patterns (OWASP)
_XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe[^>]*>",
    r"<object[^>]*>",
]


def _check_dangerous_content(value: str) -> bool:
    """Check for SQL injection or XSS patterns"""
    if not value:
        return False
    for pattern in _SQL_INJECTION_PATTERNS + _XSS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            return True
    return False


def _sanitize_text(value: str, max_length: int = 10000) -> str:
    """Sanitize text input: remove null bytes, strip whitespace, limit length"""
    if not value:
        return value
    # Remove null bytes
    sanitized = value.replace("\x00", "")
    # Strip whitespace
    sanitized = sanitized.strip()
    # Limit length
    return sanitized[:max_length]


# ============================================================================
# Task Status & Priority Enums
# ============================================================================


class TaskStatus:
    """Task status constants"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    DONE_END = "done_end"  # Q6: Done-End archiving


class TaskPriority:
    """Task priority constants"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PhaseName:
    """Phase name constants (Q1: Task within Phase)"""

    IDEATION = "ideation"
    DESIGN = "design"
    MVP = "mvp"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"


class TaskSortField:
    """
    Task sort field constants (P0-4: SQL Injection Hardening)

    Whitelist of allowed sort columns for ORDER BY clauses.
    Prevents SQL injection by restricting to predefined database columns.
    """

    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    PRIORITY = "priority"
    COMPLETENESS = "completeness"

    @classmethod
    def get_valid_fields(cls) -> list[str]:
        """Get list of all valid sort fields"""
        return [cls.CREATED_AT, cls.UPDATED_AT, cls.PRIORITY, cls.COMPLETENESS]

    @classmethod
    def validate(cls, value: str) -> str:
        """
        Validate sort field against whitelist.

        Args:
            value: Sort field to validate

        Returns:
            Validated sort field (lowercase)

        Raises:
            ValueError: If field not in whitelist
        """
        normalized = value.lower()
        if normalized not in cls.get_valid_fields():
            raise ValueError(
                f"Invalid sort field '{value}'. "
                f"Must be one of: {', '.join(cls.get_valid_fields())}"
            )
        return normalized


# ============================================================================
# Task Base Models
# ============================================================================


class TaskBase(BaseModel):
    """Base task model with common fields"""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)  # MED-02: Length limit
    phase_name: str = Field(..., description="Phase this task belongs to (Q1)")
    status: str = Field(default=TaskStatus.PENDING)
    priority: str = Field(default=TaskPriority.MEDIUM)
    completeness: int = Field(default=0, ge=0, le=100, description="Completion percentage (0-100)")
    estimated_hours: float = Field(default=0.0, ge=0, le=10000)  # MED-02: Max 10000 hours
    actual_hours: float = Field(default=0.0, ge=0, le=10000)  # MED-02: Max 10000 hours

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        """MED-02: Validate and sanitize title"""
        sanitized = _sanitize_text(v, max_length=255)
        if _check_dangerous_content(sanitized):
            raise ValueError("Title contains potentially dangerous content")
        if len(sanitized) < 1:
            raise ValueError("Title must not be empty")
        return sanitized

    @field_validator("description")
    @classmethod
    def validate_description(cls, v):
        """MED-02: Validate and sanitize description"""
        if v is None:
            return v
        sanitized = _sanitize_text(v, max_length=5000)
        if _check_dangerous_content(sanitized):
            raise ValueError("Description contains potentially dangerous content")
        return sanitized

    @field_validator("phase_name")
    @classmethod
    def validate_phase(cls, v):
        """Validate phase name"""
        valid_phases = [PhaseName.IDEATION, PhaseName.DESIGN, PhaseName.MVP, PhaseName.IMPLEMENTATION, PhaseName.TESTING]
        if v not in valid_phases:
            raise ValueError(f"Phase must be one of: {', '.join(valid_phases)}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """Validate status"""
        valid_statuses = [
            TaskStatus.PENDING,
            TaskStatus.IN_PROGRESS,
            TaskStatus.BLOCKED,
            TaskStatus.COMPLETED,
            TaskStatus.DONE_END,
        ]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        """Validate priority"""
        valid_priorities = [TaskPriority.CRITICAL, TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW]
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v


# ============================================================================
# Task CRUD Models
# ============================================================================


class TaskCreate(TaskBase):
    """Task creation request"""

    phase_id: UUID = Field(..., description="Phase ID (foreign key)")

    # AI Creation (Q2: AI Hybrid creation)
    ai_suggested: bool = Field(default=False, description="Created by AI suggestion")
    ai_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI confidence score (0.0-1.0)")


class TaskUpdate(BaseModel):
    """Task update request (all fields optional)"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)  # MED-02: Length limit
    status: Optional[str] = None
    priority: Optional[str] = None
    completeness: Optional[int] = Field(None, ge=0, le=100)
    estimated_hours: Optional[float] = Field(None, ge=0, le=10000)  # MED-02: Max limit
    actual_hours: Optional[float] = Field(None, ge=0, le=10000)  # MED-02: Max limit
    quality_score: Optional[int] = Field(None, ge=0, le=100)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        """MED-02: Validate and sanitize title"""
        if v is None:
            return v
        sanitized = _sanitize_text(v, max_length=255)
        if _check_dangerous_content(sanitized):
            raise ValueError("Title contains potentially dangerous content")
        if len(sanitized) < 1:
            raise ValueError("Title must not be empty")
        return sanitized

    @field_validator("description")
    @classmethod
    def validate_description(cls, v):
        """MED-02: Validate and sanitize description"""
        if v is None:
            return v
        sanitized = _sanitize_text(v, max_length=5000)
        if _check_dangerous_content(sanitized):
            raise ValueError("Description contains potentially dangerous content")
        return sanitized


class Task(TaskBase):
    """Full task model (database representation)"""

    task_id: UUID = Field(default_factory=uuid4)
    phase_id: UUID

    # AI Creation (Q2: AI Hybrid creation)
    ai_suggested: bool = False
    ai_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    approved_by: Optional[str] = None
    approval_timestamp: Optional[datetime] = None

    # Quality Gate (Q3: Hybrid completion)
    quality_gate_passed: bool = False
    quality_score: Optional[int] = Field(None, ge=0, le=100)
    constitutional_compliant: bool = True
    violated_articles: List[str] = Field(default_factory=list)

    # User Confirmation (Q3: Quality gate + user confirmation)
    user_confirmed: bool = False
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Task Filtering & Sorting
# ============================================================================


class TaskFilters(BaseModel):
    """Query filters for task list"""

    phase: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    min_completeness: Optional[int] = Field(None, ge=0, le=100)
    max_completeness: Optional[int] = Field(None, ge=0, le=100)
    ai_suggested: Optional[bool] = None
    quality_gate_passed: Optional[bool] = None


class TaskSortBy:
    """Sort options for task list"""

    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    PRIORITY = "priority"
    COMPLETENESS = "completeness"
    ESTIMATED_HOURS = "estimated_hours"


# ============================================================================
# Phase Operations
# ============================================================================


class PhaseChangeRequest(BaseModel):
    """Request to move task to different phase"""

    new_phase_id: UUID
    new_phase_name: str
    reason: Optional[str] = Field(None, max_length=500)  # MED-02: Length limit

    @field_validator("new_phase_name")
    @classmethod
    def validate_phase(cls, v):
        """Validate new phase name"""
        valid_phases = [PhaseName.IDEATION, PhaseName.DESIGN, PhaseName.MVP, PhaseName.IMPLEMENTATION, PhaseName.TESTING]
        if v not in valid_phases:
            raise ValueError(f"Phase must be one of: {', '.join(valid_phases)}")
        return v

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v):
        """MED-02: Validate and sanitize reason"""
        if v is None:
            return v
        sanitized = _sanitize_text(v, max_length=500)
        if _check_dangerous_content(sanitized):
            raise ValueError("Reason contains potentially dangerous content")
        return sanitized


# ============================================================================
# Quality Gate Models (Q3: Hybrid completion)
# ============================================================================


class QualityGateCheck(BaseModel):
    """Individual quality gate check"""

    check_name: str
    passed: bool
    message: str
    article: Optional[str] = None  # Constitutional article (e.g., "P1", "P5")


class QualityGateResult(BaseModel):
    """Quality gate execution result"""

    task_id: UUID
    quality_gate_passed: bool
    quality_score: int = Field(..., ge=0, le=100)
    constitutional_compliant: bool
    violated_articles: List[str] = Field(default_factory=list)
    checks: List[QualityGateCheck]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    execution_time_ms: float


# ============================================================================
# Archive Models (Q6: Done-End + AI -> Obsidian)
# ============================================================================


class ArchiveRequest(BaseModel):
    """Request to archive task"""

    archived_by: str = Field(..., min_length=1, max_length=100)  # MED-02: Length limit
    generate_ai_summary: bool = Field(default=True, description="Generate AI summary using GPT-4o (Q6)")
    reason: Optional[str] = Field(None, max_length=500)  # MED-02: Length limit

    @field_validator("archived_by")
    @classmethod
    def validate_archived_by(cls, v):
        """MED-02: Validate and sanitize archived_by field"""
        sanitized = _sanitize_text(v, max_length=100)
        if _check_dangerous_content(sanitized):
            raise ValueError("archived_by contains potentially dangerous content")
        if len(sanitized) < 1:
            raise ValueError("archived_by must not be empty")
        return sanitized

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v):
        """MED-02: Validate and sanitize reason"""
        if v is None:
            return v
        sanitized = _sanitize_text(v, max_length=500)
        if _check_dangerous_content(sanitized):
            raise ValueError("Reason contains potentially dangerous content")
        return sanitized


class TaskArchive(BaseModel):
    """Archived task with AI summary"""

    task_id: UUID
    task_data: Task
    ai_summary: Optional[str] = Field(None, description="GPT-4o generated summary")
    archived_at: datetime = Field(default_factory=datetime.utcnow)
    archived_by: str
    obsidian_synced: bool = Field(default=False, description="Synced to Obsidian knowledge base")

    class Config:
        from_attributes = True


# ============================================================================
# Response Models with Pagination
# ============================================================================


class PaginationMeta(BaseModel):
    """Pagination metadata"""

    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class TaskListResponse(BaseModel):
    """Paginated task list response"""

    data: List[Task]
    pagination: PaginationMeta


# ============================================================================
# Status & Priority Change
# ============================================================================


class StatusChangeRequest(BaseModel):
    """Request to change task status"""

    new_status: str
    reason: Optional[str] = Field(None, max_length=500)  # MED-02: Length limit

    @field_validator("new_status")
    @classmethod
    def validate_status(cls, v):
        """Validate new status"""
        valid_statuses = [
            TaskStatus.PENDING,
            TaskStatus.IN_PROGRESS,
            TaskStatus.BLOCKED,
            TaskStatus.COMPLETED,
            TaskStatus.DONE_END,
        ]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v):
        """MED-02: Validate and sanitize reason"""
        if v is None:
            return v
        sanitized = _sanitize_text(v, max_length=500)
        if _check_dangerous_content(sanitized):
            raise ValueError("Reason contains potentially dangerous content")
        return sanitized


class PriorityChangeRequest(BaseModel):
    """Request to change task priority"""

    new_priority: str
    reason: Optional[str] = Field(None, max_length=500)  # MED-02: Length limit

    @field_validator("new_priority")
    @classmethod
    def validate_priority(cls, v):
        """Validate new priority"""
        valid_priorities = [TaskPriority.CRITICAL, TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW]
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v):
        """MED-02: Validate and sanitize reason"""
        if v is None:
            return v
        sanitized = _sanitize_text(v, max_length=500)
        if _check_dangerous_content(sanitized):
            raise ValueError("Reason contains potentially dangerous content")
        return sanitized


class CompletenessUpdateRequest(BaseModel):
    """Request to update task completeness"""

    completeness: int = Field(..., ge=0, le=100)
    updated_by: str = Field(..., min_length=1, max_length=100)  # MED-02: Length limit

    @field_validator("updated_by")
    @classmethod
    def validate_updated_by(cls, v):
        """MED-02: Validate and sanitize updated_by field"""
        sanitized = _sanitize_text(v, max_length=100)
        if _check_dangerous_content(sanitized):
            raise ValueError("updated_by contains potentially dangerous content")
        if len(sanitized) < 1:
            raise ValueError("updated_by must not be empty")
        return sanitized


# ============================================================================
# Error Models
# ============================================================================


class TaskNotFoundError(Exception):
    """Raised when task not found"""

    def __init__(self, task_id: UUID):
        super().__init__(f"Task with ID {task_id} not found")


class TaskValidationError(Exception):
    """Raised when task validation fails"""

    pass


class QualityGateFailedError(Exception):
    """Raised when quality gate check fails (Q3)"""

    def __init__(self, task_id: UUID, violated_articles: List[str]):
        articles_str = ", ".join(violated_articles)
        super().__init__(f"Task {task_id} failed quality gate. " f"Violated articles: {articles_str}")
