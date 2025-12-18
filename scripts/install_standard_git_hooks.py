#!/usr/bin/env python3
"""
Standard Level Git Hooks Installer

Standard [EMOJI] [EMOJI] [EMOJI] Git Hooks [EMOJI]
- pre-commit: [EMOJI] [EMOJI] [EMOJI], [EMOJI] [EMOJI] [EMOJI]
- pre-push: [EMOJI] [EMOJI] [EMOJI]
- post-commit: [EMOJI] [EMOJI] [EMOJI]
"""

import os
import sys
import subprocess
import json
from pathlib import Path


class StandardGitHooksInstaller:
    def __init__(self, project_root=None):
        self.project_root = Path(project_root or os.getcwd())
        self.git_hooks_dir = self.project_root / ".git" / "hooks"
        self.scripts_dir = self.project_root / "scripts" / "git-hooks"

    def install_all(self):
        """[EMOJI] Git hooks [EMOJI]"""
        print("[EMOJI] Installing Standard Level Git Hooks...")

        # hooks [EMOJI] [EMOJI]
        self.scripts_dir.mkdir(parents=True, exist_ok=True)

        # [EMOJI] hook [EMOJI]
        self.install_pre_commit()
        self.install_pre_push()
        self.install_post_commit()

        print("[OK] Standard Git Hooks installed successfully!")
        print("\n[EMOJI] Installed hooks:")
        print("  - pre-commit: [EMOJI] [EMOJI], [EMOJI] [EMOJI] [EMOJI]")
        print("  - pre-push: [EMOJI] [EMOJI] [EMOJI]")
        print("  - post-commit: [EMOJI] [EMOJI] [EMOJI] [EMOJI]")

    def install_pre_commit(self):
        """pre-commit hook [EMOJI]"""

        hook_content = '''#!/usr/bin/env python3
"""
Standard Level Pre-commit Hook
- [EMOJI] [EMOJI] [EMOJI]
- [EMOJI] [EMOJI] [EMOJI]
- [EMOJI] [EMOJI] [EMOJI] [EMOJI]
"""

import subprocess
import sys
import re
import json
from pathlib import Path

def get_current_branch():
    """[EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def get_module_from_files():
    """[EMOJI] [EMOJI] [EMOJI] ID [EMOJI]"""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True
    )

    files = result.stdout.strip().split("\\n")

    # [EMOJI] [EMOJI] [EMOJI] ID [EMOJI] ([EMOJI]: backend/auth/login.py -> auth/login)
    modules = set()
    for file in files:
        if file.startswith("backend/") and file.endswith(".py"):
            parts = file.replace("backend/", "").replace(".py", "").split("/")
            if len(parts) >= 2:
                module_id = "/".join(parts[:2])
                modules.add(module_id)

    return list(modules)

def check_module_ownership(module_id):
    """[EMOJI] [EMOJI] [EMOJI] (Standard [EMOJI])"""
    # TODO: Redis[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]
    # [EMOJI] [EMOJI] [EMOJI]

    ownership_file = Path(".udo/module_ownership.json")
    if not ownership_file.exists():
        return True, None

    with open(ownership_file) as f:
        ownerships = json.load(f)

    if module_id in ownerships:
        owner = ownerships[module_id].get("developer")
        # [EMOJI] [EMOJI] [EMOJI] (git config user.name)
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True
        )
        current_user = result.stdout.strip()

        if owner != current_user:
            return False, owner

    return True, None

def check_commit_message():
    """[EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
    with open(".git/COMMIT_EDITMSG", "r") as f:
        message = f.read()

    # Standard [EMOJI]: [EMOJI] ID[EMOJI] [EMOJI] [EMOJI]
    module_pattern = r"\\[(\\w+/\\w+)\\]"
    if not re.search(module_pattern, message):
        return False, "[EMOJI] [EMOJI] [EMOJI] ID[EMOJI] [EMOJI]. [EMOJI]: [auth/login] [EMOJI] [EMOJI] [EMOJI]"

    return True, None

def main():
    print("[EMOJI] Standard Level Pre-commit checks...")

    # 1. [EMOJI] [EMOJI] [EMOJI]
    branch = get_current_branch()
    modules = get_module_from_files()

    if modules and branch != "main" and branch != "develop":
        # Standard [EMOJI]: feature/module-id [EMOJI] [EMOJI]
        for module_id in modules:
            expected_branch = f"feature/{module_id.replace('/', '-')}"
            if not branch.startswith(expected_branch):
                print(f"[WARN]  WARNING: [EMOJI] [EMOJI] '{expected_branch}'[EMOJI] [EMOJI] ([EMOJI]: {branch})")

    # 2. [EMOJI] [EMOJI] [EMOJI]
    for module_id in modules:
        owned, owner = check_module_ownership(module_id)
        if not owned:
            print(f"[FAIL] ERROR: [EMOJI] '{module_id}'[EMOJI]([EMOJI]) {owner}[EMOJI] [EMOJI] [EMOJI]!")
            print("   [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI].")
            return 1

    # 3. [EMOJI] [EMOJI] [EMOJI]
    msg_valid, msg_error = check_commit_message()
    if not msg_valid:
        print(f"[FAIL] ERROR: {msg_error}")
        return 1

    print("[OK] Pre-commit checks passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

        hook_path = self.git_hooks_dir / "pre-commit"
        self.write_hook(hook_path, hook_content)

    def install_pre_push(self):
        """pre-push hook [EMOJI]"""

        hook_content = '''#!/usr/bin/env python3
"""
Standard Level Pre-push Hook
- [EMOJI] [EMOJI] [EMOJI] ([EMOJI])
- [EMOJI] [EMOJI] [EMOJI] ([EMOJI])
"""

import subprocess
import sys
import json
from pathlib import Path

def run_tests():
    """[EMOJI] [EMOJI]"""
    print("🧪 Running tests before push (Standard Level requirement)...")

    # Python [EMOJI] [EMOJI]
    if Path("pytest.ini").exists() or Path("setup.cfg").exists():
        result = subprocess.run(
            ["python", "-m", "pytest", "--tb=short"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("[FAIL] Tests failed! Fix tests before pushing.")
            print(result.stdout)
            return False

    # JavaScript [EMOJI] [EMOJI]
    if Path("package.json").exists():
        with open("package.json") as f:
            package = json.load(f)

        if "test" in package.get("scripts", {}):
            result = subprocess.run(
                ["npm", "test"],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print("[FAIL] JavaScript tests failed!")
                print(result.stdout)
                return False

    return True

def check_test_coverage():
    """[EMOJI] [EMOJI] [EMOJI] ([EMOJI])"""
    # Standard [EMOJI]: [EMOJI] [EMOJI]
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "--cov", "--cov-report=term-missing", "--quiet"],
            capture_output=True,
            text=True
        )

        # [EMOJI] [EMOJI] ([EMOJI] [EMOJI])
        for line in result.stdout.split("\\n"):
            if "TOTAL" in line:
                parts = line.split()
                if len(parts) >= 4:
                    coverage = int(parts[-1].replace("%", ""))
                    if coverage < 60:
                        print(f"[WARN]  WARNING: Test coverage is {coverage}% (recommend >60%)")
    except:
        pass

def main():
    print("[EMOJI] Standard Level Pre-push checks...")

    # Standard [EMOJI]: [EMOJI] [EMOJI]
    if not run_tests():
        print("\\n[FAIL] Push blocked: Tests must pass (Standard Level requirement)")
        return 1

    # [EMOJI] [EMOJI] ([EMOJI])
    check_test_coverage()

    print("[OK] Pre-push checks passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

        hook_path = self.git_hooks_dir / "pre-push"
        self.write_hook(hook_path, hook_content)

    def install_post_commit(self):
        """post-commit hook [EMOJI]"""

        hook_content = '''#!/usr/bin/env python3
"""
Standard Level Post-commit Hook
- [EMOJI] [EMOJI] [EMOJI] [EMOJI]
- [EMOJI] [EMOJI]
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime

def get_commit_info():
    """[EMOJI] [EMOJI] [EMOJI]"""
    result = subprocess.run(
        ["git", "log", "-1", "--pretty=format:%H|%s|%an"],
        capture_output=True,
        text=True
    )

    parts = result.stdout.strip().split("|")
    return {
        "hash": parts[0],
        "message": parts[1],
        "author": parts[2]
    }

def extract_module_id(message):
    """[EMOJI] [EMOJI] [EMOJI] ID [EMOJI]"""
    import re
    match = re.search(r"\\[(\\w+/\\w+)\\]", message)
    if match:
        return match.group(1)
    return None

def update_module_status(module_id, commit_info):
    """[EMOJI] [EMOJI] [EMOJI]"""

    # .udo [EMOJI] [EMOJI]
    udo_dir = Path(".udo")
    udo_dir.mkdir(exist_ok=True)

    # [EMOJI] [EMOJI] [EMOJI]
    status_file = udo_dir / "module_status.json"

    if status_file.exists():
        with open(status_file) as f:
            statuses = json.load(f)
    else:
        statuses = {}

    if module_id not in statuses:
        statuses[module_id] = {
            "status": "coding",
            "progress": 30,
            "commits": [],
            "last_update": None
        }

    # [EMOJI] [EMOJI]
    statuses[module_id]["commits"].append(commit_info["hash"][:8])
    statuses[module_id]["last_update"] = datetime.now().isoformat()

    # [EMOJI] [EMOJI] [EMOJI]
    current_progress = statuses[module_id]["progress"]
    commit_count = len(statuses[module_id]["commits"])

    if commit_count >= 5:
        statuses[module_id]["status"] = "testing"
        statuses[module_id]["progress"] = 70
    elif commit_count >= 3:
        statuses[module_id]["progress"] = 50
    else:
        statuses[module_id]["progress"] = min(60, current_progress + 10)

    # [EMOJI]
    with open(status_file, "w") as f:
        json.dump(statuses, f, indent=2)

    return statuses[module_id]

def main():
    commit_info = get_commit_info()
    module_id = extract_module_id(commit_info["message"])

    if module_id:
        status = update_module_status(module_id, commit_info)
        print(f"[EMOJI] Module '{module_id}' status updated:")
        print(f"   Status: {status['status']}")
        print(f"   Progress: {status['progress']}%")
        print(f"   Commits: {len(status['commits'])}")

if __name__ == "__main__":
    main()
'''

        hook_path = self.git_hooks_dir / "post-commit"
        self.write_hook(hook_path, hook_content)

    def write_hook(self, path, content):
        """Hook [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
        path.write_text(content)
        path.chmod(0o755)
        print(f"  [EMOJI] Installed: {path.name}")

    def uninstall_all(self):
        """[EMOJI] Git hooks [EMOJI]"""
        hooks = ["pre-commit", "pre-push", "post-commit"]

        for hook in hooks:
            hook_path = self.git_hooks_dir / hook
            if hook_path.exists():
                hook_path.unlink()
                print(f"  [EMOJI] Removed: {hook}")

        print("[OK] Standard Git Hooks uninstalled")


def main():
    """[EMOJI] [EMOJI]"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Standard Level Git Hooks Installer"
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall hooks"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        help="Project root directory"
    )

    args = parser.parse_args()

    installer = StandardGitHooksInstaller(args.project_root)

    if args.uninstall:
        installer.uninstall_all()
    else:
        installer.install_all()


if __name__ == "__main__":
    main()