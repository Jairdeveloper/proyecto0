# RECPL Compiler Bot

**RECPL** (READ-EVAL-PRINT Compiler Loop) es un bot shell que procesa instrucciones en lenguaje natural utilizando un pipeline compilador clasico basado en la teoria de Aho, Sethi y Ullman (Dragon Book).

```
INPUT: "crea un modulo de pagos en NestJS"
  ↓
[ PREPROCESADOR ] → normaliza, lowercase, segmenta
  ↓
[ LEXER (READ) ]  → DFA con maximal munch → tokens JSON
  ↓
[ PARSER (EVAL) ] → LL(1) recursivo descendente → AST JSON
  ↓
[ SEMANTICO ]     → tabla de simbolos + type checking
  ↓
[ IR GENERATOR ]  → representacion intermedia canonica (IR.json)
  ↓
[ SYNTHESIS ]     → respuesta del bot + scaffolding de archivos
  ↓
OUTPUT: "Generando modulo Pagos en NestJS..."
         + archivos generados en modules/pagos/
```

## Arquitectura

```
compiler-bot/
├── frontend/               # ANALISIS (Front-end)
│   ├── preprocessor.sh     # Normaliza input: trim, lowercase, split
│   ├── lexer.sh            # DFA tokenizer con maximal munch
│   ├── parser.sh           # Parser LL(1) recursivo descendente
│   └── semantic.sh         # Tabla de simbolos + validacion semantica
├── middleend/
│   └── ir_generator.sh     # AST → IR.json canonico
├── backend/                # SINTESIS (Back-end)
│   ├── synthesis.sh        # IR.json → respuesta del bot
│   └── scaffold.sh         # Templates → archivos en disco
├── templates/              # Scaffolds reutilizables
│   ├── module-nestjs/      # NestJS: module, controller, service
│   ├── entity-nestjs/      # NestJS: entity class
│   └── module-prisma/      # Prisma: modelo de datos
├── recpl.sh                # LOOP principal (interactivo/batch)
└── tests/
    └── run_tests.sh        # 47 tests automatizados
```

## Quick Start

```sh
# Modo interactivo
./compiler-bot/recpl.sh

# Modo batch
echo "crea un modulo de pagos en NestJS" | ./compiler-bot/recpl.sh

# Pipeline completo paso a paso
input=$(./compiler-bot/frontend/preprocessor.sh "crea un modulo de pagos en nestjs")
./compiler-bot/frontend/lexer.sh "$input" | \
  ./compiler-bot/frontend/parser.sh | \
  ./compiler-bot/frontend/semantic.sh | \
  ./compiler-bot/middleend/ir_generator.sh | \
  ./compiler-bot/backend/synthesis.sh

# Ejecutar tests
./compiler-bot/tests/run_tests.sh
```

## Lenguaje Soportado

### Acciones

| Verbo | Token | Ejemplo |
|-------|-------|---------|
| crear, generar, make, new | `ACTION_CREATE` | "crea modulo pagos" |
| eliminar, borrar, delete, remove | `ACTION_DELETE` | "eliminar payments" |
| actualizar, modificar, update, edit | `ACTION_UPDATE` | "actualizar usuarios" |
| mostrar, listar, get, show, read | `ACTION_READ` | "listar productos" |

### Ejemplos de Instrucciones

```
> crea un modulo de pagos en NestJS
> listar usuarios
> eliminar modulo payments
> actualizar entidad productos en prisma
> crear modulo de usuarios en Prisma
> mostrar payments
> quit
```

## Scaffolding

Las instrucciones `CREATE` generan archivos reales en `modules/<nombre>/`:

```
modules/pagos/
├── pagos.controller.ts
├── pagos.module.ts
└── pagos.service.ts
```

Los templates usan placeholders `__NAME__` (PascalCase) y `__LOWERNAME__` (camelCase).

## Tests

```sh
./compiler-bot/tests/run_tests.sh
```

Suite de 47 tests que cubren:

| Area | Tests |
|------|-------|
| Sintaxis (bash -n) | 8 |
| Preprocesador | 3 |
| Lexer | 8 |
| Parser | 5 |
| Pipeline completo | 5 |
| Errores semanticos | 2 |
| LOOP batch | 4 |
| Scaffolding | 3 |
| Persistencia de estado | 1 |
| Ejecutables | 8 |

## Estado del Proyecto

| Fase | Estado |
|------|--------|
| FASE-1: Nucleo RECPL (lexer + parser) | COMPLETED |
| FASE-2: Semantica e IR | COMPLETED |
| FASE-3: Synthesis y Output | COMPLETED |
| FASE-4: Trazabilidad y Scoring | PENDING (opcional) |
| FASE-5: Tests | COMPLETED (47 tests) |

## Documentacion

Los documentos de especificacion y plan de accion estan en `docs/`:

- `006_PROP_DEV_COMPILER_BOT_1_0_DRAFT.md` — Propuesta y especificacion completa
- `007_GUIDE_DEV_COMPILER_BOT_1_0_DRAFT.md` — Plan de accion detallado
- `009_GUIDE_DEV_COMPILER_BOT_IMPL_REPORT_1_0_DRAFT.md` — Reporte de implementacion

## Convenciones

Todos los scripts siguen `docs/000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md`:
- No `set -e`, no `eval`
- Variables siempre double-quoted
- Indentacion 4 espacios
- Funciones `snake_case`, constantes `SCREAMING_SNAKE_CASE`
- Validacion: `bash -n` + `shellcheck`
