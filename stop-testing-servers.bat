@echo off
REM Stop all testing servers

echo Stopping UDO testing servers...

REM Kill backend (uvicorn on port 8000)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    taskkill /PID %%a /F >nul 2>&1
)

REM Kill frontend (Next.js on port 3000)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo [OK] Servers stopped
echo.
echo To clear test data: .venv\Scripts\python.exe scripts\seed_test_data.py --clear
pause
