"""
Kanban Task Dependencies - DAG Implementation (P0 Critical Issue #4).

Implements directed acyclic graph (DAG) for task dependencies with:
- Cycle detection and prevention
- Topological sort using Kahn's Algorithm
- Performance target: <50ms for 1,000 tasks
- 4 dependency types: FS, SS, FF, SF (like MS Project)
"""

from datetime import datetime
from typing import List, Optional, Dict, Set
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from enum import Enum


class DependencyType(str, Enum):
    """
    Dependency types (Microsoft Project standard):

    - FS (Finish-to-Start): Task B starts after Task A finishes [default]
    - SS (Start-to-Start): Task B starts when Task A starts
    - FF (Finish-to-Finish): Task B finishes when Task A finishes
    - SF (Start-to-Finish): Task B finishes when Task A starts [rare]
    """
    FINISH_TO_START = "FS"  # Most common
    START_TO_START = "SS"
    FINISH_TO_FINISH = "FF"
    START_TO_FINISH = "SF"


class DependencyStatus(str, Enum):
    """Dependency status"""
    PENDING = "pending"  # Dependency active
    COMPLETED = "completed"  # Predecessor completed
    OVERRIDDEN = "overridden"  # Emergency override (Q7)


class DependencyBase(BaseModel):
    """Base model for task dependency"""
    task_id: UUID = Field(..., description="Dependent task (successor)")
    depends_on_task_id: UUID = Field(..., description="Predecessor task")
    dependency_type: DependencyType = Field(
        DependencyType.FINISH_TO_START,
        description="Type of dependency"
    )
    status: DependencyStatus = Field(
        DependencyStatus.PENDING,
        description="Dependency status"
    )


class DependencyCreate(DependencyBase):
    """Create dependency request"""
    pass


class Dependency(DependencyBase):
    """Dependency (from database)"""
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class EmergencyOverride(BaseModel):
    """Emergency override request (Q7: Hard Block with Emergency override)"""
    dependency_id: UUID
    reason: str = Field(..., min_length=10, description="Override reason (min 10 chars)")
    overridden_by: str = Field(..., description="User who authorized override")


class DependencyAudit(BaseModel):
    """Audit log for emergency overrides"""
    id: UUID = Field(default_factory=uuid4)
    dependency_id: UUID
    task_id: UUID
    depends_on_task_id: UUID
    reason: str
    overridden_by: str
    overridden_at: datetime = Field(default_factory=datetime.utcnow)


class CircularDependencyError(Exception):
    """Raised when circular dependency detected"""
    def __init__(self, cycle: List[UUID]):
        self.cycle = cycle
        cycle_str = " -> ".join(str(t) for t in cycle)
        super().__init__(f"Circular dependency detected: {cycle_str}")


class TopologicalSortResult(BaseModel):
    """Result of topological sort"""
    ordered_tasks: List[UUID] = Field(..., description="Tasks in dependency order")
    execution_time_ms: float = Field(..., description="Algorithm execution time (ms)")
    task_count: int = Field(..., description="Number of tasks sorted")
    dependency_count: int = Field(..., description="Number of dependencies processed")


class DependencyGraphNode(BaseModel):
    """
    Node in dependency graph (for D3.js visualization).

    Enhanced for Week 3 Day 1-2: Includes task metadata for rich visualization.
    """
    id: str
    task_id: UUID
    label: str  # Task title
    type: str = "task"  # task, milestone, etc.

    # Task metadata for D3.js visualization
    title: Optional[str] = None  # Full task title
    phase: Optional[str] = None  # ideation, design, mvp, implementation, testing
    status: str = "pending"  # pending, in_progress, blocked, completed, done_end
    priority: Optional[str] = None  # critical, high, medium, low
    completeness: int = Field(default=0, ge=0, le=100)  # Completion percentage (0-100)
    is_blocked: bool = False  # Whether task is blocked by dependencies


class DependencyGraphEdge(BaseModel):
    """Edge in dependency graph"""
    source: str
    target: str
    dependency_type: DependencyType
    status: DependencyStatus


class DependencyGraph(BaseModel):
    """Complete dependency graph (for D3.js force-directed layout)"""
    nodes: List[DependencyGraphNode]
    edges: List[DependencyGraphEdge]
    has_cycles: bool = False
    cycles: List[List[UUID]] = Field(default_factory=list)


class DAGStatistics(BaseModel):
    """DAG performance statistics"""
    total_tasks: int
    total_dependencies: int
    max_depth: int = Field(..., description="Longest dependency chain")
    avg_dependencies_per_task: float
    topological_sort_time_ms: float
    cycle_detection_time_ms: float
    meets_performance_target: bool = Field(..., description="<50ms for 1,000 tasks")
