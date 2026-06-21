---
id: "P03"
area: dev
type: plan
module: recpl_arch_remaining
version: "1.0"
status: IMPLEMENTED
tags: ["plan", "implementation", "refactor", "thread-safety", "event-bus", "dead-code"]
summary: "Plan de ejecucion para los items arquitectonicos pendientes del plan 121: P4 (thread-safe StageSubject), P5 (unificacion EventBus), y apertura de decision para P2 (RequirementDecomposer dead code)"
changelog:
  - version: "1.0"
    date: "2026-06-19"
    author: "Sistema"
    description: "Version inicial — plan para items pendientes tras verificacion de plan 121"
---

# Plan de Ejecucion — Items Arquitectonicos Pendientes (Planes 121/129)

> **Documento base:** `docs/121_PLAN_DEV_ARCHITECTURAL_REFACTOR_1_0_DRAFT.md`  
> **Verificacion:** `docs/149_PLAN_DEV_REMAINING_ARCHITECTURAL_ITEMS_1_0_DRAFT.md` (este documento)  
> **Objetivo:** Implementar el 100% de los items P4, P5, y resolver decision sobre P2  
> **Esfuerzo total estimado:** ~17h efectivas + decision P2  
> **Dependencias:** M0 completado (ruff, pytest, imports, ParserGLR rename)

---

## Estado Actual Verificado

| ID | Item | Prioridad | Estado | Esfuerzo restante |
|----|------|-----------|--------|-------------------|
| P4 | Thread-safe `StageSubject` | Media | ❌ No implementado | 4h |
| P5 | Unificar `EventBus` + `StageSubject` | Media | ⚠️ Parcial (bridge existe, P5.2 OK) | 6h |
| P2 | RequirementDecomposer dead code | Media | ❌ No implementado (pendiente decision) | 1.5h o — |

---

## P4 — Thread-safe StageSubject (4h)

**Problema:** `StageSubject._observers` es una `list` mutable sin `threading.Lock`. Si dos hilos llaman `attach()`/`detach()` simultaneamente mientras otro itera en `notify()`, se produce `RuntimeError: list changed during iteration`.

### Tareas

| ID | Tarea | Archivos | Esfuerzo | Depende De | Criterio de Aceptacion |
|----|-------|----------|----------|------------|------------------------|
| P4.1 | Agregar `threading.Lock` a `StageSubject._observers` con copy-on-write en `notify()` | `prompt_chain/observer_base.py` (MODIFICAR) | 1.5h | — | `notify()` itera sobre copia congelada; `attach()`/`detach()` usan lock |
| P4.2 | Verificar que `PipelineStage.subject` (class var en `base_stage.py`) es compatible con lock interno | `base_stage.py` (VERIFICAR, sin cambios) | 0.5h | P4.1 | Race condition test pasa: 10 threads attach/detach/notify simultaneos |
| P4.3 | Test de concurrencia: 10 hilos llamando `attach`, `detach`, `notify` simultaneamente | `tests/test_observer_pattern.py` (EXTENDER) | 2h | P4.1 | Test no falla ni produce `RuntimeError: list changed during iteration` |

**Total P4:** 4h

### Ruta de implementacion sugerida P4.1

```python
# En StageSubject.__init__:
self._lock = threading.Lock()

# attach/detach usan lock:
def attach(self, observer: StageObserver) -> None:
    with self._lock:
        self._observers.append(observer)

def detach(self, observer: StageObserver) -> None:
    with self._lock:
        self._observers.remove(observer)

# notify itera sobre copia congelada:
def notify(self, event: StageEvent) -> None:
    with self._lock:
        snapshot = list(self._observers)
    for observer in snapshot:
        observer.on_event(event)
    self._bus.publish(event.stage, event)
```

### Riesgo de implementacion

- `PipelineStage.subject` es class var, compartida por todas las subclases. Si el lock es instancia, no protege acceso entre subclases. Solucion: lock tambien como class var o pasar a instancia.

### Verificacion

```bash
pytest tests/test_observer_pattern.py -v -k "concurrent"
# Output: test_concurrent_attach_detach_notify PASSED
```

---

## P5 — Unificar EventBus + StageSubject(6h) 

**Problema:** `StageSubject` (prompt_chain/) y `EventBus` (agents/) son dos implementaciones de pub/sub con la misma funcion. Actualmente `StageSubject` ya importa `EventBus` y publica eventos en el (P5.2 completado), pero `StageObserver` y el sistema local de observers siguen existiendo como mecanismo paralelo.

### Estado actual

- ✅ P5.2: `StageSubject.notify()` ya llama a `self._bus.publish(event.stage, event)` — bridge existe
- ❌ P5.1: Interfaces no unificadas — `StageSubject.attach/detach` y `EventBus.subscribe/unsubscribe` coexisten sin relacion
- ❌ P5.3: `StageObserver` no eliminado — 6 observers lo implementan
- ❌ P5.4: Imports no actualizados — 8 archivos importan desde `prompt_chain.observer_base`

### Tareas

| ID | Tarea | Archivos | Esfuerzo | Depende De | Criterio de Aceptacion |
|----|-------|----------|----------|------------|------------------------|
| P5.1 | Unificar interfaces: `EventBus.subscribe(topic, callback)` → wrapper que coincida con `attach(observer)`, o `StageSubject` como fachada que delega en `EventBus` | `prompt_chain/observer_base.py`, `agents/event_bus.py` (MODIFICAR) | 3h | — | Todo `attach()` es traducible a `subscribe()`; todo `detach()` a `unsubscribe()` |
| P5.3 | Eliminar `StageObserver` y migrar todos los observers concretos a usar `StageEvent` directamente via `EventBus.subscribe()` | `observers/*.py`, `security/bandit_scanner.py` (MODIFICAR) | 2h | P5.1 | `git grep "StageObserver" -- "*.py"` = 0 (excepto compatibilidad) |
| P5.4 | Actualizar imports en todos los archivos: `base_stage.py`, `handler_base.py`, `prompt_chain/orchestrator.py`, `prompt_chain/__init__.py`, `tests/test_observer_pattern.py` | 5 archivos (MODIFICAR) | 1h | P5.3 | Todos los imports apuntan a `EventBus` o nuevo modulo unificado |

**Total P5:** 6h (plan 121 estimo 9h, pero P5.2 ya esta hecho)

### Estrategia recomendada

Hacer que `StageSubject` sea una fachada delgada que:

1. Mantiene API `attach(observer)/detach(observer)/notify(event)` por compatibilidad
2. Internamente, `attach()` llama a `EventBus.subscribe(observer.stage, observer.on_event)`
3. `notify()` solo publica en `EventBus` (ya no itera observers locales)
4. `StageObserver` se depreca y se elimina progresivamente

Esto minimiza cambios en los 6 observers concretos mientras se unifica el bus.

### Archivos que requieren cambios (imports)

```
compiler-bot/agentic_pipeline/base_stage.py                  — StageSubject import
compiler-bot/agentic_pipeline/prompt_chain/handler_base.py   — StageSubject import
compiler-bot/agentic_pipeline/prompt_chain/orchestrator.py   — StageSubject import
compiler-bot/agentic_pipeline/prompt_chain/__init__.py        — StageObserver/StageSubject exports
compiler-bot/agentic_pipeline/observers/audit_observer.py     — StageObserver import
compiler-bot/agentic_pipeline/observers/debug_observer.py     — StageObserver import (docstring)
compiler-bot/agentic_pipeline/observers/metrics_observer.py   — StageObserver import (docstring)
compiler-bot/agentic_pipeline/observers/dashboard_observer.py — StageObserver import (docstring)
compiler-bot/agentic_pipeline/observers/prompt_optimizer_observer.py — StageObserver (docstring)
compiler-bot/agentic_pipeline/security/bandit_scanner.py      — StageObserver import
compiler-bot/agentic_pipeline/tests/test_observer_pattern.py  — StageSubject/StageObserver imports
```

### Verificacion

```bash
git grep -l "StageObserver" -- "*.py" | grep -v __pycache__
# Output: 0 archivos (o solo alias de compatibilidad)

git grep -l "StageSubject" -- "*.py" | grep -v __pycache__
# Output: solo observer_base.py (unificado) y base_stage.py (class var)

pytest tests/test_observer_pattern.py -v  # todos pasan
pytest tests/ -v --cov  # sin regresiones
```

---

## P2 — RequirementDecomposer Dead Code (pendiente decision)

**Problema:** `nodes/requirement_decomposer.py` existe, `Stage.REQUIREMENT_DECOMPOSER` esta en el enum, pero no esta en `NODE_MAP` ni se usa en ningun flujo del pipeline.

### Estado actual

- `nodes/requirement_decomposer.py` — archivo existente (317 lineas, con `RequirementGraph`, `DomainClassifier`, `EntityExtractor`, `FeatureIdentifier`, `ConstraintDetector`, `StoryGenerator`)
- `stage_models.py:19` — `Stage.REQUIREMENT_DECOMPOSER` en el enum
- `NODE_MAP` (orchestrator.py:75-86) — NO incluye `REQUIREMENT_DECOMPOSER`
- `tests/test_requirement_decomposer.py` — 3 tests existentes
- `AGENTS.md` — listado como componente activo

### Plan 121 decia

```
### P2 — RequirementDecomposer dead code (MEDIA) **NO IMPLEMENTAR (EN EVALUACION)**
```

La evaluacion original recomendo no eliminar porque existe una propuesta (`docs/120_PROP_DEV_DASHBOARD_MVP_1_0_DRAFT.md`) para **cablearlo como capa adaptativa central** del pipeline.

### Decision necesaria

| Opcion | Esfuerzo | Riesgo | Beneficio |
|--------|----------|--------|-----------|
| **A: Eliminar** (P2.1-P2.3) | 1.5h | Bajo | -317 lineas dead code, enum mas limpio |
| **B: Cablear en NODE_MAP** | 2h | Medio | Pipeline adaptativo, RequirementGraph generado |
| **C: Mantener como esta** | 0h | Bajo | Dead code persiste, confusion continua |

### Si se elige Opcion A (Eliminar)

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| P2.1 | Verificar que ningun import referencia `requirement_decomposer` o `Stage.REQUIREMENT_DECOMPOSER` en codigo activo | (grep en `*.py` fuera de tests/) | 0.5h | `grep` retorna 0 referencias (salvo enum y tests) |
| P2.2 | Eliminar `nodes/requirement_decomposer.py` | `nodes/requirement_decomposer.py` (ELIMINAR) | 0.5h | Archivo eliminado |
| P2.3 | Eliminar `REQUIREMENT_DECOMPOSER` del enum `Stage` en `state_models.py` | `state_models.py` (MODIFICAR) | 0.5h | Enum compila sin ese valor, tests pasan |

### Si se elige Opcion B (Cablear)

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| P2.B1 | Agregar `REQUIREMENT_DECOMPOSER` en `NODE_MAP` entre `PARSER` y `SEMANTIC_ANALYZER` | `orchestrator.py` (MODIFICAR) | 0.5h | `Stage.REQUIREMENT_DECOMPOSER: RequirementDecomposer` en NODE_MAP |
| P2.B2 | Preservar `raw_text` a traves del pipeline para que RequirementDecomposer lo reciba | `orchestrator.py` (`_make_node`) | 0.5h | RequirementDecomposer recibe texto crudo + AST parcial |
| P2.B3 | Verificar que `RequirementGraph` producido se consume aguas abajo | `nodes/semantic_analyzer.py` (VERIFICAR) | 1h | SemanticAnalyzer acepta RequirementGraph como entrada opcional |

**Nota:** La opcion B requiere validacion adicional de que el LLM esta disponible y configurado (RequirementDecomposer usa `LLMOrchestrator`).

---

## Resumen de Ejecucion

### Orden sugerido

```
1. P2 ── Decision sobre RequirementDecomposer (prioridad: definir antes de refactors)
2. P4 ── Thread-safe StageSubject (independiente, bajo riesgo)
3. P5 ── Unificar EventBus (depende de entendimiento del sistema de observers)
```

### Presupuesto por opcion

| Escenario | P4 | P5 | P2 | Total |
|-----------|----|----|-----|-------|
| Eliminar P2 (A) | 4h | 6h | 1.5h | **11.5h** |
| Cablear P2 (B) | 4h | 6h | 2h | **12h** |
| Mantener P2 (C) | 4h | 6h | 0h | **10h** |

### Verificacion global

```bash
# Ruff
ruff check . && ruff format --check .

# Tests de los modulos afectados
pytest tests/test_observer_pattern.py -v
pytest tests/test_validator_chain.py -v
pytest tests/test_security_scanner.py -v

# Tests de regresion (si el entorno lo permite)
pytest tests/ -v --cov 2>&1 | tail -20
```

---

## Apendice: Referencias a StageObserver por archivo

```bash
# Archivos que importan o implementan StageObserver (14 archivos):
compiler-bot/agentic_pipeline/prompt_chain/observer_base.py      ← definicion
compiler-bot/agentic_pipeline/prompt_chain/__init__.py            ← export
compiler-bot/agentic_pipeline/base_stage.py                       ← import
compiler-bot/agentic_pipeline/prompt_chain/handler_base.py        ← import
compiler-bot/agentic_pipeline/prompt_chain/orchestrator.py        ← import
compiler-bot/agentic_pipeline/observers/audit_observer.py         ← implementa
compiler-bot/agentic_pipeline/observers/metrics_observer.py       ← implementa (docstring)
compiler-bot/agentic_pipeline/observers/debug_observer.py         ← implementa (docstring)
compiler-bot/agentic_pipeline/observers/dashboard_observer.py     ← implementa (docstring)
compiler-bot/agentic_pipeline/observers/prompt_optimizer_observer.py ← implementa (docstring)
compiler-bot/agentic_pipeline/security/bandit_scanner.py          ← implementa
compiler-bot/agentic_pipeline/tests/test_observer_pattern.py      ← tests
```

---

*Documento generado a partir de la verificacion de plan 121. Fecha: 2026-06-19.*