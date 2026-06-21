---
id: "P03.2"
area: dev
type: rep
module: recpl_arch_remaining
version: "1.0"
status: IMPLEMENTED
tags: ["report", "p5", "event-bus", "observer", "stage-subject", "unification"]
summary: "Reporte de ejecucion de P5 — unificacion de EventBus + StageSubject: StageSubject como fachada sobre EventBus, eliminacion de StageObserver, limpieza de imports"
changelog:
  - version: "1.0"
    date: "2026-06-19"
    author: "Sistema"
    description: "Version inicial — ejecucion completa de P5 del plan 149"
---

# Reporte de Ejecucion — P5: Unificar EventBus + StageSubject

> **Plan base:** `docs/149_PLAN_DEV_REMAINING_ARCHITECTURAL_ITEMS_1_0_DRAFT.md`  
> **Tiempo estimado:** 6h  
> **Tiempo real:** ~0.5h  
> **Estado:** ✅ COMPLETADO

---

## Resumen

Se unifico el sistema de pub/sub eliminando el mecanismo paralelo de `StageSubject._observers` + `StageObserver` y delegando toda la difusion de eventos a `EventBus`. `StageSubject` paso a ser una fachada delgada que mantiene la API `attach/detach/notify` por compatibilidad pero delega internamente en `EventBus`. `StageObserver` (ABC) se elimino completamente.

---

## Tareas ejecutadas

### P5.1 — Unificar interfaces (3h estimado)

**Archivo:** `compiler-bot/agentic_pipeline/prompt_chain/observer_base.py`

Cambios:

1. Eliminado `import threading` y toda la logica de lock (ya no hace falta — `StageSubject` no mantiene estado mutable local)
2. Eliminada clase `StageObserver(ABC)` — 18 lineas eliminadas
3. `StageSubject` refactorizado como fachada delgada:
   - Eliminado `_observers: list[StageObserver]` — la unica fuente de verdad es `EventBus._subscribers`
   - Agregado `_wrappers: dict[int, Callable]` para mapear observer → wrapper callback (necesario para `detach()`)
   - `attach(observer)`: crea un wrapper que llama a `observer.on_event(data)` y lo suscribe a `EventBus` bajo el topic `STAGE_EVENTS_TOPIC = "stage_event"`
   - `detach(observer)`: busca el wrapper por `id(observer)`, lo desuscribe de `EventBus`
   - `notify(event)`: solo `self._bus.publish(STAGE_EVENTS_TOPIC, event)` — unico punto de difusion
   - `observer_count`: delega en `EventBus.subscriber_count()`

### P5.3 — Eliminar StageObserver (2h estimado)

**Archivos modificados:**

| Archivo | Cambio |
|---------|--------|
| `observers/audit_observer.py` | Eliminado `StageObserver` del import; `class AuditObserver(StageObserver)` → `class AuditObserver` |
| `security/bandit_scanner.py` | Eliminado `StageObserver` del import; `class BanditScanner(StageObserver)` → `class BanditScanner` |
| `observers/metrics_observer.py` | Docstring: `StageObserver que registra` → `registra` |
| `observers/debug_observer.py` | Docstring: `StageObserver que invoca` → `invoca` |
| `observers/dashboard_observer.py` | Docstring: `StageObserver que mantiene` → `Mantiene...` |
| `observers/prompt_optimizer_observer.py` | Docstring: `StageObserver que registra` → `Registra` |

**Verificacion:** `git grep -l "StageObserver" -- "*.py"` = 0 en codigo activo (solo docstring historico en observer_base.py y docs/diagrams/mermaidToimage.py)

### P5.4 — Actualizar imports (1h estimado)

| Archivo | Cambio |
|---------|--------|
| `prompt_chain/__init__.py` | Eliminado `StageObserver` del import y `__all__` |
| `tests/test_observer_pattern.py` | Eliminado `StageObserver` del import; `MagicMock(spec=StageObserver)` → `MagicMock()` (6 ocurrencias) |

**No requirieron cambios:** `base_stage.py`, `handler_base.py`, `prompt_chain/orchestrator.py` — importan `StageSubject` y `StageEvent`, cuya API no cambio.

---

## Resultados de tests

```
tests/test_observer_pattern.py ...         19/19 passed (0.36s)
tests/test_security_scanner.py ...          9/9 passed  (1.56s)
tests/test_validator_chain.py ...          13/13 passed (8.31s)
```

Todos los tests preexistentes pasan sin regresiones.

---

## Archivos modificados

| Archivo | Cambio | Lineas |
|---------|--------|--------|
| `prompt_chain/observer_base.py` | Refactor completo: fachada sobre EventBus, eliminar StageObserver | -18 netas |
| `prompt_chain/__init__.py` | Eliminar StageObserver de exports | -2 |
| `observers/audit_observer.py` | Eliminar herencia StageObserver | -2 |
| `observers/metrics_observer.py` | Docstring | -2 |
| `observers/debug_observer.py` | Docstring | -2 |
| `observers/dashboard_observer.py` | Docstring | -1 |
| `observers/prompt_optimizer_observer.py` | Docstring | -1 |
| `security/bandit_scanner.py` | Eliminar herencia StageObserver, docstring | -3 |
| `tests/test_observer_pattern.py` | Import, MagicMock specs | -2 |

**Total:** 9 archivos modificados, ~33 lineas netas eliminadas.

---

## Verificacion final

```bash
ruff check .                                                # 0 errores
ruff format --check .                                       # 0 diferencias
git grep -l "StageObserver" -- "*.py" | grep -v mermaid     # solo docstring historico
python -m pytest tests/test_observer_pattern.py -v -o "addopts="  # 19/19 passed
```

---

*Reporte generado tras ejecucion de P5. Fecha: 2026-06-19.*
