@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   UDO Development Platform - 개발 환경 완전 초기화
echo   (기존 프로젝트 규칙 및 훅 자동 설치)
echo ============================================================
echo.

:: 프로젝트 루트 디렉토리 설정
set "PROJECT_ROOT=%~dp0..\.."
pushd "%PROJECT_ROOT%"

:: ========================================
:: 1. 요구사항 확인
:: ========================================
echo [1/8] 요구사항 확인 중...
python "%~dp0check_requirements.py"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] 필수 요구사항이 충족되지 않았습니다.
    pause
    exit /b 1
)

:: ========================================
:: 2. Python 가상환경 생성
:: ========================================
echo.
echo [2/8] Python 가상환경 생성 중...
if not exist ".venv" (
    python -m venv .venv
    echo     가상환경 생성 완료: .venv
) else (
    echo     가상환경 이미 존재: .venv
)

:: 가상환경 활성화
call .venv\Scripts\activate.bat

:: ========================================
:: 3. Backend 의존성 설치
:: ========================================
echo.
echo [3/8] Backend 의존성 설치 중...
pip install --upgrade pip -q
pip install -r backend\requirements.txt -q
pip install -r requirements.txt -q 2>nul
echo     Backend 의존성 설치 완료

:: ========================================
:: 4. Frontend 의존성 설치
:: ========================================
echo.
echo [4/8] Frontend 의존성 설치 중...
cd web-dashboard
if not exist "node_modules" (
    call npm install
) else (
    echo     node_modules 이미 존재, 업데이트 확인 중...
    call npm install
)
cd ..
echo     Frontend 의존성 설치 완료

:: ========================================
:: 5. 환경 변수 파일 설정
:: ========================================
echo.
echo [5/8] 환경 변수 설정 중...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo     .env 파일 생성 완료
    echo     [주의] .env 파일을 열어 필요한 값을 설정하세요!
) else (
    echo     .env 파일 이미 존재
)

if not exist "backend\.env" (
    if exist "backend\.env.example" (
        copy "backend\.env.example" "backend\.env" >nul
        echo     backend\.env 파일 생성 완료
    )
)

:: ========================================
:: 6. Pre-commit 훅 설치 (.pre-commit-config.yaml 기반)
:: ========================================
echo.
echo [6/8] Git Pre-commit 훅 설치 중...
pip install pre-commit -q
pre-commit install 2>nul
if %ERRORLEVEL% EQU 0 (
    pre-commit install --hook-type pre-push 2>nul
    echo     Pre-commit 훅 설치 완료
    echo     - Black 포맷터 (Python)
    echo     - Flake8 린터
    echo     - 한글 텍스트 보호 체크
    echo     - 시스템 규칙 검증
) else (
    echo     Git 저장소 아님 - 훅 설치 스킵
)

:: ========================================
:: 7. Obsidian 동기화 설정 (.governance.yaml 기반)
:: ========================================
echo.
echo [7/8] Obsidian 동기화 설정 중...
if exist "scripts\install_obsidian_git_hook.py" (
    python scripts\install_obsidian_git_hook.py 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo     Obsidian Git Hook 설치 완료
    ) else (
        echo     Obsidian Hook 설치 스킵 (Git 저장소 확인 필요)
    )
) else (
    echo     Obsidian Hook 스크립트 없음 (스킵)
)

:: ========================================
:: 8. Governance 상태 확인 (.governance.yaml)
:: ========================================
echo.
echo [8/8] Governance 설정 확인 중...
if exist ".governance.yaml" (
    echo     .governance.yaml 발견됨
    echo     현재 Tier: [CLI 도구로 확인: udo.bat status]
) else (
    echo     [경고] .governance.yaml 없음 - Governance 미설정
)

:: ========================================
:: 설치 완료
:: ========================================
echo.
echo ============================================================
echo   설치 완료!
echo ============================================================
echo.
echo 반영된 기존 규칙:
echo   [x] .pre-commit-config.yaml - Git 훅 (Black, Flake8, 한글보호)
echo   [x] .governance.yaml - 4-Tier Governance System
echo   [x] Obsidian 자동 동기화 (post-commit hook)
echo   [x] 시스템 규칙 검증 (pre-push hook)
echo.
echo 다음 단계:
echo   1. .env 파일을 열어 필요한 설정을 확인/수정하세요
echo   2. Governance 상태 확인: udo.bat status
echo   3. 실행: launcher\start\start_local.bat (Local 모드)
echo.
echo 세션 시작 프로토콜 (CLAUDE.md 기반):
echo   python scripts\session_start.py
echo.

popd
pause
