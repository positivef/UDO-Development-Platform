#!/usr/bin/env python3
"""
Database Migration Runner
Executes SQL migration files in order
"""
import sys
import os
from pathlib import Path
import psycopg2
from psycopg2 import sql
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MigrationRunner:
    """Database migration runner"""

    def __init__(self, db_config: dict):
        """
        Initialize migration runner

        Args:
            db_config: Database configuration dict
                {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'udo_dev',
                    'user': 'postgres',
                    'password': 'password'
                }
        """
        self.db_config = db_config
        self.conn = None
        self.migrations_dir = Path(__file__).parent

    def connect(self):
        """Connect to database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = False  # Use transactions
            logger.info(f"Connected to database: {self.db_config['database']}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False

    def disconnect(self):
        """Disconnect from database"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from database")

    def create_migrations_table(self):
        """Create migrations tracking table if not exists"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(255) NOT NULL UNIQUE,
                    filename VARCHAR(500) NOT NULL,
                    executed_at TIMESTAMPTZ DEFAULT NOW(),
                    execution_time_ms INTEGER,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT
                )
            """)
            self.conn.commit()
            logger.info("Migrations tracking table ready")
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to create migrations table: {e}")
            return False

    def get_executed_migrations(self) -> set:
        """Get list of already executed migrations"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT version FROM schema_migrations
                WHERE success = TRUE
                ORDER BY executed_at
            """)
            executed = {row[0] for row in cursor.fetchall()}
            logger.info(f"Found {len(executed)} executed migrations")
            return executed
        except Exception as e:
            logger.error(f"Failed to get executed migrations: {e}")
            return set()

    def get_pending_migrations(self) -> list:
        """Get list of pending migration files"""
        executed = self.get_executed_migrations()
        migration_files = sorted(self.migrations_dir.glob("*.sql"))

        pending = []
        for filepath in migration_files:
            version = filepath.stem  # e.g., "001_initial_schema"
            if version not in executed:
                pending.append(filepath)

        logger.info(f"Found {len(pending)} pending migrations")
        return pending

    def execute_migration(self, filepath: Path) -> bool:
        """
        Execute a migration file

        Args:
            filepath: Path to SQL migration file

        Returns:
            True if successful, False otherwise
        """
        version = filepath.stem
        logger.info(f"Executing migration: {version}")

        start_time = datetime.now()

        try:
            # Read SQL file
            with open(filepath, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # Execute SQL
            cursor = self.conn.cursor()
            cursor.execute(sql_content)

            # Calculate execution time
            end_time = datetime.now()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # Record migration
            cursor.execute("""
                INSERT INTO schema_migrations (version, filename, execution_time_ms, success)
                VALUES (%s, %s, %s, %s)
            """, (version, filepath.name, execution_time_ms, True))

            # Commit transaction
            self.conn.commit()

            logger.info(f"[OK] Migration completed: {version} ({execution_time_ms}ms)")
            return True

        except Exception as e:
            # Rollback on error
            self.conn.rollback()

            # Record failed migration
            try:
                cursor = self.conn.cursor()
                cursor.execute("""
                    INSERT INTO schema_migrations (version, filename, success, error_message)
                    VALUES (%s, %s, %s, %s)
                """, (version, filepath.name, False, str(e)))
                self.conn.commit()
            except:
                pass

            logger.error(f"[FAIL] Migration failed: {version}")
            logger.error(f"Error: {e}")
            return False

    def run_migrations(self, dry_run: bool = False) -> bool:
        """
        Run all pending migrations

        Args:
            dry_run: If True, only show what would be executed

        Returns:
            True if all migrations successful, False otherwise
        """
        if not self.connect():
            return False

        if not self.create_migrations_table():
            self.disconnect()
            return False

        pending = self.get_pending_migrations()

        if not pending:
            logger.info("[OK] No pending migrations")
            self.disconnect()
            return True

        if dry_run:
            logger.info("\n[EMOJI] DRY RUN - Would execute:")
            for filepath in pending:
                logger.info(f"  - {filepath.name}")
            self.disconnect()
            return True

        # Execute migrations
        logger.info(f"\n[EMOJI] Executing {len(pending)} migration(s):\n")

        success_count = 0
        for filepath in pending:
            if self.execute_migration(filepath):
                success_count += 1
            else:
                logger.error(f"\n[FAIL] Migration failed, stopping execution")
                break

        self.disconnect()

        # Summary
        logger.info(f"\n{'='*60}")
        logger.info(f"MIGRATION SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total pending: {len(pending)}")
        logger.info(f"Executed: {success_count}")
        logger.info(f"Failed: {len(pending) - success_count}")
        logger.info(f"{'='*60}\n")

        if success_count == len(pending):
            logger.info("[OK] All migrations completed successfully!")
            return True
        else:
            logger.error("[FAIL] Some migrations failed!")
            return False

    def rollback_migration(self, version: str) -> bool:
        """
        Rollback a specific migration (if rollback script exists)

        Args:
            version: Migration version to rollback

        Returns:
            True if successful, False otherwise
        """
        rollback_file = self.migrations_dir / f"{version}_rollback.sql"

        if not rollback_file.exists():
            logger.error(f"Rollback file not found: {rollback_file.name}")
            return False

        if not self.connect():
            return False

        logger.info(f"Rolling back migration: {version}")

        try:
            # Read rollback SQL
            with open(rollback_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # Execute rollback
            cursor = self.conn.cursor()
            cursor.execute(sql_content)

            # Delete migration record
            cursor.execute("""
                DELETE FROM schema_migrations
                WHERE version = %s
            """, (version,))

            self.conn.commit()

            logger.info(f"[OK] Rollback completed: {version}")
            self.disconnect()
            return True

        except Exception as e:
            self.conn.rollback()
            logger.error(f"[FAIL] Rollback failed: {e}")
            self.disconnect()
            return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Database Migration Runner')
    parser.add_argument('--dry-run', action='store_true', help='Show pending migrations without executing')
    parser.add_argument('--rollback', type=str, help='Rollback specific migration (version)')
    parser.add_argument('--host', default='localhost', help='Database host')
    parser.add_argument('--port', type=int, default=5432, help='Database port')
    parser.add_argument('--database', default='udo_dev', help='Database name')
    parser.add_argument('--user', default='postgres', help='Database user')
    parser.add_argument('--password', default='', help='Database password')

    args = parser.parse_args()

    # Database configuration
    db_config = {
        'host': args.host,
        'port': args.port,
        'database': args.database,
        'user': args.user,
        'password': args.password or os.getenv('DB_PASSWORD', 'postgres')
    }

    # Create runner
    runner = MigrationRunner(db_config)

    # Execute
    if args.rollback:
        success = runner.rollback_migration(args.rollback)
    else:
        success = runner.run_migrations(dry_run=args.dry_run)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
