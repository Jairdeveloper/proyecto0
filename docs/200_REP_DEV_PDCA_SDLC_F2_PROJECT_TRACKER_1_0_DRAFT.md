---
id: 200
area: dev
type: rep
module: pdca-sdlc
version: 1.0
status: DRAFT
tags:
  - report
  - development
  - pdca-sdlc
  - project-tracker
  - fase-2
  - monitoreo
  - metricas
  - riesgos
summary: "Reporte de implementacion del ProjectTracker de Fase 2: agente de monitoreo y metricas que clasifica eventos, emite reportes periodicos y detecta riesgos."
keywords:
  - project-tracker
  - monitoreo
  - metricas
  - riesgos
  - clasificacion
  - reportes
  - eventos
  - pdca-sdlc
  - fase-2
  - tests
changelog:
  - version: 1.0
    date: 2026-06-22
    author: sisyphus
    description: Reporte de implementacion del ProjectTracker (Dia 16)
---

# Reporte de Implementacion: ProjectTracker (Dia 16)

## Resumen Ejecutivo

Se implemento el **ProjectTracker**, agente de monitoreo y metricas para
PDCA-sdlc Fase 2. Se suscribe a todos los eventos del proyecto via
wildcard (`proyecto.>`), clasifica cada evento en categorias, mantiene
contadores acumulados en memoria, emite reportes periodicos y detecta
condiciones de riesgo (alta tasa de fallos, muchos pendientes, tareas
bloqueadas por timeout).

Componentes creados: 1 agente (~230 lines) + 1 suite de tests (5 tests).
Todos los tests pasan (0.23s). Ruff check: 0 errores.

---

## 1. Arquitectura del ProjectTracker

```
proyecto.{id}.> (wildcard subscription)
  │
  └── handle_event(event)
        │
        ├── Clasificar: pending / completed / failed / other
        ├── Actualizar contadores por proyecto
        ├── Detectar riesgos:
        │     ├── failed_count > threshold → high_failure_rate
        │     ├── pending_count > threshold → too_many_pending
        │     └── data.type == "swarm_timeout" → blocked_task
        └── Emitir reporte cada N eventos:
              └── project.progress.report
```

### Principio de Diseno

> **No orquesta. Solo observa, registra y alerta.**

ProjectTracker es un agente puramente reactivo. No genera comandos ni
controla el flujo del pipeline. Su proposito es proveer visibilidad
sobre la salud del proyecto.

---

## 2. Implementacion

### 2.1 Clasificacion de Eventos

`_classify_event(topic)` parsea el topic del evento:

| Palabra clave en topic | Categoria |
|------------------------|-----------|
| `created`, `proposed` | `pending` |
| `passed`, `complete` | `completed` |
| `failed` | `failed` |
| cualquier otra | `other` |

### 2.2 Contadores en Memoria

```python
self._counters: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
self._total_events: dict[str, int] = defaultdict(int)
self._fired_risks: dict[str, set[str]] = defaultdict(set)
```

Estructura: `{project_id: {category: count}}`. Los contadores son
acumulativos desde el inicio del agente.

### 2.3 Deteccion de Riesgos

`_detect_risks(project_id, event)` evalua tres condiciones:

| Riesgo | Condicion | Evento emitido |
|--------|-----------|----------------|
| `high_failure_rate` | `failed_count > failure_threshold` (default: 3) | `risk.identified` |
| `too_many_pending` | `pending_count > pending_threshold` (default: 10) | `risk.identified` |
| `blocked_task` | `event.data.type == "swarm_timeout"` | `risk.identified` |

Cada riesgo se emite una sola vez por project_id (trackeado via
`_fired_risks`). Para `blocked_task`, la clave incluye el req_id
para permitir deteccion independiente por tarea.

### 2.4 Reportes Periodicos

Cada N eventos (default: 10), el tracker emite:

```
project.progress.report
  project_id: "p-01"
  total_events: 10
  counters:
    pending: 5
    completed: 3
    failed: 2
    other: 0
```

El reporte tambien puede obtenerse bajo demanda via `get_report()`.

---

## 3. Tests

### 3.1 Suite de Tests

| Test | Verifica |
|------|----------|
| `test_tracker_classification` | Eventos created/completed/failed clasificados correctamente |
| `test_tracker_report` | Tras 10 eventos, reporte emitido con contadores |
| `test_risk_high_failure` | 4 eventos failed -> risk.identified (high_failure_rate) |
| `test_risk_timeout` | Evento swarm_timeout -> risk.identified (blocked_task) |
| `test_tracker_no_events` | Sin eventos -> no emite nada |

### 3.2 Resultados

```
5 passed in 0.23s
Ruff check: 0 errors
Ruff format: OK
```

### 3.3 Cobertura de Casos

- **Clasificacion**: 3 categorias con 3 topics distintos
- **Reporte**: contadores correctos tras 10 eventos mixtos
- **Riesgo por fallos**: 4 eventos failed superan threshold=3, un solo riesgo emitido
- **Riesgo por timeout**: evento con `type: swarm_timeout` mapeado a `blocked_task`
- **Sin eventos**: `get_report()` retorna None para proyecto sin actividad

---

## 4. Archivos

| Archivo | Accion | Lines |
|---------|--------|-------|
| `compiler-bot/pdca_sdlc/agents/project_tracker.py` | CREATED | ~230 |
| `compiler-bot/pdca_sdlc/tests/test_project_tracker.py` | CREATED | ~180 |
| `compiler-bot/pdca_sdlc/agents/__init__.py` | MODIFIED | +lines |
| `docs/200_REP_DEV_PDCA_SDLC_F2_PROJECT_TRACKER_1_0_DRAFT.md` | CREATED | ~200 |

---

## 5. Integracion con Fase 2

El ProjectTracker se suscribe a `proyecto.>` (wildcard), capturando
todos los eventos del pipeline:

```
ArchitectAgent  ── architecture.proposed ──┐
VerificationAgent ── verification.complete ─┤
QualityGate     ── quality.gate.failed ────┤
SwarmDetector   ── risk.identified ────────┤
                                           ├──> ProjectTracker
CoderAgent      ── code.committed ─────────┘
                                  ┌────────┐
                                  │Tracker │
                                  │ 1. cls │
                                  │ 2. cnt │
                                  │ 3. rsk │
                                  │ 4. rpt │
                                  └────────┘
```

---

## 6. Riesgos y Limitaciones

1. **Sin persistencia**: Contadores en memoria volatil. Al reiniciar
   el agente, todo el historial se pierde. Mitigacion: opcionalmente
   escribir periodicamente al KG.

2. **Riesgos emitidos una sola vez**: `high_failure_rate` y
   `too_many_pending` se emiten una unica vez. Si la condicion empeora,
   no se re-emite. Diseno intencional para evitar spam.

3. **Thresholds globales**: Los umbrales de riesgo son los mismos
   para todos los proyectos. Podrian necesitar ajuste por proyecto.

4. **Reporte por tiempo no implementado**: Solo se emite reporte por
   conteo de eventos, no por intervalo de tiempo. Podria anadirse
   un scheduler en Fase 3.

---

## 7. Proximos Pasos

1. **Dashboard de metricas**: Conectar `project.progress.report` al
   dashboard PDCA-sdlc para visualizacion en tiempo real.

2. **Persistencia periodica**: Escribir contadores al KG cada N reportes
   para supervivencia a reinicios.

3. **Alertas configurables**: Permitir thresholds por proyecto via
   config.yaml.

4. **Reportes temporales**: Anadir ventanas de tiempo (ultima hora,
   ultimo dia) para detectar tendencias.

---

## 8. Referencias

- Plan de ejecucion: `docs/159_PLAN_DEV_PDCA_SDLC_F2_EXECUTION_1_0_DRAFT.md`
  (lineas 326-353, Dia 16)
- BaseAgent: `compiler-bot/pdca_sdlc/core/base_agent.py`
- AsyncEventBus: `compiler-bot/pdca_sdlc/core/event_bus.py`
