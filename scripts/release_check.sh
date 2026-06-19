#!/usr/bin/env bash
# release_check.sh — Gate de release para RECPL
#
# Ejecuta los seis comandos del gate de release y reporta PASS/FAIL.
# Sale 1 si algun comando falla.
#
# NOTA: El paso 6 (pytest completo) puede fallar en entornos sin _sqlite3,
# torch/CUDA funcional o con referencias antiguas a HybridPlanner.
# En ese caso, priorizar reparar el entorno antes de hacer release.
#
# Uso: ./scripts/release_check.sh

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

echo "=== RECPL Release Gate ==="
echo ""

run_step "Version alignment" bash "$PROJECT_ROOT/scripts/check_version_alignment.sh"

run_step "ruff" ruff check "$PROJECT_ROOT/compiler-bot/agentic_pipeline"

run_step "RECPL shell tests" bash "$PROJECT_ROOT/compiler-bot/tests/run_tests.sh"

run_step "Agent-robot tests" bash "$PROJECT_ROOT/compiler-bot/tests/test_agent.sh"

run_step "Metrics CLI" "$PROJECT_ROOT/compiler-bot/agentic" --metrics json

run_step "Python test suite" python -m pytest "$PROJECT_ROOT/compiler-bot/agentic_pipeline/tests/" -q --tb=short -o "addopts="

echo "=== Summary ==="
echo "$RESULTS"

if [ "$FAIL" -eq 0 ]; then
    echo "Release gate: PASS"
    exit 0
fi

echo "Release gate: FAIL — review failures above"
echo ""
echo "If the Python test suite failed, the environment may need修复:"
echo "  - Ensure Python has _sqlite3 compiled in"
echo "  - Fix torch/CUDA libcudart.so.13 errors"
echo "  - Update tests referencing HybridPlanner -> ReasoningEngine"
exit 1
