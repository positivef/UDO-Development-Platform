#!/bin/bash
#
# UDO Development Platform - Local 모드 시작 (Docker 불필요)
#

set -e

echo ""
echo "============================================================"
echo "  UDO Development Platform - Local 모드 시작 (Docker 불필요)"
echo "============================================================"
echo ""

# 프로젝트 루트 디렉토리 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 가상환경 활성화
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo -e "${YELLOW}[ERROR] 가상환경이 없습니다. 먼저 install_unix.sh를 실행하세요.${NC}"
    exit 1
fi

# 환경변수 설정 (Local 모드)
export ENVIRONMENT=development
export DATABASE_URL="sqlite:///./udo_local.db"
export LOG_LEVEL=INFO
export DISABLE_REDIS=true

echo "[INFO] Local 모드로 시작합니다 (SQLite + No Redis)"
echo ""

# Backend 시작 (백그라운드)
echo "[1/2] Backend 서버 시작 중... (Port 8000)"
cd "$PROJECT_ROOT"
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# PID 저장
echo $BACKEND_PID > "$PROJECT_ROOT/.backend.pid"

# 잠시 대기
sleep 3

# Frontend 시작 (백그라운드)
echo "[2/2] Frontend 서버 시작 중... (Port 3000)"
cd "$PROJECT_ROOT/web-dashboard"
npm run dev &
FRONTEND_PID=$!

# PID 저장
echo $FRONTEND_PID > "$PROJECT_ROOT/.frontend.pid"

cd "$PROJECT_ROOT"

echo ""
echo "============================================================"
echo -e "  ${GREEN}서버 시작 완료!${NC}"
echo "============================================================"
echo ""
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "  종료하려면: ./launcher/stop/stop_all.sh"
echo "  또는 Ctrl+C"
echo ""

# 종료 시그널 핸들러
cleanup() {
    echo ""
    echo "서버 종료 중..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    rm -f "$PROJECT_ROOT/.backend.pid" "$PROJECT_ROOT/.frontend.pid"
    echo "종료 완료"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 대기
wait
