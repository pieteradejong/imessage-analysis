#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PYTHON_BIN=""
if command -v python3.12 >/dev/null 2>&1; then
  PYTHON_BIN="python3.12"
elif command -v python3 >/dev/null 2>&1; then
  # Verify python3 is 3.12.x
  if python3 -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3,12) else 1)'; then
    PYTHON_BIN="python3"
  fi
fi

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "Error: Python 3.12 is required."
  echo "Install Python 3.12 and ensure python3.12 is on PATH (or python3 points to 3.12)."
  exit 1
fi

echo "Using Python: ${PYTHON_BIN}"

VENV_DIR="${ROOT_DIR}/.venv"
if [[ ! -d "${VENV_DIR}" ]]; then
  echo "Creating virtualenv at ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
else
  echo "Virtualenv already exists at ${VENV_DIR}"
fi

PY="${VENV_DIR}/bin/python"
PIP="${VENV_DIR}/bin/pip"

echo "Upgrading pip..."
"${PY}" -m pip install --upgrade pip

echo "Installing Python dependencies (editable + dev extras)..."
"${PIP}" install -e "${ROOT_DIR}[dev]"

echo "Installing frontend dependencies..."
if [[ -d "${ROOT_DIR}/frontend" ]]; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "Error: npm is required to install frontend deps."
    echo "Install Node.js + npm, then re-run ./init.sh"
    exit 1
  fi
  (cd "${ROOT_DIR}/frontend" && npm install)
else
  echo "No frontend/ directory found; skipping npm install."
fi

echo "init.sh complete."

