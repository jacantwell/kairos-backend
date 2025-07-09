#!/bin/bash

# Optional: activate virtual environment
# source venv/bin/activate

# Set default host and port
HOST="127.0.0.1"
PORT="8000"

# Launch uvicorn
poetry run uvicorn app.main:app --host $HOST --port $PORT --reload
