---
id: 198
area: dev
type: rep
module: pdca-sdlc
version: 1.0
status: DRAFT
tags:
  - report
  - development
  - pdca-sdlc
  - swarm-coordinator
  - fase-2
  - swarm-detector
  - completitud
  - event-driven
summary: "Reporte de implementacion del SwarmCoordinator de Fase 2: deteccion de completitud de tareas via eventos asincronos con expectativas, timeouts y eventos de riesgo."
keywords:
  - swarm
  - swarm-detector
  - completitud
  - eventos
  - expectativas
  - timeout
  - risk-identified
  - event-bus
  - pdca-sdlc
  - fase-2
  - tests
changelog:
  - version: 1.0
    date: 2026-06-22
    author: sisyphus
    description: Reporte de implementacion del SwarmCoordinator (Dia 15)
---

# Reporte de Implementacion: SwarmCoordinator (Dia 15)

## Resumen Ejecutivo

Se implemento el **SwarmCoordinator** (`SwarmDetector`), un mecanismo de
deteccion de completitud basado en eventos asincronos. Permite registrar
expectativas para un conjunto de sub-eventos que deben llegar antes de
considerar una tarea completa. Maneja timeouts con emision automatica de
eventos `risk.identified`.

Componentes creados: 1 modulo (~170 lines) + 1 suite de tests (5 tests).
Todos los tests pasan (0.24s). Ruff check: 0 errores.

---

## 1. Arquitectura del SwarmDetector

```
expect(req_id, [topic_a, topic_b], "design.complete", timeout=300)
  │
  ├─ on_event(event) ──┬─ topic_a recibido  → marca True
  │                     └─ topic_b recibido  → emite "design.complete"
  │
  └─ check_timeouts() ──┬─ timeout no expirado → no hace nada
                         └─ timeout expirado    → emite risk.identified
                                                    └─ pending: [topic_b]
```

### API Publica

| Metodo | Args | Retorno | Descripcion |
|--------|------|---------|-------------|
| `expect()` | req_id, expected_topics, completion_topic, timeout | None | Registra expectativa |
| `on_event()` | event | None | Procesa evento entrante |
| `check_timeouts()` | — | None | Barre expectativas expiradas |
| `active_expectations` | — | dict | Copia de expectativas activas |
| `clear()` | — | None | Elimina todas las expectativas |

### Flujo de Completitud

1. **Registro**: `detector.expect("req-001", ["arch.proposed", "sec.review"], "design.complete")`
2. **Procesamiento**: Cada llamada a `on_event(event)` verifica si el topic del
   evento coincide con algun topic esperado. Si es el primer evento, almacena
   el `project_id` para usar en timeouts.
3. **Completitud**: Cuando todos los topics esperados han llegado, emite un
   evento con el `completion_topic` y elimina la expectativa.
4. **Timeout**: `check_timeouts()` recorre todas las expectativas. Si alguna ha
   superado su timeout, emite `proyecto.{id}.risk.identified` con los topics
   pendientes.

### Formato de Eventos Emitidos

**Completitud:**
```json
{
  "topic": "design.complete",
  "source": "swarm-coordinator",
  "project_id": "p-01",
  "data": {
    "req_id": "req-001",
    "events": ["architecture.proposed", "security.review.completed"]
  }
}
```

**Timeout / Riesgo:**
```json
{
  "topic": "proyecto.p-01.risk.identified",
  "source": "swarm-coordinator",
  "project_id": "p-01",
  "data": {
    "type": "swarm_timeout",
    "req_id": "req-003",
    "pending": ["security.review.completed"]
  }
}
```

---

## 2. Implementacion

### 2.1 Estructura de Expectativas

Cada expectativa almacena:

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `expected` | `dict[str, bool]` | Topics esperados con estado de recepcion |
| `completion_topic` | `str` | Topic a emitir al completar |
| `timeout` | `float` | Tiempo maximo en segundos |
| `started_at` | `float` | Timestamp de registro (`time.time()`) |
| `project_id` | `str` | Almacenado del primer evento recibido |

### 2.2 Deteccion de `req_id`

El metodo `on_event` busca `requirement_id` o `req_id` en `event.data`:

```python
req_id = event.data.get("requirement_id") or event.data.get("req_id")
```

Si no se encuentra el req_id o no hay expectativa registrada, el evento
se ignora silenciosamente (no levanta excepcion).

### 2.3 Proyecto en Timeouts

El `project_id` para el evento de riesgo se obtiene de:
1. El `project_id` almacenado del primer evento recibido (prioritario)
2. Fallback: primera parte del `req_id` antes del primer `-`

Esto garantiza que incluso si nunca llega ningun evento, el timeout
puede emitir un evento con un project_id razonable.

---

## 3. Tests

### 3.1 Suite de Tests

| Test | Verifica |
|------|----------|
| `test_swarm_completion` | 2/2 eventos esperados -> completion emitido |
| `test_swarm_partial` | 1/2 eventos -> completion NO emitido aun |
| `test_swarm_timeout` | 1/2 eventos en timeout -> risk.identified |
| `test_swarm_unrelated_event` | Evento inesperado -> ignorado, expectativa intacta |
| `test_swarm_multiple_requests` | 2 reqs independientes -> cada uno completa por separado |

### 3.2 Resultados

```
5 passed in 0.24s
Ruff check: 0 errors
Ruff format: OK
```

### 3.3 Cobertura de Casos

- **Completitud normal**: flujo feliz 2/2 eventos
- **Parcial**: solo 1/2, no debe emitir prematuremente
- **Timeout**: expiracion con un evento pendiente -> risk.identified
- **Evento no relacionado**: topic no esperado no altera estado
- **Multiples requests independientes**: cada req_id tiene su propio estado

---

## 4. Archivos

| Archivo | Accion | Lines |
|---------|--------|-------|
| `compiler-bot/pdca_sdlc/core/swarm_coordinator.py` | CREATED | ~170 |
| `compiler-bot/pdca_sdlc/tests/test_swarm_coordinator.py` | CREATED | ~160 |
| `compiler-bot/pdca_sdlc/core/__init__.py` | MODIFIED | +2 lines |
| `docs/198_REP_DEV_PDCA_SDLC_F2_SWARM_COORDINATOR_1_0_DRAFT.md` | CREATED | ~200 |

---

## 5. Integracion con Fase 2

El SwarmDetector se integra con el resto del pipeline:

```
architecture.proposed ──┐
                         ├──> SwarmDetector ──> design.complete
security.review ─────────┘
```

Cuando `architecture.proposed` es emitido por el ArchitectAgent, el
SwarmDetector puede registrar expectativas adicionales:

```python
# En el flujo deep-path:
swarm.expect(req_id,
    ["architecture.proposed", "security.review.completed"],
    "design.complete",
    timeout=config.swarm_timeout,
)
```

---

## 6. Riesgos y Limitaciones

1. **Sin persistencia**: Las expectativas se pierden si el proceso se
   reinicia. Para produccion, considerar almacenar en el KG o Redis.

2. **Timeout fijo por expectativa**: No hay escalado automatico del
   timeout segun complejidad del proyecto.

3. **Deteccion de req_id limitada**: Solo busca `requirement_id` o
   `req_id` en event.data. Si otros agentes usan keys distintas, no
   se detectara.

4. **Sin deduplicacion**: Si el mismo evento llega dos veces, se
   marca el topic como recibido sin consecuencias, pero no hay
   proteccion contra eventos duplicados.

5. **check_timeouts debe invocarse externamente**: No hay scheduler
   interno. Un loop externo debe llamar `check_timeouts()`
   periodicamente.

---

## 7. Proximos Pasos

1. **Scheduler automatico**: Integrar `check_timeouts()` en el main
   loop de PDCA-sdlc.

2. **Persistencia de expectativas**: Opcionalmente almacenar en KG
   para supervivencia a reinicios.

3. **API de consulta**: Exponer `active_expectations` via dashboard.

4. **Metricas**: Registrar tiempo promedio de completitud por tipo
   de tarea.

---

## 8. Referencias

- Plan de ejecucion: `docs/159_PLAN_DEV_PDCA_SDLC_F2_EXECUTION_1_0_DRAFT.md`
  (lineas 248-322, Dia 15)
- AsyncEventBus: `compiler-bot/pdca_sdlc/core/event_bus.py`
- KnowledgeGraph: `compiler-bot/pdca_sdlc/core/knowledge_graph.py`
