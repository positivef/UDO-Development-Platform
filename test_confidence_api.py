"""
Quick test for Confidence API endpoint
"""
import requests
import json

url = "http://localhost:8000/api/uncertainty/confidence"
payload = {
    "phase": "implementation",
    "context": {
        "phase": "implementation",
        "has_code": True,
        "validation_score": 0.7,
        "team_size": 3,
        "timeline_weeks": 8
    },
    "historical_outcomes": [True, True, False, True, True],
    "use_fast_mode": True
}

print("Testing Confidence API...")
print(f"POST {url}")

try:
    response = requests.post(url, json=payload, timeout=5)
    print(f"\nStatus: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print("\n✅ SUCCESS! Response:")
        print(json.dumps(data, indent=2))
    else:
        print(f"\n❌ ERROR: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"\n❌ EXCEPTION: {e}")
