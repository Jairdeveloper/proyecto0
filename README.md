# RECPL — Natural Language to IR Compiler

[![Python](https://img.shields.io/badge/python-3.11-blue)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-699_passing-green)](https://github.com/proyect0)
[![Ruff](https://img.shields.io/badge/ruff-0_errors-brightgreen)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

**RECPL** (READ-EVAL-PRINT Compiler Loop) es un compilador de lenguaje
natural a codigo IR (Intermediate Representation). Toma instrucciones en
lenguaje natural y produce una representacion intermedia canonica.
Generadores opcionales traducen el IR a codigo especifico (NestJS, Prisma,
React, etc.).

```
INPUT: "crea un modulo de pagos con NestJS y Prisma"
  ↓
[ Intent Stage ]    → clasifica intencion + extrae entidades
[ Preprocessor ]    → normaliza, segmenta, enriquece
[ Lexer (READ) ]    → DFA tokenizer con maximal munch
[ Parser (EVAL) ]   → Lark parser (AST jerarquico)
[ Semantic ]        → tabla de simbolos + type checking
[ IR Generator ]    → representacion intermedia canonica
[ Planner ]         → plan de ejecucion con dependencias
[ Synthesis ]       → generacion de codigo IR (plugins opcionales)
  ↓
OUTPUT: IR canonico (JSON) → [opcional] codigo especifico
```

## Quick Start

```bash
# 1. Instalar
pip install -e compiler-bot/agentic_pipeline/

# 2. Ejecutar (CLI)
./compiler-bot/agentic --prompt "crea un modulo de pagos con NestJS"

# 3. Ver resultado
ls modules/pagos/
```

### Solo IR (sin generacion de codigo)

```bash
# Obtener solo el IR canonico sin generar codigo especifico
./compiler-bot/agentic --prompt "crea un modulo de pagos" --ir-only

# El output es un JSON con accion, entidades y relaciones:
# {
#   "accion": "create",
#   "modulo": "pagos",
#   "entidades": ["Pago"],
#   "relaciones": [],
#   "tecnologias": [],
#   "plan": []
# }
```

### Dashboard Local

```bash
# Arrancar servidor dashboard (http://127.0.0.1:8765)
./compiler-bot/agentic --dashboard

# Puerto y host personalizados
./compiler-bot/agentic --dashboard --host 127.0.0.1 --port 8765
```

El dashboard muestra KPIs (total records, errors, success rate, prompt chain rate),
tabla de stages ordenable y detalle de registros recientes por stage.

**Notas:**
- Las metricas son acumuladas (historico desde que se empezo a registrar).
- El dashboard usa `MetricsStore` (SQLite si `_sqlite3` esta disponible,
  JSON fallback en caso contrario).
- La UI es HTML/CSS/JS local, sin CDN ni build step.

### Metricas (CLI)

```bash
./compiler-bot/agentic --metrics json      # Resumen en JSON
./compiler-bot/agentic --metrics table     # Resumen en tabla
./scripts/pipeline_stats.sh                # Dashboard shell legado
```

### Docker

```bash
docker build -t recpl .
docker run recpl "crea un modulo de pagos con NestJS"     # prompt directo
docker run recpl --prompt "crea un modulo" --output /app/modules  # flags explicitos
```

## Arquitectura (Python v2.0)

```
compiler-bot/
├── agentic                          # CLI entrypoint
├── agentic_pipeline/
│   ├── nodes/                       # 10 PipelineStages (StateGraph)
│   │   ├── intent_stage.py          # NLP: clasificador + NER + slots
│   │   ├── preprocessor.py          # Filtros en cadena (Chain of Responsibility)
│   │   ├── lexer.py                 # DFA tokenizer + trie multi-word
│   │   ├── parser.py                # Lark parser + AST builders
│   │   ├── semantic_analyzer.py     # Visitor pattern + SymbolTable
│   │   ├── ir_generator.py          # IR tree + serializacion (JSON/YAML/DOT)
│   │   ├── planner.py               # TaskGraph + Heuristic/LLM planner
│   │   ├── synthesis.py             # GeneratorFactory: 6 generadores
│   │   ├── ui_generator.py          # UI components (Builder pattern)
│   │   └── validator.py             # Chain of Responsibility (syntax+type+security)
│   ├── generators/                  # 6 generadores de codigo
│   │   ├── nestjs_generator.py
│   │   ├── prisma_generator.py
│   │   ├── react_generator.py
│   │   ├── nextjs_generator.py
│   │   ├── tailwind_generator.py
│   │   └── docker_generator.py
│   ├── grammars/                    # Gramaticas Lark
│   ├── orchestrator.py              # StateGraph integrador
│   ├── feedback_loop.py             # Metricas + ajuste de pesos
│   └── tests/                       # 699 tests (pytest)
├── recpl.sh                         # Shell v1.0 (legacy, reference)
└── agent-robot/                     # Shell agent layer (legacy, reference)
```

## Generadores Soportados

| Target | Generador | Archivos que produce |
|--------|-----------|---------------------|
| `nestjs` | NestJSGenerator | Controller, Service, Module, Entity |
| `prisma` | PrismaGenerator | schema.prisma con modelos |
| `react` | ReactGenerator | Componentes y paginas TSX |
| `nextjs` | NextJSGenerator | Pages y components con App Router |
| `tailwind` | TailwindGenerator | tailwind.config.js + globals.css |
| `docker` | DockerGenerator | Dockerfile + docker-compose.yml |

## Lenguaje Soportado

```
> crea un modulo de pagos en NestJS
> crear entidad Usuario con nombre:string email:string edad:int
> pagina login con formulario de registro
> base de datos postgresql con docker
```

## Roadmap

| Sprint | Objetivo | Estado |
|--------|----------|--------|
| S15 | NLP + Intent pipeline | COMPLETED |
| S16 | Integracion de generators | IN PROGRESS |
| S17 | Performance + snapshot tests | PLANNED |
| S18 | Docker demo + README | PLANNED |
| S19 | Documentacion API + archive | PLANNED |
| S20 | Onboarding + release v2.1.0 | PLANNED |

Ver `docs/093_PLAN_DEV_SPRINT16_1_0_DRAFT.md` para detalle del Sprint 16.

## Tests

```bash
cd compiler-bot/agentic_pipeline
python -m pytest tests/ -v --tb=short
```

699 tests cubriendo todos los stages del pipeline.

## Documentacion

Ver `docs/` para planes, reportes y guias detalladas.

## Licencia

MIT
