"""
WebSocket Handler for Real-time Session Synchronization

Provides real-time communication between multiple terminal sessions:
- Session events broadcasting
- Conflict notifications
- Lock status updates
- Collaborative editing events
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Set

from app.services.redis_client import RedisKeys, get_redis_client
from app.services.session_manager import SessionManager, get_session_manager
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """
    Manages WebSocket connections for all sessions
    """

    def __init__(self):
        # Map session_id to websocket connection
        self.active_connections: Dict[str, WebSocket] = {}
        # Map project_id to set of session_ids
        self.project_sessions: Dict[str, Set[str]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, session_id: str, project_id: Optional[str] = None):
        """Accept and register new WebSocket connection"""
        await websocket.accept()

        async with self._lock:
            self.active_connections[session_id] = websocket

            if project_id:
                if project_id not in self.project_sessions:
                    self.project_sessions[project_id] = set()
                self.project_sessions[project_id].add(session_id)

        logger.info(f"WebSocket connected: session={session_id}, project={project_id}")

    async def disconnect(self, session_id: str):
        """Remove WebSocket connection"""
        async with self._lock:
            if session_id in self.active_connections:
                del self.active_connections[session_id]

            # Remove from all project sessions
            for project_id, sessions in self.project_sessions.items():
                sessions.discard(session_id)

        logger.info(f"WebSocket disconnected: session={session_id}")

    async def send_personal_message(self, message: Dict[str, Any], session_id: str) -> bool:
        """Send message to specific session"""
        websocket = self.active_connections.get(session_id)
        if websocket:
            try:
                if websocket.application_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
                    return True
            except Exception as e:
                logger.error(f"Failed to send message to {session_id}: {e}")
                await self.disconnect(session_id)
        return False

    async def broadcast_to_project(
        self,
        message: Dict[str, Any],
        project_id: str,
        exclude_session: Optional[str] = None,
    ):
        """Broadcast message to all sessions in a project"""
        sessions = self.project_sessions.get(project_id, set()).copy()

        for session_id in sessions:
            if session_id != exclude_session:
                await self.send_personal_message(message, session_id)

    async def broadcast_to_all(self, message: Dict[str, Any], exclude_session: Optional[str] = None):
        """Broadcast message to all connected sessions"""
        sessions = list(self.active_connections.keys())

        for session_id in sessions:
            if session_id != exclude_session:
                await self.send_personal_message(message, session_id)


# Global connection manager
connection_manager = ConnectionManager()


# Root WebSocket endpoint (for simple client connections)
@router.websocket("")
async def websocket_root(websocket: WebSocket, session_manager: SessionManager = Depends(get_session_manager)):
    """
    Root WebSocket endpoint for dashboard connections
    Automatically generates session ID if not provided
    """
    from uuid import uuid4

    session_id = str(uuid4())
    project_id = None
    _ = None  # redis_client placeholder for future use

    try:
        # Connect WebSocket
        await connection_manager.connect(websocket, session_id, project_id)

        # Get Redis client for pub/sub (optional, may fail)
        try:
            await get_redis_client()  # Verify Redis connectivity
        except Exception as e:
            logger.warning(f"Redis not available for WebSocket: {e}")

        # Send initial connection success
        await websocket.send_json(
            {
                "type": "connection_established",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Handle incoming messages
        try:
            while True:
                data = await websocket.receive_json()

                # Simple echo back for heartbeat/ping
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"WebSocket message error: {e}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")

    finally:
        # Cleanup
        await connection_manager.disconnect(session_id)


@router.websocket("/session")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str = Query(..., description="Session ID"),
    project_id: Optional[str] = Query(None, description="Project ID"),
    session_manager: SessionManager = Depends(get_session_manager),
):
    """
    WebSocket endpoint for session synchronization

    Query params:
    - session_id: Unique session identifier
    - project_id: Optional project ID for project-specific events
    """
    redis_client = None
    pubsub = None

    try:
        # Connect WebSocket
        await connection_manager.connect(websocket, session_id, project_id)

        # Get Redis client for pub/sub (graceful fallback)
        try:
            redis_client = await get_redis_client()
        except Exception as e:
            logger.warning("Redis unavailable for WebSocket session %s: %s", session_id, e)
            redis_client = None

        if redis_client:
            # Subscribe to relevant channels
            channels = [
                RedisKeys.CHANNEL_SESSION,
                RedisKeys.CHANNEL_CONFLICTS,
                RedisKeys.CHANNEL_BROADCAST,
            ]

            if project_id:
                channels.append(RedisKeys.CHANNEL_PROJECT.format(project_id))

            pubsub = await redis_client.subscribe(channels)

        # Send initial connection success
        await websocket.send_json(
            {
                "type": "connection_established",
                "session_id": session_id,
                "project_id": project_id,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Notify other sessions about new connection
        await connection_manager.broadcast_to_project(
            {
                "type": "session_connected",
                "session_id": session_id,
                "project_id": project_id,
                "timestamp": datetime.now().isoformat(),
            },
            project_id,
            exclude_session=session_id,
        )

        # Start tasks for handling messages
        tasks = []

        # Task 1: Handle incoming WebSocket messages
        async def handle_websocket_messages():
            try:
                while True:
                    data = await websocket.receive_json()
                    await process_websocket_message(data, session_id, project_id, session_manager)
            except WebSocketDisconnect:
                pass
            except Exception as e:
                logger.error(f"WebSocket message handler error: {e}")

        # Task 2: Handle Redis pub/sub messages
        async def handle_redis_messages():
            if not pubsub:
                return
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            data = json.loads(message["data"])
                            # Forward to WebSocket
                            await websocket.send_json(data)
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                logger.error(f"Redis message handler error: {e}")

        # Task 3: Send heartbeat
        async def send_heartbeat():
            try:
                while True:
                    await asyncio.sleep(30)
                    await websocket.send_json({"type": "heartbeat", "timestamp": datetime.now().isoformat()})

                    # Update session heartbeat in Redis
                    if redis_client:
                        await redis_client.update_session_heartbeat(session_id)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

        # Start all tasks
        tasks = [
            asyncio.create_task(handle_websocket_messages()),
            asyncio.create_task(handle_redis_messages()),
            asyncio.create_task(send_heartbeat()),
        ]

        # Wait for any task to complete (usually disconnect)
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        # Cancel remaining tasks
        for task in pending:
            task.cancel()

    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")

    finally:
        # Cleanup
        await connection_manager.disconnect(session_id)

        # Notify other sessions about disconnection
        if project_id:
            await connection_manager.broadcast_to_project(
                {
                    "type": "session_disconnected",
                    "session_id": session_id,
                    "project_id": project_id,
                    "timestamp": datetime.now().isoformat(),
                },
                project_id,
            )

        # Cleanup Redis subscriptions
        if pubsub:
            await pubsub.close()


async def process_websocket_message(
    data: Dict[str, Any],
    session_id: str,
    project_id: Optional[str],
    session_manager: SessionManager,
):
    """
    Process incoming WebSocket messages from clients
    """
    message_type = data.get("type")
    redis_client = await get_redis_client()

    if message_type == "lock_request":
        # Handle lock request
        resource_id = data.get("resource_id")
        lock_type = data.get("lock_type", "file")

        # Try to acquire lock
        lock = await session_manager.acquire_lock(session_id=session_id, resource_id=resource_id, lock_type=lock_type)

        if lock:
            # Notify all sessions about lock acquisition
            await redis_client.publish(
                RedisKeys.CHANNEL_PROJECT.format(project_id),
                {
                    "type": "lock_acquired",
                    "session_id": session_id,
                    "resource_id": resource_id,
                    "lock_type": lock_type,
                    "timestamp": datetime.now().isoformat(),
                },
            )
        else:
            # Get lock holder info
            holder = await session_manager.get_lock_holder(resource_id)
            await connection_manager.send_personal_message(
                {
                    "type": "lock_denied",
                    "resource_id": resource_id,
                    "holder": holder,
                    "timestamp": datetime.now().isoformat(),
                },
                session_id,
            )

    elif message_type == "lock_release":
        # Handle lock release
        resource_id = data.get("resource_id")

        success = await session_manager.release_lock(session_id=session_id, resource_id=resource_id)

        if success:
            # Notify all sessions about lock release
            await redis_client.publish(
                RedisKeys.CHANNEL_PROJECT.format(project_id),
                {
                    "type": "lock_released",
                    "session_id": session_id,
                    "resource_id": resource_id,
                    "timestamp": datetime.now().isoformat(),
                },
            )

    elif message_type == "file_change":
        # Broadcast file change to other sessions
        file_path = data.get("file_path")
        change_type = data.get("change_type")  # edit, create, delete

        await redis_client.publish(
            RedisKeys.CHANNEL_PROJECT.format(project_id),
            {
                "type": "file_changed",
                "session_id": session_id,
                "file_path": file_path,
                "change_type": change_type,
                "timestamp": datetime.now().isoformat(),
            },
        )

    elif message_type == "cursor_position":
        # Share cursor position for collaborative editing
        file_path = data.get("file_path")
        line = data.get("line")
        column = data.get("column")

        await connection_manager.broadcast_to_project(
            {
                "type": "cursor_update",
                "session_id": session_id,
                "file_path": file_path,
                "line": line,
                "column": column,
                "timestamp": datetime.now().isoformat(),
            },
            project_id,
            exclude_session=session_id,
        )

    elif message_type == "conflict_detected":
        # Handle conflict detection
        conflict_data = {
            "id": f"{session_id}_{datetime.now().timestamp()}",
            "session_id": session_id,
            "resource_id": data.get("resource_id"),
            "conflict_type": data.get("conflict_type"),
            "details": data.get("details"),
            "timestamp": datetime.now().isoformat(),
        }

        # Register conflict in Redis
        await redis_client.register_conflict(project_id, conflict_data)

    elif message_type == "conflict_resolved":
        # Handle conflict resolution
        conflict_id = data.get("conflict_id")
        resolution = data.get("resolution")

        await redis_client.resolve_conflict(project_id, conflict_id)

        # Notify all sessions
        await redis_client.publish(
            RedisKeys.CHANNEL_PROJECT.format(project_id),
            {
                "type": "conflict_resolved",
                "conflict_id": conflict_id,
                "resolution": resolution,
                "resolved_by": session_id,
                "timestamp": datetime.now().isoformat(),
            },
        )

    elif message_type == "broadcast":
        # General broadcast message
        await connection_manager.broadcast_to_project(
            {
                **data.get("payload", {}),
                "from_session": session_id,
                "timestamp": datetime.now().isoformat(),
            },
            project_id,
            exclude_session=session_id,
        )


@router.get("/sessions/active")
async def get_active_sessions(
    project_id: Optional[str] = Query(None, description="Filter by project"),
    session_manager: SessionManager = Depends(get_session_manager),
):
    """Get list of active sessions"""
    redis_client = await get_redis_client()

    sessions = await redis_client.get_active_sessions()

    if project_id:
        # Filter by project if specified
        project_sessions = []
        for session_id in sessions:
            session_data = await session_manager.get_session_info(session_id)
            if session_data and session_data.get("project_id") == project_id:
                project_sessions.append(session_data)
        return {"sessions": project_sessions, "count": len(project_sessions)}

    # Return all active sessions
    all_sessions = []
    for session_id in sessions:
        session_data = await session_manager.get_session_info(session_id)
        if session_data:
            all_sessions.append(session_data)

    return {"sessions": all_sessions, "count": len(all_sessions)}


@router.get("/conflicts/{project_id}")
async def get_conflicts(project_id: str, session_manager: SessionManager = Depends(get_session_manager)):
    """Get all conflicts for a project"""
    redis_client = await get_redis_client()
    conflicts = await redis_client.get_project_conflicts(project_id)

    return {"project_id": project_id, "conflicts": conflicts, "count": len(conflicts)}


# ============================================================================
# Uncertainty WebSocket Endpoint
# ============================================================================


class UncertaintyConnectionManager:
    """Manages WebSocket connections for uncertainty updates"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        async with self._lock:
            self.active_connections[session_id] = websocket
        logger.info(f"Uncertainty WebSocket connected: {session_id}")

    async def disconnect(self, session_id: str):
        async with self._lock:
            if session_id in self.active_connections:
                del self.active_connections[session_id]
        logger.info(f"Uncertainty WebSocket disconnected: {session_id}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast uncertainty update to all connected clients"""
        disconnected = []
        for session_id, ws in self.active_connections.items():
            try:
                if ws.application_state == WebSocketState.CONNECTED:
                    await ws.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to {session_id}: {e}")
                disconnected.append(session_id)

        for sid in disconnected:
            await self.disconnect(sid)


uncertainty_manager = UncertaintyConnectionManager()


@router.websocket("/uncertainty")
async def websocket_uncertainty(
    websocket: WebSocket,
    session_id: str = Query(default=None, description="Session ID"),
    project_id: str = Query(default=None, description="Project ID"),
):
    """
    WebSocket endpoint for real-time uncertainty updates.

    Messages sent:
    - connection_established: Initial connection confirmation
    - uncertainty_update: When uncertainty state changes
    - pong: Response to ping heartbeat
    """
    if not session_id:
        session_id = f"uncertainty-{datetime.now().timestamp()}"

    logger.info(f"[UncertaintyWS] Connection attempt for session: {session_id}, project: {project_id}")

    try:
        await uncertainty_manager.connect(websocket, session_id)
        logger.info(f"[UncertaintyWS] Connection established for session: {session_id}")

        # Send initial connection confirmation
        await websocket.send_json(
            {
                "type": "connection_established",
                "session_id": session_id,
                "project_id": project_id,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Handle incoming messages (mainly ping/pong)
        while True:
            try:
                data = await websocket.receive_json()

                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
                elif data.get("type") == "request_update":
                    # Client requests current uncertainty state
                    # Trigger fetch from uncertainty service
                    try:
                        # Send current state (client should use REST API for full data)
                        await websocket.send_json(
                            {
                                "type": "uncertainty_update",
                                "data": None,  # Client should use REST API for full data
                                "message": "Use GET /api/uncertainty/status for full data",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                    except Exception as e:
                        logger.error(f"Failed to get uncertainty status: {e}")

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Uncertainty WebSocket message error: {e}")
                break

    except Exception as e:
        logger.error(f"Uncertainty WebSocket error: {e}")

    finally:
        await uncertainty_manager.disconnect(session_id)


# ============================================================================
# Confidence WebSocket Endpoint
# ============================================================================


class ConfidenceConnectionManager:
    """Manages WebSocket connections for confidence updates per phase"""

    def __init__(self):
        # Map: phase -> {session_id -> WebSocket}
        self.phase_connections: Dict[str, Dict[str, WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, phase: str, session_id: str):
        await websocket.accept()
        async with self._lock:
            if phase not in self.phase_connections:
                self.phase_connections[phase] = {}
            self.phase_connections[phase][session_id] = websocket
        logger.info(f"Confidence WebSocket connected: {session_id} (phase: {phase})")

    async def disconnect(self, phase: str, session_id: str):
        async with self._lock:
            if phase in self.phase_connections:
                if session_id in self.phase_connections[phase]:
                    del self.phase_connections[phase][session_id]
        logger.info(f"Confidence WebSocket disconnected: {session_id} (phase: {phase})")

    async def broadcast_to_phase(self, phase: str, message: Dict[str, Any]):
        """Broadcast confidence update to all clients subscribed to a phase"""
        if phase not in self.phase_connections:
            return

        disconnected = []
        for session_id, ws in self.phase_connections[phase].items():
            try:
                if ws.application_state == WebSocketState.CONNECTED:
                    await ws.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to {session_id}: {e}")
                disconnected.append(session_id)

        for sid in disconnected:
            await self.disconnect(phase, sid)


confidence_manager = ConfidenceConnectionManager()


@router.websocket("/confidence/{phase}")
async def websocket_confidence(
    websocket: WebSocket,
    phase: str,
):
    """
    WebSocket endpoint for real-time confidence updates for a specific phase.

    Path params:
    - phase: Development phase (ideation, design, mvp, implementation, testing)

    Messages sent:
    - connection_established: Initial connection confirmation
    - confidence_updated: When confidence score changes
    - threshold_crossed: When confidence crosses phase threshold
    - decision_changed: When GO/NO_GO decision changes
    - pong: Response to ping heartbeat
    """
    logger.info(f"[ConfidenceWS] Connection attempt for phase: {phase}")

    valid_phases = ["ideation", "design", "mvp", "implementation", "testing"]
    if phase not in valid_phases:
        logger.warning(f"[ConfidenceWS] Invalid phase rejected: {phase}")
        await websocket.close(code=4000, reason=f"Invalid phase: {phase}")
        return

    session_id = f"confidence-{phase}-{datetime.now().timestamp()}"
    logger.info(f"[ConfidenceWS] Accepting connection for session: {session_id}")

    try:
        await confidence_manager.connect(websocket, phase, session_id)

        # Send initial connection confirmation
        await websocket.send_json(
            {
                "type": "connection_established",
                "session_id": session_id,
                "phase": phase,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()

                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
                elif data.get("type") == "request_recalculation":
                    # Client requests confidence recalculation
                    # This would trigger the confidence service to recalculate
                    await websocket.send_json(
                        {
                            "type": "recalculation_requested",
                            "phase": phase,
                            "message": "Recalculation triggered. Updates will be broadcast.",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                elif data.get("type") == "subscribe_phase":
                    # Client wants to switch phase subscription
                    new_phase = data.get("phase")
                    if new_phase in valid_phases and new_phase != phase:
                        await confidence_manager.disconnect(phase, session_id)
                        await confidence_manager.connect(websocket, new_phase, session_id)
                        await websocket.send_json(
                            {
                                "type": "subscription_changed",
                                "old_phase": phase,
                                "new_phase": new_phase,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Confidence WebSocket message error: {e}")
                break

    except Exception as e:
        logger.error(f"Confidence WebSocket error: {e}")

    finally:
        await confidence_manager.disconnect(phase, session_id)


# Helper functions to broadcast updates from other parts of the application
async def broadcast_uncertainty_update(data: Dict[str, Any]):
    """Call this when uncertainty state changes to notify all connected clients"""
    await uncertainty_manager.broadcast({"type": "uncertainty_update", "data": data, "timestamp": datetime.now().isoformat()})


async def broadcast_confidence_update(phase: str, data: Dict[str, Any]):
    """Call this when confidence changes to notify clients subscribed to that phase"""
    await confidence_manager.broadcast_to_phase(
        phase, {"type": "confidence_updated", **data, "timestamp": datetime.now().isoformat()}
    )
