#!/bin/sh
# ============================================================================
# lexer.sh - Analizador Lexico (READ) del bot RECPL
# ============================================================================
#
# PROPOSITO:
#   Tokeniza texto en lenguaje natural usando DFA con maximal munch.
#   Recibe input ya preprocesado (lowercase, sin puntuacion repetida).
#
# USO:
#   ./lexer.sh <texto>
#
# SALIDA:
#   JSON tokens (uno por linea) a stdout
#
# ERRORES:
#   Tokens no reconocidos se reportan a stderr, no detienen el procesamiento
# ============================================================================

# --- Constants ---
SCRIPT_NAME="lexer.sh"
LOG_FILE="${LOG_FILE:-/tmp/recpl_lexer.log}"

# --- Logging ---
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# --- Longitud de string ---
str_len() {
    echo "$1" | awk '{print length}'
}

# --- Substring desde pos ---
substr_from() {
    echo "$1" | awk "{print substr(\$0, $2 + 1)}"
}

# --- Match patron ERE al inicio usando awk (soporta | como alternancia) ---
awk_match_prefix() {
    text="$1"
    pattern="$2"
    echo "$text" | awk "{
        if (match(\$0, /^($pattern)/)) {
            print substr(\$0, RSTART, RLENGTH)
        }
    }"
}

# --- Token matching: devuelve el match mas largo (maximal munch) ---
match_token() {
    text="$1"

    best_type=""
    best_lexeme=""
    best_len=0

    for entry in \
        "ACTION_CREATE:creando|crear|crea|generar|make|new" \
        "ACTION_DELETE:eliminar|borrar|delete|remove" \
        "ACTION_UPDATE:actualizar|modificar|update|edit" \
        "ACTION_READ:mostrar|listar|get|show|read" \
        "MODULE:modulo|module" \
        "TECH_NESTJS:nestjs" \
        "TECH_PRISMA:prisma" \
        "PREP_IN:en|para|de|in|for|of"; do

        type="${entry%%:*}"
        pattern="${entry#*:}"
        matched=$(awk_match_prefix "$text" "$pattern")
        if [ -n "$matched" ]; then
            len=$(str_len "$matched")
            if [ "$len" -gt "$best_len" ]; then
                best_type="$type"
                best_lexeme="$matched"
                best_len="$len"
            fi
        fi
    done

    # ENTITY: cualquier palabra lowercase (solo si no hay keyword mas larga)
    matched=$(awk_match_prefix "$text" "[a-z][a-z]*")
    if [ -n "$matched" ]; then
        len=$(str_len "$matched")
        if [ "$len" -gt "$best_len" ]; then
            best_type="ENTITY"
            best_lexeme="$matched"
            best_len="$len"
        fi
    fi

    # SEPARATOR
    matched=$(awk_match_prefix "$text" "[,.;!?]")
    if [ -n "$matched" ]; then
        len=$(str_len "$matched")
        if [ "$len" -gt "$best_len" ]; then
            best_type="SEPARATOR"
            best_lexeme="$matched"
            best_len="$len"
        fi
    fi

    if [ "$best_len" -gt 0 ]; then
        echo "$best_type|$best_lexeme|$best_len"
        return 0
    fi
    return 1
}

# --- DFA principal (READ) ---
read_tokens() {
    input="$1"
    len=$(str_len "$input")
    pos=0
    col=1

    while [ "$pos" -lt "$len" ]; do
        rest=$(substr_from "$input" "$pos")

        # Saltar whitespace
        ws=$(awk_match_prefix "$rest" "[ \t]+")
        if [ -n "$ws" ]; then
            ws_len=$(str_len "$ws")
            pos=$((pos + ws_len))
            col=$((col + ws_len))
            continue
        fi

        if [ "$pos" -ge "$len" ]; then
            break
        fi

        result=$(match_token "$rest")
        if [ -n "$result" ]; then
            type="${result%%|*}"
            rest_result="${result#*|}"
            lexeme="${rest_result%%|*}"
            match_len="${rest_result##*|}"

            echo "{\"type\":\"$type\",\"lexeme\":\"$lexeme\",\"position\":{\"line\":1,\"col\":$col}}"
            pos=$((pos + match_len))
            col=$((col + match_len))
            log "OK: token $type \"$lexeme\" en col $col"
        else
            char=$(echo "$rest" | awk '{print substr($0, 1, 1)}')
            echo "Error lexico: token no reconocido en col $col: '$char'" >&2
            log "ERROR: token no reconocido en col $col: '$char'"
            pos=$((pos + 1))
            col=$((col + 1))
        fi
    done
}

# --- Main dispatch ---
main() {
    text="$*"

    if [ -z "$text" ]; then
        exit 0
    fi

    read_tokens "$text"
}

main "$@"
