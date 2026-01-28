@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   UDO Development Platform - Local 모드 시작 (Docker 불필요)
echo ============================================================
echo.

:: 프로젝트 루트 디렉토리 설정
set "PROJECT_ROOT=%~dp0..\.."
pushd "%PROJECT_ROOT%"

:: 가상환경 활성화
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo [ERROR] 가상환경이 없습니다. 먼저 install_windows.bat을 실행하세요.
    pause
    exit /b 1
)

:: 환경변수 설정 (Local 모드)
set "ENVIRONMENT=development"
set "DATABASE_URL=sqlite:///./udo_local.db"
set "LOG_LEVEL=INFO"
set "DISABLE_REDIS=true"

echo [INFO] Local 모드로 시작합니다 (SQLite + No Redis)
echo.

:: Backend 시작 (별도 창)
echo [1/2] Backend 서버 시작 중... (Port 8000)
start "UDO Backend" cmd /k "cd /d %PROJECT_ROOT% && .venv\Scripts\activate.bat && set DATABASE_URL=sqlite:///./udo_local.db && python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"

:: 잠시 대기
timeout /t 3 /nobreak >nul

:: Frontend 시작 (별도 창)
echo [2/2] Frontend 서버 시작 중... (Port 3000)
start "UDO Frontend" cmd /k "cd /d %PROJECT_ROOT%\web-dashboard && npm run dev"

echo.
echo ============================================================
echo   서버 시작 완료!
echo ============================================================
echo.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   API Docs: http://localhost:8000/docs
echo.
echo   종료하려면 각 터미널 창을 닫거나 Ctrl+C를 누르세요.
echo   또는: launcher\stop\stop_all.bat
echo.

popd
pause
