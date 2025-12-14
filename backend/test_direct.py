#!/usr/bin/env python3
"""Direct test of get_project_context_service"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("Direct Test of get_project_context_service")
print("=" * 60)

# Step 1: Enable mock service
print("\nStep 1: Enabling mock service...")
try:
    from app.services.project_context_service import enable_mock_service
    enable_mock_service()
    print("  SUCCESS")
except Exception as e:
    print(f"  FAILED: {e}")
    sys.exit(1)

# Step 2: Get service
print("\nStep 2: Getting service...")
try:
    from app.services.project_context_service import get_project_context_service
    service = get_project_context_service()
    print(f"  Type: {type(service)}")
    print(f"  Class: {service.__class__.__name__ if service else 'None'}")
except Exception as e:
    print(f"  FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Check global variables
print("\nStep 3: Checking global variables...")
try:
    import app.services.project_context_service as pcs
    print(f"  _use_mock_service: {pcs._use_mock_service}")
    print(f"  _mock_service_instance: {type(pcs._mock_service_instance) if pcs._mock_service_instance else 'None'}")
    print(f"  _project_context_service: {type(pcs._project_context_service) if pcs._project_context_service else 'None'}")
except Exception as e:
    print(f"  FAILED: {e}")

# Step 4: Now import router and test get_service
print("\nStep 4: Testing router's get_service...")
try:
    from app.routers.project_context import get_service
    router_service = get_service()
    print(f"  Type: {type(router_service)}")
    print(f"  Class: {router_service.__class__.__name__ if router_service else 'None'}")
except Exception as e:
    print(f"  FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test completed")
print("=" * 60)
