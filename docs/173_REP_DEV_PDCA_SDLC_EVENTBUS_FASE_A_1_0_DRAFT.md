---
id: "173"
area: "DEV"
type: "REP"
module: "PDCA_SDLC"
version: "1.0"
status: "DRAFT"
tags: ["report", "execution", "event-bus", "fase-a", "query-engine", "sse"]
summary: "Reporte de ejecucion de Fase A — Query Engine + Agregaciones + SSE callbacks en AsyncEventBus."
changelog:
  - version: "1.0"
    date: "2026-06-20"
    author: "Sistema"
    description: "Version inicial — reporte de ejecucion Fase A"
---

# Reporte de Ejecucion — PDCA-sdlc Fase A: Query Engine + Agregaciones + SSE

> **Plan base:** `docs/172_PLAN_DEV_PDCA_SDLC_EVENTBUS_API_EXECUTION_1_0_DRAFT.md`
> **Analisis base:** `docs/171_ANALYSIS_DEV_PDCA_SDLC_EVENTBUS_API_1_0_DRAFT.md`
> **Duracion:** 1 dia
> **Tests finales:** 176 (57 event bus + 119 otros)

---

## Resumen

Implementacion completa del motor de consultas, agregaciones y SSE callbacks
en `AsyncEventBus`. Se agregaron indices auxiliares (`_by_project`, `_by_id`),
10 nuevos metodos publicos, y soporte para SSE callbacks. 38 tests nuevos,
0 regresiones, ruff 0 errores.

---

## Cambios Realizados

### Archivo: `core/event_bus.py`

| Seccion | Cambio | LOC |
|---------|--------|-----|
| Docstring | Actualizado para reflejar nuevas capacidades | ~2 |
| `__init__` | Agregados `_by_project`, `_by_id`, `_sse_callbacks` | ~3 |
| `publish()` | Mantenimiento de indices en cada publicacion | ~12 |
| `publish()` | Invocacion de SSE callbacks por project_id y `_all` | ~4 |
| `query_events()` | Nuevo — filtros por project, topic (wildcard), source, time range, search, pagination | ~40 |
| `get_event()` | Nuevo — lookup por event_id via `_by_id` | ~3 |
| `get_topic_distribution()` | Nuevo — conteo de eventos por topic para un proyecto | ~6 |
| `get_timeline()` | Nuevo — buckets temporales (1s/1m/1h) | ~12 |
| `get_topics()` | Nuevo — topics unicos con count y last_seen | ~14 |
| `get_sources()` | Nuevo — sources unicos con count y topics | ~18 |
| `get_stats()` | Nuevo — metricas de salud del bus | ~14 |
| `get_subscribers()` | Nuevo — introspeccion de handlers exactos y wildcard | ~22 |
| `register_sse_callback()` | Nuevo — registro de callback SSE | ~5 |
| `unregister_sse_callback()` | Nuevo — eliminacion de callback SSE | ~5 |
| `clear()` | Limpieza de `_by_project`, `_by_id`, `_sse_callbacks` | ~3 |

**Total LOC anadidos:** ~160
**Total archivo:** 382 lineas (+225 desde version anterior)

### Archivo: `tests/test_event_bus_query.py` (NUEVO)

| Clase de Test | Tests | Descripcion |
|---------------|-------|-------------|
| `TestQueryEvents` | 12 | Filtros (project, topic, source, time, search), pagination, total count |
| `TestGetEvent` | 2 | Lookup por ID, not found |
| `TestTopicDistribution` | 2 | Distribucion basica, proyecto vacio |
| `TestTimeline` | 4 | Timeline basico, vacio, granularidad 1s, granularidad invalida |
| `TestTopics` | 2 | Topics unicos, vacio |
| `TestSources` | 2 | Sources unicos, vacio |
| `TestStats` | 2 | Metricas de salud, bus vacio |
| `TestSubscribers` | 3 | Wildcard, exacto, vacio |
| `TestSSECallbacks` | 5 | Invocacion, multi-proyecto, unregister, `_all`, filtro por proyecto |
| `TestIndices` | 4 | Consistencia en overflow, clear, retrocompatibilidad replay, since_sequence |

**Total tests:** 38

---

## Detalles de Implementacion

### Indices auxiliares

Se agregaron dos indices para optimizar consultas:

- `_by_project: dict[str, list[Event]]` — lista FIFO por project_id, permite
  consultas O(1) por proyecto vs O(n) de `_event_log`
- `_by_id: dict[str, Event]` — lookup O(1) por event_id

Ambos indices se mantienen sincronizados en `publish()` y se limpian en el
FIFO overflow (lineas 138-144). El test `test_indices_consistent_on_overflow`
verifica que al exceder `_max_log_size=3` con 5 eventos, solo los 3 mas
recientes permanecen en los indices.

### Query Engine

`query_events()` implementa filtros combinados via AND:

1. **project_id** — usa `_by_project` si el proyecto existe, o recorre
   `_event_log` si es None (todos los proyectos)
2. **topic_pattern** — reusa `TopicMatcher.matches()` para soportar
   wildcards `*` (un nivel) y `>` (subarbol)
3. **source** — filtro exacto (case-sensitive)
4. **since_time / until_time** — filtro por timestamp (inclusive)
5. **search_text** — busqueda case-insensitive en `str(event.data)`
6. **since_sequence** — filtro por numero de secuencia (exclusivo)

Retorna `(events_paginated, total_count)` para facilitar la paginacion
en el frontend. Limit default: 100, offset default: 0.

### SSE Callbacks

Mecanismo para Server-Sent Events:

```python
def register_sse_callback(self, project_id, callback)
def unregister_sse_callback(self, project_id, callback)
```

- Los callbacks se almacenan en `_sse_callbacks: dict[str, list[Callable]]`
- `_all` como project_id especial recibe eventos de todos los proyectos
- Se invocan en `publish()` despues de wildcard dispatch, antes del
  `publish_async` interno
- Se limpian en `clear()`

### Introspeccion de Subscriptores

`get_subscribers()` combina:
- Handlers exactos del `_EventBus._subscribers` interno (topic exacto)
- Handlers wildcard del `_wildcard_handlers` local

Cada entrada incluye: `pattern`, `handler` (nombre de funcion), `type`
(exact|wildcard).

---

## Verificacion

| Comando | Resultado |
|---------|-----------|
| `python -m pytest tests/test_event_bus.py -v` | 19 passed |
| `python -m pytest tests/test_event_bus_query.py -v` | 38 passed |
| `python -m pytest tests/ -v` | 176 passed |
| `ruff check core/event_bus.py tests/test_event_bus_query.py` | All checks passed |
| `ruff format core/event_bus.py tests/test_event_bus_query.py` | 2 files reformatted |

---

## Proximos Pasos

Fase B (API — Dia 2): Implementar nuevos endpoints en `dashboard/service.py`
y `dashboard/app.py`, incluyendo el SSE endpoint sobre los callbacks
registrados en Fase A. Ver `docs/172_PLAN_DEV_PDCA_SDLC_EVENTBUS_API_EXECUTION_1_0_DRAFT.md`.
