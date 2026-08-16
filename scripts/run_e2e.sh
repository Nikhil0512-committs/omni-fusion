#!/bin/bash
set -e
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"
trap 'echo "Killing servers..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true' EXIT

echo "Starting Backend..."
PYTHONPATH=backend python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Starting Frontend..."
cd frontend
NEXT_PUBLIC_E2E_TEST=true npm run start &
FRONTEND_PID=$!

echo "Waiting for servers to start..."
sleep 15

echo "Running Edge Cases Puppeteer script..."
node test_edge_cases.js

echo "Killing servers..."
kill $BACKEND_PID
kill $FRONTEND_PID

echo "End-to-End Test Complete!"
