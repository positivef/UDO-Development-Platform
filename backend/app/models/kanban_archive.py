"""
Kanban Archive Models

Week 3 Day 4-5: Archive View + AI Summarization.
Implements Q6: Done-End archive with AI summarization and Obsidian knowledge extraction.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# ============================================================================
# AI Summarization Models (GPT-4o)
# ============================================================================


class AISummaryConfidence:
    """AI summary quality confidence levels"""

    HIGH = "high"  # >90% confidence, comprehensive summary
    MEDIUM = "medium"  # 70-90% confidence, good summary
    LOW = "low"  # <70% confidence, basic summary


class AISummaryRequest(BaseModel):
    """Request for AI-generated task summary"""

    task_id: UUID
    include_context: bool = Field(default=True, description="Include task context in summary")
    include_quality_metrics: bool = Field(default=True, description="Include quality metrics in summary")
    include_roi_analysis: bool = Field(default=True, description="Include ROI analysis in summary")


class AISummary(BaseModel):
    """AI-generated task summary (GPT-4o)"""

    task_id: UUID
    summary: str = Field(..., min_length=50, max_length=2000, description="AI-generated summary of task accomplishments")
    key_learnings: List[str] = Field(default_factory=list, description="Key learnings extracted from task")
    technical_insights: List[str] = Field(default_factory=list, description="Technical insights for knowledge base")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for future tasks")
    confidence: str = Field(default=AISummaryConfidence.MEDIUM, description="AI confidence in summary quality")
    model_used: str = Field(default="gpt-4o", description="AI model used for generation")
    generation_time_ms: float = Field(default=0.0, description="Time taken to generate summary (ms)")
    token_usage: Optional[Dict[str, int]] = Field(None, description="Token usage stats (prompt, completion, total)")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# ROI Metrics Models
# ============================================================================


class ROIMetrics(BaseModel):
    """Return on Investment metrics for archived task"""

    task_id: UUID

    # Time metrics (defaults for tasks without estimates)
    estimated_hours: float = Field(default=0.0, ge=0)
    actual_hours: float = Field(default=0.0, ge=0)
    time_saved_hours: float = Field(default=0.0, description="Time saved compared to baseline (can be negative)")
    efficiency_percentage: float = Field(default=100.0, ge=0, le=200, description="Efficiency: (estimated / actual) * 100")

    # Quality metrics (defaults for tasks without quality checks)
    quality_score: int = Field(default=0, ge=0, le=100)
    constitutional_compliance: bool
    violated_articles: List[str] = Field(default_factory=list)

    # AI metrics
    ai_suggested: bool
    ai_confidence: Optional[float] = None
    ai_accuracy: Optional[float] = Field(None, ge=0, le=1.0, description="How accurate was AI suggestion (user feedback)")

    # Value metrics
    business_value: Optional[str] = Field(None, description="Business value delivered (user assessment)")
    technical_debt_added: Optional[int] = Field(None, ge=0, le=100, description="Technical debt score (0=none, 100=severe)")

    calculated_at: datetime = Field(default_factory=datetime.utcnow)


class ROIStatistics(BaseModel):
    """Aggregated ROI statistics for multiple tasks"""

    total_tasks: int
    total_estimated_hours: float
    total_actual_hours: float
    total_time_saved_hours: float
    average_efficiency: float
    average_quality_score: float

    # Phase breakdown
    phase_breakdown: Dict[str, int] = Field(default_factory=dict, description="Task count by phase")

    # AI performance
    ai_suggested_tasks: int
    ai_suggestion_accuracy: Optional[float] = None

    # Quality
    constitutional_compliant_tasks: int
    constitutional_compliance_rate: float

    period_start: datetime
    period_end: datetime


# ============================================================================
# Obsidian Knowledge Extraction Models
# ============================================================================


class ObsidianKnowledgeEntry(BaseModel):
    """Knowledge entry for Obsidian sync"""

    task_id: UUID
    title: str
    phase_name: str
    summary: str
    key_learnings: List[str]
    technical_insights: List[str]
    tags: List[str] = Field(default_factory=list, description="Tags for Obsidian organization")
    related_tasks: List[UUID] = Field(default_factory=list, description="Related task IDs for linking")
    created_at: datetime
    archived_at: datetime


class ObsidianSyncStatus(BaseModel):
    """Status of Obsidian knowledge sync"""

    task_id: UUID
    synced: bool
    obsidian_note_path: Optional[str] = Field(None, description="Path to Obsidian note file")
    sync_timestamp: Optional[datetime] = None
    sync_error: Optional[str] = None
    retry_count: int = Field(default=0)


# ============================================================================
# Archive List & Filtering Models
# ============================================================================


class ArchiveFilters(BaseModel):
    """Query filters for archive list"""

    phase: Optional[str] = None
    archived_after: Optional[datetime] = None
    archived_before: Optional[datetime] = None
    archived_by: Optional[str] = None
    ai_suggested: Optional[bool] = None
    obsidian_synced: Optional[bool] = None
    min_quality_score: Optional[int] = Field(None, ge=0, le=100)
    min_efficiency: Optional[float] = Field(None, ge=0)


class ArchiveSortBy:
    """Sort options for archive list"""

    ARCHIVED_AT = "archived_at"
    QUALITY_SCORE = "quality_score"
    EFFICIENCY = "efficiency"
    TIME_SAVED = "time_saved"


class ArchivedTaskWithMetrics(BaseModel):
    """Archived task with full metrics"""

    # Task data
    task_id: UUID
    title: str
    description: Optional[str]
    phase_name: str

    # Archive data
    archived_at: datetime
    archived_by: str

    # AI summary
    ai_summary: Optional[AISummary] = None

    # ROI metrics
    roi_metrics: Optional[ROIMetrics] = None

    # Obsidian sync
    obsidian_synced: bool
    obsidian_note_path: Optional[str] = None

    class Config:
        from_attributes = True


class ArchiveListResponse(BaseModel):
    """Paginated archive list response"""

    data: List[ArchivedTaskWithMetrics]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

    # Aggregated metrics
    roi_statistics: Optional[ROIStatistics] = None


# ============================================================================
# Archive Operations Models
# ============================================================================


class ArchiveTaskRequest(BaseModel):
    """Request to archive a completed task"""

    task_id: UUID
    archived_by: str
    generate_ai_summary: bool = Field(default=True, description="Generate AI summary using GPT-4o (Q6)")
    sync_to_obsidian: bool = Field(default=True, description="Sync to Obsidian knowledge base (Q6)")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for archiving")


class ArchiveTaskResponse(BaseModel):
    """Response after archiving task"""

    task_id: UUID
    success: bool
    message: str
    archived_at: datetime

    # Summary generation results
    ai_summary_generated: bool
    ai_summary: Optional[AISummary] = None
    summary_generation_time_ms: Optional[float] = None

    # Obsidian sync results
    obsidian_synced: bool
    obsidian_note_path: Optional[str] = None
    obsidian_sync_error: Optional[str] = None

    # ROI metrics
    roi_metrics: Optional[ROIMetrics] = None


class BulkArchiveRequest(BaseModel):
    """Request to archive multiple tasks at once"""

    task_ids: List[UUID] = Field(..., min_length=1, max_length=50)
    archived_by: str
    generate_ai_summaries: bool = True
    sync_to_obsidian: bool = True
    reason: Optional[str] = None


class BulkArchiveResponse(BaseModel):
    """Response after bulk archiving"""

    total_requested: int
    successful: int
    failed: int
    archived_task_ids: List[UUID]
    failed_task_ids: List[UUID]
    errors: Dict[str, str] = Field(default_factory=dict, description="Task ID -> error message mapping")
    total_time_ms: float


# ============================================================================
# Error Models
# ============================================================================


class ArchiveError(Exception):
    """Base exception for archive operations"""

    pass


class TaskNotArchivableError(ArchiveError):
    """Raised when task cannot be archived"""

    def __init__(self, task_id: UUID, reason: str):
        super().__init__(f"Task {task_id} cannot be archived: {reason}")


class AISummaryGenerationError(ArchiveError):
    """Raised when AI summary generation fails"""

    def __init__(self, task_id: UUID, error: str):
        super().__init__(f"Failed to generate AI summary for task {task_id}: {error}")


class ObsidianSyncError(ArchiveError):
    """Raised when Obsidian sync fails"""

    def __init__(self, task_id: UUID, error: str):
        super().__init__(f"Failed to sync task {task_id} to Obsidian: {error}")
