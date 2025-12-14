#!/usr/bin/env python3
"""
Standard Level Git Hooks Installer

Standard 레벨 규칙을 강제하는 Git Hooks 설치
- pre-commit: 브랜치 이름 검증, 모듈 점유 확인
- pre-push: 테스트 실행 확인
- post-commit: 모듈 상태 업데이트
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
        """모든 Git hooks 설치"""
        print("🔧 Installing Standard Level Git Hooks...")

        # hooks 디렉토리 생성
        self.scripts_dir.mkdir(parents=True, exist_ok=True)

        # 각 hook 설치
        self.install_pre_commit()
        self.install_pre_push()
        self.install_post_commit()

        print("✅ Standard Git Hooks installed successfully!")
        print("\n📋 Installed hooks:")
        print("  - pre-commit: 브랜치 이름, 모듈 점유 체크")
        print("  - pre-push: 테스트 실행 확인")
        print("  - post-commit: 모듈 상태 자동 업데이트")

    def install_pre_commit(self):
        """pre-commit hook 설치"""

        hook_content = '''#!/usr/bin/env python3
"""
Standard Level Pre-commit Hook
- 브랜치 이름 검증
- 모듈 점유 확인
- 커밋 메시지 형식 검증
"""

import subprocess
import sys
import re
import json
from pathlib import Path

def get_current_branch():
    """현재 브랜치 이름 가져오기"""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def get_module_from_files():
    """변경된 파일에서 모듈 ID 추출"""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True
    )

    files = result.stdout.strip().split("\\n")

    # 파일 경로에서 모듈 ID 추출 (예: backend/auth/login.py -> auth/login)
    modules = set()
    for file in files:
        if file.startswith("backend/") and file.endswith(".py"):
            parts = file.replace("backend/", "").replace(".py", "").split("/")
            if len(parts) >= 2:
                module_id = "/".join(parts[:2])
                modules.add(module_id)

    return list(modules)

def check_module_ownership(module_id):
    """모듈 점유 확인 (Standard 레벨)"""
    # TODO: Redis에서 실제 점유 정보 확인
    # 여기서는 간단히 구현

    ownership_file = Path(".udo/module_ownership.json")
    if not ownership_file.exists():
        return True, None

    with open(ownership_file) as f:
        ownerships = json.load(f)

    if module_id in ownerships:
        owner = ownerships[module_id].get("developer")
        # 현재 사용자와 비교 (git config user.name)
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
    """커밋 메시지 형식 확인"""
    with open(".git/COMMIT_EDITMSG", "r") as f:
        message = f.read()

    # Standard 레벨: 모듈 ID가 포함되어야 함
    module_pattern = r"\\[(\\w+/\\w+)\\]"
    if not re.search(module_pattern, message):
        return False, "커밋 메시지에 모듈 ID를 포함해주세요. 예: [auth/login] 로그인 기능 구현"

    return True, None

def main():
    print("🔍 Standard Level Pre-commit checks...")

    # 1. 브랜치 이름 체크
    branch = get_current_branch()
    modules = get_module_from_files()

    if modules and branch != "main" and branch != "develop":
        # Standard 레벨: feature/module-id 형식 권장
        for module_id in modules:
            expected_branch = f"feature/{module_id.replace('/', '-')}"
            if not branch.startswith(expected_branch):
                print(f"⚠️  WARNING: 브랜치 이름 '{expected_branch}'를 권장합니다 (현재: {branch})")

    # 2. 모듈 점유 체크
    for module_id in modules:
        owned, owner = check_module_ownership(module_id)
        if not owned:
            print(f"❌ ERROR: 모듈 '{module_id}'은(는) {owner}님이 개발 중입니다!")
            print("   먼저 모듈을 점유하거나 완료를 기다려주세요.")
            return 1

    # 3. 커밋 메시지 체크
    msg_valid, msg_error = check_commit_message()
    if not msg_valid:
        print(f"❌ ERROR: {msg_error}")
        return 1

    print("✅ Pre-commit checks passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

        hook_path = self.git_hooks_dir / "pre-commit"
        self.write_hook(hook_path, hook_content)

    def install_pre_push(self):
        """pre-push hook 설치"""

        hook_content = '''#!/usr/bin/env python3
"""
Standard Level Pre-push Hook
- 테스트 실행 확인 (필수)
- 테스트 커버리지 체크 (권장)
"""

import subprocess
import sys
import json
from pathlib import Path

def run_tests():
    """테스트 실행"""
    print("🧪 Running tests before push (Standard Level requirement)...")

    # Python 테스트 실행
    if Path("pytest.ini").exists() or Path("setup.cfg").exists():
        result = subprocess.run(
            ["python", "-m", "pytest", "--tb=short"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("❌ Tests failed! Fix tests before pushing.")
            print(result.stdout)
            return False

    # JavaScript 테스트 실행
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
                print("❌ JavaScript tests failed!")
                print(result.stdout)
                return False

    return True

def check_test_coverage():
    """테스트 커버리지 체크 (경고만)"""
    # Standard 레벨: 커버리지는 경고만
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "--cov", "--cov-report=term-missing", "--quiet"],
            capture_output=True,
            text=True
        )

        # 커버리지 파싱 (간단한 예시)
        for line in result.stdout.split("\\n"):
            if "TOTAL" in line:
                parts = line.split()
                if len(parts) >= 4:
                    coverage = int(parts[-1].replace("%", ""))
                    if coverage < 60:
                        print(f"⚠️  WARNING: Test coverage is {coverage}% (recommend >60%)")
    except:
        pass

def main():
    print("🚀 Standard Level Pre-push checks...")

    # Standard 레벨: 테스트는 필수
    if not run_tests():
        print("\\n❌ Push blocked: Tests must pass (Standard Level requirement)")
        return 1

    # 커버리지 체크 (경고만)
    check_test_coverage()

    print("✅ Pre-push checks passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

        hook_path = self.git_hooks_dir / "pre-push"
        self.write_hook(hook_path, hook_content)

    def install_post_commit(self):
        """post-commit hook 설치"""

        hook_content = '''#!/usr/bin/env python3
"""
Standard Level Post-commit Hook
- 모듈 상태 자동 업데이트
- 진행률 업데이트
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime

def get_commit_info():
    """커밋 정보 가져오기"""
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
    """커밋 메시지에서 모듈 ID 추출"""
    import re
    match = re.search(r"\\[(\\w+/\\w+)\\]", message)
    if match:
        return match.group(1)
    return None

def update_module_status(module_id, commit_info):
    """모듈 상태 업데이트"""

    # .udo 디렉토리 생성
    udo_dir = Path(".udo")
    udo_dir.mkdir(exist_ok=True)

    # 상태 파일 업데이트
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

    # 상태 업데이트
    statuses[module_id]["commits"].append(commit_info["hash"][:8])
    statuses[module_id]["last_update"] = datetime.now().isoformat()

    # 진행률 자동 증가
    current_progress = statuses[module_id]["progress"]
    commit_count = len(statuses[module_id]["commits"])

    if commit_count >= 5:
        statuses[module_id]["status"] = "testing"
        statuses[module_id]["progress"] = 70
    elif commit_count >= 3:
        statuses[module_id]["progress"] = 50
    else:
        statuses[module_id]["progress"] = min(60, current_progress + 10)

    # 저장
    with open(status_file, "w") as f:
        json.dump(statuses, f, indent=2)

    return statuses[module_id]

def main():
    commit_info = get_commit_info()
    module_id = extract_module_id(commit_info["message"])

    if module_id:
        status = update_module_status(module_id, commit_info)
        print(f"📊 Module '{module_id}' status updated:")
        print(f"   Status: {status['status']}")
        print(f"   Progress: {status['progress']}%")
        print(f"   Commits: {len(status['commits'])}")

if __name__ == "__main__":
    main()
'''

        hook_path = self.git_hooks_dir / "post-commit"
        self.write_hook(hook_path, hook_content)

    def write_hook(self, path, content):
        """Hook 파일 작성 및 실행 권한 설정"""
        path.write_text(content)
        path.chmod(0o755)
        print(f"  ✓ Installed: {path.name}")

    def uninstall_all(self):
        """모든 Git hooks 제거"""
        hooks = ["pre-commit", "pre-push", "post-commit"]

        for hook in hooks:
            hook_path = self.git_hooks_dir / hook
            if hook_path.exists():
                hook_path.unlink()
                print(f"  ✓ Removed: {hook}")

        print("✅ Standard Git Hooks uninstalled")


def main():
    """메인 함수"""
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