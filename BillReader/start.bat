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
start "" http://127.0.0.1:8000
uvicorn src.main:app --port 8000
