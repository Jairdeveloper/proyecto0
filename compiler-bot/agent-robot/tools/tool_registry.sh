#!/bin/sh
# ============================================================================
# tool_registry.sh - Registro central de herramientas del agente
# ============================================================================
#
# Formato por herramienta:
#   nombre:script_relativo:descripcion:parametros_json
#
# script_relativo es relativo a tools/
# ============================================================================

TOOL_REGISTRY='recpl:tool_recpl.sh:Ejecuta instrucciones RECPL:{"instruction":"string","description":"Instruccion en lenguaje natural para RECPL"}
respond:tool_respond.sh:Responde directamente al usuario:{"message":"string","description":"Mensaje textual para el usuario"}
read_file:tool_read_file.sh:Lee el contenido de un archivo:{"path":"string","description":"Ruta absoluta o relativa del archivo"}
write_file:tool_write_file.sh:Escribe contenido en un archivo:{"path":"string","content":"string","description":"Ruta del archivo y contenido a escribir"}
run_command:tool_run_command.sh:Ejecuta un comando del sistema:{"command":"string","description":"Comando shell a ejecutar"}
search_code:tool_search_code.sh:Busca texto en el codigo fuente:{"pattern":"string","path":"string","description":"Patron de busqueda y ruta opcional"}'

# --- Listar todas las herramientas disponibles ---
# Uso: list_tools
# Output: lista legible
list_tools() {
    echo "$TOOL_REGISTRY" | while IFS=: read -r _name _script _desc _params; do
        echo "  $_name  - $_desc"
    done
}

# --- Verificar si una herramienta existe ---
# Uso: has_tool <nombre>
# Output: 0 si existe, 1 si no
has_tool() {
    _name="$1"
    echo "$TOOL_REGISTRY" | cut -d: -f1 | grep -q "^${_name}$"
}

# --- Obtener script de una herramienta ---
# Uso: get_tool_script <nombre>
get_tool_script() {
    _name="$1"
    echo "$TOOL_REGISTRY" | while IFS=: read -r _n _s _d _p; do
        [ "$_n" = "$_name" ] && echo "$_s" && return 0
    done
}

# --- Obtener descripcion de una herramienta ---
# Uso: get_tool_desc <nombre>
get_tool_desc() {
    _name="$1"
    echo "$TOOL_REGISTRY" | while IFS=: read -r _n _s _d _p; do
        [ "$_n" = "$_name" ] && echo "$_d" && return 0
    done
}

# --- Ejecutar una herramienta ---
# Uso: run_tool <nombre> [parametros...]
# Output: resultado de la herramienta
run_tool() {
    _name="$1"
    shift

    has_tool "$_name" || {
        echo "{\"exito\":false,\"mensaje\":\"Herramienta desconocida: $_name\"}"
        return 1
    }

    _script=$(get_tool_script "$_name")
    _tool_path="$(dirname "$0")/$_script"

    if [ ! -f "$_tool_path" ]; then
        echo "{\"exito\":false,\"mensaje\":\"Script de herramienta no encontrado: $_script\"}"
        return 1
    fi

    # Cargar y ejecutar la herramienta
    . "$_tool_path"
    _func_name="tool_${_name}"
    $_func_name "$@"
}
