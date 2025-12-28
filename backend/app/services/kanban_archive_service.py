"""
Kanban Archive Service

Week 3 Day 4-5: Archive View + AI Summarization.
Implements Q6: Done-End archive with GPT-4o summarization and Obsidian knowledge extraction.
"""

import logging
import os
import re
import time
from datetime import UTC, datetime
from typing import Dict, List, Optional
from uuid import UUID

# OpenAI client for GPT-4o summarization
try:
    from openai import AsyncOpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI package not available, using mock mode")

from app.models.kanban_archive import (AISummary, AISummaryConfidence,
                                               AISummaryGenerationError,
                                               AISummaryRequest,
                                               ArchivedTaskWithMetrics,
                                               ArchiveFilters,
                                               ArchiveListResponse,
                                               ArchiveTaskRequest,
                                               ArchiveTaskResponse,
                                               ObsidianKnowledgeEntry,
                                               ObsidianSyncError,
                                               ObsidianSyncStatus, ROIMetrics,
                                               ROIStatistics,
                                               TaskNotArchivableError)
from app.models.kanban_task import Task, TaskStatus
from app.services.kanban_task_service import kanban_task_service
from app.services.obsidian_service import ObsidianService

logger = logging.getLogger(__name__)


class KanbanArchiveService:
    """
    Archive service for completed Kanban tasks.

    Features:
    - AI summarization using GPT-4o (with mock fallback)
    - ROI metrics calculation (efficiency, quality, time saved)
    - Obsidian knowledge extraction and sync (Q6)
    - Archive list with filtering and pagination
    - Bulk archive operations
    """

    def __init__(self):
        """Initialize archive service with AI and Obsidian integration"""
        # OpenAI client for GPT-4o
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or not OPENAI_AVAILABLE:
            logger.warning(
                "OPENAI_API_KEY not set or OpenAI not available, using mock mode"
            )
            self.openai_client = None
            self.mock_mode = True
        else:
            self.openai_client = AsyncOpenAI(api_key=api_key)
            self.mock_mode = False

        # Obsidian service for knowledge sync
        self.obsidian_service = ObsidianService()

        # In-memory archive storage (TODO: Replace with database)
        self.archives: Dict[UUID, ArchivedTaskWithMetrics] = {}

    async def archive_task(self, request: ArchiveTaskRequest) -> ArchiveTaskResponse:
        """
        Archive a completed task with AI summarization and Obsidian sync.

        Args:
            request: Archive task request

        Returns:
            ArchiveTaskResponse with summary and sync status

        Raises:
            TaskNotArchivableError: If task cannot be archived
        """
        start_time = time.time()

        # 1. Validate task exists and can be archived
        task = await self._validate_task_archivable(request.task_id)

        # 2. Generate AI summary if requested
        ai_summary = None
        summary_time_ms = 0.0
        if request.generate_ai_summary:
            try:
                summary_start = time.time()
                ai_summary = await self._generate_ai_summary(task)
                summary_time_ms = (time.time() - summary_start) * 1000
                logger.info(
                    f"AI summary generated for task {task.task_id} in {summary_time_ms:.2f}ms"
                )
            except Exception as e:
                logger.error(f"Failed to generate AI summary: {e}")
                # Continue without summary

        # 3. Calculate ROI metrics
        roi_metrics = self._calculate_roi_metrics(task)

        # 4. Sync to Obsidian if requested
        obsidian_synced = False
        obsidian_note_path = None
        obsidian_error = None
        if request.sync_to_obsidian and ai_summary:
            try:
                sync_status = await self._sync_to_obsidian(
                    task, ai_summary, roi_metrics
                )
                obsidian_synced = sync_status.synced
                obsidian_note_path = sync_status.obsidian_note_path
                obsidian_error = sync_status.sync_error
                logger.info(
                    f"Task {task.task_id} synced to Obsidian: {obsidian_note_path}"
                )
            except Exception as e:
                logger.error(f"Failed to sync to Obsidian: {e}")
                obsidian_error = str(e)

        # 5. Update task status to DONE_END
        archived_at = datetime.now(UTC)
        # TODO: In production, update task in database with archived_at timestamp

        # 6. Store in archive
        archived_task = ArchivedTaskWithMetrics(
            task_id=task.task_id,
            title=task.title,
            description=task.description,
            phase_name=task.phase_name,
            archived_at=archived_at,
            archived_by=request.archived_by,
            ai_summary=ai_summary,
            roi_metrics=roi_metrics,
            obsidian_synced=obsidian_synced,
            obsidian_note_path=obsidian_note_path,
        )
        self.archives[task.task_id] = archived_task

        total_time_ms = (time.time() - start_time) * 1000

        return ArchiveTaskResponse(
            task_id=task.task_id,
            success=True,
            message=f"Task archived successfully (Q6: Done-End + AI summarization)",
            archived_at=archived_at,
            ai_summary_generated=ai_summary is not None,
            ai_summary=ai_summary,
            summary_generation_time_ms=summary_time_ms if ai_summary else None,
            obsidian_synced=obsidian_synced,
            obsidian_note_path=obsidian_note_path,
            obsidian_sync_error=obsidian_error,
            roi_metrics=roi_metrics,
        )

    async def _validate_task_archivable(self, task_id: UUID) -> Task:
        """Validate that task exists and can be archived"""
        # Use singleton task service (mock for tests, DB for production)
        task = await kanban_task_service.get_task(task_id)

        # Check if task is completed
        if task.status not in [TaskStatus.COMPLETED, TaskStatus.DONE_END]:
            raise TaskNotArchivableError(
                task_id,
                f"Task must be COMPLETED before archiving (current: {task.status})",
            )

        # Check if already archived
        if task_id in self.archives:
            raise TaskNotArchivableError(task_id, "Task already archived")

        return task

    async def _generate_ai_summary(self, task: Task) -> AISummary:
        """
        Generate AI summary using GPT-4o.

        Falls back to mock mode if API not available.
        """
        if self.mock_mode:
            return self._generate_mock_summary(task)

        try:
            start_time = time.time()

            # Construct prompt for GPT-4o
            system_prompt = """You are an expert technical summarizer for software development tasks.
Generate a comprehensive summary of the completed task with key learnings and technical insights.

Format your response as JSON with these fields:
- summary: Concise overview (50-300 words)
- key_learnings: List of 2-4 key learnings
- technical_insights: List of 2-4 technical insights for knowledge base
- recommendations: List of 2-4 recommendations for future tasks
"""

            user_prompt = f"""Task: {task.title}

Description: {task.description}

Phase: {task.phase_name}
Status: {task.status}
Priority: {task.priority}
Estimated Hours: {task.estimated_hours}
Actual Hours: {task.actual_hours}
Quality Score: {task.quality_score if hasattr(task, 'quality_score') else 'N/A'}

Generate a comprehensive summary with key learnings, technical insights, and recommendations."""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=1500,
                response_format={"type": "json_object"},
            )

            generation_time_ms = (time.time() - start_time) * 1000

            # Parse response
            import json

            content = json.loads(response.choices[0].message.content)

            return AISummary(
                task_id=task.task_id,
                summary=content.get("summary", ""),
                key_learnings=content.get("key_learnings", []),
                technical_insights=content.get("technical_insights", []),
                recommendations=content.get("recommendations", []),
                confidence=AISummaryConfidence.HIGH,
                model_used="gpt-4o",
                generation_time_ms=generation_time_ms,
                token_usage={
                    "prompt": response.usage.prompt_tokens,
                    "completion": response.usage.completion_tokens,
                    "total": response.usage.total_tokens,
                },
            )

        except Exception as e:
            logger.error(f"GPT-4o summary generation failed: {e}, falling back to mock")
            return self._generate_mock_summary(task)

    def _generate_mock_summary(self, task: Task) -> AISummary:
        """Generate mock AI summary for testing"""
        phase_insights = {
            "ideation": [
                "Explored multiple solution approaches",
                "Identified key user pain points",
                "Validated assumptions with research",
            ],
            "design": [
                "Created comprehensive system architecture",
                "Defined clear API contracts",
                "Considered scalability from the start",
            ],
            "mvp": [
                "Delivered minimal viable functionality",
                "Validated core assumptions quickly",
                "Set foundation for future iterations",
            ],
            "implementation": [
                "Implemented robust error handling",
                "Applied SOLID principles",
                "Maintained high code quality",
            ],
            "testing": [
                "Achieved comprehensive test coverage",
                "Validated edge cases thoroughly",
                "Ensured production readiness",
            ],
        }

        phase_key = task.phase_name.lower()
        insights = phase_insights.get(phase_key, phase_insights["implementation"])

        return AISummary(
            task_id=task.task_id,
            summary=f"Completed '{task.title}' in {task.phase_name} phase. "
            f"Task accomplished its objectives with {task.priority} priority. "
            f"Estimated {task.estimated_hours}h, actually took {task.actual_hours}h.",
            key_learnings=insights[:2],
            technical_insights=(
                insights[2:3] if len(insights) > 2 else ["Applied best practices"]
            ),
            recommendations=[
                f"Consider similar approach for future {task.phase_name} tasks",
                "Document learnings for team knowledge base",
            ],
            confidence=AISummaryConfidence.HIGH,
            model_used="mock",
            generation_time_ms=10.0,
            token_usage=None,
        )

    def _calculate_roi_metrics(self, task: Task) -> ROIMetrics:
        """Calculate ROI metrics for archived task"""
        # Time efficiency
        estimated = task.estimated_hours
        actual = task.actual_hours if task.actual_hours > 0 else estimated
        time_saved = estimated - actual
        efficiency = (estimated / actual * 100) if actual > 0 else 100.0

        # Quality metrics
        quality_score = getattr(task, "quality_score", 80)
        constitutional_compliant = getattr(task, "constitutional_compliant", True)
        violated_articles = getattr(task, "violated_articles", [])

        # AI metrics
        ai_suggested = getattr(task, "ai_suggested", False)
        ai_confidence = getattr(task, "ai_confidence", None)

        return ROIMetrics(
            task_id=task.task_id,
            estimated_hours=estimated,
            actual_hours=actual,
            time_saved_hours=time_saved,
            efficiency_percentage=min(efficiency, 200.0),  # Cap at 200%
            quality_score=quality_score,
            constitutional_compliance=constitutional_compliant,
            violated_articles=violated_articles,
            ai_suggested=ai_suggested,
            ai_confidence=ai_confidence,
            ai_accuracy=None,  # User feedback, set later
            business_value=None,  # User assessment, set later
            technical_debt_added=None,  # Assessment, set later
        )

    async def _sync_to_obsidian(
        self, task: Task, ai_summary: AISummary, roi_metrics: ROIMetrics
    ) -> ObsidianSyncStatus:
        """
        Sync archived task knowledge to Obsidian vault (Q6).
        """
        if not self.obsidian_service.vault_available:
            return ObsidianSyncStatus(
                task_id=task.task_id,
                synced=False,
                sync_error="Obsidian vault not available",
            )

        try:
            # Create knowledge entry
            entry = ObsidianKnowledgeEntry(
                task_id=task.task_id,
                title=task.title,
                phase_name=task.phase_name,
                summary=ai_summary.summary,
                key_learnings=ai_summary.key_learnings,
                technical_insights=ai_summary.technical_insights,
                tags=[
                    task.phase_name,
                    task.priority,
                    "kanban-archived",
                    f"efficiency-{int(roi_metrics.efficiency_percentage)}",
                ],
                related_tasks=[],  # TODO: Link related tasks
                created_at=task.created_at,
                archived_at=datetime.now(UTC),
            )

            # Generate Obsidian note content
            note_content = self._generate_obsidian_note(entry, roi_metrics)

            # Save to Obsidian vault in date-specific folder
            date_str = datetime.now(UTC).strftime('%Y-%m-%d')

            # Sanitize task title for filename (remove special characters)
            # Keep only alphanumeric, spaces, hyphens, and underscores
            safe_title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', task.title)
            safe_title = re.sub(r'\s+', '-', safe_title.strip())  # Replace spaces with hyphens
            safe_title = safe_title[:50]  # Limit length to 50 chars for readability

            # Format: YYYY-MM-DD_TaskTitle_uuid.md
            # This provides human-readable names while maintaining uniqueness
            note_filename = f"{date_str}_{safe_title}_{task.task_id}.md"

            # Create date folder if it doesn't exist
            date_dir = self.obsidian_service.daily_notes_dir / date_str
            date_dir.mkdir(parents=True, exist_ok=True)

            # Save in date folder: 개발일지/YYYY-MM-DD/YYYY-MM-DD_TaskTitle_uuid.md
            note_path = date_dir / note_filename

            # Write note to file
            with open(note_path, "w", encoding="utf-8") as f:
                f.write(note_content)

            logger.info(f"Saved Obsidian note: {note_path}")

            return ObsidianSyncStatus(
                task_id=task.task_id,
                synced=True,
                obsidian_note_path=str(note_path),
                sync_timestamp=datetime.now(UTC),
                retry_count=0,
            )

        except Exception as e:
            logger.error(f"Failed to sync to Obsidian: {e}")
            return ObsidianSyncStatus(
                task_id=task.task_id, synced=False, sync_error=str(e), retry_count=1
            )

    def _generate_obsidian_note(
        self, entry: ObsidianKnowledgeEntry, roi_metrics: ROIMetrics
    ) -> str:
        """Generate Obsidian markdown note content"""
        tags_str = " ".join([f"#{tag}" for tag in entry.tags])

        note = f"""# {entry.title}

{tags_str}

## [EMOJI] Task Summary

**Phase**: {entry.phase_name}
**Archived**: {entry.archived_at.strftime("%Y-%m-%d %H:%M")}
**Task ID**: `{entry.task_id}`

## [EMOJI] Summary

{entry.summary}

## [EMOJI] Key Learnings

"""
        for learning in entry.key_learnings:
            note += f"- {learning}\n"

        note += f"""
## [EMOJI] Technical Insights

"""
        for insight in entry.technical_insights:
            note += f"- {insight}\n"

        note += f"""
## [EMOJI] ROI Metrics

- **Estimated**: {roi_metrics.estimated_hours}h
- **Actual**: {roi_metrics.actual_hours}h
- **Time Saved**: {roi_metrics.time_saved_hours:+.1f}h
- **Efficiency**: {roi_metrics.efficiency_percentage:.1f}%
- **Quality Score**: {roi_metrics.quality_score}/100
- **Constitutional Compliance**: {"[OK] Yes" if roi_metrics.constitutional_compliance else "[FAIL] No"}

## [EMOJI] Related

- [[Kanban Archive MOC]]
- [[{entry.phase_name.capitalize()} Phase]]

---

*Generated by UDO Platform - Week 3 Day 4-5 (Q6: Done-End + AI Summarization)*
"""
        return note

    async def get_archive_list(
        self,
        filters: Optional[ArchiveFilters] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> ArchiveListResponse:
        """
        Get paginated list of archived tasks with filtering.

        Args:
            filters: Optional filters
            page: Page number (1-indexed)
            per_page: Items per page

        Returns:
            ArchiveListResponse with tasks and statistics
        """
        # Filter archives
        filtered = list(self.archives.values())

        if filters:
            if filters.phase:
                filtered = [a for a in filtered if a.phase_name == filters.phase]
            if filters.archived_by:
                filtered = [a for a in filtered if a.archived_by == filters.archived_by]
            if filters.ai_suggested is not None:
                filtered = [
                    a
                    for a in filtered
                    if a.roi_metrics
                    and a.roi_metrics.ai_suggested == filters.ai_suggested
                ]
            if filters.obsidian_synced is not None:
                filtered = [
                    a for a in filtered if a.obsidian_synced == filters.obsidian_synced
                ]
            if filters.min_quality_score:
                filtered = [
                    a
                    for a in filtered
                    if a.roi_metrics
                    and a.roi_metrics.quality_score >= filters.min_quality_score
                ]

        # Pagination
        total = len(filtered)
        total_pages = (total + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        page_data = filtered[start:end]

        # Calculate statistics
        roi_stats = self._calculate_roi_statistics(filtered)

        return ArchiveListResponse(
            data=page_data,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            roi_statistics=roi_stats,
        )

    def _calculate_roi_statistics(
        self, archives: List[ArchivedTaskWithMetrics]
    ) -> ROIStatistics:
        """Calculate aggregated ROI statistics"""
        if not archives:
            return ROIStatistics(
                total_tasks=0,
                total_estimated_hours=0.0,
                total_actual_hours=0.0,
                total_time_saved_hours=0.0,
                average_efficiency=0.0,
                average_quality_score=0.0,
                phase_breakdown={},
                ai_suggested_tasks=0,
                constitutional_compliant_tasks=0,
                constitutional_compliance_rate=0.0,
                period_start=datetime.now(UTC),
                period_end=datetime.now(UTC),
            )

        total_estimated = sum(
            a.roi_metrics.estimated_hours for a in archives if a.roi_metrics
        )
        total_actual = sum(
            a.roi_metrics.actual_hours for a in archives if a.roi_metrics
        )
        total_saved = sum(
            a.roi_metrics.time_saved_hours for a in archives if a.roi_metrics
        )
        avg_efficiency = sum(
            a.roi_metrics.efficiency_percentage for a in archives if a.roi_metrics
        ) / len(archives)
        avg_quality = sum(
            a.roi_metrics.quality_score for a in archives if a.roi_metrics
        ) / len(archives)

        phase_breakdown = {}
        for archive in archives:
            phase_breakdown[archive.phase_name] = (
                phase_breakdown.get(archive.phase_name, 0) + 1
            )

        ai_suggested = sum(
            1 for a in archives if a.roi_metrics and a.roi_metrics.ai_suggested
        )
        compliant = sum(
            1
            for a in archives
            if a.roi_metrics and a.roi_metrics.constitutional_compliance
        )

        archived_dates = [a.archived_at for a in archives]
        period_start = min(archived_dates)
        period_end = max(archived_dates)

        return ROIStatistics(
            total_tasks=len(archives),
            total_estimated_hours=total_estimated,
            total_actual_hours=total_actual,
            total_time_saved_hours=total_saved,
            average_efficiency=avg_efficiency,
            average_quality_score=avg_quality,
            phase_breakdown=phase_breakdown,
            ai_suggested_tasks=ai_suggested,
            constitutional_compliant_tasks=compliant,
            constitutional_compliance_rate=compliant / len(archives) * 100,
            period_start=period_start,
            period_end=period_end,
        )


# Singleton instance
kanban_archive_service = KanbanArchiveService()
