---
id: 033
area: dev
type: rep
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - report
  - implementation
  - fase-l2
  - llm
  - classifier
  - facade
  - ir-mapper
  - compiler-bot
  - recpl
summary: "Reporte de implementacion de la FASE-L2 del plan 031: fachada LLM (llm_classifier.sh) y mapper IR (llm_ir_mapper.sh). Incluye archivos creados, correccion de bug de trailing newline, validaciones de sintaxis y pruebas de mapeo."
keywords:
  - reporte
  - implementacion
  - fase-l2
  - llm-classifier
  - facade
  - ir-mapper
  - validacion
  - sintaxis
  - pruebas
  - bash
changelog:
  - version: 1.0
    date: 2026-06-11
    author: workflow-agent
    description: Implementacion de FASE-L2 del plan 031 — fachada LLM y mapper IR
---

# Reporte de Implementacion: FASE-L2 — LLM Classifier (Fachada) + IR Mapper

> **Plan de referencia:** `031_PLAN_DEV_COMPILER_BOT_LLM_EXECUTION_1_0_DRAFT.md`
> **Fase anterior:** `032_REP_DEV_COMPILER_BOT_LLM_FASE_L1_1_0_DRAFT.md`
> **Guia de estilo:** `000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md`

---

## 0. Resumen

Se implemento la FASE-L2 del plan de integracion LLM: la fachada
`llm_classifier.sh` que unifica el acceso a los proveedores, y el
mapper `llm_ir_mapper.sh` que convierte tool calls a IR.json canonico.

**Estado:** COMPLETADO

---

## 1. Archivos Creados

### 1.1 `compiler-bot/frontend/llm_classifier.sh` (148 lineas)

**Proposito:** Fachada (Facade Pattern) que oculta toda la complejidad
de los proveedores LLM. El pipeline solo llama a `llm_classify` y
recibe IR.json.

**Funciones:**

| Funcion | Descripcion |
|---------|-------------|
| `get_system_prompt()` | System prompt del compilador: define rol, reglas y techs soportadas |
| `get_tools_json()` | Schema de las 6 tools que el LLM puede invocar (scaffold_module, scaffold_entity, delete_module, read_module, clarify, respond) |
| `map_tool_to_ir()` | Convierte nombre de tool + parametros a IR.json canonico |
| `llm_classify()` | Fachada principal: selecciona provider, construye payload, invoca al LLM, parsea respuesta y devuelve IR.json o respuesta textual |

**Flujo interno de `llm_classify()`:**

```
llm_classify("crea un modulo de pagos en NestJS")
    │
    ├─ 1. Determinar provider (RECPL_LLM_PROVIDER o default: claude)
    ├─ 2. Cargar adapter del proveedor (. ./providers/claude.sh)
    ├─ 3. Construir llamada:
    │      claude_complete(get_system_prompt(), instruction, get_tools_json())
    ├─ 4. Recibir respuesta en formato interno comun
    ├─ 5. Parsear response_type:
    │      ├─ "tool_use" → map_tool_to_ir() → IR.json
    │      └─ "text"     → {"accion":"respond","mensaje":"..."}
    └─ 6. Retornar resultado
```

**System prompt del compilador:**

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
SOLO USA TECHS de la lista soportada.

FORMATO DE SALIDA: Tool call con parametros exactos.
NO inventes tools que no esten en la lista.
```

**Tools expuestas al LLM (6):**

| Tool | Descripcion | Parametros |
|------|-------------|------------|
| `scaffold_module` | Crea un modulo nuevo | nombre, tech |
| `scaffold_entity` | Crea una entidad nueva | nombre, tech |
| `delete_module` | Elimina un modulo existente | nombre |
| `read_module` | Muestra informacion de un modulo | nombre |
| `clarify` | Pregunta al usuario cuando falta informacion | pregunta |
| `respond` | Responde texto directamente | mensaje |

### 1.2 `compiler-bot/middleend/llm_ir_mapper.sh` (82 lineas)

**Proposito:** Mapper independiente que lee de stdin un tool call en
formato interno comun y produce IR.json canonico. Separado de
`llm_classifier.sh` para poder usarse como filtro en pipelines shell.

**Funcion principal:** `llm_ir_mapper()` — lee JSON de stdin, extrae
`.tool`, `.nombre`, `.tech`, y produce IR.json con `jq -n --arg`.

**Ejemplo de uso:**
```sh
echo '{"tool":"scaffold_module","nombre":"Pagos","tech":"NestJS"}' \
  | compiler-bot/middleend/llm_ir_mapper.sh
# → {"accion":"scaffold","tipo":"module","nombre":"Pagos","tech":"NestJS"}
```

---

## 2. Validaciones Realizadas

### 2.1 Sintaxis (`bash -n`)

| Archivo | Resultado |
|---------|-----------|
| `frontend/llm_classifier.sh` | OK — sin errores de sintaxis |
| `middleend/llm_ir_mapper.sh` | OK — sin errores de sintaxis |

### 2.2 Mapeo de tool calls (llm_ir_mapper.sh)

Se probaron las 6 tools + caso de error. Todos los resultados son
JSON valido sin trailing newlines en los valores:

| Tool | Input | Output | Resultado |
|------|-------|--------|-----------|
| `scaffold_module` | `{"nombre":"Pagos","tech":"NestJS"}` | `{"accion":"scaffold","tipo":"module","nombre":"Pagos","tech":"NestJS"}` | ✅ |
| `scaffold_entity` | `{"nombre":"Usuario","tech":"Prisma"}` | `{"accion":"scaffold","tipo":"entity","nombre":"Usuario","tech":"Prisma"}` | ✅ |
| `delete_module` | `{"nombre":"Pagos"}` | `{"accion":"delete","tipo":"module","nombre":"Pagos"}` | ✅ |
| `read_module` | `{"nombre":"Usuarios"}` | `{"accion":"read","tipo":"module","nombre":"Usuarios"}` | ✅ |
| `clarify` | `{"pregunta":"Que modulo quieres crear?"}` | `{"accion":"clarify","mensaje":"Que modulo quieres crear?"}` | ✅ |
| `respond` | `{"mensaje":"Tienes 2 modulos disponibles"}` | `{"accion":"respond","mensaje":"Tienes 2 modulos disponibles"}` | ✅ |
| `invalid_tool` | `{"tool":"invalid_tool"}` | `{"accion":"error","mensaje":"Tool desconocida: invalid_tool"}` (exit 1) | ✅ |

### 2.3 Mapeo interno (map_tool_to_ir en llm_classifier.sh)

Se probaron las mismas 6 tools via source directo. Todos los outputs
son JSON valido sin trailing newlines:

| Tool | Output | Resultado |
|------|--------|-----------|
| `scaffold_module` | `{"accion":"scaffold","tipo":"module","nombre":"Pagos","tech":"NestJS"}` | ✅ |
| `scaffold_entity` | `{"accion":"scaffold","tipo":"entity","nombre":"Usuario","tech":"Prisma"}` | ✅ |
| `delete_module` | `{"accion":"delete","tipo":"module","nombre":"Pagos"}` | ✅ |
| `clarify` | `{"accion":"clarify","mensaje":"Que modulo quieres crear?"}` | ✅ |
| `respond` | `{"accion":"respond","mensaje":"Hola, soy el compilador"}` | ✅ |

### 2.4 Text response path

Se verifico que la ruta de respuesta textual (cuando el LLM no invoca
una tool) produce JSON valido:

```json
{"accion":"respond","mensaje":"Tienes 2 modulos: Pagos, Usuarios"}
```

### 2.5 Manejo de errores

| Prueba | Resultado |
|--------|-----------|
| `llm_classify` sin `ANTHROPIC_API_KEY` | Error claro: "ANTHROPIC_API_KEY no esta configurada" (exit 1) |
| `llm_classify` con instruccion vacia | `{"accion":"error","mensaje":"Instruccion vacia"}` |
| `llm_ir_mapper` con tool desconocida | `{"accion":"error","mensaje":"Tool desconocida: ..."}` (exit 1) |

### 2.6 Checklist FASE-L2

- [x] `frontend/llm_classifier.sh` — get_system_prompt, get_tools_json, map_tool_to_ir, llm_classify
- [x] `middleend/llm_ir_mapper.sh` — mapper separado con jq
- [x] Validacion: `bash -n` en ambos archivos
- [x] Validacion: map_tool_to_ir con cada tipo de tool (6/6 OK + error)
- [x] Validacion: llm_ir_mapper con cada tipo de tool (6/6 OK + error)
- [x] Validacion: mensaje de error sin API key

---

## 3. Bug Encontrado y Corregido

### 3.1 Trailing newlines en map_tool_to_ir

**Problema:** La implementacion inicial usaba:
```sh
echo "$params" | jq -r .nombre | jq -R -s .
```

Esto producia `"Pagos\n"` en vez de `"Pagos"` porque `jq -r` emite un
newline, y `echo` agrega otro, y `jq -R -s` codifica todo como string.

**Solucion:** Separar en dos pasos capturando el valor con `$()` (que
strippe los trailing newlines) y usando `printf '%s'` en vez de `echo`
para no reintroducirlos:
```sh
nombre=$(echo "$params" | jq -r '.nombre // ""')
...
printf '%s' "$nombre" | jq -R -s .
```

**Leccion:** `echo` siempre agrega un newline. Para pasar texto a
`jq -R -s .` sin newlines adicionales, usar `printf '%s'`.

---

## 4. Decisiones de Diseno

### 4.1 Dos niveles de mapeo

Existen dos funciones de mapeo, con diferentes propositos:

| Funcion | Ubicacion | Proposito |
|---------|-----------|-----------|
| `map_tool_to_ir()` | `llm_classifier.sh` | Mapeo interno durante el flujo de clasificacion |
| `llm_ir_mapper.sh` | `middleend/llm_ir_mapper.sh` | Script independiente para pipelines shell |

La separacion permite que otros scripts (tests, debug) usen el mapper
sin cargar toda la fachada.

### 4.2 Compact JSON para tools

`get_tools_json()` emite las tools en una sola linea (JSON compacto)
para evitar problemas de newlines al incrustarlo en el payload de curl.
El JSON compacto es funcionalmente identico al pretty-printed.

### 4.3 Provider lazy-loading

El adapter del proveedor se carga con `.` (source) solo cuando se
necesita, no al arrancar. Esto permite que `llm_classifier.sh` se
defina sin forzar la presencia de ambos adapters.

---

## 5. Proximos Pasos

Completada FASE-L2. La siguiente fase (FASE-L3) debe implementar:

1. `frontend/router.sh` — router inteligente (Strategy Pattern)
2. Modificacion de `recpl.sh` — flags `--llm`, `--provider`, integracion del router

Ver `031_PLAN_DEV_COMPILER_BOT_LLM_EXECUTION_1_0_DRAFT.md` seccion FASE-L3.

---

## 6. Referencias

- `031_PLAN_DEV_COMPILER_BOT_LLM_EXECUTION_1_0_DRAFT.md` — Plan de ejecucion
- `032_REP_DEV_COMPILER_BOT_LLM_FASE_L1_1_0_DRAFT.md` — Fase anterior (adapters)
- `000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md` — Guia de estilo shell
