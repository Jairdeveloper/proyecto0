---
id: 084
area: dev
type: plan
module: project
version: 1.0
status: DRAFT
tags:
  - execution-plan
  - technical-debt
  - security
  - sustainability
  - metrics-store
  - llm-caching
  - ci-cd
summary: >-
  Plan de ejecución detallado para las tareas ACEPTADAS del reporte de
  decisiones 083. Cada tarea incluye objetivo, archivos modificados,
  cambios realizados, tests y resultado.
keywords:
  - execution-plan
  - path-traversal
  - metrics-prune
  - llm-cache
  - changelog
  - ci
changelog:
  - version: '1.0'
    date: 2026-06-14
    description: Plan de ejecución de deuda técnica
---

# 084_PLAN_DEV_EXECUTION_TECH_DEBT_1_0_DRAFT

## Contexto

Ejecución de las tareas ACEPTADAS y por COMPLETAR identificadas en el
reporte de decisiones `083_REP_DEV_PROJECT0_DECISION_REPORT_1_0_DRAFT.md`,
secciones 4.3, 4.4, 6 (R2, R4, R5), 7.3 y 8.1.

**Estado final: 471 tests (PASS), ruff 0 errores, commit `5e4205b`.**

---

## Tarea 1: R5 — Límite de 1000 entradas en MetricsStore

### Objetivo
Evitar crecimiento infinito del almacenamiento de métricas en disco.

### Archivos modificados
- `compiler-bot/agentic_pipeline/metrics_store.py`

### Cambios realizados
1. Añadida constante `MAX_ENTRIES_PER_STAGE = 1000`
2. En `record()` vía SQLite: después de INSERT, ejecuta DELETE de registros
   viejos cuando exceden el límite (OFFSET query)
3. En `record()` vía JSON fallback: trunca `entries` a los últimos N antes
   de escribir

### Criterio de éxito
MetricsStore no retiene más de 1000 entradas por stage en ningún momento.

### Código clave
```python
MAX_ENTRIES_PER_STAGE = 1000

# SQLite path
conn.execute(
    "DELETE FROM stage_metrics WHERE id IN ("
    "SELECT id FROM stage_metrics WHERE stage = ? "
    "ORDER BY id DESC LIMIT -1 OFFSET ?)",
    (stage, MAX_ENTRIES_PER_STAGE),
)

# JSON fallback path
if len(entries) > MAX_ENTRIES_PER_STAGE:
    entries = entries[-MAX_ENTRIES_PER_STAGE:]
```

---

## Tarea 2: #12/R4 — Path Traversal en Synthesis

### Objetivo
Prevenir que rutas con `../` proporcionadas por el comando del plan
puedan escribir archivos fuera del directorio de salida.

### Archivos modificados
- `compiler-bot/agentic_pipeline/nodes/synthesis.py`
- `compiler-bot/agentic_pipeline/tests/test_synthesis.py`

### Cambios realizados
1. Añadido método `_sanitize_path()` que rechaza paths con `..` en sus
   componentes (via `Path.parts`)
2. En `act()`, reemplazo de `Path(path_str)` directo por:
   ```python
   safe_path = self._sanitize_path(path_str)
   if safe_path is None:
       errors.append(f"Path traversal blocked: '{path_str}'")
       continue
   ```
3. Tests añadidos:
   - `test_sanitize_path_rejects_traversal`: `../etc` → None, `safe/path` → Path
   - `test_act_rejects_path_traversal`: comando con `../../../tmp/evil`
     → error sin escribir archivo

### Criterio de éxito
Cualquier path que contenga `..` es rechazado antes de crear directorios.

---

## Tarea 3: R2 — Cache de LLM en RequirementDecomposer

### Objetivo
Evitar recomputación del RequirementGraph cuando el mismo texto se procesa
múltiples veces. Reduce dependencia de LLM y mejora tiempo de respuesta.

### Archivos modificados
- `compiler-bot/agentic_pipeline/nodes/requirement_decomposer.py`

### Cambios realizados
1. Import de `ASTCache` desde `.ast_cache`
2. Inicialización de `self._cache = ASTCache(maxsize=64)` en `__init__`
3. Refactor de `act()`: delega la construcción del grafo a `_build_graph()`
   y cachea el resultado:
   ```python
   def act(self, plan: ActionPlan) -> StageOutput:
       graph = self._cache.get_or_compute(
           self._raw_text,
           lambda: self._build_graph(),
       )
   ```
4. Extracción de `_build_graph()` como método separado con la lógica
   original (domain classifier → entity extractor → features → stories)

### Criterio de éxito
Misma entrada → misma salida. Segunda llamada no ejecuta LLM tools.

---

## Tarea 4: 7.3 — Actualización de CHANGELOG.md

### Objetivo
Reflejar el cambio de versión a 2.0.0 y documentar todos los cambios
de los Sprints 9-13 más las correcciones de deuda técnica.

### Archivos modificados
- `CHANGELOG.md`

### Cambios realizados
1. Nueva entrada `[2.0.0] — 2026-06-14` antes de `[1.8.0]`
2. Secciones Added (Python v2.0, CLI, generadores, StateGraph, CI, tests),
   Changed (Shell congelado, C Core archivado, docs archivados),
   Fixed (path traversal, metrics prune, LLM cache, feedback loop)

---

## Tarea 5: 8.1 — Acciones Inmediatas (Verificación)

### Estado de las 6 acciones del sprint

| # | Acción | Archivos | Estado |
|---|--------|----------|--------|
| 1 | Archivar C Core en `contrib/` | `core/` → `contrib/c-core-archive/` | ✅ COMPLETADO |
| 2 | Crear `VERSION` file | `VERSION` → `2.0.0` | ✅ COMPLETADO |
| 3 | Crear `ci.sh` | `ci.sh` con ruff + pytest | ✅ COMPLETADO |
| 4 | Tests de integración | `tests/test_integration.py` (6 escenarios) | ✅ COMPLETADO |
| 5 | Archivar reportes de sprint | `docs/archive/` (12 docs) | ✅ COMPLETADO |
| 6 | Actualizar `AGENTS.md` | Stack decisión + tabla Python | ✅ COMPLETADO |

---

## Resultados Finales

| Métrica | Valor |
|---------|-------|
| Tests | **471 passed** (+8 desde 463) |
| Ruff | 0 errores |
| CI | syntax → ruff → pytest → VERSION, all green |
| CHANGELOG | v2.0.0 documentado |
| Path traversal | Bloqueado en synthesis stage |
| MetricsStore | Límite de 1000 entradas por stage |
| LLM cache | ASTCache (maxsize=64) en RequirementDecomposer |
| Commit | `HEAD` on `main` |
