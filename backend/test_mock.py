#!/usr/bin/env python3
"""Test mock service availability"""

from app.services.project_context_service import (enable_mock_service,
                                                  get_project_context_service)

# Enable mock service mode
print("Enabling mock service mode...")
enable_mock_service()

# Try to get the service
print("Getting project context service...")
service = get_project_context_service()

if service:
    print(f"Service available: {type(service)}")
    print(f"Service class name: {service.__class__.__name__}")

    # Check if it has the required methods
    required_methods = [
        "list_projects",
        "get_current_project",
        "save_context",
        "load_context",
    ]
    for method in required_methods:
        if hasattr(service, method):
            print(f"  Has method: {method}")
        else:
            print(f"  Missing method: {method}")
else:
    print("Service is None")
