"""
Cache Manager with 50MB limit and LRU eviction policy (P0 Critical Issue #2).

Features:
- Maximum 50MB memory limit
- LRU (Least Recently Used) eviction policy
- Automatic eviction when size limit exceeded
- Thread-safe operations
"""

import sys
from collections import OrderedDict
from typing import Any, Optional
from threading import Lock


class CacheManager:
    """
    Memory-bounded cache with LRU eviction.

    Critical for preventing OOM (Out of Memory) issues when caching
    large objects like task contexts, AI responses, or dependency graphs.

    Usage:
        cache = CacheManager(max_size_bytes=50 * 1024 * 1024)  # 50MB
        cache.set("key", large_object)
        value = cache.get("key")
    """

    MAX_SIZE_BYTES = 50 * 1024 * 1024  # 50MB default

    def __init__(self, max_size_bytes: Optional[int] = None):
        """
        Initialize cache manager.

        Args:
            max_size_bytes: Maximum cache size in bytes (default: 50MB)
        """
        self.max_size_bytes = max_size_bytes or self.MAX_SIZE_BYTES
        self._cache: OrderedDict[str, tuple[Any, int]] = OrderedDict()
        self._current_size = 0
        self._lock = Lock()

        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (marks as recently used).

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None

            value, size = entry
            self._hits += 1

            # Move to end (most recently used)
            self._cache.move_to_end(key)

            return value

    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache with automatic eviction if needed.

        Args:
            key: Cache key
            value: Value to cache

        Raises:
            ValueError: If single value exceeds max_size_bytes
        """
        with self._lock:
            value_size = sys.getsizeof(value)

            # Check if single value exceeds max size
            if value_size > self.max_size_bytes:
                raise ValueError(
                    f"Value size ({value_size} bytes) exceeds max cache size "
                    f"({self.max_size_bytes} bytes)"
                )

            # Remove existing entry if present
            if key in self._cache:
                _, old_size = self._cache[key]
                self._current_size -= old_size
                del self._cache[key]

            # Evict until space available
            while self._current_size + value_size > self.max_size_bytes:
                if not self._cache:
                    break  # Safety check
                self._evict_lru()

            # Add new entry
            self._cache[key] = (value, value_size)
            self._cache.move_to_end(key)
            self._current_size += value_size

    def delete(self, key: str) -> bool:
        """
        Delete specific key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key existed and was deleted, False otherwise
        """
        with self._lock:
            if key not in self._cache:
                return False

            _, size = self._cache[key]
            del self._cache[key]
            self._current_size -= size
            return True

    def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            self._cache.clear()
            self._current_size = 0

    def _evict_lru(self) -> None:
        """
        Evict least recently used entry.

        Internal method called automatically when cache is full.
        """
        if not self._cache:
            return

        # OrderedDict: first item is LRU
        lru_key = next(iter(self._cache))
        _, size = self._cache[lru_key]

        del self._cache[lru_key]
        self._current_size -= size
        self._evictions += 1

    @property
    def size(self) -> int:
        """Current cache size in bytes."""
        return self._current_size

    @property
    def count(self) -> int:
        """Number of entries in cache."""
        return len(self._cache)

    @property
    def utilization(self) -> float:
        """Cache utilization as percentage (0.0 to 1.0)."""
        return self._current_size / self.max_size_bytes if self.max_size_bytes > 0 else 0.0

    def get_statistics(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with hit rate, miss rate, evictions, size, etc.
        """
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "evictions": self._evictions,
            "current_size_bytes": self._current_size,
            "max_size_bytes": self.max_size_bytes,
            "utilization": self.utilization,
            "entry_count": self.count,
        }

    def reset_statistics(self) -> None:
        """Reset hit/miss/eviction counters."""
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._evictions = 0


# Global cache instance (can be imported and used across application)
global_cache = CacheManager()


def get_cache() -> CacheManager:
    """Get global cache instance."""
    return global_cache
