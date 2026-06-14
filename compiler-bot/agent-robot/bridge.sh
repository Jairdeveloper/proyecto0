#!/bin/sh
# ============================================================================
# bridge.sh - Bridge entre Agent-Robot y el pipeline RECPL existente
# ============================================================================
#
# PROPOSITO:
#   Unico punto de contacto entre agent-robot y RECPL. Aisla al agente de
#   los detalles internos del pipeline compilador.
#
# CONTRATO:
#   bridge_recpl(instruction)  → JSON { exito, origen, tipo_respuesta, ... }
#   bridge_debug(instruction)  → JSON con trazabilidad completa
#   bridge_state()             → JSON con tabla de simbolos actual
# ============================================================================

# --- Ruta a RECPL (relativa a este script) ---
BRIDGE_SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# --- Ejecutar instruccion en RECPL y devolver respuesta estructurada ---
# Uso: bridge_recpl "instruccion"
# Output: JSON con exito, origen, tipo_respuesta, mensaje, payload, raw, tiempo_ms
bridge_recpl() {
    _instruction="$1"
    _start_time=$(date +%s 2>/dev/null)
    [ -z "$_start_time" ] && _start_time=0

    # Llamar a recpl.sh en modo comando
    _raw_output=$(cd "$BRIDGE_SCRIPT_DIR" && ./recpl.sh -c "$_instruction" 2>/dev/null)
    _exit_code=$?

    _end_time=$(date +%s 2>/dev/null)
    _elapsed=$((_end_time - _start_time))
    [ "$_elapsed" -lt 0 ] && _elapsed=0

    if [ $_exit_code -ne 0 ] || [ -z "$_raw_output" ]; then
        cat <<EOF
{
  "exito": false,
  "origen": "recpl",
  "tipo_respuesta": "error",
  "mensaje": "RECPL no pudo procesar la instruccion",
  "payload": null,
  "raw": $(printf '%s' "$_raw_output" | jq -R -s . 2>/dev/null || echo '""'),
  "tiempo_ms": $_elapsed
}
EOF
        return 1
    fi

    # Intentar parsear como JSON (RECPL responde JSON en synthesis)
    _parsed=$(printf '%s' "$_raw_output" | jq -e . 2>/dev/null) && {
        _accion=$(echo "$_parsed" | jq -r '.accion // "unknown"')
        _mensaje=$(echo "$_parsed" | jq -r '.mensaje // ""')
        _payload=$(echo "$_parsed" | jq -r '.payload // {}')

        cat <<EOF
{
  "exito": true,
  "origen": "recpl",
  "tipo_respuesta": "action",
  "mensaje": $(printf '%s' "$_mensaje" | jq -R -s .),
  "payload": $_payload,
  "raw": $_parsed,
  "tiempo_ms": $_elapsed
}
EOF
        return 0
    }

    # Si no es JSON, devolver como texto
    cat <<EOF
{
  "exito": true,
  "origen": "recpl",
  "tipo_respuesta": "text",
  "mensaje": $(printf '%s' "$_raw_output" | jq -R -s .),
  "payload": {},
  "raw": $(printf '%s' "$_raw_output" | jq -R -s .),
  "tiempo_ms": $_elapsed
}
EOF
}

# --- Ejecutar instruccion con pipeline_debugger.sh ---
# Uso: bridge_debug "instruccion"
# Output: JSON con trazabilidad completa
bridge_debug() {
    _instruction="$1"

    _output=$(cd "$BRIDGE_SCRIPT_DIR" && ./pipeline_debugger.sh --output "$_instruction" 2>/dev/null)
    _exit_code=$?

    if [ $_exit_code -ne 0 ]; then
        echo '{"exito":false,"origen":"debugger","tipo_respuesta":"error","mensaje":"Debugger fallo"}'
        return 1
    fi

    printf '%s' "$_output" | jq -e . 2>/dev/null && return 0

    echo '{"exito":true,"origen":"debugger","tipo_respuesta":"text","mensaje":""}'
}

# --- Ejecutar instruccion en LLM y devolver respuesta estructurada ---
# Uso: bridge_llm "instruccion"
# Output: JSON con respuesta del LLM
bridge_llm() {
    _instruction="$1"
    _provider="${AGENT_LLM_PROVIDER:-}"

    _start_time=$(date +%s 2>/dev/null)
    [ -z "$_start_time" ] && _start_time=0

    if [ -n "$_provider" ]; then
        _raw_output=$(RECPL_LLM_PROVIDER="$_provider" \
            cd "$BRIDGE_SCRIPT_DIR" && ./recpl.sh --llm -c "$_instruction" 2>/dev/null)
    else
        _raw_output=$(cd "$BRIDGE_SCRIPT_DIR" && ./recpl.sh --llm -c "$_instruction" 2>/dev/null)
    fi
    _exit_code=$?

    _end_time=$(date +%s 2>/dev/null)
    _elapsed=$((_end_time - _start_time))
    [ "$_elapsed" -lt 0 ] && _elapsed=0

    if [ -z "$_raw_output" ]; then
        jq -n --arg exito false --arg origen "llm" \
            --arg tipo "error" \
            --arg msg "LLM no produjo respuesta" \
            '{exito: $exito, origen: $origen, tipo_respuesta: $tipo, mensaje: $msg, payload: null, raw: "", tiempo_ms: 0}'
        return
    fi

    jq -n --arg exito true --arg origen "llm" \
        --arg tipo "llm_response" \
        --arg respuesta "$_raw_output" \
        '{exito: $exito, origen: $origen, tipo_respuesta: $tipo, mensaje: $respuesta, payload: {}, raw: $respuesta, tiempo_ms: 0}'
}

# --- Consultar estado interno de RECPL ---
# Uso: bridge_state
# Output: JSON con snapshot del estado
bridge_state() {
    _state_dir="${RECPL_STATE_DIR:-/tmp/recpl_state_$$}"

    if [ ! -d "$_state_dir" ]; then
        echo '{"exito":true,"modulos":[],"simbolos":{}}'
        return 0
    fi

    _modulos=""
    for _f in "$_state_dir"/*.json; do
        [ -f "$_f" ] || continue
        _content=$(cat "$_f" 2>/dev/null)
        _modulos="${_modulos}${_modulos:+,}$_content"
    done

    cat <<EOF
{
  "exito": true,
  "modulos": [$_modulos],
  "state_dir": "$_state_dir"
}
EOF
}
