#!/bin/sh
# ============================================================================
# tool_run_command.sh - Herramienta: ejecutar comandos del sistema
# ============================================================================
#
# Uso (via tool_registry): run_tool run_command "ls -la"
#
# NOTA: Usa jq -n --arg para construir JSON de forma segura.
# ============================================================================

tool_run_command() {
    _command="$*"

    if [ -z "$_command" ]; then
        jq -n --arg exito false --arg msg "Comando vacio" '{exito: $exito, mensaje: $msg}'
        return 1
    fi

    # Ejecutar comando
    _start_time=$(date +%s 2>/dev/null)
    _output=$(sh -c "$_command" 2>&1)
    _exit_code=$?
    _end_time=$(date +%s 2>/dev/null)
    _elapsed=$((_end_time - _start_time))
    [ "$_elapsed" -lt 0 ] && _elapsed=0

    _line_count=$(echo "$_output" | wc -l 2>/dev/null || echo 0)

    jq -n \
        --arg exito "$( [ $_exit_code -eq 0 ] && echo true || echo false )" \
        --arg tipo "command_output" \
        --arg comando "$_command" \
        --argjson exit_code "$_exit_code" \
        --argjson lineas "$_line_count" \
        --arg output "$_output" \
        --argjson tiempo_ms "$_elapsed" \
        '{exito: $exito, tipo_respuesta: $tipo, comando: $comando, exit_code: $exit_code, lineas: $lineas, output: $output, tiempo_ms: $tiempo_ms}'
}
