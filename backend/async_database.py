"""
Async Database Connection and Configuration
PostgreSQL connection management with async connection pooling (asyncpg)
"""

import asyncio
import logging
import os
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional

import asyncpg
from dotenv import load_dotenv

# Load .env file from backend directory
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (asyncpg.PostgresError, asyncio.TimeoutError, ConnectionError),
):
    """
    Retry decorator for async functions with exponential backoff

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each attempt
        exceptions: Tuple of exceptions to retry on
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )

            # All retries exhausted, raise the last exception
            raise last_exception

        return wrapper

    return decorator


class AsyncDatabaseConfig:
    """Async database configuration"""

    def __init__(self):
        """Load configuration from environment variables"""
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", "5432"))
        self.database = os.getenv("DB_NAME", "udo_dev")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "postgres")

        # Connection pool settings (P0-5: Expanded to match sync pool capacity)
        # Increased from min=2/max=10 to min=5/max=30 for production load
        self.min_size = int(os.getenv("DB_POOL_MIN", "5"))
        self.max_size = int(os.getenv("DB_POOL_MAX", "30"))

    def get_dsn(self) -> str:
        """Get database DSN (connection string)"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    def __repr__(self):
        return f"AsyncDatabaseConfig(host={self.host}, port={self.port}, database={self.database}, user={self.user})"


class AsyncDatabase:
    """Async database connection manager with pooling"""

    def __init__(self, config: Optional[AsyncDatabaseConfig] = None):
        """
        Initialize async database manager

        Args:
            config: Database configuration (defaults to env vars)
        """
        self.config = config or AsyncDatabaseConfig()
        self._pool: Optional[asyncpg.Pool] = None
        self._initialized = False

    @async_retry(max_attempts=3, delay=1.0, backoff=2.0)
    async def initialize(self):
        """Initialize async connection pool with retry logic"""
        if self._initialized:
            logger.warning("Async database already initialized")
            return

        try:
            self._pool = await asyncpg.create_pool(
                dsn=self.config.get_dsn(),
                min_size=self.config.min_size,
                max_size=self.config.max_size,
                timeout=5.0,  # 5 second connection timeout
                command_timeout=10.0,  # 10 second command timeout
            )
            self._initialized = True
            logger.info(f"[OK] Async database pool initialized: {self.config.database}")
            logger.info(
                f"   Pool size: min={self.config.min_size}, max={self.config.max_size}"
            )
        except Exception as e:
            logger.error(f"[FAIL] Failed to initialize async database pool: {e}")
            raise

    async def close(self):
        """Close all connections in pool"""
        if self._pool:
            await self._pool.close()
            self._initialized = False
            logger.info("Async database pool closed")

    def get_pool(self) -> asyncpg.Pool:
        """
        Get the connection pool

        Returns:
            asyncpg.Pool instance

        Raises:
            RuntimeError if pool not initialized
        """
        if not self._initialized or not self._pool:
            raise RuntimeError(
                "Database pool not initialized. Call initialize() first."
            )
        return self._pool

    @async_retry(max_attempts=2, delay=0.5, backoff=2.0)
    async def health_check(self) -> bool:
        """
        Check database connection health with retry

        Returns:
            True if healthy, False otherwise
        """
        if not self._initialized or not self._pool:
            return False

        try:
            async with self._pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            logger.error(f"[FAIL] Health check failed: {e}")
            return False

    def get_pool_stats(self) -> dict:
        """
        Get connection pool statistics

        Returns:
            Dictionary with pool statistics
        """
        if not self._initialized or not self._pool:
            return {
                "initialized": False,
                "size": 0,
                "free": 0,
                "min_size": self.config.min_size,
                "max_size": self.config.max_size,
            }

        return {
            "initialized": True,
            "size": self._pool.get_size(),
            "free": self._pool.get_idle_size(),
            "in_use": self._pool.get_size() - self._pool.get_idle_size(),
            "min_size": self._pool.get_min_size(),
            "max_size": self._pool.get_max_size(),
        }


# Global async database instance
async_db = AsyncDatabase()


# Convenience functions
def get_async_db() -> AsyncDatabase:
    """Get global async database instance"""
    return async_db


async def initialize_async_database():
    """Initialize global async database instance"""
    await async_db.initialize()


async def close_async_database():
    """Close global async database instance"""
    await async_db.close()


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test_connection():
        """Test database connection"""
        logging.basicConfig(level=logging.INFO)

        print("Testing async database connection...")
        print(f"Config: {async_db.config}")
        print(f"DSN: {async_db.config.get_dsn()}")

        try:
            # Initialize
            await initialize_async_database()

            # Health check
            if await async_db.health_check():
                print("[OK] Async database connection successful!")

                # Test query
                pool = async_db.get_pool()
                async with pool.acquire() as conn:
                    result = await conn.fetchval(
                        """
                        SELECT COUNT(*)
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                    """
                    )
                    print(f"Tables in database: {result}")
            else:
                print("[FAIL] Async database connection failed!")

        except Exception as e:
            print(f"[FAIL] Error: {e}")
            import traceback

            traceback.print_exc()
        finally:
            await close_async_database()

    # Run test
    asyncio.run(test_connection())
