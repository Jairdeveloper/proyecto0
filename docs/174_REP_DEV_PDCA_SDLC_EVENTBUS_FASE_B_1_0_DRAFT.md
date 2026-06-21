---
id: "174"
area: dev
type: rep
module: pdca_sdlc
version: "1.0"
status: IMPLEMENTED
tags: ["report", "execution", "dashboard", "fase-b", "api", "endpoints", "sse"]
summary: "Reporte de ejecucion de Fase B — Endpoints Dashboard: query, distribution, timeline, topics, sources, subscriptions, metrics, SSE."
changelog:
  - version: "1.0"
    date: "2026-06-20"
    author: "Sistema"
    description: "Version inicial — reporte de ejecucion Fase B"
---

# Reporte de Ejecucion — PDCA-sdlc Fase B: Endpoints Dashboard

> **Plan base:** `docs/172_PLAN_DEV_PDCA_SDLC_EVENTBUS_API_EXECUTION_1_0_DRAFT.md`
> **Fase anterior:** `docs/173_REP_DEV_PDCA_SDLC_EVENTBUS_FASE_A_1_0_DRAFT.md`
> **Duracion:** 1 dia
> **Tests finales:** 198 (22 nuevos, 0 regresiones)

---

## Resumen

Implementacion completa de 9 nuevos endpoints REST para el dashboard,
incluyendo el endpoint SSE (Server-Sent Events) para streaming en
tiempo real. Se agregaron 8 metodos a `SdlcDashboardService`, 9 rutas
a `DashboardHTTPHandler`, y 22 tests de integracion. 0 regresiones,
ruff 0 errores.

---

## Cambios Realizados

### Archivo: `dashboard/service.py`

| Metodo | Descripcion |
|--------|-------------|
| `_serialize_event()` | Helper estatico para serializar Event a dict JSON-safe |
| `query_events()` | Wrapper sobre `bus.query_events()` con filtros y paginacion |
| `get_event_detail()` | Wrapper sobre `bus.get_event()`, devuelve None si no existe |
| `get_event_distribution()` | Wrapper sobre `bus.get_topic_distribution()` |
| `get_event_timeline()` | Wrapper sobre `bus.get_timeline()` con granularidad |
| `get_topics()` | Wrapper sobre `bus.get_topics()` |
| `get_sources()` | Wrapper sobre `bus.get_sources()` |
| `get_subscriptions()` | Wrapper sobre `bus.get_subscribers()` |
| `get_metrics()` | Combina `bus.get_stats()` con status y timestamp |

**Import adicional:** `Event` desde `pdca_sdlc.core.event_bus`

### Archivo: `dashboard/app.py`

| Ruta | Metodo / Funcion | Parseo params |
|------|-----------------|---------------|
| `GET /api/health/metrics` | `service.get_metrics()` | — |
| `GET /api/events` (extendido) | `service.query_events()` | `project`, `topic`, `source`, `search`, `since_time`, `until_time`, `limit`, `offset` |
| `GET /api/events/:id` | `service.get_event_detail()` | Path param `id` |
| `GET /api/events/distribution` | `service.get_event_distribution()` | `project` |
| `GET /api/events/timeline` | `service.get_event_timeline()` | `project`, `granularity` |
| `GET /api/events/live` | `_handle_sse()` — SSE stream | `project` |
| `GET /api/topics` | `service.get_topics()` | — |
| `GET /api/sources` | `service.get_sources()` | — |
| `GET /api/subscriptions` | `service.get_subscriptions()` | — |

**Nuevo:** `DashboardHTTPHandler.bus` — variable de clase para acceso al
EventBus desde el handler (necesario para SSE).

**Nuevo:** `DashboardHTTPHandler._handle_sse()` — establece conexion SSE
con headers `text/event-stream`, registra callback via
`bus.register_sse_callback()`, mantiene heartbeat cada 15s, y limpia
el callback al desconectar.

**Actualizado:** `create_server()` acepta nuevo parametro `bus:
AsyncEventBus | None`.

**Actualizado:** `run_server()` acepta nuevo parametro `bus`.

### Archivo: `main.py`

Actualizada la llamada a `run_server()` para pasar `bus=bus` como
keyword argument.

### Archivo: `tests/test_dashboard_api.py` (modificado)

Actualizados 2 tests para alinearse con el nuevo formato de respuesta
de `/api/events` (ahora usa `query_events()` siempre):
- `test_events()`: usa `data["total"]` en vez de `data["project_id"]`
- `test_events_missing_project_param()`: ya no retorna 400 (retorna todos los eventos)

### Archivo: `tests/test_dashboard_api_v2.py` (NUEVO)

| Clase | Tests | Descripcion |
|-------|-------|-------------|
| `TestQueryEventsV2` | 9 | Query defaults, topic filter, source filter, pagination, search, no match, missing project, all projects, limit validation |
| `TestEventDetail` | 2 | Detail by ID, not found |
| `TestEventDistribution` | 2 | Distribution, missing project |
| `TestEventTimeline` | 3 | Timeline basic, granularity, missing project |
| `TestTopics` | 1 | Topics endpoint |
| `TestSources` | 1 | Sources endpoint |
| `TestSubscriptions` | 1 | Subscriptions endpoint |
| `TestMetrics` | 2 | Metrics endpoint, health still works |
| `Test404` | 1 | Unknown route returns 404 |

**Total tests nuevos:** 22

---

## Detalles de Implementacion

### SSE Endpoint

El endpoint `/api/events/live?project=X` utiliza Server-Sent Events
para transmitir eventos en tiempo real al dashboard:

1. El handler registra un callback via `bus.register_sse_callback()`
   que escribe en `self.wfile` en formato SSE (`data: {...}\n\n`)
2. Mantiene la conexion abierta con heartbeats cada 15s
3. Al desconectarse (BrokenPipeError), limpia el callback via
   `bus.unregister_sse_callback()`
4. Soporta `project=_all` para recibir eventos de todos los proyectos

El mecanismo SSE depende de los callbacks registrados en Fase A.

### Routing de `/api/events`

El endpoint `/api/events` ahora usa `service.query_events()` que
soporta filtros opcionales:
- `project`: filtro por proyecto (o `_all` para todos)
- `topic`: patron wildcard (usa `TopicMatcher.matches()`)
- `source`: filtro exacto
- `since_time` / `until_time`: rango temporal (Unix epoch)
- `search`: busqueda case-insensitive en `data`
- `limit` / `offset`: paginacion

Si no se especifica `project`, retorna eventos de todos los proyectos.

### Cambio en `create_server()` / `run_server()`

Ambas funciones aceptan ahora un parametro `bus` opcional. Esto es
necesario para que el handler del SSE endpoint pueda registrar
callbacks en el EventBus. El handler expone `DashboardHTTPHandler.bus`
como variable de clase, accesible desde `_handle_sse()`.

---

## Verificacion

| Comando | Resultado |
|---------|-----------|
| `python -m pytest tests/test_dashboard_api.py -v` | 12 passed |
| `python -m pytest tests/test_dashboard_api_v2.py -v` | 22 passed |
| `python -m pytest tests/ -v` | 198 passed |
| `ruff check dashboard/ main.py` | All checks passed |
| `ruff format dashboard/ main.py` | OK |

---

## Proximos Pasos

Fase C (Frontend — Dia 3): Visualizaciones Canvas, timeline SVG,
explorador de eventos con filtros, modal de detalle, e indicador
live con SSE consumer en el frontend. Ver
`docs/172_PLAN_DEV_PDCA_SDLC_EVENTBUS_API_EXECUTION_1_0_DRAFT.md`.
