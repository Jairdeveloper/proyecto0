---
id: 051
area: dev
type: rep
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - report
  - agent-robot
  - fase1
  - foundation
  - implementation
summary: "Reporte de implementacion de la Fase 1 del plan 049: Fundacion del Agente. Cobertura completa de la capa agent-robot: config, bridge, agent loop, tool registry, herramientas basicas, memoria, entrypoint global, flag --agent, y tests. Incluye bugs corregidos durante la fase."
keywords:
  - report
  - fase1
  - agent
  - foundation
  - bridge
  - recpl
  - tools
  - registry
  - memory
  - tests
changelog:
  - version: 1.0
    date: 2026-06-13
    author: workflow-agent
    description: Reporte de implementacion de Fase 1 — Fundacion del Agente (capa agent-robot sobre pipeline RECPL)
---

# Reporte de Implementacion: Fase 1 — Fundacion del Agente

> **Plan de ejecucion:** `docs/049_PLAN_DEV_COMPILER_BOT_AGENT_EXECUTION_1_0_DRAFT.md`
> **Fase:** 1
> **Estado:** COMPLETED

---

## Resumen

La Fase 1 establece la **capa agent-robot** sobre el pipeline RECPL existente.
Crea un agente shell que recibe instrucciones en lenguaje natural, clasifica la
intencion (via heuristica de palabras clave), delega en RECPL via bridge, o
responde textualmente.

**Objetivo del plan:** `agent.sh` funcional que recibe instrucciones, clasifica
intencion, delega en RECPL via bridge, o responde textualmente.

**Duracion real:** ~5 horas (incluyendo debugging de compatibilidad con dash)

---

## Arquitectura de la capa agent-robot

```
USUARIO → agent-robot.sh → agent.sh → classify_intent()
                                         ├── "respond" → tool_respond()
                                         ├── "help"    → show_help()
                                         ├── "recpl"   → bridge.sh → recpl.sh
                                         └── (default) → bridge.sh → recpl.sh

                                 bridge.sh
                                   ├── bridge_recpl() → recpl.sh -c
                                   ├── bridge_debug() → pipeline_debugger.sh --output
                                   └── bridge_state() → RECPL_STATE_DIR
```

---

## Archivos creados

### `compiler-bot/agent-robot/config.sh`

Variables de entorno del agente con valores por defecto:

| Variable | Default | Descripcion |
|----------|---------|-------------|
| `AGENT_LLM_MODE` | `auto` | Modo de operacion: auto, llm, deterministic |
| `AGENT_LLM_PROVIDER` | `""` | Proveedor LLM preferido |
| `AGENT_LLM_TIER` | `auto` | Capa LLM: free, paid, auto |
| `AGENT_MEMORY_DIR` | `/tmp/agent_memory` | Directorio de memoria persistente |
| `AGENT_LOG_FILE` | `/tmp/agent.log` | Archivo de log |
| `AGENT_VERSION` | `1.0.0` | Version del agente |
| `AGENT_PREFIX` | `🤖` | Prefijo visual en respuestas |

### `compiler-bot/agent-robot/bridge.sh`

Adapter unidireccional entre agent-robot y el pipeline RECPL. Proporciona 3
funciones:

- **`bridge_recpl(instruction)`**: Ejecuta `recpl.sh -c` y devuelve JSON
  estructurado con `exito`, `origen`, `tipo_respuesta`, `mensaje`, `payload`,
  `raw`, `tiempo_ms`. Maneja 3 casos: exito con JSON, exito con texto, error.
- **`bridge_debug(instruction)`**: Ejecuta `pipeline_debugger.sh --output`
  para obtener trazabilidad completa del pipeline.
- **`bridge_state()`**: Consulta el directorio `RECPL_STATE_DIR` y devuelve
  snapshot de la tabla de simbolos actual.

### `compiler-bot/agent-robot/agent.sh`

Bucle principal del agente. Flujo de ejecucion:

1. Carga `config.sh` y `memory.sh`
2. Inicializa memoria y log
3. Parsea argumentos (--llm, --deterministic, --help, --version)
4. Recibe instruccion (argumento o stdin)
5. Clasifica intencion via `classify_intent()` — heuristica de palabras clave
6. Ejecuta la accion via `execute_intent()` — case dispatch
7. Formatea la respuesta via `format_response()`
8. Guarda en historial y log

**Clasificador heuristico de intencion (orden de precedencia):**

| Patron | Intencion | Accion |
|--------|-----------|--------|
| `^(hola\|buenas\|hey\|quien eres\|que eres)` | `respond` | Saludo |
| `^(adios\|chao\|bye\|hasta luego)` | `respond` | Despedida |
| `^(gracias\|thanks)` | `respond` | Agradecimiento |
| `^(ayuda\|help)` | `help` | Mostrar ayuda |
| `^(crea\|genera\|elimina\|lista\|...` | `recpl` | Delegar en RECPL |
| `(crea \|genera \|elimina \|...)` | `recpl` | RECPL (medio) |
| default | `recpl` | Fallback a RECPL |

### `compiler-bot/agent-robot/memory.sh`

Sistema de memoria persistente del agente. Almacenamiento en archivo JSON en
`AGENT_MEMORY_DIR`. Funciones:

| Funcion | Descripcion |
|---------|-------------|
| `memory_init()` | Inicializa archivo de memoria y log |
| `memory_save(key, value)` | Guarda valor en contexto |
| `memory_get(key)` | Recupera valor del contexto |
| `memory_add_history(inst, resp)` | Agrega entrada al historial |
| `memory_history()` | Obtiene historial completo |
| `memory_context()` | Obtiene contexto completo |
| `memory_last(n)` | Obtiene ultimas N instrucciones |
| `memory_log(msg)` | Registra mensaje en archivo de log |

### `compiler-bot/agent-robot/tools/tool_registry.sh`

Registro central de herramientas del agente. Formato de registro:

```
nombre:script_relativo:descripcion:parametros_json
```

Funciones:

| Funcion | Descripcion |
|---------|-------------|
| `list_tools()` | Lista herramientas disponibles |
| `has_tool(name)` | Verifica existencia (0/1) |
| `get_tool_script(name)` | Obtiene script relativo |
| `get_tool_desc(name)` | Obtiene descripcion |
| `run_tool(name, params...)` | Ejecuta herramienta por nombre |

**Registro inicial (6 herramientas):**

| Nombre | Script | Proposito |
|--------|--------|-----------|
| `recpl` | `tool_recpl.sh` | Ejecuta instrucciones RECPL |
| `respond` | `tool_respond.sh` | Responde textualmente al usuario |
| `read_file` | `tool_read_file.sh` | Lee archivos (Fase 2) |
| `write_file` | `tool_write_file.sh` | Escribe archivos (Fase 2) |
| `run_command` | `tool_run_command.sh` | Ejecuta comandos (Fase 2) |
| `search_code` | `tool_search_code.sh` | Busca en codigo (Fase 3) |

### `compiler-bot/agent-robot/tools/tool_recpl.sh`

Herramienta que delega en RECPL via bridge. Carga `bridge.sh` y llama a
`bridge_recpl(instruction)`.

### `compiler-bot/agent-robot/tools/tool_respond.sh`

Herramienta de respuesta textual. Devuelve JSON con `tipo_respuesta: "respond"`
y el mensaje codificado como JSON string. Construye la respuesta mediante
`jq -n --arg` para evitar problemas de expansion de shell.

### `compiler-bot/agent-robot.sh`

Entrypoint global que delega en `agent-robot/agent.sh`:

```sh
#!/bin/sh
SCRIPT_DIR="$(dirname "$0")"
exec "$SCRIPT_DIR/agent-robot/agent.sh" "$@"
```

---

## Archivos modificados

### `compiler-bot/recpl.sh` (+3 lineas)

Agregado el flag `--agent` / `--robot` en el parseo de argumentos:

```sh
--agent|--robot)
    shift
    exec "$SCRIPT_DIR/agent-robot.sh" "$@"
    ;;
```

Esto permite invocar al agente directamente desde la CLI de RECPL:
```sh
./recpl.sh --agent "hola"
./recpl.sh --robot "crea modulo payments en nestjs"
```

---

## Bugs corregidos durante Fase 1

### Bug 1: Sintaxis incorrecta en `tool_registry.sh`

**Archivo:** `compiler-bot/agent-robot/tools/tool_registry.sh`
**Linea:** 72
**Error:** `}` donde deberia ser `fi` en bloque `if`

```sh
# ANTES (roto):
    if [ ! -f "$_tool_path" ]; then
        echo "{\"exito\":false,\"mensaje\":\"Script de herramienta no encontrado: $_script\"}"
        return 1
    }

# DESPUES (corregido):
    if [ ! -f "$_tool_path" ]; then
        echo "{\"exito\":false,\"mensaje\":\"Script de herramienta no encontrado: $_script\"}"
        return 1
    fi
```

**Impacto:** El syntax check (`bash -n`) fallaba en `tool_registry.sh`, y
cualquier script que sourceara este archivo recibia un error de sintaxis.

### Bug 2: Dependencia `jq` no instalada

**Contexto:** Toda la capa agent-robot depende de `jq` para parsing y
generacion de JSON (tool_respond, memory, tool_registry, bridge).

**Solucion:** Instalar `jq` via binario estatico desde jqlang/jq releases
(v1.7.1 linux-amd64). **No** usar el paquete npm `jq`, que es un wrapper
Node.js incompleto que falla al parsear JSON.

### Bug 3: `echo` de dash interpreta secuencias de escape

**Shell:** `/bin/sh` es **dash** en Debian/Ubuntu (no bash).
**Problema:** `echo "\n"` en dash imprime una nueva linea literal en vez de
`\n`. Cuando el JSON contiene `\n` escapados (ej: contenido de archivos),
`echo "$json" | jq ...` produce JSON invalido.

**Fix:** Usar `printf '%s' "$json"` en vez de `echo "$json"` en todas las
funciones que procesan JSON. Este fix se aplico en Fase 2 (descubierto durante
la integracion de herramientas del sistema).

---

## Tests de Fase 1

**Archivo:** `compiler-bot/tests/test_agent.sh`

7 tests funcionales:

| Test | Descripcion |
|------|-------------|
| `test_files_exist` | Verifica que los 7 archivos base existen |
| `test_bash_syntax` | Verifica `bash -n` en los 7 archivos |
| `test_tool_respond` | `tool_respond "test message"` devuelve `exito: true` con el mensaje |
| `test_tool_registry` | `has_tool("respond")` devuelve yes |
| `test_memory` | `memory_save/get` persiste y recupera valores |
| `test_agent_greeting` | `agent.sh "hola"` responde con saludo |
| `test_agent_identity` | `agent.sh "quien eres?"` responde identidad |
| `test_bridge_recpl` | Bridge delegua en RECPL (warning si RECPL falla) |
| `test_agent_flag` | `recpl.sh --agent "hola"` invoca al agente |

---

## Criterios de exito verificados

```sh
# 1. El agente responde comandos RECPL
./compiler-bot/agent-robot/agent.sh "crea modulo payments en nestjs"
# Output: 🤖 Proyecto0(RECPL) v1.0.0
#         ✅ ...

# 2. El agente responde textualmente
./compiler-bot/agent-robot/agent.sh "hola"
# Output: 🤖 Proyecto0(RECPL) v1.0.0
#         ✅ Hola! Soy Proyecto0(RECPL)...

# 3. El flag --agent funciona desde recpl.sh
./compiler-bot/recpl.sh --agent "hola"
# Output: 🤖 Proyecto0(RECPL) v1.0.0

# 4. Tests pasan
./compiler-bot/tests/test_agent.sh
# Output: FAIL=0

# 5. Syntax check de todos los archivos nuevos
bash -n compiler-bot/agent-robot/*.sh
bash -n compiler-bot/agent-robot/tools/*.sh
# Todos OK
```

---

## Resultados de tests

| Suite | Tests | Pasaron | Fallaron |
|-------|-------|---------|----------|
| RECPL (run_tests.sh) | 72 | 72 | 0 |
| Agent (test_agent.sh) | 7 | 7 | 0 |

---

## Archivos involucrados (solo Fase 1)

| Archivo | Accion | Proposito |
|---------|--------|-----------|
| `compiler-bot/agent-robot/config.sh` | CREADO | Variables de entorno del agente |
| `compiler-bot/agent-robot/bridge.sh` | CREADO | Adapter unidireccional a RECPL |
| `compiler-bot/agent-robot/agent.sh` | CREADO | Bucle principal del agente |
| `compiler-bot/agent-robot/memory.sh` | CREADO | Memoria persistente del agente |
| `compiler-bot/agent-robot/tools/tool_registry.sh` | CREADO | Registro central de herramientas |
| `compiler-bot/agent-robot/tools/tool_recpl.sh` | CREADO | Herramienta RECPL via bridge |
| `compiler-bot/agent-robot/tools/tool_respond.sh` | CREADO | Herramienta de respuesta textual |
| `compiler-bot/agent-robot.sh` | CREADO | Entrypoint global |
| `compiler-bot/recpl.sh` | MODIFICADO | Flag --agent agregado |
| `compiler-bot/tests/test_agent.sh` | CREADO | Suite de tests de Fase 1 |

---

## Dependencias externas

| Dependencia | Version | Instalacion | Proposito |
|-------------|---------|-------------|-----------|
| `jq` | 1.7.1 | Binario estatico (jqlang/jq) | Parsing y generacion de JSON |
| `recpl.sh` | 1.6.0 | Propio | Pipeline RECPL subyacente |
| `pipeline_debugger.sh` | 1.4.0 | Propio | Trazabilidad del pipeline |

---

## Estado de transicion a Fase 2

Al finalizar Fase 1, la capa agent-robot puede:

- [x] Recibir instrucciones via argumento o stdin
- [x] Clasificar intencion por palabras clave (saludo, ayuda, RECPL)
- [x] Delegar en RECPL via bridge con respuesta estructurada
- [x] Responder textualmente a saludos y preguntas de identidad
- [x] Mantener historial de conversacion y contexto en memoria
- [x] Invocarse desde recpl.sh via flag --agent
- [x] Pasar 7 tests funcionales + 72 tests RECPL

Limitaciones conocidas al finalizar Fase 1:

- [ ] No puede leer archivos (Fase 2)
- [ ] No puede escribir archivos (Fase 2)
- [ ] No puede ejecutar comandos (Fase 2)
- [ ] No puede planificar tareas multi-paso (Fase 3)
- [ ] No tiene prompts de sistema (Fase 4)
