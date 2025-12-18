#!/usr/bin/env bash
set -euo pipefail

# iMessage Analysis - Single entry point
# Automatically runs ETL if needed, then starts the app

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
ANALYSIS_DB="${HOME}/.imessage_analysis/analysis.db"
SNAPSHOTS_DIR="${HOME}/.imessage_analysis/snapshots"
MAX_AGE_DAYS=7

# ============================================================================
# Prerequisites
# ============================================================================

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "❌ Virtual environment not found. Run ./init.sh first."
  exit 1
fi

PY="${VENV_DIR}/bin/python"

if ! command -v npm >/dev/null 2>&1; then
  echo "❌ npm is required. Please install Node.js."
  exit 1
fi

if [[ ! -d "${ROOT_DIR}/frontend/node_modules" ]]; then
  echo "📦 Installing frontend dependencies..."
  (cd "${ROOT_DIR}/frontend" && npm install)
fi

# ============================================================================
# ETL Check - Run if analysis.db is missing or stale
# ============================================================================

run_etl() {
  echo ""
  echo "╔════════════════════════════════════════════════════════════╗"
  echo "║                 Running ETL Pipeline                       ║"
  echo "╚════════════════════════════════════════════════════════════╝"
  echo ""

  # Check Full Disk Access
  CHAT_DB="${HOME}/Library/Messages/chat.db"
  if [[ ! -r "${CHAT_DB}" ]]; then
    echo "❌ Cannot read chat.db - Full Disk Access required"
    echo ""
    echo "   1. Open: System Preferences → Privacy & Security → Full Disk Access"
    echo "   2. Add your terminal app (Terminal, iTerm, VS Code, or Cursor)"
    echo "   3. Restart your terminal completely"
    echo "   4. Run ./run.sh again"
    echo ""
    exit 1
  fi
  echo "✓ chat.db accessible"

  # Check for Contacts database
  CONTACTS_ARG="None"
  CONTACTS_DIR="${HOME}/Library/Application Support/AddressBook"
  if [[ -d "${CONTACTS_DIR}" ]] && [[ -r "${CONTACTS_DIR}" ]]; then
    CONTACTS_DB=$(find "${CONTACTS_DIR}" -name "AddressBook-v*.abcddb" 2>/dev/null | head -1 || true)
    if [[ -n "${CONTACTS_DB}" ]] && [[ -r "${CONTACTS_DB}" ]]; then
      echo "✓ Contacts database found"
      CONTACTS_ARG="Path('${CONTACTS_DB}')"
    else
      echo "⚠ Contacts not accessible (names will be limited)"
    fi
  else
    echo "⚠ Contacts not accessible (names will be limited)"
  fi

  echo ""
  echo "Extracting and transforming data..."
  echo ""

  "${PY}" -c "
from pathlib import Path
from imessage_analysis.etl.pipeline import run_etl_with_snapshot

result = run_etl_with_snapshot(
    source_db_path=Path.home() / 'Library/Messages/chat.db',
    analysis_db_path=Path.home() / '.imessage_analysis/analysis.db',
    snapshots_dir=Path.home() / '.imessage_analysis/snapshots',
    contacts_db_path=${CONTACTS_ARG},
    force_full=True,
)
print(result)
"

  echo ""
  echo "✓ ETL complete"
  echo ""
}

needs_etl() {
  # Check if analysis.db exists
  if [[ ! -f "${ANALYSIS_DB}" ]]; then
    echo "📊 analysis.db not found - ETL required"
    return 0
  fi

  # Check if analysis.db has data
  local msg_count
  msg_count=$("${PY}" -c "
import sqlite3
conn = sqlite3.connect('${ANALYSIS_DB}')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM fact_message')
print(cursor.fetchone()[0])
conn.close()
" 2>/dev/null || echo "0")

  if [[ "${msg_count}" == "0" ]]; then
    echo "📊 analysis.db is empty - ETL required"
    return 0
  fi

  # Check if analysis.db is stale (older than MAX_AGE_DAYS)
  local file_age_days
  if [[ "$(uname)" == "Darwin" ]]; then
    # macOS
    local file_mtime
    file_mtime=$(stat -f %m "${ANALYSIS_DB}")
    local now
    now=$(date +%s)
    file_age_days=$(( (now - file_mtime) / 86400 ))
  else
    # Linux
    file_age_days=$(( ($(date +%s) - $(stat -c %Y "${ANALYSIS_DB}")) / 86400 ))
  fi

  if [[ "${file_age_days}" -ge "${MAX_AGE_DAYS}" ]]; then
    echo "📊 analysis.db is ${file_age_days} days old - refreshing"
    return 0
  fi

  echo "✓ analysis.db is up to date (${msg_count} messages, ${file_age_days} days old)"
  return 1
}

# Run ETL if needed
if needs_etl; then
  run_etl
fi

# ============================================================================
# Start the App
# ============================================================================

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              iMessage Analysis App                         ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  Frontend:     http://127.0.0.1:${FRONTEND_PORT}                        ║"
echo "║  Backend API:  http://${BACKEND_HOST}:${BACKEND_PORT}                        ║"
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
  [[ -n "${BACKEND_PID}" ]] && kill "${BACKEND_PID}" 2>/dev/null
  [[ -n "${FRONTEND_PID}" ]] && kill "${FRONTEND_PID}" 2>/dev/null
  echo "Goodbye!"
}

trap cleanup EXIT INT TERM

# Start backend
"${PY}" -m uvicorn imessage_analysis.api:app --host "${BACKEND_HOST}" --port "${BACKEND_PORT}" &
BACKEND_PID="$!"

# Start frontend
(cd "${ROOT_DIR}/frontend" && npm run dev -- --host 127.0.0.1 --port "${FRONTEND_PORT}") &
FRONTEND_PID="$!"

# Wait for both
wait "${BACKEND_PID}" "${FRONTEND_PID}"
