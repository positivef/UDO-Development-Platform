"""API Routers"""
from .version_history import router as version_history_router
from .quality_metrics import router as quality_metrics_router
from .constitutional import router as constitutional_router
from .time_tracking import router as time_tracking_router
from .gi_formula import router as gi_formula_router
from .ck_theory import router as ck_theory_router
from .uncertainty import router as uncertainty_router

# Try importing project context routers
try:
    from .project_context import router as project_context_router, projects_router
    project_context_available = True
except ImportError:
    project_context_available = False

# Try importing WebSocket handler
try:
    from . import websocket_handler
    websocket_available = True
except ImportError:
    websocket_available = False

# Build exports dynamically
__all__ = [
    "version_history_router",
    "quality_metrics_router",
    "constitutional_router",
    "time_tracking_router",
    "gi_formula_router",
    "ck_theory_router",
    "uncertainty_router"
]

if project_context_available:
    __all__.extend(["project_context_router", "projects_router"])

if websocket_available:
    __all__.append("websocket_handler")
