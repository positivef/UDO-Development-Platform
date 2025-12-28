"""
Time Tracking Models

Database models for tracking task execution time, ROI metrics, and productivity analysis.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """Task type categories for baseline comparison"""

    ERROR_RESOLUTION = "error_resolution"
    DESIGN_TASK = "design_task"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    CODE_REVIEW = "code_review"
    REFACTORING = "refactoring"
    DEBUGGING = "debugging"
    PHASE_TRANSITION = "phase_transition"
    OTHER = "other"


class Phase(str, Enum):
    """Development phases"""

    IDEATION = "ideation"
    DESIGN = "design"
    MVP = "mvp"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"


class AIModel(str, Enum):
    """AI models used"""

    CLAUDE = "claude"
    CODEX = "codex"
    GEMINI = "gemini"
    MULTI = "multi"
    NONE = "none"


class TaskSession(BaseModel):
    """
    Record of a single task execution session

    Tracks time spent, AI usage, and success metrics.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique session ID")
    task_id: str = Field(..., description="Task identifier")
    task_type: TaskType = Field(..., description="Type of task")
    phase: Phase = Field(..., description="Development phase")
    ai_used: AIModel = Field(..., description="AI model used")

    # Time tracking
    start_time: datetime = Field(..., description="Task start timestamp")
    end_time: Optional[datetime] = Field(None, description="Task end timestamp")
    pause_duration_seconds: int = Field(
        0, description="Total pause duration in seconds"
    )

    # Metrics
    duration_seconds: Optional[int] = Field(
        None, description="Actual task duration in seconds"
    )
    baseline_seconds: int = Field(
        ..., description="Expected manual task duration in seconds"
    )
    time_saved_seconds: Optional[int] = Field(
        None, description="Time saved vs baseline"
    )

    # Results
    success: bool = Field(..., description="Whether task completed successfully")
    error_message: Optional[str] = Field(
        None, description="Error message if task failed"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional task metadata"
    )

    # Relations
    project_id: Optional[UUID] = Field(None, description="Associated project ID")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "task_id": "auth_error_fix_001",
                "task_type": "error_resolution",
                "phase": "implementation",
                "ai_used": "claude",
                "start_time": "2025-11-20T14:00:00",
                "end_time": "2025-11-20T14:02:30",
                "pause_duration_seconds": 0,
                "duration_seconds": 150,
                "baseline_seconds": 1800,
                "time_saved_seconds": 1650,
                "success": True,
                "error_message": None,
                "metadata": {
                    "error_type": "401",
                    "resolution_method": "tier1_obsidian",
                },
                "project_id": "660e8400-e29b-41d4-a716-446655440000",
            }
        }


class TaskSessionCreate(BaseModel):
    """Create new task session"""

    task_id: str
    task_type: TaskType
    phase: Phase
    ai_used: AIModel = AIModel.NONE
    baseline_seconds: int
    metadata: Optional[Dict[str, Any]] = None
    project_id: Optional[UUID] = None


class TaskSessionUpdate(BaseModel):
    """Update existing task session"""

    end_time: Optional[datetime] = None
    pause_duration_seconds: Optional[int] = None
    duration_seconds: Optional[int] = None
    time_saved_seconds: Optional[int] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TaskMetrics(BaseModel):
    """
    Calculated metrics for a completed task
    """

    task_id: str
    duration_seconds: int
    baseline_seconds: int
    time_saved_seconds: int
    time_saved_minutes: float = Field(..., description="Time saved in minutes")
    time_saved_hours: float = Field(..., description="Time saved in hours")
    efficiency_percentage: float = Field(..., description="Efficiency gain percentage")
    roi_percentage: float = Field(..., description="ROI percentage")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "auth_error_fix_001",
                "duration_seconds": 150,
                "baseline_seconds": 1800,
                "time_saved_seconds": 1650,
                "time_saved_minutes": 27.5,
                "time_saved_hours": 0.46,
                "efficiency_percentage": 91.67,
                "roi_percentage": 1100.0,
            }
        }


class TimeMetrics(BaseModel):
    """
    Aggregated time metrics for a period

    Used for daily/weekly/monthly reporting.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique metrics record ID")
    period_type: str = Field(
        ..., description="Period type: daily, weekly, monthly, annual"
    )
    period_start: date = Field(..., description="Period start date")
    period_end: date = Field(..., description="Period end date")

    # Aggregated metrics
    total_tasks: int = Field(..., description="Total tasks completed")
    total_duration_seconds: int = Field(..., description="Total actual time spent")
    total_baseline_seconds: int = Field(..., description="Total manual baseline time")
    total_saved_seconds: int = Field(..., description="Total time saved")

    # Calculated percentages
    roi_percentage: float = Field(..., description="ROI percentage")
    efficiency_gain: float = Field(..., description="Efficiency gain percentage")

    # Analysis
    bottlenecks: Optional[Dict[str, Any]] = Field(
        None, description="Identified bottlenecks"
    )
    top_time_savers: Optional[Dict[str, Any]] = Field(
        None, description="Tasks with most time saved"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "770e8400-e29b-41d4-a716-446655440000",
                "period_type": "weekly",
                "period_start": "2025-11-18",
                "period_end": "2025-11-24",
                "total_tasks": 45,
                "total_duration_seconds": 14400,
                "total_baseline_seconds": 86400,
                "total_saved_seconds": 72000,
                "roi_percentage": 500.0,
                "efficiency_gain": 83.33,
                "bottlenecks": {
                    "slow_tasks": ["design_task_003", "implementation_042"]
                },
                "top_time_savers": {"error_resolution": 28800, "testing": 18000},
            }
        }


class Bottleneck(BaseModel):
    """
    Identified bottleneck in development workflow
    """

    task_type: TaskType
    avg_duration_seconds: int
    baseline_seconds: int
    overhead_seconds: int
    overhead_percentage: float
    frequency: int = Field(..., description="How many times this task type occurred")
    severity: str = Field(..., description="Severity: low, medium, high, critical")

    class Config:
        json_schema_extra = {
            "example": {
                "task_type": "design_task",
                "avg_duration_seconds": 7200,
                "baseline_seconds": 3600,
                "overhead_seconds": 3600,
                "overhead_percentage": 100.0,
                "frequency": 5,
                "severity": "high",
            }
        }


class ROIReport(BaseModel):
    """
    Comprehensive ROI report for a time period
    """

    period: str = Field(..., description="Period: daily, weekly, monthly, annual")
    period_start: date
    period_end: date

    # Time metrics (hours for readability)
    manual_time_hours: float = Field(
        ..., description="Total manual baseline time in hours"
    )
    actual_time_hours: float = Field(
        ..., description="Total actual time spent in hours"
    )
    time_saved_hours: float = Field(..., description="Total time saved in hours")

    # ROI calculations
    roi_percentage: float = Field(
        ..., description="ROI percentage: (saved/actual) * 100"
    )
    efficiency_gain: float = Field(..., description="Efficiency: (saved/manual) * 100")

    # Projections
    annual_projection_hours: Optional[float] = Field(
        None, description="Projected annual time saved"
    )
    annual_projection_value: Optional[float] = Field(
        None, description="Projected annual value saved"
    )

    # Breakdown
    tasks_completed: int
    success_rate: float = Field(..., description="Task success rate percentage")

    # AI performance
    ai_breakdown: Dict[str, Dict[str, Any]] = Field(
        ..., description="Performance by AI model"
    )

    # Phase performance
    phase_breakdown: Dict[str, Dict[str, Any]] = Field(
        ..., description="Performance by phase"
    )

    # Top performers
    top_time_savers: List[Dict[str, Any]] = Field(
        ..., description="Top 5 time-saving task types"
    )
    bottlenecks: List[Bottleneck] = Field(..., description="Identified bottlenecks")

    class Config:
        json_schema_extra = {
            "example": {
                "period": "weekly",
                "period_start": "2025-11-18",
                "period_end": "2025-11-24",
                "manual_time_hours": 24.0,
                "actual_time_hours": 4.0,
                "time_saved_hours": 20.0,
                "roi_percentage": 500.0,
                "efficiency_gain": 83.33,
                "annual_projection_hours": 1040.0,
                "annual_projection_value": 104000.0,
                "tasks_completed": 45,
                "success_rate": 95.56,
                "ai_breakdown": {
                    "claude": {"tasks": 25, "time_saved_hours": 12.5},
                    "codex": {"tasks": 15, "time_saved_hours": 6.0},
                    "multi": {"tasks": 5, "time_saved_hours": 1.5},
                },
                "phase_breakdown": {
                    "implementation": {"tasks": 20, "time_saved_hours": 10.0},
                    "testing": {"tasks": 15, "time_saved_hours": 7.5},
                    "design": {"tasks": 10, "time_saved_hours": 2.5},
                },
                "top_time_savers": [
                    {
                        "task_type": "error_resolution",
                        "time_saved_hours": 8.0,
                        "tasks": 12,
                    },
                    {"task_type": "testing", "time_saved_hours": 5.0, "tasks": 8},
                ],
                "bottlenecks": [],
            }
        }


class WeeklyReport(BaseModel):
    """
    Weekly summary report
    """

    week_start: date
    week_end: date
    roi_report: ROIReport
    trends: Dict[str, Any] = Field(..., description="Week-over-week trends")
    recommendations: List[str] = Field(..., description="Actionable recommendations")

    class Config:
        json_schema_extra = {
            "example": {
                "week_start": "2025-11-18",
                "week_end": "2025-11-24",
                "roi_report": {},  # ROIReport example from above
                "trends": {
                    "roi_change": "+15%",
                    "efficiency_change": "+8%",
                    "tasks_change": "+10",
                },
                "recommendations": [
                    "Focus on automating design tasks (highest bottleneck)",
                    "Increase multi-AI usage for complex tasks",
                    "Review slow implementation tasks for optimization",
                ],
            }
        }


# Request/Response models for API endpoints
class StartTrackingRequest(BaseModel):
    """Request to start tracking a task"""

    task_id: str
    task_type: TaskType
    phase: Phase = Phase.IMPLEMENTATION
    ai_used: AIModel = AIModel.NONE
    metadata: Optional[Dict[str, Any]] = None
    project_id: Optional[UUID] = None


class StartTrackingResponse(BaseModel):
    """Response after starting task tracking"""

    success: bool
    session_id: UUID
    message: str
    baseline_seconds: int


class EndTrackingRequest(BaseModel):
    """Request to end task tracking"""

    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EndTrackingResponse(BaseModel):
    """Response after ending task tracking"""

    success: bool
    metrics: TaskMetrics
    message: str


class PauseTrackingResponse(BaseModel):
    """Response after pausing task tracking"""

    success: bool
    message: str
    paused_at: datetime


class ResumeTrackingResponse(BaseModel):
    """Response after resuming task tracking"""

    success: bool
    message: str
    resumed_at: datetime
