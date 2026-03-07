@echo off
setlocal enabledelayedexpansion
title Bill Reconciliation App

echo ========================================
echo Starting Bill Reconciliation App...
echo ========================================
echo.

REM 1. Check for Python
python --version >nul 2>&1
if !errorlevel! neq 0 (
    python3 --version >nul 2>&1
    if !errorlevel! neq 0 (
        py --version >nul 2>&1
        if !errorlevel! neq 0 (
            echo [ERROR] Python not found! 
            echo Please install Python from https://www.python.org/
            pause
            exit /b 1
        ) else (
            set PY_EXE=py
        )
    ) else (
        set PY_EXE=python3
    )
) else (
    set PY_EXE=python
)

REM 2. Check if venv is valid for Windows
if exist "venv\" (
    if not exist "venv\Scripts\activate" (
        echo [INFO] Incompatible virtual environment detected - Mac/Linux.
        echo [INFO] Recreating environment for Windows...
        rmdir /s /q venv
    )
)

REM 3. Create venv if missing
if not exist "venv\" (
    echo [INFO] Setting up the environment for the first time...
    !PY_EXE! -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    
    echo [INFO] Installing required libraries...
    call venv\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install requirements.
        pause
        exit /b 1
    )
    echo [SUCCESS] Setup complete!
    echo.
)

REM 4. Activate and Start
call venv\Scripts\activate

REM Open browser after 3 seconds
start /b cmd /c "timeout /t 3 /nobreak >nul && start "" http://127.0.0.1:8000"

echo [SUCCESS] Server starting at http://127.0.0.1:8000
echo [TIP] Press Ctrl+C to stop the server when finished.
echo.

uvicorn src.main:app --port 8000
pause
