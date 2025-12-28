@echo off
set "PYTHON_EXE=.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Virtual environment python not found at %PYTHON_EXE%
    echo Please run setup first.
    exit /b 1
)

"%PYTHON_EXE%" cli/udo.py %*
