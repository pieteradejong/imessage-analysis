#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "Error: .venv not found. Run ./init.sh first."
  exit 1
fi

PY="${VENV_DIR}/bin/python"

echo "Running black (check)..."
"${PY}" -m black --check .

echo "Running mypy..."
"${PY}" -m mypy imessage_analysis

echo "Running pytest..."
"${PY}" -m pytest

echo "All tests passed."

