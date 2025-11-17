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

# FastAPI app
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
    if UDO_AVAILABLE:
        try:
            udo_system = IntegratedUDOSystem(project_name="UDO-Dashboard")
            logger.info("✅ UDO system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize UDO: {e}")
    else:
        logger.warning("Running in mock mode - UDO not available")

# Health check
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "udo_available": UDO_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

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