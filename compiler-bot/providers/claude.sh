# ============================================================================
# claude.sh - Adapter para Anthropic Claude Messages API
# ============================================================================
#
# PROPOSITO:
#   Traduce el formato interno comun de RECPL a la API de Claude y viceversa.
#   Implementa el patron Adapter: normaliza las diferencias de la API de
#   Anthropic a un formato interno comun.
#
# DEPENDENCIAS:
#   provider_common.sh, curl, jq
#
# VARIABLES DE ENTORNO:
#   ANTHROPIC_API_KEY   (requerida)
#   RECPL_LLM_TIMEOUT   (opcional, default 30s)
#   RECPL_LLM_MAX_TOKENS (opcional, default 1024)
# ============================================================================

API_URL="https://api.anthropic.com/v1/messages"
API_KEY="${ANTHROPIC_API_KEY:-}"

# ============================================================================
# SECTION: Llamada completa a Claude
# ============================================================================

# --- Enviar instruccion a Claude y obtener respuesta ---
# Uso: claude_complete "system prompt" "mensaje usuario" '[...tools json...]'
# Output: formato interno comun (tool_use o text)
claude_complete() {
    system="$1"
    message="$2"
    tools_json="$3"

    # Validar API key
    if [ -z "$API_KEY" ]; then
        echo "Error: ANTHROPIC_API_KEY no esta configurada" >&2
        return 1
    fi

    # Validar dependencias
    check_curl || return 1
    check_jq || return 1

    # Construir payload
    payload=$(cat <<EOF
{
  "model": "claude-sonnet-4-20250514",
  "max_tokens": $RECPL_LLM_MAX_TOKENS,
  "system": $(echo "$system" | jq -R -s .),
  "messages": [
    {"role": "user", "content": $(echo "$message" | jq -R -s .)}
  ],
  "tools": $tools_json
}
EOF
)

    # Llamar a la API
    response=$(curl -s -w "\n%{http_code}" \
        --max-time "$RECPL_LLM_TIMEOUT" \
        -X POST "$API_URL" \
        -H "x-api-key: $API_KEY" \
        -H "anthropic-version: 2023-06-01" \
        -H "content-type: application/json" \
        -d "$payload" 2>/dev/null)

    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" != "200" ]; then
        echo "Error: Claude API respondio con codigo $http_code" >&2
        echo "$body" >&2
        return 1
    fi

    # Extraer tool_use o text
    content_type=$(echo "$body" | jq -r '.content[0].type // "text"')

    if [ "$content_type" = "tool_use" ]; then
        tool_name=$(echo "$body" | jq -r '.content[0].name')
        tool_input=$(echo "$body" | jq -r '.content[0].input')
        format_tool_response "$tool_name" "$tool_input"
    else
        text=$(echo "$body" | jq -r '.content[0].text // ""')
        format_text_response "$text"
    fi
}
