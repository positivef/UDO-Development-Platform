#!/usr/bin/env python3
"""
Unit tests for PhaseStateManager

Tests phase state tracking, transitions, event emission, and history management.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from time import sleep

# Add src directory to path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from phase_state_manager import (  # noqa: E402
    PhaseStateManager,
    PhaseTransitionEvent,
    Phase,
    get_global_phase_manager,
    reset_global_phase_manager,
)


class TestPhaseEnum:
    """Test Phase enum"""

    def test_phase_values(self):
        """Test all phase values are correct"""
        assert Phase.IDEATION.value == "ideation"
        assert Phase.DESIGN.value == "design"
        assert Phase.MVP.value == "mvp"
        assert Phase.IMPLEMENTATION.value == "implementation"
        assert Phase.TESTING.value == "testing"

    def test_phase_count(self):
        """Test we have exactly 5 phases"""
        assert len(Phase) == 5


class TestPhaseTransitionEvent:
    """Test PhaseTransitionEvent dataclass"""

    def test_event_creation(self):
        """Test creating a phase transition event"""
        event = PhaseTransitionEvent(
            from_phase=Phase.IDEATION, to_phase=Phase.DESIGN, transition_time=datetime.utcnow(), duration_seconds=3600
        )

        assert event.from_phase == Phase.IDEATION
        assert event.to_phase == Phase.DESIGN
        assert event.duration_seconds == 3600
        assert isinstance(event.transition_time, datetime)

    def test_event_to_dict(self):
        """Test converting event to dictionary"""
        transition_time = datetime(2025, 11, 21, 12, 0, 0)
        event = PhaseTransitionEvent(
            from_phase=Phase.IDEATION,
            to_phase=Phase.DESIGN,
            transition_time=transition_time,
            duration_seconds=3600,
            metadata={"reason": "requirements complete"},
        )

        event_dict = event.to_dict()

        assert event_dict["from_phase"] == "ideation"
        assert event_dict["to_phase"] == "design"
        assert event_dict["duration_seconds"] == 3600
        assert event_dict["metadata"]["reason"] == "requirements complete"
        assert "2025-11-21" in event_dict["transition_time"]

    def test_event_first_phase(self):
        """Test event for first phase (no from_phase)"""
        event = PhaseTransitionEvent(
            from_phase=None, to_phase=Phase.IDEATION, transition_time=datetime.utcnow(), duration_seconds=None
        )

        assert event.from_phase is None
        assert event.to_phase == Phase.IDEATION
        assert event.duration_seconds is None

        event_dict = event.to_dict()
        assert event_dict["from_phase"] is None


class TestPhaseStateManager:
    """Test PhaseStateManager class"""

    def setup_method(self):
        """Create fresh manager for each test"""
        self.manager = PhaseStateManager()

    def teardown_method(self):
        """Clean up after each test"""
        self.manager.reset()

    def test_initialization(self):
        """Test manager initializes with no phase"""
        assert self.manager.current_phase is None
        assert self.manager.phase_start_time is None
        assert len(self.manager.phase_history) == 0
        assert len(self.manager.listeners) == 0

    def test_set_first_phase(self):
        """Test setting the first phase"""
        self.manager.set_phase(Phase.IDEATION)

        assert self.manager.current_phase == Phase.IDEATION
        assert self.manager.phase_start_time is not None
        assert len(self.manager.phase_history) == 1

        # Check history entry
        history = self.manager.phase_history[0]
        assert history["from_phase"] is None
        assert history["to_phase"] == "ideation"
        assert history["duration_seconds"] is None

    def test_phase_transition(self):
        """Test transitioning between phases"""
        # Start with ideation
        self.manager.set_phase(Phase.IDEATION)
        sleep(0.1)  # Small delay to ensure duration > 0

        # Transition to design
        self.manager.set_phase(Phase.DESIGN)

        assert self.manager.current_phase == Phase.DESIGN
        assert len(self.manager.phase_history) == 2

        # Check second history entry
        history = self.manager.phase_history[1]
        assert history["from_phase"] == "ideation"
        assert history["to_phase"] == "design"
        assert history["duration_seconds"] is not None
        assert history["duration_seconds"] >= 0

    def test_multiple_transitions(self):
        """Test multiple phase transitions"""
        phases = [Phase.IDEATION, Phase.DESIGN, Phase.MVP, Phase.IMPLEMENTATION, Phase.TESTING]

        for phase in phases:
            self.manager.set_phase(phase)
            sleep(0.01)

        assert self.manager.current_phase == Phase.TESTING
        assert len(self.manager.phase_history) == 5

        # Verify transition sequence
        for i, phase in enumerate(phases):
            assert self.manager.phase_history[i]["to_phase"] == phase.value

    def test_get_current_phase(self):
        """Test getting current phase"""
        assert self.manager.get_current_phase() is None

        self.manager.set_phase(Phase.IDEATION)
        assert self.manager.get_current_phase() == Phase.IDEATION

        self.manager.set_phase(Phase.DESIGN)
        assert self.manager.get_current_phase() == Phase.DESIGN

    def test_get_phase_duration(self):
        """Test getting current phase duration"""
        # No phase set
        assert self.manager.get_phase_duration() is None

        # Set phase and check duration
        self.manager.set_phase(Phase.IDEATION)
        sleep(0.1)

        duration = self.manager.get_phase_duration()
        assert duration is not None
        assert duration >= 0

    def test_get_phase_history(self):
        """Test getting phase history"""
        assert len(self.manager.get_phase_history()) == 0

        self.manager.set_phase(Phase.IDEATION)
        self.manager.set_phase(Phase.DESIGN)

        history = self.manager.get_phase_history()
        assert len(history) == 2
        assert isinstance(history, list)

        # Verify it's a copy (modifying returned list doesn't affect manager)
        history.append({"fake": "entry"})
        assert len(self.manager.get_phase_history()) == 2

    def test_listener_registration(self):
        """Test registering event listeners"""
        events_received = []

        def listener(event: PhaseTransitionEvent):
            events_received.append(event)

        self.manager.register_listener(listener)
        assert len(self.manager.listeners) == 1

        # Trigger event
        self.manager.set_phase(Phase.IDEATION)

        assert len(events_received) == 1
        assert events_received[0].to_phase == Phase.IDEATION

    def test_multiple_listeners(self):
        """Test multiple listeners receive events"""
        events_1 = []
        events_2 = []

        def listener1(event: PhaseTransitionEvent):
            events_1.append(event)

        def listener2(event: PhaseTransitionEvent):
            events_2.append(event)

        self.manager.register_listener(listener1)
        self.manager.register_listener(listener2)

        self.manager.set_phase(Phase.IDEATION)

        assert len(events_1) == 1
        assert len(events_2) == 1
        assert events_1[0].to_phase == Phase.IDEATION
        assert events_2[0].to_phase == Phase.IDEATION

    def test_listener_unregistration(self):
        """Test unregistering listeners"""
        events_received = []

        def listener(event: PhaseTransitionEvent):
            events_received.append(event)

        self.manager.register_listener(listener)
        self.manager.set_phase(Phase.IDEATION)
        assert len(events_received) == 1

        # Unregister and trigger another event
        self.manager.unregister_listener(listener)
        self.manager.set_phase(Phase.DESIGN)

        # Should still be 1 (listener not called for second event)
        assert len(events_received) == 1

    def test_listener_error_handling(self):
        """Test that listener errors don't break the manager"""
        events_received = []

        def bad_listener(event: PhaseTransitionEvent):
            raise Exception("Listener error")

        def good_listener(event: PhaseTransitionEvent):
            events_received.append(event)

        self.manager.register_listener(bad_listener)
        self.manager.register_listener(good_listener)

        # Should not raise exception despite bad_listener failing
        self.manager.set_phase(Phase.IDEATION)

        # Good listener should still receive event
        assert len(events_received) == 1

    def test_reset(self):
        """Test resetting phase state"""
        self.manager.set_phase(Phase.IDEATION)
        self.manager.set_phase(Phase.DESIGN)

        assert self.manager.current_phase is not None
        assert len(self.manager.phase_history) > 0

        self.manager.reset()

        assert self.manager.current_phase is None
        assert self.manager.phase_start_time is None
        assert len(self.manager.phase_history) == 0

    def test_get_statistics_empty(self):
        """Test statistics with no phases"""
        stats = self.manager.get_statistics()

        assert stats["total_transitions"] == 0
        assert stats["current_phase"] is None
        assert stats["current_duration_seconds"] is None
        assert stats["total_duration_seconds"] == 0

    def test_get_statistics_single_phase(self):
        """Test statistics with single phase"""
        self.manager.set_phase(Phase.IDEATION)
        sleep(0.1)

        stats = self.manager.get_statistics()

        assert stats["total_transitions"] == 1
        assert stats["current_phase"] == "ideation"
        assert stats["current_duration_seconds"] is not None
        assert stats["total_duration_seconds"] >= 0

    def test_get_statistics_multiple_phases(self):
        """Test statistics with multiple phases"""
        self.manager.set_phase(Phase.IDEATION)
        sleep(0.1)
        self.manager.set_phase(Phase.DESIGN)
        sleep(0.1)

        stats = self.manager.get_statistics()

        assert stats["total_transitions"] == 2
        assert stats["current_phase"] == "design"
        assert "ideation" in stats["phases_visited"]
        assert "design" in stats["phases_visited"]
        assert stats["total_duration_seconds"] >= 0

    def test_phase_metadata(self):
        """Test setting phase with metadata"""
        metadata = {"reason": "requirements complete", "confidence": 0.85, "reviewer": "team-lead"}

        self.manager.set_phase(Phase.DESIGN, metadata=metadata)

        history = self.manager.phase_history[0]
        assert history["metadata"] == metadata


class TestGlobalPhaseManager:
    """Test global phase manager singleton"""

    def teardown_method(self):
        """Reset global manager after each test"""
        reset_global_phase_manager()

    def test_get_global_manager(self):
        """Test getting global manager creates singleton"""
        manager1 = get_global_phase_manager()
        manager2 = get_global_phase_manager()

        assert manager1 is manager2

    def test_global_manager_state_persists(self):
        """Test global manager maintains state"""
        manager = get_global_phase_manager()
        manager.set_phase(Phase.IDEATION)

        # Get again
        manager2 = get_global_phase_manager()
        assert manager2.current_phase == Phase.IDEATION

    def test_reset_global_manager(self):
        """Test resetting global manager"""
        manager = get_global_phase_manager()
        manager.set_phase(Phase.IDEATION)

        reset_global_phase_manager()

        # Should get new instance
        new_manager = get_global_phase_manager()
        assert new_manager.current_phase is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
