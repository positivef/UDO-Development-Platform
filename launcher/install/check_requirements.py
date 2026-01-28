#!/usr/bin/env python3
"""
UDO Development Platform - 시스템 요구사항 체커
다른 컴퓨터에서 개발 환경을 설정하기 전 필수 소프트웨어 확인
"""

import subprocess
import sys
import shutil
from pathlib import Path

# ANSI Color Codes (Windows 10+ 지원)
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

def enable_windows_ansi():
    """Windows에서 ANSI 색상 지원 활성화"""
    if sys.platform == "win32":
        import os
        os.system("")  # Enable ANSI escape sequences

def check_python():
    """Python 버전 확인 (3.10+ 필요)"""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version.major >= 3 and version.minor >= 10:
        return True, version_str, "Python 3.10+ ✓"
    else:
        return False, version_str, "Python 3.10+ 필요"

def check_node():
    """Node.js 버전 확인 (18+ 필요)"""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        version = result.stdout.strip().lstrip("v")
        major = int(version.split(".")[0])

        if major >= 18:
            return True, version, "Node.js 18+ ✓"
        else:
            return False, version, "Node.js 18+ 필요"
    except FileNotFoundError:
        return False, "미설치", "nodejs.org에서 설치 필요"
    except Exception as e:
        return False, "오류", str(e)

def check_npm():
    """npm 설치 확인"""
    try:
        result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        version = result.stdout.strip()
        return True, version, "npm ✓"
    except FileNotFoundError:
        return False, "미설치", "Node.js와 함께 설치됨"
    except Exception as e:
        return False, "오류", str(e)

def check_git():
    """Git 버전 확인"""
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        version = result.stdout.strip().replace("git version ", "")
        return True, version, "Git ✓"
    except FileNotFoundError:
        return False, "미설치", "git-scm.com에서 설치 필요"
    except Exception as e:
        return False, "오류", str(e)

def check_docker():
    """Docker 설치 확인 (선택)"""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        version = result.stdout.strip().replace("Docker version ", "").split(",")[0]
        return True, version, "Docker ✓ (Docker 모드 사용 가능)"
    except FileNotFoundError:
        return None, "미설치", "Local 모드 사용 가능"
    except Exception as e:
        return None, "오류", "Local 모드 사용 가능"

def check_postgresql():
    """PostgreSQL 설치 확인 (선택)"""
    try:
        result = subprocess.run(
            ["psql", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        version = result.stdout.strip()
        return True, version.split()[-1] if version else "설치됨", "PostgreSQL ✓"
    except FileNotFoundError:
        return None, "미설치", "SQLite 폴백 모드 사용 가능"
    except Exception as e:
        return None, "오류", "SQLite 폴백 모드 사용 가능"

def print_result(name: str, passed: bool | None, version: str, message: str):
    """검사 결과 출력"""
    if passed is True:
        icon = f"{GREEN}✓{RESET}"
        status = f"{GREEN}PASS{RESET}"
    elif passed is False:
        icon = f"{RED}✗{RESET}"
        status = f"{RED}FAIL{RESET}"
    else:  # Optional (None)
        icon = f"{YELLOW}○{RESET}"
        status = f"{YELLOW}OPTIONAL{RESET}"

    print(f"  {icon} {name:15} {version:15} {status:10} {message}")

def main():
    enable_windows_ansi()

    print(f"\n{BOLD}{BLUE}=" * 60)
    print("  UDO Development Platform - 요구사항 검사")
    print("=" * 60 + f"{RESET}\n")

    results = []

    # 필수 항목
    print(f"{BOLD}필수 요구사항:{RESET}")

    passed, version, msg = check_python()
    print_result("Python", passed, version, msg)
    results.append(("Python", passed))

    passed, version, msg = check_node()
    print_result("Node.js", passed, version, msg)
    results.append(("Node.js", passed))

    passed, version, msg = check_npm()
    print_result("npm", passed, version, msg)
    results.append(("npm", passed))

    passed, version, msg = check_git()
    print_result("Git", passed, version, msg)
    results.append(("Git", passed))

    # 선택 항목
    print(f"\n{BOLD}선택 요구사항:{RESET}")

    passed, version, msg = check_docker()
    print_result("Docker", passed, version, msg)

    passed, version, msg = check_postgresql()
    print_result("PostgreSQL", passed, version, msg)

    # 결과 요약
    print(f"\n{BOLD}{'=' * 60}{RESET}")

    failed = [name for name, passed in results if passed is False]

    if not failed:
        print(f"\n{GREEN}{BOLD}✓ 모든 필수 요구사항이 충족되었습니다!{RESET}")
        print(f"\n다음 단계:")
        print(f"  1. 설치: {BLUE}install_windows.bat{RESET} 또는 {BLUE}install_unix.sh{RESET}")
        print(f"  2. 실행: {BLUE}start_local.bat{RESET} (Local 모드)")
        print(f"          또는 {BLUE}start_all.bat{RESET} (Docker 모드)")
        return 0
    else:
        print(f"\n{RED}{BOLD}✗ 다음 요구사항 설치가 필요합니다:{RESET}")
        for name in failed:
            print(f"  - {name}")
        print(f"\n설치 후 다시 실행해 주세요.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
