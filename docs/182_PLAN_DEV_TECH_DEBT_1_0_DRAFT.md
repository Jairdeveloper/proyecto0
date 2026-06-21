---
id: 182
area: dev
type: plan
module: tech_debt
version: 1.0
status: DRAFT
tags:
  - plan
  - tech-debt
  - refactor
  - security
  - tests
  - documentation
  - type-hints
  - dead-code
summary: "Plan de ejecucion para eliminar la deuda tecnica identificada en el analisis del 2026-06-21. Cubre 8 fases: seguridad, versionado, codigo muerto Python y Shell, type hints, tests, documentacion y refactors estructurales."
keywords:
  - tech-debt
  - execution-plan
  - security
  - dead-code
  - type-annotations
  - testing
  - documentation
changelog:
  - version: 1.0
    date: 2026-06-21
    author: system
---

# Plan de Ejecucion — Eliminacion de Deuda Tecnica

## Contexto

Analisis de deuda tecnica realizado el 2026-06-21 sobre el proyecto Proyecto0
(compiler-bot/agentic_pipeline v2.8.4 + pdca_sdlc v0.1.0 + shell v1.0 legacy).

Se identificaron ~23 items distribuidos en: seguridad (critico), versionado,
codigo muerto Python y Shell, type hints faltantes, tests bloqueados,
documentacion desactualizada y refactors estructurales.

Este plan organiza la remediacion en 8 fases secuenciales con dependencias
explicitas.

---

## Fase 1 — Seguridad (Critico, 1 sesion)

### 1.1 Revocar API key y excluir `.env` de git

**Problema:** `.env` con `OPENAI_API_KEY` activa esta trackeado en git.
No figura en `.gitignore`.

**Accion:**
1. Agregar `.env` a `.gitignore`
2. Revocar la API key actual en https://platform.openai.com/api-keys
3. Ejecutar `git rm --cached .env`
4. Commit: "fix: revoke exposed API key, add .env to gitignore"

**Archivos:** `.gitignore`
**Verificacion:** `git ls-files .env` retorna vacio; `git diff --cached` no
muestra `.env`.

### 1.2 Sourcear `tool_respond.sh` en `agent.sh`

**Problema:** `agent.sh` llama a `tool_respond` en lineas 212, 215, 218, 221,
224 pero nunca hace `. "$SCRIPT_DIR/tools/tool_respond.sh"`. Las respuestas de
saludo/agradecimiento lanzan "command not found".

**Accion:** Agregar `. "$SCRIPT_DIR/tools/tool_respond.sh"` en el bloque de
sourcing de tools (~linea 208), antes del primer uso de `tool_respond`.

**Archivos:** `compiler-bot/agent-robot/agent.sh`
**Verificacion:** Ejecutar `bash -n agent.sh && shellcheck agent.sh`

### 1.3 Agregar `set -o pipefail` a todos los shells

**Problema:** Ningun script shell en `compiler-bot/` usa `set -o pipefail`.
Errores en pipelines se silencian (e.g. parser.sh falla pero echo tiene exito).

**Accion:** Agregar `set -o pipefail` inmediatamente despues del shebang en
todos los scripts que usan pipes:
- `compiler-bot/recpl.sh`
- `compiler-bot/pipeline_debugger.sh`
- `compiler-bot/frontend/*.sh` (5 archivos)
- `compiler-bot/backend/*.sh` (3 archivos)
- `compiler-bot/middleend/*.sh` (2 archivos)
- `compiler-bot/agent-robot/*.sh` (8 archivos)
- `compiler-bot/agent-robot/tools/*.sh` (7 archivos)
- `compiler-bot/agent-robot/providers/*.sh` (2 archivos)

**Archivos:** ~30 archivos shell
**Verificacion:** `bash -n` en cada archivo modificado

---

## Fase 2 — Versionado y Config (1 sesion)

### 2.1 Alinear versiones

**Problema:** `CHANGELOG.md` dice 2.8.5 pero `VERSION` y
`agentic_pipeline/pyproject.toml` dicen 2.8.4.

**Accion:** Actualizar:
- `VERSION` → `2.8.5`
- `agentic_pipeline/pyproject.toml` → `version = "2.8.5"`

**Archivos:** `VERSION`, `compiler-bot/agentic_pipeline/pyproject.toml`
**Verificacion:** `bash scripts/check_version_alignment.sh`

### 2.2 Incluir `pdca_sdlc` en version check

**Problema:** `check_version_alignment.sh` solo verifica VERSION,
agentic_pipeline/pyproject.toml y CHANGELOG.md. pdca_sdlc (v0.1.0) nunca se
verifica.

**Accion:** Agregar logica para verificar tambien
`compiler-bot/pdca_sdlc/pyproject.toml` contra una variable `PDCA_VERSION`
en el script.

**Archivos:** `scripts/check_version_alignment.sh`
**Verificacion:** `bash scripts/check_version_alignment.sh` reporta OK para
ambos paquetes.

### 2.3 Completar `.gitignore`

**Problema:** Faltan patterns estandar: `.DS_Store`, `*.swp`, `*.swo`,
`.coverage`, `htmlcov/`.

**Accion:** Agregar al final de `.gitignore`.

**Archivos:** `.gitignore`
**Verificacion:** `git status --ignores` muestra los archivos ignorados.

---

## Fase 3 — Codigo Muerto Python (1 sesion)

### 3.1 Archivar modulos no utilizados

**Problema:** 6 modulos Python nunca son importados en produccion. Solo
existen para que sus tests sigan funcionando.

**Accion:** En cada archivo, reemplazar el contenido con un stub que lance
`ImportError("DEPRECATED")` y mover los originales a un directorio de
archivo o eliminarlos. Los tests que los importan deben actualizarse para
no depender de codigo muerto.

**Archivos:**
- `compiler-bot/agentic_pipeline/nodes/requirement_decomposer.py`
- `compiler-bot/agentic_pipeline/nodes/plan_executor.py`
- `compiler-bot/agentic_pipeline/nodes/evaluation_visitor.py`
- `compiler-bot/agentic_pipeline/nodes/validation_visitor.py`
- `compiler-bot/agentic_pipeline/optimizer.py`
- `compiler-bot/agentic_pipeline/prompt_chain/commands.py`

**Verificacion:** `ruff check . --select=F401` no muestra imports huérfanos;
tests que dependian de estos modulos pasan con las importaciones actualizadas.

### 3.2 Eliminar shims de backward-compat

**Problema:** `planner.py` (17 lineas), `synthesis.py` (5 lineas) e
`intent_stage.py` (3 lineas) solo re-exportan de otros modulos.
Mantenerlos es ruido y oculta las dependencias reales.

**Accion:**
1. `planner.py` → tests que importan `HybridPlanner` desde aqui deben
   importar de `reasoning_engine.py`. Luego eliminar `planner.py`.
2. `synthesis.py` → tests que importan `SynthesisOrchestrator` desde aqui
   deben importar `ActionExecutor` de `action_executor.py`. Luego eliminar
   `synthesis.py`.
3. `intent_stage.py` → `orchestrator.py` (linea 307) hace lazy import de
   `IntentStage`. Cambiar a importar `PerceptionUnit` de
   `perception_unit.py`. Luego eliminar `intent_stage.py`.
4. `plan_executor.py` tambien importa desde `planner.py` — ya cubierto en
   3.1.

**Archivos:**
- `compiler-bot/agentic_pipeline/nodes/planner.py`
- `compiler-bot/agentic_pipeline/nodes/synthesis.py`
- `compiler-bot/agentic_pipeline/nodes/intent_stage.py`
- `compiler-bot/agentic_pipeline/orchestrator.py`
- `tests/test_heuristic_planner.py`
- `tests/test_plan_executor.py`
- `tests/test_synthesis.py`

**Verificacion:** `pytest tests/ -x --co` reporta 0 errores de importacion.

---

## Fase 4 — Codigo Muerto Shell (1 sesion)

### 4.1 Eliminar funciones nunca llamadas

**Problema:** 7 funciones definidas en shell que nunca son invocadas desde
ningun otro script.

**Accion:** Eliminar las definiciones de funcion.

| Funcion | Archivo | Lineas |
|---------|---------|--------|
| `bridge_debug()` | `agent-robot/bridge.sh` | 87-140 |
| `bridge_state()` | `agent-robot/bridge.sh` | 142-152 |
| `apifreellm_call()` | `agent-robot/providers/apifreellm.sh` | 21-44 |
| `apifreellm_available()` | `agent-robot/providers/apifreellm.sh` | 45-53 |
| `memory_list_sessions()` | `agent-robot/memory.sh` | 129-140 |
| `memory_set_session()` | `agent-robot/memory.sh` | 141-148 |
| `memory_export()` | `agent-robot/memory.sh` | 149-158 |

**Archivos:** `bridge.sh`, `apifreellm.sh`, `memory.sh`
**Verificacion:** `grep -rn 'bridge_debug\|bridge_state\|\
apifreellm_call\|apifreellm_available\|memory_list_sessions\|\
memory_set_session\|memory_export' compiler-bot/` solo muestra las
definiciones restantes.

### 4.2 Archivar `llm_ir_mapper.sh`

**Problema:** `middleend/llm_ir_mapper.sh` (81 lineas) nunca es sourceado
ni llamado. Su funcionalidad fue reemplazada por `frontend/llm_classifier.sh`.

**Accion:** Eliminar el archivo. No migrar — es codigo legacy congelado.

**Archivos:** `compiler-bot/middleend/llm_ir_mapper.sh`
**Verificacion:** `bash -n compiler-bot/middleend/*.sh` no referencia al archivo.

---

## Fase 5 — Linting y Type Hints (2 sesiones)

### 5.1 Agregar `ANN` a reglas de ruff

**Problema:** Ruff no tiene `ANN` (annotations) en reglas seleccionadas. Esto
permite que funciones sin type hints pasen CI sin advertencias.

**Accion:** Agregar `"ANN"` a `[tool.ruff.lint.select]` en ambos
pyproject.toml. Opcional: agregar `"B"` (bugbear), `"SIM"` (simplify).

**Nota:** Agregar `ANN` generara ~151 errores nuevos. Se solucionaran en
5.2 gradualmente. Considerar usar `[tool.ruff.lint.per-file-ignores]`
para tests.

**Archivos:**
- `compiler-bot/agentic_pipeline/pyproject.toml`
- `compiler-bot/pdca_sdlc/pyproject.toml`

**Verificacion:** `ruff check . --select=ANN --statistics` reporta cantidad
de errores (esperado para hacer seguimiento).

### 5.2 Fix type hints — top 5 archivos

**Problema:** 151/748 funciones (20%) sin return type hint. Peores ofensores:

| Archivo | Missing/Total | % |
|---------|--------------|---|
| `nodes/sub_dfa.py` | 8/10 | 80% |
| `generators/ui_component_builder.py` | 7/9 | 78% |
| `prompt_chain/llm_backend.py` | 15/21 | 71% |
| `prompt_chain/commands.py` | 6/12 | 50% |
| `nodes/ast_nodes.py` | 5/15 | 33% |

**Accion:** Agregar return type hints a todas las funciones en estos 5
archivos. Priorizar funciones publicas y metodos de clase sobre helpers
internos.

**Archivos:** 5 archivos listados arriba
**Verificacion:** `ruff check --select=ANN` sobre cada archivo reporta 0.

### 5.3 Reemplazar `create_subprocess_shell`

**Problema:** `run_command.py:20` usa `asyncio.create_subprocess_shell()`
que es funcionalmente equivalente a `subprocess.run(..., shell=True)`.
Viola la convencion Python.

**Accion:** Reemplazar con `asyncio.create_subprocess_exec()` y pasar
el comando como lista de argumentos. Usar `shlex.split()` para parsear
el string de entrada.

**Archivos:** `compiler-bot/agent-robot/tools/tool_run_command.py`
**Verificacion:** `ruff check . --select=S605` (bandit shell=True) reporta 0.

---

## Fase 6 — Tests (2 sesiones)

### 6.1 Fix import en `test_performance.py`

**Problema:** Linea 14 importa `HybridPlanner` desde `nodes.planner`, pero
`planner.py` solo exporta `HeuristicPlanner`, `ReasoningEngine`, `Task`,
`TaskGraph`, `TaskState`. `HybridPlanner` no existe como clase exportada.

**Accion:** Verificar si `HybridPlanner` existe en `reasoning_engine.py` o si
es un nombre obsoleto. Actualizar el import al simbolo correcto.

**Archivos:** `tests/test_performance.py`
**Verificacion:** `pytest tests/test_performance.py -x` pasa.

### 6.2 Tests unitarios para modulos sin cobertura

**Problema:** ~15 modulos no tienen tests dedicados. Los mas criticos por
riesgo de regresion:

| Modulo | Riesgo | Prioridad |
|--------|--------|-----------|
| `nodes/action_executor.py` | Alto (orquestacion) | Alta |
| `nodes/ir_serializer.py` | Alto (formato salida) | Alta |
| `nodes/ir_generator.py` | Alto (generacion IR) | Alta |
| `generators/ui_component_builder.py` | Medio (UI) | Media |
| `security/bandit_scanner.py` | Medio (seguridad) | Media |
| `prompt_chain/fallbacks.py` | Bajo (error handling) | Baja |

**Accion:** Escribir test suite para cada modulo priorizado. Seguir el
patron de los tests existentes (pytest, fixtures en conftest.py si aplica).

**Archivos:** `tests/test_action_executor.py`, `tests/test_ir_serializer.py`,
`tests/test_ir_generator.py`, etc.
**Verificacion:** `pytest tests/ -x --co` incluye los nuevos tests y pasan.

### 6.3 Arreglar contador PASS/FAIL en `test_agent.sh`

**Problema:** `test_agent.sh` inicializa `PASS=0` y `FAIL=0` pero nunca
incrementa `PASS`. Solo incrementa `FAIL` cuando un test falla. La salida
final siempre muestra `PASS=0`.

**Accion:** Agregar `PASS=$((PASS + 1))` al final de cada bloque de test
que termina con `exit 0`. Alternativamente, cambiar a un sistema basado en
`tap` (Test Anything Protocol) con `echo "ok # test_name"`.

**Archivos:** `compiler-bot/tests/test_agent.sh`
**Verificacion:** Ejecutar `bash compiler-bot/tests/test_agent.sh` y
verificar que `PASS` refleja la cantidad real de tests exitosos.

---

## Fase 7 — Documentacion (2 sesiones)

### 7.1 Reconstruir INDEX.md

**Problema:** `INDEX.md` afirma "54 documentos activos". El proyecto tiene
~145 docs activos (mas 46 archivados). Los documentos NNN 097-181 no
aparecen en las tablas.

**Accion:** Reconstruir las tablas del indice para incluir todos los
documentos hasta NNN 182. Actualizar el conteo de documentos activos.
Corregir secciones de area para reflejar la distribucion real.

**Archivos:** `docs/INDEX.md`
**Verificacion:** El indice lista todos los archivos NNN 001-182.

### 7.2 Resolver duplicacion `index.md` vs `INDEX.md`

**Problema:** Existen `docs/index.md` (pagina MkDocs con diagrama de
pipeline) y `docs/INDEX.md` (indice maestro de documentacion). Ambos
coexisten y pueden confundir.

**Accion:** Evaluar dos opciones:
- Opcion A: Renombrar `INDEX.md` a `MASTER_INDEX.md` y actualizar
  referencias.
- Opcion B: Fusionar el contenido de `INDEX.md` dentro de `index.md` y
  eliminar `INDEX.md`.

**Archivos:** `docs/index.md`, `docs/INDEX.md`
**Verificacion:** MkDocs build no reporta archivos duplicados.

### 7.3 Resolver IDs duplicados en frontmatter

**Problema:** 22 archivos tienen IDs duplicados o ausentes:

| ID | Archivos | Accion |
|----|----------|--------|
| 094 | `094_REP_DEV_TRACK_AB` y `094_REP_DEV_TRACK_ABC` | Reasignar el obsoleto (v1.0) a `094a` |
| 139 | `139.0_REP_DEV_PHASE0` y `139.1_REP_DEV_FASE1` | Reasignar a `139.0` y `139.1` en frontmatter |
| 018 | `008_PRM_BUILD_AGENT` tiene `id: 018` (typo) | Cambiar a `id: 008` |
| P03 | `122_PLAN_DEV_PATTERNS_REFACTOR` y `149_PLAN_DEV_REMAINING_ARCHITECTURAL_ITEMS` | Reasignar el mas reciente |
| P04 | `123_PLAN_DEV_PATTERNS_ACTION` y `157_PLAN_DEV_PDCA_SDLC_IMPLEMENTATION` | Reasignar el mas reciente |
| P05 | `126_PLAN_DEV_PIPELINE_FIXES` y `158_PLAN_DEV_PDCA_SDLC_EXECUTION` | Reasignar el mas reciente |
| — | `082`, `127-135` (10 archivos) sin `id:` en frontmatter | Agregar `id:` segun su NNN |

**Archivos:** ~22 archivos .md
**Verificacion:** `python3 -c "import yaml; ..."` sobre todos los frontmatter
reporta 0 IDs duplicados.

### 7.4 Agregar `id:` a archivos que no tienen

**Problema:** 10 archivos (082, 127, 128, 129, 130, 131, 132, 133, 134, 135)
no tienen campo `id:` en su frontmatter.

**Accion:** Agregar `id:` acorde a su numero de archivo:
- `082_REP_DEV_PROJECT0_COMPREHENSIVE_ANALYSIS` → `id: 082`
- `127_PROP_DEV_PIPELINE_HTTP_WRAPPER` → `id: 127`
- ... etc.

**Archivos:** docs/082, 127-135
**Verificacion:** `grep -r '^id:' docs/*.md | wc -l` = cantidad de archivos
con frontmatter.

---

## Fase 8 — Refactors Estructurales (Backlog, opcional)

### 8.1 Evaluar reduccion de dependencias NLP

**Problema:** `spacy` (~300MB) + `nltk` (~50MB) + `sentence-transformers`
(~1.5GB con modelos) son ~2GB de dependencias. Si el pipeline LLM es el
path primario, estas son redundantes.

**Accion:** Analizar uso actual de cada libreria en:
- `nodes/perception_unit.py`
- `nodes/spacy_processor.py`
- Verificar si `nltk` se usa directamente o solo como dependencia
  transitiva.
- Mover las no esenciales a `[project.optional-dependencies]` NLP.

**Archivos:** `pyproject.toml`
**Esfuerzo:** 1 sesion

### 8.2 Migrar temp files a directorio controlado

**Problema:** 15+ archivos shell usan `/tmp/recpl_*` con nombres basados en
PID. Vulnerable a symlink attacks. Sin cleanup en SIGTERM/SIGINT.

**Accion:** Unificar todos los temp files bajo `$RECPL_STATE_DIR/tmp/` con
`trap` que cubra EXIT, SIGTERM, SIGINT.

**Archivos:** `recpl.sh`, `frontend/*.sh`, `backend/*.sh`, `middleend/*.sh`
**Esfuerzo:** 2 sesiones

### 8.3 Reemplazar `2>/dev/null` por manejo explicito

**Problema:** 20+ ocurrencias de errores silenciados en lugar de manejados.
Especialmente critico en `frontend/router.sh` lineas 80-102.

**Accion:** Cada etapa del pipeline en router.sh debe verificar el codigo
de salida y emitir un error diagnostico antes de fallar.

**Archivos:** `frontend/router.sh`, `agent-robot/bridge.sh`
**Esfuerzo:** 1 sesion

### 8.4 Reducir boilerplate en IR nodes

**Problema:** 5 clases IRNode (`IRConfig`, `IRComponent`, `IREntity`,
`IRAPI`, `IRInfra`) comparten firma identica de 4 metodos. Pattern
Template Method con ~20 declaraciones repetidas.

**Accion:** Extraer clase base `IRNodeBase` con implementacion por defecto
de `to_code()`, `validate()`, `dependencies()`. Las subclases solo
sobrescriben lo que varia.

**Archivos:** `nodes/ir_nodes.py`
**Esfuerzo:** 1 sesion

### 8.5 Solventar entorno de CI

**Problema:** 4 tests bloqueados por:
- `_sqlite3` module missing (Python compilado sin sqlite3)
- `libcudart.so.13` corrupto (falla torch, que falla transformers, que
  falla langchain-core)
- `HybridPlanner` import error

**Accion:** (1) Reinstalar Python con sqlite3 support. (2) Reinstalar CUDA
toolkit o torch sin CUDA. (3) Fix import (cubierto en 6.1).

**Archivos:** Entorno/CI
**Esfuerzo:** Variable

---

## Resumen de Fases

| Fase | Descripcion | Sesiones | Depende de |
|------|-------------|----------|------------|
| 1 | Seguridad | 1 | — |
| 2 | Versionado y Config | 1 | — |
| 3 | Codigo muerto Python | 1 | — |
| 4 | Codigo muerto Shell | 1 | — |
| 5 | Linting y Type Hints | 2 | 3 (shims eliminados) |
| 6 | Tests | 2 | 3, 5 (imports saneados) |
| 7 | Documentacion | 2 | 2 (version alineada) |
| 8 | Refactors backlog | 5+ | 3, 4, 5, 6 |
| **Total** | | **~10-12** | |

## Criterios de Exito

1. `ruff check .` devuelve 0 errores en ambos paquetes
2. `ruff check . --select=ANN` devuelve 0 en los 5 archivos target
3. `pytest tests/ -x` pasa en agentic_pipeline y pdca_sdlc
4. `bash compiler-bot/tests/run_tests.sh` = 72 PASS
5. `bash compiler-bot/tests/test_agent.sh` muestra PASS > 0
6. `git ls-files .env` vacio
7. `scripts/check_version_alignment.sh` reporta OK
8. INDEX.md lista NNN 001-182
9. Cero IDs duplicados en frontmatter YAML
10. `shellcheck` 0 errores en scripts modificados
