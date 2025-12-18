"""
Database Connection and Configuration
PostgreSQL connection management with connection pooling
"""
import os
from typing import Optional, Dict, Any
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration"""

    def __init__(self):
        """Load configuration from environment variables"""
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', '5432'))
        self.database = os.getenv('DB_NAME', 'udo_dev')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', 'postgres')

        # Connection pool settings
        self.min_connections = int(os.getenv('DB_POOL_MIN', '2'))
        self.max_connections = int(os.getenv('DB_POOL_MAX', '10'))

    def get_connection_params(self) -> Dict[str, Any]:
        """Get connection parameters as dict"""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password
        }

    def __repr__(self):
        return f"DatabaseConfig(host={self.host}, port={self.port}, database={self.database}, user={self.user})"


class Database:
    """Database connection manager with pooling"""

    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize database manager

        Args:
            config: Database configuration (defaults to env vars)
        """
        self.config = config or DatabaseConfig()
        self._pool: Optional[pool.SimpleConnectionPool] = None
        self._initialized = False

    def initialize(self):
        """Initialize connection pool"""
        if self._initialized:
            logger.warning("Database already initialized")
            return

        try:
            self._pool = pool.SimpleConnectionPool(
                self.config.min_connections,
                self.config.max_connections,
                **self.config.get_connection_params()
            )
            self._initialized = True
            logger.info(f"[OK] Database pool initialized: {self.config.database}")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    def close(self):
        """Close all connections in pool"""
        if self._pool:
            self._pool.closeall()
            self._initialized = False
            logger.info("Database pool closed")

    @contextmanager
    def get_connection(self, cursor_factory=RealDictCursor):
        """
        Get a database connection from pool

        Args:
            cursor_factory: Cursor factory (default: RealDictCursor for dict results)

        Yields:
            Database connection

        Example:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM projects")
                results = cursor.fetchall()
        """
        if not self._initialized:
            self.initialize()

        conn = None
        try:
            conn = self._pool.getconn()
            conn.cursor_factory = cursor_factory
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                self._pool.putconn(conn)

    @contextmanager
    def get_cursor(self, commit: bool = True):
        """
        Get a database cursor (convenience method)

        Args:
            commit: Auto-commit on success

        Yields:
            Database cursor

        Example:
            with db.get_cursor() as cursor:
                cursor.execute("INSERT INTO projects (...) VALUES (...)")
                # Auto-commits on exit
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception as e:
                conn.rollback()
                raise

    async def execute(self, query: str, params: tuple = None, fetch: str = None):
        """
        Execute a query (async-compatible wrapper)

        Args:
            query: SQL query
            params: Query parameters
            fetch: 'one', 'all', or None

        Returns:
            Query results or None
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)

            if fetch == 'one':
                return cursor.fetchone()
            elif fetch == 'all':
                return cursor.fetchall()
            return None

    def health_check(self) -> bool:
        """
        Check database connection health

        Returns:
            True if healthy, False otherwise
        """
        try:
            with self.get_cursor(commit=False) as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Global database instance
db = Database()


# Convenience functions
def get_db() -> Database:
    """Get global database instance"""
    return db


def initialize_database():
    """Initialize global database instance"""
    db.initialize()


def close_database():
    """Close global database instance"""
    db.close()


# Example usage
if __name__ == "__main__":
    # Test database connection
    logging.basicConfig(level=logging.INFO)

    print("Testing database connection...")
    print(f"Config: {db.config}")

    try:
        # Initialize
        initialize_database()

        # Health check
        if db.health_check():
            print("[OK] Database connection successful!")

            # Test query
            with db.get_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """)
                result = cursor.fetchone()
                print(f"Tables in database: {result['count']}")
        else:
            print("[FAIL] Database connection failed!")

    except Exception as e:
        print(f"[FAIL] Error: {e}")
    finally:
        close_database()
