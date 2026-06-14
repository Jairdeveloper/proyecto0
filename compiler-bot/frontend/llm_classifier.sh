# ============================================================================
# llm_classifier.sh - Fachada LLM para el RECPL Compiler Bot
# ============================================================================
#
# PROPOSITO:
#   Toma una instruccion en lenguaje natural, la envia a un LLM
#   (Claude/OpenAI), y devuelve un IR.json canonico o una respuesta
#   textual. Implementa el patron Facade: oculta la complejidad de
#   los proveedores, el formateo de payloads y el parseo de
#   respuestas.
#
# USO:
#   llm_classify "instruccion del usuario"
#   → IR.json (para synthesis) o {"accion":"respond",...}
#
# DEPENDENCIAS:
#   providers/provider_common.sh
#   providers/claude.sh
#   providers/openai.sh
#
# VARIABLES DE ENTORNO:
#   RECPL_LLM_PROVIDER  (claude|openai, default: claude)
#   ANTHROPIC_API_KEY   (si provider=claude)
#   OPENAI_API_KEY      (si provider=openai)
# ============================================================================

SCRIPT_DIR="$(dirname "$0")"

# --- Cargar providers ---
. "$SCRIPT_DIR/../providers/provider_common.sh"

# ============================================================================
# SECTION: System prompt del compilador
# ============================================================================

# --- Prompt que define el rol del LLM como compilador RECPL ---
# Si RECPL_LLM_SYSTEM_PROMPT esta definido, usarlo; si no, el default
get_system_prompt() {
    if [ -n "${RECPL_LLM_SYSTEM_PROMPT:-}" ]; then
        printf '%s\n' "$RECPL_LLM_SYSTEM_PROMPT"
        return
    fi
    cat <<'SYSTEM'
Eres un compilador de lenguaje natural a codigo (RECPL).
Traduces instrucciones del usuario en acciones del compilador.

REGLAS:
- Si el usuario pide crear/generar/hacer/necesito: usa scaffold_module o scaffold_entity
- Si el usuario pide eliminar/borrar: usa delete_module
- Si el usuario pide mostrar/listar: usa read_module
- Si la instruccion es ambigua: usa clarify para preguntar
- Si el usuario saluda o pregunta algo general: usa respond

TECHS SOPORTADAS: NestJS, Prisma, Express, FastAPI
SOLO USA TECHS de la lista soportada.

FORMATO DE SALIDA: Tool call con parametros exactos.
NO inventes tools que no esten en la lista.
SYSTEM
}

# ============================================================================
# SECTION: Tools del compilador (function calling schema)
# ============================================================================

# --- Schema de tools que el LLM puede invocar ---
get_tools_json() {
    # Si se sobreescribe el system prompt, no enviar tools por defecto
    if [ -n "${RECPL_LLM_SYSTEM_PROMPT:-}" ]; then
        echo '[]'
        return
    fi
    cat <<'TOOLS'
[
  {"name":"scaffold_module","description":"Crea un modulo nuevo en la tecnologia especificada","parameters":{"type":"object","properties":{"nombre":{"type":"string","description":"Nombre del modulo"},"tech":{"type":"string","description":"Tecnologia (NestJS, Prisma, Express, FastAPI)"}},"required":["nombre","tech"]}},
  {"name":"scaffold_entity","description":"Crea una entidad nueva","parameters":{"type":"object","properties":{"nombre":{"type":"string","description":"Nombre de la entidad"},"tech":{"type":"string","description":"Tecnologia"}},"required":["nombre","tech"]}},
  {"name":"delete_module","description":"Elimina un modulo existente","parameters":{"type":"object","properties":{"nombre":{"type":"string","description":"Nombre del modulo a eliminar"}},"required":["nombre"]}},
  {"name":"read_module","description":"Muestra informacion de un modulo existente","parameters":{"type":"object","properties":{"nombre":{"type":"string","description":"Nombre del modulo a consultar"}},"required":["nombre"]}},
  {"name":"clarify","description":"Pregunta al usuario cuando la instruccion es ambigua o falta informacion","parameters":{"type":"object","properties":{"pregunta":{"type":"string","description":"Pregunta clara para el usuario"}},"required":["pregunta"]}},
  {"name":"respond","description":"Responde texto directamente al usuario (saludos, informacion general, ayuda)","parameters":{"type":"object","properties":{"mensaje":{"type":"string","description":"Mensaje de respuesta"}},"required":["mensaje"]}}
]
TOOLS
}

# ============================================================================
# SECTION: Mapeo de tool calls a IR.json
# ============================================================================

# --- Convertir tool call del LLM a IR.json canonico ---
map_tool_to_ir() {
    tool_name="$1"
    params="$2"

    case "$tool_name" in
        scaffold_module)
            nombre=$(echo "$params" | jq -r '.nombre // ""')
            tech=$(echo "$params" | jq -r '.tech // ""')
            echo "{\"accion\":\"scaffold\",\"tipo\":\"module\",\"nombre\":$(printf '%s' "$nombre" | jq -R -s .),\"tech\":$(printf '%s' "$tech" | jq -R -s .)}"
            ;;
        scaffold_entity)
            nombre=$(echo "$params" | jq -r '.nombre // ""')
            tech=$(echo "$params" | jq -r '.tech // ""')
            echo "{\"accion\":\"scaffold\",\"tipo\":\"entity\",\"nombre\":$(printf '%s' "$nombre" | jq -R -s .),\"tech\":$(printf '%s' "$tech" | jq -R -s .)}"
            ;;
        delete_module)
            nombre=$(echo "$params" | jq -r '.nombre // ""')
            echo "{\"accion\":\"delete\",\"tipo\":\"module\",\"nombre\":$(printf '%s' "$nombre" | jq -R -s .)}"
            ;;
        read_module)
            nombre=$(echo "$params" | jq -r '.nombre // ""')
            echo "{\"accion\":\"read\",\"tipo\":\"module\",\"nombre\":$(printf '%s' "$nombre" | jq -R -s .)}"
            ;;
        clarify)
            pregunta=$(echo "$params" | jq -r '.pregunta // ""')
            echo "{\"accion\":\"clarify\",\"mensaje\":$(printf '%s' "$pregunta" | jq -R -s .)}"
            ;;
        respond)
            mensaje=$(echo "$params" | jq -r '.mensaje // ""')
            echo "{\"accion\":\"respond\",\"mensaje\":$(printf '%s' "$mensaje" | jq -R -s .)}"
            ;;
        *)
            echo "{\"accion\":\"error\",\"mensaje\":\"Tool desconocida: $tool_name\"}"
            return 1
            ;;
    esac
}

# ============================================================================
# SECTION: Fachada principal
# ============================================================================

# --- Clasificar instruccion via LLM y devolver IR.json o respuesta textual ---
llm_classify() {
    instruction="$1"
    provider="${RECPL_LLM_PROVIDER:-claude}"

    if [ -z "$instruction" ]; then
        echo "{\"accion\":\"error\",\"mensaje\":\"Instruccion vacia\"}"
        return 1
    fi

    # Cargar adapter del proveedor y ejecutar
    case "$provider" in
        claude)
            . "$SCRIPT_DIR/../providers/claude.sh" 2>/dev/null || {
                echo "{\"accion\":\"error\",\"mensaje\":\"No se pudo cargar provider claude\"}"
                return 1
            }
            response=$(claude_complete "$(get_system_prompt)" "$instruction" "$(get_tools_json)")
            ;;
        openai)
            . "$SCRIPT_DIR/../providers/openai.sh" 2>/dev/null || {
                echo "{\"accion\":\"error\",\"mensaje\":\"No se pudo cargar provider openai\"}"
                return 1
            }
            response=$(openai_complete "$(get_system_prompt)" "$instruction" "$(get_tools_json)")
            ;;
        *)
            echo "{\"accion\":\"error\",\"mensaje\":\"Provider no soportado: $provider. Usa claude o openai\"}"
            return 1
            ;;
    esac

    if [ $? -ne 0 ] || [ -z "$response" ]; then
        echo "{\"accion\":\"error\",\"mensaje\":\"Error en la comunicacion con el LLM\"}"
        return 1
    fi

    # Parsear respuesta: tool_use o text
    response_type=$(echo "$response" | jq -r '.type // "text"')

    if [ "$response_type" = "tool_use" ]; then
        tool_name=$(echo "$response" | jq -r '.tool')
        params=$(echo "$response" | jq -r '.parameters')
        map_tool_to_ir "$tool_name" "$params"
    else
        content=$(echo "$response" | jq -r '.content // ""')
        echo "{\"accion\":\"respond\",\"mensaje\":$(printf '%s' "$content" | jq -R -s .)}"
    fi
}

# ============================================================================
# SECTION: Entry point (standalone)
# ============================================================================

# Cuando se ejecuta como script standalone (no sourced),
# router.sh le pasa la instruccion por stdin.
# Leer la primera linea y ejecutar llm_classify.
if echo "$0" | grep -q "llm_classifier.sh"; then
    read -r _input_line || true
    if [ -n "$_input_line" ]; then
        llm_classify "$_input_line"
    else
        echo "{\"accion\":\"error\",\"mensaje\":\"Instruccion vacia (stdin)\"}"
    fi
fi
