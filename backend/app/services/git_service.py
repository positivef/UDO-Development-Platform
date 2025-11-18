"""
Git Integration Service
Provides Git repository interaction and version history extraction
"""
import subprocess
import os
import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import logging

from ..models.version_history import VersionCommit, VersionHistory, VersionComparison

logger = logging.getLogger(__name__)


class GitService:
    """Git repository service"""

    def __init__(self, repo_path: str):
        """
        Initialize Git service

        Args:
            repo_path: Path to Git repository
        """
        self.repo_path = Path(repo_path).resolve()

        if not self._is_git_repo():
            raise ValueError(f"Not a Git repository: {repo_path}")

    def _is_git_repo(self) -> bool:
        """Check if directory is a Git repository"""
        git_dir = self.repo_path / ".git"
        return git_dir.exists() and git_dir.is_dir()

    def _run_git_command(self, args: List[str]) -> Tuple[str, str, int]:
        """
        Run Git command

        Args:
            args: Git command arguments

        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except Exception as e:
            logger.error(f"Git command failed: {e}")
            return "", str(e), 1

    def get_current_branch(self) -> str:
        """Get current branch name"""
        stdout, _, returncode = self._run_git_command(["branch", "--show-current"])

        if returncode != 0:
            return "unknown"

        return stdout.strip() or "HEAD"

    def get_commit_count(self, branch: Optional[str] = None) -> int:
        """
        Get total commit count

        Args:
            branch: Branch name (default: current branch)

        Returns:
            Number of commits
        """
        args = ["rev-list", "--count", branch or "HEAD"]
        stdout, _, returncode = self._run_git_command(args)

        if returncode != 0:
            return 0

        try:
            return int(stdout.strip())
        except ValueError:
            return 0

    def get_commits(
        self,
        branch: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
        author: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        search: Optional[str] = None
    ) -> List[VersionCommit]:
        """
        Get commit history

        Args:
            branch: Branch name (default: current branch)
            limit: Maximum number of commits
            skip: Number of commits to skip
            author: Filter by author
            since: Commits after this date
            until: Commits before this date
            search: Search in commit messages

        Returns:
            List of VersionCommit objects
        """
        # Build Git log arguments
        args = [
            "log",
            f"--max-count={limit}",
            f"--skip={skip}",
            "--format=%H|%h|%an|%ae|%ai|%s|%b",
            "--numstat",
            "--no-merges"
        ]

        if branch:
            args.append(branch)
        else:
            args.append("HEAD")

        if author:
            args.append(f"--author={author}")

        if since:
            args.append(f"--since={since.isoformat()}")

        if until:
            args.append(f"--until={until.isoformat()}")

        if search:
            args.append(f"--grep={search}")

        stdout, stderr, returncode = self._run_git_command(args)

        if returncode != 0:
            logger.error(f"Failed to get commits: {stderr}")
            return []

        return self._parse_commit_log(stdout)

    def _parse_commit_log(self, log_output: str) -> List[VersionCommit]:
        """
        Parse Git log output

        Args:
            log_output: Output from git log --numstat

        Returns:
            List of VersionCommit objects
        """
        commits = []
        current_commit = None
        lines_added = 0
        lines_deleted = 0
        files_modified = []
        files_added = []
        files_deleted = []

        for line in log_output.split("\n"):
            line = line.strip()

            if not line:
                # Empty line marks end of commit stats
                if current_commit:
                    current_commit.lines_added = lines_added
                    current_commit.lines_deleted = lines_deleted
                    current_commit.files_modified = files_modified
                    current_commit.files_added = files_added
                    current_commit.files_deleted = files_deleted

                    commits.append(current_commit)

                    # Reset for next commit
                    current_commit = None
                    lines_added = 0
                    lines_deleted = 0
                    files_modified = []
                    files_added = []
                    files_deleted = []
                continue

            if "|" in line and not current_commit:
                # Commit header line
                parts = line.split("|")
                if len(parts) >= 6:
                    commit_hash = parts[0]
                    short_hash = parts[1]
                    author = parts[2]
                    author_email = parts[3]
                    date_str = parts[4]
                    message = parts[5]

                    # Parse date
                    try:
                        commit_date = datetime.fromisoformat(date_str.replace(" ", "T"))
                    except:
                        commit_date = datetime.now()

                    # Get tags for this commit
                    tags = self.get_commit_tags(commit_hash)

                    # Get branches for this commit
                    branches = self.get_commit_branches(commit_hash)

                    current_commit = VersionCommit(
                        commit_hash=commit_hash,
                        short_hash=short_hash,
                        author=author,
                        author_email=author_email,
                        date=commit_date,
                        message=message,
                        tags=tags,
                        branches=branches
                    )

            elif current_commit and "\t" in line:
                # File stat line: "5\t3\tfile.py"
                parts = line.split("\t")
                if len(parts) >= 3:
                    added_str = parts[0]
                    deleted_str = parts[1]
                    filename = parts[2]

                    # Track file changes
                    if added_str == "-" and deleted_str == "-":
                        # Binary file
                        files_modified.append(filename)
                    elif added_str != "0" or deleted_str != "0":
                        # Modified file
                        files_modified.append(filename)

                        # Track lines
                        try:
                            lines_added += int(added_str) if added_str != "-" else 0
                            lines_deleted += int(deleted_str) if deleted_str != "-" else 0
                        except ValueError:
                            pass

        # Don't forget last commit
        if current_commit:
            current_commit.lines_added = lines_added
            current_commit.lines_deleted = lines_deleted
            current_commit.files_modified = files_modified
            commits.append(current_commit)

        return commits

    def get_commit_tags(self, commit_hash: str) -> List[str]:
        """Get tags pointing to a commit"""
        stdout, _, returncode = self._run_git_command([
            "tag", "--points-at", commit_hash
        ])

        if returncode != 0:
            return []

        tags = [tag.strip() for tag in stdout.split("\n") if tag.strip()]
        return tags

    def get_commit_branches(self, commit_hash: str) -> List[str]:
        """Get branches containing a commit"""
        stdout, _, returncode = self._run_git_command([
            "branch", "--contains", commit_hash, "--format=%(refname:short)"
        ])

        if returncode != 0:
            return []

        branches = [branch.strip() for branch in stdout.split("\n") if branch.strip()]
        return branches

    def get_version_history(
        self,
        branch: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> VersionHistory:
        """
        Get complete version history

        Args:
            branch: Branch name (default: current branch)
            limit: Maximum number of commits
            skip: Number of commits to skip

        Returns:
            VersionHistory object
        """
        current_branch = branch or self.get_current_branch()
        total_commits = self.get_commit_count(current_branch)

        commits = self.get_commits(
            branch=current_branch,
            limit=limit,
            skip=skip
        )

        # Calculate statistics
        unique_authors = set()
        first_commit_date = None
        last_commit_date = None

        for commit in commits:
            unique_authors.add(commit.author_email)

            if first_commit_date is None or commit.date < first_commit_date:
                first_commit_date = commit.date

            if last_commit_date is None or commit.date > last_commit_date:
                last_commit_date = commit.date

        return VersionHistory(
            project_name=self.repo_path.name,
            project_path=str(self.repo_path),
            current_branch=current_branch,
            total_commits=total_commits,
            commits=commits,
            total_contributors=len(unique_authors),
            first_commit_date=first_commit_date,
            last_commit_date=last_commit_date
        )

    def compare_commits(
        self,
        from_commit: str,
        to_commit: str
    ) -> VersionComparison:
        """
        Compare two commits

        Args:
            from_commit: Source commit hash
            to_commit: Target commit hash

        Returns:
            VersionComparison object
        """
        # Get diff stats
        stdout, _, returncode = self._run_git_command([
            "diff", "--numstat", from_commit, to_commit
        ])

        if returncode != 0:
            logger.error(f"Failed to compare commits")
            return VersionComparison(
                from_commit=from_commit,
                to_commit=to_commit
            )

        # Parse diff stats
        files_changed = []
        files_added = []
        files_deleted = []
        total_lines_added = 0
        total_lines_deleted = 0

        for line in stdout.split("\n"):
            line = line.strip()
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) >= 3:
                added_str = parts[0]
                deleted_str = parts[1]
                filename = parts[2]

                files_changed.append(filename)

                try:
                    if added_str != "-":
                        total_lines_added += int(added_str)
                    if deleted_str != "-":
                        total_lines_deleted += int(deleted_str)
                except ValueError:
                    pass

        # Get commits in between
        stdout, _, returncode = self._run_git_command([
            "log", f"{from_commit}..{to_commit}",
            "--format=%H|%h|%an|%ae|%ai|%s",
            "--no-merges"
        ])

        commits_between = []
        if returncode == 0:
            commits_between = self._parse_commit_log(stdout)

        return VersionComparison(
            from_commit=from_commit,
            to_commit=to_commit,
            files_changed=files_changed,
            files_added=files_added,
            files_deleted=files_deleted,
            total_lines_added=total_lines_added,
            total_lines_deleted=total_lines_deleted,
            commits_between=commits_between
        )
