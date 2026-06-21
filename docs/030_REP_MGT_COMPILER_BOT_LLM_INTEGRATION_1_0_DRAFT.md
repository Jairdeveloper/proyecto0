---
id: 030
area: mgt
type: rep
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - report
  - management
  - reverse-engineering
  - llm
  - claude
  - openai
  - intent
  - nlp
  - api
  - compiler-bot
  - recpl
summary: "Reporte de gerencia sobre la integracion del RECPL Compiler Bot con APIs de LLM (Claude, OpenAI). Incluye ingenieria inversa de los patrones publicos de comunicacion de agentes, propuesta de arquitectura para traducir intencion del usuario, y plan de implementacion para que el bot entienda, razone y responda con mutaciones sobre el codigo generado."
keywords:
  - reverse-engineering
  - claude
  - openai
  - llm
  - intent
  - api
  - recpl
  - compiler-bot
  - tool-use
  - function-calling
  - structured-output
  - agente
  - arquitectura
  - plan
changelog:
  - version: 1.0
    date: 2026-06-11
    author: workflow-agent
    description: Reporte de ingenieria inversa de Claude/OpenAI y propuesta de integracion con RECPL
---

# Reporte de Gerencia: Ingenieria Inversa

## prompt

Hacer ingenieria inversa a claude y openai de acuerdo a su informacion publica para replicar su comportamiento en la forma en que se comunican sus agentes y sus procesos principales. Generar reporte.

---

## 0. Resumen Ejecutivo

Este reporte analiza los patrones publicos de comunicacion de agentes de
Claude (Anthropic) y OpenAI (GPT-4, GPT-4o) con el objetivo de integrar
el RECPL Compiler Bot con APIs de LLM. La integracion permite que el bot
no solo ejecute reglas deterministicas (lexer → parser → IR), sino que
**entienda intencion del usuario, resuelva ambiguedades, y genere
mutaciones de codigo contextuales** usando modelos de lenguaje.

El resultado es un compilador hibrido: reglas deterministicas para lo
predecible + LLM para lo ambiguo y contextual.

---

## 1. Ingenieria Inversa: Patrones Publicos de Claude y OpenAI

### 1.1 Claude (Anthropic) — Messages API

**Fuente:** docs.anthropic.com/en/api/messages

**Patron de comunicacion:**

```
POST https://api.anthropic.com/v1/messages
Headers:
  x-api-key: <key>
  anthropic-version: 2023-06-01
  Content-Type: application/json

Body:
{
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 8192,
  "system": "Eres un compilador de lenguaje natural...",
  "messages": [
    {"role": "user", "content": "crea un modulo de pagos en NestJS"}
  ],
  "tools": [
    {
      "name": "scaffold_module",
      "description": "Genera un modulo NestJS",
      "input_schema": {
        "type": "object",
        "properties": {
          "nombre": {"type": "string"},
          "tech": {"type": "string"}
        }
      }
    }
  ]
}
```

**Mecanismos clave identificados:**

| Mecanismo | Descripcion | Util para RECPL |
|-----------|-------------|-----------------|
| **Tool Use / Function Calling** | El modelo declara que herramienta usar y con que argumentos | Reemplaza al parser deterministico: el LLM extrae accion y entidades directamente |
| **System Prompt** | Instrucciones de alto nivel que definen el rol del agente | Define el comportamiento del compilador (que techos soporta, que formato de salida) |
| **Structured Output** | Respuesta forzada a un schema JSON | El output del LLM se mapea directamente al IR.json |
| **Streaming** | Respuesta chunk-by-chunk via SSE | Feedback en tiempo real al usuario |
| **Multi-turn** | Historial de mensajes para contexto | Dialogo de clarificacion: "No entendi, quiere decir modulo o entidad?" |
| **Thinking** | Claude puede mostrar su razonamiento interno | Trazabilidad de decisiones (TASK-009 Tracer) |

### 1.2 OpenAI — Chat Completions API

**Fuente:** platform.openai.com/docs/api-reference/chat

**Patron de comunicacion:**

```
POST https://api.openai.com/v1/chat/completions
Headers:
  Authorization: Bearer <key>
  Content-Type: application/json

Body:
{
  "model": "gpt-4o",
  "messages": [
    {"role": "system", "content": "Eres un compilador..."},
    {"role": "user", "content": "crea modulo pagos"}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "scaffold_module",
        "parameters": {
          "type": "object",
          "properties": {
            "nombre": {"type": "string"},
            "tech": {"type": "string", "enum": ["NestJS", "Prisma"]}
          },
          "required": ["nombre", "tech"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}
```

**Diferencias con Claude:**

| Aspecto | Claude | OpenAI |
|---------|--------|--------|
| Formato de tools | `tools: [{name, input_schema}]` | `tools: [{type: "function", function: {name, parameters}}]` |
| Sistema | Campo `system` separado | `role: "system"` en messages |
| Tool choice | Implicito (decide el modelo) | Explicito: `tool_choice: "auto"` |
| Streaming | SSE nativo | SSE nativo (mismo formato) |
| Vision | Soporta imagenes en base64 | Soporta imagenes en URL o base64 |
| Costo tipico | $3/M input, $15/M output | $2.5/M input, $10/M output |

### 1.3 Patron Comun de Agentes

Ambos APIs comparten el mismo patron arquitectonico:

```
┌──────────────────────────────────────────────┐
│               AGENTE LLM                     │
│                                              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐ │
│  │ SYSTEM   │   │ TOOLS    │   │ MESSAGES │ │
│  │ PROMPT   │   │ (funcs)  │   │ history  │ │
│  └──────────┘   └──────────┘   └──────────┘ │
│       │              │              │        │
│       └──────────────┼──────────────┘        │
│                      ▼                       │
│              ┌──────────────┐                │
│              │    LLM       │                │
│              │   DECISION   │                │
│              └──────┬───────┘                │
│                     │                        │
│           ┌─────────┼─────────┐              │
│           ▼         ▼         ▼              │
│       ┌──────┐ ┌──────┐ ┌────────┐          │
│       │TEXT  │ │TOOL  │ │MULTI  │          │
│       │RESP  │ │CALL  │ │TURN   │          │
│       └──────┘ └──────┘ └────────┘          │
└──────────────────────────────────────────────┘
```

**El agente decide:**
1. Si responde texto directamente (pregunta, clarificacion, saludo)
2. Si invoca una herramienta (scaffold, delete, read)
3. Si necesita mas informacion (multi-turn, pregunta al usuario)

---

## 2. Arquitectura Propuesta: RECPL + LLM

### 2.1 El LLM como reemplazo del front-end deterministico

```
    INPUT: "crea un modulo de pagos en NestJS"
              │
              ▼
┌──────────────────────────────┐
│     CAPA LLM (Nueva)         │
│                              │
│  ┌────────────────────────┐  │
│  │   intent_classifier    │  │
│  │   ────────────────     │  │
│  │   System: Eres un      │  │
│  │   compilador RECPL...  │  │
│  │   Tools: scaffold,     │  │
│  │   delete, read, etc.   │  │
│  │                        │  │
│  │   Output: Tool Call o  │  │
│  │   Text Response        │  │
│  └───────────┬────────────┘  │
└──────────────┼───────────────┘
               │
               ▼
┌──────────────────────────────┐
│   IR.json (igual que hoy)    │
│                              │
│  { accion, tipo, nombre,     │
│    tech, template, entidades }│
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│   BACK-END (sin cambios)     │
│                              │
│   synthesis.sh + scaffold.sh │
│   → archivos en modules/     │
└──────────────────────────────┘
```

### 2.2 Dos modos de operacion

| Modo | Front-end | Back-end | Caso de uso |
|------|-----------|----------|-------------|
| **Deterministico** (actual) | preprocessor → lexer → parser → semantic | synthesis + scaffold | Instrucciones simples y predecibles |
| **LLM** (nuevo) | intent_classifier → LLM → tool call → IR mapper | synthesis + scaffold | Instrucciones ambiguas, multi-intencion, contexto |

### 2.3 Donde encaja el LLM en el pipeline actual

```
Pipeline actual:
  preprocess → lexer → parser → semantic → IR → synthesis → scaffold

Pipeline hibrido:
                                           ┌─ deterministico ─┐
  preprocess → router ─→ si es simple ───→│ lexer → parser   │
                │                         │ → semantic → IR  │
                └─ si es ambiguo ────────→│ LLM → IR mapper  │
                                           └──────────────────┘
                                                │
                                                ▼
                                          synthesis → scaffold
```

El **router** decide que camino tomar basado en:
- Complejidad de la instruccion (numero de tokens, entidades)
- Ambiguedad detectada por el preprocesador
- Presencia de palabras que el lexer no reconoce
- Flag explicito del usuario: `--llm` o `--deterministic`

### 2.4 Herramientas (tools) que expone el bot al LLM

Cada herramienta es una funcion que el LLM puede invocar:

| Tool | Descripcion | Parametros | Equivalente RECPL |
|------|-------------|------------|-------------------|
| `scaffold_module` | Genera un modulo NestJS/Prisma | nombre, tech | CREATE + MODULE |
| `scaffold_entity` | Genera una entidad | nombre, tech, campos | CREATE + ENTITY |
| `delete_module` | Elimina un modulo existente | nombre | DELETE |
| `read_module` | Muestra informacion de un modulo | nombre | READ |
| `update_module` | Modifica un modulo existente | nombre, cambios | UPDATE |
| `clarify` | Pregunta al usuario para resolver ambiguedad | pregunta | Multi-turn |
| `respond` | Responde texto directamente | mensaje | Chat mode |

### 2.5 System prompt del compilador LLM

```
Eres un compilador de lenguaje natural a codigo (RECPL).
Traduces instrucciones del usuario en acciones del compilador.

REGLAS:
- Si el usuario pide crear/ generar/ hacer: usa scaffold_module o scaffold_entity
- Si el usuario pide eliminar/ borrar: usa delete_module
- Si el usuario pide mostrar/ listar: usa read_module
- Si el usuario pide modificar/ actualizar: usa update_module
- Si la instruccion es ambigua, usa clarify para preguntar
- Si el usuario saluda o pregunta algo general, usa respond

TECHS SOPORTADAS: NestJS, Prisma, Express, FastAPI
FORMATO DE SALIDA: Tool call en JSON con parametros exactos
```

---

## 3. Estrategia de Implementacion

### 3.1 Fase 1: LLM como reemplazo del lexer+parser (Semana 1)

Crear un script `frontend/llm_classifier.sh` que:

```sh
#!/bin/sh
# llm_classifier.sh - Clasificador de intencion via LLM
#
# Recibe: texto preprocesado
# Envia: a API de Claude/OpenAI con tools
# Recibe: tool call o respuesta textual
# Output: IR.json o JSON de respuesta

llm_classify() {
    instruction="$1"
    provider="${RECPL_LLM_PROVIDER:-claude}"
    api_key="${RECPL_LLM_KEY:-}"

    # Construir payload segun provider
    case "$provider" in
        claude)
            # POST a Anthropic Messages API con tools
            # Response: tool_use o text
            ;;
        openai)
            # POST a OpenAI Chat Completions con functions
            # Response: tool_calls o content
            ;;
    esac

    # Mapear tool call a IR.json
    # o devolver respuesta textual
}
```

**Decision de diseno:** Abstraer el provider detras de una interfaz
unica. El pipeline no sabe si esta llamando a Claude o OpenAI.

```
llm_classifier.sh
    │
    ├─ provider="claude"  → claude_api.sh
    ├─ provider="openai"  → openai_api.sh
    │
    └─ output: siempre el mismo formato JSON
```

### 3.2 Fase 2: Router inteligente (Semana 1-2)

Crear un `frontend/router.sh` que decide que camino tomar:

```sh
router() {
    instruction="$1"

    # Criterios para modo deterministico:
    # 1. La instruccion encaja exactamente en la gramatica RECPL
    # 2. Todos los tokens son reconocidos por el lexer
    # 3. Sin ambiguedad semantica

    if is_deterministic "$instruction"; then
        # Pipeline clasico
        lexer "$instruction" | parser | semantic
    else
        # Pipeline LLM
        llm_classifier "$instruction"
    fi
}
```

### 3.3 Fase 3: Mutaciones y respuestas contextuales (Semana 2-3)

El LLM no solo clasifica intencion, sino que puede:

1. **Responder preguntas:** "Que modulos tengo?" → consulta la tabla de
   simbolos y responde con lenguaje natural

2. **Modificar codigo existente:** "Agrega validacion al modulo pagos" →
   lee el archivo generado, entiende su estructura, y produce un parche

3. **Refactorizar:** "Cambia todos los modulos de Prisma a TypeORM" →
   opera sobre todos los archivos generados

4. **Explicar codigo:** "Que hace el controlador de pagos?" →
   lee el archivo y explica en lenguaje natural

Para esto, el LLM necesita acceso a:
- La tabla de simbolos (que modulo existe, su estado)
- Los archivos generados en `modules/`
- El contexto de la conversacion (multi-turn)

### 3.4 Diagrama de flujo completo

```
USUARIO: "crea un modulo de pagos en NestJS"
                │
                ▼
┌──────────────────────────────┐
│       PREPROCESSOR          │
│  (normaliza, lowercase)     │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│         ROUTER               │
│                              │
│  Es la gramatica conocida?  │
│  Hay palabras no reconoci-  │
│  das por el lexer?          │
└──────┬──────────────┬───────┘
       │              │
       SI             NO
       ▼              ▼
┌──────────────┐ ┌──────────────────────────────┐
│ PIPELINE     │ │      LLM CLASSIFIER          │
│ DETERMIN-   │ │                              │
| ISTICO      │ │  POST /v1/messages           │
│ lexer→parser│ │  tools: [scaffold, delete,   │
│ →semantic→IR│ │          read, clarify]      │
└──────┬──────┘ │                              │
       │        │  ← tool_use: scaffold_module │
       │        │    nombre: "pagos"           │
       │        │    tech: "NestJS"            │
       │        └──────────────┬───────────────┘
       │                       │
       └───────────┬───────────┘
                   ▼
┌──────────────────────────────┐
│      IR MAPPER              │
│  Convierte tool call a       │
│  IR.json canonico            │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│     SYNTHESIS + SCAFFOLD    │
│  (sin cambios)              │
└──────────────┬───────────────┘
               ▼
       archivos en modules/
       + respuesta JSON
```

---

## 4. Contrato de API Unificado

Para abstraer la diferencia entre providers, se define un formato
interno comun:

### 4.1 Request (desde RECPL hacia el LLM)

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
      "description": "Genera un modulo de codigo",
      "parameters": {
        "nombre": "string",
        "tech": "string"
      }
    }
  ],
  "max_tokens": 1024
}
```

### 4.2 Response (desde el LLM hacia RECPL)

```json
{
  "type": "tool_use",
  "tool": "scaffold_module",
  "parameters": {
    "nombre": "Pagos",
    "tech": "NestJS"
  },
  "raw": { ... }  // respuesta original del provider para depuracion
}
```

o

```json
{
  "type": "text",
  "content": "Claro, tengo estos modulos disponibles: pagos, usuarios, productos",
  "raw": { ... }
}
```

### 4.3 Mapeo a IR.json

```sh
map_tool_call_to_ir() {
    tool="$1"
    params="$2"

    case "$tool" in
        scaffold_module)
            echo "{accion:scaffold, tipo:module, nombre:$(echo $params | jq .nombre), tech:$(echo $params | jq .tech)}"
            ;;
        scaffold_entity)
            echo "{accion:scaffold, tipo:entity, nombre:$(echo $params | jq .nombre), tech:$(echo $params | jq .tech)}"
            ;;
        delete_module)
            echo "{accion:delete, tipo:module, nombre:$(echo $params | jq .nombre)}"
            ;;
        read_module)
            echo "{accion:read, tipo:module, nombre:$(echo $params | jq .nombre)}"
            ;;
        respond)
            # Respuesta textual directa al usuario, sin pasar por synthesis
            echo "{accion:respond, mensaje:$(echo $params | jq .mensaje)}"
            ;;
    esac
}
```

---

## 5. Adapter Layer: Proveedores

### 5.1 Claude Adapter (`providers/claude.sh`)

```sh
# providers/claude.sh
API_URL="https://api.anthropic.com/v1/messages"
API_KEY="${ANTHROPIC_API_KEY}"

claude_complete() {
    system="$1"
    message="$2"
    tools_json="$3"

    response=$(curl -s -X POST "$API_URL" \
        -H "x-api-key: $API_KEY" \
        -H "anthropic-version: 2023-06-01" \
        -H "content-type: application/json" \
        -d "{
            \"model\": \"claude-sonnet-4-20250514\",
            \"max_tokens\": 1024,
            \"system\": \"$system\",
            \"messages\": [{\"role\": \"user\", \"content\": \"$message\"}],
            \"tools\": $tools_json
        }")

    # Extraer tool_use o text de la respuesta
    echo "$response" | jq '{type: .content[0].type, tool: .content[0].name, parameters: .content[0].input}'
}
```

### 5.2 OpenAI Adapter (`providers/openai.sh`)

```sh
# providers/openai.sh
API_URL="https://api.openai.com/v1/chat/completions"
API_KEY="${OPENAI_API_KEY}"

openai_complete() {
    system="$1"
    message="$2"
    tools_json="$3"

    response=$(curl -s -X POST "$API_URL" \
        -H "Authorization: Bearer $API_KEY" \
        -H "content-type: application/json" \
        -d "{
            \"model\": \"gpt-4o\",
            \"messages\": [
                {\"role\": \"system\", \"content\": \"$system\"},
                {\"role\": \"user\", \"content\": \"$message\"}
            ],
            \"tools\": $tools_json,
            \"tool_choice\": \"auto\"
        }")

    # Extraer tool_calls o content de la respuesta
    echo "$response" | jq '{type: "tool_use", tool: .choices[0].message.tool_calls[0].function.name, parameters: .choices[0].message.tool_calls[0].arguments}'
}
```

### 5.3 Variable de entorno para seleccion de provider

```sh
export RECPL_LLM_PROVIDER=claude    # o "openai"
export ANTHROPIC_API_KEY=sk-ant-...  # si provider=claude
export OPENAI_API_KEY=sk-...         # si provider=openai
export RECPL_LLM_MODE=auto           # auto, deterministic, llm
```

---

## 6. Mutaciones: Respuesta Contextual del Bot

### 6.1 Que son las mutaciones

Ademas de generar scaffolding, el bot con LLM puede:
- **Modificar** archivos existentes
- **Explicar** en lenguaje natural
- **Conversar** manteniendo contexto
- **Recomendar** arquitectura basada en el estado actual

### 6.2 Ejemplos de mutacion

```
Usuario: "Agrega un campo email al modulo usuarios"
  → LLM lee modules/usuarios/usuarios.entity.ts
  → LLM genera: nuevo archivo con campo email agregado
  → output: "Agregado campo email a la entidad Usuarios"

Usuario: "Que modulos tengo creados?"
  → LLM lee tabla de simbolos
  → Responde textual: "Tienes 3 modulos: Pagos, Usuarios, Productos"

Usuario: "Explica el controlador de pagos"
  → LLM lee modules/pagos/pagos.controller.ts
  → Responde: "El controlador expone endpoints CRUD sobre /api/pagos"
```

### 6.3 Arquitectura de mutaciones

```
LLM recibe instruccion +
  ├─ simbolos actuales (de RECPL_STATE_DIR)
  ├─ archivos en modules/ (si aplica)
  └─ contexto de la conversacion

LLM decide:
  ├─ tool_call → scaffold, delete, read, update
  │   └─ synthesis ejecuta la accion
  │
  ├─ tool_call → mutate_file
  │   └─ mutation_engine aplica el cambio
  │
  └─ text → respond
      └─ respuesta directa al usuario
```

---

## 7. Costos y Viabilidad

### 7.1 Estimacion de costos por instruccion

| Provider | Modelo | Input (estimado) | Output (estimado) | Costo por instruccion |
|----------|--------|-----------------|------------------|----------------------|
| Claude | Sonnet 4 | ~500 tokens | ~200 tokens | $0.0015 + $0.003 = $0.0045 |
| OpenAI | GPT-4o | ~500 tokens | ~200 tokens | $0.00125 + $0.002 = $0.00325 |
| Claude | Haiku 3.5 | ~500 tokens | ~200 tokens | $0.00025 + $0.00125 = $0.0015 |
| (local) | Ollama/LLaMA | ~500 tokens | ~200 tokens | $0 (hardware propio) |

**Escenario:** 1000 instrucciones/mes con Sonnet 4 = ~$4.50/mes.

### 7.2 Modo hibrido para optimizar costos

```
Siempre intentar modo deterministico primero.
Solo usar LLM si:
  a) El lexer no reconoce la instruccion
  b) Hay ambiguedad semantica
  c) El usuario pide explicitamente modo LLM

Esto reduce el uso de LLM a ~10-20% de las instrucciones.
```

---

## 8. Plan de Implementacion

### Fase 1: Adapters y LLM Classifier (Semana 1)

| Tarea | Archivos | Dependencia |
|-------|----------|-------------|
| Crear `providers/claude.sh` | Nuevo | Ninguna |
| Crear `providers/openai.sh` | Nuevo | Ninguna |
| Crear `frontend/llm_classifier.sh` | Nuevo | providers |
| Definir formato de tool calls | Documentacion | — |
| Test: llamada a API real | Manual | API keys |

### Fase 2: Router y Pipeline Hibrido (Semana 2)

| Tarea | Archivos | Dependencia |
|-------|----------|-------------|
| Crear `frontend/router.sh` | Nuevo | Fase 1 |
| Modificar `recpl.sh` para modo LLM | Modificar | router.sh |
| Agregar flag `--llm` y `--provider` a CLI | Modificar | Fase 1 |
| Mapeo tool call → IR.json | `middleend/ir_generator.sh` | Fase 1 |
| Test: pipeline hibrido completo | tests/ | Fase 2 |

### Fase 3: Mutaciones y Contexto (Semana 3)

| Tarea | Archivos | Dependencia |
|-------|----------|-------------|
| Agregar tool `mutate_file` | Nuevo | Fase 2 |
| Agregar tool `explain` | Nuevo | Fase 2 |
| Contexto multi-turn (historial) | `frontend/semantic.sh` | Fase 2 |
| Tool `clarify` para dialogo | Nuevo | Fase 2 |
| Test: mutaciones sobre archivos reales | tests/ | Fase 3 |

### Fase 4: Modo Local (Opcional, Semana 4)

| Tarea | Archivos | Dependencia |
|-------|----------|-------------|
| Adapter para Ollama | `providers/ollama.sh` | Fase 1 |
| Soporte de modelos locales (LLaMA, Mistral) | providers | Fase 4 |
| Benchmark: deterministico vs LLM vs hibrido | tests/benchmark.sh | Fase 3 |

---

## 9. Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigacion |
|--------|---------|------------|
| **Dependencia de API externa** | Si la API cae, el bot no funciona en modo LLM | El modo deterministico sigue funcionando sin internet |
| **Costo impredecible** | El usuario puede abusar del modo LLM | Limitar modo LLM a N requests/dia o solo con flag explicito |
| **Latencia** | LLM tarda 1-3s vs 50ms del pipeline deterministico | Usar streaming, cachear respuestas, modo deterministico por defecto |
| **Alucinaciones** | El LLM puede inventar nombres de techos o modulos | El mapper de tool calls valida contra la lista blanca de techos |
| **Cambios en API de proveedores** | El adapter deja de funcionar | Abstraccion por provider, tests de integracion periodicos |

---

## 10. Conclusion

La integracion con LLMs transforma RECPL de un compilador deterministico
a un **compilador hibrido**: reglas para lo predecible, LLM para lo
ambiguo. El costo es bajo (~$4.50/1000 instrucciones con Claude) y la
implementacion es incremental — no requiere reescribir el pipeline
existente.

El patron de ingenieria inversa de Claude/OpenAI revela que ambos usan
el mismo mecanismo fundamental: **tool use / function calling** con
schemas JSON. RECPL puede replicar este comportamiento definiendo sus
propias tools (scaffold, delete, read, update) y exponiendolas al LLM
como un "compilador como servicio".
