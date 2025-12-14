import requests
import json

try:
    print("Testing backend API...")
    response = requests.get("http://localhost:8000/api/health", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except requests.exceptions.Timeout:
    print("ERROR: Request timed out")
except requests.exceptions.ConnectionError as e:
    print(f"ERROR: Connection failed - {e}")
except Exception as e:
    print(f"ERROR: {e}")
