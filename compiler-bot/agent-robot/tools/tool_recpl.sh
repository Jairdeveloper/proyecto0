#!/bin/sh
# ============================================================================
# tool_recpl.sh - Herramienta: delega en RECPL via bridge
# ============================================================================
#
# Uso (via tool_registry): run_tool recpl "instruccion"
# ============================================================================

tool_recpl() {
    _instruction="$*"

    if [ -z "$_instruction" ]; then
        echo "{\"exito\":false,\"mensaje\":\"Instruccion vacia para RECPL\"}"
        return 1
    fi

    # Cargar bridge (relativo a tools/ -> ../)
    _bridge_path="$(dirname "$0")/../bridge.sh"
    [ -f "$_bridge_path" ] && . "$_bridge_path"

    bridge_recpl "$_instruction"
}
