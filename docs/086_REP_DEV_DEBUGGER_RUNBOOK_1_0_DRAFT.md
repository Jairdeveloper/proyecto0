---
id: 086
area: dev
type: rep
module: compiler_bot
version: 1.0
status: IMPLEMENTED
tags:
  - sprint-14
  - debugger
  - runbook
  - pipeline-debug
  - report
summary: >-
  Reporte de implementacion del Sprint 14.4 — Modo Debug para Pipeline
  Python v2.0. Se creo PipelineDebugger con 4 modos (trace, step, timing,
  inspect) integrado via flag --debug en el CLI. Incluye runbook de uso.
keywords:
  - debugger
  - runbook
  - trace
  - step
  - timing
  - inspect
  - pipeline-debug
  - cli
changelog:
  - version: '1.0'
    date: 2026-06-15
    description: Reporte de implementacion Sprint 14.4 + runbook del debugger
---

# 086_REP_DEV_DEBUGGER_RUNBOOK_1_0_DRAFT

## Sprint 14.4: Modo Debug para Pipeline Python

### Objetivo

Proveer visibilidad del estado intermedio del pipeline Python v2.0,
equivalente al `pipeline_debugger.sh` de Shell v1.0. Antes de este sprint
no existia forma de inspeccionar que producia cada etapa del pipeline
cuando algo fallaba.

### Archivos creados

| Archivo | Descripcion |
|---------|-------------|
| `compiler-bot/agentic_pipeline/debugger.py` | Clase `PipelineDebugger` con 4 modos + source location + output preview (205 lineas) |
| `compiler-bot/agentic_pipeline/tests/test_debugger.py` | Suite de 13 tests para los 4 modos + output preview (90 lineas) |

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `compiler-bot/agentic` | Flags `--debug` y `--show-output` agregados al CLI |

### Detalle de implementacion

#### PipelineDebugger (debugger.py)

Clase que wrappea `PipelineOrchestrator` e inyecta un `stream_callback`
que se ejecuta tras cada etapa del pipeline. El callback se selecciona
segun el modo:

1. **trace mode** (`_trace_stage`): Imprime a stderr:
   - `[stage_name] OK/FAIL (tamaño_datos)`
   - Si fallo: `error: mensaje`
   - Si hay metricas: `metrics: clave=valor ...`

2. **step mode** (`_step_stage`): Igual que trace pero pausa entre etapas:
   - Si `sys.stdin.isatty()`: muestra `Press Enter to continue...` y espera
   - Si no hay TTY (test, pipe): muestra `(non-interactive, continuing)`
   - Captura `EOFError` y `KeyboardInterrupt` para no romper el pipeline

3. **timing mode** (`_timing_stage`): Acumula tiempos por etapa usando
   `output.metrics.get("duration_seconds", 0)`. Al final del pipeline
   imprime resumen con:
   - Barra ASCII (`█`/`░`) de proporcion
   - Porcentaje del total
   - Total acumulado

4. **inspect mode** (`_inspect_stage`): Guarda snapshot JSON por etapa en
   `debug_output/<session_id>/<stage>.json` con:
   - `stage`, `success`, `error`, `metrics`
   - `output_data` resumido a 200 caracteres (o completo si `show_output=True`)
   - `source_location`: ruta:linea del stage class

Todos los modos soportan el flag `show_output` (activado via `--show-output`
en CLI). Cuando esta activo, cada etapa imprime una linea adicional con el
contenido de `output_data` serializado a JSON (truncado a 300 caracteres):

Todos los modos incluyen **source location tracking**: anotan cada etapa
con el archivo y numero de linea donde esta definida la clase del stage
(`← nodes/lexer.py:42`). La funcion `_resolve_stage_locations()` usa
`inspect.getmodule()` + `inspect.getsourcelines()` sobre el `NODE_MAP`
del orchestrator para resolver la ubicacion exacta de cada implementacion.

Metodos auxiliares:
- `_estimate_size()`: Estima tamaño de datos en B/KB via `json.dumps`
- `_summarize()`: Trunca representacion JSON a `max_len` caracteres
- `_loc(stage)`: Retorna string `"ruta/relativa.py:linea"` para un stage
- `_resolve_stage_locations()`: Funcion standalone que construye el mapa
  stage_name → ubicacion desde `NODE_MAP` al momento de importacion
- `_output_preview(data, max_len=300)`: Serializa `output_data` a JSON y
  trunca a `max_len` caracteres para mostrar en una linea de debug

#### Integracion CLI (compiler-bot/agentic)

```python
parser.add_argument(
    "--debug", type=str, choices=["trace", "step", "timing", "inspect"],
    help="Debug mode: trace|step|timing|inspect",
)
parser.add_argument(
    "--show-output", action="store_true",
    help="Print output_data preview for each stage (use with --debug)",
)
```

Cuando `--debug` esta presente, se instancia `PipelineDebugger` en vez de
`PipelineOrchestrator` directo. El modo normal (sin `--debug`) no se ve
afectado.

Si ademas se pasa `--show-output`, el debugger imprime el contenido de
`output_data` que cada etapa entrega a la siguiente, serializado a JSON
y truncado a 300 caracteres. Esto permite rastrear exactamente que datos
flu yen entre etapas del pipeline.

### Tests

13 tests en `test_debugger.py` — todos pasando:

| Test | Que verifica |
|------|-------------|
| `test_trace_mode_runs` | trace mode ejecuta y retorna dict con "output" |
| `test_timing_mode_runs` | timing mode ejecuta sin errores |
| `test_timing_collects_stage_times` | `_stage_times` tiene entradas y suma >= 0 |
| `test_inspect_mode_creates_snapshots` | Crea archivos JSON en `debug_output/` |
| `test_step_mode_continues_noninteractive` | step mode no bloquea sin TTY |
| `test_estimate_size_small` | Objeto chico retorna "XB" |
| `test_estimate_size_large` | Objeto grande retorna "X.XKB" |
| `test_summarize_truncates` | Texto largo se trunca con "..." |
| `test_summarize_short` | Texto corto no se trunca |
| `test_run_returns_dict` | Input vacio retorna dict con "output" |
| `test_trace_with_show_output_does_not_crash` | trace + show_output ejecuta sin errores |
| `test_timing_with_show_output_does_not_crash` | timing + show_output ejecuta sin errores |
| `test_inspect_with_show_output_has_full_data` | inspect + show_output guarda datos completos |

### Estado

- [x] `PipelineDebugger` class con 4 modos
- [x] `trace` mode: imprime entrada/salida de cada etapa
- [x] `step` mode: pausa entre etapas (con proteccion non-TTY)
- [x] `timing` mode: muestra tiempo por etapa + resumen con barra ASCII
- [x] `inspect` mode: snapshots JSON en `debug_output/<session>/`
- [x] `show_output` flag: preview de `output_data` en todos los modos
- [x] Flag `--debug` en CLI
- [x] Flag `--show-output` en CLI
- [x] 13 tests pasando
- [x] `ruff check .` = 0 errores

---

## Runbook: PipelineDebugger

### Que es

`PipelineDebugger` es un wrapper sobre `PipelineOrchestrator` que permite
inspeccionar el estado intermedio del pipeline RECPL v2.0 en tiempo real.
No modifica la logica del pipeline — solo anade observabilidad.

### Modos de uso

#### trace

Muestra resumen de cada etapa en stderr:

```bash
./compiler-bot/agentic --prompt "crea un modulo de pagos" --debug trace
```

Salida (stderr):
```
  [requirement_decomposer] OK  (145B)  ← nodes/requirement_decomposer.py:24
    metrics: tokens_used=85
  [preprocessor] OK  (523B)  ← nodes/preprocessor.py:44
  [lexer] OK  (2.3KB)  ← nodes/lexer.py:65
    metrics: tokens=12
  [parser] OK  (4.1KB)  ← nodes/parser.py:36
    metrics: grammar=project
  [semantic_analyzer] OK  (3.9KB)  ← nodes/semantic_analyzer.py:52
    metrics: errors=0
  [ir_generator] OK  (5.2KB)  ← nodes/ir_generator.py:31
  [planner] OK  (6.8KB)  ← nodes/planner.py:43
  [synthesis] OK  (1.2KB)  ← nodes/synthesis.py:57
    metrics: files_generated=4
  [ui_generator] OK  (890B)  ← nodes/ui_generator.py:72
  [validator] OK  (340B)  ← nodes/validator.py:28
    metrics: warnings=0
```

#### step

Igual que trace pero pausa entre etapas. Requiere Enter para continuar:

```bash
./compiler-bot/agentic --prompt "crea un modulo de pagos" --debug step
```

En pipelines y tests (sin TTY) continua automaticamente.

#### timing

Muestra tiempo por etapa y resumen final con barra de proporcion:

```bash
./compiler-bot/agentic --prompt "crea un modulo de pagos" --debug timing
```

Salida (stderr):
```
  [requirement_decomposer] OK  0.042s  ← nodes/requirement_decomposer.py:24
  [preprocessor] OK  0.001s  ← nodes/preprocessor.py:44
  [lexer] OK  0.003s  ← nodes/lexer.py:65
  [parser] OK  0.001s  ← nodes/parser.py:36
  [semantic_analyzer] OK  0.002s  ← nodes/semantic_analyzer.py:52
  [ir_generator] OK  0.001s  ← nodes/ir_generator.py:31
  [planner] OK  0.001s  ← nodes/planner.py:43
  [synthesis] OK  0.015s  ← nodes/synthesis.py:57
  [ui_generator] OK  0.001s  ← nodes/ui_generator.py:72
  [validator] OK  0.001s  ← nodes/validator.py:28

=== Timing Summary ===
  requirement_decomposer          0.042s ████████████████████  62.7%
  preprocessor                    0.001s ░░░░░░░░░░░░░░░░░░░░   1.5%
  lexer                           0.003s █░░░░░░░░░░░░░░░░░░░   4.5%
  parser                          0.001s ░░░░░░░░░░░░░░░░░░░░   1.5%
  semantic_analyzer               0.002s █░░░░░░░░░░░░░░░░░░░   3.0%
  ir_generator                    0.001s ░░░░░░░░░░░░░░░░░░░░   1.5%
  planner                         0.001s ░░░░░░░░░░░░░░░░░░░░   1.5%
  synthesis                       0.015s ███████░░░░░░░░░░░░░  22.4%
  ui_generator                    0.001s ░░░░░░░░░░░░░░░░░░░░   1.5%
  validator                       0.001s ░░░░░░░░░░░░░░░░░░░░   1.5%
  TOTAL                           0.067s
```

#### inspect

Guarda snapshot JSON de cada etapa en `debug_output/<session_id>/`:

```bash
./compiler-bot/agentic --prompt "crea un modulo de pagos" --debug inspect
```

Los archivos se crean en:
```
debug_output/
  └── 20260615_143021/
      ├── requirement_decomposer.json
      ├── preprocessor.json
      ├── lexer.json
      ├── parser.json
      ├── semantic_analyzer.json
      ├── ir_generator.json
      ├── planner.json
      ├── synthesis.json
      ├── ui_generator.json
      └── validator.json
```

Cada snapshot contiene:
```json
{
  "stage": "lexer",
  "success": true,
  "error": null,
  "metrics": {"tokens": 12},
  "output_data": "{... resumido a 200 chars ...}",
  "source_location": "nodes/lexer.py:65"
}
```

### Output Preview (`--show-output`)

El flag `--show-output` se combina con cualquier modo `--debug` para
inspeccionar el contenido exacto que fluye entre etapas del pipeline.
Cada etapa recibe el `output_data` de la etapa anterior como `input_data`.

#### trace + show-output

```bash
./compiler-bot/agentic --prompt "crea un modulo de pagos" --debug trace --show-output
```

Salida (stderr):
```
  [requirement_decomposer] OK  (293B)  ← nodes/requirement_decomposer.py:29
    metrics: tokens_used=85
    ── output: {"domain": "web", "entities": ["pagos"], "features": ["crear", "listar", "actualizar", "eliminar"], "constraints": [], ...}
  [preprocessor] OK  (424B)  ← nodes/preprocessor.py:172
    ── output: {"domain": "web", "entities": ["pagos"], "features": ["crear", "listar", ...], "raw_text": "crea un modulo de pagos", ...}
  [lexer] OK  (560B)  ← nodes/lexer.py:106
    metrics: tokens=12
    ── output: {"tokens": [{"value": "crea", "type": "ACTION_CREATE", "category": "action", ...}, ...]}
```

#### step + show-output

Igual que trace pero pausa entre etapas para examinar el contenido:
```bash
./compiler-bot/agentic --prompt "crea un modulo" --debug step --show-output
```

Salida:
```
  [requirement_decomposer] OK  (293B)  ← nodes/requirement_decomposer.py:29
    ── output: {"domain": "web", "entities": [...], ...}
  Press Enter to continue...
  [preprocessor] OK  (424B)  ← nodes/preprocessor.py:172
    ── output: {"domain": "web", "raw_text": "crea un modulo", ...}
  Press Enter to continue...
```

#### timing + show-output

```bash
./compiler-bot/agentic --prompt "crea un modulo" --debug timing --show-output
```

Salida:
```
  [requirement_decomposer] OK  0.042s  ← nodes/requirement_decomposer.py:29
    ── output: {"domain": "web", "entities": [...], ...}
  [preprocessor] OK  0.001s  ← nodes/preprocessor.py:172
    ── output: {"domain": "web", "raw_text": "crea un modulo", ...}
```

#### inspect + show-output

Cuando se combina `--debug inspect --show-output`, los snapshots JSON
contienen el `output_data` **completo** (sin truncar a 200 caracteres):

```json
{
  "stage": "requirement_decomposer",
  "success": true,
  "error": null,
  "metrics": {"tokens_used": 85},
  "output_data": {
    "domain": "web",
    "entities": ["pagos"],
    "features": ["crear", "listar"],
    "constraints": [],
    "raw_text": "crea un modulo de pagos"
  },
  "source_location": "nodes/requirement_decomposer.py:29"
}
```

Esto permite hacer diff entre snapshots de distintas ejecuciones para
detectar cambios en el comportamiento del pipeline.

### Casos de uso tipicos

| Situacion | Modo recomendado |
|-----------|-----------------|
| "El pipeline no produce nada" | `trace` para ver que etapa falla |
| "Quiero entender el flujo" | `step` para inspeccionar paso a paso |
| "El pipeline es lento" | `timing` para identificar cuellos de botella |
| "Necesito datos para debugging offline" | `inspect` para tener snapshots persistentes |
| "Que datos entrega cada etapa?" | Cualquier modo + `--show-output` para ver el contrato dataflow |
| "Quiero comparar dos ejecuciones" | `inspect --show-output` para snapshots completos y hacer diff |

### Notas tecnicas

- Todo el output de debug va a **stderr** — el JSON de salida del pipeline
  siempre va a stdout y no se contamina
- El modo `step` detecta automaticamente si hay un terminal interactivo
  (`sys.stdin.isatty()`). En CI/CD, pipes, y tests continua sin pausa
- Los snapshots de `inspect` incluyen `output_data` truncado a 200
  caracteres para no consumir disco innecesariamente
- No hay penalidad de rendimiento en modo normal (sin `--debug`)
- Dependencia: `PipelineDebugger` usa `PipelineOrchestrator.stream_callback`
  que se ejecuta sincronamente tras cada etapa
- **Source location tracking**: cada linea de debug muestra `← ruta/archivo.py:linea`
  indicando donde esta definida la clase del stage. Esto permite navegar
  directamente al codigo fuente de cada etapa del pipeline sin buscar
  manualmente. La resolucion usa `inspect.getmodule()` + `inspect.getsourcelines()`
  sobre `NODE_MAP` y se calcula una vez al instanciar `PipelineDebugger`
- **Output preview** (`--show-output`): cuando esta activo, cada etapa imprime
  el contenido de `output_data` serializado a JSON (truncado a 300 caracteres).
  Esto permite rastrear exactamente que datos fluyen de una etapa a la siguiente.
  En modo `inspect`, los snapshots guardan el `output_data` completo (sin truncar)
  para poder hacer diff entre ejecuciones.
- `--show-output` no tiene efecto sin `--debug`. No afecta al modo normal del pipeline.

### Localizacion de archivos

```
compiler-bot/agentic_pipeline/
  ├── debugger.py          # PipelineDebugger class (4 modos + show_output)
  └── tests/
      └── test_debugger.py # 13 tests
compiler-bot/
  └── agentic              # CLI con flags --debug y --show-output
```

### Comandos de validacion

```bash
# Verificar que ruff no encuentra errores
ruff check compiler-bot/agentic_pipeline/debugger.py

# Ejecutar tests del debugger
pytest compiler-bot/agentic_pipeline/tests/test_debugger.py -v

# Probar modo trace
./compiler-bot/agentic --prompt "crea un modulo" --debug trace 2>/dev/null

# Probar modo trace con output preview
./compiler-bot/agentic --prompt "crea un modulo" --debug trace --show-output 2>/dev/null

# Probar modo timing
./compiler-bot/agentic --prompt "crea un modulo" --debug timing 2>/dev/null

# Probar modo timing con output preview
./compiler-bot/agentic --prompt "crea un modulo" --debug timing --show-output 2>/dev/null

# Probar modo inspect con output completo
./compiler-bot/agentic --prompt "crea un modulo" --debug inspect --show-output
cat debug_output/*/requirement_decomposer.json
rm -rf debug_output/
```
