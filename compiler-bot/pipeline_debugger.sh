#!/bin/sh
# ============================================================================
# pipeline_debugger.sh - Debugger instrumentado del pipeline RECPL
# ============================================================================
#
# PROPOSITO:
#   Ejecuta el pipeline compilador etapa por etapa con instrumentacion:
#   tiempos, inspeccion JSON, captura de stderr, modo paso a paso.
#   No modifica ninguna etapa del pipeline — solo captura I/O.
#
# USO:
#   ./pipeline_debugger.sh [opciones] "instruccion"
#
# MODOS:
#   -t, --trace        Modo trace completo (default)
#   -s, --step         Modo paso a paso con pausa interactiva
#   -m, --timing       Modo solo metricas (tabla compacta)
#   -i, --inspect ETAPA  Mostrar solo el JSON de salida de ETAPA
#   -x, --xtrace       Modo bash -x profundo con PS4 contextual
#   -o, --output       Solo el JSON final a stdout (para piping)
#   -h, --help         Mostrar ayuda
#
# EJEMPLOS:
#   ./pipeline_debugger.sh "crea modulo pagos en nestjs"
#   ./pipeline_debugger.sh --step "crea modulo pagos en nestjs"
#   ./pipeline_debugger.sh --timing "crea modulo pagos en nestjs"
#   ./pipeline_debugger.sh --inspect parser "crea modulo pagos en nestjs"
#   ./pipeline_debugger.sh --xtrace "crea modulo pagos en nestjs"
# ============================================================================

# --- Constants ---
SCRIPT_NAME="pipeline_debugger.sh"
VERSION="1.0.0"
SCRIPT_DIR="$(dirname "$0")"

# Nombres de etapa (para mostrar)
STAGE_NAMES="preprocessor lexer parser semantic ir_generator synthesis"
STAGE_LABELS="preprocessor.sh lexer.sh parser.sh semantic.sh ir_generator.sh synthesis.sh"
TOTAL_STAGES=6

# Directorio temporal para esta ejecucion
DEBUG_STAGE_DIR="/tmp/recpl_debug_stages_$$"
DEBUG_STATE_DIR="/tmp/recpl_debug_state_$$"

# --- Detectar herramientas disponibles ---
HAS_DATE_NANO=false
HAS_BC=false
HAS_PYTHON=false
HAS_AWK=false
HAS_JQ=false
HAS_JQ_VALID=false

detect_tools() {
    date +%s.%N >/dev/null 2>&1 && HAS_DATE_NANO=true
    command -v bc >/dev/null 2>&1 && HAS_BC=true
    command -v python3 >/dev/null 2>&1 && HAS_PYTHON=true
    command -v awk >/dev/null 2>&1 && HAS_AWK=true
    if command -v jq >/dev/null 2>&1; then
        HAS_JQ=true
        echo '{}' | jq -e . >/dev/null 2>&1 && HAS_JQ_VALID=true
    fi
}

# --- Timing ---
get_time_nano() {
    if $HAS_DATE_NANO; then
        date +%s.%N
    else
        date +%s
    fi
}

float_sub() {
    _a="$1"
    _b="$2"
    if $HAS_PYTHON; then
        python3 -c "print(${_a} - ${_b})" 2>/dev/null
    elif $HAS_AWK; then
        awk "BEGIN { printf \"%.6f\", ${_a} - ${_b} }" 2>/dev/null
    elif $HAS_BC; then
        echo "${_a} - ${_b}" | bc 2>/dev/null
    else
        echo "0"
    fi
}

# --- Limpieza ---
clean_debug() {
    rm -rf "$DEBUG_STAGE_DIR" "$DEBUG_STATE_DIR"
}

# --- Error ---
die() {
    echo "Error: $*" >&2
    clean_debug
    exit 1
}

# --- Ayuda ---
show_help() {
    cat <<HELP
pipeline_debugger.sh v${VERSION}

Debugger instrumentado del pipeline RECPL. Ejecuta cada etapa del
compilador con metricas de tiempo, inspeccion JSON y captura de errores.

USO:
  ./pipeline_debugger.sh [opciones] "instruccion"

MODOS:
  -t, --trace           Modo trace completo (default)
  -s, --step            Modo paso a paso con pausa interactiva
  -m, --timing          Modo solo metricas (tabla compacta)
  -i, --inspect ETAPA   Mostrar solo el JSON de salida de ETAPA
                        ETAPA: preprocessor, lexer, parser, semantic, ir_generator, synthesis
  -x, --xtrace          Modo bash -x profundo con PS4 contextual
  -o, --output          Solo el JSON final a stdout (para piping)
  -h, --help            Mostrar ayuda

VARIABLES DE ENTORNO:
  RECPL_STATE_DIR  Directorio de estado (default: /tmp/recpl_debug_state_PID)
  RECPL_LLM_MODE   auto|llm|deterministic (default: auto)

HERRAMIENTAS REQUERIDAS:
  date +%s.%N    Para medicion de tiempo (modo timing)
  awk o python3  Para aritmetica decimal de tiempos
  jq             Para validacion e inspeccion de JSON
HELP
}

# ============================================================================
# SECTION: Instrumentacion de etapa
# ============================================================================

# --- Ejecutar una etapa con instrumentacion ---
# run_stage "nombre" "script" "tipo_input" "input" "stage_num"
#   tipo_input: "arg" → el script recibe el input como argumento
#               "stdin" → el script recibe el input por stdin
run_stage() {
    _stage_name="$1"
    _stage_script="$2"
    _input_type="$3"
    _input="$4"
    _stage_num="$5"

    _stdout_file="$DEBUG_STAGE_DIR/${_stage_name}.stdout"
    _stderr_file="$DEBUG_STAGE_DIR/${_stage_name}.stderr"

    _start=$(get_time_nano)

    case "$_input_type" in
        arg)
            FRONTEND_DIR="$SCRIPT_DIR/frontend" \
                "$_stage_script" "$_input" \
                > "$_stdout_file" 2> "$_stderr_file"
            ;;
        stdin)
            echo "$_input" | \
                "$_stage_script" \
                > "$_stdout_file" 2> "$_stderr_file"
            ;;
    esac
    _exit_code=$?

    _end=$(get_time_nano)
    _elapsed=$(float_sub "$_end" "$_start")

    # Determinar status
    if [ "$_exit_code" -ne 0 ]; then
        _status="FAIL"
    elif [ ! -s "$_stdout_file" ]; then
        _status="EMPTY"
    else
        _status="OK"
    fi

    # Tamanio del stdout
    _stdout_size=$(wc -c < "$_stdout_file" 2>/dev/null | tr -d ' ')
    [ -z "$_stdout_size" ] && _stdout_size=0

    # Leer stderr
    _stderr_content=$(cat "$_stderr_file" 2>/dev/null)
    _stderr_note="(none)"
    [ -n "$_stderr_content" ] && _stderr_note="see below"

    # Guardar resultados en variables globales (para que el llamante las lea)
    _STAGE_EXIT_CODE=$_exit_code
    _STAGE_ELAPSED=$_elapsed
    _STAGE_STATUS=$_status
    _STAGE_STDOUT_SIZE=$_stdout_size
    _STAGE_STDERR_CONTENT="$_stderr_content"
    _STAGE_STDOUT_FILE="$_stdout_file"
}

# --- Mostrar resultado de etapa en modo trace ---
print_stage_trace() {
    _num="$1"
    _total="$2"
    _name="$3"
    _status="$4"
    _elapsed="$5"
    _size="$6"
    _stderr="$7"

    printf "  [%s/%s] %s\n" "$_num" "$_total" "$_name"
    printf "    status: %s\n" "$_status"
    printf "    time:   %ss\n" "$_elapsed"
    printf "    stdout: %s bytes\n" "$_size"
    if [ -n "$_stderr" ]; then
        printf "    stderr: %s\n" "$_stderr"
    else
        printf "    stderr: (none)\n"
    fi
    echo
}

# --- Mostrar resultado de etapa en modo timing (una linea) ---
print_stage_timing() {
    _name="$1"
    _status="$2"
    _elapsed="$3"
    _size="$4"

    printf "  %-20s %8ss  %8s bytes  %s\n" "$_name" "$_elapsed" "$_size" "$_status"
}

# ============================================================================
# SECTION: Pipeline deterministico instrumentado
# ============================================================================

# --- Ejecutar pipeline deterministico completo con instrumentacion ---
run_deterministic_debug() {
    _instruction="$1"
    _mode="$2"
    _state_dir="${RECPL_STATE_DIR:-$DEBUG_STATE_DIR}"

    mkdir -p "$_state_dir"

    _preprocessed=""
    _tokens=""
    _ast=""
    _validated=""
    _ir=""
    _final_output=""

    _all_ok=true
    _total_time="0"

    # ---- Stage 1: preprocessor (arg) ----
    run_stage "preprocessor" "$SCRIPT_DIR/frontend/preprocessor.sh" \
        "arg" "$_instruction" "1"
    _preprocessed=$(cat "$_STAGE_STDOUT_FILE" 2>/dev/null)
    [ -z "$_preprocessed" ] && _preprocessed="$_instruction"
    _total_time=$(float_sub "$_total_time + $_STAGE_ELAPSED" "0" 2>/dev/null || echo "$_STAGE_ELAPSED")
    if [ "$_STAGE_STATUS" != "OK" ]; then _all_ok=false; fi

    case "$_mode" in
        trace)   print_stage_trace "1" "$TOTAL_STAGES" "preprocessor.sh" "$_STAGE_STATUS" "$_STAGE_ELAPSED" "$_STAGE_STDOUT_SIZE" "$_STAGE_STDERR_CONTENT" ;;
        timing)  print_stage_timing "preprocessor.sh" "$_STAGE_STATUS" "$_STAGE_ELAPSED" "$_STAGE_STDOUT_SIZE" ;;
    esac

    if [ "$_mode" = "step" ]; then
        print_stage_trace "1" "$TOTAL_STAGES" "preprocessor.sh" "$_STAGE_STATUS" "$_STAGE_ELAPSED" "$_STAGE_STDOUT_SIZE" "$_STAGE_STDERR_CONTENT"
        step_prompt "preprocessor.sh"
    fi

    # ---- Stage 2: lexer (arg) ----
    run_stage "lexer" "$SCRIPT_DIR/frontend/lexer.sh" \
        "arg" "$_preprocessed" "2"
    _tokens=$(cat "$_STAGE_STDOUT_FILE" 2>/dev/null)
    _total_time=$(float_sub "$_total_time + $_STAGE_ELAPSED" "0")
    if [ "$_STAGE_STATUS" != "OK" ]; then _all_ok=false; fi

    case "$_mode" in
        trace)   print_stage_trace "2" "$TOTAL_STAGES" "lexer.sh" "$_STAGE_STATUS" "$_STAGE_ELAPSED" "$_STAGE_STDOUT_SIZE" "$_STAGE_STDERR_CONTENT" ;;
        timing)  print_stage_timing "lexer.sh" "$_STAGE_STATUS" "$_STAGE_ELAPSED" "$_STAGE_STDOUT_SIZE" ;;
    esac

    if [ "$_mode" = "step" ]; then
        print_stage_trace "2" "$TOTAL_STAGES" "lexer.sh" "$_STAGE_STATUS" "$_STAGE_ELAPSED" "$_STAGE_STDOUT_SIZE" "$_STAGE_STDERR_CONTENT"
        step_prompt "lexer.sh"
    fi

    # ---- Stage 3: parser (stdin) ----
    run_stage "parser" "$SCRIPT_DIR/frontend/parser.sh" \
        "stdin" "$_tokens" "3"
    _ast=$(cat "$_STAGE_STDOUT_FILE" 2>/dev/null)
    _total_time=$(float_sub "$_total_time + $_STAGE_ELAPSED" "0")
    if [ "$_STAGE_STATUS" != "OK" ]; then _all_ok=false; fi

    case "$_mode" in
        trace)   print_stage_trace "3" "$TOTAL_STAGES" "parser.sh" "$_STAGE_STATUS" "$_STAGE_ELAPSED" "$_STAGE_STDOUT_SIZE" "$_STAGE_STDERR_CONTENT" ;;
        timing)  print_stage_timing "parser.sh" "$_STAGE_STATUS" "$_STAGE_ELAPSED" "$_STAGE_STDOUT_SIZE" ;;
    esac

    if [ "$_mode" = "step" ]; then
        print_stage_trace "3" "$TOTAL_STAGES" "parser.sh" "$_STAGE_STATUS" "$_STAGE_ELAPSED" "$_STAGE_STDOUT_SIZE" "$_STAGE_STDERR_CONTENT"
        step_prompt "parser.sh"
    fi

    # ---- Stage 4: semantic (stdin, necesita RECPL_STATE_DIR) ----
    run_stage "semantic" "$SCRIPT_DIR/frontend/semantic.sh" \
        "stdin" "$_ast" "4"
    _validated=$(cat "$_STAGE_STDOUT_FILE" 2>/dev/null)
    _total_time=$(float_sub "$_total_time + $_STAGE_ELAPSED" "0")
    if [ "$_STAGE_STATUS" != "OK" ]; then _all_ok=false; fi

    case "$_mode" in
        trace)   print_stage_trace "4" "$TOTAL_STAGES" "semantic.sh" "$_STAGE_STATUS" "$_STAGE_ELAPSED" "$_STAGE_STDOUT_SIZE" "$_STAGE_STDERR_CONTENT" ;;
        timing)  print_stage_timing "semantic.sh" "$_STAGE_STATUS" "$_STAGE_ELAPSED" "$_STAGE_STDOUT_SIZE" ;;
    esac

    if [ "$_mode" = "step" ]; then
        print_stage_trace "4" "$TOTAL_STAGES" "semantic.sh" "$_STAGE_STATUS" "$_STAGE_ELAPSED" "$_STAGE_STDOUT_SIZE" "$_STAGE_STDERR_CONTENT"
        step_prompt "semantic.sh"
    fi

    # ---- Stage 5: IR generator (stdin) ----
    run_stage "ir_generator" "$SCRIPT_DIR/middleend/ir_generator.sh" \
        "stdin" "$_validated" "5"
    _ir=$(cat "$_STAGE_STDOUT_FILE" 2>/dev/null)
    _total_time=$(float_sub "$_total_time + $_STAGE_ELAPSED" "0")
    if [ "$_STAGE_STATUS" != "OK" ]; then _all_ok=false; fi

    case "$_mode" in
        trace)   print_stage_trace "5" "$TOTAL_STAGES" "ir_generator.sh" "$_STAGE_STATUS" "$_STAGE_ELAPSED" "$_STAGE_STDOUT_SIZE" "$_STAGE_STDERR_CONTENT" ;;
        timing)  print_stage_timing "ir_generator.sh" "$_STAGE_STATUS" "$_STAGE_ELAPSED" "$_STAGE_STDOUT_SIZE" ;;
    esac

    if [ "$_mode" = "step" ]; then
        print_stage_trace "5" "$TOTAL_STAGES" "ir_generator.sh" "$_STAGE_STATUS" "$_STAGE_ELAPSED" "$_STAGE_STDOUT_SIZE" "$_STAGE_STDERR_CONTENT"
        step_prompt "ir_generator.sh"
    fi

    # ---- Stage 6: synthesis (stdin) ----
    run_stage "synthesis" "$SCRIPT_DIR/backend/synthesis.sh" \
        "stdin" "$_ir" "6"
    _final_output=$(cat "$_STAGE_STDOUT_FILE" 2>/dev/null)
    _total_time=$(float_sub "$_total_time + $_STAGE_ELAPSED" "0")
    if [ "$_STAGE_STATUS" != "OK" ]; then _all_ok=false; fi

    case "$_mode" in
        trace)   print_stage_trace "6" "$TOTAL_STAGES" "synthesis.sh" "$_STAGE_STATUS" "$_STAGE_ELAPSED" "$_STAGE_STDOUT_SIZE" "$_STAGE_STDERR_CONTENT" ;;
        timing)  print_stage_timing "synthesis.sh" "$_STAGE_STATUS" "$_STAGE_ELAPSED" "$_STAGE_STDOUT_SIZE" ;;
    esac

    if [ "$_mode" = "step" ]; then
        print_stage_trace "6" "$TOTAL_STAGES" "synthesis.sh" "$_STAGE_STATUS" "$_STAGE_ELAPSED" "$_STAGE_STDOUT_SIZE" "$_STAGE_STDERR_CONTENT"
        step_prompt "synthesis.sh"
    fi

    # --- Resumen ---
    _stage_ok_count=0
    for _sfx in $STAGE_NAMES; do
        _sf="$DEBUG_STAGE_DIR/${_sfx}.stdout"
        [ -s "$_sf" ] && _stage_ok_count=$((_stage_ok_count + 1))
    done

    echo
    echo "  --- Resumen ---"
    echo "  Total:  ${_total_time}s"
    echo "  Etapas: ${_stage_ok_count}/${TOTAL_STAGES} OK"
    if $_all_ok; then
        echo "  Estado: TODAS OK"
    else
        echo "  Estado: HUBO FALLOS"
    fi

    # Estado del directorio de simbolos
    _sym_count=0
    if [ -d "$_state_dir" ]; then
        _sym_count=$(find "$_state_dir" -type f 2>/dev/null | wc -l | tr -d ' ')
        echo "  State:  ${_state_dir} (${_sym_count} archivos)"
        for _sym_file in "$_state_dir"/*; do
            [ -f "$_sym_file" ] && echo "    $(basename "$_sym_file"): $(head -c 80 "$_symFile" 2>/dev/null)"
        done
    fi

    echo

    # Devolver JSON final a stdout
    if [ -n "$_final_output" ]; then
        echo "$_final_output"
    fi
}

# ============================================================================
# SECTION: Modos del debugger
# ============================================================================

# --- Modo trace ---
debug_trace() {
    _instruction="$1"
    _state_dir="${RECPL_STATE_DIR:-$DEBUG_STATE_DIR}"

    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│ PIPELINE DEBUGGER — trace mode                          │"
    echo "│ Input: \"${_instruction}\"                                │"
    echo "├─────────────────────────────────────────────────────────┤"
    echo

    run_deterministic_debug "$_instruction" "trace"
}

# --- Modo step ---
step_prompt() {
    _stage="$1"
    while true; do
        printf "  [step] Presiona Enter para continuar (o 'q' para salir, 'help' para comandos)... "
        if ! read -r _cmd; then
            echo
            return
        fi
        case "$_cmd" in
            "")
                return
                ;;
            q|Q)
                echo "  [step] Debugger abortado por el usuario."
                clean_debug
                exit 0
                ;;
            stdout)
                echo "  [step] STDOUT de ${_stage}:"
                _sf="$DEBUG_STAGE_DIR/${_stage}.stdout"
                if [ -f "$_sf" ]; then
                    cat "$_sf" 2>/dev/null | while IFS= read -r _line; do
                        echo "    | $_line"
                    done
                else
                    echo "    (no disponible)"
                fi
                ;;
            stderr)
                echo "  [step] STDERR de ${_stage}:"
                _sf="$DEBUG_STAGE_DIR/${_stage}.stderr"
                if [ -f "$_sf" ] && [ -s "$_sf" ]; then
                    cat "$_sf" 2>/dev/null | while IFS= read -r _line; do
                        echo "    ! $_line"
                    done
                else
                    echo "    (none)"
                fi
                ;;
            json)
                _sf="$DEBUG_STAGE_DIR/${_stage}.stdout"
                if [ -f "$_sf" ] && [ -s "$_sf" ]; then
                    if $HAS_JQ_VALID; then
                        jq -e . "$_sf" >/dev/null 2>&1 && \
                            jq -C . "$_sf" 2>/dev/null || \
                            echo "    (JSON invalido)"
                    else
                        cat "$_sf" 2>/dev/null | while IFS= read -r _line; do
                            echo "    | $_line"
                        done
                    fi
                else
                    echo "    (no disponible)"
                fi
                ;;
            state)
                _sd="${RECPL_STATE_DIR:-$DEBUG_STATE_DIR}"
                if [ -d "$_sd" ]; then
                    echo "  [step] State dir: $_sd"
                    ls -la "$_sd" 2>/dev/null | while IFS= read -r _line; do
                        echo "    $_line"
                    done
                else
                    echo "    (vacio)"
                fi
                ;;
            help)
                echo "  Comandos disponibles:"
                echo "    Enter   Continuar a la siguiente etapa"
                echo "    q       Salir del debugger"
                echo "    stdout  Mostrar stdout completo de la ultima etapa"
                echo "    stderr  Mostrar stderr completo de la ultima etapa"
                echo "    json    Validar y mostrar JSON formateado"
                echo "    state   Mostrar contenido de RECPL_STATE_DIR"
                echo "    help    Mostrar esta ayuda"
                ;;
            *)
                echo "  Comando no reconocido: $_cmd (escribe 'help' para ayuda)"
                ;;
        esac
    done
}

debug_step() {
    _instruction="$1"

    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│ PIPELINE DEBUGGER — step mode                           │"
    echo "│ Input: \"${_instruction}\"                                │"
    echo "├─────────────────────────────────────────────────────────┤"
    echo "│ Paso a paso: presiona Enter entre cada etapa           │"
    echo "│ Comandos: stdout, stderr, json, state, q, help         │"
    echo "└─────────────────────────────────────────────────────────┘"
    echo

    run_deterministic_debug "$_instruction" "step"
}

# --- Modo timing ---
debug_timing() {
    _instruction="$1"

    if ! $HAS_DATE_NANO; then
        echo "Error: modo timing requiere date +%s.%N (no disponible)" >&2
        echo "Usa --trace como alternativa." >&2
        return 1
    fi

    echo "  Etapa                  Tiempo       Tamanio      Status"
    echo "  ─────────────────────────────────────────────────────────"

    run_deterministic_debug "$_instruction" "timing"
}

# --- Modo inspect ---
debug_inspect() {
    _stage_name="$1"
    _instruction="$2"
    _state_dir="${RECPL_STATE_DIR:-$DEBUG_STATE_DIR}"
    mkdir -p "$_state_dir"

    # Mapa de nombres de etapa a script y tipo de input
    case "$_stage_name" in
        preprocessor)
            _script="$SCRIPT_DIR/frontend/preprocessor.sh"
            _type="arg"
            ;;
        lexer)
            _script="$SCRIPT_DIR/frontend/lexer.sh"
            _type="arg"
            ;;
        parser)
            _script="$SCRIPT_DIR/frontend/parser.sh"
            _type="stdin"
            ;;
        semantic)
            _script="$SCRIPT_DIR/frontend/semantic.sh"
            _type="stdin"
            ;;
        ir_generator)
            _script="$SCRIPT_DIR/middleend/ir_generator.sh"
            _type="stdin"
            ;;
        synthesis)
            _script="$SCRIPT_DIR/backend/synthesis.sh"
            _type="stdin"
            ;;
        *)
            echo "Error: etapa desconocida '$_stage_name'" >&2
            echo "Etapas disponibles: preprocessor, lexer, parser, semantic, ir_generator, synthesis" >&2
            return 1
            ;;
    esac

    # Construir input para la etapa solicitada
    _input="$_instruction"
    if [ "$_stage_name" != "preprocessor" ] && [ "$_stage_name" != "lexer" ]; then
        # Necesita las etapas anteriores
        _preprocessed=$(FRONTEND_DIR="$SCRIPT_DIR/frontend" \
            "$SCRIPT_DIR/frontend/preprocessor.sh" "$_instruction" 2>/dev/null)
        [ -z "$_preprocessed" ] && _preprocessed="$_instruction"

        if [ "$_stage_name" = "parser" ]; then
            _input=$(FRONTEND_DIR="$SCRIPT_DIR/frontend" \
                "$SCRIPT_DIR/frontend/lexer.sh" "$_preprocessed" 2>/dev/null)
        elif [ "$_stage_name" = "semantic" ]; then
            _tokens=$(FRONTEND_DIR="$SCRIPT_DIR/frontend" \
                "$SCRIPT_DIR/frontend/lexer.sh" "$_preprocessed" 2>/dev/null)
            _input=$(echo "$_tokens" | "$SCRIPT_DIR/frontend/parser.sh" 2>/dev/null)
        elif [ "$_stage_name" = "ir_generator" ]; then
            _tokens=$(FRONTEND_DIR="$SCRIPT_DIR/frontend" \
                "$SCRIPT_DIR/frontend/lexer.sh" "$_preprocessed" 2>/dev/null)
            _ast=$(echo "$_tokens" | "$SCRIPT_DIR/frontend/parser.sh" 2>/dev/null)
            _input=$(echo "$_ast" | RECPL_STATE_DIR="$_state_dir" \
                "$SCRIPT_DIR/frontend/semantic.sh" 2>/dev/null)
        elif [ "$_stage_name" = "synthesis" ]; then
            _tokens=$(FRONTEND_DIR="$SCRIPT_DIR/frontend" \
                "$SCRIPT_DIR/frontend/lexer.sh" "$_preprocessed" 2>/dev/null)
            _ast=$(echo "$_tokens" | "$SCRIPT_DIR/frontend/parser.sh" 2>/dev/null)
            _validated=$(echo "$_ast" | RECPL_STATE_DIR="$_state_dir" \
                "$SCRIPT_DIR/frontend/semantic.sh" 2>/dev/null)
            _input=$(echo "$_validated" | \
                "$SCRIPT_DIR/middleend/ir_generator.sh" 2>/dev/null)
        fi
    fi

    # Ejecutar la etapa y mostrar su stdout
    case "$_type" in
        arg)
            FRONTEND_DIR="$SCRIPT_DIR/frontend" \
                "$_script" "$_input" 2>/dev/null
            ;;
        stdin)
            echo "$_input" | "$_script" 2>/dev/null
            ;;
    esac
}

# --- Modo xtrace ---
debug_xtrace() {
    _instruction="$1"
    _state_dir="${RECPL_STATE_DIR:-$DEBUG_STATE_DIR}"
    mkdir -p "$_state_dir"

    export PS4='+[${BASH_SOURCE##*/}:${LINENO}:${FUNCNAME[0]:-MAIN}] '
    export RECPL_STATE_DIR="$_state_dir"
    export FRONTEND_DIR="$SCRIPT_DIR/frontend"

    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│ PIPELINE DEBUGGER — xtrace mode                         │"
    echo "│ Input: \"${_instruction}\"                                │"
    echo "│ Cada etapa se ejecuta con bash -x (PS4 con contexto)    │"
    echo "├─────────────────────────────────────────────────────────┤"
    echo

    _pp_out="$DEBUG_STAGE_DIR/xtrace_preprocessor.out"
    FRONTEND_DIR="$SCRIPT_DIR/frontend" bash -x \
        "$SCRIPT_DIR/frontend/preprocessor.sh" "$_instruction" \
        > "$_pp_out" 2>&1
    cat "$_pp_out"
    echo

    _pp_output=$(grep -v '^+' "$_pp_out" 2>/dev/null | head -1)
    [ -z "$_pp_output" ] && _pp_output="$_instruction"

    _lex_out="$DEBUG_STAGE_DIR/xtrace_lexer.out"
    FRONTEND_DIR="$SCRIPT_DIR/frontend" bash -x \
        "$SCRIPT_DIR/frontend/lexer.sh" "$_pp_output" \
        > "$_lex_out" 2>&1
    cat "$_lex_out"
    echo

    _lex_output=$(grep -v '^+' "$_lex_out" 2>/dev/null)

    _par_out="$DEBUG_STAGE_DIR/xtrace_parser.out"
    echo "$_lex_output" | bash -x \
        "$SCRIPT_DIR/frontend/parser.sh" \
        > "$_par_out" 2>&1
    cat "$_par_out"
    echo

    _par_output=$(grep -v '^+' "$_par_out" 2>/dev/null)

    _sem_out="$DEBUG_STAGE_DIR/xtrace_semantic.out"
    echo "$_par_output" | RECPL_STATE_DIR="$_state_dir" bash -x \
        "$SCRIPT_DIR/frontend/semantic.sh" \
        > "$_sem_out" 2>&1
    cat "$_sem_out"
    echo

    _sem_output=$(grep -v '^+' "$_sem_out" 2>/dev/null)

    _ir_out="$DEBUG_STAGE_DIR/xtrace_ir.out"
    echo "$_sem_output" | bash -x \
        "$SCRIPT_DIR/middleend/ir_generator.sh" \
        > "$_ir_out" 2>&1
    cat "$_ir_out"
    echo

    _ir_output=$(grep -v '^+' "$_ir_out" 2>/dev/null)

    _syn_out="$DEBUG_STAGE_DIR/xtrace_synthesis.out"
    echo "$_ir_output" | bash -x \
        "$SCRIPT_DIR/backend/synthesis.sh" \
        > "$_syn_out" 2>&1
    cat "$_syn_out"
    echo

    echo "--- fin xtrace ---"
}

# ============================================================================
# SECTION: Main
# ============================================================================

main() {
    trap 'clean_debug; exit 0' INT TERM

    detect_tools

    _mode="trace"
    _inspect_stage=""
    _output_only=false

    while [ $# -gt 0 ]; do
        case "$1" in
            -t|--trace)
                _mode="trace"
                shift
                ;;
            -s|--step)
                _mode="step"
                shift
                ;;
            -m|--timing)
                _mode="timing"
                shift
                ;;
            -i|--inspect)
                _mode="inspect"
                if [ -z "${2:-}" ]; then
                    echo "Error: --inspect requiere un nombre de etapa" >&2
                    echo "Etapas: preprocessor, lexer, parser, semantic, ir_generator, synthesis" >&2
                    exit 1
                fi
                _inspect_stage="$2"
                shift 2
                ;;
            -x|--xtrace)
                _mode="xtrace"
                shift
                ;;
            -o|--output)
                _output_only=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            --)
                shift
                break
                ;;
            -*)
                echo "Error: opcion desconocida: $1" >&2
                echo "Usa --help para ver las opciones disponibles." >&2
                exit 1
                ;;
            *)
                break
                ;;
        esac
    done

    _instruction="$*"
    [ -z "$_instruction" ] && _instruction="$1"

    if [ -z "$_instruction" ]; then
        echo "Error: se requiere una instruccion." >&2
        echo "Usa: $SCRIPT_NAME \"crea modulo pagos en nestjs\"" >&2
        exit 1
    fi

    mkdir -p "$DEBUG_STAGE_DIR"

    # Si es modo output-only, ejecutar pipeline normal y solo mostrar JSON final
    if $_output_only; then
        debug_trace "$_instruction" >/dev/null 2>&1
        exit 0
    fi

    case "$_mode" in
        trace)
            debug_trace "$_instruction"
            ;;
        step)
            if [ ! -t 0 ]; then
                echo "Modo step requiere terminal. Cambiando a trace." >&2
                debug_trace "$_instruction"
            else
                debug_step "$_instruction"
            fi
            ;;
        timing)
            debug_timing "$_instruction"
            ;;
        inspect)
            debug_inspect "$_inspect_stage" "$_instruction"
            ;;
        xtrace)
            debug_xtrace "$_instruction"
            ;;
    esac

    clean_debug
}

main "$@"
