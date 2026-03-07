#!/bin/bash

# Exit script if any command fails
set -e

# Start the FastAPI server
echo "Starting FastAPI server..."
cd phase5 || exit
# Render passes the port in the $PORT env variable, default to 8000
PORT=${PORT:-8000}
uvicorn api:app --host 0.0.0.0 --port $PORT
