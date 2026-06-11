# ============================================================================
# openai.sh - Adapter para OpenAI Chat Completions API
# ============================================================================
#
# PROPOSITO:
#   Traduce el formato interno comun de RECPL a la API de OpenAI y viceversa.
#   Implementa el patron Adapter: normaliza las diferencias de la API de
#   OpenAI a un formato interno comun.
#
# DEPENDENCIAS:
#   provider_common.sh, curl, jq
#
# VARIABLES DE ENTORNO:
#   OPENAI_API_KEY      (requerida)
#   RECPL_LLM_TIMEOUT   (opcional, default 30s)
#   RECPL_LLM_MAX_TOKENS (opcional, default 1024)
# ============================================================================

API_URL="https://api.openai.com/v1/chat/completions"
API_KEY="${OPENAI_API_KEY:-}"

# ============================================================================
# SECTION: Llamada completa a OpenAI
# ============================================================================

# --- Enviar instruccion a OpenAI y obtener respuesta ---
# Uso: openai_complete "system prompt" "mensaje usuario" '[...tools json...]'
# Output: formato interno comun (tool_use o text)
openai_complete() {
    system="$1"
    message="$2"
    tools_json="$3"

    # Validar API key
    if [ -z "$API_KEY" ]; then
        echo "Error: OPENAI_API_KEY no esta configurada" >&2
        return 1
    fi

    # Validar dependencias
    check_curl || return 1
    check_jq || return 1

    # Construir payload: OpenAI pone system en messages[]
    payload=$(cat <<EOF
{
  "model": "gpt-4o",
  "max_tokens": $RECPL_LLM_MAX_TOKENS,
  "messages": [
    {"role": "system", "content": $(echo "$system" | jq -R -s .)},
    {"role": "user", "content": $(echo "$message" | jq -R -s .)}
  ],
  "tools": $tools_json,
  "tool_choice": "auto"
}
EOF
)

    # Llamar a la API
    response=$(curl -s -w "\n%{http_code}" \
        --max-time "$RECPL_LLM_TIMEOUT" \
        -X POST "$API_URL" \
        -H "Authorization: Bearer $API_KEY" \
        -H "content-type: application/json" \
        -d "$payload" 2>/dev/null)

    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" != "200" ]; then
        echo "Error: OpenAI API respondio con codigo $http_code" >&2
        echo "$body" >&2
        return 1
    fi

    # Extraer tool_calls o content
    tool_calls=$(echo "$body" | jq -r '.choices[0].message.tool_calls')
    content=$(echo "$body" | jq -r '.choices[0].message.content // ""')

    if [ "$tool_calls" != "null" ] && [ -n "$tool_calls" ]; then
        tool_name=$(echo "$tool_calls" | jq -r '.[0].function.name')
        tool_input=$(echo "$tool_calls" | jq -r '.[0].function.arguments')
        format_tool_response "$tool_name" "$tool_input"
    elif [ -n "$content" ] && [ "$content" != "null" ]; then
        format_text_response "$content"
    else
        echo "Error: respuesta inesperada de OpenAI" >&2
        return 1
    fi
}
