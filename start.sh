#!/bin/bash
# Kill any existing instances
lsof -ti:8000 | xargs kill -9 2>/dev/null

cd "$(dirname "$0")"
echo "Starting Tri-LLM..."
echo "Local:  http://localhost:8000"
echo ""
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
