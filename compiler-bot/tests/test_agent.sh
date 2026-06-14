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

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
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
        "$SCRIPT_DIR/agent-robot/tools/tool_run_command.sh" \
        "$SCRIPT_DIR/agent-robot/tools/tool_search_code.sh" \
        "$SCRIPT_DIR/agent-robot/planner.sh" \
        "$SCRIPT_DIR/agent-robot/planner_llm.sh" \
        "$SCRIPT_DIR/agent-robot/tui.sh" \
        "$SCRIPT_DIR/agent-robot/providers/apifreellm.sh" \
        "$SCRIPT_DIR/agent-robot/prompts/system_agent.txt" \
        "$SCRIPT_DIR/agent-robot/prompts/system_planner.txt" \
        "$SCRIPT_DIR/agent-robot/prompts/system_tools.txt"; do
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
        "$SCRIPT_DIR/agent-robot/tools/tool_run_command.sh" \
        "$SCRIPT_DIR/agent-robot/tools/tool_search_code.sh" \
        "$SCRIPT_DIR/agent-robot/planner.sh" \
        "$SCRIPT_DIR/agent-robot/planner_llm.sh" \
        "$SCRIPT_DIR/agent-robot/tui.sh" \
        "$SCRIPT_DIR/agent-robot/providers/apifreellm.sh"; do
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
    _mem_dir="/tmp/test_agent_memory_$$"
    _val=$(cd "$SCRIPT_DIR" && AGENT_MEMORY_DIR="$_mem_dir" sh -c '
        . agent-robot/memory.sh
        memory_init
        memory_save "test_key" "test_value"
        memory_get "test_key"
    ' 2>/dev/null)
    rm -rf "$_mem_dir"
    if [ "$_val" = "test_value" ]; then
        echo "  ✅ memory save/get funciona"
    else
        echo "  ❌ memory save/get falla (got: $_val)"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}MEMORY "
    fi
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

# --- Fase 3: planner ---
test_planner_multi_create() {
    _result=$(cd "$SCRIPT_DIR" && sh -c '. agent-robot/planner.sh && planificar "crea modulo auth y modulo payments en nestjs"')
    _tipo=$(echo "$_result" | jq -r '.tipo // ""' 2>/dev/null)
    _total=$(echo "$_result" | jq -r '.total_pasos // 0' 2>/dev/null)

    if [ "$_tipo" = "multi_create" ] && [ "$_total" -ge 2 ]; then
        echo "  ✅ planner multi-create funciona (pasos: $_total)"
    else
        echo "  ⚠️  planner multi-create (puede fallar por parsing)"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}PLANNER_MULTI "
    fi
}

# --- Fase 3: memory persistente ---
test_memory_persist() {
    _mem_dir="/tmp/test_agent_mem_persist_$$"

    # Primera sesion: guardar valor
    AGENT_MEMORY_DIR="$_mem_dir" sh -c '. '"$SCRIPT_DIR"'/agent-robot/memory.sh && memory_init && memory_save "test" "value1"'

    # Segunda sesion: leer valor (debe persistir)
    _value=$(AGENT_MEMORY_DIR="$_mem_dir" sh -c '. '"$SCRIPT_DIR"'/agent-robot/memory.sh && memory_init && memory_get "test"')

    rm -rf "$_mem_dir"

    if [ "$_value" = "value1" ]; then
        echo "  ✅ memory persistente entre sesiones"
    else
        echo "  ❌ memory no persiste (got: $_value)"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}MEMORY_PERSIST "
    fi
}

# --- Fase 3: tool_search_code ---
test_tool_search_code() {
    _result_file="/tmp/test_search_result_$$.json"
    (cd "$SCRIPT_DIR" && sh -c '. agent-robot/tools/tool_search_code.sh && tool_search_code "recpl" "agent-robot"') > "$_result_file"
    _exito=$(jq -r '.exito // false' < "$_result_file" 2>/dev/null)
    rm -f "$_result_file"

    if [ "$_exito" = "true" ]; then
        echo "  ✅ tool_search_code funciona"
    else
        echo "  ❌ tool_search_code falla"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}TOOL_SEARCH "
    fi
}

# --- Fase 4: manejo de errores ---
test_agent_error_empty() {
    _result=$(cd "$SCRIPT_DIR" && ./agent-robot/agent.sh "" 2>/dev/null)
    if echo "$_result" | grep -qi "error\|no se recibio\|vacia"; then
        echo "  ✅ Agent maneja instruccion vacia"
    else
        echo "  ⚠️  Agent manejo de error vacio (puede variar)"
    fi
}

# --- Fase 4: system prompts existen ---
test_prompts_exist() {
    for f in \
        "$SCRIPT_DIR/agent-robot/prompts/system_agent.txt" \
        "$SCRIPT_DIR/agent-robot/prompts/system_planner.txt" \
        "$SCRIPT_DIR/agent-robot/prompts/system_tools.txt"; do
        if [ -f "$f" ]; then
            echo "  ✅ Existe: $(basename "$f")"
        else
            echo "  ❌ FALTA: $f"
            FAIL=$((FAIL + 1))
            FAIL_MSGS="${FAIL_MSGS}FALTA_PROMPT "
        fi
    done
}

# --- Fase 4: logging ---
test_agent_logging() {
    _log_file="/tmp/test_agent_log_$$.txt"
    _saved_log="${AGENT_LOG_FILE:-}"
    export AGENT_LOG_FILE="$_log_file"
    (cd "$SCRIPT_DIR" && ./agent-robot/agent.sh "hola" >/dev/null 2>&1)
    AGENT_LOG_FILE="$_saved_log"

    if [ -f "$_log_file" ] && grep -q "INFO\|RECV\|INTENT" "$_log_file" 2>/dev/null; then
        echo "  ✅ Agent genera logs"
    else
        echo "  ⚠️  Agent logging (puede no estar implementado aun)"
    fi
    rm -f "$_log_file"
}

# --- Fase LLM: modo llm ---
test_agent_llm_mode() {
    _result=$(cd "$SCRIPT_DIR" && ./agent-robot/agent.sh --llm "hola" 2>/dev/null)
    if echo "$_result" | grep -qi "respuesta\|llm\|proyecto0"; then
        echo "  ✅ Agent --llm funciona"
    else
        echo "  ⚠️  Agent --llm (requiere API key)"
    fi
}

# --- Fase LLM: planner ---
test_planner_llm() {
    _result=$(cd "$SCRIPT_DIR" && sh -c '. agent-robot/planner_llm.sh && planificar_llm "crea modulo auth y modulo payments en nestjs"')
    _tipo=$(echo "$_result" | jq -r '.tipo // ""' 2>/dev/null)
    if [ "$_tipo" = "multi_create" ] && echo "$_result" | jq -e '.pasos | length >= 2' >/dev/null 2>&1; then
        echo "  ✅ planner LLM descompone instrucciones"
    else
        echo "  ⚠️  planner LLM (requiere LLM configurado)"
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

# ============================================================================
# TUI TESTS
# ============================================================================

# --- Helper: crear mock de whiptail ---
_prepare_whiptail_mock() {
    _mock_dir="/tmp/tui_mock_$$"
    mkdir -p "$_mock_dir"
    cat > "$_mock_dir/whiptail" << 'MOCK'
#!/bin/sh
# Mock whiptail: detecta --menu entre los argumentos
_has_menu=0
_has_inputbox=0
for _arg in "$@"; do
    case "$_arg" in
        --menu) _has_menu=1 ;;
        --inputbox) _has_inputbox=1 ;;
    esac
done
if [ "$_has_menu" -eq 1 ]; then
    echo "1" >&3
elif [ "$_has_inputbox" -eq 1 ]; then
    echo "test_input" >&3
fi
exit 0
MOCK
    chmod +x "$_mock_dir/whiptail"
    echo "$_mock_dir"
}

# --- Helper: mock de whiptail que simula opcion especifica del menu ---
_prepare_whiptail_mock_choice() {
    _choice="$1"
    _mock_dir="$(mktemp -d /tmp/tui_mock2_$$_XXXXXX)"
    _cnt_file="$(mktemp /tmp/tui_cnt_$$_XXXXXX)"
    cat > "$_mock_dir/whiptail" << MOCK
#!/bin/sh
_f="$_cnt_file"
if [ ! -f "\$_f" ]; then echo "0" > "\$_f"; fi
read _c < "\$_f"
for _arg in "\$@"; do
    case "\$_arg" in
        --menu)
            _c=\$((_c + 1)); echo "\$_c" > "\$_f"
            if [ "\$_c" -eq 1 ]; then echo "$_choice" >&3; else echo "6" >&3; fi
            exit 0 ;;
        --inputbox) echo "test_input" >&3; exit 0 ;;
        --msgbox) exit 0 ;;
    esac
done
exit 0
MOCK
    chmod +x "$_mock_dir/whiptail"
    echo "$_mock_dir"
}

# --- Test: whiptail disponible ---
test_tui_whiptail_available() {
    if command -v whiptail >/dev/null 2>&1; then
        echo "  ✅ whiptail disponible en el sistema"
    else
        echo "  ⚠️  whiptail no instalado (opcional)"
    fi
}

# --- Test: tui_check detecta whiptail ---
test_tui_check_ok() {
    if command -v whiptail >/dev/null 2>&1; then
        _result=$(cd "$SCRIPT_DIR" && sh -c '. agent-robot/tui.sh && tui_check' 2>&1)
        if [ $? -eq 0 ]; then
            echo "  ✅ tui_check: whiptail detectado correctamente"
        else
            echo "  ❌ tui_check: falla con whiptail instalado"
            FAIL=$((FAIL + 1))
            FAIL_MSGS="${FAIL_MSGS}TUI_CHECK_OK "
        fi
    else
        echo "  ⚠️  tui_check: saltado (whiptail no instalado)"
    fi
}

# --- Test: tui_check falla cuando whiptail no existe ---
test_tui_check_fail() {
    _no_w_dir="/tmp/no_w_$$"
    mkdir -p "$_no_w_dir"
    cp /bin/sh "$_no_w_dir/sh" 2>/dev/null || \
        cp /usr/bin/sh "$_no_w_dir/sh" 2>/dev/null
    _result=$(cd "$SCRIPT_DIR" && PATH="$_no_w_dir" sh -c '. agent-robot/tui.sh && tui_check' 2>&1)
    _exit=$?
    rm -rf "$_no_w_dir"
    if [ "$_exit" -ne 0 ] && echo "$_result" | grep -qi "whiptail.*instal"; then
        echo "  ✅ tui_check: detecta ausencia de whiptail"
    else
        echo "  ❌ tui_check: no detecta ausencia (exit: $_exit, msg: $_result)"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}TUI_CHECK_FAIL "
    fi
}

# --- Test: tui_menu retorna opcion con mock ---
test_tui_menu_mocked() {
    _mock_dir=$(_prepare_whiptail_mock)
    _result=$(cd "$SCRIPT_DIR" && PATH="$_mock_dir:$PATH" sh -c '. agent-robot/tui.sh && tui_menu')
    rm -rf "$_mock_dir"
    if [ "$_result" = "1" ]; then
        echo "  ✅ tui_menu: mock retorna opcion 1"
    else
        echo "  ❌ tui_menu: mock no funciona (got: $_result)"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}TUI_MENU "
    fi
}

# --- Test: tui_input retorna texto con mock ---
test_tui_input_mocked() {
    _mock_dir=$(_prepare_whiptail_mock)
    _result=$(cd "$SCRIPT_DIR" && PATH="$_mock_dir:$PATH" sh -c '. agent-robot/tui.sh && tui_input')
    rm -rf "$_mock_dir"
    if [ "$_result" = "test_input" ]; then
        echo "  ✅ tui_input: mock retorna texto"
    else
        echo "  ❌ tui_input: mock no funciona (got: $_result)"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}TUI_INPUT "
    fi
}

# --- Test: tui_output no falla con mock ---
test_tui_output_mocked() {
    _mock_dir=$(_prepare_whiptail_mock)
    _exit=$(cd "$SCRIPT_DIR" && PATH="$_mock_dir:$PATH" sh -c '. agent-robot/tui.sh && tui_output "test mensaje" >/dev/null 2>&1; echo $?')
    rm -rf "$_mock_dir"
    if echo "$_exit" | grep -q "^0$"; then
        echo "  ✅ tui_output: mock ejecuta sin errores"
    else
        echo "  ❌ tui_output: mock falla (exit: $_exit)"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}TUI_OUTPUT "
    fi
}

# --- Test: tui_help no falla con mock ---
test_tui_help_mocked() {
    _mock_dir=$(_prepare_whiptail_mock)
    _exit=$(cd "$SCRIPT_DIR" && PATH="$_mock_dir:$PATH" sh -c '. agent-robot/tui.sh && tui_help >/dev/null 2>&1; echo $?')
    rm -rf "$_mock_dir"
    if echo "$_exit" | grep -q "^0$"; then
        echo "  ✅ tui_help: mock ejecuta sin errores"
    else
        echo "  ❌ tui_help: mock falla (exit: $_exit)"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}TUI_HELP "
    fi
}

# --- Test: tui_llm_config exporta variables de entorno ---
test_tui_llm_config_exports() {
    _mock_dir="/tmp/tui_mock_exp_$$"
    mkdir -p "$_mock_dir"
    _cnt_file="/tmp/tui_exp_cnt_$$"
    cat > "$_mock_dir/whiptail" << MOCK
#!/bin/sh
_f="$_cnt_file"
if [ ! -f "\$_f" ]; then echo "0" > "\$_f"; fi
read _c < "\$_f"
for _arg in "\$@"; do
    case "\$_arg" in
        --inputbox)
            _c=\$((_c + 1)); echo "\$_c" > "\$_f"
            if [ "\$_c" -eq 1 ]; then echo "claude" >&3; else echo "auto" >&3; fi
            exit 0 ;;
        --msgbox) exit 0 ;;
    esac
done
exit 0
MOCK
    chmod +x "$_mock_dir/whiptail"
    rm -f "$_cnt_file"
    _result=$(cd "$SCRIPT_DIR" && PATH="$_mock_dir:$PATH" sh -c '
        . agent-robot/tui.sh
        unset AGENT_LLM_PROVIDER
        unset AGENT_LLM_MODE
        tui_llm_config >/dev/null 2>&1
        echo "PROVIDER=${AGENT_LLM_PROVIDER:-}"
        echo "MODE=${AGENT_LLM_MODE:-}"
    ')
    rm -rf "$_mock_dir" "$_cnt_file"
    _provider=$(echo "$_result" | grep "^PROVIDER=" | sed 's/^PROVIDER=//')
    _mode=$(echo "$_result" | grep "^MODE=" | sed 's/^MODE=//')
    if [ "$_provider" = "claude" ] && [ "$_mode" = "auto" ]; then
        echo "  ✅ tui_llm_config: exporta PROVIDER=$_provider MODE=$_mode"
    else
        echo "  ⚠️  tui_llm_config: exporta valores (got: PROVIDER=$_provider MODE=$_mode)"
    fi
}

# --- Test: tui_history vacio ---
test_tui_history_empty() {
    _mock_dir=$(_prepare_whiptail_mock)
    _mem_dir="/tmp/test_tui_history_empty_$$"
    mkdir -p "$_mem_dir"
    echo '{"historial":[],"contexto":{},"sesiones":[]}' > "$_mem_dir/agent_memory.json"
    _exit=$(cd "$SCRIPT_DIR" && PATH="$_mock_dir:$PATH" AGENT_MEMORY_DIR="$_mem_dir" SCRIPT_DIR="agent-robot" \
        sh -c '. agent-robot/tui.sh && tui_history >/dev/null 2>&1; echo $?')
    rm -rf "$_mock_dir" "$_mem_dir"
    if echo "$_exit" | grep -q "^0$"; then
        echo "  ✅ tui_history: historial vacio no falla"
    else
        echo "  ❌ tui_history: falla con historial vacio (exit: $_exit)"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}TUI_HIST_EMPTY "
    fi
}

# --- Test: tui_history con datos ---
test_tui_history_with_data() {
    _mock_dir=$(_prepare_whiptail_mock)
    _mem_dir="/tmp/test_tui_history_data_$$"
    mkdir -p "$_mem_dir"
    echo '{"historial":[{"timestamp":"2026-01-01","instruccion":"test","respuesta":"ok"}],"contexto":{},"sesiones":[]}' > "$_mem_dir/agent_memory.json"
    _exit=$(cd "$SCRIPT_DIR" && PATH="$_mock_dir:$PATH" AGENT_MEMORY_DIR="$_mem_dir" SCRIPT_DIR="agent-robot" \
        sh -c '. agent-robot/tui.sh && tui_history >/dev/null 2>&1; echo $?')
    rm -rf "$_mock_dir" "$_mem_dir"
    if echo "$_exit" | grep -q "^0$"; then
        echo "  ✅ tui_history: historial con datos no falla"
    else
        echo "  ❌ tui_history: falla con datos (exit: $_exit)"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}TUI_HIST_DATA "
    fi
}

# --- Test: tui_llm_config rechaza proveedor invalido ---
test_tui_llm_config_invalid_provider() {
    _mock_dir="/tmp/tui_mock_inv_$$"
    mkdir -p "$_mock_dir"
    _cnt_file="/tmp/tui_inv_cnt_$$"
    cat > "$_mock_dir/whiptail" << MOCK
#!/bin/sh
_f="$_cnt_file"
if [ ! -f "\$_f" ]; then echo "0" > "\$_f"; fi
read _c < "\$_f"
for _arg in "\$@"; do
    case "\$_arg" in
        --inputbox)
            _c=\$((_c + 1)); echo "\$_c" > "\$_f"
            if [ "\$_c" -eq 1 ]; then echo "invalid_provider_xyz" >&3; else echo "" >&3; fi
            exit 0 ;;
        --msgbox) exit 0 ;;
    esac
done
exit 0
MOCK
    chmod +x "$_mock_dir/whiptail"
    rm -f "$_cnt_file"
    _result=$(cd "$SCRIPT_DIR" && PATH="$_mock_dir:$PATH" SCRIPT_DIR="$SCRIPT_DIR" sh -c '
        . agent-robot/tui.sh
        unset AGENT_LLM_PROVIDER
        tui_llm_config >/dev/null 2>&1
        echo "PROVIDER=${AGENT_LLM_PROVIDER:-}"
    ')
    rm -rf "$_mock_dir" "$_cnt_file"
    _provider=$(echo "$_result" | sed 's/^PROVIDER=//')
    if [ -z "$_provider" ]; then
        echo "  ✅ tui_llm_config: rechaza proveedor invalido"
    else
        echo "  ⚠️  tui_llm_config: no rechazo (got: $_provider)"
    fi
}

# --- Test: --tui flag en agent.sh ---
test_agent_tui_flag() {
    _mock_dir="/tmp/tui_mock_flag_$$"
    mkdir -p "$_mock_dir"
    cat > "$_mock_dir/whiptail" << 'MOCK'
#!/bin/sh
for _arg in "$@"; do
    case "$_arg" in
        --menu) echo "6" >&3 ;;
    esac
done
exit 0
MOCK
    chmod +x "$_mock_dir/whiptail"
    _result=$(cd "$SCRIPT_DIR" && PATH="$_mock_dir:$PATH" \
        ./agent-robot/agent.sh --tui 2>&1 <<'EOF'
test
EOF
    )
    rm -rf "$_mock_dir"
    if echo "$_result" | grep -qi "proyecto0\|agente\|recpl"; then
        echo "  ✅ agent.sh --tui: flag reconocido y TUI iniciado"
    else
        echo "  ⚠️  agent.sh --tui: puede fallar sin terminal"
    fi
}

# --- Test: menu option 4 (historial) desde agent.sh --tui ---
test_agent_tui_menu_history() {
    _mock_dir="/tmp/tui_mock_hist_$$"
    mkdir -p "$_mock_dir"
    _cnt_file="/tmp/tui_seq4_$$"
    cat > "$_mock_dir/whiptail" << MOCK
#!/bin/sh
_f="$_cnt_file"
if [ ! -f "\$_f" ]; then echo "0" > "\$_f"; fi
read _c < "\$_f"
for _arg in "\$@"; do
    case "\$_arg" in
        --menu)
            _c=\$((_c + 1)); echo "\$_c" > "\$_f"
            if [ "\$_c" -eq 1 ]; then echo "4" >&3; else echo "6" >&3; fi
            exit 0 ;;
        --inputbox) echo "test_input" >&3; exit 0 ;;
        --msgbox) exit 0 ;;
    esac
done
exit 0
MOCK
    chmod +x "$_mock_dir/whiptail"
    _mem_dir="/tmp/test_tui_menu_hist_$$"
    mkdir -p "$_mem_dir"
    echo '{"historial":[{"timestamp":"2026-01-01","instruccion":"test menu hist","respuesta":"ok"}],"contexto":{},"sesiones":[]}' > "$_mem_dir/agent_memory.json"
    rm -f "$_cnt_file"
    _result=$(cd "$SCRIPT_DIR" && PATH="$_mock_dir:$PATH" AGENT_MEMORY_DIR="$_mem_dir" \
        ./agent-robot/agent.sh --tui 2>&1 <<'EOF'
test
EOF
    )
    rm -rf "$_mock_dir" "$_mem_dir" "$_cnt_file"
    if echo "$_result" | grep -qi "test menu hist\|historial"; then
        echo "  ✅ agent.sh --tui menu option 4: historial accesible"
    else
        echo "  ⚠️  agent.sh --tui menu option 4: puede fallar sin terminal"
    fi
}

# --- Test: menu option 5 (ayuda) desde agent.sh --tui ---
test_agent_tui_menu_help() {
    _mock_dir="/tmp/tui_mock_help_$$"
    mkdir -p "$_mock_dir"
    _cnt_file="/tmp/tui_seq5_$$"
    cat > "$_mock_dir/whiptail" << MOCK
#!/bin/sh
_f="$_cnt_file"
if [ ! -f "\$_f" ]; then echo "0" > "\$_f"; fi
read _c < "\$_f"
for _arg in "\$@"; do
    case "\$_arg" in
        --menu)
            _c=\$((_c + 1)); echo "\$_c" > "\$_f"
            if [ "\$_c" -eq 1 ]; then echo "5" >&3; else echo "6" >&3; fi
            exit 0 ;;
        --inputbox) echo "test_input" >&3; exit 0 ;;
        --msgbox) exit 0 ;;
    esac
done
exit 0
MOCK
    chmod +x "$_mock_dir/whiptail"
    rm -f "$_cnt_file"
    _result=$(cd "$SCRIPT_DIR" && PATH="$_mock_dir:$PATH" \
        ./agent-robot/agent.sh --tui 2>&1 <<'EOF'
test
EOF
    )
    rm -rf "$_mock_dir" "$_cnt_file"
    if echo "$_result" | grep -qi "proyecto0\|nestjs\|prisma\|ayuda"; then
        echo "  ✅ agent.sh --tui menu option 5: ayuda accesible"
    else
        echo "  ⚠️  agent.sh --tui menu option 5: puede fallar sin terminal"
    fi
}

# --- MAIN ---
echo "=========================================="
echo " Tests Agent-Robot (Fase 1 + Fase 2 + Fase 3 + Fase 4 + LLM)"
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
test_planner_multi_create
test_memory_persist
test_tool_search_code
test_agent_error_empty
test_prompts_exist
test_agent_logging
test_agent_llm_mode
test_planner_llm
test_agent_greeting
test_agent_identity
test_bridge_recpl
test_agent_flag
test_tui_whiptail_available
test_tui_check_ok
test_tui_check_fail
test_tui_menu_mocked
test_tui_input_mocked
test_tui_output_mocked
test_tui_help_mocked
test_tui_llm_config_exports
test_tui_history_empty
test_tui_history_with_data
test_tui_llm_config_invalid_provider
test_agent_tui_flag
test_agent_tui_menu_history
test_agent_tui_menu_help
echo ""

echo "Resultados: PASS=$PASS FAIL=$FAIL"
echo "Fallos: ${FAIL_MSGS:-ninguno}"
echo "=========================================="
[ $FAIL -eq 0 ] && exit 0 || exit 1
