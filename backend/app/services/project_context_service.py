"""
Project Context Service

Service layer for managing project contexts and seamless project switching.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
from pathlib import Path
import asyncpg

logger = logging.getLogger(__name__)


class ProjectContextService:
    """
    Service for managing project contexts and state.

    Features:
    - Save/load project context (UDO state, ML models, editor state)
    - Seamless project switching
    - Context auto-loading on project activation
    """

    def __init__(self, db_pool: asyncpg.Pool):
        """Initialize service with database connection pool"""
        self.db_pool = db_pool
        self.current_project_id: Optional[UUID] = None

    # ============================================================
    # Core Context Operations
    # ============================================================

    async def save_context(
        self,
        project_id: UUID,
        udo_state: Optional[Dict[str, Any]] = None,
        ml_models: Optional[Dict[str, Any]] = None,
        recent_executions: Optional[List[Dict[str, Any]]] = None,
        ai_preferences: Optional[Dict[str, Any]] = None,
        editor_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save project context to database.

        Uses UPSERT (INSERT ... ON CONFLICT) to create or update context.
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Prepare data with defaults
                context_data = {
                    "project_id": project_id,
                    "udo_state": udo_state or {},
                    "ml_models": ml_models or {},
                    "recent_executions": recent_executions or [],
                    "ai_preferences": ai_preferences or {},
                    "editor_state": editor_state or {}
                }

                # UPSERT query
                query = """
                INSERT INTO project_contexts (
                    project_id, udo_state, ml_models, recent_executions,
                    ai_preferences, editor_state, saved_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                ON CONFLICT (project_id)
                DO UPDATE SET
                    udo_state = EXCLUDED.udo_state,
                    ml_models = EXCLUDED.ml_models,
                    recent_executions = EXCLUDED.recent_executions,
                    ai_preferences = EXCLUDED.ai_preferences,
                    editor_state = EXCLUDED.editor_state,
                    saved_at = NOW()
                RETURNING id, project_id, udo_state, ml_models, recent_executions,
                          ai_preferences, editor_state, saved_at, loaded_at
                """

                result = await conn.fetchrow(
                    query,
                    context_data["project_id"],
                    context_data["udo_state"],
                    context_data["ml_models"],
                    context_data["recent_executions"],
                    context_data["ai_preferences"],
                    context_data["editor_state"]
                )

                logger.info(f"✅ Saved context for project {project_id}")
                return dict(result)

        except asyncpg.ForeignKeyViolationError:
            logger.error(f"❌ Project {project_id} does not exist")
            raise ValueError(f"Project with ID {project_id} not found")
        except Exception as e:
            logger.error(f"❌ Failed to save context: {e}")
            raise

    async def load_context(self, project_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Load project context from database.

        Updates loaded_at timestamp when context is loaded.
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Load context and update loaded_at
                query = """
                UPDATE project_contexts
                SET loaded_at = NOW()
                WHERE project_id = $1
                RETURNING id, project_id, udo_state, ml_models, recent_executions,
                          ai_preferences, editor_state, saved_at, loaded_at
                """

                result = await conn.fetchrow(query, project_id)

                if result:
                    logger.info(f"✅ Loaded context for project {project_id}")
                    return dict(result)
                else:
                    logger.warning(f"⚠️ No context found for project {project_id}")
                    return None

        except Exception as e:
            logger.error(f"❌ Failed to load context: {e}")
            raise

    async def delete_context(self, project_id: UUID) -> bool:
        """Delete project context (CASCADE delete when project is deleted)"""
        try:
            async with self.db_pool.acquire() as conn:
                query = "DELETE FROM project_contexts WHERE project_id = $1"
                result = await conn.execute(query, project_id)

                deleted = result.split()[-1] == "1"
                if deleted:
                    logger.info(f"✅ Deleted context for project {project_id}")
                return deleted

        except Exception as e:
            logger.error(f"❌ Failed to delete context: {e}")
            raise

    # ============================================================
    # Project Switching
    # ============================================================

    async def switch_project(
        self,
        target_project_id: UUID,
        auto_save_current: bool = True
    ) -> Dict[str, Any]:
        """
        Switch to a different project with context auto-loading.

        Workflow:
        1. Save current project context (if auto_save_current=True)
        2. Load target project context
        3. Update current_project_id
        4. Return loaded context
        """
        try:
            async with self.db_pool.acquire() as conn:
                # 1. Verify target project exists
                project_query = "SELECT id, name FROM projects WHERE id = $1"
                project = await conn.fetchrow(project_query, target_project_id)

                if not project:
                    raise ValueError(f"Project {target_project_id} not found")

                previous_project_id = self.current_project_id

                # 2. Auto-save current project if requested
                if auto_save_current and previous_project_id:
                    try:
                        # Note: This would need current context data passed in
                        # For now, we just log the intention
                        logger.info(f"📝 Auto-save requested for project {previous_project_id}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to auto-save current context: {e}")

                # 3. Load target project context
                context = await self.load_context(target_project_id)

                # 4. Update current project
                self.current_project_id = target_project_id

                return {
                    "previous_project_id": previous_project_id,
                    "new_project_id": target_project_id,
                    "project_name": project["name"],
                    "context_loaded": context is not None,
                    "context": context,
                    "message": f"Successfully switched to project '{project['name']}'"
                }

        except ValueError as e:
            logger.error(f"❌ Invalid project: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to switch project: {e}")
            raise

    # ============================================================
    # Project Listing
    # ============================================================

    async def list_projects(
        self,
        include_archived: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List all projects with context availability status.

        Returns projects sorted by last_active_at (most recent first).
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Build query with optional archived filter
                where_clause = "" if include_archived else "WHERE p.is_archived = FALSE"

                query = f"""
                SELECT
                    p.id,
                    p.name,
                    p.description,
                    p.current_phase,
                    p.last_active_at,
                    p.is_archived,
                    (pc.id IS NOT NULL) as has_context,
                    pc.saved_at as context_saved_at
                FROM projects p
                LEFT JOIN project_contexts pc ON p.id = pc.project_id
                {where_clause}
                ORDER BY p.last_active_at DESC
                LIMIT $1 OFFSET $2
                """

                count_query = f"""
                SELECT COUNT(*) FROM projects p
                {where_clause}
                """

                projects = await conn.fetch(query, limit, offset)
                total = await conn.fetchval(count_query)

                return {
                    "projects": [dict(p) for p in projects],
                    "total": total,
                    "current_project_id": self.current_project_id
                }

        except Exception as e:
            logger.error(f"❌ Failed to list projects: {e}")
            raise

    async def get_current_project(self) -> Optional[Dict[str, Any]]:
        """Get currently active project with context"""
        if not self.current_project_id:
            return None

        try:
            async with self.db_pool.acquire() as conn:
                query = """
                SELECT
                    p.*,
                    (pc.id IS NOT NULL) as has_context
                FROM projects p
                LEFT JOIN project_contexts pc ON p.id = pc.project_id
                WHERE p.id = $1
                """

                project = await conn.fetchrow(query, self.current_project_id)
                return dict(project) if project else None

        except Exception as e:
            logger.error(f"❌ Failed to get current project: {e}")
            raise

    # ============================================================
    # Utility Methods
    # ============================================================

    async def update_execution_history(
        self,
        project_id: UUID,
        execution: Dict[str, Any],
        max_history: int = 10
    ) -> None:
        """
        Add execution to recent_executions (FIFO, max 10).

        Automatically maintains only the most recent N executions.
        """
        try:
            context = await self.load_context(project_id)

            if context:
                recent = context.get("recent_executions", [])

                # Add new execution at the beginning
                recent.insert(0, execution)

                # Keep only the most recent max_history items
                recent = recent[:max_history]

                # Save updated context
                await self.save_context(
                    project_id=project_id,
                    udo_state=context.get("udo_state"),
                    ml_models=context.get("ml_models"),
                    recent_executions=recent,
                    ai_preferences=context.get("ai_preferences"),
                    editor_state=context.get("editor_state")
                )

                logger.info(f"✅ Updated execution history for project {project_id}")
            else:
                logger.warning(f"⚠️ No context to update for project {project_id}")

        except Exception as e:
            logger.error(f"❌ Failed to update execution history: {e}")
            raise

    async def merge_context(
        self,
        project_id: UUID,
        partial_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge partial context update with existing context.

        Only updates provided fields, keeps others unchanged.
        """
        try:
            # Load existing context
            existing = await self.load_context(project_id)

            if not existing:
                # No existing context, create new one
                return await self.save_context(
                    project_id=project_id,
                    udo_state=partial_context.get("udo_state"),
                    ml_models=partial_context.get("ml_models"),
                    recent_executions=partial_context.get("recent_executions"),
                    ai_preferences=partial_context.get("ai_preferences"),
                    editor_state=partial_context.get("editor_state")
                )

            # Merge with existing
            merged = {
                "udo_state": partial_context.get("udo_state", existing.get("udo_state")),
                "ml_models": partial_context.get("ml_models", existing.get("ml_models")),
                "recent_executions": partial_context.get("recent_executions", existing.get("recent_executions")),
                "ai_preferences": partial_context.get("ai_preferences", existing.get("ai_preferences")),
                "editor_state": partial_context.get("editor_state", existing.get("editor_state"))
            }

            return await self.save_context(project_id=project_id, **merged)

        except Exception as e:
            logger.error(f"❌ Failed to merge context: {e}")
            raise

    async def initialize_default_project(self) -> Optional[UUID]:
        """
        Initialize default project (UDO-Development-Platform) as current.

        Called on service startup to set initial project.
        """
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                SELECT id FROM projects
                WHERE name = 'UDO-Development-Platform'
                LIMIT 1
                """

                result = await conn.fetchval(query)

                if result:
                    self.current_project_id = result
                    logger.info(f"✅ Initialized default project: {result}")
                    return result
                else:
                    logger.warning("⚠️ Default project not found")
                    return None

        except Exception as e:
            logger.error(f"❌ Failed to initialize default project: {e}")
            return None


# ============================================================
# Singleton Instance
# ============================================================

# Global service instance (initialized in main.py with db_pool)
_project_context_service: Optional[ProjectContextService] = None
_use_mock_service: bool = False
_mock_service_instance: Optional[Any] = None


def get_project_context_service() -> Optional[Any]:
    """Get the global project context service instance (ProjectContextService or MockProjectService)"""
    global _mock_service_instance

    if _use_mock_service:
        # Return cached mock service instance
        if _mock_service_instance:
            logger.debug(f"Returning cached mock service instance: {type(_mock_service_instance)}")
            return _mock_service_instance
        # If not cached, create and cache it
        try:
            from app.services.mock_project_service import MockProjectService
            _mock_service_instance = MockProjectService()
            logger.info("✅ MockProjectService instance created and cached")
            return _mock_service_instance
        except ImportError as e:
            logger.error(f"Failed to import MockProjectService: {e}")
            return None
    logger.debug(f"Returning database service: {type(_project_context_service) if _project_context_service else 'None'}")
    return _project_context_service


def init_project_context_service(db_pool: asyncpg.Pool) -> ProjectContextService:
    """Initialize the global project context service"""
    global _project_context_service
    _project_context_service = ProjectContextService(db_pool)
    return _project_context_service


def enable_mock_service():
    """Enable mock service mode when database is unavailable"""
    global _use_mock_service, _mock_service_instance
    _use_mock_service = True

    # Create mock service instance immediately
    try:
        from app.services.mock_project_service import MockProjectService
        _mock_service_instance = MockProjectService()
        logger.info("✅ MockProjectService instance initialized")
    except Exception as e:
        logger.error(f"Failed to initialize MockProjectService: {e}")
        _mock_service_instance = None
