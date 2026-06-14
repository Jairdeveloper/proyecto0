---
id: 060
area: dev
type: REP
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - report
  - audit
  - inconsistencies
  - code-quality
  - technical-debt
summary: "Reporte de inconsistencias del codigo del RECPL Compiler Bot. Cubre 88 hallazgos en 11 categorias: shebangs faltantes, dead code, features documentadas no implementadas, typos en variables, inyeccion JSON, dependencia de SCRIPT_DIR, paths hardcodeados, issues de shellcheck, error handling faltante, naming inconsistente y otros bugs. Incluye priorizacion de correcciones."
keywords:
  - report
  - audit
  - inconsistencies
  - bugs
  - code-quality
  - technical-debt
  - shell
  - json-injection
  - dead-code
changelog:
  - version: 1.0
    date: 2026-06-13
    author: workflow-agent
    description: Reporte de inconsistencias del codigo — 88 hallazgos, 11 categorias, priorizacion de correcciones
---

# Reporte de Inconsistencias: RECPL Compiler Bot

## Resumen Ejecutivo

Se audito el arbol `compiler-bot/` en busca de inconsistencias de codigo,
features documentadas no implementadas, bugs y malas practicas. Se
encontraron **88 hallazgos** en **11 categorias**.

| Categoria | Count | Severidad |
|-----------|-------|-----------|
| Shebangs faltantes | 6 | Media |
| Dead code (funciones no llamadas) | 7 | Baja |
| Documentado pero no implementado | 3 features | Alta |
| Typos en variables | 1 | Alta (rompe debug) |
| Inyeccion JSON | 7 sitios | Alta |
| Dependencia de SCRIPT_DIR | 3 archivos | Media |
| Paths hardcodeados (`/tmp/`) | 30+ sitios | Media |
| Issues ShellCheck | 6 | Media-Alta |
| Error handling faltante | 10+ sitios | Media |
| Naming inconsistente | 6 funciones | Baja |
| Otros bugs | 5 | Alta |

---

## 1. Shebangs Faltantes

Seis archivos `.sh` carecen de `#!/bin/sh` o `#!/bin/bash` en la primera
linea. Comienzan directamente con un banner comentario.

| # | Archivo | Primera linea | Notas |
|---|---------|---------------|-------|
| 1 | `frontend/llm_classifier.sh` | `# =====` | Tiene guarda de entry point (l.189), puede ejecutarse standalone |
| 2 | `frontend/router.sh` | `# =====` | Tiene guarda de entry point (l.174), puede ejecutarse standalone |
| 3 | `middleend/llm_ir_mapper.sh` | `# =====` | Solo para source |
| 4 | `providers/claude.sh` | `# =====` | Solo para source |
| 5 | `providers/openai.sh` | `# =====` | Solo para source |
| 6 | `providers/provider_common.sh` | `# =====` | Solo para source |

**Riesgo:** `llm_classifier.sh` y `router.sh` tienen guardas y pueden
invocarse directamente. Sin shebang, el kernel puede rechazar la ejecucion
via `./script.sh` si el shell no auto-detecta.

---

## 2. Dead Code (Funciones Definidas No Llamadas)

| # | Funcion | Archivo | Linea | Notas |
|---|---------|---------|-------|-------|
| 1 | `list_tools()` | `agent-robot/tools/tool_registry.sh` | 22 | Nunca llamada |
| 2 | `get_tool_desc()` | `agent-robot/tools/tool_registry.sh` | 47 | Nunca llamada |
| 3 | `memory_set_session()` | `agent-robot/memory.sh` | 141 | Nunca llamada |
| 4 | `memory_export()` | `agent-robot/memory.sh` | 149 | Nunca llamada |
| 5 | `bridge_debug()` | `agent-robot/bridge.sh` | 87 | Nunca llamada |
| 6 | `bridge_state()` | `agent-robot/bridge.sh` | 142 | Nunca llamada |
| 7 | `timeout_run()` | `agent-robot/agent.sh` | 51 | Definida pero no usada en ningun code path |

**Nota:** `_memory_read()` / `_memory_write()` usan prefijo `_`
(convencion privada) y SI son llamadas internamente.

---

## 3. Documentado Pero No Implementado

### 3a. `tool_edit`, `tool_delete`, `tool_list`

Mencionados en documentacion (`docs/047_PROP`) y en el patron del tool
registry, pero **no existen** como archivos `tool_edit.sh`,
`tool_delete.sh` o `tool_list.sh` en `agent-robot/tools/`.

### 3b. `apifreellm`

- `tui.sh:53` — el prompt TUI ofrece `"claude, openai, apifreellm"`
- `agent.sh:20` — documenta `AGENT_LLM_PROVIDER  claude|openai|apifreellm`
- `docs/045_PROP_DEV_COMPILER_BOT_PROVIDER_APIFREELLM_1_0_DRAFT.md` —
  propuesta completa
- **Realidad:** No existe `providers/apifreellm.sh`. Seleccionar
  `apifreellm` en TUI produce error silencioso
  (`llm_classifier.sh:158`: `*) echo "...Provider no soportado..."`).

### 3c. `AGENT_LLM_TIER`

- `config.sh:25`: `AGENT_LLM_TIER="${AGENT_LLM_TIER:-auto}"`
- `agent.sh:21`: documentado como `free|paid|auto`
- **Realidad:** `AGENT_LLM_TIER` **nunca se lee** en ningun lado. Ningun
  branch decisiona sobre su valor. Variable de configuracion muerta.

---

## 4. Typos en Variables

### `pipeline_debugger.sh:374-375`

```sh
# Linea 374: define _sym_file (con underscore)
for _sym_file in "$_state_dir"/*; do
    # Linea 375: referencia _symFile (capital F, sin underscore) — NUNCA ASIGNADA
    ...head -c 80 "$_symFile" 2>/dev/null)
```

**Impacto:** `$_symFile` siempre es `""`, por lo que `head -c 80 ""` lee
de stdin (cuelga) o produce salida vacia. El listado del state directory
en modo debug/trace esta roto.

---

## 5. Inyeccion JSON

### 5a. `recpl.sh:111,119`

```sh
# Linea 111: $raw_input es controlado por el usuario
echo "{\"tipo_respuesta\":\"error\",\"mensaje\":\"Error al procesar: $raw_input\",...}"

# Linea 119: $accion, $mensaje vienen de jq -r pero se injectan sin escape
echo "{\"tipo_respuesta\":\"$accion\",\"mensaje\":\"$mensaje\",...}"
```

### 5b. `backend/synthesis.sh:87-154`

Todas las funciones `execute_*` construyen JSON via `echo` con
interpolacion de variables. Cualquier variable con `"`, newlines o
caracteres de control produce JSON invalido.

### 5c. `providers/provider_common.sh:56`

```sh
echo "{ \"type\": \"tool_use\", \"tool\": \"$tool_name\", ... }"
```

**Impacto:** Un usuario escribiendo `crea modulo "pagos" en nestjs`
puede producir JSON malformado, rompiendo el parsing en el bridge.

---

## 6. Dependencia de `SCRIPT_DIR`

### 6a. `agent-robot/memory.sh`

NO define `SCRIPT_DIR` ni sourcea `config.sh`. Depende de que el script
que lo sourcee (`agent.sh`) haya seteado `AGENT_MEMORY_DIR`. Si se
sourcea independientemente, falla porque `AGENT_MEMORY_DIR` no esta
definido.

### 6b. `agent-robot/planner.sh:120`

```sh
_result=$(cd "$SCRIPT_DIR" && ./agent.sh "$_inst" 2>/dev/null)
```

`SCRIPT_DIR` no se define en este archivo. Depende de ser sourceado por
`agent.sh`. Si se sourcea fuera de ese contexto (e.g. desde
`planner_llm.sh`), `$SCRIPT_DIR` puede no estar definido.

### 6c. `agent-robot/planner_llm.sh:20`

```sh
SCRIPT_DIR_PLANNER="${SCRIPT_DIR:-agent-robot}"
```

El fallback `agent-robot` es una ruta relativa. Si el CWD no es el
project root, `cd "$SCRIPT_DIR_PLANNER/.."` (l.53) falla silenciosamente.

---

## 7. Paths Hardcodeados (`/tmp/`)

Uso extensivo de `/tmp/` en todo el codebase (~30 sitios). Riesgo en
entornos multi-tenant y potencial de conflictos entre instancias.

Archivos afectados: `recpl.sh`, `pipeline_debugger.sh`, `agent.sh`,
`config.sh`, `memory.sh`, `bridge.sh`, `router.sh`, `semantic.sh`,
`parser.sh`, `lexer.sh`, `preprocessor.sh`, `ir_generator.sh`,
`synthesis.sh`, `scaffold.sh`, `tests/run_tests.sh`,
`tests/test_agent.sh`, `tests/test_router.sh`.

**Riesgo:** Paths basados en PID (`/tmp/recpl_state_$$`) son predecibles
si se adivina el PID. Varios archivos carecen de `trap` de limpieza.

---

## 8. Issues ShellCheck

### 8a. `pipeline_debugger.sh:374` — Unquoted glob expansion

```sh
for _sym_file in "$_state_dir"/*; do
```
Si `$_state_dir` esta vacio, expande a `/*` — lista TODO el filesystem.

### 8b. `agent-robot/bridge.sh:114-115` — Environment variable scoping bug

```sh
_raw_output=$(RECPL_LLM_PROVIDER="$_provider" \
    cd "$BRIDGE_SCRIPT_DIR" && ./recpl.sh --llm -c "$_instruction" 2>/dev/null)
```

`RECPL_LLM_PROVIDER` solo se setea para `cd`, NO para `./recpl.sh`. El
flag `--provider` es efectivamente ignorado via bridge.

### 8c. `providers/provider_common.sh:56,65` — JSON manual

`$tool_name` y texto de respuesta se injectan sin escape en JSON.

### 8d. `backend/synthesis.sh:87-154` — JSON manual en todas las execute_*

Variables como `$nombre_cap`, `$tech`, `$template`, `$tipo` vienen de
`json_field()` (parsing con `awk`) — si el IR contiene quotes, el JSON
se rompe.

### 8e. `agent-robot/tools/tool_search_code.sh:24` — `|| echo 0` mascarado

```sh
_count=$(echo "$_results" | grep -c . 2>/dev/null || echo 0)
```
`|| echo 0` mascara fallos de `grep`, retornando `0` incluso si `grep`
falla por razones distintas a "sin matches".

### 8f. `agent-robot/agent.sh:35` — Mutable trap override

```sh
trap 'echo "..."; exit 0' INT TERM
```
Si `agent.sh` es sourceado por otro script, sobreescribe el trap del
padre.

---

## 9. Error Handling Faltante

### 9a. Sin checks de existencia antes de ejecutar scripts

- `recpl.sh:100-108`: Llama a `preprocessor.sh` y `router.sh` sin
  verificar que existan.
- `agent-robot/bridge.sh:28`: `./recpl.sh -c "$_instruction"` — sin
  check de existencia.
- `agent-robot/bridge.sh:90`: `./pipeline_debugger.sh --output` — sin
  check.
- `agent-robot/agent.sh:251`: `. "$SCRIPT_DIR/bridge.sh"` — sin check
  antes de sourcear.
- `frontend/router.sh:80-84`: Llama a `preprocessor.sh` y `lexer.sh` sin
  verificar existencia.

### 9b. Sin traps de limpieza para archivos temporales

- `frontend/lexer.sh`: Crea `$TOKEN_FILE` pero no tiene `trap` de
  limpieza (contrasta con `parser.sh:33` que SI tiene).
- `frontend/preprocessor.sh`: No tiene trap en `LOG_FILE`.

### 9c. `run_stage()` sobreescribe estado global

`pipeline_debugger.sh:186-192`: Escribe en variables globales
`_STAGE_EXIT_CODE`, `_STAGE_ELAPSED`, etc. Sin aislamiento entre etapas.

---

## 10. Naming Inconsistente

### 10a. Funciones en espanol (3) vs ingles (resto)

| Funcion | Archivo | Linea | Idioma |
|---------|---------|-------|--------|
| `planificar()` | `planner.sh` | 20 | Espanol |
| `ejecutar_plan()` | `planner.sh` | 102 | Espanol |
| `planificar_llm()` | `planner_llm.sh` | 23 | Espanol |

### 10b. Prefijo `_` inconsistente

- `_memory_read()`, `_memory_write()` — usan prefijo (convencion privada)
- `log()`, `json_field()`, `capitalize()` — deberian tener prefijo `_`
  pero no lo usan

### 10c. `json_field()` duplicado en 3 archivos

1. `backend/synthesis.sh:28` — implementacion con `awk`
2. `frontend/semantic.sh:117` — implementacion con `awk`
3. `frontend/parser.sh:51` — implementacion con `awk`

Cada una es ligeramente diferente. Violacion DRY.

---

## 11. Otros Bugs

### 11a. `--output` mode en `pipeline_debugger.sh` esta roto

```sh
# Lineas 752-755
if $_output_only; then
    debug_trace "$_instruction" >/dev/null 2>&1
    exit 0
fi
```

El modo `--output` esta documentado como "Solo el JSON final a stdout
(for piping)" pero la salida se redirige a `/dev/null`. Zero output.

### 11b. `llm_ir_mapper.sh:81` — Sin guarda de entry point

```sh
llm_ir_mapper   # Se ejecuta al final del archivo incondicionalmente
```

A diferencia de `router.sh` y `llm_classifier.sh` que tienen guarda, este
archivo ejecuta su logica siempre que es sourceado.

### 11c. `TOOL_REGISTRY` no usado fuera de `tool_registry.sh`

`list_tools`, `get_tool_script`, `get_tool_desc`, `run_tool` estan
definidos pero `agent.sh` NO usa `tool_registry.sh` — sourcea
directamente los archivos individuales de herramientas.

### 11d. `modules/` en `.gitignore` sin proteccion de directorio

`synthesis.sh:71` hardcodea `output_dir="modules/${lowername}"` relativo
a CWD. Si CWD no es el project root, los archivos se escriben en
ubicaciones inesperadas.

### 11e. Shell `sh` vs `bash` incompatibilidad potencial

Varios scripts usan `#!/bin/sh` pero contienen caracteristicas de bash
(e.g. `$((_c + 1))` sin `$` en la variable es POSIX, pero patrones como
`sh -c` con redirecciones a fd3 pueden comportarse distinto en dash).

---

## Priorizacion de Correcciones

### Criticas (Alta prioridad)

1. **`pipeline_debugger.sh:375`** — `$_symFile` typo (variable no
   asignada, debug trace roto)
2. **`pipeline_debugger.sh:752-755`** — modo `--output` redirige a
   `/dev/null`, zero output
3. **`recpl.sh:111,119`** — Inyeccion JSON: usar `jq -n --arg` en lugar
   de `echo` con interpolacion
4. **`bridge.sh:114-115`** — Environment variable scoping bug: provider
   ignorado
5. **`pipeline_debugger.sh:374`** — Glob expansion peligrosa si
   `$_state_dir` esta vacio

### Altas

6. `synthesis.sh:87-154` — JSON builders manuales → migrar a `jq -n`
7. `provider_common.sh:56` — JSON builder manual
8. `tui.sh:53` — `apifreellm` no implementado, no deberia aparecer en
   el menu TUI

### Medias

9. `llm_ir_mapper.sh:81` — Anadir guarda de entry point
10. `planner.sh:120` — `SCRIPT_DIR` no definido localmente
11. `config.sh:25` — `AGENT_LLM_TIER` muerto → remover o implementar
12. `memory.sh` — No sourcea `config.sh` para defaults
13. `lexer.sh` — Sin `trap` de limpieza para `$TOKEN_FILE`
14. `planner_llm.sh:20` — Fallback relativo fragil

### Bajas

15. `tool_registry.sh` — Dead code (`list_tools`, `get_tool_desc`)
16. `memory.sh` — Dead code (`memory_set_session`, `memory_export`)
17. `bridge.sh` — Dead code (`bridge_debug`, `bridge_state`)
18. `agent.sh` — Dead code (`timeout_run`)
19. `synthesis.sh` — `json_field()` duplicado en 3 archivos
20. Shebangs faltantes en 6 archivos

---

## Referencias

- `docs/043_REP_DEV_COMPILER_BOT_PIPELINE_RE_1_0_DRAFT.md` — Ingenieria
  inversa del pipeline (3 bugs detectados previamente)
- `docs/041_REP_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_1_0_ACTIVE.md` —
  Reporte del debugger
- `docs/045_PROP_DEV_COMPILER_BOT_PROVIDER_APIFREELLM_1_0_DRAFT.md` —
  Propuesta de proveedor apifreellm (no implementado)
- `docs/059_GUIDE_DEV_COMPILER_BOT_ARCHITECTURE_1_0_DRAFT.md` — Guia de
  arquitectura del compilador
