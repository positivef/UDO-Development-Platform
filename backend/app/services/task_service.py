"""
Task Management Service

[EMOJI] [EMOJI](Task) [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI].
[EMOJI] [EMOJI] TODO [EMOJI], [EMOJI] [EMOJI], [EMOJI] [EMOJI].
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
from enum import Enum
import uuid
import json
import logging

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """[EMOJI] [EMOJI]"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    TESTING = "testing"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class TodoStatus(Enum):
    """TODO [EMOJI] [EMOJI]"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class TaskService:
    """
    [EMOJI] [EMOJI] [EMOJI]

    [EMOJI] [EMOJI] [EMOJI] [EMOJI],
    [EMOJI] [EMOJI] [EMOJI] Mock [EMOJI] [EMOJI].
    """

    def __init__(self):
        """TaskService [EMOJI]"""
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.task_contexts: Dict[str, Dict[str, Any]] = {}

        # [EMOJI] [EMOJI] [EMOJI] [EMOJI]
        self._create_default_tasks()

    def _create_default_tasks(self):
        """[EMOJI] [EMOJI] [EMOJI] [EMOJI]"""

        # Task 1: JWT Authentication
        task1_id = "task-jwt-auth"
        self.tasks[task1_id] = {
            "id": task1_id,
            "title": "Implement JWT Authentication",
            "description": "JWT [EMOJI] [EMOJI] [EMOJI] [EMOJI]",
            "project": "UDO Platform",
            "project_id": "proj-udo-001",
            "phase": "development",
            "status": TaskStatus.IN_PROGRESS.value,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),

            # TODO [EMOJI]
            "todo_groups": [
                {
                    "id": "group-1",
                    "title": "1. Planning",
                    "status": "completed",
                    "order": 1,
                    "items": [
                        {
                            "id": "todo-1-1",
                            "title": "Review requirements",
                            "status": "completed",
                            "completed_at": "2025-11-18T10:00:00Z"
                        },
                        {
                            "id": "todo-1-2",
                            "title": "Design database schema",
                            "status": "completed",
                            "completed_at": "2025-11-18T11:00:00Z"
                        },
                        {
                            "id": "todo-1-3",
                            "title": "API endpoint design",
                            "status": "completed",
                            "completed_at": "2025-11-18T12:00:00Z"
                        }
                    ]
                },
                {
                    "id": "group-2",
                    "title": "2. Implementation",
                    "status": "in_progress",
                    "order": 2,
                    "items": [
                        {
                            "id": "todo-2-1",
                            "title": "User model",
                            "status": "completed",
                            "completed_at": "2025-11-19T09:00:00Z",
                            "files": ["backend/app/models/user.py"]
                        },
                        {
                            "id": "todo-2-2",
                            "title": "JWT middleware",
                            "status": "in_progress",
                            "current": True,
                            "started_at": "2025-11-19T10:00:00Z",
                            "subtasks": [
                                "Install jsonwebtoken package",
                                "Create JWT config",
                                "Implement token generation",
                                "Implement token verification",
                                "Add to Express middleware chain"
                            ],
                            "files": [
                                "backend/app/middleware/auth.py",
                                "backend/app/core/security.py"
                            ]
                        },
                        {
                            "id": "todo-2-3",
                            "title": "Login endpoint",
                            "status": "pending"
                        },
                        {
                            "id": "todo-2-4",
                            "title": "Register endpoint",
                            "status": "pending"
                        }
                    ]
                },
                {
                    "id": "group-3",
                    "title": "3. Testing",
                    "status": "pending",
                    "order": 3,
                    "items": [
                        {
                            "id": "todo-3-1",
                            "title": "Unit tests",
                            "status": "pending",
                            "acceptance_criteria": [
                                "Test token generation",
                                "Test token verification",
                                "Test expired token handling",
                                "Test invalid token handling"
                            ]
                        },
                        {
                            "id": "todo-3-2",
                            "title": "Integration tests",
                            "status": "pending",
                            "acceptance_criteria": [
                                "Test protected routes",
                                "Test authentication flow",
                                "Test token refresh"
                            ]
                        }
                    ]
                }
            ],

            # [EMOJI] [EMOJI] [EMOJI]
            "current_step": {
                "group_index": 1,
                "item_index": 1,
                "description": "JWT middleware implementation"
            },

            # [EMOJI] [EMOJI]
            "completeness": 45,

            # [EMOJI] [EMOJI]
            "estimated_hours": 8,
            "actual_hours": 3.5,

            # Git [EMOJI]
            "git_branch": "feature/jwt-auth",
            "last_commit": "feat: Add user model and schema"
        }

        # Task 1[EMOJI] [EMOJI]
        self.task_contexts[task1_id] = {
            "task_id": task1_id,
            "files": [
                "backend/app/middleware/auth.py",
                "backend/app/core/security.py",
                "backend/app/models/user.py",
                "tests/middleware/test_auth.py"
            ],
            "git_branch": "feature/jwt-auth",
            "prompt_history": [
                "Create user model with SQLAlchemy",
                "Implement JWT token generation function",
                "Add password hashing with bcrypt"
            ],
            "checkpoint": {
                "step": "Implementing JWT middleware",
                "next_action": "Create token verification function",
                "blockers": None
            },
            "environment": {
                "python_version": "3.11",
                "dependencies": ["fastapi", "pyjwt", "passlib", "sqlalchemy"]
            }
        }

        # Task 2: Task Management UI
        task2_id = "task-ui-management"
        self.tasks[task2_id] = {
            "id": task2_id,
            "title": "Add Task Management UI",
            "description": "[EMOJI] [EMOJI] UI [EMOJI] [EMOJI]",
            "project": "UDO Platform",
            "project_id": "proj-udo-001",
            "phase": "planning",
            "status": TaskStatus.PENDING.value,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),

            "todo_groups": [
                {
                    "id": "group-1",
                    "title": "1. Design",
                    "status": "in_progress",
                    "order": 1,
                    "items": [
                        {
                            "id": "todo-1-1",
                            "title": "Component architecture",
                            "status": "completed"
                        },
                        {
                            "id": "todo-1-2",
                            "title": "UI mockups",
                            "status": "in_progress",
                            "current": True
                        },
                        {
                            "id": "todo-1-3",
                            "title": "API design",
                            "status": "pending"
                        }
                    ]
                }
            ],

            "current_step": {
                "group_index": 0,
                "item_index": 1,
                "description": "Creating UI mockups"
            },

            "completeness": 20,
            "estimated_hours": 12,
            "actual_hours": 1,
            "git_branch": "feature/task-ui",
            "last_commit": None
        }

        # Task 3: Real-time WebSocket
        task3_id = "task-websocket"
        self.tasks[task3_id] = {
            "id": task3_id,
            "title": "Implement WebSocket Real-time Updates",
            "description": "WebSocket[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]",
            "project": "UDO Platform",
            "project_id": "proj-udo-001",
            "phase": "development",
            "status": TaskStatus.BLOCKED.value,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),

            "todo_groups": [
                {
                    "id": "group-1",
                    "title": "1. Setup",
                    "status": "completed",
                    "order": 1,
                    "items": [
                        {
                            "id": "todo-1-1",
                            "title": "Install WebSocket dependencies",
                            "status": "completed"
                        },
                        {
                            "id": "todo-1-2",
                            "title": "Configure WebSocket server",
                            "status": "completed"
                        }
                    ]
                },
                {
                    "id": "group-2",
                    "title": "2. Implementation",
                    "status": "blocked",
                    "order": 2,
                    "items": [
                        {
                            "id": "todo-2-1",
                            "title": "Event handlers",
                            "status": "blocked",
                            "blockers": ["Redis not configured", "Need session management"]
                        }
                    ]
                }
            ],

            "current_step": {
                "group_index": 1,
                "item_index": 0,
                "description": "Blocked on Redis configuration"
            },

            "completeness": 30,
            "estimated_hours": 6,
            "actual_hours": 2,
            "git_branch": "feature/websocket",
            "last_commit": "chore: Add WebSocket dependencies"
        }

        logger.info(f"Created {len(self.tasks)} default tasks")

    async def list_tasks(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        phase: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        [EMOJI] [EMOJI] [EMOJI]

        Args:
            project_id: [EMOJI] ID ([EMOJI])
            status: [EMOJI] [EMOJI] ([EMOJI])
            phase: [EMOJI] [EMOJI] ([EMOJI])

        Returns:
            [EMOJI] [EMOJI]
        """
        tasks = list(self.tasks.values())

        # [EMOJI]
        if project_id:
            tasks = [t for t in tasks if t.get("project_id") == project_id]

        if status:
            tasks = [t for t in tasks if t.get("status") == status]

        if phase:
            tasks = [t for t in tasks if t.get("phase") == phase]

        # [EMOJI] ([EMOJI] [EMOJI] [EMOJI])
        tasks.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        return tasks

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        [EMOJI] [EMOJI] [EMOJI]

        Args:
            task_id: [EMOJI] ID

        Returns:
            [EMOJI] [EMOJI] [EMOJI] None
        """
        return self.tasks.get(task_id)

    async def get_task_context(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        [EMOJI] [EMOJI] [EMOJI]

        CLI[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI].

        Args:
            task_id: [EMOJI] ID

        Returns:
            [EMOJI] [EMOJI] [EMOJI] None
        """
        task = self.tasks.get(task_id)
        if not task:
            return None

        context = self.task_contexts.get(task_id, {})

        # [EMOJI] TODO [EMOJI]
        current_todo = None
        for group in task.get("todo_groups", []):
            for item in group.get("items", []):
                if item.get("current"):
                    current_todo = {
                        "group": group["title"],
                        "item": item["title"],
                        "subtasks": item.get("subtasks", []),
                        "files": item.get("files", [])
                    }
                    break
            if current_todo:
                break

        return {
            "task_id": task_id,
            "title": task["title"],
            "description": task["description"],
            "project": task["project"],
            "phase": task["phase"],
            "status": task["status"],
            "current_todo": current_todo,
            "git_branch": context.get("git_branch"),
            "files": context.get("files", []),
            "prompt_history": context.get("prompt_history", []),
            "checkpoint": context.get("checkpoint"),
            "command": self._generate_cli_command(task_id),
            "updated_at": task["updated_at"]
        }

    def _generate_cli_command(self, task_id: str) -> str:
        """
        CLI [EMOJI] [EMOJI]

        Args:
            task_id: [EMOJI] ID

        Returns:
            CLI [EMOJI]
        """
        # Deep Link [EMOJI] (Windows)
        # [EMOJI] [EMOJI] [EMOJI] [EMOJI], [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]
        return f"claude-code://continue?task={task_id}"

    async def update_task_progress(
        self,
        task_id: str,
        progress: Dict[str, Any]
    ) -> bool:
        """
        [EMOJI] [EMOJI] [EMOJI] [EMOJI]

        Args:
            task_id: [EMOJI] ID
            progress: [EMOJI] [EMOJI] [EMOJI]

        Returns:
            [EMOJI] [EMOJI]
        """
        task = self.tasks.get(task_id)
        if not task:
            return False

        # [EMOJI] [EMOJI] [EMOJI]
        if "status" in progress:
            task["status"] = progress["status"]

        if "current_step" in progress:
            task["current_step"] = progress["current_step"]

        if "completeness" in progress:
            task["completeness"] = progress["completeness"]

        if "actual_hours" in progress:
            task["actual_hours"] = progress["actual_hours"]

        # TODO [EMOJI] [EMOJI]
        if "todo_update" in progress:
            todo_id = progress["todo_update"]["id"]
            new_status = progress["todo_update"]["status"]

            for group in task.get("todo_groups", []):
                for item in group.get("items", []):
                    if item["id"] == todo_id:
                        item["status"] = new_status
                        if new_status == "completed":
                            item["completed_at"] = datetime.now(UTC).isoformat()
                            item["current"] = False
                        elif new_status == "in_progress":
                            item["started_at"] = datetime.now(UTC).isoformat()
                            item["current"] = True
                        break

        task["updated_at"] = datetime.now(UTC).isoformat()

        logger.info(f"Updated task progress: {task_id}")
        return True

    async def create_task(self, task_data: Dict[str, Any]) -> str:
        """
        [EMOJI] [EMOJI] [EMOJI]

        Args:
            task_data: [EMOJI] [EMOJI]

        Returns:
            [EMOJI] [EMOJI] ID
        """
        task_id = f"task-{uuid.uuid4().hex[:8]}"

        task = {
            "id": task_id,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "status": TaskStatus.PENDING.value,
            "completeness": 0,
            "actual_hours": 0,
            **task_data
        }

        self.tasks[task_id] = task
        self.task_contexts[task_id] = {
            "task_id": task_id,
            "files": [],
            "prompt_history": [],
            "checkpoint": None
        }

        logger.info(f"Created new task: {task_id}")
        return task_id

    async def save_task_context(
        self,
        task_id: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        [EMOJI] [EMOJI] [EMOJI]

        Args:
            task_id: [EMOJI] ID
            context: [EMOJI] [EMOJI]

        Returns:
            [EMOJI] [EMOJI]
        """
        if task_id not in self.tasks:
            return False

        self.task_contexts[task_id] = {
            **self.task_contexts.get(task_id, {}),
            **context,
            "updated_at": datetime.now(UTC).isoformat()
        }

        logger.info(f"Saved task context: {task_id}")
        return True

    async def calculate_completeness(self, task_id: str) -> int:
        """
        [EMOJI] [EMOJI] [EMOJI]

        Args:
            task_id: [EMOJI] ID

        Returns:
            [EMOJI] (0-100)
        """
        task = self.tasks.get(task_id)
        if not task:
            return 0

        total_items = 0
        completed_items = 0

        for group in task.get("todo_groups", []):
            for item in group.get("items", []):
                total_items += 1
                if item.get("status") == "completed":
                    completed_items += 1

        if total_items == 0:
            return 0

        return int((completed_items / total_items) * 100)

    def get_active_task_count(self) -> int:
        """[EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
        return sum(
            1 for task in self.tasks.values()
            if task.get("status") in [
                TaskStatus.IN_PROGRESS.value,
                TaskStatus.REVIEW.value,
                TaskStatus.TESTING.value
            ]
        )

    def get_blocked_task_count(self) -> int:
        """[EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
        return sum(
            1 for task in self.tasks.values()
            if task.get("status") == TaskStatus.BLOCKED.value
        )


# Create singleton instance
task_service = TaskService()

# Export
__all__ = ['TaskService', 'task_service', 'TaskStatus', 'TodoStatus']