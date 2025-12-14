"""
Quality Metrics Data Models

Pydantic models for quality metrics API
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class PylintIssue(BaseModel):
    """Individual Pylint issue"""
    type: str
    module: str
    line: int
    column: int
    message: str
    message_id: str
    symbol: str


class PylintMetrics(BaseModel):
    """Pylint quality metrics"""
    score: float = Field(..., ge=0.0, le=10.0, description="Pylint score (0-10)")
    total_issues: int = Field(..., ge=0, description="Total number of issues")
    issues_by_type: Dict[str, int] = Field(
        default_factory=dict,
        description="Issues grouped by type (convention, refactor, warning, error, fatal)"
    )
    messages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Sample issues (first 10)"
    )
    analyzed_at: str = Field(..., description="ISO 8601 timestamp")
    error: Optional[str] = Field(None, description="Error message if analysis failed")


class ESLintMetrics(BaseModel):
    """ESLint quality metrics"""
    score: float = Field(..., ge=0.0, le=10.0, description="ESLint score (0-10)")
    total_files: int = Field(..., ge=0, description="Total files analyzed")
    total_errors: int = Field(..., ge=0, description="Total errors found")
    total_warnings: int = Field(..., ge=0, description="Total warnings found")
    total_issues: int = Field(..., ge=0, description="Total issues (errors + warnings)")
    messages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Sample issues (first 10)"
    )
    analyzed_at: str = Field(..., description="ISO 8601 timestamp")
    error: Optional[str] = Field(None, description="Error message if analysis failed")


class TestCoverageMetrics(BaseModel):
    """Test coverage metrics"""
    coverage_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall test coverage percentage"
    )
    tests_total: int = Field(..., ge=0, description="Total number of tests")
    tests_passed: int = Field(..., ge=0, description="Number of passed tests")
    tests_failed: int = Field(..., ge=0, description="Number of failed tests")
    success_rate: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Test success rate percentage"
    )
    files_covered: Optional[int] = Field(None, description="Number of files with coverage")
    analyzed_at: str = Field(..., description="ISO 8601 timestamp")
    error: Optional[str] = Field(None, description="Error message if analysis failed")


class CodeQualityMetrics(BaseModel):
    """Combined code quality metrics"""
    python: PylintMetrics = Field(..., description="Pylint metrics for Python code")
    typescript: ESLintMetrics = Field(..., description="ESLint metrics for TypeScript code")


class QualityMetricsResponse(BaseModel):
    """Complete quality metrics response"""
    overall_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Overall quality score (weighted average)"
    )
    code_quality: CodeQualityMetrics = Field(..., description="Code quality metrics")
    test_metrics: TestCoverageMetrics = Field(..., description="Test coverage metrics")
    collected_at: str = Field(..., description="ISO 8601 timestamp of collection")

    class Config:
        arbitrary_types_allowed = True
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "overall_score": 8.5,
                "code_quality": {
                    "python": {
                        "score": 9.2,
                        "total_issues": 12,
                        "issues_by_type": {
                            "convention": 8,
                            "refactor": 3,
                            "warning": 1,
                            "error": 0,
                            "fatal": 0
                        },
                        "messages": [],
                        "analyzed_at": "2025-11-17T10:00:00"
                    },
                    "typescript": {
                        "score": 8.8,
                        "total_files": 45,
                        "total_errors": 0,
                        "total_warnings": 3,
                        "total_issues": 3,
                        "messages": [],
                        "analyzed_at": "2025-11-17T10:00:05"
                    }
                },
                "test_metrics": {
                    "coverage_percentage": 85.5,
                    "tests_total": 120,
                    "tests_passed": 118,
                    "tests_failed": 2,
                    "success_rate": 98.33,
                    "files_covered": 67,
                    "analyzed_at": "2025-11-17T10:00:10"
                },
                "collected_at": "2025-11-17T10:00:10"
            }
        }


class QualityTrendPoint(BaseModel):
    """Quality metrics at a specific point in time"""
    timestamp: datetime
    overall_score: float
    pylint_score: float
    eslint_score: float
    coverage_percentage: float


class QualityTrendResponse(BaseModel):
    """Historical quality metrics trend"""
    project_id: Optional[str] = None
    trend_data: List[QualityTrendPoint]
    period_start: datetime
    period_end: datetime
    average_score: float
    improvement_percentage: float = Field(
        ...,
        description="Improvement percentage over the period"
    )
