#!/bin/bash
#
# UDO Development Platform - Docker 모드 시작
#

set -e

echo ""
echo "============================================================"
echo "  UDO Development Platform - Docker 모드 시작"
echo "============================================================"
echo ""

# 프로젝트 루트 디렉토리 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# Docker 확인
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker가 설치되지 않았습니다."
    echo "Docker를 설치하거나 Local 모드를 사용하세요:"
    echo "  ./launcher/start/start_local.sh"
    exit 1
fi

# Docker Compose 실행
echo "[INFO] Docker 컨테이너 시작 중..."
docker-compose up -d

echo ""
echo "============================================================"
echo "  Docker 서비스 시작 완료!"
echo "============================================================"
echo ""
echo "  Backend:    http://localhost:8000"
echo "  Frontend:   http://localhost:3001"
echo "  API Docs:   http://localhost:8000/docs"
echo "  Grafana:    http://localhost:3000 (admin/admin123)"
echo "  pgAdmin:    http://localhost:5050"
echo ""
echo "  상태 확인: docker-compose ps"
echo "  로그 확인: docker-compose logs -f"
echo "  종료:      ./launcher/stop/stop_all.sh"
echo ""
