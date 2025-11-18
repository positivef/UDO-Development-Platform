"""
Version History API Router
Provides endpoints for Git version history and commit tracking
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
import logging

from ..models.version_history import (
    VersionHistory,
    VersionCommit,
    VersionComparison,
    VersionHistoryQuery
)
from ..services.git_service import GitService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/version-history",
    tags=["version-history"]
)

# Default project path (can be configured)
DEFAULT_PROJECT_PATH = Path(__file__).parent.parent.parent.parent


@router.get("/", response_model=VersionHistory)
async def get_version_history(
    project_path: Optional[str] = Query(
        default=None,
        description="Path to Git repository (default: current project)"
    ),
    branch: Optional[str] = Query(
        default=None,
        description="Branch name (default: current branch)"
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of commits to return"
    ),
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of commits to skip"
    ),
    author: Optional[str] = Query(
        default=None,
        description="Filter by author email"
    ),
    since: Optional[datetime] = Query(
        default=None,
        description="Commits after this date (ISO 8601)"
    ),
    until: Optional[datetime] = Query(
        default=None,
        description="Commits before this date (ISO 8601)"
    ),
    search: Optional[str] = Query(
        default=None,
        description="Search in commit messages"
    )
):
    """
    Get version history for a project

    Returns Git commit history with file changes, statistics, and metadata.

    **Query Parameters:**
    - `project_path`: Path to Git repository (optional, defaults to current project)
    - `branch`: Branch to query (optional, defaults to current branch)
    - `limit`: Maximum number of commits (1-500, default: 50)
    - `skip`: Number of commits to skip for pagination
    - `author`: Filter by author email
    - `since`: Show commits after this date
    - `until`: Show commits before this date
    - `search`: Search text in commit messages

    **Example:**
    ```
    GET /api/version-history/?limit=20&branch=main&author=john@example.com
    ```
    """
    try:
        # Determine project path
        repo_path = project_path if project_path else str(DEFAULT_PROJECT_PATH)

        # Initialize Git service
        git_service = GitService(repo_path)

        # Get version history
        history = git_service.get_version_history(
            branch=branch,
            limit=limit,
            skip=skip
        )

        # Apply additional filters if needed
        if author or since or until or search:
            filtered_commits = git_service.get_commits(
                branch=branch,
                limit=limit,
                skip=skip,
                author=author,
                since=since,
                until=until,
                search=search
            )
            history.commits = filtered_commits

        return history

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting version history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get version history: {str(e)}")


@router.get("/commits/{commit_hash}", response_model=VersionCommit)
async def get_commit_details(
    commit_hash: str,
    project_path: Optional[str] = Query(
        default=None,
        description="Path to Git repository"
    )
):
    """
    Get details for a specific commit

    **Path Parameters:**
    - `commit_hash`: Full or short Git commit hash

    **Example:**
    ```
    GET /api/version-history/commits/a1b2c3d
    ```
    """
    try:
        repo_path = project_path if project_path else str(DEFAULT_PROJECT_PATH)
        git_service = GitService(repo_path)

        # Get commits (limit 1) starting from this hash
        commits = git_service.get_commits(limit=1, skip=0)

        # Find the commit
        for commit in commits:
            if commit.commit_hash == commit_hash or commit.short_hash == commit_hash:
                return commit

        raise HTTPException(status_code=404, detail=f"Commit not found: {commit_hash}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting commit details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare", response_model=VersionComparison)
async def compare_commits(
    from_commit: str = Query(..., description="Source commit hash"),
    to_commit: str = Query(..., description="Target commit hash"),
    project_path: Optional[str] = Query(
        default=None,
        description="Path to Git repository"
    )
):
    """
    Compare two commits

    Returns differences between two commits including file changes,
    line statistics, and commits in between.

    **Query Parameters:**
    - `from_commit`: Source commit hash (full or short)
    - `to_commit`: Target commit hash (full or short)

    **Example:**
    ```
    GET /api/version-history/compare?from_commit=a1b2c3d&to_commit=x9y8z7w
    ```
    """
    try:
        repo_path = project_path if project_path else str(DEFAULT_PROJECT_PATH)
        git_service = GitService(repo_path)

        comparison = git_service.compare_commits(from_commit, to_commit)

        return comparison

    except Exception as e:
        logger.error(f"Error comparing commits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_repository_stats(
    project_path: Optional[str] = Query(
        default=None,
        description="Path to Git repository"
    )
):
    """
    Get repository statistics

    Returns high-level statistics about the repository including
    commit count, contributors, date range, etc.

    **Example:**
    ```
    GET /api/version-history/stats
    ```
    """
    try:
        repo_path = project_path if project_path else str(DEFAULT_PROJECT_PATH)
        git_service = GitService(repo_path)

        current_branch = git_service.get_current_branch()
        total_commits = git_service.get_commit_count()

        # Get all commits to calculate stats
        all_commits = git_service.get_commits(limit=1000)

        unique_authors = set()
        first_commit_date = None
        last_commit_date = None
        total_lines_added = 0
        total_lines_deleted = 0

        for commit in all_commits:
            unique_authors.add(commit.author_email)
            total_lines_added += commit.lines_added
            total_lines_deleted += commit.lines_deleted

            if first_commit_date is None or commit.date < first_commit_date:
                first_commit_date = commit.date

            if last_commit_date is None or commit.date > last_commit_date:
                last_commit_date = commit.date

        return {
            "project_name": Path(repo_path).name,
            "project_path": repo_path,
            "current_branch": current_branch,
            "total_commits": total_commits,
            "total_contributors": len(unique_authors),
            "first_commit_date": first_commit_date,
            "last_commit_date": last_commit_date,
            "total_lines_added": total_lines_added,
            "total_lines_deleted": total_lines_deleted,
            "net_lines": total_lines_added - total_lines_deleted
        }

    except Exception as e:
        logger.error(f"Error getting repository stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/branches")
async def list_branches(
    project_path: Optional[str] = Query(
        default=None,
        description="Path to Git repository"
    )
):
    """
    List all branches in repository

    **Example:**
    ```
    GET /api/version-history/branches
    ```
    """
    try:
        repo_path = project_path if project_path else str(DEFAULT_PROJECT_PATH)
        git_service = GitService(repo_path)

        stdout, _, returncode = git_service._run_git_command([
            "branch", "--format=%(refname:short)"
        ])

        if returncode != 0:
            raise HTTPException(status_code=500, detail="Failed to list branches")

        branches = [b.strip() for b in stdout.split("\n") if b.strip()]
        current_branch = git_service.get_current_branch()

        return {
            "branches": branches,
            "current_branch": current_branch,
            "total": len(branches)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing branches: {e}")
        raise HTTPException(status_code=500, detail=str(e))
