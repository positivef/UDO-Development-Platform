"""
Time Tracking Service

Comprehensive time tracking and ROI measurement system for UDO Development Platform.
Tracks task execution time, calculates ROI, identifies bottlenecks, and generates reports.
"""

import asyncio
import logging
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import yaml

from ..models.time_tracking import (AIModel, Bottleneck, Phase, ROIReport,
                                    TaskMetrics, TaskSession,
                                    TaskSessionCreate, TaskSessionUpdate,
                                    TaskType, TimeMetrics, WeeklyReport)

logger = logging.getLogger(__name__)


class TimeTrackingService:
    """
    Service for time tracking and ROI measurement

    Features:
    - Millisecond-precision time tracking
    - Automatic baseline comparison
    - ROI calculation (daily/weekly/monthly/annual)
    - Bottleneck detection
    - AI performance analysis
    - Phase performance tracking
    - Obsidian integration
    """

    def __init__(
        self, pool=None, obsidian_service=None, config_path: Optional[Path] = None
    ):
        """
        Initialize Time Tracking Service

        Args:
            pool: Database connection pool (asyncpg)
            obsidian_service: ObsidianService instance for knowledge sync
            config_path: Path to baseline_times.yaml (auto-detected if not provided)
        """
        self.pool = pool
        self.obsidian_service = obsidian_service

        # Load baseline configuration
        if config_path is None:
            config_path = (
                Path(__file__).parent.parent.parent / "config" / "baseline_times.yaml"
            )

        self.config = self._load_config(config_path)
        self.baseline_times: Dict[str, int] = self._extract_baseline_times()

        # In-memory session tracking (for pause/resume)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.paused_sessions: Dict[str, datetime] = {}

        logger.info(
            "TimeTrackingService initialized with %d baseline types",
            len(self.baseline_times),
        )

    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded baseline configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            # Return default config
            return {
                "baselines": {
                    "error_resolution": {"manual_minutes": 30},
                    "design_task": {"manual_minutes": 120},
                    "implementation": {"manual_minutes": 240},
                    "testing": {"manual_minutes": 60},
                    "documentation": {"manual_minutes": 60},
                    "code_review": {"manual_minutes": 30},
                    "refactoring": {"manual_minutes": 180},
                    "debugging": {"manual_minutes": 45},
                    "phase_transition": {"manual_minutes": 15},
                    "other": {"manual_minutes": 30},
                },
                "roi_settings": {"hourly_rate": 100},
            }

    def _extract_baseline_times(self) -> Dict[str, int]:
        """Extract baseline times in seconds from config"""
        baselines = {}
        for task_type, data in self.config.get("baselines", {}).items():
            manual_minutes = data.get("manual_minutes", 30)
            baselines[task_type] = manual_minutes * 60  # Convert to seconds
        return baselines

    def _get_baseline_seconds(self, task_type: TaskType) -> int:
        """Get baseline time in seconds for a task type"""
        baseline_key = task_type.value
        return self.baseline_times.get(baseline_key, 1800)  # Default: 30 minutes

    async def start_task(
        self,
        task_id: str,
        task_type: TaskType,
        phase: Phase = Phase.IMPLEMENTATION,
        ai_used: AIModel = AIModel.NONE,
        metadata: Optional[Dict[str, Any]] = None,
        project_id: Optional[UUID] = None,
    ) -> UUID:
        """
        Start tracking a task

        Args:
            task_id: Unique task identifier
            task_type: Type of task
            phase: Development phase
            ai_used: AI model used
            metadata: Additional task metadata
            project_id: Associated project ID

        Returns:
            session_id: Unique session ID for this tracking session
        """
        try:
            # Get baseline time
            baseline_seconds = self._get_baseline_seconds(task_type)

            # Create session
            start_time = datetime.now(UTC)
            session_create = TaskSessionCreate(
                task_id=task_id,
                task_type=task_type,
                phase=phase,
                ai_used=ai_used,
                baseline_seconds=baseline_seconds,
                metadata=metadata,
                project_id=project_id,
            )

            # Insert into database
            query = """
                INSERT INTO task_sessions (
                    task_id, task_type, phase, ai_used,
                    start_time, baseline_seconds, success, metadata, project_id
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
            """

            if self.pool:
                async with self.pool.acquire() as conn:
                    session_id = await conn.fetchval(
                        query,
                        task_id,
                        task_type.value,
                        phase.value,
                        ai_used.value,
                        start_time,
                        baseline_seconds,
                        False,  # success = False until completed
                        metadata,
                        project_id,
                    )
            else:
                # Mock mode for testing
                from uuid import uuid4

                session_id = uuid4()
                logger.warning("No database pool - running in mock mode")

            # Store in active sessions for pause/resume
            self.active_sessions[str(session_id)] = {
                "task_id": task_id,
                "start_time": start_time,
                "pause_start": None,
                "total_pause_duration": 0,
            }

            logger.info(
                f"Started tracking task {task_id} (session: {session_id}, "
                f"type: {task_type.value}, baseline: {baseline_seconds}s)"
            )

            return session_id

        except Exception as e:
            logger.error(f"Failed to start task tracking: {e}")
            raise

    async def end_task(
        self,
        session_id: UUID,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TaskMetrics:
        """
        End task tracking and calculate metrics

        Args:
            session_id: Session ID from start_task
            success: Whether task completed successfully
            error_message: Error message if task failed
            metadata: Additional result metadata

        Returns:
            TaskMetrics with calculated time savings and ROI
        """
        try:
            end_time = datetime.now(UTC)

            # Get session info from memory
            session_key = str(session_id)
            if session_key not in self.active_sessions:
                logger.warning(f"Session {session_id} not found in active sessions")
                # Try to load from database
                session_info = await self._load_session_from_db(session_id)
                if not session_info:
                    raise ValueError(f"Session {session_id} not found")
            else:
                session_info = self.active_sessions[session_key]

            # Calculate duration
            start_time = session_info["start_time"]
            total_pause_duration = session_info.get("total_pause_duration", 0)
            total_duration_seconds = int((end_time - start_time).total_seconds())
            active_duration_seconds = total_duration_seconds - total_pause_duration

            # Update database
            if self.pool:
                query = """
                    UPDATE task_sessions
                    SET end_time = $1,
                        duration_seconds = $2,
                        pause_duration_seconds = $3,
                        success = $4,
                        error_message = $5,
                        metadata = $6
                    WHERE id = $7
                    RETURNING task_id, task_type, baseline_seconds
                """
                async with self.pool.acquire() as conn:
                    row = await conn.fetchrow(
                        query,
                        end_time,
                        active_duration_seconds,
                        total_pause_duration,
                        success,
                        error_message,
                        metadata,
                        session_id,
                    )

                    if not row:
                        raise ValueError(f"Session {session_id} not found in database")

                    task_id = row["task_id"]
                    baseline_seconds = row["baseline_seconds"]
            else:
                # Mock mode
                task_id = session_info["task_id"]
                baseline_seconds = 1800  # Default

            # Calculate time saved
            time_saved_seconds = baseline_seconds - active_duration_seconds

            # Update time_saved in database
            if self.pool:
                async with self.pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE task_sessions SET time_saved_seconds = $1 WHERE id = $2",
                        time_saved_seconds,
                        session_id,
                    )

            # Calculate metrics
            metrics = self._calculate_task_metrics(
                task_id=task_id,
                duration_seconds=active_duration_seconds,
                baseline_seconds=baseline_seconds,
                time_saved_seconds=time_saved_seconds,
            )

            # Trigger uncertainty adjustment if we overran baseline significantly
            ratio = (
                active_duration_seconds / baseline_seconds if baseline_seconds else 0
            )
            if ratio > 1.2:
                await self._handle_uncertainty_overrun(
                    task_id=task_id,
                    phase=(
                        session_info.get("phase", Phase.IMPLEMENTATION)
                        if isinstance(session_info, dict)
                        else Phase.IMPLEMENTATION
                    ),
                    ratio=ratio,
                )

            # Remove from active sessions
            if session_key in self.active_sessions:
                del self.active_sessions[session_key]
            if session_key in self.paused_sessions:
                del self.paused_sessions[session_key]

            # Sync to Obsidian
            if self.obsidian_service:
                await self._sync_to_obsidian(session_id, metrics, success)

            logger.info(
                f"Ended task {task_id}: {active_duration_seconds}s actual, "
                f"{baseline_seconds}s baseline, {time_saved_seconds}s saved "
                f"({metrics.efficiency_percentage:.1f}% efficiency)"
            )

            return metrics

        except Exception as e:
            logger.error(f"Failed to end task tracking: {e}")
            raise

    async def pause_task(self, session_id: UUID) -> bool:
        """
        Pause task timer

        Useful for interruptions (meetings, breaks, context switches)

        Args:
            session_id: Session ID to pause

        Returns:
            True if successfully paused
        """
        try:
            session_key = str(session_id)

            if session_key not in self.active_sessions:
                logger.warning(f"Cannot pause - session {session_id} not active")
                return False

            if session_key in self.paused_sessions:
                logger.warning(f"Session {session_id} already paused")
                return False

            # Record pause start time
            self.paused_sessions[session_key] = datetime.now(UTC)

            logger.info(f"Paused task session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to pause task: {e}")
            return False

    async def resume_task(self, session_id: UUID) -> bool:
        """
        Resume paused task

        Args:
            session_id: Session ID to resume

        Returns:
            True if successfully resumed
        """
        try:
            session_key = str(session_id)

            if session_key not in self.paused_sessions:
                logger.warning(f"Cannot resume - session {session_id} not paused")
                return False

            # Calculate pause duration
            pause_start = self.paused_sessions[session_key]
            pause_duration = int((datetime.now(UTC) - pause_start).total_seconds())

            # Add to total pause duration
            self.active_sessions[session_key]["total_pause_duration"] += pause_duration

            # Remove from paused sessions
            del self.paused_sessions[session_key]

            logger.info(
                f"Resumed task session {session_id} (paused for {pause_duration}s)"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to resume task: {e}")
            return False

    async def get_task_metrics(self, task_id: str) -> Optional[TaskMetrics]:
        """
        Get metrics for a specific task

        Args:
            task_id: Task identifier

        Returns:
            TaskMetrics if task found, None otherwise
        """
        try:
            if not self.pool:
                logger.warning("No database pool - cannot retrieve metrics")
                return None

            query = """
                SELECT task_id, duration_seconds, baseline_seconds, time_saved_seconds
                FROM task_sessions
                WHERE task_id = $1 AND end_time IS NOT NULL
                ORDER BY end_time DESC
                LIMIT 1
            """

            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, task_id)

                if not row:
                    return None

                return self._calculate_task_metrics(
                    task_id=row["task_id"],
                    duration_seconds=row["duration_seconds"],
                    baseline_seconds=row["baseline_seconds"],
                    time_saved_seconds=row["time_saved_seconds"],
                )

        except Exception as e:
            logger.error(f"Failed to get task metrics: {e}")
            return None

    def _calculate_task_metrics(
        self,
        task_id: str,
        duration_seconds: int,
        baseline_seconds: int,
        time_saved_seconds: int,
    ) -> TaskMetrics:
        """Calculate metrics for a task"""
        time_saved_minutes = time_saved_seconds / 60
        time_saved_hours = time_saved_seconds / 3600

        # Efficiency percentage: how much time was saved relative to baseline
        efficiency_percentage = (
            (time_saved_seconds / baseline_seconds * 100) if baseline_seconds > 0 else 0
        )

        # ROI percentage: return on investment (saved time / actual time spent)
        roi_percentage = (
            (time_saved_seconds / duration_seconds * 100) if duration_seconds > 0 else 0
        )

        return TaskMetrics(
            task_id=task_id,
            duration_seconds=duration_seconds,
            baseline_seconds=baseline_seconds,
            time_saved_seconds=time_saved_seconds,
            time_saved_minutes=time_saved_minutes,
            time_saved_hours=time_saved_hours,
            efficiency_percentage=efficiency_percentage,
            roi_percentage=roi_percentage,
        )

    async def calculate_roi(
        self,
        period: str = "week",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> ROIReport:
        """
        Calculate ROI for specified period

        Args:
            period: "daily", "weekly", "monthly", or "annual"
            start_date: Optional start date (calculated if not provided)
            end_date: Optional end date (calculated if not provided)

        Returns:
            Comprehensive ROI report
        """
        try:
            # Calculate period dates
            if start_date is None or end_date is None:
                start_date, end_date = self._calculate_period_dates(period)

            # Get tasks for period
            tasks = await self._get_tasks_for_period(start_date, end_date)

            if not tasks:
                logger.warning(f"No tasks found for period {start_date} to {end_date}")
                return self._empty_roi_report(period, start_date, end_date)

            # Calculate aggregated metrics
            total_duration = sum(t["duration_seconds"] for t in tasks)
            total_baseline = sum(t["baseline_seconds"] for t in tasks)
            total_saved = sum(t["time_saved_seconds"] for t in tasks)

            # Convert to hours
            manual_time_hours = total_baseline / 3600
            actual_time_hours = total_duration / 3600
            time_saved_hours = total_saved / 3600

            # Calculate ROI
            roi_percentage = (
                (total_saved / total_duration * 100) if total_duration > 0 else 0
            )
            efficiency_gain = (
                (total_saved / total_baseline * 100) if total_baseline > 0 else 0
            )

            # Calculate success rate
            successful_tasks = sum(1 for t in tasks if t["success"])
            success_rate = (successful_tasks / len(tasks) * 100) if tasks else 0

            # AI breakdown
            ai_breakdown = self._calculate_ai_breakdown(tasks)

            # Phase breakdown
            phase_breakdown = self._calculate_phase_breakdown(tasks)

            # Top time savers
            top_time_savers = self._calculate_top_time_savers(tasks)

            # Identify bottlenecks
            bottlenecks = await self.get_bottlenecks(start_date, end_date)

            # Calculate annual projection
            annual_projection_hours = self._project_annual(time_saved_hours, period)
            hourly_rate = self.config.get("roi_settings", {}).get("hourly_rate", 100)
            annual_projection_value = annual_projection_hours * hourly_rate

            return ROIReport(
                period=period,
                period_start=start_date,
                period_end=end_date,
                manual_time_hours=manual_time_hours,
                actual_time_hours=actual_time_hours,
                time_saved_hours=time_saved_hours,
                roi_percentage=roi_percentage,
                efficiency_gain=efficiency_gain,
                annual_projection_hours=annual_projection_hours,
                annual_projection_value=annual_projection_value,
                tasks_completed=len(tasks),
                success_rate=success_rate,
                ai_breakdown=ai_breakdown,
                phase_breakdown=phase_breakdown,
                top_time_savers=top_time_savers,
                bottlenecks=bottlenecks,
            )

        except Exception as e:
            logger.error(f"Failed to calculate ROI: {e}")
            raise

    async def get_bottlenecks(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> List[Bottleneck]:
        """
        Identify bottlenecks (tasks taking longer than baseline)

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            List of bottlenecks sorted by severity
        """
        try:
            if start_date is None:
                start_date = date.today() - timedelta(days=7)
            if end_date is None:
                end_date = date.today()

            tasks = await self._get_tasks_for_period(start_date, end_date)

            # Group by task type
            task_type_stats: Dict[str, List[Dict]] = {}
            for task in tasks:
                task_type = task["task_type"]
                if task_type not in task_type_stats:
                    task_type_stats[task_type] = []
                task_type_stats[task_type].append(task)

            # Calculate bottlenecks
            bottlenecks = []
            thresholds = self.config.get("roi_settings", {}).get(
                "bottleneck_thresholds",
                {"low": 10, "medium": 25, "high": 50, "critical": 100},
            )

            for task_type, task_list in task_type_stats.items():
                avg_duration = sum(t["duration_seconds"] for t in task_list) / len(
                    task_list
                )
                avg_baseline = sum(t["baseline_seconds"] for t in task_list) / len(
                    task_list
                )

                # Only consider if actually slower than baseline
                if avg_duration > avg_baseline:
                    overhead_seconds = int(avg_duration - avg_baseline)
                    overhead_percentage = (
                        (overhead_seconds / avg_baseline * 100)
                        if avg_baseline > 0
                        else 0
                    )

                    # Determine severity
                    if overhead_percentage >= thresholds.get("critical", 100):
                        severity = "critical"
                    elif overhead_percentage >= thresholds.get("high", 50):
                        severity = "high"
                    elif overhead_percentage >= thresholds.get("medium", 25):
                        severity = "medium"
                    else:
                        severity = "low"

                    bottlenecks.append(
                        Bottleneck(
                            task_type=TaskType(task_type),
                            avg_duration_seconds=int(avg_duration),
                            baseline_seconds=int(avg_baseline),
                            overhead_seconds=overhead_seconds,
                            overhead_percentage=overhead_percentage,
                            frequency=len(task_list),
                            severity=severity,
                        )
                    )

            # Sort by severity and overhead
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            bottlenecks.sort(
                key=lambda b: (severity_order[b.severity], -b.overhead_seconds)
            )

            return bottlenecks

        except Exception as e:
            logger.error(f"Failed to get bottlenecks: {e}")
            return []

    async def generate_weekly_report(self) -> WeeklyReport:
        """
        Generate comprehensive weekly report

        Returns:
            WeeklyReport with ROI, trends, and recommendations
        """
        try:
            # Get current week
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)

            # Calculate ROI
            roi_report = await self.calculate_roi("weekly", week_start, week_end)

            # Calculate trends (compare to previous week)
            prev_week_start = week_start - timedelta(days=7)
            prev_week_end = week_start - timedelta(days=1)
            prev_roi = await self.calculate_roi(
                "weekly", prev_week_start, prev_week_end
            )

            trends = self._calculate_trends(roi_report, prev_roi)

            # Generate recommendations
            recommendations = self._generate_recommendations(roi_report)

            return WeeklyReport(
                week_start=week_start,
                week_end=week_end,
                roi_report=roi_report,
                trends=trends,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Failed to generate weekly report: {e}")
            raise

    # Helper methods

    async def _load_session_from_db(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """Load session info from database"""
        if not self.pool:
            return None

        try:
            query = "SELECT task_id, start_time FROM task_sessions WHERE id = $1"
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, session_id)
                if row:
                    return {
                        "task_id": row["task_id"],
                        "start_time": row["start_time"],
                        "total_pause_duration": 0,
                    }
        except Exception as e:
            logger.error(f"Failed to load session from database: {e}")

        return None

    def _calculate_period_dates(self, period: str) -> Tuple[date, date]:
        """Calculate start and end dates for period"""
        today = date.today()

        if period == "daily":
            return today, today
        elif period == "weekly":
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            return week_start, week_end
        elif period == "monthly":
            month_start = today.replace(day=1)
            next_month = month_start + timedelta(days=32)
            month_end = next_month.replace(day=1) - timedelta(days=1)
            return month_start, month_end
        elif period == "annual":
            year_start = today.replace(month=1, day=1)
            year_end = today.replace(month=12, day=31)
            return year_start, year_end
        else:
            # Default to weekly
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            return week_start, week_end

    async def _get_tasks_for_period(
        self, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """Get completed tasks for a period"""
        if not self.pool:
            return []

        try:
            query = """
                SELECT
                    task_id,
                    task_type,
                    phase,
                    ai_used,
                    duration_seconds,
                    baseline_seconds,
                    time_saved_seconds,
                    success,
                    start_time,
                    end_time
                FROM task_sessions
                WHERE end_time IS NOT NULL
                    AND DATE(start_time) >= $1
                    AND DATE(start_time) <= $2
                ORDER BY start_time
            """

            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, start_date, end_date)
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get tasks for period: {e}")
            return []

    def _calculate_ai_breakdown(self, tasks: List[Dict]) -> Dict[str, Dict[str, Any]]:
        """Calculate performance breakdown by AI model"""
        ai_stats: Dict[str, Dict[str, Any]] = {}

        for task in tasks:
            ai_model = task["ai_used"]
            if ai_model not in ai_stats:
                ai_stats[ai_model] = {
                    "tasks": 0,
                    "time_saved_seconds": 0,
                    "time_saved_hours": 0.0,
                }

            ai_stats[ai_model]["tasks"] += 1
            ai_stats[ai_model]["time_saved_seconds"] += task["time_saved_seconds"]
            ai_stats[ai_model]["time_saved_hours"] = (
                ai_stats[ai_model]["time_saved_seconds"] / 3600
            )

        return ai_stats

    def _calculate_phase_breakdown(
        self, tasks: List[Dict]
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate performance breakdown by phase"""
        phase_stats: Dict[str, Dict[str, Any]] = {}

        for task in tasks:
            phase = task["phase"]
            if phase not in phase_stats:
                phase_stats[phase] = {
                    "tasks": 0,
                    "time_saved_seconds": 0,
                    "time_saved_hours": 0.0,
                }

            phase_stats[phase]["tasks"] += 1
            phase_stats[phase]["time_saved_seconds"] += task["time_saved_seconds"]
            phase_stats[phase]["time_saved_hours"] = (
                phase_stats[phase]["time_saved_seconds"] / 3600
            )

        return phase_stats

    def _calculate_top_time_savers(
        self, tasks: List[Dict], top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """Calculate top time-saving task types"""
        task_type_stats: Dict[str, Dict[str, Any]] = {}

        for task in tasks:
            task_type = task["task_type"]
            if task_type not in task_type_stats:
                task_type_stats[task_type] = {
                    "task_type": task_type,
                    "tasks": 0,
                    "time_saved_seconds": 0,
                    "time_saved_hours": 0.0,
                }

            task_type_stats[task_type]["tasks"] += 1
            task_type_stats[task_type]["time_saved_seconds"] += task[
                "time_saved_seconds"
            ]
            task_type_stats[task_type]["time_saved_hours"] = (
                task_type_stats[task_type]["time_saved_seconds"] / 3600
            )

        # Sort by time saved and return top N
        sorted_stats = sorted(
            task_type_stats.values(),
            key=lambda x: x["time_saved_seconds"],
            reverse=True,
        )

        return sorted_stats[:top_n]

    def _project_annual(self, time_saved_hours: float, period: str) -> float:
        """Project annual time savings based on period"""
        if period == "daily":
            work_days_per_year = (
                self.config.get("roi_settings", {}).get("work_weeks_per_year", 48) * 5
            )
            return time_saved_hours * work_days_per_year
        elif period == "weekly":
            work_weeks_per_year = self.config.get("roi_settings", {}).get(
                "work_weeks_per_year", 48
            )
            return time_saved_hours * work_weeks_per_year
        elif period == "monthly":
            return time_saved_hours * 12
        elif period == "annual":
            return time_saved_hours
        else:
            # Default to weekly projection
            return time_saved_hours * 48

    def _empty_roi_report(
        self, period: str, start_date: date, end_date: date
    ) -> ROIReport:
        """Create empty ROI report when no data"""
        return ROIReport(
            period=period,
            period_start=start_date,
            period_end=end_date,
            manual_time_hours=0.0,
            actual_time_hours=0.0,
            time_saved_hours=0.0,
            roi_percentage=0.0,
            efficiency_gain=0.0,
            annual_projection_hours=0.0,
            annual_projection_value=0.0,
            tasks_completed=0,
            success_rate=0.0,
            ai_breakdown={},
            phase_breakdown={},
            top_time_savers=[],
            bottlenecks=[],
        )

    def _calculate_trends(
        self, current: ROIReport, previous: ROIReport
    ) -> Dict[str, Any]:
        """Calculate week-over-week trends"""
        trends = {}

        # ROI change
        if previous.roi_percentage > 0:
            roi_change = (
                (current.roi_percentage - previous.roi_percentage)
                / previous.roi_percentage
            ) * 100
            trends["roi_change"] = f"{roi_change:+.1f}%"
        else:
            trends["roi_change"] = "N/A"

        # Efficiency change
        if previous.efficiency_gain > 0:
            efficiency_change = (
                (current.efficiency_gain - previous.efficiency_gain)
                / previous.efficiency_gain
            ) * 100
            trends["efficiency_change"] = f"{efficiency_change:+.1f}%"
        else:
            trends["efficiency_change"] = "N/A"

        # Tasks change
        tasks_change = current.tasks_completed - previous.tasks_completed
        trends["tasks_change"] = f"{tasks_change:+d}"

        # Time saved change
        time_saved_change = current.time_saved_hours - previous.time_saved_hours
        trends["time_saved_change"] = f"{time_saved_change:+.1f}h"

        return trends

    def _generate_recommendations(self, roi_report: ROIReport) -> List[str]:
        """Generate actionable recommendations based on ROI report"""
        recommendations = []

        # Check for bottlenecks
        if roi_report.bottlenecks:
            critical_bottlenecks = [
                b for b in roi_report.bottlenecks if b.severity in ["critical", "high"]
            ]
            if critical_bottlenecks:
                top_bottleneck = critical_bottlenecks[0]
                recommendations.append(
                    f"Focus on optimizing {top_bottleneck.task_type.value} tasks "
                    f"(currently {top_bottleneck.overhead_percentage:.0f}% over baseline)"
                )

        # Check AI usage
        if "none" in roi_report.ai_breakdown:
            none_count = roi_report.ai_breakdown["none"]["tasks"]
            total_count = roi_report.tasks_completed
            none_percentage = (none_count / total_count * 100) if total_count > 0 else 0

            if none_percentage > 30:
                recommendations.append(
                    f"Increase AI usage: {none_percentage:.0f}% of tasks don't use AI assistance"
                )

        # Check multi-AI usage
        if "multi" in roi_report.ai_breakdown:
            multi_count = roi_report.ai_breakdown["multi"]["tasks"]
            total_count = roi_report.tasks_completed
            multi_percentage = (
                (multi_count / total_count * 100) if total_count > 0 else 0
            )

            if multi_percentage < 10:
                recommendations.append(
                    "Consider using multi-AI approach for complex tasks to improve efficiency"
                )

        # Check success rate
        if roi_report.success_rate < 90:
            recommendations.append(
                f"Improve task success rate (currently {roi_report.success_rate:.1f}%)"
            )

        # Check if meeting targets
        targets = self.config.get("targets", {}).get("weekly", {})
        target_hours = targets.get("target_hours_saved", 20)

        if roi_report.time_saved_hours < target_hours:
            gap = target_hours - roi_report.time_saved_hours
            recommendations.append(
                f"Need {gap:.1f} more hours saved to meet weekly target ({target_hours}h)"
            )
        elif roi_report.time_saved_hours >= targets.get("stretch_hours_saved", 30):
            recommendations.append(
                "Excellent! Exceeded stretch target - maintain this productivity level"
            )

        # Default recommendation if no issues found
        if not recommendations:
            recommendations.append(
                "Maintain current efficiency levels and continue monitoring for optimization opportunities"
            )

        return recommendations

    async def _handle_uncertainty_overrun(
        self, task_id: str, phase: Phase, ratio: float
    ):
        """
        Adjust uncertainty when a task exceeds 1.2x baseline.

        Light-touch hook to avoid tight coupling: uses global UDO system if present.
        """
        try:
            import sys

            main_module = sys.modules.get("main")
            if not main_module:
                return

            udo_system = getattr(main_module, "udo_system", None)
            if not udo_system:
                return

            uncertainty_map = udo_system.components.get("uncertainty")
            if not uncertainty_map:
                return

            context = {
                "phase": phase.value if hasattr(phase, "value") else str(phase),
                "has_code": True,
                "validation_score": 0.6,
                "team_size": 3,
                "timeline_weeks": 8,
            }

            vector, _state = uncertainty_map.analyze_context(context)

            technical_delta = min(0.3, (ratio - 1.2) * 0.5)
            timeline_delta = min(0.2, (ratio - 1.2) * 0.3)

            adjusted_vector = type(vector)(
                technical=min(1.0, vector.technical + technical_delta),
                market=vector.market,
                resource=vector.resource,
                timeline=min(1.0, vector.timeline + timeline_delta),
                quality=vector.quality,
            )

            magnitude = adjusted_vector.magnitude()
            new_state = uncertainty_map.classify_state(magnitude)

            logger.warning(
                "Time tracking overrun for task %s (ratio=%.2f) -> risk ^ (tech +%.2f, timeline +%.2f), state=%s",
                task_id,
                ratio,
                technical_delta,
                timeline_delta,
                new_state.value,
            )

            if self.obsidian_service:
                await self.obsidian_service.append_log(
                    f"## Time Tracking Overrun\n"
                    f"- Task: {task_id}\n"
                    f"- Ratio: {ratio:.2f}x baseline\n"
                    f"- Risk increase: technical +{technical_delta:.0%}, timeline +{timeline_delta:.0%}\n"
                    f"- New state: {new_state.value}\n"
                    f"#time-tracking #risk-surge #uncertainty\n"
                )
        except Exception as e:
            logger.error(
                f"Failed to handle uncertainty overrun for task {task_id}: {e}"
            )

    async def _sync_to_obsidian(
        self, session_id: UUID, metrics: TaskMetrics, success: bool
    ):
        """Sync task completion to Obsidian"""
        if not self.obsidian_service:
            return

        try:
            await self.obsidian_service.sync_event(
                "task_completed",
                {
                    "session_id": str(session_id),
                    "task_id": metrics.task_id,
                    "duration_seconds": metrics.duration_seconds,
                    "baseline_seconds": metrics.baseline_seconds,
                    "time_saved_seconds": metrics.time_saved_seconds,
                    "time_saved_hours": metrics.time_saved_hours,
                    "efficiency_percentage": metrics.efficiency_percentage,
                    "roi_percentage": metrics.roi_percentage,
                    "success": success,
                },
            )
        except Exception as e:
            logger.error(f"Failed to sync to Obsidian: {e}")
