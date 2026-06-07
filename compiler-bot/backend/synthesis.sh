#!/bin/sh
# ============================================================================
# synthesis.sh - Synthesis/PRINT del bot RECPL
# ============================================================================
#
# PROPOSITO:
#   Recibe IR.json del ir_generator.sh por stdin y produce la respuesta del bot
#   (mensaje + payload de accion). Es la fase PRINT del ciclo RECPL.
#
# USO:
#   ... | ./semantic.sh | ./ir_generator.sh | ./synthesis.sh
#
# SALIDA:
#   JSON con tipo_respuesta, mensaje y payload a stdout
# ============================================================================

# --- Constants ---
SCRIPT_NAME="synthesis.sh"
LOG_FILE="${LOG_FILE:-/tmp/recpl_synthesis.log}"
SCRIPT_DIR="$(dirname "$0")"

# --- Logging ---
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# --- Extraer campo JSON ---
json_field() {
    line="$1"
    key="$2"
    echo "$line" | awk -F'"' -v k="$key" '{
        for (i=1; i<NF; i++) {
            if ($i == k) {
                val = $(i+2)
                gsub(/^:[[:space:]]*/, "", val)
                gsub(/^"|"$/, "", val)
                gsub(/,$/, "", val)
                if (val == "null") val = ""
                print val
                exit
            }
        }
    }'
}

# --- Capitalizar primera letra ---
capitalize() {
    text="$1"
    first=$(echo "$text" | awk '{print substr($0,1,1)}' | tr '[:lower:]' '[:upper:]')
    rest=$(echo "$text" | awk '{print substr($0,2)}')
    echo "$first$rest"
}

# --- Lowercase first letter ---
to_lower() {
    echo "$1" | awk '{print tolower(substr($0,1,1)) substr($0,2)}'
}

# --- Accion scaffold (CREATE) ---
execute_scaffold() {
    ir_json="$1"
    tipo=$(json_field "$ir_json" "tipo")
    nombre=$(json_field "$ir_json" "nombre")
    tech=$(json_field "$ir_json" "tech")
    template=$(json_field "$ir_json" "template")

    nombre_cap=$(capitalize "$nombre")
    lowername=$(to_lower "$nombre_cap")

    template_dir="${SCRIPT_DIR}/../templates/${template}"
    output_dir="modules/${lowername}"

    archivos="[]"
    if [ -d "$template_dir" ]; then
        scaffold_output=$("${SCRIPT_DIR}/scaffold.sh" "$template_dir" "$nombre_cap" "$output_dir" 2>&1)
        if [ $? -eq 0 ] && [ -n "$scaffold_output" ]; then
            archivos="[$scaffold_output]"
        fi
    fi

    if [ -n "$tech" ]; then
        mensaje="Generando ${tipo} ${nombre_cap} en ${tech}..."
    else
        mensaje="Generando ${tipo} ${nombre_cap}..."
    fi

    echo "  \"tipo_respuesta\": \"action\","
    echo "  \"mensaje\": \"$mensaje\","
    echo "  \"payload\": {"
    echo "    \"accion\": \"scaffold:${tipo}\","
    echo "    \"params\": {"
    echo "      \"nombre\": \"$nombre_cap\","
    echo "      \"tech\": \"$tech\","
    echo "      \"template\": \"$template\""
    echo "    },"
    echo "    \"archivos\": $archivos"
    echo "  }"
}

# --- Accion delete ---
execute_delete() {
    ir_json="$1"
    tipo=$(json_field "$ir_json" "tipo")
    nombre=$(json_field "$ir_json" "nombre")

    nombre_cap=$(capitalize "$nombre")

    echo "  \"tipo_respuesta\": \"action\","
    echo "  \"mensaje\": \"Eliminando ${tipo} ${nombre_cap}...\","
    echo "  \"payload\": {"
    echo "    \"accion\": \"delete:${tipo}\","
    echo "    \"params\": {"
    echo "      \"nombre\": \"$nombre_cap\""
    echo "    },"
    echo "    \"archivos\": []"
    echo "  }"
}

# --- Accion update ---
execute_update() {
    ir_json="$1"
    tipo=$(json_field "$ir_json" "tipo")
    nombre=$(json_field "$ir_json" "nombre")

    nombre_cap=$(capitalize "$nombre")

    echo "  \"tipo_respuesta\": \"action\","
    echo "  \"mensaje\": \"Modificando ${tipo} ${nombre_cap}...\","
    echo "  \"payload\": {"
    echo "    \"accion\": \"update:${tipo}\","
    echo "    \"params\": {"
    echo "      \"nombre\": \"$nombre_cap\""
    echo "    },"
    echo "    \"archivos\": []"
    echo "  }"
}

# --- Accion read ---
execute_read() {
    ir_json="$1"
    tipo=$(json_field "$ir_json" "tipo")
    nombre=$(json_field "$ir_json" "nombre")

    nombre_cap=$(capitalize "$nombre")

    echo "  \"tipo_respuesta\": \"info\","
    echo "  \"mensaje\": \"Mostrando ${tipo} ${nombre_cap}...\","
    echo "  \"payload\": {"
    echo "    \"accion\": \"read:${tipo}\","
    echo "    \"params\": {"
    echo "      \"nombre\": \"$nombre_cap\""
    echo "    },"
    echo "    \"archivos\": []"
    echo "  }"
}

# --- Synthesis main ---
synthesize() {
    ir_json="$1"
    accion=$(json_field "$ir_json" "accion")

    echo "{"
    case "$accion" in
        scaffold) execute_scaffold "$ir_json" ;;
        delete)   execute_delete "$ir_json" ;;
        update)   execute_update "$ir_json" ;;
        read)     execute_read "$ir_json" ;;
        *)
            echo "  \"tipo_respuesta\": \"error\","
            echo "  \"mensaje\": \"Accion desconocida: $accion\","
            echo "  \"payload\": null"
            ;;
    esac
    echo "}"
}

# --- Main dispatch ---
main() {
    ir_json=""
    first=true

    while IFS= read -r line; do
        if [ "$first" = true ]; then
            ir_json="$line"
            first=false
        else
            ir_json="$ir_json$line"
        fi
    done

    if [ -z "$ir_json" ]; then
        echo "Error: no hay IR.json de entrada" >&2
        exit 1
    fi

    synthesize "$ir_json"
}

main "$@"
