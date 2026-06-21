---
id: "P06"
area: dev
type: plan
module: pdca_sdlc
version: "1.0"
status: "DRAFT"
tags: ["plan", "execution", "iso12207", "fase2", "architect", "quality-gates", "swarm", "verification"]
summary: "Plan de ejecucion para Fase 2 del modulo PDCA-sdlc — agentes Architect, Verification, Quality Gates, SwarmCoordinator, ProjectTracker. Deep-Path completo."
changelog:
  - version: "1.0"
    date: "2026-06-19"
    author: "Sistema"
    description: "Version inicial — plan de ejecucion Fase 2"
---

# Plan de Ejecucion — PDCA-sdlc Fase 2: Expansion

> **Plan base:** `docs/157_PLAN_DEV_PDCA_SDLC_IMPLEMENTATION_1_0_DRAFT.md`  
> **Fase anterior:** `docs/158_PLAN_DEV_PDCA_SDLC_EXECUTION_1_0_DRAFT.md` (F1 — Fundacion)  
> **Proxima:** `docs/160_PLAN_DEV_PDCA_SDLC_F3_EXECUTION_1_0_DRAFT.md` (F3 — Robustez)  
> **Decisiones:** D1=Hibrido, D2=Adaptation->Req->Coder->..., D3=Adapter, D4=NetworkX->Neo4j

---

## Resumen

**Objetivo:** Deep-Path funcional completo:
```
Adaptation -> Req -> Architect -> Coder -> Verification
                                (con Quality Gates + Swarm)
```

**Duracion:** 10 dias (Dias 11-20 del proyecto total)
**Archivos nuevos:** 5 (~500 LOC)
**Tests nuevos:** ~42 (acumulado ~86)
**Dependencias externas nuevas:** `nats-py` (opcional, solo si throughput lo requiere)

---

## Tareas por Dia

### Dia 11: ArchitectAgent — Diseno de Componentes

`agents/architect_agent.py`

**Logica:**
1. Recibe `requirement.created` (evento con `requirement_ids`)
2. Carga cada requisito del Knowledge Graph via `read_graph(req_id)`
3. Para proyectos SIMPLE (Fase 1): no interviene (fast-path directo a Coder)
4. Para proyectos MODERATE/COMPLEX:
   - Prompt al LLM (modelo "pro") con los requisitos como contexto
   - Tree-of-Thought (cap 17): explora 2-3 variantes arquitectonicas
   - Genera lista de componentes con: name, tech_stack, interfaces, implements_requirements
   - Genera Architecture Decision Records (ADR): title, context, decision, consequences
5. Escribe al Knowledge Graph:
   - Nodos `architecture_decision` por cada ADR
   - Nodos `component` por cada componente
   - Aristas `component.IMPLEMENTS.requirement`
6. Emite: `architecture.proposed`

**Estructura del prompt:**
```
System: You are a Software Architect following ISO 12207.
Given these requirements, design a component architecture.
Return JSON: {components: [{name, tech_stack, interfaces, implements_requirements}],
              decisions: [{title, context, decision, consequences}]}

Requirements: {reqs_json}
```

**Cobertura de modelos:**
| Escenario | Modelo | Temp |
|-----------|--------|------|
| Proyecto MODERATE | flash | 0.3 |
| Proyecto COMPLEX | pro | 0.2 |
| Fallback (LLM caido) | Flat: 1 componente por requisito | — |

**Tests (`test_architect_agent.py` ~8 tests):**
- `test_component_generation`: 4 requisitos -> 2-3 componentes con nombres validos
- `test_traceability_edges`: cada componente tiene arista IMPLEMENTS a >= 1 requisito
- `test_adr_creation`: cada ADR tiene title, context, decision, consequences no vacios
- `test_fast_path_skip`: proyecto SIMPLE -> architect no emite nada (no se suscribe)
- `test_fallback_flat`: LLM falla -> arquitectura flat generada deterministicamente
- `test_complex_project_architecture`: proyecto COMPLEX produce mas componentes que MODERATE
- `test_no_duplicate_components`: mismo requisito no genera 2 componentes iguales
- `test_architecture_proposed_event`: evento contiene component_ids y decision_ids

**Criterio de exito:** `ruff check . && ruff format . && python -m pytest tests/test_architect_agent.py -v -o "addopts="`

---

### Dia 12: ArchitectAgent — Diseno Detallado

Extension del ArchitectAgent para el diseno detallado.

**Logica adicional:**
1. Recibe (opcional) `architecture.review.approved` si hay HITL habilitado
2. Para cada componente, genera diseno detallado:
   - Interfaces especificas (metodos, params, tipos)
   - Schema de datos (entidades, campos, relaciones)
   - Dependencias entre componentes
3. Escribe al KG:
   - Propiedades detalladas en nodos `component`
   - Aristas `component.DEPENDS_ON.component` para dependencias
4. Emite: `design.detailed.complete`

**Tests adicionales (`test_architect_detailed.py` ~3 tests):**
- `test_interface_definition`: cada componente tiene interfaces con metodos
- `test_dependency_graph`: aristas DEPENDS_ON creadas correctamente
- `test_schema_generation`: componentes con DB tienen schema definido

**Criterio de exito:** `ruff check . && ruff format .`

---

### Dia 13: QualityGate — Puntos de Control

`core/quality_gate.py`

**Logica:**
```python
class GateResult:
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"

class QualityGate:
    def __init__(self, event_bus, kg):
        self._gates = {}  # gate_name -> callable

    def register_gate(self, name: str, fn: callable):
        # fn(kg, project_id, context) -> True | str(error)
        self._gates[name] = fn

    async def evaluate(self, name, project_id, context) -> GateResult:
        fn = self._gates.get(name)
        if not fn:
            return GateResult.PASSED
        result = fn(self.kg, project_id, context)
        if result is True:
            return GateResult.PASSED
        await self.event_bus.publish(Event(
            topic=f"proyecto.{project_id}.quality.gate.failed",
            data={"gate": name, "reason": str(result)}
        ))
        return GateResult.FAILED
```

**Gates predefinidos (functions standalone):**

```python
def gate_requisitos_tienen_aceptacion(kg, project_id, ctx) -> bool | str:
    """CHECK: todos los requisitos deben tener acceptance_criteria."""
    reqs = kg.query(node_type=NodeType.REQUIREMENT)
    for r in reqs:
        ac = r.get("acceptance_criteria", [])
        if not ac:
            return f"Requisito {r.id} sin criterios de aceptacion"
    return True

def gate_componentes_tienen_trazabilidad(kg, project_id, ctx) -> bool | str:
    """CHECK: cada componente traza a al menos un requisito."""
    comps = kg.query(node_type=NodeType.COMPONENT)
    for c in comps:
        traces = kg.get_outgoing(c.id, EdgeType.IMPLEMENTS)
        if not traces:
            return f"Componente {c.id} sin trazabilidad a requisitos"
    return True

def gate_modulos_tienen_trazabilidad(kg, project_id, ctx) -> bool | str:
    """CHECK: cada modulo traza a al menos un componente."""
    mods = kg.query(node_type=NodeType.CODE_MODULE)
    for m in mods:
        traces = kg.get_outgoing(m.id, EdgeType.IMPLEMENTS)
        if not traces:
            return f"Modulo {m.id} sin trazabilidad a componente"
    return True
```

**Reuso:** `agentic_pipeline.prompt_chain.observer_base.StageSubject`.
- `QualityGate` internamente usa un `StageSubject` para notificar a observers cuando un gate falla
- Los observers son agentes que necesitan reaccionar a fallos de calidad

**Tests (`test_quality_gate.py` ~6 tests):**
- `test_gate_passes`: todos los requisitos con acceptance_criteria -> PASSED
- `test_gate_fails`: un requisito sin acceptance_criteria -> FAILED con mensaje
- `test_gate_not_found`: gate inexistente -> PASSED
- `test_gate_component_traceability`: componente sin aristas -> FAILED
- `test_gate_module_traceability`: modulo sin aristas -> FAILED
- `test_gate_event_emitted`: gate fail publicado como evento en el bus

**Criterio de exito:** `ruff check . && ruff format . && python -m pytest tests/test_quality_gate.py -v -o "addopts="`

---

### Dia 14: VerificationAgent — Verificacion y Validacion

`agents/verification_agent.py`

**Logica:**
1. Recibe `code.committed`
2. **Verificacion:** recorre cadena de trazabilidad module -> component -> requirement en el KG
   - `kg.get_incoming(module_id, EdgeType.IMPLEMENTS)` -> component_id
   - `kg.get_incoming(component_id, EdgeType.IMPLEMENTS)` -> requirement_id
   - Si la cadena esta completa: verificacion PASSED
   - Si falta algun eslabon: verificacion FAILED
3. **Validacion:** LLM-as-a-Judge (cap 19)
   - Envia al LLM: el requisito original + el acceptance_criteria + el codigo generado
   - El LLM evalua si el codigo satisface el criterio
   - Escala: 1-5 (1=no cumple, 5=cumple completamente)
   - Threshold configurable en config.yaml (default: 3)
4. Dispara Quality Gates:
   - `gate_modulos_tienen_trazabilidad`
   - `gate_componentes_tienen_trazabilidad`
5. Emite: `verification.complete`, `validation.complete`, o `quality.gate.failed`

**Prompt de validacion (LLM-as-a-Judge):**
```
You are a QA Engineer evaluating if the generated code satisfies the requirement.

Requirement: {req_text}
Acceptance Criteria: {acceptance_criteria}
Code: {code_snippet}

Rate from 1 to 5:
1 = Code does not address the requirement
2 = Code partially addresses it but is incomplete
3 = Code meets the basic requirement
4 = Code fully meets the requirement with good quality
5 = Code exceeds the requirement with excellent quality

Respond with ONLY the number.
```

**Tests (`test_verification_agent.py` ~6 tests):**
- `test_verification_trace_complete`: module -> component -> requirement -> PASSED
- `test_verification_trace_broken`: module sin component -> FAILED
- `test_validation_llm_judge_passes`: LLM-as-a-Judge retorna >= 3 -> validation PASSED
- `test_validation_llm_judge_fails`: retorna < 3 -> validation FAILED
- `test_quality_gate_invoked`: verification dispara quality gates
- `test_verification_no_code_module`: no hay nodo module -> error graceful

**Criterio de exito:** `ruff check . && ruff format . && python -m pytest tests/test_verification_agent.py -v -o "addopts="`

---

### Dia 15: SwarmCoordinator — Deteccion de Completitud

`core/swarm_coordinator.py`

**Logica:**
```python
class SwarmDetector:
    """Detecta cuando un conjunto de sub-eventos forma una tarea completa.
    
    Ejemplo: cuando architecture.proposed + security.review.completed
    han llegado para el mismo req_id, emite design.complete.
    """

    def __init__(self, event_bus, kg):
        self.event_bus = event_bus
        self.kg = kg
        self._expectations: dict[str, dict] = {}
        # {req_id: {expected_topic: bool}}

    def expect(self, req_id: str, expected_topics: list[str],
               completion_topic: str, timeout: float = 300.0):
        """Registra que req_id requiere expected_topics para completarse."""
        self._expectations[req_id] = {
            "expected": {t: False for t in expected_topics},
            "completion_topic": completion_topic,
            "timeout": timeout,
            "started_at": time.time()
        }

    async def on_event(self, event: Event):
        """Procesa un evento y evalua condiciones de swarm."""
        req_id = event.data.get("requirement_id") or \
                 event.data.get("req_id")
        if not req_id or req_id not in self._expectations:
            return

        exp = self._expectations[req_id]
        if event.topic in exp["expected"]:
            exp["expected"][event.topic] = True

        if all(exp["expected"].values()):
            await self.event_bus.publish(Event(
                topic=exp["completion_topic"],
                source="swarm-coordinator",
                project_id=event.project_id,
                data={"req_id": req_id, "events": list(exp["expected"].keys())}
            ))
            del self._expectations[req_id]

    async def check_timeouts(self):
        """Barre expectativas y emite risk.identified si expiraron."""
        now = time.time()
        for req_id, exp in list(self._expectations.items()):
            if now - exp["started_at"] > exp["timeout"]:
                await self.event_bus.publish(Event(
                    topic=f"proyecto.{req_id.split('-')[0]}.risk.identified",
                    data={"type": "swarm_timeout", "req_id": req_id,
                          "pending": [t for t, v in exp["expected"].items() if not v]}
                ))
                del self._expectations[req_id]
```

**Integracion con ArchitectAgent:**
Cuando `architecture.proposed` es emitido, el SwarmDetector puede registrar expectativas:
- Para reqs de alta complejidad: esperar `security.review` + `ux.review` + `architecture.proposed`
- Cuando todas llegan: emitir `design.complete`

**Tests (`test_swarm_coordinator.py` ~5 tests):**
- `test_swarm_completion`: 2/2 eventos esperados -> completion emitido
- `test_swarm_partial`: 1/2 eventos -> completion NO emitido aun
- `test_swarm_timeout`: solo 1/2 en timeout -> risk.identified
- `test_swarm_unrelated_event`: evento no esperado -> ignorado
- `test_swarm_multiple_requests`: 2 reqs independientes -> cada uno completa por separado

**Criterio de exito:** `ruff check . && ruff format . && python -m pytest tests/test_swarm_coordinator.py -v -o "addopts="`

---

### Dia 16: ProjectTracker — Monitoreo y Metricas

`agents/project_tracker.py`

**Logica:**
1. Se suscribe a `proyecto.{id}.>` (todos los eventos del proyecto)
2. Clasifica cada evento en categorias:
   - **created/proposed** = pending
   - **passed/complete** = completed
   - **failed** = failed
3. Mantiene contadores por proyecto en memoria (`defaultdict(lambda: defaultdict(int))`)
4. Emite reporte `project.progress.report` cada 10 eventos o bajo demanda
5. Detecta riesgos:
   - `failed_count > 3` -> risk.identified (high_failure_rate)
   - `pending_count > 10` -> risk.identified (too_many_pending)
   - `swarm_timeout` recibido -> risk.identified (blocked_task)

**No orquesta.** Solo observa, registra, y alerta. Es el "cerebro" que monitorea pero no controla.

**Tests (`test_project_tracker.py` ~5 tests):**
- `test_tracker_classification`: eventos created/completed/failed clasificados correctamente
- `test_tracker_report`: tras 10 eventos, reporte emitido con contadores
- `test_risk_high_failure`: 4 eventos failed consecutivos -> risk.identified
- `test_risk_timeout`: evento swarm_timeout -> risk.identified (blocked_task)
- `test_tracker_no_events`: sin eventos -> no emite nada

**Criterio de exito:** `ruff check . && ruff format . && python -m pytest tests/test_project_tracker.py -v -o "addopts="`

---

### Dia 17: Integracion F2 — Deep-Path Baseline

Integracion de todos los componentes de Fase 2 en el flujo Deep-Path.

**Actualizacion a `main.py`:**
```python
async def main():
    bus = AsyncEventBus()
    kg = KnowledgeGraph()
    registry = CapabilityRegistry()
    llm = LLMClient(config)
    qg = QualityGate(bus, kg)
    swarm = SwarmDetector(bus, kg)

    # Registrar gates predefinidos
    qg.register_gate("requisitos_tienen_aceptacion",
                      gate_requisitos_tienen_aceptacion)
    qg.register_gate("componentes_tienen_trazabilidad",
                      gate_componentes_tienen_trazabilidad)
    qg.register_gate("modulos_tienen_trazabilidad",
                      gate_modulos_tienen_trazabilidad)

    # Agentes F1
    agents = [
        AdaptationAgent(ctx, llm),
        RequirementsAnalystAgent(ctx, llm),
        CoderAgent(ctx, llm),
        # Agentes F2
        ArchitectAgent(ctx, llm),
        VerificationAgent(ctx, llm, qg),
        ProjectTracker(ctx),
    ]
    for a in agents:
        await a.start()

    # Swarm detector escucha eventos
    bus.subscribe("proyecto.{id}.>", swarm.on_event)

    # Complexity classifier decide fast-path vs deep-path
    await bus.publish(Event(topic="project.initialized", ...))

    # Loop principal
    while True:
        await swarm.check_timeouts()
        await asyncio.sleep(1)
```

**Tests de integracion (`test_integration_f2.py` ~6 tests):**
- `test_deep_path_complete`: proyecto COMPLEX -> architect + verification + quality gates -> flujo completo
- `test_quality_gate_blocks_flow`: verification falla -> quality.gate.failed -> risk.identified
- `test_fast_path_bypasses_architect`: proyecto SIMPLE -> Coder directo, Architect no interviene
- `test_traceability_chain`: module -> component -> requirement -> goal (cadena completa)
- `test_swarm_design_complete`: architecture.proposed + security.review -> design.complete
- `test_tracker_reports_during_flow`: durante flujo deep-path, tracker emite reportes

---

### Dia 18: Tests de Cobertura y Casos Borde

**Tests adicionales (~6 tests):**
- `test_architect_empty_requirements`: 0 requisitos -> architect no emite nada
- `test_verification_missing_trace`: modulo sin componente en KG -> FAILED con mensaje claro
- `test_quality_gate_multiple_gates`: 3 gates, 1 falla -> FAILED, 2 no evaluados
- `test_swarm_timeout_during_deep_path`: architect tarda mas del timeout -> risk.identified
- `test_project_tracker_persistence`: metricas sobreviven a eventos fuera de orden
- `test_design_detailed_after_architecture`: design.detailed.complete solo si architecture.proposed existio

---

### Dia 19: Documentacion y Ruff Cleanup

- Docstrings en todas las clases y metodos publicos de Fase 2
- Verificar imports: solo importan de `agentic_pipeline` o de `PDCA-sdlc.core`, nunca al reves
- `ruff check . --no-fix` -> 0 errors
- `ruff format . --check` -> sin cambios
- `python -m pytest tests/ -v -o "addopts="` -> 86 tests PASS

---

### Dia 20: Buffer

- Resolver issues imprevistos
- Verificar que ejemplos de uso funcionan:
  - `python -m compiler-bot.PDCA-sdlc.main "CRUD de productos"` (Fast-Path)
  - `python -m compiler-bot.PDCA-sdlc.main "Sistema multi-tenant con OAuth2"` (Deep-Path)

---

## Resumen de Archivos F2

| Archivo | LOC estimado | Tests |
|---------|-------------|-------|
| `agents/architect_agent.py` | 150 | 11 |
| `core/quality_gate.py` | 70 | 6 |
| `agents/verification_agent.py` | 120 | 6 |
| `core/swarm_coordinator.py` | 80 | 5 |
| `agents/project_tracker.py` | 90 | 5 |
| `tests/test_integration_f2.py` | 100 | 6 |
| Actualizaciones `main.py`, `config.yaml` | 30 | — |
| **Total** | **~640** | **~42** |

---

## Criterio de Exito F2

```bash
ruff check .          # 0 errors
ruff format .         # sin cambios
python -m pytest tests/ -v -o "addopts="  # ~86 tests PASS
python -m compiler-bot.PDCA-sdlc.main "Sistema multi-tenant con OAuth2"
# Resultado: requisitos -> componentes -> codigo -> verificacion -> reporte
```

---

*Plan de ejecucion Fase 2 basado en `docs/157_PLAN_DEV_PDCA_SDLC_IMPLEMENTATION_1_0_DRAFT.md`. Fecha: 2026-06-19.*
