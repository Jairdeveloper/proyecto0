---
id: "P05"
area: "DEV"
type: "PLAN"
module: "PDCA_SDLC"
version: "1.0"
status: "DRAFT"
tags: ["plan", "execution", "iso12207", "pdca", "sdlc", "decisions-resolved"]
summary: "Plan de ejecucion para Fase 1 del modulo PDCA-sdlc (orquestador SDLC ISO 12207 reactivo). Include las 4 decisiones tecnicas resueltas y tareas por dia."
changelog:
  - version: "1.0"
    date: "2026-06-19"
    author: "Sistema"
    description: "Version inicial — plan de ejecucion con decisiones tecnicas tomadas"
---

# Plan de Ejecucion — PDCA-sdlc Fase 1: Fundacion

> **Plan base:** `docs/157_PLAN_DEV_PDCA_SDLC_IMPLEMENTATION_1_0_DRAFT.md`  
> **Documentos de diseno:** `154_PROP` (analisis), `155_PROP` (vision reactiva), `156_PROP` (esqueleto Python)  
> **Review arquitectonico:** `docs/114_REP_DEV_ARCHITECTURAL_REVIEW_ISO12207_1_0_DRAFT.md`

---

## Decisiones Tecnicas Resueltas

| # | Decision | Resolucion | Justificacion |
|---|----------|-----------|---------------|
| D1 | **CoderAgent + synthesis.py** | **C — Hibrido** | CoderAgent usa LLM directo (ReAct) para codigo simple; delega a `synthesis.py` via Tool Use para scaffolding NestJS/Prisma. Permite reuso del pipeline existente sin acoplamiento fuerte. |
| D2 | **Orden Fase 1** | **Adaptation -> Req -> Coder** | Flujo natural ISO 12207: adaptar/clasificar primero, elicitar requisitos, codificar. Cada agente recibe la salida estructurada del anterior. |
| D3 | **EventBus** | **Adapter sobre existente** | `AsyncEventBus` en PDCA-sdlc envuelve a `agentic_pipeline.agents.event_bus.EventBus`. Anade: topicos jerarquicos (`.`), wildcard (`>` `*`), sequence numbers, event log para replay. NATS JetStream evaluado en Fase 2+ si el throughput lo demanda. |
| D4 | **Knowledge Graph** | **NetworkX (F1) -> Neo4j (F3)** | MVP rapido con NetworkX en memoria. Migrar a Neo4j en Fase 3 para persistencia y consultas complejas. |

---

## Arquitectura del Modulo

```
compiler-bot/
├── agentic_pipeline/            ← EXISTENTE (no tocar)
│   ├── agents/event_bus.py      →  Base para AsyncEventBus (adapter)
│   ├── nodes/planner.py         →  Reusado por AdaptationAgent
│   ├── nodes/requirement_decomposer.py →  Reusado por RequirementsAnalyst
│   ├── nodes/synthesis.py       →  Reusado por CoderAgent (Tool Use)
│   └── templates/               →  Scaffolding via CoderAgent
│
└── PDCA-sdlc/                   ← NUEVO (crear ahora)
    ├── __init__.py
    ├── core/
    │   ├── __init__.py
    │   ├── event_bus.py         AsyncEventBus (adapter sobre existente)
    │   ├── knowledge_graph.py   NetworkX wrapper con tipos
    │   ├── capability_registry.py Registro de capacidades
    │   ├── base_agent.py        Clase abstracta BaseAgent
    │   └── llm_client.py        Cliente LLM con fallback
    ├── agents/
    │   ├── __init__.py
    │   ├── adaptation_agent.py  Clasifica, selecciona procesos, define ciclo
    │   ├── requirements_analyst.py NL -> structured requirements
    │   └── coder_agent.py       Codigo + tests (hibrido LLM + synthesis)
    ├── protocols/
    │   ├── __init__.py
    │   └── event_schemas.py     Pydantic models de eventos
    ├── tests/
    │   ├── __init__.py
    │   ├── test_event_bus.py
    │   ├── test_knowledge_graph.py
    │   ├── test_capability_registry.py
    │   ├── test_base_agent.py
    │   ├── test_llm_client.py
    │   ├── test_adaptation_agent.py
    │   ├── test_requirements_analyst.py
    │   ├── test_coder_agent.py
    │   └── test_integration_f1.py
    ├── main.py                  Entrypoint
    └── config.yaml              Configuracion
```

---

## Tareas por Dia

### Dia 1: Estructura + EventBus

**Mañana:** Crear estructura de directorio y `__init__.py` files.

- `mkdir -p compiler-bot/PDCA-sdlc/{core,agents,protocols,tests}`
- `__init__.py` en cada subdirectorio con imports explícitos
- `config.yaml` con defaults

**Tarde:** `core/event_bus.py`

- `TopicMatcher`: clase estatica con `matches(pattern, topic)` — wildcard `.>` (subarbol) y `.*` (un nivel)
- `Event`: dataclass con `id`, `topic`, `source`, `project_id`, `data`, `timestamp`, `sequence`
- `AsyncEventBus`: adapter que internamente usa `agentic_pipeline.agents.event_bus.EventBus`

```python
# API publica de AsyncEventBus
bus = AsyncEventBus()
await bus.subscribe("proyecto.{id}.requirement.created", handler)
await bus.publish(Event(topic="proyecto.p-01.requirement.created", ...))
events = bus.replay("p-01", since_sequence=5)
```

**Tests:** `test_event_bus.py`
- `test_topic_matcher_exact`
- `test_topic_matcher_wildcard`
- `test_publish_subscribe`
- `test_publish_async_handler`
- `test_replay_events`
- `test_sequence_numbers`

**Criterio de exito:** `ruff check . && ruff format . && python -m pytest tests/test_event_bus.py -v`

---

### Dia 2: Knowledge Graph + Capability Registry

**Mañana:** `core/knowledge_graph.py`

- `NodeType` enum (requirement, component, code_module, architecture_decision, goal, risk, artifact, task, milestone)
- `EdgeType` enum (satisfies, implements, verifies, affects, depends_on, generates, documents, precedes)
- `Node` dataclass: `id`, `node_type`, `properties: dict`, `created_by`, `created_at`
- `Edge` dataclass: `source_id`, `target_id`, `edge_type`, `properties`
- `KnowledgeGraph`: `add_node`, `get_node`, `update_node`, `add_edge`, `get_outgoing`, `get_incoming`, `get_trace` (BFS), `query` (filtros por type, status, properties)

**Tarde:** `core/capability_registry.py`

- `CapabilityManifest` dataclass: `agent_id`, `agent_name`, `description`, `iso_12207` (dict con process/activities/tasks), `triggers` (list de event patterns), `output_events`, `llm_profile`, `version`, `status`
- `CapabilityRegistry`: `register`, `unregister`, `find_by_event`, `find_by_iso_activity`, `get_all`, `update_status`

**Tests:** `test_knowledge_graph.py`, `test_capability_registry.py`
- KG: crear nodos, crear aristas, query por tipo/status, get_trace entre nodos
- Registry: registrar agente, encontrar por evento, encontrar por actividad ISO

**Criterio de exito:** `ruff check . && ruff format . && python -m pytest tests/test_knowledge_graph.py tests/test_capability_registry.py -v`

---

### Dia 3: BaseAgent + LLMClient

**Mañana:** `core/llm_client.py`

- `LLMClient` clase generica con metodo `complete(prompt, max_tokens, response_format)` -> str
- Fallback: intenta OpenRouter primero, LiteLLM segundo, mock local tercero
- Configurable via `config.yaml`: modelo por perfil (flash, pro), temperatura, max_tokens
- Timeout configurable, retry con backoff exponencial

**Tarde:** `core/base_agent.py`

- `AgentContext` dataclass: `event_bus`, `knowledge_graph`, `capability_registry`, `agent_id`
- `BaseAgent(ABC)`: `start()`, `stop()`, `_handle_event_wrapper` (try/except + risk.identified en fallo), `handle_event(event)` abstracto, `emit(topic, project_id, data)`, `read_graph(node_id)`, `write_graph(node)`, `query_graph(**filters)`
- Lifecycle: register en registry -> subscribe a triggers -> loop de eventos -> unregister en stop

**Tests:** `test_base_agent.py`, `test_llm_client.py`
- BaseAgent: start/stop, handle_event wrapper captura excepciones, emit crea Event con sequence
- LLMClient: fallback testing, timeout, response parsing

**Criterio de exito:** `ruff check . && ruff format . && python -m pytest tests/ -v`

---

### Dia 4: Event Schemas + Configuration

**Protocolos:** `protocols/event_schemas.py`

Schemas Pydantic para cada evento del bus:

```python
class ProjectInitialized(BaseModel):
    description: str
    project_id: str

class AdaptationComplete(BaseModel):
    complexity: Literal["simple", "moderate", "complex"]
    lifecycle: Literal["fast_track", "iterative", "incremental", "agile", "spiral"]
    processes: list[str]
    activities: list[str]
    effort_estimate: dict

class RequirementCreated(BaseModel):
    requirement_ids: list[str]
    count: int

class ArchitectureProposed(BaseModel):
    component_ids: list[str]
    components: list[dict]
    requirement_ids: list[str]

class CodeCommitted(BaseModel):
    module_id: str
    component: str
    files: list[str]
    tests_passed: bool

class CodeFailed(BaseModel):
    module_id: str
    component: str
    error: str

class QualityGateResult(BaseModel):
    module_id: str | None = None
    gate: str
    result: Literal["passed", "failed"]
    details: str | None = None

class RiskIdentified(BaseModel):
    description: str
    severity: Literal["low", "medium", "high", "critical"]
    source_event: str = ""
```

**Config:** `config.yaml`
- LLM profiles: flash, pro con modelo, temperatura, max_tokens
- EventBus: max_event_log_size, replay_batch_size
- Agentes: enable/disable por agente

**Tests:** Validar que todos los schemas serializan/deserializan correctamente.

**Criterio de exito:** `ruff check . && ruff format .`

---

### Dia 5: AdaptationAgent

`agents/adaptation_agent.py`

**Logica:**
1. Recibe `project.initialized` con `description` del proyecto
2. Clasifica complejidad via LLM: SIMPLE (CRUD, 1-2 entidades), MODERATE (3-5 entidades, cambios menores), COMPLEX (multi-modulo, seguridad, decisiones arquitectonicas)
3. Selecciona template de procesos ISO 12207 segun complejidad:
   - SIMPLE -> minimal (Requirements Elicitation, Software Implementation, Unit Testing; fast-track lifecycle)
   - MODERATE -> standard (anade Architecture Design, Verification, Configuration Mgmt; iterative lifecycle)
   - COMPLEX -> full (anade Project Planning, Risk Management, Quality Assurance; agile lifecycle)
4. Estima esfuerzo basado en actividades seleccionadas
5. Escribe nodo `goal` al Knowledge Graph con toda la informacion
6. Emite: `adaptation.complete`, `complexity.classified`, `lifecycle.proposed`

**Reuso:** `agentic_pipeline.nodes.planner` para descomposicion fina de tareas si el proyecto es COMPLEX.

**Tests:** `test_adaptation_agent.py`
- Clasifica como SIMPLE para "CRUD de productos"
- Clasifica como COMPLEX para "Sistema multi-tenant con OAuth2"
- Fallback deterministico cuando LLM falla
- Emite los 3 eventos esperados

**Criterio de exito:** `ruff check . && ruff format . && python -m pytest tests/test_adaptation_agent.py -v`

---

### Dia 6: RequirementsAnalystAgent

`agents/requirements_analyst.py`

**Logica:**
1. Recibe `adaptation.complete` (o `requirement.clarification_needed`)
2. Lee la descripcion del proyecto del Knowledge Graph
3. Prompt Chaining: NL del usuario -> lista de `RequirementSchema` (structured output JSON)
4. Cada requirement: id, text, type (functional/business/user/non_functional), priority, acceptance_criteria
5. Escribe nodos `requirement` al Knowledge Graph
6. Emite: `requirement.created`

**Reuso:** `agentic_pipeline.nodes.requirement_decomposer` para el parsing de entidades del lenguaje natural. Uso via adapter: se llama al metodo de descomposicion y se mapea la salida a `RequirementSchema`.

**Tests:** `test_requirements_analyst.py`
- Convierte "Quiero login con Google" en requisitos funcionales
- Cada requisito tiene acceptance_criteria
- La cantidad de requisitos es razonable (3-8 para proyecto tipico)
- Rechaza input vacio

**Criterio de exito:** `ruff check . && ruff format . && python -m pytest tests/test_requirements_analyst.py -v`

---

### Dia 7: CoderAgent (Hibrido)

`agents/coder_agent.py`

**Logica (Decision D1 — Hibrido):**
1. Recibe `requirement.created` (y opcionalmente `architecture.proposed` si existe)
2. **Para codigo simple** (SIMPLE classification): LLM directo con ReAct:
   - Thought: planificar implementacion basado en requisitos
   - Action: generate_code() mediante LLM
   - Observation: validar que compila/parsea
   - Loop hasta que pase o max_retries
3. **Para scaffolding** (NestJS/Prisma modules): Tool Use -> llama a `synthesis.py`:
   - Construye el payload de entrada que synthesis.py espera
   - Ejecuta como subproceso o import directo (segun config)
   - Captura el codigo generado
4. Escribe nodo `code_module` al Knowledge Graph
5. Crea aristas de trazabilidad: `module.IMPLEMENTS.component` (o directo `module.IMPLEMENTS.requirement` si no hay architect)
6. Ejecuta tests unitarios simulados (placeholder; en Fase 2+ seran reales via pytest)
7. Emite: `code.committed` (tests pass) o `code.failed` (con error)

**Reuso:** `agentic_pipeline.nodes.synthesis` via Tool Use interno. Se crea un adapter `SynthesisTool` que toma los requisitos y produce el scaffolding.

**Tests:** `test_coder_agent.py`
- Genera codigo para requisito simple (CRUD) -> emite code.committed
- Reporta error si el LLM falla -> emite code.failed
- Max_retries: tras N fallos consecutivos, escala a risk.identified
- Trazabilidad: module.IMPLEMENTS.requirement existe en KG

**Criterio de exito:** `ruff check . && ruff format . && python -m pytest tests/test_coder_agent.py -v`

---

### Dia 8-9: Integracion F1

`main.py` + tests de integracion

**main.py:**
```python
async def main():
    bus = AsyncEventBus()
    kg = KnowledgeGraph()
    registry = CapabilityRegistry()
    llm = LLMClient(config)

    agents = [
        AdaptationAgent(ctx, llm),
        RequirementsAnalystAgent(ctx, llm),
        CoderAgent(ctx, llm),
    ]
    for a in agents:
        await a.start()

    await bus.publish(Event(
        topic="project.initialized",
        source="cli",
        project_id="p-001",
        data={"description": sys.argv[1]}
    ))
    await asyncio.sleep(5)  # esperar a que los agentes procesen
    # mostrar resumen del KG
```

**Tests de integracion:** `test_integration_f1.py`
- `test_fast_path_complete`: "CRUD productos" -> adaptation -> reqs -> codigo. Verificar que: (1) KG tiene nodo goal, (2) KG tiene >= 3 nodos requirement, (3) KG tiene nodo code_module, (4) KG tiene aristas de trazabilidad
- `test_fast_path_traceability`: Verificar que la cadena module -> requirement existe y es completa
- `test_sequential_processing`: Verificar que los eventos se emiten en orden: adaptation.complete -> requirement.created -> code.committed
- `test_error_handling`: Input invalido -> risk.identified emitido

**Criterio de exito final F1:**
```bash
ruff check .          # 0 errors
ruff format .         # sin cambios
python -m pytest tests/ -v -o "addopts="  # ~44 tests PASS
```

---

### Dia 10: Buffer + Documentacion

- Resolver issues de integracion
- Escribir docstring en todas las clases y metodos publicos
- Verificar que ruff pasa en 100% de los archivos
- Verificar que todos los imports son correctos (tanto internos como de agentic_pipeline)
- Escribir `docs/159_REP_DEV_PDCA_SDLC_F1_EXECUTION_1_0_DRAFT.md` con resultados de Fase 1

---

## Resumen de Archivos y Tests

| Archivo | LOC estimado | Tests |
|---------|-------------|-------|
| `core/event_bus.py` | 80 | 6 |
| `core/knowledge_graph.py` | 90 | 6 |
| `core/capability_registry.py` | 60 | 4 |
| `core/base_agent.py` | 70 | 4 |
| `core/llm_client.py` | 50 | 3 |
| `protocols/event_schemas.py` | 60 | 2 |
| `agents/adaptation_agent.py` | 120 | 5 |
| `agents/requirements_analyst.py` | 100 | 5 |
| `agents/coder_agent.py` | 130 | 5 |
| `main.py` | 60 | — |
| `config.yaml` | 30 | — |
| `tests/integration_f1.py` | 80 | 4 |
| **Total** | **~930** | **~44** |

---

## Checklist de Validacion por Dia

| Dia | Check | Comando |
|-----|-------|---------|
| 1 | EventBus funcional | `python -m pytest tests/test_event_bus.py -v -o "addopts="` |
| 2 | KG + Registry | `python -m pytest tests/test_knowledge_graph.py tests/test_capability_registry.py -v -o "addopts="` |
| 3 | BaseAgent + LLMClient | `python -m pytest tests/test_base_agent.py tests/test_llm_client.py -v -o "addopts="` |
| 4 | Schemas + Config | `ruff check .` |
| 5 | AdaptationAgent | `python -m pytest tests/test_adaptation_agent.py -v -o "addopts="` |
| 6 | RequirementsAnalyst | `python -m pytest tests/test_requirements_analyst.py -v -o "addopts="` |
| 7 | CoderAgent | `python -m pytest tests/test_coder_agent.py -v -o "addopts="` |
| 8-9 | Integracion F1 | `python -m pytest tests/ -v -o "addopts="` + `ruff check . && ruff format .` |
| 10 | Cierre | `ruff check . --no-fix && ruff format . --check && python -m pytest tests/ -v -o "addopts="` |

---

## Dependencias Externas a Instalar

```bash
pip install networkx pyyaml  # Fase 1
# openrouter/litellm se evalua cuando el LLMClient necesite conexion real
```

Las pruebas usan LLM mockeado (devuelve JSON predefinido), asi que no requieren credenciales de API en Fase 1.

---

## Proximos Pasos (al completar F1)

1. Ejecutar checklist final del Dia 10
2. Escribir reporte `159_REP_DEV_PDCA_SDLC_F1_EXECUTION_1_0_DRAFT.md`
3. Commit con mensaje: `feat(PDCA-sdlc): Fase 1 fundacion — EventBus, KG, Registry, BaseAgent, 3 agentes, Fast-Path`
4. Iniciar planificacion de Fase 2 (ArchitectAgent, VerificationAgent, SwarmCoordinator)

---

*Plan de ejecucion basado en `docs/157_PLAN_DEV_PDCA_SDLC_IMPLEMENTATION_1_0_DRAFT.md` con decisiones D1-D4 resueltas. Fecha: 2026-06-19.*
