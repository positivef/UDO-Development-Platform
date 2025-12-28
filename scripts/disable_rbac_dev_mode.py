"""
Temporarily disable RBAC for Kanban endpoints (Development Mode)

This script comments out RBAC dependencies to allow frontend development
without authentication. Should be re-enabled before production.

Usage:
    python scripts/disable_rbac_dev_mode.py
"""

import re
from pathlib import Path

# Files to modify
ROUTER_FILES = [
    "backend/app/routers/kanban_tasks.py",
    "backend/app/routers/kanban_dependencies.py",
    "backend/app/routers/kanban_projects.py",
    "backend/app/routers/kanban_context.py",
]

DEV_MODE_MARKER = "# DEV_MODE: RBAC disabled for development"
TODO_MARKER = "# TODO: Re-enable RBAC in Week 5 Day 2 (see UNCERTAINTY_MAP_WEEK5_ANALYSIS.md P0-1)"


def disable_rbac_in_file(file_path: Path) -> tuple[int, bool]:
    """
    Disable RBAC dependencies in a router file.

    Returns:
        (modifications_count, success)
    """
    if not file_path.exists():
        print(f"[SKIP] File not found: {file_path}")
        return 0, False

    content = file_path.read_text(encoding="utf-8")
    original_content = content
    modifications = 0

    # Pattern 1: dependencies=[Depends(require_role(UserRole.XXXX))],
    pattern1 = r"(\s+)(dependencies=\[Depends\(require_role\([^\)]+\)\)\],)"

    def replace_dependency(match):
        nonlocal modifications
        indent = match.group(1)
        dependency_line = match.group(2)

        # Check if already disabled
        if DEV_MODE_MARKER in content[max(0, match.start() - 200) : match.start()]:
            return match.group(0)  # Already disabled, skip

        modifications += 1

        # Return commented version with markers
        return f"{indent}{DEV_MODE_MARKER}\n{indent}{TODO_MARKER}\n{indent}# {dependency_line}"

    content = re.sub(pattern1, replace_dependency, content)

    # Pattern 2: current_user: dict = Depends(get_current_user)
    pattern2 = r"(\s+)(current_user:\s*dict\s*=\s*Depends\(get_current_user\))"

    def replace_current_user(match):
        nonlocal modifications
        indent = match.group(1)
        param_line = match.group(2)

        # Check if already disabled
        if "# DEV_MODE" in content[max(0, match.start() - 100) : match.start()]:
            return match.group(0)  # Already disabled, skip

        modifications += 1

        # Return commented version
        return f"{indent}# DEV_MODE: Auth disabled\n{indent}# {param_line}"

    content = re.sub(pattern2, replace_current_user, content)

    if content != original_content:
        file_path.write_text(content, encoding="utf-8")
        print(f"[OK] Modified {file_path.name}: {modifications} RBAC dependencies disabled")
        return modifications, True
    else:
        print(f"[OK] {file_path.name}: No modifications needed (already disabled or no RBAC)")
        return 0, True


def main():
    """Main execution"""
    print("=" * 70)
    print("RBAC Development Mode: Disabling RBAC for Kanban endpoints")
    print("=" * 70)
    print()

    repo_root = Path(__file__).parent.parent
    total_modifications = 0
    modified_files = []

    for router_file in ROUTER_FILES:
        file_path = repo_root / router_file
        mods, success = disable_rbac_in_file(file_path)

        if success and mods > 0:
            total_modifications += mods
            modified_files.append(router_file)

    print()
    print("=" * 70)
    print("[COMPLETE] RBAC Development Mode Applied")
    print("=" * 70)
    print(f"\n[STATS] Statistics:")
    print(f"   - Files modified: {len(modified_files)}")
    print(f"   - RBAC dependencies disabled: {total_modifications}")

    if modified_files:
        print(f"\n[FILES] Modified files:")
        for file in modified_files:
            print(f"   - {file}")

    print(f"\n[WARNING] RBAC is now disabled for development!")
    print(f"   This allows frontend to access Kanban APIs without authentication.")
    print(f"   Re-enable in Week 5 Day 2 before production deployment.")
    print(f"\n[NEXT STEPS]:")
    print(f"   1. Restart backend server (uvicorn will auto-reload)")
    print(f"   2. Test frontend at http://localhost:3000/kanban")
    print(f"   3. Verify no 403 errors in server logs")
    print(f"   4. Track re-enablement in Week 5 backlog")


if __name__ == "__main__":
    main()
