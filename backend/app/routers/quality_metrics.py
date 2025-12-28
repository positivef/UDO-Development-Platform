"""
Quality Metrics API Routes

API endpoints for code quality metrics and test coverage
"""

import logging
from typing import Optional

from app.models.quality_metrics import QualityMetricsResponse
from app.services.quality_service import quality_service
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quality-metrics", tags=["Quality Metrics"])


@router.get(
    "",
    response_model=QualityMetricsResponse,
    summary="Get quality metrics",
    description="""
    Collect and return comprehensive quality metrics for the project.

    Includes:
    - Pylint score and issues for Python code
    - ESLint score and issues for TypeScript/JavaScript code
    - Test coverage percentage and test results
    - Overall weighted quality score

    **Note**: This endpoint runs analysis tools which may take 5-30 seconds.
    """,
)
async def get_quality_metrics(
    project_id: Optional[str] = Query(
        None, description="Project ID (reserved for multi-project support)"
    )
) -> QualityMetricsResponse:
    """
    Get comprehensive quality metrics

    Args:
        project_id: Optional project ID (not yet implemented)

    Returns:
        QualityMetricsResponse with all metrics
    """
    try:
        logger.info("Collecting quality metrics...")

        # Get all metrics
        metrics = quality_service.get_all_metrics()

        logger.info(
            f"Quality metrics collected. Overall score: {metrics['overall_score']}"
        )

        return QualityMetricsResponse(**metrics)

    except Exception as e:
        logger.error(f"Error collecting quality metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to collect quality metrics: {str(e)}"
        )


@router.get(
    "/pylint",
    summary="Get Pylint metrics only",
    description="Run Pylint analysis on Python code and return metrics",
)
async def get_pylint_metrics():
    """Get Pylint metrics for Python code"""
    try:
        metrics = quality_service.get_pylint_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting Pylint metrics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get Pylint metrics: {str(e)}"
        )


@router.get(
    "/eslint",
    summary="Get ESLint metrics only",
    description="Run ESLint analysis on TypeScript/JavaScript code and return metrics",
)
async def get_eslint_metrics():
    """Get ESLint metrics for TypeScript/JavaScript code"""
    try:
        metrics = quality_service.get_eslint_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting ESLint metrics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get ESLint metrics: {str(e)}"
        )


@router.get(
    "/coverage",
    summary="Get test coverage metrics only",
    description="Run pytest with coverage and return metrics",
)
async def get_coverage_metrics():
    """Get test coverage metrics"""
    try:
        metrics = quality_service.get_test_coverage_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting coverage metrics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get coverage metrics: {str(e)}"
        )


@router.post(
    "/refresh",
    response_model=QualityMetricsResponse,
    summary="Refresh quality metrics",
    description="Force refresh of all quality metrics (same as GET but explicit about refresh)",
)
async def refresh_quality_metrics() -> QualityMetricsResponse:
    """
    Refresh and return quality metrics

    This endpoint is identical to GET /quality-metrics but uses POST
    to make it clear that analysis tools are being run.
    """
    try:
        logger.info("Refreshing quality metrics...")
        metrics = quality_service.get_all_metrics()
        return QualityMetricsResponse(**metrics)
    except Exception as e:
        logger.error(f"Error refreshing quality metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to refresh quality metrics: {str(e)}"
        )
