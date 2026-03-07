#!/bin/bash

# Exit script if any command fails
set -e

# Install playwright browsers
python3 -m playwright install chromium

# 1. Run the initial Scrape & DB setup pipeline
echo "Starting data initialization pipeline..."
cd orchestrator || exit
python3 run_pipeline.py

# 2. Start the daily background scheduler
echo "Starting background cron scheduler for daily updates..."
python3 scheduler.py &

# 3. Start the FastAPI server
echo "Starting FastAPI server..."
cd ../phase5 || exit
# Render passes the port in the $PORT env variable, default to 8000
PORT=${PORT:-8000}
uvicorn api:app --host 0.0.0.0 --port $PORT
