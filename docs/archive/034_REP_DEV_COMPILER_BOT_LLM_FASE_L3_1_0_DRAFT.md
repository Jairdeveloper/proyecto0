---
id: 034
area: dev
type: rep
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - report
  - implementation
  - fase-l3
  - llm
  - router
  - strategy-pattern
  - compiler-bot
  - recpl
summary: "Reporte de implementacion de la FASE-L3 del plan 031: router inteligente (router.sh) con patron Strategy, integracion del router en recpl.sh, y flags CLI --llm/--provider. Incluye archivos creados, modificaciones, validaciones y resultados de pruebas."
keywords:
  - reporte
  - implementacion
  - fase-l3
  - router
  - strategy
  - integracion
  - validacion
  - recpl
  - bash
changelog:
  - version: 1.0
    date: 2026-06-11
    author: workflow-agent
    description: Implementacion de FASE-L3 del plan 031 — router inteligente e integracion en recpl.sh
---

# Reporte de Implementacion: FASE-L3 — Router Inteligente

> **Plan de referencia:** `031_PLAN_DEV_COMPILER_BOT_LLM_EXECUTION_1_0_DRAFT.md`
> **Fase anterior:** `033_REP_DEV_COMPILER_BOT_LLM_FASE_L2_1_0_DRAFT.md`
> **Guia de estilo:** `000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md`

---

## 0. Resumen

Se implemento la FASE-L3 del plan de integracion LLM: el router
inteligente que decide si una instruccion se procesa con el pipeline
deterministico o con el LLM, y su integracion completa en `recpl.sh`.

**Estado:** COMPLETADO

---

## 1. Archivos Creados y Modificados

### 1.1 `compiler-bot/frontend/router.sh` (NUEVO, 146 lineas)

**Proposito:** Router inteligente que implementa el patron Strategy.
Decide el camino de procesamiento segun la estrategia seleccionada.

**Funciones:**

| Funcion | Descripcion |
|---------|-------------|
| `is_deterministic_candidate()` | Evalua si una instruccion es apta para el pipeline deterministico segun modo y heuristica |
| `run_deterministic()` | Ejecuta el pipeline completo (preprocess → lexer → parser → semantic → IR) |
| `router()` | Punto de entrada: selecciona estrategia, ejecuta, con fallback |

**Estrategias de ruteo:**

| Modo | Comportamiento |
|------|----------------|
| `auto` (default) | Intenta deterministico si instruccion <= 10 palabras y tiene keywords conocidas; si falla → fallback a LLM |
| `deterministic` | Solo pipeline deterministico, sin fallback a LLM |
| `llm` | Envia directamente al LLM, salta el pipeline deterministico |

**Heuristica en modo `auto`:**
- Instrucciones > 10 palabras → van al LLM
- Instrucciones con keywords (`crea`, `genera`, `elimina`, `muestra`, etc.) → intentan deterministico
- Instrucciones sin match claro ("hola", "que es nestjs?") → van al LLM

**Flujo del router:**

```
router("crea modulo pagos en nestjs")
    │
    ├─ is_deterministic_candidate? → SI (modo auto, <= 10 palabras, keyword "crea")
    │
    ├─ run_deterministic()
    │   ├─ mkdir -p RECPL_STATE_DIR
    │   ├─ preprocessor.sh  → texto normalizado
    │   ├─ lexer.sh         → tokens JSON
    │   ├─ parser.sh        → AST JSON
    │   ├─ semantic.sh      → AST validado + symbol table
    │   └─ ir_generator.sh  → IR.json
    │
    ├─ exito? → retornar IR.json
    │
    └─ fallo? → fallback a LLM (si no es modo deterministic-only)
```

### 1.2 `compiler-bot/recpl.sh` (MODIFICADO, de 262 a 276 lineas)

**Cambios realizados:**

| Cambio | Descripcion |
|--------|-------------|
| Version | `1.1.0` → `1.2.0` |
| `process_instruction()` | Reemplazado: ahora llama al router en vez de ejecutar el pipeline inline |
| `main()` flag parsing | Nuevo bloque `while` que parsea `--llm` y `--provider` antes del dispatch existente |
| `show_help()` | Nuevas banderas `--llm`, `--provider` y seccion `VARIABLES DE ENTORNO` |

**Detalle de `process_instruction()` (nueva):**

```sh
process_instruction() {
    raw_input="$1"

    # Preprocesar (siempre)
    preprocessed=$(...preprocessor.sh...)

    # Router decide el camino (deterministico o LLM)
    result=$(...router.sh "$preprocessed"...)

    # Si respond/clarify → mostrar directamente
    # Si scaffolding → pasar a synthesis.sh
}
```

**Flags nuevos:**

| Flag | Efecto |
|------|--------|
| `--llm` | Exporta `RECPL_LLM_MODE=llm` antes del dispatch |
| `--provider claude|openai` | Exporta `RECPL_LLM_PROVIDER=valor` antes del dispatch |

Ambos flags se pueden combinar con `-c` y `-f`:
```sh
./recpl.sh --llm -c "crea un modulo de pagos en NestJS"
./recpl.sh --provider openai -c "explica que es un modulo"
```

---

## 2. Validaciones Realizadas

### 2.1 Sintaxis (`bash -n`)

| Archivo | Resultado |
|---------|-----------|
| `frontend/router.sh` | OK — sin errores de sintaxis |
| `recpl.sh` | OK — sin errores de sintaxis |

### 2.2 Logica de ruteo (`is_deterministic_candidate`)

| Entrada | Modo | Resultado | Esperado |
|---------|------|-----------|----------|
| `"crea modulo pagos en nestjs"` | auto | `0` (deterministico) | ✅ |
| `"crea modulo pagos en nestjs"` | llm | `1` (LLM) | ✅ |
| `"texto muy largo que supera las diez palabras de limite"` | auto | `1` (LLM) | ✅ |
| `"hola"` | auto | `1` (LLM) | ✅ |
| `"listar usuarios"` | auto | `0` (deterministico) | ✅ |

### 2.3 Pipeline deterministico (`run_deterministic`)

| Prueba | Entrada | Resultado |
|--------|---------|-----------|
| Scaffolding exitoso | `"crea modulo pagos en nestjs"` | `{"accion":"scaffold","tipo":"module","nombre":"Pagos","tech":"NestJS"}` |
| Bug corregido: state dir | Sin `RECPL_STATE_DIR` existente | `mkdir -p` automatico en `run_deterministic()` |

### 2.4 Integracion end-to-end (`recpl.sh`)

| Comando | Resultado |
|---------|-----------|
| `./recpl.sh --version` | `RECPL Compiler Bot v1.2.0` |
| `./recpl.sh -c "crea modulo pagos en nestjs"` | `{"tipo_respuesta":"action","mensaje":"Generando module Pagos en nestjs..."}` |
| `./recpl.sh --llm -c "hola"` | `{"tipo_respuesta":"error","mensaje":"Error al procesar: hola"}` (sin API key) |
| `./recpl.sh --provider unknown -c "test"` | `{"tipo_respuesta":"error","mensaje":"Error al procesar: test"}` |
| `./recpl.sh --help` | Muestra flags `--llm`, `--provider` y vars `RECPL_LLM_*` |

### 2.5 Checklist FASE-L3

- [x] `frontend/router.sh` — is_deterministic_candidate, run_deterministic, router()
- [x] Modificar `recpl.sh` — process_instruction usa router
- [x] Flag `--llm` en recpl.sh (exporta `RECPL_LLM_MODE=llm`)
- [x] Flag `--provider` en recpl.sh (exporta `RECPL_LLM_PROVIDER`)
- [x] Variable `RECPL_LLM_MODE` (auto|llm|deterministic)
- [x] Variable `RECPL_LLM_PROVIDER` (claude|openai)
- [x] `show_help()` actualizado con nuevas banderas y variables de entorno
- [x] Validacion: `bash -n recpl.sh` (OK)
- [x] Validacion: `bash -n router.sh` (OK)
- [x] Validacion: modo deterministico funcionando
- [x] Validacion: fallback a LLM cuando deterministico falla

---

## 3. Bug Encontrado y Corregido

### 3.1 `RECPL_STATE_DIR` inexistente en `run_deterministic`

**Problema:** `semantic.sh` requiere que `RECPL_STATE_DIR` exista para
escribir la tabla de simbolos. El `run_deterministic()` pasaba la
variable pero sin crear el directorio, causando:

```
cannot create /tmp/recpl_state_XXXX/symbols.tmp: Directory nonexistent
exit: 2
```

**Solucion:** Agregar `mkdir -p "$state_dir"` al inicio de
`run_deterministic()`, antes de cualquier paso del pipeline.

```sh
run_deterministic() {
    instruction="$1"
    state_dir="${RECPL_STATE_DIR:-/tmp/recpl_state_$$}"
    mkdir -p "$state_dir"   # ← solucion
    ...
}
```

**Leccion:** El router es responsable de garantizar las precondiciones
del pipeline deterministico (directorio de estado existente) antes de
invocar los subprocesos.

---

## 4. Decisiones de Diseno

### 4.1 Parseo de flags --llm y --provider antes del dispatch

Se implemento como un bucle `while` al inicio de `main()`, antes del
`case` existente que parsea `-c`, `-f`, `--help`. Esto permite que
`--llm` y `--provider` se combinen con otros flags:

```sh
./recpl.sh --llm -c "crea modulo pagos"
./recpl.sh --provider claude -f instrucciones.txt
```

### 4.2 Fallback a LLM en modo auto

Cuando el pipeline deterministico falla (lexer, parser o semantic
retornan error), el router intenta el LLM automaticamente. Esto solo
ocurre en modo `auto`. En modo `deterministic`, no hay fallback.

### 4.3 Router como subproceso independiente

`router.sh` se invoca como subproceso (no source), lo que:
- Aísla el entorno del router del script principal
- Permite probarlo independientemente con `./frontend/router.sh`
- Sigue el mismo patron que los otros componentes del pipeline

---

## 5. Estado Actual del Pipeline LLM

### Arbol completo tras FASE-L3

```
compiler-bot/
├── providers/
│   ├── provider_common.sh    ← L1: utilidades
│   ├── claude.sh             ← L1: adapter Claude
│   └── openai.sh             ← L1: adapter OpenAI
├── frontend/
│   ├── llm_classifier.sh     ← L2: fachada LLM
│   ├── router.sh             ← L3: router inteligente (NUEVO)
│   ├── preprocessor.sh       ← existente
│   ├── lexer.sh              ← existente
│   ├── parser.sh             ← existente
│   └── semantic.sh           ← existente
├── middleend/
│   ├── ir_generator.sh       ← existente
│   └── llm_ir_mapper.sh      ← L2: mapper IR
├── backend/
│   ├── synthesis.sh          ← existente
│   └── scaffold.sh           ← existente
├── recpl.sh                  ← L3: integrado con router (v1.2.0)
└── tests/
    └── run_tests.sh           ← existente (pendiente L4)
```

### Pipeline hibrido funcional

```
INPUT → preprocessor → router ─┬─ deterministic (lexer→parser→semantic→IR)
                                │
                                └─ LLM (classifier → provider → mapper → IR)
                                │
                                ▼
                            synthesis → scaffold → OUTPUT
```

---

## 6. Proximos Pasos

Completada FASE-L3. La siguiente fase (FASE-L4) debe implementar:

1. `tests/test_router.sh` — tests del router
2. `tests/run_tests.sh` — actualizar con nuevos tests
3. Ejecutar tests existentes y verificar que pasan
4. `shellcheck` en todos los scripts nuevos
5. Documentacion de uso actualizada

Ver `031_PLAN_DEV_COMPILER_BOT_LLM_EXECUTION_1_0_DRAFT.md` seccion FASE-L4.

---

## 7. Referencias

- `031_PLAN_DEV_COMPILER_BOT_LLM_EXECUTION_1_0_DRAFT.md` — Plan de ejecucion
- `033_REP_DEV_COMPILER_BOT_LLM_FASE_L2_1_0_DRAFT.md` — Fase anterior (classifier + mapper)
- `000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md` — Guia de estilo shell
