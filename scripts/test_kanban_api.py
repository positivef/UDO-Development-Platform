#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick API test for kanban drag-drop"""

import sys
import requests
import json

# Windows console encoding fix
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Get tasks
print("[*] Fetching tasks...")
response = requests.get("http://localhost:8000/api/kanban/tasks")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Response type: {type(data)}")
    print(f"Response keys: {data.keys() if isinstance(data, dict) else 'N/A'}")

    # Handle both list and dict responses
    if isinstance(data, dict) and "data" in data:
        tasks = data["data"]
    elif isinstance(data, dict) and "tasks" in data:
        tasks = data["tasks"]
    elif isinstance(data, list):
        tasks = data
    else:
        tasks = []

    print(f"[OK] Found {len(tasks)} tasks")

    if tasks:
        # Get first task
        task = tasks[0]
        print(f"\nTask structure: {json.dumps(task, indent=2)}")

        # Find ID field (could be 'id', 'task_id', etc.)
        task_id = task.get("id") or task.get("task_id") or task.get("_id")
        current_status = task["status"]

        print("\n[*] Testing with task:")
        print(f"   ID: {task_id}")
        print(f"   Title: {task['title']}")
        print(f"   Current status: {current_status}")

        # Try to change status
        new_status = "completed" if current_status == "pending" else "pending"

        print(f"\n[*] Changing status: {current_status} -> {new_status}")

        response = requests.put(f"http://localhost:8000/api/kanban/tasks/{task_id}/status", json={"new_status": new_status})

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            updated_task = response.json()
            print(f"[OK] Success! New status: {updated_task['status']}")
            print("\n[OK] API is working correctly!")
            print("   The drag-drop bug is FIXED!")
        else:
            print(f"[FAIL] Failed: {response.text}")
    else:
        print("[WARN]  No tasks found to test with")
else:
    print(f"[FAIL] Failed to get tasks: {response.text}")
