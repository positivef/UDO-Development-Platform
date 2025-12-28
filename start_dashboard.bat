@echo off
echo =====================================
echo Starting UDO Dashboard v3.0
echo =====================================
echo.

:: Start backend server
echo Starting FastAPI backend...
start /B cmd /c "cd backend && pip install -r requirements.txt && python main.py"
echo Backend started on http://localhost:8000
echo.

:: Wait for backend to initialize
timeout /t 3 /nobreak > nul

:: Start frontend
echo Starting Next.js dashboard...
start /B cmd /c "cd web-dashboard && npm install && npm run dev"
echo Dashboard will be available at http://localhost:3000
echo.

echo =====================================
echo All services started!
echo.
echo Backend API: http://localhost:8000/docs
echo Dashboard UI: http://localhost:3000
echo.
echo Press Ctrl+C to stop all services
echo =====================================

:: Keep window open
pause > nul
