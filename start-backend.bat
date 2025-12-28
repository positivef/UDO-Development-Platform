@echo off
REM UDO Backend Server Launcher
REM Automatically finds available port and starts uvicorn

echo 🚀 Starting UDO Backend Server...
echo.

REM Activate virtual environment
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo ❌ Virtual environment not found. Please run: python -m venv .venv
    exit /b 1
)

REM Find available port
for /f %%i in ('python backend\app\utils\port_finder.py') do set PORT=%%i

if "%PORT%"=="" (
    echo ❌ Failed to find available port
    exit /b 1
)

echo ✅ Using port: %PORT%
echo 📝 API docs will be available at: http://localhost:%PORT%/docs
echo.

REM Update frontend .env.local if it exists
if exist web-dashboard\.env.local (
    echo NEXT_PUBLIC_API_URL=http://localhost:%PORT% > web-dashboard\.env.local
    echo ✅ Updated web-dashboard/.env.local with port %PORT%
    echo.
)

REM Start uvicorn
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port %PORT%
