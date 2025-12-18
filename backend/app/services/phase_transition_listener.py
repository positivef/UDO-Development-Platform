"""
Phase Transition Listener Service

Listens for phase transition events from PhaseStateManager and:
- Ends previous time tracking sessions
- Records transitions in database
- Starts new sessions for new phases
- Broadcasts updates via WebSocket

Author: UDO Platform Team
Date: 2025-11-21
Version: 1.0.0
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, UTC
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

# Add src to path for PhaseStateManager import
src_dir = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_dir))

from phase_state_manager import PhaseTransitionEvent, Phase

from ..models.time_tracking import TaskType, AIModel

logger = logging.getLogger(__name__)


class PhaseTransitionListener:
    """
    Listens for phase transition events and manages time tracking integration

    Features:
    - Automatic session management on phase changes
    - Database persistence of transitions
    - WebSocket broadcasting to dashboard
    - Graceful error handling

    Example:
        >>> listener = PhaseTransitionListener(pool, time_tracking, websocket)
        >>> await listener.start()
        >>> # Phase changes automatically trigger session management
    """

    def __init__(
        self,
        pool,
        time_tracking_service,
        broadcast_func=None
    ):
        """
        Initialize Phase Transition Listener

        Args:
            pool: Database connection pool (asyncpg)
            time_tracking_service: TimeTrackingService instance
            broadcast_func: WebSocket broadcast function (optional)
        """
        self.pool = pool
        self.time_tracking = time_tracking_service
        self.broadcast = broadcast_func

        # Track current session and phase
        self.current_session_id: Optional[UUID] = None
        self.current_phase: Optional[Phase] = None

        logger.info("PhaseTransitionListener initialized")

    async def on_phase_transition(
        self,
        from_phase: Optional[Phase],
        to_phase: Phase,
        transition_time: datetime,
        duration_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Handle phase transition event

        Args:
            from_phase: Previous phase (None if first phase)
            to_phase: New phase being entered
            transition_time: When the transition occurred
            duration_seconds: Time spent in previous phase
            metadata: Additional transition context

        Returns:
            UUID of the phase transition record

        Raises:
            Exception: If transition handling fails
        """
        try:
            logger.info(
                f"Handling phase transition: {from_phase.value if from_phase else 'None'} -> {to_phase.value}"
            )

            # 1. End previous phase session (if exists)
            if self.current_session_id and from_phase:
                logger.info(f"Ending previous session: {self.current_session_id}")

                await self.time_tracking.stop_task(
                    session_id=self.current_session_id,
                    metadata={
                        "phase_transition": True,
                        "to_phase": to_phase.value,
                        "automated": True
                    }
                )

            # 2. Record transition in database
            transition_id = await self._record_transition(
                from_phase,
                to_phase,
                transition_time,
                duration_seconds,
                metadata
            )

            logger.info(f"Recorded transition: {transition_id}")

            # 3. Start new phase session
            logger.info(f"Starting new phase session: {to_phase.value}")

            self.current_session_id = await self.time_tracking.start_task(
                task_id=f"phase_{to_phase.value}_{transition_time.strftime('%Y%m%d_%H%M%S')}",
                task_type=TaskType.PHASE_TRANSITION,
                phase=to_phase,
                ai_used=AIModel.MULTI,  # Assume multi-AI in UDO v2
                metadata={
                    "phase_transition": True,
                    "from_phase": from_phase.value if from_phase else None,
                    "transition_id": str(transition_id),
                    "automated": True
                }
            )

            # Update current phase tracking
            self.current_phase = to_phase

            # 4. Broadcast real-time update to dashboard
            await self._broadcast_phase_change(
                from_phase,
                to_phase,
                transition_id,
                duration_seconds
            )

            logger.info(
                f"[OK] Phase transition completed: {from_phase.value if from_phase else 'None'} -> {to_phase.value} "
                f"(transition_id: {transition_id}, session_id: {self.current_session_id})"
            )

            return transition_id

        except Exception as e:
            logger.error(f"Failed to handle phase transition: {e}", exc_info=True)
            raise

    async def _record_transition(
        self,
        from_phase: Optional[Phase],
        to_phase: Phase,
        transition_time: datetime,
        duration_seconds: Optional[int],
        metadata: Optional[Dict[str, Any]]
    ) -> UUID:
        """
        Record phase transition in database

        Args:
            from_phase: Previous phase
            to_phase: New phase
            transition_time: Transition timestamp
            duration_seconds: Duration of previous phase
            metadata: Additional data

        Returns:
            UUID of created transition record
        """
        if not self.pool:
            # Mock mode - return fake UUID
            logger.warning("No database pool - using mock transition ID")
            return uuid4()

        query = """
            INSERT INTO phase_transitions (
                from_phase, to_phase, transition_time,
                duration_seconds, automated, metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """

        try:
            async with self.pool.acquire() as conn:
                transition_id = await conn.fetchval(
                    query,
                    from_phase.value if from_phase else None,
                    to_phase.value,
                    transition_time,
                    duration_seconds,
                    True,  # automated = True
                    metadata
                )

            return transition_id

        except Exception as e:
            logger.error(f"Failed to record transition in database: {e}")
            raise

    async def _broadcast_phase_change(
        self,
        from_phase: Optional[Phase],
        to_phase: Phase,
        transition_id: UUID,
        duration_seconds: Optional[int]
    ):
        """
        Broadcast phase change to dashboard via WebSocket

        Args:
            from_phase: Previous phase
            to_phase: New phase
            transition_id: Transition record ID
            duration_seconds: Duration of previous phase
        """
        if not self.broadcast:
            logger.debug("No broadcast function - skipping WebSocket update")
            return

        try:
            await self.broadcast({
                "type": "phase_transition",
                "data": {
                    "from_phase": from_phase.value if from_phase else None,
                    "to_phase": to_phase.value,
                    "transition_id": str(transition_id),
                    "duration_seconds": duration_seconds,
                    "timestamp": datetime.now(UTC).isoformat()
                }
            })

            logger.debug(f"Broadcasted phase change: {to_phase.value}")

        except Exception as e:
            logger.warning(f"Failed to broadcast phase change: {e}")
            # Don't raise - broadcasting is non-critical

    async def start(self):
        """
        Start listening for phase transitions

        This method would typically:
        1. Connect to PhaseStateManager
        2. Register this instance as a listener
        3. Begin processing events

        Note: In actual implementation, this would be called during app startup
        """
        logger.info("PhaseTransitionListener started and ready")

    async def stop(self):
        """
        Stop listening and clean up resources

        This method would typically:
        1. Unregister from PhaseStateManager
        2. End any active sessions
        3. Close connections
        """
        if self.current_session_id:
            try:
                await self.time_tracking.stop_task(
                    session_id=self.current_session_id,
                    metadata={"automated_shutdown": True}
                )
                logger.info(f"Stopped active session: {self.current_session_id}")
            except Exception as e:
                logger.error(f"Failed to stop active session: {e}")

        logger.info("PhaseTransitionListener stopped")

    def get_current_state(self) -> Dict[str, Any]:
        """
        Get current listener state

        Returns:
            Dictionary with current session and phase info
        """
        return {
            "current_session_id": str(self.current_session_id) if self.current_session_id else None,
            "current_phase": self.current_phase.value if self.current_phase else None
        }


# Helper function to create listener from event
def create_listener_callback(listener: PhaseTransitionListener):
    """
    Create a callback function for PhaseStateManager

    Args:
        listener: PhaseTransitionListener instance

    Returns:
        Async callback function

    Example:
        >>> listener = PhaseTransitionListener(pool, time_tracking)
        >>> callback = create_listener_callback(listener)
        >>> phase_manager.register_listener(callback)
    """
    async def callback(event: PhaseTransitionEvent):
        """Handle phase transition event"""
        await listener.on_phase_transition(
            from_phase=event.from_phase,
            to_phase=event.to_phase,
            transition_time=event.transition_time,
            duration_seconds=event.duration_seconds,
            metadata=event.metadata
        )

    return callback
