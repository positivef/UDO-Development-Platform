#!/usr/bin/env python3
"""Test Phase Transition imports from backend directory context"""

import sys
from pathlib import Path

# Mimic main.py path setup
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

print(f"[DEBUG] sys.path[0]: {sys.path[0]}")
print(f"[DEBUG] sys.path[1]: {sys.path[1]}")

# Test imports exactly as they appear in main.py
try:
    from app.services.phase_transition_listener import PhaseTransitionListener, create_listener_callback
    print("[OK] PhaseTransitionListener imported")
except Exception as e:
    print(f"[FAIL] PhaseTransitionListener: {e}")
    sys.exit(1)

try:
    from phase_state_manager import PhaseStateManager
    print("[OK] PhaseStateManager imported")
except Exception as e:
    print(f"[FAIL] PhaseStateManager: {e}")
    sys.exit(1)

try:
    from app.services.time_tracking_service import TimeTrackingService
    print("[OK] TimeTrackingService imported")
except Exception as e:
    print(f"[FAIL] TimeTrackingService: {e}")
    sys.exit(1)

print("\n[SUCCESS] All imports work from backend directory context!")
print("PHASE_TRANSITION_AVAILABLE should be True in main.py")
