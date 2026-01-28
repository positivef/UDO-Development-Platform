#!/usr/bin/env python3
"""
UDO Development Platform - 시스템 헬스체크
모든 서비스 상태를 확인하고 보고합니다.
"""

import subprocess
import sys
import socket
import urllib.request
import json
from pathlib import Path

# ANSI Color Codes
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
        os.system("")

def check_port(host: str, port: int, timeout: float = 2.0) -> bool:
    """포트가 열려있는지 확인"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def check_http_endpoint(url: str, timeout: float = 5.0) -> tuple[bool, str]:
    """HTTP 엔드포인트 확인"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "UDO-HealthCheck/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return True, str(response.status)
    except urllib.error.HTTPError as e:
        return False, str(e.code)
    except urllib.error.URLError as e:
        return False, str(e.reason)
    except Exception as e:
        return False, str(e)

def check_backend_health(base_url: str = "http://localhost:8000") -> dict:
    """Backend API 헬스체크"""
    result = {
        "name": "Backend API",
        "url": base_url,
        "status": "unknown",
        "details": {}
    }

    # 포트 확인
    if not check_port("localhost", 8000):
        result["status"] = "down"
        result["details"]["port"] = "Port 8000 not open"
        return result

    # /api/health 엔드포인트 확인
    success, status = check_http_endpoint(f"{base_url}/api/health")
    if success:
        result["status"] = "healthy"
        result["details"]["http"] = f"HTTP {status}"
    else:
        # /docs 확인 (최소 확인)
        success2, status2 = check_http_endpoint(f"{base_url}/docs")
        if success2:
            result["status"] = "running"
            result["details"]["http"] = f"API running (no /api/health)"
        else:
            result["status"] = "error"
            result["details"]["http"] = status

    return result

def check_frontend_health(base_url: str = "http://localhost:3000") -> dict:
    """Frontend 헬스체크"""
    result = {
        "name": "Frontend (Next.js)",
        "url": base_url,
        "status": "unknown",
        "details": {}
    }

    # 포트 확인
    if not check_port("localhost", 3000):
        result["status"] = "down"
        result["details"]["port"] = "Port 3000 not open"
        return result

    # 메인 페이지 확인
    success, status = check_http_endpoint(base_url)
    if success:
        result["status"] = "healthy"
        result["details"]["http"] = f"HTTP {status}"
    else:
        result["status"] = "error"
        result["details"]["http"] = status

    return result

def check_database_health() -> dict:
    """Database 헬스체크"""
    result = {
        "name": "Database",
        "status": "unknown",
        "details": {}
    }

    # PostgreSQL 포트 확인
    if check_port("localhost", 5432):
        result["status"] = "healthy"
        result["details"]["type"] = "PostgreSQL"
        result["details"]["port"] = "5432 open"
        return result

    # SQLite 파일 확인
    project_root = Path(__file__).parent.parent.parent
    sqlite_path = project_root / "udo_local.db"
    if sqlite_path.exists():
        result["status"] = "healthy"
        result["details"]["type"] = "SQLite"
        result["details"]["path"] = str(sqlite_path)
        return result

    result["status"] = "not configured"
    result["details"]["type"] = "None"
    return result

def check_redis_health() -> dict:
    """Redis 헬스체크"""
    result = {
        "name": "Redis Cache",
        "status": "unknown",
        "details": {}
    }

    if check_port("localhost", 6379):
        result["status"] = "healthy"
        result["details"]["port"] = "6379 open"
    else:
        result["status"] = "disabled"
        result["details"]["note"] = "Local 모드에서는 비활성화됨"

    return result

def print_service_status(service: dict):
    """서비스 상태 출력"""
    status = service["status"]
    name = service["name"]

    if status == "healthy":
        icon = f"{GREEN}✓{RESET}"
        status_text = f"{GREEN}HEALTHY{RESET}"
    elif status == "running":
        icon = f"{YELLOW}○{RESET}"
        status_text = f"{YELLOW}RUNNING{RESET}"
    elif status in ("disabled", "not configured"):
        icon = f"{YELLOW}○{RESET}"
        status_text = f"{YELLOW}{status.upper()}{RESET}"
    else:
        icon = f"{RED}✗{RESET}"
        status_text = f"{RED}{status.upper()}{RESET}"

    print(f"  {icon} {name:20} {status_text}")

    for key, value in service.get("details", {}).items():
        print(f"      {key}: {value}")

def main():
    enable_windows_ansi()

    print(f"\n{BOLD}{BLUE}{'=' * 60}")
    print("  UDO Development Platform - 시스템 헬스체크")
    print("=" * 60 + f"{RESET}\n")

    services = []

    # 각 서비스 확인
    print(f"{BOLD}서비스 상태:{RESET}\n")

    backend = check_backend_health()
    services.append(backend)
    print_service_status(backend)

    frontend = check_frontend_health()
    services.append(frontend)
    print_service_status(frontend)

    database = check_database_health()
    services.append(database)
    print_service_status(database)

    redis = check_redis_health()
    services.append(redis)
    print_service_status(redis)

    # 요약
    print(f"\n{BOLD}{'=' * 60}{RESET}")

    healthy = sum(1 for s in services if s["status"] in ("healthy", "running"))
    total_required = 2  # Backend + Frontend

    if backend["status"] in ("healthy", "running") and frontend["status"] in ("healthy", "running"):
        print(f"\n{GREEN}{BOLD}✓ 핵심 서비스 정상 작동 중!{RESET}")
        print(f"\n  Dashboard: {BLUE}http://localhost:3000{RESET}")
        print(f"  API Docs:  {BLUE}http://localhost:8000/docs{RESET}")
        return 0
    else:
        print(f"\n{RED}{BOLD}✗ 일부 서비스가 실행되지 않았습니다.{RESET}")
        print(f"\n  시작 명령어:")
        print(f"    Local 모드: {BLUE}launcher\\start\\start_local.bat{RESET}")
        print(f"    Docker 모드: {BLUE}launcher\\start\\start_all.bat{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
