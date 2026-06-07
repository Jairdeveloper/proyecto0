#!/bin/sh
# ============================================================================
# parser.sh - Analizador Sintactico (EVAL) del bot RECPL
# ============================================================================
#
# PROPOSITO:
#   Parser recursivo descendente LL(1). Recibe tokens JSON del lexer por stdin
#   y produce un AST en JSON con la estructura del comando.
#
# GRAMATICA BNF:
#   comando       → accion modulo_espec opcional_tech
#   accion        → ACTION_CREATE | ACTION_DELETE | ACTION_UPDATE | ACTION_READ
#   modulo_espec  → MODULE ARTICLE? ENTITY (PREP ENTITY)*
#                 | ENTITY
#   opcional_tech → PREP TECH (SEPARATOR TECH)*
#                 | ε
#
# USO:
#   ./lexer.sh <texto> | ./parser.sh
#
# SALIDA:
#   AST en JSON a stdout
#
# ERRORES:
#   Errores sintacticos a stderr, exit 1
# ============================================================================

# --- Constants ---
SCRIPT_NAME="parser.sh"
LOG_FILE="${LOG_FILE:-/tmp/recpl_parser.log}"
TOKEN_FILE="/tmp/recpl_tokens_$$.tmp"

trap 'rm -f "$TOKEN_FILE"' EXIT

# --- Global state ---
cursor=0
token_count=0

# --- Valores de retorno globales (evita subshell) ---
g_accion=""
g_obj_tipo=""
g_obj_ents=""
g_tech=""

# --- Logging ---
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# --- Extraer campo JSON por clave ---
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

# --- Cargar tokens desde stdin a archivo temporal ---
load_tokens() {
    while IFS= read -r line; do
        echo "$line" >> "$TOKEN_FILE"
        token_count=$((token_count + 1))
    done
}

# --- Obtener token en cursor ---
current_token_raw() {
    if [ "$cursor" -ge "$token_count" ]; then
        echo ""
        return
    fi
    line_num=$((cursor + 1))
    sed -n "${line_num}p" "$TOKEN_FILE"
}

# --- Obtener type del token actual ---
current_type() {
    t=$(current_token_raw)
    if [ -z "$t" ]; then
        echo "EOF"
        return
    fi
    json_field "$t" "type"
}

# --- Obtener lexeme del token actual ---
current_lexeme() {
    t=$(current_token_raw)
    if [ -z "$t" ]; then
        echo ""
        return
    fi
    json_field "$t" "lexeme"
}

# --- Avanzar cursor ---
advance() {
    cursor=$((cursor + 1))
}

# --- Esperar un tipo de token ---
expect() {
    expected="$1"
    actual=$(current_type)
    lexeme=$(current_lexeme)

    if [ "$actual" = "$expected" ]; then
        advance
        return 0
    fi

    echo "Error sintactico en token $cursor: se esperaba '$expected', se encontro '$actual' (lexema: '$lexeme')" >&2
    log "ERROR: sintactico en token $cursor: esperaba '$expected', obtuve '$actual'"
    exit 1
}

# --- Es ARTICLE? ---
is_article() {
    lexeme=$(current_lexeme)
    for art in "un" "una" "el" "la" "los" "las"; do
        if [ "$lexeme" = "$art" ]; then
            return 0
        fi
    done
    return 1
}

# --- parse_accion ---
parse_accion() {
    t=$(current_type)

    case "$t" in
        ACTION_CREATE)
            g_accion="CREATE"
            advance
            ;;
        ACTION_DELETE)
            g_accion="DELETE"
            advance
            ;;
        ACTION_UPDATE)
            g_accion="UPDATE"
            advance
            ;;
        ACTION_READ)
            g_accion="READ"
            advance
            ;;
        *)
            lexeme=$(current_lexeme)
            echo "Error sintactico en token $cursor: se esperaba una accion, se encontro '$t' ('$lexeme')" >&2
            exit 1
            ;;
    esac
}

# --- Consumir entidades con PREP opcional: [PREP] ENTITY (PREP ENTITY)* ---
# Retorna en g_obj_ents. PREP seguido de TECH se deja para opcional_tech.
parse_entity_list() {
    # PREP opcional antes de la ENTITY principal
    t=$(current_type)
    if echo "$t" | grep -q "^PREP_"; then
        saved_cursor=$cursor
        advance
        next_t=$(current_type)
        cursor=$saved_cursor
        if echo "$next_t" | grep -q "^TECH_"; then
            : # No consumir, dejar para opcional_tech
        else
            advance # consumir PREP
        fi
    fi

    t=$(current_type)
    if [ "$t" != "ENTITY" ]; then
        lexeme=$(current_lexeme)
        echo "Error sintactico en token $cursor: se esperaba ENTITY, se encontro '$t' ('$lexeme')" >&2
        exit 1
    fi
    g_obj_ents=$(current_lexeme)
    advance

    # (PREP ENTITY)*
    while true; do
        t=$(current_type)
        [ "$t" = "EOF" ] && break
        if echo "$t" | grep -q "^PREP_"; then
            saved_cursor=$cursor
            advance
            next_t=$(current_type)
            cursor=$saved_cursor
            if echo "$next_t" | grep -q "^TECH_"; then
                break
            fi
            # Consumir PREP + ENTITY
            advance
            t=$(current_type)
            if [ "$t" = "ENTITY" ]; then
                g_obj_ents="$g_obj_ents $(current_lexeme)"
                advance
            fi
        else
            break
        fi
    done
}

# --- parse_modulo_espec ---
parse_modulo_espec() {
    t=$(current_type)

    if [ "$t" = "MODULE" ]; then
        advance
        g_obj_tipo="module"
        g_obj_ents=""

        # ARTICLE opcional
        if is_article; then
            advance
        fi

        parse_entity_list
    elif [ "$t" = "ENTITY" ]; then
        # Si la ENTITY es un articulo, puede que le siga MODULE
        if is_article; then
            saved_cursor=$cursor
            advance
            next_t=$(current_type)
            cursor=$saved_cursor
            if [ "$next_t" = "MODULE" ]; then
                advance # consumir articulo
                t=$(current_type)
                if [ "$t" = "MODULE" ]; then
                    advance
                    g_obj_tipo="module"
                    g_obj_ents=""
                    parse_entity_list
                    return
                fi
            fi
        fi
        g_obj_tipo="entity"
        g_obj_ents=$(current_lexeme)
        advance
    else
        lexeme=$(current_lexeme)
        echo "Error sintactico en token $cursor: se esperaba MODULE o ENTITY, se encontro '$t' ('$lexeme')" >&2
        exit 1
    fi
}

# --- parse_opcional_tech ---
parse_opcional_tech() {
    t=$(current_type)

    if echo "$t" | grep -q "^PREP_"; then
        advance
        g_tech=""

        t=$(current_type)
        if echo "$t" | grep -q "^TECH_"; then
            g_tech=$(current_lexeme)
            advance
        fi

        # (SEPARATOR TECH)*
        while true; do
            t=$(current_type)
            [ "$t" = "EOF" ] && break
            if [ "$t" = "SEPARATOR" ]; then
                advance
                t=$(current_type)
                if echo "$t" | grep -q "^TECH_"; then
                    g_tech="$g_tech $(current_lexeme)"
                    advance
                fi
            else
                break
            fi
        done
    else
        g_tech=""
    fi
}

# --- parse_comando ---
parse_comando() {
    parse_accion
    parse_modulo_espec
    parse_opcional_tech
}

# --- Formatear AST como JSON ---
format_ast() {
    ent_json=""
    for e in $g_obj_ents; do
        if [ -n "$ent_json" ]; then
            ent_json="$ent_json, \"$e\""
        else
            ent_json="\"$e\""
        fi
    done

    tech_json="null"
    if [ -n "$g_tech" ]; then
        tech_json="\"$g_tech\""
    fi

    echo "{\"tipo\":\"Comando\",\"accion\":\"$g_accion\",\"objetivo\":{\"tipo\":\"$g_obj_tipo\",\"entidades\":[$ent_json]},\"tech\":$tech_json}"
}

# --- Main dispatch ---
main() {
    load_tokens

    if [ "$token_count" -eq 0 ]; then
        echo "Error: no hay tokens de entrada" >&2
        exit 1
    fi

    parse_comando

    # Verificar que no sobren tokens
    t=$(current_type)
    if [ "$t" != "EOF" ]; then
        lexeme=$(current_lexeme)
        echo "Error sintactico en token $cursor: se esperaba fin de entrada, se encontro '$t' ('$lexeme')" >&2
        exit 1
    fi

    format_ast
}

main "$@"
