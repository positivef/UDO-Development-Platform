"""Test uncertainty-time tracking integration"""

import json

import requests

base_url = "http://127.0.0.1:8003"

# Test 1: Health check
print("=" * 60)
print("Test 1: Health Check")
print("=" * 60)
response = requests.get(f"{base_url}/api/uncertainty/health")
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))
print()

# Test 2: Uncertainty-aware tracking
print("=" * 60)
print("Test 2: Uncertainty-Aware Tracking")
print("=" * 60)

payload = {
    "task_id": "test_integration_001",
    "task_type": "implementation",
    "phase": "implementation",
    "ai_used": "claude",
    "uncertainty_context": {
        "phase": "implementation",
        "has_code": True,
        "validation_score": 0.7,
        "team_size": 3,
        "timeline_weeks": 8,
    },
    "metadata": {"test": "uncertainty_integration"},
}

try:
    response = requests.post(
        f"{base_url}/api/uncertainty/track-with-uncertainty", json=payload
    )
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, indent=2, default=str))
    else:
        print("Error response:")
        print(response.text)
except Exception as e:
    print(f"Exception: {e}")
    import traceback

    traceback.print_exc()
