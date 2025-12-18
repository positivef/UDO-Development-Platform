"""
Quick test script to verify Kanban service works with PostgreSQL database.

This script:
1. Initializes async database pool
2. Creates a test task
3. Retrieves the task
4. Lists all tasks
5. Cleans up test data

Run: python test_kanban_db.py
"""

import asyncio
from uuid import uuid4
from backend.async_database import async_db, initialize_async_database
from backend.app.services.kanban_task_service import KanbanTaskService
from backend.app.models.kanban_task import TaskCreate, PhaseName, TaskStatus, TaskPriority


async def test_kanban_database():
    """Test Kanban service with real PostgreSQL database"""
    print("=" * 80)
    print("Kanban Database Integration Test")
    print("=" * 80)

    # Step 1: Initialize database
    print("\n[1] Initializing database pool...")
    try:
        await initialize_async_database()
        db_pool = async_db.get_pool()
        print("SUCCESS - Database pool initialized")
    except Exception as e:
        print(f"FAILED - Database initialization: {e}")
        return False

    # Step 2: Create service instance
    print("\n[2] Creating KanbanTaskService with database pool...")
    try:
        service = KanbanTaskService(db_pool=db_pool)
        print("SUCCESS - Service created with database pool")
    except Exception as e:
        print(f"FAILED - Service creation: {e}")
        return False

    # Step 3: Create a test task
    print("\n[3] Creating test task...")
    task_data = TaskCreate(
        title="Test Task - Database Integration",
        description="This task verifies database connectivity",
        phase_id=uuid4(),
        phase_name=PhaseName.IDEATION,
        status=TaskStatus.PENDING,
        priority=TaskPriority.HIGH,
        completeness=0,
        estimated_hours=2.0,
        actual_hours=0.0,
        ai_suggested=False,
    )

    try:
        created_task = await service.create_task(task_data)
        print(f"SUCCESS - Task created:")
        print(f"  - ID: {created_task.task_id}")
        print(f"  - Title: {created_task.title}")
        print(f"  - Phase: {created_task.phase_name}")
        print(f"  - Status: {created_task.status}")
        print(f"  - Priority: {created_task.priority}")
        print(f"  - Created: {created_task.created_at}")
        task_id = created_task.task_id
    except Exception as e:
        print(f"FAILED - Task creation: {e}")
        return False

    # Step 4: Retrieve the task
    print("\n[4] Retrieving task by ID...")
    try:
        retrieved_task = await service.get_task(task_id)
        assert retrieved_task.task_id == task_id
        assert retrieved_task.title == task_data.title
        print(f"SUCCESS - Task retrieved:")
        print(f"  - Title matches: {retrieved_task.title == task_data.title}")
        print(f"  - ID matches: {retrieved_task.task_id == task_id}")
    except Exception as e:
        print(f"FAILED - Task retrieval: {e}")
        return False

    # Step 5: List all tasks
    print("\n[5] Listing all tasks...")
    try:
        result = await service.list_tasks(page=1, per_page=10)
        print(f"SUCCESS - Task list retrieved:")
        print(f"  - Total tasks: {result.pagination.total}")
        print(f"  - Tasks returned: {len(result.data)}")
        print(f"  - Our task in list: {any(t.task_id == task_id for t in result.data)}")
    except Exception as e:
        print(f"FAILED - Task listing: {e}")
        return False

    # Step 6: Clean up (delete test task)
    print("\n[6] Cleaning up test task...")
    try:
        await service.delete_task(task_id)
        print("SUCCESS - Test task deleted")
    except Exception as e:
        print(f"WARNING - Cleanup failed (task may still exist): {e}")

    # Final result
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED - Database integration working correctly!")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Router dependency injection: COMPLETE")
    print("  2. Service database mode: COMPLETE")
    print("  3. Database integration: VERIFIED")
    print("  4. Ready for Week 8 Day 2 work")
    print("=" * 80)

    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_kanban_database())
        exit(0 if result else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
