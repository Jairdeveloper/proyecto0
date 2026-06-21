---
id: 040
area: dev
type: prop
module: compiler-bot
version: 1.1
status: IMPLEMENTED
tags:
  - prop
  - debugger
  - pipeline
  - instrumentation
  - trace
  - profiling
  - reverse-engineering
summary: "Propuesta de un debugger visual para el pipeline RECPL. Herramienta shell que ejecuta cada etapa del compilador con instrumentacion: tiempos por etapa, inspeccion de JSON intermedio, modo paso a paso, captura de stderr y reporte de consistencia. Orientado a ingeniaria inversa del pipeline."
keywords:
  - debugger
  - pipeline
  - trace
  - profiling
  - json-inspection
  - shell
  - recpl
  - instrumentacion
changelog:
  - version: 1.1
    date: 2026-06-12
    author: workflow-agent
    description: Implementacion completada (pipeline_debugger.sh, 784 lineas, 5 modos). Status actualizado a IMPLEMENTED.
  - version: 1.0
    date: 2026-06-12
    author: workflow-agent
    description: Propuesta de debugger de pipeline RECPL para ingeniaria inversa
---
# Propuesta: Debugger de Pipeline RECPL

> **Archivo nuevo:** `compiler-bot/pipeline_debugger.sh`
> **Depende de:** Pipeline RECPL existente (preprocessor, lexer, parser, semantic, ir_generator, synthesis, router)
> **Inspiracion:** Herramientas ad-hoc de debug (bash -x, PS4, LOG_FILE) y necesidad de visibilidad
>   en cada etapa del pipeline compilador.

---

## 0. Resumen Ejecutivo

Actualmente, debuggear el pipeline RECPL requiere ejecutar cada etapa
manualmente con pipes (`./preprocessor.sh | ./lexer.sh | ...`), silenciar
el stderr (`2>/dev/null`), y no hay forma de ver tiempos, inspeccionar
JSON intermedio, o pausar entre etapas.

Esta propuesta crea **`pipeline_debugger.sh`**, un script que envuelve
el pipeline con instrumentacion completa:

```
Entrada → [preprocess] → [lexer] → [parser] → [semantic] → [IR] → [synthesis]
              ↓            ↓         ↓           ↓          ↓         ↓
           tiempo       tiempo    tiempo       tiempo     tiempo    tiempo
           JSON I/O     JSON I/O  JSON I/O     JSON I/O   JSON I/O  JSON I/O
           stderr       stderr    stderr       stderr     stderr    stderr
```

El debugger no modifica las etapas del pipeline. Es una capa de
instrumentacion que se interpone entre ellas sin tocarlas.

---

## 1. Motivacion

### 1.1 Problemas actuales

| Problema | Sintoma | Ejemplo concreto |
|----------|---------|------------------|
| Caja negra | No se ve el JSON intermedio | `lexer.sh` produce tokens, pero no se sabe si son correctos sin ejecutar el parser |
| Stderr silenciado | Errores ocultos | `2>/dev/null` en todas las llamadas; un error lexico se traga sin aviso |
| Sin metricas | No se sabe que etapa es lenta | Una instruccion que tarda 3s — no se sabe si es el LLM, el parser, o el scaffold |
| Sin trazabilidad | No se puede reproducir un bug | El estado del RECPL_STATE_DIR se borra al salir |
| Sin modo paso a paso | No se puede inspeccionar etapa por etapa | Para entender un bug hay que ejecutar 6 comandos manuales |

### 1.2 Audiencia objetivo

1. **Equipo de ingenieria inversa** — entender el flujo interno del pipeline,
   detectar anomalias en los JSON intermedios, medir latencias
2. **Desarrolladores del pipeline** — encontrar bugs en etapas individuales
   sin tener que armar el pipe manualmente
3. **Usuarios avanzados** — entender por que una instruccion no produjo el
   resultado esperado

---

## 2. Diseno

### 2.1 Arquitectura

```
pipeline_debugger.sh
        │
        ├── Modo: trace (default)
        ├── Modo: step    (paso a paso con pausa)
        ├── Modo: timing  (solo metricas)
        └── Modo: inspect (solo JSON de una etapa)

Cada modo ejecuta el pipeline pero con instrumentacion entre etapas:
  [stage N] → capturar stdout+stderr+tiempo → [-pausa-] → [stage N+1]
```

### 2.2 Modos de operacion

#### Modo trace (default): cada etapa con detalle

```
$ ./pipeline_debugger.sh "crea modulo pagos en nestjs"
┌─────────────────────────────────────────────────────────┐
│ PIPELINE DEBUGGER — trace mode                          │
│ Input: "crea modulo pagos en nestjs"                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ [1/6] preprocessor.sh                                   │
│   status: OK (0)                                        │
│   time:   0.002s                                        │
│   stdout: "crea modulo pagos en nestjs"                 │
│   stderr: (none)                                        │
│                                                         │
│ [2/6] lexer.sh                                          │
│   status: OK (0)                                        │
│   time:   0.001s                                        │
│   stdout: 5 tokens                                      │
│   stderr: (none)                                        │
│                                                         │
│ [3/6] parser.sh                                         │
│   status: OK (0)                                        │
│   time:   0.003s                                        │
│   stdout: {"tipo":"Comando","accion":"CREATE",...}      │
│   stderr: (none)                                        │
│                                                         │
│ [...etc...]                                             │
│                                                         │
│ ─── Resumen ───                                         │
│   Total:  0.023s                                        │
│   Etapas: 6 OK, 0 FAIL                                  │
│   Output: {"tipo_respuesta":"action","mensaje":"..."}    │
│   State:  /tmp/recpl_debug_12345/                       │
│   State:  1 simbolo: pagos                              │
└─────────────────────────────────────────────────────────┘
```

#### Modo step: pausa entre etapas

```
$ ./pipeline_debugger.sh --step "crea modulo pagos en nestjs"

[1/6] preprocessor.sh — 0.002s — OK
Presiona Enter para continuar (o 'q' para salir)...
```

En cada pausa se puede inspeccionar:

| Comando | Accion |
|---------|--------|
| Enter | Continuar a la siguiente etapa |
| `q` | Salir del debugger |
| `stdout` | Mostrar stdout completo de la ultima etapa |
| `stderr` | Mostrar stderr completo de la ultima etapa |
| `json` | Validar y mostrar formateado el JSON de salida |
| `state` | Mostrar contenido de RECPL_STATE_DIR |
| `help` | Mostrar comandos disponibles |

#### Modo timing: solo metricas

```
$ ./pipeline_debugger.sh --timing "crea modulo pagos en nestjs"
  Etapa                  Tiempo    Salida     Status
  ─────────────────────────────────────────────────
  preprocessor.sh       0.002s    72 bytes    OK
  lexer.sh              0.001s    245 bytes   OK
  parser.sh             0.003s    189 bytes   OK
  semantic.sh           0.004s    215 bytes   OK
  ir_generator.sh       0.001s    178 bytes   OK
  synthesis.sh          0.012s    312 bytes   OK
  ─────────────────────────────────────────────────
  Total                 0.023s
  Output final: {"tipo_respuesta":"action", ...}
```

#### Modo inspect: extraer JSON de una etapa

```
$ ./pipeline_debugger.sh --inspect lexer "crea modulo pagos en nestjs"
{"type":"ACTION_CREATE","lexeme":"crea","position":{"line":1,"col":1}}
{"type":"MODULE","lexeme":"modulo","position":{"line":1,"col":6}}
{"type":"ENTITY","lexeme":"pagos","position":{"line":1,"col":13}}
{"type":"PREP_IN","lexeme":"en","position":{"line":1,"col":19}}
{"type":"TECH_NESTJS","lexeme":"nestjs","position":{"line":1,"col":22}}

$ ./pipeline_debugger.sh --inspect parser "crea modulo pagos en nestjs"
{"tipo":"Comando","accion":"CREATE","objetivo":{"tipo":"module","entidades":["pagos"],"tech":"nestjs"}}
```

### 2.3 Salida combinada (modo trace)

Para no romper pipes, el debugger separa:
- **stdout**: Solo el JSON final del pipeline (igual que recpl.sh normal)
- **stderr**: Todo el detalle de instrumentacion (tablas, tiempos, JSON inspeccionado)

Esto permite:

```sh
# El JSON final va a stdout, como siempre
./pipeline_debugger.sh "crea modulo pagos" | jq '.mensaje'

# El detalle va a stderr, visible en terminal
./pipeline_debugger.sh "crea modulo pagos" 2>&1 | less
```

### 2.4 Integracion con bash -x y PS4

Modo `--xtrace` que ejecuta cada etapa con `bash -x` y `PS4`
configurado para mostrar archivo, linea y funcion:

```
$ ./pipeline_debugger.sh --xtrace "crea modulo pagos"
  [TRACE] Ejecutando cada etapa con bash -x (PS4 con contexto)
  ─────────────────────────────────────────────────────────
  [preprocessor.sh]
  +preprocessor.sh:42:normalize() echo 'crea modulo pagos en nestjs' | tr '[:upper:]' '[:lower:]'
  +preprocessor.sh:55:collapse_punct() ...
  ...

  [lexer.sh]
  +lexer.sh:28:tokenize() case $1 in
  +lexer.sh:29:tokenize() crea) echo '{"type":"ACTION_CREATE",...}'
  ...
```

### 2.5 Estado del pipeline

Al finalizar, el debugger muestra el estado de `RECPL_STATE_DIR`:

```
  State:  /tmp/recpl_debug_12345/
  State:  2 simbolos: pagos (module, nestjs), usuarios (module, prisma)
```

### 2.6 Validacion de consistencia

Cada JSON intermedio se valida con `jq` para detectar:

- JSON mal formado (error de sintaxis)
- Campos obligatorios ausentes
- Tipos incorrectos (string vs number vs null)

```
  [3/6] parser.sh
    status: OK (0)
    time:   0.003s
    VALIDACION: ✓ JSON valido, ✓ campo "tipo" existe, ✓ campo "accion" existe
```

---

## 3. Implementacion

### 3.1 Funciones propuestas

```sh
# pipeline_debugger.sh — Instrumentacion del pipeline RECPL
# Modos: trace (default), step, timing, inspect, xtrace

pipeline_debugger() {
    instruction="$1"
    mode="${2:-trace}"
    stage_data_dir="/tmp/recpl_debug_$$"
    mkdir -p "$stage_data_dir"

    # Determinar el pipeline segun el router
    # (pipeline deterministico o LLM)

    case "$mode" in
        trace)   debug_trace "$instruction" ;;
        step)    debug_step "$instruction" ;;
        timing)  debug_timing "$instruction" ;;
        inspect) debug_inspect "$3" "$instruction" ;;  # 3er arg: stage name
        xtrace)  debug_xtrace "$instruction" ;;
    esac
}

# Ejecutar una etapa con instrumentacion
run_stage() {
    stage_name="$1"       # ej: "preprocessor.sh"
    stage_script="$2"     # ej: "$SCRIPT_DIR/frontend/preprocessor.sh"
    input="$3"            # texto o JSON de entrada
    stage_num="$4"        # ej: "1/6"
    total_stages="$5"     # ej: "6"

    # Capturar stdout, stderr, codigo de salida y tiempo
    start_time=$(date +%s.%N 2>/dev/null || echo "0")
    stdout_file="$stage_data_dir/${stage_name}.stdout"
    stderr_file="$stage_data_dir/${stage_name}.stderr"

    echo "$input" | "$stage_script" > "$stdout_file" 2> "$stderr_file"
    exit_code=$?
    end_time=$(date +%s.%N 2>/dev/null || echo "0")

    # Calcular tiempo (con fallback si date no soporta %N)
    elapsed=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "0")

    # Determinar status
    if [ $exit_code -ne 0 ]; then
        status="FAIL"
    elif [ ! -s "$stdout_file" ]; then
        status="EMPTY"
    else
        status="OK"
    fi

    # Mostrar resultado segun modo
    ...
}

# Inspeccionar JSON de salida de una etapa
inspect_json() {
    file="$1"
    if jq -e . "$file" >/dev/null 2>&1; then
        echo "  VALIDACION: ✓ JSON valido"
        jq -r '. | keys[]' "$file" | while read -r key; do
            echo "    ├─ $key: $(jq -r ".$key" "$file" | head -c 40)"
        done
    else
        echo "  VALIDACION: ✗ JSON invalido"
    fi
}
```

### 3.2 Pseudocodigo del modo trace

```
debug_trace(instruction):
    1. Mostrar cabecera del debugger
    2. Ejecutar preprocessor.sh con instrumentacion
    3. Mostrar resultado (status, tiempo, tamano, stderr)
    4. Si OK, pasar su stdout a lexer.sh
    5. Repetir para cada etapa del pipeline
    6. Al final, mostrar resumen (total time, status count, state dir)
```

### 3.3 Pseudocodigo del modo step

```
debug_step(instruction):
    1. Para cada etapa del pipeline:
       a. Ejecutar etapa con instrumentacion (igual que trace)
       b. Mostrar resultado resumido
       c. Entrar en bucle de comandos:
          - Enter → continue
          - 'stdout' → cat stdout de la etapa
          - 'stderr' → cat stderr de la etapa
          - 'json'   → jq . del stdout
          - 'state'  → ls RECPL_STATE_DIR/
          - 'q'      → abortar
```

### 3.4 Pseudocodigo del modo xtrace

```
debug_xtrace(instruction):
    1. Configurar PS4 para contexto completo:
       PS4='+[${BASH_SOURCE##*/}:${LINENO}:${FUNCNAME[0]:-MAIN}] '
    2. Para cada etapa del pipeline:
       a. Ejecutar con: bash -x "$stage_script" <<< "$input"
       b. Mostrar salida y stderr de bash -x
```

### 3.5 Banderas

```
./pipeline_debugger.sh [opciones] "instruccion"

Opciones:
  -t, --trace      Modo trace completo (default)
  -s, --step       Modo paso a paso con pausa interactiva
  -m, --timing     Modo solo metricas (tabla compacta)
  -i, --inspect ETAPA  Mostrar solo el JSON de salida de ETAPA
  -x, --xtrace     Modo bash -x profundo con PS4 contextual
  -o, --output     Solo el JSON final a stdout (para piping)
  -h, --help       Mostrar ayuda

Ejemplos:
  ./pipeline_debugger.sh "crea modulo pagos en nestjs"
  ./pipeline_debugger.sh --step "crea modulo pagos en nestjs"
  ./pipeline_debugger.sh --timing "crea modulo pagos en nestjs"
  ./pipeline_debugger.sh --inspect parser "crea modulo pagos en nestjs"
  ./pipeline_debugger.sh --xtrace "crea modulo pagos en nestjs"
```

---

## 4. Plan de implementacion

| Fase | Descripcion | Estimacion |
|------|-------------|------------|
| 1 | Crear `pipeline_debugger.sh` con modo trace (run_stage, instrumentacion basica: status, time, stdout size, stderr) | 45 min |
| 2 | Agregar modos timing y inspect (tabla compacta, extraccion de JSON por etapa) | 30 min |
| 3 | Agregar modo step (bucle interactivo de comandos entre etapas) | 30 min |
| 4 | Agregar modo xtrace (integracion con bash -x y PS4 contextual) | 20 min |
| 5 | Validacion de consistencia (jq .keys, campos obligatorios en cada etapa) | 20 min |
| 6 | Pruebas: depurar 3 instrucciones conocidas, comparar output con recpl.sh normal | 25 min |
| **Total** | | **~2.5 horas** |

---

## 5. Ejemplos de uso

### 5.1 Encontrar un bug lexico

```sh
# Una instruccion con guion bajo falla silenciosamente en modo normal
./recpl.sh -c "crea modulo test_module en nestjs"
# → {"tipo_respuesta":"error","mensaje":"Error al procesar: ..."}

# El debugger revela la causa exacta
./pipeline_debugger.sh "crea modulo test_module en nestjs"
# [2/6] lexer.sh
#   status: OK (0)  ← el lexer no falla, pero produce salida inesperada
#   stderr: "Error lexico: token no reconocido en col 17: '_'"
#   stdout incluye: ENTITY "test" y ENTITY "source" separados
```

### 5.2 Medir latencia del LLM vs deterministico

```sh
# Comparar tiempos
echo "=== MODO DETERMINISTICO ==="
./pipeline_debugger.sh --timing "crea modulo pagos en nestjs"

echo "=== MODO LLM ==="
RECPL_LLM_MODE=llm ./pipeline_debugger.sh --timing "crea modulo pagos en nestjs"

# La tabla de timing muestra donde se pierde el tiempo
```

### 5.3 Depurar un error semantico

```sh
./pipeline_debugger.sh --step "mostrar pagos"
# Paso 1-3: OK (preprocess, lexer, parser producen JSON validos)
# Paso 4: semantic.sh
#   status: FAIL (exit 1)
#   stderr: "Error semantico: pagos no existe en la tabla de simbolos"

# En la pausa, inspeccionar el estado:
# > state
#   State dir: /tmp/recpl_debug_12345/ esta VACIO
#   → Confirmado: no hay simbolos porque nunca se ejecuto un CREATE
```

### 5.4 Ingenieria inversa del JSON interno

```sh
# Ver el AST completo que produce el parser
./pipeline_debugger.sh --inspect parser "crea modulo pagos en nestjs"
# {"tipo":"Comando","accion":"CREATE","objetivo":{"tipo":"module","entidades":["pagos"],"tech":"nestjs"}}

# Ver el IR final antes de synthesis
./pipeline_debugger.sh --inspect ir_generator "crea modulo pagos en nestjs"
# {"accion":"scaffold","tipo":"module","nombre":"pagos","tech":"nestjs","template":"module-nestjs"}
```

---

## 6. Riesgos y mitigaciones

Cada riesgo se evaluó contra las herramientas reales del sistema
(`date +%s.%N` disponible, `bc` no disponible, `jq` no disponible,
`python3` disponible, `awk` disponible) y las convenciones del proyecto.

| Riesgo | Impacto | Mitigacion original | Mitigacion propuesta |
|--------|---------|---------------------|----------------------|
| `date +%s.%N` no disponible | Timing muestra 0 | Fallback a `date +%s` (pierde precision sub-second) | Hacer `date +%s.%N` **dependencia obligatoria** del modo timing. Si no esta disponible, `--timing` muestra error y sugiere `--trace`. El `date` POSIX moderno soporta `%N` en Linux, BSD y macOS. |
| `bc` no instalado para resta de flotantes | Timing muestra 0 | Usar `awk` o `python3 -c` como fallback | Usar **`awk` o `python3 -c "print($end - $start)"`** como unica opcion de resta decimal. Ambos estan disponibles en el sistema actual. Detectar al inicio y fallar si ninguno existe. |
| `jq` no disponible | Validacion de JSON salta | Detectar al inicio, omitir validacion | Hacer **`jq` dependencia obligatoria del debugger** y fallar al arranque si no existe, porque el debugger necesita inspeccionar y validar JSON en cada etapa (a diferencia de recpl.sh que puede funcionar sin el con fallo silencioso). |
| Modo step sin terminal | No hay entrada interactiva | Detectar `[ -t 0 ]`, saltar a trace | Detectar con `[ -t 0 ]` (patron de recpl.sh:343). Si no hay terminal, **ejecutar en modo trace automático** mostrando cada etapa en tiempo real. Mensaje al inicio: "Modo step requiere terminal. Cambiando a trace." |
| Archivos temporales no limpiados | Residuos en disco | Trap EXIT | Seguir el **patron exacto del proyecto** (recpl.sh:39-42, 287): `trap 'clean_debug; exit 0' INT TERM` con `clean_debug(){ rm -rf "$DEBUG_STAGE_DIR" "$DEBUG_STATE_DIR"; }`. Usar `$$` en el nombre del directorio (recpl.sh:22). |
| Debugger modifica el comportamiento | Mediciones inexactas | "Solo captura I/O, no modifica datos" | **Reconocer el overhead** y mostrarlo en el resumen: "Overhead del debugger: +0.00Xs". Medir solo el tiempo real del subproceso (antes y despues de la ejecucion, no dentro). |

---

## 7. Referencias

- `compiler-bot/frontend/preprocessor.sh` — Etapa 1 del pipeline
- `compiler-bot/frontend/lexer.sh` — Etapa 2: DFA tokenizer
- `compiler-bot/frontend/parser.sh` — Etapa 3: LL(1) recursive descent
- `compiler-bot/frontend/semantic.sh` — Etapa 4: symbol table + type checking
- `compiler-bot/middleend/ir_generator.sh` — Etapa 5: validated AST → IR.json
- `compiler-bot/backend/synthesis.sh` — Etapa 6: IR.json → bot response
- `compiler-bot/frontend/router.sh` — Router determinista/LLM
- `compiler-bot/recpl.sh` — Bucle principal (process_instruction)
- `docs/025_GUIDE_DEV_COMPILER_BOT_PIPELINE_1_0_DRAFT.md` — Pipeline teorico
- `docs/026_GUIDE_DEV_COMPILER_BOT_LOOP_1_0_DRAFT.md` — Arquitectura del bucle
