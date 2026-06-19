---
id: "A01"
area: "DEV"
type: "ARCH"
module: "RECPL_V2"
version: "1.0"
status: "DRAFT"
tags: ["architecture", "review", "as-is", "to-be", "risk-assessment"]
summary: "Reporte de arquitectura completo del sistema RECPL Compiler Bot v2.0+ — analisis AS-IS, problemas detectados, deuda tecnica, propuesta TO-BE y recomendaciones priorizadas"
changelog:
  - version: "1.0"
    date: "2026-06-18"
    author: "Arquitecto Senior"
    description: "Version inicial — analisis basado en 7 diagramas UML + revision de codigo fuente (~170 archivos, ~20K LOC)"
---

# Reporte de Arquitectura — RECPL Compiler Bot v2.0+

> **Audiencia:** Stakeholders técnicos y no técnicos  
> **Base:** 7 diagramas UML + código fuente (98 módulos Python, 72 tests, ~20,861 LOC)  
> **Propósito:** Evaluación crítica de la arquitectura actual, identificación de deuda técnica, riesgos, y plan de mejora priorizado

---

## Tabla de Contenidos

1. [Resumen del Sistema](#1-resumen-del-sistema)
2. [Arquitectura Actual (AS-IS)](#2-arquitectura-actual-as-is)
3. [Problemas Detectados](#3-problemas-detectados)
4. [Deuda Técnica](#4-deuda-técnica)
5. [Riesgos y Cuellos de Botella](#5-riesgos-y-cuellos-de-botella)
6. [Mejores Prácticas Incumplidas](#6-mejores-prácticas-incumplidas)
7. [Arquitectura Propuesta (TO-BE)](#7-arquitectura-propuesta-to-be)
8. [Diagramas de Arquitectura Descritos](#8-diagramas-de-arquitectura-descritos)
9. [Tecnologías y Justificación](#9-tecnologías-y-justificación)
10. [Seguridad](#10-seguridad)
11. [Escalabilidad y Rendimiento](#11-escalabilidad-y-rendimiento)
12. [Recomendaciones Priorizadas](#12-recomendaciones-priorizadas)
13. [Conclusión](#13-conclusión)

---

## 1. Resumen del Sistema

### 1.1 Propósito

RECPL Compiler Bot v2.0+ es un **compilador de lenguaje natural a código**. Toma instrucciones en español (ej. *"crea un módulo de pagos en NestJS"*) y genera scaffolding completo de módulos NestJS, entidades Prisma, componentes React, y configuraciones Docker/Next.js/Tailwind.

### 1.2 Principio de Funcionamiento

El sistema implementa un **pipeline compilador de 10 etapas** orquestado por un `StateGraph` (LangGraph), con un subsistema alterno de **Prompt Chaining** (Chain of Responsibility) para rutas basadas exclusivamente en LLM:

```
INPUT → [Perception → Preprocessor → Lexer → Parser → Semantic → IR → Planner → Synthesis → UI → Validator] → OUTPUT
```

Cada etapa es un `PipelineStage` con ciclo de vida: `receive_mission → analyze → reflect_and_plan → act → learn_and_improve`, siguiendo el patrón **Template Method**.

### 1.3 Métricas del Sistema

| Métrica | Valor |
|---------|-------|
| Módulos Python | 98 fuente + 72 test |
| Líneas de código totales | ~20,861 |
| Etapas del pipeline | 10 (StateGraph) |
| Handlers de Prompt Chain | 6 (Chain of Responsibility) |
| Patrones GoF implementados | 7 (Template, CoR, Command, Observer, Strategy, Factory, Builder, Composite, Memento) |
| Tests | 72 archivos, pytest con clases |
| Gramáticas Lark | 4 (project, data, ui, infra) |
| Generadores de código | 7 (React, NextJS, NestJS, Prisma, Docker, Tailwind, UI Builder) |
| Agentes multi-agente | 5 (Perception, Reasoning, Execution, Validator, Supervisor) |

---

## 2. Arquitectura Actual (AS-IS)

### 2.1 Vista de Alto Nivel

```
┌────────────────────────────────────────────────────────────────────────┐
│                           CLI Layer (agentic)                          │
│                  debugger.py  |  --chain  |  --monitor                  │
└───────────────────────┬────────────────────────────────────────────────┘
                        │
┌───────────────────────▼────────────────────────────────────────────────┐
│                      Orchestration Layer                               │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  AgentOrchestrator (StateGraph)     ┌─────────────────────────┐  │  │
│  │  NODE_MAP: 10 stages → sequential   │ ChainOrchestrator (CoR) │  │  │
│  │  conditional edges via ErrorGuard   │ 6 PromptHandler chain   │  │  │
│  └────────────┬─────────────────────────┘  retry loop gen↔verify  │  │  │
│               │                          └─────────────────────────┘  │  │
│               │                          ┌─────────────────────────┐  │  │
│               │                          │ PipelineMacroCommand    │  │  │
│               │                          │ (Command Pattern)       │  │  │
│               │                          └─────────────────────────┘  │  │
│               └─── 3 formas de ejecutar ─── el mismo pipeline ────────┘  │
└────────────────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────▼────────────────────────────────────────────────┐
│                  10 Pipeline Stages (nodes/)                           │
│                                                                        │
│  INTENT ─► PREPROCESSOR ─► LEXER ─► PARSER ─► SEMANTIC ─► IR ─►      │
│  PLANNER ─► SYNTHESIS ─► UI ─► VALIDATOR                              │
│                                                                        │
│  Cada stage: StageSubject.notify(event)  ──►  Observers                │
└────────────────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────▼────────────────────────────────────────────────┐
│  Generators        │  NLP Pipeline     │  Multi-Agent System           │
│  (7 generadores)    │  (4 clasificadores)│  (5 agentes + EventBus)      │
│  Factory + Strategy │  PerceptionUnit    │  Supervisor orquesta         │
└─────────────────────┴───────────────────┴──────────────────────────────┘
```

### 2.2 Patrones GoF Implementados

| Patrón | Componentes | Ubicación |
|--------|-------------|-----------|
| **Template Method** | `PipelineStage.execute()` define esqueleto; subclasses implementan `receive_mission()`, `act()` | `base_stage.py` (abstract), 10 subclasses en `nodes/` |
| **Chain of Responsibility** | `PromptHandler` → `PreprocessHandler` → `IntentHandler` → `PlanHandler` → `GenerateHandler` → `VerifyHandler` → `FormatHandler` | `prompt_chain/handler_base.py`, `prompts/*.py` |
| **Command** | `Command.execute()`, `MacroCommand`, `CommandHistory`, 7 `*Command` concretos | `prompt_chain/command_base.py`, `prompt_chain/commands.py` |
| **Observer** | `StageSubject`, `StageObserver`, `StageEvent`, 4 observers concretos | `prompt_chain/observer_base.py`, `feedback_loop.py` |
| **Strategy + Factory** | `BaseGenerator.generate()`, `GeneratorFactory.get_generator()`, 7 generadores concretos | `generators/base_generator.py` |
| **Composite** | `IRNode` raíz con `children: list[IRNode]`; 7 subclases (IRProject, IRPage, IRComponent, etc.) | `nodes/ir_nodes.py` |
| **Builder** | `UIComponentBuilder.build_structure()` → `apply_styles()` → `add_behavior()` → `add_accessibility()` → `add_animations()` → `build()` | `generators/ui_component_builder.py` |
| **Memento** | `SymbolTable.save_memento()` / `restore()` | `nodes/symbol_table.py` |

### 2.3 Vista por Subsistemas

#### 2.3.1 Pipeline Principal (StateGraph)

El `AgentOrchestrator` construye un `StateGraph` de LangGraph con 10 nodos conectados secuencialmente vía `add_conditional_edges(ErrorGuard.should_continue)`. Cada nodo crea una nueva instancia de su `PipelineStage` por invocación.

**Flujo de datos:** `StageContext.input_data` → cada stage produce `StageOutput.output_data` → pasa al siguiente stage como `input_data`.

**Problema:** No hay inmutabilidad del contexto — `StageContext` se muta en cada nodo. Esto rompe trazabilidad y dificulta debugging.

#### 2.3.2 Prompt Chain (Chain of Responsibility)

El `ChainOrchestrator` construye una cadena de 6 `PromptHandler` que se pasan el `PromptRequest` y `ChainContext` secuencialmente. Soporta reintentos en el loop `Generate → Verify` hasta `max_retries`.

**Flujo:** `Preprocess → Intent → Plan → Generate → Verify → (retry loop) → Format`

**Problema:** La cadena es fija — no hay forma de reordenar handlers dinámicamente según el intent.

#### 2.3.3 Sistema Multi-Agente (agents/)

5 agentes (Perception, Reasoning, Execution, Validator, Supervisor) orquestados vía `SharedContext` + `EventBus`.

**Problema crítico:** Este sistema multi-agente está **completamente desconectado** del pipeline principal. No hay código que ejecute los agentes a través de los pipeline stages. Conviven dos arquitecturas diferentes sin integración.

#### 2.3.4 Observers

`MetricsObserver`, `DebugObserver`, `PromptOptimizerObserver`, `DashboardObserver` se registran en un `StageSubject` compartido (clase `PipelineStage.subject`). `DashboardObserver` prepara un buffer deque para futura salida WebSocket.

---

## 3. Problemas Detectados

### 3.1 Arquitectónicos

| ID | Problema | Severidad | Componente |
|----|----------|-----------|------------|
| P1 | **Dos sistemas de agentes desconectados**: pipeline stages vs. multi-agent system sin integración | ALTA | Arquitectura global |
| P2 | **RequirementDecomposer es dead code**: existe como archivo y enum pero no está en `NODE_MAP` | MEDIA | `nodes/requirement_decomposer.py` |
| P3 | **ParserGLR no es GLR**: el nombre dice GLR pero implementa Earley (`parser="earley"` en Lark) | BAJA | `nodes/parser.py` |
| P4 | **StateSubject compartido mutable**: `PipelineStage.subject` es class variable — no thread-safe | MEDIA | `base_stage.py` |
| P5 | **Dos event buses paralelos**: `StageSubject` en `prompt_chain/` y `EventBus` en `agents/` — misma función, distinta implementación | MEDIA | Cruzado |
| P6 | **PipelineMacroCommand duplica lógica del StateGraph**: ejecuta los mismos stages manualmente sin usar el grafo | BAJA | `orchestrator.py` |

### 3.2 Calidad de Código

| ID | Problema | Severidad |
|----|----------|-----------|
| Q1 | **Sin configuración de ruff** en `pyproject.toml` pese a que AGENTS.md lo exige (line-length 100, 4 espacios) | ALTA |
| Q2 | **Sin `[tool.pytest.ini_options]`** en `pyproject.toml` | MEDIA |
| Q3 | **5 de 9 paquetes con `__init__.py` vacío**: `nodes/`, `nlp/`, `providers/`, `grammars/`, `tests/` | MEDIA |
| Q4 | **`feedback_loop.py` viola SRP**: contiene 7 clases (FeedbackLoop, GlobalFeedbackLoop, 4 observers, PromptOptimizer) | MEDIA |
| Q5 | **Type hints incompletos**: `feedback_loop.py` usa `Any` excesivamente en interfaces que deberían ser tipadas | BAJA |
| Q6 | **Rutas de importación inconsistentes**: algunos imports usan `from .` relativo, otros `<pkg>.module` absoluto | BAJA |

### 3.3 Testing

| ID | Problema | Severidad |
|----|----------|-----------|
| T1 | **Sin integración entre tests de pipeline y tests de agents** — se prueban como sistemas separados | MEDIA |
| T2 | **Sin fixtures compartidas** más allá de `mock_context` — cada test setup duplica lógica | MEDIA |
| T3 | **Sin tests de performance/benchmark** pese a tener `pytest-benchmark` como dependencia | BAJA |
| T4 | **Sin tests de integración con LLM real** (solo mocks) — los fallbacks no se prueban contra API real | BAJA |

---

## 4. Deuda Técnica

### 4.1 Deuda Acumulada

| Item | Impacto | Esfuerzo Est. | Prioridad |
|------|---------|---------------|-----------|
| `requirement_decomposer.py` — dead code (2.7% del código muerto) | Confusión, mantenimiento extra | 1h (eliminar) | Alta |
| Dos event buses (`StageSubject` + `EventBus`) | Duplicación, confusión de integración | 8h (unificar) | Alta |
| Sin cacheo de LLM efectivo — `LLMCache` existe pero no está cableado | Costo LLM ~30% más alto del necesario | 4h (wiring) | Alta |
| `ParserGLR` mal nombrado — `parser.py` usa Lark Earley no GLR | Desinformación arquitectónica | 0.5h (rename) | Baja |
| Sin configuración ruff/pytest en `pyproject.toml` | CI/CD no puede validar estilo automáticamente | 1h | Alta |
| `__init__.py` vacíos en 5 paquetes | IDE autocompletado pobre, duck-typing en imports | 2h | Media |
| `PipelineMacroCommand` duplica a `AgentOrchestrator` | 146 líneas de código redundante | 3h (refactor) | Media |

### 4.2 Deuda Estratégica

| Deuda Estratégica | Razón | Costo Futuro |
|-------------------|-------|-------------|
| No unificar pipeline y multi-agentes | Se priorizó tener ambos funcionando | Alto — confusión arquitectónica persistente |
| No usar base de datos relacional para métricas | SQLite + JSON file híbrido para MVP | Medio — migración a PostgreSQL necesaria en producción |
| Sin inmutabilidad en StageContext | Simplicidad inicial | Medio — bugs difíciles de rastrear |

---

## 5. Riesgos y Cuellos de Botella

### 5.1 Riesgos Técnicos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|-----------|
| **LLM API rate limiting** en cadena: 6-10 llamadas por solicitud | Alta | Alto | Implementar circuit breaker + cola de reintentos con backoff exponencial |
| **StateGraph en memoria**: pérdida total en crash del proceso | Media | Alto | Persistencia de checkpoint en SQLite + snapshots periódicos |
| **Sin aislamiento de stages**: una excepción en un stage propaga al orquestador vía `re-raise` | Alta | Medio | ErrorGuard captura pero no aísla — implementar bulkhead pattern |
| **StageSubject mutable compartido**: race condition en concurrencia | Baja | Medio | `threading.Lock` o `copy-on-write` para observer list |
| **Sin autenticación**: la CLI expone API keys en env vars | Alta | Alto | Usar secrets manager + rotación automática |
| **Dependencia crítica de LangGraph**: cambios breaking en upstream afectan TODO el pipeline | Media | Alto | Abstraer la interfaz StateGraph detrás de una interfaz propia |

### 5.2 Cuellos de Botella de Rendimiento

| Punto | Causa | Impacto |
|-------|-------|---------|
| Llamadas LLM secuenciales (6-10 por request) | Sin paralelización de handlers independientes | Latencia: 15-60s por solicitud |
| Parsing Lark 4 gramáticas en serie | Cada gramática se procesa secuencialmente | +2-5s por solicitud |
| Observers bloqueantes | `StageSubject.notify()` itera observers en el mismo thread | +1-3% overhead por stage |
| Sin cacheo de LRU para AST/IR repetidos | `ASTCache` existe pero no se usa consistentemente | Cómputo redundante hasta 40% |

---

## 6. Mejores Prácticas Incumplidas

### 6.1 SOLID

| Principio | Violación | Detalle |
|-----------|-----------|---------|
| **S** — Single Responsibility | `feedback_loop.py` contiene 7 clases no relacionadas | Metrics, Observers, y Optimizer en un solo archivo de 302 líneas |
| **O** — Open/Closed | `NODE_MAP` es un dict fijo — agregar un nuevo stage requiere modificar `orchestrator.py` | Debería ser extensible vía registro declarativo |
| **I** — Interface Segregation | `PipelineStage` tiene 5 métodos abstractos pero cada subclase solo implementa 2-3 | Separar en interfaces menores (Analyzable, Plannable, Executable) |

### 6.2 Arquitecurales

| Práctica | Estado Actual | Recomendación |
|----------|--------------|---------------|
| **Inmutabilidad de datos** | `StageContext` se muta en cada nodo | Usar `dataclass(frozen=True)` o eventos inmutables |
| **Separación CQRS** | Lectura/escritura mezcladas en `SharedContext` | Separar queries de comandos |
| **Circuit Breaker** | No existe | Implementar para LLM calls con umbrales configurables |
| **Health checks** | No existen | Endpoint `/health` para monitoreo |
| **Observabilidad estructurada** | Solo `logging` estándar | OpenTelemetry traces + metrics + logs correlacionados |
| **Graceful degradation** | Sin fallbacks para LLM outage | Modo offline con reglas heurísticas |

### 6.3 Seguridad

| Práctica | Estado |
|----------|--------|
| API keys en variables de entorno | ✅ Documentado |
| Validación de entrada en todos los stages | ✅ `STAGE_CONTRACTS` Pydantic |
| Sin hardcodeo de secrets | ✅ `pydantic-settings` |
| Sin sanitización de salida generada | ❌ El código generado podría contener vulnerabilidades |
| Sin autenticación/autorización | ❌ No hay control de acceso |
| Sin rate limiting | ❌ No hay límite de requests |
| Sin auditoría de acciones | ❌ No hay log de quién ejecutó qué |

---

## 7. Arquitectura Propuesta (TO-BE)

### 7.1 Principios de Diseño

1. **Un solo pipeline**, dos modos de ejecución (stage-graph y prompt-chain son estrategias intercambiables)
2. **Inmutabilidad de datos** en todo el flujo — cada stage recibe un snapshot, no una referencia mutable
3. **Extensibilidad por registro** — nuevos stages se agregan por configuración, no modificando el orquestador
4. **Observabilidad first-class** — tracing distribuido, métricas exportables, logging estructurado
5. **Graceful degradation** — el sistema funciona (con capacidad reducida) sin LLM

### 7.2 Arquitectura TO-BE

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        API Gateway (FastAPI)                             │
│  /v1/compile  POST   │   /v1/agents/:id/task  POST   │   /health GET    │
│  Rate Limiter │ Auth │   Audit Log │ Request Validator                   │
└─────────────────────┬───────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────────────┐
│                     Unified Orchestrator                                 │
│                                                                          │
│  ┌──────────────────────────────┐   ┌────────────────────────────────┐  │
│  │  RoutingStrategy:            │   │  PipelineStageRegistry:        │  │
│  │  - StateGraphStrategy        │──►│  YAML-configured stage list    │  │
│  │  - ChainStrategy             │   │  + dependency injection        │  │
│  │  - HybridStrategy (auto)     │   │  + plugin loader               │  │
│  └──────────────────────────────┘   └────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  EventBus Unificado (reemplaza StageSubject + EventBus)         │   │
│  │  - topics: stage.completed, stage.failed, llm.called, etc.      │   │
│  │  - subscribers: MetricsObserver, AuditObserver, Dashboard       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────────────┐
│  10 Pipeline Stages (refactorizados)                                     │
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Intent   │  │ Preproc  │  │ Lexer    │  │ Parser   │  │ Semantic │  │
│  │ (LLM/NLP)│  │ (filters)│  │ (DFA)    │  │ (Lark)   │  │ (types)  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ IR Gen   │  │ Planner  │  │ Synthesis│  │ UI Gen   │  │ Validator│  │
│  │(composite)│  │(task gr.)│  │(generators)│  │(builder) │  │(CoR)    │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                                          │
│  Cada stage implementa: StageInterface o StageWithLLM (separadas)       │
└─────────────────────────────────────────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────────────────┐
│  Shared Infrastructure Layer                                             │
│                                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────┐     │
│  │ LLM Client │  │ Cache      │  │ Circuit    │  │ Observability│     │
│  │ (pooled)   │  │ (redis/lru)│  │ Breaker    │  │ (OTel)       │     │
│  └────────────┘  └────────────┘  └────────────┘  └──────────────┘     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────┐     │
│  │ Metrics    │  │ State/      │  │ Auth       │  │ Audit        │     │
│  │ (prometheus)│  │Snapshot DB │  │ (JWT/APIKey)│  │(immutable log)│     │
│  └────────────┘  └────────────┘  └────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Cambios Clave

| Componente Actual | Componente TO-BE | Justificación |
|------------------|-----------------|---------------|
| `StageSubject` + `EventBus` | `EventBus` unificado | Una interfaz pub/sub en lugar de dos |
| `NODE_MAP` hardcodeado en `orchestrator.py` | `PipelineStageRegistry` configurable vía YAML | Open/Closed: nuevos stages sin modificar el orquestador |
| `PipelineStage` monolítico (5 métodos) | `StageInterface` + `StageWithLLM` segregadas | ISP: stages sin LLM no necesitan métodos LLM |
| Herencia rígida de `PipelineStage` | Composición: `StageExecutor` + `LifecycleHooks` | Mayor flexibilidad, testabilidad |
| 3 formas de ejecutar pipeline | 1 `RoutingStrategy` con 3 implementaciones | Menos duplicación, lógica de ruteo centralizada |
| Sin cacheo consistente | `CacheLayer` (Redis + LRU local) con decoradores | ~30% reducción de llamadas LLM |
| `StateGraph` directamente acoplado | Abstracción `GraphBackend` (implementación LangGraph internamente) | Aislamiento de upstream breaking changes |

### 7.4 Diagrama de Secuencia TO-BE

```
Usuario     API Gateway    UnifiedOrch    Router      Stage[N]     EventBus    LLMClient   Cache
   │             │             │            │            │            │           │          │
   │──POST──────►│             │            │            │            │           │          │
   │  /v1/compile│             │            │            │            │           │          │
   │◄──401 (sin auth)───┤      │            │            │            │           │          │
   │──POST+JWT───►│             │            │            │            │           │          │
   │             │──run()─────►│            │            │            │           │          │
   │             │             │──route()──►│            │            │           │          │
   │             │             │◄─strategy──┤            │            │           │          │
   │             │             │            │            │            │           │          │
   │             │             │═══ loop [stages] ═══════╪════════════╪═══════════╪══════════╡
   │             │             │──execute──►│──┬────────►│            │           │          │
   │             │             │            │  │         │            │           │          │
   │             │             │            │  │ if LLM: │──generate──►│──check───►│          │
   │             │             │            │  │         │            │◄──hit/miss─┤          │
   │             │             │            │  │         │───(LLM call)───────────►│          │
   │             │             │            │  │         │            │           │          │
   │             │             │            │◄─┘         │            │           │          │
   │             │             │◄─StageOutput─┤          │            │           │          │
   │             │             │            │  │         │            │           │          │
   │             │             │──publish──►│  │         │            │           │          │
   │             │             │            │  │         │──on_event──►│           │          │
   │             │             │            │  │         │            │           │          │
   │             │◄───result──────┤         │            │            │           │          │
   │◄──200 JSON─────┤             │            │            │            │           │          │
   │             │             │            │            │            │           │          │
```

---

## 8. Diagramas de Arquitectura Descritos

### 8.1 Diagrama de Clases (001)

El sistema tiene ~110 clases organizadas en 10 jerarquías:

| Jerarquía | Clase Base | Subclases | Patrón |
|-----------|-----------|-----------|--------|
| Pipeline Stages | `PipelineStage` (ABC) | 10 stages (Intent → Validator) | Template Method |
| Agentes | `Agent` (ABC) | 5 agentes (Perception, Reasoning, Execution, Validator, Supervisor) | — |
| Prompt Handlers | `PromptHandler` (ABC) | 6 handlers (Preprocess → Format) | Chain of Responsibility |
| Commands | `Command` (ABC) | 6 prompt commands + ToolCommand + PipelineMacroCommand | Command |
| Observers | `StageObserver` (interface) | 5 observers (Metrics, Debug, PromptOptimizer, Dashboard, Plan) | Observer |
| Generators | `BaseGenerator` (ABC) | 6 generators (React, NextJS, NestJS, Prisma, Docker, Tailwind) | Strategy + Factory |
| IR Nodes | `IRNode` (ABC) | 7 nodos (Project, Page, Component, Entity, API, Config, Infra) | Composite |
| AST Nodes | `ASTNode` (ABC) | 5 nodos (Project, Page, Component, Entity, Infra) | — |
| NLP | 4 clasificadores independientes | IntentClassifier, NERExtractor, SlotFiller, AmbiguityDetector | Pipeline |
| Soporte | 12 clases auxiliares | SymbolTable, SubDFA, Trie, LLMBackend, ToolRegistry, ErrorGuard, etc. | Varios |

### 8.2 Diagrama de Casos de Uso (002)

**Actores:**
- **Usuario** — interpreta lenguaje natural, ejecuta pipeline
- **Desarrollador** — genera código, scaffolding, comandos
- **Admin Sistema** — monitorea métricas, observa eventos, supervisa agentes
- **LLM Service** (externo) — backends de IA
- **File System** (externo) — persistencia

**Flujo principal:** Usuario → Interpretar Lenguaje Natural → Normalizar → Clasificar Intención → Descomponer → Generar Código → Validar → Formatear.

**Flujo alternativo:** Verificación fallida → re-intento (<<extend>>) hasta N veces.

### 8.3 Diagrama de Componentes (006)

| Subsistema | Módulo | Interfaces | Dependencias |
|-----------|--------|-----------|--------------|
| CLI | `agentic`, `debugger.py` | Llamada directa | Orchestrators, File System, LLM API |
| Orchestration | `orchestrator.py`, `prompt_chain/orchestrator.py` | StateGraph, CoR chain | 10 stages, ErrorGuard |
| Pipeline Stages | `nodes/` | `PipelineStage` | Generators, NLP, IR System |
| Prompt Handlers | `prompt_chain/prompts/` | `PromptHandler` | LLMBackend, ChainContext |
| Observer | `observer_base.py`, `feedback_loop.py` | `StageObserver` | GlobalFeedbackLoop |
| Generators | `generators/` | `BaseGenerator` | File System (escritura) |
| NLP | `nlp/` | 4 clasificadores | PerceptionUnit |
| IR System | `nodes/ir_*.py` | Composite tree | IRBuilder, DependencyGraph |
| Multi-Agent | `agents/` | EventBus, SharedContext | ToolRegistry, LLM |

### 8.4 Diagrama de Despliegue (007)

**Nodo 1 — Máquina del Usuario (CPython 3.11)**
- Artefactos: AgentOrchestrator, ChainOrchestrator, 10 stages, 6 handlers, 5 agents, 7 generators, 4 observers
- Almacenamiento local: SQLite (metrics), JSON (memory), templates/, output/modules/

**Nodo 2 — LLM API Service (Cloud)**
- Backends: OpenAI GPT-4o, GPT-4o-mini, Custom LLM
- Protocolo: HTTPS/REST

**Nodo 3 — File System (Local/Network)**
- Directorios: templates/, output/modules/

**Comunicación:**
- CLI → LLM API: HTTPS (API key vía env)
- Stages → Observers: en memoria (pub/sub)
- Stages → File System: escritura de archivos

---

## 9. Tecnologías y Justificación

### 9.1 Stack Actual

| Tecnología | Versión | Propósito | ¿Reemplazar? |
|-----------|---------|-----------|--------------|
| Python | ≥3.11 | Lenguaje principal | ✅ Mantener |
| LangGraph | ≥0.2.0 | StateGraph pipeline | ⚠️ Abstraer interfaz |
| LangChain | ≥0.3.0 | LLM orchestration | ⚠️ Evaluar dependencia directa |
| Pydantic v2 | ≥2.0 | Validación de datos, contratos | ✅ Mantener |
| Lark | ≥1.3.0 | Parsing GLR/Earley | ✅ Mantener (corregir nombre) |
| spaCy | ≥3.7 | NLP (texto) | ✅ Mantener |
| SQLite | stdlib | Métricas persistente | ⚠️ PostgreSQL para prod |
| OpenAI | — | LLM backend | ✅ Mantener + multi-model |

### 9.2 Tecnologías Recomendadas Adicionales

| Tecnología | Propósito | Prioridad | Justificación |
|-----------|-----------|-----------|---------------|
| **Redis** | Cache LLM, rate limiting, cola de eventos | Alta | ~30% reducción de latencia LLM |
| **OpenTelemetry** | Trazas distribuidas, métricas exportables | Alta | Observabilidad cross-stage |
| **Prometheus + Grafana** | Dashboards de rendimiento | Alta | Métricas exportables no bloqueantes |
| **FastAPI** | API HTTP sobre la CLI | Alta | Acceso remoto, integración CI/CD |
| **PostgreSQL** | Estado persistente, historial, auditoría | Media | Migración desde SQLite/JSON |
| **Pydantic Settings** (ya incluido) | Config centralizada | ✅ Ya existe |
| **pre-commit** (ya en dev) | Hooks de calidad | ✅ Configurar hooks |
| **ruff** (ya en dev) | Linter + formatter | ✅ Configurar `pyproject.toml` |
| **pytest-asyncio** (ya en dev) | Tests async | ✅ Ya existe |

### 9.3 Justificación de Decisiones Clave

| Decisión | Alternativa Rechazada | Motivo |
|----------|----------------------|--------|
| Mantener LangGraph pero abstraer | Reemplazar con StateMachine custom | LangGraph es maduro y probado; abstraer interfaz evita lock-in sin reescribir |
| EventBus unificado | Mantener StageSubject + EventBus | Un solo patrón pub/subs es más simple de mantener y documentar |
| FastAPI como API | gRPC | Python+gRPC agrega complejidad innecesaria para un sistema CLIs primero |
| Composiciones en stages | Herencia profunda | Composición permite testing más aislado y evolución independiente |

---

## 10. Seguridad

### 10.1 Estado Actual

| Aspecto | Estado | Riesgo |
|---------|--------|--------|
| API Keys (env vars) | ✅ Documentado en pydantic-settings | Bajo |
| Validación de entrada | ✅ Pydantic contracts por stage | Bajo |
| Sin hardcodeo de secrets | ✅ `AGENTIC_` prefijo | Bajo |
| Sin sanitización de salida | ❌ Código generado no se sanitiza | **Alto** — el generador podría producir código con vulnerabilidades |
| Sin autenticación | ❌ No hay control de acceso a la CLI | Medio — acceso local únicamente |
| Sin rate limiting | ❌ No hay protección contra abuso | Medio — cuando se exponga vía API |
| Sin auditoría | ❌ No se logea quién ejecutó qué | Medio — sin trazabilidad forense |
| Sin escaneo de dependencias | ❌ No hay SCA (Software Composition Analysis) | Alto — vulnerabilidades en dependencias |

### 10.2 Recomendaciones

| Prioridad | Medida | Implementación |
|-----------|--------|---------------|
| **Crítica** | Sanitizar código generado | Integrar `bandit` o `semgrep` como stage final del pipeline |
| **Alta** | Autenticación API | JWT + API keys via pydantic-settings |
| **Alta** | Auditoría de acciones | Log inmutable (append-only JSON) de cada compilación |
| **Media** | Rate limiting | Token bucket (en memoria → Redis) |
| **Media** | SCA automático | `pip-audit` en CI + pre-commit hook |
| **Baja** | Encriptación de LLM cache | AES-256-GCM para respuestas cacheadas |

---

## 11. Escalabilidad y Rendimiento

### 11.1 Perfil de Rendimiento Actual

**Cuello de botella principal:** Llamadas LLM secuenciales.

| Solicitud típica | LLM Calls | Latencia Estimada | Costo API (GPT-4o) |
|-----------------|-----------|-------------------|-------------------|
| Pipeline completo (10 stages) | 6-8 | 30-60s | $0.15-0.30 |
| Prompt Chain (6 handlers) | 6-10 | 20-50s | $0.10-0.25 |
| Modo mixto | 4-6 | 15-40s | $0.08-0.20 |

### 11.2 Estrategia de Escalabilidad

| Dimensión | Estado Actual | Mejora Propuesta | Impacto |
|-----------|--------------|-----------------|---------|
| **Paralelización** | Completamente secuencial | Ejecutar stages independientes en paralelo (Synthesis + UI pueden ejecutarse simultáneamente) | -40% latencia |
| **Cacheo LLM** | No implementado | Cache LRU + Redis con TTL por prompt | -30% llamadas |
| **Pooling de conexiones** | 1 conexión/request | httpx connection pool reutilizable | -200ms overhead |
| **Modelos diferenciados** | Un solo modelo | GPT-4o-mini para stages simples (preprocess, format) + GPT-4o para complejos | -60% costo |
| **Batching de prompts** | No implementado | Prompts similares agrupados en llamadas batch | -50% overhead |

### 11.3 Límites Conocidos

1. **Memoria**: Sin límite documentado — `MetricsStore` crece indefinidamente
2. **StateGraph**: Compilado en memoria — sin persistencia entre invocaciones
3. **File handles**: Sin pool — cada generator abre/cierra archivos individualmente
4. **SQLite**: Lock de escritura exclusivo — cuello de botella en concurrencia

---

## 12. Recomendaciones Priorizadas

### 12.1 Alto Impacto — Siguiente Sprint

| # | Acción | Esfuerzo | Beneficio | Dependencias |
|---|--------|----------|-----------|--------------|
| 1 | **Configurar ruff + pytest** en `pyproject.toml` | 1h | CI/CD funcional, calidad automática | Ninguna |
| 2 | **Eliminar dead code** (`RequirementDecomposer` si no se usa, `PipelineMacroCommand` redundante) | 2h | -2.7% código muerto, menos confusión | Ninguna |
| 3 | **Cablear LLMCache** en pipeline stages | 4h | -30% latencia y costo LLM | Ninguna |
| 4 | **Unificar EventBus + StageSubject** | 8h | Arquitectura consistente, menos duplicación | Ninguna |
| 5 | **Agregar `__init__.py` exports** en nodes/, nlp/ | 2h | IDE autocompletado, imports limpios | Ninguna |
| 6 | **Fix nombre ParserGLR → LarkParser** | 0.5h | Veracidad arquitectónica | Ninguna |

### 12.2 Medio Impacto — Próximo Milestone

| # | Acción | Esfuerzo | Beneficio |
|---|--------|----------|-----------|
| 7 | **Separar `feedback_loop.py`** en módulos (metrics/, observers/, optimizer/) | 4h | SRP, testabilidad |
| 8 | **Agregar FastAPI wrapper** sobre el pipeline | 16h | Acceso remoto, integración CI/CD |
| 9 | **Abstract StateGraph detrás de `GraphBackend` interface** | 8h | Aislamiento de upstream LangGraph changes |
| 10 | **Implementar Circuit Breaker** para LLM calls | 6h | Robustez ante fallos de API |
| 11 | **Refactor `StageContext` a frozen/inmutable** | 4h | Trazabilidad, debugging |
| 12 | **Agregar sanitización de código generado** (bandit/semgrep) | 4h | Seguridad de salida |

### 12.3 Bajo Impacto — Backlog

| # | Acción | Esfuerzo | Beneficio |
|---|--------|----------|-----------|
| 13 | **Reemplazar `NODE_MAP` hardcodeado con registro YAML** | 8h | Extensibilidad sin modificar orquestador |
| 14 | **Agregar tests de integración con LLM real** | 8h | Cobertura de fallbacks |
| 15 | **Pipeline de CI/CD completo** (lint → test → build → deploy) | 8h | Automatización completa |
| 16 | **Integrar OpenTelemetry** | 12h | Observabilidad distribuida |
| 17 | **Migrar metrics a PostgreSQL** | 8h | Concurrencia, reporting |
| 18 | **Agregar Dashboard WebSocket** (basado en DashboardObserver existente) | 16h | Monitoreo en tiempo real |

### 12.4 Mapa de Ruta Recomendado

```
Sprint 1 (1-2 semanas)         Sprint 2 (2-3 semanas)        Sprint 3 (3-4 semanas)
┌─────────────────────┐       ┌─────────────────────┐       ┌─────────────────────┐
│ 1. ruff + pytest     │       │ 7. Separar módulos   │       │ 13. Registro YAML   │
│ 2. Dead code cleanup │       │ 8. FastAPI wrapper   │       │ 14. Tests LLM real  │
│ 3. LLMCache wiring   │       │ 9. GraphBackend abs  │       │ 15. CI/CD pipeline  │
│ 4. EventBus unify    │       │ 10. Circuit Breaker  │       │ 16. OpenTelemetry   │
│ 5. __init__ exports  │       │ 11. Frozen context   │       │ 17. PostgreSQL mig  │
│ 6. Parser rename     │       │ 12. Code sanitize    │       │ 18. Dashboard WS    │
└─────────────────────┘       └─────────────────────┘       └─────────────────────┘
```

---

## 13. Conclusión

### 13.1 Fortalezas del Sistema

1. **Arquitectura coherente**: El pipeline compilador de 10 etapas es conceptualmente sólido y sigue fielmente el modelo de compiladores clásicos (Dragon Book).
2. **Implementación de patrones GoF**: 7 patrones implementados correctamente, con separación de concerns entre Template Method (ciclo de vida), CoR (handlers), Command (operaciones), Observer (eventos), Strategy+Factory (generadores), Composite (IR), y Builder (UI).
3. **Cobertura de tests**: 72 archivos de test con pytest indican una cultura de testing establecida.
4. **Calidad de datos**: Uso correcto de Pydantic v2 para contratos en todos los límites del sistema.
5. **Extensibilidad**: El diseño basado en `NODE_MAP` y registros permite agregar stages sin modificar el flujo central.

### 13.2 Debilidades

1. **Deuda técnica de integración**: Dos arquitecturas paralelas (pipeline y multi-agentes) sin conexión.
2. **Dependencia frágil**: LangGraph acoplado directamente sin abstracción protectora.
3. **Observabilidad básica**: Solo logging estándar y SQLite local para métricas.
4. **Rendimiento secuencial**: Sin paralelismo, sin cacheo de LLM — cada solicitud sufre latencia completa.
5. **Configuración de calidad ausente**: Aunque las herramientas están en dependencias dev, no están configuradas.

### 13.3 Veredicto

El sistema RECPL Compiler Bot v2.0+ es un **MVP funcional con arquitectura conceptualmente sólida** pero con **deuda técnica de integración y configuración** que debe pagarse antes de escalar a producción. La separación entre el pipeline compilador y el sistema multi-agente es la decisión arquitectónica más cuestionable — unifica ambas visiones en la propuesta TO-BE.

**Puntuación de madurez arquitectónica (NASA TRL-like): TRL 5 — Validación en entorno relevante.**

Para alcanzar TRL 7 (demostración en entorno operacional), las prioridades son: (1) unificar arquitecturas, (2) agregar cacheo LLM, (3) envolver en API con autenticación, y (4) configurar calidad automatizada en CI/CD.

---

*Documento generado a partir del análisis de 7 diagramas UML y ~20,861 LOC de código fuente. Fecha: 2026-06-18.*
