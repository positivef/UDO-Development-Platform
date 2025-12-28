"""
Kanban WebSocket Handler for Real-time Task Updates

Provides real-time task synchronization for Kanban board:
- Task creation/update/delete/archive events
- Multi-user collaboration
- Optimistic update confirmation
- Project-based broadcasting
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Set
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

# P0-2: JWT authentication for WebSocket
from app.core.security import JWTManager, UserRole, get_current_user, require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws/kanban", tags=["kanban-websocket"])


class KanbanConnectionManager:
    """
    Manages WebSocket connections for Kanban board users
    """

    def __init__(self):
        # Map client_id to websocket connection
        self.active_connections: Dict[str, WebSocket] = {}
        # Map project_id to set of client_ids
        self.project_clients: Dict[str, Set[str]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        project_id: str,
        user_email: str,
        user_id: str,
    ):
        """
        Accept and register new WebSocket connection

        Args:
            websocket: WebSocket connection
            client_id: Client identifier
            project_id: Project identifier
            user_email: Authenticated user email (from JWT)
            user_id: Authenticated user ID (from JWT)
        """
        await websocket.accept()

        async with self._lock:
            self.active_connections[client_id] = websocket

            if project_id not in self.project_clients:
                self.project_clients[project_id] = set()
            self.project_clients[project_id].add(client_id)

        logger.info(
            f"Kanban WebSocket connected: client={client_id}, user={user_email}, project={project_id}"
        )

        # Send connection confirmation
        await self.send_to_client(
            {
                "type": "connection_established",
                "client_id": client_id,
                "project_id": project_id,
                "user_email": user_email,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
            },
            client_id,
        )

    async def disconnect(self, client_id: str, project_id: Optional[str] = None):
        """Remove WebSocket connection"""
        async with self._lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]

            # Remove from project clients
            if project_id and project_id in self.project_clients:
                self.project_clients[project_id].discard(client_id)

        logger.info(f"Kanban WebSocket disconnected: client={client_id}")

    async def send_to_client(self, message: Dict[str, Any], client_id: str) -> bool:
        """Send message to specific client"""
        websocket = self.active_connections.get(client_id)
        if websocket:
            try:
                # [WARN] CRITICAL: Use client_state (NOT application_state)
                # Starlette WebSocket uses client_state for connection tracking
                # See: docs/guides/ERROR_PREVENTION_GUIDE.md#websocket-state-checking
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
                    return True
                else:
                    logger.warning(
                        f"WebSocket not connected for {client_id}: state={websocket.client_state}"
                    )
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                await self.disconnect(client_id)
        return False

    async def broadcast_to_project(
        self,
        message: Dict[str, Any],
        project_id: str,
        exclude_client: Optional[str] = None,
    ):
        """Broadcast message to all clients in a project"""
        clients = self.project_clients.get(project_id, set()).copy()

        for client_id in clients:
            if client_id != exclude_client:
                await self.send_to_client(message, client_id)

    def get_project_client_count(self, project_id: str) -> int:
        """Get number of active clients for a project"""
        return len(self.project_clients.get(project_id, set()))


# Global connection manager for Kanban
kanban_manager = KanbanConnectionManager()


@router.websocket("/projects/{project_id}")
async def kanban_websocket_endpoint(
    websocket: WebSocket,
    project_id: str,
    token: Optional[str] = Query(None, description="JWT access token"),
    client_id: Optional[str] = Query(
        None, description="Client ID (auto-generated if not provided)"
    ),
):
    """
    WebSocket endpoint for Kanban real-time updates

    **Security (P0-2)**: JWT authentication required via query parameter.

    Path params:
    - project_id: Project ID for task filtering

    Query params:
    - token: JWT access token (REQUIRED)
    - client_id: Optional client identifier (UUID generated if not provided)

    Authentication:
    - WebSocket connections require valid JWT token in query parameter
    - Token is validated before accepting connection
    - Invalid/expired tokens result in 1008 Policy Violation close

    Message types (client -> server):
    - ping: Heartbeat check
    - task_created: New task created (broadcast to all)
    - task_updated: Task updated (broadcast to all)
    - task_moved: Task status changed (broadcast to all)
    - task_deleted: Task deleted (broadcast to all)
    - task_archived: Task archived (broadcast to all)

    Message types (server -> client):
    - connection_established: Connection confirmed (includes user info)
    - pong: Heartbeat response
    - task_created: New task notification
    - task_updated: Task update notification
    - task_moved: Task move notification
    - task_deleted: Task deletion notification
    - task_archived: Task archive notification
    - client_joined: Another client joined project
    - client_left: Another client left project
    """
    # Generate client_id if not provided
    if not client_id:
        client_id = str(uuid4())

    try:
        # P0-2: Validate JWT token
        if not token:
             if os.environ.get("ENVIRONMENT") == "development":
                 token = "dev-token" # Use dummy token to trigger dev bypass in security.py
                 logger.warning("[DEV] No token provided for WebSocket, using dev-token")
             else:
                 await websocket.close(code=1008, reason="Missing authentication token")
                 return

        try:
            payload = await JWTManager.decode_token_async(token, check_blacklist=True)
            user_email = payload.get("sub")
            user_id = payload.get("user_id")

            if not user_email or not user_id:
                logger.warning(f"WebSocket auth failed: invalid token payload for client {client_id}")
                await websocket.close(code=1008, reason="Invalid token payload")
                return

        except Exception as e:
            logger.warning(f"WebSocket auth failed: {e} for client {client_id}")
            await websocket.close(code=1008, reason="Authentication failed")
            return

        # Connect WebSocket with authenticated user info
        await kanban_manager.connect(websocket, client_id, project_id, user_email, user_id)

        # Notify other clients about new connection
        await kanban_manager.broadcast_to_project(
            {
                "type": "client_joined",
                "client_id": client_id,
                "project_id": project_id,
                "active_clients": kanban_manager.get_project_client_count(project_id),
                "timestamp": datetime.now().isoformat(),
            },
            project_id,
            exclude_client=client_id,
        )

        # Handle incoming messages
        try:
            while True:
                data = await websocket.receive_json()

                await process_kanban_message(data, client_id, project_id)
        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"WebSocket message error: {e}")

    except Exception as e:
        logger.error(f"Kanban WebSocket error for client {client_id}: {e}")

    finally:
        # Cleanup
        await kanban_manager.disconnect(client_id, project_id)

        # Notify other clients about disconnection
        await kanban_manager.broadcast_to_project(
            {
                "type": "client_left",
                "client_id": client_id,
                "project_id": project_id,
                "active_clients": kanban_manager.get_project_client_count(project_id),
                "timestamp": datetime.now().isoformat(),
            },
            project_id,
        )


async def process_kanban_message(data: Dict[str, Any], client_id: str, project_id: str):
    """
    Process incoming Kanban WebSocket messages
    """
    message_type = data.get("type")

    if message_type == "ping":
        # Simple heartbeat response
        await kanban_manager.send_to_client(
            {"type": "pong", "timestamp": datetime.now().isoformat()}, client_id
        )

    elif message_type == "task_created":
        # Broadcast new task to all clients in project
        task_data = data.get("task")

        await kanban_manager.broadcast_to_project(
            {
                "type": "task_created",
                "task": task_data,
                "created_by": client_id,
                "timestamp": datetime.now().isoformat(),
            },
            project_id,
            exclude_client=client_id,  # Don't send back to creator
        )

    elif message_type == "task_updated":
        # Broadcast task update to all clients
        task_id = data.get("task_id")
        updates = data.get("updates")

        await kanban_manager.broadcast_to_project(
            {
                "type": "task_updated",
                "task_id": task_id,
                "updates": updates,
                "updated_by": client_id,
                "timestamp": datetime.now().isoformat(),
            },
            project_id,
            exclude_client=client_id,
        )

    elif message_type == "task_moved":
        # Broadcast task status change (drag & drop)
        task_id = data.get("task_id")
        old_status = data.get("old_status")
        new_status = data.get("new_status")

        await kanban_manager.broadcast_to_project(
            {
                "type": "task_moved",
                "task_id": task_id,
                "old_status": old_status,
                "new_status": new_status,
                "moved_by": client_id,
                "timestamp": datetime.now().isoformat(),
            },
            project_id,
            exclude_client=client_id,
        )

    elif message_type == "task_deleted":
        # Broadcast task deletion
        task_id = data.get("task_id")

        await kanban_manager.broadcast_to_project(
            {
                "type": "task_deleted",
                "task_id": task_id,
                "deleted_by": client_id,
                "timestamp": datetime.now().isoformat(),
            },
            project_id,
            exclude_client=client_id,
        )

    elif message_type == "task_archived":
        # Broadcast task archiving
        task_id = data.get("task_id")

        await kanban_manager.broadcast_to_project(
            {
                "type": "task_archived",
                "task_id": task_id,
                "archived_by": client_id,
                "timestamp": datetime.now().isoformat(),
            },
            project_id,
            exclude_client=client_id,
        )

    else:
        logger.warning(f"Unknown message type: {message_type}")


@router.get(
    "/projects/{project_id}/clients",
    dependencies=[Depends(require_role(UserRole.VIEWER))],
)
async def get_active_clients(
    project_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Get number of active clients for a project

    **RBAC**: Requires `viewer` role or higher.
    **Security (P0-2)**: JWT authentication required.
    """
    count = kanban_manager.get_project_client_count(project_id)
    return {
        "project_id": project_id,
        "active_clients": count,
        "timestamp": datetime.now().isoformat(),
    }
