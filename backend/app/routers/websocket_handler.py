"""
WebSocket Handler for Real-time Session Synchronization

Provides real-time communication between multiple terminal sessions:
- Session events broadcasting
- Conflict notifications
- Lock status updates
- Collaborative editing events
"""

import json
import asyncio
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime
from uuid import UUID

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Query,
    status
)
from starlette.websockets import WebSocketState

from app.services.session_manager import SessionManager, get_session_manager
from app.services.redis_client import get_redis_client, RedisKeys

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

    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        project_id: Optional[str] = None
    ):
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

    async def send_personal_message(
        self,
        message: Dict[str, Any],
        session_id: str
    ) -> bool:
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
        exclude_session: Optional[str] = None
    ):
        """Broadcast message to all sessions in a project"""
        sessions = self.project_sessions.get(project_id, set()).copy()

        for session_id in sessions:
            if session_id != exclude_session:
                await self.send_personal_message(message, session_id)

    async def broadcast_to_all(
        self,
        message: Dict[str, Any],
        exclude_session: Optional[str] = None
    ):
        """Broadcast message to all connected sessions"""
        sessions = list(self.active_connections.keys())

        for session_id in sessions:
            if session_id != exclude_session:
                await self.send_personal_message(message, session_id)


# Global connection manager
connection_manager = ConnectionManager()


@router.websocket("/session")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str = Query(..., description="Session ID"),
    project_id: Optional[str] = Query(None, description="Project ID"),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    WebSocket endpoint for session synchronization

    Query params:
    - session_id: Unique session identifier
    - project_id: Optional project ID for project-specific events
    """
    redis_client = None

    try:
        # Connect WebSocket
        await connection_manager.connect(websocket, session_id, project_id)

        # Get Redis client for pub/sub
        redis_client = await get_redis_client()

        # Subscribe to relevant channels
        channels = [
            RedisKeys.CHANNEL_SESSION,
            RedisKeys.CHANNEL_CONFLICTS,
            RedisKeys.CHANNEL_BROADCAST
        ]

        if project_id:
            channels.append(RedisKeys.CHANNEL_PROJECT.format(project_id))

        pubsub = await redis_client.subscribe(channels)

        # Send initial connection success
        await websocket.send_json({
            "type": "connection_established",
            "session_id": session_id,
            "project_id": project_id,
            "timestamp": datetime.now().isoformat()
        })

        # Notify other sessions about new connection
        await connection_manager.broadcast_to_project(
            {
                "type": "session_connected",
                "session_id": session_id,
                "project_id": project_id,
                "timestamp": datetime.now().isoformat()
            },
            project_id,
            exclude_session=session_id
        )

        # Start tasks for handling messages
        tasks = []

        # Task 1: Handle incoming WebSocket messages
        async def handle_websocket_messages():
            try:
                while True:
                    data = await websocket.receive_json()
                    await process_websocket_message(
                        data,
                        session_id,
                        project_id,
                        session_manager
                    )
            except WebSocketDisconnect:
                pass
            except Exception as e:
                logger.error(f"WebSocket message handler error: {e}")

        # Task 2: Handle Redis pub/sub messages
        async def handle_redis_messages():
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
                    await websocket.send_json({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat()
                    })

                    # Update session heartbeat in Redis
                    if redis_client:
                        await redis_client.update_session_heartbeat(session_id)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

        # Start all tasks
        tasks = [
            asyncio.create_task(handle_websocket_messages()),
            asyncio.create_task(handle_redis_messages()),
            asyncio.create_task(send_heartbeat())
        ]

        # Wait for any task to complete (usually disconnect)
        done, pending = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED
        )

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
                    "timestamp": datetime.now().isoformat()
                },
                project_id
            )

        # Cleanup Redis subscriptions
        if pubsub:
            await pubsub.close()


async def process_websocket_message(
    data: Dict[str, Any],
    session_id: str,
    project_id: Optional[str],
    session_manager: SessionManager
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
        lock = await session_manager.acquire_lock(
            session_id=session_id,
            resource_id=resource_id,
            lock_type=lock_type
        )

        if lock:
            # Notify all sessions about lock acquisition
            await redis_client.publish(
                RedisKeys.CHANNEL_PROJECT.format(project_id),
                {
                    "type": "lock_acquired",
                    "session_id": session_id,
                    "resource_id": resource_id,
                    "lock_type": lock_type,
                    "timestamp": datetime.now().isoformat()
                }
            )
        else:
            # Get lock holder info
            holder = await session_manager.get_lock_holder(resource_id)
            await connection_manager.send_personal_message(
                {
                    "type": "lock_denied",
                    "resource_id": resource_id,
                    "holder": holder,
                    "timestamp": datetime.now().isoformat()
                },
                session_id
            )

    elif message_type == "lock_release":
        # Handle lock release
        resource_id = data.get("resource_id")

        success = await session_manager.release_lock(
            session_id=session_id,
            resource_id=resource_id
        )

        if success:
            # Notify all sessions about lock release
            await redis_client.publish(
                RedisKeys.CHANNEL_PROJECT.format(project_id),
                {
                    "type": "lock_released",
                    "session_id": session_id,
                    "resource_id": resource_id,
                    "timestamp": datetime.now().isoformat()
                }
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
                "timestamp": datetime.now().isoformat()
            }
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
                "timestamp": datetime.now().isoformat()
            },
            project_id,
            exclude_session=session_id
        )

    elif message_type == "conflict_detected":
        # Handle conflict detection
        conflict_data = {
            "id": f"{session_id}_{datetime.now().timestamp()}",
            "session_id": session_id,
            "resource_id": data.get("resource_id"),
            "conflict_type": data.get("conflict_type"),
            "details": data.get("details"),
            "timestamp": datetime.now().isoformat()
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
                "timestamp": datetime.now().isoformat()
            }
        )

    elif message_type == "broadcast":
        # General broadcast message
        await connection_manager.broadcast_to_project(
            {
                **data.get("payload", {}),
                "from_session": session_id,
                "timestamp": datetime.now().isoformat()
            },
            project_id,
            exclude_session=session_id
        )


@router.get("/sessions/active")
async def get_active_sessions(
    project_id: Optional[str] = Query(None, description="Filter by project"),
    session_manager: SessionManager = Depends(get_session_manager)
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
async def get_conflicts(
    project_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Get all conflicts for a project"""
    redis_client = await get_redis_client()
    conflicts = await redis_client.get_project_conflicts(project_id)

    return {
        "project_id": project_id,
        "conflicts": conflicts,
        "count": len(conflicts)
    }