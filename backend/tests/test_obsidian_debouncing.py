"""
Unit tests for Obsidian Service Debouncing

Tests cover event-based sync with debouncing strategy:
- Single event immediate flush (3s window)
- Multiple events batched within window
- Events across windows create separate notes
- Force flush functionality
- Batching statistics
- Token optimization metrics
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from app.services.obsidian_service import ObsidianService


@pytest.fixture
def temp_vault():
    """Create temporary Obsidian vault for testing"""
    temp_dir = Path(tempfile.mkdtemp())
    vault_dir = temp_dir / "test_vault"
    vault_dir.mkdir()

    # Create .obsidian directory to mark as vault
    (vault_dir / ".obsidian").mkdir()

    # Create daily notes directory
    daily_notes = vault_dir / "개발일지"
    daily_notes.mkdir()

    yield vault_dir

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def debouncing_service(temp_vault):
    """Create ObsidianService with 1s debounce window for faster testing"""
    service = ObsidianService(vault_path=temp_vault, debounce_window=1)
    return service


class TestDebouncingBasics:
    """Test basic debouncing functionality"""

    @pytest.mark.asyncio
    async def test_single_event_queued_then_flushed(self, debouncing_service):
        """First event should be queued then flushed after debounce window"""
        service = debouncing_service

        # First event - should be queued (not flushed immediately)
        success = await service.sync_event("test_event", {"test": "data"})

        assert success is True
        assert len(service.pending_events) == 1  # Queued, not flushed yet
        assert len(service.sync_history) == 0  # Not flushed yet

        # Wait for debounce window
        await asyncio.sleep(service.debounce_window + 0.2)

        # Should be flushed now
        assert len(service.sync_history) == 1
        assert service.sync_history[0]["events_count"] == 1
        assert service.last_sync is not None
        assert len(service.pending_events) == 0

    @pytest.mark.asyncio
    async def test_single_event_after_3s_flushes_immediately(self, debouncing_service):
        """Event after debounce window should flush immediately"""
        service = debouncing_service

        # First event - gets queued and flushed
        await service.sync_event("event_1", {"test": "first"})
        await asyncio.sleep(service.debounce_window + 0.2)  # Let it flush

        # Verify first event flushed
        assert len(service.sync_history) == 1

        # Wait another debounce window to ensure enough time passed
        await asyncio.sleep(service.debounce_window + 0.1)

        # Second event after 2x window - should flush immediately (last_sync > 3s ago)
        await service.sync_event("event_2", {"test": "second"})

        # Give it a moment to process
        await asyncio.sleep(0.1)

        # Second event should have triggered immediate flush since debounce window passed
        assert len(service.sync_history) == 2
        assert service.sync_history[0]["events_count"] == 1
        assert service.sync_history[1]["events_count"] == 1

    @pytest.mark.asyncio
    async def test_multiple_events_within_window_batched(self, debouncing_service):
        """Multiple events within debounce window should be batched"""
        service = debouncing_service

        # Queue 3 events quickly
        await service.sync_event("event_1", {"test": "first"})
        await asyncio.sleep(0.1)
        await service.sync_event("event_2", {"test": "second"})
        await asyncio.sleep(0.1)
        await service.sync_event("event_3", {"test": "third"})

        # Wait for debounce window
        await asyncio.sleep(service.debounce_window + 0.2)

        # Should have 1 batch sync
        assert len(service.sync_history) == 1
        assert service.sync_history[0]["events_count"] == 3
        assert service.sync_history[0]["event_type"] == "batch_sync"

    @pytest.mark.asyncio
    async def test_events_cleared_from_queue_after_flush(self, debouncing_service):
        """Pending events should be cleared after flush"""
        service = debouncing_service

        # Queue events
        await service.sync_event("event_1", {"test": "first"})
        await asyncio.sleep(0.1)
        await service.sync_event("event_2", {"test": "second"})

        # Should have pending events
        assert len(service.pending_events) > 0

        # Wait for flush
        await asyncio.sleep(service.debounce_window + 0.2)

        # Pending events should be cleared
        assert len(service.pending_events) == 0

    @pytest.mark.asyncio
    async def test_events_across_windows_create_separate_notes(self, debouncing_service):
        """Events in different windows should create separate notes"""
        service = debouncing_service

        # Batch 1
        await service.sync_event("event_1", {"test": "first"})
        await asyncio.sleep(0.1)
        await service.sync_event("event_2", {"test": "second"})

        # Wait for flush
        await asyncio.sleep(service.debounce_window + 0.2)

        # Batch 2
        await service.sync_event("event_3", {"test": "third"})
        await asyncio.sleep(0.1)
        await service.sync_event("event_4", {"test": "fourth"})

        # Wait for flush
        await asyncio.sleep(service.debounce_window + 0.2)

        # Should have 2 separate syncs
        assert len(service.sync_history) == 2
        assert service.sync_history[0]["events_count"] == 2
        assert service.sync_history[1]["events_count"] == 2


class TestForceFlush:
    """Test force flush functionality"""

    @pytest.mark.asyncio
    async def test_force_flush_pending_events(self, debouncing_service):
        """Force flush should immediately flush pending events"""
        service = debouncing_service

        # Queue events but don't wait
        await service.sync_event("event_1", {"test": "first"})
        await asyncio.sleep(0.1)
        await service.sync_event("event_2", {"test": "second"})

        # Should have pending events
        assert len(service.pending_events) > 0

        # Force flush
        events_flushed = await service.force_flush()

        assert events_flushed == 2
        assert len(service.pending_events) == 0
        assert len(service.sync_history) == 1

    @pytest.mark.asyncio
    async def test_force_flush_with_no_pending_events(self, debouncing_service):
        """Force flush with no pending events should return 0"""
        service = debouncing_service

        events_flushed = await service.force_flush()

        assert events_flushed == 0
        assert len(service.sync_history) == 0

    @pytest.mark.asyncio
    async def test_force_flush_prevents_delayed_flush(self, debouncing_service):
        """Force flush should prevent scheduled delayed flush"""
        service = debouncing_service

        # Queue events (triggers delayed flush)
        await service.sync_event("event_1", {"test": "first"})
        await asyncio.sleep(0.1)
        await service.sync_event("event_2", {"test": "second"})

        # Force flush immediately
        await service.force_flush()

        # Wait past debounce window
        await asyncio.sleep(service.debounce_window + 0.2)

        # Should only have 1 sync (from force flush)
        assert len(service.sync_history) == 1
        assert service.sync_history[0]["events_count"] == 2


class TestBatchNoteFormat:
    """Test batch note generation"""

    @pytest.mark.asyncio
    async def test_batch_title_generation(self, debouncing_service):
        """Test batch title generation"""
        service = debouncing_service

        # Same type events
        events = [
            {"type": "task_completion", "data": {}},
            {"type": "task_completion", "data": {}},
        ]
        title = service._generate_batch_title(events)
        assert "task_completion" in title
        assert "2" in title

        # Mixed type events
        events = [
            {"type": "task_completion", "data": {}},
            {"type": "error_resolution", "data": {}},
        ]
        title = service._generate_batch_title(events)
        assert "Development Events" in title

    @pytest.mark.asyncio
    async def test_batch_content_structure(self, debouncing_service):
        """Test batch content has correct structure"""
        service = debouncing_service

        events = [
            {
                "type": "task_completion",
                "data": {"project": "Test", "tags": ["test"]},
                "timestamp": datetime.now()
            },
            {
                "type": "error_resolution",
                "data": {"project": "Test", "solution": "Fix"},
                "timestamp": datetime.now()
            }
        ]

        content = service._generate_batch_content(events)

        # Check frontmatter
        assert "frontmatter" in content
        assert content["frontmatter"]["event_type"] == "batch_sync"
        assert content["frontmatter"]["events_count"] == 2
        assert "batch" in content["frontmatter"]["tags"]

        # Check content has event sections
        assert "content" in content
        assert "## Event 1:" in content["content"]
        assert "## Event 2:" in content["content"]

    @pytest.mark.asyncio
    async def test_batch_note_created_on_disk(self, debouncing_service):
        """Test that batch note is actually created"""
        service = debouncing_service

        # Queue multiple events
        await service.sync_event("event_1", {"test": "first"})
        await asyncio.sleep(0.1)
        await service.sync_event("event_2", {"test": "second"})

        # Wait for flush
        await asyncio.sleep(service.debounce_window + 0.2)

        # Check that note was created
        today = datetime.now().strftime("%Y-%m-%d")
        today_dir = service.daily_notes_dir / today

        assert today_dir.exists()
        md_files = list(today_dir.glob("*.md"))
        assert len(md_files) > 0

        # Check content
        note_content = md_files[0].read_text(encoding="utf-8")
        assert "events_count: 2" in note_content
        assert "event_type: batch_sync" in note_content


class TestBatchingStatistics:
    """Test batching statistics tracking"""

    @pytest.mark.asyncio
    async def test_statistics_track_batching_metrics(self, debouncing_service):
        """Test that statistics include batching metrics"""
        service = debouncing_service

        # Create mix of single and batched syncs
        # Batch 1 (2 events)
        await service.sync_event("event_1", {"test": "first"})
        await asyncio.sleep(0.1)
        await service.sync_event("event_2", {"test": "second"})
        await asyncio.sleep(service.debounce_window + 0.2)

        # Single event
        await service.sync_event("event_3", {"test": "third"})
        await asyncio.sleep(service.debounce_window + 0.2)

        # Batch 2 (3 events)
        await service.sync_event("event_4", {"test": "fourth"})
        await asyncio.sleep(0.1)
        await service.sync_event("event_5", {"test": "fifth"})
        await asyncio.sleep(0.1)
        await service.sync_event("event_6", {"test": "sixth"})
        await asyncio.sleep(service.debounce_window + 0.2)

        stats = service.get_sync_statistics()

        assert stats["total_syncs"] == 3
        assert stats["total_events"] == 6
        assert stats["avg_events_per_sync"] == 2.0
        assert stats["batching_syncs"] == 2
        assert stats["batching_rate"] > 0
        assert stats["tokens_saved_estimate"] > 0

    @pytest.mark.asyncio
    async def test_statistics_pending_events_count(self, debouncing_service):
        """Test that statistics show current pending events"""
        service = debouncing_service

        # Queue events without flushing
        await service.sync_event("event_1", {"test": "first"})
        await asyncio.sleep(0.1)
        await service.sync_event("event_2", {"test": "second"})

        stats = service.get_sync_statistics()

        assert stats["pending_events"] == 2

        # After flush
        await asyncio.sleep(service.debounce_window + 0.2)

        stats = service.get_sync_statistics()
        assert stats["pending_events"] == 0


class TestTokenOptimization:
    """Test token optimization through batching"""

    @pytest.mark.asyncio
    async def test_token_savings_calculation(self, debouncing_service):
        """Test that token savings are calculated correctly"""
        service = debouncing_service

        # Batch of 5 events
        for i in range(5):
            await service.sync_event(f"event_{i}", {"test": f"data_{i}"})
            await asyncio.sleep(0.05)

        await asyncio.sleep(service.debounce_window + 0.2)

        stats = service.get_sync_statistics()

        # 5 events batched = 4 events saved * 100 tokens = 400 tokens
        assert stats["tokens_saved_estimate"] == 400

    @pytest.mark.asyncio
    async def test_no_token_savings_for_single_events(self, debouncing_service):
        """Single events should not count as token savings"""
        service = debouncing_service

        # Single event
        await service.sync_event("event_1", {"test": "first"})
        await asyncio.sleep(service.debounce_window + 0.2)

        stats = service.get_sync_statistics()

        assert stats["tokens_saved_estimate"] == 0


class TestEdgeCases:
    """Test edge cases and error scenarios"""

    @pytest.mark.asyncio
    async def test_debouncing_with_unavailable_vault(self):
        """Test debouncing when vault is not available"""
        service = ObsidianService(vault_path=Path("/nonexistent"), debounce_window=1)

        success = await service.sync_event("test_event", {"test": "data"})

        assert success is False
        assert len(service.pending_events) == 0

    @pytest.mark.asyncio
    async def test_concurrent_event_queuing(self, debouncing_service):
        """Test concurrent event queuing doesn't cause race conditions"""
        service = debouncing_service

        # Queue events concurrently
        tasks = [
            service.sync_event(f"event_{i}", {"test": f"data_{i}"})
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(results)

        # Wait for flush
        await asyncio.sleep(service.debounce_window + 0.2)

        # Should have 1 batch with 10 events
        assert len(service.sync_history) == 1
        assert service.sync_history[0]["events_count"] == 10

    @pytest.mark.asyncio
    async def test_flush_task_cancellation(self, debouncing_service):
        """Test that flush task can be cancelled properly"""
        service = debouncing_service

        # Queue event (starts delayed flush)
        await service.sync_event("event_1", {"test": "first"})

        # Queue another event immediately (should cancel first flush)
        await service.sync_event("event_2", {"test": "second"})

        # Wait for flush
        await asyncio.sleep(service.debounce_window + 0.2)

        # Should have only 1 sync (both events batched)
        assert len(service.sync_history) == 1
        assert service.sync_history[0]["events_count"] == 2


class TestPerformanceRequirements:
    """Test performance requirements"""

    @pytest.mark.asyncio
    async def test_sync_event_completes_quickly(self, debouncing_service):
        """sync_event should complete quickly (queue operation)"""
        service = debouncing_service

        start_time = datetime.now()

        await service.sync_event("test_event", {"test": "data"})

        elapsed = (datetime.now() - start_time).total_seconds()

        # Queueing should be very fast (<100ms)
        assert elapsed < 0.1, f"sync_event took {elapsed}s (target: <0.1s)"

    @pytest.mark.asyncio
    async def test_force_flush_completes_within_3_seconds(self, debouncing_service):
        """Force flush should complete within 3 seconds"""
        service = debouncing_service

        # Queue multiple events
        for i in range(5):
            await service.sync_event(f"event_{i}", {"test": f"data_{i}"})

        start_time = datetime.now()

        await service.force_flush()

        elapsed = (datetime.now() - start_time).total_seconds()

        assert elapsed < 3.0, f"Force flush took {elapsed}s (target: <3s)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
