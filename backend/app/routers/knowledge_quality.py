"""
Knowledge Quality API Router

FastAPI router for knowledge extraction quality gates.
Provides endpoints for quality validation and monitoring.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.models.knowledge_quality import (
    ContinuousMonitoringResult,
    KnowledgeQualityReport,
    PostExtractionGateResult,
    PreExtractionGateResult,
    QualityThresholds,
    StaleContentAlert,
)
from app.services.knowledge_quality_gate_service import (
    knowledge_quality_gate_service,
    KnowledgeQualityGateService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge-quality", tags=["Knowledge Quality"])


# ============================================================================
# Request/Response Models
# ============================================================================


class ValidateInputRequest(BaseModel):
    """Request to validate input content."""

    content: str = Field(..., min_length=1, description="Content to validate")
    file_path: Optional[str] = Field(None, description="Source file path")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ValidateInputResponse(BaseModel):
    """Response from input validation."""

    is_valid: bool
    token_estimate: int
    file_type: Optional[str]
    errors: List[str]
    warnings: List[str]


class ValidateExtractionRequest(BaseModel):
    """Request to validate extraction output."""

    extraction_data: Dict[str, Any] = Field(..., description="Extraction output to validate")
    source_content: str = Field(..., description="Original source content")
    document_id: Optional[UUID] = Field(None, description="Document ID for tracking")


class ValidateExtractionResponse(BaseModel):
    """Response from extraction validation."""

    passed: bool
    quality_level: str
    total_char_count: int
    categories_covered: int
    g_eval_score: Optional[float]
    actionability_score: Optional[float]
    gates: Dict[str, str]
    improvement_suggestions: List[str]


class GenerateReportRequest(BaseModel):
    """Request to generate comprehensive quality report."""

    content: str = Field(..., min_length=1, description="Source content")
    extraction_data: Dict[str, Any] = Field(..., description="Extraction output")
    file_path: Optional[str] = Field(None, description="Source file path")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    document_id: Optional[UUID] = Field(None, description="Document ID for tracking")


class RegisterDocumentRequest(BaseModel):
    """Request to register document for monitoring."""

    document_id: UUID
    document_path: str
    content_hash: str


class RecordFeedbackRequest(BaseModel):
    """Request to record user feedback."""

    document_id: UUID
    helpful: Optional[bool] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None


class ThresholdConfigRequest(BaseModel):
    """Request to update quality thresholds."""

    min_total_chars: Optional[int] = Field(None, ge=100)
    target_total_chars: Optional[int] = Field(None, ge=1000)
    min_category_chars: Optional[int] = Field(None, ge=50)
    target_category_chars: Optional[int] = Field(None, ge=500)
    min_categories_required: Optional[int] = Field(None, ge=1, le=5)
    min_g_eval_score: Optional[float] = Field(None, ge=1.0, le=5.0)
    min_actionability_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class QualityStatsResponse(BaseModel):
    """Response with quality statistics."""

    total_documents: int
    documents_by_quality: Dict[str, int]
    average_g_eval: Optional[float]
    average_actionability: Optional[float]
    stale_content_count: int
    active_alerts_count: int


# ============================================================================
# Dependency Injection
# ============================================================================


def get_quality_service() -> KnowledgeQualityGateService:
    """Get quality gate service instance."""
    return knowledge_quality_gate_service


# ============================================================================
# Pre-Extraction Endpoints
# ============================================================================


@router.post(
    "/validate/input",
    response_model=ValidateInputResponse,
    summary="Validate input content",
    description="Validate content before knowledge extraction. Checks size, encoding, and context.",
)
async def validate_input(
    request: ValidateInputRequest,
    service: KnowledgeQualityGateService = Depends(get_quality_service),
) -> ValidateInputResponse:
    """Validate input content before extraction."""
    try:
        result = service.validate_input(
            content=request.content,
            file_path=request.file_path,
            context=request.context,
        )

        return ValidateInputResponse(
            is_valid=result.is_valid,
            token_estimate=result.token_estimate,
            file_type=result.file_type.value if result.file_type else None,
            errors=result.errors,
            warnings=result.warnings,
        )

    except Exception as e:
        logger.error(f"Input validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}",
        )


@router.post(
    "/validate/pre-extraction",
    response_model=PreExtractionGateResult,
    summary="Run pre-extraction gates",
    description="Run all pre-extraction quality gates including input validation and context checks.",
)
async def run_pre_extraction_gates(
    request: ValidateInputRequest,
    service: KnowledgeQualityGateService = Depends(get_quality_service),
) -> PreExtractionGateResult:
    """Run all pre-extraction quality gates."""
    try:
        result = service.run_pre_extraction_gates(
            content=request.content,
            file_path=request.file_path,
            context=request.context,
        )
        return result

    except Exception as e:
        logger.error(f"Pre-extraction gates failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gate execution failed: {str(e)}",
        )


# ============================================================================
# Post-Extraction Endpoints
# ============================================================================


@router.post(
    "/validate/extraction",
    response_model=ValidateExtractionResponse,
    summary="Validate extraction output",
    description="Validate extraction output against quality thresholds. Checks char count, categories, G-Eval, etc.",
)
async def validate_extraction(
    request: ValidateExtractionRequest,
    service: KnowledgeQualityGateService = Depends(get_quality_service),
) -> ValidateExtractionResponse:
    """Validate extraction output."""
    try:
        result = service.run_post_extraction_gates(
            extraction_data=request.extraction_data,
            source_content=request.source_content,
            document_id=request.document_id,
        )

        return ValidateExtractionResponse(
            passed=result.passed,
            quality_level=result.quality_level.value,
            total_char_count=result.total_char_count,
            categories_covered=result.categories_covered,
            g_eval_score=result.g_eval.overall if result.g_eval else None,
            actionability_score=result.actionability.score if result.actionability else None,
            gates={k: v.value for k, v in result.gates.items()},
            improvement_suggestions=result.improvement_suggestions,
        )

    except Exception as e:
        logger.error(f"Extraction validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}",
        )


@router.post(
    "/validate/post-extraction",
    response_model=PostExtractionGateResult,
    summary="Run post-extraction gates",
    description="Run all post-extraction quality gates with detailed results.",
)
async def run_post_extraction_gates(
    request: ValidateExtractionRequest,
    service: KnowledgeQualityGateService = Depends(get_quality_service),
) -> PostExtractionGateResult:
    """Run all post-extraction quality gates."""
    try:
        result = service.run_post_extraction_gates(
            extraction_data=request.extraction_data,
            source_content=request.source_content,
            document_id=request.document_id,
        )
        return result

    except Exception as e:
        logger.error(f"Post-extraction gates failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gate execution failed: {str(e)}",
        )


# ============================================================================
# Comprehensive Report Endpoint
# ============================================================================


@router.post(
    "/report",
    response_model=KnowledgeQualityReport,
    summary="Generate quality report",
    description="Generate comprehensive quality report covering all gate types.",
)
async def generate_quality_report(
    request: GenerateReportRequest,
    service: KnowledgeQualityGateService = Depends(get_quality_service),
) -> KnowledgeQualityReport:
    """Generate comprehensive quality report."""
    try:
        report = service.generate_quality_report(
            content=request.content,
            extraction_data=request.extraction_data,
            file_path=request.file_path,
            context=request.context,
            document_id=request.document_id,
        )
        return report

    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}",
        )


# ============================================================================
# Continuous Monitoring Endpoints
# ============================================================================


@router.post(
    "/monitoring/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register document for monitoring",
    description="Register a document for continuous quality monitoring.",
)
async def register_document(
    request: RegisterDocumentRequest,
    service: KnowledgeQualityGateService = Depends(get_quality_service),
) -> Dict[str, Any]:
    """Register document for monitoring."""
    try:
        service.register_document(
            document_id=request.document_id,
            document_path=request.document_path,
            content_hash=request.content_hash,
        )

        return {
            "success": True,
            "document_id": str(request.document_id),
            "message": "Document registered for monitoring",
        }

    except Exception as e:
        logger.error(f"Document registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


@router.post(
    "/monitoring/view/{document_id}",
    summary="Track document view",
    description="Record a view for the specified document.",
)
async def track_view(
    document_id: UUID,
    service: KnowledgeQualityGateService = Depends(get_quality_service),
) -> Dict[str, Any]:
    """Track document view."""
    try:
        service.track_view(document_id)
        return {
            "success": True,
            "document_id": str(document_id),
            "message": "View recorded",
        }

    except Exception as e:
        logger.error(f"View tracking failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tracking failed: {str(e)}",
        )


@router.post(
    "/monitoring/feedback",
    summary="Record user feedback",
    description="Record user feedback for a document (helpful votes, ratings, comments).",
)
async def record_feedback(
    request: RecordFeedbackRequest,
    service: KnowledgeQualityGateService = Depends(get_quality_service),
) -> Dict[str, Any]:
    """Record user feedback."""
    try:
        service.record_feedback(
            document_id=request.document_id,
            helpful=request.helpful,
            rating=request.rating,
            comment=request.comment,
        )

        return {
            "success": True,
            "document_id": str(request.document_id),
            "message": "Feedback recorded",
        }

    except Exception as e:
        logger.error(f"Feedback recording failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feedback failed: {str(e)}",
        )


@router.get(
    "/monitoring/status/{document_id}",
    response_model=ContinuousMonitoringResult,
    summary="Get monitoring status",
    description="Get comprehensive monitoring status for a document.",
)
async def get_monitoring_status(
    document_id: UUID,
    service: KnowledgeQualityGateService = Depends(get_quality_service),
) -> ContinuousMonitoringResult:
    """Get document monitoring status."""
    try:
        result = service.get_monitoring_status(document_id)
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Monitoring status retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status retrieval failed: {str(e)}",
        )


@router.get(
    "/monitoring/alerts",
    response_model=List[StaleContentAlert],
    summary="Get stale content alerts",
    description="Get all active stale content alerts across registered documents.",
)
async def get_stale_alerts(
    service: KnowledgeQualityGateService = Depends(get_quality_service),
) -> List[StaleContentAlert]:
    """Get stale content alerts."""
    try:
        alerts = service.generate_stale_alerts()
        return alerts

    except Exception as e:
        logger.error(f"Alert generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Alert generation failed: {str(e)}",
        )


# ============================================================================
# Configuration Endpoints
# ============================================================================


@router.get(
    "/config/thresholds",
    response_model=QualityThresholds,
    summary="Get quality thresholds",
    description="Get current quality threshold configuration.",
)
async def get_thresholds(
    service: KnowledgeQualityGateService = Depends(get_quality_service),
) -> QualityThresholds:
    """Get current quality thresholds."""
    return service.thresholds


@router.put(
    "/config/thresholds",
    response_model=QualityThresholds,
    summary="Update quality thresholds",
    description="Update quality threshold configuration.",
)
async def update_thresholds(
    request: ThresholdConfigRequest,
    service: KnowledgeQualityGateService = Depends(get_quality_service),
) -> QualityThresholds:
    """Update quality thresholds."""
    try:
        # Update only provided fields
        current = service.thresholds

        if request.min_total_chars is not None:
            current.min_total_chars = request.min_total_chars
        if request.target_total_chars is not None:
            current.target_total_chars = request.target_total_chars
        if request.min_category_chars is not None:
            current.min_category_chars = request.min_category_chars
        if request.target_category_chars is not None:
            current.target_category_chars = request.target_category_chars
        if request.min_categories_required is not None:
            current.min_categories_required = request.min_categories_required
        if request.min_g_eval_score is not None:
            current.min_g_eval_score = request.min_g_eval_score
        if request.min_actionability_score is not None:
            current.min_actionability_score = request.min_actionability_score

        logger.info(f"Updated quality thresholds: {current}")
        return current

    except Exception as e:
        logger.error(f"Threshold update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}",
        )


# ============================================================================
# Statistics Endpoints
# ============================================================================


@router.get(
    "/stats",
    response_model=QualityStatsResponse,
    summary="Get quality statistics",
    description="Get aggregate quality statistics across all monitored documents.",
)
async def get_quality_stats(
    service: KnowledgeQualityGateService = Depends(get_quality_service),
) -> QualityStatsResponse:
    """Get quality statistics."""
    try:
        # Get all alerts
        alerts = service.generate_stale_alerts()

        # Calculate stats from registered documents
        total_docs = len(service._document_registry)

        # Get quality distribution (would need to track this in production)
        quality_dist: Dict[str, int] = {
            "excellent": 0,
            "good": 0,
            "acceptable": 0,
            "poor": 0,
            "rejected": 0,
        }

        # Count stale content
        stale_count = sum(1 for a in alerts if a.alert_type == "stale")

        return QualityStatsResponse(
            total_documents=total_docs,
            documents_by_quality=quality_dist,
            average_g_eval=None,  # Would need tracking
            average_actionability=None,  # Would need tracking
            stale_content_count=stale_count,
            active_alerts_count=len(alerts),
        )

    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stats retrieval failed: {str(e)}",
        )


# ============================================================================
# Health Check
# ============================================================================


@router.get(
    "/health",
    summary="Health check",
    description="Check if quality gate service is operational.",
)
async def health_check(
    service: KnowledgeQualityGateService = Depends(get_quality_service),
) -> Dict[str, Any]:
    """Health check for quality gate service."""
    return {
        "status": "healthy",
        "service": "knowledge_quality_gate_service",
        "thresholds": {
            "min_chars": service.thresholds.min_total_chars,
            "target_chars": service.thresholds.target_total_chars,
            "min_g_eval": service.thresholds.min_g_eval_score,
        },
        "registered_documents": len(service._document_registry),
        "ai_scoring_enabled": service.enable_ai_scoring,
    }
