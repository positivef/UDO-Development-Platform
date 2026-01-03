"""
Unit Tests for Time Tracking Service

Tests time tracking, ROI calculation, bottleneck detection, and reporting.
"""

import asyncio
from datetime import date, datetime, timedelta  # noqa: F401
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from backend.app.models.time_tracking import AIModel, Bottleneck, Phase, ROIReport, TaskMetrics, TaskType
from backend.app.services.time_tracking_service import TimeTrackingService


@pytest.fixture
def config_path():
    """Fixture for config path"""
    return Path(__file__).parent.parent / "config" / "baseline_times.yaml"


@pytest.fixture
def time_tracking_service(config_path):
    """Fixture for TimeTrackingService"""
    return TimeTrackingService(pool=None, obsidian_service=None, config_path=config_path)  # Mock mode for testing


class TestTimeTrackingService:
    """Test TimeTrackingService functionality"""

    @pytest.mark.asyncio
    async def test_service_initialization(self, time_tracking_service):
        """Test service initializes correctly"""
        assert time_tracking_service is not None
        assert len(time_tracking_service.baseline_times) > 0
        assert time_tracking_service.config is not None

    @pytest.mark.asyncio
    async def test_baseline_times_loaded(self, time_tracking_service):
        """Test baseline times are loaded correctly"""
        baselines = time_tracking_service.baseline_times

        # Check key task types exist
        assert "error_resolution" in baselines
        assert "design_task" in baselines
        assert "implementation" in baselines
        assert "testing" in baselines

        # Verify values are in seconds
        assert baselines["error_resolution"] == 30 * 60  # 30 minutes
        assert baselines["design_task"] == 120 * 60  # 120 minutes
        assert baselines["testing"] == 60 * 60  # 60 minutes

    @pytest.mark.asyncio
    async def test_get_baseline_seconds(self, time_tracking_service):
        """Test getting baseline seconds for task types"""
        # Test known task types
        assert time_tracking_service._get_baseline_seconds(TaskType.ERROR_RESOLUTION) == 1800
        assert time_tracking_service._get_baseline_seconds(TaskType.DESIGN_TASK) == 7200
        assert time_tracking_service._get_baseline_seconds(TaskType.TESTING) == 3600

    @pytest.mark.asyncio
    async def test_start_task(self, time_tracking_service):
        """Test starting a task"""
        session_id = await time_tracking_service.start_task(
            task_id="test_task_001",
            task_type=TaskType.ERROR_RESOLUTION,
            phase=Phase.IMPLEMENTATION,
            ai_used=AIModel.CLAUDE,
            metadata={"test": "data"},
        )

        assert session_id is not None
        assert isinstance(session_id, UUID)

        # Verify session is in active sessions
        assert str(session_id) in time_tracking_service.active_sessions

    @pytest.mark.asyncio
    async def test_pause_resume_task(self, time_tracking_service):
        """Test pausing and resuming a task"""
        # Start task
        session_id = await time_tracking_service.start_task(
            task_id="test_pause_001",
            task_type=TaskType.IMPLEMENTATION,
            phase=Phase.IMPLEMENTATION,
            ai_used=AIModel.CODEX,
        )

        # Pause task
        paused = await time_tracking_service.pause_task(session_id)
        assert paused is True
        assert str(session_id) in time_tracking_service.paused_sessions

        # Try to pause again (should fail)
        paused_again = await time_tracking_service.pause_task(session_id)
        assert paused_again is False

        # Delay to ensure pause duration > 0 (at least 1 second for int truncation)
        await asyncio.sleep(1.1)

        # Resume task
        resumed = await time_tracking_service.resume_task(session_id)
        assert resumed is True
        assert str(session_id) not in time_tracking_service.paused_sessions

        # Verify pause duration was recorded (>= 1 second due to int truncation)
        session_info = time_tracking_service.active_sessions[str(session_id)]
        assert session_info["total_pause_duration"] >= 1

    @pytest.mark.asyncio
    async def test_end_task_success(self, time_tracking_service):
        """Test ending a task successfully"""
        # Start task
        session_id = await time_tracking_service.start_task(
            task_id="test_end_001",
            task_type=TaskType.ERROR_RESOLUTION,
            phase=Phase.IMPLEMENTATION,
            ai_used=AIModel.CLAUDE,
        )

        # Delay to ensure duration >= 1 second (int truncation needs at least 1s)
        await asyncio.sleep(1.1)

        # End task
        metrics = await time_tracking_service.end_task(
            session_id=session_id,
            success=True,
            metadata={"resolution_method": "tier1_obsidian"},
        )

        # Verify metrics
        assert isinstance(metrics, TaskMetrics)
        assert metrics.task_id == "test_end_001"
        assert metrics.duration_seconds >= 1  # At least 1 second due to int truncation
        assert metrics.baseline_seconds == 1800  # 30 minutes for error_resolution
        assert metrics.time_saved_seconds > 0  # Should have saved time (very fast)
        assert metrics.efficiency_percentage > 0
        assert metrics.roi_percentage >= 0  # Could be 0 for near-instant tasks

        # Verify session is removed from active sessions
        assert str(session_id) not in time_tracking_service.active_sessions

    @pytest.mark.asyncio
    async def test_calculate_task_metrics(self, time_tracking_service):
        """Test task metrics calculation"""
        # Fast task (2 minutes actual vs 30 minutes baseline)
        metrics = time_tracking_service._calculate_task_metrics(
            task_id="test_metrics_001",
            duration_seconds=120,
            baseline_seconds=1800,
            time_saved_seconds=1680,
        )

        assert metrics.task_id == "test_metrics_001"
        assert metrics.duration_seconds == 120
        assert metrics.baseline_seconds == 1800
        assert metrics.time_saved_seconds == 1680
        assert metrics.time_saved_minutes == 28.0
        assert metrics.time_saved_hours == pytest.approx(0.467, rel=0.01)
        assert metrics.efficiency_percentage == pytest.approx(93.33, rel=0.01)
        assert metrics.roi_percentage == pytest.approx(1400.0, rel=0.01)

    @pytest.mark.asyncio
    async def test_calculate_period_dates(self, time_tracking_service):
        """Test period date calculation"""
        # Daily
        start, end = time_tracking_service._calculate_period_dates("daily")
        assert start == date.today()
        assert end == date.today()

        # Weekly
        start, end = time_tracking_service._calculate_period_dates("weekly")
        today = date.today()
        assert start == today - timedelta(days=today.weekday())
        assert end == start + timedelta(days=6)

        # Monthly
        start, end = time_tracking_service._calculate_period_dates("monthly")
        today = date.today()
        assert start == today.replace(day=1)
        assert end >= start

        # Annual
        start, end = time_tracking_service._calculate_period_dates("annual")
        today = date.today()
        assert start == today.replace(month=1, day=1)
        assert end == today.replace(month=12, day=31)

    @pytest.mark.asyncio
    async def test_calculate_ai_breakdown(self, time_tracking_service):
        """Test AI performance breakdown calculation"""
        tasks = [
            {"ai_used": "claude", "time_saved_seconds": 1680},
            {"ai_used": "claude", "time_saved_seconds": 1200},
            {"ai_used": "codex", "time_saved_seconds": 3600},
            {"ai_used": "gemini", "time_saved_seconds": 900},
            {"ai_used": "claude", "time_saved_seconds": 600},
        ]

        breakdown = time_tracking_service._calculate_ai_breakdown(tasks)

        assert "claude" in breakdown
        assert breakdown["claude"]["tasks"] == 3
        assert breakdown["claude"]["time_saved_seconds"] == 3480
        assert breakdown["claude"]["time_saved_hours"] == pytest.approx(0.967, rel=0.01)

        assert "codex" in breakdown
        assert breakdown["codex"]["tasks"] == 1
        assert breakdown["codex"]["time_saved_seconds"] == 3600

        assert "gemini" in breakdown
        assert breakdown["gemini"]["tasks"] == 1

    @pytest.mark.asyncio
    async def test_calculate_phase_breakdown(self, time_tracking_service):
        """Test phase performance breakdown calculation"""
        tasks = [
            {"phase": "implementation", "time_saved_seconds": 3600},
            {"phase": "implementation", "time_saved_seconds": 1800},
            {"phase": "testing", "time_saved_seconds": 2400},
            {"phase": "design", "time_saved_seconds": 1200},
        ]

        breakdown = time_tracking_service._calculate_phase_breakdown(tasks)

        assert "implementation" in breakdown
        assert breakdown["implementation"]["tasks"] == 2
        assert breakdown["implementation"]["time_saved_seconds"] == 5400

        assert "testing" in breakdown
        assert breakdown["testing"]["tasks"] == 1

        assert "design" in breakdown
        assert breakdown["design"]["tasks"] == 1

    @pytest.mark.asyncio
    async def test_calculate_top_time_savers(self, time_tracking_service):
        """Test top time savers calculation"""
        tasks = [
            {"task_type": "error_resolution", "time_saved_seconds": 1680},
            {"task_type": "error_resolution", "time_saved_seconds": 1200},
            {"task_type": "implementation", "time_saved_seconds": 7200},
            {"task_type": "testing", "time_saved_seconds": 1800},
            {"task_type": "documentation", "time_saved_seconds": 600},
        ]

        top_savers = time_tracking_service._calculate_top_time_savers(tasks, top_n=3)

        # Should be sorted by time saved descending
        assert len(top_savers) == 3
        assert top_savers[0]["task_type"] == "implementation"
        assert top_savers[0]["time_saved_seconds"] == 7200
        assert top_savers[1]["task_type"] == "error_resolution"
        assert top_savers[1]["time_saved_seconds"] == 2880

    @pytest.mark.asyncio
    async def test_project_annual(self, time_tracking_service):
        """Test annual projection calculation"""
        # Daily projection
        annual = time_tracking_service._project_annual(2.0, "daily")
        assert annual == pytest.approx(480.0, rel=0.01)  # 2h * 240 work days

        # Weekly projection
        annual = time_tracking_service._project_annual(20.0, "weekly")
        assert annual == pytest.approx(960.0, rel=0.01)  # 20h * 48 weeks

        # Monthly projection
        annual = time_tracking_service._project_annual(80.0, "monthly")
        assert annual == pytest.approx(960.0, rel=0.01)  # 80h * 12 months

        # Annual projection
        annual = time_tracking_service._project_annual(1000.0, "annual")
        assert annual == 1000.0

    @pytest.mark.asyncio
    async def test_empty_roi_report(self, time_tracking_service):
        """Test empty ROI report generation"""
        start = date(2025, 11, 18)
        end = date(2025, 11, 24)

        report = time_tracking_service._empty_roi_report("weekly", start, end)

        assert report.period == "weekly"
        assert report.period_start == start
        assert report.period_end == end
        assert report.manual_time_hours == 0.0
        assert report.actual_time_hours == 0.0
        assert report.time_saved_hours == 0.0
        assert report.roi_percentage == 0.0
        assert report.tasks_completed == 0
        assert len(report.ai_breakdown) == 0
        assert len(report.top_time_savers) == 0

    @pytest.mark.asyncio
    async def test_generate_recommendations(self, time_tracking_service):
        """Test recommendation generation"""
        # Create mock ROI report with bottleneck
        bottleneck = Bottleneck(
            task_type=TaskType.DESIGN_TASK,
            avg_duration_seconds=7200,
            baseline_seconds=3600,
            overhead_seconds=3600,
            overhead_percentage=100.0,
            frequency=5,
            severity="high",
        )

        roi_report = ROIReport(
            period="weekly",
            period_start=date(2025, 11, 18),
            period_end=date(2025, 11, 24),
            manual_time_hours=24.0,
            actual_time_hours=6.0,
            time_saved_hours=18.0,
            roi_percentage=300.0,
            efficiency_gain=75.0,
            annual_projection_hours=936.0,
            annual_projection_value=93600.0,
            tasks_completed=30,
            success_rate=93.3,
            ai_breakdown={
                "claude": {"tasks": 20, "time_saved_hours": 12.0},
                "none": {"tasks": 10, "time_saved_hours": 6.0},
            },
            phase_breakdown={},
            top_time_savers=[],
            bottlenecks=[bottleneck],
        )

        recommendations = time_tracking_service._generate_recommendations(roi_report)

        assert len(recommendations) > 0
        # Should recommend focusing on design_task bottleneck
        assert any("design_task" in rec.lower() for rec in recommendations)
        # Should recommend increasing AI usage (33% without AI)
        assert any("ai usage" in rec.lower() for rec in recommendations)

    @pytest.mark.asyncio
    async def test_calculate_trends(self, time_tracking_service):
        """Test trend calculation"""
        # Current week
        current = ROIReport(
            period="weekly",
            period_start=date(2025, 11, 18),
            period_end=date(2025, 11, 24),
            manual_time_hours=24.0,
            actual_time_hours=4.0,
            time_saved_hours=20.0,
            roi_percentage=500.0,
            efficiency_gain=83.33,
            tasks_completed=45,
            success_rate=95.5,
            ai_breakdown={},
            phase_breakdown={},
            top_time_savers=[],
            bottlenecks=[],
        )

        # Previous week
        previous = ROIReport(
            period="weekly",
            period_start=date(2025, 11, 11),
            period_end=date(2025, 11, 17),
            manual_time_hours=20.0,
            actual_time_hours=5.0,
            time_saved_hours=15.0,
            roi_percentage=300.0,
            efficiency_gain=75.0,
            tasks_completed=35,
            success_rate=91.4,
            ai_breakdown={},
            phase_breakdown={},
            top_time_savers=[],
            bottlenecks=[],
        )

        trends = time_tracking_service._calculate_trends(current, previous)

        assert "roi_change" in trends
        assert "efficiency_change" in trends
        assert "tasks_change" in trends
        assert "time_saved_change" in trends

        # ROI improved from 300% to 500% = +66.67%
        assert "+66.7%" in trends["roi_change"] or "+66.6%" in trends["roi_change"]

        # Tasks increased by 10
        assert trends["tasks_change"] == "+10"

    @pytest.mark.asyncio
    async def test_performance_overhead(self, time_tracking_service):
        """Test that time tracking overhead is minimal"""
        import time

        # Measure start_task overhead
        start_time = time.perf_counter()
        session_id = await time_tracking_service.start_task(
            task_id="perf_test_001",
            task_type=TaskType.ERROR_RESOLUTION,
            phase=Phase.IMPLEMENTATION,
            ai_used=AIModel.CLAUDE,
        )
        start_overhead = (time.perf_counter() - start_time) * 1000  # Convert to ms

        # Start overhead should be < 5ms
        assert start_overhead < 5.0, f"Start overhead too high: {start_overhead:.2f}ms"

        # Measure end_task overhead
        await asyncio.sleep(0.01)  # Minimum task duration

        end_time = time.perf_counter()
        await time_tracking_service.end_task(session_id=session_id, success=True)
        end_overhead = (time.perf_counter() - end_time) * 1000  # Convert to ms

        # End overhead should be < 5ms (without database)
        assert end_overhead < 5.0, f"End overhead too high: {end_overhead:.2f}ms"

        # Total overhead should be < 10ms
        total_overhead = start_overhead + end_overhead
        assert total_overhead < 10.0, f"Total overhead too high: {total_overhead:.2f}ms"

    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, time_tracking_service):
        """Test handling multiple concurrent sessions"""
        # Start multiple tasks concurrently
        tasks = []
        for i in range(10):
            task_coro = time_tracking_service.start_task(
                task_id=f"concurrent_test_{i}",
                task_type=TaskType.ERROR_RESOLUTION,
                phase=Phase.IMPLEMENTATION,
                ai_used=AIModel.CLAUDE,
            )
            tasks.append(task_coro)

        session_ids = await asyncio.gather(*tasks)

        # All should have unique session IDs
        assert len(session_ids) == 10
        assert len(set(str(sid) for sid in session_ids)) == 10

        # All should be in active sessions
        for session_id in session_ids:
            assert str(session_id) in time_tracking_service.active_sessions

        # End all tasks
        end_tasks = []
        for session_id in session_ids:
            end_coro = time_tracking_service.end_task(session_id, success=True)
            end_tasks.append(end_coro)

        metrics_list = await asyncio.gather(*end_tasks)

        # All should have valid metrics
        assert len(metrics_list) == 10
        for metrics in metrics_list:
            assert isinstance(metrics, TaskMetrics)
            assert metrics.duration_seconds >= 0


class TestTimeTrackingIntegration:
    """Integration tests for complete workflows"""

    @pytest.mark.asyncio
    async def test_complete_task_workflow(self, time_tracking_service):
        """Test complete task tracking workflow"""
        # 1. Start task
        session_id = await time_tracking_service.start_task(
            task_id="workflow_test_001",
            task_type=TaskType.ERROR_RESOLUTION,
            phase=Phase.IMPLEMENTATION,
            ai_used=AIModel.CLAUDE,
            metadata={"error_type": "401", "component": "auth"},
        )

        assert session_id is not None

        # 2. Work briefly before pause
        await asyncio.sleep(0.5)

        # 3. Pause task (simulating interruption)
        paused = await time_tracking_service.pause_task(session_id)
        assert paused is True

        # 4. Simulate pause duration (at least 1s for int truncation)
        await asyncio.sleep(1.1)

        # 5. Resume task
        resumed = await time_tracking_service.resume_task(session_id)
        assert resumed is True

        # 6. Work on task (at least 1s total active time for int truncation)
        await asyncio.sleep(0.6)

        # 7. End task
        metrics = await time_tracking_service.end_task(
            session_id=session_id,
            success=True,
            metadata={"resolution_method": "tier1_obsidian", "fix_time": "2min"},
        )

        # Verify complete workflow
        assert metrics.task_id == "workflow_test_001"
        assert metrics.duration_seconds >= 1  # At least 1 second active time
        assert metrics.time_saved_seconds > 0  # Should have saved time
        assert metrics.efficiency_percentage > 0
        assert metrics.roi_percentage >= 0  # Could be 0 for fast tasks

        # Verify pause was accounted for (duration should be less than total elapsed)
        session_info = time_tracking_service.active_sessions.get(str(session_id))
        # Session should be removed after ending
        assert session_info is None

    @pytest.mark.asyncio
    async def test_error_recovery(self, time_tracking_service):
        """Test error recovery scenarios"""
        # Try to pause non-existent session
        fake_id = uuid4()
        paused = await time_tracking_service.pause_task(fake_id)
        assert paused is False

        # Try to resume non-existent session
        resumed = await time_tracking_service.resume_task(fake_id)
        assert resumed is False

        # Try to end non-existent session
        with pytest.raises(ValueError):
            await time_tracking_service.end_task(fake_id, success=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
