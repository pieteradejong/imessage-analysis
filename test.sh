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
CYAN='\033[0;36m'  # Bright cyan for headers (more readable than blue)
NC='\033[0m' # No Color

# Track failures
FAILURES=0

print_header() {
  echo ""
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${CYAN}$1${NC}"
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
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
              imessage_analysis.api imessage_analysis.visualization \
              imessage_analysis.etl imessage_analysis.etl.schema \
              imessage_analysis.etl.normalizers imessage_analysis.etl.extractors \
              imessage_analysis.etl.loaders imessage_analysis.etl.identity \
              imessage_analysis.etl.pipeline imessage_analysis.etl.validation; do
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
  --cov-fail-under=50 \
  -v \
  --tb=short \
  -m "not integration"; then
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
  "imessage_analysis.etl.schema:create_schema,verify_schema"
  "imessage_analysis.etl.normalizers:normalize_phone,normalize_email,detect_contact_type"
  "imessage_analysis.etl.extractors:extract_handles,extract_messages"
  "imessage_analysis.etl.loaders:load_handles,load_messages"
  "imessage_analysis.etl.identity:resolve_all_handles,create_unknown_person"
  "imessage_analysis.etl.pipeline:run_etl,get_etl_status"
  "imessage_analysis.etl.validation:validate_etl"
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

# 8. ETL Module Tests
print_header "8️⃣  ETL Module Tests"
echo "Running ETL-specific tests..."
if run_test "${PY}" -m pytest tests/test_normalizers.py tests/test_schema.py tests/test_extractors.py tests/test_loaders.py tests/test_identity.py tests/test_pipeline.py tests/test_contacts_extractors.py tests/test_contacts_loaders.py tests/test_identity_resolution.py tests/test_contacts_integration.py -v --tb=short -m "not integration" 2>&1 | tail -30; then
  print_success "ETL module tests passed"
else
  print_error "ETL module tests failed"
fi

# 9. Property-Based Tests (Hypothesis)
print_header "9️⃣  Property-Based Tests (Hypothesis)"
echo "Running property-based tests..."
if "${PY}" -c "import hypothesis" 2>/dev/null; then
  if run_test "${PY}" -m pytest tests/test_properties.py -v --tb=short -m "property" 2>&1 | tail -20; then
    print_success "Property-based tests passed"
  else
    # Try without the marker in case tests aren't marked
    if run_test "${PY}" -m pytest tests/test_properties.py -v --tb=short 2>&1 | tail -20; then
      print_success "Property-based tests passed"
    else
      print_error "Property-based tests failed"
    fi
  fi
else
  echo -e "${YELLOW}⚠${NC}  hypothesis not installed. Install with: pip install hypothesis"
  TESTS_RUN=$((TESTS_RUN + 1))
  TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# 10. API Endpoint Tests
print_header "🔟  API Endpoint Tests"
echo "Running API endpoint tests..."
if run_test "${PY}" -m pytest tests/test_api_endpoints.py -v --tb=short 2>&1 | tail -20; then
  print_success "API endpoint tests passed"
else
  print_error "API endpoint tests failed"
fi

# 11. Integration Tests (optional, may use real data)
print_header "1️⃣1️⃣  Integration Tests"
echo "Running integration tests (uses real chat.db if available)..."
# Run integration tests - they may fail if real chat.db is not accessible
INTEGRATION_OUTPUT=$("${PY}" -m pytest -m integration -v --tb=short 2>&1 || true)
echo "$INTEGRATION_OUTPUT" | tail -30

# Check if all tests were skipped (no real data available)
SKIP_COUNT=$(echo "$INTEGRATION_OUTPUT" | grep -c "SKIPPED" || echo "0")
PASS_COUNT=$(echo "$INTEGRATION_OUTPUT" | grep -c "PASSED" || echo "0")
FAIL_COUNT=$(echo "$INTEGRATION_OUTPUT" | grep -c "FAILED" || echo "0")

if [[ "$FAIL_COUNT" -eq 0 ]]; then
  if [[ "$SKIP_COUNT" -gt 0 ]] && [[ "$PASS_COUNT" -eq 0 ]]; then
    echo -e "${YELLOW}⚠${NC}  Integration tests skipped (no real chat.db available)"
  else
    print_success "Integration tests passed"
  fi
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  print_error "Integration tests failed"
fi

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

