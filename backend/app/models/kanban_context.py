"""
Kanban Context Models

Week 2 Day 5: Context operations (ZIP upload/download, metadata)
Implements Q4 (Double-click auto-load, single-click popup)
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# Context Models
# ============================================================================


class TaskContext(BaseModel):
    """
    Task context model with ZIP storage support.

    Q4: Double-click auto-load (load_count, avg_load_time_ms tracking)
    """

    context_id: UUID = Field(default_factory=uuid4)
    task_id: UUID

    # Context Files
    files: List[str] = Field(default_factory=list, description="Array of file paths")
    file_count: int = Field(default=0, ge=0)

    # Git Info
    git_branch: Optional[str] = None
    last_commit_hash: Optional[str] = Field(None, max_length=40)
    last_commit_message: Optional[str] = None

    # ZIP Storage (Q4: Context loading)
    zip_url: Optional[str] = None
    zip_size_bytes: Optional[int] = Field(None, le=52428800, description="50MB limit")
    zip_checksum: Optional[str] = Field(None, max_length=64, description="SHA-256")

    # Obsidian Notes
    obsidian_notes: List[str] = Field(default_factory=list, description="Array of note paths")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_loaded_at: Optional[datetime] = None

    # Double-click tracking (Q4)
    load_count: int = Field(default=0, ge=0)
    avg_load_time_ms: Optional[int] = Field(None, ge=0)

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "context_id": "550e8400-e29b-41d4-a716-446655440000",
                "task_id": "550e8400-e29b-41d4-a716-446655440001",
                "files": ["src/main.py", "tests/test_main.py"],
                "file_count": 2,
                "git_branch": "feature/auth",
                "last_commit_hash": "abc123def456",
                "zip_url": "https://storage.example.com/contexts/550e8400.zip",
                "zip_size_bytes": 1024000,
                "load_count": 5,
                "avg_load_time_ms": 150,
            }
        }


class ContextMetadata(BaseModel):
    """
    Context metadata response (without full files list).

    Used for GET /api/kanban/tasks/{id}/context endpoint.
    """

    context_id: UUID
    task_id: UUID
    file_count: int
    git_branch: Optional[str] = None
    last_commit_hash: Optional[str] = Field(None, max_length=40)
    zip_url: Optional[str] = None
    zip_size_bytes: Optional[int] = None
    last_loaded_at: Optional[datetime] = None
    load_count: int = Field(default=0)
    avg_load_time_ms: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContextUploadRequest(BaseModel):
    """
    Context upload request.

    POST /api/kanban/tasks/{id}/context
    """

    files: List[str] = Field(..., min_length=1, description="Array of file paths to include")
    git_branch: Optional[str] = None
    git_commit_hash: Optional[str] = Field(None, max_length=40)
    git_commit_message: Optional[str] = None
    obsidian_notes: List[str] = Field(default_factory=list)

    @field_validator("files")
    @classmethod
    def validate_files(cls, v):
        if len(v) == 0:
            raise ValueError("At least one file path required")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "files": ["src/main.py", "tests/test_main.py", "README.md"],
                "git_branch": "feature/auth",
                "git_commit_hash": "abc123def456",
                "git_commit_message": "feat: Add authentication",
                "obsidian_notes": ["Projects/UDO/Auth Design.md"],
            }
        }


class ContextLoadRequest(BaseModel):
    """
    Context load tracking request (Q4: Double-click tracking).

    POST /api/kanban/tasks/{id}/context/load
    """

    load_time_ms: int = Field(..., ge=0, description="Time taken to load context (ms)")

    class Config:
        json_schema_extra = {"example": {"load_time_ms": 150}}


class ContextLoadResponse(BaseModel):
    """
    Context load tracking response.
    """

    success: bool
    load_count: int
    avg_load_time_ms: int
    last_loaded_at: datetime

    class Config:
        json_schema_extra = {
            "example": {"success": True, "load_count": 6, "avg_load_time_ms": 145, "last_loaded_at": "2025-12-04T10:30:00Z"}
        }


class ContextUploadResponse(BaseModel):
    """
    Context upload response with ZIP URL.
    """

    context_id: UUID
    task_id: UUID
    zip_url: str
    zip_size_bytes: int
    zip_checksum: str
    file_count: int
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "context_id": "550e8400-e29b-41d4-a716-446655440000",
                "task_id": "550e8400-e29b-41d4-a716-446655440001",
                "zip_url": "https://storage.example.com/contexts/550e8400.zip",
                "zip_size_bytes": 1024000,
                "zip_checksum": "abc123def456...",
                "file_count": 3,
                "created_at": "2025-12-04T10:30:00Z",
            }
        }


# ============================================================================
# Error Models
# ============================================================================


class ContextNotFoundError(Exception):
    """Raised when context not found for task"""

    pass


class ContextSizeLimitExceeded(Exception):
    """Raised when ZIP size exceeds 50MB limit"""

    pass


class InvalidContextFiles(Exception):
    """Raised when file list is invalid or empty"""

    pass


class ZipBombDetected(Exception):
    """Raised when ZIP bomb detected (suspicious compression ratio or file count)"""

    pass


class VirusDetected(Exception):
    """Raised when virus detected in uploaded file"""

    pass
