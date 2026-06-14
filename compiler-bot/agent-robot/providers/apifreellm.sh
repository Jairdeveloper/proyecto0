#!/bin/sh
# ============================================================================
# apifreellm.sh - Provider para API Free LLM
# ============================================================================
#
# PROPOSITO:
#   Proveedor LLM gratuito via API externa. Sigue el patron de provider
#   para ser usado por bridge.sh cuando AGENT_LLM_PROVIDER=apifreellm.
#
# USO:
#   . apifreellm.sh
#   apifreellm_call "prompt"
#   apifreellm_available && echo "disponible"
# ============================================================================

API_FREE_URL="${API_FREE_URL:-https://api.apifreellm.example.com/v1}"

# --- Llamar a API Free LLM ---
# Uso: apifreellm_call "prompt"
# Output: texto de respuesta
apifreellm_call() {
    _prompt="$1"
    _api_key="${API_FREE_KEY:-}"
    [ -z "$_api_key" ] && {
        echo '{"error":"API_FREE_KEY no configurada"}'
        return 1
    }

    _response=$(curl -s -w "\n%{http_code}" "$API_FREE_URL/chat/completions" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $_api_key" \
        -d "{\"model\":\"gpt-3.5-turbo\",\"messages\":[{\"role\":\"user\",\"content\":\"$_prompt\"}],\"temperature\":0.7}" 2>/dev/null)
    _http_code=$(echo "$_response" | tail -1)
    _body=$(echo "$_response" | sed '$d')

    if [ "$_http_code" != "200" ]; then
        echo "{\"error\":\"API Free LLM respondio con codigo $_http_code\"}"
        return 1
    fi

    echo "$_body" | jq -r '.choices[0].message.content // .error // "sin respuesta"' 2>/dev/null || echo "$_body"
}

# --- Verificar disponibilidad ---
apifreellm_available() {
    [ -n "${API_FREE_KEY:-}" ]
}
