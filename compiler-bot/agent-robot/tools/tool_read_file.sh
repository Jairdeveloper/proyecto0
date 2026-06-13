#!/bin/sh
# ============================================================================
# tool_read_file.sh - Herramienta: leer archivos del sistema
# ============================================================================
#
# Uso (via tool_registry): run_tool read_file "ruta/al/archivo.txt"
#
# NOTA: Usa jq -n --arg para construir JSON de forma segura, evitando
# que el contenido del archivo (posibles backticks, $variables) sea
# interpretado por el shell al expandir un heredoc.
# ============================================================================

tool_read_file() {
    _path="$1"

    if [ -z "$_path" ]; then
        jq -n --arg exito false --arg msg "Ruta de archivo no especificada" '{exito: $exito, mensaje: $msg}'
        return 1
    fi

    if [ ! -f "$_path" ]; then
        jq -n --arg exito false --arg msg "Archivo no encontrado: $_path" '{exito: $exito, mensaje: $msg}'
        return 1
    fi

    if [ ! -r "$_path" ]; then
        jq -n --arg exito false --arg msg "Sin permisos de lectura: $_path" '{exito: $exito, mensaje: $msg}'
        return 1
    fi

    _content=$(cat "$_path" 2>/dev/null)
    _lines=$(echo "$_content" | wc -l 2>/dev/null || echo 0)
    _size=$(wc -c < "$_path" 2>/dev/null || echo 0)

    jq -n \
        --arg exito true \
        --arg tipo "file_content" \
        --arg path "$_path" \
        --argjson lineas "$_lines" \
        --argjson bytes "$_size" \
        --arg contenido "$_content" \
        '{exito: $exito, tipo_respuesta: $tipo, path: $path, lineas: $lineas, bytes: $bytes, contenido: $contenido}'
}
