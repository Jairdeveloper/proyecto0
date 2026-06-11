#!/bin/sh
# ============================================================================
# test_llm_real.sh - Tests de integracion LLM con API real (MANUAL)
# ============================================================================
#
# PROPOSITO:
#   Tests opcionales que requieren conexion a internet y API keys configuradas.
#   Solo ejecutar si se dispone de ANTHROPIC_API_KEY o OPENAI_API_KEY.
#
# USO:
#   export ANTHROPIC_API_KEY="sk-ant-..."
#   ./test_llm_real.sh
#
# PRECAUCION:
#   Cada test realiza una llamada real a la API, lo que tiene costo.
# ============================================================================

TESTS_DIR="$(dirname "$0")"
BOT_DIR="${TESTS_DIR}/.."
PASS=0
FAIL=0

has_anthropic_key=false
has_openai_key=false

[ -n "$ANTHROPIC_API_KEY" ] && has_anthropic_key=true
[ -n "$OPENAI_API_KEY" ] && has_openai_key=true

if ! $has_anthropic_key && ! $has_openai_key; then
    echo "No hay API keys configuradas."
    echo "Configura ANTHROPIC_API_KEY o OPENAI_API_KEY para ejecutar estos tests."
    exit 0
fi

assert_contains() {
    _name="$1"
    _haystack="$2"
    _needle="$3"
    if echo "$_haystack" | grep -q "$_needle"; then
        echo "  PASS: $_name"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $_name"
        echo "    output: $_haystack"
        FAIL=$((FAIL + 1))
    fi
}

if $has_anthropic_key; then
    echo "--- Claude: scaffold_module ---"
    result=$(RECPL_LLM_PROVIDER=claude \
        "${BOT_DIR}/frontend/llm_classifier.sh" \
        "crea un modulo de pagos en NestJS" 2>/dev/null)
    assert_contains "claude: scaffold action" "$result" '"accion":"scaffold"'
    assert_contains "claude: nombre Pagos" "$result" '"nombre"'

    echo ""
    echo "--- Claude: respond (pregunta) ---"
    result=$(RECPL_LLM_PROVIDER=claude \
        "${BOT_DIR}/frontend/llm_classifier.sh" \
        "que modulos tengo?" 2>/dev/null)
    assert_contains "claude: respond action" "$result" '"accion":"respond"'
fi

if $has_openai_key; then
    echo ""
    echo "--- OpenAI: scaffold_module ---"
    result=$(RECPL_LLM_PROVIDER=openai \
        "${BOT_DIR}/frontend/llm_classifier.sh" \
        "crea una entidad Usuario en Prisma" 2>/dev/null)
    assert_contains "openai: scaffold action" "$result" '"accion":"scaffold"'
fi

echo ""
echo "=========================================="
echo "LLM Real Tests: $PASS pasaron, $FAIL fallaron"
echo "=========================================="

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
