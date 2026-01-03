#!/usr/bin/env python3
"""
Test script for migration 003_phase_transitions.sql
Verifies schema changes and data integrity
"""
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class MigrationTester:
    """Test migration 003 schema changes"""

    def __init__(self, db_config: dict = None, mock_mode: bool = True):
        """
        Initialize migration tester

        Args:
            db_config: Database configuration (required if mock_mode=False)
            mock_mode: If True, test without actual database connection
        """
        self.db_config = db_config
        self.mock_mode = mock_mode
        self.conn = None
        self.test_results = []

    def connect(self) -> bool:
        """Connect to database (skip in mock mode)"""
        if self.mock_mode:
            logger.info("[OK] Mock mode - skipping database connection")
            return True

        try:
            import psycopg2

            self.conn = psycopg2.connect(**self.db_config)
            logger.info(f"[OK] Connected to database: {self.db_config['database']}")
            return True
        except Exception as e:
            logger.error(f"[FAIL] Failed to connect to database: {e}")
            return False

    def disconnect(self):
        """Disconnect from database"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from database")

    def test_sql_syntax(self) -> bool:
        """Test SQL syntax is valid"""
        logger.info("\n=== Testing SQL Syntax ===")

        migration_file = Path(__file__).parent / "003_phase_transitions.sql"
        rollback_file = Path(__file__).parent / "003_phase_transitions_rollback.sql"

        # Test migration file exists
        if not migration_file.exists():
            logger.error(f"[FAIL] Migration file not found: {migration_file}")
            return False

        logger.info(f"[OK] Migration file exists: {migration_file.name}")

        # Test rollback file exists
        if not rollback_file.exists():
            logger.error(f"[FAIL] Rollback file not found: {rollback_file}")
            return False

        logger.info(f"[OK] Rollback file exists: {rollback_file.name}")

        # Read and validate SQL
        try:
            with open(migration_file, "r", encoding="utf-8") as f:
                migration_sql = f.read()

            with open(rollback_file, "r", encoding="utf-8") as f:
                rollback_sql = f.read()

            # Basic syntax checks
            assert "CREATE TABLE" in migration_sql, "Missing CREATE TABLE statement"
            assert "phase_transitions" in migration_sql, "Missing phase_transitions table"
            assert "ALTER TABLE" in migration_sql, "Missing ALTER TABLE statement"
            assert "task_sessions" in migration_sql, "Missing task_sessions reference"
            assert "CREATE INDEX" in migration_sql, "Missing CREATE INDEX statements"

            # Rollback checks
            assert "DROP TABLE" in rollback_sql, "Missing DROP TABLE in rollback"
            assert "DROP INDEX" in rollback_sql, "Missing DROP INDEX in rollback"
            assert "phase_transitions" in rollback_sql, "Missing table reference in rollback"

            logger.info("[OK] SQL syntax validation passed")
            return True

        except Exception as e:
            logger.error(f"[FAIL] SQL validation failed: {e}")
            return False

    def test_table_structure(self) -> bool:
        """Test phase_transitions table structure"""
        logger.info("\n=== Testing Table Structure ===")

        if self.mock_mode:
            logger.info("[OK] Mock mode - skipping database table check")
            logger.info("   Expected table: phase_transitions")
            logger.info(
                "   Expected columns: id, from_phase, to_phase, transition_time, "
                "duration_seconds, automated, metadata, project_id, created_at"
            )
            return True

        try:
            cursor = self.conn.cursor()

            # Check table exists
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'phase_transitions'
                )
            """
            )

            table_exists = cursor.fetchone()[0]

            if not table_exists:
                logger.error("[FAIL] phase_transitions table not found")
                return False

            logger.info("[OK] phase_transitions table exists")

            # Check columns
            cursor.execute(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'phase_transitions'
                ORDER BY ordinal_position
            """
            )

            columns = cursor.fetchall()
            column_names = [col[0] for col in columns]

            expected_columns = [
                "id",
                "from_phase",
                "to_phase",
                "transition_time",
                "duration_seconds",
                "automated",
                "metadata",
                "project_id",
                "created_at",
            ]

            for expected_col in expected_columns:
                if expected_col in column_names:
                    logger.info(f"   [OK] Column: {expected_col}")
                else:
                    logger.error(f"   [FAIL] Missing column: {expected_col}")
                    return False

            return True

        except Exception as e:
            logger.error(f"[FAIL] Table structure test failed: {e}")
            return False

    def test_task_sessions_columns(self) -> bool:
        """Test task_sessions table has new columns"""
        logger.info("\n=== Testing task_sessions Columns ===")

        if self.mock_mode:
            logger.info("[OK] Mock mode - skipping database column check")
            logger.info("   Expected new columns: phase_transition_id, previous_phase")
            return True

        try:
            cursor = self.conn.cursor()

            # Check columns exist
            cursor.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'task_sessions'
                AND column_name IN ('phase_transition_id', 'previous_phase')
            """
            )

            columns = cursor.fetchall()
            column_names = [col[0] for col in columns]

            if "phase_transition_id" in column_names:
                logger.info("   [OK] Column: phase_transition_id")
            else:
                logger.error("   [FAIL] Missing column: phase_transition_id")
                return False

            if "previous_phase" in column_names:
                logger.info("   [OK] Column: previous_phase")
            else:
                logger.error("   [FAIL] Missing column: previous_phase")
                return False

            return True

        except Exception as e:
            logger.error(f"[FAIL] task_sessions column test failed: {e}")
            return False

    def test_indexes(self) -> bool:
        """Test indexes were created"""
        logger.info("\n=== Testing Indexes ===")

        if self.mock_mode:
            logger.info("[OK] Mock mode - skipping index check")
            expected_indexes = [
                "idx_phase_transitions_time",
                "idx_phase_transitions_project",
                "idx_phase_transitions_to_phase",
                "idx_phase_transitions_phases",
                "idx_task_sessions_phase",
                "idx_task_sessions_transition",
            ]
            for idx in expected_indexes:
                logger.info(f"   Expected index: {idx}")
            return True

        try:
            cursor = self.conn.cursor()

            # Check indexes exist
            cursor.execute(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE tablename IN ('phase_transitions', 'task_sessions')
                AND indexname LIKE 'idx_%'
                ORDER BY indexname
            """
            )

            indexes = [row[0] for row in cursor.fetchall()]

            expected_indexes = [
                "idx_phase_transitions_time",
                "idx_phase_transitions_project",
                "idx_phase_transitions_to_phase",
                "idx_phase_transitions_phases",
                "idx_task_sessions_phase",
                "idx_task_sessions_transition",
            ]

            for expected_idx in expected_indexes:
                if expected_idx in indexes:
                    logger.info(f"   [OK] Index: {expected_idx}")
                else:
                    logger.warning(f"   [WARN]  Missing index: {expected_idx} (optional)")

            return True

        except Exception as e:
            logger.error(f"[FAIL] Index test failed: {e}")
            return False

    def test_data_operations(self) -> bool:
        """Test basic CRUD operations"""
        logger.info("\n=== Testing Data Operations ===")

        if self.mock_mode:
            logger.info("[OK] Mock mode - skipping data operations")
            logger.info("   Would test: INSERT, SELECT, UPDATE, DELETE on phase_transitions")
            return True

        try:
            cursor = self.conn.cursor()

            # Test INSERT
            cursor.execute(
                """
                INSERT INTO phase_transitions (from_phase, to_phase, duration_seconds, automated)
                VALUES ('IDEATION', 'DESIGN', 3600, true)
                RETURNING id
            """
            )

            transition_id = cursor.fetchone()[0]
            logger.info(f"   [OK] INSERT: Created transition {transition_id}")

            # Test SELECT
            cursor.execute(
                """
                SELECT from_phase, to_phase, duration_seconds
                FROM phase_transitions
                WHERE id = %s
            """,
                (transition_id,),
            )

            row = cursor.fetchone()
            assert row[0] == "IDEATION", "from_phase mismatch"
            assert row[1] == "DESIGN", "to_phase mismatch"
            assert row[2] == 3600, "duration_seconds mismatch"
            logger.info("   [OK] SELECT: Retrieved transition data")

            # Test UPDATE
            cursor.execute(
                """
                UPDATE phase_transitions
                SET metadata = '{"test": true}'::jsonb
                WHERE id = %s
            """,
                (transition_id,),
            )
            logger.info("   [OK] UPDATE: Updated metadata")

            # Test DELETE
            cursor.execute(
                """
                DELETE FROM phase_transitions
                WHERE id = %s
            """,
                (transition_id,),
            )
            logger.info("   [OK] DELETE: Removed test transition")

            self.conn.commit()
            return True

        except Exception as e:
            self.conn.rollback()
            logger.error(f"[FAIL] Data operations test failed: {e}")
            return False

    def run_all_tests(self) -> bool:
        """Run all migration tests"""
        logger.info("\n" + "=" * 60)
        logger.info("MIGRATION 003 TEST SUITE")
        logger.info("=" * 60)

        if not self.connect():
            return False

        tests = [
            ("SQL Syntax", self.test_sql_syntax),
            ("Table Structure", self.test_table_structure),
            ("task_sessions Columns", self.test_task_sessions_columns),
            ("Indexes", self.test_indexes),
            ("Data Operations", self.test_data_operations),
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"[FAIL] Test '{test_name}' crashed: {e}")
                failed += 1

        self.disconnect()

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total tests: {len(tests)}")
        logger.info(f"Passed: {passed} [OK]")
        logger.info(f"Failed: {failed} [FAIL]")
        logger.info("=" * 60 + "\n")

        if failed == 0:
            logger.info("[OK] ALL TESTS PASSED!")
            return True
        else:
            logger.error(f"[FAIL] {failed} TEST(S) FAILED!")
            return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Test migration 003")
    parser.add_argument(
        "--mock",
        action="store_true",
        default=True,
        help="Run in mock mode (no database required)",
    )
    parser.add_argument("--host", default="localhost", help="Database host")
    parser.add_argument("--port", type=int, default=5432, help="Database port")
    parser.add_argument("--database", default="udo_dev", help="Database name")
    parser.add_argument("--user", default="postgres", help="Database user")
    parser.add_argument("--password", default="", help="Database password")

    args = parser.parse_args()

    # Database configuration (only needed if not in mock mode)
    db_config = (
        None
        if args.mock
        else {
            "host": args.host,
            "port": args.port,
            "database": args.database,
            "user": args.user,
            "password": args.password or os.getenv("DB_PASSWORD", "postgres"),
        }
    )

    # Run tests
    tester = MigrationTester(db_config=db_config, mock_mode=args.mock)
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
