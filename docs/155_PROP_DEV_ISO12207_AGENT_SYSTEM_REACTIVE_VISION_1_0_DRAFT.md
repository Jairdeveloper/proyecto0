---
id: "R04"
area: dev
type: prop
module: iso12207_agent_system
version: "1.0"
status: IMPLEMENTED
tags: ["proposal", "alternative", "iso12207", "event-driven", "capability-based", "reactive", "multi-agent", "swarm"]
summary: "Propuesta alternativa al sistema agentico ISO 12207 — arquitectura reactiva basada en capacidades, bus de eventos, y composicion dinamica, en contraste con la vision jerarquica de 154_PROP."
changelog:
  - version: "1.0"
    date: "2026-06-19"
    author: "Sistema"
    description: "Version inicial — propuesta alternativa reactiva vs jerarquica"
---

# Propuesta Alternativa: Sistema Agentico ISO 12207 — Arquitectura Reactiva de Capacidades

> **Vision alternativa a 154_PROP**  
> **Paradigma:** Bottom-up, event-driven, capability-based, emergent  
> **Contraste directo con:** Top-down, hierarchical, process-driven, orchestrated

---

## 0. Filosofia de Diseno: Dos Visiones

| Dimension | 154_PROP (Jerarquica) | Esta propuesta (Reactiva) |
|-----------|----------------------|---------------------------|
| **Control** | Centralizado (Orchestrator) | Distribuido (Event Bus) |
| **Flujo** | Pipeline lineal: Adaptation -> Req -> Arch -> Code -> Test -> Docs | Grafo de eventos: agentes reaccionan a cambios de estado |
| **ISO 12207** | Estructura impuesta: procesos = agentes | Metadata aplicada: procesos = tags sobre capacidades |
| **Acoplamiento** | Contratos formales entre capas | Contrato minimo: solo el schema del event bus |
| **Topologia** | Jerarquica 3 niveles | Plana: todos los agentes son peers |
| **Orquestacion** | Orchestrator decide quien sigue | Cada agente decide si reacciona al evento |
| **Estado** | Pasado por pipeline (workspace-per-task) | Grafo de conocimiento compartido (Knowledge Graph) |
| **Escalamiento** | Vertical (agregar agentes a la jerarquia) | Horizontal (agregar peers al bus) |
| **Tolerancia a fallos** | Checkpoint/Rollback por etapa | Replicacion de eventos + replay |
| **Ciclo de mejora** | Agente separado (Mejora Continua) | PDCA es el motor nativo del bus |

---

## 1. Arquitectura General

```
                    ┌─────────────────────────────┐
                    │       Event Bus (NATS/Redis)  │
                    │  (topico: proyecto.> )        │
                    └──────────┬──────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │ Capability    │   │ Knowledge     │   │ Agent        │
   │ Registry      │   │ Graph Store   │   │ Swarm        │
   └──────────────┘   └──────────────┘   └──────────────┘
          │                    │                    │
          │                    │                    │
          ▼                    ▼                    ▼
   ┌─────────────────────────────────────────────────────┐
   │              Pool de Agentes (Peers)                 │
   │                                                      │
   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │
   │  │Req Analyst│ │Architect │ │ Coder    │ │ Tester │  │
   │  └──────────┘ └──────────┘ └──────────┘ └────────┘  │
   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │
   │  │Doc Writer│ │Sec Engine│ │Config Mgr│ │UX Agent│  │
   │  └──────────┘ └──────────┘ └──────────┘ └────────┘  │
   └─────────────────────────────────────────────────────┘
```

**Principio:** No hay un orchestrador central. Cada agente es un peer autonomo que:

1. Se registra en el **Capability Registry** publicando que ISO 12207 actividades sabe ejecutar
2. Escucha el **Event Bus** por eventos que matchean sus capacidades
3. Cuando recibe un evento, evalua si debe actuar, actua, y emite nuevos eventos
4. Lee/escribe en el **Knowledge Graph** el estado compartido del proyecto

---

## 2. Componentes Fundamentales

### 2.1 Event Bus (Columna Vertebral)

**No es un lanzador de tareas.** Es un sistema de eventos donde fluye informacion sobre cambios de estado del proyecto.

**Topicos:**

| Topico | Eventos tipicos | Consumidores |
|--------|-----------------|--------------|
| `proyecto.{id}.requirement.created` | `{req_id, text, type, source}` | Architect, Doc Writer, Tester |
| `proyecto.{id}.architecture.proposed` | `{arch_id, components, decisions}` | Coder, Sec Engineer, UX |
| `proyecto.{id}.code.committed` | `{commit_id, files, diff_summary}` | Tester, Sec Engineer, Config Mgr |
| `proyecto.{id}.test.executed` | `{test_id, results, coverage}` | Coder (para debug), QA |
| `proyecto.{id}.artifact.published` | `{artifact_id, type, url}` | Doc Writer, Config Mgr |
| `proyecto.{id}.risk.identified` | `{risk_id, severity, description}` | Todos los agentes relevantes |
| `proyecto.{id}.quality.gate.failed` | `{gate, criteria, details}` | Agente responsable + mejora continua |

**Patron aplicado:** **A2A (Inter-Agent Communication)** del capitulo 15. El bus de eventos es el mecanismo de coordinacion. Agentes publican y se suscriben sin conocerse directamente.

### 2.2 Capability Registry

Cada agente publica un documento JSON con sus capacidades:

```json
{
  "agent_id": "req-analyst-v1",
  "name": "Requirements Analyst",
  "description": "Traduce lenguaje natural a requerimientos estructurados",
  "iso_12207_mapping": {
    "process": "Development",
    "activities": ["Requirements Elicitation", "Requirements Analysis"],
    "tasks": [
      "Define functional requirements",
      "Define business requirements",
      "Define user documentation requirements"
    ]
  },
  "triggers": [
    {"event": "project.initialized", "role": "primary"},
    {"event": "requirement.clarification_needed", "role": "primary"},
    {"event": "architecture.review.needs_requirements_input", "role": "secondary"}
  ],
  "output_events": [
    "requirement.created",
    "requirement.updated",
    "requirement.validated"
  ],
  "llm_profile": {
    "recommended_model": "flash",
    "max_tokens": 8192,
    "temperature": 0.2
  }
}
```

**Patron aplicado:** **Routing (LLM-based + Registry-based)** del capitulo 2. El registry permite routing dinamico: cuando un evento ocurre, el sistema consulta que agente tiene la capacidad de manejarlo.

### 2.3 Knowledge Graph (Estado Compartido)

En vez de pasar estado serializado por un pipeline, el estado del proyecto es un **grafo de conocimiento** accesible por todos los agentes.

**Nodos del grafo:**

| Tipo de nodo | Atributos | Creado por |
|-------------|-----------|------------|
| `Requirement` | id, text, type, status, priority, acceptance_criteria | Req Analyst |
| `ArchitectureDecision` | id, title, context, decision, consequences | Architect |
| `Component` | id, name, tech_stack, interfaces, status | Architect |
| `CodeModule` | id, path, language, coverage, last_commit | Coder |
| `TestSuite` | id, module_id, results, regression_status | Tester |
| `Risk` | id, description, severity, mitigation, status | cualquier agente |
| `Artifact` | id, type, location, version, generated_from | Doc Writer, Config Mgr |

**Aristas del grafo:**

- `requirement.SATISFIES.goal` — un requerimiento satisface un objetivo de negocio
- `component.IMPLEMENTS.requirement` — trazabilidad codigo -> req
- `test.VERIFIES.component` — cobertura de tests sobre componentes
- `archdecision.AFFECTS.component` — decisiones que impactan componentes
- `artifact.DOCUMENTS.module` — documentacion que describe codigo

**Patron aplicado:** **Memory Management** del capitulo 8: semantic memory (conocimiento factual del proyecto como grafo), episodic memory (historial de eventos como timeline), working memory (contexto inmediato del agente viniendo del ultimo evento).

### 2.4 Agent Swarm (Pool de Agentes)

Los agentes no tienen una relacion padre-hijo. Todos son peers en una **swarm**. Cuando ocurre un evento que requiere N capacidades, multiples agentes pueden reaccionar en paralelo o coordinarse via sub-eventos.

**Mecanismo de swarm para tareas complejas:**

```
Evento: requirement.created (req-042: "login with OAuth2")
         │
         ▼
  Swarm evalua: que capacidades se necesitan?
         │
         ├── Architect: disena componente auth
         ├── Security Engineer: evalua riesgos de OAuth2
         ├── UX Agent: disena flujo de login
         └── Doc Writer: prepara borrador de docs de autenticacion
         │
         ▼
  Cada agente trabaja en paralelo, emitiendo eventos cuando termina
         │
         ▼
  Swarm detecta que todos los sub-eventos han llegado -> emite
  event: design.complete (req-042)
```

**Patron aplicado:** **Parallelization** del capitulo 3 + **Multi-Agent** del capitulo 7 (topologia descentralizada peer-to-peer).

---

## 3. Mapeo ISO 12207 a Capacidades (No a Agentes)

La diferencia fundamental con 154_PROP: ISO 12207 no define la estructura del sistema, sino que es **metadata que los agentes se auto-asignan**.

```
ISO 12207 no es:  Agent_Requirements = ISO_12207_Requirements_Process
ISO 12207 es:     Agent_X.capabilities.iso_12207 = ["Requirements Elicitation", ...]
```

Un agente puede tener multiples capacidades de diferentes procesos ISO 12207. La composicion es libre:

| Agente | Capacidades ISO 12207 |
|--------|----------------------|
| **Req Analyst** | Requirements Elicitation, Requirements Analysis, User Documentation |
| **Architect** | Architecture Design, Detailed Design, Integration Planning |
| **Coder** | Software Implementation, Unit Testing, Code Review |
| **Tester** | Unit Testing, Integration Testing, Quality Assurance |
| **Sec Engineer** | Risk Management, Security Verification, Audit |
| **Config Mgr** | Configuration Management, Release Management, Change Control |
| **Doc Writer** | User Documentation, Technical Documentation, Training Material |
| **UX Agent** | User Interface Design, Usability Testing, Accessibility Review |
| **Project Tracker** | Project Planning, Progress Monitoring, Risk Tracking |

Esto permite **alta cohesion** (un agente tiene capacidades relacionadas) y **bajo acoplamiento** (los agentes no dependen entre si, solo del bus y el grafo).

---

## 4. Flujo Tipico: De "Quiero un login OAuth2" a Codigo

### Paso 1: Proyecto inicializado

```
Usuario envia: "Crea un modulo de autenticacion OAuth2"
       │
       ▼
Event Bus: project.initialized {description: "modulo auth OAuth2", project_id: "p-42"}
       │
       ▼
Req Analyst (escucha project.initialized):
  1. Lee la descripcion del proyecto
  2. Usa Prompt Chaining (cap 1): NL -> structured requirements
  3. Escribe al Knowledge Graph: Requirement nodes
  4. Emite: requirement.created {ids: [req-001, req-002, req-003]}
```

### Paso 2: Diseno colaborativo

```
requirement.created [req-001: "login con Google OAuth", req-002: "refresh token", req-003: "user profile"]
       │
       ▼ (swarm detection: se requieren architect + sec + ux)
       │
  ┌────┼────┐
  │    │    │
  ▼    ▼    ▼
Arch  Sec  UX
  │    │    │
  │    │    │
  ▼    ▼    ▼
Event Bus: architecture.proposed {req_ids: [...], components: [...]}
Event Bus: security.review.completed {req_ids: [...], risks: [...]}
Event Bus: ux.flow.proposed {req_ids: [...], screens: [...]}
       │
       ▼
  Swarm detector: todos los eventos de "design" han llegado
       │
       ▼
Event Bus: design.complete {req_ids: [req-001, req-002, req-003]}
```

### Paso 3: Codificacion paralela

```
design.complete
       │
       ▼ (swarm: cada componente a un Coder diferente)
       │
  ┌────┼────┐
  │    │    │
  ▼    ▼    ▼
Coder1 Coder2 Coder3
(auth) (token)(profile)
  │    │    │
  │    │    │
  ▼    ▼    ▼
Event Bus: code.committed {module: "auth-oauth", files: [...], req_ids: [...]}
Event Bus: code.committed {module: "token-mgmt", files: [...], req_ids: [...]}
Event Bus: code.committed {module: "user-profile", files: [...], req_ids: [...]}
```

### Paso 4: Verificacion reactiva

```
code.committed (auth-oauth)
       │
  ┌────┼────┐
  │    │    │
  ▼    ▼    ▼
Tester  Sec   Config

Tester: ejecuta tests -> emite test.executed
Sec: escanea vulnerabilidades -> emite security.review
Config: versiona el modulo -> emite artifact.published
       │
       ▼
  Quality Gate: todos los verificadores pasaron?
     │            │
     YES          NO
     │            │
     ▼            ▼
  design.complete  risk.identified {blocker: true}
  para req-001    → el agente responsable recibe alerta
```

### Paso 5: Documentacion continua

```
Doc Writer observa todos los eventos code.committed y architecture.proposed:
  - Por cada modulo nuevo, genera/actualiza documentacion tecnica
  - Por cada requisito completado, actualiza el manual de usuario
  - Emite: artifact.published {type: "docs", module: "auth-oauth"}
```

---

## 5. Ciclo PDCA como Motor Nativo

En 154_PROP, el ciclo PDCA es un agente separado (Mejora Continua). En esta propuesta, **PDCA es el motor interno del sistema**:

| Fase | Mecanismo |
|------|-----------|
| **PLAN** | El project.tracker emite `project.plan.proposed`. Los agentes reaccionan confirmando disponibilidad basada en su capability registry y carga actual. |
| **DO** | Los agentes ejecutan sus capacidades cuando los eventos relevantes ocurren. Sin orden central, pero con restricciones implicitas (no codificar si req.validated no ha ocurrido). |
| **CHECK** | Quality Gates: puntos en el flujo donde se evalua si las condiciones se cumplen antes de continuar. Implementado como agentes evaluadores que escuchan eventos especificos. |
| **ACT** | Metricas historicas del Knowledge Graph alimentan ajustes: prompts, thresholds, routing rules. **MASS** (cap 17) puede optimizar la topologia del swarm periodicamente. |

**La ventaja:** PDCA no es un modulo aparte que "mejora" el sistema. Es como el sistema funciona intrinsicamente. Cada evento es un PLAN, cada reaccion es un DO, cada quality gate es un CHECK, y cada ajuste de capacidad es un ACT.

---

## 6. Routing Inteligente: Fast-Path vs Deep-Path

La propuesta 154_PROP menciona un bypass para tareas simples. Esta propuesta incorpora un **routing nativo de 2 velocidades** como parte del Capability Registry:

```
Evento: project.initialized
       │
       ▼
  Complexity Classifier (agente liviano, modelo flash)
       │
       │
  ┌─────┴─────┐
  │           │
  ▼           ▼
SIMPLE      COMPLEX
(task)      (proyecto)
  │           │
  │           ▼
  │     Swarm detection:
  │     requisito -> arquitecto -> codigo -> test -> docs
  │     (paralelismo controlado, quality gates obligatorios)
  │
  ▼
Fast-Path:
  Req Analyst -> Coder -> Tester
  (lineal, 3 eventos, sin diseno arquitectonico)
  Para tareas tipo: "Agregar campo email a User entity"
```

**Criterios de clasificacion:**

| Factor | Simple | Complejo |
|--------|--------|----------|
| Archivos afectados | 1-2 | 3+ |
| Nuevas dependencias | No | Si |
| Cambio de esquema DB | No | Si |
| Riesgo de seguridad | Bajo | Medio+ |
| Requiere decision arquitectonica | No | Si |

**Patrones aplicados:** **Routing (LLM-based)** del capitulo 2 para clasificar, **Resource-Aware Optimization** del capitulo 16 para elegir el camino.

---

## 7. Contratos entre Agentes: Esquema Compartido, No Interfaces Fijas

En 154_PROP los contratos son formales entre capas (Pydantic rígido). Aca los contratos son **esquemas compartidos en el Knowledge Graph**:

```python
# No hay un contrato fijo entre Requirements y Architect.
# Hay un nodo Requirement en el grafo que ambos leen/escriben:

class Requirement(Node):
    id: str
    text: str
    type: Literal["functional", "business", "user"]
    status: Literal["draft", "validated", "approved", "implemented", "verified"]
    acceptance_criteria: list[str]
    trace: list[Edge]  # hacia goals, componentes, tests
```

**Ventaja:** Si el Req Analyst anade un campo nuevo (`security_classification`), el Architect no se rompe. Solo los agentes que necesitan ese campo lo usan. El acoplamiento es minimal.

**Desventaja:** Sin validacion estricta en los boundaries, los errores se detectan mas tarde. Mitigacion: **Guardrails (Output Filtering)** del capitulo 18 en cada publicacion de evento.

---

## 8. Manejo de Fallos: Replay de Eventos, No Checkpoint/Rollback

En 154_PROP el fallo se maneja con checkpoint/rollback por etapa del pipeline. En esta propuesta:

```
Fallo: Coder genera codigo con error de compilacion
       │
       ▼
Event Bus: code.failed {module: "auth-oauth", error: "compilation error", details: {...}}
       │
       ▼
Coder recibe su propio evento de fallo:
  1. Recupera el requirement del Knowledge Graph
  2. Recupera el architecture.decision asociado
  3. Analiza el error (Self-Correction, cap 17)
  4. Genera nueva version y emite code.committed
       │
       ▼
Si falla N veces seguidas -> emite risk.identified {type: "stuck_task", escalation: true}
       │
       ▼
Swarm puede re-asignar la tarea a otro Coder, o escalar a humano (HITL, cap 13)
```

**Mecanismo de replay:** El Event Bus persiste todos los eventos. Si un agente se cae y vuelve, reproduce los eventos relevantes para reconstruir su estado. No necesita checkpoint explicito: el flujo de eventos ES el checkpoint.

---

## 9. Mejora Continua: MASS Periodico + Aprendizaje por Refuerzo

En vez de un agente de mejora continua que "observa" el sistema, el sistema se auto-optimiza:

1. **MASS (cap 17) semanal:** El sistema toma el log de eventos del Knowledge Graph, corre MASS (Multi-Agent System Search) para optimizar:
   - Prompts individuales de cada agente (Block-Level)
   - Topologia del swarm (Workflow Topology)
   - Prompts del sistema completo (Workflow-Level)

2. **Aprendizaje por refuerzo implicito:**
   - Eventos exitosos (test.passed, quality.gate.approved) refuerzan los paths actuales
   - Eventos fallidos (test.failed, risk.identified) debilitan esos paths
   - El Capability Registry se actualiza con pesos: "Coder-A es bueno para modulos NestJS, Coder-B para APIs REST"

---

## 10. Implementacion Progresiva (Fast MVP)

El principio de esta arquitectura es que **un MVP funcional con 3 agentes ya produce valor**, a diferencia de la propuesta jerarquica donde todas las capas deben existir.

### Fase 1: Fundacion (semana 1-2)

| Componente | Tecnologia | Resultado |
|-----------|-----------|-----------|
| Event Bus | Redis Streams o NATS JetStream | Topicos basicos |
| Knowledge Graph | SQLite con extensiom de grafo (o NetworkX en memoria) | Nodos Requirement, Component, CodeModule |
| Agentes | 3: Req Analyst, Coder, Tester | Pipeline basico: NL -> req -> codigo -> test |
| Fast-Path routing | Reglas deterministicas | Clasificador simple/complejo |

### Fase 2: Expansion (semana 3-4)

| Componente | Anade |
|-----------|-------|
| Agente Architect | Diseno de componentes |
| Agente Doc Writer | Documentacion automatica |
| Capability Registry | Registro dinamico de agentes |
| Swarm detection | Coordinacion multi-agente para tareas complejas |

### Fase 3: Robustez (semana 5-6)

| Componente | Anade |
|-----------|-------|
| Quality Gates | Verificacion cruzada entre agentes |
| MASS optimization | Optimizacion periodica de prompts y topologia |
| Event replay | Recuperacion ante fallos |
| Deep-Path routing | Pipeline completo para tareas complejas |

### Fase 4: Escala (semana 7-8)

| Componente | Anade |
|-----------|-------|
| HITL | Puntos de intervencion humana |
| Guardrails | Seguridad multi-capa |
| ISO 5338 + 38507 | Gobierno de IA y calidad de datos |
| Dashboard | Monitoreo de KPIs del sistema |

---

## 11. Tabla Comparativa: 154_PROP vs Esta Propuesta

| Aspecto | 154_PROP (Jerarquica) | Esta propuesta (Reactiva) |
|---------|----------------------|---------------------------|
| **Tiempo hasta MVP** | 4-6 semanas (necesita todas las capas) | 1-2 semanas (3 agentes + bus ya producen) |
| **Complejidad inicial** | Alta (5 capas, contratos formales, schema fijo) | Baja (bus + grafo + agentes peer) |
| **Latencia tipica** | 3.5-14 min (7 handoffs secuenciales) | 1-5 min (eventos paralelos, no secuenciales) |
| **Tolerancia a fallos** | Checkpoint/Rollback por etapa | Replay de eventos (el bus es el checkpoint) |
| **Escalamiento** | Vertical (jerarquia fija) | Horizontal (nuevos peers al bus) |
| **Acoplamiento** | Medio-alto (contratos entre capas) | Bajo (solo el schema del bus) |
| **Trazabilidad** | Issue-based (RECPL) | Event-based (timeline completo) |
| **Flexibilidad ISO** | Baja (ISO = estructura) | Alta (ISO = metadata) |
| **Costo operacional** | Mayor (cada etapa paga overhead de handoff) | Menor (eventos ligeros, paralelismo nativo) |
| **Curva de aprendizaje** | Alta (entender 5 capas + contratos) | Media (event bus + grafo + patrones reactivos) |
| **Debugging** | Dificil (estado distribuido en pipeline) | Mas facil (event replay = reproduccion exacta) |
| **PDCA** | Agente separado | Motor nativo del sistema |

---

## 12. Riesgos Especificos de Esta Propuesta

| Riesgo | Severidad | Mitigacion |
|--------|-----------|------------|
| **Eventos fuera de orden** | Alta | Usar Redis Streams con consumer groups que garantizan orden por particion. Version de eventos con timestamps + sequence numbers. |
| **Tormenta de eventos** un cambio pequeno puede generar N eventos que saturan el bus | Media | Throttling por agente, windowing (acumular eventos en ventanas de 100ms), debouncing de eventos redundantes. |
| **Consistencia eventual** el Knowledge Graph puede tener datos inconsistentes temporalmente | Media | Usar eventos de compensacion (Saga pattern). Quality Gates detectan inconsistencias antes de continuar. |
| **Swarm deadlock** dos agentes esperando mutuamente por un evento que nunca llega | Alta | Timeout por tarea con escalation. Si un sub-evento no llega en N segundos, el swarm detector emite risk.identified. |
| **Sobrecarga cognitiva** el usuario no entiende como funciona el sistema "invisible" | Media | Dashboard en tiempo real mostrando el flujo de eventos, agentes activos, y estado del grafo. |
| **ISO 12207 no garantizado** como metadata, no hay enforcement de que el proceso se siga correctamente | Media | Quality Gates obligatorios en puntos clave. Auditoria periodica: un agente externo verifica que los eventos en el bus corresponden a las actividades ISO 12207 requeridas. |

---

## 13. Stack Tecnologico Sugerido

| Componente | Opcion primaria | Alternativa |
|-----------|----------------|-------------|
| **Event Bus** | NATS JetStream | Redis Streams |
| **Knowledge Graph** | Neo4j (produccion) / NetworkX (MVP) | PostgreSQL + pgvector |
| **Agentes** | LangGraph (sub-graphs reactivos) + LangChain tools | CrewAI con procesos no secuenciales |
| **Capability Registry** | etcd / Redis | JSON schema + git |
| **Swarm Detection** | LangGraph (conditional edges con fan-out) | Custom Python con asyncio |
| **Quality Gates** | Agentes evaluadores dedicados + LLM-as-a-Judge | pytest + validation hooks |
| **MASS Optimization** | DSPy (goldset + objective function) | Optuna + LLM evaluator |
| **Guardrails** | Pydantic + policy enforcer agent (CrewAI) | Vertex AI callbacks |
| **Dashboard** | Streamlit / Grafana | React + WebSocket |
| **LLM Routing** | OpenRouter (auto model selection + fallback) | LiteLLM |

---

## 14. Conclusion

Esta propuesta presenta una **alternativa radical** a la vision jerarquica de 154_PROP:

- Donde 154_PROP construye una **piramide de procesos**, esta construye un **ecosistema de capacidades**
- Donde 154_PROP impone ISO 12207 desde arriba, esta propuesta lo deja **emerger desde abajo**
- Donde 154_PROP orquesta con un conductor, esta propuesta **deja que los musicos escuchen y toquen**

Ambas visiones son validas. La eleccion depende del caso de uso:

- **Elegir 154_PROP** si: el sistema tiene requisitos estrictos de auditoria, el equipo entiende y acepta la rigidez del pipeline, y el costo de latencia es aceptable para el dominio.
- **Elegir esta propuesta** si: se valora la flexibilidad y evolucion organica, se necesita un MVP rapido, y el sistema operara en un entorno donde los requisitos y la arquitectura cambian frecuentemente.

---

*Propuesta alternativa generada de los patrones en `152_GUIDE_DEV_AGENT_PATTERNS_SUMMARY_1_0_DRAFT.md` y `153_GUIDE_DEV_AGENT_DESIGN_PATTERNS2_SUMMARY_1_0_DRAFT.md`. Fecha: 2026-06-19.*
