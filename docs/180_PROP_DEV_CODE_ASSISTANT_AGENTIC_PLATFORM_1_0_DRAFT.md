---
id: 180
area: DEV
type: PROP
module: CODE_ASSISTANT_AGENTIC_PLATFORM
version: 1.0
status: DRAFT
tags:
  - proposal
  - architecture
  - migration
  - agentic-platform
  - roadmap
  - world-model
  - goal-manager
  - intention-graph
  - reasoning-memory
  - experience-engine
  - cost-optimizer
  - model-router
  - timeline
  - prediction-engine
  - agentic-ir
summary: "Propuesta de extension cognitiva para la Code Assistant Agentic Platform — World Model, Goal Manager, Intention Graph, Reasoning Memory, Experience Engine, Cost Optimizer, Multi-Model Router, Repository Timeline, Prediction Engine y Agentic IR. Corrige y amplia la propuesta 179."
keywords:
  - world-model
  - goal-manager
  - intention-graph
  - reasoning-memory
  - experience-engine
  - cost-optimizer
  - multi-model-router
  - repository-timeline
  - prediction-engine
  - agentic-ir
  - cognitive-architecture
changelog:
  - version: 1.0
    date: 2026-06-20
    author: system
    changes:
      - "Creacion de propuesta de extension cognitiva post-179"
---

# Propuesta de Extension Cognitiva — Code Assistant Agentic Platform

**Version del documento:** 1.0
**Fecha:** 2026-06-20
**Pre-requisito:** F3 completado + propuesta 179 aceptada
**Relacion:** Continuacion directa de `docs/179_PROP_DEV_CODE_ASSISTANT_AGENTIC_PLATFORM_1_0_DRAFT.md`
**Estado:** PROPUESTA — incorpora observaciones y correcciones sobre 179

---

## Tabla de Contenidos

1. [Proposito de este documento](#1-proposito-de-este-documento)
2. [Correccion: Agentic IR (no eliminar IR canonico)](#2-correccion-agentic-ir-no-eliminar-ir-canonico)
3. [World Model](#3-world-model)
4. [Goal Manager](#4-goal-manager)
5. [Intention Graph](#5-intention-graph)
6. [Reasoning Memory](#6-reasoning-memory)
7. [Experience Engine](#7-experience-engine)
8. [Cost Optimizer](#8-cost-optimizer)
9. [Multi-Model Router](#9-multi-model-router)
10. [Repository Timeline](#10-repository-timeline)
11. [Prediction Engine](#11-prediction-engine)
12. [Arquitectura Integrada (179 + 180)](#12-arquitectura-integrada-179--180)
13. [Arbol de archivos actualizado](#13-arbol-de-archivos-actualizado)
14. [Roadmap actualizado (F4-F8)](#14-roadmap-actualizado-f4-f8)
15. [Tabla de esfuerzo actualizada](#15-tabla-de-esfuerzo-actualizada)
16. [Autonomia: diferencias entre 9/10 y 10/10](#16-autonomia-diferencias-entre-910-y-1010)

---

## 1. Proposito de este documento

### 1.1 Relacion con 179

El documento `179_PROP_DEV_CODE_ASSISTANT_AGENTIC_PLATFORM_1_0_DRAFT.md` establecio la vision arquitectonica general: migrar de pipeline-centric a agent-centric, con Repository Graph, 9 agentes especializados, 16 herramientas, memoria de 3 niveles, Prompt Pipeline, LangGraph dinamico y roadmap F4-F7.

Este documento **no reemplaza** a 179. Lo **extiende y corrige** en 10 areas identificadas durante la revision:

| Area | Tipo | Descripcion |
|------|------|-------------|
| World Model | Nuevo | Capa superior al Repository Graph para estado global del proyecto |
| Goal Manager | Nuevo | Descomposicion de requests multi-objetivo |
| Intention Graph | Nuevo | Trazabilidad completa intento → goal → decision → task → action → result |
| Reasoning Memory | Nuevo | 4to nivel de memoria: el razonamiento detras de cada decision |
| Experience Engine | Nuevo | Aprendizaje continuo desde la ejecucion de tareas |
| Cost Optimizer | Nuevo | Ruteo inteligente: herramienta > LLM cuando sea posible |
| Multi-Model Router | Nuevo | Modelo optimo para cada tipo de tarea |
| Repository Timeline | Nuevo | Historial temporal de cambios |
| Prediction Engine | Nuevo | Prediccion de impacto antes de ejecutar |
| Agentic IR | Correccion | No eliminar IR canonico; mantener IR de alto nivel como contrato |

### 1.2 Puntuacion de autoevaluacion

Este documento surge de identificar las brechas entre 9/10 y 10/10 en las capacidades cognitivas del sistema. Cada seccion aborda una carencia especifica:

| Area evaluada | Nota en 179 | Que falta para 10/10 | Seccion en 180 |
|---------------|-------------|----------------------|----------------|
| Agentes | 9/10 | Capacidad de entender estado global del proyecto | §3 World Model |
| Herramientas | 9/10 | Decision inteligente: herramienta vs LLM | §8 Cost Optimizer |
| Prompt Pipeline | 9/10 | Enrutamiento a modelo optimo por tarea | §9 Multi-Model Router |
| Memoria | 8/10 | Memoria de razonamiento (no solo resultados) | §6 Reasoning Memory |
| Planificacion | 8/10 | Descomposicion de objetivos multiples | §4 Goal Manager |
| Autonomia | 7/10 | Aprendizaje continuo, prediccion de impacto | §7 Experience Engine, §11 Prediction Engine |

---

## 2. Correccion: Agentic IR (no eliminar IR canonico)

### 2.1 Problema identificado

La propuesta 179 (§13.4) establecia:

> `agentic_pipeline/nodes/ir_generator.py` → **Remover** (IR ya no es necesario)

Esta decision es parcialmente incorrecta. El IR canonico actual (mapeo de AST a JSON con acciones, modulos, entidades, tech_stack) es efectivamente un artifacto del pipeline de compilacion que pierde sentido cuando el centro del sistema deja de ser el pipeline.

Sin embargo, **eliminar completamente el IR** crea un vacio: no hay un contrato formal entre el planificador (PlanningAgent) y los ejecutores (CodingAgent, RefactorAgent, TestAgent).

### 2.2 Solucion: Agentic IR

Se introduce un **Agentic IR** (AIR): un formato de representacion intermedia de **alto nivel** que captura la intencion de una tarea, no el codigo generado.

```python
@dataclass
class AgenticIR:
    """Representacion Intermedia Agentica.
    
    No describe codigo. Describe la INTENCION de una tarea.
    Sirve como contrato entre PlanningAgent y los agentes ejecutores.
    """
    ir_id: str                          # UUID
    goal: str                           # "Create CRUD module"
    entity: str                         # "User"
    framework: str                      # "NestJS"
    constraints: list[str]              # ["DDD", "JWT", "Clean Architecture"]
    parent_ir: str | None               # IR padre (para sub-tareas)
    dependencies: list[str]             # IR IDs que deben completarse antes
    acceptance_criteria: list[str]      # Criterios de exito
    estimated_complexity: str           # simple | moderate | complex
    model_preference: str | None        # Modelo LLM recomendado para esta tarea
```

### 2.3 Ejemplo de uso

```json
{
  "ir_id": "air-001",
  "goal": "Create CRUD module",
  "entity": "User",
  "framework": "NestJS",
  "constraints": ["DDD", "JWT"],
  "parent_ir": null,
  "dependencies": [],
  "acceptance_criteria": [
    "User entity with email, password, role",
    "AuthController with login/register/refresh",
    "JWT guard protecting /users/*"
  ],
  "estimated_complexity": "moderate",
  "model_preference": "claude-sonnet-4"
}
```

### 2.4 Flujo del Agentic IR

```
User Request
      │
      ▼
IntentRouter
      │
      ▼
GoalManager
      │
      ▼
PlanningAgent ──→ genera uno o mas AgenticIR
      │                    │
      │         ┌──────────┼──────────┐
      │         ▼          ▼          ▼
      │    AgenticIR   AgenticIR   AgenticIR
      │    "auth"      "users"     "docs"
      │         │          │          │
      └─────────┼──────────┼──────────┘
                ▼          ▼          ▼
          CodingAgent  CodingAgent  DocAgent
                │          │          │
                └──────────┼──────────┘
                           ▼
                     Validacion
                           │
                      ReviewAgent
```

### 2.5 Beneficios del Agentic IR

| Beneficio | Explicacion |
|-----------|-------------|
| **Contrato formal** | PlanningAgent produce AIR, agentes ejecutores lo consumen. Interfaz clara. |
| **Framework-agnostico** | El AIR no menciona archivos ni codigo. Solo intencion. Los agentes deciden como implementar. |
| **Divisible** | Un AIR padre genera N AIR hijos. Cada sub-tarea tiene su propio contrato. |
| **Trazable** | Cada AIR tiene ID. Se almacena en el Intention Graph. Se puede responder "por que se creo este archivo?" |
| **Ruteable** | `model_preference` permite al Multi-Model Router elegir el modelo optimo. |
| **Versionable** | El AIR evoluciona. Se puede comparar AIR v1 vs AIR v2 para ver cambios de intencion. |

### 2.6 Mapeo: IR canonico → Agentic IR

| Aspecto | IR canonico (actual) | Agentic IR (nuevo) |
|---------|---------------------|---------------------|
| **Proposito** | Representar codigo generado | Representar intencion de tarea |
| **Origen** | AST del parser | Goal Manager → PlanningAgent |
| **Consumidor** | ActionExecutor (generators) | CodingAgent, RefactorAgent, TestAgent, DocAgent |
| **Contenido** | tokens, AST nodes, symbol table | goal, entity, framework, constraints, acceptance_criteria |
| **Formato** | JSON anidado con actions, modules | JSON plano con IR IDs y dependencias |
| **Persistencia** | Transitorio (en pipeline) | Permanente (en Intention Graph) |
| **Version** | No versionado | Versionado con changelog |

### 2.7 Implementacion

No se elimina el IR canonico existente. Se **congela** como parte del pipeline legacy. El Agentic IR se implementa como un nuevo modulo:

```
compiler-bot/core/agentic_ir.py
├── AgenticIR (dataclass)
├── AgenticIRBuilder (construye AIR desde Goal)
├── AgenticIRSerializer (JSON / YAML)
├── AgenticIRValidator (valida integridad: campos requeridos, referencias)
└── AgenticIRGraph (DAG de AIRs para trazabilidad)
```

---

## 3. World Model

### 3.1 Que es

El **World Model** es una capa superior al Repository Graph que modela el **estado global del proyecto**, no solo su codigo fuente.

```
Repository Graph         World Model
┌──────────────┐       ┌──────────────────────┐
│ SourceFile   │       │ Microservices        │
│ Class        │       │ Dependencies         │
│ Method       │       │ Databases            │
│ Function     │       │ Infrastructure       │
│ Interface    │       │ CI/CD pipelines      │
│ Endpoint     │       │ Roadmap              │
│ Entity       │       │ Issues               │
│ DTO          │       │ Open PRs             │
│ Test         │       │ Test results         │
│ Import       │       │ Coverage trends      │
│ Dependency   │       │ Known bugs           │
└──────────────┘       │ Deployments          │
        │              │ Environment configs  │
        ▼              │ Team ownership       │
   "Que archivos       │ SLA / SLO            │
    existen?"          └──────────────────────┘
                               │
                          "Que esta pasando
                           en el proyecto?"
```

### 3.2 Componentes del World Model

| Componente | Descripcion | Fuente de datos |
|------------|-------------|-----------------|
| **ServiceMap** | Topologia de microservicios y sus conexiones | docker-compose, kubernetes manifests, code analysis |
| **DependencyGraph** | Dependencias externas (npm, pip, maven) con versiones | package.json, pyproject.toml, go.mod |
| **DatabaseSchema** | Modelo de datos completo: tablas, relaciones, indices | Prisma schema, TypeORM entities, SQLAlchemy models |
| **InfrastructureMap** | Infraestructura: contenedores, colas, caches, buckets | Dockerfile, docker-compose, Terraform, CloudFormation |
| **CIDashboard** | Estado de pipelines CI/CD | GitHub Actions, GitLab CI, Jenkins API |
| **RoadmapTracker** | Features planificadas, en progreso, completadas | Issues, milestones, project boards |
| **IssueTracker** | Bugs, features, tech debt items con estado | GitHub Issues, Jira API |
| **PRTracker** | Pull requests abiertos, revisados, mergeados | GitHub / GitLab API |
| **TestDashboard** | Resultados de tests: pasados, fallidos, cobertura historica | TestRunnerTool, coverage reports |
| **BugTracker** | Bugs conocidos con severidad, impacto, area | Issue tracker, monitoring alerts |
| **DeploymentHistory** | Historial de despliegues: version, timestamp, estado | CI/CD pipelines, container registry |
| **TeamModel** | Quien es dueno de cada modulo/area | CODEOWNERS, git blame history |
| **SLOMonitor** | SLA/SLO: latencia, disponibilidad, error budget | Monitoring APIs (Datadog, Grafana) |

### 3.3 Integracion con el Knowledge Graph

```python
class NodeType(str, Enum):
    # ... tipos existentes + Repository Graph types ...
    
    # World Model types
    MICROSERVICE = "microservice"
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"
    CI_PIPELINE = "ci_pipeline"
    ROADMAP_ITEM = "roadmap_item"
    ISSUE = "issue"
    PULL_REQUEST = "pull_request"
    DEPLOYMENT = "deployment"
    ENVIRONMENT = "environment"
    SLO = "slo"
    TEAM = "team"
    SERVICE_OWNER = "service_owner"

class EdgeType(str, Enum):
    # ... tipos existentes + Repository Graph types ...
    
    # World Model edges
    DEPLOYS_TO = "deploys_to"           # Microservice → Environment
    CONNECTS_TO = "connects_to"         # Microservice → Database
    DEPENDS_ON_SERVICE = "depends_on_service"  # Microservice → Microservice
    MONITORED_BY = "monitored_by"       # Service → SLO
    OWNED_BY = "owned_by"               # Module → Team
    TRACKED_BY = "tracked_by"           # Feature → Issue
    RESOLVED_BY = "resolved_by"         # Issue → PullRequest
    DEPLOYED_IN = "deployed_in"         # Commit → Deployment
```

### 3.4 Queries que el World Model permite responder

| Pregunta | Query |
|----------|-------|
| "Cual es la topologia de servicios?" | `MICROSERVICE --[connects_to/depends_on_service]--> *` |
| "Que servicios afecta esta base de datos?" | `DATABASE <--[connects_to]-- MICROSERVICE` |
| "Que PRs estan abiertos para este modulo?" | `MODULE <--[changes]-- PULL_REQUEST WHERE state=open` |
| "Cual es la cobertura de tests de este servicio?" | `MICROSERVICE --[has]--> TEST_SUITE` |
| "Hay bugs abiertos en auth?" | `BUG WHERE area=auth AND state=open` |
| "Quien es dueno de este modulo?" | `MODULE --[owned_by]--> TEAM` |
| "Cual fue el ultimo deploy a produccion?" | `DEPLOYMENT WHERE environment=production ORDER BY timestamp DESC LIMIT 1` |
| "Que servicios dependen de este microservicio?" | `MICROSERVICE <--[depends_on_service]-- MICROSERVICE` |

### 3.5 WorldModelAgent

```python
class WorldModelAgent(Agent):
    """Mantiene actualizado el World Model del proyecto.
    
    Se suscribe a eventos del mundo exterior (GitHub, CI, monitoreo)
    y actualiza el Knowledge Graph con el estado global.
    """
    
    manifest = CapabilityManifest(
        agent_id="world-model-agent",
        description="Maintains project-level global state",
        triggers=[
            "external.github.push",
            "external.github.pr.*",
            "external.github.issue.*",
            "external.ci.*",
            "external.deploy.*",
            "schedule.hourly"  # Actualizacion periodica
        ],
        output_events=[
            "world.model.updated",
            "world.model.risk.identified"
        ]
    )
    
    async def handle_event(self, event: Event):
        if event.topic == "external.github.push":
            await self._update_from_push(event.data)
        elif event.topic.startswith("external.github.pr"):
            await self._update_prs(event.data)
        elif event.topic.startswith("external.github.issue"):
            await self._update_issues(event.data)
        elif event.topic == "external.ci.completed":
            await self._update_ci_status(event.data)
        
        await self.event_bus.publish(Event(
            topic="world.model.updated",
            data={"timestamp": time.time()}
        ))
```

---

## 4. Goal Manager

### 4.1 Problema

Una peticion puede contener multiples objetivos:

> "Agrega autenticacion, documenta la API y mejora el rendimiento"

El sistema actual trataria esto como un unico goal, forzando a todos los agentes a trabajar en paralelo sobre objetivos no relacionados.

### 4.2 Solucion: Goal Manager

```python
class GoalManager:
    """Descompone una solicitud en objetivos atomicos e independientes.
    
    1. Recibe request del IntentRouter
    2. LLM clasifica: cuantos objetivos hay? son independientes?
    3. Crea N nodos GOAL en el Knowledge Graph
    4. Para cada goal, decide si requiere PlanningAgent o es directo
    5. Publica eventos goal.created por cada objetivo
    """
    
    async def decompose(self, request: str) -> list[Goal]:
        """Descompone request en objetivos atomicos."""
        
        # LLM call: extraer objetivos
        prompt = f"""Descompone la siguiente solicitud en objetivos atomicos.
Cada objetivo debe ser independiente y ejecutable por separado.

Solicitud: {request}

Responde SOLO con JSON:
{{
  "goals": [
    {{
      "id": "g-001",
      "description": "descripcion corta",
      "type": "feature|refactor|doc|test|security|performance",
      "dependencies": [],  // IDs de otros goals de los que depende
      "priority": "high|medium|low"
    }}
  ]
}}
"""
        response = await self.llm.complete(prompt)
        goals = self._parse_goals(response)
        
        # Almacenar en Knowledge Graph
        for goal in goals:
            await self.kg.add_node(Node(
                id=goal.id,
                node_type=NodeType.GOAL,
                properties={
                    "description": goal.description,
                    "type": goal.type,
                    "priority": goal.priority,
                    "status": "pending"
                }
            ))
        
        # Establecer dependencias entre goals
        for goal in goals:
            for dep_id in goal.dependencies:
                await self.kg.add_edge(Edge(
                    source_id=goal.id,
                    target_id=dep_id,
                    edge_type=EdgeType.DEPENDS_ON
                ))
        
        return goals
```

### 4.3 Flujo del Goal Manager

```
Request: "Agrega autenticacion, documenta la API y mejora el rendimiento"
      │
      ▼
GoalManager.decompose()
      │
      ├── Goal 1: "Implement JWT authentication"  (type: feature, priority: high)
      ├── Goal 2: "Document public API endpoints"  (type: doc, priority: medium)
      │     └── depends_on: Goal 1  (primero hay que crear los endpoints, luego documentarlos)
      └── Goal 3: "Optimize database queries"      (type: performance, priority: low)
      │
      ▼
Knowledge Graph
  ├── GOAL g-001: "Implement JWT authentication" ─── status: pending
  ├── GOAL g-002: "Document public API endpoints" ─── status: pending
  │     └── DEPENDS_ON → g-001
  └── GOAL g-003: "Optimize database queries" ─── status: pending
  
      │
      ▼
EventBus publica:
  ├── goal.created (g-001)
  ├── goal.created (g-002)
  └── goal.created (g-003)

      │
      ▼
PlanningAgent recibe cada goal.created por separado
  └── Para cada goal, genera su propio Task Graph y AgenticIR
```

### 4.4 Beneficios

| Beneficio | Explicacion |
|-----------|-------------|
| **Paralelismo** | Goals independientes se ejecutan en paralelo |
| **Priorizacion** | Goals de alta prioridad se ejecutan primero |
| **Trazabilidad** | Cada archivo generado se asocia a un goal especifico |
| **Cancelacion** | Si un goal falla, los que dependen de el se marcan como "blocked" |
| **Progreso** | Se puede reportar "3/5 goals completados" |

---

## 5. Intention Graph

### 5.1 Que es

El **Intention Graph** es un DAG que almacena la trazabilidad completa de cada decision:

```
Intent
  │
  ▼
Goal
  │
  ▼
SubGoal
  │
  ▼
Decision  ──── Razón: "elegimos X porque Y"
  │
  ▼
Task (AgenticIR)
  │
  ▼
Action (tool call)
  │
  ▼
Result (archivo generado, test pasado, etc.)
```

### 5.2 Estructura en el Knowledge Graph

```python
class NodeType(str, Enum):
    # ... existentes ...
    
    # Intention Graph types
    INTENT = "intent"               # La intencion original del usuario
    GOAL = "goal"                   # Objetivo atomico (del Goal Manager)
    SUBGOAL = "subgoal"             # Sub-objetivo dentro de un goal
    DECISION = "decision"           # Decision arquitectonica o de diseno
    REASON = "reason"               # Razon detras de una decision
    TASK_IR = "task_ir"             # AgenticIR
    ACTION = "action"               # Accion concreta (tool call)
    ACTION_RESULT = "action_result"  # Resultado de una accion
    REJECTED_ALTERNATIVE = "rejected_alternative"  # Alternativa considerada pero rechazada

class EdgeType(str, Enum):
    # ... existentes ...
    
    # Intention Graph edges
    MOTIVATES = "motivates"          # Intent → Goal (que motivo este goal)
    DECOMPOSES_TO = "decomposes_to"  # Goal → SubGoal
    RESULTS_IN = "results_in"        # Decision → Task (la decision resulto en esta tarea)
    EXECUTED_AS = "executed_as"      # Task → Action (la tarea se ejecuto como...)
    PRODUCES = "produces"            # Action → ActionResult
    REJECTED_IN_FAVOR_OF = "rejected_in_favor_of"  # RejectedAlternative → Decision
    BECAUSE = "because"              # Decision → Reason (se decidio X porque Y)
    EVIDENCE_OF = "evidence_of"      # ActionResult → Reason (el resultado confirma la razon)
```

### 5.3 Ejemplo completo de trazabilidad

```
Intent: "Agrega autenticacion JWT al proyecto"
  │
  ├── MOTIVATES → Goal: "Implement JWT authentication"
  │                  │
  │                  ├── DECOMPOSES_TO → SubGoal: "Design auth architecture"
  │                  │     │
  │                  │     └── RESULTS_IN → Decision: "Use Passport.js JWT strategy"
  │                  │           │
  │                  │           ├── BECAUSE → Reason: "NestJS has native Passport support"
  │                  │           ├── BECAUSE → Reason: "Team is familiar with Passport"
  │                  │           ├── REJECTED_IN_FAVOR_OF → RejectedAlternative: "Custom JWT middleware"
  │                  │           │     └── BECAUSE → Reason: "Would require more boilerplate"
  │                  │           │
  │                  │           └── RESULTS_IN → TaskIR: air-002 (auth module)
  │                  │                 │
  │                  │                 ├── EXECUTED_AS → Action: "WriteFileTool: auth.module.ts"
  │                  │                 │     └── PRODUCES → ActionResult: auth.module.ts (created)
  │                  │                 ├── EXECUTED_AS → Action: "WriteFileTool: jwt.strategy.ts"
  │                  │                 │     └── PRODUCES → ActionResult: jwt.strategy.ts (created)
  │                  │                 └── EXECUTED_AS → Action: "WriteFileTool: auth.controller.ts"
  │                  │                       └── PRODUCES → ActionResult: auth.controller.ts (created)
  │                  │
  │                  └── DECOMPOSES_TO → SubGoal: "Create user entity"
  │                        │
  │                        └── RESULTS_IN → Decision: "Extend existing User entity"
  │                              └── ... (misma estructura)
```

### 5.4 Beneficios del Intention Graph

| Beneficio | Explicacion |
|-----------|-------------|
| **Explicabilidad** | Se puede responder "por que se creo este archivo?" con trazabilidad completa |
| **Auditabilidad** | Cada decision tiene razones asociadas. Se puede auditar el proceso. |
| **Reutilizacion** | Decisiones similares se pueden reutilizar en futuros proyectos |
| **Correccion** | Si una decision fue incorrecta, se puede rastrear que razones la motivaron |
| **Ensenanza** | El sistema puede explicar su razonamiento a un desarrollador humano |

---

## 6. Reasoning Memory

### 6.1 Problema

La propuesta 179 tiene 3 niveles de memoria:

| Nivel | Que almacena | Ejemplo |
|-------|-------------|---------|
| Episodica | Que hice | "Cree auth.module.ts en la sesion anterior" |
| Semantica | Que significa | "Este proyecto usa Clean Architecture" |
| Procedural | Como se hace | "Para crear un endpoint: DTO → Service → Controller" |

Ninguno almacena el **razonamiento detras de las decisiones**.

### 6.2 Solucion: 4to nivel — Reasoning Memory

```python
class ReasoningMemory:
    """Memoria de razonamiento: almacena el 'por que' de cada decision.
    
    Se alimenta del Intention Graph (nodos DECISION y REASON).
    Permite al sistema recordar no solo QUE hizo, sino POR QUE lo hizo.
    """
    
    async def get_reasoning_chain(self, decision_id: str) -> list[Reason]:
        """Recupera la cadena de razonamiento que llevo a una decision."""
        reasons = await self.kg.get_incoming(
            decision_id, 
            EdgeType.BECAUSE
        )
        return [Reason(
            text=r.properties["text"],
            context=r.properties.get("context"),
            confidence=r.properties.get("confidence", 1.0),
            timestamp=r.created_at
        ) for r in reasons]
    
    async def get_decision_tree(self, goal_id: str) -> DecisionTree:
        """Recupera el arbol completo de decisiones para un goal."""
        decisions = await self.kg.query(
            node_type=NodeType.DECISION,
            source_id=goal_id,
            edge_type=EdgeType.RESULTS_IN
        )
        tree = DecisionTree(goal_id=goal_id)
        for dec in decisions:
            reasons = await self.get_reasoning_chain(dec.id)
            alternatives = await self.kg.get_incoming(
                dec.id,
                EdgeType.REJECTED_IN_FAVOR_OF
            )
            tree.add_decision(Decision(
                id=dec.id,
                text=dec.properties["text"],
                reasons=reasons,
                rejected_alternatives=[a.properties for a in alternatives],
                timestamp=dec.created_at
            ))
        return tree
    
    async def compare_strategies(self, goal_type: str) -> StrategyComparison:
        """Compara estrategias usadas en el pasado para un tipo de goal.
        
        Responde: para goals de tipo 'feature/auth', que estrategias
        se usaron antes, cual tuvo mas exito, cual menos errores.
        """
        past_decisions = await self.kg.query(
            node_type=NodeType.DECISION,
            filter={"goal_type": goal_type}
        )
        # Analizar resultados de cada decision
        comparison = StrategyComparison(goal_type=goal_type)
        for dec in past_decisions:
            results = await self.kg.get_outgoing(
                dec.id,
                EdgeType.RESULTS_IN
            )
            success_rate = self._calculate_success_rate(results)
            comparison.add_strategy(
                strategy=dec.properties["text"],
                success_rate=success_rate,
                times_used=len(results)
            )
        return comparison
```

### 6.3 Donde se almacena

No es un almacen separado. Es una **capa de interpretacion** sobre:

- **Intention Graph** (nodos DECISION + aristas BECAUSE)
- **EventBus log** (eventos de decision, tool calls, resultados)
- **Experience Engine** (metricas de exito por estrategia)

```
Reasoning Memory
      │
      ├── Lee del Intention Graph → "por que se eligio X"
      ├── Lee del EventBus → "que paso cuando se ejecuto X"
      ├── Lee del Experience Engine → "X funciona mejor que Y para este tipo de tarea"
      └── Consulta via API → "cual fue el razonamiento detras de esta decision?"
```

### 6.4 Integracion con el Prompt Pipeline

Cuando el sistema enfrenta una decision similar a una ya tomada, el Prompt Pipeline puede incluir:

```
Paso 4: Plan
  └── Contexto adicional desde Reasoning Memory:
       "En el pasado, para un goal similar (type: auth),
        se eligio Passport.js JWT strategy porque:
        - NestJS tiene soporte nativo
        - El equipo esta familiarizado
        - Resultado: exitoso (3/3 acceptance criteria cumplidos)
        
        Alternativa rechazada: Custom JWT middleware
        - Razon: requiere mas boilerplate
        - Correcta? Si, el resultado fue exitoso"
```

---

## 7. Experience Engine

### 7.1 Que es

El **Experience Engine** es el mecanismo de **aprendizaje continuo** del sistema. Cada tarea ejecutada genera experiencia que el sistema utiliza para mejorar su desempeno futuro.

### 7.2 Ciclo de aprendizaje

```
Task
  │
  ▼
Execution
  │
  ├── Success? → Learn what worked
  │     ├── "El prompt de CodingAgent con modelo claude-sonnet-4
  │     │    produjo codigo que paso todos los tests en el primer intento"
  │     └── → Knowledge Graph: actualizar preferencias de modelo
  │
  ├── Failure? → Learn what failed
  │     ├── "El prompt de ReviewAgent marco falsos positivos de seguridad
  │     │    porque no entendio el contexto del proyecto"
  │     └── → Knowledge Graph: ajustar prompt de ReviewAgent
  │
  └── Partial? → Learn what to improve
        ├── "TestAgent genero tests pero con 40% de cobertura
        │    (threshold: 70%)"
        └── → Knowledge Graph: ajustar estrategia de generacion de tests
              → Experiencia almacenada para futuras optimizaciones

Knowledge Graph
  └── Nodos EXPERIENCE con:
        ├── task_type: "feature/auth"
        ├── strategy: "passport-jwt"
        ├── model: "claude-sonnet-4"
        ├── tools_used: ["WriteFileTool", "SearchTool"]
        ├── success_rate: 0.95
        ├── avg_duration: 45.2  # segundos
        ├── error_rate: 0.05
        ├── times_used: 12
        └── lessons_learned: [
              "Usar SearchTool antes de WriteFileTool para verificar
               que el archivo no existe",
              "Incluir JWT guard en el mismo paso que el modulo auth"
            ]
```

### 7.3 Experience Agent

```python
class ExperienceAgent(Agent):
    """Agente de experiencia: aprende de cada tarea ejecutada.
    
    No ejecuta tareas. Solo observa resultados y extrae lecciones.
    """
    
    manifest = CapabilityManifest(
        agent_id="experience-agent",
        description="Learns from task execution to improve future performance",
        triggers=[
            "agent.*.task.completed",
            "agent.*.task.failed",
            "review.completed",
            "tests.passed",
            "tests.failed"
        ],
        output_events=[
            "experience.learned",
            "experience.optimization.suggested"
        ]
    )
    
    async def handle_event(self, event: Event):
        if "failed" in event.topic:
            await self._learn_from_failure(event)
        elif "completed" in event.topic or "passed" in event.topic:
            await self._learn_from_success(event)
    
    async def _learn_from_failure(self, event: Event):
        """Analiza un fallo y extrae lecciones."""
        # 1. Recuperar contexto del Intention Graph
        decision_chain = await self.reasoning_memory.get_decision_tree(
            event.data.get("goal_id")
        )
        
        # 2. Analizar causa raiz via LLM
        analysis = await self.llm.complete(f"""
        Analiza este fallo y extrae lecciones aprendidas.
        
        Evento: {event.topic}
        Datos: {json.dumps(event.data)}
        Decisiones previas: {json.dumps(decision_chain)}
        
        Responde JSON:
        {{
            "root_cause": "causa raiz",
            "lesson": "leccion aprendida",
            "suggestion": "que cambiar para evitar este fallo",
            "confidence": 0.0-1.0
        }}
        """)
        
        # 3. Almacenar experiencia
        await self.kg.add_node(Node(
            node_type="experience",
            properties={
                "event_type": event.topic,
                "root_cause": analysis["root_cause"],
                "lesson": analysis["lesson"],
                "suggestion": analysis["suggestion"],
                "confidence": analysis["confidence"],
                "timestamp": time.time()
            }
        ))
        
        # 4. Sugerir optimizacion
        if analysis["confidence"] > 0.7:
            await self.event_bus.publish(Event(
                topic="experience.optimization.suggested",
                data={
                    "target": event.data.get("agent_id"),
                    "suggestion": analysis["suggestion"],
                    "confidence": analysis["confidence"]
                }
            ))
    
    async def get_best_strategy(self, task_type: str) -> Strategy:
        """Retorna la mejor estrategia conocida para un tipo de tarea."""
        experiences = await self.kg.query(
            node_type="experience",
            filter={"task_type": task_type}
        )
        
        if not experiences:
            return Strategy.default()
        
        # Ponderar por success_rate y times_used
        best = max(experiences, 
                   key=lambda e: e.properties["success_rate"] * 
                                 math.log(e.properties["times_used"] + 1))
        
        return Strategy(
            model=best.properties.get("model"),
            tools=best.properties.get("tools_used", []),
            lessons=best.properties.get("lessons_learned", []),
            confidence=best.properties["success_rate"]
        )
```

### 7.4 Que aprende el Experience Engine

| Que aprende | Como se usa |
|-------------|-------------|
| **Modelos optimos** | "Para code generation, claude-sonnet-4 tiene 95% exito vs gpt-4o con 82%" |
| **Herramientas efectivas** | "SearchTool antes de WriteFileTool reduce errores de sobrescritura" |
| **Prompts efectivos** | "Incluir 3 ejemplos en el prompt de ReviewAgent reduce falsos positivos" |
| **Estrategias de testing** | "TestAgent genera mejores tests si se le pasa el acceptance_criteria" |
| **Patrones de fallo** | "72% de los fallos en CodingAgent ocurren cuando el contexto del proyecto es insuficiente" |
| **Duracion promedio** | "Tasks de tipo 'feature/auth' toman promedio 45s" |

### 7.5 Integracion con PDCAEngine

El PDCAEngine existente (F3) ejecuta MASS optimization cada N eventos. El Experience Engine alimenta a MASS con datos concretos:

```
ExperienceEngine
      │
      ├── Datos de exito/fallo por agente
      ├── Metricas de duracion por tipo de tarea
      ├── Lecciones aprendidas
      │
      ▼
PDCAEngine.run_mass_optimization()
  ├── Block-Level: ajustar prompts segun lecciones
  ├── Topology-Level: reordenar agentes segun efectividad
  └── Workflow-Level: ajustar pipeline segun patrones de exito
```

---

## 8. Cost Optimizer

### 8.1 Problema

Cada llamada al LLM tiene un costo (economico y de latencia). Muchas tareas que actualmente se resuelven con LLM podrian resolverse con herramientas deterministicas mas rapidas y economicas.

### 8.2 Solucion: Cost Optimizer

```python
class CostOptimizer:
    """Optimizador de costos: decide si usar LLM o herramienta.
    
    Antes de cada llamada LLM, evalua:
    1. Se puede resolver con AST? → Usar ASTTool
    2. Se puede resolver con LSP? → Usar LSPTool  
    3. Se puede resolver con regex/ripgrep? → Usar SearchTool
    4. Se puede resolver con gramatica/conocimiento local? → Usar cache
    5. Si nada aplica → Usar LLM (con el modelo mas barato que funcione)
    """
    
    # Reglas de decision: (patron de tarea, herramienta, ahorro estimado)
    RULES = [
        # Encontrar definiciones
        DecisionRule(
            pattern="find_definition|goto_def|where_is",
            tool="LSPTool",
            cost_saving=0.95,  # 95% mas barato que LLM
            latency_saving=0.90,  # 90% mas rapido
            confidence=0.99
        ),
        # Encontrar referencias
        DecisionRule(
            pattern="find_references|who_calls|where_used",
            tool="LSPTool",
            cost_saving=0.95,
            latency_saving=0.90,
            confidence=0.99
        ),
        # Busqueda textual
        DecisionRule(
            pattern="search|find.*pattern|grep|locate",
            tool="SearchTool",
            cost_saving=0.98,
            latency_saving=0.95,
            confidence=0.99
        ),
        # Analisis de dependencias
        DecisionRule(
            pattern="dependency|import_graph|module_map",
            tool="DependencyGraphTool",
            cost_saving=0.90,
            latency_saving=0.85,
            confidence=0.95
        ),
        # Obtener estructura del codigo
        DecisionRule(
            pattern="class_structure|method_signature|interface",
            tool="ASTTool",
            cost_saving=0.92,
            latency_saving=0.88,
            confidence=0.97
        ),
        # Busqueda semantica
        DecisionRule(
            pattern="semantic_search|similar_code|find_by_purpose",
            tool="EmbeddingSearchTool",
            cost_saving=0.85,
            latency_saving=0.80,
            confidence=0.90
        ),
        # Obtener historial git
        DecisionRule(
            pattern="git_log|blame|commit_history|who_changed",
            tool="GitTool",
            cost_saving=0.97,
            latency_saving=0.92,
            confidence=0.99
        ),
        # Diff
        DecisionRule(
            pattern="diff|compare|what_changed",
            tool="DiffTool",
            cost_saving=0.95,
            latency_saving=0.90,
            confidence=0.99
        ),
        # Lectura de archivos
        DecisionRule(
            pattern="read_file|show_file|cat|open",
            tool="ReadFileTool",
            cost_saving=0.99,
            latency_saving=0.95,
            confidence=1.0
        ),
        # Test runner
        DecisionRule(
            pattern="run_test|execute_test|pytest|jest",
            tool="TestRunnerTool",
            cost_saving=0.95,
            latency_saving=0.80,
            confidence=0.98
        ),
        # Simbolos de autocompletado
        PatternRule(
            pattern="autocomplete|completion|suggest",
            tool="LSPTool",
            cost_saving=0.95,
            latency_saving=0.90,
            confidence=0.98
        ),
        # Detectar lenguaje de archivo
        PatternRule(
            pattern="detect_language|file_type",
            tool="LanguageDetector",
            cost_saving=0.99,
            latency_saving=0.95,
            confidence=1.0
        ),
        # Formateo de codigo
        PatternRule(
            pattern="format|prettier|lint_fix",
            tool="TerminalTool",
            cost_saving=0.96,
            latency_saving=0.85,
            confidence=0.95
        ),
    ]
    
    async def optimize(self, task: AgentTask) -> OptimizationPlan:
        """Evalua si una tarea puede resolverse sin LLM."""
        
        # 1. Verificar cache de resultados previos
        cached = await self.llm_cache.get(task.cache_key())
        if cached:
            return OptimizationPlan(
                method="cache",
                tool=None,
                estimated_cost=0,
                estimated_latency=0.001,
                confidence=1.0
            )
        
        # 2. Evaluar reglas de costo
        for rule in self.RULES:
            if re.search(rule.pattern, task.prompt, re.IGNORECASE):
                tool = self.tool_registry.get(rule.tool)
                return OptimizationPlan(
                    method="tool",
                    tool=tool,
                    estimated_cost=0,  # herramientas locales son gratuitas
                    estimated_latency=tool.estimated_latency,
                    confidence=rule.confidence
                )
        
        # 3. Si todo falla, usar LLM con el modelo mas barato
        model = await self.model_router.cheapest_for_task(task.type)
        return OptimizationPlan(
            method="llm",
            model=model,
            estimated_cost=model.cost_per_token * task.estimated_tokens,
            estimated_latency=model.estimated_latency(task.estimated_tokens),
            confidence=0.8
        )
```

### 8.3 Metricas de ahorro

| Periodo | Llamadas LLM evitadas | Ahorro estimado |
|---------|----------------------|-----------------|
| Por tarea promedio | 3-5 llamadas | $0.03-$0.15 |
| Por sesion (10 tareas) | 30-50 llamadas | $0.30-$1.50 |
| Por dia (50 sesiones) | 1,500-2,500 llamadas | $15-$75 |
| Por mes (22 dias) | 33,000-55,000 llamadas | $330-$1,650 |

### 8.4 Decision visual

```
Tarea: "Donde esta definida la funcion authenticate()?"
          │
          ▼
CostOptimizer.optimize()
          │
          ├── Pattern match: "find_definition" → LSPTool
          ├── Costo LLM estimado: $0.02, latencia: 3s
          ├── Costo herramienta: $0.00, latencia: 0.05s
          │
          ▼
          NO se usa LLM. Se usa LSPTool.
          Ahorro: $0.02, 2.95s

Tarea: "Refactoriza esta funcion para usar async/await"
          │
          ▼
CostOptimizer.optimize()
          │
          ├── Pattern match: NINGUNA regla coincide
          │
          ▼
          Se usa LLM (modelo optimo segun Multi-Model Router)
```

---

## 9. Multi-Model Router

### 9.1 Problema

Actualmente el sistema usa un unico modelo LLM para todas las tareas. Esto es suboptimo porque:

- Modelos grandes (GPT-5, Claude Opus) son caros y lentos para tareas simples
- Modelos especializados (Qwen-Coder para codigo, Gemma para resumenes) rinden mejor en sus areas
- La calidad y el costo no escalan linealmente

### 9.2 Solucion: Multi-Model Router

```python
class ModelRouter:
    """Router de modelos: elige el modelo optimo para cada tarea.
    
    Criterios:
    - Tipo de tarea (planning, code, review, test, doc, summary)
    - Complejidad (simple, moderate, complex)
    - Restricciones de costo (budget por sesion)
    - Restricciones de latencia (modo interactive vs batch)
    - Disponibilidad del modelo (fallback si uno esta caido)
    """
    
    MODEL_PROFILES = {
        "planning": {
            "complex": {
                "primary": "gpt-5",  # Razonamiento profundo
                "fallback": "claude-opus-4",
                "temperature": 0.2,
                "max_tokens": 4096
            },
            "moderate": {
                "primary": "gpt-4o",
                "fallback": "claude-sonnet-4",
                "temperature": 0.3,
                "max_tokens": 2048
            },
            "simple": {
                "primary": "gpt-4o-mini",
                "fallback": "claude-haiku",
                "temperature": 0.3,
                "max_tokens": 1024
            }
        },
        "code_generation": {
            "complex": {
                "primary": "qwen-coder-32b",  # Especializado en codigo
                "fallback": "claude-sonnet-4",
                "temperature": 0.2,
                "max_tokens": 8192
            },
            "moderate": {
                "primary": "codestral-latest",
                "fallback": "gpt-4o-mini",
                "temperature": 0.1,
                "max_tokens": 4096
            },
            "simple": {
                "primary": "gpt-4o-mini",
                "fallback": "codestral-latest",
                "temperature": 0.1,
                "max_tokens": 2048
            }
        },
        "code_review": {
            "primary": "claude-sonnet-4",  # Mejor en analisis critico
            "fallback": "gpt-4o",
            "temperature": 0.1,
            "max_tokens": 4096
        },
        "test_generation": {
            "primary": "qwen-coder-32b",
            "fallback": "gpt-4o-mini",
            "temperature": 0.2,
            "max_tokens": 4096
        },
        "documentation": {
            "primary": "claude-haiku",  # Rapido y economico
            "fallback": "gpt-4o-mini",
            "temperature": 0.4,
            "max_tokens": 4096
        },
        "summary": {
            "primary": "gemma-2-27b",  # Pequeno y rapido
            "fallback": "gpt-4o-mini",
            "temperature": 0.3,
            "max_tokens": 1024
        },
        "classification": {
            "primary": "gpt-4o-mini",  # Suficiente para clasificar
            "fallback": "claude-haiku",
            "temperature": 0.1,
            "max_tokens": 256
        },
        "security_scan": {
            "primary": "claude-sonnet-4",
            "fallback": "gpt-4o",
            "temperature": 0.1,
            "max_tokens": 2048
        },
        "performance_analysis": {
            "primary": "gpt-5",
            "fallback": "claude-opus-4",
            "temperature": 0.2,
            "max_tokens": 4096
        }
    }
    
    async def route(self, task_type: str, complexity: str) -> ModelConfig:
        """Retorna la configuracion de modelo optima."""
        profile = self.MODEL_PROFILES.get(task_type, self.MODEL_PROFILES["planning"])
        
        if isinstance(profile, dict) and "primary" not in profile:
            # Tiene sub-perfiles por complejidad
            sub = profile.get(complexity, profile["moderate"])
            return ModelConfig(
                primary=sub["primary"],
                fallback=sub["fallback"],
                temperature=sub["temperature"],
                max_tokens=sub["max_tokens"]
            )
        
        return ModelConfig(
            primary=profile["primary"],
            fallback=profile["fallback"],
            temperature=profile["temperature"],
            max_tokens=profile["max_tokens"]
        )
    
    async def route_with_fallback(self, task_type: str, complexity: str) -> str:
        """Intenta con primary, si falla usa fallback."""
        config = await self.route(task_type, complexity)
        
        try:
            return await self.llm_client.complete(
                model=config.primary,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
        except ModelUnavailableError:
            self.event_bus.publish(Event(
                topic="model.fallback.activated",
                data={
                    "primary": config.primary,
                    "fallback": config.fallback,
                    "task_type": task_type
                }
            ))
            return await self.llm_client.complete(
                model=config.fallback,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
```

### 9.3 Mapa de modelos a tareas

```
TASK TYPE                  MODELO PRINCIPAL       MODELO FALLBACK       COSTO
─────────────────────────────────────────────────────────────────────────────
Planning (complex)         GPT-5                  Claude Opus 4         $$$$$
Planning (moderate)        GPT-4o                 Claude Sonnet 4       $$$
Planning (simple)          GPT-4o-mini            Claude Haiku          $
Code gen (complex)         Qwen-Coder 32B         Claude Sonnet 4       $$$
Code gen (moderate)        Codestral              GPT-4o-mini           $$
Code gen (simple)          GPT-4o-mini            Codestral             $
Code review                Claude Sonnet 4        GPT-4o                $$$
Test generation            Qwen-Coder 32B         GPT-4o-mini           $$$
Documentation              Claude Haiku           GPT-4o-mini           $
Summaries                  Gemma 2 27B            GPT-4o-mini           $
Classification             GPT-4o-mini            Claude Haiku          $
Security scan              Claude Sonnet 4        GPT-4o                $$$
Performance analysis       GPT-5                  Claude Opus 4         $$$$$
```

### 9.4 Estimacion de ahorro vs modelo unico

| Escenario | Modelo unico (GPT-5) | Multi-Model Router | Ahorro |
|-----------|---------------------|-------------------|--------|
| 100 tareas mixtas | $15.00 (100 llamadas GPT-5) | $3.20 (20 planning + 30 code + 20 review + 30 doc) | **78%** |
| 1000 tareas/dia | $150.00 | $32.00 | **$118/dia** |
| Por mes (22 dias) | $3,300.00 | $704.00 | **$2,596/mes** |

---

## 10. Repository Timeline

### 10.1 Problema

El Repository Graph (propuesto en 179) es un snapshot del estado actual del codigo. No responde preguntas temporales como:

- "Cuando se introdujo este bug?"
- "Que archivos cambiaron en el ultimo release?"
- "Cual es la tendencia de deuda tecnica?"

### 10.2 Solucion: Repository Timeline

```python
class RepositoryTimeline:
    """Historial temporal del repositorio.
    
    No es un reemplazo de git. Es una capa semantica SOBRE git
    que permite responder preguntas temporales sobre el codigo.
    """
    
    TIMELINE_EVENTS = [
        "commit.created",           # Nuevo commit
        "branch.created",           # Nueva rama
        "branch.merged",            # Rama mergeada
        "tag.created",              # Nuevo tag / release
        "file.created",             # Archivo nuevo
        "file.modified",            # Archivo modificado
        "file.deleted",             # Archivo eliminado
        "file.renamed",             # Archivo renombrado
        "dependency.added",         # Nueva dependencia
        "dependency.removed",       # Dependencia eliminada
        "dependency.updated",       # Dependencia actualizada
        "refactor.detected",        # Refactor detectado por analisis
        "bug.introduced",           # Bug introducido (por git bisect)
        "bug.fixed",                # Bug corregido
        "coverage.changed",         # Cobertura de tests cambio
        "tech_debt.added",          # Deuda tecnica incrementada
        "tech_debt.resolved",       # Deuda tecnica resuelta
    ]
    
    async def get_timeline(self, 
                           file_path: str | None = None,
                           since: str | None = None,
                           until: str | None = None) -> list[TimelineEvent]:
        """Recupera linea de tiempo del repositorio o archivo."""
        query = {"node_type": "timeline_event"}
        if file_path:
            query["file_path"] = file_path
        if since:
            query["timestamp_gte"] = since
        if until:
            query["timestamp_lte"] = until
        
        return await self.kg.query(**query)
    
    async def get_file_history(self, file_path: str) -> FileHistory:
        """Historial completo de un archivo: creacion, modificaciones, renombres."""
        events = await self.get_timeline(file_path=file_path)
        
        return FileHistory(
            file_path=file_path,
            created=next((e for e in events if e.type == "file.created"), None),
            modifications=[e for e in events if e.type == "file.modified"],
            renamed_from=[e for e in events if e.type == "file.renamed"],
            deleted=next((e for e in events if e.type == "file.deleted"), None),
            current_state=await self._get_current_state(file_path)
        )
    
    async def get_release_diff(self, from_tag: str, to_tag: str) -> ReleaseDiff:
        """Diferencia entre dos releases: archivos nuevos, modificados, eliminados."""
        from_events = await self.kg.query(
            node_type="timeline_event",
            filter={"tag": from_tag}
        )
        to_events = await self.kg.query(
            node_type="timeline_event",
            filter={"tag": to_tag}
        )
        # ... calcular diff ...
    
    async def answer_temporal_question(self, question: str) -> str:
        """Responde preguntas temporales sobre el repositorio.
        
        Ejemplo: "Cuando se introdujo este bug?" → "Commit a3f2b1c del 2026-05-15"
        """
        # Usar git bisect logic + timeline
        ...
```

### 10.3 Integracion con git

```python
class GitTimelineBuilder:
    """Construye el Repository Timeline desde git."""
    
    async def build_from_git(self, repo_path: str):
        """Escanea el historial git completo y construye timeline."""
        
        # git log --all --format=...
        log = await self.git.log(all=True, format="%H|%an|%ae|%ad|%s")
        
        # Para cada commit, extraer cambios
        for commit_hash in log:
            diff = await self.git.show(commit_hash, stat=True)
            files = self._parse_diff(diff)
            
            # Almacenar evento de commit
            await self.kg.add_node(Node(
                node_type="timeline_event",
                properties={
                    "type": "commit.created",
                    "commit_hash": commit_hash,
                    "author": log[commit_hash]["author"],
                    "timestamp": log[commit_hash]["date"],
                    "message": log[commit_hash]["message"],
                    "files": files,
                    "additions": sum(f["additions"] for f in files),
                    "deletions": sum(f["deletions"] for f in files)
                }
            ))
            
            # Para cada archivo, almacenar eventos individuales
            for file in files:
                event_type = "file.modified"
                if file["status"] == "A":
                    event_type = "file.created"
                elif file["status"] == "D":
                    event_type = "file.deleted"
                elif file["status"] == "R":
                    event_type = "file.renamed"
                
                await self.kg.add_node(Node(
                    node_type="timeline_event",
                    properties={
                        "type": event_type,
                        "file_path": file["path"],
                        "commit_hash": commit_hash,
                        "timestamp": log[commit_hash]["date"],
                        "additions": file["additions"],
                        "deletions": file["deletions"]
                    }
                ))
```

---

## 11. Prediction Engine

### 11.1 Que es

El **Prediction Engine** analiza los cambios propuestos y predice su impacto antes de que se ejecuten.

### 11.2 Como funciona

```python
class PredictionEngine:
    """Predice el impacto de cambios antes de ejecutarlos.
    
    Usa el Repository Graph + World Model + Experience Engine
    para responder: "si cambio X, que mas se va a romper?"
    """
    
    async def predict_impact(self, proposed_changes: list[Change]) -> ImpactReport:
        """Predice el impacto de una serie de cambios propuestos."""
        
        impact_report = ImpactReport()
        
        for change in proposed_changes:
            # 1. Encontrar el nodo en el Repository Graph
            node = await self._find_affected_node(change)
            
            # 2. BFS hacia adelante: que depende de este nodo?
            dependents = await self._get_dependents(node.id)
            for dep in dependents:
                impact_report.add_affected(
                    node=dep,
                    relationship="depends_on",
                    confidence=0.95
                )
            
            # 3. BFS hacia atras: de que depende este nodo?
            dependencies = await self._get_dependencies(node.id)
            for dep in dependencies:
                impact_report.add_affected(
                    node=dep,
                    relationship="dependency_of",
                    confidence=0.90
                )
            
            # 4. Consultar World Model: que servicios afecta?
            services = await self._get_affected_services(node.id)
            for svc in services:
                impact_report.add_affected(
                    node=svc,
                    relationship="service",
                    confidence=0.80
                )
            
            # 5. Consultar Experience Engine: patrones historicos
            similar_changes = await self.experience.get_similar_changes(change)
            for past in similar_changes:
                if past.had_regression:
                    impact_report.add_warning(
                        message=f"Cambio similar causo regression en {past.affected_area}",
                        confidence=past.confidence
                    )
            
            # 6. Consultar TestDashboard: que tests validan este codigo?
            tests = await self._get_tests_for_node(node.id)
            for test in tests:
                impact_report.add_affected(
                    node=test,
                    relationship="tested_by",
                    confidence=0.99
                )
        
        # 7. Generar resumen
        impact_report.summary = self._generate_summary(impact_report)
        
        return impact_report
    
    async def predict_impact_from_ir(self, air: AgenticIR) -> ImpactReport:
        """Predice impacto desde un AgenticIR antes de ejecutarlo."""
        # Convertir AIR a cambios concretos estimados
        estimated_changes = await self._estimate_changes_from_ir(air)
        return await self.predict_impact(estimated_changes)
```

### 11.3 Ejemplo de output

```
Prediction Report for: "Refactor authenticate() to use async/await"
─────────────────────────────────────────────────────────────────────

AFFECTED (will need changes):
  auth.service.ts          ─── depends_on → authenticate()
  auth.controller.ts       ─── calls → authenticate()
  auth.module.ts           ─── imports → auth.service
  auth.spec.ts             ─── tests → authenticate()

MAY BE AFFECTED (review recommended):
  rate-limiter.middleware.ts  ─── calls → authenticate() (indirect)
  audit.service.ts            ─── references → auth.service

SERVICES AFFECTED:
  auth-service (deploy required)

TESTS THAT VALIDATE THIS CODE:
  auth.spec.ts (23 tests)
  integration/auth.e2e-spec.ts (5 tests)

HISTORICAL PATTERNS:
  ⚠ Cambio similar en login.service.ts (2026-05-10) causo regression
    en rate-limiter por 2 dias. Asegurar rate-limiter despues del cambio.

RECOMMENDATIONS:
  1. Ejecutar auth.spec.ts antes y despues del cambio
  2. Revisar rate-limiter.middleware.ts manualmente
  3. Tiene cobertura de tests suficiente para authenticate()? (actual: 68%)
```

### 11.4 Integracion con el Prompt Pipeline

El Prediction Engine se ejecuta **antes** del paso "Generate" en el Prompt Pipeline:

```
Request
  │
  ▼
Step 1-3: Understand + Analyze + Retrieve
  │
  ▼
Step 4: Plan → produce AgenticIR
  │
  ▼
Step 4.5: PREDICT IMPACT (nuevo paso)
  ├── Repository Graph → que archivos/nodos afecta?
  ├── World Model → que servicios afecta?
  ├── Experience Engine → patrones historicos de cambios similares
  └── Output: ImpactReport
        │
        ├── Si impacto es BAJO → continuar a Generate
        ├── Si impacto es MEDIO → generar con precauciones
        └── Si impacto es ALTO → HITL: requerir aprobacion humana
              │
              ▼
Step 5-9: Generate + Review + Test + Refactor + Commit
```

---

## 12. Arquitectura Integrada (179 + 180)

### 12.1 Diagrama completo

```
                              ┌─────────────────────────────┐
                              │         User Request        │
                              └─────────────┬───────────────┘
                                            │
                              ┌─────────────▼───────────────┐
                              │       IntentRouter          │
                              │  (clasifica tipo de tarea)  │
                              └─────────────┬───────────────┘
                                            │
                              ┌─────────────▼───────────────┐
                              │       GoalManager           │  ← NUEVO
                              │  (descompone multi-objetivo) │
                              └─────────────┬───────────────┘
                                            │
              ┌─────────────────────────────┼─────────────────────────────┐
              │                             │                             │
              ▼                             ▼                             ▼
   ┌────────────────────┐      ┌────────────────────┐      ┌────────────────────┐
   │   PlanningAgent    │      │   Repository       │      │   World Model      │
   │  (Task Graph +     │◄─────┤   Intelligence     │◄─────┤   Agent            │  ← NUEVO
   │   AgenticIR)       │      │   Agent            │      │  (estado global)   │
   └─────────┬──────────┘      └────────────────────┘      └────────────────────┘
             │                                                      │
             │                              ┌───────────────────────┘
             │                              ▼
             │                     ┌────────────────────┐
             │                     │   Repository       │
             │                     │   Timeline         │  ← NUEVO
             │                     │  (historial temp.) │
             │                     └────────────────────┘
             │
             ▼
   ┌────────────────────┐
   │    Task Graph      │
   │  (DAG de tareas)   │
   │  + AgenticIRs      │  ← CORREGIDO (IR preservado)
   └─────────┬──────────┘
             │
             ▼
   ┌────────────────────┐
   │   Cost Optimizer   │  ← NUEVO
   │(tool vs LLM route) │
   └─────────┬──────────┘
             │
             ▼
   ┌────────────────────┐
   │  Multi-Model       │  ← NUEVO
   │  Router            │
   │(modelo x tarea)    │
   └─────────┬──────────┘
             │
             ▼
   ┌────────────────────┐
   │   Prediction       │  ← NUEVO
   │   Engine           │
   │(impacto previo)    │
   └─────────┬──────────┘
             │
             ▼
   ┌──────────────────────────────────────────────────┐
   │           Prompt Pipeline                        │
   │  Understand → Analyze → Plan → Generate →       │
   │  Review → Test → Refactor → Commit              │
   └─────────────────────┬────────────────────────────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
   ┌──────────────┐ ┌──────────┐ ┌──────────┐
   │ CodingAgent  │ │TestAgent │ │ DocAgent │
   │ RefactorAgent│ │          │ │          │
   │ SecurityAgent│ │          │ │          │
   └──────┬───────┘ └────┬─────┘ └────┬─────┘
          │              │            │
          └──────────────┼────────────┘
                         ▼
              ┌────────────────────┐
              │   Validation Gate  │
              │  (Quality Gates +  │
              │   Review)          │
              └─────────┬──────────┘
                        │
              ┌─────────▼──────────┐
              │    Git Operations  │
              └────────────────────┘

              ┌──────────────────────────────────────────────────┐
              │               Knowledge Graph                    │
              │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
              │  │  SDLC    │ │  Repo    │ │   World Model    │  │
              │  │  Layer   │ │  Graph   │ │   (servicios,    │  │
              │  │(F1-F3)   │ │(codigo)  │ │    infra, CI,    │  │
              │  │          │ │          │ │    issues, PRs)  │  │
              │  └──────────┘ └──────────┘ └──────────────────┘  │
              │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
              │  │ Intention│ │ Timeline │ │   Experience     │  │
              │  │ Graph    │ │(historico│ │   (lecciones     │  │
              │  │(trazabil)│ │ temporal)│ │    aprendidas)   │  │
              │  └──────────┘ └──────────┘ └──────────────────┘  │
              └──────────────────────────────────────────────────┘

              ┌──────────────────────────────────────────────────┐
              │               Memory System (4 niveles)          │
              │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐│
              │  │Episodica │ │Semantica │ │Procedural│ │Reason││  ← NUEVO
              │  │(que hice)│ │(que sign)│ │(como se) │ │(por q)││
              │  └──────────┘ └──────────┘ └──────────┘ └──────┘│
              └──────────────────────────────────────────────────┘

              ┌──────────────────────────────────────────────────┐
              │        EventBus + ToolRegistry + LLMClient       │
              │        + ExperienceEngine + PDCAEngine           │
              └──────────────────────────────────────────────────┘
```

### 12.2 Nuevos topicos de EventBus

De la propuesta 179 se agregaron ~30 topicos operativos. Adicionalmente:

```python
# World Model
"world.model.updated"
"world.model.risk.identified"
"external.github.push"
"external.github.pr.*"
"external.github.issue.*"
"external.ci.*"
"external.deploy.*"

# Goal Manager
"goal.created"
"goal.completed"
"goal.failed"
"goal.dependency.blocked"

# Intention Graph
"intention.graph.updated"
"decision.recorded"

# Experience Engine
"experience.learned"
"experience.optimization.suggested"

# Cost Optimizer
"cost.optimizer.llm_avoided"
"cost.optimizer.tool_used"
"cost.optimizer.cache_hit"

# Multi-Model Router
"model.routed"
"model.fallback.activated"

# Prediction
"prediction.impact.assessed"
"prediction.impact.high_risk"

# Timeline
"timeline.event.recorded"
```

### 12.3 Matriz de agentes vs capacidades

| Agente | 179 | 180 | Integracion |
|--------|-----|-----|-------------|
| IntentRouter | Si | Si | GoalManager llama a IntentRouter |
| GoalManager | — | **NUEVO** | Se inserta entre IntentRouter y PlanningAgent |
| PlanningAgent | Si | Si | Produce AgenticIR en vez de TaskGraph solo |
| RepositoryIntelligence | Si | Si | Alimenta al World Model |
| WorldModelAgent | — | **NUEVO** | Capa superior al RepositoryIntelligence |
| CodingAgent | Si | Si | Usa AgenticIR como contrato |
| ReviewAgent | Si | Si | Usa modelos del Multi-Model Router |
| TestAgent | Si | Si | Prediction Engine evalua impacto en tests |
| RefactorAgent | Si | Si | Usa Repository Timeline para cambios previos |
| SecurityAgent | Si | Si | Prediction Engine prioriza areas de riesgo |
| PerformanceAgent | Si | Si | World Model da contexto de infraestructura |
| DocumentationAgent | Si | Si | Intention Graph da razones de decisiones |
| ExperienceAgent | — | **NUEVO** | Observa y aprende de todos los agentes |
| ProjectTracker | Si (F3) | Si | ExperienceEngine le da datos de calidad |
| PDCAEngine | Si (F3) | Si | MASS usa datos de ExperienceEngine |
| HITLGateway | Si (F3) | Si | Prediction Engine puede trigger HITL |

---

## 13. Correccion a la seccion 13.4 de 179

### 13.1 Mapeo actualizado (IR canonico preservado)

La tabla en `179 §13.4` debe corregirse para el IR:

| Archivo actual | Accion en 179 | Accion CORREGIDA en 180 |
|---------------|---------------|-------------------------|
| `agentic_pipeline/nodes/ir_generator.py` | **Remover** (IR ya no es necesario) | **Congelar** como parte del pipeline legacy. El IR canonico NO se elimina. Se preserva como mecanismo interno del pipeline clasico. |
| — | (no existia) | **NUEVO**: `compiler-bot/core/agentic_ir.py` — Agentic IR como reemplazo conceptual |
| — | (no existia) | **NUEVO**: `compiler-bot/core/ir_registry.py` — Registro de IRs activos y su trazabilidad |

**El IR canonico del pipeline legacy se congela pero no se elimina.**

**El Agentic IR se agrega como nuevo componente** para el nuevo sistema de agentes.

**Ambos coexisten:** el pipeline legacy usa su IR canonico internamente; el nuevo sistema de agentes usa Agentic IR como contrato.

---

## 14. Arbol de archivos actualizado (post-179 + 180)

Respecto al arbol propuesto en `179 §14.2`, se agregan:

```
compiler-bot/
├── core/
│   ├── agentic_ir.py               # NUEVO: Agentic IR (dataclass, builder, serializer, validator)
│   ├── ir_registry.py              # NUEVO: Registro de AgenticIRs activos
│   ├── goal_manager.py             # NUEVO: Descomposicion de objetivos multiples
│   ├── cost_optimizer.py           # NUEVO: Decision tool vs LLM
│   ├── model_router.py             # NUEVO: Multi-model routing
│   └── prediction_engine.py        # NUEVO: Prediccion de impacto
│
├── agents/
│   ├── world_model_agent.py        # NUEVO: World Model (estado global del proyecto)
│   ├── experience_agent.py         # NUEVO: Aprendizaje continuo desde experiencia
│   └── ... (agentes de 179)
│
├── memory/
│   ├── reasoning_memory.py         # NUEVO: 4to nivel de memoria (razonamiento)
│   └── ... (memorias de 179)
│
├── repository_agent/
│   ├── timeline_builder.py         # NUEVO: Repository Timeline desde git
│   └── ... (componentes de 179)
│
├── intention_graph/                # NUEVO: Intention Graph completo
│   ├── __init__.py
│   ├── intention_graph_builder.py  # Construye el grafo desde eventos
│   ├── intention_graph_querier.py  # Consulta el grafo
│   └── intention_graph_visualizer.py # Visualiza cadenas de decision
│
├── world_model/                    # NUEVO: World Model completo
│   ├── __init__.py
│   ├── service_map.py             # Topologia de microservicios
│   ├── dependency_tracker.py      # Dependencias externas
│   ├── ci_monitor.py              # Estado de CI/CD
│   ├── issue_tracker_adapter.py   # Issues externos (GitHub, Jira)
│   ├── pr_tracker.py              # Pull requests
│   ├── deployment_tracker.py      # Despliegues
│   └── team_model.py              # Ownership
│
├── cost_optimizer/                 # NUEVO: Modulo de optimizacion de costos
│   ├── __init__.py
│   ├── cost_rules.py              # Reglas de decision tool vs LLM
│   ├── cost_tracker.py            # Seguimiento de ahorro
│   └── budget_manager.py          # Gestion de presupuesto por sesion
│
├── model_router/                   # NUEVO: Multi-model router
│   ├── __init__.py
│   ├── model_profiles.py          # Perfiles de modelos por tarea
│   ├── model_registry.py          # Registro de modelos disponibles
│   └── fallback_chain.py          # Cadenas de fallback
│
├── prediction/                     # NUEVO: Prediction Engine
│   ├── __init__.py
│   ├── impact_analyzer.py         # Analisis de impacto en Repository Graph
│   ├── regression_predictor.py    # Prediccion de regresiones
│   └── historical_analyzer.py     # Analisis de cambios historicos
│
└── experience/                     # NUEVO: Experience Engine
    ├── __init__.py
    ├── experience_recorder.py     # Registro de experiencias
    ├── strategy_analyzer.py       # Analisis de efectividad de estrategias
    ├── lesson_extractor.py        # Extraccion de lecciones via LLM
    └── experience_querier.py      # Consulta de experiencias
```

---

## 15. Roadmap actualizado (F4-F8)

### 15.1 Roadmap original (179) vs actualizado (180)

```
179 ROADMAP (original):
  F4 — Foundation (4 sprints)
  F5 — Agent Expansion (4 sprints)
  F6 — Production (4 sprints)
  F7 — Intelligence (4 sprints)
  Total: 16 sprints

180 ROADMAP (actualizado):
  F4 — Foundation + World Model (5 sprints)
  F5 — Agent Expansion + Cost Optimization (5 sprints)
  F6 — Intelligence: Memoria, Experiencia, Prediccion (5 sprints)
  F7 — Production: Timeline, IR, Multi-Model (4 sprints)
  F8 — Autonomy: Goal Manager, Intention Graph, Autonomía 10/10 (5 sprints)
  Total: 24 sprints
```

### 15.2 F4: Foundation + World Model (5 sprints)

| Sprint | Componentes de 179 | Componentes NUEVOS de 180 |
|--------|-------------------|---------------------------|
| **F4-S1** | RepositoryIntelligenceAgent + language_detector + treesitter_parser + ast_builder | — |
| **F4-S2** | symbol_graph + dependency_graph + architecture_detector + repository_graph_builder | — |
| **F4-S3** | ToolRegistry + 8 tools (Read, Write, Search, Ripgrep, Glob, Git, Docker, Diff) | — |
| **F4-S4** | ToolRegistry + 8 tools (TestRunner, Terminal, Browser, AST, DepGraph, LSP, EmbeddingSearch, SymbolLookup) | WorldModelAgent + service_map + dependency_tracker |
| **F4-S5** | IntentRouter + MemorySystem (3 niveles) + AgentGraphBuilder | GoalManager + AgenticIR (dataclass, builder, validator) + Integracion F4 |

### 15.3 F5: Agent Expansion + Cost Optimization (5 sprints)

| Sprint | Componentes de 179 | Componentes NUEVOS de 180 |
|--------|-------------------|---------------------------|
| **F5-S1** | ReviewAgent (SOLID, Clean Code) | CostOptimizer + cost_rules + cost_tracker |
| **F5-S2** | TestAgent + TestRunnerTool | MultiModelRouter + model_profiles + model_registry + fallback_chain |
| **F5-S3** | RefactorAgent + SecurityAgent | PredictionEngine + impact_analyzer |
| **F5-S4** | PerformanceAgent + Integracion F5 | ExperienceAgent + experience_recorder + RepositoryTimeline + timeline_builder |
| **F5-S5** | — | BudgetManager + regression_predictor + historical_analyzer + strategy_analyzer |

### 15.4 F6: Intelligence — Memoria, Experiencia, Prediccion (5 sprints)

| Sprint | Componentes | Descripcion |
|--------|-------------|-------------|
| **F6-S1** | ReasoningMemory + IntentionGraphBuilder | 4to nivel de memoria + trazabilidad de decisiones |
| **F6-S2** | LessonExtractor + ExperienceQuerier | Extraccion automatica de lecciones desde fallos/exitos |
| **F6-S3** | PredictionEngine (full) + ImpactReport | Prediccion de impacto completa con recomendaciones |
| **F6-S4** | IntentionGraphQuerier + Visualizer | Consulta y visualizacion de cadenas de decision |
| **F6-S5** | Integracion F6: Memoria 4 niveles + Experiencia + Prediccion en Prompt Pipeline | El Prompt Pipeline incluye pasos de prediccion y consulta de experiencia |

### 15.5 F7: Production — Timeline, IR, Multi-Model (4 sprints)

| Sprint | Componentes | Descripcion |
|--------|-------------|-------------|
| **F7-S1** | GitTimelineBuilder + RepositoryTimeline (full) | Timeline completa desde git history |
| **F7-S2** | AgenticIRRegistry + IR versioning + IR diff | Versionado y comparacion de AgenticIRs |
| **F7-S3** | ModelRouter production hardening + budget enforcement | Hardening del Multi-Model Router con presupuesto |
| **F7-S4** | Watchman (file watcher) + Integracion F7 | Watcher en tiempo real, integracion final F7 |

### 15.6 F8: Autonomy — Goal Manager, Intention Graph, Autonomia 10/10 (5 sprints)

| Sprint | Componentes | Descripcion |
|--------|-------------|-------------|
| **F8-S1** | GoalManager avanzado + dependency resolution | Goals con dependencias complejas, deteccion de conflictos |
| **F8-S2** | IntentionGraph full + auto-decision tracking | Registro automatico de todas las decisiones con razones |
| **F8-S3** | Self-healing agents (basado en ExperienceEngine) | Agentes que se auto-reparan segun experiencias pasadas |
| **F8-S4** | Autonomous HITL reduction | Reduccion de intervenciones humanas: el sistema predictivo reemplaza al HITL en casos de confianza alta |
| **F8-S5** | Integracion F8 + Congelacion del pipeline legacy + Documentacion final | Sistema completamente autonomo. Pipeline legacy congelado como reference code. |

---

## 16. Tabla de esfuerzo actualizada

### 16.1 Archivos nuevos por fase

| Fase | Archivos 179 | Archivos NUEVOS 180 | Total archivos | LOC estimado 179 | LOC estimado 180 | Total LOC |
|------|-------------|---------------------|----------------|-------------------|-------------------|-----------|
| F4 | 15 | 8 | **23** | ~2,250 | ~1,200 | **~3,450** |
| F5 | 10 | 12 | **22** | ~950 | ~1,800 | **~2,750** |
| F6 | 8 | 8 | **16** | ~1,500 | ~1,200 | **~2,700** |
| F7 | 6 | 6 | **12** | ~1,200 | ~900 | **~2,100** |
| F8 | — | 10 | **10** | — | ~1,500 | **~1,500** |
| **Total** | **39** | **44** | **~83** | **~5,900** | **~6,600** | **~12,500** |

### 16.2 Tests nuevos por fase

| Fase | Tests 179 | Tests NUEVOS 180 | Total tests |
|------|-----------|-------------------|-------------|
| F4 | 80 | 60 | **140** |
| F5 | 120 | 90 | **210** |
| F6 | 100 | 80 | **180** |
| F7 | 80 | 50 | **130** |
| F8 | — | 100 | **100** |
| **Total** | **~380** | **~380** | **~760** |

### 16.3 Acumulado total post-migracion

| Componente | Actual (post-F3) | Post-migracion (F8) |
|------------|------------------|---------------------|
| Archivos Python | ~233 | ~316 (+83) |
| Lineas Python | ~29,241 | ~41,741 (+12,500) |
| Tests Python | ~1,072 | ~1,832 (+760) |
| Agentes | 10 (SDLC) | 16 (SDLC + nuevos) |
| Herramientas | 0 (todo LLM) | 16+ herramientas |
| Niveles de memoria | 0 | 4 |
| Grafos en KG | 1 (SDLC) | 6 (SDLC + Repo + World + Intention + Timeline + Experience) |

---

## 17. Autonomia: Diferencias entre 9/10 y 10/10

### 17.1 Que hace falta para 10/10 en autonomia

| Capacidad | 9/10 | 10/10 |
|-----------|------|-------|
| **Planificacion** | Descompone tareas secuencialmente | Descompone multi-objetivo, detecta dependencias, prioriza (GoalManager) |
| **Contexto** | Conoce el codigo (Repository Graph) | Conoce el proyecto completo (World Model) |
| **Decisiones** | Toma decisiones, no las registra | Toma decisiones, las registra con razones (Intention Graph + Reasoning Memory) |
| **Aprendizaje** | Ejecuta, no aprende de errores | Aprende de cada exito y fallo (Experience Engine) |
| **Costo** | Usa LLM para todo | Decide si usar herramienta o LLM (Cost Optimizer) |
| **Modelos** | Usa un modelo para todo | Usa el modelo optimo para cada tarea (Multi-Model Router) |
| **Prediccion** | Reacciona a errores | Predice errores antes de ejecutar (Prediction Engine) |
| **Memoria** | 3 niveles (que, que significa, como) | 4 niveles (+ por que) |
| **Mejora continua** | PDCA MASS cada N eventos | PDCA MASS + datos reales de Experience Engine |
| **Intervencion humana** | Requiere aprobacion para cambios complejos | Solo requiere aprobacion para cambios de alto riesgo (predichos por Prediction Engine) |

### 17.2 Cuando se alcanza el 10/10

```
Autonomia 10/10 = F8 completado

Condiciones:
  ✓ GoalManager descompone cualquier request multi-objetivo
  ✓ WorldModel conoce estado global del proyecto
  ✓ IntentionGraph registra toda decision con su razon
  ✓ ExperienceEngine ha acumulado >= 1000 experiencias
  ✓ CostOptimizer evita >= 60% de llamadas LLM
  ✓ MultiModelRouter elige modelo optimo con >= 95% acierto
  ✓ PredictionEngine predice impacto con >= 85% precision
  ✓ ReasoningMemory puede explicar cualquier decision pasada
  ✓ HITL solo interviene en < 10% de las tareas
  ✓ 0 regresiones en los ultimos 100 cambios autonomos
```

---

## 18. Riesgos especificos de la extension cognitiva

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| **GoalManager genera objetivos incorrectos** | Media | Alto | Validacion humana en F4-S5. Gradualmente reducir HITL a medida que mejora la precision. |
| **IntentionGraph crece sin control (>1M nodos)** | Alta | Medio | Podar nodos de baja importancia, agregar TTL a razones de decisiones antiguas. |
| **ExperienceEngine aprende patrones incorrectos** | Baja | Alto | Toda experiencia tiene `confidence`. Solo experiencias con confianza > 0.7 afectan decisiones. |
| **CostOptimizer subestima tareas complejas** | Media | Medio | Toda decision del CostOptimizer es sobreescribible por el MultiModelRouter si el resultado no es optimo. |
| **PredictionEngine genera falsos positivos** | Alta | Bajo | Falso positivo = precaucion extra, no bloqueo. El sistema continua pero con alertas. |
| **MultiModelRouter aumenta latencia por decision de ruteo** | Baja | Medio | El ruteo es O(1) (hash lookup). No afecta latencia apreciablemente. |

---

## 19. Conclusion

### 19.1 Resumen de cambios respecto a 179

| Aspecto | 179 (original) | 180 (corregido/extendido) |
|---------|---------------|---------------------------|
| IR canonico | Eliminar | Preservar como legacy + NUEVO AgenticIR |
| Niveles de memoria | 3 | 4 (+ Reasoning Memory) |
| Agentes | 9 | 11 (+ WorldModelAgent, ExperienceAgent) |
| Roadmap | F4-F7 (16 sprints) | F4-F8 (24 sprints) |
| LOC estimado | ~5,900 | ~12,500 |
| Tests estimados | ~380 | ~760 |
| EventBus topics | ~50 | ~80 |
| Herramientas | 16 | 16 (con CostOptimizer) |
| Modelos | 1 para todo | Multi-modelo por tarea |

### 19.2 Proximos pasos

1. **Aceptar/rechazar cada seccion de 180** en una revision
2. Si aceptado, generar **plan de ejecucion F4** (`181_PLAN_DEV_CODE_ASSISTANT_F4_EXECUTION_1_0_DRAFT.md`) con:
   - Desglose por sprint (F4-S1 a F4-S5)
   - Especificacion tecnica detallada de cada componente
   - Dependencias entre tareas
   - Criterios de exito por sprint
   - Estimacion de esfuerzo por archivo

---

*Documento de extension cognitiva basado en la revision de `docs/179_PROP_DEV_CODE_ASSISTANT_AGENTIC_PLATFORM_1_0_DRAFT.md` y las observaciones del arquitecto. Fecha: 2026-06-20.*
