@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   UDO Development Platform - 서비스 중지
echo ============================================================
echo.

:: 프로젝트 루트 디렉토리 설정
set "PROJECT_ROOT=%~dp0..\.."
pushd "%PROJECT_ROOT%"

:: 1. Local 모드 프로세스 종료
echo [1/2] Local 모드 프로세스 종료 중...

:: uvicorn (Backend) 종료
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo     Port 8000 사용 프로세스 종료: PID %%a
    taskkill /PID %%a /F >nul 2>&1
)

:: Next.js (Frontend) 종료
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    echo     Port 3000 사용 프로세스 종료: PID %%a
    taskkill /PID %%a /F >nul 2>&1
)

:: node 프로세스 중 관련된 것 종료 (선택적)
:: taskkill /IM node.exe /F >nul 2>&1

:: 2. Docker 모드 컨테이너 종료
echo [2/2] Docker 컨테이너 종료 중...
docker --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    docker-compose down 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo     Docker 컨테이너 종료 완료
    ) else (
        echo     Docker 컨테이너 없음 (이미 종료됨)
    )
) else (
    echo     Docker 미설치 (스킵)
)

echo.
echo ============================================================
echo   모든 서비스가 종료되었습니다.
echo ============================================================
echo.

popd
pause
