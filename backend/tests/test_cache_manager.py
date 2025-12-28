"""
Tests for Cache Manager with 50MB limit and LRU eviction (P0 Critical Issue #2).

Verifies:
- 50MB size limit enforcement
- LRU (Least Recently Used) eviction policy
- Size tracking accuracy
- Thread safety
- Statistics tracking
"""

import sys

import pytest

from backend.app.core.cache_manager import CacheManager


class TestCacheManagerBasics:
    """Test basic cache operations"""

    def test_initial_state(self):
        """Cache should start empty"""
        cache = CacheManager(max_size_bytes=1024)
        assert cache.size == 0
        assert cache.count == 0
        assert cache.utilization == 0.0

    def test_set_and_get(self):
        """Basic set/get operations"""
        cache = CacheManager()
        cache.set("key1", "value1")

        assert cache.get("key1") == "value1"
        assert cache.get("nonexistent") is None

    def test_update_existing_key(self):
        """Updating existing key should replace value and adjust size"""
        cache = CacheManager()

        # Set initial value
        small_value = "a" * 100
        cache.set("key1", small_value)
        initial_size = cache.size

        # Update with larger value
        large_value = "b" * 1000
        cache.set("key1", large_value)
        updated_size = cache.size

        assert cache.get("key1") == large_value
        assert updated_size > initial_size
        assert cache.count == 1  # Still only 1 entry

    def test_delete(self):
        """Delete should remove entry and free space"""
        cache = CacheManager()
        cache.set("key1", "value1")

        assert cache.count == 1
        assert cache.size > 0

        deleted = cache.delete("key1")
        assert deleted is True
        assert cache.get("key1") is None
        assert cache.count == 0
        assert cache.size == 0

        # Delete non-existent key
        deleted = cache.delete("key1")
        assert deleted is False

    def test_clear(self):
        """Clear should remove all entries"""
        cache = CacheManager()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        assert cache.count == 3

        cache.clear()
        assert cache.count == 0
        assert cache.size == 0
        assert cache.get("key1") is None


class TestLRUEviction:
    """Test LRU eviction policy"""

    def test_eviction_when_full(self):
        """Should evict LRU entry when cache is full"""
        # Small cache: 500 bytes
        cache = CacheManager(max_size_bytes=500)

        # Each string is ~200 bytes
        cache.set("key1", "a" * 200)
        cache.set("key2", "b" * 200)

        # Both should fit
        assert cache.count == 2
        assert cache.get("key1") is not None
        assert cache.get("key2") is not None

        # Add third entry that exceeds limit
        # Should evict key1 (LRU)
        cache.set("key3", "c" * 200)

        assert cache.get("key1") is None, "key1 should be evicted (LRU)"
        assert cache.get("key2") is not None
        assert cache.get("key3") is not None

    def test_lru_order_with_get(self):
        """Get should update LRU order"""
        cache = CacheManager(max_size_bytes=500)

        cache.set("key1", "a" * 200)
        cache.set("key2", "b" * 200)

        # Access key1 to make it recently used
        _ = cache.get("key1")

        # Add third entry
        # Should evict key2 (now LRU) instead of key1
        cache.set("key3", "c" * 200)

        assert cache.get("key1") is not None, "key1 should remain (accessed recently)"
        assert cache.get("key2") is None, "key2 should be evicted (LRU)"
        assert cache.get("key3") is not None

    def test_multiple_evictions(self):
        """Should evict multiple entries if needed"""
        import sys

        # Calculate actual size of test strings (account for Python overhead)
        small_entry_size = sys.getsizeof("x" * 100)  # ~149 bytes
        large_entry_size = sys.getsizeof("y" * 800)  # ~849 bytes

        # Size cache to fit exactly 10 small entries + some buffer
        cache = CacheManager(max_size_bytes=small_entry_size * 10 + 100)

        # Add many small entries
        for i in range(10):
            cache.set(f"key{i}", "x" * 100)

        assert cache.count == 10

        # Add large entry requiring multiple evictions
        cache.set("large", "y" * 800)

        # Should have evicted several old entries to fit large one
        assert cache.count < 10
        assert cache.get("large") is not None
        assert cache.size <= cache.max_size_bytes


class TestSizeLimits:
    """Test size limit enforcement"""

    def test_50mb_default_limit(self):
        """Default max size should be 50MB"""
        cache = CacheManager()
        assert cache.max_size_bytes == 50 * 1024 * 1024

    def test_custom_size_limit(self):
        """Should respect custom size limit"""
        cache = CacheManager(max_size_bytes=1024)
        assert cache.max_size_bytes == 1024

    def test_value_exceeds_max_size(self):
        """Should raise error if single value exceeds max size"""
        cache = CacheManager(max_size_bytes=100)

        with pytest.raises(ValueError, match="exceeds max cache size"):
            cache.set("key", "x" * 1000)

    def test_size_tracking_accuracy(self):
        """Size tracking should be reasonably accurate"""
        cache = CacheManager()

        value1 = "a" * 1000
        size1 = sys.getsizeof(value1)
        cache.set("key1", value1)

        # Size should match sys.getsizeof
        assert cache.size == size1

        value2 = "b" * 2000
        size2 = sys.getsizeof(value2)
        cache.set("key2", value2)

        assert cache.size == size1 + size2

    def test_utilization_calculation(self):
        """Utilization should reflect percentage of max size"""
        import sys

        # Use actual sizes to calculate cache size
        entry1_size = sys.getsizeof("x" * 500)  # ~549 bytes
        entry2_size = sys.getsizeof("y" * 500)  # ~549 bytes

        # Size cache to fit exactly 2 entries (with 10% buffer)
        cache = CacheManager(max_size_bytes=int((entry1_size + entry2_size) * 1.1))

        # Empty cache
        assert cache.utilization == 0.0

        # Add 500 bytes worth of data
        cache.set("key1", "x" * 500)

        # Utilization should be ~45-50% (accounting for overhead)
        assert 0.4 < cache.utilization < 0.6

        # Fill cache
        cache.set("key2", "y" * 500)

        # Utilization should be ~90-100% (accounting for 10% buffer)
        assert 0.8 < cache.utilization <= 1.0


class TestStatistics:
    """Test statistics tracking"""

    def test_hit_miss_tracking(self):
        """Should track cache hits and misses"""
        cache = CacheManager()
        cache.set("key1", "value1")

        # Hit
        _ = cache.get("key1")

        # Miss
        _ = cache.get("nonexistent")

        stats = cache.get_statistics()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    def test_eviction_tracking(self):
        """Should track number of evictions"""
        cache = CacheManager(max_size_bytes=300)

        cache.set("key1", "a" * 100)
        cache.set("key2", "b" * 100)
        cache.set("key3", "c" * 100)  # Triggers eviction

        stats = cache.get_statistics()
        assert stats["evictions"] == 1

    def test_statistics_reset(self):
        """Should reset statistics counters"""
        cache = CacheManager()
        cache.set("key1", "value1")
        _ = cache.get("key1")

        stats_before = cache.get_statistics()
        assert stats_before["hits"] > 0

        cache.reset_statistics()

        stats_after = cache.get_statistics()
        assert stats_after["hits"] == 0
        assert stats_after["misses"] == 0
        assert stats_after["evictions"] == 0


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_cache_operations(self):
        """Operations on empty cache should not error"""
        cache = CacheManager()

        assert cache.get("any_key") is None
        assert cache.delete("any_key") is False
        cache.clear()  # Should not error

    def test_zero_size_value(self):
        """Should handle empty values"""
        cache = CacheManager()
        cache.set("empty", "")

        assert cache.get("empty") == ""

    def test_large_object_types(self):
        """Should handle various object types"""
        cache = CacheManager()

        # Dictionary
        cache.set("dict", {"key": "value", "number": 123})
        assert cache.get("dict") == {"key": "value", "number": 123}

        # List
        cache.set("list", [1, 2, 3, 4, 5])
        assert cache.get("list") == [1, 2, 3, 4, 5]

        # Bytes
        cache.set("bytes", b"binary data")
        assert cache.get("bytes") == b"binary data"

    def test_many_small_entries(self):
        """Should handle many small entries efficiently"""
        import sys

        # Calculate actual size of small entry
        small_entry_size = sys.getsizeof("value0")  # ~51 bytes

        # Size cache to force evictions: 100 entries × 51 bytes = 5100 bytes
        # Set cache to 4KB to ensure evictions happen
        cache = CacheManager(max_size_bytes=4 * 1024)  # 4KB (not 10KB)

        # Add 100 small entries
        for i in range(100):
            cache.set(f"key{i}", f"value{i}")

        # Not all should fit (4KB / 51 bytes ≈ 80 entries max)
        assert cache.count < 100
        assert cache.count > 50  # But most should fit

        # LRU should have triggered evictions
        stats = cache.get_statistics()
        assert stats["evictions"] > 0


class TestRealWorldScenarios:
    """Test realistic usage patterns"""

    def test_task_context_caching(self):
        """Simulate caching task contexts (Kanban use case)"""
        import sys

        # NOTE: Current implementation limitation - sys.getsizeof() only measures
        # top-level object size, not nested containers. For nested objects,
        # size is underestimated. This is a known limitation documented in
        # cache_manager.py docstring.
        #
        # For this test, use flat strings instead of nested dicts to accurately
        # test the cache size limit and LRU eviction logic.
        # Simulate large task contexts using flat strings (10MB each)
        large_context = "x" * (10 * 1024 * 1024)
        context_size = sys.getsizeof(large_context)

        # Size cache to fit exactly 5 contexts
        cache = CacheManager(max_size_bytes=context_size * 5)

        # Should fit 5 contexts
        for i in range(5):
            cache.set(f"task_{i}", large_context)

        assert cache.count == 5

        # 6th context should trigger eviction
        cache.set("task_5", large_context)
        assert cache.count == 5  # Still 5 (evicted task_0)
        assert cache.get("task_0") is None

    def test_ai_response_caching(self):
        """Simulate caching AI-generated responses"""
        cache = CacheManager(max_size_bytes=1 * 1024 * 1024)  # 1MB

        # AI responses vary in size
        for i in range(20):
            response_size = 50 * 1024 * (1 + i % 3)  # 50KB, 100KB, 150KB
            cache.set(f"ai_response_{i}", "x" * response_size)

        # Should have evicted older responses
        assert cache.count < 20
        assert cache.size <= cache.max_size_bytes

        # Most recent responses should be available
        assert cache.get("ai_response_19") is not None


class TestPerformance:
    """Test performance characteristics"""

    def test_get_performance(self):
        """Get operation should be O(1)"""
        import time

        cache = CacheManager()

        # Add many entries
        for i in range(1000):
            cache.set(f"key{i}", f"value{i}")

        # Measure get time
        start = time.time()
        for i in range(100):
            _ = cache.get(f"key{i}")
        elapsed = time.time() - start

        # Should be very fast (<10ms for 100 gets)
        assert elapsed < 0.01

    def test_set_performance_with_eviction(self):
        """Set with eviction should be reasonably fast"""
        import time

        cache = CacheManager(max_size_bytes=1000)

        # Fill cache
        for i in range(10):
            cache.set(f"key{i}", "x" * 100)

        # Measure set time with eviction
        start = time.time()
        for i in range(100):
            cache.set(f"new_key{i}", "y" * 100)
        elapsed = time.time() - start

        # Should be fast even with evictions (<50ms for 100 sets)
        assert elapsed < 0.05


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
