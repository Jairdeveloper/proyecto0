---
id: "171"
area: "DEV"
type: "ANALYSIS"
module: "PDCA_SDLC"
version: "1.0"
status: "DRAFT"
tags: ["analysis", "event-bus", "api", "dashboard", "async-event-bus", "replay"]
summary: "Analisis de la API AsyncEventBus (replay) y oportunidades de implementacion de funcionalidades/endpoints para el dashboard."
changelog:
  - version: "1.0"
    date: "2026-06-20"
    author: "Sistema"
    description: "Version inicial — analisis de la API AsyncEventBus y oportunidades de mejora"
---

# Analisis API AsyncEventBus y Oportunidades para el Dashboard

## 1. API Actual — `AsyncEventBus` (`core/event_bus.py`)

### Metodos publicos

| Metodo | Firma | Uso en Dashboard |
|--------|-------|------------------|
| `set_max_log_size` | `(size: int) -> None` | No usado |
| `subscribe` | `(topic: str, handler: Callable) -> None` | Uso interno por agentes |
| `unsubscribe` | `(topic: str, handler: Callable) -> None` | Uso interno |
| `publish` | `(event: Event) -> None` | Uso interno |
| `replay` | `(project_id: str, since_sequence: int = 0) -> list[Event]` | **Unico acceso del dashboard** |
| `has_subscribers` | `(topic: str) -> bool` | No usado |
| `clear` | `() -> None` | No usado |

### Modelo `Event` (dataclass)

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `topic` | `str` | Jerarquico: `project.initialized`, `adaptation.complete`, etc. |
| `source` | `str` | `adaptation-agent`, `requirements-analyst`, `coder-agent` |
| `project_id` | `str` | `p-01` |
| `data` | `dict[str, Any]` | Payload arbitrario (validado por Pydantic en `event_schemas.py`) |
| `id` | `str` | UUID hex 12 chars |
| `timestamp` | `float` | Unix epoch |
| `sequence` | `int` | Auto-incremento por project_id |

### Rutas del dashboard actual (`dashboard/app.py`)

| Ruta | Metodo | Backing (`service.py`) |
|------|--------|----------------------|
| `/api/health` | GET | `get_health()` — timestamp |
| `/api/projects` | GET | `get_projects()` — lista con counts |
| `/api/projects/:id` | GET | `get_project(id)` — goal + reqs + artifacts |
| `/api/projects/:id/trace` | GET | `get_trace(id)` — BFS del KG |
| `/api/agents` | GET | `get_agents()` — registry manifests |
| `/api/events?project=&limit=` | GET | `get_events(pid, limit)` — replay + slice |
| `/` | GET | Static SPA |
| `/static/*` | GET | Static files |

---

## 2. Limitaciones Identificadas

### 2.1. `replay()` es un filtro lineal simple

```python
def replay(self, project_id: str, since_sequence: int = 0) -> list[Event]:
    return [e for e in self._event_log if e.project_id == project_id and e.sequence > since_sequence]
```

- **Solo filtra por project_id + sequence** — no hay filtro por topic, source, time range, ni busqueda en data
- **O(n) sobre todo el log** — con `_max_log_size=10000`, es aceptable pero no escala a multiples proyectos concurrentes
- **No hay paginacion** — siempre devuelve todo el subconjunto
- **No hay acceso por event_id** — no se puede obtener un evento individual
- **No hay agregaciones** — counts, distribucion, series temporales

### 2.2. Sin introspeccion de subscriptores

`_wildcard_handlers` es privado. No hay forma de preguntar:
- Que agentes estan suscritos a que topics?
- Que handlers estan registrados?

### 2.3. Sin estadisticas ni metricas

No se puede obtener del EventBus:
- Total de eventos emitidos
- Tasa de publicacion (eventos/segundo)
- Distribucion por topic
- Distribucion por source
- Uso actual del log vs capacidad

### 2.4. Sin soporte para tiempo real

El dashboard es pull-based (refresca con click). Sin SSE (Server-Sent Events), no hay actualizacion automatica.

### 2.5. Dashboard: sin visualizacion de datos agregados

Las KPIs actuales (Proyectos, Agentes, Eventos, Artefactos) son totales planos. No hay:
- Grafica de distribucion de eventos por tipo
- Timeline de eventos
- Vista de heatmap de actividad
- Proporcion exito/fallo

---

## 3. Oportunidades de Implementacion

Agrupadas por impacto y dependencia.

### 3.1. ALTA — Extender `AsyncEventBus` con query engine

Nuevo metodo `query_events()` que reemplace/amplie `replay()`:

```python
def query_events(
    self,
    project_id: str | None = None,
    topic_pattern: str | None = None,   # wildcards: "project.*", ">.created"
    source: str | None = None,
    since_sequence: int = 0,
    since_time: float | None = None,
    until_time: float | None = None,
    search_text: str | None = None,      # busqueda en data (JSON str)
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[Event], int]:            # (events, total_count)
```

**Beneficio:** Habilita todos los endpoints de filtrado y paginacion desde el dashboard.

**Implementacion:** Indices auxiliares:
- `_event_log` (lineal) — principal
- `_by_project: dict[str, list[Event]]` — lookup rapido por proyecto
- `_by_id: dict[str, Event]` — lookup por event_id
- `TopicMatcher` para filtros wildcard

**Costo:** ~40 LOC en `event_bus.py`, mantener indices en `publish()` y `clear()`.

### 3.2. ALTA — Endpoints nuevos en el dashboard

| Endpoint | Descripcion | Backing |
|----------|-------------|---------|
| `GET /api/events?project=&topic=&source=&since_time=&until_time=&search=&limit=&offset=` | Query con filtros | `service.query_events(...)` |
| `GET /api/events/:id` | Evento individual | `bus.get_event(id)` |
| `GET /api/events/distribution?project=` | Conteo por topic | `bus.get_topic_distribution(pid)` |
| `GET /api/events/timeline?project=&granularity=1m` | Buckets temporales | `bus.get_timeline(pid, granularity)` |
| `GET /api/topics` | Todos los topics vistos | `bus.get_all_topics()` |
| `GET /api/sources` | Todos los sources vistos | `bus.get_all_sources()` |
| `GET /api/subscriptions` | Registro de subscriptores | `bus.get_subscribers()` |
| `GET /api/health/metrics` | Metricas extendidas | `service.get_metrics()` |
| `GET /api/events/live?project=` | SSE stream en tiempo real | Nuevo mecanismo de callback |

**Implementacion:** ~120 LOC en `service.py`, ~80 LOC en `app.py`.

### 3.3. ALTA — Server-Sent Events para live dashboard

Agregar a `AsyncEventBus`:

```python
# Registration
def register_sse_callback(self, project_id: str, callback: Callable[[Event], None]) -> None: ...
def unregister_sse_callback(self, project_id: str, callback: Callable[[Event], None]) -> None: ...

# Inside publish(), after logging:
for cb in self._sse_callbacks.get(event.project_id, []):
    cb(event)
```

En `app.py`, endpoint `GET /api/events/live?project=` retorna `text/event-stream`:

```
data: {"sequence": 5, "topic": "code.committed", "source": "coder-agent", ...}

data: {"sequence": 6, "topic": "quality_gate.result", ...}
```

El frontend usa `EventSource` JS API nativa (sin dependencias).

### 3.4. MEDIA — Dashboard frontend: nuevas vistas

| Vista | Descripcion | Dependencia |
|-------|-------------|-------------|
| **Distribucion de eventos** | Bar chart (Canvas API) mostrando eventos por tipo | `/api/events/distribution` |
| **Timeline** | SVG/Canvas linea temporal de actividad del pipeline | `/api/events/timeline` |
| **Explorador de eventos** | Tabla paginada con filtros por topic/source/fecha | `/api/events` (query) |
| **Detalle de evento** | Modal/panel expandido mostrando `data` crudo | `/api/events/:id` |
| **Topologia de agentes** | Grafo SVG mostrando agentes y sus suscripciones | `/api/subscriptions` + `/api/agents` |
| **Health expandido** | Barra de metricas: uso del log, tasa, errores | `/api/health/metrics` |
| **Live indicator** | Badge verde "Live" + contador de eventos en tiempo real | SSE endpoint |

**Canvas API** para charts requiere ~80-100 LOC de JS (sin dependencias externas) para bar charts basicos. SVG para topologia es mas complejo (~150 LOC).

### 3.5. BAJA — Exportacion

| Endpoint | Formato |
|----------|---------|
| `GET /api/events/export?project=&format=json` | JSON array |
| `GET /api/events/export?project=&format=csv` | CSV plano |

### 3.6. BAJA — Log Management

| Endpoint | Descripcion |
|----------|-------------|
| `POST /api/events/clear` | Resetear log (solo si autenticado) |
| `POST /api/events/maxlog?size=50000` | Redimensionar log |

---

## 4. Dependencias Tecnicas

| Feature | Requiere cambio en `event_bus.py`? | Requiere cambio en `service.py`? | Requiere cambio en `app.py`? | Requiere cambio en frontend? |
|---------|--------------------------------------|------------------------------------|-------------------------------|-------------------------------|
| Query engine | Si (nuevo `query_events`) | Si (wrapper) | Si (nueva ruta) | Si (explorador) |
| Event distribution | Si (`get_topic_distribution`) | Si | Si | Si (bar chart) |
| Timeline | Si (`get_timeline`) | Si | Si | Si (SVG timeline) |
| SSE live | Si (callbacks) | No* | Si (endpoint SSE) | Si (EventSource) |
| Subscribers | Si (`get_subscribers`) | Si | Si | Si (tabla) |
| Export | No (usa query) | Si | Si | No |
| Health metrics | Si (`get_stats`) | Si (wrapper) | Si | Si (KPI row) |

*\*SSE puede integrarse directamente desde `app.py` si el handler tiene acceso al bus.*

---

## 5. Roadmap Propuesto

```
Fase A (Core) — Dia 1
  +-- Extender AsyncEventBus: query_events(), indices, get_topic_distribution(),
  |   get_timeline(), get_subscribers(), get_stats()
  +-- Tests: ~15 nuevos
  +-- Verificar: 0 regresiones (138 -> 153 tests)

Fase B (API) — Dia 2
  +-- Nuevos endpoints en service.py y app.py
  +-- SSE mechanism (register_sse_callback en bus + endpoint text/event-stream)
  +-- Tests: ~8 nuevos (161 total)
  +-- Verificar: ruff 0 errors

Fase C (Frontend) — Dia 3
  +-- Bar chart de distribucion (Canvas API)
  +-- Event timeline (SVG)
  +-- Event explorer con filtros
  +-- Live indicator + SSE consumer
  +-- Topologia de agentes (SVG opcional)
  +-- Tests: ~4 frontend smoke tests (165 total)
```

**Total estimado:** ~300 LOC backend, ~200 LOC frontend, ~30 tests.

---

## 6. Riesgos y Consideraciones

| Riesgo | Mitigacion |
|--------|------------|
| `_event_log` crece sin control | Ya hay `_max_log_size`; anyadir purge periodico o FIFO |
| SSE consume conexiones del HTTPServer | El server es threading-based; cada SSE es una conexion larga. Limite practico: ~50 conexiones simultaneas |
| Canvas charts requieren mantenimiento | Vanilla JS charts son fragiles. Alternativa: agregar dependencia liviana (Chart.js 3.x ~60KB) |
| `query_events()` O(n) sin indices reales | Con `_by_project` dict, bajar a O(m) por proyecto. Con `_max_log_size=10000`, es aceptable en RAM |
| Sin wildcard `fnmatch` en query | Reusar `TopicMatcher.matches()` para filtrar topics |

---

## Resumen

El `AsyncEventBus` tiene una API minimalista pero solida. La funcionalidad `replay()` es la llave — actualmente infrautilizada. Extenderla con un `query_events()` indexado desbloquea 9 endpoints nuevos. El SSE es el game-changer para UX: live dashboard sin polling. Las visualizaciones con Canvas API nativa mantienen la filosofia zero-dependency.
