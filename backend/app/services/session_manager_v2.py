"""
Session Manager V2 with Centralized Redis Integration

Enhanced version using the centralized RedisClient for better
distributed locking and event management.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from app.services.redis_client import RedisClient, RedisKeys, get_redis_client
from app.services.session_manager import Conflict, ConflictType, LockType, ResourceLock, Session, SessionStatus

logger = logging.getLogger(__name__)


class SessionManagerV2:
    """
    Enhanced Session Manager using centralized Redis client
    """

    def __init__(self):
        self.redis_client: Optional[RedisClient] = None
        self.local_sessions: Dict[str, Session] = {}
        self.event_handlers = {}
        self._initialized = False
        self._event_listener_task = None

    async def initialize(self):
        """Initialize with Redis client"""
        if self._initialized:
            return

        try:
            # Get centralized Redis client
            self.redis_client = await get_redis_client()

            if await self.redis_client.ensure_connected():
                # Start event listener
                self._event_listener_task = asyncio.create_task(self._start_event_listener())

                self._initialized = True
                logger.info("[OK] SessionManagerV2 initialized with centralized Redis")
            else:
                logger.warning("[WARN] Redis not available, using in-memory mode")
                self.redis_client = None
                self._initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize SessionManagerV2: {e}")
            self.redis_client = None
            self._initialized = True

    async def create_session(
        self,
        terminal_id: str,
        user_id: str = "default",
        project_id: Optional[str] = None,
        working_directory: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> Session:
        """Create a new session with improved tracking"""

        session_id = f"{terminal_id}_{uuid4().hex[:8]}_{int(datetime.now().timestamp())}"

        # Check if should be primary
        is_primary = await self._should_be_primary(project_id) if project_id else False

        session = Session(
            id=session_id,
            terminal_id=terminal_id,
            project_id=project_id,
            user_id=user_id,
            status=SessionStatus.ACTIVE,
            started_at=datetime.now(),
            last_active=datetime.now(),
            is_primary=is_primary,
            locks=[],
            current_branch=None,
            working_directory=working_directory,
            env_vars=env_vars or {},
        )

        # Store locally
        self.local_sessions[session_id] = session

        # Store in Redis
        if self.redis_client:
            await self.redis_client.register_session(session_id, session.to_dict(), ttl=86400)  # 24 hours

            # Add to project sessions if applicable
            if project_id:
                project_sessions_key = RedisKeys.PROJECT_SESSIONS.format(project_id)
                await self.redis_client._client.sadd(project_sessions_key, session_id)

            # Broadcast event
            await self.redis_client.publish(
                RedisKeys.CHANNEL_SESSION,
                {
                    "type": "session_created",
                    "session_id": session_id,
                    "project_id": project_id,
                    "is_primary": is_primary,
                    "terminal_id": terminal_id,
                },
            )

        logger.info(f"[SESSION] created: {session_id} (Primary: {is_primary})")
        return session

    async def acquire_lock(
        self,
        session_id: str,
        resource_id: str,
        lock_type: LockType = LockType.FILE,
        timeout: int = 300,
        wait: bool = False,
        metadata: Optional[Dict] = None,
    ) -> Optional[ResourceLock]:
        """Acquire lock using centralized Redis client"""

        # Generate lock key
        if lock_type == LockType.FILE:
            lock_key = RedisKeys.FILE_LOCK.format(resource_id)
        elif lock_type == LockType.GIT_BRANCH:
            lock_key = RedisKeys.GIT_LOCK.format(resource_id)
        else:
            lock_key = RedisKeys.RESOURCE_LOCK.format(f"{lock_type.value}:{resource_id}")

        # Try to acquire lock
        if self.redis_client:
            success = await self.redis_client.acquire_lock(
                key=lock_key,
                value=session_id,
                ttl=timeout,
                blocking=wait,
                blocking_timeout=30 if wait else 0,
            )

            if not success:
                # Check who holds the lock
                holder = await self.redis_client.get_lock_holder(lock_key)

                if holder and holder != session_id:
                    # Conflict detected
                    await self._record_conflict(ConflictType.RESOURCE_LOCK, [session_id, holder], resource_id)

                    logger.warning(f"[LOCK] conflict: {resource_id} held by {holder}")

                return None

            # Create lock object
            lock = ResourceLock(
                resource_id=resource_id,
                lock_type=lock_type,
                session_id=session_id,
                acquired_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=timeout),
                metadata=metadata or {},
            )

            # Track lock in session
            locks_key = RedisKeys.SESSION_LOCKS.format(session_id)
            await self.redis_client._client.sadd(locks_key, lock_key)

            # Broadcast lock acquisition
            await self.redis_client.publish(
                (
                    RedisKeys.CHANNEL_PROJECT.format(self.local_sessions[session_id].project_id)
                    if session_id in self.local_sessions and self.local_sessions[session_id].project_id
                    else RedisKeys.CHANNEL_BROADCAST
                ),
                {
                    "type": "lock_acquired",
                    "session_id": session_id,
                    "resource": resource_id,
                    "lock_type": lock_type.value,
                },
            )

            logger.info(f"[OK] Lock acquired: {resource_id} by {session_id}")
            return lock

        else:
            # Fallback to in-memory locking
            # (simplified version for when Redis is not available)
            lock = ResourceLock(
                resource_id=resource_id,
                lock_type=lock_type,
                session_id=session_id,
                acquired_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=timeout),
                metadata=metadata or {},
            )

            return lock

    async def release_lock(self, session_id: str, resource_id: str, lock_type: LockType = LockType.FILE) -> bool:
        """Release lock using centralized Redis client"""

        # Generate lock key
        if lock_type == LockType.FILE:
            lock_key = RedisKeys.FILE_LOCK.format(resource_id)
        elif lock_type == LockType.GIT_BRANCH:
            lock_key = RedisKeys.GIT_LOCK.format(resource_id)
        else:
            lock_key = RedisKeys.RESOURCE_LOCK.format(f"{lock_type.value}:{resource_id}")

        if self.redis_client:
            success = await self.redis_client.release_lock(lock_key, session_id)

            if success:
                # Remove from session locks
                locks_key = RedisKeys.SESSION_LOCKS.format(session_id)
                await self.redis_client._client.srem(locks_key, lock_key)

                # Broadcast lock release
                await self.redis_client.publish(
                    (
                        RedisKeys.CHANNEL_PROJECT.format(self.local_sessions[session_id].project_id)
                        if session_id in self.local_sessions and self.local_sessions[session_id].project_id
                        else RedisKeys.CHANNEL_BROADCAST
                    ),
                    {
                        "type": "lock_released",
                        "session_id": session_id,
                        "resource": resource_id,
                        "lock_type": lock_type.value,
                    },
                )

                logger.info(f"[LOCK] released: {resource_id} by {session_id}")

            return success

        return True  # In-memory mode always succeeds

    async def detect_conflict(self, session_id: str, operation: str, resource: str) -> Optional[Conflict]:
        """Detect potential conflicts for an operation"""

        _ = []  # conflicts list placeholder for future use

        # Check for file edit conflicts
        if operation == "file_edit":
            # Check if another session has lock on the file
            lock_key = RedisKeys.FILE_LOCK.format(resource)

            if self.redis_client:
                holder = await self.redis_client.get_lock_holder(lock_key)

                if holder and holder != session_id:
                    conflict = Conflict(
                        id=f"conflict_{uuid4().hex[:8]}",
                        type=ConflictType.FILE_EDIT,
                        sessions=[session_id, holder],
                        resource=resource,
                        detected_at=datetime.now(),
                        resolution_strategy="wait_or_merge",
                        resolved=False,
                        resolution_metadata=None,
                    )

                    await self._record_conflict(ConflictType.FILE_EDIT, [session_id, holder], resource)

                    return conflict

        # Check for git conflicts
        elif operation == "git_operation":
            branch_lock_key = RedisKeys.GIT_LOCK.format(resource)

            if self.redis_client:
                holder = await self.redis_client.get_lock_holder(branch_lock_key)

                if holder and holder != session_id:
                    conflict = Conflict(
                        id=f"conflict_{uuid4().hex[:8]}",
                        type=ConflictType.GIT_MERGE,
                        sessions=[session_id, holder],
                        resource=resource,
                        detected_at=datetime.now(),
                        resolution_strategy="coordinate_push",
                        resolved=False,
                        resolution_metadata=None,
                    )

                    await self._record_conflict(ConflictType.GIT_MERGE, [session_id, holder], resource)

                    return conflict

        return None

    async def resolve_conflict(self, conflict_id: str, resolution: str, metadata: Optional[Dict] = None) -> bool:
        """Resolve a conflict"""

        if self.redis_client:
            # Get conflict from Redis
            conflicts = await self.redis_client.get_project_conflicts(
                self.local_sessions[list(self.local_sessions.keys())[0]].project_id if self.local_sessions else "default"
            )

            for conflict_data in conflicts:
                if conflict_data.get("id") == conflict_id:
                    # Mark as resolved
                    await self.redis_client.resolve_conflict(conflict_data.get("project_id", "default"), conflict_id)

                    logger.info(f"[OK] Conflict resolved: {conflict_id}")
                    return True

        return False

    async def get_active_sessions(self, project_id: Optional[str] = None) -> List[Session]:
        """Get all active sessions, optionally filtered by project"""

        sessions = []

        if self.redis_client:
            active_session_ids = await self.redis_client.get_active_sessions()

            for session_id in active_session_ids:
                session_data = await self._get_session_data(session_id)

                if session_data:
                    session = Session.from_dict(session_data)

                    if project_id is None or session.project_id == project_id:
                        sessions.append(session)
        else:
            # Use local sessions
            for session in self.local_sessions.values():
                if project_id is None or session.project_id == project_id:
                    sessions.append(session)

        return sessions

    async def terminate_session(self, session_id: str) -> bool:
        """Terminate a session and cleanup resources"""

        if session_id not in self.local_sessions:
            return False

        session = self.local_sessions[session_id]

        # Release all locks held by session
        if self.redis_client:
            locks_key = RedisKeys.SESSION_LOCKS.format(session_id)
            lock_keys = await self.redis_client._client.smembers(locks_key)

            for lock_key in lock_keys:
                await self.redis_client.release_lock(lock_key, session_id)

            # Remove session from Redis
            await self.redis_client.remove_session(session_id)

            # Remove from project sessions
            if session.project_id:
                project_sessions_key = RedisKeys.PROJECT_SESSIONS.format(session.project_id)
                await self.redis_client._client.srem(project_sessions_key, session_id)

            # Broadcast termination
            await self.redis_client.publish(
                RedisKeys.CHANNEL_SESSION,
                {
                    "type": "session_terminated",
                    "session_id": session_id,
                    "project_id": session.project_id,
                },
            )

        # Remove locally
        del self.local_sessions[session_id]

        logger.info(f"[SESSION] terminated: {session_id}")
        return True

    async def heartbeat(self, session_id: str) -> bool:
        """Update session heartbeat"""

        if session_id in self.local_sessions:
            self.local_sessions[session_id].last_active = datetime.now()

            if self.redis_client:
                await self.redis_client.update_session_heartbeat(session_id)

            return True

        return False

    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed session information"""

        if session_id in self.local_sessions:
            return self.local_sessions[session_id].to_dict()

        if self.redis_client:
            session_key = RedisKeys.SESSION_DATA.format(session_id)
            session_data = await self.redis_client._client.get(session_key)

            if session_data:
                return json.loads(session_data)

        return None

    async def coordinate_operation(
        self, session_id: str, operation: str, resource: str, timeout: int = 60
    ) -> Tuple[bool, Optional[str]]:
        """
        Coordinate an operation across sessions

        Returns:
            (success, error_message)
        """

        # First check for conflicts
        conflict = await self.detect_conflict(session_id, operation, resource)

        if conflict:
            return False, f"Conflict detected: {conflict.type.value} on {resource}"

        # Try to acquire necessary locks
        lock_type = LockType.FILE if operation == "file_edit" else LockType.GIT_BRANCH

        lock = await self.acquire_lock(session_id, resource, lock_type, timeout=timeout, wait=False)

        if not lock:
            return False, f"Could not acquire lock for {resource}"

        return True, None

    # Private methods

    async def _should_be_primary(self, project_id: str) -> bool:
        """Determine if session should be primary for project"""

        if not self.redis_client:
            return True  # First session is always primary in memory mode

        # Check existing sessions for project
        project_sessions_key = RedisKeys.PROJECT_SESSIONS.format(project_id)
        existing_sessions = await self.redis_client._client.smembers(project_sessions_key)

        # First session for project becomes primary
        return len(existing_sessions) == 0

    async def _record_conflict(self, conflict_type: ConflictType, sessions: List[str], resource: str):
        """Record a conflict in Redis"""

        if not self.redis_client:
            return

        conflict_data = {
            "id": f"conflict_{uuid4().hex[:8]}",
            "type": conflict_type.value,
            "sessions": sessions,
            "resource": resource,
            "detected_at": datetime.now().isoformat(),
            "resolved": False,
        }

        # Get project_id from first session
        project_id = None
        for session_id in sessions:
            if session_id in self.local_sessions:
                project_id = self.local_sessions[session_id].project_id
                break

        if project_id:
            await self.redis_client.register_conflict(project_id, conflict_data)

    async def _get_session_data(self, session_id: str) -> Optional[Dict]:
        """Get session data from Redis"""

        if not self.redis_client:
            return None

        session_key = RedisKeys.SESSION_DATA.format(session_id)
        data = await self.redis_client._client.get(session_key)

        if data:
            return json.loads(data)

        return None

    async def _start_event_listener(self):
        """Start listening for Redis events"""

        if not self.redis_client:
            return

        channels = [
            RedisKeys.CHANNEL_SESSION,
            RedisKeys.CHANNEL_CONFLICTS,
            RedisKeys.CHANNEL_BROADCAST,
        ]

        pubsub = await self.redis_client.subscribe(channels)

        if pubsub:
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        await self._handle_event(message)
            except Exception as e:
                logger.error(f"Event listener error: {e}")

    async def _handle_event(self, message: Dict):
        """Handle incoming Redis events"""

        try:
            data = json.loads(message["data"])
            event_type = data.get("type")

            if event_type in self.event_handlers:
                await self.event_handlers[event_type](data)

            logger.debug(f"[EVENT] received: {event_type}")

        except Exception as e:
            logger.error(f"Error handling event: {e}")

    def register_event_handler(self, event_type: str, handler):
        """Register handler for specific event types"""
        self.event_handlers[event_type] = handler

    async def cleanup(self):
        """Cleanup resources on shutdown"""

        # Terminate all local sessions
        for session_id in list(self.local_sessions.keys()):
            await self.terminate_session(session_id)

        # Cancel event listener
        if self._event_listener_task:
            self._event_listener_task.cancel()

        logger.info("[OK] SessionManagerV2 cleaned up")


# Singleton instance
_session_manager: Optional[SessionManagerV2] = None


async def get_session_manager() -> SessionManagerV2:
    """Get or create SessionManagerV2 singleton"""
    global _session_manager

    if _session_manager is None:
        _session_manager = SessionManagerV2()
        await _session_manager.initialize()

    return _session_manager
