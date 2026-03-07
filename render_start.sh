#!/bin/bash

# Exit script if any command fails
set -e

# Rebuild ChromaDB vectors natively in Linux from the JSON chunks
echo "Reconstructing ChromaDB Database locally..."
cd phase4 || exit
python3 run_phase4.py
cd ..

# Start the FastAPI server
echo "Starting FastAPI server..."
cd phase5 || exit
# Render passes the port in the $PORT env variable, default to 8000
PORT=${PORT:-8000}
uvicorn api:app --host 0.0.0.0 --port $PORT
