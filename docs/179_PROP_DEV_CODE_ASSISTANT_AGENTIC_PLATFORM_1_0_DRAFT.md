---
id: 179
area: dev
type: prop
module: code_assistant_agentic_platform
version: 1.0
status: DRAFT
tags:
  - proposal
  - architecture
  - migration
  - agentic-platform
  - roadmap
  - post-f3
summary: "Propuesta de migracion/adaptacion de la arquitectura actual (pipeline compilador + SDLC reactivo) hacia una Code Assistant Agentic Platform, tipo Cursor/Claude Code, con agentes especializados, Repository Graph, memoria de 3 niveles y enrutamiento dinamico."
keywords:
  - code-assistant
  - agentic-platform
  - repository-graph
  - multi-agent
  - knowledge-graph
  - treesitter
  - langgraph
  - event-bus
  - technical-debt
changelog:
  - version: 1.0
    date: 2026-06-20
    author: system
    changes:
      - "Creacion de propuesta de migracion arquitectonica post-F2+F3"
---

# Propuesta de Migracion Arquitectonica — Code Assistant Agentic Platform

**Version del documento:** 1.0
**Fecha:** 2026-06-20
**Pre-requisito:** Fase 2 (`docs/159_PLAN_DEV_PDCA_SDLC_F2_EXECUTION_1_0_DRAFT.md`) y Fase 3 (`docs/160_PLAN_DEV_PDCA_SDLC_F3_EXECUTION_1_0_DRAFT.md`) completadas
**Estado:** PROPUESTA — sujeta a revision y refinamiento

---

## Tabla de Contenidos

1. [Executive Summary](#1-executive-summary)
2. [Current State (Post-F2+F3)](#2-current-state-post-f2f3)
3. [Vision: Code Assistant Agentic Platform](#3-vision-code-assistant-agentic-platform)
4. [Architectural Shift: Pipeline → Agent-Centric](#4-architectural-shift-pipeline--agent-centric)
5. [Repository Intelligence Agent](#5-repository-intelligence-agent)
6. [Extended Knowledge Graph](#6-extended-knowledge-graph)
7. [Multi-Agent Architecture](#7-multi-agent-architecture)
8. [Tool System](#8-tool-system)
9. [Memory System](#9-memory-system)
10. [Prompt Pipeline](#10-prompt-pipeline)
11. [LangGraph Evolution](#11-langgraph-evolution)
12. [EventBus Evolution](#12-eventbus-evolution)
13. [Migration Roadmap](#13-migration-roadmap)
14. [Dependency Map](#14-dependency-map)
15. [Risks and Mitigation](#15-risks-and-mitigation)
16. [Conclusion](#16-conclusion)

---

## 1. Executive Summary

### Que propone este documento

Una migracion arquitectonica del sistema actual (pipeline compilador NL→Codigo + SDLC reactivo ISO 12207) hacia una **Code Assistant Agentic Platform**: un sistema multi-agente donde el centro no es el pipeline de compilacion sino un conjunto de **agentes especializados** que colaboran via EventBus, operan sobre un **Repository Graph** vivo, y ejecutan tareas de ingenieria de software (analisis, codificacion, review, testing, refactor, documentacion).

### Prerequisito critico

Esta propuesta **no reemplaza** las Fases 2 y 3 del plan PDCA-sdlc. Al contrario, las asume como base: la infraestructura de agentes (F1), el Deep-Path con ArchitectAgent, VerificationAgent, Quality Gates, SwarmCoordinator (F2), y el SDLC completo con TesterAgent, DocWriterAgent, ConfigMgmtAgent, PDCAEngine, HITLGateway (F3) son los **cimientos** sobre los que se construye esta nueva capa.

### Relacion con el codigo existente

| Componente actual | Rol en la nueva arquitectura |
|-------------------|------------------------------|
| `agentic_pipeline/` (10 stages) | Se **refactoriza**: los stages pasan de ser el centro a ser **habilidades invocables** por los agentes |
| `pdca_sdlc/` (agentes SDLC) | Se **extiende**: los agentes actuales se convierten en sub-agentes del nuevo ecosistema |
| `AsyncEventBus` | Sigue siendo el **sistema nervioso central** |
| `KnowledgeGraph` | Se **expande drasticamente** para modelar el codigo fuente |
| `generators/` | Se **mantienen** como herramientas de los CodingAgent y RefactorAgent |
| `prompt_chain/` | Se **refactoriza** a Prompt Pipeline con encadenamiento estructurado |
| `orchestrator.py` (StateGraph) | Se **evoluciona** a un grafo de agentes dinamico |

---

## 2. Current State (Post-F2+F3)

### 2.1 Arquitectura resultante tras F2+F3

```
                    main.py (entrypoint)
                         │
                    AsyncEventBus
                         │
      ┌──────────────────┼──────────────────┐
      ▼                  ▼                  ▼
 8-10 Agentes SDLC   QualityGates     SwarmCoordinator
      │                  │                  │
      └──────────────────┼──────────────────┘
                         ▼
                  KnowledgeGraph
                  (NetworkX/Neo4j)
                         │
                  Dashboard HTTP
                  (15 endpoints + SSE)
```

### 2.2 Agentes existentes tras F3

| Agente | Evento Trigger | Output | Proposito |
|--------|---------------|--------|-----------|
| AdaptationAgent | `project.initialized` | `adaptation.complete` | Clasifica complejidad, asigna lifecycle |
| RequirementsAnalyst | `adaptation.complete` | `requirement.created` | Descompone descripcion en requisitos |
| ArchitectAgent | `requirement.created` | `architecture.proposed` | Disena componentes, ADRs |
| CoderAgent | `architecture.proposed` | `code.committed` / `code.failed` | Genera codigo via generators/LLM |
| TesterAgent | `code.committed` | `test.executed` | Ejecuta tests, mide cobertura |
| VerificationAgent | `code.committed` | `verification.complete` | Trazabilidad + LLM-as-a-Judge |
| DocWriterAgent | `code.committed` | `artifact.published` | Documentacion automatica |
| ConfigMgmtAgent | `code.committed` | `artifact.versioned` | Versionado semantico, baselines |
| ProjectTracker | `proyecto.{id}.>` | `project.progress.report` | Monitoreo pasivo, deteccion de riesgos |
| HITLGateway | `human.input.needed` | `human.decision.submitted` | Intervencion humana |

### 2.3 Limitaciones detectadas (post-F3)

| Limitacion | Problema | Impacto |
|------------|----------|---------|
| Conocimiento del repositorio | El sistema no tiene un modelo vivo del codigo fuente. Solo ve lo que los agentes escriben. | No puede responder preguntas como "que archivos afectan este endpoint?" |
| Agentes monoliticos | Cada agente mezcla razonamiento + ejecucion. No hay separacion de concerns. | Dificil de testear, extender, o remplazar individualmente |
| Sin contexto del proyecto real | El sistema opera sobre descripciones abstractas, no sobre el arbol de archivos real | El codigo generado puede no integrarse con el codigo existente |
| Sin memoria de largo plazo | No hay distincion entre memoria episodica (que hice), semantica (que significa), procedural (como se hace) | El sistema no aprende de experiencia |
| Sin herramientas explicitas | Los agentes usan LLM para todo, no invocan herramientas especializadas | Costo alto, precision baja en tareas deterministicas |
| Sin enrutamiento inteligente | El pipeline SDLC es fijo (Adaptation → Req → Architect → Coder → ...) | No puede saltar directamente a "necesito refactorizar X funcion" |

---

## 3. Vision: Code Assistant Agentic Platform

### 3.1 Filosofia

> De "transformar lenguaje natural en codigo" a "mantener un modelo vivo del repositorio, razonar sobre el, y coordinar agentes especializados que colaboran para desarrollar, revisar, probar y evolucionar el software."

### 3.2 Arquitectura objetivo

```
                    ┌─────────────────────────────┐
                    │        User Request         │
                    │  (CLI, WebUI, API, Editor)  │
                    └─────────────┬───────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │      Intent Router          │
                    │  (clasifica: refactor?      │
                    │   new feature? test? doc?)  │
                    └─────────────┬───────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │  Planning Agent │  │  Repository     │  │  Memory         │
    │  (Task Graph)   │◄─┤  Intelligence   │◄─┤  (3 niveles)    │
    └────────┬────────┘  │  Agent          │  └─────────────────┘
             │           └────────┬────────┘
             │                    │
             └────────────────────┼────────────────────┐
                                  │                    │
                    ┌─────────────▼───────────────┐    │
                    │      Task Decomposer        │    │
                    │  (goal → DAG de sub-tasks)  │    │
                    └─────────────┬───────────────┘    │
                                  │                    │
              ┌───────────────────┼───────────────────┐│
              ▼                   ▼                   ▼▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │  Coding Agent   │  │  Review Agent   │  │  Test Agent     │
    │  (genera codigo)│  │  (SOLID, Clean) │  │  (genera tests) │
    └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
             │                    │                    │
             ▼                    ▼                    ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │  Refactor Agent │  │  Security Agent │  │  Documentation  │
    │  (mejora codigo)│  │  (OWASP, XSS)   │  │  Agent (docs)   │
    └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
             │                    │                    │
             └────────────────────┼────────────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │      Validation Gate        │
                    │  (Quality Gates + Review)   │
                    └─────────────┬───────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │      Git Operations         │
                    │  (commit, branch, PR)       │
                    └─────────────────────────────┘

              ┌──────────────────────────────────────────┐
              │           EventBus + KnowledgeGraph      │
              │  (coordinacion reactiva entre todos)     │
              └──────────────────────────────────────────┘
```

### 3.3 Principios rectores

1. **Agent-Centric**: Los agentes son el centro. El pipeline es solo un patron de coordinacion mas.
2. **Modelo Vivo del Repositorio**: El sistema mantiene un grafo actualizado del codigo fuente en todo momento.
3. **Herramientas Explicitas**: Los agentes invocan herramientas (AST, LSP, ripgrep, git) en vez de depender del LLM para tareas deterministicas.
4. **Memoria de 3 Niveles**: Episodica (que hice), Semantica (que significa), Procedural (como se hace).
5. **Encadenamiento de Prompts**: Cada paso produce salida estructurada que alimenta al siguiente.
6. **Reactivo por Eventos**: Todo el sistema se coordina via EventBus con topicos jerarquicos y wildcards.
7. **Enrutamiento Dinamico**: El grafo de agentes no es fijo; se construye segun la tarea.

---

## 4. Architectural Shift: Pipeline → Agent-Centric

### 4.1 Que cambia

| Aspecto | Hoy (post-F3) | Objetivo |
|---------|---------------|----------|
| Centro del sistema | Pipeline SDLC fijo (10 etapas secuenciales) | Agentes especializados con enrutamiento dinamico |
| Flujo de trabajo | Adaptation → Req → Architect → Coder → Tester → Verifier → Docs → Config | Intent Router → Plan → Task Graph → Agentes especializados → Validacion → Git |
| Conocimiento del codigo | Solo el que los agentes escriben al KG | Repository Graph construido via TreeSitter + AST + LSP |
| Herramientas | Ninguna explicita (todo via LLM) | 15+ herramientas explicitas (ReadFile, Search, AST, LSP, Git, Docker) |
| Memoria | Conversacional (event log) | 3 niveles: Episodica, Semantica, Procedural |
| Pipeline de prompts | Unico prompt grande por agente | Encadenamiento estructurado: Understand → Analyze → Plan → Generate → Review → Test → Refactor → Commit |
| Routing | Lineal fijo (si-complex entonces architect) | Grafo dinamico segun tipo de tarea (analysis, refactor, doc, test, feature) |

### 4.2 Que se preserva

| Componente | Por que se preserva |
|------------|---------------------|
| `AsyncEventBus` | Es el sistema nervioso central. Ya soporta wildcards, indices, SSE. Solo extender topicos. |
| `KnowledgeGraph` | Se expande pero su interfaz (add_node, add_edge, query, get_trace) se mantiene. |
| `QualityGates` | Siguen siendo el mecanismo de validacion en los puntos de control. |
| `generators/` | Los CodingAgent y RefactorAgent los usan como herramientas. |
| `Dashboard` | Se extiende con nuevos endpoints para el Repository Graph. |
| `HITLGateway` | Sigue manejando intervencion humana cuando los agentes lo requieren. |
| `ConfigMgmtAgent` | Versionado y baselines siguen siendo necesarios. |
| `PDCAEngine` | MASS optimization se aplica a los nuevos agentes tambien. |

### 4.3 Mapeo de componentes actuales a nuevos

| Componente actual | Nuevo rol | Cambio requerido |
|-------------------|-----------|------------------|
| `perception_unit.py` | → `IntentRouter` (primer paso del Prompt Pipeline) | Refactor: separar clasificacion de intencion del pipeline |
| `preprocessor.py` | → `RepositoryIntelligenceAgent` (normalizacion de texto + code context) | Expandir: de texto plano a code-aware |
| `lexer.py` + `parser.py` | → `RepositoryIntelligenceAgent` (AST builder via TreeSitter) | Reescribir: de DFA/Lark a TreeSitter + AST |
| `semantic_analyzer.py` | → `RepositoryIntelligenceAgent` (Symbol Graph) | Expandir: de type checking a grafo de simbolos completo |
| `ir_generator.py` | → Se elimina como etapa. IR se construye directamente del Task Graph | Remover: el IR canonico deja de ser necesario |
| `reasoning_engine.py` | → `PlanningAgent` (Task Graph desde goals) | Refactor: de planner de pipeline a planner de agentes |
| `action_executor.py` | → `CodingAgent` (usa generators como herramientas) | Refactor: separar ejecucion de plan de decision |
| `ui_generator.py` | → `CodingAgent` (herramienta UI) | Integrar como herramienta |
| `validator.py` | → `ReviewAgent` + `SecurityAgent` | Dividir: cada concern en su propio agente |
| `feedback_loop.py` | → `Memory` (nivel semantico + procedural) | Expandir: de metricas de stage a memoria completa |

---

## 5. Repository Intelligence Agent

### 5.1 Que es

Es el agente que **construye y mantiene un modelo vivo del repositorio de codigo**.

Cuando el sistema se conecta a un proyecto, este agente:
1. Escanea todo el arbol de archivos
2. Construye ASTs con TreeSitter para cada archivo de codigo
3. Extrae simbolos (clases, funciones, metodos, interfaces, tipos)
4. Construye el grafo de dependencias (imports, requires, extends)
5. Detecta patrones arquitectonicos (DDD?, Clean Architecture?, MVC?)
6. Indexa endpoints, entidades, DTOs, schemas, tests
7. Almacena todo en el `KnowledgeGraph` como `Repository Graph`

### 5.2 Pipeline de construccion del Repository Graph

```
Open Repository
      │
      ▼
Language Detector
  ├── Detecta lenguajes por extension/ shebang
  ├── multi-lenguaje (Python, TypeScript, Go, Rust, etc.)
  └── output: {language: path[]}
      │
      ▼
TreeSitter Parser
  ├── Por cada archivo: parsea a AST concreto
  ├── Extrae: clases, funciones, metodos, interfaces, tipos, imports, exports
  └── output: list[SyntaxNode]
      │
      ▼
AST Builder
  ├── Construye AST semantico (no sintactico)
  ├── Resuelve referencias cruzadas entre archivos
  └── output: SemanticAST (cruzado por archivo)
      │
      ▼
Symbol Graph Builder
  ├── Extrae todos los simbolos del proyecto
  ├── Resuelve: quien define X, quien importa X, quien extiende X
  ├── Detecta: ciclos, dependencias no utilizadas, dependencias faltantes
  └── output: SymbolGraph (NetworkX DiGraph)
      │
      ▼
Dependency Graph Builder
  ├── Por modulo/archivo: grafo de dependencias
  ├── Niveles: external → internal → same-module
  └── output: DependencyGraph
      │
      ▼
Architecture Detector
  ├── Heuristics para detectar patrones:
  │   - NestJS: modules, controllers, services, entities
  │   - DDD: domain, application, infrastructure, interfaces
  │   - Clean Architecture: usecases, entities, gateways
  │   - MVC: models, views, controllers
  ├── Detecta violaciones de capas
  └── output: ArchitectureModel + list[Violation]
      │
      ▼
Repository Graph
  ├── Nodos: Repository, Module, Class, Method, Function,
  │          Interface, Entity, Endpoint, DTO, Schema, Test,
  │          Import, Export, Decorator, Annotation
  ├── Aristas: defines, imports, extends, implements, calls,
  │            called_by, belongs_to, references, tested_by
  └── Almacenado en: KnowledgeGraph (NEO4J para persistencia)
```

### 5.3 Arbol de archivos propuesto

```
compiler-bot/repository_agent/
├── __init__.py
├── repository_intelligence_agent.py   # Agente principal
├── language_detector.py               # Deteccion de lenguajes
├── treesitter_parser.py               # TreeSitter wrapper
├── ast_builder.py                     # AST semantico
├── symbol_graph.py                    # Grafo de simbolos
├── dependency_graph.py                # Grafo de dependencias
├── architecture_detector.py           # Deteccion de patrones
├── repository_graph_builder.py        # Constructor del Repository Graph
├── watchman.py                        # Watcher de cambios en tiempo real
└── tests/
    ├── test_language_detector.py
    ├── test_treesitter_parser.py
    ├── test_symbol_graph.py
    ├── test_dependency_graph.py
    └── test_architecture_detector.py
```

### 5.4 Integracion con el Knowledge Graph existente

Los tipos de nodo existentes (requirement, goal, artifact, risk, component, code_module) **se mantienen**. Se agregan nuevos tipos:

```python
class NodeType(str, Enum):
    # Existentes (F1-F3)
    GOAL = "goal"
    REQUIREMENT = "requirement"
    COMPONENT = "component"
    CODE_MODULE = "code_module"
    ARCHITECTURE_DECISION = "architecture_decision"
    RISK = "risk"
    ARTIFACT = "artifact"
    TASK = "task"
    MILESTONE = "milestone"
    TEST_SUITE = "test_suite"

    # Nuevos (Repository Graph)
    REPOSITORY = "repository"           # El proyecto en si
    SOURCE_FILE = "source_file"         # Archivo de codigo fuente
    CLASS = "class"                      # Clase
    METHOD = "method"                    # Metodo de clase
    FUNCTION = "function"                # Funcion libre
    INTERFACE = "interface"             # Interfaz / type / protocol
    ENTITY = "entity"                    # Entidad de dominio / DB
    ENDPOINT = "endpoint"               # Endpoint HTTP
    DTO = "dto"                          # Data Transfer Object
    SCHEMA = "schema"                   # Schema de validacion
    TEST = "test"                       # Test individual
    IMPORT = "import"                    # Import / require
    DEPENDENCY = "dependency"           # Dependencia externa (npm, pip)
    DECORATOR = "decorator"             # Decorador / anotacion
    VARIABLE = "variable"               # Variable global / constante
    PROMPT = "prompt"                   # Prompt template
    TOOL = "tool"                       # Herramienta del sistema
    AGENT = "agent"                     # Agente del sistema
    FEATURE = "feature"                 # Feature / funcionalidad
    COMMIT = "commit"                   # Commit de git
```

### 5.5 Relaciones del Repository Graph

```python
class EdgeType(str, Enum):
    # Existentes
    SATISFIES = "satisfies"
    IMPLEMENTS = "implements"
    VERIFIES = "verifies"
    DEPENDS_ON = "depends_on"
    DOCUMENTS = "documents"
    PRECEDES = "precedes"

    # Nuevas (Repository Graph)
    DEFINES = "defines"                 # Archivo define clase/funcion
    IMPORTS = "imports"                 # Archivo importa otro archivo/simbolo
    EXPORTS = "exports"                 # Archivo exporta simbolo
    EXTENDS = "extends"                 # Clase extiende otra
    IMPLEMENTS_INTERFACE = "implements_interface"
    CALLS = "calls"                     # Funcion llama a otra
    CALLED_BY = "called_by"             # Inversa de calls
    BELONGS_TO = "belongs_to"           # Metodo pertenece a clase
    REFERENCES = "references"           # Referencia a simbolo
    TESTED_BY = "tested_by"             # Codigo tiene test
    TESTS = "tests"                     # Test testea codigo
    GENERATED_BY = "generated_by"       # Archivo generado por agente
    OWNS = "owns"                       # Agente es dueno de archivo
    USES = "uses"                       # Agente usa herramienta
    CONTAINS = "contains"               # Modulo contiene archivo
    ANNOTATED_BY = "annotated_by"       # Decorado por
    CONNECTS_TO = "connects_to"         # Endpoint conecta a DB/API
```

### 5.6 Queries que el Repository Graph permite responder

| Pregunta | Query en el Grafo |
|----------|-------------------|
| "Que archivos afectan este endpoint?" | `ENDPOINT --[belongs_to]--> SOURCE_FILE` |
| "Donde esta definida esta clase?" | `CLASS --[defined_in]--> SOURCE_FILE` |
| "Que tests cubren esta funcion?" | `FUNCTION <--[tests]-- TEST` |
| "Cual es el grafo de dependencias de este modulo?" | `SOURCE_FILE --[imports]--> SOURCE_FILE (BFS)` |
| "Hay ciclos de dependencias?" | DFS sobre `SOURCE_FILE --[imports]--> SOURCE_FILE` |
| "Que endpoints no tienen tests?" | `ENDPOINT --[belongs_to]--> MODULE WHERE sin incoming TEST` |
| "Quien modifico este archivo?" | `SOURCE_FILE <--[changed_by]-- COMMIT <--[authored_by]-- AGENT` |
| "Que capas arquitectonicas viola este modulo?" | `MODULE --[violates]--> ARCHITECTURE_LAYER` |
| "Que dependencias externas usa este proyecto?" | `DEPENDENCY --[used_by]--> SOURCE_FILE` |
| "Cual es el arbol de llamadas de esta funcion?" | `FUNCTION --[calls]--> FUNCTION (recursive BFS)` |

---

## 6. Extended Knowledge Graph

### 6.1 Arquitectura del KG objetivo

```
                    ┌─────────────────────────────────────┐
                    │        NEO4J (persistente)          │
                    │                                     │
                    │  ┌───────────────────────────────┐  │
                    │  │     SDLC Layer (existente)     │  │
                    │  │  Goal ──→ Requirement ──→      │  │
                    │  │  Component ──→ CodeModule      │  │
                    │  │  Artifact ──→ Milestone        │  │
                    │  │  Risk ──→ TestSuite            │  │
                    │  └───────────────────────────────┘  │
                    │                                     │
                    │  ┌───────────────────────────────┐  │
                    │  │   Repository Layer (nuevo)    │  │
                    │  │  Repository ──→ SourceFile    │  │
                    │  │  SourceFile ──→ Class         │  │
                    │  │  Class ──→ Method             │  │
                    │  │  Interface ──→ Function       │  │
                    │  │  Endpoint ──→ Entity          │  │
                    │  │  Import ──→ Dependency        │  │
                    │  └───────────────────────────────┘  │
                    │                                     │
                    │  ┌───────────────────────────────┐  │
                    │  │   Agent Layer (nuevo)         │  │
                    │  │  Agent ──→ Tool               │  │
                    │  │  Agent ──→ Prompt             │  │
                    │  │  Agent ──→ Feature            │  │
                    │  └───────────────────────────────┘  │
                    └─────────────────────────────────────┘
```

### 6.2 Como se conectan las capas

```
SDLC Layer                    Repository Layer
Goal ──────────────────────── Feature (funcionalidad implementada)
Requirement ────────────────── Function / Endpoint (codigo que satisface)
Component ─────────────────── Module / Class (diseno → codigo)
CodeModule ────────────────── SourceFile (unidad de despliegue)
Artifact ──────────────────── Commit (documentacion del cambio)
TestSuite ─────────────────── Test (suite → tests individuales)

Agent Layer                   Repository Layer
Agent ─────[uses]─────────── Tool (agente usa herramienta)
Agent ─────[generates]────── SourceFile (agente escribe archivo)
Agent ─────[owns]─────────── Feature (agente dueno de funcionalidad)
Prompt ────[specialized_for] Agent (prompt define comportamiento)
```

### 6.3 Estrategia de migracion del KG

| Fase | Accion | Componentes afectados |
|------|--------|----------------------|
| **F3 (pre-req)** | Migrar SDLC layer de NetworkX a Neo4j | `Neo4jKnowledgeGraph` con fallback a NetworkX |
| **F4a** | Agregar Repository Layer a Neo4j | `repository_graph_builder.py` escribe nodos SOURCE_FILE, CLASS, METHOD |
| **F4b** | Agregar Agent Layer a Neo4j | Agents auto-registran su manifest como nodo AGENT |
| **F4c** | Unificar queries cross-layer | `kg.query("MATCH ...")` que cruce SDLC ↔ Repository ↔ Agent |
| **F5** | Indices y performance | Indices por node_type, properties, full-text search |

---

## 7. Multi-Agent Architecture

### 7.1 Agentes propuestos

| Agente | Responsabilidad | Entrada | Salida | Herramientas que usa |
|--------|----------------|---------|--------|---------------------|
| **IntentRouter** | Clasifica request: refactor? feature? test? doc? bugfix? | User request | Intent + Confidence | LLM (clasificacion ligera) |
| **PlanningAgent** | Descompone goal en Task Graph (DAG topologico) | Intent + Repository Context | Task Graph | LLM (Tree-of-Thought) |
| **RepositoryIntelligence** | Construye y consulta el Repository Graph | File system | Repository Graph | TreeSitter, AST, SymbolGraph, LSP |
| **CodingAgent** | Genera codigo siguiendo el Task Graph | Task + Context + Arch Decision | Source files | Generators (NestJS, Prisma, React), WriteFile, Search |
| **ReviewAgent** | Revisa codigo: SOLID, Clean Code, DDD, convenciones | Source files + Diff | Review Report | LLM-as-a-Judge, Search, AST |
| **TestAgent** | Genera y ejecuta tests | Source files | Test files + Results | TestRunner (pytest, jest), Coverage |
| **RefactorAgent** | Mejora codigo existente sin cambiar funcionalidad | Source files + Goal | Refactored files | AST, LSP, Search, Rename |
| **SecurityAgent** | Escanea vulnerabilidades | Source files | Security Report | Pattern matching, AST, OWASP rules |
| **DocumentationAgent** | Genera documentacion | Source files + Architecture | Markdown/ADR | ReadFile, Search, LLM |
| **PerformanceAgent** | Detecta cuellos de botella | Source files + Profile data | Performance Report | AST (loop detection), Query analyzer |

### 7.2 Ciclo de vida de un agente

Cada agente sigue el mismo ciclo de vida:

```python
class Agent(ABC):
    """Base para todos los agentes del sistema."""
    
    # Metadatos
    agent_id: str
    manifest: CapabilityManifest
    
    # Dependencias inyectadas
    event_bus: AsyncEventBus
    knowledge_graph: KnowledgeGraph
    tools: ToolRegistry
    memory: MemorySystem
    llm: LLMClient
    
    async def start(self):
        """Suscribe al EventBus segun su manifest.triggers."""
        for topic in self.manifest.triggers:
            await self.event_bus.subscribe(topic, self.handle_event)
    
    @abstractmethod
    async def handle_event(self, event: Event):
        """Procesa un evento y produce resultado."""
        # 1. Analyze: cargar contexto del KG
        context = await self._load_context(event)
        
        # 2. Plan: decidir acciones
        plan = await self._plan(context)
        
        # 3. Execute: usar herramientas
        result = await self._execute(plan)
        
        # 4. Learn: actualizar memoria
        await self._learn(event, plan, result)
        
        # 5. Publish: emitir evento de salida
        await self.event_bus.publish(result.event)
    
    async def stop(self):
        """Cancela suscripciones y libera recursos."""
        ...
```

### 7.3 Enrutamiento dinamico via IntentRouter

El IntentRouter no es un agente mas. Es el **primer punto de contacto** que decide que agentes activar:

```python
class IntentRouter:
    """Router de intenciones. Decide que agentes activar segun el request."""
    
    INTENT_ROUTES = {
        "new_feature": {
            "agents": ["repository", "planning", "coding", "review", "test"],
            "requires_architect": True,
            "pipeline": "feature_pipeline"
        },
        "refactor": {
            "agents": ["repository", "refactor", "review", "test"],
            "requires_architect": False,
            "pipeline": "refactor_pipeline"
        },
        "bugfix": {
            "agents": ["repository", "coding", "test"],
            "requires_architect": False,
            "pipeline": "bugfix_pipeline"
        },
        "documentation": {
            "agents": ["repository", "documentation"],
            "requires_architect": False,
            "pipeline": "doc_pipeline"
        },
        "test": {
            "agents": ["repository", "test"],
            "requires_architect": False,
            "pipeline": "test_pipeline"
        },
        "security_audit": {
            "agents": ["repository", "security"],
            "requires_architect": False,
            "pipeline": "security_pipeline"
        },
        "performance_audit": {
            "agents": ["repository", "performance"],
            "requires_architect": False,
            "pipeline": "performance_pipeline"
        },
        "analysis": {
            "agents": ["repository"],
            "requires_architect": False,
            "pipeline": "analysis_pipeline"
        }
    }
    
    async def route(self, request: str) -> IntentRoute:
        """Clasifica request y retorna ruta de agentes."""
        intent = await self._classify_intent(request)
        route = self.INTENT_ROUTES.get(intent, self.INTENT_ROUTES["new_feature"])
        
        # Publicar evento de ruta
        await self.event_bus.publish(Event(
            topic="intent.routed",
            data={
                "intent": intent,
                "pipeline": route["pipeline"],
                "agents": route["agents"],
                "raw_request": request
            }
        ))
        return route
```

### 7.4 Coordinacion via EventBus

Los agentes no se llaman directamente. Se coordinan via eventos:

```
intent.routed
  └→ repository.indexed (RepositoryIntelligence completa analisis)
       └→ plan.created (PlanningAgent genera Task Graph)
            ├→ code.generated (CodingAgent completa tarea)
            │    ├→ review.completed (ReviewAgent aprueba)
            │    │    └→ tests.passed (TestAgent verifica)
            │    │         └→ code.committed (Git operations)
            │    └→ test.failed → code.failed → risk.identified
            └→ code.refactored (RefactorAgent)
                 └→ review.completed
                      └→ tests.passed
                           └→ code.committed
```

---

## 8. Tool System

### 8.1 Filosofia

> **No todo debe pasar por el LLM.**

Tareas deterministicas (buscar en el codigo, leer un archivo, ejecutar sintaxis) deben ser ejecutadas por herramientas especializadas, no por el LLM. Esto reduce costos, aumenta precision, y permite auditabilidad.

### 8.2 Catalogo de herramientas propuesto

| Herramienta | Proposito | Implementacion | La usa(n) |
|-------------|-----------|----------------|-----------|
| **ReadFileTool** | Leer contenido de archivo | `open().read()` | Todos los agentes |
| **WriteFileTool** | Escribir contenido a archivo | `open().write()` con backup | Coding, Refactor, Doc |
| **SearchTool** | Busqueda textual (ripgrep-like) | `re.search()` sobre archivos | Repository, Review, Security |
| **RipgrepTool** | Busqueda regex rapida | `subprocess.run(["rg", ...])` | Repository, Review, Security |
| **GlobTool** | Listar archivos por patron | `glob.glob()` | Repository, Planning |
| **GitTool** | Operaciones git (diff, log, status, commit) | `subprocess.run(["git", ...])` | Planning, Review |
| **DockerTool** | Build/run contenedores | `subprocess.run(["docker", ...])` | Test, Coding |
| **TestRunnerTool** | Ejecutar tests y parsear resultados | `subprocess.run([pytest|jest, ...])` | TestAgent |
| **TerminalTool** | Ejecutar comandos arbitrarios | `subprocess.run()` con sandbox | Todos (con restricciones) |
| **BrowserTool** | Navegar/documentacion web | `httpx` + `BeautifulSoup` | Documentation |
| **ASTTool** | Construir/consultar AST de archivos | TreeSitter | Repository, Refactor, Review |
| **DependencyGraphTool** | Resolver grafo de dependencias | `SymbolGraph` + `networkx` | Repository, Planning |
| **LSPTool** | Code intelligence (goto def, find refs, hover) | LSP protocol via `pygls` | Coding, Refactor, Review |
| **EmbeddingSearchTool** | Busqueda semantica en el codigo | `sentence-transformers` + FAISS | Repository, Planning |
| **SymbolLookupTool** | Encontrar definicion de simbolo | Repository Graph query | Todos |
| **DiffTool** | Generar y mostrar diff de cambios | `difflib` | Review, Git |

### 8.3 Arquitectura del Tool Registry

```python
class ToolRegistry:
    """Registro central de herramientas. Los agentes acceden via inyeccion."""
    
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> BaseTool:
        return self._tools[name]
    
    def list_for_agent(self, agent_id: str) -> list[BaseTool]:
        """Retorna herramientas disponibles para un agente."""
        return [t for t in self._tools.values() 
                if agent_id in t.allowed_agents or "*" in t.allowed_agents]

class BaseTool(ABC):
    name: str
    description: str
    allowed_agents: list[str]  # ["*"] = todos
    
    @abstractmethod
    async def execute(self, params: dict) -> ToolResult:
        ...
    
    @abstractmethod
    def get_schema(self) -> dict:
        """Retorna JSON schema de parametros."""
        ...
```

### 8.4 Seguridad de herramientas

| Mecanismo | Descripcion |
|-----------|-------------|
 | Sandbox de terminal | `TerminalTool` solo ejecuta comandos en lista blanca |
| Backup en WriteFile | `WriteFileTool` guarda `.bak` antes de sobrescribir |
| Rate limiting | Max N llamadas por minuto por agente |
| Auditoria | Todas las llamadas a herramientas se registran en el EventBus como `tool.executed` |
| Restriccion por agente | Cada herramienta tiene `allowed_agents` |

---

## 9. Memory System

### 9.1 Los 3 niveles

```
Memory System
      │
      ├── Episodic Memory
      │   ├── Que hice: sesiones, acciones, decisiones
      │   ├── Almacen: EventBus log (ya existe)
      │   ├── Persistencia: SQLite / Neo4j
      │   └── Query: "que hice en la sesion anterior?"
      │
      ├── Semantic Memory
      │   ├── Que significa: patrones del proyecto, arquitectura, convenciones
      │   ├── Almacen: Knowledge Graph (Repository Graph + SDLC Graph)
      │   ├── Persistencia: Neo4j
      │   └── Query: "este proyecto usa Clean Architecture?"
      │
      └── Procedural Memory
          ├── Como se hace: recetas, workflows, templates
          ├── Almacen: Knowledge Graph (nodos PROCEDURE)
          ├── Persistencia: Neo4j + YAML files
          └── Query: "como creo un endpoint en NestJS?"
```

### 9.2 Episodic Memory

Implementada sobre el EventLog existente:

```python
class EpisodicMemory:
    """Memoria episodica basada en el EventBus log."""
    
    def __init__(self, event_bus: AsyncEventBus):
        self.event_bus = event_bus
    
    async def get_session(self, session_id: str) -> list[Event]:
        """Recupera todos los eventos de una sesion."""
        return await self.event_bus.query_events(
            source=session_id
        )
    
    async def get_recent_actions(self, agent_id: str, limit: int = 10) -> list[Event]:
        """Ultimas acciones de un agente."""
        return await self.event_bus.query_events(
            source=agent_id,
            limit=limit
        )
    
    async def replay_session(self, session_id: str):
        """Replay de una sesion completa."""
        events = await self.get_session(session_id)
        for event in events:
            await self.event_bus.replay(event.id)
```

### 9.3 Semantic Memory

Se construye desde el Repository Graph + SDLC artifacts:

```python
class SemanticMemory:
    """Memoria semantica: patrones, arquitectura, conocimiento del proyecto."""
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
    
    async def get_architecture_pattern(self) -> str:
        """Retorna el patron arquitectonico detectado."""
        nodes = self.kg.query(node_type="architecture_pattern")
        return nodes[0].properties["pattern"] if nodes else "unknown"
    
    async def get_conventions(self) -> list[str]:
        """Retorna convenciones detectadas del proyecto."""
        nodes = self.kg.query(node_type="convention")
        return [n.properties["rule"] for n in nodes]
    
    async def learn_from_experience(self, event: Event, result: dict):
        """Extrae conocimiento semantico de una experiencia."""
        if result.get("success") and event.topic == "review.completed":
            # Aprender patrones de codigo aprobado
            await self._extract_patterns(event.data)
```

### 9.4 Procedural Memory

Recetas almacenadas como nodos PROCEDURE en el KG:

```python
class ProceduralMemory:
    """Memoria procedural: recetas y workflows."""
    
    RECIPES = {
        "create_nestjs_endpoint": [
            {"step": "create_dto", "tool": "WriteFileTool", 
             "template": "dto.template.ts"},
            {"step": "create_service", "tool": "WriteFileTool",
             "template": "service.template.ts"},
            {"step": "create_controller", "tool": "WriteFileTool",
             "template": "controller.template.ts"},
            {"step": "update_module", "tool": "WriteFileTool",
             "template": "module.template.ts"},
            {"step": "create_test", "tool": "TestTool",
             "template": "spec.template.ts"},
        ],
        "add_prisma_model": [
            {"step": "update_schema", "tool": "ReadEditTool",
             "file": "schema.prisma"},
            {"step": "generate_migration", "tool": "TerminalTool",
             "command": "npx prisma migrate dev"},
            {"step": "create_entity", "tool": "WriteFileTool",
             "template": "entity.template.ts"},
        ]
    }
    
    async def get_recipe(self, task_type: str) -> list[dict]:
        return self.RECIPES.get(task_type, [])
    
    async def learn_recipe(self, task_type: str, steps: list[dict]):
        """Aprende una nueva receta basada en experiencia."""
        self.RECIPES[task_type] = steps
        # Persistir a KG
        await self.kg.add_node(Node(
            node_type="procedure",
            properties={"task_type": task_type, "steps": steps}
        ))
```

---

## 10. Prompt Pipeline

### 10.1 De prompt unico a pipeline encadenado

En lugar de un unico prompt gigante por agente:

```
System: Eres un asistente de codigo. Haz lo siguiente...
[context enorme]
[instrucciones complejas]
[formato de salida]
```

Cada paso produce una **salida estructurada** que alimenta al siguiente:

```
Request
  │
  ▼
Step 1: Understand
  ├── Input: user request + project context
  ├── LLM: "Explica que se necesita, en tus palabras"
  ├── Output: Understanding (structured: goal, constraints, scope)
  │   ↓
Step 2: Analyze Repository
  ├── Input: Understanding + Repository Graph
  ├── Tool: RepositoryIntelligenceAgent (consulta KG, no LLM)
  ├── Output: Context (affected files, dependencies, patterns)
  │   ↓
Step 3: Retrieve Context
  ├── Input: Context
  ├── Tool: ReadFileTool + ASTTool + SymbolLookupTool
  ├── Output: DetailedContext (code snippets, signatures, imports)
  │   ↓
Step 4: Plan
  ├── Input: Understanding + DetailedContext
  ├── LLM (Tree-of-Thought): explora 2-3 estrategias
  ├── Output: Plan (Task Graph con tareas ordenadas)
  │   ↓
Step 5: Generate
  ├── Input: Plan + Context
  ├── Tool: CodingAgent (generators + WriteFileTool)
  ├── Output: Generated code (archivos en filesystem)
  │   ↓
Step 6: Review
  ├── Input: Generated code + Plan + Conventions
  ├── LLM (ReviewAgent): evalua SOLID, Clean Code, etc.
  ├── Output: ReviewReport (approved | changes_requested)
  │   ↓
Step 7: Test
  ├── Input: Generated code
  ├── Tool: TestAgent (genera tests + TestRunnerTool)
  ├── Output: TestResults (passed | failed)
  │   ↓
Step 8: Refactor (si review o tests fallaron)
  ├── Input: ReviewReport + TestResults + Code
  ├── Tool: RefactorAgent
  ├── Output: Refactored code
  │   ↓
Step 9: Commit
  ├── Input: Code + Summary
  ├── Tool: GitTool (diff, add, commit)
  └── Output: Commit (hash, message, files)
```

### 10.2 Ventajas del encadenamiento

| Beneficio | Explicacion |
|-----------|-------------|
| **Cada paso es especializado** | Un prompt para entender, otro para planificar, otro para generar. Cada uno optimo para su tarea. |
| **Salidas estructuradas** | No hay "output libre". Cada paso produce JSON validable. |
| **Costo optimizado** | Pasos 2, 3, 5, 7, 9 no usan LLM. Solo los pasos 1, 4, 6 usan llamadas costosas. |
| **Auditabilidad** | Cada paso produce un evento en el EventBus. Se puede replayear cualquier sesion. |
| **Paralelizable** | Pasos independientes (ej: Review + Test) pueden ejecutarse en paralelo. |

### 10.3 Integracion con el PromptChain existente

El `prompt_chain/` actual (Command pattern, CommandHistory, LLMCache) se refactoriza para soportar este pipeline:

```python
class PromptPipeline:
    """Pipeline de prompts encadenados. Reemplaza el uso directo de prompt_chain."""
    
    def __init__(self, event_bus, llm, tool_registry):
        self.event_bus = event_bus
        self.llm = llm
        self.tools = tool_registry
        self.steps: list[PipelineStep] = []
    
    def add_step(self, step: PipelineStep):
        """Agrega un paso al pipeline."""
        self.steps.append(step)
    
    async def execute(self, request: str) -> PipelineResult:
        """Ejecuta el pipeline completo."""
        context = {"request": request}
        
        for step in self.steps:
            # Publicar evento de inicio
            await self.event_bus.publish(Event(
                topic=f"pipeline.step.{step.name}.started",
                data=context
            ))
            
            # Ejecutar paso
            result = await step.execute(context)
            context[step.name] = result
            
            # Publicar evento de completitud
            await self.event_bus.publish(Event(
                topic=f"pipeline.step.{step.name}.completed",
                data={"result": result}
            ))
            
            if not result.success:
                return PipelineResult(success=False, failed_step=step.name)
        
        return PipelineResult(success=True, context=context)
```

---

## 11. LangGraph Evolution

### 11.1 StateGraph actual

Actualmente el `AgentOrchestrator` construye un `StateGraph(StageContext)` con 10 nodos fijos y aristas condicionales (continue/abort).

```
[Perception] → [Preprocessor] → [Lexer] → [Parser] → [Semantic] → [IR] → [Reasoning] → [Executor] → [UI] → [Validator]
```

### 11.2 StateGraph objetivo: Agent Graph dinamico

```python
class AgentGraphBuilder:
    """Construye un StateGraph dinamico segun la ruta de agentes."""
    
    def build(self, route: IntentRoute) -> StateGraph:
        """Construye grafo de agentes para una ruta especifica."""
        graph = StateGraph(AgentContext)
        
        # Nodo inicial: siempre IntentRouter
        graph.add_node("intent_router", IntentRouterNode())
        graph.set_entry_point("intent_router")
        
        # Nodo final: siempre GitCommit (opcional)
        graph.add_node("git_commit", GitCommitNode())
        
        # Agregar agentes segun la ruta
        for agent_name in route.agents:
            agent_node = self._create_agent_node(agent_name)
            graph.add_node(agent_name, agent_node)
        
        # Conectar agentes en orden (con paralelismo cuando sea posible)
        prev_node = "intent_router"
        for agent_name in route.agents:
            graph.add_edge(prev_node, agent_name)
            prev_node = agent_name
        
        # Conectar al nodo final
        graph.add_edge(prev_node, "git_commit")
        
        # Aristas condicionales para review/rework
        graph.add_conditional_edges(
            "review_agent",
            ReviewRouter().should_approve,
            {
                "approved": "git_commit",
                "changes_requested": "coding_agent",  # loop de rework
                "blocked": END
            }
        )
        
        return graph.compile()
```

### 11.3 Routing dinamico

```
          User Request
                │
         IntentRouter
                │
      ┌─────────┼──────────┐
      ▼         ▼          ▼
   Feature   Refactor   Bugfix
      │         │          │
      ▼         ▼          ▼
   PlanningAgent (compartido)
      │         │          │
      ▼         ▼          ▼
   TaskGraph (compartido)
      │         │          │
      ▼         ▼          ▼
   Coding    Refactor   Coding
   Agent     Agent      Agent
      │         │          │
      ▼         ▼          ▼
   ReviewAgent (compartido)
      │         │          │
      └─────────┼──────────┘
                ▼
         TestAgent (compartido)
                │
          [pass/fail]
                │
          GitCommit
```

### 11.4 Integracion con EventBus

El StateGraph **no reemplaza** al EventBus. Son complementarios:

| Componente | Rol | Cuando se usa |
|------------|-----|---------------|
| **EventBus** | Coordinacion reactiva y asincrona | Agentes que operan en background, eventos de larga duracion, SSE |
| **StateGraph** | Orquestacion sincrona y deterministica | Pasos que requieren secuencia estricta, pipelines de un solo request |

```
Request entrante
      │
      ▼
IntentRouter → StateGraph (plan → execute → review → test)
      │                          │
      │                    (cada paso publica eventos al bus)
      │                          │
      ├── EventBus recibe:  task.started, code.generated, review.completed
      ├── Agentes reactivos: ProjectTracker, PDCAEngine, HITLGateway
      └── Dashboard: actualizacion via SSE
```

---

## 12. EventBus Evolution

### 12.1 Topicos actuales (SDLC)

```
project.initialized
adaptation.complete
requirement.created
architecture.proposed
code.committed
code.failed
verification.complete
test.executed
artifact.published
artifact.versioned
baseline.created
human.input.needed
human.decision.submitted
quality.gate.failed
risk.identified
system.pdca.optimization.complete
```

### 12.2 Topicos adicionales (Code Assistant)

```
# Intencion y ruteo
intent.routed                          # Ruta de agentes definida
pipeline.step.{name}.started           # Paso de pipeline iniciado
pipeline.step.{name}.completed         # Paso de pipeline completado

# Repository
repository.scan.started                # Escaneo de repositorio iniciado
repository.scan.completed              # Escaneo completado
repository.file.changed                # Archivo modificado (watch)
repository.file.created                # Archivo creado
repository.file.deleted                # Archivo eliminado
repository.graph.updated               # Repository Graph actualizado

# Agentes
agent.{id}.task.started                # Agente comienza tarea
agent.{id}.task.completed              # Agente completa tarea
agent.{id}.tool.called                 # Agente invoca herramienta
agent.{id}.error                       # Error en agente

# Code generation
code.generated                         # Codigo generado (pre-commit)
code.reviewed                          # Code review completado
code.test.passed                        # Tests pasan
code.test.failed                        # Tests fallan
code.refactored                        # Refactor completado

# Security
security.vulnerability.found           # Vulnerabilidad detectada
security.vulnerability.fixed           # Vulnerabilidad corregida

# Performance
performance.bottleneck.found           # Cuello de botella detectado
performance.optimization.applied       # Optimizacion aplicada

# Tools
tool.executed                          # Herramienta ejecutada
tool.error                             # Error en herramienta

# Memory
memory.episodic.stored                 # Experiencia almacenada
memory.semantic.learned                # Patron aprendido
memory.procedural.learned              # Receta aprendida
```

### 12.3 Flujo completo de eventos (Code Assistant)

```
repository.scan.completed
  └→ intent.routed
       └→ agent.planning.task.started
            └→ agent.planning.task.completed
                 └→ pipeline.step.generate.started
                      ├→ agent.coding.tool.called (WriteFileTool)
                      ├→ agent.coding.tool.called (ASTTool)
                      └→ pipeline.step.generate.completed
                           └→ pipeline.step.review.started
                                ├→ agent.review.tool.called (SearchTool)
                                └→ pipeline.step.review.completed
                                     ├→ review.approved
                                     │    └→ pipeline.step.test.started
                                     │         ├→ agent.test.tool.called (TestRunnerTool)
                                     │         └→ pipeline.step.test.completed
                                     │              ├→ tests.passed
                                     │              │    └→ agent.coding.tool.called (GitTool)
                                     │              │         └→ code.committed
                                     │              └→ tests.failed
                                     │                   └→ code.generated (rework loop)
                                     └→ review.changes_requested
                                          └→ agent.refactor.task.started
                                               └→ ...
```

---

## 13. Migration Roadmap

### 13.1 Vis general

```
F3 (completado)
  │
  ├── SDLC completo ISO 12207
  ├── Agents: 8-10
  ├── Neo4j (opcional)
  │
  ▼
F4 — Foundation (4 sprints)
  │
  ├── RepositoryIntelligenceAgent (construye Repository Graph)
  ├── ToolRegistry + 16 herramientas
  ├── Memory System (3 niveles, basico)
  ├── IntentRouter (punto de entrada unico)
  ├── LangGraph dinamico (AgentGraphBuilder)
  │
  ▼
F5 — Agent Expansion (4 sprints)
  │
  ├── ReviewAgent (SOLID, Clean Code)
  ├── TestAgent (generacion + ejecucion)
  ├── RefactorAgent (AST-based refactoring)
  ├── SecurityAgent (OWASP scanner)
  ├── PerformanceAgent (profiling)
  │
  ▼
F6 — Production (4 sprints)
  │
  ├── Watchman (file watcher en tiempo real)
  ├── LSP integration (goto def, find refs)
  ├── Web UI (React sobre REST+SSE existente)
  ├── Multi-repo support
  ├── VS Code extension
  │
  ▼
F7 — Intelligence (4 sprints)
  │
  ├── Prompt Pipeline optimizado con cache
  ├── Aprendizaje continuo (PDCA MASS sobre agentes)
  ├── Embedding search en el Repository Graph
  ├── Automatic convention detection
  └── Self-healing: agentes se auto-reparan
```

### 13.2 F4: Foundation (detalle)

**Duracion:** 4 sprints (~4 semanas)
**Archivos nuevos:** ~15
**Tests nuevos:** ~80
**Dependencias externas nuevas:** `tree-sitter`, `pygls` (opcional)

| Sprint | Componente | Archivos | Depende de |
|--------|------------|----------|------------|
| **F4-S1** | `RepositoryIntelligenceAgent` + `language_detector` + `treesitter_parser` + `ast_builder` | 4 archivos (~500 LOC) | F3 completo, TreeSitter instalado |
| **F4-S2** | `symbol_graph` + `dependency_graph` + `architecture_detector` + `repository_graph_builder` | 4 archivos (~450 LOC) | F4-S1 |
| **F4-S3** | `ToolRegistry` + 16 tools (1 por dia) | `tool_registry.py` + `tools/` (16 archivos, ~800 LOC) | F4-S2 (tools usan Repository Graph) |
| **F4-S4** | `IntentRouter` + `MemorySystem` + `AgentGraphBuilder` + integracion | 4 archivos (~500 LOC) | F4-S3 |

### 13.3 F5: Agent Expansion (detalle)

**Duracion:** 4 sprints (~4 semanas)
**Archivos nuevos:** ~10
**Tests nuevos:** ~120

| Sprint | Agente | Archivos | Herramientas que usa |
|--------|--------|----------|---------------------|
| **F5-S1** | ReviewAgent | `agents/review_agent.py` (~200 LOC) | SearchTool, ASTTool, DiffTool, LLM |
| **F5-S2** | TestAgent | `agents/test_agent.py` (~200 LOC) | ReadFileTool, WriteFileTool, TestRunnerTool |
| **F5-S3** | RefactorAgent + SecurityAgent | 2 archivos (~350 LOC) | ASTTool, LSPTool, SearchTool, WriteFileTool |
| **F5-S4** | PerformanceAgent + Integracion F5 | 2 archivos (~200 LOC) | ASTTool, DependencyGraphTool, TerminalTool |

### 13.4 Mapeo de archivos actuales a nuevos

| Archivo actual | Accion | Nuevo archivo |
|---------------|--------|---------------|
| `agentic_pipeline/nodes/perception_unit.py` | Refactor → IntentRouter | `compiler-bot/core/intent_router.py` |
| `agentic_pipeline/nodes/preprocessor.py` | Refactor → Normalizer (herramienta) | `compiler-bot/tools/normalizer_tool.py` |
| `agentic_pipeline/nodes/lexer.py` | Remover (reemplazado por TreeSitter) | — |
| `agentic_pipeline/nodes/parser.py` | Remover (reemplazado por TreeSitter) | — |
| `agentic_pipeline/nodes/semantic_analyzer.py` | Refactor → SymbolGraph | `compiler-bot/repository_agent/symbol_graph.py` |
| `agentic_pipeline/nodes/ir_generator.py` | Remover (IR ya no es necesario) | — |
| `agentic_pipeline/nodes/reasoning_engine.py` | Refactor → PlanningAgent | `compiler-bot/agents/planning_agent.py` |
| `agentic_pipeline/nodes/action_executor.py` | Refactor → CodingAgent | `compiler-bot/agents/coding_agent.py` |
| `agentic_pipeline/nodes/validator.py` | Dividir → ReviewAgent + SecurityAgent | `compiler-bot/agents/review_agent.py`, `security_agent.py` |
| `agentic_pipeline/nodes/ui_generator.py` | Migrar → herramienta de CodingAgent | `compiler-bot/tools/ui_generator_tool.py` |
| `agentic_pipeline/agents/` (6 files) | Mantener como legacy, no migrar | (congelado, reference code) |
| `agentic_pipeline/prompt_chain/` | Refactor → PromptPipeline | `compiler-bot/core/prompt_pipeline.py` |
| `agentic_pipeline/observers/` | Mantener + extender | `compiler-bot/observers/` |
| `agentic_pipeline/feedback_loop.py` | Refactor → Memory (episodica) | `compiler-bot/memory/episodic_memory.py` |
| `agentic_pipeline/dashboard/` | Mantener + extender | `compiler-bot/dashboard/` (nuevos endpoints) |
| `agentic_pipeline/generators/` | Mantener (herramientas de CodingAgent) | `compiler-bot/tools/generators/` |
| `pdca_sdlc/core/event_bus.py` | Preservar + extender topicos | (se queda igual, solo nuevos topics) |
| `pdca_sdlc/core/knowledge_graph.py` | Preservar + extender tipos de nodo | (se queda igual, nuevos NodeTypes) |
| `pdca_sdlc/agents/` (8-10 files) | Preservar (sub-agentes SDLC) | (se quedan igual) |
| `pdca_sdlc/dashboard/` | Preservar + extender | (nuevos endpoints para Repository Graph) |

### 13.5 Estrategia de migracion

**Principio: No romper el pipeline existente hasta que el nuevo sistema sea estable.**

```
Fase 1 (F4): Paralelo
  ├── Sistema actual (post-F3) sigue funcionando como siempre
  ├── Nuevo sistema se construye en paralelo en nuevo namespace
  └── Solo se conectan al final via IntentRouter

Fase 2 (F5): Coexistencia
  ├── IntentRouter decide si usar pipeline clasico o nuevo sistema
  ├── Para requests simples: pipeline clasico
  ├── Para requests complejas: nuevo sistema de agentes
  └── Ambos comparten EventBus y KnowledgeGraph

Fase 3 (F6-F7): Transicion
  ├── IntentRouter usa 100% nuevo sistema
  ├── Pipeline clasico queda como fallback
  └── Se congela pipeline clasico como "reference code" (igual que Shell v1.0)
```

---

## 14. Dependency Map

### 14.1 Mapa general

```
                        ┌──────────────────────┐
                        │     CLI (unificado)   │
                        │  compiler-bot/agentic │
                        └──────────┬───────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │       IntentRouter           │
                    │  (clasifica y enruta)        │
                    └──────────────┬──────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │  Pipeline Mode   │  │  Agent Mode      │  │  SDLC Mode       │
   │  (agentic viejo) │  │  (nuevo)         │  │  (pdca_sdlc)     │
   └──────────────────┘  └────────┬─────────┘  └──────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │  PlanningAgent   │  │  Repository      │  │  Memory System   │
   │  (Task Graph)    │◄─┤  Intelligence    │◄─┤  (3 niveles)     │
   └────────┬─────────┘  │  Agent           │  └──────────────────┘
            │            └────────┬─────────┘
            │                     │
            └─────────────────────┼─────────────────────┐
                                  │                     │
              ┌───────────────────┼───────────────────┐ │
              ▼                   ▼                   ▼ ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │  CodingAgent     │  │  ReviewAgent     │  │  TestAgent       │
   │  RefactorAgent   │  │  SecurityAgent   │  │  PerformanceAgent│
   │  DocAgent        │  │                  │  │                  │
   └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
            │                     │                     │
            └─────────────────────┼─────────────────────┘
                                  │
              ┌───────────────────▼───────────────────┐
              │           ToolRegistry                │
              │  (16+ herramientas especializadas)    │
              └───────────────────┬───────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │  EventBus        │  │  KnowledgeGraph  │  │  LLMClient       │
   │  (AsyncEventBus) │  │  (Neo4j/NetworkX)│  │  (multi-provider)│
   └──────────────────┘  └──────────────────┘  └──────────────────┘
```

### 14.2 Arbol de archivos propuesto (post-migracion)

```
compiler-bot/
├── agentic                          # CLI unificado (entrypoint)
│
├── core/                            # Nucleo del sistema
│   ├── __init__.py
│   ├── intent_router.py            # Clasificador de intenciones
│   ├── prompt_pipeline.py          # Pipeline de prompts encadenados
│   ├── prompt_pipeline_steps.py    # Pasos del pipeline (Understand, Plan, etc.)
│   ├── tool_registry.py            # Registro central de herramientas
│   ├── base_tool.py                # Clase base para herramientas
│   └── agent_graph_builder.py      # StateGraph dinamico para agentes
│
├── agents/                          # Agentes especializados (nuevos)
│   ├── __init__.py
│   ├── planning_agent.py           # Task Graph desde goals
│   ├── coding_agent.py             # Generacion de codigo
│   ├── review_agent.py             # Code review (SOLID, Clean Code)
│   ├── test_agent.py               # Generacion y ejecucion de tests
│   ├── refactor_agent.py           # Refactor sin cambiar funcionalidad
│   ├── security_agent.py           # Escaneo OWASP
│   ├── performance_agent.py        # Deteccion de cuellos de botella
│   └── documentation_agent.py      # Documentacion automatica
│
├── repository_agent/               # Repository Intelligence
│   ├── __init__.py
│   ├── repository_intelligence_agent.py
│   ├── language_detector.py
│   ├── treesitter_parser.py
│   ├── ast_builder.py
│   ├── symbol_graph.py
│   ├── dependency_graph.py
│   ├── architecture_detector.py
│   ├── repository_graph_builder.py
│   └── watchman.py
│
├── memory/                          # Sistema de memoria
│   ├── __init__.py
│   ├── base_memory.py
│   ├── episodic_memory.py
│   ├── semantic_memory.py
│   └── procedural_memory.py
│
├── tools/                           # Herramientas explicitas
│   ├── __init__.py
│   ├── read_file_tool.py
│   ├── write_file_tool.py
│   ├── search_tool.py
│   ├── ripgrep_tool.py
│   ├── glob_tool.py
│   ├── git_tool.py
│   ├── docker_tool.py
│   ├── test_runner_tool.py
│   ├── terminal_tool.py
│   ├── browser_tool.py
│   ├── ast_tool.py
│   ├── dependency_graph_tool.py
│   ├── lsp_tool.py
│   ├── embedding_search_tool.py
│   ├── symbol_lookup_tool.py
│   ├── diff_tool.py
│   └── generators/                 # Generadores existentes (mantener)
│       ├── base_generator.py
│       ├── nestjs_generator.py
│       ├── prisma_generator.py
│       ├── react_generator.py
│       ├── docker_generator.py
│       ├── nextjs_generator.py
│       └── tailwind_generator.py
│
├── observers/                       # Observers (mantener + extender)
│   ├── metrics_observer.py
│   ├── audit_observer.py
│   ├── debug_observer.py
│   └── dashboard_observer.py
│
├── dashboard/                       # Dashboard (mantener + extender)
│   ├── app.py
│   ├── service.py
│   └── static/
│
├── pdca_sdlc/                       # Modulo SDLC existente (preservar)
│   ├── main.py
│   ├── core/
│   │   ├── event_bus.py
│   │   ├── knowledge_graph.py
│   │   ├── base_agent.py
│   │   ├── capability_registry.py
│   │   └── llm_client.py
│   ├── agents/                      # 8-10 agentes SDLC (F1-F3)
│   │   ├── adaptation_agent.py
│   │   ├── requirements_analyst.py
│   │   ├── architect_agent.py
│   │   ├── coder_agent.py
│   │   ├── tester_agent.py
│   │   ├── verification_agent.py
│   │   ├── doc_writer_agent.py
│   │   ├── config_mgr_agent.py
│   │   ├── project_tracker.py
│   │   └── hitl_gateway.py
│   ├── core/
│   │   ├── quality_gate.py
│   │   ├── swarm_coordinator.py
│   │   └── pdca_engine.py
│   ├── protocols/
│   │   └── event_schemas.py
│   ├── dashboard/
│   └── tests/
│
├── agentic_pipeline/                # Pipeline clasico (congelar)
│   ├── (todos los archivos existentes)
│   └── README.md: "LEGACY — usar solo como fallback"
│
└── tests/                           # Tests del nuevo sistema
    ├── test_intent_router.py
    ├── test_tool_registry.py
    ├── test_repository_agent/
    ├── test_agents/
    ├── test_memory/
    ├── test_tools/
    └── test_integration/
```

---

## 15. Risks and Mitigation

### 15.1 Riesgos tecnicos

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| **TreeSitter no soporta todos los lenguajes del proyecto** | Media | Alto | Usar TreeSitter como parser primario, fallback a regex-based parsing para lenguajes no soportados |
| **Repository Graph demasiado grande (>1M nodos)** | Media | Medio | Indexacion perezosa (lazy), solo cargar subgrafos relevantes al contexto actual |
| **LSP integration compleja** | Alta | Medio | Empezar con funcionalidad basica (goto def, find refs), diferir features avanzados |
| **Migracion de pipeline legacy a nuevo sistema rompe compatibilidad** | Media | Alto | Coexistencia por 2 fases completas antes de deprecar el pipeline viejo |
| **Performance del Watchman en repos grandes** | Alta | Bajo | Usar `watchdog` + debouncing, solo re-indexar archivos modificados |
| **Complejidad de la memoria de 3 niveles** | Media | Medio | Implementar episodica primero (sobre EventBus existente), luego semantica, luego procedural. Cada nivel es independiente. |

### 15.2 Riesgos arquitectonicos

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| **Demasiados agentes -> complejidad de coordinacion** | Alta | Alto | Cada agente es independiente y testeable. La coordinacion via EventBus es desacoplada por diseno. |
| **Duplicacion de funcionalidad entre agente SDLC y nuevo agente** | Alta | Medio | Los agentes SDLC se enfocan en el lifecycle ISO 12207. Los nuevos agentes se enfocan en tareas de ingenieria de codigo. Son complementarios, no redundantes. |
| **Perdida de la simplicidad del pipeline original** | Alta | Medio | El pipeline original se congela como "fast path". Solo las tareas complejas usan el nuevo sistema de agentes. |
| **EventBus se vuelve cuello de botella** | Baja | Alto | El EventBus actual ya maneja 10K eventos en FIFO circular. Si se necesita mas throughput, migrar a NATS (ya evaluado en F2). |

### 15.3 Riesgos de migracion

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| **El equipo no conoce TreeSitter** | Alta | Bajo | TreeSitter tiene bindings Python maduros y documentacion extensa. Curva de aprendizaje: 2-3 dias. |
| **El pipeline legacy queda sin mantenimiento** | Media | Bajo | No necesita mantenimiento. Esta congelado como reference code (igual que Shell v1.0). |
| **Pruebas de regresion insuficientes** | Media | Alto | La suite de tests actual (1,072 tests) debe seguir pasando. Agregar tests de integracion que validen que ambos sistemas producen el mismo resultado para inputs simples. |

---

## 16. Conclusion

### 16.1 Resumen de la propuesta

| Aspecto | Propuesta |
|---------|-----------|
| **Que** | Migrar de arquitectura pipeline-centric a agent-centric |
| **Por que** | El pipeline es optimo para compilar NL→Codigo, pero un asistente de codigo necesita un modelo vivo del repositorio, agentes especializados, y herramientas explicitas |
| **Como** | 4 fases (F4-F7), ~16 sprints, coexistencia con el sistema actual durante la migracion |
| **Pre-requisito** | F3 completado (SDLC ISO 12207 completo con 8-10 agentes, Quality Gates, Swarm, PDCA, HITL) |
| **Que se preserva** | EventBus, KnowledgeGraph, QualityGates, generators, dashboards, agentes SDLC |
| **Que se refactoriza** | Pipeline stages → agentes + herramientas, prompt_chain → PromptPipeline |
| **Que se elimina** | Lexer/parser DFA/Lark → TreeSitter, IR canonico (ya no necesario), pipeline fijo → grafo dinamico |
| **Que se agrega** | RepositoryIntelligenceAgent, 9 agentes especializados, 16 herramientas, memoria de 3 niveles, IntentRouter, AgentGraphBuilder |

### 16.2 Tabla de esfuerzo

| Fase | Sprints | Archivos nuevos | Tests nuevos | LOC estimado |
|------|---------|-----------------|-------------|--------------|
| F4 — Foundation | 4 | 15 | 80 | ~2,250 |
| F5 — Agent Expansion | 4 | 10 | 120 | ~950 |
| F6 — Production | 4 | 8 | 100 | ~1,500 |
| F7 — Intelligence | 4 | 6 | 80 | ~1,200 |
| **Total** | **16** | **~39** | **~380** | **~5,900** |

### 16.3 Impacto en el sistema actual

| Sistema | Impacto |
|---------|---------|
| `agentic_pipeline/` (2.8.4) | Se congela como reference code (igual que Shell v1.0). Usado como fallback. |
| `pdca_sdlc/` (0.1.0) | Se preserva y extiende. Los agentes SDLC coexisten con los nuevos agentes. |
| `agentic` CLI | Se unifica: `--mode pipeline|agent|sdlc` para elegir modo de operacion. |
| Dashboard | Se extiende con endpoints para Repository Graph y Memory. |
| Tests existentes (1,072) | Deben seguir pasando. No se eliminan tests legacy. |
| `docs/` | Se actualiza con la nueva arquitectura. Documentos legacy se preservan. |
| `CHANGELOG.md` | Cada fase agrega su entrada. |

### 16.4 Proximo paso

Si esta propuesta es aceptada, el siguiente documento seria el **plan de ejecucion detallado para F4** (`docs/180_PLAN_DEV_CODE_ASSISTANT_F4_EXECUTION_1_0_DRAFT.md`), con:

- Desglose por sprint (F4-S1 a F4-S4)
- Especificacion tecnica de cada componente
- Dependencias entre tareas
- Criterios de exito por sprint
- Estimacion de esfuerzo por archivo

---

*Documento de propuesta basado en el analisis tecnico completo (`docs/178_ANALYSIS_DEV_COMPREHENSIVE_TECHNICAL_REPORT_1_0_DRAFT.md`) y los planes de ejecucion F2 (`docs/159_PLAN_DEV_PDCA_SDLC_F2_EXECUTION_1_0_DRAFT.md`) y F3 (`docs/160_PLAN_DEV_PDCA_SDLC_F3_EXECUTION_1_0_DRAFT.md`).*
