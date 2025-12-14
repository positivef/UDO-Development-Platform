"""
Kanban Task Models

Core task management models for Kanban-UDO integration.
Implements Q1-Q8 decisions from KANBAN_INTEGRATION_STRATEGY.md.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from uuid import UUID, uuid4


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


# ============================================================================
# Task Base Models
# ============================================================================

class TaskBase(BaseModel):
    """Base task model with common fields"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    phase_name: str = Field(..., description="Phase this task belongs to (Q1)")
    status: str = Field(default=TaskStatus.PENDING)
    priority: str = Field(default=TaskPriority.MEDIUM)
    completeness: int = Field(default=0, ge=0, le=100, description="Completion percentage (0-100)")
    estimated_hours: float = Field(default=0.0, ge=0)
    actual_hours: float = Field(default=0.0, ge=0)

    @field_validator('phase_name')
    @classmethod
    def validate_phase(cls, v):
        """Validate phase name"""
        valid_phases = [
            PhaseName.IDEATION,
            PhaseName.DESIGN,
            PhaseName.MVP,
            PhaseName.IMPLEMENTATION,
            PhaseName.TESTING
        ]
        if v not in valid_phases:
            raise ValueError(f"Phase must be one of: {', '.join(valid_phases)}")
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate status"""
        valid_statuses = [
            TaskStatus.PENDING,
            TaskStatus.IN_PROGRESS,
            TaskStatus.BLOCKED,
            TaskStatus.COMPLETED,
            TaskStatus.DONE_END
        ]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        """Validate priority"""
        valid_priorities = [
            TaskPriority.CRITICAL,
            TaskPriority.HIGH,
            TaskPriority.MEDIUM,
            TaskPriority.LOW
        ]
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
    ai_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="AI confidence score (0.0-1.0)"
    )


class TaskUpdate(BaseModel):
    """Task update request (all fields optional)"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    completeness: Optional[int] = Field(None, ge=0, le=100)
    estimated_hours: Optional[float] = Field(None, ge=0)
    actual_hours: Optional[float] = Field(None, ge=0)
    quality_score: Optional[int] = Field(None, ge=0, le=100)


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
    reason: Optional[str] = None

    @field_validator('new_phase_name')
    @classmethod
    def validate_phase(cls, v):
        """Validate new phase name"""
        valid_phases = [
            PhaseName.IDEATION,
            PhaseName.DESIGN,
            PhaseName.MVP,
            PhaseName.IMPLEMENTATION,
            PhaseName.TESTING
        ]
        if v not in valid_phases:
            raise ValueError(f"Phase must be one of: {', '.join(valid_phases)}")
        return v


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
# Archive Models (Q6: Done-End + AI → Obsidian)
# ============================================================================

class ArchiveRequest(BaseModel):
    """Request to archive task"""
    archived_by: str
    generate_ai_summary: bool = Field(
        default=True,
        description="Generate AI summary using GPT-4o (Q6)"
    )
    reason: Optional[str] = None


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
    reason: Optional[str] = None

    @field_validator('new_status')
    @classmethod
    def validate_status(cls, v):
        """Validate new status"""
        valid_statuses = [
            TaskStatus.PENDING,
            TaskStatus.IN_PROGRESS,
            TaskStatus.BLOCKED,
            TaskStatus.COMPLETED,
            TaskStatus.DONE_END
        ]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


class PriorityChangeRequest(BaseModel):
    """Request to change task priority"""
    new_priority: str
    reason: Optional[str] = None

    @field_validator('new_priority')
    @classmethod
    def validate_priority(cls, v):
        """Validate new priority"""
        valid_priorities = [
            TaskPriority.CRITICAL,
            TaskPriority.HIGH,
            TaskPriority.MEDIUM,
            TaskPriority.LOW
        ]
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v


class CompletenessUpdateRequest(BaseModel):
    """Request to update task completeness"""
    completeness: int = Field(..., ge=0, le=100)
    updated_by: str


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
        super().__init__(
            f"Task {task_id} failed quality gate. "
            f"Violated articles: {articles_str}"
        )
