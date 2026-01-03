#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify PostgreSQL database integration
Tests CRUD operations on project_states table
"""

import asyncio
import sys
from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv

# Fix Windows console encoding for emoji support
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# CRITICAL: Load .env BEFORE importing database modules
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"Loaded .env from: {env_path}")
else:
    print(f"Warning: .env not found at {env_path}")

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.project_context_service import ProjectContextService  # noqa: E402
from async_database import (  # noqa: E402
    async_db,
    close_async_database,
    initialize_async_database,
)


async def test_database_connection():
    """Test basic database connection"""
    print("=" * 60)
    print("Testing Database Connection")
    print("=" * 60)

    try:
        await initialize_async_database()
        pool = async_db.get_pool()

        if pool is None:
            print("[FAIL] Database pool is None")
            return False

        # Test simple query
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            print(f"[OK] Database connection successful: {result}")

            # Check if project_states table exists
            table_exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'project_states'
                )
            """
            )
            print(f"[OK] project_states table exists: {table_exists}")

            return True
    except Exception as e:
        print(f"[FAIL] Database connection failed: {e}")
        return False


async def test_list_projects():
    """Test listing projects"""
    print("\n" + "=" * 60)
    print("Testing List Projects")
    print("=" * 60)

    try:
        pool = async_db.get_pool()
        service = ProjectContextService(pool)

        result = await service.list_projects(limit=10)

        print("[OK] Projects listed successfully")
        print(f"   Total projects: {result['total']}")
        print(f"   Projects returned: {len(result['projects'])}")
        print(f"   Current project ID: {result['current_project_id']}")

        for project in result["projects"]:
            print(f"   - {project['name']} (phase: {project.get('current_phase')})")

        return True
    except Exception as e:
        print(f"[FAIL] Failed to list projects: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_save_and_load_context():
    """Test saving and loading project context"""
    print("\n" + "=" * 60)
    print("Testing Save and Load Context")
    print("=" * 60)

    try:
        pool = async_db.get_pool()
        service = ProjectContextService(pool)

        # Use existing test project ID
        project_id = UUID("22222222-2222-2222-2222-222222222222")

        # Test data
        test_udo_state = {
            "phase": "implementation",
            "confidence": 0.85,
            "recent_decisions": ["test_decision_1", "test_decision_2"],
        }

        test_ml_models = {"uncertainty_predictor": {"version": "1.0", "accuracy": 0.92}}

        test_executions = [
            {"task": "test_task_1", "result": "success"},
            {"task": "test_task_2", "result": "success"},
        ]

        # Save context
        print(f"\n[SAVE] context for project {project_id}")
        saved = await service.save_context(
            project_id=project_id,
            udo_state=test_udo_state,
            ml_models=test_ml_models,
            recent_executions=test_executions,
        )
        print("[OK] Context saved successfully")
        print(f"   Saved at: {saved['saved_at']}")

        # Load context
        print(f"\n[LOAD] context for project {project_id}")
        loaded = await service.load_context(project_id)

        if loaded:
            print("[OK] Context loaded successfully")
            print(f"   Loaded at: {loaded['loaded_at']}")
            print(f"   UDO state phase: {loaded['udo_state'].get('phase')}")
            print(f"   ML models: {list(loaded['ml_models'].keys())}")
            print(f"   Recent executions: {len(loaded['recent_executions'])}")

            # Verify data integrity
            assert loaded["udo_state"]["phase"] == test_udo_state["phase"]
            assert loaded["udo_state"]["confidence"] == test_udo_state["confidence"]
            assert len(loaded["recent_executions"]) == len(test_executions)
            print("[OK] Data integrity verified")

            return True
        else:
            print("[FAIL] Failed to load context")
            return False

    except Exception as e:
        print(f"[FAIL] Failed to save/load context: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_switch_project():
    """Test project switching"""
    print("\n" + "=" * 60)
    print("Testing Project Switching")
    print("=" * 60)

    try:
        pool = async_db.get_pool()
        service = ProjectContextService(pool)

        # Use existing test project ID
        target_project_id = UUID("22222222-2222-2222-2222-222222222222")

        print(f"\n[SWITCH] to project {target_project_id}")
        result = await service.switch_project(target_project_id=target_project_id, auto_save_current=False)

        print("[OK] Project switched successfully")
        print(f"   Project name: {result['project_name']}")
        print(f"   Context loaded: {result['context_loaded']}")
        print(f"   Message: {result['message']}")

        return True
    except Exception as e:
        print(f"[FAIL] Failed to switch project: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("PostgreSQL Database Integration Test Suite")
    print("=" * 60)

    tests = [
        ("Database Connection", test_database_connection),
        ("List Projects", test_list_projects),
        ("Save and Load Context", test_save_and_load_context),
        ("Project Switching", test_switch_project),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[FAIL] Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Cleanup
    await close_async_database()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed ({passed / total * 100:.1f}%)")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
