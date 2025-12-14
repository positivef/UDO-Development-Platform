#!/usr/bin/env python3
"""Test Phase Transition imports"""

import sys
from pathlib import Path

# Add paths
backend_dir = Path(__file__).parent / "backend"
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(src_dir))

try:
    from app.services.phase_transition_listener import PhaseTransitionListener, create_listener_callback
    print("[OK] PhaseTransitionListener imported successfully")
except Exception as e:
    print(f"[FAIL] PhaseTransitionListener import failed: {e}")
    sys.exit(1)

try:
    from phase_state_manager import PhaseStateManager
    print("[OK] PhaseStateManager imported successfully")
except Exception as e:
    print(f"[FAIL] PhaseStateManager import failed: {e}")
    sys.exit(1)

try:
    from app.services.time_tracking_service import TimeTrackingService
    print("[OK] TimeTrackingService imported successfully")
except Exception as e:
    print(f"[FAIL] TimeTrackingService import failed: {e}")
    sys.exit(1)

print("\n[SUCCESS] All Phase Transition imports successful!")
