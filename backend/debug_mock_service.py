#!/usr/bin/env python3
"""Debug mock service initialization"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("Testing Mock Service Initialization")
print("=" * 60)

# Test 1: Import enable_mock_service
print("\n1. Importing enable_mock_service...")
try:
    from app.services.project_context_service import enable_mock_service, get_project_context_service
    print("   SUCCESS: Functions imported")
except ImportError as e:
    print(f"   FAILED: Import error - {e}")
    sys.exit(1)

# Test 2: Enable mock service
print("\n2. Enabling mock service...")
try:
    enable_mock_service()
    print("   SUCCESS: Mock service enabled")
except Exception as e:
    print(f"   FAILED: Error enabling - {e}")
    sys.exit(1)

# Test 3: Get service instance
print("\n3. Getting service instance...")
try:
    service = get_project_context_service()
    if service:
        print(f"   SUCCESS: Service instance retrieved")
        print(f"   Type: {type(service)}")
        print(f"   Class: {service.__class__.__name__}")
        print(f"   Module: {service.__class__.__module__}")
    else:
        print("   FAILED: Service is None")
        sys.exit(1)
except Exception as e:
    print(f"   FAILED: Error getting service - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check service methods
print("\n4. Checking service methods...")
required_methods = ['list_projects', 'get_current_project', 'save_context', 'load_context']
for method in required_methods:
    if hasattr(service, method):
        print(f"   [EMOJI] Has method: {method}")
    else:
        print(f"   [EMOJI] Missing method: {method}")

# Test 5: Check global variables
print("\n5. Checking global variables...")
try:
    from app.services import project_context_service as pcs_module
    print(f"   _use_mock_service: {pcs_module._use_mock_service}")
    print(f"   _mock_service_instance: {pcs_module._mock_service_instance}")
    print(f"   _project_context_service: {pcs_module._project_context_service}")
except Exception as e:
    print(f"   FAILED: {e}")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
