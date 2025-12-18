#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

# Check for virtual environment
if [[ ! -d "${VENV_DIR}" ]]; then
  echo "Error: .venv not found. Run ./init.sh first."
  exit 1
fi

PY="${VENV_DIR}/bin/python"

# Check for frontend directory
if [[ ! -d "${ROOT_DIR}/frontend" ]]; then
  echo "Error: frontend/ not found."
  exit 1
fi

# Check for npm
if ! command -v npm >/dev/null 2>&1; then
  echo "Error: npm is required to run the frontend."
  exit 1
fi

# Check for frontend dependencies
if [[ ! -d "${ROOT_DIR}/frontend/node_modules" ]]; then
  echo "Frontend dependencies not installed. Running npm install..."
  (cd "${ROOT_DIR}/frontend" && npm install)
fi

# Configuration
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

# Print startup banner
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              iMessage Analysis App                         ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  Backend API:  http://${BACKEND_HOST}:${BACKEND_PORT}                        ║"
echo "║  Frontend:     http://127.0.0.1:${FRONTEND_PORT}                        ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  Press Ctrl+C to stop                                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  echo "Shutting down..."
  set +e
  if [[ -n "${BACKEND_PID}" ]]; then
    kill "${BACKEND_PID}" >/dev/null 2>&1 || true
  fi
  if [[ -n "${FRONTEND_PID}" ]]; then
    kill "${FRONTEND_PID}" >/dev/null 2>&1 || true
  fi
  echo "Goodbye!"
}

trap cleanup EXIT INT TERM

# Start backend
"${PY}" -m uvicorn imessage_analysis.api:app --reload --host "${BACKEND_HOST}" --port "${BACKEND_PORT}" &
BACKEND_PID="$!"

# Start frontend
(cd "${ROOT_DIR}/frontend" && npm run dev -- --host 127.0.0.1 --port "${FRONTEND_PORT}") &
FRONTEND_PID="$!"

# Wait for both processes
wait "${BACKEND_PID}" "${FRONTEND_PID}"
