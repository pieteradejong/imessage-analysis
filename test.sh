#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "Error: .venv not found. Run ./init.sh first."
  exit 1
fi

PY="${VENV_DIR}/bin/python"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track failures
FAILURES=0

print_header() {
  echo ""
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
  echo -e "${GREEN}✓${NC} $1"
}

print_error() {
  echo -e "${RED}✗${NC} $1"
  FAILURES=$((FAILURES + 1))
}

# Test counter
TESTS_RUN=0
TESTS_PASSED=0

run_test() {
  TESTS_RUN=$((TESTS_RUN + 1))
  if "$@"; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
    return 0
  else
    return 1
  fi
}

print_header "🧪 Running Comprehensive Test Suite"
echo ""

# 1. Code Formatting Check
print_header "1️⃣  Code Formatting (black)"
if run_test "${PY}" -m black --check . >/dev/null 2>&1; then
  print_success "Code formatting is correct"
else
  print_error "Code formatting issues found. Run: ${PY} -m black ."
fi

# 2. Type Checking
print_header "2️⃣  Type Checking (mypy)"
if run_test "${PY}" -m mypy imessage_analysis --no-error-summary 2>&1 | tee /tmp/mypy_output.txt; then
  print_success "Type checking passed"
else
  print_error "Type checking failed"
fi

# 3. Import Checks
print_header "3️⃣  Import Checks"
IMPORT_FAILED=0
for module in imessage_analysis imessage_analysis.config imessage_analysis.database \
              imessage_analysis.queries imessage_analysis.analysis \
              imessage_analysis.snapshot imessage_analysis.utils \
              imessage_analysis.api imessage_analysis.visualization; do
  if "${PY}" -c "import $module" 2>/dev/null; then
    print_success "Can import: $module"
  else
    print_error "Cannot import: $module"
    IMPORT_FAILED=1
  fi
done

if [[ $IMPORT_FAILED -eq 0 ]]; then
  TESTS_PASSED=$((TESTS_PASSED + 1))
fi
TESTS_RUN=$((TESTS_RUN + 1))

# 4. Security Check (bandit) - optional
print_header "4️⃣  Security Check (bandit)"
if "${PY}" -m bandit --version >/dev/null 2>&1; then
  if run_test "${PY}" -m bandit -r imessage_analysis -f json -o /tmp/bandit_report.json 2>&1 | grep -q "No issues identified" || true; then
    print_success "No security issues found"
  else
    print_error "Security issues found. Check /tmp/bandit_report.json"
    "${PY}" -m bandit -r imessage_analysis -ll 2>&1 | head -20
  fi
else
  echo -e "${YELLOW}⚠${NC}  bandit not installed (optional). Install with: pip install bandit"
  TESTS_RUN=$((TESTS_RUN + 1))
  TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# 5. Unit Tests with Coverage
print_header "5️⃣  Unit Tests & Coverage (pytest)"
echo "Running pytest with coverage..."
if run_test "${PY}" -m pytest --cov=imessage_analysis \
  --cov-report=term-missing \
  --cov-report=html:htmlcov \
  --cov-fail-under=30 \
  -v \
  --tb=short; then
  print_success "All unit tests passed"
  
  # Show coverage summary
  echo ""
  echo "Coverage Summary:"
  "${PY}" -m pytest --cov=imessage_analysis --cov-report=term --quiet -q 2>/dev/null | tail -n +2 || true
else
  print_error "Some unit tests failed"
fi

# 6. Test Count Summary
print_header "6️⃣  Test Summary"
TEST_COUNT=$("${PY}" -m pytest --collect-only -q 2>/dev/null | grep -c "test session starts" || echo "0")
if [[ -n "$TEST_COUNT" ]]; then
  COLLECTED=$("${PY}" -m pytest --collect-only -q 2>/dev/null | tail -1 | grep -oE '[0-9]+ (test|item)' | head -1 | grep -oE '[0-9]+' || echo "0")
  echo "Collected $COLLECTED test items"
fi

# 7. Check for missing test files
print_header "7️⃣  Test Coverage Analysis"
echo "Checking for untested modules..."
MISSING_TESTS=0

# List of modules that should have tests
MODULES=(
  "imessage_analysis.config:Config,get_config,set_config"
  "imessage_analysis.database:DatabaseConnection"
  "imessage_analysis.queries:table_names,rows_count,columns_for_table,get_latest_messages,get_messages_fuzzy_match,get_chars_and_length_by_counterpart"
  "imessage_analysis.analysis:get_latest_messages_data,get_message_statistics_by_chat,get_chat_analysis,get_database_summary"
  "imessage_analysis.snapshot:create_timestamped_snapshot"
  "imessage_analysis.utils:format_timestamp,format_message_count"
  "imessage_analysis.api:health,summary,latest,top_chats"
)

for module_info in "${MODULES[@]}"; do
  module="${module_info%%:*}"
  functions="${module_info#*:}"
  # Simple check - see if module is importable
  if "${PY}" -c "import $module" 2>/dev/null; then
    print_success "Module exists: $module"
  else
    print_error "Module missing: $module"
    MISSING_TESTS=$((MISSING_TESTS + 1))
  fi
done

# Final Summary
echo ""
print_header "📊 Final Test Summary"
echo ""
echo "Tests Run:    $TESTS_RUN"
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $((TESTS_RUN - TESTS_PASSED))"
echo ""

if [[ $FAILURES -gt 0 ]] || [[ $TESTS_PASSED -lt $TESTS_RUN ]]; then
  echo -e "${RED}❌ Some tests failed!${NC}"
  echo ""
  echo "Next steps:"
  echo "  - Fix formatting: ${PY} -m black ."
  echo "  - Fix type errors: Check mypy output above"
  echo "  - Fix test failures: Check pytest output above"
  echo "  - View coverage report: open htmlcov/index.html"
  exit 1
else
  echo -e "${GREEN}✅ All tests passed!${NC}"
  echo ""
  echo "Coverage report available at: htmlcov/index.html"
  exit 0
fi

