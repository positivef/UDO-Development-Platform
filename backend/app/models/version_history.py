"""
Version History Data Models
Tracks Git commits with quality metrics snapshots
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VersionCommit(BaseModel):
    """Single Git commit with metadata"""

    commit_hash: str = Field(..., description="Full Git commit SHA")
    short_hash: str = Field(..., description="Short commit SHA (7 chars)")
    author: str = Field(..., description="Commit author name")
    author_email: str = Field(..., description="Commit author email")
    date: datetime = Field(..., description="Commit date")
    message: str = Field(..., description="Commit message")

    # File changes
    files_modified: List[str] = Field(
        default_factory=list, description="List of modified files"
    )
    files_added: List[str] = Field(
        default_factory=list, description="List of added files"
    )
    files_deleted: List[str] = Field(
        default_factory=list, description="List of deleted files"
    )
    lines_added: int = Field(default=0, description="Total lines added")
    lines_deleted: int = Field(default=0, description="Total lines deleted")

    # Quality metrics snapshot (if available)
    quality_metrics: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Quality metrics at this commit (test coverage, lint score, etc.)",
    )

    # UDO execution result (if this commit was created by UDO)
    udo_execution: Optional[Dict[str, Any]] = Field(
        default=None, description="UDO execution details that led to this commit"
    )

    # Tags and references
    tags: List[str] = Field(default_factory=list, description="Git tags at this commit")
    branches: List[str] = Field(
        default_factory=list, description="Branches containing this commit"
    )

    class Config:
        arbitrary_types_allowed = True
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "commit_hash": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
                "short_hash": "a1b2c3d",
                "author": "John Doe",
                "author_email": "john@example.com",
                "date": "2025-11-17T10:30:00Z",
                "message": "feat: Add user authentication",
                "files_modified": ["src/auth.py", "tests/test_auth.py"],
                "files_added": ["src/models/user.py"],
                "files_deleted": [],
                "lines_added": 250,
                "lines_deleted": 10,
                "quality_metrics": {"test_coverage": 85.5, "lint_score": 9.2},
                "tags": ["v1.2.0"],
                "branches": ["main", "feature/auth"],
            }
        }


class VersionHistory(BaseModel):
    """Complete version history for a project"""

    project_name: str = Field(..., description="Project name")
    project_path: str = Field(..., description="Project path")
    current_branch: str = Field(..., description="Current Git branch")
    total_commits: int = Field(..., description="Total number of commits")
    commits: List[VersionCommit] = Field(..., description="List of commits")

    # Statistics
    total_contributors: int = Field(
        default=0, description="Number of unique contributors"
    )
    first_commit_date: Optional[datetime] = Field(
        default=None, description="Date of first commit"
    )
    last_commit_date: Optional[datetime] = Field(
        default=None, description="Date of last commit"
    )

    class Config:
        arbitrary_types_allowed = True
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "project_name": "UDO-Development-Platform",
                "project_path": "/path/to/project",
                "current_branch": "main",
                "total_commits": 150,
                "commits": [],
                "total_contributors": 3,
                "first_commit_date": "2025-10-01T10:00:00Z",
                "last_commit_date": "2025-11-17T10:30:00Z",
            }
        }


class VersionComparison(BaseModel):
    """Comparison between two commits"""

    from_commit: str = Field(..., description="Source commit hash")
    to_commit: str = Field(..., description="Target commit hash")

    # File changes
    files_changed: List[str] = Field(
        default_factory=list, description="Files that changed"
    )
    files_added: List[str] = Field(default_factory=list, description="Files added")
    files_deleted: List[str] = Field(default_factory=list, description="Files deleted")

    # Line statistics
    total_lines_added: int = Field(default=0, description="Total lines added")
    total_lines_deleted: int = Field(default=0, description="Total lines deleted")

    # Quality metrics change
    quality_delta: Optional[Dict[str, float]] = Field(
        default=None, description="Change in quality metrics (positive = improvement)"
    )

    # Commits in between
    commits_between: List[VersionCommit] = Field(
        default_factory=list, description="Commits between from and to"
    )

    class Config:
        arbitrary_types_allowed = True
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "from_commit": "a1b2c3d",
                "to_commit": "x9y8z7w",
                "files_changed": ["src/auth.py"],
                "files_added": ["src/models/user.py"],
                "files_deleted": ["src/old_auth.py"],
                "total_lines_added": 500,
                "total_lines_deleted": 200,
                "quality_delta": {"test_coverage": 5.5, "lint_score": 0.3},
                "commits_between": [],
            }
        }


class VersionHistoryQuery(BaseModel):
    """Query parameters for version history"""

    branch: Optional[str] = Field(
        default=None, description="Branch to query (default: current)"
    )
    limit: int = Field(
        default=50, description="Maximum number of commits", ge=1, le=500
    )
    skip: int = Field(default=0, description="Number of commits to skip", ge=0)
    author: Optional[str] = Field(default=None, description="Filter by author")
    since: Optional[datetime] = Field(
        default=None, description="Commits after this date"
    )
    until: Optional[datetime] = Field(
        default=None, description="Commits before this date"
    )
    search: Optional[str] = Field(default=None, description="Search in commit messages")

    class Config:
        arbitrary_types_allowed = True
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "branch": "main",
                "limit": 50,
                "skip": 0,
                "author": "john@example.com",
                "since": "2025-11-01T00:00:00Z",
                "search": "feat",
            }
        }
