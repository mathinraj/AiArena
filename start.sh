#!/bin/bash
# Kill any existing instance on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null

cd "$(dirname "$0")"
uvicorn backend.main:app --reload --port 8000
