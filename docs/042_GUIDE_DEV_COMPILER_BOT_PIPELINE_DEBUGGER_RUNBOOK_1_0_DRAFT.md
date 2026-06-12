---
id: 042
area: dev
type: GUIDE
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - guide
  - runbook
  - debugger
  - pipeline
  - trace
  - profiling
  - troubleshooting
summary: "Runbook de uso operativo del pipeline_debugger.sh. Describe los 5 modos de debug, ejemplos de uso por escenario, interpretacion de resultados, troubleshooting y buenas practicas."
keywords:
  - runbook
  - debugger
  - pipeline
  - trace
  - step
  - timing
  - inspect
  - xtrace
  - troubleshooting
  - ejemplos
changelog:
  - version: 1.0
    date: 2026-06-12
    author: workflow-agent
    description: Creacion del runbook de uso del pipeline_debugger.sh
---
# Runbook: Pipeline Debugger RECPL

> **Script:** `compiler-bot/pipeline_debugger.sh`
> **Propuesta:** `040_PROP_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_1_0_DRAFT.md`
> **Reporte:** `041_REP_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_1_0_ACTIVE.md`

---

## 1. Descripcion General

`pipeline_debugger.sh` ejecuta el pipeline RECPL (preprocessor, lexer,
parser, semantic, ir_generator, synthesis) con instrumentacion
completa: tiempos por etapa, inspeccion de JSON intermedio, captura de
stderr, modo paso a paso y tracing profundo con bash -x.

No modifica ninguna etapa del pipeline. Es transparente — solo captura
I/O entre ellas.

### 1.1 Cuando usarlo

| Situacion | Modo recomendado |
|-----------|-----------------|
| Una instruccion falla y no sabes donde | `--trace` (default) |
| Quieres ver el JSON exacto que produce el parser | `--inspect parser` |
| Una instruccion es lenta, quieres medir tiempos | `--timing` |
| Estas depurando un bug y necesitas inspeccionar etapa por etapa | `--step` |
| Necesitas ver el codigo fuente ejecutandose linea a linea | `--xtrace` |
| Quieres el JSON final para pipearlo a jq | `--output` |

### 1.2 Dependencias

| Herramienta | Necesaria para | Si falta |
|-------------|---------------|----------|
| `date` con `%N` | Modo timing (precision nanosegundos) | Timing da error, usa trace |
| `python3` o `awk` | Aritmetica decimal de tiempos | Tiempos muestran 0 |
| `jq` | Validacion JSON, formateo colorido | Step muestra JSON raw sin validar |

---

## 2. Modos de Ejecucion

### 2.1 Modo Trace (default)

Muestra cada etapa del pipeline con status, tiempo, tamano de stdout
y contenido de stderr. Al final, resumen con tiempo total y estado
del directorio de simbolos.

```sh
./pipeline_debugger.sh "crea modulo pagos en nestjs"
```

Salida tipica:

```
┌─────────────────────────────────────────────────────────┐
│ PIPELINE DEBUGGER — trace mode                          │
│ Input: "crea modulo pagos en nestjs"                    │
├─────────────────────────────────────────────────────────┤

  [1/6] preprocessor.sh
    status: OK
    time:   0.002s
    stdout: 28 bytes
    stderr: (none)

  [2/6] lexer.sh
    status: OK
    time:   0.109s
    stdout: 339 bytes
    stderr: (none)

  [3/6] parser.sh
    status: OK
    time:   0.045s
    stdout: 104 bytes
    stderr: (none)

  [4/6] semantic.sh
    status: OK
    time:   0.019s
    stdout: 225 bytes
    stderr: (none)

  [5/6] ir_generator.sh
    status: OK
    time:   0.028s
    stdout: 339 bytes
    stderr: (none)

  [6/6] synthesis.sh
    status: OK
    time:   0.042s
    stdout: 365 bytes
    stderr: (none)

  --- Resumen ---
  Total:  0.245s
  Etapas: 6/6 OK
  Estado: TODAS OK
  State:  /tmp/recpl_debug_state_12345 (1 archivos)
    pagos: module nestjs

{"tipo_respuesta":"action","mensaje":"Generando module Pagos en nestjs...","payload":{...}}
```

**Interpretacion:**

- `status: OK` — la etapa termino con codigo 0 y produjo salida
- `status: FAIL` — la etapa termino con codigo distinto de 0
- `status: EMPTY` — la etapa termino con codigo 0 pero sin stdout
- `stderr: (none)` — no hubo salida de error
- `stderr: see below` — hay contenido en stderr, se muestra en la linea siguiente
- El JSON final se imprime al final del bloque (stdout del debugger)

#### Identificar una etapa fallida

Cuando una etapa falla, el debugger muestra `FAIL` y la salida de error:

```
  [3/6] parser.sh
    status: FAIL
    time:   0.003s
    stdout: 0 bytes
    stderr: Error de sintaxis: token inesperado 'test'
```

Las etapas siguientes **no se saltan** — el debugger las ejecuta igual
(con entrada vacia o corrupta) para mostrar el efecto cascada.

### 2.2 Modo Step

Pausa entre cada etapa y permite inspeccionar estado intermedio.

```sh
./pipeline_debugger.sh --step "crea modulo pagos en nestjs"
```

Salida:

```
┌─────────────────────────────────────────────────────────┐
│ PIPELINE DEBUGGER — step mode                           │
│ Input: "crea modulo pagos en nestjs"                    │
├─────────────────────────────────────────────────────────┤
│ Paso a paso: presiona Enter entre cada etapa           │
│ Comandos: stdout, stderr, json, state, q, help         │
└─────────────────────────────────────────────────────────┘

  [1/6] preprocessor.sh
    status: OK
    time:   0.002s
    stdout: 28 bytes
    stderr: (none)

  [step] Presiona Enter para continuar (o 'q' para salir, 'help' para comandos)...
```

**Comandos disponibles en la pausa:**

| Comando | Que hace |
|---------|----------|
| Enter | Continua a la siguiente etapa |
| `q` | Aborta el debugger y limpia archivos temporales |
| `stdout` | Muestra el stdout completo de la ultima etapa |
| `stderr` | Muestra el stderr completo de la ultima etapa |
| `json` | Valida y muestra el JSON formateado (con jq si disponible) |
| `state` | Lista el contenido del directorio de estado RECPL_STATE_DIR |
| `help` | Muestra los comandos disponibles |

**Ejemplo de sesion step:**

```
  [step] Presiona Enter para continuar (o 'q' para salir, 'help' para comandos)... stderr
  [step] STDERR de parser.sh:
    ! Error lexico: token no reconocido en col 17: '_'

  [step] Presiona Enter para continuar (o 'q' para salir, 'help' para comandos)... json
  {
    "tipo": "Comando",
    "accion": "CREATE",
    "objetivo": {
      "tipo": "module",
      "entidades": ["pagos"]
    }
  }
```

**Nota:** Si `pipeline_debugger.sh` se ejecuta sin terminal (pipe o
redireccion), el modo step fallback automaticamente a trace:

```
Modo step requiere terminal. Cambiando a trace.
```

### 2.3 Modo Timing

Tabla compacta con solo metricas de cada etapa.

```sh
./pipeline_debugger.sh --timing "crea modulo pagos en nestjs"
```

Salida:

```
  Etapa                  Tiempo       Tamanio      Status
  ─────────────────────────────────────────────────────────
  preprocessor.sh      0.006s           28 bytes  OK
  lexer.sh             0.130s          339 bytes  OK
  parser.sh            0.052s          104 bytes  OK
  semantic.sh          0.019s          225 bytes  OK
  ir_generator.sh      0.028s          339 bytes  OK
  synthesis.sh         0.042s          365 bytes  OK
  ─────────────────────────────────────────────────────────
  Total:               0.277s

  --- Resumen ---
  Total:  0.277s
  Etapas: 6/6 OK
  Estado: TODAS OK
  State:  /tmp/recpl_debug_state_12345 (1 archivos)
    pagos: module nestjs
```

**Uso tipico para profiling:**

```sh
# Comparar dos instrucciones
echo "=== CREATE ==="
./pipeline_debugger.sh --timing "crea modulo pagos en nestjs"
echo "=== READ ==="
./pipeline_debugger.sh --timing "mostrar pagos"
```

**Nota:** El modo timing requiere `date +%s.%N`. Si no esta disponible,
muestra:

```
Error: modo timing requiere date +%s.%N (no disponible)
Usa --trace como alternativa.
```

### 2.4 Modo Inspect

Extrae y muestra solo el JSON de salida de una etapa especifica del
pipeline. Ejecuta automaticamente las etapas anteriores para construir
el input necesario.

```sh
./pipeline_debugger.sh --inspect <etapa> "instruccion"
```

**Etapas disponibles:**

| Etapa | Que muestra | Ejemplo de salida |
|-------|-------------|-------------------|
| `preprocessor` | Texto normalizado (minusculas, colapsado) | `crea modulo pagos en nestjs` |
| `lexer` | Tokens DFA uno por linea | `{"type":"ACTION_CREATE","lexeme":"crea",...}` |
| `parser` | AST completo | `{"tipo":"Comando","accion":"CREATE",...}` |
| `semantic` | AST validado con tipos | `{"tipo":"Comando","accion":"CREATE","objetivo":{...}}` |
| `ir_generator` | IR canonico pre-synthesis | `{"accion":"scaffold","tipo":"module","nombre":"pagos",...}` |
| `synthesis` | Respuesta final del bot | `{"tipo_respuesta":"action","mensaje":"Generando...",...}` |

**Ejemplos:**

```sh
# Ver el AST que produce el parser
./pipeline_debugger.sh --inspect parser "crea modulo pagos en nestjs"
# {"tipo":"Comando","accion":"CREATE","objetivo":{"tipo":"module","entidades":["pagos"]},"tech":"nestjs"}

# Ver el IR antes de synthesis
./pipeline_debugger.sh --inspect ir_generator "crea modulo pagos en nestjs"
# {"accion":"scaffold","tipo":"module","nombre":"pagos","tech":"nestjs","template":"module-nestjs"}

# Ver los tokens del lexer
./pipeline_debugger.sh --inspect lexer "crea modulo pagos en nestjs" | jq -s .

# Ver la respuesta final
./pipeline_debugger.sh --inspect synthesis "crea modulo pagos en nestjs" | jq '.mensaje'
```

**Error si la etapa no existe:**

```
Error: etapa desconocida 'bogus'
Etapas disponibles: preprocessor, lexer, parser, semantic, ir_generator, synthesis
```

### 2.5 Modo Xtrace

Ejecuta cada etapa con `bash -x` y `PS4` configurado para mostrar
archivo, linea y funcion. La salida combinada (trace + stdout) se
captura en archivos separados; el stdout real se filtra para pasarlo
a la siguiente etapa.

```sh
./pipeline_debugger.sh --xtrace "crea modulo pagos en nestjs"
```

Salida tipica:

```
┌─────────────────────────────────────────────────────────┐
│ PIPELINE DEBUGGER — xtrace mode                         │
│ Input: "crea modulo pagos en nestjs"                    │
│ Cada etapa se ejecuta con bash -x (PS4 con contexto)    │
├─────────────────────────────────────────────────────────┤

+[preprocessor.sh:23:MAIN] SCRIPT_NAME=preprocessor.sh
+[preprocessor.sh:24:MAIN] LOG_FILE=/tmp/recpl_preprocessor.log
+[preprocessor.sh:94:MAIN] main 'crea modulo pagos en nestjs'
+[preprocessor.sh:77:main] text='crea modulo pagos en nestjs'
+[preprocessor.sh:78:main] echo "$text"
+[preprocessor.sh:79:main] tr '[:upper:]' '[:lower:]'
+[preprocessor.sh:80:main] tr -s ' '
crea modulo pagos en nestjs

+[lexer.sh:23:MAIN] SCRIPT_NAME=lexer.sh
...
```

**Cuando usar xtrace:**

- El error no es obvio en trace mode (status OK pero salida incorrecta)
- Necesitas entender el flujo exacto de una etapa
- Estas modificando una etapa del pipeline y quieres verificar que
  cada linea se ejecuta como esperas
- La etapa falla en produccion pero no en debug — xtrace puede revelar
  diferencias de entorno

### 2.6 Flag --output (modo silencioso)

Ejecuta el pipeline completo pero solo emite el JSON final a stdout.
Todo el detalle de instrumentacion se descarta.

```sh
./pipeline_debugger.sh --output "crea modulo pagos en nestjs"
```

**Uso para piping:**

```sh
# Extraer solo el mensaje
./pipeline_debugger.sh --output "crea modulo pagos en nestjs" | jq '.mensaje'

# Verificar estructura del JSON final
./pipeline_debugger.sh --output "crea modulo pagos" | jq '.tipo_respuesta'

# Comparable con la salida de recpl.sh normal
./pipeline_debugger.sh --output "crea modulo pagos" > /tmp/debug_output.json
./recpl.sh -c "crea modulo pagos" > /tmp/normal_output.json
diff /tmp/debug_output.json /tmp/normal_output.json
```

---

## 3. Ayuda y Flags

```sh
./pipeline_debugger.sh --help
```

Muestra todas las opciones, modos y variables de entorno:

```
pipeline_debugger.sh v1.0.0

Debugger instrumentado del pipeline RECPL. Ejecuta cada etapa del
compilador con metricas de tiempo, inspeccion JSON y captura de errores.

USO:
  ./pipeline_debugger.sh [opciones] "instruccion"

MODOS:
  -t, --trace           Modo trace completo (default)
  -s, --step            Modo paso a paso con pausa interactiva
  -m, --timing          Modo solo metricas (tabla compacta)
  -i, --inspect ETAPA   Mostrar solo el JSON de salida de ETAPA
                        ETAPA: preprocessor, lexer, parser, semantic, ir_generator, synthesis
  -x, --xtrace          Modo bash -x profundo con PS4 contextual
  -o, --output          Solo el JSON final a stdout (para piping)
  -h, --help            Mostrar ayuda

VARIABLES DE ENTORNO:
  RECPL_STATE_DIR  Directorio de estado (default: /tmp/recpl_debug_state_PID)
  RECPL_LLM_MODE   auto|llm|deterministic (default: auto)
```

---

## 4. Escenarios de Depuracion

### 4.1 Instruccion falla sin mensaje claro

```sh
# La instruccion falla pero no sabes donde
./pipeline_debugger.sh "crea modulo test_module en nestjs"
```

Salida:

```
  [2/6] lexer.sh
    status: OK
    time:   0.001s
    stdout: 339 bytes
    stderr: Error lexico: token no reconocido en col 17: '_'

  [3/6] parser.sh
    status: FAIL
    time:   0.003s
    stdout: 0 bytes
    stderr: Error de sintaxis: token inesperado
```

**Diagnostico:** El lexer produce un warning (stderr) por el guion bajo
pero no falla. Sin embargo, el parser recibe tokens incorrectos
("test" y "module" separados) y falla. Solucion: evitar guion bajo
en nombres, o usa `testmodule` en vez de `test_module`.

### 4.2 Error semantico: entidad no existe

```sh
./pipeline_debugger.sh "mostrar pagos"
```

Salida:

```
  [4/6] semantic.sh
    status: FAIL
    time:   0.004s
    stdout: 0 bytes
    stderr: Error semantico: undefined: pagos
```

**Diagnostico:** La entidad `pagos` no existe en la tabla de simbolos.
Primero debes crearla con `crea modulo pagos` en la misma sesion.

### 4.3 Instruccion va lenta

```sh
./pipeline_debugger.sh --timing "crea modulo usuarios en nestjs con prisma"
```

Si una etapa muestra tiempo inusualmente alto, esa es la causa. El lexer
es el mas comun por su estructura DFA. Si el problema es el synthesis,
puede ser que el scaffold este escribiendo archivos grandes.

### 4.4 El modo trace muestra OK pero el JSON final es incorrecto

Usa paso a paso para inspeccionar el JSON intermedio:

```sh
./pipeline_debugger.sh --step "crea modulo pagos en nestjs"
```

En la pausa del parser, escribe `json` para ver el AST. Si el AST es
correcto pero el IR no, el problema esta en la fase intermedia
(ir_generator.sh). Si el IR es correcto pero la respuesta final no,
el problema esta en synthesis.sh.

### 4.5 Comparar pipeline con y sin debugger

```sh
# Salida normal
./recpl.sh -c "crea modulo pagos en nestjs" > /tmp/normal.json

# Salida con debugger (solo JSON)
./pipeline_debugger.sh --output "crea modulo pagos en nestjs" > /tmp/debug.json

# Comparar
diff /tmp/normal.json /tmp/debug.json
```

Ambas salidas deben ser identicas (el debugger no modifica datos).

---

## 5. Variables de Entorno

### `RECPL_STATE_DIR`

Directorio donde el pipeline persiste la tabla de simbolos. Por defecto,
el debugger crea `/tmp/recpl_debug_state_PID`. Para compartir estado
entre ejecuciones:

```sh
RECPL_STATE_DIR=/tmp/mi_estado ./pipeline_debugger.sh "crea modulo pagos"
RECPL_STATE_DIR=/tmp/mi_estado ./pipeline_debugger.sh "mostrar pagos"
```

### `RECPL_LLM_MODE`

Controla el modo del router (auto/llm/deterministic). El debugger
actualmente solo soporta el pipeline deterministico. El modo LLM no
esta instrumentado.

---

## 6. Troubleshooting

### 6.1 "Error: se requiere una instruccion"

No pasaste el texto de la instruccion:

```sh
# MAL
./pipeline_debugger.sh

# BIEN
./pipeline_debugger.sh "crea modulo pagos"
```

### 6.2 "Modo step requiere terminal. Cambiando a trace."

Ejecutaste `--step` dentro de un pipe o redireccion. Step necesita
un terminal para leer comandos interactivos. Usa `--trace` en su
lugar, o ejecuta sin pipe:

```sh
# MAL (step detecta que no hay terminal)
echo "crea modulo pagos" | ./pipeline_debugger.sh --step

# BIEN (step funciona en terminal directa)
./pipeline_debugger.sh --step "crea modulo pagos"
```

### 6.3 "Error: modo timing requiere date +%s.%N"

Tu sistema no tiene `date` con soporte para nanosegundos. Usa
`--trace` en su lugar, que tambien muestra tiempos pero no valida
la disponibilidad de %N.

```sh
./pipeline_debugger.sh --trace "crea modulo pagos"
```

### 6.4 "Error: opcion desconocida: --algo"

Flag no reconocido:

```sh
# MAL
./pipeline_debugger.sh --algo "instruccion"

# BIEN (revisar opciones)
./pipeline_debugger.sh --help
```

### 6.5 Los tiempos son inconsistentes entre ejecuciones

El debugger ejecuta cada etapa como subproceso con redireccion a
archivos temporales. Overhead esperado: ~1-5ms por etapa. Variaciones
mayores pueden deberse a carga del sistema (CPU, I/O). Para mediciones
precisas, ejecuta varias veces y promedia:

```sh
for i in 1 2 3; do
    ./pipeline_debugger.sh --timing "crea modulo pagos" | grep "Total"
done
```

### 6.6 El modo xtrace pierde lineas de salida

El modo xtrace filtra lineas que empiezan con `+` (propias de bash -x)
para extraer el stdout real. Si una etapa produce JSON que contiene
una linea que empieza con `+` en la primera columna, esa linea se
perderia. Esto es extremadamente raro en JSON valido (que siempre
empieza con `{` o `[`).

### 6.7 Directorios temporales no se limpian

Si el debugger se mata con SIGKILL (`kill -9`), el trap no se ejecuta.
Limpia manualmente:

```sh
rm -rf /tmp/recpl_debug_stages_* /tmp/recpl_debug_state_*
```

---

## 7. Consejos y Buenas Practicas

1. **Empieza con trace**: Es el modo mas informativo para diagnosticar
   problemas desconocidos. Muestra toda la informacion de todas las
   etapas en un solo bloque.

2. **Usa inspect para preguntas rapidas**: Si solo necesitas ver el
   AST o los tokens, inspect es mas rapido que trace porque muestra
   solo lo que pides.

3. **Step para bugs complejos**: Cuando la interaccion entre etapas
   importa (ej: el estado compartido entre CREATE y READ), step te
   permite verificar que el estado persiste correctamente.

4. **Timing para optimizar**: Si el pipeline va lento, timing te da
   la fraccion de tiempo de cada etapa sin distracciones.

5. **Combina con jq**: La salida de --inspect y --output se disena
   para pipear a jq:

   ```sh
   ./pipeline_debugger.sh --inspect parser "crea modulo pagos" | jq '.objetivo.entidades'
   ./pipeline_debugger.sh --output "crea modulo pagos" | jq -r '.mensaje'
   ```

6. **Verifica el stderr**: Un status OK no significa que no haya
   problemas. El stderr puede contener advertencias importantes.
   El modo trace muestra stderr explicitamente.

7. **Estado compartido entre pruebas**: Usa `RECPL_STATE_DIR` fijo
   si necesitas simular sesiones multi-instruccion:

   ```sh
   export RECPL_STATE_DIR=/tmp/test_state
   mkdir -p "$RECPL_STATE_DIR"
   ./pipeline_debugger.sh "crea modulo pagos en nestjs"
   ./pipeline_debugger.sh "crea modulo usuarios en prisma"
   ./pipeline_debugger.sh "mostrar pagos"
   ./pipeline_debugger.sh "mostrar usuarios"
   rm -rf "$RECPL_STATE_DIR"
   ```

---

## 8. Referencias

- `compiler-bot/pipeline_debugger.sh` — Script del debugger
- `compiler-bot/recpl.sh` — Bucle principal RECPL
- `docs/040_PROP_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_1_0_DRAFT.md` — Propuesta
- `docs/041_REP_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_1_0_ACTIVE.md` — Reporte de implementacion
- `docs/010_GUIDE_DEV_COMPILER_BOT_RUNBOOK_1_0_DRAFT.md` — Runbook principal RECPL
- `docs/000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md` — Guia de estilo shell
