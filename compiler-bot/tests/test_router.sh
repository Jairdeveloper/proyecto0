#!/bin/sh
# ============================================================================
# test_router.sh - Tests para el router inteligente del RECPL Compiler Bot
# ============================================================================
#
# PROPOSITO:
#   Verifica que el router (frontend/router.sh) decide correctamente entre
#   pipeline deterministico y LLM, y que maneja errores adecuadamente.
#
# USO:
#   ./test_router.sh
#
# DEPENDENCIAS:
#   jq, bash
# ============================================================================

TESTS_DIR="$(dirname "$0")"
BOT_DIR="${TESTS_DIR}/.."
PASS=0
FAIL=0

assert_exit() {
    _name="$1"
    _code="$2"
    _exp="$3"
    if [ "$_code" -eq "$_exp" ]; then
        echo "  PASS: $_name"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $_name (exit code: $_code, esperado: $_exp)"
        FAIL=$((FAIL + 1))
    fi
}

assert_contains() {
    _name="$1"
    _haystack="$2"
    _needle="$3"
    if echo "$_haystack" | grep -q "$_needle"; then
        echo "  PASS: $_name"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $_name"
        echo "    patron no encontrado: $_needle"
        echo "    en: $_haystack"
        FAIL=$((FAIL + 1))
    fi
}

echo "--- Router: Deterministic mode ---"

result=$(RECPL_LLM_MODE=deterministic \
    RECPL_STATE_DIR="/tmp/recpl_router_test_$$" \
    "${BOT_DIR}/frontend/router.sh" "crea modulo pagos en nestjs" 2>/dev/null)
assert_contains "deterministic: scaffold action" "$result" '"accion":"scaffold"'
assert_contains "deterministic: module type" "$result" '"tipo":"module"'
assert_contains "deterministic: nombre pagos" "$result" '"nombre"'
rm -rf "/tmp/recpl_router_test_$$"

echo ""
echo "--- Router: LLM mode (no API key) ---"

result=$(RECPL_LLM_MODE=llm \
    RECPL_STATE_DIR="/tmp/recpl_router_test_$$" \
    "${BOT_DIR}/frontend/router.sh" "crea modulo pagos en nestjs" 2>/dev/null)
assert_contains "llm mode: error" "$result" '"accion":"error"'
rm -rf "/tmp/recpl_router_test_$$"

echo ""
echo "--- Router: Empty input ---"

result=$("${BOT_DIR}/frontend/router.sh" "" 2>/dev/null)
assert_contains "empty input: error" "$result" '"accion":"error"'

echo ""
echo "--- Router: Unknown instruction (auto mode, no LLM) ---"

result=$(RECPL_LLM_MODE=auto \
    RECPL_STATE_DIR="/tmp/recpl_router_test_$$" \
    "${BOT_DIR}/frontend/router.sh" "haz algo bonito" 2>/dev/null)
assert_contains "unknown instruction: error" "$result" '"accion":"error"'
rm -rf "/tmp/recpl_router_test_$$"

echo ""
echo "=========================================="
echo "Router Tests: $PASS pasaron, $FAIL fallaron"
echo "=========================================="

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
