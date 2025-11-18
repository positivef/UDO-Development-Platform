"""
Multi-Session Manager for UDO Platform
Handles concurrent terminal sessions, conflict resolution, and distributed locking
"""

import json
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from uuid import uuid4
from enum import Enum
import redis.asyncio as redis
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Session status types"""
    ACTIVE = "active"
    IDLE = "idle"
    LOCKED = "locked"
    WAITING = "waiting"
    TERMINATED = "terminated"


class LockType(Enum):
    """Lock types for different resources"""
    FILE = "file"
    PROJECT = "project"
    GIT_BRANCH = "git_branch"
    DATABASE = "database"
    EXCLUSIVE = "exclusive"


class ConflictType(Enum):
    """Types of conflicts that can occur"""
    FILE_EDIT = "file_edit"
    GIT_MERGE = "git_merge"
    CONTEXT_SWITCH = "context_switch"
    RESOURCE_LOCK = "resource_lock"
    STATE_DIVERGENCE = "state_divergence"


@dataclass
class Session:
    """Session data structure"""
    id: str
    terminal_id: str
    project_id: Optional[str]
    user_id: str
    status: SessionStatus
    started_at: datetime
    last_active: datetime
    is_primary: bool
    locks: List[Dict[str, Any]]
    current_branch: Optional[str]
    working_directory: Optional[str]
    env_vars: Dict[str, str]

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['status'] = self.status.value
        data['started_at'] = self.started_at.isoformat()
        data['last_active'] = self.last_active.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Session':
        """Create from dictionary"""
        data['status'] = SessionStatus(data['status'])
        data['started_at'] = datetime.fromisoformat(data['started_at'])
        data['last_active'] = datetime.fromisoformat(data['last_active'])
        return cls(**data)


@dataclass
class ResourceLock:
    """Resource lock information"""
    resource_id: str
    lock_type: LockType
    session_id: str
    acquired_at: datetime
    expires_at: datetime
    metadata: Dict[str, Any]

    def is_expired(self) -> bool:
        """Check if lock has expired"""
        return datetime.now() > self.expires_at


@dataclass
class Conflict:
    """Conflict information"""
    id: str
    type: ConflictType
    sessions: List[str]
    resource: str
    detected_at: datetime
    resolution_strategy: Optional[str]
    resolved: bool
    resolution_metadata: Optional[Dict[str, Any]]


class SessionManager:
    """
    Manages multiple concurrent sessions with conflict resolution
    and distributed locking capabilities
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.local_sessions: Dict[str, Session] = {}
        self.locks: Dict[str, ResourceLock] = {}
        self.conflicts: List[Conflict] = []
        self.pubsub: Optional[redis.client.PubSub] = None
        self._event_handlers = {}
        self._initialized = False

    async def initialize(self):
        """Initialize Redis connection and pubsub"""
        if self._initialized:
            return

        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )

            # Test connection
            await self.redis_client.ping()

            # Setup pubsub for event broadcasting
            self.pubsub = self.redis_client.pubsub()

            # Start listening for events
            asyncio.create_task(self._event_listener())

            self._initialized = True
            logger.info("✅ SessionManager initialized with Redis")

        except Exception as e:
            logger.warning(f"⚠️ Redis not available, using in-memory mode: {e}")
            self._initialized = True

    async def create_session(
        self,
        terminal_id: str,
        user_id: str = "default",
        project_id: Optional[str] = None,
        working_directory: Optional[str] = None
    ) -> Session:
        """Create a new session for a terminal"""

        session_id = f"{terminal_id}_{uuid4().hex[:8]}_{int(datetime.now().timestamp())}"

        # Check if this should be primary session
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
            env_vars={}
        )

        # Store locally
        self.local_sessions[session_id] = session

        # Store in Redis if available
        if self.redis_client:
            await self.redis_client.hset(
                "sessions",
                session_id,
                json.dumps(session.to_dict())
            )

            # Set expiry (24 hours)
            await self.redis_client.expire(f"session:{session_id}", 86400)

            # Broadcast session creation
            await self._broadcast_event("session_created", {
                "session_id": session_id,
                "project_id": project_id,
                "is_primary": is_primary
            })

        logger.info(f"📌 Session created: {session_id} (Primary: {is_primary})")
        return session

    async def acquire_lock(
        self,
        session_id: str,
        resource_id: str,
        lock_type: LockType = LockType.FILE,
        timeout: int = 300,  # 5 minutes default
        wait: bool = False,
        metadata: Optional[Dict] = None
    ) -> Optional[ResourceLock]:
        """
        Acquire a lock on a resource

        Args:
            session_id: Session requesting the lock
            resource_id: Resource to lock (file path, project id, etc.)
            lock_type: Type of lock
            timeout: Lock timeout in seconds
            wait: Whether to wait for lock if not available
            metadata: Additional lock metadata

        Returns:
            ResourceLock if acquired, None otherwise
        """

        lock_key = f"lock:{lock_type.value}:{resource_id}"

        # Check for existing lock
        existing_lock = await self._get_existing_lock(lock_key)

        if existing_lock and not existing_lock.is_expired():
            if existing_lock.session_id == session_id:
                # Session already has the lock
                return existing_lock

            if not wait:
                # Lock held by another session
                logger.warning(f"🔒 Lock conflict: {resource_id} held by {existing_lock.session_id}")

                # Record conflict
                await self._record_conflict(
                    ConflictType.RESOURCE_LOCK,
                    [session_id, existing_lock.session_id],
                    resource_id
                )

                return None

            # Wait for lock with timeout
            return await self._wait_for_lock(session_id, lock_key, timeout, metadata)

        # Create new lock
        lock = ResourceLock(
            resource_id=resource_id,
            lock_type=lock_type,
            session_id=session_id,
            acquired_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=timeout),
            metadata=metadata or {}
        )

        # Store lock
        if self.redis_client:
            # Use Redis SET with NX (only if not exists) and EX (expiry)
            success = await self.redis_client.set(
                lock_key,
                json.dumps({
                    "session_id": session_id,
                    "acquired_at": lock.acquired_at.isoformat(),
                    "expires_at": lock.expires_at.isoformat(),
                    "metadata": lock.metadata
                }),
                nx=True,
                ex=timeout
            )

            if not success:
                # Race condition - someone else got the lock
                return None

        self.locks[lock_key] = lock

        # Update session locks
        if session_id in self.local_sessions:
            self.local_sessions[session_id].locks.append({
                "resource": resource_id,
                "type": lock_type.value,
                "acquired_at": lock.acquired_at.isoformat()
            })

        # Broadcast lock acquisition
        await self._broadcast_event("lock_acquired", {
            "session_id": session_id,
            "resource": resource_id,
            "lock_type": lock_type.value
        })

        logger.info(f"✅ Lock acquired: {resource_id} by {session_id}")
        return lock

    async def release_lock(
        self,
        session_id: str,
        resource_id: str,
        lock_type: LockType = LockType.FILE
    ) -> bool:
        """Release a lock held by a session"""

        lock_key = f"lock:{lock_type.value}:{resource_id}"

        # Verify session owns the lock
        existing_lock = await self._get_existing_lock(lock_key)

        if not existing_lock or existing_lock.session_id != session_id:
            logger.warning(f"⚠️ Cannot release lock not owned by session: {session_id}")
            return False

        # Release in Redis
        if self.redis_client:
            # Use Lua script for atomic check-and-delete
            lua_script = """
            local lock_data = redis.call('get', KEYS[1])
            if lock_data then
                local lock = cjson.decode(lock_data)
                if lock['session_id'] == ARGV[1] then
                    return redis.call('del', KEYS[1])
                end
            end
            return 0
            """

            result = await self.redis_client.eval(
                lua_script, 1, lock_key, session_id
            )

            if result == 0:
                return False

        # Remove from local storage
        if lock_key in self.locks:
            del self.locks[lock_key]

        # Update session
        if session_id in self.local_sessions:
            session = self.local_sessions[session_id]
            session.locks = [
                l for l in session.locks
                if l['resource'] != resource_id
            ]

        # Broadcast lock release
        await self._broadcast_event("lock_released", {
            "session_id": session_id,
            "resource": resource_id,
            "lock_type": lock_type.value
        })

        logger.info(f"🔓 Lock released: {resource_id} by {session_id}")
        return True

    async def detect_conflicts(
        self,
        session_id: str,
        action: str,
        resource: str
    ) -> List[Conflict]:
        """Detect potential conflicts before an action"""

        conflicts = []
        session = self.local_sessions.get(session_id)

        if not session:
            return conflicts

        # Get all active sessions in the same project
        project_sessions = await self._get_project_sessions(session.project_id)

        for other_session in project_sessions:
            if other_session.id == session_id:
                continue

            # Check for file edit conflicts
            if action == "edit_file" and resource in [
                l['resource'] for l in other_session.locks
                if l['type'] == LockType.FILE.value
            ]:
                conflict = Conflict(
                    id=str(uuid4()),
                    type=ConflictType.FILE_EDIT,
                    sessions=[session_id, other_session.id],
                    resource=resource,
                    detected_at=datetime.now(),
                    resolution_strategy="wait_or_merge",
                    resolved=False,
                    resolution_metadata=None
                )
                conflicts.append(conflict)

            # Check for git branch conflicts
            if action == "git_operation" and session.current_branch == other_session.current_branch:
                conflict = Conflict(
                    id=str(uuid4()),
                    type=ConflictType.GIT_MERGE,
                    sessions=[session_id, other_session.id],
                    resource=session.current_branch or "main",
                    detected_at=datetime.now(),
                    resolution_strategy="coordinate",
                    resolved=False,
                    resolution_metadata=None
                )
                conflicts.append(conflict)

        # Store detected conflicts
        self.conflicts.extend(conflicts)

        # Broadcast conflicts
        for conflict in conflicts:
            await self._broadcast_event("conflict_detected", {
                "conflict_id": conflict.id,
                "type": conflict.type.value,
                "sessions": conflict.sessions,
                "resource": conflict.resource,
                "strategy": conflict.resolution_strategy
            })

        return conflicts

    async def coordinate_sessions(
        self,
        project_id: str,
        coordination_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        Coordinate multiple sessions working on the same project

        Args:
            project_id: Project to coordinate
            coordination_type: 'auto', 'manual', 'ai_assisted'

        Returns:
            Coordination plan
        """

        sessions = await self._get_project_sessions(project_id)

        if len(sessions) <= 1:
            return {"status": "no_coordination_needed"}

        coordination_plan = {
            "project_id": project_id,
            "sessions": [s.id for s in sessions],
            "primary_session": next((s.id for s in sessions if s.is_primary), None),
            "assignments": {},
            "restrictions": {},
            "notifications": []
        }

        if coordination_type == "auto":
            # Auto-assign work areas to avoid conflicts

            # Analyze current locks and activities
            locked_resources = {}
            for session in sessions:
                for lock in session.locks:
                    locked_resources[lock['resource']] = session.id

            # Assign non-conflicting areas
            for session in sessions:
                if session.is_primary:
                    # Primary session has priority
                    coordination_plan["assignments"][session.id] = {
                        "role": "primary",
                        "allowed_areas": ["*"],
                        "priority": 1
                    }
                else:
                    # Secondary sessions get specific areas
                    coordination_plan["assignments"][session.id] = {
                        "role": "secondary",
                        "allowed_areas": self._get_safe_areas(locked_resources, session.id),
                        "priority": 2
                    }

            # Add notifications
            coordination_plan["notifications"] = [
                {
                    "type": "info",
                    "message": f"Auto-coordination active: {len(sessions)} sessions",
                    "sessions": [s.id for s in sessions]
                }
            ]

        elif coordination_type == "ai_assisted":
            # Use ML to predict optimal work distribution
            coordination_plan["ai_recommendations"] = await self._get_ai_coordination(sessions)

        # Broadcast coordination plan
        await self._broadcast_event("coordination_updated", coordination_plan)

        return coordination_plan

    async def handle_session_termination(self, session_id: str):
        """Clean up when a session terminates"""

        session = self.local_sessions.get(session_id)
        if not session:
            return

        # Release all locks held by session
        for lock_info in session.locks[:]:  # Copy list to avoid modification during iteration
            await self.release_lock(
                session_id,
                lock_info['resource'],
                LockType(lock_info['type'])
            )

        # Update session status
        session.status = SessionStatus.TERMINATED

        # If this was primary, promote another session
        if session.is_primary and session.project_id:
            await self._promote_new_primary(session.project_id, exclude=session_id)

        # Remove from Redis
        if self.redis_client:
            await self.redis_client.hdel("sessions", session_id)

        # Remove from local storage
        del self.local_sessions[session_id]

        # Broadcast termination
        await self._broadcast_event("session_terminated", {
            "session_id": session_id,
            "was_primary": session.is_primary
        })

        logger.info(f"🔚 Session terminated: {session_id}")

    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed session status"""

        session = self.local_sessions.get(session_id)
        if not session:
            # Try Redis
            if self.redis_client:
                data = await self.redis_client.hget("sessions", session_id)
                if data:
                    session = Session.from_dict(json.loads(data))
                else:
                    return None
            else:
                return None

        # Get related sessions
        related_sessions = []
        if session.project_id:
            project_sessions = await self._get_project_sessions(session.project_id)
            related_sessions = [
                {
                    "id": s.id,
                    "status": s.status.value,
                    "is_primary": s.is_primary,
                    "locks": len(s.locks)
                }
                for s in project_sessions if s.id != session_id
            ]

        # Get conflicts
        session_conflicts = [
            {
                "id": c.id,
                "type": c.type.value,
                "resource": c.resource,
                "with_session": [s for s in c.sessions if s != session_id][0] if len(c.sessions) > 1 else None,
                "resolved": c.resolved
            }
            for c in self.conflicts if session_id in c.sessions
        ]

        return {
            "session": session.to_dict(),
            "related_sessions": related_sessions,
            "active_locks": session.locks,
            "conflicts": session_conflicts,
            "metrics": {
                "uptime_minutes": (datetime.now() - session.started_at).seconds // 60,
                "idle_minutes": (datetime.now() - session.last_active).seconds // 60
            }
        }

    # Private helper methods

    async def _should_be_primary(self, project_id: str) -> bool:
        """Determine if a new session should be primary"""
        sessions = await self._get_project_sessions(project_id)

        # No existing sessions or no primary session
        has_primary = any(s.is_primary for s in sessions)
        return not has_primary

    async def _get_project_sessions(self, project_id: Optional[str]) -> List[Session]:
        """Get all sessions for a project"""
        if not project_id:
            return []

        sessions = []

        # Check local sessions
        for session in self.local_sessions.values():
            if session.project_id == project_id and session.status == SessionStatus.ACTIVE:
                sessions.append(session)

        # Check Redis if available
        if self.redis_client and not sessions:
            all_sessions = await self.redis_client.hgetall("sessions")
            for session_data in all_sessions.values():
                session = Session.from_dict(json.loads(session_data))
                if session.project_id == project_id and session.status == SessionStatus.ACTIVE:
                    sessions.append(session)

        return sessions

    async def _get_existing_lock(self, lock_key: str) -> Optional[ResourceLock]:
        """Get existing lock information"""

        # Check local storage
        if lock_key in self.locks:
            return self.locks[lock_key]

        # Check Redis
        if self.redis_client:
            lock_data = await self.redis_client.get(lock_key)
            if lock_data:
                data = json.loads(lock_data)
                return ResourceLock(
                    resource_id=lock_key.split(":")[-1],
                    lock_type=LockType(lock_key.split(":")[1]),
                    session_id=data['session_id'],
                    acquired_at=datetime.fromisoformat(data['acquired_at']),
                    expires_at=datetime.fromisoformat(data['expires_at']),
                    metadata=data.get('metadata', {})
                )

        return None

    async def _wait_for_lock(
        self,
        session_id: str,
        lock_key: str,
        timeout: int,
        metadata: Optional[Dict]
    ) -> Optional[ResourceLock]:
        """Wait for a lock to become available"""

        start_time = datetime.now()
        max_wait = timedelta(seconds=timeout)

        while datetime.now() - start_time < max_wait:
            # Check if lock is available
            existing_lock = await self._get_existing_lock(lock_key)

            if not existing_lock or existing_lock.is_expired():
                # Try to acquire
                return await self.acquire_lock(
                    session_id,
                    lock_key.split(":")[-1],
                    LockType(lock_key.split(":")[1]),
                    timeout,
                    wait=False,
                    metadata=metadata
                )

            # Wait before retry
            await asyncio.sleep(1)

        return None

    async def _record_conflict(
        self,
        conflict_type: ConflictType,
        sessions: List[str],
        resource: str
    ):
        """Record a conflict"""

        conflict = Conflict(
            id=str(uuid4()),
            type=conflict_type,
            sessions=sessions,
            resource=resource,
            detected_at=datetime.now(),
            resolution_strategy=None,
            resolved=False,
            resolution_metadata=None
        )

        self.conflicts.append(conflict)

        # Store in Redis if available
        if self.redis_client:
            await self.redis_client.lpush(
                "conflicts",
                json.dumps({
                    "id": conflict.id,
                    "type": conflict.type.value,
                    "sessions": conflict.sessions,
                    "resource": conflict.resource,
                    "detected_at": conflict.detected_at.isoformat(),
                    "resolved": conflict.resolved
                })
            )

            # Keep only last 100 conflicts
            await self.redis_client.ltrim("conflicts", 0, 99)

    async def _promote_new_primary(self, project_id: str, exclude: str):
        """Promote a new primary session when current primary terminates"""

        sessions = await self._get_project_sessions(project_id)
        eligible = [s for s in sessions if s.id != exclude and s.status == SessionStatus.ACTIVE]

        if eligible:
            # Promote the oldest active session
            new_primary = min(eligible, key=lambda s: s.started_at)
            new_primary.is_primary = True

            # Update in Redis
            if self.redis_client:
                await self.redis_client.hset(
                    "sessions",
                    new_primary.id,
                    json.dumps(new_primary.to_dict())
                )

            # Broadcast promotion
            await self._broadcast_event("primary_promoted", {
                "session_id": new_primary.id,
                "project_id": project_id
            })

            logger.info(f"👑 New primary session: {new_primary.id}")

    def _get_safe_areas(self, locked_resources: Dict[str, str], session_id: str) -> List[str]:
        """Get safe work areas for a session to avoid conflicts"""

        # This would be more sophisticated in production
        # For now, return areas not locked by others
        safe_areas = []

        common_areas = [
            "tests/*",
            "docs/*",
            "README.md",
            "package.json",
            "requirements.txt"
        ]

        for area in common_areas:
            if area not in locked_resources or locked_resources[area] == session_id:
                safe_areas.append(area)

        return safe_areas if safe_areas else ["docs/*", "tests/*"]

    async def _get_ai_coordination(self, sessions: List[Session]) -> Dict[str, Any]:
        """Get AI-assisted coordination recommendations"""

        # This would integrate with ML system
        # For now, return basic recommendations
        return {
            "recommended_distribution": {
                sessions[0].id: ["backend/*", "api/*"] if len(sessions) > 0 else [],
                sessions[1].id: ["frontend/*", "components/*"] if len(sessions) > 1 else [],
                sessions[2].id: ["tests/*", "docs/*"] if len(sessions) > 2 else []
            },
            "conflict_probability": 0.25,
            "efficiency_score": 0.85
        }

    async def _broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcast event to all listening sessions"""

        if not self.redis_client:
            return

        message = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        await self.redis_client.publish(
            "udo:events",
            json.dumps(message)
        )

    async def _event_listener(self):
        """Listen for events from other sessions"""

        if not self.pubsub:
            return

        await self.pubsub.subscribe("udo:events")

        try:
            while True:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True)

                if message and message['type'] == 'message':
                    event = json.loads(message['data'])

                    # Call registered event handlers
                    if event['type'] in self._event_handlers:
                        for handler in self._event_handlers[event['type']]:
                            asyncio.create_task(handler(event['data']))

                await asyncio.sleep(0.01)

        except asyncio.CancelledError:
            await self.pubsub.unsubscribe("udo:events")

    def register_event_handler(self, event_type: str, handler):
        """Register an event handler"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)


# Global session manager instance
_session_manager: Optional[SessionManager] = None


async def get_session_manager() -> SessionManager:
    """Get or create the global session manager"""
    global _session_manager

    if not _session_manager:
        _session_manager = SessionManager()
        await _session_manager.initialize()

    return _session_manager