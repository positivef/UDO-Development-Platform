"""
Time Tracking Router

FastAPI endpoints for time tracking and ROI measurement.
"""

import logging
from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from ..core.dependencies import get_time_tracking_service
from ..models.time_tracking import (
    Bottleneck,
    EndTrackingRequest,
    EndTrackingResponse,
    PauseTrackingResponse,
    ResumeTrackingResponse,
    ROIReport,
    StartTrackingRequest,
    StartTrackingResponse,
    TaskMetrics,
    WeeklyReport,
)
from ..services.time_tracking_service import TimeTrackingService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/time-tracking",
    tags=["time-tracking"],
    responses={404: {"description": "Not found"}},
)


@router.post("/start", response_model=StartTrackingResponse)
async def start_tracking(
    request: StartTrackingRequest,
    service: TimeTrackingService = Depends(get_time_tracking_service),
):
    """
    Start tracking a task

    Creates a new tracking session and returns the session ID.

    **Example:**
    ```json
    {
        "task_id": "auth_error_fix_001",
        "task_type": "error_resolution",
        "phase": "implementation",
        "ai_used": "claude",
        "metadata": {
            "error_type": "401",
            "component": "auth_service"
        }
    }
    ```
    """
    try:
        session_id = await service.start_task(
            task_id=request.task_id,
            task_type=request.task_type,
            phase=request.phase,
            ai_used=request.ai_used,
            metadata=request.metadata,
            project_id=request.project_id,
        )

        baseline_seconds = service._get_baseline_seconds(request.task_type)

        return StartTrackingResponse(
            success=True,
            session_id=session_id,
            message=f"Started tracking task {request.task_id}",
            baseline_seconds=baseline_seconds,
        )

    except Exception as e:
        logger.error(f"Failed to start tracking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/end/{session_id}", response_model=EndTrackingResponse)
async def end_tracking(
    session_id: UUID,
    request: EndTrackingRequest,
    service: TimeTrackingService = Depends(get_time_tracking_service),
):
    """
    End task tracking and calculate metrics

    Completes the tracking session and returns calculated metrics including
    time saved, ROI, and efficiency percentage.

    **Example:**
    ```json
    {
        "success": true,
        "metadata": {
            "resolution_method": "tier1_obsidian",
            "lines_changed": 15
        }
    }
    ```
    """
    try:
        metrics = await service.end_task(
            session_id=session_id,
            success=request.success,
            error_message=request.error_message,
            metadata=request.metadata,
        )

        return EndTrackingResponse(
            success=True,
            metrics=metrics,
            message=f"Task completed: {metrics.time_saved_hours:.2f}h saved ({metrics.efficiency_percentage:.1f}% efficiency)",
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to end tracking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pause/{session_id}", response_model=PauseTrackingResponse)
async def pause_tracking(session_id: UUID, service: TimeTrackingService = Depends(get_time_tracking_service)):
    """
    Pause task tracking

    Temporarily pauses the timer for interruptions (meetings, breaks, etc.).
    The paused time will not count toward task duration.
    """
    try:
        from datetime import UTC, datetime

        success = await service.pause_task(session_id)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to pause task (not active or already paused)",
            )

        return PauseTrackingResponse(success=True, message="Task tracking paused", paused_at=datetime.now(UTC))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause tracking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume/{session_id}", response_model=ResumeTrackingResponse)
async def resume_tracking(session_id: UUID, service: TimeTrackingService = Depends(get_time_tracking_service)):
    """
    Resume paused task tracking

    Resumes a previously paused task. The time spent paused will not count
    toward the task duration.
    """
    try:
        from datetime import UTC, datetime

        success = await service.resume_task(session_id)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to resume task (not paused)")

        return ResumeTrackingResponse(success=True, message="Task tracking resumed", resumed_at=datetime.now(UTC))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume tracking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{task_id}", response_model=TaskMetrics)
async def get_task_metrics(task_id: str, service: TimeTrackingService = Depends(get_time_tracking_service)):
    """
    Get metrics for a specific task

    Returns the most recent metrics for the specified task ID.
    """
    try:
        metrics = await service.get_task_metrics(task_id)

        if metrics is None:
            raise HTTPException(status_code=404, detail=f"No metrics found for task {task_id}")

        return metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/roi", response_model=ROIReport)
async def get_roi(
    period: str = Query("weekly", regex="^(daily|weekly|monthly|annual)$"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    service: TimeTrackingService = Depends(get_time_tracking_service),
):
    """
    Get ROI report for specified period

    Calculate comprehensive ROI metrics including:
    - Time saved vs baseline
    - ROI percentage
    - Efficiency gain
    - AI performance breakdown
    - Phase performance breakdown
    - Top time-saving task types
    - Identified bottlenecks

    **Periods:**
    - `daily`: Today's metrics
    - `weekly`: Current week (Monday-Sunday)
    - `monthly`: Current month
    - `annual`: Current year

    **Custom Date Range:**
    Optionally specify `start_date` and `end_date` for custom period.
    """
    try:
        roi_report = await service.calculate_roi(period=period, start_date=start_date, end_date=end_date)

        return roi_report

    except Exception as e:
        logger.error(f"Failed to calculate ROI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bottlenecks", response_model=List[Bottleneck])
async def get_bottlenecks(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    service: TimeTrackingService = Depends(get_time_tracking_service),
):
    """
    Get current bottlenecks

    Identifies tasks that are taking longer than baseline and returns them
    sorted by severity (critical > high > medium > low).

    Bottlenecks are tasks where actual duration exceeds baseline by:
    - **Low**: 10-25% over baseline
    - **Medium**: 25-50% over baseline
    - **High**: 50-100% over baseline
    - **Critical**: >100% over baseline (taking 2x+ expected time)

    **Example Response:**
    ```json
    [
        {
            "task_type": "design_task",
            "avg_duration_seconds": 7200,
            "baseline_seconds": 3600,
            "overhead_seconds": 3600,
            "overhead_percentage": 100.0,
            "frequency": 5,
            "severity": "high"
        }
    ]
    ```
    """
    try:
        bottlenecks = await service.get_bottlenecks(start_date=start_date, end_date=end_date)

        return bottlenecks

    except Exception as e:
        logger.error(f"Failed to get bottlenecks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/weekly", response_model=WeeklyReport)
async def get_weekly_report(
    service: TimeTrackingService = Depends(get_time_tracking_service),
):
    """
    Get weekly summary report

    Generates a comprehensive weekly report including:
    - Complete ROI analysis
    - Week-over-week trends
    - Actionable recommendations

    Reports are generated for the current week (Monday-Sunday).
    """
    try:
        report = await service.generate_weekly_report()
        return report

    except Exception as e:
        logger.error(f"Failed to generate weekly report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends")
async def get_trends(
    days: int = Query(30, ge=7, le=365),
    service: TimeTrackingService = Depends(get_time_tracking_service),
):
    """
    Get productivity trends over time

    Returns daily/weekly aggregated metrics for trend analysis.

    **Parameters:**
    - `days`: Number of days to analyze (7-365, default: 30)

    **Example Response:**
    ```json
    {
        "period_days": 30,
        "data_points": [
            {
                "date": "2025-11-20",
                "tasks_completed": 15,
                "time_saved_hours": 6.5,
                "roi_percentage": 450.0,
                "efficiency_percentage": 82.5
            }
        ],
        "overall_trend": "improving",
        "avg_daily_time_saved": 4.2
    }
    ```
    """
    try:
        from datetime import timedelta

        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Get tasks for period
        tasks = await service._get_tasks_for_period(start_date, end_date)

        # Group by day
        daily_stats = {}
        for task in tasks:
            task_date = task["start_time"].date()
            if task_date not in daily_stats:
                daily_stats[task_date] = {
                    "date": task_date.isoformat(),
                    "tasks": [],
                    "tasks_completed": 0,
                    "time_saved_seconds": 0,
                    "duration_seconds": 0,
                    "baseline_seconds": 0,
                }

            daily_stats[task_date]["tasks"].append(task)
            daily_stats[task_date]["tasks_completed"] += 1
            daily_stats[task_date]["time_saved_seconds"] += task["time_saved_seconds"]
            daily_stats[task_date]["duration_seconds"] += task["duration_seconds"]
            daily_stats[task_date]["baseline_seconds"] += task["baseline_seconds"]

        # Calculate metrics for each day
        data_points = []
        for task_date, stats in sorted(daily_stats.items()):
            time_saved_hours = stats["time_saved_seconds"] / 3600
            roi_percentage = (
                (stats["time_saved_seconds"] / stats["duration_seconds"] * 100) if stats["duration_seconds"] > 0 else 0
            )
            efficiency_percentage = (
                (stats["time_saved_seconds"] / stats["baseline_seconds"] * 100) if stats["baseline_seconds"] > 0 else 0
            )

            data_points.append(
                {
                    "date": stats["date"],
                    "tasks_completed": stats["tasks_completed"],
                    "time_saved_hours": round(time_saved_hours, 2),
                    "roi_percentage": round(roi_percentage, 1),
                    "efficiency_percentage": round(efficiency_percentage, 1),
                }
            )

        # Calculate overall trend
        if len(data_points) >= 2:
            first_half = data_points[: len(data_points) // 2]
            second_half = data_points[len(data_points) // 2 :]

            avg_first = sum(d["time_saved_hours"] for d in first_half) / len(first_half) if first_half else 0
            avg_second = sum(d["time_saved_hours"] for d in second_half) / len(second_half) if second_half else 0

            if avg_second > avg_first * 1.1:
                overall_trend = "improving"
            elif avg_second < avg_first * 0.9:
                overall_trend = "declining"
            else:
                overall_trend = "stable"
        else:
            overall_trend = "insufficient_data"

        # Calculate average daily time saved
        total_time_saved = sum(d["time_saved_hours"] for d in data_points)
        avg_daily_time_saved = total_time_saved / days if days > 0 else 0

        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "data_points": data_points,
            "overall_trend": overall_trend,
            "avg_daily_time_saved": round(avg_daily_time_saved, 2),
            "total_time_saved_hours": round(total_time_saved, 2),
            "total_tasks": sum(d["tasks_completed"] for d in data_points),
        }

    except Exception as e:
        logger.error(f"Failed to get trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check endpoint

    Returns the status of the time tracking service.
    """
    return {"status": "healthy", "service": "time_tracking", "version": "1.0.0"}
