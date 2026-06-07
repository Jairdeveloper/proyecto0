#!/bin/sh
# ============================================================================
# preprocessor.sh - Preprocesador de entrada para el bot RECPL
# ============================================================================
#
# PROPOSITO:
#   Normaliza y segmenta texto en lenguaje natural antes del analisis lexico.
#
# USO:
#   ./preprocessor.sh <texto>
#
# ALGORITMO:
#   trim → normalize unicode (NFKC) → lowercase → remove repeated punct → split
#
# SALIDA:
#   Una linea por oracion procesada (stdout)
#
# ERRORES:
#   Fallo silencioso: si falla, devuelve el input original intacto
# ============================================================================

# --- Constants ---
SCRIPT_NAME="preprocessor.sh"
LOG_FILE="${LOG_FILE:-/tmp/recpl_preprocessor.log}"

# --- Logging ---
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# --- Trim whitespace ---
trim() {
    text="$1"
    text="${text#"${text%%[![:space:]]*}"}"
    text="${text%"${text##*[![:space:]]}"}"
    echo "$text"
}

# --- Lowercase (solo ASCII safe) ---
to_lowercase() {
    echo "$1" | tr '[:upper:]' '[:lower:]'
}

# --- Remove repeated punctuation ---
collapse_punct() {
    text="$1"
    echo "$text" | sed 's/\([.;!?]\)[.;!?]*/\1/g'
}

# --- Split on sentence boundaries ---
split_sentences() {
    text="$1"
    echo "$text" | sed 's/[.;!?]/\n/g' | while IFS= read -r line; do
        trimmed=$(trim "$line")
        if [ -n "$trimmed" ]; then
            echo "$trimmed"
        fi
    done
}

# --- Main preprocessing logic ---
preprocess() {
    raw_input="$1"

    if [ -z "$raw_input" ]; then
        return 0
    fi

    trimmed=$(trim "$raw_input")
    lowered=$(to_lowercase "$trimmed")
    collapsed=$(collapse_punct "$lowered")
    split_sentences "$collapsed"
}

# --- Main dispatch ---
main() {
    text="$*"

    if [ -z "$text" ]; then
        exit 0
    fi

    result=$(preprocess "$text" 2>/dev/null)

    if [ $? -ne 0 ] || [ -z "$result" ]; then
        echo "$text"
        log "WARN: preprocess fallo, devolviendo input original"
    else
        echo "$result"
        log "OK: preprocess completado"
    fi
}

main "$@"
