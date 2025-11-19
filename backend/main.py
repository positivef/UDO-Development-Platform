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
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

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
# CRITICAL: Enable mock service BEFORE importing routers
# This ensures global variables are set when routers load
# ============================================================
try:
    from app.services.project_context_service import enable_mock_service
    enable_mock_service()
    logger.info("✅ Mock service enabled (BEFORE router imports)")
except Exception as e:
    logger.error(f"Failed to enable mock service before router imports: {e}")

# Import routers
try:
    from app.routers import version_history_router, quality_metrics_router
    ROUTERS_AVAILABLE = True
except ImportError as e:
    ROUTERS_AVAILABLE = False
    logger.warning(f"Routers not available: {e}")

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

# Import WebSocket handler and SessionManagerV2
try:
    from app.routers import websocket_handler
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
    from async_database import async_db, initialize_async_database, close_async_database
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

# FastAPI app - with updated MockProjectService
app = FastAPI(
    title="UDO Development Platform API",
    version="3.0.0",
    description="Real-time development automation and monitoring"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup global error handlers
if ERROR_HANDLER_AVAILABLE:
    setup_error_handlers(app)
    logger.info("✅ Global error handlers configured")

# Include routers
if ROUTERS_AVAILABLE:
    app.include_router(version_history_router)
    logger.info("✅ Version History router included")
    app.include_router(quality_metrics_router)
    logger.info("✅ Quality Metrics router included")

    if PROJECT_CONTEXT_AVAILABLE:
        app.include_router(project_context_router)
        logger.info("✅ Project Context router included")
        app.include_router(projects_router)
        logger.info("✅ Projects router included")

    if MODULES_ROUTER_AVAILABLE:
        app.include_router(modules_router)
        logger.info("✅ Modules router included (Standard Level MDO)")

    if WEBSOCKET_AVAILABLE:
        app.include_router(websocket_handler.router)
        logger.info("✅ WebSocket handler included")

# Global UDO instance
udo_system = None
connected_clients = []

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
                logger.info("✅ Redis client initialized")
            else:
                logger.warning("⚠️ Redis not available, distributed features disabled")
        except Exception as e:
            logger.warning(f"⚠️ Redis initialization failed: {e}")

    # Initialize SessionManagerV2
    if WEBSOCKET_AVAILABLE:
        try:
            session_manager = await get_session_manager()
            logger.info("✅ SessionManagerV2 initialized")
        except Exception as e:
            logger.warning(f"⚠️ SessionManager initialization failed: {e}")

    # Initialize async database and project context service
    if ASYNC_DB_AVAILABLE:
        try:
            await initialize_async_database()
            logger.info("✅ Async database initialized")

            # Initialize project context service with database pool
            db_pool = async_db.get_pool()
            project_context_service = init_project_context_service(db_pool)

            # Initialize default project
            await project_context_service.initialize_default_project()
            logger.info("✅ Project context service initialized")
        except Exception as e:
            logger.warning(f"⚠️  Database not available, project context features disabled: {e}")
            logger.info("💡 To enable project context features, ensure PostgreSQL is running and database is created")
            # Mock service already enabled before router imports
    else:
        # If async database module is not available at all
        logger.warning("⚠️ Async database module not available, using mock service")
        # Mock service already enabled before router imports

    # Initialize UDO system
    if UDO_AVAILABLE:
        try:
            udo_system = IntegratedUDOSystem(project_name="UDO-Dashboard")
            logger.info("✅ UDO system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize UDO: {e}")
    else:
        logger.warning("Running in mock mode - UDO not available")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""

    # Cleanup SessionManager
    if WEBSOCKET_AVAILABLE:
        try:
            session_manager = await get_session_manager()
            await session_manager.cleanup()
            logger.info("✅ SessionManagerV2 cleaned up")
        except Exception as e:
            logger.error(f"❌ Failed to cleanup SessionManager: {e}")

    # Cleanup Redis
    if REDIS_AVAILABLE:
        try:
            await cleanup_redis()
            logger.info("✅ Redis client cleaned up")
        except Exception as e:
            logger.error(f"❌ Failed to cleanup Redis: {e}")

    # Cleanup async database
    if ASYNC_DB_AVAILABLE:
        try:
            await close_async_database()
            logger.info("✅ Async database closed")
        except Exception as e:
            logger.error(f"❌ Failed to close async database: {e}")

# Error statistics endpoint (if error handler available)
if ERROR_HANDLER_AVAILABLE:
    @app.get("/api/errors/stats")
    async def get_error_statistics():
        """Get error statistics and history"""
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
    if not udo_system:
        return {
            "status": "offline",
            "message": "UDO system not initialized"
        }

    try:
        report = udo_system.get_system_report()
        return {
            "status": "online",
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Execute development cycle
@app.post("/api/execute")
async def execute_task(request: TaskRequest):
    if not udo_system:
        raise HTTPException(status_code=503, detail="UDO system not available")

    try:
        result = udo_system.execute_development_cycle(
            task=request.task,
            phase=request.phase
        )

        # Broadcast update to connected clients
        await broadcast_update({
            "type": "task_executed",
            "data": result
        })

        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Train ML models
@app.post("/api/train")
async def train_models():
    if not udo_system:
        raise HTTPException(status_code=503, detail="UDO system not available")

    try:
        results = udo_system.train_ml_models()
        return {"success": True, "training_results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get dashboard metrics
@app.get("/api/metrics")
async def get_metrics():
    """Get comprehensive dashboard metrics"""
    if not udo_system:
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

    try:
        report = udo_system.get_system_report()

        # Get latest execution if available
        latest_execution = None
        if udo_system.execution_history:
            latest_execution = udo_system.execution_history[-1]

        metrics = {
            "system_status": report.get("status", {}),
            "current_phase": report.get("project_context", {}).get("current_phase", "unknown"),
            "confidence_level": latest_execution.get("plan", {}).get("confidence", 0.0) if latest_execution else 0.0,
            "uncertainty_state": latest_execution.get("uncertainty", {}).get("state", "unknown") if latest_execution else "unknown",
            "ai_services": report.get("ai_services", {}),
            "ml_metrics": report.get("ml_models", {}),
            "recent_tasks": udo_system.execution_history[-5:] if udo_system else [],
            "performance_metrics": {
                "execution_count": len(udo_system.execution_history) if udo_system else 0,
                "avg_confidence": sum(e.get("plan", {}).get("confidence", 0) for e in udo_system.execution_history) / max(len(udo_system.execution_history), 1) if udo_system and udo_system.execution_history else 0
            }
        }

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

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)

    try:
        # Send initial status
        if udo_system:
            await websocket.send_json({
                "type": "connection_established",
                "data": udo_system.get_system_report()
            })

        # Keep connection alive
        while True:
            # Receive and echo messages
            data = await websocket.receive_text()

            # Process commands if needed
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in connected_clients:
            connected_clients.remove(websocket)

async def broadcast_update(message: Dict):
    """Broadcast updates to all connected WebSocket clients"""
    for client in connected_clients:
        try:
            await client.send_json(message)
        except:
            # Remove disconnected clients
            connected_clients.remove(client)

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
                await broadcast_update({
                    "type": "phase_changed",
                    "data": {"new_phase": new_phase}
                })
                return {"success": True, "message": f"Phase changed to {new_phase}"}

        else:
            raise HTTPException(status_code=400, detail=f"Unknown command: {command.command}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mock data endpoint for development
@app.get("/api/mock/generate")
async def generate_mock_data():
    """Generate mock data for UI development"""
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