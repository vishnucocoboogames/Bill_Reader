#!/bin/bash
title="Bill Reconciliation App"

echo "Starting Bill Reconciliation App..."
echo ""

# Navigate to script directory
cd "$(dirname "$0")"

# Check if venv exists, if not create it
if [ ! -d "venv" ]; then
    echo "Setting up for first time..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    echo "Setup complete!"
    echo ""
fi

# Activate virtual environment and start the server
source venv/bin/activate

# Open browser after 2 seconds
sleep 2 && open "http://127.0.0.1:8000" &

echo "Server starting at http://127.0.0.1:8000"
echo "Press Ctrl+C to stop the server."
echo ""

uvicorn src.main:app --port 8000
