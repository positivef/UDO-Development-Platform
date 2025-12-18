"""
Mock Project Service for when database is not available

Provides mock data for project-related operations when PostgreSQL is not running.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class MockProjectService:
    """Mock service for project context when database is unavailable"""

    def __init__(self):
        """Initialize with mock data"""
        self.mock_projects = [
            {
                "id": str(uuid4()),
                "name": "UDO-Development-Platform",
                "description": "Intelligent development automation platform with MDO system",
                "current_phase": "implementation",
                "is_active": True,
                "has_context": True,
                "is_archived": False,
                "last_active_at": datetime.now().isoformat(),
                "created_at": (datetime.now() - timedelta(days=7)).isoformat(),
                "archived": False,
                "tags": ["MDO", "Standard Level", "Development"],
                "framework": "FastAPI + Next.js"
            },
            {
                "id": str(uuid4()),
                "name": "E-Commerce-Platform",
                "description": "Sample e-commerce platform project",
                "current_phase": "testing",
                "is_active": False,
                "has_context": False,
                "is_archived": False,
                "last_active_at": (datetime.now() - timedelta(days=2)).isoformat(),
                "created_at": (datetime.now() - timedelta(days=14)).isoformat(),
                "archived": False,
                "tags": ["Web", "E-Commerce", "React"],
                "framework": "React + Node.js"
            },
            {
                "id": str(uuid4()),
                "name": "Mobile-Banking-App",
                "description": "Secure mobile banking application",
                "current_phase": "design",
                "is_active": False,
                "has_context": False,
                "is_archived": False,
                "last_active_at": (datetime.now() - timedelta(days=5)).isoformat(),
                "created_at": (datetime.now() - timedelta(days=30)).isoformat(),
                "archived": False,
                "tags": ["Mobile", "Finance", "Security"],
                "framework": "React Native"
            }
        ]

        # Current active project (first one)
        self.current_project = self.mock_projects[0]

        logger.info("[OK] MockProjectService initialized with sample data (with current_phase)")

    async def list_projects(
        self,
        include_archived: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Return mock list of projects"""

        # Filter projects
        filtered_projects = [
            p for p in self.mock_projects
            if include_archived or not p.get("archived", False)
        ]

        # Apply pagination
        paginated = filtered_projects[offset:offset + limit]

        return {
            "projects": paginated,
            "total": len(filtered_projects),  # Changed from total_count to match expected format
            "current_project_id": self.current_project.get("id") if self.current_project else None
        }

    async def get_current_project(self) -> Optional[Dict[str, Any]]:
        """Return the current active project"""
        return self.current_project

    async def save_context(
        self,
        project_id: UUID,
        udo_state: Optional[Dict] = None,
        ml_models: Optional[Dict] = None,
        recent_executions: Optional[List] = None,
        ai_preferences: Optional[Dict] = None,
        editor_state: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Mock save context - just returns success"""

        logger.info(f"[EMOJI] Mock: Saving context for project {project_id}")

        # Find project
        project = next((p for p in self.mock_projects if p["id"] == str(project_id)), None)

        if not project:
            # Create new project
            project = {
                "id": str(project_id),
                "name": f"Project-{str(project_id)[:8]}",
                "description": "Auto-created project",
                "is_active": True,
                "has_context": True,
                "last_active_at": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat(),
                "archived": False,
                "tags": [],
                "framework": "Unknown"
            }
            self.mock_projects.append(project)

        # Update project
        project["has_context"] = True
        project["last_active_at"] = datetime.now().isoformat()

        # Return format matching ProjectContextResponse model
        return {
            "id": str(project_id),  # Required by ProjectContextResponse
            "project_id": str(project_id),
            "udo_state": udo_state or {},
            "ml_models": ml_models or {},
            "recent_executions": recent_executions[:10] if recent_executions else [],  # FIFO limit
            "ai_preferences": ai_preferences or {},
            "editor_state": editor_state or {},
            "saved_at": datetime.now().isoformat(),
            "loaded_at": None
        }

    async def load_context(self, project_id: UUID) -> Optional[Dict[str, Any]]:
        """Mock load context - returns mock data"""

        logger.info(f"[EMOJI] Mock: Loading context for project {project_id}")

        # Find project
        project = next((p for p in self.mock_projects if p["id"] == str(project_id)), None)

        if not project:
            return None

        # Return format matching ProjectContextResponse model
        return {
            "id": str(project_id),
            "project_id": str(project_id),
            "udo_state": {
                "current_phase": "development",
                "confidence_level": 0.75,
                "quantum_state": "Deterministic",
                "decision": "GO"
            },
            "ml_models": {
                "active_models": ["random_forest", "neural_network"],
                "accuracy": 0.85
            },
            "recent_executions": [],
            "ai_preferences": {
                "preferred_model": "claude",
                "temperature": 0.7
            },
            "editor_state": {
                "open_files": [],
                "cursor_positions": {}
            },
            "saved_at": datetime.now().isoformat(),
            "loaded_at": datetime.now().isoformat()
        }

    async def delete_context(self, project_id: UUID) -> bool:
        """Mock delete context"""

        logger.info(f"[EMOJI] Mock: Deleting context for project {project_id}")

        # Find project
        project = next((p for p in self.mock_projects if p["id"] == str(project_id)), None)

        if project:
            project["has_context"] = False
            return True

        return False

    async def switch_project(
        self,
        target_project_id: UUID,
        auto_save_current: bool = True
    ) -> Dict[str, Any]:
        """Mock project switch"""

        logger.error(f"[EMOJI] ENTERING MODIFIED switch_project METHOD [EMOJI] target={target_project_id}")
        logger.info(f"[EMOJI] Mock: Switching to project {target_project_id}")

        # Find target project
        target_project = next(
            (p for p in self.mock_projects if p["id"] == str(target_project_id)),
            None
        )

        if not target_project:
            raise ValueError(f"Project {target_project_id} not found")

        # Update current project
        if self.current_project:
            self.current_project["is_active"] = False

        # Set new current project
        target_project["is_active"] = True
        self.current_project = target_project

        # Mock context loading
        context = await self.load_context(target_project_id)

        result = {
            "previous_project_id": self.current_project.get("id") if self.current_project else None,
            "new_project_id": str(target_project_id),
            "context_loaded": context is not None,
            "context": context,
            "message": f"Switched to project {target_project.get('name', 'Unknown')}"
        }

        logger.info(f"[DEBUG] MockProjectService.switch_project returning: {list(result.keys())}")

        return result

    async def update_execution_history(
        self,
        project_id: UUID,
        execution: Dict[str, Any],
        max_history: int = 10
    ) -> None:
        """Mock update execution history"""
        logger.info(f"[EMOJI] Mock: Updating execution history for project {project_id}")
        # In mock mode, just log the update
        return

    async def merge_context(
        self,
        project_id: UUID,
        partial_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock merge context update with existing context"""
        logger.info(f"[EMOJI] Mock: Merging context for project {project_id}")

        # Return merged context (mock)
        return {
            "project_id": str(project_id),
            "udo_state": partial_context.get("udo_state", {}),
            "ml_models": partial_context.get("ml_models", {}),
            "recent_executions": partial_context.get("recent_executions", []),
            "ai_preferences": partial_context.get("ai_preferences", {}),
            "editor_state": partial_context.get("editor_state", {}),
            "saved_at": datetime.now().isoformat(),
            "loaded_at": None
        }

    async def initialize_default_project(self) -> Optional[UUID]:
        """Mock initialize default project"""
        logger.info("[OK] Mock: Initializing default project")

        # Return the first project's ID as UUID
        if self.mock_projects:
            return UUID(self.mock_projects[0]["id"])
        return None