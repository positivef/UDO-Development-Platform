#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UDO Dashboard Backend API
FastAPI server for real-time system monitoring and control
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
import secrets
import asyncio
import logging

# Load environment variables from .env file
from dotenv import load_dotenv

# Load .env from project root (parent of backend directory)
project_root = Path(__file__).parent.parent
dotenv_path = project_root / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
# Add backend directory to path for app module imports
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import UDO components
try:
    from integrated_udo_system import IntegratedUDOSystem
    UDO_AVAILABLE = True
except ImportError:
    UDO_AVAILABLE = False
    logger.warning("UDO system not available")

# ============================================================
# NOTE: Mock service will be enabled in startup_event if database fails
# Do NOT enable it unconditionally here, let database connection try first
# ============================================================
logger.info("[EMOJI] Mock service will be enabled ONLY if database connection fails")

# Import routers
try:
    from app.routers import (
        version_history_router,
        quality_metrics_router,
        constitutional_router,
        time_tracking_router,
        gi_formula_router,
        ck_theory_router,
        uncertainty_router
    )
    ROUTERS_AVAILABLE = True
    CONSTITUTIONAL_ROUTER_AVAILABLE = True
    TIME_TRACKING_ROUTER_AVAILABLE = True
    GI_FORMULA_ROUTER_AVAILABLE = True
    CK_THEORY_ROUTER_AVAILABLE = True
    UNCERTAINTY_ROUTER_AVAILABLE = True
    print(f"[DEBUG] uncertainty_router imported successfully, UNCERTAINTY_ROUTER_AVAILABLE = {UNCERTAINTY_ROUTER_AVAILABLE}")
except ImportError as e:
    ROUTERS_AVAILABLE = False
    CONSTITUTIONAL_ROUTER_AVAILABLE = False
    TIME_TRACKING_ROUTER_AVAILABLE = False
    GI_FORMULA_ROUTER_AVAILABLE = False
    CK_THEORY_ROUTER_AVAILABLE = False
    UNCERTAINTY_ROUTER_AVAILABLE = False
    logger.warning(f"Routers not available: {e}")

# Import auth router separately
try:
    from app.routers.auth import router as auth_router
    AUTH_ROUTER_AVAILABLE = True
except ImportError as e:
    AUTH_ROUTER_AVAILABLE = False
    logger.warning(f"Auth router not available: {e}")

# Import project context routers separately (optional)
try:
    from app.routers import project_context_router, projects_router
    PROJECT_CONTEXT_AVAILABLE = True
except ImportError as e:
    PROJECT_CONTEXT_AVAILABLE = False
    logger.info(f"Project context routers not available (optional): {e}")

# Import modules router for Standard Level MDO
try:
    from app.routers.modules import router as modules_router
    MODULES_ROUTER_AVAILABLE = True
except ImportError as e:
    MODULES_ROUTER_AVAILABLE = False
    logger.info(f"Modules router not available (optional): {e}")

# Import tasks router for Task Management
try:
    from app.routers.tasks import router as tasks_router
    TASKS_ROUTER_AVAILABLE = True
except ImportError as e:
    TASKS_ROUTER_AVAILABLE = False
    logger.info(f"Tasks router not available: {e}")

# Import Obsidian router for Knowledge Management
try:
    from app.routers.obsidian import router as obsidian_router
    OBSIDIAN_ROUTER_AVAILABLE = True
except ImportError as e:
    OBSIDIAN_ROUTER_AVAILABLE = False
    logger.info(f"Obsidian router not available: {e}")

# Import Kanban Tasks router for Kanban-UDO Integration (Week 2 Day 3-4)
try:
    from app.routers.kanban_tasks import router as kanban_tasks_router
    KANBAN_TASKS_ROUTER_AVAILABLE = True
except ImportError as e:
    KANBAN_TASKS_ROUTER_AVAILABLE = False
    logger.info(f"Kanban Tasks router not available: {e}")

# Import Kanban Dependencies router for DAG management (Week 2 Day 3-4)
try:
    from app.routers.kanban_dependencies import router as kanban_dependencies_router
    KANBAN_DEPENDENCIES_ROUTER_AVAILABLE = True
except ImportError as e:
    KANBAN_DEPENDENCIES_ROUTER_AVAILABLE = False
    logger.info(f"Kanban Dependencies router not available: {e}")

# Import Kanban Projects router for Multi-Project management (Week 2 Day 3-4, Q5)
try:
    from app.routers.kanban_projects import router as kanban_projects_router
    KANBAN_PROJECTS_ROUTER_AVAILABLE = True
except ImportError as e:
    KANBAN_PROJECTS_ROUTER_AVAILABLE = False
    logger.info(f"Kanban Projects router not available: {e}")

# Import Kanban Context router for Context operations (Week 2 Day 5, Q4)
try:
    from app.routers.kanban_context import router as kanban_context_router
    KANBAN_CONTEXT_ROUTER_AVAILABLE = True
except ImportError as e:
    KANBAN_CONTEXT_ROUTER_AVAILABLE = False
    logger.info(f"Kanban Context router not available: {e}")

# Import Kanban AI router for AI Task Suggestions (Week 3 Day 3, Q2)
try:
    from app.routers.kanban_ai import router as kanban_ai_router
    KANBAN_AI_ROUTER_AVAILABLE = True
except ImportError as e:
    KANBAN_AI_ROUTER_AVAILABLE = False
    logger.info(f"Kanban AI router not available: {e}")

# Import Kanban Archive router for Done-End Archive (Week 3 Day 4-5, Q6)
try:
    from app.routers.kanban_archive import router as kanban_archive_router
    KANBAN_ARCHIVE_ROUTER_AVAILABLE = True
except ImportError as e:
    KANBAN_ARCHIVE_ROUTER_AVAILABLE = False
    logger.info(f"Kanban Archive router not available: {e}")

# Import Kanban WebSocket router for Real-time Updates (Week 7+)
try:
    from app.routers.kanban_websocket import router as kanban_websocket_router
    KANBAN_WEBSOCKET_ROUTER_AVAILABLE = True
except ImportError as e:
    KANBAN_WEBSOCKET_ROUTER_AVAILABLE = False
    logger.info(f"Kanban WebSocket router not available: {e}")

# Import Test WebSocket router for debugging (Week 7 Troubleshooting)
try:
    from app.routers.test_websocket import router as test_websocket_router
    TEST_WEBSOCKET_ROUTER_AVAILABLE = True
except ImportError as e:
    TEST_WEBSOCKET_ROUTER_AVAILABLE = False
    logger.info(f"Test WebSocket router not available: {e}")

# Import Admin router for Feature Flags (Week 4, Tier 1 Rollback)
try:
    from app.routers.admin import router as admin_router
    ADMIN_ROUTER_AVAILABLE = True
except ImportError as e:
    ADMIN_ROUTER_AVAILABLE = False
    logger.info(f"Admin router not available: {e}")

# Import Knowledge Feedback router for Accuracy Tracking (Week 6 Day 4-5)
try:
    from app.routers.knowledge_feedback import router as knowledge_feedback_router
    KNOWLEDGE_FEEDBACK_ROUTER_AVAILABLE = True
except ImportError as e:
    KNOWLEDGE_FEEDBACK_ROUTER_AVAILABLE = False
    logger.info(f"Knowledge Feedback router not available: {e}")

# Import Knowledge Search router for 3-Tier Search (Week 6 Day 4 PM)
try:
    from app.routers.knowledge_search import router as knowledge_search_router
    KNOWLEDGE_SEARCH_ROUTER_AVAILABLE = True
except ImportError as e:
    KNOWLEDGE_SEARCH_ROUTER_AVAILABLE = False
    logger.info(f"Knowledge Search router not available: {e}")

# Import WebSocket handler and SessionManagerV2
try:
    from app.routers import websocket_handler
    from app.routers.websocket_handler import connection_manager
    from app.services.session_manager_v2 import get_session_manager
    WEBSOCKET_AVAILABLE = True
except ImportError as e:
    WEBSOCKET_AVAILABLE = False
    logger.warning(f"WebSocket/SessionManager not available: {e}")

# Import Redis client
try:
    from app.services.redis_client import get_redis_client, cleanup_redis
    REDIS_AVAILABLE = True
except ImportError as e:
    REDIS_AVAILABLE = False
    logger.warning(f"Redis client not available: {e}")

# Import async database and project context service
try:
    from backend.async_database import async_db, initialize_async_database, close_async_database
    from app.services.project_context_service import init_project_context_service, enable_mock_service
    ASYNC_DB_AVAILABLE = True
except ImportError as e:
    ASYNC_DB_AVAILABLE = False
    logger.warning(f"Async database not available: {e}")

# Import error handler
try:
    from app.core.error_handler import setup_error_handlers, error_handler
    ERROR_HANDLER_AVAILABLE = True
except ImportError as e:
    ERROR_HANDLER_AVAILABLE = False
    logger.warning(f"Error handler not available: {e}")

# Import Phase Transition components
try:
    from app.services.phase_transition_listener import PhaseTransitionListener, create_listener_callback
    from phase_state_manager import PhaseStateManager
    from app.services.time_tracking_service import TimeTrackingService
    PHASE_TRANSITION_AVAILABLE = True
    logger.info(f"[DEBUG] Phase Transition components imported successfully, PHASE_TRANSITION_AVAILABLE = {PHASE_TRANSITION_AVAILABLE}")
except ImportError as e:
    PHASE_TRANSITION_AVAILABLE = False
    logger.warning(f"Phase Transition components not available: {e}")

# Import security components
try:
    from app.core.security import (
        setup_security,
        JWTManager,
        PasswordHasher,
        SecureUserCreate,
        SecureProjectCreate,
        security
    )
    SECURITY_AVAILABLE = True
except ImportError as e:
    SECURITY_AVAILABLE = False
    logger.warning(f"Security components not available: {e}")

# Import monitoring components
try:
    from app.core.monitoring import (
        setup_monitoring,
        performance_monitor,
        monitor_performance
    )
    MONITORING_AVAILABLE = True
except ImportError as e:
    MONITORING_AVAILABLE = False
    logger.warning(f"Monitoring components not available: {e}")

# FastAPI app - with updated MockProjectService
app = FastAPI(
    title="UDO Development Platform API",
    version="3.0.0",
    description="Real-time development automation and monitoring"
)

# ============================================================
# HIGH-03: Security Headers Middleware
# ============================================================
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses (OWASP recommendations)"""

    async def dispatch(self, request: Request, call_next):
        # Skip WebSocket connections (let them pass through)
        # Check both lowercase and capitalized header names
        upgrade_header = request.headers.get("upgrade") or request.headers.get("Upgrade")
        if upgrade_header and upgrade_header.lower() == "websocket":
            return await call_next(request)

        response = await call_next(request)

        # Prevent XSS attacks
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Prevent information disclosure
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy (relaxed for API)
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"

        # HSTS (only in production)
        if os.environ.get("ENVIRONMENT") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Remove server information
        response.headers["Server"] = "UDO-API"

        return response


# ============================================================
# HIGH-04: Debug Endpoint Protection
# ============================================================
IS_PRODUCTION = os.environ.get("ENVIRONMENT") == "production"
DEBUG_ENABLED = os.environ.get("DEBUG", "false").lower() == "true" and not IS_PRODUCTION


# ============================================================
# CORS Configuration - Development mode with permissive settings
# ============================================================
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

IS_DEV = os.environ.get("ENVIRONMENT") != "production"

if IS_DEV:
    logger.info("[DEV] CORS: Using permissive settings for development")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if IS_DEV else CORS_ORIGINS,
    allow_credentials=False if IS_DEV else True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)
logger.info("[OK] CORS middleware ENABLED for API + WebSocket support")

# NOTE: OPTIONS handled by CORSASGIWrapper at ASGI level (see below)

# Add security headers middleware
# TEMPORARILY DISABLED for WebSocket testing
# app.add_middleware(SecurityHeadersMiddleware)
logger.info("[WARN] Security headers middleware DISABLED for WebSocket testing")

# ============================================================
# Adaptive cache for expensive operations (uncertainty-aware TTL)
# ============================================================
from datetime import timedelta
_cache = {
    "status": {"data": None, "expires": datetime.now()},
    "metrics": {"data": None, "expires": datetime.now()}
}

def get_adaptive_ttl(uncertainty_state: str = None) -> int:
    """Calculate TTL based on uncertainty state"""
    # Default TTL increased from 10s to 60s
    if uncertainty_state is None:
        return 60

    # Adaptive TTL based on uncertainty state
    ttl_map = {
        "DETERMINISTIC": 300,  # 5 minutes (highly predictable)
        "PROBABILISTIC": 60,   # 1 minute (statistically confident)
        "QUANTUM": 10,         # 10 seconds (multiple possibilities)
        "CHAOTIC": 2,          # 2 seconds (high uncertainty)
        "VOID": 1              # 1 second (unknown territory)
    }
    return ttl_map.get(uncertainty_state.upper(), 60)

def get_cached(key: str, ttl_seconds: int = None):
    """Get cached value if not expired"""
    cache_entry = _cache.get(key)
    if cache_entry and datetime.now() < cache_entry["expires"]:
        return cache_entry["data"]
    return None

def set_cached(key: str, data: any, ttl_seconds: int = None):
    """Set cached value with adaptive expiration"""
    if ttl_seconds is None:
        ttl_seconds = 60  # Default increased from 10s to 60s

    _cache[key] = {
        "data": data,
        "expires": datetime.now() + timedelta(seconds=ttl_seconds)
    }

# Setup global error handlers
# TEMPORARILY DISABLED for WebSocket testing
# if ERROR_HANDLER_AVAILABLE:
#     setup_error_handlers(app)
#     logger.info("[OK] Global error handlers configured")
logger.info("[WARN] Error handlers DISABLED for WebSocket testing")

# Setup security middleware
# TEMPORARILY DISABLED for WebSocket testing
# if SECURITY_AVAILABLE:
#     setup_security(app)
#     logger.info("[OK] Security middleware configured")
logger.info("[WARN] Security middleware DISABLED for WebSocket testing")

# Setup performance monitoring
# TEMPORARILY DISABLED for WebSocket testing
# if MONITORING_AVAILABLE:
#     setup_monitoring(app)
#     logger.info("[OK] Performance monitoring configured")
logger.info("[WARN] Performance monitoring DISABLED for WebSocket testing")

# Include routers
if ROUTERS_AVAILABLE:
    app.include_router(version_history_router)
    logger.info("[OK] Version History router included")
    app.include_router(quality_metrics_router)
    app.include_router(constitutional_router)
    logger.info("[OK] Constitutional router included (AI Governance)")
    logger.info("[OK] Quality Metrics router included")

    if PROJECT_CONTEXT_AVAILABLE:
        app.include_router(project_context_router)
        logger.info("[OK] Project Context router included")
        app.include_router(projects_router)
        logger.info("[OK] Projects router included")

# Include auth router
if AUTH_ROUTER_AVAILABLE:
    app.include_router(auth_router)
    logger.info("[OK] Authentication router included")

if MODULES_ROUTER_AVAILABLE:
    app.include_router(modules_router)
    logger.info("[OK] Modules router included (Standard Level MDO)")

if TASKS_ROUTER_AVAILABLE:
    app.include_router(tasks_router)
    logger.info("[OK] Tasks router included (Task Management)")

if OBSIDIAN_ROUTER_AVAILABLE:
    app.include_router(obsidian_router)
    logger.info("[OK] Obsidian router included (Knowledge Management)")

if KANBAN_TASKS_ROUTER_AVAILABLE:
    app.include_router(kanban_tasks_router)
    logger.info("[OK] Kanban Tasks router included (Kanban-UDO Integration: /api/kanban/tasks)")

if KANBAN_DEPENDENCIES_ROUTER_AVAILABLE:
    app.include_router(kanban_dependencies_router)
    logger.info("[OK] Kanban Dependencies router included (DAG Management: /api/kanban/dependencies)")

if KANBAN_PROJECTS_ROUTER_AVAILABLE:
    app.include_router(kanban_projects_router)
    logger.info("[OK] Kanban Projects router included (Multi-Project Q5: /api/kanban/projects)")

if KANBAN_CONTEXT_ROUTER_AVAILABLE:
    app.include_router(kanban_context_router)
    logger.info("[OK] Kanban Context router included (Context Operations Q4: /api/kanban/context)")

if KANBAN_AI_ROUTER_AVAILABLE:
    app.include_router(kanban_ai_router)
    logger.info("[OK] Kanban AI router included (AI Task Suggestions Q2: /api/kanban/ai)")

if KANBAN_ARCHIVE_ROUTER_AVAILABLE:
    app.include_router(kanban_archive_router)
    logger.info("[OK] Kanban Archive router included (Done-End Archive Q6: /api/kanban/archive)")

if TEST_WEBSOCKET_ROUTER_AVAILABLE:
    app.include_router(test_websocket_router)
    logger.info("[OK] Test WebSocket router included (Debugging: /ws/test)")

if KANBAN_WEBSOCKET_ROUTER_AVAILABLE:
    app.include_router(kanban_websocket_router)
    logger.info("[OK] Kanban WebSocket router included (Real-time Updates Week 7+: /ws/kanban)")

if ADMIN_ROUTER_AVAILABLE:
    app.include_router(admin_router)
    logger.info("[OK] Admin router included (Feature Flags Tier 1 Rollback: /api/admin)")

if KNOWLEDGE_FEEDBACK_ROUTER_AVAILABLE:
    logger.info(f"[DEBUG] knowledge_feedback_router object: {knowledge_feedback_router}")
    logger.info(f"[DEBUG] knowledge_feedback_router prefix: {knowledge_feedback_router.prefix}")
    logger.info(f"[DEBUG] knowledge_feedback_router routes: {len(knowledge_feedback_router.routes)}")

    # List all routes before including
    logger.info(f"[DEBUG] App routes before include: {len(app.routes)}")

    app.include_router(knowledge_feedback_router)

    # List all routes after including
    logger.info(f"[DEBUG] App routes after include: {len(app.routes)}")

    # List knowledge routes
    knowledge_routes = [route for route in app.routes if hasattr(route, 'path') and '/knowledge' in route.path]
    logger.info(f"[DEBUG] Knowledge routes: {[route.path for route in knowledge_routes]}")

    logger.info("[OK] Knowledge Feedback router included (Accuracy Tracking Week 6: /api/knowledge)")

if KNOWLEDGE_SEARCH_ROUTER_AVAILABLE:
    app.include_router(knowledge_search_router)
    logger.info("[OK] Knowledge Search router included (3-Tier Search Week 6: /api/knowledge/search)")

if TIME_TRACKING_ROUTER_AVAILABLE:
    app.include_router(time_tracking_router)
    logger.info("[OK] Time Tracking router included (ROI Measurement)")

if GI_FORMULA_ROUTER_AVAILABLE:
    app.include_router(gi_formula_router)
    logger.info("[OK] GI Formula router included (Genius Insight Formula)")

if CK_THEORY_ROUTER_AVAILABLE:
    app.include_router(ck_theory_router)
    logger.info("[OK] C-K Theory router included (Design Alternatives)")

# Force reload to register Uncertainty Map router
if UNCERTAINTY_ROUTER_AVAILABLE:
    app.include_router(uncertainty_router)
    logger.info("[OK] Uncertainty Map router included (Predictive Uncertainty)")

# TEMPORARILY DISABLED - Conflicts with Kanban WebSocket
# if WEBSOCKET_AVAILABLE:
#     app.include_router(websocket_handler.router)
#     logger.info("[OK] WebSocket handler included")
logger.info("[WARN] WebSocket handler DISABLED to test Kanban WebSocket")

# ============================================================
# ASGI-Level CORS Wrapper - Intercepts ALL requests BEFORE routing
# This is the ONLY reliable way to handle OPTIONS in FastAPI
# ============================================================
class CORSASGIWrapper:
    """
    Pure ASGI middleware that wraps the entire FastAPI application.
    Intercepts OPTIONS requests at the lowest level, BEFORE any routing.
    This solves the issue where routers return 405 for OPTIONS.
    """

    def __init__(self, app):
        self.app = app

    def __getattr__(self, name):
        """Delegate all attribute access to the wrapped FastAPI app"""
        return getattr(self.app, name)

    async def __call__(self, scope, receive, send):
        # Only handle HTTP requests, pass through WebSocket etc.
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")

        # Intercept ALL OPTIONS requests and return CORS headers
        if method == "OPTIONS":
            # Extract origin from headers
            headers_list = scope.get("headers", [])
            origin = b"*"
            request_headers = b"*"

            for name, value in headers_list:
                if name.lower() == b"origin":
                    origin = value
                elif name.lower() == b"access-control-request-headers":
                    request_headers = value

            # Build CORS response headers
            response_headers = [
                (b"access-control-allow-origin", origin if origin != b"*" else b"*"),
                (b"access-control-allow-methods", b"GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD"),
                (b"access-control-allow-headers", request_headers),
                (b"access-control-allow-credentials", b"true"),
                (b"access-control-max-age", b"600"),
                (b"content-length", b"0"),
                (b"content-type", b"text/plain"),
            ]

            # Send HTTP response start
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": response_headers,
            })

            # Send empty body and complete
            await send({
                "type": "http.response.body",
                "body": b"",
            })

            # Log for debugging
            path = scope.get("path", "/")
            logger.info(f"[CORS-ASGI] OPTIONS preflight handled for {path}")
            return

        # For non-OPTIONS requests, proceed normally
        await self.app(scope, receive, send)

# Wrap the entire FastAPI app with CORS handler
# This MUST be after all routers are included
original_app = app
app = CORSASGIWrapper(original_app)
logger.info("[OK] ASGI-level CORS wrapper applied (intercepts OPTIONS before routing)")

# ============================================================
# Lazy Initialization Pattern for UDO System
# ============================================================
# Global UDO instance (lazy-loaded on first request)
_udo_system_instance = None
_udo_initialization_lock = False

def get_udo_system():
    """Lazy initialization of UDO system (initialize on first request)

    This pattern defers expensive initialization until the first API call,
    reducing server startup time from 8+ seconds to instant.
    """
    global _udo_system_instance, _udo_initialization_lock, udo_system

    # Return existing instance if already initialized
    if _udo_system_instance is not None:
        # Keep backward-compatible alias in sync for routers that look it up
        udo_system = _udo_system_instance
        return _udo_system_instance

    # Thread-safe initialization check
    if _udo_initialization_lock:
        logger.warning("[WARN] UDO system initialization already in progress")
        return None

    # Initialize UDO system
    if UDO_AVAILABLE:
        try:
            _udo_initialization_lock = True
            logger.info("[EMOJI] Initializing UDO system (first request)...")
            _udo_system_instance = IntegratedUDOSystem(project_name="UDO-Dashboard")
            # Expose as module-level alias for routers that resolve via main.udo_system
            udo_system = _udo_system_instance
            logger.info("[OK] UDO system initialized (lazy loading complete)")
        except Exception as e:
            logger.error(f"[FAIL] Failed to initialize UDO: {e}")
            _udo_system_instance = None
        finally:
            _udo_initialization_lock = False
    else:
        logger.warning("[WARN] UDO not available - running in mock mode")

    return _udo_system_instance

# Backward compatibility alias
udo_system = None

# Global Phase Transition components
phase_state_manager = None
phase_transition_listener = None

# TEST: Minimal WebSocket endpoint
from fastapi import WebSocket

@app.websocket("/ws/test")
async def test_websocket(websocket: WebSocket):
    """Minimal WebSocket endpoint for testing"""
    await websocket.accept()
    await websocket.send_text("Hello from test WebSocket!")
    await websocket.close()

# Pydantic models
class TaskRequest(BaseModel):
    task: str
    phase: Optional[str] = None
    priority: Optional[str] = "normal"

class SystemCommand(BaseModel):
    command: str
    params: Optional[Dict] = {}

class DashboardMetrics(BaseModel):
    system_status: Dict
    current_phase: str
    confidence_level: float
    uncertainty_state: str
    ai_services: Dict
    ml_metrics: Dict
    recent_tasks: List[Dict]
    performance_metrics: Dict

# Startup event
@app.on_event("startup")
async def startup_event():
    global udo_system

    # Initialize Redis client
    if REDIS_AVAILABLE:
        try:
            redis_client = await get_redis_client()
            if await redis_client.ensure_connected():
                logger.info("[OK] Redis client initialized")
            else:
                logger.warning("[WARN] Redis not available, distributed features disabled")
        except Exception as e:
            logger.warning(f"[WARN] Redis initialization failed: {e}")

    # Initialize SessionManagerV2
    if WEBSOCKET_AVAILABLE:
        try:
            session_manager = await get_session_manager()
            logger.info("[OK] SessionManagerV2 initialized")
        except Exception as e:
            logger.warning(f"[WARN] SessionManager initialization failed: {e}")

    # Initialize async database and project context service
    if ASYNC_DB_AVAILABLE:
        try:
            await initialize_async_database()
            logger.info("[OK] Async database initialized")

            # Initialize project context service with database pool
            db_pool = async_db.get_pool()
            project_context_service = init_project_context_service(db_pool)

            # Initialize default project
            await project_context_service.initialize_default_project()
            logger.info("[OK] Project context service initialized")
        except Exception as e:
            logger.warning(f"[WARN]  Database not available, falling back to mock service: {e}")
            logger.info("[EMOJI] To enable database features, ensure PostgreSQL is running and database is created")
            # Enable mock service as fallback
            from app.services.project_context_service import enable_mock_service
            enable_mock_service()
            logger.info("[OK] Mock service enabled as fallback")
    else:
        # If async database module is not available at all
        logger.warning("[WARN] Async database module not available, using mock service")
        from app.services.project_context_service import enable_mock_service
        enable_mock_service()
        logger.info("[OK] Mock service enabled (async_database module missing)")

    # Initialize UDO system immediately (eager initialization)
    # Required for uncertainty router and WebSocket broadcasting
    if UDO_AVAILABLE:
        try:
            logger.info("[EMOJI] Initializing UDO system (startup)...")
            from src.integrated_udo_system import IntegratedUDOSystem
            udo_system = IntegratedUDOSystem(project_name="UDO-Dashboard")
            logger.info("[OK] UDO system initialized with all components")
        except Exception as e:
            logger.error(f"[FAIL] Failed to initialize UDO system: {e}")
            logger.warning("[WARN] Uncertainty Map and related features will be unavailable")
            udo_system = None
    else:
        logger.warning("[WARN] UDO system not available (src modules missing)")

    # Initialize Phase Transition System
    global phase_state_manager, phase_transition_listener
    if PHASE_TRANSITION_AVAILABLE:
        try:
            # Initialize PhaseStateManager
            phase_state_manager = PhaseStateManager()
            logger.info("[OK] PhaseStateManager initialized")

            # Initialize TimeTrackingService (requires database pool)
            if ASYNC_DB_AVAILABLE:
                try:
                    db_pool = async_db.get_pool()
                    if db_pool is None:
                        raise RuntimeError("Database pool is None - database not initialized")

                    time_tracking_service = TimeTrackingService(pool=db_pool)

                    # Get WebSocket broadcast function
                    broadcast_func = None
                    if WEBSOCKET_AVAILABLE:
                        try:
                            session_manager = await get_session_manager()
                            broadcast_func = session_manager.broadcast_to_all
                        except Exception as e:
                            logger.warning(f"[WARN] WebSocket broadcast not available for phase transitions: {e}")

                    # Initialize PhaseTransitionListener
                    phase_transition_listener = PhaseTransitionListener(
                        pool=db_pool,
                        time_tracking_service=time_tracking_service,
                        broadcast_func=broadcast_func
                    )

                    # Register listener callback with PhaseStateManager
                    callback = create_listener_callback(phase_transition_listener)
                    phase_state_manager.register_listener(callback)

                    logger.info("[OK] PhaseTransitionListener initialized and registered")
                except Exception as e:
                    logger.warning(f"[WARN] Phase Transition with database failed: {e}")
                    logger.info("[EMOJI] Phase transitions will not auto-track time without database")
            else:
                logger.info("[EMOJI] Phase Transition System requires database for time tracking")
        except Exception as e:
            logger.error(f"[FAIL] Failed to initialize Phase Transition System: {e}")
    else:
        logger.info("[EMOJI] Phase Transition System not available")

    # Start background Obsidian sync (periodic backup every 1-2 hours)
    try:
        from app.background_tasks import start_background_sync

        # Get sync interval from environment or use default (1 hour)
        sync_interval = int(os.getenv("OBSIDIAN_SYNC_INTERVAL_HOURS", "1"))
        await start_background_sync(sync_interval_hours=sync_interval)
        logger.info(f"[OK] Background Obsidian sync started (every {sync_interval}h)")
    except Exception as e:
        logger.warning(f"[WARN] Background sync not available: {e}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""

    # Cleanup SessionManager
    if WEBSOCKET_AVAILABLE:
        try:
            session_manager = await get_session_manager()
            await session_manager.cleanup()
            logger.info("[OK] SessionManagerV2 cleaned up")
        except Exception as e:
            logger.error(f"[FAIL] Failed to cleanup SessionManager: {e}")

    # Cleanup Phase Transition System
    global phase_transition_listener
    if phase_transition_listener is not None:
        try:
            await phase_transition_listener.stop()
            logger.info("[OK] PhaseTransitionListener stopped")
        except Exception as e:
            logger.error(f"[FAIL] Failed to stop PhaseTransitionListener: {e}")

    # Cleanup Redis
    if REDIS_AVAILABLE:
        try:
            await cleanup_redis()
            logger.info("[OK] Redis client cleaned up")
        except Exception as e:
            logger.error(f"[FAIL] Failed to cleanup Redis: {e}")

    # Cleanup async database
    if ASYNC_DB_AVAILABLE:
        try:
            await close_async_database()
            logger.info("[OK] Async database closed")
        except Exception as e:
            logger.error(f"[FAIL] Failed to close async database: {e}")

    # Stop background sync
    try:
        from app.background_tasks import stop_background_sync
        await stop_background_sync()
        logger.info("[OK] Background sync stopped")
    except Exception as e:
        logger.error(f"[FAIL] Failed to stop background sync: {e}")

# Error statistics endpoint (if error handler available)
# HIGH-04: Protected in production (internal debugging endpoint)
if ERROR_HANDLER_AVAILABLE:
    @app.get("/api/errors/stats")
    async def get_error_statistics():
        """Get error statistics and history (development only)"""
        if IS_PRODUCTION:
            raise HTTPException(
                status_code=403,
                detail="Error statistics endpoint is disabled in production"
            )
        return error_handler.get_error_statistics()

# Health check
@app.get("/api/health")
async def health_check():
    """Comprehensive health check for all services"""
    health_status = {
        "status": "healthy",
        "udo_available": UDO_AVAILABLE,
        "database_available": False,
        "project_context_available": PROJECT_CONTEXT_AVAILABLE if ROUTERS_AVAILABLE else False,
        "timestamp": datetime.now().isoformat()
    }

    # Check async database health
    if ASYNC_DB_AVAILABLE:
        try:
            health_status["database_available"] = await async_db.health_check()
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health_status["database_available"] = False

    # Overall status
    if not health_status["database_available"] and PROJECT_CONTEXT_AVAILABLE:
        health_status["status"] = "degraded"

    return health_status

# Get system status
@app.get("/api/status")
async def get_system_status():
    # Lazy initialization: system initializes on first request
    udo = get_udo_system()
    if not udo:
        return {
            "status": "offline",
            "message": "UDO system not initialized"
        }

    # Check cache first (adaptive TTL based on uncertainty)
    cached = get_cached("status")
    if cached:
        return cached

    try:
        # Use async version for parallel component queries (30% faster)
        report = await udo.get_system_report_async()

        # Extract uncertainty state for adaptive caching
        latest_execution = None
        if udo.execution_history:
            latest_execution = udo.execution_history[-1]
        uncertainty_state = latest_execution.get("uncertainty", {}).get("state") if latest_execution else None

        result = {
            "status": "online",
            "report": report
        }

        # Cache with adaptive TTL
        ttl = get_adaptive_ttl(uncertainty_state)
        set_cached("status", result, ttl_seconds=ttl)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Execute development cycle
@app.post("/api/execute")
async def execute_task(request: TaskRequest):
    udo = get_udo_system()
    if not udo:
        raise HTTPException(status_code=503, detail="UDO system not available")

    try:
        result = udo.execute_development_cycle(
            task=request.task,
            phase=request.phase
        )

        # Broadcast update to connected clients
        if WEBSOCKET_AVAILABLE:
            await connection_manager.broadcast_to_all({
                "type": "task_executed",
                "data": result
            })

        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Train ML models
@app.post("/api/train")
async def train_models():
    udo = get_udo_system()
    if not udo:
        raise HTTPException(status_code=503, detail="UDO system not available")

    try:
        results = udo.train_ml_models()
        return {"success": True, "training_results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get dashboard metrics
@app.get("/api/metrics")
async def get_metrics():
    """Get comprehensive dashboard metrics"""
    udo = get_udo_system()
    if not udo:
        # Return mock data if UDO not available
        return {
            "system_status": {
                "udo": False, "uncertainty": False,
                "ai_connector": False, "ml_system": False
            },
            "current_phase": "ideation",
            "confidence_level": 0.0,
            "uncertainty_state": "unknown",
            "ai_services": {},
            "ml_metrics": {},
            "recent_tasks": [],
            "performance_metrics": {}
        }

    # Check cache first (adaptive TTL)
    cached = get_cached("metrics")
    if cached:
        return cached

    try:
        # Use async version for parallel component queries (30% faster)
        report = await udo.get_system_report_async()

        # Get latest execution if available
        latest_execution = None
        if udo.execution_history:
            latest_execution = udo.execution_history[-1]

        uncertainty_state = latest_execution.get("uncertainty", {}).get("state", "unknown") if latest_execution else "unknown"

        metrics = {
            "system_status": report.get("status", {}),
            "current_phase": report.get("project_context", {}).get("current_phase", "unknown"),
            "confidence_level": latest_execution.get("plan", {}).get("confidence", 0.0) if latest_execution else 0.0,
            "uncertainty_state": uncertainty_state,
            "ai_services": report.get("ai_services", {}),
            "ml_metrics": report.get("ml_models", {}),
            "recent_tasks": udo.execution_history[-5:] if udo else [],
            "performance_metrics": {
                "execution_count": len(udo.execution_history) if udo else 0,
                "avg_confidence": sum(e.get("plan", {}).get("confidence", 0) for e in udo.execution_history) / max(len(udo.execution_history), 1) if udo and udo.execution_history else 0
            }
        }

        # Cache with adaptive TTL based on uncertainty state
        ttl = get_adaptive_ttl(uncertainty_state)
        set_cached("metrics", metrics, ttl_seconds=ttl)
        return metrics
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get phase-specific data
@app.get("/api/phases/{phase}")
async def get_phase_data(phase: str):
    valid_phases = ["ideation", "design", "mvp", "implementation", "testing"]
    if phase not in valid_phases:
        raise HTTPException(status_code=400, detail=f"Invalid phase. Must be one of {valid_phases}")

    if not udo_system:
        return {"phase": phase, "data": {}}

    # Get phase-specific executions
    phase_executions = [e for e in udo_system.execution_history if e.get("phase") == phase]

    return {
        "phase": phase,
        "execution_count": len(phase_executions),
        "avg_confidence": sum(e.get("plan", {}).get("confidence", 0) for e in phase_executions) / max(len(phase_executions), 1) if phase_executions else 0,
        "recent_executions": phase_executions[-3:]
    }

# WebSocket handled by websocket_handler router (included at line 248)

# System control endpoints
@app.post("/api/control")
async def system_control(command: SystemCommand):
    """Control system operations"""
    if not udo_system:
        raise HTTPException(status_code=503, detail="UDO system not available")

    try:
        if command.command == "reset":
            # Reset system state
            udo_system.execution_history = []
            return {"success": True, "message": "System reset"}

        elif command.command == "save_state":
            # Save system state
            filepath = command.params.get("filepath", "system_state.json")
            udo_system.save_state(filepath)
            return {"success": True, "message": f"State saved to {filepath}"}

        elif command.command == "change_phase":
            # Change current phase
            new_phase = command.params.get("phase")
            if new_phase:
                udo_system.project_context.current_phase = new_phase
                if WEBSOCKET_AVAILABLE:
                    await connection_manager.broadcast_to_all({
                        "type": "phase_changed",
                        "data": {"new_phase": new_phase}
                    })
                return {"success": True, "message": f"Phase changed to {new_phase}"}

        else:
            raise HTTPException(status_code=400, detail=f"Unknown command: {command.command}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mock data endpoint for development (HIGH-04: Protected in production)
@app.get("/api/mock/generate")
async def generate_mock_data():
    """Generate mock data for UI development (disabled in production)"""
    # HIGH-04: Block debug endpoints in production
    if IS_PRODUCTION:
        raise HTTPException(
            status_code=403,
            detail="Debug endpoints are disabled in production"
        )

    import random

    phases = ["ideation", "design", "mvp", "implementation", "testing"]
    states = ["Deterministic", "Probabilistic", "Quantum", "Chaotic", "Void"]

    mock_data = {
        "executions": [],
        "metrics": {
            "total_executions": random.randint(50, 200),
            "success_rate": random.uniform(0.7, 0.95),
            "avg_confidence": random.uniform(0.6, 0.9),
            "avg_uncertainty": random.uniform(0.1, 0.5)
        }
    }

    # Generate mock execution history
    for i in range(10):
        mock_data["executions"].append({
            "id": i + 1,
            "task": f"Task {i + 1}: {'Implement feature' if i % 2 else 'Fix bug'}",
            "phase": random.choice(phases),
            "confidence": random.uniform(0.5, 0.95),
            "uncertainty_state": random.choice(states),
            "timestamp": datetime.now().isoformat(),
            "decision": random.choice(["GO", "GO_WITH_CHECKPOINTS", "NO_GO"]),
            "duration": random.randint(100, 5000)  # ms
        })

    return mock_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
