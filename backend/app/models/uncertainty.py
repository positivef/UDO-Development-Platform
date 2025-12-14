"""
Uncertainty Map Pydantic Models

API models for Uncertainty Map v3.0 integration
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UncertaintyStateEnum(str, Enum):
    """Quantum-inspired uncertainty states"""
    DETERMINISTIC = "deterministic"      # <10% uncertainty
    PROBABILISTIC = "probabilistic"      # 10-30% uncertainty
    QUANTUM = "quantum"                   # 30-60% uncertainty
    CHAOTIC = "chaotic"                   # 60-90% uncertainty
    VOID = "void"                         # >90% uncertainty


class UncertaintyVectorResponse(BaseModel):
    """Multi-dimensional uncertainty representation"""
    technical: float = Field(..., ge=0, le=1, description="Technical uncertainty (0-1)")
    market: float = Field(..., ge=0, le=1, description="Market uncertainty (0-1)")
    resource: float = Field(..., ge=0, le=1, description="Resource uncertainty (0-1)")
    timeline: float = Field(..., ge=0, le=1, description="Timeline uncertainty (0-1)")
    quality: float = Field(..., ge=0, le=1, description="Quality uncertainty (0-1)")
    magnitude: float = Field(..., ge=0, le=1, description="Total uncertainty magnitude (0-1)")
    dominant_dimension: str = Field(..., description="Dimension with highest uncertainty")

    class Config:
        json_schema_extra = {
            "example": {
                "technical": 0.3,
                "market": 0.2,
                "resource": 0.4,
                "timeline": 0.5,
                "quality": 0.2,
                "magnitude": 0.35,
                "dominant_dimension": "timeline"
            }
        }


class MitigationStrategyResponse(BaseModel):
    """Auto-generated mitigation strategy"""
    id: str
    uncertainty_id: str
    action: str
    priority: int = Field(..., ge=1, le=5, description="Priority (1-5)")
    estimated_impact: float = Field(..., ge=0, le=1, description="Impact (0-1)")
    estimated_cost: float = Field(..., ge=0, description="Cost in hours")
    prerequisites: List[str]
    success_probability: float = Field(..., ge=0, le=1, description="Success probability (0-1)")
    fallback_strategy: Optional[str] = None
    roi: float = Field(..., description="Return on investment")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "mit_001",
                "uncertainty_id": "tech_001",
                "action": "Add integration tests for critical path",
                "priority": 1,
                "estimated_impact": 0.6,
                "estimated_cost": 4.0,
                "prerequisites": ["Test framework setup", "Mock data"],
                "success_probability": 0.85,
                "fallback_strategy": "Manual testing protocol",
                "roi": 0.1275
            }
        }


class PredictiveModelResponse(BaseModel):
    """Predictive model for uncertainty evolution"""
    trend: str = Field(..., description="Trend: increasing, decreasing, stable, oscillating")
    velocity: float = Field(..., description="Rate of change")
    acceleration: float = Field(..., description="Change of rate")
    predicted_resolution: Optional[datetime] = Field(None, description="Predicted resolution time")
    confidence_interval_lower: float = Field(..., ge=0, le=1)
    confidence_interval_upper: float = Field(..., ge=0, le=1)

    class Config:
        json_schema_extra = {
            "example": {
                "trend": "decreasing",
                "velocity": -0.05,
                "acceleration": 0.01,
                "predicted_resolution": "2025-11-23T14:30:00",
                "confidence_interval_lower": 0.15,
                "confidence_interval_upper": 0.35
            }
        }


class UncertaintyStatusResponse(BaseModel):
    """Complete uncertainty status response"""
    vector: UncertaintyVectorResponse
    state: UncertaintyStateEnum
    confidence_score: float = Field(..., ge=0, le=1, description="Overall confidence (1 - magnitude)")
    prediction: PredictiveModelResponse
    mitigations: List[MitigationStrategyResponse]
    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "vector": {
                    "technical": 0.3,
                    "market": 0.2,
                    "resource": 0.4,
                    "timeline": 0.5,
                    "quality": 0.2,
                    "magnitude": 0.35,
                    "dominant_dimension": "timeline"
                },
                "state": "probabilistic",
                "confidence_score": 0.65,
                "prediction": {
                    "trend": "decreasing",
                    "velocity": -0.05,
                    "acceleration": 0.01,
                    "predicted_resolution": "2025-11-23T14:30:00",
                    "confidence_interval_lower": 0.15,
                    "confidence_interval_upper": 0.35
                },
                "mitigations": [],
                "timestamp": "2025-11-22T12:00:00"
            }
        }


class MitigationAckRequest(BaseModel):
    """Request to acknowledge and apply a mitigation strategy"""
    mitigation_id: Optional[str] = Field(None, description="ID of the mitigation being applied (optional when provided in path)")
    dimension: Optional[str] = Field(default=None, description="Optional dimension to reduce (technical/timeline/...)")
    applied_impact: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Optional override of impact (0-1). Defaults to mitigation estimated_impact"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "mitigation_id": "mit_001",
                "dimension": "timeline",
                "applied_impact": 0.2
            }
        }


class MitigationAckResponse(BaseModel):
    """Response after applying a mitigation"""
    success: bool
    mitigation_id: str
    message: str
    updated_vector: Optional[UncertaintyVectorResponse] = None
    updated_state: Optional[UncertaintyStateEnum] = None
    confidence_score: Optional[float] = None
    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "mitigation_id": "mit_001",
                "message": "Applied mitigation and reduced timeline risk",
                "updated_vector": {
                    "technical": 0.25,
                    "market": 0.2,
                    "resource": 0.35,
                    "timeline": 0.3,
                    "quality": 0.2,
                    "magnitude": 0.31,
                    "dominant_dimension": "timeline"
                },
                "updated_state": "probabilistic",
                "confidence_score": 0.69,
                "timestamp": "2025-11-22T12:10:00"
            }
        }


class ContextAnalysisRequest(BaseModel):
    """Request for analyzing context and generating uncertainty"""
    phase: str = Field(..., description="Current development phase")
    has_code: bool = Field(default=False, description="Whether code exists")
    validation_score: float = Field(default=0.0, ge=0, le=1, description="Market validation score")
    team_size: int = Field(default=1, ge=1, description="Team size")
    timeline_weeks: int = Field(default=4, ge=1, description="Timeline in weeks")

    class Config:
        json_schema_extra = {
            "example": {
                "phase": "implementation",
                "has_code": True,
                "validation_score": 0.7,
                "team_size": 3,
                "timeline_weeks": 8
            }
        }


# ============================================================================
# Bayesian Confidence Scoring Models
# ============================================================================

class BayesianConfidenceRequest(BaseModel):
    """Request for Bayesian confidence calculation"""
    phase: str = Field(..., description="Development phase (ideation/design/mvp/implementation/testing)")
    context: dict = Field(..., description="Project context for analysis")
    historical_outcomes: List[bool] = Field(
        default_factory=list,
        description="Historical success/failure outcomes for similar contexts"
    )
    use_fast_mode: bool = Field(
        default=True,
        description="Use fast approximation (<5ms) vs full Bayesian (10-20ms)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "phase": "implementation",
                "context": {
                    "phase": "implementation",
                    "has_code": True,
                    "validation_score": 0.7,
                    "team_size": 3,
                    "timeline_weeks": 8
                },
                "historical_outcomes": [True, True, False, True, True],
                "use_fast_mode": False
            }
        }


class BayesianMetadata(BaseModel):
    """Detailed Bayesian analysis metadata"""
    mode: str = Field(..., description="Calculation mode: fast or full")
    prior_mean: Optional[float] = Field(None, description="Prior confidence from phase")
    likelihood: Optional[float] = Field(None, description="Evidence-based likelihood")
    posterior_mean: Optional[float] = Field(None, description="Bayesian posterior mean")
    credible_interval_lower: float = Field(..., ge=0, le=1, description="95% CI lower bound")
    credible_interval_upper: float = Field(..., ge=0, le=1, description="95% CI upper bound")
    effective_sample_size: Optional[int] = Field(None, description="Statistical power measure")
    uncertainty_magnitude: float = Field(..., ge=0, le=1, description="Uncertainty vector magnitude")
    confidence_precision: Optional[float] = Field(None, description="Inverse variance (higher = more precise)")
    risk_level: str = Field(..., description="Risk assessment: low/medium/high/critical")
    monitoring_level: str = Field(..., description="Monitoring intensity: minimal/standard/enhanced/intensive/critical")
    dominant_dimension: str = Field(..., description="Primary uncertainty source")

    class Config:
        json_schema_extra = {
            "example": {
                "mode": "full",
                "prior_mean": 0.70,
                "likelihood": 0.82,
                "posterior_mean": 0.75,
                "credible_interval_lower": 0.65,
                "credible_interval_upper": 0.79,
                "effective_sample_size": 12,
                "uncertainty_magnitude": 0.32,
                "confidence_precision": 0.08,
                "risk_level": "medium",
                "monitoring_level": "standard",
                "dominant_dimension": "timeline"
            }
        }


class BayesianConfidenceResponse(BaseModel):
    """Response with Bayesian confidence analysis"""
    confidence_score: float = Field(..., ge=0, le=1, description="Bayesian posterior confidence (0-1)")
    state: UncertaintyStateEnum = Field(..., description="Uncertainty state classification")
    decision: str = Field(..., description="GO/GO_WITH_CHECKPOINTS/NO_GO")
    metadata: BayesianMetadata = Field(..., description="Full statistical context")
    recommendations: List[str] = Field(..., description="Actionable recommendations based on state")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "confidence_score": 0.72,
                "state": "probabilistic",
                "decision": "GO",
                "metadata": {
                    "mode": "full",
                    "prior_mean": 0.70,
                    "likelihood": 0.82,
                    "posterior_mean": 0.75,
                    "credible_interval_lower": 0.65,
                    "credible_interval_upper": 0.79,
                    "effective_sample_size": 12,
                    "uncertainty_magnitude": 0.32,
                    "confidence_precision": 0.08,
                    "risk_level": "medium",
                    "monitoring_level": "standard",
                    "dominant_dimension": "timeline"
                },
                "recommendations": [
                    "✓ Good confidence - proceed with standard checkpoints",
                    "📋 Document assumptions and validate periodically"
                ],
                "timestamp": "2025-12-01T02:30:00Z"
            }
        }
