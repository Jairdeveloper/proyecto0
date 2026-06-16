---
id: 045
area: dev
type: PROP
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - prop
  - provider
  - llm
  - apifreellm
  - adapter
  - openai-compatible
summary: "Propuesta de implementacion del provider apifreellm.com para el RECPL Compiler Bot. Cubre el analisis de la API, diseno del adapter para tier gratuito y premium, y modificaciones necesarias en llm_classifier.sh."
keywords:
  - propuesta
  - provider
  - llm
  - apifreellm
  - adapter
  - free
  - premium
  - openai-compatible
  - recpl
changelog:
  - version: 1.0
    date: 2026-06-12
    author: workflow-agent
    description: Propuesta de provider apifreellm.com — analisis de API, diseno de adapter free/premium, integracion con llm_classifier.sh
---
# Propuesta: Provider apifreellm.com para RECPL Compiler Bot

> **Archivo nuevo:** `compiler-bot/providers/apifreellm.sh`
> **Modificar:** `compiler-bot/frontend/llm_classifier.sh`
> **Depende de:** `provider_common.sh`, `curl`, `jq`
> **Inspiracion:** `claude.sh`, `openai.sh` (patron Adapter)

---

## 0. Resumen Ejecutivo

Se propone implementar un adapter para [apifreellm.com](https://apifreellm.com/),
un proveedor LLM gratuito con modelos de 200B+ parametros. La API
tiene dos niveles:

| Tier | Costo | Rate limit | Contexto | Tool calling | API type |
|------|-------|------------|----------|-------------|----------|
| Free | $0 | 1 req/20s | 32k tokens | NO | Proprietaria |
| Premium | $20/mes | Ilimitado | 128k tokens | SI | OpenAI-compatible |

**Decision de diseno:** Implementar **dos estrategias** en un mismo
adapter, detectadas por la variable `APIFREELLM_TIER`:

1. **Free (`free`):** Modo texto plano. Embed del system prompt + tools
   dentro del mensaje. Sin tool calling real. Parseo heuristico de la
   respuesta para clasificarla como tool call o texto.

2. **Premium (`premium`):** OpenAI-compatible. Usa la misma logica de
   `openai.sh` pero apuntando al endpoint de apifreellm. Soporte
   completo de tool calling (function calling).

---

## 1. Analisis de la API

### 1.1 Documentacion oficial

| Aspecto | Free | Premium |
|---------|------|---------|
| Endpoint | `POST https://apifreellm.com/api/v1/chat` | OpenAI-compatible (endpoint por confirmar) |
| Auth | `Authorization: Bearer <API_KEY>` | `Authorization: Bearer <API_KEY>` |
| Request body | `{"message": "..."}` | `{"model":"...","messages":[...],"tools":[...]}` |
| Response | `{"success":true,"response":"...","tier":"free","features":{...}}` | OpenAI Chat Completions format |
| Rate limit | 1 request cada 20s | Ilimitado |
| Contexto | 32k tokens | 128k tokens |
| Function calling | NO (free tier no soporta) | SI (via OpenAI-compatible) |

### 1.2 Endpoint Free

**Request:**

```sh
curl -X POST "https://apifreellm.com/api/v1/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <API_KEY>" \
  -d '{"message": "Crea un modulo de pagos en NestJS"}'
```

**Response:**

```json
{
  "success": true,
  "response": "He creado el modulo Pagos en NestJS...",
  "tier": "free",
  "features": {
    "unlimited": true,
    "delaySeconds": 25,
    "priorityProcessing": false
  }
}
```

**Limitaciones detectadas:**

1. No hay campo `system` ni `role` — solo un mensaje plano.
2. No soporta tool/function calling en el tier gratuito.
3. Rate limit de 20s entre requests (verificado en la web).
4. Sin streaming (respuesta completa via POST).
5. Sin modo OpenAI-compatible en el tier gratuito.

### 1.3 Endpoint Premium

El tier premium ($20/mes) desbloquea un endpoint "OpenAI-compatible"
que permite usar el SDK oficial de OpenAI. Una vez activado, se puede
usar `openai.sh` existente cambiando `API_URL` y `API_KEY`.

---

## 2. Diseno del Adapter

### 2.1 Arquitectura

```
llm_classifier.sh
    │
    ├─ RECPL_LLM_PROVIDER=claude   → claude.sh
    ├─ RECPL_LLM_PROVIDER=openai   → openai.sh
    └─ RECPL_LLM_PROVIDER=apifreellm → apifreellm.sh
                                            │
                                    ┌───────┴────────┐
                                    │  APIFREELLM_TIER │
                                    │  =free | premium │
                                    └───────┬────────┘
                                            │
                        ┌───────────────────┴───────────────────┐
                        │ free                                  │ premium
                        ▼                                       ▼
              apifreellm_complete_free()           apifreellm_complete_premium()
                        │                                       │
                        │ Embed system+tools                    │ Reuse OpenAI
                        │ into message field                    │ compatible format
                        ▼                                       ▼
              POST /api/v1/chat                         POST /v1/chat/completions
```

### 2.2 Variables de Entorno

| Variable | Default | Descripcion |
|----------|---------|-------------|
| `APIFREELLM_API_KEY` | — | API key (requerida) |
| `APIFREELLM_TIER` | `free` | `free` o `premium` |
| `RECPL_LLM_TIMEOUT` | `30` | Timeout de curl en segundos |
| `RECPL_LLM_MAX_TOKENS` | `1024` | Max tokens en premium (free no soporta) |

### 2.3 Logica del Adapter

```sh
# ============================================================================
# apifreellm.sh - Adapter para apifreellm.com API
# ============================================================================

API_URL_FREE="https://apifreellm.com/api/v1/chat"
API_URL_PREMIUM=""  # Por determinar (endpoint OpenAI-compatible)
API_KEY="${APIFREELLM_API_KEY:-}"
TIER="${APIFREELLM_TIER:-free}"

# --- Enviar instruccion a apifreellm y obtener respuesta ---
apifreellm_complete() {
    system="$1"
    message="$2"
    tools_json="$3"

    # Validar API key
    if [ -z "$API_KEY" ]; then
        echo "Error: APIFREELLM_API_KEY no esta configurada" >&2
        return 1
    fi

    # Validar dependencias
    check_curl || return 1
    check_jq || return 1

    case "$TIER" in
        free)    apifreellm_complete_free "$system" "$message" "$tools_json" ;;
        premium) apifreellm_complete_premium "$system" "$message" "$tools_json" ;;
        *)
            echo "Error: APIFREELLM_TIER no valido: $TIER (usar free o premium)" >&2
            return 1
            ;;
    esac
}
```

### 2.4 Modo Free (texto plano)

**Estrategia:** El system prompt y los tools se concatenan al mensaje
del usuario en un solo campo `message`. El LLM responde texto plano;
el adapter parsea heuristicamente la respuesta para clasificarla como
tool call o texto.

**Funcion:**

```sh
# --- Modo free: embed system prompt + tools en el mensaje ---
apifreellm_complete_free() {
    system="$1"
    message="$2"
    tools_json="$3"

    # Construir un mensaje compuesto que incluye system prompt y tools
    composite_message="$system"
    composite_message="${composite_message}\n\nTOOLS DISPONIBLES:\n$tools_json"
    composite_message="${composite_message}\n\nINSTRUCCION DEL USUARIO:\n$message"
    composite_message="${composite_message}\n\nRESPONDE SOLO CON JSON: {\"tool\":\"...\",\"parameters\":{...}} o {\"text\":\"...\"}"

    # Construir payload
    payload=$(cat <<EOF
{
  "message": $(printf '%s' "$composite_message" | jq -R -s .)
}
EOF
)

    # Llamar a la API
    response=$(curl -s -w "\n%{http_code}" \
        --max-time "$RECPL_LLM_TIMEOUT" \
        -X POST "$API_URL_FREE" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $API_KEY" \
        -d "$payload" 2>/dev/null)

    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | sed '$d')

    # Manejar rate limit (429)
    if [ "$http_code" = "429" ]; then
        echo "Error: Rate limit de apifreellm (1 request cada 20s)" >&2
        return 1
    fi

    if [ "$http_code" != "200" ]; then
        echo "Error: apifreellm API respondio con codigo $http_code" >&2
        echo "$body" >&2
        return 1
    fi

    # Verificar success field
    success=$(echo "$body" | jq -r '.success // false')
    if [ "$success" != "true" ]; then
        echo "Error: apifreellm respondio con success=false" >&2
        echo "$body" >&2
        return 1
    fi

    # Extraer respuesta textual
    response_text=$(echo "$body" | jq -r '.response // ""')

    if [ -z "$response_text" ]; then
        echo "Error: respuesta vacia de apifreellm" >&2
        return 1
    fi

    # Intentar parsear como JSON tool call
    maybe_json=$(echo "$response_text" | jq -e . 2>/dev/null) && {
        tool_name=$(echo "$maybe_json" | jq -r '.tool // ""')
        params=$(echo "$maybe_json" | jq -r '.parameters // ""')
        if [ -n "$tool_name" ] && [ -n "$params" ]; then
            format_tool_response "$tool_name" "$params"
            return 0
        fi
    }

    # Si el LLM uso formato tool directamente (respuesta raw)
    tool_match=$(echo "$response_text" | grep -o '"tool":"[^"]*"' | head -1 | cut -d'"' -f4)
    params_match=$(echo "$response_text" | grep -o '"parameters":{[^}]*}' | head -1)
    if [ -n "$tool_match" ] && [ -n "$params_match" ]; then
        format_tool_response "$tool_match" "$params_match"
        return 0
    fi

    # Fallback: respuesta textual
    format_text_response "$response_text"
}
```

**Heuristica de parseo:**

El LLM (modelo 200B+) es capaz de seguir instrucciones de formato.
Se le pide explicitamente en el composite_message que responda en
JSON. Si responde con JSON valido, se parsea directamente. Si no,
se usa grep para extraer patrones de tool call. Como ultimo recurso,
se trata como respuesta textual.

### 2.5 Modo Premium (OpenAI-compatible)

**Estrategia:** Reutilizar el formato de OpenAI. El endpoint
OpenAI-compatible de apifreellm acepta el mismo payload que OpenAI,
permitiendo usar `gpt-4o` como modelo placeholder.

**Funcion:**

```sh
# --- Modo premium: OpenAI-compatible ---
apifreellm_complete_premium() {
    system="$1"
    message="$2"
    tools_json="$3"

    # Construir payload OpenAI-compatible
    payload=$(cat <<EOF
{
  "model": "apifreellm",
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
        -X POST "$API_URL_PREMIUM" \
        -H "Authorization: Bearer $API_KEY" \
        -H "content-type: application/json" \
        -d "$payload" 2>/dev/null)

    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" != "200" ]; then
        echo "Error: apifreellm (premium) respondio con codigo $http_code" >&2
        echo "$body" >&2
        return 1
    fi

    # Parsear OpenAI-compatible response (misma logica que openai.sh)
    tool_calls=$(echo "$body" | jq -r '.choices[0].message.tool_calls')
    content=$(echo "$body" | jq -r '.choices[0].message.content // ""')

    if [ "$tool_calls" != "null" ] && [ -n "$tool_calls" ]; then
        tool_name=$(echo "$tool_calls" | jq -r '.[0].function.name')
        tool_input=$(echo "$tool_calls" | jq -r '.[0].function.arguments')
        format_tool_response "$tool_name" "$tool_input"
    elif [ -n "$content" ] && [ "$content" != "null" ]; then
        format_text_response "$content"
    else
        echo "Error: respuesta inesperada de apifreellm (premium)" >&2
        return 1
    fi
}
```

### 2.6 Manejo de Rate Limit (Free)

El tier free tiene un rate limit de 20s entre requests. El adapter:

1. Detecta HTTP 429 y muestra mensaje claro al usuario.
2. No implementa retry automatico (dado que el pipeline completo
   tarda ~0.25s, esperar 20s bloquearia el flujo).
3. Sugiere al usuario: esperar 20s, cambiar a premium, o usar
   pipeline deterministico.

```sh
if [ "$http_code" = "429" ]; then
    echo "Error: apifreellm rate limit (1 request cada 20s)." >&2
    echo "  Sugerencias:" >&2
    echo "  - Espera 20s y reintenta" >&2
    echo "  - Usa APIFREELLM_TIER=premium (sin rate limit)" >&2
    echo "  - Usa RECPL_LLM_MODE=deterministic (sin LLM)" >&2
    return 1
fi
```

---

## 3. Modificaciones a llm_classifier.sh

### 3.1 Nuevo branch en el case

```sh
apifreellm)
    . "$SCRIPT_DIR/../providers/apifreellm.sh" 2>/dev/null || {
        echo "{\"accion\":\"error\",\"mensaje\":\"No se pudo cargar provider apifreellm\"}"
        return 1
    }
    response=$(apifreellm_complete "$(get_system_prompt)" "$instruction" "$(get_tools_json)")
    ;;
```

### 3.2 Actualizar help/usage

En `recpl.sh` y donde corresponda, actualizar la lista de providers
soportados:

```
  RECPL_LLM_PROVIDER   claude|openai|apifreellm (default: claude)
```

### 3.3 Actualizar validacion

En `llm_classifier.sh`, el case `*)` actual:

```sh
echo "Provider no soportado: $provider. Usa claude o openai"
```

Cambiar a:

```sh
echo "Provider no soportado: $provider. Usa claude, openai o apifreellm"
```

---

## 4. Limitaciones Conocidas

### 4.1 Free Tier

| Limitacion | Impacto | Mitigacion |
|------------|---------|------------|
| Sin tool calling real | El LLM debe responder en JSON textual; el adapter parsea heuristicamente | System prompt instructivo + doble parseo (jq + grep) |
| Rate limit 20s | Una sola llamada LLM cada 20s | Mensaje claro al usuario + sugerencia de modo deterministico |
| Sin campo `system` | System prompt embed en `message` | Composite message funciona pero aumenta tokens |
| Sin control de `max_tokens` | Respuesta truncada a 32k contexto | No mitigable en free tier |
| Sin `model` selection | No se puede elegir modelo | La API usa default (200B+ params) |
| Sin OpenAI-compatible | No se puede usar SDK oficial | Solo via adapter HTTP directo |

### 4.2 Premium Tier

| Limitacion | Impacto | Mitigacion |
|------------|---------|------------|
| Costo $20/mes | No es gratuito | Usar free tier por defecto, premium como opcion |
| Endpoint desconocido | Requiere verificacion tras activar premium | Configurable via variable de entorno |
| Tool calling no verificado | Depende de la implementacion de apifreellm | Fallback a parseo heuristico igual que free |

---

## 5. Plan de Implementacion

| Fase | Descripcion | Estimacion |
|------|-------------|------------|
| 1 | Obtener API key de apifreellm.com (sign in with Google) | 5 min |
| 2 | Probar endpoint free manualmente con curl | 10 min |
| 3 | Crear `providers/apifreellm.sh` con modo free | 45 min |
| 4 | Implementar parseo heuristico de tool calls | 20 min |
| 5 | Agregar branch en `llm_classifier.sh` | 5 min |
| 6 | Probar integracion con `llm_classify()` | 15 min |
| 7 | Agregar manejo de rate limit (HTTP 429) | 10 min |
| 8 | Documentar en help y runbook | 15 min |
| 9 | (Opcional) Verificar modo premium con OpenAI-compatible | 30 min |
| **Total** | | **~2.5 horas** |

### 5.1 Pruebas propuestas

```sh
# 1. Probar modo free con instruccion simple
RECPL_LLM_PROVIDER=apifreellm \
  APIFREELLM_API_KEY="<key>" \
  ./pipeline_debugger.sh --inspect synthesis "crea modulo pagos en nestjs"

# 2. Probar rate limit (segunda llamada inmediata)
RECPL_LLM_PROVIDER=apifreellm \
  APIFREELLM_API_KEY="<key>" \
  ./pipeline_debugger.sh --inspect synthesis "crea modulo pagos"

# 3. Probar modo premium
RECPL_LLM_PROVIDER=apifreellm \
  APIFREELLM_TIER=premium \
  APIFREELLM_API_KEY="<key>" \
  ./pipeline_debugger.sh --inspect synthesis "crea modulo pagos en nestjs"

# 4. Probar error con API key invalida
RECPL_LLM_PROVIDER=apifreellm \
  APIFREELLM_API_KEY="invalida" \
  ./pipeline_debugger.sh --inspect synthesis "crea modulo pagos"
```

---

## 6. Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigacion |
|--------|---------|------------|
| API de apifreellm cambia sin aviso | Adapter deja de funcionar | Abstraccion via adapter; parche rapido en 1 funcion |
| Modelo 200B+ no sigue instrucciones de formato JSON | Parseo heuristico falla | Fallback a texto plano; el usuario ve la respuesta raw |
| Rate limit 20s frustra al usuario | Experiencia de usuario pobre | Mensaje claro con sugerencias; modo deterministico como alternativa |
| Premium tool calling no compatible realmente | Modo premium falla | Fallback a modo free con parseo heuristico |
| API key gratuita expira o se revoca | Provider deja de funcionar | Error claro: "APIFREELLM_API_KEY invalida o expirada" |

---

## 7. Referencias

- `https://apifreellm.com/en/api-access` — Documentacion oficial de la API
- `compiler-bot/providers/claude.sh` — Adapter existente (patron de referencia)
- `compiler-bot/providers/openai.sh` — Adapter existente (base para modo premium)
- `compiler-bot/providers/provider_common.sh` — Utilidades compartidas
- `compiler-bot/frontend/llm_classifier.sh` — Fachada LLM (modificar)
- `docs/006_PROP_DEV_COMPILER_BOT_1_0_DRAFT.md` — Propuesta original del compilador
- `docs/043_REP_DEV_COMPILER_BOT_PIPELINE_RE_1_0_DRAFT.md` — Ingenieria inversa del pipeline
