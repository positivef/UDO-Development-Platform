"""
Kanban Context Service - ZIP-based Context Management

Implements Week 2 Day 5: Context operations (upload/download/metadata)
Q4: Double-click auto-load tracking

Key features:
- ZIP creation from file list (<50MB limit)
- PostgreSQL storage with asyncpg (Week 6 Day 2: DB integration)
- Double-click load tracking
- Average load time calculation

Week 6 Day 2: Migrated from mock data to real PostgreSQL database.
"""

import hashlib
import io
import json
import logging
import zipfile
from datetime import UTC, datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

# Optional asyncpg import (not needed for Mock mode)
try:
    import asyncpg
except ImportError:
    asyncpg = None

from app.models.kanban_context import (
    ContextLoadRequest,
    ContextLoadResponse,
    ContextMetadata,
    ContextNotFoundError,
    ContextSizeLimitExceeded,
    ContextUploadRequest,
    ContextUploadResponse,
    InvalidContextFiles,
    TaskContext,
)

logger = logging.getLogger(__name__)


class KanbanContextService:
    """
    Service for managing task contexts with PostgreSQL database.

    Uses asyncpg connection pool for all database operations.
    ZIP files are stored in the database (context_zip BYTEA column).

    Week 6 Day 2: Migrated from mock to real PostgreSQL database.
    """

    def __init__(self, db_pool: "asyncpg.Pool"):
        """
        Initialize service with database connection pool.

        Args:
            db_pool: asyncpg connection pool
        """
        self.db_pool = db_pool

        # Storage base URL for ZIP download links
        self._storage_url = "/api/kanban/context"

        logger.info("KanbanContextService initialized with database pool")

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
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT
                    context_id,
                    task_id,
                    context_metadata,
                    octet_length(context_zip) as zip_size_bytes,
                    double_click_loads as load_count,
                    manual_loads,
                    last_loaded_at,
                    created_at,
                    updated_at
                FROM kanban.task_contexts
                WHERE task_id = $1
            """
            row = await conn.fetchrow(query, task_id)

            if not row:
                return None

            # Extract metadata from JSONB
            metadata_json = row["context_metadata"] or {}
            if isinstance(metadata_json, str):
                metadata_json = json.loads(metadata_json)

            file_count = len(metadata_json.get("files", []))
            git_branch = metadata_json.get("git_branch")
            last_commit_hash = metadata_json.get("last_commit_hash")

            # Calculate avg load time from total loads
            total_loads = row["load_count"] + row["manual_loads"]
            avg_load_time_ms = metadata_json.get("avg_load_time_ms")

            return ContextMetadata(
                context_id=row["context_id"],
                task_id=row["task_id"],
                file_count=file_count,
                git_branch=git_branch,
                last_commit_hash=last_commit_hash,
                zip_url=f"{self._storage_url}/{task_id}/download",
                zip_size_bytes=row["zip_size_bytes"],
                last_loaded_at=row["last_loaded_at"],
                load_count=total_loads,
                avg_load_time_ms=avg_load_time_ms,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def get_context_full(self, task_id: UUID) -> Optional[TaskContext]:
        """
        Get full context including files list.

        Args:
            task_id: Task ID

        Returns:
            TaskContext or None if not found
        """
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT
                    context_id,
                    task_id,
                    context_metadata,
                    octet_length(context_zip) as zip_size_bytes,
                    double_click_loads as load_count,
                    manual_loads,
                    last_loaded_at,
                    created_at,
                    updated_at
                FROM kanban.task_contexts
                WHERE task_id = $1
            """
            row = await conn.fetchrow(query, task_id)

            if not row:
                return None

            # Extract metadata from JSONB
            metadata_json = row["context_metadata"] or {}
            if isinstance(metadata_json, str):
                metadata_json = json.loads(metadata_json)

            files = metadata_json.get("files", [])
            git_branch = metadata_json.get("git_branch")
            last_commit_hash = metadata_json.get("last_commit_hash")
            last_commit_message = metadata_json.get("last_commit_message")
            zip_checksum = metadata_json.get("zip_checksum")
            obsidian_notes = metadata_json.get("obsidian_notes", [])
            avg_load_time_ms = metadata_json.get("avg_load_time_ms")

            total_loads = row["load_count"] + row["manual_loads"]

            return TaskContext(
                context_id=row["context_id"],
                task_id=row["task_id"],
                files=files,
                file_count=len(files),
                git_branch=git_branch,
                last_commit_hash=last_commit_hash,
                last_commit_message=last_commit_message,
                zip_url=f"{self._storage_url}/{task_id}/download",
                zip_size_bytes=row["zip_size_bytes"],
                zip_checksum=zip_checksum,
                obsidian_notes=obsidian_notes,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                last_loaded_at=row["last_loaded_at"],
                load_count=total_loads,
                avg_load_time_ms=avg_load_time_ms,
            )

    async def get_context_zip(self, task_id: UUID) -> Optional[bytes]:
        """
        Get raw ZIP file bytes for download.

        Args:
            task_id: Task ID

        Returns:
            ZIP file bytes or None if not found
        """
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT context_zip
                FROM kanban.task_contexts
                WHERE task_id = $1
            """
            row = await conn.fetchrow(query, task_id)

            if not row or not row["context_zip"]:
                return None

            return bytes(row["context_zip"])

    # ========================================================================
    # Context Upload Operations
    # ========================================================================

    async def upload_context(self, task_id: UUID, upload_request: ContextUploadRequest) -> ContextUploadResponse:
        """
        Upload context files as metadata (no actual ZIP creation).

        Args:
            task_id: Task ID
            upload_request: Upload request with files list

        Returns:
            ContextUploadResponse with ZIP URL

        Raises:
            ContextSizeLimitExceeded: If estimated ZIP size > 50MB
            InvalidContextFiles: If files list is empty or invalid
        """
        # Validate files
        if not upload_request.files or len(upload_request.files) == 0:
            raise InvalidContextFiles("At least one file path required")

        # Calculate estimated ZIP size (avg 100KB per file)
        estimated_size_bytes = len(upload_request.files) * 100 * 1024

        # Check 50MB limit
        if estimated_size_bytes > 52428800:
            raise ContextSizeLimitExceeded(f"Estimated ZIP size {estimated_size_bytes} bytes exceeds 50MB limit")

        # Generate ZIP checksum (hash of file list)
        file_list_str = ",".join(sorted(upload_request.files))
        zip_checksum = hashlib.sha256(file_list_str.encode()).hexdigest()

        # Build metadata JSONB
        metadata = {
            "files": upload_request.files,
            "total_size": estimated_size_bytes,
            "compression_ratio": 0.7,  # Estimated
            "git_branch": upload_request.git_branch,
            "last_commit_hash": upload_request.git_commit_hash,
            "last_commit_message": upload_request.git_commit_message,
            "zip_checksum": zip_checksum,
            "obsidian_notes": upload_request.obsidian_notes or [],
        }

        async with self.db_pool.acquire() as conn:
            # UPSERT: Insert or update context for this task
            query = """
                INSERT INTO kanban.task_contexts (
                    task_id,
                    context_metadata,
                    double_click_loads,
                    manual_loads
                )
                VALUES ($1, $2, 0, 0)
                ON CONFLICT (task_id) DO UPDATE SET
                    context_metadata = EXCLUDED.context_metadata,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING
                    context_id,
                    task_id,
                    created_at,
                    updated_at
            """
            row = await conn.fetchrow(query, task_id, json.dumps(metadata))

            context_id = row["context_id"]
            created_at = row["created_at"]

        logger.info(f"Uploaded context metadata for task {task_id}: " f"{len(upload_request.files)} files")

        return ContextUploadResponse(
            context_id=context_id,
            task_id=task_id,
            zip_url=f"{self._storage_url}/{task_id}/download",
            zip_size_bytes=estimated_size_bytes,
            zip_checksum=zip_checksum,
            file_count=len(upload_request.files),
            created_at=created_at,
        )

    async def upload_context_file(self, task_id: UUID, filename: str, contents: bytes) -> ContextUploadResponse:
        """
        Upload context ZIP file (Week 6 Day 2: Database storage).

        Args:
            task_id: Task ID
            filename: Original filename
            contents: ZIP file contents as bytes

        Returns:
            ContextUploadResponse with ZIP URL

        Raises:
            ContextSizeLimitExceeded: If ZIP size > 50MB
            InvalidContextFiles: If ZIP is invalid or empty
            ZipBombDetected: If ZIP bomb detected (P0-2)
            VirusDetected: If virus detected (P0-2)
        """
        # Validate ZIP file size (50MB = 52,428,800 bytes)
        MAX_SIZE = 50 * 1024 * 1024
        file_size = len(contents)

        if file_size > MAX_SIZE:
            raise ContextSizeLimitExceeded(f"ZIP file size {file_size} bytes exceeds 50MB limit")

        # P0-2: Virus scan (ClamAV)
        await self._scan_for_virus(contents, filename)

        # Extract file list from ZIP
        try:
            zip_buffer = io.BytesIO(contents)
            with zipfile.ZipFile(zip_buffer, "r") as zip_file:
                # Get file list (exclude directories)
                file_list = [name for name in zip_file.namelist() if not name.endswith("/")]

                if not file_list:
                    raise InvalidContextFiles("ZIP file contains no files")

                # Extract file sizes for metadata
                total_uncompressed_size = sum(info.file_size for info in zip_file.infolist() if not info.is_dir())

                # P0-2: ZIP bomb detection
                self._detect_zip_bomb(file_size, total_uncompressed_size, len(file_list), zip_file)

        except zipfile.BadZipFile:
            raise InvalidContextFiles("Invalid ZIP file format")

        # Generate ZIP checksum (SHA256 of contents)
        zip_checksum = hashlib.sha256(contents).hexdigest()

        # Calculate compression ratio
        compression_ratio = file_size / total_uncompressed_size if total_uncompressed_size > 0 else 1.0

        # Build metadata JSONB
        metadata = {
            "files": file_list,
            "total_size": total_uncompressed_size,
            "compressed_size": file_size,
            "compression_ratio": compression_ratio,
            "original_filename": filename,
            "zip_checksum": zip_checksum,
        }

        async with self.db_pool.acquire() as conn:
            # UPSERT: Insert or update context for this task
            query = """
                INSERT INTO kanban.task_contexts (
                    task_id,
                    context_zip,
                    context_metadata,
                    double_click_loads,
                    manual_loads
                )
                VALUES ($1, $2, $3, 0, 0)
                ON CONFLICT (task_id) DO UPDATE SET
                    context_zip = EXCLUDED.context_zip,
                    context_metadata = EXCLUDED.context_metadata,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING
                    context_id,
                    task_id,
                    created_at,
                    updated_at
            """
            row = await conn.fetchrow(query, task_id, contents, json.dumps(metadata))

            context_id = row["context_id"]
            created_at = row["created_at"]

        logger.info(
            f"Uploaded ZIP file for task {task_id}: {filename}, "
            f"{len(file_list)} files, {file_size} bytes compressed, "
            f"{total_uncompressed_size} bytes uncompressed"
        )

        return ContextUploadResponse(
            context_id=context_id,
            task_id=task_id,
            zip_url=f"{self._storage_url}/{task_id}/download",
            zip_size_bytes=file_size,
            zip_checksum=zip_checksum,
            file_count=len(file_list),
            created_at=created_at,
        )

    # ========================================================================
    # Context Load Tracking (Q4: Double-click)
    # ========================================================================

    async def track_context_load(self, task_id: UUID, load_request: ContextLoadRequest) -> ContextLoadResponse:
        """
        Track context load (Q4: Double-click auto-load).

        Updates load_count and avg_load_time_ms in database.

        Args:
            task_id: Task ID
            load_request: Load tracking request with load_time_ms

        Returns:
            ContextLoadResponse with updated stats

        Raises:
            ContextNotFoundError: If context not found for task
        """
        async with self.db_pool.acquire() as conn:
            # First, get current stats
            select_query = """
                SELECT
                    context_id,
                    double_click_loads,
                    manual_loads,
                    context_metadata
                FROM kanban.task_contexts
                WHERE task_id = $1
            """
            row = await conn.fetchrow(select_query, task_id)

            if not row:
                raise ContextNotFoundError(f"Context not found for task {task_id}")

            # Calculate new average load time
            old_count = row["double_click_loads"] + row["manual_loads"]
            metadata_json = row["context_metadata"] or {}
            if isinstance(metadata_json, str):
                metadata_json = json.loads(metadata_json)

            old_avg = metadata_json.get("avg_load_time_ms", 0)
            new_count = old_count + 1
            new_avg = ((old_avg * old_count) + load_request.load_time_ms) // new_count

            # Update metadata with new avg
            metadata_json["avg_load_time_ms"] = new_avg

            # Update database
            update_query = """
                UPDATE kanban.task_contexts
                SET
                    double_click_loads = double_click_loads + 1,
                    last_loaded_at = CURRENT_TIMESTAMP,
                    context_metadata = $2,
                    updated_at = CURRENT_TIMESTAMP
                WHERE task_id = $1
                RETURNING last_loaded_at
            """
            update_row = await conn.fetchrow(update_query, task_id, json.dumps(metadata_json))
            last_loaded_at = update_row["last_loaded_at"]

        logger.info(
            f"Tracked context load for task {task_id}: "
            f"load #{new_count}, time {load_request.load_time_ms}ms, "
            f"avg {new_avg}ms"
        )

        return ContextLoadResponse(
            success=True,
            load_count=new_count,
            avg_load_time_ms=new_avg,
            last_loaded_at=last_loaded_at,
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
        async with self.db_pool.acquire() as conn:
            query = """
                DELETE FROM kanban.task_contexts
                WHERE task_id = $1
                RETURNING context_id
            """
            row = await conn.fetchrow(query, task_id)

            if row:
                logger.info(f"Deleted context for task {task_id}")
                return True
            return False

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _estimate_zip_size(self, file_paths: list[str]) -> int:
        """
        Estimate ZIP size from file paths.

        Args:
            file_paths: List of file paths

        Returns:
            Estimated size in bytes (100KB per file average)
        """
        return len(file_paths) * 100 * 1024

    def _detect_zip_bomb(
        self, compressed_size: int, uncompressed_size: int, file_count: int, zip_file: zipfile.ZipFile
    ) -> None:
        """
        Detect ZIP bomb attacks (P0-2 Security).

        ZIP bombs are malicious archives designed to crash or render useless the system reading it.
        Detection criteria:
        1. Compression ratio > 100:1 (highly suspicious)
        2. File count > 10,000 (excessive files)
        3. Uncompressed size > 1GB (resource exhaustion)
        4. Deeply nested directories (> 10 levels)

        Args:
            compressed_size: ZIP file size in bytes
            uncompressed_size: Total uncompressed size in bytes
            file_count: Number of files in ZIP
            zip_file: ZipFile object for additional checks

        Raises:
            ZipBombDetected: If any ZIP bomb indicators detected
        """
        from backend.app.models.kanban_context import ZipBombDetected

        # Check 1: Compression ratio (> 100:1)
        if uncompressed_size > 0:
            compression_ratio = uncompressed_size / compressed_size
            if compression_ratio > 100:
                raise ZipBombDetected(
                    f"Suspicious compression ratio: {compression_ratio:.1f}:1 "
                    f"(compressed: {compressed_size / 1024 / 1024:.2f}MB, "
                    f"uncompressed: {uncompressed_size / 1024 / 1024:.2f}MB)"
                )

        # Check 2: File count (> 10,000)
        if file_count > 10000:
            raise ZipBombDetected(f"Excessive file count: {file_count} files (limit: 10,000)")

        # Check 3: Uncompressed size (> 1GB)
        MAX_UNCOMPRESSED_SIZE = 1 * 1024 * 1024 * 1024  # 1GB
        if uncompressed_size > MAX_UNCOMPRESSED_SIZE:
            raise ZipBombDetected(
                f"Excessive uncompressed size: {uncompressed_size / 1024 / 1024 / 1024:.2f}GB " f"(limit: 1GB)"
            )

        # Check 4: Deeply nested directories (> 10 levels)
        for name in zip_file.namelist():
            depth = name.count("/")
            if depth > 10:
                raise ZipBombDetected(f"Deeply nested path detected: {name} (depth: {depth}, limit: 10)")

        logger.info(
            f"ZIP bomb check passed: ratio={uncompressed_size / compressed_size:.1f}:1, "
            f"files={file_count}, size={uncompressed_size / 1024 / 1024:.2f}MB"
        )

    async def _scan_for_virus(self, contents: bytes, filename: str) -> None:
        """
        Scan file for viruses using ClamAV (P0-2 Security).

        Uses pyclamd library to connect to ClamAV daemon.
        In development, if ClamAV is not available, logs warning but allows upload.
        In production, virus scan failure blocks upload.

        Args:
            contents: File contents as bytes
            filename: Original filename for logging

        Raises:
            VirusDetected: If virus found in file
        """
        from backend.app.models.kanban_context import VirusDetected
        import os

        # Check if we're in development mode (allow bypassing ClamAV if not available)
        is_dev = os.getenv("ENVIRONMENT", "development") == "development"

        try:
            import pyclamd

            # Try to connect to ClamAV daemon
            cd = pyclamd.ClamdUnixSocket() if os.name != "nt" else pyclamd.ClamdNetworkSocket()

            # Ping to check if ClamAV is running
            if not cd.ping():
                if is_dev:
                    logger.warning(f"ClamAV daemon not responding - SKIPPING virus scan in DEV mode " f"(file: {filename})")
                    return
                else:
                    raise VirusDetected("Virus scanning service unavailable (production mode)")

            # Scan the file contents
            scan_result = cd.scan_stream(contents)

            if scan_result:
                # Virus detected - scan_result format: {stream: ('FOUND', 'Virus.Name')}
                virus_info = scan_result.get("stream", ("UNKNOWN", "Unknown virus"))
                virus_name = virus_info[1] if len(virus_info) > 1 else "Unknown"
                raise VirusDetected(f"Virus detected in {filename}: {virus_name}")

            logger.info(f"Virus scan passed: {filename} ({len(contents)} bytes)")

        except ImportError:
            # pyclamd not installed
            if is_dev:
                logger.warning(
                    f"pyclamd not installed - SKIPPING virus scan in DEV mode "
                    f"(file: {filename}). "
                    "Install: pip install pyclamd"
                )
            else:
                raise VirusDetected("Virus scanning library not available (production mode)")
        except Exception as e:
            # Other errors (connection failed, etc.)
            if is_dev:
                logger.warning(f"Virus scan failed in DEV mode: {e} - ALLOWING upload (file: {filename})")
            else:
                raise VirusDetected(f"Virus scan failed: {str(e)}")


# ============================================================================
# Mock Service for Testing
# ============================================================================


class MockKanbanContextService:
    """
    Mock implementation of KanbanContextService for testing without database.

    Uses in-memory Dict storage for all operations.
    """

    def __init__(self):
        """Initialize with empty mock storage."""
        self._mock_contexts: Dict[UUID, TaskContext] = {}
        self._storage_url = "/api/kanban/context"
        logger.info("MockKanbanContextService initialized")

    async def get_context_metadata(self, task_id: UUID) -> Optional[ContextMetadata]:
        """Get context metadata for task."""
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
        """Get full context including files list."""
        for context in self._mock_contexts.values():
            if context.task_id == task_id:
                return context
        return None

    async def get_context_zip(self, task_id: UUID) -> Optional[bytes]:
        """Mock: Returns None as no actual ZIP is stored."""
        return None

    async def upload_context(self, task_id: UUID, upload_request: ContextUploadRequest) -> ContextUploadResponse:
        """Upload context files as mock storage."""
        if not upload_request.files:
            raise InvalidContextFiles("At least one file path required")

        estimated_size = len(upload_request.files) * 100 * 1024
        if estimated_size > 52428800:
            raise ContextSizeLimitExceeded(f"Size {estimated_size} exceeds 50MB limit")

        file_list_str = ",".join(sorted(upload_request.files))
        zip_checksum = hashlib.sha256(file_list_str.encode()).hexdigest()

        context_id = uuid4()
        context = TaskContext(
            context_id=context_id,
            task_id=task_id,
            files=upload_request.files,
            file_count=len(upload_request.files),
            git_branch=upload_request.git_branch,
            last_commit_hash=upload_request.git_commit_hash,
            last_commit_message=upload_request.git_commit_message,
            zip_url=f"{self._storage_url}/{task_id}/download",
            zip_size_bytes=estimated_size,
            zip_checksum=zip_checksum,
            obsidian_notes=upload_request.obsidian_notes or [],
        )

        # Remove existing context for task
        self._mock_contexts = {k: v for k, v in self._mock_contexts.items() if v.task_id != task_id}
        self._mock_contexts[context_id] = context

        return ContextUploadResponse(
            context_id=context_id,
            task_id=task_id,
            zip_url=context.zip_url,
            zip_size_bytes=estimated_size,
            zip_checksum=zip_checksum,
            file_count=len(upload_request.files),
            created_at=context.created_at,
        )

    async def upload_context_file(self, task_id: UUID, filename: str, contents: bytes) -> ContextUploadResponse:
        """Upload context ZIP file (mock)."""
        MAX_SIZE = 50 * 1024 * 1024
        if len(contents) > MAX_SIZE:
            raise ContextSizeLimitExceeded(f"Size {len(contents)} exceeds 50MB limit")

        try:
            zip_buffer = io.BytesIO(contents)
            with zipfile.ZipFile(zip_buffer, "r") as zip_file:
                file_list = [n for n in zip_file.namelist() if not n.endswith("/")]
                if not file_list:
                    raise InvalidContextFiles("ZIP file contains no files")
        except zipfile.BadZipFile:
            raise InvalidContextFiles("Invalid ZIP file format")

        zip_checksum = hashlib.sha256(contents).hexdigest()
        context_id = uuid4()

        context = TaskContext(
            context_id=context_id,
            task_id=task_id,
            files=file_list,
            file_count=len(file_list),
            zip_url=f"{self._storage_url}/{task_id}/download",
            zip_size_bytes=len(contents),
            zip_checksum=zip_checksum,
        )

        self._mock_contexts = {k: v for k, v in self._mock_contexts.items() if v.task_id != task_id}
        self._mock_contexts[context_id] = context

        return ContextUploadResponse(
            context_id=context_id,
            task_id=task_id,
            zip_url=context.zip_url,
            zip_size_bytes=len(contents),
            zip_checksum=zip_checksum,
            file_count=len(file_list),
            created_at=context.created_at,
        )

    async def track_context_load(self, task_id: UUID, load_request: ContextLoadRequest) -> ContextLoadResponse:
        """Track context load (mock)."""
        context = await self.get_context_full(task_id)
        if not context:
            raise ContextNotFoundError(f"Context not found for task {task_id}")

        old_avg = context.avg_load_time_ms or 0
        old_count = context.load_count
        new_count = old_count + 1
        new_avg = ((old_avg * old_count) + load_request.load_time_ms) // new_count

        context.load_count = new_count
        context.avg_load_time_ms = new_avg
        context.last_loaded_at = datetime.now(UTC)
        context.updated_at = datetime.now(UTC)

        return ContextLoadResponse(
            success=True,
            load_count=new_count,
            avg_load_time_ms=new_avg,
            last_loaded_at=context.last_loaded_at,
        )

    async def delete_context(self, task_id: UUID) -> bool:
        """Delete context for task (mock)."""
        to_delete = [k for k, v in self._mock_contexts.items() if v.task_id == task_id]
        if to_delete:
            for k in to_delete:
                del self._mock_contexts[k]
            return True
        return False


# ============================================================================
# Singleton Instance for Testing
# ============================================================================

kanban_context_service = MockKanbanContextService()


# ============================================================================
# Dependency Injection
# ============================================================================


def get_kanban_context_service() -> KanbanContextService:
    """
    Dependency function for FastAPI routes.

    Returns a KanbanContextService instance with the global database pool.
    Used via Depends(get_kanban_context_service) in route handlers.
    """
    from backend.async_database import async_db

    db_pool = async_db.get_pool()
    if db_pool is None:
        raise RuntimeError("Database pool not initialized. Ensure startup_event has run.")

    return KanbanContextService(db_pool=db_pool)
