#!/bin/sh
# ============================================================================
# agent.sh - Bucle principal del agente Proyecto0(RECPL)
# ============================================================================
#
# PROPOSITO:
#   Recibe una instruccion, clasifica la intencion, ejecuta la accion
#   correspondiente (RECPL via bridge, herramienta, o respuesta textual),
#   y devuelve el resultado formateado.
#
# USO:
#   ./agent.sh "instruccion"             # modo normal
#   ./agent.sh --llm "instruccion"       # fuerza LLM
#   ./agent.sh --deterministic "instruc" # solo RECPL deterministico
#   echo "instruccion" | ./agent.sh      # modo batch (stdin)
#
# VARIABLES DE ENTORNO:
#   AGENT_LLM_MODE      auto|llm|deterministic (default: auto)
#   AGENT_LLM_PROVIDER  claude|openai|apifreellm
#   AGENT_LLM_TIER      free|paid|auto
#   AGENT_MEMORY_DIR    directorio de memoria (default: /tmp/agent_memory)
# ============================================================================

# --- Cargar configuracion ---
SCRIPT_DIR="$(dirname "$0")"
. "$SCRIPT_DIR/config.sh"
. "$SCRIPT_DIR/memory.sh"

# --- Inicializar memoria ---
memory_init
memory_log "Agent started (v$AGENT_VERSION)"

# --- Banner ---
show_banner() {
    echo "${AGENT_PREFIX} Proyecto0(RECPL) v${AGENT_VERSION}"
    echo "   Un agente de codigo abierto para escribir y ejecutar codigo."
    echo ""
}

# --- Mostrar ayuda ---
show_help() {
    cat <<HELP
${AGENT_PREFIX} Proyecto0(RECPL) v${AGENT_VERSION}

USO:
  ./agent.sh "instruccion"                Modo normal
  ./agent.sh --llm "instruccion"          Fuerza uso de LLM
  ./agent.sh --deterministic "instruc"    Solo RECPL deterministico
  ./agent.sh --help                       Esta ayuda

MODOS (via AGENT_LLM_MODE):
  auto          Intenta RECPL deterministico, luego LLM si falla (default)
  llm           Usa LLM directamente
  deterministic Solo RECPL deterministico

EJEMPLOS:
  ./agent.sh "crea modulo pagos en nestjs"
  ./agent.sh "hola"
  ./agent.sh --llm "explica que es RECPL"
HELP
}

# --- Clasificar intencion (heuristica inicial, sin LLM) ---
# Fase 1: deteccion basica por palabras clave.
# Fase 3+: se reemplaza por planner.sh con LLM.
classify_intent() {
    _instruction="$1"

    # Normalizar a minusculas
    _lower=$(echo "$_instruction" | tr '[:upper:]' '[:lower:]')

    # Detectar saludo/pregunta personal
    echo "$_lower" | grep -qE '^(hola|buenas|hey|buenos dias|buenas tardes|quien eres|que eres)' && {
        echo "respond"
        return
    }

    # Detectar despedida
    echo "$_lower" | grep -qE '^(adios|chao|bye|hasta luego|nos vemos)' && {
        echo "respond"
        return
    }

    # Detectar agradecimiento
    echo "$_lower" | grep -qE '^(gracias|thanks|thank you)' && {
        echo "respond"
        return
    }

    # Detectar ayuda
    echo "$_lower" | grep -qE '^(ayuda|help|que puedes hacer)' && {
        echo "help"
        return
    }

    # --- Fase 2: herramientas del sistema (antes que RECPL por ser mas especificas) ---

    # Detectar escritura de archivos (antes que el "crea" generico de RECPL)
    echo "$_lower" | grep -qE '^(crea archivo|escribe|write|crea el archivo|genera archivo) ' && {
        echo "write_file"
        return
    }

    # Detectar lectura de archivos
    echo "$_lower" | grep -qE '^(lee|muestra|cat|abre|read) ' && {
        echo "read_file"
        return
    }

    # Detectar ejecucion de comandos
    echo "$_lower" | grep -qE '^(ejecuta|corre|run|executa|lanza) ' && {
        echo "run_command"
        return
    }

    # Detectar comando RECPL (palabras clave: crea, genera, elimina, lista, etc.)
    echo "$_lower" | grep -qE '^(crea|genera|elimina|borra|lista|muestra|actualiza|modifica|source|exec)' && {
        echo "recpl"
        return
    }

    # Si tiene palabras clave de accion en medio
    echo "$_lower" | grep -qE '(crea |genera |elimina |borra |lista |muestra )' && {
        echo "recpl"
        return
    }

    # Por defecto: intentar RECPL (puede fallar si no entiende)
    echo "recpl"
}

# --- Ejecutar accion segun intencion ---
execute_intent() {
    _intent="$1"
    _instruction="$2"

    case "$_intent" in
        respond)
            # Respuesta textual segun el tipo de saludo
            _lower=$(echo "$_instruction" | tr '[:upper:]' '[:lower:]')
            case "$_lower" in
                *"quien eres"*|*"que eres"*)
                    tool_respond "Soy Proyecto0(RECPL) v${AGENT_VERSION}, un agente de codigo abierto que te ayuda a escribir y ejecutar codigo con cualquier modelo de IA."
                    ;;
                *"gracias"*)
                    tool_respond "De nada! Estoy aqui para ayudarte con tu codigo."
                    ;;
                *"hola"*|*"buenas"*)
                    tool_respond "Hola! Soy Proyecto0(RECPL). En que puedo ayudarte? Puedes pedirme que cree modulos, lea archivos, ejecute comandos, o simplemente conversar."
                    ;;
                *"adios"*|*"chao"*|*"bye"*)
                    tool_respond "Hasta luego! Vuelve cuando necesites ayuda con tu codigo."
                    ;;
                *)
                    tool_respond "Hola! En que puedo ayudarte?"
                    ;;
            esac
            ;;

        help)
            show_help
            ;;

        read_file)
            . "$SCRIPT_DIR/tools/tool_read_file.sh"
            # Extraer ruta: remover "lee " o "muestra " o "cat " del inicio
            _path=$(echo "$_instruction" | sed 's/^\(lee\|muestra\|cat\|abre\|read\) //')
            tool_read_file "$_path"
            ;;

        write_file)
            . "$SCRIPT_DIR/tools/tool_write_file.sh"
            # Parseo basico: "crea archivo <ruta> con contenido <contenido>"
            _rest=$(echo "$_instruction" | sed 's/^\(crea archivo\|escribe\|write\|crea el archivo\|genera archivo\) //')
            _path=$(echo "$_rest" | sed 's/ con contenido.*//' | sed 's/ con texto.*//' | xargs)
            _content=$(echo "$_rest" | sed 's/^.* con contenido //' | sed 's/^.* con texto //')
            [ -z "$_content" ] && _content="$_rest"
            tool_write_file "$_path" "$_content"
            ;;

        run_command)
            . "$SCRIPT_DIR/tools/tool_run_command.sh"
            _cmd=$(echo "$_instruction" | sed 's/^\(ejecuta\|corre\|run\|executa\|lanza\) //')
            tool_run_command "$_cmd"
            ;;

        recpl)
            # Delegar en RECPL via bridge
            . "$SCRIPT_DIR/bridge.sh"
            bridge_recpl "$_instruction"
            ;;

        *)
            # Intento fallback: RECPL
            . "$SCRIPT_DIR/bridge.sh"
            bridge_recpl "$_instruction"
            ;;
    esac
}

# --- Formatear respuesta para el usuario ---
# Maneja distintos tipos de respuesta: mensaje textual, contenido de archivo,
# salida de comando, escritura de archivo.
format_response() {
    _json="$1"

    _exito=$(printf '%s' "$_json" | jq -r '.exito // false' 2>/dev/null)
    _tipo=$(printf '%s' "$_json" | jq -r '.tipo_respuesta // "text"' 2>/dev/null)

    case "$_tipo" in
        file_content)
            _path=$(printf '%s' "$_json" | jq -r '.path // ""' 2>/dev/null)
            _lines=$(printf '%s' "$_json" | jq -r '.lineas // 0' 2>/dev/null)
            _content=$(printf '%s' "$_json" | jq -r '.contenido // ""' 2>/dev/null)
            printf '✅ %s (%s lineas)\n' "$_path" "$_lines"
            [ -n "$_content" ] && printf '%s\n' "$_content"
            ;;
        command_output)
            _output=$(printf '%s' "$_json" | jq -r '.output // ""' 2>/dev/null)
            printf '✅ %s\n' "$(printf '%s' "$_output" | head -5)"
            ;;
        file_written)
            _mensaje=$(printf '%s' "$_json" | jq -r '.mensaje // ""' 2>/dev/null)
            printf '✅ %s\n' "$_mensaje"
            ;;
        *)
            _mensaje=$(printf '%s' "$_json" | jq -r '.mensaje // ""' 2>/dev/null)
            if [ "$_exito" = "true" ]; then
                printf '✅ %s\n' "$_mensaje"
            else
                printf '❌ %s\n' "$_mensaje"
            fi
            ;;
    esac
}

# --- MAIN ---
main() {
    _mode="${AGENT_LLM_MODE:-auto}"
    _instruction=""

    # Parsear argumentos
    while [ $# -gt 0 ]; do
        case "$1" in
            --llm|--llm-only)
                _mode="llm"
                shift
                ;;
            --deterministic|--deterministic-only)
                _mode="deterministic"
                shift
                ;;
            -h|--help)
                show_banner
                show_help
                return 0
                ;;
            -v|--version)
                echo "Proyecto0(RECPL) v${AGENT_VERSION}"
                return 0
                ;;
            --)
                shift
                break
                ;;
            -*)
                echo "Error: opcion desconocida: $1"
                echo "Usa --help para ver las opciones disponibles."
                return 1
                ;;
            *)
                break
                ;;
        esac
    done

    _instruction="$*"

    # Si no hay instruccion en args, leer de stdin
    if [ -z "$_instruction" ]; then
        read -r _instruction || true
    fi

    if [ -z "$_instruction" ]; then
        show_banner
        echo "No se recibio ninguna instruccion."
        echo "Uso: echo \"instruccion\" | ./agent.sh"
        echo "     ./agent.sh \"instruccion\""
        return 1
    fi

    memory_log "RECV: $_instruction"

    # Mostrar banner en primera interaccion
    show_banner

    # Clasificar intencion
    _intent=$(classify_intent "$_instruction")
    memory_log "INTENT: $_intent"

    # Ejecutar (usando archivo temporal para evitar bug de dash + $() + jq)
    _result_file="/tmp/agent_result_$$.tmp"
    execute_intent "$_intent" "$_instruction" > "$_result_file"
    _exit_code=$?

    # Formatear y mostrar
    format_response "$(cat "$_result_file")"
    memory_log "RESP: $(cat "$_result_file" | jq -c '.' 2>/dev/null || cat "$_result_file")"

    # Guardar en historial
    memory_add_history "$_instruction" "$(cat "$_result_file")"
    rm -f "$_result_file"

    return $_exit_code
}

# --- Entrypoint ---
main "$@"
