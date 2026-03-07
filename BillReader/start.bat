@echo off
title Bill Reconciliation App

echo Starting Bill Reconciliation App...
echo.

REM Check if venv exists, if not create it
if not exist "venv\" (
    echo Setting up for first time...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
    echo Setup complete!
    echo.
)

REM Activate virtual environment and start the server
call venv\Scripts\activate

REM Wait 3 seconds for server to start, then open browser
start /b cmd /c "timeout /t 3 /nobreak >nul && start "" http://127.0.0.1:8000"

echo Server running at http://127.0.0.1:8000
echo Press Ctrl+C to stop the server.
echo.

uvicorn src.main:app --port 8000
