---
id: 050
area: dev
type: REP
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - report
  - agent-robot
  - fase2
  - tools
  - implementation
  - dash-compat
summary: "Reporte de implementacion de la Fase 2 del plan 049: herramientas del sistema para la capa agent-robot. Cobertura: tool_read_file, tool_write_file, tool_run_command, integracion en agent.sh, tests. Incluye fix de compatibilidad con dash (echo vs printf)."
keywords:
  - report
  - fase2
  - tools
  - read-file
  - write-file
  - run-command
  - agent
  - dash
  - compatibilidad
changelog:
  - version: 1.0
    date: 2026-06-13
    author: workflow-agent
    description: Reporte de implementacion de Fase 2 — herramientas del sistema, integracion en agent.sh, tests, y fix de compatibilidad con dash
---

# Reporte de Implementacion: Fase 2 — Herramientas del Sistema

> **Plan de ejecucion:** `docs/049_PLAN_DEV_COMPILER_BOT_AGENT_EXECUTION_1_0_DRAFT.md`
> **Fase:** 2
> **Estado:** COMPLETED

---

## Resumen

La Fase 2 dota al agente de la capacidad de leer archivos, escribir archivos,
y ejecutar comandos del sistema. Se crearon 3 herramientas nuevas, se integraron
en el bucle principal del agente (`agent.sh`), y se agregaron 3 tests funcionales.

**Duracion:** ~3 horas (incluyendo debugging de compatibilidad con dash)

---

## Archivos creados

### `compiler-bot/agent-robot/tools/tool_read_file.sh`

Lee archivos del sistema y devuelve su contenido en JSON. Validaciones:
- Ruta vacia → error
- Archivo inexistente → error
- Sin permisos de lectura → error
- Exito → JSON con path, lineas, bytes, contenido

### `compiler-bot/agent-robot/tools/tool_write_file.sh`

Escribe contenido en archivos. Validaciones:
- Ruta vacia → error
- Contenido vacio → error
- Crea directorios intermedios automaticamente
- Verifica permisos de escritura
- Exito → JSON con path, bytes, mensaje

### `compiler-bot/agent-robot/tools/tool_run_command.sh`

Ejecuta comandos del sistema via `sh -c`. Retorna:
- exit_code, output, lineas, tiempo_ms
- `exito: true` si exit_code == 0

---

## Archivos modificados

### `compiler-bot/agent-robot/agent.sh`

1. **`classify_intent()`**: Agregada deteccion de intencion para las 3 herramientas
   - `read_file`: "lee", "muestra", "cat", "abre", "read"
   - `write_file`: "crea archivo", "escribe", "write", "crea el archivo", "genera archivo"
   - `run_command`: "ejecuta", "corre", "run", "executa", "lanza"
   - Las detecciones de Fase 2 se ubicaron **antes** que las de RECPL para evitar
     que "crea" (RECPL) capture "crea archivo" (write_file)

2. **`execute_intent()`**: Agregados 3 nuevos casos en el case:
   - `read_file)`: extrae ruta via sed y delega en tool_read_file
   - `write_file)`: parsea "crea archivo <ruta> con contenido <texto>"
   - `run_command)`: extrae comando via sed y delega en tool_run_command

3. **`format_response()`**: Ampliada para manejar tipos de respuesta especificos:
   - `file_content`: muestra path, lineas, y contenido
   - `command_output`: muestra output del comando
   - `file_written`: muestra mensaje de confirmacion
   - Fallback generico para mensajes de texto

4. **`main()`**: Cambiado el mecanismo de captura de respuesta:
   - **Antes:** `_result=$(execute_intent ...)` con variable en memoria
   - **Despues:** archivo temporal `/tmp/agent_result_$$.tmp`
   - `printf '%s'` en vez de `echo` para pasar JSON a jq

### `compiler-bot/agent-robot/tools/tool_respond.sh`

Reescrito para usar `jq -n --arg` en lugar de heredoc + `jq -R -s`, eliminando
riesgo de expansion de shell en el contenido del mensaje.

### `compiler-bot/tests/test_agent.sh`

- Agregados 3 tests: `test_tool_read_file`, `test_tool_write_file`, `test_tool_run_command`
- Actualizados `test_files_exist` y `test_bash_syntax` para incluir los 3 nuevos archivos
- Titulo actualizado a "Fase 1 + Fase 2"
- Suite: 10 tests funcionales

---

## Bug corregido: dash + echo + jq

### Sintoma

`format_response` mostraba `❌` (vacio) al leer archivos via agente. Write y
command funcionaban correctamente.

### Causa raiz

`/bin/sh` en este sistema es **dash**, que a diferencia de bash, interpreta
secuencias de escape (`\n`, `\t`) en `echo`. El JSON generado por
`tool_read_file` contiene `\n` escapados dentro del campo `contenido`. Al
hacer `echo "$json" | jq ...`, dash convertia los `\n` a newlines literales,
rompiendo la estructura JSON.

### Fix

1. Reemplazar `echo "$_json"` por `printf '%s' "$_json"` en toda funcion que
   procese JSON (format_response, principalmente).
2. Usar `printf` en vez de `echo` en todas las salidas de format_response para
   mantener consistencia.

### Leccion aprendida

`#!/bin/sh` no garantiza compatibilidad con bash. En Debian/Ubuntu, `/bin/sh`
es dash. Scripts que procesen JSON con jq deben usar `printf '%s'` en vez de
`echo` para evitar interpretacion de backslash sequences.

---

## Criterios de exito verificados

```sh
# 1. El agente lee archivos
./compiler-bot/agent-robot/agent.sh "lee compiler-bot/agent-robot/config.sh"
# Output: ✅ compiler-bot/agent-robot/config.sh (37 lineas)

# 2. El agente escribe archivos
./compiler-bot/agent-robot/agent.sh "crea archivo /tmp/test.txt con contenido hola mundo"
# Output: ✅ Archivo escrito correctamente (10 bytes)

# 3. El agente ejecuta comandos
./compiler-bot/agent-robot/agent.sh "ejecuta echo comando exitoso"
# Output: ✅ comando exitoso

# 4. Tests pasan
./compiler-bot/tests/test_agent.sh | grep "FAIL=0"
# Output: Fallos: ninguno
```

---

## Resultados de tests

| Suite | Tests | Pasaron | Fallaron |
|-------|-------|---------|----------|
| RECPL (run_tests.sh) | 72 | 72 | 0 |
| Agent (test_agent.sh) | 10 | 10 | 0 |

**Total:** 82 tests, 0 fallos.

---

## Archivos involucrados

| Archivo | Accion | Lineas aprox. |
|---------|--------|---------------|
| `compiler-bot/agent-robot/tools/tool_read_file.sh` | CREADO | 52 |
| `compiler-bot/agent-robot/tools/tool_write_file.sh` | CREADO | 70 |
| `compiler-bot/agent-robot/tools/tool_run_command.sh` | CREADO | 48 |
| `compiler-bot/agent-robot/agent.sh` | MODIFICADO | +60 (format_response, main, classify_intent, execute_intent) |
| `compiler-bot/agent-robot/tools/tool_respond.sh` | MODIFICADO | -5 (reescrito a jq -n) |
| `compiler-bot/tests/test_agent.sh` | MODIFICADO | +75 (3 tests, archivos en checks) |
| `docs/050_REP_DEV_COMPILER_BOT_FASE2_AGENT_TOOLS_1_0_DRAFT.md` | CREADO | Este archivo |
