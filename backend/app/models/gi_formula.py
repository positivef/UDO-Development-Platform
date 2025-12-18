"""
GI Formula Data Models

Pydantic models for Genius Insight Formula (5-stage insight generation)
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class StageType(str, Enum):
    """GI Formula stage types"""
    OBSERVATION = "observation"
    CONNECTION = "connection"
    PATTERN = "pattern"
    SYNTHESIS = "synthesis"
    BIAS_CHECK = "bias_check"


class StageResult(BaseModel):
    """Result from a single GI Formula stage"""
    stage: StageType
    content: str = Field(..., description="Stage output content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Stage-specific metadata")
    duration_ms: int = Field(..., ge=0, description="Execution time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "stage": "observation",
                "content": "Key facts: API response time is 200ms, target is 100ms...",
                "metadata": {"facts_count": 5, "patterns_found": 3},
                "duration_ms": 4800,
                "timestamp": "2025-11-20T14:30:00"
            }
        }


class BiasCheckResult(BaseModel):
    """Bias check analysis result"""
    biases_detected: List[str] = Field(
        default_factory=list,
        description="List of cognitive biases detected"
    )
    mitigation_strategies: List[str] = Field(
        default_factory=list,
        description="Strategies to mitigate detected biases"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in bias-free analysis"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "biases_detected": ["confirmation bias", "availability heuristic"],
                "mitigation_strategies": [
                    "Consider counter-evidence",
                    "Use data-driven validation"
                ],
                "confidence_score": 0.85
            }
        }


class GIFormulaRequest(BaseModel):
    """Request to generate insight using GI Formula"""
    problem: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Problem to analyze"
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context for analysis"
    )
    project: Optional[str] = Field(
        "UDO-Development-Platform",
        description="Project name"
    )

    @validator('problem')
    def validate_problem(cls, v):
        """Validate problem statement"""
        # Check for meaningful content
        if len(v.strip().split()) < 3:
            raise ValueError("Problem must contain at least 3 words")

        # Basic spam filter
        spam_patterns = ['test test test', 'asdf', 'xxxx', '1234']
        if any(pattern in v.lower() for pattern in spam_patterns):
            raise ValueError("Invalid problem statement")

        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "problem": "How can we reduce API response time by 50%?",
                "context": {
                    "current_latency": "200ms",
                    "target_latency": "100ms",
                    "bottleneck": "database queries"
                },
                "project": "UDO-Development-Platform"
            }
        }


class GIFormulaResult(BaseModel):
    """Complete GI Formula insight result"""
    id: str = Field(..., description="Unique insight ID")
    problem: str = Field(..., description="Original problem statement")
    stages: Dict[str, StageResult] = Field(
        ...,
        description="Results from each of the 5 stages"
    )
    final_insight: str = Field(..., description="Synthesized actionable insight")
    bias_check: BiasCheckResult = Field(..., description="Bias check analysis")
    total_duration_ms: int = Field(..., ge=0, description="Total execution time")
    created_at: datetime = Field(default_factory=datetime.now)
    project: Optional[str] = Field("UDO-Development-Platform")
    obsidian_path: Optional[str] = Field(
        None,
        description="Path to saved Obsidian note"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "gi-2025-11-20-001",
                "problem": "How can we reduce API response time by 50%?",
                "final_insight": "Implement connection pooling and add Redis cache layer for frequently accessed data...",
                "bias_check": {
                    "biases_detected": [],
                    "mitigation_strategies": [],
                    "confidence_score": 0.92
                },
                "total_duration_ms": 28500,
                "created_at": "2025-11-20T14:30:00",
                "obsidian_path": "[EMOJI]/2025-11-20/GI-Insight-API-Performance.md"
            }
        }


class GIInsightSummary(BaseModel):
    """Summary of GI insight for list views"""
    id: str
    problem: str = Field(..., max_length=100)
    final_insight: str = Field(..., max_length=200)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    total_duration_ms: int
    created_at: datetime
    project: Optional[str]

    class Config:
        json_schema_extra = {
            "example": {
                "id": "gi-2025-11-20-001",
                "problem": "How can we reduce API response time by 50%?",
                "final_insight": "Implement connection pooling and add Redis cache layer...",
                "confidence_score": 0.92,
                "total_duration_ms": 28500,
                "created_at": "2025-11-20T14:30:00",
                "project": "UDO-Development-Platform"
            }
        }
