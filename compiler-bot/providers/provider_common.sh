# ============================================================================
# provider_common.sh - Utilidades compartidas para adapters de LLM
# ============================================================================
#
# PROPOSITO:
#   Funciones compartidas entre todos los adapters de proveedores LLM.
#   Incluye validacion de dependencias (curl, jq) y formateo de
#   respuestas al formato interno comun.
#
# USO:
#   . ./providers/provider_common.sh
#
# DEPENDENCIAS:
#   Ninguna (shell puro)
#
# VARIABLES DE ENTORNO:
#   RECPL_LLM_TIMEOUT    (opcional, default 30s)
#   RECPL_LLM_MAX_TOKENS (opcional, default 1024)
# ============================================================================

# --- Constants ---
RECPL_LLM_TIMEOUT="${RECPL_LLM_TIMEOUT:-30}"
RECPL_LLM_MAX_TOKENS="${RECPL_LLM_MAX_TOKENS:-1024}"

# ============================================================================
# SECTION: Validacion de dependencias
# ============================================================================

# --- Verificar que curl esta disponible ---
check_curl() {
    if ! command -v curl >/dev/null 2>&1; then
        echo "Error: curl no esta instalado" >&2
        return 1
    fi
}

# --- Verificar que jq esta disponible ---
check_jq() {
    if ! command -v jq >/dev/null 2>&1; then
        echo "Error: jq no esta instalado" >&2
        return 1
    fi
}

# ============================================================================
# SECTION: Formateo de respuestas
# ============================================================================

# --- Formatear tool call al formato interno comun ---
# Uso: format_tool_response "scaffold_module" '{"nombre":"Pagos","tech":"NestJS"}'
# Output: {"type":"tool_use","tool":"scaffold_module","parameters":{...}}
format_tool_response() {
    tool_name="$1"
    tool_input="$2"

    echo "{ \"type\": \"tool_use\", \"tool\": \"$tool_name\", \"parameters\": $tool_input }"
}

# --- Formatear respuesta textual al formato interno comun ---
# Uso: format_text_response "Hola, soy el compilador"
# Output: {"type":"text","content":"Hola, soy el compilador"}
format_text_response() {
    content="$1"

    echo "{ \"type\": \"text\", \"content\": $(echo "$content" | jq -R -s .) }"
}
