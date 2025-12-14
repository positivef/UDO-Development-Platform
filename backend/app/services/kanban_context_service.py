"""
Kanban Context Service - ZIP-based Context Management

Implements Week 2 Day 5: Context operations (upload/download/metadata)
Q4: Double-click auto-load tracking

Key features:
- ZIP creation from file list (<50MB limit)
- Mock storage (will be replaced with S3/MinIO)
- Double-click load tracking
- Average load time calculation
"""

from typing import Dict, Optional
from uuid import UUID, uuid4
from datetime import datetime, UTC
import hashlib
import logging

from backend.app.models.kanban_context import (
    TaskContext,
    ContextMetadata,
    ContextUploadRequest,
    ContextLoadRequest,
    ContextLoadResponse,
    ContextUploadResponse,
    ContextNotFoundError,
    ContextSizeLimitExceeded,
    InvalidContextFiles,
)

logger = logging.getLogger(__name__)


class KanbanContextService:
    """
    Service for managing task contexts with ZIP storage.

    Mock implementation for Week 2 (will be replaced with S3/MinIO storage later).
    """

    def __init__(self, db_session=None):
        """
        Initialize service with database session.

        Args:
            db_session: Database session (optional for testing with mock data)
        """
        self.db = db_session

        # In-memory storage for testing (will be replaced by DB + S3)
        self._mock_contexts: Dict[UUID, TaskContext] = {}

        # Mock storage base URL (will be replaced with S3/MinIO)
        self._mock_storage_url = "https://mock-storage.udo-platform.com/contexts"

        logger.info("KanbanContextService initialized")

    # ========================================================================
    # Context Metadata Operations
    # ========================================================================

    async def get_context_metadata(self, task_id: UUID) -> Optional[ContextMetadata]:
        """
        Get context metadata for task (without full files list).

        Args:
            task_id: Task ID

        Returns:
            ContextMetadata or None if not found
        """
        if self.db:
            # Database implementation
            pass
        else:
            # Mock implementation
            for context in self._mock_contexts.values():
                if context.task_id == task_id:
                    return ContextMetadata(
                        context_id=context.context_id,
                        task_id=context.task_id,
                        file_count=context.file_count,
                        git_branch=context.git_branch,
                        last_commit_hash=context.last_commit_hash,
                        zip_url=context.zip_url,
                        zip_size_bytes=context.zip_size_bytes,
                        last_loaded_at=context.last_loaded_at,
                        load_count=context.load_count,
                        avg_load_time_ms=context.avg_load_time_ms,
                        created_at=context.created_at,
                        updated_at=context.updated_at,
                    )
            return None

    async def get_context_full(self, task_id: UUID) -> Optional[TaskContext]:
        """
        Get full context including files list.

        Args:
            task_id: Task ID

        Returns:
            TaskContext or None if not found
        """
        if self.db:
            # Database implementation
            pass
        else:
            # Mock implementation
            for context in self._mock_contexts.values():
                if context.task_id == task_id:
                    return context
            return None

    # ========================================================================
    # Context Upload Operations
    # ========================================================================

    async def upload_context(
        self,
        task_id: UUID,
        upload_request: ContextUploadRequest
    ) -> ContextUploadResponse:
        """
        Upload context files as ZIP.

        Args:
            task_id: Task ID
            upload_request: Upload request with files list

        Returns:
            ContextUploadResponse with ZIP URL

        Raises:
            ContextSizeLimitExceeded: If ZIP size > 50MB
            InvalidContextFiles: If files list is empty or invalid
        """
        # Validate files
        if not upload_request.files or len(upload_request.files) == 0:
            raise InvalidContextFiles("At least one file path required")

        # Calculate mock ZIP size (estimate: avg 100KB per file)
        estimated_size_bytes = len(upload_request.files) * 100 * 1024

        # Check 50MB limit
        if estimated_size_bytes > 52428800:
            raise ContextSizeLimitExceeded(
                f"Estimated ZIP size {estimated_size_bytes} bytes exceeds 50MB limit"
            )

        # Generate ZIP checksum (mock: hash of file list)
        file_list_str = ",".join(sorted(upload_request.files))
        zip_checksum = hashlib.sha256(file_list_str.encode()).hexdigest()

        # Generate mock ZIP URL
        context_id = uuid4()
        zip_url = f"{self._mock_storage_url}/{context_id}.zip"

        # Create context
        context = TaskContext(
            context_id=context_id,
            task_id=task_id,
            files=upload_request.files,
            file_count=len(upload_request.files),
            git_branch=upload_request.git_branch,
            last_commit_hash=upload_request.git_commit_hash,
            last_commit_message=upload_request.git_commit_message,
            zip_url=zip_url,
            zip_size_bytes=estimated_size_bytes,
            zip_checksum=zip_checksum,
            obsidian_notes=upload_request.obsidian_notes,
        )

        if self.db:
            # Database implementation + S3 upload
            pass
        else:
            # Mock implementation
            # Delete existing context for this task (unique constraint)
            existing_context_ids = [
                ctx_id for ctx_id, ctx in self._mock_contexts.items()
                if ctx.task_id == task_id
            ]
            for ctx_id in existing_context_ids:
                del self._mock_contexts[ctx_id]

            # Store new context
            self._mock_contexts[context_id] = context

        logger.info(
            f"Uploaded context for task {task_id}: {len(upload_request.files)} files, "
            f"{estimated_size_bytes} bytes"
        )

        return ContextUploadResponse(
            context_id=context.context_id,
            task_id=context.task_id,
            zip_url=context.zip_url,
            zip_size_bytes=context.zip_size_bytes,
            zip_checksum=context.zip_checksum,
            file_count=context.file_count,
            created_at=context.created_at,
        )

    # ========================================================================
    # Context Load Tracking (Q4: Double-click)
    # ========================================================================

    async def track_context_load(
        self,
        task_id: UUID,
        load_request: ContextLoadRequest
    ) -> ContextLoadResponse:
        """
        Track context load (Q4: Double-click auto-load).

        Updates load_count and avg_load_time_ms.

        Args:
            task_id: Task ID
            load_request: Load tracking request with load_time_ms

        Returns:
            ContextLoadResponse with updated stats

        Raises:
            ContextNotFoundError: If context not found for task
        """
        context = await self.get_context_full(task_id)
        if not context:
            raise ContextNotFoundError(f"Context not found for task {task_id}")

        # Update load stats
        old_avg = context.avg_load_time_ms or 0
        old_count = context.load_count

        # Calculate new average: (old_avg * old_count + new_time) / new_count
        new_count = old_count + 1
        new_avg = ((old_avg * old_count) + load_request.load_time_ms) // new_count

        # Update context
        context.load_count = new_count
        context.avg_load_time_ms = new_avg
        context.last_loaded_at = datetime.now(UTC)
        context.updated_at = datetime.now(UTC)

        if self.db:
            # Database implementation
            pass
        else:
            # Mock implementation - already updated in place
            pass

        logger.info(
            f"Tracked context load for task {task_id}: "
            f"load #{new_count}, time {load_request.load_time_ms}ms, "
            f"avg {new_avg}ms"
        )

        return ContextLoadResponse(
            success=True,
            load_count=context.load_count,
            avg_load_time_ms=context.avg_load_time_ms,
            last_loaded_at=context.last_loaded_at,
        )

    # ========================================================================
    # Context Deletion
    # ========================================================================

    async def delete_context(self, task_id: UUID) -> bool:
        """
        Delete context for task.

        Args:
            task_id: Task ID

        Returns:
            True if deleted, False if not found
        """
        if self.db:
            # Database implementation + S3 deletion
            pass
        else:
            # Mock implementation
            context_id_to_delete = None
            for ctx_id, ctx in self._mock_contexts.items():
                if ctx.task_id == task_id:
                    context_id_to_delete = ctx_id
                    break

            if context_id_to_delete:
                del self._mock_contexts[context_id_to_delete]
                logger.info(f"Deleted context for task {task_id}")
                return True
            return False

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _estimate_zip_size(self, file_paths: list[str]) -> int:
        """
        Estimate ZIP size from file paths (mock implementation).

        In production, this would read actual file sizes and calculate compressed size.

        Args:
            file_paths: List of file paths

        Returns:
            Estimated size in bytes
        """
        # Mock: Estimate 100KB per file
        return len(file_paths) * 100 * 1024


# ============================================================================
# Singleton Instance
# ============================================================================

kanban_context_service = KanbanContextService()
