#!/usr/bin/env python3
"""Quick migration status checker"""
import psycopg2
from psycopg2 import sql

# Database configuration
db_config = {
    'host': 'localhost',
    'port': 5432,
    'database': 'udo_v3',
    'user': 'udo_dev',
    'password': 'dev_password_123'
}

try:
    # Connect to database
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    print("✅ Connected to database: udo_v3\n")

    # Check if migrations table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'schema_migrations'
        )
    """)
    migrations_table_exists = cursor.fetchone()[0]

    if migrations_table_exists:
        print("✅ Migrations table exists\n")

        # Get executed migrations
        cursor.execute("""
            SELECT version, filename, executed_at, execution_time_ms, success
            FROM schema_migrations
            ORDER BY executed_at
        """)
        migrations = cursor.fetchall()

        if migrations:
            print(f"📋 Executed migrations ({len(migrations)}):\n")
            for version, filename, executed_at, exec_time_ms, success in migrations:
                status = "✅" if success else "❌"
                print(f"{status} {version:30} | {filename:40} | {executed_at} | {exec_time_ms}ms")
        else:
            print("⚠️ No migrations executed yet")
    else:
        print("⚠️ Migrations table does not exist (no migrations run yet)")

    print("\n" + "="*80)

    # Check if kanban schema exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.schemata
            WHERE schema_name = 'kanban'
        )
    """)
    kanban_schema_exists = cursor.fetchone()[0]

    if kanban_schema_exists:
        print("\n✅ Kanban schema exists\n")

        # Get kanban tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'kanban'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()

        if tables:
            print(f"📊 Kanban tables ({len(tables)}):\n")
            for (table_name,) in tables:
                # Get row count
                cursor.execute(sql.SQL("SELECT COUNT(*) FROM kanban.{}").format(sql.Identifier(table_name)))
                count = cursor.fetchone()[0]
                print(f"   - {table_name:30} ({count} rows)")
        else:
            print("⚠️ No tables in kanban schema")
    else:
        print("\n❌ Kanban schema does NOT exist")
        print("   → Need to run migration: 004_kanban_schema.sql")

    cursor.close()
    conn.close()

except psycopg2.OperationalError as e:
    print(f"❌ Database connection failed: {e}")
    print("\nPossible reasons:")
    print("  1. PostgreSQL is not running")
    print("  2. Database 'udo_v3' does not exist")
    print("  3. User 'udo_dev' does not exist or has wrong password")
except Exception as e:
    print(f"❌ Error: {e}")
