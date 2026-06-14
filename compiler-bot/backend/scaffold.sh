#!/bin/sh
# ============================================================================
# scaffold.sh - Generador de codigo desde templates para el bot RECPL
# ============================================================================
#
# ADVERTENCIA: DEPRECATED
#   Esta herramienta ha sido reemplazada por el sistema de generadores
#   AST-based en agentic_pipeline/generators/ (Sprint 9).
#   Los templates en templates/ han sido movidos a templates/archive/.
#   Usar solo para compatibilidad hacia atras con el pipeline v1 shell.
#
# PROPOSITO:
#   Dado un template y un nombre de entidad, genera los archivos
#   reemplazando los placeholders __NAME__ y __LOWERNAME__.
#
# USO:
#   ./scaffold.sh <template_dir> <nombre_entidad> <output_dir>
#
# EJEMPLO:
#   ./scaffold.sh templates/module-nestjs Payments modules/payments
# ============================================================================

# --- Constants ---
SCRIPT_NAME="scaffold.sh"
LOG_FILE="${LOG_FILE:-/tmp/recpl_scaffold.log}"

# --- Logging ---
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# --- Lowercase first letter, rest keep as-is ---
to_camel() {
    echo "$1" | awk '{print tolower(substr($0,1,1)) substr($0,2)}'
}

# --- Scaffold desde template ---
scaffold() {
    template_dir="$1"
    nombre="$2"
    output_dir="$3"

    if [ ! -d "$template_dir" ]; then
        echo "Error: template no encontrado: $template_dir" >&2
        return 1
    fi

    mkdir -p "$output_dir"
    lowername=$(to_camel "$nombre")
    output_files=""

    for template_file in "$template_dir"/*; do
        [ -f "$template_file" ] || continue

        filename=$(basename "$template_file")
        # Reemplazar __LOWERNAME__ en el nombre del archivo
        out_filename=$(echo "$filename" | sed "s/__LOWERNAME__/$lowername/g")
        out_path="${output_dir}/${out_filename}"

        # Reemplazar placeholders en el contenido
        sed \
            -e "s/__NAME__/$nombre/g" \
            -e "s/__LOWERNAME__/$lowername/g" \
            "$template_file" > "$out_path"

        if [ -n "$output_files" ]; then
            output_files="$output_files, \"$out_path\""
        else
            output_files="\"$out_path\""
        fi
        log "OK: generado $out_path"
    done

    echo "$output_files"
    return 0
}

# --- Main ---
main() {
    template_dir="$1"
    nombre="$2"
    output_dir="$3"

    if [ -z "$template_dir" ] || [ -z "$nombre" ]; then
        echo "Uso: $0 <template_dir> <nombre> [output_dir]" >&2
        exit 1
    fi

    if [ -z "$output_dir" ]; then
        lowername=$(to_camel "$nombre")
        output_dir="modules/${lowername}"
    fi

    scaffold "$template_dir" "$nombre" "$output_dir"
}

main "$@"
