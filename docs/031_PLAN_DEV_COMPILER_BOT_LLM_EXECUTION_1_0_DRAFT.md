---
id: 031
area: dev
type: plan
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - plan
  - execution
  - llm
  - claude
  - openai
  - router
  - provider-adapter
  - strategy-pattern
  - compiler-bot
  - recpl
summary: "Plan de ejecucion detallado para integrar LLMs (Claude, OpenAI) en el RECPL Compiler Bot. Describe la arquitectura de adapters por proveedor, el router inteligente, y el pipeline hibrido deterministico+LLM. Explica el funcionamiento de la integracion con patrones de diseno, y proporciona un plan de implementacion faseado, realizable y documentable."
keywords:
  - plan
  - ejecucion
  - llm
  - integracion
  - claude
  - openai
  - router
  - provider
  - adapter
  - strategy
  - patterns
  - pipeline
  - hibrido
  - implementacion
  - diseno
changelog:
  - version: 1.0
    date: 2026-06-11
    author: workflow-agent
    description: Plan de ejecucion para integracion LLM con patrones de diseno, basado en docs/030_REP_MGT_COMPILER_BOT_LLM_INTEGRATION
---

# Plan de Ejecucion: Integracion LLM en el RECPL Compiler Bot

> **Referencia:** `030_REP_MGT_COMPILER_BOT_LLM_INTEGRATION_1_0_DRAFT.md`
> **Patron composite:** `028_PROP_DEV_COMPILER_BOT_COMPOSITE_1_0_DRAFT.md`
> **Capa NLP previa:** `014_PROP_DEV_COMPILER_BOT_NLP_INTENT_1_0_DRAFT.md`
> **Guia de estilo:** `000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md`

---

## 0. Resumen Ejecutivo

Este plan describe como conectar el RECPL Compiler Bot con LLMs (Claude,
OpenAI, y potencialmente modelos locales) para que el bot entienda
instrucciones ambiguas, preguntas, y conversaciones multi-turno — cosas
que el pipeline deterministico (lexer → parser) no puede manejar.

**El problema:** El pipeline actual solo entiende instrucciones que
encajan exactamente en su gramatica BNF. Cualquier variacion — una
pregunta, una descripcion vaga, una referencia contextual — produce un
error lexico o sintactico.

**La solucion:** Un **router inteligente** que decide si enviar la
instruccion al pipeline deterministico (rapido, gratis, predecible) o al
LLM (flexible, contextual, con costo). Ambos caminos convergen en el
mismo IR.json y back-end de synthesis/scaffold.

**Por que es realizable:**
- Usa el mismo patron de pipeline modular que el proyecto ya tiene
- Los adapters son scripts shell que hacen llamadas curl
- El router es una funcion `case` de ~30 lineas
- No requiere modificar el back-end existente (synthesis, scaffold)
- Se implementa en 4 fases de 2-3 dias cada una

---

## 1. Como Funciona la Integracion (Explicacion Sencilla)

### 1.1 La idea central

En lugar de que el bot intente entender cada palabra con reglas fijas
(lexer), le preguntamos a un LLM que entienda la intencion. El LLM
recibe la instruccion del usuario y devuelve una accion estructurada:
"esto es un CREATE de modulo 'pagos' en NestJS".

```
ANTES (solo deterministico):
  "crea un modulo de pagos en NestJS"
    → lexer busca palabra por palabra
    → parser verifica gramatica
    → si no encaja: ERROR

DESPUES (hibrido):
  "necesito un sistema de pagos con stripe, que tenga auth"
    → router decide: esto es muy complejo para el lexer
    → se lo enviamos al LLM
    → LLM responde: "accion: CREATE, tipo: module, nombre: pagos, tech: [nestjs, stripe]"
    → eso se mapea al mismo IR.json
    → synthesis + scaffold funcionan igual que siempre
```

### 1.2 El LLM no piensa — solo clasifica

En esta arquitectura, el LLM no "piensa" ni "decide". Simplemente
**clasifica** la intencion del usuario y **extrae** parametros. Es como
un lexer + parser mucho mas flexible, pero que corre en una API externa.

El LLM recibe:
1. Un **system prompt** que le dice: "Eres un compilador. Tus tools son..."
2. La **instruccion del usuario**
3. Una lista de **tools** (funciones) que puede invocar

El LLM responde con:
- Una **tool call** (nombre de la tool + parametros) → se mapea a IR.json
- O **texto** (si el usuario pregunto algo general) → se muestra al usuario

### 1.3 Pipeline hibrido

```
INPUT: texto del usuario
    │
    ▼
┌──────────────────────┐
│    PREPROCESSOR      │  (existe hoy, normaliza texto)
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│       ROUTER         │  ← NUEVO: decide camino
│                      │
│  ┌────────────────┐  │
│  │ REGLAS         │  │
│  │ • Palabras     │  │
│  │   conocidas?   │  │
│  │ • Gramatica    │  │
│  │   simple?      │  │
│  │ • Flag --llm?  │  │
│  └────────┬───────┘  │
└───────────┼──────────┘
            │
     ┌──────┴──────┐
     ▼              ▼
┌──────────┐  ┌──────────┐
│ DETERMIN │  │    LLM   │
│ ISTICO   │  │          │
│ lexer →  │  │ adapter  │
│ parser → │  │ → tool   │
│ semantic │  │   call   │
│ → IR     │  │ → mapper │
└────┬─────┘  │ → IR     │
     │        └────┬─────┘
     └──────┬──────┘
            ▼
┌──────────────────────┐
│   IR.json (igual)    │  ← mismo formato, mismo back-end
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ SYNTHESIS + SCAFFOLD │  (sin cambios)
└──────────────────────┘
```

---

## 2. Patrones de Diseno Utilizados

### 2.1 Adapter Pattern (Proveedores)

Cada proveedor LLM (Claude, OpenAI, Ollama) tiene un adapter que
normaliza las diferencias de API a un formato interno comun.

```
┌──────────────┐
│   RECPL      │
│  (cliente)   │
└──────┬───────┘
       │ llama a
       ▼
┌──────────────────────────────┐
│     llm_complete()           │  ← interfaz unificada
│     (en llm_classifier.sh)   │
└──────┬───────────────────────┘
       │ delega a
       ├────────────────────────────────────┐
       ▼                                    ▼
┌──────────────────┐          ┌──────────────────────┐
│  providers/      │          │  providers/           │
│  claude.sh       │          │  openai.sh            │
│                  │          │                       │
│ POST /v1/        │          │ POST /v1/chat/        │
│ messages         │          │ completions           │
│ x-api-key        │          │ Authorization: Bearer │
│ tools: [{name,   │          │ tools: [{type:        │
│   input_schema}] │          │   function, ...}]     │
└──────────────────┘          └───────────────────────┘
       │                                    │
       └──────────────────┬─────────────────┘
                          ▼
              ┌──────────────────────┐
              │ FORMATO INTERNO COMUN │
              │ { type, tool, params }│
              └──────────────────────┘
```

**Beneficio:** Si Anthropic cambia su API, solo se modifica
`providers/claude.sh`. El resto del pipeline no se entera.

### 2.2 Strategy Pattern (Router)

El router implementa una estrategia de seleccion: deterministico vs LLM.
Se puede cambiar la estrategia en caliente via flag o variable de entorno.

```
router(instruccion)
    │
    ├── estrategia "deterministic-first"
    │   (por defecto)
    │
    ├── estrategia "llm-first"
    │   (flag --llm)
    │
    └── estrategia "llm-only"
        (flag --llm-only)
```

**Beneficio:** El usuario controla como se procesa su instruccion sin
cambiar la logica del pipeline.

### 2.3 Facade Pattern (LLM Classifier)

`llm_classifier.sh` es una **fachada** que oculta toda la complejidad
del LLM: seleccion de proveedor, construccion de payload, llamada HTTP,
parseo de respuesta, mapeo a IR.json.

```sh
# El pipeline solo ve esto:
llm_classifier "instruccion del usuario"
# → devuelve IR.json (igual que el pipeline deterministico)
```

**Beneficio:** El back-end (synthesis, scaffold) no sabe ni necesita
saber si la instruccion vino del pipeline deterministico o del LLM.

### 2.4 Chain of Responsibility (Pipeline)

Cada etapa del pipeline es un eslabon en una cadena. Cada eslabon
decide si procesa o pasa al siguiente. El router es el primer eslabon
que decide que cadena seguir.

```
preprocess → router → (deterministic-chain | llm-chain) → synthesis
```

**Beneficio:** Se pueden agregar nuevas etapas (ej: un validador
post-LLM) sin modificar las existentes.

### 2.5 Composite Pattern (Interactive Mode)

Tomado de `028_PROP_DEV_COMPILER_BOT_COMPOSITE`. El modo interactivo
puede invocar `source` (archivo), `exec` (inline), y ahora `--llm`
como comandos internos, compartiendo el estado.

---

## 3. Arquitectura Detallada

### 3.1 Arbol de archivos nuevo

```
compiler-bot/
├── frontend/
│   ├── preprocessor.sh      (sin cambios)
│   ├── lexer.sh             (sin cambios)
│   ├── parser.sh            (sin cambios)
│   ├── semantic.sh          (sin cambios)
│   └── router.sh            ← NUEVO
│
├── providers/               ← NUEVO: adapters por proveedor
│   ├── claude.sh
│   ├── openai.sh
│   ├── ollama.sh            (opcional, futura fase)
│   └── provider_common.sh   ← NUEVO: utilidades compartidas
│
├── frontend/
│   └── llm_classifier.sh    ← NUEVO: fachada LLM
│
├── middleend/
│   ├── ir_generator.sh      (sin cambios)
│   └── llm_ir_mapper.sh     ← NUEVO: mapea tool call → IR.json
│
├── backend/
│   ├── synthesis.sh         (sin cambios)
│   └── scaffold.sh          (sin cambios)
│
├── recpl.sh                 ← MODIFICADO: integra router
│
└── tests/
    ├── run_tests.sh         ← MODIFICADO: agrega tests LLM
    ├── test_router.sh       ← NUEVO
    └── test_llm.sh          ← NUEVO
```

### 3.2 Contrato de datos: formato interno comun

Toda comunicacion entre el pipeline y los LLM usa este formato JSON:

**Request (pipeline → adapter):**
```json
{
  "provider": "claude",
  "model": "claude-sonnet-4-20250514",
  "system": "Eres un compilador RECPL...",
  "messages": [
    {"role": "user", "content": "crea un modulo de pagos en NestJS"}
  ],
  "tools": [
    {
      "name": "scaffold_module",
      "description": "Genera un modulo NestJS/Prisma",
      "parameters": {
        "nombre": "string",
        "tech": "string"
      }
    }
  ],
  "max_tokens": 1024
}
```

**Response (adapter → pipeline):**
```json
{
  "type": "tool_use",
  "tool": "scaffold_module",
  "parameters": {
    "nombre": "Pagos",
    "tech": "NestJS"
  }
}
```

O si es respuesta textual:
```json
{
  "type": "text",
  "content": "Tienes 3 modulos: Pagos, Usuarios, Productos"
}
```

### 3.3 Catalogo de tools del compilador

Estas son las funciones que el LLM puede invocar. Cada una corresponde
a una accion del pipeline RECPL:

| Tool | Que hace | Parametros | Equivalente RECPL |
|------|----------|------------|-------------------|
| `scaffold_module` | Crea un modulo nuevo | nombre, tech | CREATE + MODULE |
| `scaffold_entity` | Crea una entidad | nombre, tech, campos | CREATE + ENTITY |
| `delete_module` | Elimina un modulo | nombre | DELETE |
| `read_module` | Muestra info de un modulo | nombre | READ |
| `clarify` | Pregunta algo al usuario | pregunta | Dialogo |
| `respond` | Responde texto directamente | mensaje | Chat |

### 3.4 System prompt del compilador LLM

El system prompt es la "guia de estilo" del LLM. Le dice como
comportarse:

```
Eres un compilador de lenguaje natural a codigo (RECPL).
Traduces instrucciones del usuario en acciones del compilador.

REGLAS:
- Si el usuario pide crear/generar/hacer/necesito: usa scaffold_module o scaffold_entity
- Si el usuario pide eliminar/borrar: usa delete_module
- Si el usuario pide mostrar/listar: usa read_module
- Si la instruccion es ambigua: usa clarify para preguntar
- Si el usuario saluda o pregunta algo general: usa respond

TECHS SOPORTADAS: NestJS, Prisma, Express, FastAPI
FORMATO DE SALIDA: Tool call con parametros exactos
```

---

## 4. Plan de Ejecucion por Fases

### FASE-L1: Adapters de Proveedor (2-3 dias)

**Objetivo:** Tener scripts que llamen a Claude y OpenAI, y devuelvan
el formato interno comun.

#### Paso L1.1 — Crear `providers/provider_common.sh`

**Archivo:** `compiler-bot/providers/provider_common.sh`

Funciones compartidas entre todos los adapters:

```sh
# ============================================================================
# provider_common.sh - Utilidades compartidas para adapters de LLM
# ============================================================================

# --- Constantes ---
RECPL_LLM_TIMEOUT="${RECPL_LLM_TIMEOUT:-30}"  # segundos
RECPL_LLM_MAX_TOKENS="${RECPL_LLM_MAX_TOKENS:-1024}"

# --- Validar que curl esta disponible ---
check_curl() {
    if ! command -v curl >/dev/null 2>&1; then
        echo "Error: curl no esta instalado" >&2
        return 1
    fi
}

# --- Validar que jq esta disponible ---
check_jq() {
    if ! command -v jq >/dev/null 2>&1; then
        echo "Error: jq no esta instalado" >&2
        return 1
    fi
}

# --- Formatear respuesta al formato interno comun ---
format_tool_response() {
    tool_name="$1"
    tool_input="$2"
    echo "{ \"type\": \"tool_use\", \"tool\": \"$tool_name\", \"parameters\": $tool_input }"
}

format_text_response() {
    content="$1"
    echo "{ \"type\": \"text\", \"content\": $(echo "$content" | jq -R -s .) }"
}
```

**Validacion:** `bash -n provider_common.sh` pasa sin errores

#### Paso L1.2 — Crear `providers/claude.sh`

**Archivo:** `compiler-bot/providers/claude.sh`

```sh
# ============================================================================
# claude.sh - Adapter para Anthropic Claude Messages API
# ============================================================================
#
# PROPOSITO:
#   Traduce el formato interno comun de RECPL a la API de Claude y viceversa.
#
# DEPENDENCIAS:
#   provider_common.sh, curl, jq
#
# VARIABLES DE ENTORNO:
#   ANTHROPIC_API_KEY  (requerida)
#   RECPL_LLM_TIMEOUT  (opcional, default 30s)
# ============================================================================

API_URL="https://api.anthropic.com/v1/messages"
API_KEY="${ANTHROPIC_API_KEY:-}"

# --- Llamada completa a Claude ---
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
        text=$(echo "$body" | jq -r '.content[0].text // .content[0].text')
        format_text_response "$text"
    fi
}
```

**Validacion:**
- `bash -n claude.sh` pasa
- Con ANTHROPIC_API_KEY configurada y conectividad:
  ```sh
  . ./providers/provider_common.sh
  . ./providers/claude.sh
  claude_complete "Eres un asistente" "Hola" "[]"
  # → {"type":"text","content":"..."}
  ```

#### Paso L1.3 — Crear `providers/openai.sh`

**Archivo:** `compiler-bot/providers/openai.sh`

Misma estructura que claude.sh pero con:
- URL: `https://api.openai.com/v1/chat/completions`
- Auth: `Authorization: Bearer $OPENAI_API_KEY`
- Formato de tools: `tools: [{type: "function", function: {name, parameters}}]`
- Extraccion: `.choices[0].message.tool_calls[0]`

```sh
# ============================================================================
# openai.sh - Adapter para OpenAI Chat Completions API
# ============================================================================

API_URL="https://api.openai.com/v1/chat/completions"
API_KEY="${OPENAI_API_KEY:-}"

openai_complete() {
    system="$1"
    message="$2"
    tools_json="$3"

    if [ -z "$API_KEY" ]; then
        echo "Error: OPENAI_API_KEY no esta configurada" >&2
        return 1
    fi

    check_curl || return 1
    check_jq || return 1

    # OpenAI pone system en messages[]
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
```

**Validacion:** misma que claude.sh pero con OPENAI_API_KEY

#### Checkpoint FASE-L1

- [ ] `bash -n providers/provider_common.sh` sin errores
- [ ] `bash -n providers/claude.sh` sin errores
- [ ] `bash -n providers/openai.sh` sin errores
- [ ] `shellcheck providers/*.sh` sin warnings (si disponible)
- [ ] Con API key: claude_complete devuelve JSON valido
- [ ] Con API key: openai_complete devuelve JSON valido
- [ ] Sin API key: mensaje de error claro

---

### FASE-L2: LLM Classifier (Fachada) + IR Mapper (2-3 dias)

**Objetivo:** Tener una fachada `llm_classifier.sh` que cualquier parte
del pipeline pueda llamar, y un mapper que convierta tool calls a
IR.json.

#### Paso L2.1 — Definir el system prompt del compilador

No es un archivo separado, sino una funcion en `llm_classifier.sh`:

```sh
get_system_prompt() {
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
Si el usuario pide una tech no soportada, usa clarify.

FORMATO DE SALIDA: Tool call con parametros exactos.
NO inventes tools que no esten en la lista.
SYSTEM
}
```

#### Paso L2.2 — Definir las tools del compilador

```sh
get_tools_json() {
    cat <<'TOOLS'
[
  {
    "name": "scaffold_module",
    "description": "Crea un modulo nuevo en la tecnologia especificada",
    "parameters": {
      "type": "object",
      "properties": {
        "nombre": {"type": "string", "description": "Nombre del modulo"},
        "tech": {"type": "string", "description": "Tecnologia (NestJS, Prisma, Express, FastAPI)"}
      },
      "required": ["nombre", "tech"]
    }
  },
  {
    "name": "scaffold_entity",
    "description": "Crea una entidad nueva",
    "parameters": {
      "type": "object",
      "properties": {
        "nombre": {"type": "string", "description": "Nombre de la entidad"},
        "tech": {"type": "string", "description": "Tecnologia"}
      },
      "required": ["nombre", "tech"]
    }
  },
  {
    "name": "delete_module",
    "description": "Elimina un modulo existente",
    "parameters": {
      "type": "object",
      "properties": {
        "nombre": {"type": "string", "description": "Nombre del modulo a eliminar"}
      },
      "required": ["nombre"]
    }
  },
  {
    "name": "read_module",
    "description": "Muestra informacion de un modulo existente",
    "parameters": {
      "type": "object",
      "properties": {
        "nombre": {"type": "string", "description": "Nombre del modulo a consultar"}
      },
      "required": ["nombre"]
    }
  },
  {
    "name": "clarify",
    "description": "Pregunta al usuario cuando la instruccion es ambigua o falta informacion",
    "parameters": {
      "type": "object",
      "properties": {
        "pregunta": {"type": "string", "description": "Pregunta clara para el usuario"}
      },
      "required": ["pregunta"]
    }
  },
  {
    "name": "respond",
    "description": "Responde texto directamente al usuario (saludos, informacion general, ayuda)",
    "parameters": {
      "type": "object",
      "properties": {
        "mensaje": {"type": "string", "description": "Mensaje de respuesta"}
      },
      "required": ["mensaje"]
    }
  }
]
TOOLS
}
```

#### Paso L2.3 — Crear `frontend/llm_classifier.sh`

**Archivo:** `compiler-bot/frontend/llm_classifier.sh`

```sh
# ============================================================================
# llm_classifier.sh - Fachada LLM para el RECPL Compiler Bot
# ============================================================================
#
# PROPOSITO:
#   Toma una instruccion en lenguaje natural, la envia a un LLM (Claude/OpenAI),
#   y devuelve un IR.json canonico o una respuesta textual.
#
#   Esta es la fachada (Facade Pattern) que oculta:
#     - Que proveedor LLM se usa
#     - Como se construye el payload
#     - Como se parsea la respuesta
#     - Como se mapea a IR.json
#
# USO:
#   llm_classify "instruccion del usuario"
#   → IR.json (para synthesis) o respuesta textual
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

# --- System prompt del compilador ---
get_system_prompt() {
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

# --- Tools del compilador ---
get_tools_json() {
    cat <<'TOOLS'
[
  {"name":"scaffold_module","description":"Crea un modulo nuevo","parameters":{"type":"object","properties":{"nombre":{"type":"string"},"tech":{"type":"string"}},"required":["nombre","tech"]}},
  {"name":"scaffold_entity","description":"Crea una entidad nueva","parameters":{"type":"object","properties":{"nombre":{"type":"string"},"tech":{"type":"string"}},"required":["nombre","tech"]}},
  {"name":"delete_module","description":"Elimina un modulo","parameters":{"type":"object","properties":{"nombre":{"type":"string"}},"required":["nombre"]}},
  {"name":"read_module","description":"Muestra info de un modulo","parameters":{"type":"object","properties":{"nombre":{"type":"string"}},"required":["nombre"]}},
  {"name":"clarify","description":"Pregunta al usuario cuando falta informacion","parameters":{"type":"object","properties":{"pregunta":{"type":"string"}},"required":["pregunta"]}},
  {"name":"respond","description":"Responde texto directamente","parameters":{"type":"object","properties":{"mensaje":{"type":"string"}},"required":["mensaje"]}}
]
TOOLS
}

# --- Mapear tool call a IR.json ---
map_tool_to_ir() {
    tool_name="$1"
    params="$2"

    case "$tool_name" in
        scaffold_module)
            echo "{\"accion\":\"scaffold\",\"tipo\":\"module\",\"nombre\":$(echo "$params" | jq -r .nombre | jq -R -s .),\"tech\":$(echo "$params" | jq -r .tech | jq -R -s .)}"
            ;;
        scaffold_entity)
            echo "{\"accion\":\"scaffold\",\"tipo\":\"entity\",\"nombre\":$(echo "$params" | jq -r .nombre | jq -R -s .),\"tech\":$(echo "$params" | jq -r .tech | jq -R -s .)}"
            ;;
        delete_module)
            echo "{\"accion\":\"delete\",\"tipo\":\"module\",\"nombre\":$(echo "$params" | jq -r .nombre | jq -R -s .)}"
            ;;
        read_module)
            echo "{\"accion\":\"read\",\"tipo\":\"module\",\"nombre\":$(echo "$params" | jq -r .nombre | jq -R -s .)}"
            ;;
        clarify)
            echo "{\"accion\":\"clarify\",\"mensaje\":$(echo "$params" | jq -r .pregunta | jq -R -s .)}"
            ;;
        respond)
            echo "{\"accion\":\"respond\",\"mensaje\":$(echo "$params" | jq -r .mensaje | jq -R -s .)}"
            ;;
        *)
            echo "{\"accion\":\"error\",\"mensaje\":\"Tool desconocida: $tool_name\"}"
            return 1
            ;;
    esac
}

# --- Fachada principal: clasificar instruccion via LLM ---
llm_classify() {
    instruction="$1"
    provider="${RECPL_LLM_PROVIDER:-claude}"

    if [ -z "$instruction" ]; then
        echo "{\"accion\":\"error\",\"mensaje\":\"Instruccion vacia\"}"
        return 1
    fi

    # Cargar adapter del proveedor
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

    # Parsear respuesta
    response_type=$(echo "$response" | jq -r '.type // "text"')

    if [ "$response_type" = "tool_use" ]; then
        tool_name=$(echo "$response" | jq -r '.tool')
        params=$(echo "$response" | jq -r '.parameters')
        map_tool_to_ir "$tool_name" "$params"
    else
        content=$(echo "$response" | jq -r '.content // ""')
        echo "{\"accion\":\"respond\",\"mensaje\":$(echo "$content" | jq -R -s .)}"
    fi
}
```

**Validacion:**
- `bash -n frontend/llm_classifier.sh` sin errores
- Con ANTHROPIC_API_KEY:
  ```sh
  . ./frontend/llm_classifier.sh
  llm_classify "crea un modulo de pagos en NestJS"
  # → {"accion":"scaffold","tipo":"module","nombre":"Pagos","tech":"NestJS"}
  ```

#### Paso L2.4 — Crear `middleend/llm_ir_mapper.sh`

**Archivo:** `compiler-bot/middleend/llm_ir_mapper.sh`

Mapper separado para que `ir_generator.sh` (deterministico) y
`llm_ir_mapper.sh` (LLM) produzcan el mismo formato.

```sh
# ============================================================================
# llm_ir_mapper.sh - Mapea tool call de LLM a IR.json canonico
# ============================================================================
#
# USO:
#   echo '{"tool":"scaffold_module","nombre":"Pagos","tech":"NestJS"}' \
#     | llm_ir_mapper.sh
#   → {"accion":"scaffold","tipo":"module","nombre":"Pagos","tech":"NestJS"}
# ============================================================================

llm_ir_mapper() {
    input=$(cat)

    tool=$(echo "$input" | jq -r '.tool')
    nombre=$(echo "$input" | jq -r '.nombre // ""')
    tech=$(echo "$input" | jq -r '.tech // ""')

    case "$tool" in
        scaffold_module)
            jq -n \
                --arg accion "scaffold" \
                --arg tipo "module" \
                --arg nombre "$nombre" \
                --arg tech "$tech" \
                '{accion: $accion, tipo: $tipo, nombre: $nombre, tech: $tech}'
            ;;
        scaffold_entity)
            jq -n \
                --arg accion "scaffold" \
                --arg tipo "entity" \
                --arg nombre "$nombre" \
                --arg tech "$tech" \
                '{accion: $accion, tipo: $tipo, nombre: $nombre, tech: $tech}'
            ;;
        delete_module)
            jq -n \
                --arg accion "delete" \
                --arg tipo "module" \
                --arg nombre "$nombre" \
                '{accion: $accion, tipo: $tipo, nombre: $nombre}'
            ;;
        read_module)
            jq -n \
                --arg accion "read" \
                --arg tipo "module" \
                --arg nombre "$nombre" \
                '{accion: $accion, tipo: $tipo, nombre: $nombre}'
            ;;
        clarify|respond)
            mensaje=$(echo "$input" | jq -r '.mensaje // .pregunta // ""')
            jq -n \
                --arg accion "$tool" \
                --arg mensaje "$mensaje" \
                '{accion: $accion, mensaje: $mensaje}'
            ;;
        *)
            echo "{\"accion\":\"error\",\"mensaje\":\"Tool desconocida: $tool\"}"
            return 1
            ;;
    esac
}

llm_ir_mapper
```

**Validacion:**
```sh
echo '{"tool":"scaffold_module","nombre":"Pagos","tech":"NestJS"}' \
  | compiler-bot/middleend/llm_ir_mapper.sh
# → {"accion":"scaffold","tipo":"module","nombre":"Pagos","tech":"NestJS"}
```

#### Checkpoint FASE-L2

- [ ] `bash -n frontend/llm_classifier.sh` sin errores
- [ ] `bash -n middleend/llm_ir_mapper.sh` sin errores
- [ ] `llm_classify` con instruccion simple devuelve IR.json valido
- [ ] `llm_classify` con pregunta devuelve `{"accion":"respond",...}`
- [ ] `llm_classify` con instruccion ambigua devuelve `{"accion":"clarify",...}`
- [ ] `llm_ir_mapper` mapea correctamente las 6 tools
- [ ] `shellcheck frontend/llm_classifier.sh` sin warnings

---

### FASE-L3: Router Inteligente (1-2 dias)

**Objetivo:** Crear el router que decide si usar pipeline deterministico
o LLM, e integrarlo en `process_instruction()`.

#### Paso L3.1 — Crear `frontend/router.sh`

**Archivo:** `compiler-bot/frontend/router.sh`

```sh
# ============================================================================
# router.sh - Router inteligente del pipeline RECPL
# ============================================================================
#
# PROPOSITO:
#   Decide si una instruccion debe procesarse con el pipeline deterministico
#   (rapido, sin costo) o con el LLM (flexible, con costo).
#
#   Implementa el patron Strategy: la estrategia se selecciona por
#   variable de entorno o flag.
#
# ESTRATEGIAS:
#   deterministic-first  (default): intenta deterministico, fallback a LLM
#   llm-first:                       intenta LLM primero
#   llm-only:                        solo LLM, nunca deterministico
#   deterministic-only:              solo deterministico, nunca LLM
#
# USO:
#   router "instruccion del usuario"
#   → IR.json (de cualquier camino)
#
# VARIABLES DE ENTORNO:
#   RECPL_LLM_MODE  (auto|llm|deterministic, default: auto)
# ============================================================================

SCRIPT_DIR="$(dirname "$0")"

# --- Cargar clasificador LLM ---
. "$SCRIPT_DIR/llm_classifier.sh" 2>/dev/null

# --- Cargar pipeline deterministico ---
. "$SCRIPT_DIR/lexer.sh" 2>/dev/null
. "$SCRIPT_DIR/parser.sh" 2>/dev/null
. "$SCRIPT_DIR/semantic.sh" 2>/dev/null

# --- Criterios para modo deterministico ---
is_deterministic_candidate() {
    instruction="$1"

    # Si el modo es explicitamente LLM, no intentar deterministico
    [ "${RECPL_LLM_MODE:-auto}" = "llm" ] && return 1

    # Si el modo es deterministic-only, siempre deterministico
    [ "${RECPL_LLM_MODE:-auto}" = "deterministic" ] && return 0

    # Modo auto: intentar deterministico primero
    # Criterio 1: la instruccion es corta (< 10 palabras)
    word_count=$(echo "$instruction" | wc -w | tr -d ' ')
    [ "$word_count" -gt 10 ] && return 1

    # Criterio 2: contiene palabras conocidas por el lexer
    # (accion + posible modulo/entidad)
    case "$instruction" in
        *crea*|*crear*|*genera*|*elimina*|*borra*|*muestra*|*listar*|*modifica*)
            return 0
            ;;
    esac

    # Si no hay match claro, delegar al LLM
    return 1
}

# --- Router principal ---
router() {
    instruction="$1"

    if [ -z "$instruction" ]; then
        echo "{\"accion\":\"error\",\"mensaje\":\"Instruccion vacia\"}"
        return 1
    fi

    if is_deterministic_candidate "$instruction"; then
        # Pipeline deterministico
        preprocessed=$(echo "$instruction" | preprocess 2>/dev/null)
        [ -z "$preprocessed" ] && preprocessed="$instruction"

        tokens=$(echo "$preprocessed" | lex 2>/dev/null)
        if [ $? -ne 0 ] || [ -z "$tokens" ]; then
            # Fallback a LLM si el lexer falla
            llm_classify "$instruction"
            return $?
        fi

        ast=$(echo "$tokens" | parse 2>/dev/null)
        if [ $? -ne 0 ] || [ -z "$ast" ]; then
            llm_classify "$instruction"
            return $?
        fi

        validated=$(echo "$ast" | semantic 2>/dev/null)
        if [ $? -ne 0 ] || [ -z "$validated" ]; then
            llm_classify "$instruction"
            return $?
        fi

        echo "$validated" | ir_generate 2>/dev/null
    else
        # Pipeline LLM
        llm_classify "$instruction"
    fi
}

# --- Punto de entrada ---
if echo "$0" | grep -q "router.sh"; then
    instruction="$1"
    router "$instruction"
fi
```

**Validacion:**
- `bash -n frontend/router.sh` sin errores
- `router "crea modulo pagos en nestjs"` → deterministico
- `RECPL_LLM_MODE=llm router "crea modulo pagos en nestjs"` → LLM
- `router "que es nestjs?"` → LLM (texto)
- `router "crea un modulo"` → LLM (ambiguo)

#### Paso L3.2 — Modificar `recpl.sh` para integrar el router

**Archivo:** `compiler-bot/recpl.sh`

Cambios en `process_instruction()`:

```sh
# reemplazar:
process_instruction() {
    raw_input="$1"
    ...
}

# por:
process_instruction() {
    raw_input="$1"

    # Preprocesar (siempre)
    preprocessed=$(FRONTEND_DIR="$SCRIPT_DIR/frontend" \
        "$SCRIPT_DIR/frontend/preprocessor.sh" "$raw_input" 2>/dev/null)
    [ -z "$preprocessed" ] && preprocessed="$raw_input"

    # Router decide el camino
    result=$(RECPL_STATE_DIR="$RECPL_STATE_DIR" \
        "$SCRIPT_DIR/frontend/router.sh" "$preprocessed" 2>/dev/null)

    if [ $? -ne 0 ] || [ -z "$result" ]; then
        echo "{\"tipo_respuesta\":\"error\",\"mensaje\":\"Error al procesar: $raw_input\",\"payload\":null}"
        return
    fi

    # Si el resultado es un respond o clarify, mostrarlo directamente
    accion=$(echo "$result" | jq -r '.accion // ""')
    if [ "$accion" = "respond" ] || [ "$accion" = "clarify" ]; then
        mensaje=$(echo "$result" | jq -r '.mensaje // ""')
        echo "{\"tipo_respuesta\":\"$accion\",\"mensaje\":\"$mensaje\",\"payload\":null}"
        return
    fi

    # Si es una accion de scaffolding, pasar a synthesis
    "$SCRIPT_DIR/backend/synthesis.sh" 2>/dev/null <<EOF
$result
EOF
}
```

Tambien agregar flags `--llm` y `--provider` al CLI:

```sh
# En main(), antes del dispatch actual:
case "${1:-}" in
    --llm)
        export RECPL_LLM_MODE="llm"
        shift
        ;;
    --provider)
        if [ -z "${2:-}" ]; then
            echo "Error: --provider requiere un argumento" >&2
            exit 1
        fi
        export RECPL_LLM_PROVIDER="$2"
        shift 2
        ;;
esac
```

#### Paso L3.3 — Actualizar `show_help()` con las nuevas banderas

Agregar al bloque HELP:

```
BANDERAS:
  -c, --command TEXTO      Ejecuta una instruccion y termina
  -f, --file ARCHIVO       Ejecuta las instrucciones del archivo y termina
  --llm                    Fuerza modo LLM para todas las instrucciones
  --provider claude|openai Selecciona el proveedor LLM (default: claude)
  -h, --help               Muestra esta ayuda
  -v, --version            Muestra la version

VARIABLES DE ENTORNO:
  RECPL_LLM_MODE           auto|llm|deterministic (default: auto)
  RECPL_LLM_PROVIDER       claude|openai (default: claude)
  ANTHROPIC_API_KEY        Key para Claude (requerido si provider=claude)
  OPENAI_API_KEY           Key para OpenAI (requerido si provider=openai)
```

#### Checkpoint FASE-L3

- [ ] `bash -n frontend/router.sh` sin errores
- [ ] `bash -n recpl.sh` sin errores
- [ ] `shellcheck frontend/router.sh` sin warnings
- [ ] `recpl.sh -c "crea modulo pagos en nestjs"` funciona (deterministico)
- [ ] `recpl.sh --llm -c "crea modulo pagos en nestjs"` funciona (LLM)
- [ ] `recpl.sh --provider openai -c "hola"` funciona (respuesta textual)
- [ ] `RECPL_LLM_MODE=llm recpl.sh` modo interactivo con LLM
- [ ] Sin API key: mensaje de error claro

---

### FASE-L4: Tests, Documentacion y Hardening (2-3 dias)

**Objetivo:** Tests automatizados, documentacion de uso, validacion
shellcheck.

#### Paso L4.1 — Crear `tests/test_router.sh`

```sh
# ============================================================================
# test_router.sh - Tests para el router inteligente
# ============================================================================

test_deterministic_simple() {
    result=$(echo "crea modulo pagos en nestjs" | \
        RECPL_LLM_MODE=deterministic \
        compiler-bot/frontend/router.sh 2>/dev/null)
    echo "$result" | jq -e '.accion == "scaffold"' >/dev/null 2>&1
}

test_llm_mode() {
    # Solo prueba que el modo LLM se selecciona, no que la API responda
    result=$(RECPL_LLM_MODE=llm \
        compiler-bot/frontend/router.sh "test" 2>/dev/null)
    # En modo llm sin API key, debe dar error
    echo "$result" | jq -e '.accion == "error"' >/dev/null 2>&1
}

test_router_fallback() {
    # Instruccion que el lexer no entiende debe caer en LLM
    result=$(echo "haz algo bonito" | \
        compiler-bot/frontend/router.sh 2>/dev/null)
    # Sin API key, debe dar error
    echo "$result" | jq -e '.accion == "error"' >/dev/null 2>&1
}
```

#### Paso L4.2 — Tests de integracion con API real (manual/opcional)

```sh
# test_llm_real.sh (manual, requiere API key)
#
# Ejecutar solo si ANTHROPIC_API_KEY o OPENAI_API_KEY estan configuradas

test_real_llm_classify() {
    ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
    RECPL_LLM_PROVIDER=claude \
    compiler-bot/frontend/llm_classifier.sh "crea un modulo de pagos en NestJS"
    # Debe devolver IR.json con accion=scaffold
}
```

#### Paso L4.3 — Documentar en el runbook

Actualizar `010_GUIDE_DEV_COMPILER_BOT_RUNBOOK_1_0_DRAFT.md` con:

- Nueva seccion: "Modo LLM"
- Ejemplos de uso con `--llm`, `--provider`
- Configuracion de API keys
- Explicacion de cuando usar cada modo

#### Checkpoint FASE-L4

- [ ] `tests/test_router.sh` pasa (3+ tests)
- [ ] `bash tests/run_tests.sh` pasa (47 tests existentes + nuevos)
- [ ] `shellcheck compiler-bot/frontend/router.sh` sin warnings
- [ ] `shellcheck compiler-bot/frontend/llm_classifier.sh` sin warnings
- [ ] `shellcheck compiler-bot/providers/*.sh` sin warnings
- [ ] Documentacion de uso actualizada
- [ ] Este documento actualizado con resultados de implementacion

---

## 5. Uso del Sistema (Guia Rapida)

### 5.1 Configuracion inicial

```sh
# 1. Configurar API key (Claude o OpenAI)
export ANTHROPIC_API_KEY="sk-ant-..."
# o
export OPENAI_API_KEY="sk-..."

# 2. Opcional: seleccionar proveedor y modo
export RECPL_LLM_PROVIDER="claude"    # o "openai"
export RECPL_LLM_MODE="auto"          # o "llm" o "deterministic"
```

### 5.2 Modos de uso

```sh
# Modo interactivo con LLM (instrucciones complejas)
./compiler-bot/recpl.sh --llm
> necesito un sistema de pagos con stripe en nestjs
Generando modulo Pagos en NestJS...

# Modo interactivo hibrido (auto: intenta deterministico, fallback a LLM)
./compiler-bot/recpl.sh
> crea modulo usuarios en nestjs       # deterministico (rapido)
Generando modulo Usuarios en NestJS...
> necesito un crud de productos con auth  # LLM (flexible)
Generando modulo Productos en NestJS...
> que modulos tengo?                    # LLM (respuesta textual)
Tienes 2 modulos: Usuarios, Productos

# Modo comando con LLM
./compiler-bot/recpl.sh --llm -c "crea un modulo de pagos en NestJS"

# Modo comando con proveedor especifico
./compiler-bot/recpl.sh --provider openai -c "explica que es un modulo"

# Solo deterministico (sin LLM, sin necesidad de API key)
./compiler-bot/recpl.sh
```

### 5.3 Ejemplos de lo que el LLM entiende (y el deterministico no)

| Instruccion | Deterministico | LLM | Nota |
|-------------|---------------|-----|------|
| "crea modulo pagos en nestjs" | OK | OK | Ambos funcionan |
| "necesito un sistema de pagos" | ERROR | OK | Descripcion vaga |
| "que modulos tengo?" | ERROR | OK | Pregunta |
| "crea un modulo... este... de usuarios" | ERROR | OK | Tipeo/hesitacion |
| "agregale auth al modulo pagos" | ERROR | OK | Requiere contexto |
| "como se configura nestjs?" | ERROR | OK | Pregunta tecnica |

---

## 6. Costos y Consideraciones

### 6.1 Costo por instruccion LLM

| Provider | Modelo | Input | Output | Costo/instruccion |
|----------|--------|-------|--------|-------------------|
| Claude | Sonnet 4 | ~600 tok | ~200 tok | ~$0.005 |
| OpenAI | GPT-4o | ~600 tok | ~200 tok | ~$0.004 |
| Claude | Haiku 3.5 | ~600 tok | ~200 tok | ~$0.0015 |

**1000 instrucciones/mes con Sonnet 4:** ~$5.00/mes

### 6.2 Cuando se usa el LLM

En modo `auto` (default), el LLM solo se usa cuando:
1. La instruccion tiene mas de 10 palabras (compleja)
2. El lexer no reconoce las palabras
3. El parser falla (gramatica no reconocida)

Esto significa que ~80% de las instrucciones simples siguen siendo
deterministicas (gratis). El LLM solo se usa para ~20% de los casos.

### 6.3 Latencia

- **Pipeline deterministico:** ~50ms
- **LLM (Claude Sonnet):** ~1-3s
- **LLM (OpenAI GPT-4o):** ~1-3s

El usuario percibe la diferencia, pero es aceptable para instrucciones
complejas. Para respuestas rapidas, el modo deterministico sigue
disponible.

---

## 7. Riesgos y Mitigaciones

| Riesgo | Impacto | Probabilidad | Mitigacion |
|--------|---------|--------------|------------|
| **API key no configurada** | El modo LLM no funciona | Alta | Mensaje de error claro; fallback a deterministico automatico |
| **API caida** | El modo LLM no funciona | Baja | Fallback automatico a deterministico; timeout configurable |
| **Costo impredecible** | Gastos inesperados | Media | Modo deterministic-first por defecto; flag `--llm` explicito requerido |
| **Alucinaciones** | Tools/params inventados | Media | System prompt restrictivo; validacion post-LLM en mapper |
| **Latencia alta** | Mala experiencia de usuario | Media | Timeout configurable; feedback "procesando..." |
| **Cambios en API externa** | Adapter deja de funcionar | Baja | Abstraccion por provider; tests de integracion periodicos |
| **Shellcheck compatibilidad** | Scripts no portables | Media | Validacion con shellcheck en CI; pruebas en /bin/sh |

---

## 8. Resumen de Archivos

### Archivos nuevos (7)

| Archivo | Proposito | Fase |
|---------|-----------|------|
| `compiler-bot/providers/provider_common.sh` | Utilidades compartidas para adapters | L1 |
| `compiler-bot/providers/claude.sh` | Adapter para Claude API | L1 |
| `compiler-bot/providers/openai.sh` | Adapter para OpenAI API | L1 |
| `compiler-bot/frontend/llm_classifier.sh` | Fachada LLM (Facade Pattern) | L2 |
| `compiler-bot/middleend/llm_ir_mapper.sh` | Mapea tool call a IR.json | L2 |
| `compiler-bot/frontend/router.sh` | Router inteligente (Strategy Pattern) | L3 |
| `compiler-bot/tests/test_router.sh` | Tests del router | L4 |

### Archivos modificados (2)

| Archivo | Cambio | Fase |
|---------|--------|------|
| `compiler-bot/recpl.sh` | Integrar router, flags --llm y --provider | L3 |
| `compiler-bot/tests/run_tests.sh` | Agregar tests de router y LLM | L4 |

### Archivos sin cambios (6)

| Archivo | Razon |
|---------|-------|
| `compiler-bot/frontend/preprocessor.sh` | Sigue siendo util para ambos caminos |
| `compiler-bot/frontend/lexer.sh` | Usado por el pipeline deterministico |
| `compiler-bot/frontend/parser.sh` | Usado por el pipeline deterministico |
| `compiler-bot/frontend/semantic.sh` | Usado por el pipeline deterministico |
| `compiler-bot/backend/synthesis.sh` | Compartido por ambos caminos (sin cambios) |
| `compiler-bot/backend/scaffold.sh` | Compartido por ambos caminos (sin cambios) |

---

## 9. Dependencias entre Fases

```
FASE-L1 (Adapters)
    │
    ▼
FASE-L2 (LLM Classifier + IR Mapper)
    │
    ▼
FASE-L3 (Router + Integracion en recpl.sh)
    │
    ▼
FASE-L4 (Tests + Documentacion)
```

**Orden recomendado:**
1. L1 (Adapters) — base tecnica, validacion con API real
2. L2 (Classifier) — fachada funcional, se prueba independientemente
3. L3 (Router) — integracion final, el sistema completo funciona
4. L4 (Tests + Docs) — hardening y documentacion

Cada fase produce resultados funcionales que se pueden probar y
commitar independientemente.

---

## 10. Checklist de Implementacion

### FASE-L1
- [ ] `providers/provider_common.sh` — check_curl, check_jq, format_tool_response, format_text_response
- [ ] `providers/claude.sh` — claude_complete con payload Anthropic y parseo tool_use
- [ ] `providers/openai.sh` — openai_complete con payload OpenAI y parseo tool_calls
- [ ] Validacion: `bash -n` en los 3 archivos
- [ ] Validacion: llamadas reales con API keys (opcional, manual)
- [ ] Validacion: manejo de errores (sin API key, timeout, HTTP error)

### FASE-L2
- [ ] `frontend/llm_classifier.sh` — get_system_prompt, get_tools_json, map_tool_to_ir, llm_classify
- [ ] `middleend/llm_ir_mapper.sh` — mapper separado con jq
- [ ] Validacion: `bash -n` en ambos archivos
- [ ] Validacion: llm_classify con instrucciones reales
- [ ] Validacion: llm_ir_mapper con cada tipo de tool

### FASE-L3
- [ ] `frontend/router.sh` — is_deterministic_candidate, router()
- [ ] Modificar `recpl.sh` — process_instruction usa router
- [ ] Flag `--llm` en recpl.sh
- [ ] Flag `--provider` en recpl.sh
- [ ] Variable `RECPL_LLM_MODE` (auto|llm|deterministic)
- [ ] Variable `RECPL_LLM_PROVIDER` (claude|openai)
- [ ] `show_help()` actualizado con nuevas banderas
- [ ] Validacion: `bash -n recpl.sh`
- [ ] Validacion: modo interactivo con --llm
- [ ] Validacion: fallback deterministico cuando LLM no disponible

### FASE-L4
- [ ] `tests/test_router.sh` — 3+ tests del router
- [ ] `tests/run_tests.sh` actualizado
- [ ] `bash tests/run_tests.sh` pasa (47+ tests)
- [ ] `shellcheck compiler-bot/providers/*.sh` sin warnings
- [ ] `shellcheck compiler-bot/frontend/router.sh` sin warnings
- [ ] `shellcheck compiler-bot/frontend/llm_classifier.sh` sin warnings
- [ ] Documentacion de uso actualizada
