#!/bin/sh
# ============================================================================
# tool_search_code.sh - Herramienta: buscar en codigo fuente
# ============================================================================
#
# Uso (via tool_registry): run_tool search_code "patron" "ruta_opcional"
# ============================================================================

tool_search_code() {
    _pattern="$1"
    _path="${2:-.}"

    if [ -z "$_pattern" ]; then
        echo "{\"exito\":false,\"mensaje\":\"Patron de busqueda vacio\"}"
        return 1
    fi

    if [ ! -d "$_path" ] && [ ! -f "$_path" ]; then
        echo "{\"exito\":false,\"mensaje\":\"Ruta no valida: $_path\"}"
        return 1
    fi

    _results=$(grep -rn "$_pattern" "$_path" 2>/dev/null | head -100)
    _count=$(echo "$_results" | grep -c . 2>/dev/null || echo 0)

    cat <<EOF
{
  "exito": true,
  "tipo_respuesta": "search_results",
  "pattern": $(printf '%s' "$_pattern" | jq -R -s .),
  "path": $(printf '%s' "$_path" | jq -R -s .),
  "total_resultados": $_count,
  "resultados": $(printf '%s' "$_results" | jq -R -s .)
}
EOF
}
