"""
Uncertainty-Time Tracking Integration Models

Models for integrating Uncertainty Map v3 with Time Tracking Service.
Enables uncertainty-aware time tracking and predictive baseline adjustments.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from .uncertainty import UncertaintyVectorResponse, UncertaintyStateEnum
from .time_tracking import TaskType, Phase, AIModel


class UncertaintyAwareTrackingRequest(BaseModel):
    """Request to start tracking with uncertainty context"""
    task_id: str
    task_type: TaskType
    phase: Phase = Phase.IMPLEMENTATION
    ai_used: AIModel = AIModel.NONE

    # Uncertainty context
    uncertainty_context: Dict[str, Any] = Field(
        ...,
        description="Context for uncertainty analysis (phase, has_code, validation_score, etc.)"
    )

    metadata: Optional[Dict[str, Any]] = None
    project_id: Optional[UUID] = None

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "auth_refactor_001",
                "task_type": "refactoring",
                "phase": "implementation",
                "ai_used": "claude",
                "uncertainty_context": {
                    "phase": "implementation",
                    "has_code": True,
                    "validation_score": 0.7,
                    "team_size": 3,
                    "timeline_weeks": 8
                },
                "metadata": {
                    "component": "authentication",
                    "complexity": "high"
                }
            }
        }


class UncertaintyAwareTrackingResponse(BaseModel):
    """Response after starting uncertainty-aware tracking"""
    success: bool
    session_id: UUID
    message: str

    # Standard tracking info
    baseline_seconds: int

    # Uncertainty info
    uncertainty_vector: UncertaintyVectorResponse
    uncertainty_state: UncertaintyStateEnum
    adjusted_baseline_seconds: int = Field(
        ...,
        description="Baseline adjusted based on uncertainty level"
    )
    confidence_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence in completing task within adjusted baseline"
    )

    # Risk assessment
    risk_factors: List[str] = Field(
        ...,
        description="Identified risk factors for this task"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Started uncertainty-aware tracking for task auth_refactor_001",
                "baseline_seconds": 10800,
                "uncertainty_vector": {
                    "technical": 0.4,
                    "market": 0.2,
                    "resource": 0.3,
                    "timeline": 0.5,
                    "quality": 0.3,
                    "magnitude": 0.38,
                    "dominant_dimension": "timeline"
                },
                "uncertainty_state": "quantum",
                "adjusted_baseline_seconds": 15000,
                "confidence_score": 0.62,
                "risk_factors": [
                    "Timeline uncertainty high (50%)",
                    "Quantum state - multiple possible outcomes",
                    "Complex refactoring with existing code"
                ]
            }
        }


class CorrelationAnalysisResponse(BaseModel):
    """Analysis of correlation between uncertainty and task performance"""

    total_tasks_analyzed: int
    date_range_start: datetime
    date_range_end: datetime

    # Overall correlations
    uncertainty_duration_correlation: float = Field(
        ...,
        description="Correlation between uncertainty magnitude and task duration (-1 to 1)"
    )
    uncertainty_success_correlation: float = Field(
        ...,
        description="Correlation between uncertainty magnitude and success rate (-1 to 1)"
    )

    # State-specific metrics
    state_performance: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Performance metrics grouped by uncertainty state"
    )

    # Dimension-specific metrics
    dimension_impact: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Impact of each uncertainty dimension on performance"
    )

    # Insights
    insights: List[str] = Field(
        ...,
        description="Data-driven insights from correlation analysis"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_tasks_analyzed": 127,
                "date_range_start": "2025-11-01T00:00:00",
                "date_range_end": "2025-11-23T23:59:59",
                "uncertainty_duration_correlation": 0.73,
                "uncertainty_success_correlation": -0.58,
                "state_performance": {
                    "deterministic": {
                        "avg_duration_seconds": 450,
                        "avg_baseline_seconds": 1800,
                        "success_rate": 0.98,
                        "avg_efficiency": 0.75,
                        "task_count": 35
                    },
                    "probabilistic": {
                        "avg_duration_seconds": 1200,
                        "avg_baseline_seconds": 3600,
                        "success_rate": 0.92,
                        "avg_efficiency": 0.67,
                        "task_count": 45
                    },
                    "quantum": {
                        "avg_duration_seconds": 4500,
                        "avg_baseline_seconds": 7200,
                        "success_rate": 0.76,
                        "avg_efficiency": 0.38,
                        "task_count": 32
                    }
                },
                "dimension_impact": {
                    "technical": {
                        "correlation_with_duration": 0.65,
                        "correlation_with_success": -0.52,
                        "most_impacted_phase": "implementation"
                    },
                    "timeline": {
                        "correlation_with_duration": 0.81,
                        "correlation_with_success": -0.67,
                        "most_impacted_phase": "testing"
                    }
                },
                "insights": [
                    "Strong positive correlation (0.73) between uncertainty and duration - higher uncertainty = longer tasks",
                    "Tasks in quantum/chaotic states take 3-4x longer than deterministic states",
                    "Timeline uncertainty is the strongest predictor of task overruns",
                    "Success rate drops from 98% (deterministic) to 76% (quantum)",
                    "Technical uncertainty has high impact during implementation phase"
                ]
            }
        }


class AdjustedBaselineResponse(BaseModel):
    """Uncertainty-adjusted baseline predictions"""

    task_type: TaskType
    phase: Phase

    # Standard baseline
    standard_baseline_seconds: int

    # Uncertainty-adjusted baseline
    uncertainty_vector: UncertaintyVectorResponse
    uncertainty_state: UncertaintyStateEnum
    adjusted_baseline_seconds: int
    adjustment_percentage: float = Field(
        ...,
        description="Percentage adjustment from standard baseline"
    )

    # Confidence
    confidence_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence in adjusted baseline accuracy"
    )
    confidence_interval_lower: int = Field(
        ...,
        description="Lower bound of time estimate (seconds)"
    )
    confidence_interval_upper: int = Field(
        ...,
        description="Upper bound of time estimate (seconds)"
    )

    # Explanation
    adjustment_factors: List[str] = Field(
        ...,
        description="Factors that influenced baseline adjustment"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_type": "implementation",
                "phase": "implementation",
                "standard_baseline_seconds": 14400,
                "uncertainty_vector": {
                    "technical": 0.6,
                    "market": 0.3,
                    "resource": 0.4,
                    "timeline": 0.7,
                    "quality": 0.5,
                    "magnitude": 0.54,
                    "dominant_dimension": "timeline"
                },
                "uncertainty_state": "quantum",
                "adjusted_baseline_seconds": 21600,
                "adjustment_percentage": 50.0,
                "confidence_score": 0.46,
                "confidence_interval_lower": 18000,
                "confidence_interval_upper": 25200,
                "adjustment_factors": [
                    "Quantum uncertainty state (+40%)",
                    "High timeline uncertainty (70%) (+25%)",
                    "Technical uncertainty above threshold (+15%)",
                    "Implementation phase complexity factor (+10%)"
                ]
            }
        }


class MitigationEffectivenessResponse(BaseModel):
    """Analysis of mitigation strategy effectiveness"""

    mitigation_id: str
    mitigation_action: str

    # Application tracking
    times_applied: int
    tasks_tracked: List[UUID]

    # Effectiveness metrics
    avg_uncertainty_reduction: float = Field(
        ...,
        description="Average reduction in uncertainty magnitude after mitigation"
    )
    avg_time_improvement: float = Field(
        ...,
        description="Average improvement in task duration (seconds)"
    )
    success_rate_improvement: float = Field(
        ...,
        description="Improvement in success rate after applying mitigation"
    )

    # ROI
    avg_mitigation_cost_hours: float
    avg_time_saved_hours: float
    roi_ratio: float = Field(
        ...,
        description="ROI ratio: time_saved / mitigation_cost"
    )

    # Recommendation
    effectiveness_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Overall effectiveness score (0-1)"
    )
    recommended: bool = Field(
        ...,
        description="Whether this mitigation is recommended for similar tasks"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "mitigation_id": "mit_a3f2b1_1",
                "mitigation_action": "Set up automated testing",
                "times_applied": 12,
                "tasks_tracked": [
                    "550e8400-e29b-41d4-a716-446655440001",
                    "550e8400-e29b-41d4-a716-446655440002"
                ],
                "avg_uncertainty_reduction": 0.23,
                "avg_time_improvement": 3600.0,
                "success_rate_improvement": 0.15,
                "avg_mitigation_cost_hours": 12.0,
                "avg_time_saved_hours": 18.5,
                "roi_ratio": 1.54,
                "effectiveness_score": 0.78,
                "recommended": True
            }
        }
