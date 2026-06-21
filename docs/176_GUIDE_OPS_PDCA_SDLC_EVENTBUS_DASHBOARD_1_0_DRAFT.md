---
id: 176
area: ops
type: GUIDE
module: PDCA_SDLC_EVENTBUS_DASHBOARD
version: 1.0
status: ACTIVE
tags:
  - guide
  - runbook
  - pdca-sdlc
  - event-bus
  - dashboard
  - operations
summary: "Runbook operativo del modulo PDCA-sdlc: EventBus asincrono, dashboard HTTP zero-dependency, API REST, frontend vanilla JS, y procedimientos de operacion diaria."
keywords:
  - runbook
  - pdca-sdlc
  - event-bus
  - dashboard
  - sse
  - operacion
  - troubleshooting
  - metricas
  - api
changelog:
  - version: 1.0
    date: 2026-06-20
    author: system
    changes:
      - "Creacion del runbook operativo PDCA-sdlc EventBus + Dashboard"
---

# Runbook Operativo: PDCA-sdlc EventBus + Dashboard

**Version del modulo:** 0.1.0
**Fuente:** `compiler-bot/pdca_sdlc/`
**Dashboard port default:** 8764
**Tests:** 224 PASS (pytest)

---

## 1. Resumen del Sistema

PDCA-sdlc es un modulo del RECPL Compiler Bot que implementa un bus de
eventos asincrono sobre el ciclo de vida ISO 12207. Los componentes
principales son:

| Componente | Funcion |
|------------|---------|
| `AsyncEventBus` | Bus de eventos con topicos jerarquicos, wildcards, query engine, agregaciones, SSE callbacks |
| `SdlcDashboardService` | Fachada read-only sobre EventBus + KnowledgeGraph + CapabilityRegistry |
| `DashboardHTTPHandler` | Servidor HTTP stdlib con 15 endpoints REST + SSE live + frontend estatico |
| Frontend | SPA vanilla JS con Canvas bar chart, SVG timeline, explorador de eventos, modal de detalle, live streaming |

### 1.1 Flujo tipico

```
main.py → crea AsyncEventBus, KnowledgeGraph, agents
         → publica event: project.initialized
         → agents reaccionan (RequirementsAnalyst, Adaptation, Coder)
         → publican eventos de requerimientos, artefactos, trazas
         → dashboard (opcional) expone todo via HTTP + SSE
```

---

## 2. Arquitectura

### 2.1 C4 — Contexto

```
┌──────────────┐    HTTP/SSE    ┌────────────────────┐
│   Browser    │ ←──────────── → │  Dashboard Server  │
│ (vanilla JS) │                │  (stdlib http)     │
└──────────────┘                └────────┬───────────┘
                                         │
                              ┌──────────┴───────────┐
                              │  SdlcDashboardService │
                              │  (read-only facade)   │
                              └──────────┬───────────┘
                                         │
               ┌─────────────────────────┼──────────────────────┐
               │                         │                      │
     ┌─────────┴──────────┐   ┌──────────┴──────────┐   ┌──────┴───────────┐
     │   AsyncEventBus    │   │   KnowledgeGraph    │   │CapabilityRegistry│
     │ (topic pub/sub,    │   │ (nodes, edges,      │   │(agent lookup)    │
     │  query, SSE, log)  │   │  trace BFS)         │   │                  │
     └────────────────────┘   └─────────────────────┘   └──────────────────┘
```

### 2.2 Endpoints del Dashboard

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/api/health` | Health check basico |
| GET | `/api/health/metrics` | Metricas extendidas del bus |
| GET | `/api/projects` | Lista de proyectos con resumen |
| GET | `/api/projects/<id>` | Detalle completo de proyecto |
| GET | `/api/projects/<id>/trace` | Traza BFS desde el goal |
| GET | `/api/agents` | Agentes registrados |
| GET | `/api/events` | Query filtrado de eventos |
| GET | `/api/events/<id>` | Detalle de evento individual |
| GET | `/api/events/distribution` | Distribucion por topico |
| GET | `/api/events/timeline` | Timeline por ventanas de tiempo |
| GET | `/api/events/live` | SSE streaming de eventos en vivo |
| GET | `/api/topics` | Topicos unicos con metadata |
| GET | `/api/sources` | Fuentes unicas con metadata |
| GET | `/api/subscriptions` | Subscriptores registrados |
| GET | `/` | Frontend SPA (index.html) |

---

## 3. Instalacion

### 3.1 Requisitos

- Python >= 3.11
- Dependencias: `pydantic>=2.0`, `networkx>=3.0`, `pyyaml>=6.0`
- Sin dependencias externas para el dashboard (stdlib unicamente)

### 3.2 Instalacion

```sh
# Desde la raiz del repo (modo editable)
pip install -e compiler-bot/pdca_sdlc/

# Verificar
python -m pdca_sdlc.main --help
```

### 3.3 Verificacion rapida

```sh
# Smoke test: ejecutar pipeline sin dashboard
python -m pdca_sdlc.main "crear sistema de autenticacion" -v

# Smoke test: con dashboard
python -m pdca_sdlc.main "crear sistema de autenticacion" --dashboard --port 8764
# Abrir http://127.0.0.1:8764
```

---

## 4. Operacion

### 4.1 CLI — Modo pipeline

```sh
# Ejecucion basica
python -m pdca_sdlc.main "crear modulo de pagos"

# Con proyecto ID explicito
python -m pdca_sdlc.main "crear modulo de pagos" --project-id p-042

# Verbose (DEBUG logging)
python -m pdca_sdlc.main "crear modulo de pagos" -v
```

### 4.2 CLI — Con dashboard

```sh
# Puerto custom
python -m pdca_sdlc.main "crear modulo de pagos" --dashboard --port 9876

# Host custom
python -m pdca_sdlc.main "crear modulo de pagos" --dashboard --host 0.0.0.0
```

El dashboard arranca en un thread daemon y el proceso principal termina
tras 5 segundos de procesamiento asincrono. Para uso persistente, el
dashboard requiere mantener el proceso vivo.

### 4.3 Dashboard API — Consultas utiles

```sh
# Health
curl http://127.0.0.1:8764/api/health

# Metricas
curl http://127.0.0.1:8764/api/health/metrics

# Proyectos
curl http://127.0.0.1:8764/api/projects

# Eventos de un proyecto (ultimos 20)
curl "http://127.0.0.1:8764/api/events?project=p-001"

# Eventos con filtros
curl "http://127.0.0.1:8764/api/events?project=p-001&topic=requirement&limit=5&offset=10"

# Distribucion por topico
curl "http://127.0.0.1:8764/api/events/distribution?project=p-001"

# Timeline (granularidad: 1s, 1m, 1h)
curl "http://127.0.0.1:8764/api/events/timeline?project=p-001&granularity=1m"

# Topicos
curl http://127.0.0.1:8764/api/topics

# Fuentes
curl http://127.0.0.1:8764/api/sources

# Subscriptores
curl http://127.0.0.1:8764/api/subscriptions
```

### 4.4 SSE — Streaming en vivo

```sh
curl -N "http://127.0.0.1:8764/api/events/live?project=p-001"
```

El servidor emite eventos SSE con formato:
```
data: {"topic":"requirement.created","project_id":"p-001","sequence":5,...}

```

La conexion SSE usa `register_sse_callback()` y `unregister_sse_callback()`
del EventBus. Timeout del handler: 30s por escritura.

---

## 5. Frontend

### 5.1 Pagina principal

El dashboard SPA se sirve en `GET /` y contiene:

| Seccion | Descripcion |
|---------|-------------|
| KPI cards | Total eventos, errores, topicos, fuentes |
| Distribucion | Canvas bar chart por topico |
| Timeline | SVG polyline de eventos en el tiempo |
| Explorador | Busqueda con filtros (proyecto, topico, fuente, texto) |
| Proyectos | Tabla de proyectos con detalle expandible |
| Live badge | Indicador de conexion SSE con animacion pulse |

### 5.2 Archivos estaticos

| Archivo | Tamano | Contenido |
|---------|--------|-----------|
| `dashboard/static/index.html` | ~4.3KB | SPA con todas las secciones |
| `dashboard/static/dashboard.js` | ~9KB | Logica JS: charts, SVG, explorador, SSE, modal |
| `dashboard/static/dashboard.css` | ~7KB | Dark theme, grid responsive, animaciones |

Sin frameworks externos. Sin npm. Sin build step.

---

## 6. Tests

### 6.1 Ejecutar tests

```sh
cd compiler-bot/pdca_sdlc

# Todos los tests
python -m pytest tests/ -v

# Por archivo
python -m pytest tests/test_event_bus_query.py -v
python -m pytest tests/test_dashboard_api_v2.py -v
python -m pytest tests/test_dashboard_static.py -v
```

### 6.2 Distribucion de tests (224 total)

| Archivo | Tests | Que cubre |
|---------|-------|-----------|
| `test_event_bus_query.py` | 38 | Query engine, filtros, paginacion, distribucion, timeline, stats |
| `test_dashboard_static.py` | 26 | Servicio estaticos, MIME types, directory traversal |
| `test_dashboard_api_v2.py` | 22 | API v2: events query, topics, sources, subscriptions, SSE |
| `test_event_schemas.py` | 20 | Schemas de eventos, serializacion |
| `test_coder_agent.py` | 19 | Agente coder, pipeline, generacion de artefactos |
| `test_event_bus.py` | 19 | Core: publish, subscribe, wildcards, replay |
| `test_knowledge_graph.py` | 15 | KG: nodos, aristas, CRUD, trace, type enforcement |
| `test_dashboard_api.py` | 12 | API v1: health, projects, agents, events |
| `test_requirements_analyst.py` | 12 | Decomposicion de requerimientos |
| `test_capability_registry.py` | 10 | Registro y consulta de capacidades |
| `test_adaptation_agent.py` | 10 | Mapeo a procesos ISO 12207 |
| `test_base_agent.py` | 8 | Ciclo de vida base, context, event hooks |
| `test_llm_client.py` | 7 | LLM client mock/fallback |
| `test_integration_f1.py` | 6 | Integracion end-to-end F1 |

---

## 7. Monitoreo

### 7.1 Health check

```sh
curl http://127.0.0.1:8764/api/health
# {"status":"ok","timestamp":1712345678.901}
```

### 7.2 Metricas del bus

```sh
curl http://127.0.0.1:8764/api/health/metrics
# {
#   "total_events": 142,
#   "total_projects": 1,
#   "capacity": 10000,
#   "usage_pct": 1.42,
#   "unique_sources": 5,
#   "unique_topics": 12,
#   "active_subscriptions": 8,
#   "sse_connections": 1
# }
```

Indicadores clave:
- `usage_pct`: porcentaje del log interno usado (max 10000 eventos)
- `active_subscriptions`: numero de subscriptores registrados
- `sse_connections`: conexiones SSE activas en este momento

### 7.3 Log del bus

El `AsyncEventBus` mantiene un log circular FIFO de hasta 10000 eventos.
Cuando se alcanza el limite, los eventos mas antiguos se descartan.
Los indices `_by_project` y `_by_id` se limpian en el overflow.

Configurable via:
```python
bus.set_max_log_size(50000)  # max 50000 eventos
```

---

## 8. Troubleshooting

### 8.1 El dashboard no arranca

```
Error: Address already in use
```
**Causa:** El puerto 8764 ya esta ocupado.
**Solucion:** Usar `--port` con un puerto alternativo.

### 8.2 No hay eventos en el dashboard

**Causa:** El pipeline no ha publicado eventos, o el project ID no coincide.
**Verificacion:**

```sh
curl http://127.0.0.1:8764/api/events
# Si events=[]: el bus no recibio eventos
# Si projects=[]: no hay proyectos creados

curl http://127.0.0.1:8764/api/projects
# Verificar project IDs disponibles
```

### 8.3 El SSE no recibe eventos en vivo

**Causa:** La conexion SSE se abre antes de que se publiquen eventos,
o el proyecto no coincide con el filtro.
**Verificacion:**

```sh
# Terminal 1: dashboard
python -m pdca_sdlc.main "test" --dashboard

# Terminal 2: SSE consumer
curl -N "http://127.0.0.1:8764/api/events/live?project=p-001"
```

Si no se reciben datos, verificar que el project ID del SSE coincide
con el project ID que usa el pipeline (default: `p-001`).

### 8.4 Tests fallan

```sh
# Ejecutar con traceback completo
python -m pytest tests/ -v --tb=long

# Test especifico
python -m pytest tests/test_event_bus_query.py::test_query_events_filtered -v --tb=long
```

### 8.5 Error de importacion

```
ModuleNotFoundError: No module named 'agentic_pipeline'
```

**Causa:** pdca_sdlc depende de `agentic_pipeline` (mismo repo).
**Solucion:** Instalar ambos modulos en modo editable:

```sh
pip install -e compiler-bot/agentic_pipeline/
pip install -e compiler-bot/pdca_sdlc/
```

---

## 9. Mantenimiento

### 9.1 Lint y formato

```sh
cd compiler-bot/pdca_sdlc
ruff check .
ruff format .
```

### 9.2 Agregar un nuevo endpoint

1. Agregar metodo en `dashboard/service.py` (SdlcDashboardService)
2. Agregar ruta + handler en `dashboard/app.py` (DashboardHTTPHandler)
3. Agregar tests en `tests/test_dashboard_api_v2.py`
4. Actualizar frontend si aplica (`dashboard/static/dashboard.js`)
5. Ejecutar tests y lint

### 9.3 Cambiar el tamano maximo del log

Editar `core/event_bus.py`:

```python
# Default: 10000
self._max_log_size = 10000
```

O via metodo publico:

```python
bus.set_max_log_size(50000)
```

### 9.4 Limpiar estado

```python
# Reiniciar bus (limpia eventos, subscriptores, SSE callbacks)
bus.clear()
```

### 9.5 Versionado

El modulo sigue semver. La version actual (`0.1.0`) se define en
`pyproject.toml`. Para releases:

1. Actualizar `version` en `pyproject.toml`
2. Anadir entrada en `CHANGELOG.md` del proyecto
3. Actualizar el changelog en el frontmatter de los docs relevantes

---

## 10. Referencia rapida

### 10.1 Comandos esenciales

```sh
# Arrancar
python -m pdca_sdlc.main "descripcion" --dashboard

# Tests
python -m pytest tests/ -v

# Lint
ruff check .

# Formato
ruff format .
```

### 10.2 Parametros de query de eventos

| Parametro | Tipo | Default | Descripcion |
|-----------|------|---------|-------------|
| `project` | str | — | Filtrar por project ID |
| `topic` | str | — | Filtrar por topico (soporta `*` y `>`) |
| `source` | str | — | Filtrar por fuente |
| `search` | str | — | Busqueda de texto en datos del evento |
| `since_time` | float | — | Timestamp UNIX desde |
| `until_time` | float | — | Timestamp UNIX hasta |
| `limit` | int | 20 | Max resultados (max 100) |
| `offset` | int | 0 | Paginacion |

### 10.3 Granularidad de timeline

| Valor | Ventana |
|-------|---------|
| `1s` | 1 segundo |
| `1m` | 1 minuto (default) |
| `1h` | 1 hora |

### 10.4 Topic hierarchy

Los topicos usan notacion jerarquica con puntos:

```
project.initialized
requirement.created
requirement.updated
artifact.generated
agent.started
agent.completed
```

Wildcards:
- `*` — un nivel: `requirement.*` matchea `requirement.created`
- `>` — subarbol: `requirement.>` matchea `requirement.created`, `requirement.updated`, etc.

---

## 11. Riesgos y limitaciones

| Riesgo | Impacto | Mitigacion |
|--------|---------|------------|
| Log circular FIFO de 10000 eventos | Perdida de eventos historicos | Monitorear `usage_pct`. Aumentar con `set_max_log_size()` |
| Dashboard en thread daemon | Muere al terminar el proceso principal | Mantener proceso vivo |
| Sin persistencia en disco | Perdida de eventos al reiniciar | Integrar con base de datos para persistencia (futuro) |
| Sin autenticacion en API | Acceso no autorizado al dashboard | Usar en localhost o detras de proxy con auth |
| SSE sin reconexion automatica | El cliente pierde eventos si se cae la conexion | El frontend muestra estado del SSE; no reconecta automaticamente |
