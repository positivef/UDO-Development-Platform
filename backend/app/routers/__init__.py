"""
API Routers - HIGH-09 FIX: Centralized Router Registry

This module provides a unified router registration system to reduce main.py clutter.
All routers are registered through a single function call with proper error handling.
"""

import logging
from typing import List, Tuple, Optional, Any
from fastapi import FastAPI, APIRouter

logger = logging.getLogger(__name__)

# ============================================================================
# Core Routers (Always Available)
# ============================================================================

from .ck_theory import router as ck_theory_router
from .constitutional import router as constitutional_router
from .gi_formula import router as gi_formula_router
from .governance import router as governance_router
from .quality_metrics import router as quality_metrics_router
from .time_tracking import router as time_tracking_router
from .uncertainty import router as uncertainty_router
from .version_history import router as version_history_router

# ============================================================================
# Optional Routers (Loaded with error handling)
# ============================================================================

# Project Context Routers
try:
    from .project_context import projects_router
    from .project_context import router as project_context_router

    project_context_available = True
except ImportError as e:
    logger.warning(f"Project context routers not available: {e}")
    project_context_available = False
    projects_router = None
    project_context_router = None

# WebSocket Handler
try:
    from . import websocket_handler

    websocket_available = True
except ImportError as e:
    logger.warning(f"WebSocket handler not available: {e}")
    websocket_available = False
    websocket_handler = None

# Auth Router
try:
    from .auth import router as auth_router

    auth_available = True
except ImportError as e:
    logger.warning(f"Auth router not available: {e}")
    auth_available = False
    auth_router = None

# Modules Router
try:
    from .modules import router as modules_router

    modules_available = True
except ImportError as e:
    logger.warning(f"Modules router not available: {e}")
    modules_available = False
    modules_router = None

# Tasks Router
try:
    from .tasks import router as tasks_router

    tasks_available = True
except ImportError as e:
    logger.warning(f"Tasks router not available: {e}")
    tasks_available = False
    tasks_router = None

# Obsidian Router
try:
    from .obsidian import router as obsidian_router

    obsidian_available = True
except ImportError as e:
    logger.warning(f"Obsidian router not available: {e}")
    obsidian_available = False
    obsidian_router = None

# Kanban Routers
try:
    from .kanban_tasks import router as kanban_tasks_router

    kanban_tasks_available = True
except ImportError as e:
    logger.warning(f"Kanban tasks router not available: {e}")
    kanban_tasks_available = False
    kanban_tasks_router = None

try:
    from .kanban_dependencies import router as kanban_dependencies_router

    kanban_dependencies_available = True
except ImportError as e:
    logger.warning(f"Kanban dependencies router not available: {e}")
    kanban_dependencies_available = False
    kanban_dependencies_router = None

try:
    from .kanban_projects import router as kanban_projects_router

    kanban_projects_available = True
except ImportError as e:
    logger.warning(f"Kanban projects router not available: {e}")
    kanban_projects_available = False
    kanban_projects_router = None

try:
    from .kanban_context import router as kanban_context_router

    kanban_context_available = True
except ImportError as e:
    logger.warning(f"Kanban context router not available: {e}")
    kanban_context_available = False
    kanban_context_router = None

try:
    from .kanban_ai import router as kanban_ai_router

    kanban_ai_available = True
except ImportError as e:
    logger.warning(f"Kanban AI router not available: {e}")
    kanban_ai_available = False
    kanban_ai_router = None

try:
    from .kanban_archive import router as kanban_archive_router

    kanban_archive_available = True
except ImportError as e:
    logger.warning(f"Kanban archive router not available: {e}")
    kanban_archive_available = False
    kanban_archive_router = None

try:
    from .kanban_websocket import router as kanban_websocket_router

    kanban_websocket_available = True
except ImportError as e:
    logger.warning(f"Kanban websocket router not available: {e}")
    kanban_websocket_available = False
    kanban_websocket_router = None

# Test WebSocket Router
try:
    from .test_websocket import router as test_websocket_router

    test_websocket_available = True
except ImportError as e:
    logger.debug(f"Test websocket router not available: {e}")
    test_websocket_available = False
    test_websocket_router = None

# Admin Router
try:
    from .admin import router as admin_router

    admin_available = True
except ImportError as e:
    logger.warning(f"Admin router not available: {e}")
    admin_available = False
    admin_router = None

# Knowledge Routers
try:
    from .knowledge_feedback import router as knowledge_feedback_router

    knowledge_feedback_available = True
except ImportError as e:
    logger.warning(f"Knowledge feedback router not available: {e}")
    knowledge_feedback_available = False
    knowledge_feedback_router = None

try:
    from .knowledge_search import router as knowledge_search_router

    knowledge_search_available = True
except ImportError as e:
    logger.warning(f"Knowledge search router not available: {e}")
    knowledge_search_available = False
    knowledge_search_router = None


# ============================================================================
# Router Registry
# ============================================================================


def get_all_routers() -> List[Tuple[Optional[APIRouter], str, bool]]:
    """
    Get all available routers with their names and availability status.

    Returns:
        List of tuples: (router, name, is_available)
    """
    return [
        # Core routers (always available)
        (version_history_router, "version_history", True),
        (quality_metrics_router, "quality_metrics", True),
        (constitutional_router, "constitutional", True),
        (time_tracking_router, "time_tracking", True),
        (gi_formula_router, "gi_formula", True),
        (ck_theory_router, "ck_theory", True),
        (uncertainty_router, "uncertainty", True),
        (governance_router, "governance", True),
        # Optional routers
        (project_context_router, "project_context", project_context_available),
        (projects_router, "projects", project_context_available),
        (auth_router, "auth", auth_available),
        (modules_router, "modules", modules_available),
        (tasks_router, "tasks", tasks_available),
        (obsidian_router, "obsidian", obsidian_available),
        (kanban_tasks_router, "kanban_tasks", kanban_tasks_available),
        (kanban_dependencies_router, "kanban_dependencies", kanban_dependencies_available),
        (kanban_projects_router, "kanban_projects", kanban_projects_available),
        (kanban_context_router, "kanban_context", kanban_context_available),
        (kanban_ai_router, "kanban_ai", kanban_ai_available),
        (kanban_archive_router, "kanban_archive", kanban_archive_available),
        (kanban_websocket_router, "kanban_websocket", kanban_websocket_available),
        (test_websocket_router, "test_websocket", test_websocket_available),
        (admin_router, "admin", admin_available),
        (knowledge_feedback_router, "knowledge_feedback", knowledge_feedback_available),
        (knowledge_search_router, "knowledge_search", knowledge_search_available),
    ]


def register_all_routers(app: FastAPI) -> dict:
    """
    HIGH-09 FIX: Centralized router registration.

    Register all available routers to the FastAPI application.
    This replaces scattered include_router calls in main.py.

    Args:
        app: FastAPI application instance

    Returns:
        dict with registration statistics
    """
    stats = {"registered": 0, "skipped": 0, "errors": 0, "routers": []}

    for router, name, is_available in get_all_routers():
        if not is_available or router is None:
            stats["skipped"] += 1
            logger.debug(f"Skipping unavailable router: {name}")
            continue

        try:
            app.include_router(router)
            stats["registered"] += 1
            stats["routers"].append(name)
            logger.debug(f"Registered router: {name}")
        except Exception as e:
            stats["errors"] += 1
            logger.error(f"Failed to register router {name}: {e}")

    # Register WebSocket handler separately (different API)
    if websocket_available and websocket_handler is not None:
        try:
            app.include_router(websocket_handler.router)
            stats["registered"] += 1
            stats["routers"].append("websocket_handler")
            logger.debug("Registered websocket_handler router")
        except Exception as e:
            stats["errors"] += 1
            logger.error(f"Failed to register websocket_handler: {e}")

    logger.info(
        f"Router registration complete: {stats['registered']} registered, "
        f"{stats['skipped']} skipped, {stats['errors']} errors"
    )

    return stats


def get_connection_manager() -> Optional[Any]:
    """
    Get the WebSocket connection manager if available.

    Returns:
        ConnectionManager instance or None
    """
    if websocket_available and websocket_handler is not None:
        try:
            return websocket_handler.connection_manager
        except AttributeError:
            return None
    return None


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Core routers
    "version_history_router",
    "quality_metrics_router",
    "constitutional_router",
    "time_tracking_router",
    "gi_formula_router",
    "ck_theory_router",
    "uncertainty_router",
    "governance_router",
    # Optional routers (may be None)
    "project_context_router",
    "projects_router",
    "auth_router",
    "modules_router",
    "tasks_router",
    "obsidian_router",
    "kanban_tasks_router",
    "kanban_dependencies_router",
    "kanban_projects_router",
    "kanban_context_router",
    "kanban_ai_router",
    "kanban_archive_router",
    "kanban_websocket_router",
    "test_websocket_router",
    "admin_router",
    "knowledge_feedback_router",
    "knowledge_search_router",
    "websocket_handler",
    # Registry functions
    "register_all_routers",
    "get_all_routers",
    "get_connection_manager",
    # Availability flags
    "project_context_available",
    "websocket_available",
    "auth_available",
    "modules_available",
    "tasks_available",
    "obsidian_available",
    "kanban_tasks_available",
    "kanban_dependencies_available",
    "kanban_projects_available",
    "kanban_context_available",
    "kanban_ai_available",
    "kanban_archive_available",
    "kanban_websocket_available",
    "test_websocket_available",
    "admin_available",
    "knowledge_feedback_available",
    "knowledge_search_available",
]
