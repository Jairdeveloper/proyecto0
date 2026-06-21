---
id: "P17"
area: dev
type: plan
module: pdca_sdlc
version: "1.0"
status: IMPLEMENTED
tags: ["plan", "dashboard", "sdlc-visualization", "real-time", "zero-dependency"]
summary: "Plan de implementacion y ejecucion del dashboard PDCA-sdlc para visualizacion del pipeline SDLC ISO 12207 en tiempo real. 0 dependencias externas."
changelog:
  - version: "1.0"
    date: "2026-06-20"
    author: "Sistema"
    description: "Version inicial — plan de implementacion del dashboard"
---

# Plan de Implementacion — Dashboard PDCA-sdlc

> **Repo:** Proyecto0  
> **Modulo:** `compiler-bot/pdca_sdlc/dashboard/`  
> **Base:** Fase 1 de PDCA-sdlc (126 tests, KnowledgeGraph, EventBus, 3 agentes)  
> **Inspiracion:** `agentic_pipeline/dashboard/` (mismo patron arquitectonico)

---

## 1. Resumen Ejecutivo

Dashboard web liviano (0 dependencias externas, stdlib Python puro) para visualizar en tiempo real el estado del pipeline SDLC ISO 12207. Reutiliza el patron arquitectonico del dashboard RECPL existente (`http.server` + vanilla JS), pero con capa de servicio y vistas adaptadas al modelo de datos de PDCA-sdlc (KnowledgeGraph, EventBus, CapabilityRegistry).

**Total estimado:** ~530 LOC nuevos, 3 dias de ejecucion.

---

## 2. Arquitectura

```
compiler-bot/pdca_sdlc/
├── main.py                       ← Entrypoint CLI (flag --dashboard, --port)
└── dashboard/                    ← NUEVO
    ├── __init__.py                ← Package init, exporta SdlcDashboardService
    ├── app.py                     ← HTTP server (http.server.BaseHTTPRequestHandler)
    ├── service.py                 ← Read model sobre KG + EventBus + Registry
    └── static/
        ├── index.html             ← SPA shell
        ├── dashboard.js            ← Fetch, render, interactividad (vanilla JS)
        └── dashboard.css           ← Dark theme (consistente con RECPL)
```

### Capas

```
[Frontend Vanilla JS]  ←HTTP JSON→  [service.py]  ←Python directo→  [KnowledgeGraph]
                                       (read-only)                    [AsyncEventBus]
                                                                      [CapabilityRegistry]
```

### Principios de diseno

1. **Zero-dependency**: Solo stdlib Python (http.server, json, etc.). No Flask, no React, no npm.
2. **Read-only**: El dashboard solo consulta el estado. No escribe al KG ni al bus.
3. **Mismo origen**: El servidor HTTP sirve el HTML estatico y las APIs REST. Sin CORS.
4. **Consistencia visual**: Mismo dark theme que el dashboard RECPL existente.
5. **Responsive**: Tablas y KPIs adaptables a pantallas pequenas.

---

## 3. API REST

### 3.1 GET /api/health

```
Response 200:
{"status": "ok", "timestamp": 1234567890.0}
```

### 3.2 GET /api/projects

Lista de proyectos en el Knowledge Graph.

```
Response 200:
{
  "projects": [
    {
      "project_id": "p-001",
      "complexity": "simple",
      "lifecycle": "fast_track",
      "requirement_count": 3,
      "artifact_count": 2,
      "event_count": 5
    }
  ]
}
```

**Implementacion:** Consulta nodos `goal` via `kg.query(node_type=NodeType.goal)`. Para cada uno, cuenta requisitos y artifacts correlacionados.

### 3.3 GET /api/projects/{id}

Estado completo de un proyecto.

```
Response 200:
{
  "project_id": "p-001",
  "goal": {
    "complexity": "simple",
    "lifecycle": "fast_track",
    "processes": ["6.1", "6.3"],
    "activities": ["Requirements Elicitation", "Software Implementation", "Unit Testing"],
    "effort_estimate": {"estimated_hours": 24, "estimated_days": 4}
  },
  "requirements": [
    {"id": "r-001", "text": "Crear API de productos", "type": "functional", "priority": "high"}
  ],
  "artifacts": [
    {"target": "nestjs", "status": "committed", "files": ["output/p-001/nestjs/products.controller.ts"]}
  ],
  "event_count": 5
}

Response 404:
{"error": "Project not found: ghost"}
```

### 3.4 GET /api/projects/{id}/trace

Cadena de trazabilidad BFS desde el goal.

```
Response 200:
{
  "trace": [
    {"id": "goal-p-001", "type": "goal", "properties": {"complexity": "simple"}},
    {"id": "r-001", "type": "requirement", "properties": {"text": "Crear API de productos"}},
    {"id": "gen-p-001-nestjs", "type": "artifact", "properties": {"status": "committed", "target": "nestjs"}}
  ]
}
```

### 3.5 GET /api/agents

Agentes registrados y su estado.

```
Response 200:
{
  "agents": [
    {"agent_id": "adaptation-agent", "agent_name": "AdaptationAgent", "status": "active"},
    {"agent_id": "requirements-analyst", "agent_name": "RequirementsAnalystAgent", "status": "active"},
    {"agent_id": "coder-agent", "agent_name": "CoderAgent", "status": "active"}
  ],
  "total": 3
}
```

### 3.6 GET /api/events?project={id}&limit={N}

Eventos recientes de un proyecto.

```
Response 200:
{
  "events": [
    {"sequence": 1, "topic": "project.initialized", "source": "cli", "timestamp": 1234567890.0},
    {"sequence": 2, "topic": "adaptation.complete", "source": "adaptation-agent", "timestamp": 1234567891.0}
  ],
  "project_id": "p-001",
  "count": 2
}
```

**Default limit:** 20, max 100.

---

## 4. Frontend — Vistas

### 4.1 Vista Principal: Project Overview

```
┌─────────────────────────────────────────────────┐
│  PDCA-sdlc Dashboard                    [refresh]│
├──────────┬──────────┬──────────┬────────────────┤
│ Projects │ Agents   │ Events   │ Success Rate   │
│    2     │ 3 active │    12    │     100%       │
├──────────┴──────────┴──────────┴────────────────┤
│ Projects Table (click rows para detalle)        │
│ ┌────────┬──────────┬──────┬────────┬─────────┐ │
│ │ ID     │ Complex. │ Reqs │ Artts  │ Events  │ │
│ ├────────┼──────────┼──────┼────────┼─────────┤ │
│ │ p-001  │ simple   │ 3    │ 2      │ 5       │ │
│ │ p-002  │ complex  │ 5    │ 4      │ 8       │ │
│ └────────┴──────────┴──────┴────────┴─────────┘ │
└─────────────────────────────────────────────────┘
```

### 4.2 Vista Detalle: Project Detail (al hacer clic)

```
┌─────────────────────────────────────────────────┐
│ ← Projects  |  Proyecto: p-001                  │
├─────────────────────────────────────────────────┤
│ Goal: Sistema multi-tenant con microservicios    │
│ Complexity: complex | Lifecycle: agile           │
│ Esfuerzo: 72h / 12d | Actividades: 9             │
├─────────────────────────────────────────────────┤
│ Requirements (3)                                 │
│ ┌───────┬──────────────┬───────────┬──────────┐ │
│ │ ID    │ Text         │ Type      │ Priority │ │
│ ├───────┼──────────────┼───────────┼──────────┤ │
│ │ r-001 │ API prod     │ functional│ high     │ │
│ │ r-002 │ Modelo Usr   │ functional│ medium   │ │
│ │ r-003 │ Seguridad    │ non_func  │ high     │ │
│ └───────┴──────────────┴───────────┴──────────┘ │
├─────────────────────────────────────────────────┤
│ Trazabilidad (goal → requirements → artifacts)   │
│  goal-p-001                                     │
│    ├── r-001 → gen-p-001-nestjs [committed]     │
│    ├── r-002 → gen-p-001-prisma [committed]     │
│    └── r-003 → (sin artifact)                   │
├─────────────────────────────────────────────────┤
│ Artifacts (2)                                    │
│ ┌────────┬──────────┬──────────────────────────┐ │
│ │ Target │ Status   │ Files                    │ │
│ ├────────┼──────────┼──────────────────────────┤ │
│ │ nestjs │committed │ output/p-001/nestjs/...  │ │
│ │ prisma │committed │ output/p-001/prisma/...  │ │
│ └────────┴──────────┴──────────────────────────┘ │
├─────────────────────────────────────────────────┤
│ Eventos Recientes (5)                            │
│ ┌────┬──────────────┬────────────────┬─────────┐ │
│ │ #  │ Topic        │ Source         │ Time    │ │
│ ├────┼──────────────┼────────────────┼─────────┤ │
│ │ 1  │ project.init │ cli            │ 12:00:01│ │
│ │ 2  │ adaptation.c │ adaptation-ag  │ 12:00:02│ │
│ │ 3  │ requirement. │ req-analyst    │ 12:00:03│ │
│ │ 4  │ code.committ │ coder-agent    │ 12:00:04│ │
│ │ 5  │ code.committ │ coder-agent    │ 12:00:05│ │
│ └────┴──────────────┴────────────────┴─────────┘ │
└─────────────────────────────────────────────────┘
```

---

## 5. Archivos a Crear/Modificar

### 5.1 Archivos nuevos (6 archivos)

| Archivo | LOC est. | Proposito |
|---------|----------|-----------|
| `dashboard/__init__.py` | 3 | Package init, exporta `SdlcDashboardService` y `create_server` |
| `dashboard/app.py` | 110 | HTTP server con 6 rutas API + static serving |
| `dashboard/service.py` | 80 | Read model: consultas a KG, EventBus, Registry |
| `dashboard/static/index.html` | 60 | SPA shell: KPIs, tablas, detalle oculto |
| `dashboard/static/dashboard.js` | 180 | Logica frontend: fetch, render, eventos |
| `dashboard/static/dashboard.css` | 100 | Dark theme consistente con RECPL |
| **Total** | **~533** | |

### 5.2 Archivos a modificar (1 archivo)

| Archivo | Cambio |
|---------|--------|
| `main.py` | Agregar flags `--dashboard` y `--port`. Al activarse, inicia servidor HTTP tras el pipeline. |

### 5.3 Documentacion (1 archivo)

| Archivo | Proposito |
|---------|-----------|
| `docs/170_REP_DEV_PDCA_SDLC_DASHBOARD_1_0_DRAFT.md` | Reporte de ejecucion del dashboard |

---

## 6. Plan de Ejecucion (3 dias)

### Dia 1: Service Layer + HTTP Server

| Tarea | Archivo | Detalle | Criterio de exito |
|-------|---------|---------|-------------------|
| 1.1 | `dashboard/__init__.py` | Package init con `__all__` | `from pdca_sdlc.dashboard import ...` funciona |
| 1.2 | `dashboard/service.py` | Clase `SdlcDashboardService` con metodos: `get_health()`, `get_projects()`, `get_project(project_id)`, `get_trace(project_id)`, `get_agents()`, `get_events(project_id, limit)` | Test unitario de cada metodo con KG poblado |
| 1.3 | `dashboard/app.py` | Clase `DashboardHTTPHandler(BaseHTTPRequestHandler)` con rutas `/api/*`, MIME types, manejo de errores 404/500. Funcion `create_server(host, port, service)` y `run_server(host, port)`. | `curl http://127.0.0.1:8765/api/health` → `{"status": "ok"}` |
| 1.4 | `main.py` | Agregar argparse `--dashboard` (store_true) y `--port` (default 8765). Al activarse, lanza `run_server()` en segundo plano. | `python -m pdca_sdlc.main --dashboard "test"` arranca server |

### Dia 2: Frontend

| Tarea | Archivo | Detalle |
|-------|---------|---------|
| 2.1 | `static/index.html` | SPA shell con: KPI row (4 cards), projects table, detail view (hidden por defecto), loading states, empty states |
| 2.2 | `static/dashboard.css` | Dark theme nav, cards con borde izquierdo color, tablas con hover, sticky headers, responsive breakpoint 768px |
| 2.3 | `static/dashboard.js` | `loadDashboard()` → fetch `/api/projects` + `/api/agents` + `/api/events`, renderiza KPIs y tabla. `showProject(id)` → fetch `/api/projects/{id}` + `/api/projects/{id}/trace`, renderiza detalle. `showEvents(project_id)` → fetch `/api/events?project={id}`, renderiza tabla de eventos. Manejadores de error y loading. |

### Dia 3: Integracion + Tests

| Tarea | Detalle |
|-------|---------|
| 3.1 | Test de integracion: `test_dashboard_api.py` — inicia pipeline con proyecto de prueba, verifica que las APIs retornen datos correctos |
| 3.2 | Ruff check + ruff format, 0 errores |
| 3.3 | Ejecutar suite completa: `python -m pytest tests/ -v -o "addopts="` |
| 3.4 | Escribir `docs/170_REP_DEV_PDCA_SDLC_DASHBOARD_1_0_DRAFT.md` |
| 3.5 | Commit descriptivo |

---

## 7. Criterios de Aceptacion

- [ ] `python -m pdca_sdlc.main --dashboard "CRUD productos"` inicia pipeline + servidor HTTP
- [ ] `GET /api/health` → 200 OK con timestamp
- [ ] `GET /api/projects` → lista de proyectos del KG
- [ ] `GET /api/projects/p-001` → goal + requirements + artifacts
- [ ] `GET /api/projects/p-001/trace` → cadena BFS desde goal
- [ ] `GET /api/agents` → agentes registrados con estado
- [ ] `GET /api/events?project=p-001` → event log del proyecto
- [ ] Frontend carga en navegador sin errores JS
- [ ] Vista detalle muestra goal, requirements, artifacts, trazabilidad, eventos
- [ ] Ruff 0 errores, tests existentes 126+ PASS

---

## 8. Riesgos y Mitigaciones

| Riesgo | Prob | Impacto | Mitigacion |
|--------|------|---------|------------|
| KG vacio si el pipeline no ha corrido | Alta | Bajo | API retorna arrays vacios, frontend muestra "No hay proyectos" |
| CORS bloquea fetch desde otro origen | Baja | Alto | Mismo origen: servidor sirve HTML + API en el mismo host:puerto |
| KG en memoria se pierde al terminar proceso | Alta | Medio | El dashboard solo funciona mientras el pipeline esta vivo. Normal para MVP. En F3 con Neo4j sera persistente. |
| Muchos proyectos saturan la respuesta | Baja | Medio | Paginacion implicita: KG en F1 tiene < 100 proyectos |
| Puerto 8764 ocupado | Baja | Bajo | Error claro: "Port X already in use". Usar `--port` para cambiar. |

---

## 9. Referencias

- Dashboard existente: `compiler-bot/agentic_pipeline/dashboard/` (patron arquitectonico)
- KnowledgeGraph API: `pdca_sdlc/core/knowledge_graph.py` (query, get_trace, get_node, all_nodes)
- AsyncEventBus API: `pdca_sdlc/core/event_bus.py` (replay)
- CapabilityRegistry API: `pdca_sdlc/core/capability_registry.py` (get_all)
- Fase 1: `docs/159_REP_DEV_PDCA_SDLC_F1_EXECUTION_1_0_DRAFT.md`

---

## 10. Proximos Pasos (Post-Dashboard)

| Hito | Descripcion |
|------|-------------|
| Fase 2 | ArchitectAgent, VerificationAgent, ProjectTracker, SwarmCoordinator |
| Fase 3 | Neo4j persistente, NATS JetStream, dashboard con graph visualization |
| Mejora dashboard | Agregar grafico de red (trace graph), exportar reportes, filtros por estado |

---

*Plan generado el 2026-06-20. Proximo: ejecucion (3 dias).*
