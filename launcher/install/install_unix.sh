#!/bin/bash
#
# UDO Development Platform - 개발 환경 완전 초기화
# (기존 프로젝트 규칙 및 훅 자동 설치)
#

set -e

echo ""
echo "============================================================"
echo "  UDO Development Platform - 개발 환경 완전 초기화"
echo "  (기존 프로젝트 규칙 및 훅 자동 설치)"
echo "============================================================"
echo ""

# 프로젝트 루트 디렉토리 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ========================================
# 1. 요구사항 확인
# ========================================
echo "[1/8] 요구사항 확인 중..."
python3 "$SCRIPT_DIR/check_requirements.py"
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] 필수 요구사항이 충족되지 않았습니다.${NC}"
    exit 1
fi

# ========================================
# 2. Python 가상환경 생성
# ========================================
echo ""
echo "[2/8] Python 가상환경 생성 중..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "    가상환경 생성 완료: .venv"
else
    echo "    가상환경 이미 존재: .venv"
fi

source .venv/bin/activate

# ========================================
# 3. Backend 의존성 설치
# ========================================
echo ""
echo "[3/8] Backend 의존성 설치 중..."
pip install --upgrade pip -q
pip install -r backend/requirements.txt -q
pip install -r requirements.txt -q 2>/dev/null || true
echo "    Backend 의존성 설치 완료"

# ========================================
# 4. Frontend 의존성 설치
# ========================================
echo ""
echo "[4/8] Frontend 의존성 설치 중..."
cd web-dashboard
if [ ! -d "node_modules" ]; then
    npm install
else
    echo "    node_modules 이미 존재, 업데이트 확인 중..."
    npm install
fi
cd ..
echo "    Frontend 의존성 설치 완료"

# ========================================
# 5. 환경 변수 파일 설정
# ========================================
echo ""
echo "[5/8] 환경 변수 설정 중..."
if [ ! -f ".env" ]; then
    cp ".env.example" ".env"
    echo "    .env 파일 생성 완료"
    echo -e "    ${YELLOW}[주의] .env 파일을 열어 필요한 값을 설정하세요!${NC}"
else
    echo "    .env 파일 이미 존재"
fi

if [ ! -f "backend/.env" ] && [ -f "backend/.env.example" ]; then
    cp "backend/.env.example" "backend/.env"
    echo "    backend/.env 파일 생성 완료"
fi

# ========================================
# 6. Pre-commit 훅 설치 (.pre-commit-config.yaml 기반)
# ========================================
echo ""
echo "[6/8] Git Pre-commit 훅 설치 중..."
pip install pre-commit -q
if pre-commit install 2>/dev/null; then
    pre-commit install --hook-type pre-push 2>/dev/null
    echo "    Pre-commit 훅 설치 완료"
    echo "    - Black 포맷터 (Python)"
    echo "    - Flake8 린터"
    echo "    - 한글 텍스트 보호 체크"
    echo "    - 시스템 규칙 검증"
else
    echo "    Git 저장소 아님 - 훅 설치 스킵"
fi

# ========================================
# 7. Obsidian 동기화 설정 (.governance.yaml 기반)
# ========================================
echo ""
echo "[7/8] Obsidian 동기화 설정 중..."
if [ -f "scripts/install_obsidian_git_hook.py" ]; then
    if python scripts/install_obsidian_git_hook.py 2>/dev/null; then
        echo "    Obsidian Git Hook 설치 완료"
    else
        echo "    Obsidian Hook 설치 스킵 (Git 저장소 확인 필요)"
    fi
else
    echo "    Obsidian Hook 스크립트 없음 (스킵)"
fi

# ========================================
# 8. Governance 상태 확인 (.governance.yaml)
# ========================================
echo ""
echo "[8/8] Governance 설정 확인 중..."
if [ -f ".governance.yaml" ]; then
    echo "    .governance.yaml 발견됨"
    echo "    현재 Tier: [CLI 도구로 확인: ./udo.bat status]"
else
    echo -e "    ${YELLOW}[경고] .governance.yaml 없음 - Governance 미설정${NC}"
fi

# ========================================
# 설치 완료
# ========================================
echo ""
echo "============================================================"
echo -e "  ${GREEN}설치 완료!${NC}"
echo "============================================================"
echo ""
echo "반영된 기존 규칙:"
echo "  [x] .pre-commit-config.yaml - Git 훅 (Black, Flake8, 한글보호)"
echo "  [x] .governance.yaml - 4-Tier Governance System"
echo "  [x] Obsidian 자동 동기화 (post-commit hook)"
echo "  [x] 시스템 규칙 검증 (pre-push hook)"
echo ""
echo "다음 단계:"
echo "  1. .env 파일을 열어 필요한 설정을 확인/수정하세요"
echo "  2. Governance 상태 확인: ./udo.bat status"
echo "  3. 실행: ./launcher/start/start_local.sh (Local 모드)"
echo ""
echo "세션 시작 프로토콜 (CLAUDE.md 기반):"
echo "  python scripts/session_start.py"
echo ""
