"""
Database Seed Script for User Testing

Populates database with realistic test data for 5-user testing sessions.
Creates 15 sample tasks across different phases, priorities, and states.

Run: python scripts/seed_test_data.py
"""

import asyncio
import httpx
from uuid import uuid4


async def seed_test_data():
    """Seed database with realistic test data via API"""

    print("[SEED] Seeding test data for user testing sessions...")

    # Sample tasks covering all scenarios
    test_tasks = [
        # Scenario 1: Kanban Basics - Various phases
        {
            "title": "Design API Schema",
            "description": "Create API schema for user management endpoints",
            "phase_name": "design",
            "phase_id": str(uuid4()),
            "status": "pending",
            "priority": "high",
            "estimated_hours": 6.0,
            "tags": ["api", "design", "backend"],
        },
        {
            "title": "Implement User Authentication",
            "description": "JWT authentication with refresh tokens",
            "phase_name": "implementation",
            "phase_id": str(uuid4()),
            "status": "in_progress",
            "priority": "critical",
            "estimated_hours": 12.0,
            "actual_hours": 8.0,
            "tags": ["auth", "security", "backend"],
        },
        {
            "title": "Write Unit Tests for Auth Module",
            "description": "Test coverage for authentication flows",
            "phase_name": "testing",
            "phase_id": str(uuid4()),
            "status": "pending",
            "priority": "high",
            "estimated_hours": 4.0,
            "tags": ["testing", "auth", "quality"],
        },
        {
            "title": "Database Migration Setup",
            "description": "Configure database version control",
            "phase_name": "implementation",
            "phase_id": str(uuid4()),
            "status": "completed",
            "priority": "medium",
            "estimated_hours": 3.0,
            "actual_hours": 2.5,
            "tags": ["database", "devops", "setup"],
            "completeness": 100,
        },
        # Scenario 2: Dependency Management
        {
            "title": "Implement API Endpoints",
            "description": "CRUD endpoints for user management",
            "phase_name": "implementation",
            "phase_id": str(uuid4()),
            "status": "pending",
            "priority": "high",
            "estimated_hours": 8.0,
            "tags": ["api", "backend", "crud"],
        },
        {
            "title": "Frontend Integration",
            "description": "Connect React components to backend",
            "phase_name": "implementation",
            "phase_id": str(uuid4()),
            "status": "blocked",
            "priority": "medium",
            "estimated_hours": 10.0,
            "tags": ["frontend", "react", "integration"],
        },
        # Scenario 3: Context Upload Testing
        {
            "title": "Review Code Documentation",
            "description": "Check API documentation completeness",
            "phase_name": "testing",
            "phase_id": str(uuid4()),
            "status": "pending",
            "priority": "low",
            "estimated_hours": 2.0,
            "tags": ["documentation", "quality"],
        },
        # Scenario 4: AI Suggestions
        {
            "title": "Refactor Authentication Module",
            "description": "Improve code structure and error handling",
            "phase_name": "implementation",
            "phase_id": str(uuid4()),
            "status": "pending",
            "priority": "low",
            "estimated_hours": 6.0,
            "tags": ["refactor", "auth", "quality"],
        },
        # Scenario 5: Archive & ROI
        {
            "title": "Week 1 Sprint Planning",
            "description": "Define sprint goals and tasks",
            "phase_name": "ideation",
            "phase_id": str(uuid4()),
            "status": "completed",
            "priority": "high",
            "estimated_hours": 4.0,
            "actual_hours": 3.5,
            "tags": ["planning", "sprint"],
            "completeness": 100,
        },
        # Additional tasks for comprehensive testing
        {
            "title": "Setup CI/CD Pipeline",
            "description": "Automated testing and deployment",
            "phase_name": "implementation",
            "phase_id": str(uuid4()),
            "status": "in_progress",
            "priority": "high",
            "estimated_hours": 8.0,
            "actual_hours": 5.0,
            "tags": ["devops", "ci-cd", "automation"],
            "completeness": 60,
        },
        {
            "title": "Performance Optimization",
            "description": "Improve response times and query efficiency",
            "phase_name": "testing",
            "phase_id": str(uuid4()),
            "status": "pending",
            "priority": "medium",
            "estimated_hours": 6.0,
            "tags": ["performance", "optimization"],
        },
        {
            "title": "Security Audit",
            "description": "Security review of auth system",
            "phase_name": "testing",
            "phase_id": str(uuid4()),
            "status": "pending",
            "priority": "critical",
            "estimated_hours": 10.0,
            "tags": ["security", "audit", "compliance"],
        },
        {
            "title": "User Interface Design",
            "description": "Dashboard mockups and wireframes",
            "phase_name": "design",
            "phase_id": str(uuid4()),
            "status": "completed",
            "priority": "high",
            "estimated_hours": 8.0,
            "actual_hours": 7.0,
            "tags": ["ui", "design", "frontend"],
            "completeness": 100,
        },
        {
            "title": "API Rate Limiting",
            "description": "Rate limits for public endpoints",
            "phase_name": "implementation",
            "phase_id": str(uuid4()),
            "status": "in_progress",
            "priority": "medium",
            "estimated_hours": 4.0,
            "actual_hours": 2.0,
            "tags": ["api", "security", "rate-limiting"],
            "completeness": 50,
        },
        {
            "title": "End-to-End Testing",
            "description": "Playwright tests for user workflows",
            "phase_name": "testing",
            "phase_id": str(uuid4()),
            "status": "pending",
            "priority": "high",
            "estimated_hours": 12.0,
            "tags": ["testing", "e2e", "playwright"],
        },
    ]

    # API base URL
    base_url = "http://localhost:8000"

    # Use httpx async client
    async with httpx.AsyncClient() as client:
        created_count = 0
        error_count = 0

        for i, task_data in enumerate(test_tasks, 1):
            try:
                # Add project_id (required field)
                task_data["project_id"] = "UDO-Platform"

                # Create task via API
                response = await client.post(
                    f"{base_url}/api/kanban/tasks",
                    json=task_data,
                    timeout=10.0,
                )

                if response.status_code == 201:
                    created_count += 1
                    task = response.json().get("data", {})
                    task_id = task.get("task_id", "unknown")
                    title = task.get("title", task_data["title"])
                    print(f"  [OK] [{i:2d}/15] Created: {title} (ID: {task_id})")
                else:
                    error_count += 1
                    print(
                        f"  [FAIL] [{i:2d}/15] Failed: {task_data['title']} "
                        f"(Status: {response.status_code}, Error: {response.text[:100]})"
                    )

            except Exception as e:
                error_count += 1
                print(f"  [ERROR] [{i:2d}/15] Exception: {task_data['title']} (Error: {str(e)[:100]})")

    print("\n[SUCCESS] Seeding complete!")
    print(f"   [OK] Created: {created_count}/15 tasks")
    if error_count > 0:
        print(f"   [ERROR] Errors: {error_count}/15 tasks")
    print(f"\n[INFO] Database now contains {created_count} sample tasks for user testing")


async def clear_test_data():
    """Clear all test data from database"""
    print("[CLEAR] Clearing test data...")

    base_url = "http://localhost:8000"

    async with httpx.AsyncClient() as client:
        # Fetch all tasks for UDO-Platform
        response = await client.get(
            f"{base_url}/api/kanban/tasks",
            params={"project_id": "UDO-Platform", "limit": 100},
            timeout=10.0,
        )

        if response.status_code != 200:
            print(f"[FAIL] Failed to fetch tasks: {response.text}")
            return

        data = response.json().get("data", {})
        tasks = data.get("tasks", [])

        deleted_count = 0
        for task in tasks:
            task_id = task.get("task_id")
            if not task_id:
                continue

            try:
                del_response = await client.delete(
                    f"{base_url}/api/kanban/tasks/{task_id}",
                    timeout=5.0,
                )
                if del_response.status_code == 200:
                    deleted_count += 1
                    print(f"  [OK] Deleted: {task.get('title')} (ID: {task_id})")
            except Exception as e:
                print(f"  [ERROR] Failed to delete {task_id}: {e}")

    print(f"\n[SUCCESS] Cleanup complete! Deleted {deleted_count} tasks.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        asyncio.run(clear_test_data())
    else:
        asyncio.run(seed_test_data())
