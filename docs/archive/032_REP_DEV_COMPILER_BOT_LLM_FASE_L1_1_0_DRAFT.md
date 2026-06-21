---
id: 032
area: dev
type: rep
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - report
  - implementation
  - fase-l1
  - llm
  - adapter
  - provider
  - claude
  - openai
  - compiler-bot
  - recpl
summary: "Reporte de implementacion de la FASE-L1 del plan 031: adapters de proveedor LLM (provider_common.sh, claude.sh, openai.sh). Incluye archivos creados, validaciones realizadas y resultados de sintaxis/manejo de errores."
keywords:
  - reporte
  - implementacion
  - fase-l1
  - adapters
  - proveedores
  - claude
  - openai
  - validacion
  - sintaxis
  - errores
  - bash
changelog:
  - version: 1.0
    date: 2026-06-11
    author: workflow-agent
    description: Implementacion de FASE-L1 del plan 031 — adapters de proveedor LLM
---

# Reporte de Implementacion: FASE-L1 — Adapters de Proveedor LLM

> **Plan de referencia:** `031_PLAN_DEV_COMPILER_BOT_LLM_EXECUTION_1_0_DRAFT.md`
> **Documento base:** `030_REP_MGT_COMPILER_BOT_LLM_INTEGRATION_1_0_DRAFT.md`
> **Guia de estilo:** `000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md`

---

## 0. Resumen

Se implemento la FASE-L1 del plan de integracion LLM: los 3 adapters de
proveedor que permiten al RECPL Compiler Bot comunicarse con Claude
(Anthropic) y OpenAI a traves de un formato interno comun.

**Estado:** COMPLETADO

---

## 1. Archivos Creados

### 1.1 `compiler-bot/providers/provider_common.sh`

**Proposito:** Utilidades compartidas entre todos los adapters.

**Funciones:**

| Funcion | Descripcion |
|---------|-------------|
| `check_curl()` | Verifica que `curl` esta instalado. Retorna 1 si no. |
| `check_jq()` | Verifica que `jq` esta instalado. Retorna 1 si no. |
| `format_tool_response()` | Convierte tool_name + params a `{"type":"tool_use","tool":"...","parameters":{...}}` |
| `format_text_response()` | Convierte texto a `{"type":"text","content":"..."}` usando jq para escapado |

**Constantes:**
- `RECPL_LLM_TIMEOUT` (default: 30s) — timeout para llamadas HTTP
- `RECPL_LLM_MAX_TOKENS` (default: 1024) — max tokens en respuesta

### 1.2 `compiler-bot/providers/claude.sh`

**Proposito:** Adapter para Anthropic Claude Messages API.

**Funcion principal:** `claude_complete(system, message, tools_json)`

**Detalles de implementacion:**
- URL: `https://api.anthropic.com/v1/messages`
- Auth: Header `x-api-key` con `ANTHROPIC_API_KEY`
- Version API: `anthropic-version: 2023-06-01`
- Modelo: `claude-sonnet-4-20250514`
- Formato tools: `tools: [{name, input_schema}]`
- Parseo: `.content[0].type` → `tool_use` o `text`
- Extraccion tool: `.content[0].name` + `.content[0].input`

### 1.3 `compiler-bot/providers/openai.sh`

**Proposito:** Adapter para OpenAI Chat Completions API.

**Funcion principal:** `openai_complete(system, message, tools_json)`

**Detalles de implementacion:**
- URL: `https://api.openai.com/v1/chat/completions`
- Auth: Header `Authorization: Bearer` con `OPENAI_API_KEY`
- Modelo: `gpt-4o`
- Formato tools: `tools: [{type: "function", function: {name, parameters}}]`
- `tool_choice: "auto"` para que el LLM decida
- Parseo: `.choices[0].message.tool_calls` o `.choices[0].message.content`
- Extraccion tool: `.[0].function.name` + `.[0].function.arguments`

---

## 2. Validaciones Realizadas

### 2.1 Sintaxis (`bash -n`)

| Archivo | Resultado |
|---------|-----------|
| `provider_common.sh` | OK — sin errores de sintaxis |
| `claude.sh` | OK — sin errores de sintaxis |
| `openai.sh` | OK — sin errores de sintaxis |

### 2.2 Manejo de errores (sin API key)

| Prueba | Comando | Resultado esperado | Resultado obtenido |
|--------|---------|-------------------|-------------------|
| Claude sin key | `claude_complete "test" "test" "[]"` | Error: ANTHROPIC_API_KEY no esta configurada (exit 1) | ✅ Error: ANTHROPIC_API_KEY no esta configurada (exit 1) |
| OpenAI sin key | `openai_complete "test" "test" "[]"` | Error: OPENAI_API_KEY no esta configurada (exit 1) | ✅ Error: OPENAI_API_KEY no esta configurada (exit 1) |

### 2.3 Formato interno comun

| Prueba | Entrada | Salida esperada | Salida obtenida |
|--------|---------|-----------------|-----------------|
| `format_tool_response` | `scaffold_module`, `{"nombre":"Pagos","tech":"NestJS"}` | `{"type":"tool_use","tool":"scaffold_module","parameters":{...}}` | ✅ JSON valido |

### 2.4 Checklist FASE-L1

- [x] `providers/provider_common.sh` — check_curl, check_jq, format_tool_response, format_text_response
- [x] `providers/claude.sh` — claude_complete con payload Anthropic y parseo tool_use
- [x] `providers/openai.sh` — openai_complete con payload OpenAI y parseo tool_calls
- [x] Validacion: `bash -n` en los 3 archivos (3/3 OK)
- [ ] Validacion: llamadas reales con API keys (opcional, manual — no ejecutado)
- [x] Validacion: manejo de errores (sin API key: mensajes claros en ambos)

---

## 3. Decisiones de Diseno

### 3.1 Formato de tool calls unificado

Ambos adapters normalizan la respuesta al mismo formato interno comun:

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

Esto permite que el pipeline consuma la respuesta sin saber que
proveedor la genero (Adapter Pattern).

### 3.2 Separacion de responsabilidades

`provider_common.sh` contiene solo funciones compartidas. No contiene
logica de ningun proveedor en particular. Esto permite agregar nuevos
proveedores (Ollama, Gemini, etc.) sin duplicar utilidades.

### 3.3 Manejo de errores por falla de red

Ambos adapters capturan el codigo HTTP de respuesta. Si no es 200,
emiten un mensaje claro con el codigo y el body de error. Si curl falla
por timeout, `--max-time` asegura que no se cuelgue indefinidamente.

### 3.4 Variables de entorno

| Variable | Default | Donde se usa |
|----------|---------|--------------|
| `ANTHROPIC_API_KEY` | — | claude.sh |
| `OPENAI_API_KEY` | — | openai.sh |
| `RECPL_LLM_TIMEOUT` | 30 | provider_common.sh → curl --max-time |
| `RECPL_LLM_MAX_TOKENS` | 1024 | provider_common.sh → payload max_tokens |

---

## 4. Proximos Pasos

Completada FASE-L1. La siguiente fase (FASE-L2) debe implementar:

1. `frontend/llm_classifier.sh` — fachada que usa los adapters
2. `middleend/llm_ir_mapper.sh` — mapea tool calls a IR.json

Ver `031_PLAN_DEV_COMPILER_BOT_LLM_EXECUTION_1_0_DRAFT.md` seccion FASE-L2.

---

## 5. Referencias

- `031_PLAN_DEV_COMPILER_BOT_LLM_EXECUTION_1_0_DRAFT.md` — Plan de ejecucion
- `030_REP_MGT_COMPILER_BOT_LLM_INTEGRATION_1_0_DRAFT.md` — Documento base
- `000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md` — Guia de estilo shell
