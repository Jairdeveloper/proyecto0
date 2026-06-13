#!/bin/sh
# ============================================================================
# tool_respond.sh - Herramienta: responde directamente al usuario
# ============================================================================
#
# Uso (via tool_registry): run_tool respond "mensaje"
# ============================================================================

tool_respond() {
    _message="$*"

    if [ -z "$_message" ]; then
        echo "{\"exito\":false,\"mensaje\":\"Mensaje vacio\"}"
        return 1
    fi

    cat <<EOF
{
  "exito": true,
  "tipo_respuesta": "respond",
  "mensaje": $(printf '%s' "$_message" | jq -R -s . 2>/dev/null || echo "\"$_message\""),
  "payload": {}
}
EOF
}
