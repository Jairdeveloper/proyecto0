---
id: 046
area: dev
type: prop
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - prop
  - tier
  - provider
  - free
  - paid
  - architecture
  - llm
  - routing
summary: "Propuesta de arquitectura por capas (free/paid) para el RECPL Compiler Bot. Define un proveedor de costo cero como capa gratuita y mantiene los proveedores comerciales como capa de pago, con un dispatcher inteligente que elige automaticamente segun disponibilidad y preferencia del usuario."
keywords:
  - propuesta
  - tier
  - capa-gratuita
  - capa-de-pago
  - provider
  - llm
  - dispatcher
  - recpl
  - apifreellm
  - claude
  - openai
changelog:
  - version: 1.0
    date: 2026-06-12
    author: workflow-agent
    description: Propuesta de arquitectura free/paid para providers LLM — dispatcher multi-provider, registry de proveedores, fallback chain, 0 cambios en adapters existentes
---
# Propuesta: Arquitectura de Capas Free/Paid para Providers LLM

> **Archivos nuevos:** `compiler-bot/providers/provider_registry.sh`
> **Modificar:** `compiler-bot/frontend/llm_classifier.sh`, `compiler-bot/frontend/router.sh`
> **Archivo existente:** `compiler-bot/providers/apifreellm.sh` (propuesto en 045_PROP)
> **Sin cambios:** `claude.sh`, `openai.sh`, `provider_common.sh`

---

## 0. Resumen Ejecutivo

El RECPL Compiler Bot tiene actualmente un unico nivel de LLM: el
usuario selecciona un proveedor via `RECPL_LLM_PROVIDER` (claude/openai)
y todas las llamadas LLM van a ese proveedor, con costo por token.

Se propone una **arquitectura por capas** que separa los proveedores
en dos niveles:

| Capa | Costo | Proveedores | Tool calling | Rate limit |
|------|-------|-------------|--------------|------------|
| **Free** | $0 | apifreellm (+ futuros: Ollama, HuggingFace free) | No (parseo heuristico) | Variable (20s apifreellm) |
| **Paid** | Por token | Claude, OpenAI (+ futuros: Gemini, Groq) | Si (nativo) | Ilimitado (segun plan) |

El sistema **intenta primero la capa gratuita** y, si falla o no
esta disponible, **asciende automaticamente a la capa de pago**.
El usuario puede forzar una capa especifica, bloquear la de pago
(coste cero garantizado) o dejarlo en automatico.

**Impacto en el codigo existente:** ~0 lineas modificadas en los
adapters de proveedor. Los cambios se concentran en el dispatcher
(`llm_classifier.sh`) y el router.

---

## 1. Analisis del Estado Actual

### 1.1 Arquitectura Actual

```
recpl.sh
  │
  └─ router.sh  (RECPL_LLM_MODE = auto|llm|deterministic)
       │
       ├─ deterministic pipeline  (preprocessor → lexer → parser → semantic → IR)
       │
       └─ llm_classifier.sh  (RECPL_LLM_PROVIDER = claude|openai)
              │
              ├─ claude.sh   → API Anthropic (costo por token)
              └─ openai.sh   → API OpenAI (costo por token)
```

**Problemas detectados:**

1. **Sin capa gratuita:** Toda llamada LLM tiene costo. No hay opcion
   de "probar gratis" antes de pagar.
2. **Sin fallback automatico:** Si el proveedor seleccionado falla
   (API key invalida, outage, rate limit), no hay reintento con otro
   proveedor.
3. **Sin registro de proveedores:** La lista de proveedores esta
   hardcodeada en un `case` dentro de `llm_classifier.sh`.
4. **Sin metadatos de proveedor:** No hay forma de consultar que
   proveedor soporta tool calling, cual es su rate limit, o a que
   capa pertenece.
5. **Crecimiento no escalable:** Agregar un nuevo proveedor requiere
   modificar 3 archivos (el adapter, el classifier, y el help/usage).

### 1.2 Flujo Actual de Decisión

```
¿RECPL_LLM_MODE?
  ├─ deterministic  → solo pipeline deterministico (gratis pero limitado)
  ├─ llm            → solo LLM (un unico proveedor, siempre con costo)
  └─ auto           → intenta deterministico, fallback a LLM (un proveedor)
```

Solo hay dos caminos: deterministico (vocabulario limitado a ~20
palabras) o LLM (costo por token). **No hay estado intermedio.**

---

## 2. Arquitectura Propuesta

### 2.1 Vista General

```
recpl.sh
  │
  ├─ RECPL_LLM_TIER = free | paid | auto
  │
  └─ router.sh  (RECPL_LLM_MODE = auto|llm|deterministic)
       │
       ├─ deterministic pipeline  (gratis, sin cambios)
       │
       └─ llm_classifier.sh  (NUEVO: dispatcher multi-provider)
              │
              ├─ [FREE TIER]  ─── apifreellm.sh  (intento 1)
              │                       │ fallback si:
              │                       │   • HTTP 429 (rate limit)
              │                       │   • timeout
              │                       │   • API key no configurada
              │                       ▼
              ├─ [PAID TIER]  ─── claude.sh  (intento 2)
              │                       │ fallback si:
              │                       │   • HTTP 401/403/429/500
              │                       │   • timeout
              │                       │   • API key no configurada
              │                       ▼
              └─ [PAID TIER]  ─── openai.sh  (intento 3)
                                      │ fallback final:
                                      │   • error al usuario
```

### 2.2 Las Tres Capas Logicas

```
┌────────────────────────────────────────────────────────────┐
│                      CAPA 0: DETERMINISTIC                 │
│  pipeline completo sin LLM. Sin API key, sin red, sin      │
│  costo. Vocabulario limitado (~20 palabras clave).         │
│  Tiempo: ~0.25s.                                           │
│                                                            │
│  Modos: RECPL_LLM_MODE=deterministic                       │
│         RECPL_LLM_TIER=cualquiera (no afecta)              │
├────────────────────────────────────────────────────────────┤
│                      CAPA 1: FREE LLM                      │
│  LLM via API gratuita (apifreellm, futuro: Ollama local,   │
│  HuggingFace Inference). Sin costo monetario. Rate limits  │
│  variables. Sin tool calling nativo (parseo heuristico).   │
│                                                            │
│  Variable: RECPL_LLM_TIER=free                             │
│  Providers: apifreellm                                     │
├────────────────────────────────────────────────────────────┤
│                      CAPA 2: PAID LLM                      │
│  LLM via API comercial (Claude, OpenAI, futuro: Gemini,    │
│  Groq). Costo por token. Tool calling nativo. Sin rate     │
│  limits significativos.                                    │
│                                                            │
│  Variable: RECPL_LLM_TIER=paid                             │
│  Providers: claude, openai                                 │
└────────────────────────────────────────────────────────────┘
```

### 2.3 Modos de Operacion

| `RECPL_LLM_TIER` | `RECPL_LLM_MODE` | Comportamiento |
|-------------------|-------------------|----------------|
| `auto` (default) | `auto` | deterministico → free LLM → paid LLM |
| `auto` | `llm` | free LLM → paid LLM |
| `auto` | `deterministic` | solo deterministico (ignora LLM) |
| `free` | `auto` o `llm` | deterministico → free LLM solo. Nunca paga. |
| `free` | `deterministic` | solo deterministico |
| `paid` | `auto` o `llm` | deterministico → paid LLM solo. Nunca usa free. |
| `paid` | `deterministic` | solo deterministico |

**Comportamiento en `auto`/`auto` (default recomendado):**

```
1. Intentar pipeline deterministico (costo $0, tiempo ~0.25s)
   ├─ Si exito → devolver respuesta
   └─ Si falla → pasar a paso 2

2. Intentar free LLM (costo $0, tiempo ~5-30s)
   ├─ Si exito → devolver respuesta
   ├─ Si rate limit (HTTP 429) → informar al usuario, pasar a paso 3
   └─ Si error → pasar a paso 3

3. Intentar paid LLM (costo ~$0.003-0.005, tiempo ~1-3s)
   ├─ Si exito → devolver respuesta
   └─ Si error → "No se pudo procesar con ninguna capa"
```

---

## 3. Componentes del Diseno

### 3.1 Provider Registry (NUEVO)

Archivo: `compiler-bot/providers/provider_registry.sh`

```sh
# ============================================================================
# provider_registry.sh - Registro de proveedores LLM
# ============================================================================
#
# PROPOSITO:
#   Mantiene un registro centralizado de todos los proveedores LLM
#   disponibles, con sus metadatos (capa, capacidades, script).
#   Permite consultar proveedores por capa y obtener su orden de
#   prioridad.
#
# USO:
#   . ./providers/provider_registry.sh
#   get_providers_by_tier free    → "apifreellm"
#   get_providers_by_tier paid    → "claude openai"
#   get_providers_by_tier auto    → "apifreellm claude openai"
# ============================================================================

# --- Formato por proveedor: "nombre:script_relativo:capa:tool_calling:rate_limit_seg:descripcion"
#   nombre         = identificador del provider (ej: claude)
#   script_relativo = ruta desde SCRIPT_DIR/../providers/
#   capa           = free | paid
#   tool_calling   = yes | no
#   rate_limit_seg = 0 (sin limite) | numero (segundos entre requests)
#   descripcion    = texto corto para help/usage
PROVIDER_REGISTRY='claude:claude.sh:paid:yes:0:Anthropic Claude Sonnet (costo por token)
openai:openai.sh:paid:yes:0:OpenAI GPT-4o (costo por token)
apifreellm:apifreellm.sh:free:no:20:apifreellm.com (gratuito, 200B+ params)'

# --- Obtener proveedores por capa ---
# Uso: get_providers_by_tier <tier>
#   tier = free | paid | auto
# Output: lista de nombres separados por espacio
get_providers_by_tier() {
    _tier="$1"
    _result=""

    OLD_IFS="$IFS"; IFS='
'
    for _entry in $PROVIDER_REGISTRY; do
        _name=$(echo "$_entry" | cut -d: -f1)
        _capa=$(echo "$_entry" | cut -d: -f3)

        case "$_tier" in
            free)
                [ "$_capa" = "free" ] && _result="${_result} ${_name}"
                ;;
            paid)
                [ "$_capa" = "paid" ] && _result="${_result} ${_name}"
                ;;
            auto)
                _result="${_result} ${_name}"
                ;;
        esac
    done
    IFS="$OLD_IFS"

    echo "$_result" | sed 's/^ //'
}

# --- Obtener metadata de un proveedor ---
# Uso: get_provider_meta <nombre> <campo>
#   campo = script | tier | tool_calling | rate_limit | desc
get_provider_meta() {
    _name="$1"
    _field="$2"
    _col=0

    case "$_field" in
        script)       _col=2 ;;
        tier)         _col=3 ;;
        tool_calling) _col=4 ;;
        rate_limit)   _col=5 ;;
        desc)         _col=6 ;;
        *)            echo ""; return 1 ;;
    esac

    OLD_IFS="$IFS"; IFS='
'
    for _entry in $PROVIDER_REGISTRY; do
        _entry_name=$(echo "$_entry" | cut -d: -f1)
        if [ "$_entry_name" = "$_name" ]; then
            echo "$_entry" | cut -d: -f"$_col"
            IFS="$OLD_IFS"
            return 0
        fi
    done
    IFS="$OLD_IFS"
    echo ""
    return 1
}

# --- Listar todos los proveedores (para help) ---
list_all_providers() {
    echo "$PROVIDER_REGISTRY" | while IFS=: read -r name script tier tool rate desc; do
        echo "  $name  ($tier)  $desc"
    done
}
```

**Ventajas de este diseno:**
- Un solo lugar para registrar proveedores
- Metadata estructurada y consultable
- Agregar un nuevo proveedor = 1 linea en PROVIDER_REGISTRY + 1 adapter
- Sin cambios en el dispatcher para agregar providers

### 3.2 Dispatcher Multi-Provider (MODIFICAR llm_classifier.sh)

El `llm_classifier.sh` actual (170 lineas) se refactoriza para:

1. Cargar `provider_registry.sh` al inicio
2. Obtener la lista de proveedores segun `RECPL_LLM_TIER`
3. Iterar sobre la lista, intentando cada proveedor
4. En cada intento: cargar el adapter, llamar al provider, verificar
   exito
5. Si un proveedor falla, pasar al siguiente
6. Si todos fallan, devolver error

**Cambios concretos en `llm_classifier.sh`:**

```sh
# === MODIFICACIONES ===

# Al inicio, cargar registry
SCRIPT_DIR="$(dirname "$0")"
. "$SCRIPT_DIR/../providers/provider_common.sh"
. "$SCRIPT_DIR/../providers/provider_registry.sh"  # NUEVO

# --- Determinar lista de proveedores a intentar ---
get_provider_list() {
    _tier="${RECPL_LLM_TIER:-auto}"

    # Si el usuario especifico un proveedor explicitamente, usarlo
    if [ -n "${RECPL_LLM_PROVIDER:-}" ]; then
        echo "$RECPL_LLM_PROVIDER"
        return
    fi

    # Obtener lista segun tier
    get_providers_by_tier "$_tier"
}

# --- Intentar un proveedor ---
try_provider() {
    _provider="$1"
    _instruction="$2"

    _script=$(get_provider_meta "$_provider" "script")
    [ -z "$_script" ] && return 1

    # Cargar adapter
    . "$SCRIPT_DIR/../providers/$_script" 2>/dev/null || return 1

    # Llamar al provider (convencion: <nombre>_complete)
    _response=$("${_provider}_complete" "$(get_system_prompt)" "$_instruction" "$(get_tools_json)" 2>/dev/null)
    _exit_code=$?

    if [ $_exit_code -ne 0 ] || [ -z "$_response" ]; then
        return 1
    fi

    echo "$_response"
    return 0
}

# --- Fachada principal (MODIFICADA) ---
llm_classify() {
    instruction="$1"

    if [ -z "$instruction" ]; then
        echo "{\"accion\":\"error\",\"mensaje\":\"Instruccion vacia\"}"
        return 1
    fi

    # Obtener lista de proveedores a intentar
    provider_list=$(get_provider_list)
    [ -z "$provider_list" ] && {
        echo "{\"accion\":\"error\",\"mensaje\":\"No hay proveedores LLM disponibles para el tier configurado\"}"
        return 1
    }

    # Intentar cada proveedor en orden
    _last_error=""
    for _provider in $provider_list; do
        response=$(try_provider "$_provider" "$instruction")
        if [ $? -eq 0 ] && [ -n "$response" ]; then
            # Parsear respuesta: tool_use o text
            response_type=$(echo "$response" | jq -r '.type // "text"')

            if [ "$response_type" = "tool_use" ]; then
                tool_name=$(echo "$response" | jq -r '.tool')
                params=$(echo "$response" | jq -r '.parameters')
                map_tool_to_ir "$tool_name" "$params"
                return 0
            else
                content=$(echo "$response" | jq -r '.content // ""')
                echo "{\"accion\":\"respond\",\"mensaje\":$(printf '%s' "$content" | jq -R -s .)}"
                return 0
            fi
        fi
        _last_error="All providers failed for instruction: $instruction"
    done

    echo "{\"accion\":\"error\",\"mensaje\":\"$_last_error\"}"
    return 1
}
```

**Comportamiento del dispatcher:**

| Escenario | Proveedores intentados | Resultado |
|-----------|----------------------|-----------|
| `RECPL_LLM_TIER=free`, `apifreellm` configurado | apifreellm | Respuesta free o error |
| `RECPL_LLM_TIER=free`, `apifreellm` no configurado | (ninguno) | "No hay proveedores free" |
| `RECPL_LLM_TIER=paid`, Claude configurado | claude | Respuesta Claude |
| `RECPL_LLM_TIER=paid`, Claude falla, OpenAI configurado | claude → openai | Respuesta OpenAI (fallback) |
| `RECPL_LLM_TIER=auto`, todos configurados | apifreellm → claude → openai | Respuesta del primero que funciona |
| `RECPL_LLM_TIER=auto`, solo Claude configurado | apifreellm (falla) → claude | Respuesta Claude |
| `RECPL_LLM_PROVIDER=claude` (explicito) | claude | Solo Claude (compatibilidad hacia atras) |

### 3.3 Router Modificado

El `router.sh` actualmente pasa `RECPL_LLM_PROVIDER` al `llm_classifier.sh`.
Se agrega `RECPL_LLM_TIER` al entorno:

```sh
# En router.sh, donde llama a llm_classifier.sh:
result=$(RECPL_LLM_TIER="${RECPL_LLM_TIER:-auto}" \
    RECPL_LLM_PROVIDER="${RECPL_LLM_PROVIDER:-}" \
    "$SCRIPT_DIR/llm_classifier.sh" 2>/dev/null <<LLM_INPUT
$instruction
LLM_INPUT
)
```

### 3.4 Interfaz de Usuario

**Nuevo flag en `recpl.sh`:**

```
--tier free|paid|auto    Selecciona la capa de LLM (default: auto)
                         free  = solo proveedores gratuitos (sin costo)
                         paid  = solo proveedores de pago (costo por token)
                         auto  = intenta free, luego paid
```

**Nueva variable de entorno:**

```
  RECPL_LLM_TIER         free|paid|auto (default: auto)
```

**Nuevo comando en modo interactivo:**

```
> tier free
> tier paid
> tier auto
```

### 3.5 Orden de la Fallback Chain

```
deterministic ──exito──→ OK
     │ falla
     ▼
free LLM ──exito──→ OK
     │ falla (rate limit, timeout, sin API key)
     ▼
paid LLM ──exito──→ OK
     │ falla (todos los proveedores)
     ▼
"Error: No se pudo procesar la instruccion con ninguna capa"
```

El dispatcher implementa **fail-fast**: si un proveedor falla
claramente (API key no configurada), pasa al siguiente sin esperar
timeout. Si falla por timeout, espera el tiempo configurado antes
de pasar al siguiente.

---

## 4. Plan de Implementacion

### 4.1 Fases

| Fase | Descripcion | Archivos | Estimacion |
|------|-------------|----------|------------|
| 1 | Crear `provider_registry.sh` con 3 proveedores registrados | `providers/provider_registry.sh` | 20 min |
| 2 | Refactorizar `llm_classifier.sh`: agregar dispatcher multi-provider, mantener compatibilidad hacia atras | `frontend/llm_classifier.sh` | 40 min |
| 3 | Implementar `apifreellm.sh` (adapter free, como propuesta 045) | `providers/apifreellm.sh` | 45 min |
| 4 | Modificar `router.sh` para pasar `RECPL_LLM_TIER` | `frontend/router.sh` | 5 min |
| 5 | Agregar flag `--tier` en `recpl.sh` + comando interactivo | `recpl.sh` | 15 min |
| 6 | Probar las 7 combinaciones de tier × mode | Manual | 20 min |
| 7 | Actualizar help, runbook, y documentacion | `docs/` | 15 min |
| **Total** | | | **~2.5 horas** |

### 4.2 Pruebas

```sh
# 1. Modo auto/auto (default): debe intentar free primero
RECPL_LLM_TIER=auto RECPL_LLM_MODE=auto \
  APIFREELLM_API_KEY="<key>" \
  ANTHROPIC_API_KEY="<key>" \
  ./pipeline_debugger.sh --inspect synthesis "crea modulo pagos en nestjs"

# 2. Modo free: solo apifreellm, nunca paga
RECPL_LLM_TIER=free \
  APIFREELLM_API_KEY="<key>" \
  ./pipeline_debugger.sh --inspect synthesis "crea modulo pagos en nestjs"

# 3. Modo free sin API key: debe fallar con mensaje claro
RECPL_LLM_TIER=free \
  ./pipeline_debugger.sh --inspect synthesis "crea modulo pagos en nestjs"

# 4. Modo paid: solo claude/openai
RECPL_LLM_TIER=paid \
  ANTHROPIC_API_KEY="<key>" \
  ./pipeline_debugger.sh --inspect synthesis "crea modulo pagos en nestjs"

# 5. Modo auto con fallback: apifreellm falla → claude
RECPL_LLM_TIER=auto \
  APIFREELLM_API_KEY="invalida" \
  ANTHROPIC_API_KEY="<key>" \
  ./pipeline_debugger.sh --inspect synthesis "crea modulo pagos en nestjs"

# 6. Modo auto con provider explicito (compatibilidad hacia atras)
RECPL_LLM_PROVIDER=claude \
  ANTHROPIC_API_KEY="<key>" \
  ./pipeline_debugger.sh --inspect synthesis "crea modulo pagos en nestjs"

# 7. Tier por flag
./recpl.sh --tier free -c "crea modulo pagos en nestjs"
```

---

## 5. Matriz de Decision: Estrategias Evaluadas

Se evaluaron 3 estrategias antes de elegir la propuesta:

### Estrategia A: Provider Registry + Dispatcher (SELECCIONADA)

| Aspecto | Evaluacion |
|---------|------------|
| Complejidad | Media. ~100 lineas nuevas, ~30 modificadas |
| Cambio en adapters | **0 lineas** — los adapters existentes no se tocan |
| Cambio en llm_classifier | Refactor del dispatch (case → loop) |
| Escalabilidad | Alta — agregar provider = 1 linea en registry + 1 adapter |
| Fallback chain | Automatica, configurable por tier |
| Compatibilidad | Total — `RECPL_LLM_PROVIDER` explicito saltea el tier |

### Estrategia B: Router Jerarquico (DESCARTADA)

Consiste en anidar el router: un "router de capa" que decide qué
router (free/paid) usar.

| Aspecto | Evaluacion |
|---------|------------|
| Complejidad | Alta. Duplica logica de ruteo. |
| Cambio en adapters | 0 |
| Escalabilidad | Media. Agregar capa requiere nuevo sub-router. |
| **Problema** | El router deterministico y el LLM son conceptualmente diferentes; mezclar capas a ese nivel confunde responsabilidades. |

### Estrategia C: Envoltorio de shell (wrapper script) (DESCARTADA)

Un script `llm_dispatcher.sh` que llama a `llm_classifier.sh` en un
loop con diferentes proveedores.

| Aspecto | Evaluacion |
|---------|------------|
| Complejidad | Baja. Script independiente. |
| Cambio en adapters | 0 |
| **Problema** | No puede compartir estado interno (system prompt, tools). Duplica logica de parseo. Mayor latencia por subprocesos. |

---

## 6. Migracion desde la Arquitectura Actual

La migracion es **100% backward compatible**:

| Situacion actual | Comportamiento post-migracion |
|------------------|------------------------------|
| `RECPL_LLM_PROVIDER=claude` (sin tier) | Usa solo Claude (igual que antes) |
| `RECPL_LLM_PROVIDER=openai` (sin tier) | Usa solo OpenAI (igual que antes) |
| `--llm` (sin tier) | Fuerza LLM con el provider por defecto (claude) |
| `RECPL_LLM_MODE=deterministic` | Solo deterministico (sin cambios) |
| Scripts que llaman a `llm_classifier.sh` directamente | Sin cambios — la interfaz `llm_classify()` no cambia |

**Unico cambio visible:** El usuario que configura `RECPL_LLM_TIER=auto`
notara que la primera respuesta LLM puede tardar mas (por el intento
fallido a apifreellm before hitting Claude). Solucion: en modo `auto`,
el dispatcher puede cachear el resultado del intento free para no
repetirlo en la misma sesion.

---

## 7. Proveedores Futuros (Post-MVP)

| Proveedor | Capa | Requisito | Tool calling | Notas |
|-----------|------|-----------|--------------|-------|
| Ollama (local) | free | Ollama instalado + modelo descargado | Si (via OpenAI-compatible) | Sin rate limit, sin costo, sin internet |
| HuggingFace Inference API | free | HF_TOKEN (opcional) | No | Rate limit variable, modelos 7B-70B |
| Groq | paid | GROQ_API_KEY | Si (OpenAI-compatible) | Muy rapido, modelos open-source |
| Google Gemini | paid | GEMINI_API_KEY | Si (SDK propio) | Precios competitivos, 1M contexto |
| DeepSeek | paid | DEEPSEEK_API_KEY | Si (OpenAI-compatible) | Muy economico, code-focused |

Cada uno se agrega con:
1. Crear `providers/<name>.sh` siguiendo el contrato del adapter
2. Agregar 1 linea en `PROVIDER_REGISTRY` en `provider_registry.sh`

---

## 8. Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigacion |
|--------|---------|------------|
| Free tier (apifreellm) es lento (20s rate limit) | Usuario espera 20s+ por respuesta | El dispatcher pasa rapido a paid si hay rate limit; el usuario puede forzar `tier=paid` |
| Parseo heuristico sin tool calling nativo produce respuestas inconsistentes | El LLM free no sigue el formato JSON | Fallback a texto plano; el usuario ve la respuesta raw en vez de un IR estructurado |
| Usuario cree que "free" significa "sin API key" | Confusion | Doc clara: "free = sin costo monetario, pero requiere API key gratuita de apifreellm" |
| Multiples fallbacks encubren errores reales | El usuario no sabe que proveedor fallo | Logging detallado: "Provider A fallo: reason. Intentando B..." |
| Registry crece y se vuelve dificil de mantener | Archivo grande | Cada provider es 1 linea. Si supera 20 proveedores, migrar a archivo externo `.providers` |

---

## 9. Referencias

- `compiler-bot/providers/claude.sh` — Adapter Claude (paid, sin cambios)
- `compiler-bot/providers/openai.sh` — Adapter OpenAI (paid, sin cambios)
- `compiler-bot/providers/apifreellm.sh` — Adapter apifreellm (free, propuesto en 045_PROP)
- `compiler-bot/providers/provider_common.sh` — Utilidades compartidas (sin cambios)
- `compiler-bot/frontend/llm_classifier.sh` — Dispatcher a modificar
- `compiler-bot/frontend/router.sh` — Router a modificar (pasar tier)
- `compiler-bot/recpl.sh` — Flags y env vars
- `docs/045_PROP_DEV_COMPILER_BOT_PROVIDER_APIFREELLM_1_0_DRAFT.md` — Propuesta del adapter apifreellm
- `docs/006_PROP_DEV_COMPILER_BOT_1_0_DRAFT.md` — Propuesta original del compilador
- `docs/030_REP_MGT_COMPILER_BOT_LLM_INTEGRATION_1_0_DRAFT.md` — Reporte de integracion LLM con costos
