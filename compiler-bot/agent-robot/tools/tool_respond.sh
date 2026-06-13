#!/bin/sh
# ============================================================================
# tool_respond.sh - Herramienta: responde directamente al usuario
# ============================================================================
#
# Uso (via tool_registry): run_tool respond "mensaje"
#
# NOTA: Usa jq -n --arg para construir JSON de forma segura.
# ============================================================================

tool_respond() {
    _message="$*"

    if [ -z "$_message" ]; then
        jq -n --arg exito false --arg msg "Mensaje vacio" '{exito: $exito, mensaje: $msg}'
        return 1
    fi

    jq -n \
        --arg exito true \
        --arg tipo "respond" \
        --arg mensaje "$_message" \
        '{exito: $exito, tipo_respuesta: $tipo, mensaje: $mensaje, payload: {}}'
}
