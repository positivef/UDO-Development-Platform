"""
Redis Client for Distributed Session Management

Provides Redis connection management and operations for:
- Distributed locking
- Session state management
- Event pub/sub
- Cache operations
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
from redis.asyncio.client import PubSub

logger = logging.getLogger(__name__)


class RedisConfig:
    """Redis connection configuration"""

    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", "6379"))
        self.db = int(os.getenv("REDIS_DB", "0"))
        self.password = os.getenv("REDIS_PASSWORD", None)
        self.decode_responses = True
        self.socket_timeout = 5
        self.socket_connect_timeout = 5
        self.connection_pool_kwargs = {
            "max_connections": 50,
            "retry_on_timeout": True,
            "retry_on_error": [redis.ConnectionError, redis.TimeoutError],
        }

    def get_url(self) -> str:
        """Get Redis connection URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class RedisKeys:
    """Centralized Redis key patterns"""

    # Lock keys
    LOCK_PREFIX = "udo:lock:"
    FILE_LOCK = "udo:lock:file:{}"
    GIT_LOCK = "udo:lock:git:{}"
    RESOURCE_LOCK = "udo:lock:resource:{}"

    # Session keys
    SESSION_PREFIX = "udo:session:"
    SESSION_DATA = "udo:session:{}:data"
    SESSION_HEARTBEAT = "udo:session:{}:heartbeat"
    SESSION_LOCKS = "udo:session:{}:locks"
    ACTIVE_SESSIONS = "udo:sessions:active"

    # Project keys
    PROJECT_PREFIX = "udo:project:"
    PROJECT_SESSIONS = "udo:project:{}:sessions"
    PROJECT_STATE = "udo:project:{}:state"
    PROJECT_CONFLICTS = "udo:project:{}:conflicts"

    # Event channels
    CHANNEL_PREFIX = "udo:channel:"
    CHANNEL_SESSION = "udo:channel:session"
    CHANNEL_PROJECT = "udo:channel:project:{}"
    CHANNEL_CONFLICTS = "udo:channel:conflicts"
    CHANNEL_BROADCAST = "udo:channel:broadcast"


class RedisClient:
    """
    Async Redis client with connection pooling and retry logic
    """

    def __init__(self, config: Optional[RedisConfig] = None):
        self.config = config or RedisConfig()
        self._client: Optional[redis.Redis] = None
        self._pubsub: Optional[PubSub] = None
        self._connected = False
        self._lock = asyncio.Lock()

    async def connect(self) -> bool:
        """Initialize Redis connection with retry logic"""
        async with self._lock:
            if self._connected:
                return True

            try:
                # Create connection pool
                pool = redis.ConnectionPool.from_url(
                    self.config.get_url(),
                    decode_responses=self.config.decode_responses,
                    **self.config.connection_pool_kwargs,
                )

                # Create client with pool
                self._client = redis.Redis(connection_pool=pool)

                # Test connection
                await self._client.ping()

                # Setup pub/sub
                self._pubsub = self._client.pubsub()

                self._connected = True
                logger.info("Redis connection established")
                return True

            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.error(f"Redis connection failed: {e}")
                self._connected = False
                return False

    async def disconnect(self):
        """Close Redis connection"""
        async with self._lock:
            if self._pubsub:
                await self._pubsub.close()
                self._pubsub = None

            if self._client:
                await self._client.close()
                self._client = None

            self._connected = False
            logger.info("Redis connection closed")

    async def ensure_connected(self) -> bool:
        """Ensure Redis is connected, attempt reconnect if needed"""
        if not self._connected:
            return await self.connect()

        try:
            await self._client.ping()
            return True
        except (redis.ConnectionError, redis.TimeoutError):
            self._connected = False
            return await self.connect()

    # ============= Lock Operations =============

    async def acquire_lock(
        self,
        key: str,
        value: str,
        ttl: int = 300,
        blocking: bool = False,
        blocking_timeout: int = 5,
    ) -> bool:
        """
        Acquire a distributed lock using SET NX

        Args:
            key: Lock key
            value: Lock value (usually session_id)
            ttl: Lock TTL in seconds
            blocking: Whether to wait for lock
            blocking_timeout: Max wait time if blocking

        Returns:
            True if lock acquired, False otherwise
        """
        if not await self.ensure_connected():
            return False

        try:
            if blocking:
                # Try to acquire with retries
                end_time = datetime.now() + timedelta(seconds=blocking_timeout)
                while datetime.now() < end_time:
                    success = await self._client.set(key, value, nx=True, ex=ttl)  # Only set if not exists  # Expire after TTL
                    if success:
                        return True
                    await asyncio.sleep(0.1)
                return False
            else:
                # Single attempt
                return await self._client.set(key, value, nx=True, ex=ttl)
        except Exception as e:
            logger.error(f"Failed to acquire lock {key}: {e}")
            return False

    async def release_lock(self, key: str, value: str) -> bool:
        """
        Release a lock if held by this session

        Uses Lua script for atomic check-and-delete
        """
        if not await self.ensure_connected():
            return False

        lua_script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """

        try:
            result = await self._client.eval(lua_script, 1, key, value)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to release lock {key}: {e}")
            return False

    async def extend_lock(self, key: str, value: str, ttl: int = 300) -> bool:
        """
        Extend lock TTL if held by this session

        Uses Lua script for atomic check-and-extend
        """
        if not await self.ensure_connected():
            return False

        lua_script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("EXPIRE", KEYS[1], ARGV[2])
        else
            return 0
        end
        """

        try:
            result = await self._client.eval(lua_script, 1, key, value, ttl)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to extend lock {key}: {e}")
            return False

    async def get_lock_holder(self, key: str) -> Optional[str]:
        """Get current lock holder"""
        if not await self.ensure_connected():
            return None

        try:
            return await self._client.get(key)
        except Exception as e:
            logger.error(f"Failed to get lock holder for {key}: {e}")
            return None

    # ============= Session Operations =============

    async def register_session(self, session_id: str, session_data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Register a new session"""
        if not await self.ensure_connected():
            return False

        try:
            # Store session data
            session_key = RedisKeys.SESSION_DATA.format(session_id)
            await self._client.setex(session_key, ttl, json.dumps(session_data))

            # Add to active sessions set
            await self._client.sadd(RedisKeys.ACTIVE_SESSIONS, session_id)

            # Set heartbeat
            heartbeat_key = RedisKeys.SESSION_HEARTBEAT.format(session_id)
            await self._client.setex(heartbeat_key, 30, str(datetime.now()))

            return True
        except Exception as e:
            logger.error(f"Failed to register session {session_id}: {e}")
            return False

    async def update_session_heartbeat(self, session_id: str) -> bool:
        """Update session heartbeat to keep it alive"""
        if not await self.ensure_connected():
            return False

        try:
            heartbeat_key = RedisKeys.SESSION_HEARTBEAT.format(session_id)
            await self._client.setex(heartbeat_key, 30, str(datetime.now()))
            return True
        except Exception as e:
            logger.error(f"Failed to update heartbeat for {session_id}: {e}")
            return False

    async def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        if not await self.ensure_connected():
            return []

        try:
            sessions = await self._client.smembers(RedisKeys.ACTIVE_SESSIONS)

            # Filter out dead sessions (no heartbeat)
            active = []
            for session_id in sessions:
                heartbeat_key = RedisKeys.SESSION_HEARTBEAT.format(session_id)
                if await self._client.exists(heartbeat_key):
                    active.append(session_id)
                else:
                    # Clean up dead session
                    await self._client.srem(RedisKeys.ACTIVE_SESSIONS, session_id)

            return active
        except Exception as e:
            logger.error(f"Failed to get active sessions: {e}")
            return []

    async def remove_session(self, session_id: str) -> bool:
        """Remove session and cleanup its resources"""
        if not await self.ensure_connected():
            return False

        try:
            # Remove from active sessions
            await self._client.srem(RedisKeys.ACTIVE_SESSIONS, session_id)

            # Delete session data
            session_key = RedisKeys.SESSION_DATA.format(session_id)
            await self._client.delete(session_key)

            # Delete heartbeat
            heartbeat_key = RedisKeys.SESSION_HEARTBEAT.format(session_id)
            await self._client.delete(heartbeat_key)

            # Get and release all locks held by this session
            locks_key = RedisKeys.SESSION_LOCKS.format(session_id)
            locks = await self._client.smembers(locks_key)

            for lock_key in locks:
                await self.release_lock(lock_key, session_id)

            # Delete locks set
            await self._client.delete(locks_key)

            return True
        except Exception as e:
            logger.error(f"Failed to remove session {session_id}: {e}")
            return False

    # ============= Pub/Sub Operations =============

    async def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """Publish message to channel"""
        if not await self.ensure_connected():
            return False

        try:
            await self._client.publish(channel, json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Failed to publish to {channel}: {e}")
            return False

    async def subscribe(self, channels: List[str]) -> Optional[PubSub]:
        """Subscribe to channels"""
        if not await self.ensure_connected():
            return None

        try:
            pubsub = self._client.pubsub()
            await pubsub.subscribe(*channels)
            return pubsub
        except Exception as e:
            logger.error(f"Failed to subscribe to channels: {e}")
            return None

    # ============= Conflict Management =============

    async def register_conflict(self, project_id: str, conflict_data: Dict[str, Any]) -> bool:
        """Register a detected conflict"""
        if not await self.ensure_connected():
            return False

        try:
            conflicts_key = RedisKeys.PROJECT_CONFLICTS.format(project_id)
            conflict_id = conflict_data.get("id", str(datetime.now().timestamp()))

            await self._client.hset(conflicts_key, conflict_id, json.dumps(conflict_data))

            # Publish conflict event
            await self.publish(
                RedisKeys.CHANNEL_CONFLICTS,
                {
                    "type": "conflict_detected",
                    "project_id": project_id,
                    "conflict": conflict_data,
                },
            )

            return True
        except Exception as e:
            logger.error(f"Failed to register conflict: {e}")
            return False

    async def get_project_conflicts(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all conflicts for a project"""
        if not await self.ensure_connected():
            return []

        try:
            conflicts_key = RedisKeys.PROJECT_CONFLICTS.format(project_id)
            conflicts_data = await self._client.hgetall(conflicts_key)

            conflicts = []
            for conflict_json in conflicts_data.values():
                try:
                    conflicts.append(json.loads(conflict_json))
                except json.JSONDecodeError:
                    pass

            return conflicts
        except Exception as e:
            logger.error(f"Failed to get conflicts for {project_id}: {e}")
            return []

    async def resolve_conflict(self, project_id: str, conflict_id: str) -> bool:
        """Mark conflict as resolved"""
        if not await self.ensure_connected():
            return False

        try:
            conflicts_key = RedisKeys.PROJECT_CONFLICTS.format(project_id)
            await self._client.hdel(conflicts_key, conflict_id)

            # Publish resolution event
            await self.publish(
                RedisKeys.CHANNEL_CONFLICTS,
                {
                    "type": "conflict_resolved",
                    "project_id": project_id,
                    "conflict_id": conflict_id,
                },
            )

            return True
        except Exception as e:
            logger.error(f"Failed to resolve conflict {conflict_id}: {e}")
            return False


# Singleton instance
_redis_client: Optional[RedisClient] = None


async def get_redis_client() -> RedisClient:
    """Get or create Redis client singleton"""
    global _redis_client

    if _redis_client is None:
        _redis_client = RedisClient()
        await _redis_client.connect()

    return _redis_client


async def cleanup_redis():
    """Cleanup Redis connection on shutdown"""
    global _redis_client

    if _redis_client:
        await _redis_client.disconnect()
        _redis_client = None
