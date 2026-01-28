@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   UDO Development Platform - Docker 모드 시작
echo ============================================================
echo.

:: 프로젝트 루트 디렉토리 설정
set "PROJECT_ROOT=%~dp0..\.."
pushd "%PROJECT_ROOT%"

:: Docker 확인
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker가 설치되지 않았습니다.
    echo Docker Desktop을 설치하거나 Local 모드를 사용하세요:
    echo   launcher\start\start_local.bat
    pause
    exit /b 1
)

:: Docker Compose 실행
echo [INFO] Docker 컨테이너 시작 중...
docker-compose up -d

echo.
echo ============================================================
echo   Docker 서비스 시작 완료!
echo ============================================================
echo.
echo   Backend:    http://localhost:8000
echo   Frontend:   http://localhost:3001
echo   API Docs:   http://localhost:8000/docs
echo   Grafana:    http://localhost:3000 (admin/admin123)
echo   pgAdmin:    http://localhost:5050
echo.
echo   상태 확인: docker-compose ps
echo   로그 확인: docker-compose logs -f
echo   종료:      launcher\stop\stop_all.bat
echo.

popd
pause
