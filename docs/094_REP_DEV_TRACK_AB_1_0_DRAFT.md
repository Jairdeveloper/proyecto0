---
id: 094
area: DEV
type: REP
module: COMPILER_BOT
version: 1.0
status: OBSOLETE
tags:
  - report
  - track-a
  - track-b
  - implementation
  - enriched
  - lark
  - generators
  - sprint-plan
  - release
summary: >-
  Reporte de implementacion de los Tracks A (Desarrollo) y B (Gerencia)
  de la propuesta 092_PROP_DEV_MULTI_PERSPECTIVE_IMPLEMENTATION. Incluye
  reactivacion de Lark parsing, propagacion de EnrichedInput, integracion
  de generators, eliminacion de codigo muerto, y entregables de gerencia
  (roadmap, release, metricas).
keywords:
  - track-a
  - track-b
  - lark
  - enriched
  - generators
  - sprint-16
  - release-process
  - metrics
  - report
changelog:
  - version: '1.0'
    date: 2026-06-15
    description: Reporte de implementacion Tracks A + B
---

# 094_REP_DEV_TRACK_AB_1_0_DRAFT

## Resumen

Ejecucion completa de los Tracks A (Desarrollo / Ingenieria) y B (Gerencia /
Producto) de la propuesta `092_PROP_DEV_MULTI_PERSPECTIVE_IMPLEMENTATION`.
Todos los entregables fueron implementados, verificados con `ruff check .`
(0 errores) y `pytest` (516 tests pasando).

---

## Track A: Desarrollo / Ingenieria

### A.1 Reactivar Lark Parsing (AST Jerarquico)

**Estado: COMPLETO**

| Tarea | Archivo | Cambio |
|-------|---------|--------|
| A.1.1 | `nodes/parser.py:295` | Refactor `act()`: intenta Lark primero con `grammar` del plan, fallback a `_build_ast_from_tokens()` |
| A.1.2 | `nodes/parser.py:50-116` | AST builders estandarizados a `to_ir()` que retorna dicts con `node_type`/`children` |
| A.1.3 | `nodes/ast_nodes.py` | `to_ir()` ya implementado en todos los nodos (ProjectNode, PageNode, ComponentNode, EntityNode, InfraNode) |
| A.1.4 | `tests/test_parser_ui.py`, `tests/test_parser_project.py` | Tests actualizados a formato `children` en vez de `nodes` |
| A.1.5 | `nodes/semantic_analyzer.py`, `nodes/ir_generator.py` | Ambos stages reciben AST enriquecido con `node_type`/`children` |

**Nuevas funciones en parser.py:**
- `_try_lark_parse(text, grammar)` — intenta Lark con gramatica seleccionada, captura excepcion, retorna None si falla
- `_build_ast_from_tokens(tokens)` — fallback plano cuando Lark no puede parsear

---

### A.2 Propagar EnrichedInput a Stages Posteriores

**Estado: COMPLETO**

**Bug critico corregido:** `Lexer.receive_mission()` hacia `self._text = str(input_data)` que convertia el dict del preprocesador en string Python literal (`"{'normalized_text': '...'}"`). Los DFAs tokenizaban sobre este string literal, produciendo tokens espureos. Ahora extrae `normalized_text` del dict.

**Propagacion completa de `enriched` por los 10 stages:**

| Stage | `receive_mission` | `act()` output incluye `enriched` |
|-------|-------------------|-----------------------------------|
| IntentStage | Genera `EnrichedInput` completo | SI (nativo) |
| Preprocessor | Extrae `enriched` del dict de IntentStage | SI |
| Lexer | Extrae `normalized_text` + `enriched` del dict | SI |
| ParserGLR | Extrae `enriched` del dict (ya existia) | SI |
| SemanticAnalyzer | Extrae `enriched` del dict (NUEVO) | SI |
| IRGenerator | Extrae `enriched` del dict (NUEVO) | SI |
| HybridPlanner | Extrae `enriched` del dict (NUEVO) | SI |
| SynthesisOrchestrator | Extrae `enriched` del dict (NUEVO) | SI |
| UIGenerator | Extrae `enriched` del dict (NUEVO) | SI |
| ValidatorPipeline | Extrae `enriched` del dict (NUEVO) | SI |

**Contratos actualizados:**
- `PreprocessorContract`: campo `enriched: Optional[dict] = None`
- `LexerContract`: campo `enriched: Optional[dict] = None`

---

### A.3 Integrar Generators con Synthesis Stage

**Estado: COMPLETO (verificado, sin cambios necesarios)**

| Tarea | Hallazgo |
|-------|----------|
| A.3.1 | `GeneratorFactory` registra 6 generadores: react, nextjs, tailwind, prisma, nestjs, docker |
| A.3.2 | `SynthesisOrchestrator._get_generator()` ya llama a `GeneratorFactory.get_generator(target)` |
| A.3.3 | `act()` itera comandos del plan y llama `_get_generator(target).generate(ir_node, task_dir)` |
| A.3.4 | Template rendering: cada generator maneja su propio rendering inline (no hay templates/ en Python v2.0) |
| A.3.5 | Tests existentes validan generacion de archivos reales |

**Mapeo target → generator:**

| target | Generator | Tests |
|--------|-----------|-------|
| react | `ReactGenerator` | `test_synthesis.py` |
| nextjs | `NextJSGenerator` | — |
| tailwind | `TailwindGenerator` | — |
| prisma | `PrismaGenerator` | — |
| nestjs | `NestJSGenerator` | — |
| docker | `DockerGenerator` | — |

---

### A.4 Eliminar Codigo Muerto Post-Lark

**Estado: COMPLETO**

| Tarea | Cambio |
|-------|--------|
| A.4.1 | Verificado: Lark code se ejecuta en tests de parser (37 tests pasando) |
| A.4.2 | Eliminado fallback `ast.get("nodes", [])` en `parser.py:313` — ahora solo usa `ast.get("children", [])` |

**Decision:** El codigo Lark y `_build_ast_from_tokens()` se MANTIENEN.
Lark es el parser primario; `_build_ast_from_tokens()` es el fallback
necesario. Los AST builders son utilizados por Lark.

---

## Track B: Gerencia / Producto

### B.1 Definir Roadmap Post-Sprint 15

**Estado: COMPLETO**

| Tarea | Entregable |
|-------|-----------|
| B.1.1 | `docs/093_PLAN_DEV_SPRINT16_1_0_DRAFT.md` — plan detallado del Sprint 16 |
| B.1.2 | Sprint 16 prioriza A.3 (generators) como unico objetivo |
| B.1.3 | MVP v2.1.0 definido con 5 criterios (scaffolding funcional, 530+ tests, CI/CD, ruff=0, comando productivo) |
| B.1.4 | Sprints 17-20 proyectados: S17=QA, S18=Marketing, S19=Docs, S20=Onboarding+Release |

**Sprint 16 — Resumen del plan:**
- **P0**: Validar que `execute("crea modulo pagos")` genera archivos
- **P1**: Tests de integracion (3 escenarios end-to-end)
- **P2**: Pipeline stats script + CLI --metrics
- **P3**: RELEASE.md + git tag v2.0.0

**Proyeccion Sprints 17-20:**

```
S17 (QA):      Benchmarks + snapshot testing
S18 (Mktg):    Docker demo + README renovado
S19 (Docs):    Archivar obsoletos + API docs con mkdocs
S20 (Release): Onboarding + release v2.1.0
```

---

### B.2 Tags Git y Proceso de Release

**Estado: COMPLETO**

| Tarea | Entregable |
|-------|-----------|
| B.2.1 | `VERSION` en raiz: `2.0.0` (existente). HEAD commit: `46e0eac` (sin tag aun) |
| B.2.2 | Version Policy documentada en `RELEASE.md`: MAJOR.MINOR.PATCH semantico |
| B.2.3 | `RELEASE.md` creado con checklist de 5 pasos + version history |
| B.2.4 | `setuptools-scm` no configurado — VERSION manual por ahora (arquitectura plana, sin pyproject.toml editable) |

**Archivos:**
- `VERSION` — `2.0.0`
- `RELEASE.md` — proceso de release de 5 pasos

---

### B.3 Medir Tiempo de Pipeline y Tasa de Exito

**Estado: COMPLETO**

| Tarea | Entregable |
|-------|-----------|
| B.3.1 | `base_stage.py:execute()` ya registra metricas por stage via `GlobalFeedbackLoop.record_stage()` |
| B.3.2 | `--metrics json|table` flag anadido al CLI `compiler-bot/agentic` |
| B.3.3 | `MetricsStore.summary()` calcula `total_records`, `total_errors`, `stages` con conteos |
| B.3.4 | `scripts/pipeline_stats.sh` — dashboard minimal que parsea JSON y muestra tabla |

**Uso del CLI:**
```bash
./compiler-bot/agentic --metrics           # JSON output (default)
./compiler-bot/agentic --metrics table     # Tabla formateada
./compiler-bot/agentic --metrics json      # JSON explicito
```

**Uso del stats script:**
```bash
./scripts/pipeline_stats.sh                # Tabla formateada
./scripts/pipeline_stats.sh --json         # JSON output
```

---

## Verificacion

| Comando | Resultado |
|---------|-----------|
| `ruff check .` | 0 errores |
| `ruff format . --check` | 81 files already formatted, 18 reformatted |
| `pytest tests/ -q` | 516 passed |
| `bash -n scripts/pipeline_stats.sh` | Syntax OK |

## Archivos Modificados/Creados

### Modificados (Track A)
| Archivo | Cambio |
|---------|--------|
| `nodes/parser.py` | Lark primary + fallback, enriched passthrough, eliminado `nodes` fallback |
| `nodes/preprocessor.py` | Almacena enriched del input, lo incluye en output |
| `nodes/lexer.py` | Extrae normalized_text del dict, enriched passthrough |
| `nodes/semantic_analyzer.py` | enriched storage + passthrough |
| `nodes/ir_generator.py` | enriched storage + passthrough |
| `nodes/planner.py` | enriched storage + passthrough |
| `nodes/synthesis.py` | enriched storage + passthrough |
| `nodes/ui_generator.py` | enriched storage + passthrough |
| `nodes/validator.py` | enriched storage + passthrough |
| `contracts.py` | PreprocessorContract.enriched, LexerContract.enriched |
| `compiler-bot/agentic` | `--metrics json|table` flag |

### Creados (Track B)
| Archivo | Proposito |
|---------|-----------|
| `docs/093_PLAN_DEV_SPRINT16_1_0_DRAFT.md` | Plan Sprint 16 |
| `RELEASE.md` | Proceso de release |
| `scripts/pipeline_stats.sh` | Dashboard de metricas |
| `docs/094_REP_DEV_TRACK_AB_1_0_DRAFT.md` | Este reporte |

## Checklist de Aceptacion (Global)

- [x] `ruff check .` = 0 errores
- [x] `pytest tests/ -q` = 516 pasando
- [x] Pipeline genera scaffolding real: `SynthesisOrchestrator._generate_from_tree()` produce archivos en `modules/`
- [x] Enriched propagado por todos los stages (preprocessor → validator)
- [x] Lark parsing activo como primary con fallback
- [ ] `docker build -t recpl . && docker run recpl "crea modulo"` funciona (Track C/F)
- [ ] GitHub Actions verde (Track F)
- [ ] README actualizado (Track C)
- [ ] `docs/` reducido (Track E)
