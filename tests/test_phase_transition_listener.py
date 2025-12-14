#!/usr/bin/env python3
"""
Unit tests for PhaseTransitionListener

Tests phase transition event handling, time tracking integration,
database persistence, and WebSocket broadcasting.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

# Add backend and src to path
backend_dir = Path(__file__).parent.parent / "backend"
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(src_dir))

from app.services.phase_transition_listener import (
    PhaseTransitionListener,
    create_listener_callback
)
from phase_state_manager import Phase, PhaseTransitionEvent


# Module-level fixtures for all test classes
@pytest.fixture
def mock_pool():
    """Create mock database connection pool"""
    pool = MagicMock()

    # Mock connection context manager
    conn = AsyncMock()
    conn.fetchval = AsyncMock(return_value=uuid4())

    pool.acquire = MagicMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

    return pool


@pytest.fixture
def mock_time_tracking():
    """Create mock TimeTrackingService"""
    service = AsyncMock()
    service.start_task = AsyncMock(return_value=uuid4())
    service.stop_task = AsyncMock(return_value=None)
    return service


@pytest.fixture
def mock_broadcast():
    """Create mock broadcast function"""
    return AsyncMock()


@pytest.fixture
def listener(mock_pool, mock_time_tracking, mock_broadcast):
    """Create PhaseTransitionListener instance"""
    return PhaseTransitionListener(
        pool=mock_pool,
        time_tracking_service=mock_time_tracking,
        broadcast_func=mock_broadcast
    )


class TestPhaseTransitionListener:
    """Test PhaseTransitionListener class"""

    def test_initialization(self, listener, mock_pool, mock_time_tracking, mock_broadcast):
        """Test listener initializes correctly"""
        assert listener.pool == mock_pool
        assert listener.time_tracking == mock_time_tracking
        assert listener.broadcast == mock_broadcast
        assert listener.current_session_id is None
        assert listener.current_phase is None

    @pytest.mark.asyncio
    async def test_first_phase_transition(self, listener, mock_time_tracking):
        """Test first phase transition (no previous session)"""
        transition_time = datetime.utcnow()

        transition_id = await listener.on_phase_transition(
            from_phase=None,
            to_phase=Phase.IDEATION,
            transition_time=transition_time,
            duration_seconds=None,
            metadata={"reason": "project start"}
        )

        # Should NOT call stop_task (no previous session)
        mock_time_tracking.stop_task.assert_not_called()

        # Should start new task
        mock_time_tracking.start_task.assert_called_once()
        call_args = mock_time_tracking.start_task.call_args

        assert "phase_ideation_" in call_args.kwargs["task_id"]
        assert call_args.kwargs["phase"] == Phase.IDEATION
        assert call_args.kwargs["metadata"]["phase_transition"] is True
        assert call_args.kwargs["metadata"]["from_phase"] is None

        # Should update state
        assert listener.current_phase == Phase.IDEATION
        assert listener.current_session_id is not None
        assert isinstance(transition_id, UUID)

    @pytest.mark.asyncio
    async def test_phase_transition_with_previous_session(self, listener, mock_time_tracking):
        """Test phase transition with previous session"""
        # Set up previous session
        old_session_id = uuid4()
        listener.current_session_id = old_session_id
        listener.current_phase = Phase.IDEATION

        transition_time = datetime.utcnow()

        transition_id = await listener.on_phase_transition(
            from_phase=Phase.IDEATION,
            to_phase=Phase.DESIGN,
            transition_time=transition_time,
            duration_seconds=3600,
            metadata={"reason": "requirements complete"}
        )

        # Should call stop_task for previous session (OLD session ID)
        mock_time_tracking.stop_task.assert_called_once()
        stop_call_args = mock_time_tracking.stop_task.call_args

        assert stop_call_args.kwargs["session_id"] == old_session_id
        assert stop_call_args.kwargs["metadata"]["phase_transition"] is True
        assert stop_call_args.kwargs["metadata"]["to_phase"] == "design"

        # Should start new task
        mock_time_tracking.start_task.assert_called_once()
        start_call_args = mock_time_tracking.start_task.call_args

        assert "phase_design_" in start_call_args.kwargs["task_id"]
        assert start_call_args.kwargs["phase"] == Phase.DESIGN
        assert start_call_args.kwargs["metadata"]["from_phase"] == "ideation"

        # Should update state
        assert listener.current_phase == Phase.DESIGN
        assert isinstance(transition_id, UUID)

    @pytest.mark.asyncio
    async def test_database_recording(self, listener):
        """Test phase transition is recorded in database"""
        transition_time = datetime.utcnow()

        transition_id = await listener.on_phase_transition(
            from_phase=Phase.DESIGN,
            to_phase=Phase.MVP,
            transition_time=transition_time,
            duration_seconds=7200,
            metadata={"confidence": 0.85}
        )

        # Verify database query was executed
        listener.pool.acquire.assert_called()

        # Verify returned UUID
        assert isinstance(transition_id, UUID)

    @pytest.mark.asyncio
    async def test_websocket_broadcasting(self, listener, mock_broadcast):
        """Test WebSocket broadcast on phase change"""
        transition_time = datetime.utcnow()

        await listener.on_phase_transition(
            from_phase=Phase.MVP,
            to_phase=Phase.IMPLEMENTATION,
            transition_time=transition_time,
            duration_seconds=5400
        )

        # Should broadcast phase change
        mock_broadcast.assert_called_once()
        broadcast_data = mock_broadcast.call_args[0][0]

        assert broadcast_data["type"] == "phase_transition"
        assert broadcast_data["data"]["from_phase"] == "mvp"
        assert broadcast_data["data"]["to_phase"] == "implementation"
        assert broadcast_data["data"]["duration_seconds"] == 5400
        assert "transition_id" in broadcast_data["data"]
        assert "timestamp" in broadcast_data["data"]

    @pytest.mark.asyncio
    async def test_broadcast_without_function(self, mock_pool, mock_time_tracking):
        """Test listener works without broadcast function"""
        listener = PhaseTransitionListener(
            pool=mock_pool,
            time_tracking_service=mock_time_tracking,
            broadcast_func=None
        )

        # Should not raise exception
        transition_id = await listener.on_phase_transition(
            from_phase=None,
            to_phase=Phase.IDEATION,
            transition_time=datetime.utcnow()
        )

        assert isinstance(transition_id, UUID)

    @pytest.mark.asyncio
    async def test_error_handling(self, listener, mock_time_tracking):
        """Test error handling during phase transition"""
        # Make time tracking fail
        mock_time_tracking.start_task.side_effect = Exception("Database error")

        with pytest.raises(Exception) as exc_info:
            await listener.on_phase_transition(
                from_phase=None,
                to_phase=Phase.IDEATION,
                transition_time=datetime.utcnow()
            )

        assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_start_lifecycle(self, listener):
        """Test listener start lifecycle"""
        await listener.start()
        # Should complete without error
        # Actual implementation is placeholder for now

    @pytest.mark.asyncio
    async def test_stop_lifecycle(self, listener, mock_time_tracking):
        """Test listener stop lifecycle with active session"""
        # Set up active session
        listener.current_session_id = uuid4()

        await listener.stop()

        # Should stop active session
        mock_time_tracking.stop_task.assert_called_once()
        stop_call_args = mock_time_tracking.stop_task.call_args

        assert stop_call_args.kwargs["session_id"] == listener.current_session_id
        assert stop_call_args.kwargs["metadata"]["automated_shutdown"] is True

    @pytest.mark.asyncio
    async def test_stop_without_active_session(self, listener, mock_time_tracking):
        """Test listener stop without active session"""
        # No active session
        listener.current_session_id = None

        await listener.stop()

        # Should not call stop_task
        mock_time_tracking.stop_task.assert_not_called()

    def test_get_current_state(self, listener):
        """Test getting current listener state"""
        state = listener.get_current_state()

        assert state["current_session_id"] is None
        assert state["current_phase"] is None

        # Set state
        listener.current_session_id = uuid4()
        listener.current_phase = Phase.DESIGN

        state = listener.get_current_state()

        assert state["current_session_id"] is not None
        assert state["current_phase"] == "design"

    @pytest.mark.asyncio
    async def test_mock_mode_without_database(self, mock_time_tracking, mock_broadcast):
        """Test listener works in mock mode (no database)"""
        listener = PhaseTransitionListener(
            pool=None,  # No database pool
            time_tracking_service=mock_time_tracking,
            broadcast_func=mock_broadcast
        )

        transition_id = await listener.on_phase_transition(
            from_phase=None,
            to_phase=Phase.IDEATION,
            transition_time=datetime.utcnow()
        )

        # Should return UUID even without database
        assert isinstance(transition_id, UUID)

        # Should still call time tracking and broadcast
        mock_time_tracking.start_task.assert_called_once()
        mock_broadcast.assert_called_once()


class TestListenerCallback:
    """Test create_listener_callback helper function"""

    @pytest.mark.asyncio
    async def test_callback_creation(self, mock_pool, mock_time_tracking):
        """Test callback function creation"""
        listener = PhaseTransitionListener(
            pool=mock_pool,
            time_tracking_service=mock_time_tracking
        )

        callback = create_listener_callback(listener)

        # Should be callable
        assert callable(callback)

        # Test calling the callback
        event = PhaseTransitionEvent(
            from_phase=None,
            to_phase=Phase.IDEATION,
            transition_time=datetime.utcnow(),
            duration_seconds=None,
            metadata={}
        )

        await callback(event)

        # Should have triggered listener
        mock_time_tracking.start_task.assert_called_once()


class TestIntegrationWithPhaseStateManager:
    """Test integration with PhaseStateManager"""

    @pytest.mark.asyncio
    async def test_phase_manager_event_format(self, mock_pool, mock_time_tracking):
        """Test that PhaseStateManager emits properly formatted events"""
        from phase_state_manager import PhaseStateManager

        # Create phase manager
        manager = PhaseStateManager()

        # Create listener
        listener = PhaseTransitionListener(
            pool=mock_pool,
            time_tracking_service=mock_time_tracking
        )

        # Track events received (sync callback for testing)
        events_received = []

        def tracking_callback(event: PhaseTransitionEvent):
            """Synchronous callback that tracks events"""
            events_received.append(event)

        # Register listener
        manager.register_listener(tracking_callback)

        # Trigger phase change
        manager.set_phase(Phase.IDEATION, metadata={"test": True})

        # Verify event was received and properly formatted
        assert len(events_received) == 1
        event = events_received[0]

        assert isinstance(event, PhaseTransitionEvent)
        assert event.to_phase == Phase.IDEATION
        assert event.from_phase is None
        assert event.metadata["test"] is True
        assert event.duration_seconds is None

        # Now manually trigger the listener with this event
        await listener.on_phase_transition(
            from_phase=event.from_phase,
            to_phase=event.to_phase,
            transition_time=event.transition_time,
            duration_seconds=event.duration_seconds,
            metadata=event.metadata
        )

        # Verify listener processed the event
        mock_time_tracking.start_task.assert_called_once()
        assert listener.current_phase == Phase.IDEATION


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
