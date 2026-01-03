"""
Kanban Project Service - Multi-Project Management (P0 Critical Issue #3).

Implements Q5 decision: 1 Primary + max 3 Related projects per task.

Business logic:
- set_primary_project(): Atomic primary project switching
- add_related_project(): Max 3 related projects enforcement
- remove_related_project(): Safe removal
- validate_constraints(): Integrity checks
"""

from typing import List, Optional
from uuid import UUID

from app.models.kanban_task_project import (
    MaxRelatedProjectsError,
    MultiplePrimaryProjectsError,
    NoPrimaryProjectError,
    TaskProject,
    TaskProjectSummary,
)


class KanbanProjectService:
    """
    Service for managing task-project relationships.

    Critical constraints (Q5):
    - Exactly 1 primary project per task
    - Maximum 3 related projects per task
    - Primary cannot be in related projects
    """

    def __init__(self, db_session=None):
        """
        Initialize service with database session.

        Args:
            db_session: Database session (optional for testing with mock data)
        """
        self.db = db_session
        # In-memory storage for testing (will be replaced by DB)
        self._mock_projects: dict[UUID, List[TaskProject]] = {}

    async def set_primary_project(self, task_id: UUID, project_id: UUID) -> TaskProject:
        """
        Set primary project for a task (atomic operation).

        Algorithm:
        1. Remove existing primary (if any)
        2. Set new primary
        3. Validate exactly 1 primary exists

        Args:
            task_id: Task ID
            project_id: Project ID to set as primary

        Returns:
            Updated TaskProject

        Raises:
            MultiplePrimaryProjectsError: If constraint violated
        """
        # Step 1: Remove existing primary
        await self._remove_primary_project(task_id)

        # Step 2: Check if project_id is already related
        existing_related = await self._get_related_projects(task_id)
        if any(p.project_id == project_id for p in existing_related):
            # Remove from related projects first
            await self.remove_related_project(task_id, project_id)

        # Step 3: Set new primary
        task_project = TaskProject(task_id=task_id, project_id=project_id, is_primary=True)

        if self.db:
            # Database implementation (when DB is available)
            # await self.db.execute(
            #     "INSERT INTO kanban.task_projects (task_id, project_id, is_primary) "
            #     "VALUES (:task_id, :project_id, true)",
            #     {"task_id": task_id, "project_id": project_id}
            # )
            pass
        else:
            # Mock implementation for testing
            if task_id not in self._mock_projects:
                self._mock_projects[task_id] = []
            self._mock_projects[task_id].append(task_project)

        # Step 4: Validate constraint
        await self._validate_single_primary(task_id)

        return task_project

    async def add_related_project(self, task_id: UUID, project_id: UUID) -> TaskProject:
        """
        Add related project to task.

        Args:
            task_id: Task ID
            project_id: Project ID to add as related

        Returns:
            Created TaskProject

        Raises:
            MaxRelatedProjectsError: If already has 3 related projects
            ValueError: If project_id is same as primary or already related
        """
        # Check max 3 related projects
        existing_related = await self._get_related_projects(task_id)
        if len(existing_related) >= 3:
            raise MaxRelatedProjectsError()

        # Check if already primary
        primary = await self._get_primary_project(task_id)
        if primary and primary.project_id == project_id:
            raise ValueError(f"Project {project_id} is already the primary project")

        # Check if already related
        if any(p.project_id == project_id for p in existing_related):
            raise ValueError(f"Project {project_id} is already a related project")

        # Add as related
        task_project = TaskProject(task_id=task_id, project_id=project_id, is_primary=False)

        if self.db:
            # Database implementation (when DB is available)
            pass
        else:
            # Mock implementation
            if task_id not in self._mock_projects:
                self._mock_projects[task_id] = []
            self._mock_projects[task_id].append(task_project)

        return task_project

    async def remove_related_project(self, task_id: UUID, project_id: UUID) -> bool:
        """
        Remove related project from task.

        Args:
            task_id: Task ID
            project_id: Project ID to remove

        Returns:
            True if removed, False if not found

        Raises:
            ValueError: If trying to remove primary project (use set_primary_project instead)
        """
        # Check if it's the primary project
        primary = await self._get_primary_project(task_id)
        if primary and primary.project_id == project_id:
            raise ValueError(f"Cannot remove primary project {project_id}. " "Use set_primary_project() to change primary.")

        # Remove from related
        if self.db:
            # Database implementation
            pass
        else:
            # Mock implementation
            if task_id in self._mock_projects:
                original_length = len(self._mock_projects[task_id])
                self._mock_projects[task_id] = [
                    p for p in self._mock_projects[task_id] if not (p.project_id == project_id and not p.is_primary)
                ]
                # Return True only if something was actually removed
                return len(self._mock_projects[task_id]) < original_length

        return False

    async def get_task_projects(self, task_id: UUID) -> TaskProjectSummary:
        """
        Get all project relationships for a task.

        Args:
            task_id: Task ID

        Returns:
            TaskProjectSummary with primary and related projects
        """
        primary = await self._get_primary_project(task_id)
        related = await self._get_related_projects(task_id)

        return TaskProjectSummary(task_id=task_id, primary_project=primary, related_projects=related)

    async def validate_constraints(self, task_id: UUID) -> dict:
        """
        Validate all multi-project constraints for a task.

        Args:
            task_id: Task ID

        Returns:
            Validation result with status and errors
        """
        errors = []

        # Check exactly 1 primary
        try:
            await self._validate_single_primary(task_id)
        except (NoPrimaryProjectError, MultiplePrimaryProjectsError) as e:
            errors.append(str(e))

        # Check max 3 related
        related = await self._get_related_projects(task_id)
        if len(related) > 3:
            errors.append(f"Task has {len(related)} related projects (max 3 allowed)")

        # Check no duplicates
        project_ids = [p.project_id for p in await self._get_all_projects(task_id)]
        if len(project_ids) != len(set(project_ids)):
            errors.append("Duplicate project IDs detected")

        return {"valid": len(errors) == 0, "errors": errors, "task_id": str(task_id)}

    # ============================================================
    # Private Helper Methods
    # ============================================================

    async def _get_primary_project(self, task_id: UUID) -> Optional[TaskProject]:
        """Get primary project for task"""
        if self.db:
            # Database implementation
            pass
        else:
            # Mock implementation
            projects = self._mock_projects.get(task_id, [])
            primaries = [p for p in projects if p.is_primary]
            return primaries[0] if primaries else None

    async def _get_related_projects(self, task_id: UUID) -> List[TaskProject]:
        """Get related projects for task"""
        if self.db:
            # Database implementation
            pass
        else:
            # Mock implementation
            projects = self._mock_projects.get(task_id, [])
            return [p for p in projects if not p.is_primary]

    async def _get_all_projects(self, task_id: UUID) -> List[TaskProject]:
        """Get all projects for task"""
        if self.db:
            # Database implementation
            pass
        else:
            # Mock implementation
            return self._mock_projects.get(task_id, [])

    async def _remove_primary_project(self, task_id: UUID) -> None:
        """Remove existing primary project"""
        if self.db:
            # Database implementation
            # await self.db.execute(
            #     "DELETE FROM kanban.task_projects "
            #     "WHERE task_id=:task_id AND is_primary=true",
            #     {"task_id": task_id}
            # )
            pass
        else:
            # Mock implementation
            if task_id in self._mock_projects:
                self._mock_projects[task_id] = [p for p in self._mock_projects[task_id] if not p.is_primary]

    async def _validate_single_primary(self, task_id: UUID) -> None:
        """
        Validate exactly 1 primary project exists.

        Raises:
            NoPrimaryProjectError: If no primary project
            MultiplePrimaryProjectsError: If multiple primary projects
        """
        if self.db:
            # Database implementation
            pass
        else:
            # Mock implementation
            projects = self._mock_projects.get(task_id, [])
            primaries = [p for p in projects if p.is_primary]

            if len(primaries) == 0:
                raise NoPrimaryProjectError(task_id)
            elif len(primaries) > 1:
                raise MultiplePrimaryProjectsError(task_id)


# Global service instance (can be imported and used across application)
kanban_project_service = KanbanProjectService()


def get_kanban_project_service(db_session=None) -> KanbanProjectService:
    """Get Kanban project service instance"""
    if db_session:
        return KanbanProjectService(db_session)
    return kanban_project_service
