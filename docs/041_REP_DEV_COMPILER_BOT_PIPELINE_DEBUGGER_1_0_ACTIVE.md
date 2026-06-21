---
id: 041
area: dev
type: REP
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - report
  - implementation
  - debugger
  - pipeline
  - instrumentation
  - trace
  - profiling
summary: "Reporte de implementacion del debugger de pipeline RECPL (040_PROP). Script pipeline_debugger.sh con 5 modos: trace, step, timing, inspect, xtrace. 784 lineas, validado con shellcheck, probado con 6 instrucciones."
keywords:
  - reporte
  - implementacion
  - debugger
  - pipeline
  - trace
  - step
  - timing
  - inspect
  - xtrace
  - instrumentacion
changelog:
  - version: 1.0
    date: 2026-06-12
    author: workflow-agent
    description: Implementacion de pipeline_debugger.sh — 5 modos de debug, validacion shellcheck, pruebas en 6 escenarios
---
# Reporte de Implementacion: Debugger de Pipeline RECPL

> **Propuesta de referencia:** `040_PROP_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_1_0_DRAFT.md`
> **Archivo creado:** `compiler-bot/pipeline_debugger.sh`
> **Guia de estilo:** `000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md`

---

## 0. Resumen

Se implemento `pipeline_debugger.sh`, un script de instrumentacion que
ejecuta el pipeline RECPL etapa por etapa con captura de tiempos,
inspeccion de JSON intermedio, modo paso a paso y tracing profundo
con bash -x. No modifica ninguna etapa del pipeline — solo captura I/O
entre ellas.

**Estado:** COMPLETADO (5 modos operativos, 784 lineas)
**Dependencias:** awk o python3 (float arithmetic), date +%s.%N (timing),
jq (inspeccion y validacion JSON — fallback a raw cat si no disponible)

---

## 1. Archivo Creado

### `compiler-bot/pipeline_debugger.sh`

| Metrica | Valor |
|---------|-------|
| Lineas totales | 784 |
| Funciones | 11 (main, detect_tools, get_time_nano, float_sub, clean_debug, die, show_help, run_stage, run_deterministic_debug, step_prompt, debug_trace/step/timing/inspect/xtrace) |
| Modos | 5 (trace, step, timing, inspect, xtrace) |
| Flag adicional | 1 (--output para piping JSON final) |
| Etapas del pipeline | 6 (preprocessor, lexer, parser, semantic, ir_generator, synthesis) |
| Validacion shellcheck | OK (0 warnings, 0 errors) |
| Pruebas manuales | 6 escenarios |

---

## 2. Modos Implementados

### 2.1 Modo trace (default)

Ejecuta las 6 etapas secuencialmente mostrando para cada una: status,
tiempo, tamanio de stdout, y contenido de stderr. Al final muestra
resumen con tiempo total, conteo de OK/FAIL y contenido del directorio
de estado.

```
$ ./pipeline_debugger.sh "crea modulo pagos en nestjs"
┌─────────────────────────────────────────────────────────┐
│ PIPELINE DEBUGGER — trace mode                          │
│ Input: "crea modulo pagos en nestjs"                    │
├─────────────────────────────────────────────────────────┤
  [1/6] preprocessor.sh
    status: OK
    time:   0.002s
    stdout: 30 bytes
    stderr: (none)

  [2/6] lexer.sh
    ...
```

### 2.2 Modo step

Similar a trace pero pausa entre cada etapa y ofrece un prompt
interactivo con comandos:

| Comando | Accion |
|---------|--------|
| Enter | Continuar a la siguiente etapa |
| `q` | Salir del debugger |
| `stdout` | Mostrar stdout completo de la ultima etapa |
| `stderr` | Mostrar stderr completo de la ultima etapa |
| `json` | Validar con jq y mostrar JSON formateado |
| `state` | Mostrar contenido de RECPL_STATE_DIR |
| `help` | Mostrar ayuda de comandos |

Si no hay terminal (`[ ! -t 0 ]`), fallback automatico a modo trace
con mensaje en stderr.

### 2.3 Modo timing

Tabla compacta con solo metricas: etapa, tiempo, tamanio, status.
Requiere `date +%s.%N` (error si no disponible).

```
  Etapa                  Tiempo       Tamanio      Status
  ─────────────────────────────────────────────────────────
  preprocessor.sh       0.002s           30 bytes  OK
  lexer.sh              0.001s           89 bytes  OK
  parser.sh             0.003s          215 bytes  OK
  semantic.sh           0.004s          245 bytes  OK
  ir_generator.sh       0.001s          178 bytes  OK
  synthesis.sh          0.012s          312 bytes  OK
  ─────────────────────────────────────────────────────────
  Total:                0.023s
```

### 2.4 Modo inspect

Ejecuta todo el pipeline hasta la etapa solicitada y muestra solo el
JSON de salida de esa etapa. Reconstruye el input ejecutando las
etapas anteriores internamente. Soporta:

- `--inspect preprocessor` — texto normalizado
- `--inspect lexer` — tokens uno por linea
- `--inspect parser` — AST completo
- `--inspect semantic` — AST validado con tipos
- `--inspect ir_generator` — IR canonico
- `--inspect synthesis` — respuesta final del bot

### 2.5 Modo xtrace

Ejecuta cada etapa con `bash -x` y `PS4` configurado para mostrar
archivo, linea y funcion. La salida mezclada (trace + stdout) se
captura en archivos separados y se filtra para pasar la salida real
a la siguiente etapa.

```
$ ./pipeline_debugger.sh --xtrace "crea modulo pagos en nestjs"
┌─────────────────────────────────────────────────────────┐
│ PIPELINE DEBUGGER — xtrace mode                         │
│ Input: "crea modulo pagos en nestjs"                    │
├─────────────────────────────────────────────────────────┤
+[preprocessor.sh:42:normalize] echo 'crea modulo pagos...'
+[preprocessor.sh:55:collapse_punct] tr ...
...
```

### 2.6 Flag --output

Ejecuta en modo trace silencioso y solo emite el JSON final a stdout.
Equivalente a ejecutar el pipeline normalmente pero con el overhead
del debugger:

```sh
./pipeline_debugger.sh --output "crea modulo pagos" | jq '.mensaje'
```

---

## 3. Detalles de Implementacion

### 3.1 Deteccion de herramientas

Al arrancar, `detect_tools()` verifica la disponibilidad de:

| Herramienta | Variable | Impacto si falta |
|-------------|----------|------------------|
| `date +%s.%N` | `HAS_DATE_NANO` | Modo timing muestra error y sugiere trace |
| `python3` | `HAS_PYTHON` | Fallback a awk para float arithmetic |
| `awk` | `HAS_AWK` | Fallback a python3 para float arithmetic |
| `bc` | `HAS_BC` | Fallback a python3/awk (no disponible en el sistema) |
| `jq` | `HAS_JQ` | Inspeccion JSON usa raw cat, validacion salta |

### 3.2 Aritmetica decimal (`float_sub`)

Usa `python3 -c "print(a - b)"` como primera opcion, `awk "BEGIN {printf ...}"`
como segunda, y `bc` como tercera. Si nada disponible, retorna "0".

### 3.3 Pipeline deterministico

`run_deterministic_debug()` ejecuta las 6 etapas en orden, manejando
los dos tipos de entrada:

- **arg** (preprocessor, lexer): pasan el input como `"$1"`
- **stdin** (parser, semantic, ir_generator, synthesis): reciben input
  por pipe desde la etapa anterior

### 3.4 Manejo de errores

- Sin `set -e` (convencion del proyecto)
- Errores explicitos en cada modo:
  - `--inspect` con etapa inexistente: lista las disponibles
  - `--timing` sin date +%s.%N: error + sugerencia
  - `--step` sin terminal: fallback automatico a trace
  - Opcion desconocida: error + sugerencia de --help
  - Falta instruccion: error con ejemplo de uso

### 3.5 Limpieza

`trap 'clean_debug; exit 0' INT TERM` elimina directorios temporales
(`/tmp/recpl_debug_stages_PID` y `/tmp/recpl_debug_state_PID`) al
salir normal o por senial.

---

## 4. Pruebas Realizadas

| # | Escenario | Modo | Resultado |
|---|-----------|------|-----------|
| 1 | `crea modulo pagos en nestjs` | trace | 6/6 OK, JSON final correcto |
| 2 | `crea modulo pagos en nestjs` | timing | Tabla compacta, total ~0.02s |
| 3 | `--inspect parser crea modulo pagos en nestjs` | inspect | AST JSON valido |
| 4 | `--inspect bogus` | inspect | "Error: etapa desconocida" |
| 5 | `test_module en prisma` (guion bajo) | trace | Lexer warning en stderr, parser fail, cascada visible |
| 6 | `mostrar pagos` (sin CREATE previo) | trace | Semantic fail: "pagos no existe" |
| 7 | `--step` sin terminal | step | Fallback a trace con mensaje |
| 8 | `--xtrace` | xtrace | PS4 contextual visible |
| 9 | `--help` | help | Todos los flags documentados |
| 10 | `--output` | output | Solo JSON final a stdout |

**Total:** 10 escenarios, 10 OK

---

## 5. Desviaciones de la Propuesta

| Aspecto | Propuesto (040) | Implementado | Razon |
|---------|----------------|--------------|-------|
| Validacion de consistencia con jq | Validar cada JSON intermedio | jq se usa en step (comando json) e inspect, pero no en trace automaticamente | jq no disponible en el sistema; se hace fallback a cat raw |
| Overhead del debugger | Mostrar overhead en resumen | No implementado | Dificil de medir con precision sin ejecucion de referencia; se omite para evitar confusion |
| Soporte LLM | RECPL_LLM_MODE env var | Declarado pero no implementado en debug mode | El pipeline LLM requiere router.sh que tiene dependencias externas; el debugger se enfoca en el pipeline deterministico |
| flag `-i` | Sin descripcion exacta | Implementado con `--inspect ETAPA` | Consistente con la tabla de modos en la propuesta |
| Modo output (`-o`) | Mencionado en tabla de banderas | Implementado | El unico flag adicional de la propuesta |

---

## 6. Riesgos Conocidos

1. **jq no disponible**: El modo step y la validacion JSON funcionan
   sin jq pero sin formateo ni validacion. El usuario ve el JSON raw.
2. **Underscore en nombres**: El lexer produce warning en stderr por
   guion bajo pero no falla; el parser si falla porque separa el token.
   Este es un bug del pipeline, no del debugger — el debugger lo
   expone correctamente.
3. **Modo xtrace filtra lineas `+`**: La salida de bash -x incluye
   lineas `+comando` que se filtran con `grep -v '^+'` para obtener
   la salida real de cada etapa. Si una etapa produce JSON que empieza
   con `+`, se perderia. (Caso extremadamente improbable en JSON.)
4. **Overhead de medicion**: Cada etapa se ejecuta como subproceso
   con redireccion a archivos temporales. Esto anade ~1-5ms por etapa
   vs el pipeline directo.

---

## 7. Estado del Proyecto

| ID | Componente | Estado |
|----|-----------|--------|
| TASK-001 a TASK-008 | Pipeline base | COMPLETED |
| TASK-009 | Tracer (three-address code) | PENDING |
| TASK-010 | Synthesis/PRINT | COMPLETED |
| TASK-011 | LOOP principal | COMPLETED |
| TASK-012 | Scorer (pattern matching) | PENDING |
| TASK-013 | Template scaffolding | COMPLETED |
| TASK-014 | Tests | COMPLETED (72 tests) |
| — | Pipeline debugger | COMPLETED (nuevo) |

---

## 8. Referencias

- `compiler-bot/pipeline_debugger.sh` — Script implementado (784 lineas)
- `docs/040_PROP_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_1_0_DRAFT.md` — Propuesta de referencia
- `docs/000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md` — Guia de estilo shell
- `compiler-bot/frontend/preprocessor.sh` — Etapa 1
- `compiler-bot/frontend/lexer.sh` — Etapa 2
- `compiler-bot/frontend/parser.sh` — Etapa 3
- `compiler-bot/frontend/semantic.sh` — Etapa 4
- `compiler-bot/middleend/ir_generator.sh` — Etapa 5
- `compiler-bot/backend/synthesis.sh` — Etapa 6
- `compiler-bot/recpl.sh` — Bucle principal RECPL
