#!/usr/bin/env python3
"""
Script to add time tracking router to main.py

This script safely adds the time tracking router import and registration
to the main.py file.
"""

import sys
from pathlib import Path


def add_time_tracking_router():
    """Add time tracking router to main.py"""
    main_py = Path(__file__).parent.parent / "main.py"

    if not main_py.exists():
        print(f"Error: {main_py} not found")
        return False

    with open(main_py, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if already added
    if "time_tracking_router" in content:
        print("Time tracking router already registered in main.py")
        return True

    print("Adding time tracking router to main.py...")

    # Add import
    old_import = "from app.routers import version_history_router, quality_metrics_router, constitutional_router"
    new_import = "from app.routers import version_history_router, quality_metrics_router, constitutional_router, time_tracking_router"

    content = content.replace(old_import, new_import)

    # Add router availability flag
    old_flag = """except ImportError as e:
    ROUTERS_AVAILABLE = False
    CONSTITUTIONAL_ROUTER_AVAILABLE = False
    logger.warning(f"Routers not available: {e}")"""

    new_flag = """    TIME_TRACKING_ROUTER_AVAILABLE = True
except ImportError as e:
    ROUTERS_AVAILABLE = False
    CONSTITUTIONAL_ROUTER_AVAILABLE = False
    TIME_TRACKING_ROUTER_AVAILABLE = False
    logger.warning(f"Routers not available: {e}")"""

    content = content.replace(old_flag, new_flag)

    # Add router registration (after Obsidian router)
    old_registration = """if OBSIDIAN_ROUTER_AVAILABLE:
    app.include_router(obsidian_router)
    logger.info("[OK] Obsidian router included (Knowledge Management)")"""

    new_registration = """if OBSIDIAN_ROUTER_AVAILABLE:
    app.include_router(obsidian_router)
    logger.info("[OK] Obsidian router included (Knowledge Management)")

if TIME_TRACKING_ROUTER_AVAILABLE:
    app.include_router(time_tracking_router)
    logger.info("[OK] Time Tracking router included (ROI Measurement)")"""

    content = content.replace(old_registration, new_registration)

    # Write back
    with open(main_py, "w", encoding="utf-8") as f:
        f.write(content)

    print("[OK] Time tracking router successfully added to main.py")
    return True


if __name__ == "__main__":
    success = add_time_tracking_router()
    sys.exit(0 if success else 1)
