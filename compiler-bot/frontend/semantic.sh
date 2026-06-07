#!/bin/sh
# ============================================================================
# semantic.sh - Analizador Semantico (EVAL) del bot RECPL
# ============================================================================
#
# PROPOSITO:
#   Analisis semantico y tabla de simbolos.
#   Recibe AST JSON del parser por stdin, valida y produce AST + symbol table.
#
# USO:
#   ./lexer.sh <texto> | ./parser.sh | ./semantic.sh
#
# SALIDA:
#   JSON con AST validado + symbol table a stdout
#
# ERRORES:
#   Errores semanticos a stderr, exit 1
# ============================================================================

# --- Constants ---
SCRIPT_NAME="semantic.sh"
LOG_FILE="${LOG_FILE:-/tmp/recpl_semantic.log}"
STATE_FILE="${STATE_FILE:-/tmp/recpl_symbol_table.json}"

ALLOWED_TECHS="NestJS|Prisma"

# --- Logging ---
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# --- Tabla de simbolos (hash en memoria) ---
# Usar RECPL_STATE_DIR para persistencia entre invocaciones del LOOP
if [ -n "$RECPL_STATE_DIR" ]; then
    SYMBOL_FILE="${RECPL_STATE_DIR}/symbols.tmp"
else
    SYMBOL_FILE="/tmp/recpl_symbols_$$.tmp"
    trap 'rm -f "$SYMBOL_FILE"' EXIT
fi

symbol_init() {
    # En modo LOOP (RECPL_STATE_DIR), preservar estado existente
    if [ -n "$RECPL_STATE_DIR" ] && [ -s "$SYMBOL_FILE" ]; then
        : # mantener simbolos previos
    else
        : > "$SYMBOL_FILE"
    fi
}

symbol_insert() {
    name="$1"
    tipo="$2"
    tech="$3"
    scope="$4"

    if symbol_exists "$name"; then
        echo "Error semantico: modulo duplicado: $name" >&2
        log "ERROR: duplicado: $name"
        exit 1
    fi

    echo "$name|$tipo|$tech|pending|$scope" >> "$SYMBOL_FILE"
    log "OK: insertado simbolo $name ($tipo, $tech, scope=$scope)"
}

symbol_lookup() {
    name="$1"
    grep "^$name|" "$SYMBOL_FILE" 2>/dev/null || echo ""
}

symbol_exists() {
    name="$1"
    result=$(symbol_lookup "$name")
    [ -n "$result" ]
}

symbol_delete() {
    name="$1"
    tmpf="/tmp/recpl_symbols_del_$$.tmp"
    grep -v "^$name|" "$SYMBOL_FILE" > "$tmpf" 2>/dev/null
    mv "$tmpf" "$SYMBOL_FILE"
    log "OK: eliminado simbolo $name"
}

# --- Scope stack ---
if [ -n "$RECPL_STATE_DIR" ]; then
    SCOPE_FILE="${RECPL_STATE_DIR}/scope.tmp"
else
    SCOPE_FILE="/tmp/recpl_scope_$$.tmp"
    trap 'rm -f "$SCOPE_FILE"' EXIT
fi

scope_init() {
    echo "global" > "$SCOPE_FILE"
}

scope_push() {
    name="$1"
    echo "$name" >> "$SCOPE_FILE"
    log "OK: scope push $name"
}

scope_pop() {
    lines=$(wc -l < "$SCOPE_FILE" 2>/dev/null || echo 0)
    if [ "$lines" -gt 1 ]; then
        tmpf="/tmp/recpl_scope_pop_$$.tmp"
        head -n $((lines - 1)) "$SCOPE_FILE" > "$tmpf"
        mv "$tmpf" "$SCOPE_FILE"
    fi
}

scope_current() {
    tail -n 1 "$SCOPE_FILE" 2>/dev/null || echo "global"
}

# --- Extraer campo JSON ---
json_field() {
    line="$1"
    key="$2"
    echo "$line" | awk -F'"' -v k="$key" '{
        for (i=1; i<NF; i++) {
            if ($i == k) {
                print $(i+2)
                exit
            }
        }
    }'
}

# --- Normalizar tech a capitalizada ---
normalize_tech() {
    tech="$1"
    case "$(echo "$tech" | tr '[:upper:]' '[:lower:]')" in
        nestjs) echo "NestJS" ;;
        prisma) echo "Prisma" ;;
        *) echo "$tech" ;;
    esac
}

# --- Variables globales para validate_tech ---
g_tech_validated=""
g_tech_error=""

# --- Validar tech contra lista blanca ---
validate_tech() {
    raw="$1"
    g_tech_validated=""
    g_tech_error=""
    if [ "$raw" = "null" ] || [ -z "$raw" ]; then
        g_tech_validated=""
        return
    fi
    norm=$(normalize_tech "$raw")
    for allowed in NestJS Prisma; do
        if [ "$norm" = "$allowed" ]; then
            g_tech_validated="$norm"
            return
        fi
    done
    echo "Error semantico: tech stack no soportado: $raw" >&2
    log "ERROR: tech no soportado: $raw"
    g_tech_error="true"
}

# --- Analizador semantico ---
semantic_analyzer() {
    ast_line="$1"

    accion=$(json_field "$ast_line" "accion")
    # obj_tipo esta en objetivo.tipo: extraer con awk
    obj_tipo=$(echo "$ast_line" | awk -F'"objetivo":' '{print $2}' | awk -F'"tipo":"' '{print $2}' | awk -F'"' '{print $1}')
    raw_tech=$(json_field "$ast_line" "tech")

    # Extraer entidades del array JSON "entidades":["a","b"]
    entidades=$(echo "$ast_line" | awk -F'"entidades":' '{print $2}' | awk -F']' '{print $1}' | sed 's/\[//;s/"//g')

    # Validar tech (sin subshell para que exit funcione)
    validate_tech "$raw_tech"
    [ -n "$g_tech_error" ] && exit 1
    tech="$g_tech_validated"

    # Scope actual
    current_scope=$(scope_current)

    # Procesar entidades
    IFS=','
    for entidad in $entidades; do
        entidad=$(echo "$entidad" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        [ -z "$entidad" ] && continue

        case "$accion" in
            CREATE|UPDATE)
                if symbol_exists "$entidad"; then
                    echo "Error semantico: modulo duplicado: $entidad" >&2
                    log "ERROR: duplicado: $entidad"
                    exit 1
                fi
                symbol_insert "$entidad" "$obj_tipo" "$tech" "$current_scope"
                ;;
            DELETE|READ)
                if ! symbol_exists "$entidad"; then
                    echo "Error semantico: undefined: $entidad" >&2
                    log "ERROR: undefined: $entidad"
                    exit 1
                fi
                ;;
        esac
    done
    unset IFS

    # Generar salida con tabla de simbolos
    sym_table="{"
    first=true
    while IFS='|' read -r name tipo tech estado scope; do
        if [ "$first" = true ]; then
            first=false
        else
            sym_table="$sym_table,"
        fi
        sym_table="$sym_table\"$name\":{\"tipo\":\"$tipo\",\"tech\":\"$tech\",\"estado\":\"$estado\",\"dependencias\":[],\"scope\":\"$scope\"}"
    done < "$SYMBOL_FILE"
    sym_table="$sym_table}"

    echo "{\"ast\":$ast_line,\"symbol_table\":$sym_table}"
}

# --- Main dispatch ---
main() {
    ast_line=""

    while IFS= read -r line; do
        ast_line="$line"
    done

    if [ -z "$ast_line" ]; then
        echo "Error: no hay AST de entrada" >&2
        exit 1
    fi

    symbol_init
    scope_init
    semantic_analyzer "$ast_line"
}

main "$@"
