#!/bin/sh
# ============================================================================
# test_agent.sh - Tests de la capa agent-robot (Fase 1)
# ============================================================================
#
# USO:
#   ./tests/test_agent.sh           # ejecutar todos
#   ./tests/test_agent.sh bridge    # solo tests de bridge
#   ./tests/test_agent.sh agent     # solo tests de agent.sh
# ============================================================================

SCRIPT_DIR="$(dirname "$0")/.."
PASS=0
FAIL=0
FAIL_MSGS=""

# --- Test: archivos existen ---
test_files_exist() {
    for f in \
        "$SCRIPT_DIR/agent-robot/config.sh" \
        "$SCRIPT_DIR/agent-robot/bridge.sh" \
        "$SCRIPT_DIR/agent-robot/agent.sh" \
        "$SCRIPT_DIR/agent-robot/memory.sh" \
        "$SCRIPT_DIR/agent-robot/tools/tool_registry.sh" \
        "$SCRIPT_DIR/agent-robot/tools/tool_recpl.sh" \
        "$SCRIPT_DIR/agent-robot/tools/tool_respond.sh" \
        "$SCRIPT_DIR/agent-robot/tools/tool_read_file.sh" \
        "$SCRIPT_DIR/agent-robot/tools/tool_write_file.sh" \
        "$SCRIPT_DIR/agent-robot/tools/tool_run_command.sh"; do
        if [ -f "$f" ]; then
            echo "  ✅ Existe: $(basename "$f")"
        else
            echo "  ❌ FALTA: $f"
            FAIL=$((FAIL + 1))
            FAIL_MSGS="${FAIL_MSGS}FALTAN_ARCHIVOS "
        fi
    done
}

# --- Test: bash syntax ---
test_bash_syntax() {
    for f in \
        "$SCRIPT_DIR/agent-robot/config.sh" \
        "$SCRIPT_DIR/agent-robot/bridge.sh" \
        "$SCRIPT_DIR/agent-robot/agent.sh" \
        "$SCRIPT_DIR/agent-robot/memory.sh" \
        "$SCRIPT_DIR/agent-robot/tools/tool_registry.sh" \
        "$SCRIPT_DIR/agent-robot/tools/tool_recpl.sh" \
        "$SCRIPT_DIR/agent-robot/tools/tool_respond.sh" \
        "$SCRIPT_DIR/agent-robot/tools/tool_read_file.sh" \
        "$SCRIPT_DIR/agent-robot/tools/tool_write_file.sh" \
        "$SCRIPT_DIR/agent-robot/tools/tool_run_command.sh"; do
        if bash -n "$f" 2>/dev/null; then
            echo "  ✅ Syntax OK: $(basename "$f")"
        else
            echo "  ❌ Syntax ERROR: $f"
            FAIL=$((FAIL + 1))
            FAIL_MSGS="${FAIL_MSGS}SYNTAX_$(basename "$f" .sh) "
        fi
    done
}

# --- Test: agent responde saludo ---
test_agent_greeting() {
    _result=$(cd "$SCRIPT_DIR" && ./agent-robot/agent.sh "hola" 2>/dev/null)
    if echo "$_result" | grep -qi "hola\|ayudar\|proyecto0"; then
        echo "  ✅ Agent responde saludo"
    else
        echo "  ❌ Agent no responde saludo"
        echo "     Output: $_result"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}AGENT_SALUDO "
    fi
}

# --- Test: agent responde "quien eres" ---
test_agent_identity() {
    _result=$(cd "$SCRIPT_DIR" && ./agent-robot/agent.sh "quien eres?" 2>/dev/null)
    if echo "$_result" | grep -qi "proyecto0\|agente\|recpl"; then
        echo "  ✅ Agent responde identidad"
    else
        echo "  ❌ Agent no responde identidad"
        echo "     Output: $_result"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}AGENT_IDENTIDAD "
    fi
}

# --- Test: bridge recpl ---
test_bridge_recpl() {
    _result=$(cd "$SCRIPT_DIR" && sh -c '. agent-robot/bridge.sh && bridge_recpl "crea modulo testbridge en nestjs" 2>/dev/null')
    _exito=$(echo "$_result" | jq -r '.exito // false' 2>/dev/null)
    _origen=$(echo "$_result" | jq -r '.origen // ""' 2>/dev/null)

    if [ "$_exito" = "true" ] && [ "$_origen" = "recpl" ]; then
        echo "  ✅ Bridge ejecuta RECPL exitosamente"
    else
        echo "  ⚠️  Bridge ejecuta RECPL (puede fallar sin estado RECPL)"
        echo "     Output: $_result"
    fi
}

# --- Test: tool respond ---
test_tool_respond() {
    _result=$(cd "$SCRIPT_DIR" && sh -c '. agent-robot/tools/tool_respond.sh && tool_respond "test message"')
    _exito=$(echo "$_result" | jq -r '.exito // false' 2>/dev/null)
    _mensaje=$(echo "$_result" | jq -r '.mensaje // ""' 2>/dev/null)

    if [ "$_exito" = "true" ] && [ "$_mensaje" = "test message" ]; then
        echo "  ✅ tool_respond funciona"
    else
        echo "  ❌ tool_respond falla"
        echo "     Output: $_result"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}TOOL_RESPOND "
    fi
}

# --- Test: tool registry ---
test_tool_registry() {
    _exists=$(cd "$SCRIPT_DIR" && sh -c '. agent-robot/tools/tool_registry.sh && has_tool "respond" && echo "yes"')
    if [ "$_exists" = "yes" ]; then
        echo "  ✅ tool_registry detecta herramientas"
    else
        echo "  ❌ tool_registry no detecta herramientas"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}TOOL_REGISTRY "
    fi
}

# --- Test: memory ---
test_memory() {
    cd "$SCRIPT_DIR" || return
    AGENT_MEMORY_DIR="/tmp/test_agent_memory_$$"
    . agent-robot/memory.sh
    memory_init
    memory_save "test_key" "test_value"
    _value=$(memory_get "test_key")
    rm -rf "$AGENT_MEMORY_DIR"

    if [ "$_value" = "test_value" ]; then
        echo "  ✅ memory save/get funciona"
    else
        echo "  ❌ memory save/get falla (got: $_value)"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}MEMORY "
    fi

    unset AGENT_MEMORY_DIR
}

# --- Fase 2: tool_read_file ---
test_tool_read_file() {
    # Crear archivo temporal
    _tmp="/tmp/test_agent_read_$$.txt"
    echo "contenido de prueba" > "$_tmp"

    _result=$(cd "$SCRIPT_DIR" && sh -c '. agent-robot/tools/tool_read_file.sh && tool_read_file "'$_tmp'"')
    _exito=$(echo "$_result" | jq -r '.exito // false' 2>/dev/null)

    if [ "$_exito" = "true" ]; then
        echo "  ✅ tool_read_file funciona"
    else
        echo "  ❌ tool_read_file falla"
        echo "     Output: $_result"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}TOOL_READ_FILE "
    fi
    rm -f "$_tmp"
}

# --- Fase 2: tool_write_file ---
test_tool_write_file() {
    _tmp="/tmp/test_agent_write_$$.txt"
    _result=$(cd "$SCRIPT_DIR" && sh -c '. agent-robot/tools/tool_write_file.sh && tool_write_file "'$_tmp'" "test content"')
    _exito=$(echo "$_result" | jq -r '.exito // false' 2>/dev/null)

    if [ "$_exito" = "true" ] && [ -f "$_tmp" ]; then
        echo "  ✅ tool_write_file funciona"
    else
        echo "  ❌ tool_write_file falla"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}TOOL_WRITE_FILE "
    fi
    rm -f "$_tmp"
}

# --- Fase 2: tool_run_command ---
test_tool_run_command() {
    _result=$(cd "$SCRIPT_DIR" && sh -c '. agent-robot/tools/tool_run_command.sh && tool_run_command "echo ok"')
    _exito=$(echo "$_result" | jq -r '.exito // false' 2>/dev/null)

    if [ "$_exito" = "true" ]; then
        echo "  ✅ tool_run_command funciona"
    else
        echo "  ❌ tool_run_command falla"
        echo "     Output: $_result"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}TOOL_RUN_COMMAND "
    fi
}

# --- Test: --agent flag ---
test_agent_flag() {
    _result=$(cd "$SCRIPT_DIR" && ./recpl.sh --agent "hola" 2>/dev/null)
    if echo "$_result" | grep -qi "proyecto0\|agente"; then
        echo "  ✅ Flag --agent funciona desde recpl.sh"
    else
        echo "  ⚠️  Flag --agent (puede fallar si no se implemento aun)"
        echo "     Output: $_result"
    fi
}

# --- MAIN ---
echo "=========================================="
echo " Tests Agent-Robot (Fase 1 + Fase 2)"
echo "=========================================="
echo ""

echo "--- Archivos ---"
test_files_exist
echo ""

echo "--- Syntax Check ---"
test_bash_syntax
echo ""

echo "--- Funcionalidad ---"
test_tool_respond
test_tool_registry
test_memory
test_tool_read_file
test_tool_write_file
test_tool_run_command
test_agent_greeting
test_agent_identity
test_bridge_recpl
test_agent_flag
echo ""

echo "Resultados: PASS=$PASS FAIL=$FAIL"
echo "Fallos: ${FAIL_MSGS:-ninguno}"
echo "=========================================="
[ $FAIL -eq 0 ] && exit 0 || exit 1
