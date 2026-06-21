---
id: "172"
area: "DEV"
type: "PLAN"
module: "PDCA_SDLC"
version: "1.0"
status: IMPLEMENTED
tags: ["plan", "execution", "event-bus", "api", "dashboard", "sse", "replay"]
summary: "Plan de ejecucion para extender AsyncEventBus con query engine, nuevos endpoints dashboard, SSE en tiempo real y visualizaciones Canvas."
changelog:
  - version: "1.0"
    date: "2026-06-20"
    author: "Sistema"
    description: "Version inicial — plan de ejecucion basado en analisis 171"
---

# Plan de Ejecucion — PDCA-sdlc EventBus API Extension

> **Analisis base:** `docs/171_ANALYSIS_DEV_PDCA_SDLC_EVENTBUS_API_1_0_DRAFT.md`
> **Proyecto:** PDCA-sdlc (Fase 1.5 — mejora EventBus + Dashboard)
> **Duracion:** 3 dias
> **Archivos a modificar:** 6
> **Archivos nuevos:** 0
> **Tests nuevos:** ~30
> **Total tests esperado:** ~168

---

## Resumen

Extender la API del `AsyncEventBus` con un motor de consultas rico (filtros, paginacion, agregaciones), agregar 9 endpoints nuevos al dashboard, implementar SSE para actualizaciones en tiempo real, y enriquecer el frontend con visualizaciones Canvas nativas (zero-dependency).

---

## Fase A (Core) — Dia 1: Query Engine + Agregaciones

### Archivo: `core/event_bus.py`

#### A.1. Indices auxiliares en `__init__`

```python
def __init__(self) -> None:
    self._bus = _EventBus()
    self._sequences: dict[str, int] = {}
    self._event_log: list[Event] = []
    self._by_project: dict[str, list[Event]] = {}  # NUEVO
    self._by_id: dict[str, Event] = {}              # NUEVO
    self._max_log_size: int = 10000
    self._wildcard_handlers: list[tuple[str, Callable]] = []
```

#### A.2. Mantener indices en `publish()`

```python
async def publish(self, event: Event) -> None:
    event.sequence = self._next_sequence(event.project_id)
    self._event_log.append(event)
    self._by_project.setdefault(event.project_id, []).append(event)
    self._by_id[event.id] = event
    if len(self._event_log) > self._max_log_size:
        removed = self._event_log.pop(0)
        # Limpiar indices
        if removed.id in self._by_id:
            del self._by_id[removed.id]
        proj_events = self._by_project.get(removed.project_id, [])
        if proj_events and proj_events[0].id == removed.id:
            proj_events.pop(0)
    # Wildcard dispatch...
```

#### A.3. `query_events()` — motor de consultas

```python
def query_events(
    self,
    project_id: str | None = None,
    topic_pattern: str | None = None,
    source: str | None = None,
    since_sequence: int = 0,
    since_time: float | None = None,
    until_time: float | None = None,
    search_text: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[Event], int]:
    """Query events with filters, pagination, and total count."""
    candidates: list[Event] = []
    if project_id and project_id in self._by_project:
        candidates = self._by_project[project_id]
    elif project_id is None:
        candidates = list(self._event_log)
    else:
        candidates = []

    filtered = [
        e for e in candidates
        if e.sequence > since_sequence
        and (topic_pattern is None or TopicMatcher.matches(topic_pattern, e.topic))
        and (source is None or e.source == source)
        and (since_time is None or e.timestamp >= since_time)
        and (until_time is None or e.timestamp <= until_time)
        and (search_text is None or search_text.lower() in str(e.data).lower())
    ]

    total = len(filtered)
    paginated = filtered[offset:offset + limit]
    return paginated, total
```

#### A.4. `get_event(event_id)` — lookup por ID

```python
def get_event(self, event_id: str) -> Event | None:
    return self._by_id.get(event_id)
```

#### A.5. `get_topic_distribution(project_id)`

```python
def get_topic_distribution(self, project_id: str) -> dict[str, int]:
    dist: dict[str, int] = {}
    for e in self._by_project.get(project_id, []):
        dist[e.topic] = dist.get(e.topic, 0) + 1
    return dist
```

#### A.6. `get_timeline(project_id, granularity)`

```python
def get_timeline(self, project_id: str, granularity: str = "1m") -> list[dict]:
    """Bucket events into time windows. Granularity: 1s, 1m, 1h."""
    from collections import defaultdict
    buckets: dict[int, int] = defaultdict(int)
    window = {"1s": 1, "1m": 60, "1h": 3600}.get(granularity, 60)
    for e in self._by_project.get(project_id, []):
        bucket = int(e.timestamp / window) * window
        buckets[bucket] += 1
    return sorted(
        [{"time": t, "count": c} for t, c in buckets.items()],
        key=lambda x: x["time"],
    )
```

#### A.7. `get_topics()` y `get_sources()`

```python
def get_topics(self) -> list[dict]:
    topics: dict[str, dict] = {}
    for e in self._event_log:
        if e.topic not in topics:
            topics[e.topic] = {"topic": e.topic, "count": 0, "last_seen": 0.0}
        topics[e.topic]["count"] += 1
        if e.timestamp > topics[e.topic]["last_seen"]:
            topics[e.topic]["last_seen"] = e.timestamp
    return sorted(topics.values(), key=lambda x: x["count"], reverse=True)

def get_sources(self) -> list[dict]:
    sources: dict[str, dict] = {}
    for e in self._event_log:
        if e.source not in sources:
            sources[e.source] = {"source": e.source, "count": 0, "topics": set()}
        sources[e.source]["count"] += 1
        sources[e.source]["topics"].add(e.topic)
    result = []
    for src, data in sources.items():
        result.append({"source": src, "count": data["count"], "topics": sorted(data["topics"])})
    return sorted(result, key=lambda x: x["count"], reverse=True)
```

#### A.8. `get_stats()`

```python
def get_stats(self) -> dict:
    return {
        "total_events": len(self._event_log),
        "total_projects": len(self._by_project),
        "capacity": self._max_log_size,
        "usage_pct": round(len(self._event_log) / self._max_log_size * 100, 1),
        "unique_sources": len({e.source for e in self._event_log}),
        "unique_topics": len({e.topic for e in self._event_log}),
    }
```

#### A.9. `get_subscribers()`

```python
def get_subscribers(self) -> list[dict]:
    subs: list[dict] = []
    # Exact subscribers from inner bus
    if hasattr(self._bus, '_subscriptions'):
        for topic, handlers in self._bus._subscriptions.items():
            for h in handlers:
                subs.append({
                    "pattern": topic,
                    "handler": getattr(h, "__name__", str(h)),
                    "type": "exact",
                })
    # Wildcard subscribers
    for pattern, handler in self._wildcard_handlers:
        subs.append({
            "pattern": pattern,
            "handler": getattr(handler, "__name__", str(handler)),
            "type": "wildcard",
        })
    return subs
```

#### A.10. Limpiar indices en `clear()`

```python
def clear(self) -> None:
    self._bus.clear()
    self._wildcard_handlers.clear()
    self._event_log.clear()
    self._by_project.clear()
    self._by_id.clear()
    self._sequences.clear()
```

#### A.11. SSE callbacks en `__init__`

```python
self._sse_callbacks: dict[str, list[Callable[[Event], None]]] = {}
```

#### A.12. `register_sse_callback()` / `unregister_sse_callback()`

```python
def register_sse_callback(self, project_id: str, callback: Callable[[Event], None]) -> None:
    self._sse_callbacks.setdefault(project_id, []).append(callback)

def unregister_sse_callback(self, project_id: str, callback: Callable[[Event], None]) -> None:
    cbs = self._sse_callbacks.get(project_id, [])
    if callback in cbs:
        cbs.remove(callback)
```

#### A.13. Invocar callbacks en `publish()` (al final, antes del await)

```python
for cb in self._sse_callbacks.get(event.project_id, []):
    cb(event)
for cb in self._sse_callbacks.get("_all", []):
    cb(event)
```

### Tests nuevos: `tests/test_event_bus_query.py`

| Test | Descripcion |
|------|-------------|
| `test_query_events_by_project` | Filtro basico por project_id |
| `test_query_events_by_topic_pattern` | Wildcard topic filter |
| `test_query_events_by_source` | Filtro source exacto |
| `test_query_events_by_time_range` | since_time + until_time |
| `test_query_events_search_text` | Busqueda en data |
| `test_query_events_pagination` | offset + limit |
| `test_query_events_total_count` | total != len(paginated) |
| `test_get_event_by_id` | Lookup individual |
| `test_get_topic_distribution` | Conteo por topic |
| `test_get_timeline` | Buckets temporales |
| `test_get_topics` | Lista de topics unicos |
| `test_get_sources` | Lista de sources unicos |
| `test_get_stats` | Metricas de salud |
| `test_get_subscribers` | Introspeccion de handlers |
| `test_sse_callback` | Callback invocado en publish |
| `test_sse_callback_unregister` | Callback removido correctamente |
| `test_indices_consistent_on_overflow` | Indices sincronizados con FIFO |

**Total tests nuevos Fase A: ~17**
**Regresiones esperadas: 0** (no se altera API publica existente)

---

## Fase B (API) — Dia 2: Endpoints Dashboard

### Archivo: `dashboard/service.py`

Agregar metodos a `SdlcDashboardService`:

#### B.1. `query_events()`

```python
def query_events(
    self,
    project_id: str | None = None,
    topic: str | None = None,
    source: str | None = None,
    since_time: float | None = None,
    until_time: float | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, object]:
    events, total = self._bus.query_events(
        project_id=project_id,
        topic_pattern=topic,
        source=source,
        since_time=since_time,
        until_time=until_time,
        search_text=search,
        limit=limit,
        offset=offset,
    )
    return {
        "events": [self._serialize_event(e) for e in events],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
```

#### B.2. Metodos adicionales

```python
def get_event_detail(self, event_id: str) -> dict[str, object] | None: ...
def get_event_distribution(self, project_id: str) -> dict[str, object]: ...
def get_event_timeline(self, project_id: str, granularity: str = "1m") -> dict[str, object]: ...
def get_topics(self) -> dict[str, object]: ...
def get_sources(self) -> dict[str, object]: ...
def get_subscriptions(self) -> dict[str, object]: ...
def get_metrics(self) -> dict[str, object]: ...
```

Cada metodo serializa a dict plano (JSON-safe) y delega en el bus.

#### B.3. Helper `_serialize_event()`

```python
@staticmethod
def _serialize_event(e: Event) -> dict[str, object]:
    return {
        "id": e.id,
        "sequence": e.sequence,
        "topic": e.topic,
        "source": e.source,
        "project_id": e.project_id,
        "timestamp": e.timestamp,
        "data": e.data,
    }
```

### Archivo: `dashboard/app.py`

Agregar rutas a `do_GET()`:

| Ruta | Metodo service | Parseo params |
|------|---------------|---------------|
| `GET /api/events` (extendido) | `service.query_events()` | `project`, `topic`, `source`, `since_time`, `until_time`, `search`, `limit`, `offset` |
| `GET /api/events/:id` | `service.get_event_detail()` | Path param `id` |
| `GET /api/events/distribution` | `service.get_event_distribution()` | `project` |
| `GET /api/events/timeline` | `service.get_event_timeline()` | `project`, `granularity` |
| `GET /api/topics` | `service.get_topics()` | — |
| `GET /api/sources` | `service.get_sources()` | — |
| `GET /api/subscriptions` | `service.get_subscriptions()` | — |
| `GET /api/health/metrics` | `service.get_metrics()` | — |
| `GET /api/events/live` | SSE directo | `project` |

#### B.4. SSE endpoint

```python
elif path == "/api/events/live":
    pid = params.get("project", [""])[0]
    if not pid:
        self._send_json({"error": "Missing project parameter"}, 400)
        return
    self.send_response(200)
    self.send_header("Content-Type", "text/event-stream")
    self.send_header("Cache-Control", "no-cache")
    self.send_header("Connection", "keep-alive")
    self.end_headers()

    def on_event(event: Event) -> None:
        try:
            data = json.dumps({
                "sequence": event.sequence,
                "topic": event.topic,
                "source": event.source,
                "timestamp": event.timestamp,
                "data": event.data,
            }, ensure_ascii=False, default=str)
            self.wfile.write(f"data: {data}\n\n".encode("utf-8"))
            self.wfile.flush()
        except OSError:
            pass  # Client disconnected

    bus.register_sse_callback(pid if pid != "_all" else "_all", on_event)

    # Keep connection alive
    try:
        while not self.server._shutdown_request:
            self.wfile.write(": heartbeat\n\n".encode("utf-8"))
            time.sleep(15)
    except (BrokenPipeError, OSError):
        pass
    finally:
        bus.unregister_sse_callback(pid if pid != "_all" else "_all", on_event)
```

### Tests nuevos: `tests/test_dashboard_api_v2.py`

| Test | Descripcion |
|------|-------------|
| `test_events_query_with_filters` | Query con topic + source |
| `test_events_query_pagination` | offset + limit |
| `test_event_detail_by_id` | GET /api/events/:id |
| `test_event_distribution` | GET /api/events/distribution |
| `test_event_timeline` | GET /api/events/timeline |
| `test_topics_endpoint` | GET /api/topics |
| `test_sources_endpoint` | GET /api/sources |
| `test_subscriptions_endpoint` | GET /api/subscriptions |
| `test_metrics_endpoint` | GET /api/health/metrics |

**Total tests nuevos Fase B: ~9**
**Total acumulado:** ~164

---

## Fase C (Frontend) — Dia 3: Visualizaciones

### Archivo: `dashboard/static/dashboard.js`

#### C.1. Bar chart de distribucion (Canvas API)

Nueva funcion `renderDistributionChart(canvasId, data)`:

```javascript
function renderDistributionChart(canvasId, distribution) {
    const canvas = document.getElementById(canvasId);
    const ctx = canvas.getContext('2d');
    const entries = Object.entries(distribution);
    const maxVal = Math.max(...Object.values(distribution), 1);
    const barWidth = canvas.width / (entries.length * 2);
    const padding = 40; // left margin for labels

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    entries.forEach(([topic, count], i) => {
        const x = padding + i * barWidth * 2 + barWidth * 0.3;
        const h = (count / maxVal) * (canvas.height - 30);
        const y = canvas.height - h - 10;
        ctx.fillStyle = '#4a9eff';
        ctx.fillRect(x, y, barWidth * 0.7, h);
        ctx.fillStyle = '#ccc';
        ctx.font = '10px monospace';
        const label = topic.length > 12 ? topic.substring(0, 10) + '..' : topic;
        ctx.fillText(label, x - 5, canvas.height - 2);
        ctx.fillText(count, x + 2, y - 4);
    });
}
```

Invocar en `loadDashboard()` y `showProject()`.

#### C.2. Timeline SVG

Nueva funcion `renderTimelineSVG(containerId, buckets)`:

```javascript
function renderTimelineSVG(containerId, buckets) {
    const svg = document.getElementById(containerId);
    const W = svg.clientWidth || 600;
    const H = 120;
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    const maxC = Math.max(...buckets.map(b => b.count), 1);
    const step = W / Math.max(buckets.length, 1);

    // Line
    const points = buckets.map((b, i) => {
        const x = i * step + step / 2;
        const y = H - 20 - (b.count / maxC) * (H - 40);
        return `${x},${y}`;
    }).join(' ');
    svg.innerHTML = `<polyline points="${points}" fill="none" stroke="#4a9eff" stroke-width="2"/>`;
}
```

#### C.3. Explorer de eventos con filtros

Agregar a `index.html` un modal/seccion:
- Inputs: topic, source, search text, date range
- Tabla de resultados paginada
- Click en fila abre detalle del evento (JSON raw)

#### C.4. Event detail modal

```javascript
function showEventDetail(eventId) {
    fetch(`/api/events/${eventId}`)
        .then(r => r.json())
        .then(data => {
            document.getElementById('event-detail-json').textContent =
                JSON.stringify(data, null, 2);
            document.getElementById('event-modal').style.display = 'block';
        });
}
```

#### C.5. Live indicator + SSE consumer

```javascript
let eventSource = null;

function startLiveStream(projectId) {
    if (eventSource) eventSource.close();
    document.getElementById('live-badge').style.display = 'inline-block';
    eventSource = new EventSource(`/api/events/live?project=${projectId}`);
    eventSource.onmessage = (e) => {
        const event = JSON.parse(e.data);
        // Actualizar contador
        const counter = document.getElementById('live-counter');
        counter.textContent = parseInt(counter.textContent || '0') + 1;
        // Opcional: agregar fila a tabla de eventos
    };
}

function stopLiveStream() {
    if (eventSource) eventSource.close();
    eventSource = null;
    document.getElementById('live-badge').style.display = 'none';
}
```

### Archivo: `dashboard/static/index.html`

Agregar:
- Canvas para bar chart `<canvas id="distribution-chart" width="400" height="200">`
- SVG para timeline `<svg id="timeline-svg"></svg>`
- Modal de detalle de evento `<div id="event-modal">...<pre id="event-detail-json"></pre>...</div>`
- Live badge `<span id="live-badge" class="live-badge">LIVE <span id="live-counter">0</span></span>`
- Filtros de explorador `<div id="event-explorer">...<input name="topic">...<input name="source">...<button>Buscar</button></div>`

Actualizar el flujo `loadDashboard()` para:
- Cargar distribucion `/api/events/distribution` y renderizar bar chart
- Cargar topics `/api/topics` y sources `/api/sources`
- Cargar metricas `/api/health/metrics` y actualizar KPI row

### Tests: `tests/test_dashboard_static.py`

| Test | Descripcion |
|------|-------------|
| `test_html_has_canvas` | El HTML contiene canvas#distribution-chart |
| `test_html_has_timeline_svg` | El HTML contiene svg#timeline-svg |
| `test_html_has_event_modal` | El HTML contiene div#event-modal |
| `test_html_has_live_badge` | El HTML contiene span#live-badge |

**Total tests nuevos Fase C: ~4**
**Total acumulado:** ~168

---

## Resumen de Archivos Modificados

| Archivo | Cambio | LOC estimado |
|---------|--------|-------------|
| `core/event_bus.py` | Indices, query_events, agregaciones, SSE callbacks | ~120 |
| `dashboard/service.py` | 9 metodos nuevos + helper | ~100 |
| `dashboard/app.py` | 9 rutas nuevas + SSE endpoint | ~100 |
| `dashboard/static/index.html` | Canvas, SVG, modal, filtros, live badge | ~60 |
| `dashboard/static/dashboard.js` | Bar chart, timeline, explorer, SSE consumer | ~200 |
| `dashboard/static/dashboard.css` | Estilos para nuevas secciones | ~40 |
| `tests/test_event_bus_query.py` | 17 tests nuevos | ~250 |
| `tests/test_dashboard_api_v2.py` | 9 tests nuevos | ~150 |
| `tests/test_dashboard_static.py` | 4 tests nuevos | ~60 |

**Total LOC:** ~1080

---

## Verificacion

Despues de cada fase:

```bash
# Fase A
python -m pytest tests/test_event_bus_query.py tests/test_event_bus.py -v -o "addopts="
ruff check core/event_bus.py
ruff format core/event_bus.py

# Fase B
python -m pytest tests/test_dashboard_api_v2.py tests/test_dashboard_api.py -v -o "addopts="
ruff check dashboard/service.py dashboard/app.py
ruff format dashboard/service.py dashboard/app.py

# Fase C
python -m pytest tests/ -v -o "addopts="
ruff check .
ruff format .
```

---

## Dependencias entre Fases

```
Fase A (Core)  ──>  Fase B (API)  ──>  Fase C (Frontend)
     |                    |
     v                    v
  Tests A             Tests B
     |
     v
  SSE base en event_bus.py (A.12-A.13)
     |
     v
  SSE endpoint en app.py (B.4) ──> SSE consumer en JS (C.5)
```

Fase A es requisito de Fase B. Fase B es requisito de Fase C. No hay paralelismo posible.

---

## Riesgos de esta Fase

| Riesgo | Impacto | Mitigacion |
|--------|---------|------------|
| Indices fuera de sync en FIFO overflow | Perdida de eventos en query | Log de warning en pop; test de consistencia (A.10) |
| SSE bloquea hilo del HTTPServer | Dashboard lento | Timeout de heartbeat alto (15s); cliente SSE en hilo separado |
| Canvas charts en browsers antiguos | No se renderizan | Degradacion elegante: fallback a tabla de datos |
| `_bus._subscriptions` es privado y puede no existir | `get_subscribers()` falla | Try/except con fallback a lista vacia |
