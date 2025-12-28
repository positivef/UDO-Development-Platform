"""
Test script for dual_write_manager.py
Validates PostgreSQL + Redis dual-write functionality
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.database import Base, engine, get_db
from app.db.dual_write_manager import DualWriteManager


async def test_dual_write():
    """Test dual-write manager functionality"""
    print("=" * 60)
    print("Testing Dual-Write Manager")
    print("=" * 60)

    # Initialize database tables
    print("\n1. Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("[OK] Tables created")

    # Initialize dual-write manager
    print("\n2. Initializing DualWriteManager...")
    postgres_url = "postgresql://udo_dev:dev_password_123@localhost:5432/udo_v3"
    redis_url = "redis://localhost:6379/0"
    manager = DualWriteManager(postgres_url, redis_url)
    await manager.initialize()
    print("[OK] Manager initialized")

    # Check initial migration status
    print("\n3. Checking migration status...")
    status = manager.get_migration_status()
    print(f"   Mode: {status['mode']}")
    print(f"   PostgreSQL Primary: {status['postgres_primary']}")
    print(f"   Total Writes: {status['total_writes']}")
    print(f"   PostgreSQL Success Rate: {status['postgres_success_rate']:.2%}")
    print(f"   Ready for Promotion: {status['ready_for_promotion']}")

    # Test write operation
    print("\n4. Testing write operation...")
    # Use proper UUID format
    test_project_id = "22222222-2222-2222-2222-222222222222"
    test_data = {
        "project_name": "UDO-Test",
        "phase": "testing",
        "confidence": 0.95,
        "tasks": ["Test dual-write", "Verify consistency"],
    }

    success, primary = await manager.write_project_context(
        project_id=test_project_id, data=test_data
    )

    if success:
        print(f"[OK] Write successful (primary: {primary})")
    else:
        print(f"[FAIL] Write failed")
        return False

    # Test read operation
    print("\n5. Testing read operation...")
    result = await manager.read_project_context(project_id=test_project_id)

    if result:
        print(f"[OK] Read successful")
        print(f"   Project Name: {result.get('project_name')}")
        print(f"   Phase: {result.get('phase')}")
        print(f"   Confidence: {result.get('confidence')}")
    else:
        print(f"[FAIL] Read failed")
        return False

    # Check final migration status
    print("\n6. Final migration status...")
    final_status = manager.get_migration_status()
    print(f"   Mode: {final_status['mode']}")
    print(f"   Total Writes: {final_status['total_writes']}")
    print(f"   PostgreSQL Success Rate: {final_status['postgres_success_rate']:.2%}")
    print(f"   Recent Consistency: {final_status['recent_consistency']:.2%}")
    print(f"   Ready for Promotion: {final_status['ready_for_promotion']}")

    print("\n" + "=" * 60)
    print("[PASS] All tests passed!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_dual_write())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
