#!/bin/sh
# ============================================================================
# ir_generator.sh - Generador de IR.json del bot RECPL
# ============================================================================
#
# PROPOSITO:
#   Recibe AST validado + symbol table del semantic.sh por stdin y genera
#   una representacion intermedia (IR.json) canonica y autocontenida.
#
# USO:
#   ./lexer.sh <texto> | ./parser.sh | ./semantic.sh | ./ir_generator.sh
#
# SALIDA:
#   IR.json a stdout
# ============================================================================

# --- Constants ---
SCRIPT_NAME="ir_generator.sh"
LOG_FILE="${LOG_FILE:-/tmp/recpl_ir.log}"

# --- Logging ---
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# --- Extraer campo del AST (primer nivel dentro de "ast":{...}) ---
# La entrada tiene formato: {"ast":{...},"symbol_table":{...}}
extract_ast_field() {
    line="$1"
    key="$2"
    # Extraer solo el objeto ast: sed desde '"ast":{' hasta '},"symbol_table"'
    ast_obj=$(echo "$line" | sed 's/.*"ast":{//;s/},"symbol_table".*//')
    # Buscar key en el objeto ast:  "key":"valor"  o  "key":null  o  "key":123
    echo "$ast_obj" | awk -F'"' -v k="$key" '{
        for (i=1; i<NF; i++) {
            if ($i == k) {
                val = $(i+2)
                # si val empieza con :, extraer el valor sin comillas
                gsub(/^:/, "", val)
                gsub(/^"|"$/, "", val)
                # si es null, devolver vacio
                if (val == "null") val = ""
                print val
                exit
            }
        }
    }'
}

# --- Extraer campo de objeto anidado dentro del AST ---
# Busca "objetivo":{"tipo":"module",...} y extrae el valor de inner_key
extract_nested_ast_field() {
    line="$1"
    outer="$2"
    inner="$3"
    ast_obj=$(echo "$line" | sed 's/.*"ast":{//;s/},"symbol_table".*//')
    # Extraer el objeto outer
    outer_obj=$(echo "$ast_obj" | awk -F'"'"$outer"'"' '{print $2}' | sed 's/^:[[:space:]]*{//;s/},.*//')
    echo "$outer_obj" | awk -F'"' -v k="$inner" '{
        for (i=1; i<NF; i++) {
            if ($i == k) {
                val = $(i+2)
                gsub(/^:/, "", val)
                gsub(/^"|"$/, "", val)
                print val
                exit
            }
        }
    }'
}

# --- Extraer entidades del AST ---
extract_ast_entities() {
    line="$1"
    ast_obj=$(echo "$line" | sed 's/.*"ast":{//;s/},"symbol_table".*//')
    echo "$ast_obj" | awk -F'"entidades":' '{print $2}' | awk -F']' '{print $1}' | sed 's/\[//;s/"//g'
}

# --- Extraer symbol table del JSON de entrada ---
extract_symbol_table() {
    line="$1"
    echo "$line" | sed 's/.*"symbol_table":\(.*\)}$/\1/'
}

# --- Generar trace_id ---
generate_trace_id() {
    echo "trc_$(date '+%s')_$$"
}

# --- Mapear accion a tipo IR ---
map_action() {
    accion="$1"
    case "$accion" in
        CREATE) echo "scaffold" ;;
        DELETE) echo "delete" ;;
        UPDATE) echo "update" ;;
        READ)   echo "read" ;;
        *)      echo "$accion" | tr '[:upper:]' '[:lower:]' ;;
    esac
}

# --- Mapear tipo+tech a template ---
map_template() {
    tipo="$1"
    tech="$2"
    case "$(echo "$tech" | tr '[:upper:]' '[:lower:]')" in
        nestjs) echo "${tipo}-nestjs" ;;
        prisma) echo "${tipo}-prisma" ;;
        *)      echo "${tipo}-generic" ;;
    esac
}

# --- Generar IR ---
generate_ir() {
    input_json="$1"

    accion=$(extract_ast_field "$input_json" "accion")
    obj_tipo=$(extract_nested_ast_field "$input_json" "objetivo" "tipo")
    raw_tech=$(extract_ast_field "$input_json" "tech")
    symbol_table=$(extract_symbol_table "$input_json")

    # Extraer entidades del array
    entidades=$(extract_ast_entities "$input_json")

    ir_accion=$(map_action "$accion")

    # Limpiar tech
    if [ "$raw_tech" = "null" ] || [ -z "$raw_tech" ]; then
        tech=""
    else
        tech=$(echo "$raw_tech" | sed 's/^"//;s/"$//')
    fi

    template=$(map_template "$obj_tipo" "$tech")
    trace_id=$(generate_trace_id)

    # Tomar primera entidad como nombre principal
    nombre=$(echo "$entidades" | sed 's/,.*//' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

    # Formatear entidades como JSON array con quotes
    ent_json=""
    IFS=','
    for e in $entidades; do
        e=$(echo "$e" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        if [ -n "$ent_json" ]; then
            ent_json="$ent_json, \"$e\""
        else
            ent_json="\"$e\""
        fi
    done
    unset IFS

    echo "{"
    echo "  \"accion\": \"$ir_accion\","
    echo "  \"tipo\": \"$obj_tipo\","
    echo "  \"nombre\": \"$nombre\","
    echo "  \"tech\": \"$tech\","
    echo "  \"template\": \"$template\","
    echo "  \"entidades\": [$ent_json],"
    echo "  \"dependencias\": [],"
    echo "  \"score\": null,"
    echo "  \"trace_id\": \"$trace_id\","
    echo "  \"symbol_table\": $symbol_table"
    echo "}"
}

# --- Main dispatch ---
main() {
    input_json=""

    while IFS= read -r line; do
        input_json="$line"
    done

    if [ -z "$input_json" ]; then
        echo "Error: no hay entrada JSON" >&2
        exit 1
    fi

    generate_ir "$input_json"
}

main "$@"
