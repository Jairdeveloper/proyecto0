---
id: 092
area: DEV
type: PROP
module: COMPILER_BOT
version: 1.0
status: IMPLEMENTED
tags:
  - proposal
  - implementation
  - development
  - management
  - marketing
  - qa
  - devops
  - documentation
summary: >-
  Propuesta de implementacion detallada para cada seccion del analisis
  multi-perspectiva (091). Incluye tareas concretas, dependencias,
  esfuerzo estimado y criterios de aceptacion.
keywords:
  - proposal
  - implementation-plan
  - pipeline-fix
  - ci-cd
  - generators
  - parser
  - documentation
  - devops
changelog:
  - version: '1.0'
    date: 2026-06-15
    description: Propuesta de implementacion multi-perspectiva
---

# 092_PROP_DEV_MULTI_PERSPECTIVE_IMPLEMENTATION_1_0_DRAFT

## Resumen

Propuesta de implementacion detallada para cada punto del analisis
`091_REP_MGT_MULTI_PERSPECTIVE_ANALYSIS_1_0_DRAFT`. Cada seccion
contiene tareas concretas, dependencias, esfuerzo estimado y
criterios de aceptacion. El plan se organiza en 6 tracks paralelos
con una unica ruta critica: la integracion de generators.

```
Track A: Desarrollo        ── Reactivar Lark + integrar generators
Track B: Gerencia           ── Roadmap + metricas + releases
Track C: Marketing          ── Demo + README + naming
Track D: QA                 ── Performance + snapshot + CI
Track E: Documentacion      ── Archivar + onboarding + API docs
Track F: DevOps             ── GitHub Actions + Docker + pre-commit
```

---

## Track A: Desarrollo / Ingenieria

### A.1 Reactivar Lark Parsing (AST Jerarquico)

**Problema:** El parser usa `_build_ast_from_tokens()` que produce un
AST plano (lista de acciones y entidades). Las gramaticas Lark completas
project, data, ui, infra y sus builders estan instalados pero no se
ejecutan.

**Solucion:** Modificar `ParserGLR.act()` para que intente el parsing
Lark primero, y solo use `_build_ast_from_tokens()` como fallback.

**Tareas:**

| # | Tarea | Archivos | Dependencia |
|---|-------|----------|-------------|
| A.1.1 | Refactor `act()`: intentar Lark con `grammar` del plan, capturar excepcion, fallback a `_build_ast_from_tokens` | `nodes/parser.py:291` | — |
| A.1.2 | Verificar que `AST_BUILDERS` devuelvan ProjectNode con `to_ir()` estandar | `nodes/parser.py:50-116` | A.1.1 |
| A.1.3 | Anadir `ast_to_ir()` en ast_nodes.py para convertir ProjectNode → dict plano | `nodes/ast_nodes.py` | A.1.2 |
| A.1.4 | Actualizar tests de parser_ui y parser_project para validar AST jerarquico | `tests/test_parser_ui.py`, `tests/test_parser_project.py` | A.1.1 |
| A.1.5 | Verificar stages downstream (semantic, IR) reciben AST enriquecido | `nodes/semantic_analyzer.py`, `nodes/ir_generator.py` | A.1.3 |

**Esfuerzo:** 2-3 dias
**Criterio de aceptacion:** `execute("pagina login con formulario")`
produce AST con `node_type: "project"` y children con `node_type: "page"`.

**Codigo ejemplo del cambio en `act()`:**

```python
def act(self, plan: ActionPlan) -> StageOutput:
    if not self._tokens:
        return StageOutput(... error="No tokens received from lexer")

    grammar = self.grammar_name
    if plan.steps:
        grammar = plan.steps[0].get("grammar", grammar)

    text = " ".join(t.get("value", "") for t in self._tokens)
    ast = self._try_lark_parse(text, grammar) or self._build_ast_from_tokens(self._tokens)
    return StageOutput(
        output_data={"ast": ast, "grammar": grammar},
        metrics={"tokens": len(self._tokens), "ast_nodes": len(ast.get("nodes", []))},
    )
```

---

### A.2 Propagar EnrichedInput a Stages Posteriores

**Problema:** IntentStage produce un `EnrichedInput` completo con
intent, entities, slots, ambiguity, pero Preprocessor solo extrae
`raw` y `domain`. El contexto NLP se pierde.

**Solucion:** Propagar `enriched` como campo en el output de cada
stage, acumulativo. Cada stage recibe `input_data` con `enriched` y
lo pasa al siguiente.

**Tareas:**

| # | Tarea | Archivos | Dependencia |
|---|-------|----------|-------------|
| A.2.1 | Modificar contrato `PreprocessorContract`: anadir campo `enriched: Optional[dict]` | `contracts.py` | — |
| A.2.2 | Modificar `Preprocessor.act()`: incluir `enriched` en output_data | `nodes/preprocessor.py:176` | A.2.1 |
| A.2.3 | Modificar `Lexer.receive_mission()`: aceptar `enriched` en input dict | `nodes/lexer.py` | A.2.2 |
| A.2.4 | Propagar `enriched` por todos los stages hasta synthesis | Todos los nodes | A.2.3 |
| A.2.5 | Exponer `enriched.intent` en synthesis para personalizar generacion | `nodes/synthesis.py` | A.2.4 |

**Esfuerzo:** 1-2 dias
**Criterio de aceptacion:** Debugger trace muestra `enriched: {...}`
en todos los stages desde preprocessor hasta validator.

---

### A.3 Integrar Generators con Synthesis Stage

**Problema:** Los 12 archivos en `generators/` (nestjs_generator.py,
prisma_generator.py, react_generator.py, docker_generator.py, etc.)
nunca son invocados. SynthesisStage produce `generated_files: []`.

**Solucion:** Conectar `GeneratorFactory` dentro de
`SynthesisOrchestrator.act()`. El plan del planner contiene los
targets a generar. Synthesis los itera y llama al generator
correspondiente.

**Tareas:**

| # | Tarea | Archivos | Dependencia |
|---|-------|----------|-------------|
| A.3.1 | Auditar `GeneratorFactory`: que generators existen, que entradas esperan | `generators/__init__.py`, `generators/base_generator.py` | — |
| A.3.2 | Implementar `SynthesisOrchestrator._select_generators(plan, enriched)` | `nodes/synthesis.py` | A.3.1 |
| A.3.3 | Conectar factory en `act()`: iterar targets del plan, llamar generator, acumular archivos | `nodes/synthesis.py:act()` | A.3.2 |
| A.3.4 | Anadir rendering de templates desde `templates/` del shell v1.0 | `generators/template_renderer.py` | A.3.3 |
| A.3.5 | Tests: verificar que `execute("crea un modulo de pagos")` genere archivos reales | `tests/test_synthesis.py` | A.3.3 |

**Esfuerzo:** 3-4 dias (ruta critica)
**Criterio de aceptacion:**
```bash
./compiler-bot/agentic --prompt "crea un modulo de pagos con NestJS y Prisma"
# → genera: modules/pagos/pagos.controller.ts, pagos.module.ts, pagos.service.ts, pagos.prisma
```

---

### A.4 Eliminar Codigo Muerto

**Problema:** `_build_project_ast`, `_build_ui_ast`, `_build_data_ast`,
`_build_infra_ast` y `AST_BUILDERS` (~200 lineas) no se usan desde
que el parser bypassa Lark.

**Nota:** NO eliminar hasta que A.1 este completo (Lark parsing
reactivado usara estos builders).

**Tareas:**

| # | Tarea | Archivos | Dependencia |
|---|-------|----------|-------------|
| A.4.1 | Post-A.1: verificar que codigo Lark se ejecuta en tests de parser | `nodes/parser.py` | A.1 |
| A.4.2 | Si A.1 reactivo Lark, mantener codigo. Si no, eliminar AST_BUILDERS y funciones muertas | `nodes/parser.py:50-212` | A.1 |

**Esfuerzo:** 0.5 dias
**Criterio de aceptacion:** `ruff check .` = 0, `pytest` = 516+.

---

## Track B: Gerencia / Producto

### B.1 Definir Roadmap Post-Sprint 15

**Tareas:**

| # | Tarea | Esfuerzo |
|---|-------|----------|
| B.1.1 | Crear `093_PLAN_DEV_SPRINT16_1_0_DRAFT.md` con objetivo: integrar generators | 1 dia |
| B.1.2 | Priorizar A.3 (generators) como unico objetivo del Sprint 16 | 0.5 dias |
| B.1.3 | Definir criterios de "MVP funcional" para v2.1.0 | 0.5 dias |
| B.1.4 | Proyectar Sprints 17-20 con dependencias entre tracks | 1 dia |

**MVP v2.1.0 (definicion):**
- Pipeline genera scaffolding NestJS + Prisma funcional
- Comando `recpl "crea un modulo de pagos"` produce archivos en `modules/`
- 530+ tests pasando
- CI/CD pasando en cada PR

---

### B.2 Tags Git y Proceso de Release

**Tareas:**

| # | Tarea | Comando/Herramienta |
|---|-------|---------------------|
| B.2.1 | Crear tag `v2.0.0` en commit actual | `git tag -a v2.0.0 -m "v2.0.0 — NLP pipeline complete"` |
| B.2.2 | Definir Version Policy en `VERSION` | `MAJOR.MINOR.PATCH` semantico |
| B.2.3 | Escribir `RELEASE.md` con proceso de release | Checklist de 5 pasos |
| B.2.4 | Configurar `setuptools-scm` para version desde git tag | `pyproject.toml` |

---

### B.3 Medir Tiempo de Pipeline y Tasa de Exito

**Tareas:**

| # | Tarea | Implementacion |
|---|-------|----------------|
| B.3.1 | Exportar metricas por stage en JSON estructurado | `base_stage.py:execute()` ya tiene `metrics` |
| B.3.2 | Anadir comando `--metrics json` al CLI | `compiler-bot/agentic` |
| B.3.3 | Calcular tasa de exito: `successes / total` en los ultimos N runs | `metrics_store.py` |
| B.3.4 | Dashboard minimal: script que parsea logs y muestra tabla | `scripts/pipeline_stats.sh` |

---



### C.1 Demo Ejecutable (Docker + Script)

**Tareas:**

| # | Tarea | Archivos |
|---|-------|----------|
| C.1.1 | Crear `Dockerfile` con Python 3.11 + dependencias | `Dockerfile` |
| C.1.2 | Crear `docker-compose.yml` con servicio `recpl` | `docker-compose.yml` |
| C.1.3 | Script `demo.sh` que ejecuta 3 prompts de ejemplo | `scripts/demo.sh` |
| C.1.4 | Verificar `docker run recpl "crea un modulo"` funciona sin flags | CI check |

**Ejemplo `Dockerfile`:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY compiler-bot/agentic_pipeline/ /app/agentic_pipeline/
COPY compiler-bot/agentic /app/agentic
RUN pip install -e /app/agentic_pipeline/
ENTRYPOINT ["python3", "/app/agentic"]
CMD ["--help"]
```

---

### C.2 README Renovado

**Tareas:**

| # | Tarea | Descripcion |
|---|-------|-------------|
| C.2.1 | Nuevo titulo: "RECPL — Natural Language to NestJS/Prisma Code" | Reemplazar header |
| C.2.2 | Seccion "Quick Start" con 3 comandos: instalar, ejecutar, ver resultado | `README.md` |
| C.2.3 | GIF/ASCII demo del pipeline en accion | `assets/demo.gif` o ASCII cast |
| C.2.4 | Badges: tests, python version, license | Shields.io |
| C.2.5 | Seccion "Roadmap" con proximos features | Basado en B.1 |

---

### C.3 Nombre Amigable para el Producto

**Propuesta:** Evaluar alternativas al nombre tecnico "RECPL Compiler Bot":

| Nombre | Pro | Contra |
|--------|-----|--------|
| RECPL (actual) | Unico, buscable | No dice que hace |
| **Codecribe** | Describe + Code, corto | No existe en espanol |
| **NestForge** | Nicho NestJS claro | Muy especifico |
| **LinguaCode** | Lenguaje → Codigo | Generico |
| ScaffoldBot | Dice exactamente que hace | Largo |

**Recomendacion:** Mantener RECPL como nombre tecnico, usar
"RECPL — Natural Language to NestJS/Prisma Scaffolding" en marketing.

---

## Track D: QA / Testing

### D.1 Performance Benchmarks

**Tareas:**

| # | Tarea | Herramienta |
|---|-------|-------------|
| D.1.1 | Anadir `pytest-benchmark` a dev dependencies | `pyproject.toml` |
| D.1.2 | Crear `tests/test_performance.py` con 5 benchmarks | `pytest-benchmark` |
| D.1.3 | Benchmark 1: pipeline completo con prompt corto | `test_pipeline_short` |
| D.1.4 | Benchmark 2: pipeline completo con prompt largo (500 palabras) | `test_pipeline_long` |
| D.1.5 | Benchmark 3: solo NLP (intent + NER + slots) | `test_nlp_only` |
| D.1.6 | Benchmark 4: solo parser (1000 tokens) | `test_parser_throughput` |
| D.1.7 | Benchmark 5: solo generators (10 targets) | `test_generator_throughput` |

**Criterio de aceptacion:** Pipeline completo < 2s en prompt tipico.

---

### D.2 Snapshot Testing para AST

**Tareas:**

| # | Tarea | Herramienta |
|---|-------|-------------|
| D.2.1 | Anadir `syrupy` a dev dependencies | `pyproject.toml` |
| D.2.2 | Crear `tests/test_ast_snapshots.py` | `syrupy` |
| D.2.3 | Snapshot 1: AST de "pagina login con formulario" | snapshot file |
| D.2.4 | Snapshot 2: AST de "entidad Usuario nombre:string" | snapshot file |
| D.2.5 | Snapshot 3: AST de "crea un modulo de pagos" (full pipeline) | snapshot file |

**Criterio de aceptacion:** Cambios en el AST rompen snapshots
explicitamente, no silenciosamente.

---

### D.3 Fix Debugger Test (tmp_path)

**Tareas:**

| # | Tarea | Archivo |
|---|-------|----------|
| D.3.1 | Reemplazar `Path("debug_output")` por `tmp_path` fixture | `tests/test_debugger.py:36-42` |
| D.3.2 | Verificar que no quedan archivos residuales tras tests | `tests/test_debugger.py` |

---

## Track E: Documentacion / Technical Writing

### E.1 Archivar Documentos Obsoletos

**Criterio de archive:** Un documento es candidato a archive si:
- Es una propuesta (PROP) cuya feature ya esta implementada
- Es un plan (PLAN) cuyo sprint ya se ejecuto y hay reporte (REP)
- Es una guia (GUIDE) de una version anterior (shell v1.0)
- No se ha modificado en los ultimos 30 commits

**Tareas:**

| # | Tarea | Comando |
|---|-------|---------|
| E.1.1 | Mover props implementadas a `docs/archive/` | `git mv docs/0{06,11,27,28,40,45,46}*.md docs/archive/` |
| E.1.2 | Mover planes ejecutados a `docs/archive/` | `git mv docs/0{16,31,47,68,88}*.md docs/archive/` |
| E.1.3 | Mover guias shell v1.0 a `docs/archive/` | `git mv docs/0{00,01,02,15,17,22,25,26,59,70}*.md docs/archive/` |
| E.1.4 | Actualizar INDEX.md eliminando referencias archivadas | `docs/INDEX.md` |

**Estimado:** ~40 documentos a archivar. Esfuerzo: 1 dia.
**Criterio:** `docs/` pasa de ~91 a ~50 archivos activos.

---

### E.2 Tutorial de Onboarding

**Tareas:**

| # | Tarea | Archivo |
|---|-------|----------|
| E.2.1 | Crear `docs/onboarding/README.md` con indice | `docs/onboarding/README.md` |
| E.2.2 | Tutorial 1: "Entender el pipeline" (5 min) | `docs/onboarding/01_pipeline.md` |
| E.2.3 | Tutorial 2: "Anadir un nuevo stage" (10 min) | `docs/onboarding/02_new_stage.md` |
| E.2.4 | Tutorial 3: "Escribir tests para un stage" (10 min) | `docs/onboarding/03_testing.md` |
| E.2.5 | Tutorial 4: "Depurar el pipeline con --debug" (5 min) | `docs/onboarding/04_debugging.md` |

---

### E.3 Documentacion de API Pydantic

**Tareas:**

| # | Tarea | Herramienta |
|---|-------|-------------|
| E.3.1 | Anadir `mkdocs` + `mkdocstrings` a dev dependencies | `pyproject.toml` |
| E.3.2 | Configurar `mkdocs.yml` para autogenerar docs de `agentic_pipeline/` | `mkdocs.yml` |
| E.3.3 | Documentar modelos: EnrichedInput, StageContext, StageOutput, Contracts | Docstrings existentes |
| E.3.4 | Desplegar a GitHub Pages via CI | `ci.yml` |

---

## Track F: DevOps / Seguridad

### F.1 GitHub Actions Workflow

**Archivo:** `.github/workflows/ci.yml`

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -e compiler-bot/agentic_pipeline/
      - run: ruff check compiler-bot/agentic_pipeline/
      - run: python -m pytest compiler-bot/agentic_pipeline/tests/ -q
```

**Tareas:**

| # | Tarea | Archivo |
|---|-------|----------|
| F.1.1 | Crear `.github/workflows/ci.yml` | workflow file |
| F.1.2 | Anadir job de lint (ruff) + test (pytest) | CI workflow |
| F.1.3 | Anadir job de docs build (mkdocs) opcional | CI workflow |
| F.1.4 | Verificar badge en README | `README.md` |

---

### F.2 Dockerfile

Ver C.1.1 para especificacion completa. El Dockerfile debe:
- Usar `python:3.11-slim`
- Instalar dependencias del pipeline
- Copiar `compiler-bot/agentic` como entrypoint
- Soportar `docker run recpl "crea modulo"` sin flags adicionales

---

### F.3 Pre-commit Hooks

**Archivo:** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.0
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: python -m pytest compiler-bot/agentic_pipeline/tests/ -q
        language: system
        pass_filenames: false
```

**Tareas:**

| # | Tarea | Archivo |
|---|-------|----------|
| F.3.1 | Crear `.pre-commit-config.yaml` | config file |
| F.3.2 | Anadir `pre-commit` a dev dependencies | `pyproject.toml` |
| F.3.3 | Ejecutar `pre-commit install` una vez | setup instruction |

---

## Ruta Critica y Dependencias

```
A.1 (Lark) ──→ A.4 (cleanup)
                │
A.2 (Enriched propagation) ──→ A.3 (generators) ←── B.1 (roadmap)
                                    │
                                    ↓
                               D.1 (benchmarks) ──→ D.2 (snapshots)
                                    │
                                    ↓
                               C.1 (Docker demo) ──→ C.2 (README)
                                    │
                                    ↓
                               F.1 (CI/CD) ←── F.3 (pre-commit)
                                    │
                                    ↓
                               E.3 (API docs) ──→ E.1 (archive)
                                    │
                                    ↓
                               E.2 (onboarding)
```

**Cuellos de botella:**
- A.1 (Lark) bloquea A.4. Si A.1 falla, A.4 se convierte en "eliminar
  codigo Lark muerto" en vez de "reactivar".
- A.3 (generators) es la tarea mas grande (3-4 dias) y la que
  desbloquea el valor real del producto.
- F.1 (CI/CD) es independiente y puede hacerse en cualquier momento.

---

## Resumen de Esfuerzo por Track

| Track | Tareas | Esfuerzo estimado | Dependencia externa |
|-------|--------|-------------------|---------------------|
| A. Desarrollo | 13 | 7-10 dias | — |
| B. Gerencia | 8 | 3-4 dias | A.3 parcial |
| C. Marketing | 7 | 2-3 dias | A.3, F.2 |
| D. QA | 7 | 2-3 dias | A.1, A.3 |
| E. Documentacion | 10 | 2-3 dias | — |
| F. DevOps | 6 | 1-2 dias | — |
| **Total** | **51** | **17-25 dias** | |

**Paralelizable:** Tracks B, E, F pueden ejecutarse en paralelo.
Tracks C y D dependen de A. Track A es secuencial interno.

---

## Criterios de Aceptacion Globales

- [ ] `ruff check .` = 0 errores
- [ ] `pytest tests/ -q` = 100% pasando (contador >= 516)
- [ ] `ci.sh` exitoso (syntax + lint + test)
- [ ] Pipeline genera scaffolding real: `modules/pagos/*.ts`
- [ ] `docker build -t recpl . && docker run recpl "crea modulo"` funciona
- [ ] GitHub Actions verde en PR
- [ ] README actualizado con quick start y badges
- [ ] `docs/` reducido de 91 a ~50 archivos activos
