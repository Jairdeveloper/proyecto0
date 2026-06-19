#!/usr/bin/env bash
# daily_check.sh — Gate diario estable para RECPL
#
# Ejecuta los cuatro comandos del gate diario y reporta PASS/FAIL.
# No set -e, no eval. Sale 1 si algun comando falla.
#
# Uso: ./scripts/daily_check.sh

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAIL=0
RESULTS=""

run_step() {
    local label="$1"
    shift
    echo "=== $label ==="
    if "$@"; then
        RESULTS="${RESULTS}[PASS] $label"$'\n'
        echo ""
    else
        RESULTS="${RESULTS}[FAIL] $label"$'\n'
        FAIL=1
        echo ""
    fi
}

echo "=== RECPL Daily Gate ==="
echo ""

run_step "ruff" ruff check "$PROJECT_ROOT/compiler-bot/agentic_pipeline"

run_step "RECPL shell tests" bash "$PROJECT_ROOT/compiler-bot/tests/run_tests.sh"

run_step "Agent-robot tests" bash "$PROJECT_ROOT/compiler-bot/tests/test_agent.sh"

run_step "Metrics CLI" "$PROJECT_ROOT/compiler-bot/agentic" --metrics json

echo "=== Summary ==="
echo "$RESULTS"

if [ "$FAIL" -eq 0 ]; then
    echo "Gate: PASS"
    exit 0
fi

echo "Gate: FAIL — review failures above"
exit 1
