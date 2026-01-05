@echo off
REM User Testing Server Startup Script
REM Starts backend and frontend servers for 5-user testing sessions

echo ========================================
echo UDO Platform - User Testing Setup
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv .venv
    echo Then: .venv\Scripts\activate ^&^& pip install -r requirements.txt
    exit /b 1
)

REM Check if PostgreSQL is running
echo [1/6] Checking PostgreSQL status...
sc query postgresql-x64-16 >nul 2>&1
if errorlevel 1 (
    echo [WARNING] PostgreSQL service not running
    echo Starting PostgreSQL...
    net start postgresql-x64-16
) else (
    echo [OK] PostgreSQL is running
)

REM Check if database has sample data
echo.
echo [2/6] Checking database...
.venv\Scripts\python.exe -c "from backend.app.db.database import get_db; db = next(get_db()); from backend.app.models.kanban_tasks import KanbanTask; count = db.query(KanbanTask).count(); print(f'Tasks in database: {count}'); db.close()"

echo.
echo [3/6] Would you like to seed test data? (15 sample tasks)
set /p SEED="Seed database? (y/n): "
if /i "%SEED%"=="y" (
    echo Seeding test data...
    .venv\Scripts\python.exe scripts\seed_test_data.py
    echo [OK] Test data seeded
)

REM Start backend server
echo.
echo [4/6] Starting backend server (port 8000)...
start "UDO Backend" cmd /k ".venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 5 /nobreak >nul

REM Wait for backend to be ready
echo Waiting for backend to start...
:WAIT_BACKEND
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto WAIT_BACKEND
)
echo [OK] Backend ready at http://localhost:8000

REM Check if frontend dependencies are installed
echo.
echo [5/6] Checking frontend dependencies...
if not exist "web-dashboard\node_modules\" (
    echo [WARNING] Node modules not found
    echo Installing frontend dependencies...
    cd web-dashboard
    call npm install
    cd ..
)

REM Start frontend server
echo.
echo [6/6] Starting frontend server (port 3000)...
start "UDO Frontend" cmd /k "cd web-dashboard && npm run dev"
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Servers Started Successfully!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Test ZIP: test-context.zip (4.2 KB, 3 files)
echo.
echo Press Ctrl+C in each window to stop servers
echo.
echo Ready for user testing! Open:
echo   http://localhost:3000/kanban
echo.
pause
