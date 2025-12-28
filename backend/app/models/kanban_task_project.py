"""
Kanban Task-Project Relationship Models (P0 Critical Issue #3).

Implements Q5 decision: 1 Primary + max 3 Related projects per task.

Database constraints:
- Unique index: exactly 1 primary per task
- Trigger: max 3 related projects enforcement
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class TaskProjectBase(BaseModel):
    """Base model for task-project relationship"""

    task_id: UUID = Field(..., description="Task ID")
    project_id: UUID = Field(..., description="Project ID")
    is_primary: bool = Field(False, description="Is this the primary project?")


class TaskProjectCreate(TaskProjectBase):
    """Create task-project relationship"""

    pass


class TaskProjectUpdate(BaseModel):
    """Update task-project relationship"""

    is_primary: Optional[bool] = None


class TaskProject(TaskProjectBase):
    """Task-Project relationship (from database)"""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class TaskProjectAssignment(BaseModel):
    """Complete project assignment for a task"""

    task_id: UUID
    primary_project: UUID = Field(..., description="Primary project (required)")
    related_projects: List[UUID] = Field(
        default_factory=list, max_length=3, description="Related projects (max 3)"
    )

    @field_validator("related_projects")
    @classmethod
    def validate_related_count(cls, v):
        """Enforce max 3 related projects"""
        if len(v) > 3:
            raise ValueError("Maximum 3 related projects allowed")
        return v

    @field_validator("related_projects")
    @classmethod
    def validate_no_duplicates(cls, v, info):
        """Ensure no duplicate project IDs"""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate project IDs in related_projects")
        return v

    @field_validator("related_projects")
    @classmethod
    def validate_primary_not_in_related(cls, v, info):
        """Primary project cannot be in related projects"""
        if "primary_project" in info.data and info.data["primary_project"] in v:
            raise ValueError("Primary project cannot be in related_projects")
        return v


class SetPrimaryProjectRequest(BaseModel):
    """Request to set primary project"""

    task_id: UUID
    project_id: UUID


class AddRelatedProjectRequest(BaseModel):
    """Request to add related project"""

    task_id: UUID
    project_id: UUID


class RemoveRelatedProjectRequest(BaseModel):
    """Request to remove related project"""

    task_id: UUID
    project_id: UUID


class TaskProjectSummary(BaseModel):
    """Summary of task's project relationships"""

    task_id: UUID
    primary_project: Optional[TaskProject] = None
    related_projects: List[TaskProject] = Field(default_factory=list)
    total_projects: int = 0

    def __init__(self, **data):
        super().__init__(**data)
        self.total_projects = 1 if self.primary_project else 0
        self.total_projects += len(self.related_projects)


class MultiProjectConstraintError(Exception):
    """Raised when multi-project constraints are violated"""

    pass


class MaxRelatedProjectsError(MultiProjectConstraintError):
    """Raised when trying to add more than 3 related projects"""

    def __init__(self):
        super().__init__("Maximum 3 related projects allowed per task (Q5 constraint)")


class NoPrimaryProjectError(MultiProjectConstraintError):
    """Raised when task has no primary project"""

    def __init__(self, task_id: UUID):
        super().__init__(f"Task {task_id} must have exactly 1 primary project")


class MultiplePrimaryProjectsError(MultiProjectConstraintError):
    """Raised when task has multiple primary projects"""

    def __init__(self, task_id: UUID):
        super().__init__(
            f"Task {task_id} has multiple primary projects (constraint violation)"
        )
