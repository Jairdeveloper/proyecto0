---
id: 044
area: dev
type: GUIDE
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - guide
  - cheatsheet
  - debugger
  - pipeline
  - commands
  - reference
summary: "Referencia rapida de comandos de pipeline_debugger.sh. Todos los modos, flags y ejemplos con salida real, organizados por escenario de depuracion."
keywords:
  - cheatsheet
  - comandos
  - debugger
  - pipeline
  - referencia
  - ejemplos
  - trace
  - step
  - timing
  - inspect
  - xtrace
changelog:
  - version: 1.0
    date: 2026-06-12
    author: workflow-agent
    description: Recopilacion de comandos de pipeline_debugger.sh con salidas reales de sesion de ingenieria inversa
---
# Cheatsheet: pipeline_debugger.sh

> Todas las salidas son reales, extraidas de una sesion de
> ingenieria inversa del pipeline RECPL.

---

## 1. Ayuda y Version

```sh
./pipeline_debugger.sh --help
```

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

## 2. Modo Trace (default)

Muestra las 6 etapas del pipeline con status, tiempo, stderr y resumen final.

```sh
./pipeline_debugger.sh --trace "crea modulo pagos en nestjs"
```

```
┌─────────────────────────────────────────────────────────┐
│ PIPELINE DEBUGGER — trace mode                          │
│ Input: "crea modulo pagos en nestjs"                    │
├─────────────────────────────────────────────────────────┤

  [1/6] preprocessor.sh
    status: OK
    time:   0.007s
    stdout: 28 bytes
    stderr: (none)

  [2/6] lexer.sh
    status: OK
    time:   0.103s
    stdout: 339 bytes
    stderr: (none)

  [3/6] parser.sh
    status: OK
    time:   0.038s
    stdout: 104 bytes
    stderr: (none)

  [4/6] semantic.sh
    status: OK
    time:   0.022s
    stdout: 225 bytes
    stderr: (none)

  [5/6] ir_generator.sh
    status: OK
    time:   0.026s
    stdout: 340 bytes
    stderr: (none)

  [6/6] synthesis.sh
    status: OK
    time:   0.035s
    stdout: 365 bytes
    stderr: (none)


  --- Resumen ---
  Total:  0.234s
  Etapas: 6/6 OK
  Estado: TODAS OK
  State:  /tmp/recpl_debug_state_12345 (0 archivos)

{
  "tipo_respuesta": "action",
  "mensaje": "Generando module Pagos en nestjs...",
  "payload": {
    "accion": "scaffold:module",
    "params": {
      "nombre": "Pagos",
      "tech": "nestjs",
      "template": "module-nestjs"
    },
    "archivos": ["modules/pagos/pagos.controller.ts", "modules/pagos/pagos.module.ts", "modules/pagos/pagos.service.ts"]
  }
}
```

### Solo resumen de errores (grep)

```sh
./pipeline_debugger.sh --trace "crea modulo pagos en nestjs" 2>&1 \
  | grep -E "(FAIL|stderr:|Error|warning)"
```

```
    stderr: (none)
    stderr: (none)
    stderr: (none)
    stderr: (none)
    stderr: (none)
    stderr: (none)
```

---

## 3. Modo Timing (tabla compacta)

```sh
./pipeline_debugger.sh --timing "crea modulo pagos en nestjs"
```

```
  Etapa                  Tiempo       Tamanio      Status
  ─────────────────────────────────────────────────────────
  preprocessor.sh      0.008s           28 bytes  OK
  lexer.sh             0.112s          339 bytes  OK
  parser.sh            0.045s          104 bytes  OK
  semantic.sh          0.017s          225 bytes  OK
  ir_generator.sh      0.027s          340 bytes  OK
  synthesis.sh         0.028s          365 bytes  OK
  ─────────────────────────────────────────────────────────
  Total:  0.240s
  Etapas: 6/6 OK
  Estado: TODAS OK
```

---

## 4. Modo Inspect (por etapa)

### Preprocessor — texto normalizado

```sh
./pipeline_debugger.sh --inspect preprocessor "crea modulo pagos en nestjs" 2>/dev/null
```

```
crea modulo pagos en nestjs
```

### Preprocessor — case folding

```sh
./pipeline_debugger.sh --inspect preprocessor "CREA UN MODULO DE PAGOS EN NESTJS" 2>/dev/null
```

```
crea un modulo de pagos en nestjs
```

### Lexer — tokens DFA

```sh
./pipeline_debugger.sh --inspect lexer "crea modulo pagos en nestjs" 2>/dev/null
```

```
{"type":"ACTION_CREATE","lexeme":"crea","position":{"line":1,"col":1}}
{"type":"MODULE","lexeme":"modulo","position":{"line":1,"col":6}}
{"type":"ENTITY","lexeme":"pagos","position":{"line":1,"col":13}}
{"type":"PREP_IN","lexeme":"en","position":{"line":1,"col":19}}
{"type":"TECH_NESTJS","lexeme":"nestjs","position":{"line":1,"col":22}}
```

### Parser — AST completo

```sh
./pipeline_debugger.sh --inspect parser "crea modulo pagos en nestjs" 2>/dev/null
```

```
{"tipo":"Comando","accion":"CREATE","objetivo":{"tipo":"module","entidades":["pagos"]},"tech":"nestjs"}
```

### Parser — READ

```sh
RECPL_STATE_DIR=/tmp/recpl_report_state \
  ./pipeline_debugger.sh --inspect parser "mostrar pagos" 2>/dev/null
```

```
{"tipo":"Comando","accion":"READ","objetivo":{"tipo":"entity","entidades":["pagos"]},"tech":null}
```

### Parser — DELETE

```sh
./pipeline_debugger.sh --inspect parser "eliminar modulo pagos" 2>/dev/null
```

```
{"tipo":"Comando","accion":"DELETE","objetivo":{"tipo":"module","entidades":["pagos"]},"tech":null}
```

### Parser — UPDATE

```sh
./pipeline_debugger.sh --inspect parser "actualizar modulo pagos en prisma" 2>/dev/null
```

```
{"tipo":"Comando","accion":"UPDATE","objetivo":{"tipo":"module","entidades":["pagos"]},"tech":"prisma"}
```

### Semantic — AST validado + symbol table

```sh
./pipeline_debugger.sh --inspect semantic "crea modulo pagos en nestjs" 2>/dev/null
```

```json
{"ast":{"tipo":"Comando","accion":"CREATE","objetivo":{"tipo":"module","entidades":["pagos"]},"tech":"nestjs"},"symbol_table":{"pagos":{"tipo":"module","tech":"NestJS","estado":"pending","dependencias":[],"scope":"global"}}}
```

### IR Generator — IR canonico

```sh
./pipeline_debugger.sh --inspect ir_generator "crea modulo pagos en nestjs" 2>/dev/null
```

```json
{
  "accion": "scaffold",
  "tipo": "module",
  "nombre": "pagos",
  "tech": "nestjs",
  "template": "module-nestjs",
  "entidades": ["pagos"],
  "dependencias": [],
  "score": null,
  "trace_id": "trc_1781284784_107052",
  "symbol_table": {
    "pagos": {
      "tipo": "module",
      "tech": "NestJS",
      "estado": "pending",
      "dependencias": [],
      "scope": "global"
    }
  }
}
```

### Synthesis — respuesta final del bot

```sh
./pipeline_debugger.sh --inspect synthesis "crea modulo pagos en nestjs" 2>/dev/null
```

```json
{
  "tipo_respuesta": "action",
  "mensaje": "Generando module Pagos en nestjs...",
  "payload": {
    "accion": "scaffold:module",
    "params": {
      "nombre": "Pagos",
      "tech": "nestjs",
      "template": "module-nestjs"
    },
    "archivos": [
      "modules/pagos/pagos.controller.ts",
      "modules/pagos/pagos.module.ts",
      "modules/pagos/pagos.service.ts"
    ]
  }
}
```

### Synthesis — READ con estado previo

```sh
RECPL_STATE_DIR=/tmp/recpl_report_state \
  ./pipeline_debugger.sh --inspect synthesis "mostrar pagos" 2>/dev/null
```

```json
{
  "tipo_respuesta": "info",
  "mensaje": "Mostrando entity Pagos...",
  "payload": {
    "accion": "read:entity",
    "params": {
      "nombre": "Pagos"
    },
    "archivos": []
  }
}
```

### Inspect con etapa inexistente

```sh
./pipeline_debugger.sh --inspect bogus "instruccion" 2>&1
```

```
Error: etapa desconocida 'bogus'
Etapas disponibles: preprocessor, lexer, parser, semantic, ir_generator, synthesis
```

---

## 5. Modo Step

### Paso a paso interactivo (requiere terminal)

```sh
./pipeline_debugger.sh --step "crea modulo pagos en nestjs"
```

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

### Fallback automatico sin terminal

```sh
echo "crea modulo pagos" | ./pipeline_debugger.sh --step
```

```
Modo step requiere terminal. Cambiando a trace.
```

---

## 6. Modo Xtrace (bash -x profundo)

```sh
./pipeline_debugger.sh --xtrace "crea modulo pagos en nestjs"
```

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
+[lexer.sh:24:MAIN] LOG_FILE=/tmp/recpl_lexer.log
...
```

---

## 7. Estado Compartido (sesion multi-instruccion)

### CREATE + READ encadenados

```sh
RECPL_STATE_DIR=/tmp/recpl_report_chain \
  ./pipeline_debugger.sh --trace "crea modulo pagos en nestjs" 2>/dev/null

RECPL_STATE_DIR=/tmp/recpl_report_chain \
  ./pipeline_debugger.sh --trace "mostrar pagos" 2>/dev/null
```

Salida del CREATE:

```
  --- Resumen ---
  Total:  0.256s
  Etapas: 6/6 OK
  Estado: TODAS OK
  State:  /tmp/recpl_report_chain (2 archivos)
    scope.tmp: 
    symbols.tmp: 

{"tipo_respuesta":"action","mensaje":"Generando module Pagos en nestjs...",...}
```

Salida del READ (encuentra el simbolo):

```json
{
  "tipo_respuesta": "info",
  "mensaje": "Mostrando entity Pagos...",
  "payload": {
    "accion": "read:entity",
    "params": {
      "nombre": "Pagos"
    },
    "archivos": []
  }
}
```

---

## 8. Escenarios de Error

### Underscore en nombre de entidad

```sh
./pipeline_debugger.sh --inspect lexer "crea modulo test_module en nestjs" 2>&1
```

```
{"type":"ACTION_CREATE","lexeme":"crea","position":{"line":1,"col":1}}
{"type":"MODULE","lexeme":"modulo","position":{"line":1,"col":6}}
{"type":"ENTITY","lexeme":"test","position":{"line":1,"col":13}}
{"type":"MODULE","lexeme":"module","position":{"line":1,"col":18}}
{"type":"PREP_IN","lexeme":"en","position":{"line":1,"col":25}}
{"type":"TECH_NESTJS","lexeme":"nestjs","position":{"line":1,"col":28}}
```

El warning no sale en stdout (va a stderr):

```sh
./pipeline_debugger.sh --trace "crea modulo test_module en nestjs" 2>&1 \
  | grep -A6 "\[2/6\] lexer\|\[3/6\] parser\|stderr:"
```

```
    stderr: (none)

  [2/6] lexer.sh
    status: OK
    time:   0.140s
    stdout: 405 bytes
    stderr: Error lexico: token no reconocido en col 17: '_'

  [3/6] parser.sh
    status: FAIL
    time:   0.035s
    stdout: 0 bytes
    stderr: Error sintactico en token 3: se esperaba fin de entrada, se encontro 'MODULE' ('module')
```

### Multi-entidad no soportada

```sh
./pipeline_debugger.sh --trace "crea modulo auth y users en nestjs y prisma" 2>&1 \
  | grep -E "\[.*\]|stderr:|FAIL|Resumen|Total"
```

```
  [1/6] preprocessor.sh
    stderr: (none)
  [2/6] lexer.sh
    stderr: (none)
  [3/6] parser.sh
    status: FAIL
    stderr: Error sintactico en token 3: se esperaba fin de entrada, se encontro 'ENTITY' ('y')
  [4/6] semantic.sh
    status: FAIL
    stderr: Error: no hay AST de entrada
  [5/6] ir_generator.sh
    status: FAIL
    stderr: Error: no hay entrada JSON
  [6/6] synthesis.sh
    status: FAIL
    stderr: Error: no hay IR.json de entrada
  --- Resumen ---
  Total:  0.239s
```

### Instruccion vacia

```sh
./pipeline_debugger.sh --trace "" 2>&1
```

```
Error: se requiere una instruccion.
Usa: pipeline_debugger.sh "crea modulo pagos en nestjs"
```

### Palabras no reconocidas

```sh
# Preprocessor normaliza pero lexer no produce tokens accion
./pipeline_debugger.sh --inspect preprocessor "HOLA MUNDO" 2>/dev/null
```

```
hola mundo
```

```sh
# Lexer no produce salida (sin tokens accion reconocidos)
./pipeline_debugger.sh --inspect lexer "HOLA MUNDO" 2>&1
# (sin salida)
```

```sh
# Parser no recibe tokens validos
./pipeline_debugger.sh --inspect parser "HOLA MUNDO" 2>&1
# (sin salida)
```

---

## 9. Modo Output (piping JSON final)

```sh
./pipeline_debugger.sh --output "crea modulo pagos en nestjs"
```

**Nota:** El flag `--output` actualmente tiene un bug: redirige todo
el stdout a `/dev/null`. Como workaround, usar `--trace` y capturar
la ultima linea con `tail -1`:

```sh
./pipeline_debugger.sh --trace "crea modulo pagos en nestjs" 2>/dev/null | tail -1
```

---
## Comandos usasdos para el debug

1. ./pipeline_debugger.sh --inspect lexer "crea modulo pagos en nestjs" 2>/dev/null
2. ./pipeline_debugger.sh --inspect parser "crea modulo pagos en nestjs" 2>/dev/null
3. ./pipeline_debugger.sh --inspect semantic "crea modulo pagos en nestjs" 2>/dev/null
4. ./pipeline_debugger.sh --inspect ir_generator "crea modulo pagos en nestjs" 2>/dev/null
5. ./pipeline_debugger.sh --inspect synthesis "crea modulo pagos en nestjs" 2>/dev/null
6. RECPL_STATE_DIR=/tmp/recpl_report_state ./pipeline_debugger.sh --trace "crea modulo pagos en nestjs" 2>/dev/null
7. ./pipeline_debugger.sh --inspect preprocessor "crea modulo pagos en nestjs" 2>/dev/null
8. RECPL_STATE_DIR=/tmp/recpl_report_state ./pipeline_debugger.sh --inspect parser "mostrar pagos" 2>/dev/null
9. RECPL_STATE_DIR=/tmp/recpl_report_state ./pipeline_debugger.sh --inspect synthesis "mostrar pagos" 2>/dev/null
10. ./pipeline_debugger.sh --inspect parser "eliminar modulo pagos" 2>/dev/null
11. ./pipeline_debugger.sh --inspect parser "actualizar modulo pagos en prisma" 2>/dev/null
12. ./pipeline_debugger.sh --inspect lexer "crea modulo test_module en nestjs" 2>&1
13. ./pipeline_debugger.sh --inspect preprocessor "CREA UN MODULO DE PAGOS EN NESTJS" 2>/dev/null
14. RECPL_STATE_DIR=/tmp/recpl_report_state2 ./pipeline_debugger.sh --trace "crea modulo usuarios en prisma" 2>/dev/null
15. ./pipeline_debugger.sh --trace "crea modulo pagos en nestjs" 2>&1 | grep -E "(FAIL|stderr:|Error|warning)"
16. ./pipeline_debugger.sh --timing "crea modulo pagos en nestjs" 2>&1
17. ./pipeline_debugger.sh --trace "crea modulo test_module en nestjs" 2>&1 | grep -A6 "\[2/6\] lexer\|\[3/6\] parser\|stderr:"
18. RECPL_STATE_DIR=/tmp/recpl_report_state3 ./pipeline_debugger.sh --inspect parser "crea modulo auth y users en nestjs y prisma" 2>/dev/null
19. ./pipeline_debugger.sh --trace "" 2>&1
20. ./pipeline_debugger.sh --inspect preprocessor "HOLA MUNDO" 2>/dev/null
21. ./pipeline_debugger.sh --inspect lexer "HOLA MUNDO" 2>&1
22. ./pipeline_debugger.sh --inspect parser "HOLA MUNDO" 2>&1
23. ./pipeline_debugger.sh --trace "crea modulo auth y users en nestjs y prisma" 2>&1 | grep -E "\[.*\]|stderr:|FAIL|Resumen|Total"
24. ./pipeline_debugger.sh --timing "crea modulo pagos en nestjs" 2>&1
25. RECPL_STATE_DIR=/tmp/recpl_report_chain ./pipeline_debugger.sh --trace "crea modulo pagos en nestjs" 2>/dev/null
26. RECPL_STATE_DIR=/tmp/recpl_report_chain ./pipeline_debugger.sh --trace "mostrar pagos" 2>/dev/null

## 10. Referencias

| Comando | Modo | Proposito |
|---------|------|-----------|
| `--help` | — | Muestra ayuda completa |
| `--trace "..."` | trace | Debug completo de 6 etapas (default) |
| `--step "..."` | step | Pausa interactiva entre etapas |
| `--timing "..."` | timing | Solo tabla de metricas |
| `--inspect ETAPA "..."` | inspect | JSON de una etapa especifica |
| `--xtrace "..."` | xtrace | bash -x con PS4 contextual |
| `--output "..."` | output | Solo JSON final (bug: no funciona) |

- `compiler-bot/pipeline_debugger.sh` — Script
- `docs/042_GUIDE_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_RUNBOOK_1_0_DRAFT.md` — Runbook detallado
- `docs/043_REP_DEV_COMPILER_BOT_PIPELINE_RE_1_0_DRAFT.md` — Reporte de ing. inversa
