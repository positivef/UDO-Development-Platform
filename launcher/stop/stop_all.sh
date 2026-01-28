#!/bin/bash
#
# UDO Development Platform - 서비스 중지
#

echo ""
echo "============================================================"
echo "  UDO Development Platform - 서비스 중지"
echo "============================================================"
echo ""

# 프로젝트 루트 디렉토리 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# 색상 정의
GREEN='\033[0;32m'
NC='\033[0m'

# 1. PID 파일로 프로세스 종료
echo "[1/3] PID 파일로 프로세스 종료 중..."

if [ -f ".backend.pid" ]; then
    PID=$(cat .backend.pid)
    kill $PID 2>/dev/null && echo "    Backend 종료 (PID: $PID)"
    rm -f .backend.pid
fi

if [ -f ".frontend.pid" ]; then
    PID=$(cat .frontend.pid)
    kill $PID 2>/dev/null && echo "    Frontend 종료 (PID: $PID)"
    rm -f .frontend.pid
fi

# 2. 포트로 프로세스 종료
echo "[2/3] 포트 사용 프로세스 종료 중..."

# Port 8000 (Backend)
PID_8000=$(lsof -ti:8000 2>/dev/null)
if [ -n "$PID_8000" ]; then
    kill -9 $PID_8000 2>/dev/null
    echo "    Port 8000 프로세스 종료: PID $PID_8000"
fi

# Port 3000 (Frontend)
PID_3000=$(lsof -ti:3000 2>/dev/null)
if [ -n "$PID_3000" ]; then
    kill -9 $PID_3000 2>/dev/null
    echo "    Port 3000 프로세스 종료: PID $PID_3000"
fi

# 3. Docker 컨테이너 종료
echo "[3/3] Docker 컨테이너 종료 중..."
if command -v docker &> /dev/null; then
    docker-compose down 2>/dev/null && echo "    Docker 컨테이너 종료 완료" || echo "    Docker 컨테이너 없음"
else
    echo "    Docker 미설치 (스킵)"
fi

echo ""
echo "============================================================"
echo -e "  ${GREEN}모든 서비스가 종료되었습니다.${NC}"
echo "============================================================"
echo ""
