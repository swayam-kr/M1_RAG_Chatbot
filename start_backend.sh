#!/bin/bash
# start_backend.sh — Always run this to start the FastAPI backend
# Uses the phase1 venv which has all required packages (chromadb, langchain-groq, etc.)

VENV_PYTHON="/Users/kumarswayam/Desktop/M1_RAG_Chatbot/phase1/.venv/bin/python3"
API_DIR="/Users/kumarswayam/Desktop/M1_RAG_Chatbot/phase5"

echo "⏹  Stopping any existing backend on port 8000..."
kill $(lsof -t -i:8000) 2>/dev/null
sleep 1

echo "🚀 Starting FastAPI backend with venv Python..."
cd "$API_DIR"
"$VENV_PYTHON" api.py
