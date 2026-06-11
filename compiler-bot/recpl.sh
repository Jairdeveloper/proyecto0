#!/bin/sh
# ============================================================================
# recpl.sh - READ-EVAL-PRINT-LOOP principal del bot RECPL
# ============================================================================
#
# PROPOSITO:
#   Bucle principal que conecta el pipeline compilador completo:
#   READ (lexer) → EVAL (parser + semantico) → PRINT (synthesis)
#
# USO:
#   ./recpl.sh           # modo interactivo
#   echo "texto" | ./recpl.sh  # modo batch (una instruccion)
#
# COMANDOS ESPECIALES:
#   quit, salir, exit    → termina el bucle
#   Ctrl+D               → termina el bucle
# ============================================================================

# --- Constants ---
SCRIPT_NAME="recpl.sh"
LOG_FILE="${LOG_FILE:-/tmp/recpl_loop.log}"
RECPL_STATE_DIR="/tmp/recpl_state_$$"
VERSION="1.1.0"

SCRIPT_DIR="$(dirname "$0")"

# --- Logging ---
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# --- Inicializar estado persistente ---
init_state() {
    mkdir -p "$RECPL_STATE_DIR"
    log "OK: estado inicializado en $RECPL_STATE_DIR"
}

# --- Limpiar estado al salir ---
cleanup() {
    rm -rf "$RECPL_STATE_DIR"
    log "OK: estado limpiado"
}

# --- Mostrar version ---
show_version() {
    echo "RECPL Compiler Bot v${VERSION}"
    echo "Pipeline: preprocess → lexer → parser → semantic → IR → synthesis"
}

# --- Mostrar ayuda ---
show_help() {
    cat <<HELP
RECPL Compiler Bot v${VERSION}

Un bot que procesa lenguaje natural como un compilador (Aho, Dragon Book).

USO:
  ./recpl.sh                        # modo interactivo
  ./recpl.sh -c "instruccion"       # modo comando (una instruccion)
  ./recpl.sh --command "instruccion"
  ./recpl.sh -f archivo.txt         # modo archivo (lee instrucciones)
  ./recpl.sh --file archivo.txt
  echo "instruccion" | ./recpl.sh   # modo batch (stdin pipe)
  ./recpl.sh --help                 # esta ayuda
  ./recpl.sh --version              # version

EJEMPLOS:
  > crea un modulo de pagos en NestJS
  > listar usuarios
  > eliminar modulo payments
  > quit                           # salir

COMANDOS ESPECIALES:
  quit, salir, exit, q  → termina el bucle
  help                  → muestra esta ayuda

BANDERAS:
  -c, --command TEXTO  Ejecuta una instruccion y termina
  -f, --file ARCHIVO   Ejecuta las instrucciones del archivo y termina
  -h, --help           Muestra esta ayuda
  -v, --version        Muestra la version
HELP
}

# --- Procesar una instruccion ---
process_instruction() {
    raw_input="$1"

    # Preprocesar
    preprocessed=$(FRONTEND_DIR="$SCRIPT_DIR/frontend" "$SCRIPT_DIR/frontend/preprocessor.sh" "$raw_input" 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "$preprocessed" ]; then
        preprocessed="$raw_input"
    fi

    # Lexer
    tokens=$(FRONTEND_DIR="$SCRIPT_DIR/frontend" "$SCRIPT_DIR/frontend/lexer.sh" "$preprocessed" 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "$tokens" ]; then
        echo "{\"tipo_respuesta\":\"error\",\"mensaje\":\"Error lexico al procesar: $raw_input\",\"payload\":null}"
        return
    fi

    # Parser
    ast=$(echo "$tokens" | "$SCRIPT_DIR/frontend/parser.sh" 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "$ast" ]; then
        echo "{\"tipo_respuesta\":\"error\",\"mensaje\":\"Error sintactico al procesar: $raw_input\",\"payload\":null}"
        return
    fi

    # Semantic (with persistent state)
    validated=$(echo "$ast" | RECPL_STATE_DIR="$RECPL_STATE_DIR" "$SCRIPT_DIR/frontend/semantic.sh" 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "$validated" ]; then
        echo "{\"tipo_respuesta\":\"error\",\"mensaje\":\"Error semantico al procesar: $raw_input\",\"payload\":null}"
        return
    fi

    # IR generator
    ir=$(echo "$validated" | "$SCRIPT_DIR/middleend/ir_generator.sh" 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "$ir" ]; then
        echo "{\"tipo_respuesta\":\"error\",\"mensaje\":\"Error generando IR\",\"payload\":null}"
        return
    fi

    # Synthesis (PRINT)
    "$SCRIPT_DIR/backend/synthesis.sh" 2>/dev/null <<EOF
$ir
EOF
}

# --- Modo comando (-c) ---
command_mode() {
    instruction="$1"
    init_state
    process_instruction "$instruction"
    cleanup
}

# --- Modo archivo (-f) ---
file_mode() {
    filepath="$1"

    if [ ! -f "$filepath" ]; then
        echo "Error: archivo no encontrado: $filepath" >&2
        exit 1
    fi

    if [ ! -r "$filepath" ]; then
        echo "Error: archivo sin permisos de lectura: $filepath" >&2
        exit 1
    fi

    init_state

    while IFS= read -r line <&3; do
        [ -z "$line" ] && continue
        case "$line" in
            quit|salir|exit|q) break ;;
            *) process_instruction "$line" ;;
        esac
    done 3< "$filepath"

    cleanup
}

# --- Modo batch (stdin) ---
batch_mode() {
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        case "$line" in
            quit|salir|exit|q) break ;;
            help) show_help; break ;;
            *) process_instruction "$line" ;;
        esac
    done
    cleanup
}

# --- Modo interactivo ---
interactive_mode() {
    echo "RECPL Compiler Bot v${VERSION}"
    echo "Escribe 'quit' para salir."
    echo

    while true; do
        printf "> "
        if ! read -r input; then
            echo
            log "OK: EOF recibido, saliendo"
            break
        fi

        case "$input" in
            quit|salir|exit|q)
                log "OK: comando quit recibido"
                break
                ;;
            help)
                show_help
                continue
                ;;
            version|--version)
                show_version
                continue
                ;;
            "")
                continue
                ;;
        esac

        process_instruction "$input"
        echo
    done

    cleanup
}

# --- Main ---
main() {
    trap 'cleanup; exit 0' INT TERM

    # Parsear flags que consumen argumento
    case "${1:-}" in
        -c|--command)
            if [ -z "${2:-}" ]; then
                echo "Error: -c/--command requiere un argumento" >&2
                exit 1
            fi
            command_mode "$2"
            exit $?
            ;;
        -f|--file)
            if [ -z "${2:-}" ]; then
                echo "Error: -f/--file requiere un argumento" >&2
                exit 1
            fi
            file_mode "$2"
            exit $?
            ;;
    esac

    case "$1" in
        --help|-h)
            show_help
            exit 0
            ;;
        --version|-v)
            show_version
            exit 0
            ;;
    esac

    init_state

    if [ -t 0 ]; then
        # stdin es terminal → modo interactivo
        interactive_mode
    else
        # stdin es pipe/redireccion → modo batch
        batch_mode
    fi
}

main "$@"
