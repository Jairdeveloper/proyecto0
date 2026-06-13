#!/bin/sh
# ============================================================================
# tool_write_file.sh - Herramienta: escribir/editar archivos
# ============================================================================
#
# Uso (via tool_registry): run_tool write_file "ruta" "contenido"
#
# NOTA: Usa jq -n --arg para construir JSON de forma segura.
# ============================================================================

tool_write_file() {
    _path="$1"
    shift
    _content="$*"

    if [ -z "$_path" ]; then
        jq -n --arg exito false --arg msg "Ruta de archivo no especificada" '{exito: $exito, mensaje: $msg}'
        return 1
    fi

    if [ -z "$_content" ]; then
        jq -n --arg exito false --arg msg "Contenido vacio" '{exito: $exito, mensaje: $msg}'
        return 1
    fi

    # Crear directorio si no existe
    _dir=$(dirname "$_path" 2>/dev/null)
    if [ -n "$_dir" ] && [ "$_dir" != "." ]; then
        mkdir -p "$_dir" 2>/dev/null
    fi

    # Verificar que el directorio sea escribible
    _dir_check=$(dirname "$_path" 2>/dev/null)
    [ -z "$_dir_check" ] && _dir_check="."

    if [ -d "$_dir_check" ] && [ ! -w "$_dir_check" ]; then
        jq -n --arg exito false --arg msg "Sin permisos de escritura en: $_dir_check" '{exito: $exito, mensaje: $msg}'
        return 1
    fi

    # Escribir archivo
    if printf '%s' "$_content" > "$_path" 2>/dev/null; then
        _size=$(wc -c < "$_path" 2>/dev/null || echo 0)
        jq -n \
            --arg exito true \
            --arg tipo "file_written" \
            --arg path "$_path" \
            --argjson bytes "$_size" \
            --arg msg "Archivo escrito correctamente ($_size bytes)" \
            '{exito: $exito, tipo_respuesta: $tipo, path: $path, bytes: $bytes, mensaje: $msg}'
    else
        jq -n --arg exito false --arg msg "Error al escribir archivo: $_path" '{exito: $exito, mensaje: $msg}'
        return 1
    fi
}
