#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "Error: .venv not found. Run ./init.sh first."
  exit 1
fi

PY="${VENV_DIR}/bin/python"

if [[ ! -d "${ROOT_DIR}/frontend" ]]; then
  echo "Error: frontend/ not found."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "Error: npm is required to run the frontend."
  exit 1
fi

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

echo "Starting backend on http://${BACKEND_HOST}:${BACKEND_PORT}"
echo "Starting frontend on http://127.0.0.1:${FRONTEND_PORT}"

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  set +e
  if [[ -n "${BACKEND_PID}" ]]; then
    kill "${BACKEND_PID}" >/dev/null 2>&1 || true
  fi
  if [[ -n "${FRONTEND_PID}" ]]; then
    kill "${FRONTEND_PID}" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

"${PY}" -m uvicorn imessage_analysis.api:app --reload --host "${BACKEND_HOST}" --port "${BACKEND_PORT}" &
BACKEND_PID="$!"

(cd "${ROOT_DIR}/frontend" && npm run dev -- --host 127.0.0.1 --port "${FRONTEND_PORT}") &
FRONTEND_PID="$!"

wait "${BACKEND_PID}" "${FRONTEND_PID}"

