---
id: "P04"
area: "DEV"
type: "PLAN"
module: "PDCA_SDLC"
version: "1.0"
status: IMPLEMENTED
tags: ["plan", "implementation", "iso12207", "pdca", "sdlc", "multi-agent", "event-driven", "new-module"]
summary: "Plan de implementacion del modulo PDCA-sdlc — orquestador SDLC reactivo basado en ISO 12207, construido como modulo nuevo dentro del repositorio Proyecto0, reutilizando infraestructura del pipeline RECPL existente."
changelog:
  - version: "1.0"
    date: "2026-06-19"
    author: "Sistema"
    description: "Version inicial — plan de implementacion hibrido, mismo repo, modulo nuevo"
---

# Plan de Implementacion — PDCA-sdlc: Orquestador SDLC ISO 12207

> **Documentos base:**  
> - `docs/154_PROP_DEV_ISO12207_AGENT_SYSTEM_ANALYSIS_1_0_DRAFT.md` — Analisis de viabilidad  
> - `docs/155_PROP_DEV_ISO12207_AGENT_SYSTEM_REACTIVE_VISION_1_0_DRAFT.md` — Vision reactiva de capacidades  
> - `docs/156_PROP_DEV_ISO12207_AGENT_SYSTEM_ARCHITECT_IMPL_1_0_DRAFT.md` — Esqueleto de implementacion Python  
> - `docs/114_REP_DEV_ARCHITECTURAL_REVIEW_ISO12207_1_0_DRAFT.md` — Review arquitectonico previo
>
> **Estrategia:** Hibrido — mismo repositorio (`Proyecto0`), modulo nuevo (`PDCA-sdlc`), reuso selectivo de `agentic_pipeline/`

---

## 0. Resumen Ejecutivo

**Que:** Modulo `PDCA-sdlc/` dentro de `compiler-bot/` que implementa un orquestador SDLC reactivo basado en ISO 12207. Los agentes son peers que reaccionan a eventos en un bus compartido, no un pipeline secuencial orquestado.

**Por que:** El RECPL Compiler Bot actual es un compilador NL->codigo. El PDCA-sdlc extiende el sistema para cubrir el ciclo de vida completo del software (requisitos, arquitectura, codificacion, verificacion, despliegue) siguiendo ISO 12207.

**Como:** 
- Modulo nuevo en `compiler-bot/PDCA-sdlc/`
- Reusa infraestructura de `agentic_pipeline/` (EventBus, testing patterns, synthesis, templates)
- Arquitectura reactiva: EventBus + KnowledgeGraph + CapabilityRegistry + agentes peer
- No modifica `agentic_pipeline/` existente (solo importa desde el nuevo modulo)

**Esfuerzo estimado:** ~6-8 semanas en 3 fases
**Riesgo principal:** Decisiones tecnicas pendientes (CoderAgent, synthesis integration, Fase 1 agent ordering)

---

## 1. Arquitectura Propuesta

### 1.1 Relacion con codigo existente

```
compiler-bot/
├── agentic_pipeline/            ← EXISTENTE (RECPL v2.0, 463 tests)
│   ├── agents/event_bus.py      →  Reusable (base para EventBus async)
│   ├── prompt_chain/            →  Reusable (Observer pattern para Quality Gates)
│   ├── nodes/
│   │   ├── planner.py           →  Reusable (llamado por AdaptationAgent)
│   │   ├── synthesis.py         →  Pendiente decision (ver seccion 3.3)
│   │   └── requirement_decomposer.py →  Reusable (base para RequirementsAnalyst)
│   ├── orchestrator.py          →  Reusable (StateGraph como sub-componente)
│   └── tests/                   →  Convenciones reusables (pytest, ruff)
│
├── PDCA-sdlc/                   ← NUEVO (ISO 12207 reactivo)
│   ├── core/                    Infraestructura base
│   ├── agents/                  Agentes especializados ISO 12207
│   ├── protocols/               Schemas Pydantic de eventos
│   ├── tests/                   pytest, 0 ruff errors
│   ├── main.py                  Entrypoint del modulo
│   └── config.yaml              Configuracion
│
├── templates/                   ← EXISTENTE, reusado por CoderAgent
└── docs/                        ← Documentacion actualizada
```

### 1.2 Principios de integracion

1. **Unidireccional:** `PDCA-sdlc` importa de `agentic_pipeline`, nunca al reves
2. **Adapter pattern:** Donde se requiera adaptar interfaces existentes, se usa un adapter en `PDCA-sdlc/`, no se modifica el codigo fuente de `agentic_pipeline/`
3. **Misma convencion:** Type hints obligatorios, Pydantic para datos en los limites, ruff check/format, pytest
4. **Templates compartidos:** `templates/` sigue siendo la fuente unica de scaffolding, accedida via Tool Use o MCP

### 1.3 Diagrama de componentes

```
┌─────────────────────────────────────────────────────────┐
│                    PDCA-sdlc Module                       │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │   EventBus    │  │ Knowledge     │  │  Capability     │  │
│  │ (async+NATS)  │  │ Graph (Neo4j) │  │  Registry       │  │
│  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘  │
│         │                 │                   │           │
│         └─────────────────┼───────────────────┘           │
│                           │                               │
│  ┌────────────────────────┴──────────────────────────┐   │
│  │              Agent Pool (Peers)                    │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ │   │
│  │  │Adaptation│ │  Req     │ │Architect │ │Coder │ │   │
│  │  │ Agent    │ │ Analyst  │ │ Agent    │ │Agent │ │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────┘ │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ │   │
│  │  │Verifier  │ │  Tracker │ │ DocWriter│ │Config│ │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────┘ │   │
│  └───────────────────────────────────────────────────┘   │
│                                                           │
│  ┌───────────────────────────────────────────────────┐   │
│  │         Quality Gates + Swarm Coordinator           │   │
│  └───────────────────────────────────────────────────┘   │
│                                                           │
│  ┌────────────────────┐    ┌──────────────────────────┐  │
│  │ MCP Servers        │    │ PDCA Engine (ciclo       │  │
│  │ (filesystem, git,  │    │ nativo: cada evento      │  │
│  │  synthesis...)     │    │ es PLAN, DO, CHECK, ACT) │  │
│  └────────────────────┘    └──────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│            agentic_pipeline (existente)                   │
│  (planner.py, synthesis.py, templates/, event_bus.py)     │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Reuso de Componentes Existentes

| Componente | Ubicacion | Uso en PDCA-sdlc | Tipo de reuso |
|-----------|-----------|-----------------|---------------|
| **EventBus** | `agents/event_bus.py` | Base para EventBus async del nuevo modulo | Adapter (wrap como async) |
| **StageSubject/Observer** | `prompt_chain/observer_base.py` | Implementar Quality Gates como observers | Import directo |
| **StateGraph** | `orchestrator.py` | Sub-componente interno de arquitecturas complejas | Import directo |
| **Planner** | `nodes/planner.py` | Llamado por AdaptationAgent para descomposicion fina | Import directo |
| **RequirementDecomposer** | `nodes/requirement_decomposer.py` | Base para RequirementsAnalystAgent | Import directo + extension |
| **Synthesis** | `nodes/synthesis.py` | Pendiente decision tecnica (seccion 3.3) | Pendiente |
| **Templates** | `templates/` | Scaffolding NestJS/Prisma para CoderAgent | Tool Use / MCP |
| **Tests** | `tests/` | Convenciones: pytest, ruff, -o "addopts=" para coverage | Mismas reglas |
| **Pydantic models** | Varios | Schemas de datos en los limites del sistema | Misma practica |
| **Logging** | Varios | Logging con `%s` (sin f-strings) | Misma convencion |
| **LLMClient** | (no existe un cliente unificado) | Crear LLMClient generico con fallback entre modelos | Nuevo (basado en OpenRouter) |

**Archivos de `agentic_pipeline/` que NO se reusan:**
- `nodes/preprocessor.py`, `nodes/lexer.py`, `nodes/parser.py` — son especificos del pipeline compilador NL, no del SDLC orquestador
- `nodes/semantic_analyzer.py`, `nodes/ir_generator.py` — internos del pipeline RECPL
- `nodes/validator.py` — Chain of Responsibility para validacion interna, distinto a Quality Gates
- `feedback_loop.py`, `metrics_store.py` — especificos del feedback loop del compilador

---

## 3. Decisiones Tecnicas Abiertas

Las siguientes decisiones deben resolverse en una revision tecnica antes de comenzar la implementacion de cada fase:

### 3.1 CoderAgent e integracion con synthesis.py (ALTA PRIORIDAD)

**Problema:** En las propuestas 155/156, el CoderAgent genera codigo. El pipeline existente ya tiene `nodes/synthesis.py` con 6 generadores (NestJS, Prisma, React, Docker, etc.). 

**Opciones:**

| Opcion | Descripcion | Ventajas | Desventajas |
|--------|------------|----------|-------------|
| **A. Import directo** | CoderAgent importa y llama `synthesis.py` como libreria | Minimo esfuerzo, reuso directo | Acopla modulo nuevo a implementacion interna de synthesis |
| **B. MCP Server wrapper** | Exponer synthesis.py como MCP server; CoderAgent llama via protocolo | Desacoplamiento total, interfaz estandar | Esfuerzo adicional de wrapper, latencia de red |
| **C. Agente hibrido** | CoderAgent usa LLM directamente para codigo simple, synthesis.py para scaffolding complejo | Lo mejor de ambos mundos | Mayor complejidad de implementacion, dos codigos de generacion que pueden divergir |

**Recomendacion:** Opcion C (hibrido) con opcion B como evolucion futura. El CoderAgent decide si usa LLM directo (codigo simple) o delega a synthesis.py (scaffolding NestJS/Prisma).

**Estado:** 🔴 (OPCION C APROBADA).

### 3.2 Orden de Fase 1 (ALTA PRIORIDAD)

**Opciones:**

| Orden | Agentes | Por que |
|-------|---------|---------|
| **Adaptation -> Req -> Coder** | Flujo natural ISO | El flujo natural de ISO 12207: primero se adapta, luego se elicitan reqs, luego se codifica |
| **Coder -> Req -> Adaptation** | Ver resultados rapido | CoderAgent solo (sin Req ni Adaptation) ya produce codigo; las capas de analisis se anaden despues |
| **Req -> Adaptation -> Coder** | Reqs como contrato base | Primero se define el schema de requisitos como contrato, luego el resto del sistema se construye alrededor |

**Estado:** 🔴 (Opcion Aprobada: **Adaptation -> Req -> Coder**)

### 3.3 Estrategia de EventBus (MEDIA PRIORIDAD)

**Problema:** El EventBus existente en `agentic_pipeline/agents/event_bus.py` es sincrono e in-process. El PDCA-sdlc necesita un bus async con persistencia y replay.

**Opciones:**

| Opcion | Descripcion |
|--------|-------------|
| **Extender existente** | Anadir metodos async y persistencia al EventBus actual |
| **Adapter wrapper** | Crear un AsyncEventBus en PDCA-sdlc que envuelve al EventBus existente |
| **NATS JetStream nuevo** | Reemplazar con NATS JetStream, el EventBus actual queda como legacy |

**Recomendacion:** Opcion B (adapter). El EventBus actual se mantiene intacto. PDCA-sdlc crea un `AsyncEventBus` que lo envuelve y anade async, persistencia, y soporte de topicos jerarquicos.

**Estado:** 🟡 RECOMENDACION — adapter. (**APROBADA**)

### 3.4 Knowledge Graph: persistencia (BAJA PRIORIDAD)

**Opciones:** NetworkX (MVP en memoria), SQLite + extension grafo, Neo4j.

**Recomendacion:** NetworkX para Fase 1 (MVP), migrar a Neo4j en Fase 3.

**Estado:** 🟡 RECOMENDACION — NetworkX -> Neo4j.(**Aprobado**)

---

## 4. Fases de Implementacion

### Fase 1: Fundacion (Semanas 1-2)

**Objetivo:** MVP funcional con 3 agentes y Fast-Path routing.

**Componentes a construir:**

| Componente | Archivo | Depende de | Reuso |
|-----------|---------|-----------|-------|
| `core/__init__.py` | — | — | — |
| `core/event_bus.py` | EventBus async con topicos jerarquicos + adapter sobre existente | `agentic_pipeline/agents/event_bus.py` | Adapter |
| `core/knowledge_graph.py` | Grafo en memoria (NetworkX) | — | Nuevo |
| `core/capability_registry.py` | Registro de capacidades de agentes | — | Nuevo |
| `core/base_agent.py` | Clase abstracta BaseAgent | core/event_bus, core/kg, core/registry | Nuevo |
| `core/llm_client.py` | Cliente LLM generico con fallback | — | Nuevo |
| `agents/adaptation_agent.py` | Clasifica complejidad, selecciona procesos | core/base_agent, core/llm_client | Reusa planner.py |
| `agents/requirements_analyst.py` | NL -> structured requirements | core/base_agent, core/llm_client | Reusa requirement_decomposer.py |
| `agents/coder_agent.py` | Codificacion + tests unitarios | core/base_agent, core/llm_client | Pendiente decision (3.1) |
| `protocols/event_schemas.py` | Pydantic models de eventos | — | Nuevo |
| `tests/test_event_bus.py` | Tests de EventBus | core/event_bus | pytest |
| `tests/test_knowledge_graph.py` | Tests de KG | core/knowledge_graph | pytest |
| `tests/test_requirements_analyst.py` | Tests de RequirementsAnalyst | agents/requirements_analyst | pytest |
| `main.py` | Entrypoint: inicializa bus, KG, registry, agentes | Todo lo anterior | Nuevo |
| `config.yaml` | Config de modelos, topics, thresholds | — | Nuevo |

**Entregable:** `python -m compiler-bot.PDCA-sdlc.main "Quiero un CRUD de productos"` produce:
1. Proyecto clasificado (simple/moderate/complex)
2. Requisitos estructurados en Knowledge Graph
3. Codigo generado en `modules/<project>/`
4. Trazabilidad: req -> componente -> modulo en KG

**Tests esperados:** ~40 tests
**Riesgo:** Depende de decision 3.1 (CoderAgent) y 3.2 (orden)

### Fase 2: Expansion (Semanas 3-4)

**Objetivo:** Agentes de diseno, verificacion, y monitoreo. Swarm coordination.

**Componentes a construir:**

| Componente | Descripcion |
|-----------|-------------|
| `agents/architect_agent.py` | Diseno arquitectonico, decisiones (ADR) |
| `agents/verification_agent.py` | Quality Gates, trazabilidad, V&V |
| `agents/project_tracker.py` | Monitoreo de progreso, riesgos, reports |
| `core/swarm_coordinator.py` | Detecta completitud de eventos paralelos |
| `core/quality_gate.py` | Puntos de control con condiciones del KG |
| `tests/test_architect.py` | Tests de ArchitectAgent |
| `tests/test_verification.py` | Tests de VerificationAgent |
| `tests/test_swarm.py` | Tests de SwarmDetector |

**Entregable:** Deep-Path funcional para tareas complejas:
```
Adaptation -> Req -> Architect -> Coder -> Verification (con quality gates)
```

**Tests esperados:** ~80 tests acumulados

### Fase 3: Robustez (Semanas 5-6)

**Objetivo:** Agentes de soporte completo, MASS optimization, HITL.

**Componentes a construir:**

| Componente | Descripcion |
|-----------|-------------|
| `agents/tester_agent.py` | Tests de integracion, regression |
| `agents/doc_writer_agent.py` | Documentacion sincronizada con codigo |
| `agents/config_mgr_agent.py` | Versionado, lineas base, releases |
| `core/pdca_engine.py` | Motor PDCA: recolecta metricas, trigger MASS |
| `agents/hitl_gateway.py` | Puntos de intervencion humana |
| `tests/test_integration.py` | Tests de integracion multi-agente |
| `tests/test_pdca.py` | Tests del ciclo PDCA |

**Entregable:** Sistema completo con:
- Fast-Path para tareas simples (3 agentes)
- Deep-Path para proyectos complejos (8+ agentes)
- Quality Gates automaticos
- HITL en puntos de decision
- Dashboard de metricas

**Tests esperados:** ~150 tests acumulados

---

## 5. Trazabilidad ISO 12207 por Fase

| Proceso ISO 12207 | Actividad | Fase 1 | Fase 2 | Fase 3 |
|------------------|-----------|--------|--------|--------|
| **Adaptation** | Process Selection | ✅ | ✅ | ✅ |
| **Adaptation** | Lifecycle Modeling | ✅ | ✅ | ✅ |
| **Development** | Requirements Elicitation | ✅ | ✅ | ✅ |
| **Development** | Requirements Analysis | ✅ | ✅ | ✅ |
| **Development** | Architecture Design | — | ✅ | ✅ |
| **Development** | Detailed Design | — | ✅ | ✅ |
| **Development** | Software Implementation | ✅ | ✅ | ✅ |
| **Development** | Unit Testing | ✅ | ✅ | ✅ |
| **Development** | Integration Testing | — | — | ✅ |
| **Support** | Configuration Management | — | — | ✅ |
| **Support** | Verification | — | ✅ | ✅ |
| **Support** | Validation | — | ✅ | ✅ |
| **Support** | Documentation | — | — | ✅ |
| **Organizational** | Project Planning | — | ✅ | ✅ |
| **Organizational** | Progress Monitoring | — | ✅ | ✅ |
| **Organizational** | Risk Management | — | ✅ | ✅ |
| **Organizational** | Continuous Improvement | — | — | ✅ |

---

## 6. Dependencias

### 6.1 Externas

| Dependencia | Para que | Fase |
|------------|----------|------|
| `nats-py` | EventBus con NATS JetStream | Fase 2+ |
| `networkx` | Knowledge Graph en memoria | Fase 1 |
| `neo4j` (opcional) | Knowledge Graph persistente | Fase 3+ |
| `openrouter` / `litellm` | LLM routing con fallback | Fase 1 |

### 6.2 Internas (de agentic_pipeline)

| Dependencia | Uso | Tipo |
|------------|-----|------|
| `agents/event_bus.py` | Base para adapter | Import |
| `prompt_chain/observer_base.py` | Patron Quality Gates | Import |
| `orchestrator.py` | Sub-componente | Import |
| `nodes/planner.py` | Planificador | Import |
| `nodes/requirement_decomposer.py` | Descomposicion de reqs | Import |
| `nodes/synthesis.py` | Pendiente (3.1) | Pendiente |
| `templates/` | Scaffolding | File access |

### 6.3 No dependencias

Los siguientes componentes NO se reusan (son especificos del pipeline compilador NL):
- `nodes/preprocessor.py`, `nodes/lexer.py`, `nodes/parser.py`
- `nodes/semantic_analyzer.py`, `nodes/ir_generator.py`
- `nodes/ir_builder.py`, `nodes/ir_nodes.py`
- `nodes/validator.py`
- `feedback_loop.py`, `metrics_store.py`

---

## 7. Hitos y Criterios de Exito

| Hito | Fase | Criterio de exito | Fecha estimada |
|------|------|-------------------|----------------|
| **H1: MVP funcional** | F1 | `main.py "CRUD productos"` produce reqs + codigo + trazabilidad. Tests: 40 pass. Ruff: 0 errors. | Semana 2 |
| **H2: Diseno multi-agente** | F2 | Tarea compleja activa Architect + Verification automaticamente. Quality Gates evaluan trazabilidad. | Semana 4 |
| **H3: SDLC completo** | F3 | Ciclo completo: Adaptation -> Req -> Architect -> Coder -> Verification -> Docs -> Config. PDCA optimiza prompts. HITL funciona. | Semana 6 |
| **H4: Produccion** | F3+ | 150+ tests, integrado con CI, documentacion de agentes completa. | Semana 6-8 |

---

## 8. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| **Decisiones tecnicas pendientes (3.1, 3.2)** bloquean inicio | Alta | Alto | Resolver en revision tecnica antes de comenzar Fase 1 |
| **Acoplamiento con agentic_pipeline** demasiado fuerte | Media | Medio | Regla estricta: solo import unidireccional, adapters en PDCA-sdlc |
| **El bus de eventos existente no escala** a requerimientos async | Media | Medio | Adapter pattern: EventBus actual se mantiene, PDCA-sdlc usa wrapper async |
| **Cobertura de tests insuficiente** para agentes LLM (output no deterministico) | Media | Alto | Tests con LLM mockeado (como en agentic_pipeline existente) + tests de integracion con LLM real en CI separado |
| **El nuevo modulo duplica funcionalidad** del pipeline existente | Media | Medio | Review por fase: si un componente existente ya hace lo necesario, se reusa via adapter antes de crear uno nuevo |

---

## 9. Decisiones Pendientes (Checklist para Revision Tecnica)

- [ ] **3.1 CoderAgent + synthesis.py** — Elegir opcion A, B, o C
- [ ] **3.2 Orden Fase 1** — Elegir orden de agentes
- [ ] **3.3 EventBus** — Confirmar adapter sobre existente vs NATS directo
- [ ] **3.4 Knowledge Graph** — Confirmar NetworkX -> Neo4j

---

## 10. Proximos Pasos

1. Resolver decisiones tecnicas (3.1, 3.2) en revision tecnica
2. Aprobar este plan
3. Crear estructura de directorio `compiler-bot/PDCA-sdlc/`
4. Mover `docs/157_PLAN...` desde `.opencode/plans/` a `docs/` si se aprueba
5. Iniciar Fase 1: core infrastructure (EventBus, KG, Registry, BaseAgent)
6. Por cada componente completado: `ruff check . && ruff format . && python -m pytest tests/ -v -o "addopts="`

---

*Plan de implementacion basado en `154_PROP`, `155_PROP`, y `156_PROP`. Fecha: 2026-06-19. Pendiente de revision tecnica para decisiones 3.1 y 3.2.*
