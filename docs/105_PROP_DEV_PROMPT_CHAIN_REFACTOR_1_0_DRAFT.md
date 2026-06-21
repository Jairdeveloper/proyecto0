---
id: 105
area: dev
type: prop
module: prompt_chain
version: 1.0
status: IMPLEMENTED
tags:
  - proposal
  - prompt-chaining
  - refactor
  - pipeline
  - llm
  - architecture
summary: "Propuesta de refactor del pipeline RECPL v2.0+ al patron Prompt Chaining. Cada etapa del pipeline se convierte en un prompt LLM disenado para una subtarea especifica, con respaldo rule-based y contratos Pydantic entre etapas."
keywords:
  - prompt-chaining
  - chain-of-thought
  - pipeline
  - refactor
  - llm-agents
  - recpl
changelog:
  - version: 1.0
    date: 2026-06-16
    author: workflow-agent
    description: Creacion de la propuesta de refactor a Prompt Chaining
---

# Prompt Chaining: Refactor del Pipeline RECPL

> **Version de la propuesta:** 1.0
> **Estado:** DRAFT
> **Componentes afectados:** Pipeline compilador (10 stages) + Sistema multi-agente (5 agentes) + ToolRegistry

---

## Tabla de Contenidos

1. [Diagnostico: Pipeline actual vs Prompt Chaining](#1-diagnostico)
2. [Arquitectura Propuesta](#2-arquitectura-propuesta)
   - 2.1 [Visualizacion del Flujo](#21-visualizacion-del-flujo)
   - 2.2 [Mapeo: Pipeline Actual → Prompt Chain](#22-mapeo-pipeline-actual--prompt-chain)
   - 2.3 [Estructura de Comunicacion entre Etapas](#23-estructura-de-comunicacion-entre-etapas)
   - 2.4 [Context Engineering como Capa Transversal](#24-context-engineering-como-capa-transversal)
   - 2.5 [Componentes Nuevos](#25-componentes-nuevos)
3. [Diseno de Prompts](#3-diseno-de-prompts)
4. [Integracion con Herramientas Externas](#4-integracion-con-herramientas)
5. [LLM Backend Abstraction](#5-llm-backend)
6. [Plan de Implementacion por Fases](#6-plan-de-implementacion)
7. [Criterios de Aceptacion](#7-criterios-de-aceptacion)
8. [Riesgos y Mitigaciones](#8-riesgos)

---

## 1. Diagnostico

### 1.1 Principios de Prompt Chaining

El encadenamiento de prompts (Prompt Chaining) propone:

| Principio | Descripcion |
|-----------|-------------|
| **Divide y venceras** | Problema complejo → secuencia de subproblemas manejables |
| **Prompt especifico por paso** | Cada subproblema tiene un prompt LLM disenado especificamente |
| **Flujo secuencial** | Salida de un paso → entrada del siguiente |
| **Modularidad** | Cada paso es debuggeable y optimizable independientemente |
| **Integracion externa** | Cada paso puede invocar APIs, herramientas, bases de datos |
| **Agentes autonomos** | El encadenamiento permite planificar, razonar y actuar |

### 1.2 Estado Actual del Pipeline

| Componente | Implementacion actual | Problema |
|------------|----------------------|----------|
| **IntentClassifier** | Regex + SentenceTransformers | Sin LLM. No entiende matices linguisticos. Falsos positivos en ambiguedad |
| **Preprocessor** | Filtros deterministicos + spaCy (opcional) | Sin contexto semantico. No corrige ni interpreta |
| **Lexer** | DFA + trie con maximal munch | Rigido. No generaliza a vocabulario nuevo |
| **ParserGLR** | Lark GLR con 4 gramaticas fijas | Gramatica limitada. Falla en instrucciones no cubiertas |
| **SemanticAnalyzer** | Type checking rule-based | No valida coherencia del dominio |
| **IRGenerator** | AST → IR canonico | Duplicado funcional con Planner |
| **ReasoningEngine** | GoalTreePlanner heuristico | Sin LLM. Planes rigidos (5 templates fijos) |
| **ActionExecutor** | GeneratorFactory + templates | Codigo generado por template, no por LLM |
| **UIGenerator** | Builder pattern | Solo componentes predefinidos |
| **ValidatorPipeline** | Chain of Responsibility | Validacion superficial |
| **SupervisorAgent** | Rule-based puro | Sin capacidad de razonar, solo delega |
| **Solo 2 prompts LLM** | `llm_tools.py` (domain + entities) | Infrautilizacion del LLM |

### 1.3 Gap Fundamental

> El pipeline trata el lenguaje natural como un lenguaje de programacion
> (lexer → parser → AST → IR) cuando deberia tratarlo como una
> **cadena de prompts** donde cada etapa es un LLM con un prompt
> disenado para una sub-tarea especifica.

---

## 2. Arquitectura Propuesta

### 2.1 Visuzlizacion del Flujo

```
INPUT: "crea un modulo de pagos en NestJS"
    │
    ▼
┌──────────────────────────────────────────────────────┐
│ 1. PREPROCESS PROMPT                                  │
│    "Normaliza y segmenta el texto del usuario..."     │
│    Output: {normalized, domain, language, segments}   │
├──────────────────────────────────────────────────────┤
│ 2. INTENT PROMPT                                      │
│    "Clasifica la intencion y extrae entidades..."    │
│    Output: {intent, module, entity, tech, features}   │
├──────────────────────────────────────────────────────┤
│ 3. PLAN PROMPT                                        │
│    "Descompone el objetivo en tareas ejecutables..."  │
│    Output: {tasks: [{action, target, params}]}        │
├──────────────────────────────────────────────────────┤
│ 4. GENERATE PROMPT                                    │
│    "Genera codigo NestJS/Prisma para cada tarea..."   │
│    Output: {files: [{path, content}]}                 │
├──────────────────────────────────────────────────────┤
│ 5. VERIFY PROMPT                                      │
│    "Verifica que los archivos cumplen requisitos..."  │
│    Output: {valid, checks, suggestions}               │
├──────────────────────────────────────────────────────┤
│ 6. FORMAT PROMPT                                      │
│    "Genera resumen final de lo creado..."             │
│    Output: {summary, files, next_steps}               │
└──────────────────────────────────────────────────────┘
    │
    ▼
OUTPUT: JSON + archivos generados en disco
```

### 2.2 Mapeo: Pipeline Actual → Prompt Chain

| Etapa actual (10) | Prompt Chain (6) | Accion |
|-------------------|-------------------|--------|
| Preprocessor | PREPROCESS | Refactor a prompt + fallback rule-based |
| INTENT (PerceptionUnit) | INTENT | Fusionar IntentClassifier + NER + SlotFiller + AmbiguityDetector en un prompt |
| LEXER | ~~eliminar~~ | Obsoleto. El prompt INTENT extrae tokens semanticos directamente |
| PARSER | ~~eliminar~~ | Obsoleto. La estructura la extrae el prompt INTENT |
| SemanticAnalyzer | (integrado en VERIFY) | Fusionado con validacion |
| IRGenerator | ~~eliminar~~ | Obsoleto. El prompt PLAN genera tareas directamente |
| PLANNER | PLAN | Refactor a prompt + fallback GoalTreePlanner |
| SYNTHESIS | GENERATE | Refactor a prompt + fallback GeneratorFactory |
| UIGenerator | GENERATE | Caso especifico del prompt GENERATE |
| VALIDATOR | VERIFY | Refactor a prompt + fallback ValidatorPipeline |

### 2.3 Estructura de Comunicacion entre Etapas

Cada etapa del prompt chain es un nodo que recibe entrada estructurada, la procesa
mediante un prompt LLM (o fallback rule-based), y produce salida estructurada.
La comunicacion entre etapas sigue un **contrato explicito**: la salida de la etapa N
se convierte en (parte de) la entrada de la etapa N+1 mediante sustitucion de
variables en la plantilla del prompt.

#### 2.3.1 Flujo de Datos: Concreto

```
INPUT BRUTO:
  "crea un modulo de pagos en NestJS"

  │
  ▼
┌─ ETAPA 1: PREPROCESS ──────────────────────────────────┐
│                                                        │
│  Template: "Normaliza el siguiente texto: {raw_text}"  │
│                                                        │
│  Entrada:  { "raw_text": "crea un modulo de pagos..." }│
│                                                        │
│  Salida (JSON):                                        │
│    {                                                    │
│      "normalized": "crea un modulo de pagos en nestjs",│
│      "domain": "backend",                              │
│      "language": "es",                                 │
│      "segments": ["crea un modulo de pagos en nestjs"],│
│      "has_ambiguity": false,                           │
│      "confidence": 0.95                                │
│    }                                                    │
│                                                        │
│  Tool access: read_file (si --file)                    │
└────────────────────────────────────────────────────────┘
  │
  │ ChainContext.set_output("preprocess", salida)
  │
  ▼
┌─ ETAPA 2: INTENT ──────────────────────────────────────┐
│                                                        │
│  Template:                                              │
│    "Texto normalizado: {normalized}                    │
│     Dominio: {domain}                                  │
│     Clasifica la intencion y extrae entidades..."      │
│                                                        │
│  Entrada (desde ChainContext):                          │
│    preprocess.normalized  →  {normalized}              │
│    preprocess.domain      →  {domain}                  │
│                                                        │
│  Salida (JSON):                                        │
│    {                                                    │
│      "intent": "CREATE",                               │
│      "confidence": 0.98,                               │
│      "module": "pagos",                                │
│      "entity": null,                                   │
│      "tech": ["nestjs"],                               │
│      "features": [],                                   │
│      "is_ambiguous": false,                            │
│      "missing_info": []                                │
│    }                                                    │
│                                                        │
│  Tool access: search_code, memory.get_recent()         │
└────────────────────────────────────────────────────────┘
  │
  │ ChainContext.set_output("intent", salida)
  │
  ▼
┌─ ETAPA 3: PLAN ────────────────────────────────────────┐
│                                                        │
│  Template:                                              │
│    "Intencion: {intent}                                │
│     Modulo: {module}                                   │
│     Tecnologia: {tech}                                 │
│     Descompone en tareas ejecutables..."               │
│                                                        │
│  Entrada (desde ChainContext):                          │
│    intent.intent   →  {intent}                         │
│    intent.module   →  {module}                         │
│    intent.tech     →  {tech}                           │
│    intent.features →  {features}                       │
│                                                        │
│  Salida (JSON):                                        │
│    {                                                    │
│      "tasks": [                                        │
│        {"id": "t1", "type": "scaffold_module",         │
│         "target": "pagos", "params": {"tech": "nestjs"},│
│         "dependencies": []},                            │
│        {"id": "t2", "type": "generate_code",           │
│         "target": "pagos",                              │
│         "params": {"type": "controller"},               │
│         "dependencies": ["t1"]},                        │
│        {"id": "t3", "type": "generate_code",           │
│         "target": "pagos",                              │
│         "params": {"type": "service"},                  │
│         "dependencies": ["t1"]}                         │
│      ],                                                 │
│      "execution_order": ["t1", "t2", "t3"],            │
│      "complexity": "low",                              │
│      "estimated_files": 3                               │
│    }                                                    │
│                                                        │
│  Tool access: world_model.query(), search_code         │
└────────────────────────────────────────────────────────┘
  │
  │ ... y asi sucesivamente hasta FORMAT
  ▼
```

El mecanismo de sustitucion de variables sigue el patron **LCEL**
(LangChain Expression Language):

```python
# Cada etapa se define como: template | llm | parser
preprocess_chain = preprocess_template | llm | output_parser

# La etapa siguiente toma campos especificos de la salida anterior
intent_chain = (
    {"normalized": preprocess_chain | extract_key("normalized"),
     "domain":    preprocess_chain | extract_key("domain")}
    | intent_template
    | llm
    | output_parser
)

# La cadena completa compone todas las etapas
full_chain = preprocess_chain | intent_chain | plan_chain | ...
```

#### 2.3.2 Mecanismo de Comunicacion: ChainContext

Cada etapa publica su salida en un `ChainContext` compartido, y la siguiente
etapa solo toma los campos que necesita:

```
            ChainContext (bus de datos)
  ┌──────────────────────────────────────────────────┐
  │                                                   │
  │  preprocess: {normalized, domain, language, ...}  │
  │  intent:     {intent, module, tech, features, ...}│
  │  plan:       {tasks, execution_order, ...}        │
  │  generate:   {files, errors}                      │
  │  verify:     {valid, checks, suggestions}         │
  │  format:     {summary, files_created, ...}        │
  │                                                   │
  └──────────────────────────────────────────────────┘
         ▲          ▲          ▲          ▲
         │ publish  │ publish  │ publish  │ publish
  ┌──────┴───┐ ┌───┴────┐ ┌───┴────┐ ┌───┴──────┐
  │PREPROCESS│ │ INTENT │ │  PLAN  │ │ GENERATE │ ...
  └──────────┘ └────────┘ └────────┘ └──────────┘
         │          │          │          │
         │ read     │ read     │ read     │ read
         ▼          ▼          ▼          ▼
      Template  Template  Template  Template
      (raw_text) (normalized, (intent, (tasks,
                 domain)    module,   existing_files)
                            tech)

```

`ChainContext` implementa **publicacion-selectiva**: una etapa no necesita
todo el contexto de la etapa anterior, solo los campos que su template
declara como dependencias.

```python
class ChainContext:
    """Bus de datos entre etapas con dependencias explicitas."""

    def __init__(self):
        self._data: dict[str, Any] = {}
        self._history: list[ChainStep] = []

    def set_output(self, stage: str, data: dict) -> None:
        """Guarda la salida completa de una etapa."""
        self._data[stage] = data
        self._history.append(ChainStep(stage=stage, output=data))

    def get_fields(self, stage: str, fields: list[str]) -> dict:
        """Obtiene solo los campos necesarios de una etapa anterior.
        Lanza KeyError si algun campo no existe (contrato violado).
        """
        output = self._data[stage]
        return {f: output[f] for f in fields}

    def render_template(self, template: str, stage: str, fields: list[str]) -> str:
        """Rellena un template con campos de una etapa anterior."""
        context = self.get_fields(stage, fields)
        return template.format(**context)
```

#### 2.3.3 Patrones de Encadenamiento Soportados

Basados en los 7 patrones de Prompt Chaining, la propuesta implementa
los siguientes:

| Patron | Descripcion | En la propuesta |
|--------|-------------|-----------------|
| **Secuencial lineal** | N1 → N2 → N3 sin bifurcaciones | Flujo base: PREPROCESS → INTENT → PLAN → GENERATE → VERIFY → FORMAT |
| **Condicional** | Si condicion X, rama A; si no, rama B | VERIFY: si `should_retry=true`, vuelve a GENERATE con sugerencias; si no, sigue a FORMAT |
| **Iterativo** | Repetir N veces hasta condicion de terminacion | Generacion de codigo con N intentos de refinamiento (max 3) |
| **Paralelo fan-out** | Descomponer en subtareas independientes ejecutadas simultaneamente | PLAN genera N tareas; GENERATE procesa tareas independientes en paralelo |
| **Map-reduce** | Procesar multiples items en paralelo y reducir a un unico output | GENERATE: cada archivo se genera en paralelo, VERIFY valida todos juntos |
| **Agente con estado** | Cada turno preserva historial conversacional | `ChainContext._history` + `ConversationalMemory` persisten entre invocaciones |
| **Extraccion + validacion** | Extraer datos, validar, condicionalmente re-extraer | VERIFY detecta errores → GENERATE con retroalimentacion especifica |

#### 2.3.4 Implementacion con LangGraph

Usando LangGraph (ya existente en el proyecto), cada prompt es un nodo
en el grafo de estado:

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Any

class ChainState(TypedDict):
    raw_input: str
    preprocess_output: dict | None
    intent_output: dict | None
    plan_output: dict | None
    generate_output: dict | None
    verify_output: dict | None
    format_output: dict | None
    attempt_count: int
    errors: list[str]

# Nodo 1: PREPROCESS
def preprocess_node(state: ChainState) -> dict:
    ctx = build_context("preprocess", state)
    prompt = render_prompt("preprocess", {"raw_text": state["raw_input"]},
                           context=ctx)
    result = llm.generate_structured(prompt, schema=PreprocessorContract)
    return {"preprocess_output": result.model_dump()}

# Nodo Condicional: VERIFY → GENERATE retry o FORMAT
def verify_router(state: ChainState) -> str:
    if state["verify_output"]["should_retry"] and state["attempt_count"] < 3:
        return "regenerate"
    return "format"

# Grafo
graph = StateGraph(ChainState)
graph.add_node("preprocess", preprocess_node)
graph.add_node("intent", intent_node)
graph.add_node("plan", plan_node)
graph.add_node("generate", generate_node)
graph.add_node("verify", verify_node)
graph.add_node("format", format_node)

graph.set_entry_point("preprocess")
graph.add_edge("preprocess", "intent")
graph.add_edge("intent", "plan")
graph.add_edge("plan", "generate")
graph.add_edge("generate", "verify")
graph.add_conditional_edges("verify", verify_router, {
    "regenerate": "generate",
    "format": "format",
})
graph.set_finish_point("format")

app = graph.compile()
result = app.invoke({"raw_input": "crea un modulo de pagos", "attempt_count": 0})
```

Este grafo ya puede ejecutarse con `PipelineDebugger` para trace/step/timing,
y con `show_output=True` muestra el JSON completo de cada nodo.

#### 2.3.5 Ejemplo Completo de Flujo de Datos (Input/Output Real)

```
INPUT: "crea un modulo de pagos en NestJS"

ETAPA 1 → PREPROCESS
  Template: "Normaliza: {raw_text}"
  Salida: {
    "normalized": "crea un modulo de pagos en nestjs",
    "domain": "backend",
    "language": "es",
    "segments": ["crea un modulo de pagos en nestjs"],
    "has_ambiguity": false,
    "confidence": 0.95
  }

ETAPA 2 → INTENT
  Template: "Texto: {normalized}. Dom: {domain}. Clasifica..."
  Toma del paso 1: normalized, domain
  Salida: {
    "intent": "CREATE",
    "confidence": 0.98,
    "module": "pagos",
    "entity": null,
    "tech": ["nestjs"],
    "features": [],
    "is_ambiguous": false,
    "missing_info": []
  }

ETAPA 3 → PLAN
  Template: "Intencion: {intent}. Modulo: {module}. Tech: {tech}. Planifica..."
  Toma del paso 2: intent, module, tech, features
  Salida: {
    "tasks": [
      {"id": "t1", "type": "scaffold_module", "target": "pagos",
       "params": {"tech": "nestjs"}, "dependencies": []},
      {"id": "t2", "type": "generate_code", "target": "pagos.controller",
       "params": {"type": "controller"}, "dependencies": ["t1"]}
    ],
    "execution_order": ["t1", "t2"],
    "complexity": "low",
    "estimated_files": 2
  }

ETAPA 4 → GENERATE (paralelo: t1 y t2)
  Template: "Tareas: {tasks}. Genera codigo NestJS..."
  Toma del paso 3: tasks
  Tool access: read_file(templates/), write_file(output/)
  Salida: {
    "files": [
      {"path": "modules/pagos/pagos.module.ts", "content": "..."},
      {"path": "modules/pagos/pagos.controller.ts", "content": "..."}
    ],
    "errors": []
  }

ETAPA 5 → VERIFY
  Template: "Requisitos: {requirements}. Archivos: {files}. Verifica..."
  Toma del paso 2: intent, module  (como requirements)
  Toma del paso 4: files
  Tool access: run_command(lint)
  Salida: {
    "valid": true,
    "checks": [{"check": "estructura", "passed": true}],
    "should_retry": false,
    "suggestions": ["Considera anadir un servicio para logica de negocio"]
  }

  → Router: should_retry=false → continuar a FORMAT

ETAPA 6 → FORMAT
  Template: "Resumen: plan={plan}, files={files}, valid={valid}. Formatea..."
  Toma del paso 3: tasks (plan)
  Toma del paso 4: files
  Toma del paso 5: valid, checks
  Salida: {
    "summary": "Modulo 'pagos' creado en NestJS con 2 archivos.",
    "files_created": ["modules/pagos/pagos.module.ts",
                      "modules/pagos/pagos.controller.ts"],
    "warnings": [],
    "next_steps": ["Ejecuta npm install", "Anade el modulo en app.module.ts"],
    "success": true
  }

OUTPUT FINAL: JSON + archivos en disco
```

### 2.4 Context Engineering como Capa Transversal

Cada prompt en la cadena no recibe solo la salida de la etapa anterior.
Recibe un **contexto enriquecido** construido por el motor de Context Engineering:

```
Context Engineering
  ┌────────────────────────────────────────────────────────────┐
  │                                                            │
  │  Por cada etapa, construir:                                │
  │                                                            │
  │  1. System Prompt  ──  "Eres un analista de requisitos..." │
  │                       (rol + tono + reglas fijas)          │
  │                                                            │
  │  2. Input Data  ────  Campos especificos de etapas previas │
  │                       (via ChainContext.get_fields)        │
  │                                                            │
  │  3. Retrieved Docs  ─  Template files, schemas existentes  │
  │                       (via ToolRegistry.read_file)         │
  │                                                            │
  │  4. Tool Outputs  ──  Resultados de herramientas externas  │
  │                       (via ToolRegistry.search_code, etc)  │
  │                                                            │
  │  5. Conversation     Historial de la sesion actual         │
  │     History  ──────  (via ConversationalMemory.get_recent) │
  │                                                            │
  │  6. Environment     Estado actual del proyecto en disco    │
  │     State  ────────  (via WorldModel.snapshot)             │
  │                                                            │
  └────────────────────────────────────────────────────────────┘
```

La funcion `build_context()` (N2.2c existente en `orchestrator.py`) se
extiende para construir este contexto enriquecido por etapa:

```python
def build_context(stage: str, chain_state: ChainState,
                  memory: ConversationalMemory | None = None,
                  world: WorldModel | None = None,
                  tool_registry: ToolRegistry | None = None) -> PromptContext:
    """Construye el contexto optimo para cada etapa del prompt chain.

    Capas:
    1. System prompt base (segun etapa)
    2. Input data desde ChainContext
    3. Documentos recuperados (templates, schemas)
    4. Outputs de herramientas
    5. Historial conversacional
    6. Estado del entorno
    """
    ctx = PromptContext(stage=stage)

    # Capa 1: System prompt
    ctx.system_prompt = SYSTEM_PROMPTS[stage]

    # Capa 2: Input data desde cadenas anteriores
    if stage == "intent":
        ctx.input_data = chain_state.get_fields("preprocess",
                                                ["normalized", "domain"])
    elif stage == "plan":
        ctx.input_data = chain_state.get_fields("intent",
                                                ["intent", "module", "tech",
                                                 "features"])
    # ...etc

    # Capa 5: Historial conversacional (para stages de percepcion)
    if stage in ("preprocess", "intent") and memory:
        ctx.history = memory.get_recent(limit=3)

    # Capa 6: Estado del entorno (para stages de planificacion)
    if stage in ("plan", "generate") and world:
        ctx.world_snapshot = world.snapshot()

    return ctx
```

### 2.5 Componentes Nuevos

| Componente | Archivo | Proposito |
|------------|---------|-----------|
| `PromptTemplate` | `prompt_chain/prompt_template.py` | Registro de templates con schema de entrada/salida, version, y fallback |
| `LLMBackend` | `prompt_chain/llm_backend.py` | Abstraccion sobre OpenAI / Ollama / vLLM con failover y retry |
| `ChainContext` | `prompt_chain/chain_context.py` | Bus de datos entre prompts con validacion de contratos |
| `ChainOrchestrator` | `prompt_chain/orchestrator.py` | Reemplaza SupervisorAgent rule-based con prompt-driven |
| `FallbackRegistry` | `prompt_chain/fallbacks.py` | Registro de funciones rule-based por etapa |

---

## 3. Diseno de Prompts

### 3.1 Prompt 1: PREPROCESS

```
System: Eres un asistente que normaliza instrucciones de desarrollo de software.
Analiza el texto y extrae informacion estructurada.

Reglas:
- Corrige errores ortograficos obvios
- Segmenta en oraciones
- Identifica el dominio principal
- Si el texto es ambiguo, marcalo

Input: {raw_text}

Output STRICT JSON (sin markdown, sin comentarios):
{
  "normalized": "<texto limpio>",
  "domain": "backend" | "frontend" | "infra" | "general",
  "language": "es" | "en",
  "segments": ["<oracion 1>", "<oracion 2>"],
  "has_ambiguity": true | false,
  "confidence": 0.0-1.0
}
```

**Fallback rule-based:** `NormalizationFilter` + `SegmentationFilter` actuales.
**Contrato de salida:** `PreprocessorContract` (existente, ampliado con `has_ambiguity`).

### 3.2 Prompt 2: INTENT

```
System: Eres un analista de requisitos de software. Del texto dado,
identifica que accion se pide y con que detalles.

Acciones disponibles:
- CREATE: crear modulo, entidad, proyecto, crud
- READ: consultar, listar, mostrar, leer
- UPDATE: modificar, actualizar, agregar campo, cambiar
- DELETE: eliminar, borrar, quitar, remover
- EXPLAIN: explicar, describir, como funciona

Input: {normalized_text}

Output STRICT JSON:
{
  "intent": "CREATE" | "READ" | "UPDATE" | "DELETE" | "EXPLAIN",
  "confidence": 0.0-1.0,
  "module": "<nombre del modulo>" | null,
  "entity": "<nombre de entidad>" | null,
  "tech": ["nestjs", "prisma", "react", ...],
  "features": ["autenticacion", "crud", "email", ...],
  "is_ambiguous": true | false,
  "missing_info": ["<que falta para completar la instruccion>"]
}
```

**Fallback rule-based:** `IntentClassifier` (regex) + `NERExtractor` + `SlotFiller`.
**Contrato de salida:** `NLPContract` (existente).

### 3.3 Prompt 3: PLAN

```
System: Eres un arquitecto de software. Dado un objetivo y requisitos,
genera un plan de tareas ejecutable con dependencias.

Cada tarea debe tener:
- id unico (ej: "t1", "t2")
- tipo de accion
- target (modulo, archivo, entidad)
- parametros especificos
- dependencias (task ids que deben completarse antes)

Input:
{
  "intent": "...",
  "module": "..." | null,
  "entity": "..." | null,
  "tech": [...],
  "features": [...]
}

Output STRICT JSON:
{
  "tasks": [
    {
      "id": "t1",
      "type": "scaffold_module" | "create_entity" |
             "generate_code" | "configure" | "verify",
      "target": "<nombre del modulo/entidad>",
      "params": {
        "tech": "<tecnologia>",
        "features": ["<feature>"]
      },
      "dependencies": []
    }
  ],
  "execution_order": ["t1", "t2", "t3"],
  "complexity": "low" | "medium" | "high",
  "estimated_files": <numero estimado de archivos>
}
```

**Fallback rule-based:** `GoalTreePlanner` con templates existentes.
**Contrato de salida:** `PlannerContract` (existente).

### 3.4 Prompt 4: GENERATE

```
System: Eres un generador de codigo NestJS + Prisma.
Genera el codigo completo para cada tarea del plan.

Convenciones:
- NestJS: modulo, controller, service, DTO, entity
- Prisma: schema con modelo, campos, relaciones
- Typescript: tipado estricto, decoradores
- Incluye imports completos

Input:
{
  "tasks": [...],
  "existing_files": ["<archivos existentes en el proyecto>"]
}

Output STRICT JSON:
{
  "files": [
    {
      "path": "modules/<name>/<name>.module.ts",
      "content": "<codigo completo>",
      "type": "module" | "controller" | "service" |
              "entity" | "schema" | "dto" | "test",
      "overwrite": false
    }
  ],
  "errors": ["<error si algo fallo>"]
}
```

**Fallback rule-based:** `GeneratorFactory` + templates del directorio `templates/`.
**Contrato de salida:** `SynthesisContract` (existente, ampliado).

### 3.5 Prompt 5: VERIFY

```
System: Eres un revisor de codigo. Verifica que los archivos generados
cumplan con los requisitos y las mejores practicas de NestJS/Prisma.

Criterios de verificacion:
- Estructura de archivos correcta
- imports necesarios presentes
- naming conventions (PascalCase para clases, camelCase para metodos)
- relaciones Prisma correctas
- decoradores NestJS correctos

Input:
{
  "requirements": { "intent": "...", "module": "...", ... },
  "files": [ { "path": "...", "content": "..." } ],
  "criteria": ["estructura", "imports", "naming", "relaciones", "decoradores"]
}

Output STRICT JSON:
{
  "valid": true | false,
  "checks": [
    {
      "check": "estructura",
      "passed": true | false,
      "detail": "<explicacion si fallo>"
    }
  ],
  "should_retry": true | false,
  "suggestions": ["<mejora 1>", "<mejora 2>"]
}
```

**Fallback rule-based:** `ValidatorPipeline` (SyntaxValidator + TypeChecker + SecurityScanner).
**Contrato de salida:** `ValidatorContract` (existente, ampliado).

### 3.6 Prompt 6: FORMAT (Output Final)

```
System: Eres un asistente de desarrollo. Genera un resumen claro
de lo que se ha creado o modificado para el usuario.

Input:
{
  "original_request": "...",
  "plan": { "tasks": [...], "complexity": "..." },
  "generated_files": [{"path": "...", "type": "..."}],
  "validation": { "valid": true | false, "checks": [...], "suggestions": [...] }
}

Output STRICT JSON:
{
  "summary": "<resumen en lenguaje natural, 2-3 oraciones>",
  "files_created": ["<path relativo 1>", "<path relativo 2>"],
  "warnings": ["<advertencia 1>"],
  "next_steps": [
    "Ejecuta npm install para instalar dependencias",
    "Revisa el archivo <path> para personalizar la logica"
  ],
  "success": true | false
}
```

**Fallback:** `ExplainTool` del ToolRegistry.
**Contrato de salida:** Nuevo `OutputContract`.

---

## 4. Integracion con Herramientas

### 4.1 Tool Access por Prompt

Cada prompt tiene acceso contextual al `ToolRegistry`:

| Prompt | Tools disponibles | Cuando se invocan |
|--------|------------------|-------------------|
| PREPROCESS | `read_file` | Si input viene de archivo (`--file`) |
| INTENT | `search_code`, `memory.get_recent()` | Para contextualizar con proyectos existentes |
| PLAN | `world_model.query()`, `search_code` | Para conocer estructura actual del proyecto |
| GENERATE | `read_file` (leer templates), `write_file` (escribir output) | Durante generacion de cada archivo |
| VERIFY | `run_command` (lint/typecheck), `read_file` | Para validacion post-generacion |
| FORMAT | `explain` | Para respuesta textual |

### 4.2 ChainContext

El `ChainContext` es el bus de datos entre prompts. Cada etapa escribe y lee del context:

```python
class ChainContext:
    """Bus de datos entre etapas del prompt chain."""

    def __init__(self):
        self._data: dict[str, Any] = {}
        self._contracts: dict[str, BaseModel] = {}
        self._history: list[ChainStep] = []

    def set_output(self, stage: str, data: Any) -> None:
        """Guarda output de una etapa. Valida contra contrato si existe."""
        ...

    def get_stage_output(self, stage: str) -> Any:
        """Recupera output de una etapa anterior."""
        ...

    def get_all_context(self) -> dict[str, Any]:
        """Todo el contexto acumulado para el siguiente prompt."""
        ...
```

---

## 5. LLM Backend

### 5.1 Abstraccion

```python
class LLMBackend(ABC):
    """Abstraccion sobre proveedores de LLM con failover."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str: ...

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        system: str = "",
        output_schema: type[BaseModel] = None,
    ) -> BaseModel: ...
```

### 5.2 Proveedores Soportados

| Proveedor | Clase | Configuracion |
|-----------|-------|---------------|
| OpenAI | `OpenAIBackend` | `AGENTIC_OPENAI_API_KEY`, `AGENTIC_OPENAI_MODEL` (defecto: gpt-4o-mini) |
| Ollama | `OllamaBackend` | `AGENTIC_OLLAMA_URL` (defecto: localhost:11434), `AGENTIC_OLLAMA_MODEL` |
| vLLM | `VLLMBackend` | `AGENTIC_VLLM_URL`, `AGENTIC_VLLM_MODEL` |
| HTTP API | `HTTPBackend` | `AGENTIC_LLM_URL`, `AGENTIC_LLM_API_KEY` (cualquier API compatible OpenAI) |

### 5.3 Estrategia de Failover

```
LLMBackend.generate(prompt)
  ├── 1. Intentar OpenAI (si configurado)
  ├── 2. Si falla → Intentar Ollama (si configurado)
  ├── 3. Si falla → Intentar vLLM (si configurado)
  └── 4. Si todos fallan → Usar fallback rule-based
```

### 5.4 Configuracion por Prompt

Cada prompt puede tener su propia configuracion de LLM:

```yaml
prompts:
  preprocess:
    provider: openai
    model: gpt-4o-mini
    temperature: 0.1  # baja para normalizacion deterministica
    fallback: preprocessor_filters
  intent:
    provider: openai
    model: gpt-4o-mini
    temperature: 0.2
    fallback: intent_classifier_regex
  plan:
    provider: openai
    model: gpt-4o-mini
    temperature: 0.3
    fallback: goal_tree_planner
  generate:
    provider: openai
    model: gpt-4o-mini
    temperature: 0.4  # un poco mas creativo para codigo
    fallback: generator_factory
  verify:
    provider: openai
    model: gpt-4o-mini
    temperature: 0.1
    fallback: validator_pipeline
  format:
    provider: openai
    model: gpt-4o-mini
    temperature: 0.5  # mas creativo para lenguaje natural
    fallback: explain_tool
```

---

## 6. Plan de Implementacion

### Fase 1 — Infraestructura Base

| Tarea | Archivos | Dependencias |
|-------|----------|-------------|
| 1.1 | `prompt_chain/__init__.py`, `prompt_chain/prompt_template.py` | — |
| 1.2 | `prompt_chain/llm_backend.py` + OpenAI/Ollama/vLLM backends | F1.1 |
| 1.3 | `prompt_chain/chain_context.py` | F1.1 |
| 1.4 | `prompt_chain/fallbacks.py` (wrapper sobre componentes existentes) | F1.1 |
| 1.5 | Tests: `tests/test_prompt_template.py`, `tests/test_llm_backend.py` | F1.1-F1.4 |

**Criterios de aceptacion:**
- `PromptTemplate` registry funciona con 6 templates registrados
- `LLMBackend` con OpenAI funcionando y failover a fallback
- `ChainContext` pasa datos entre etapas con validacion de contratos
- ruff 0 errores, pytest pasa

### Fase 2 — Prompts Core

| Tarea | Prompt | Fallback | Tests |
|-------|--------|----------|-------|
| 2.1 | PREPROCESS | `NormalizationFilter` + `SegmentationFilter` | `test_prompt_preprocess.py` |
| 2.2 | INTENT | `IntentClassifier` + `NERExtractor` + `SlotFiller` | `test_prompt_intent.py` |
| 2.3 | PLAN | `GoalTreePlanner` | `test_prompt_plan.py` |
| 2.4 | GENERATE | `GeneratorFactory` + templates | `test_prompt_generate.py` |
| 2.5 | VERIFY | `ValidatorPipeline` | `test_prompt_verify.py` |
| 2.6 | FORMAT | `ExplainTool` | `test_prompt_format.py` |

**Criterios de aceptacion:**
- Cada prompt produce output JSON valido contra su contrato Pydantic
- Fallback rule-based se activa cuando LLM no responde
- Cada prompt tiene al menos 5 tests (con LLM mockeado)
- ruff 0 errores

### Fase 3 — Chain Orchestrator

| Tarea | Archivo | Descripcion |
|-------|---------|-------------|
| 3.1 | `prompt_chain/orchestrator.py` | `ChainOrchestrator` que ejecuta los 6 prompts en secuencia |
| 3.2 | `prompt_chain/cli.py` | Comando `--prompt-chain` en el CLI para activar el nuevo pipeline |
| 3.3 | `compiler-bot/agentic` | Flag `--chain` para elegir entre pipeline clasico y prompt chain |

**Criterios de aceptacion:**
- `ChainOrchestrator.run("crea modulo pagos")` produce mismo output que pipeline clasico
- Flag `--chain` activa el nuevo pipeline
- Compatibilidad hacia atras: sin flag, funciona el pipeline clasico
- ruff 0 errores

### Fase 4 — Sistema Multi-Agente Prompt-Driven

| Tarea | Descripcion |
|-------|-------------|
| 4.1 | Reemplazar `SupervisorAgent` rule-based con prompt-driven |
| 4.2 | `PerceptionAgent` usa prompt INTENT en vez de SentenceTransformers |
| 4.3 | `ReasoningAgent` usa prompt PLAN en vez de GoalTreePlanner |
| 4.4 | `ExecutionAgent` usa prompt GENERATE en vez de GeneratorFactory |
| 4.5 | `ValidatorAgent` usa prompt VERIFY en vez de WorldModel.query() |

**Criterios de aceptacion:**
- Agentes funcionan con LLM y fallback rule-based
- 15 tests de `test_multiagent.py` siguen pasando
- SupervisorAgent prompt-driven decide retry/clarify/abort

### Fase 5 — Feedback Loop + Optimizacion

| Tarea | Descripcion |
|-------|-------------|
| 5.1 | `MetricsStore` registra exito/fallo de cada prompt |
| 5.2 | Ajuste automatico de temperatura y pocos ejemplos por prompt |
| 5.3 | Cache de respuestas del LLM (AST-level cache, no texto crudo) |
| 5.4 | Dashboard de metricas: tasa de exito por prompt, costos, latencia |

**Criterios de aceptacion:**
- Metricas se registran por etapa del prompt chain
- Cache reduce llamadas al LLM en >30% para prompts repetidos
- Dashboard accesible via `--metrics` flag

---

## 7. Criterios de Aceptacion Globales

- [ ] `ruff check .` — 0 errores
- [ ] `pytest tests/ -q --tb=short` — todos los tests existentes pasan (573+)
- [ ] Nuevos tests: minimo 30 tests para componentes de prompt chain
- [ ] `python compiler-bot/agentic -p "crea modulo pagos" --chain` produce JSON valido
- [ ] `python compiler-bot/agentic -p "crea modulo pagos"` (sin flag) produce mismo output que antes
- [ ] Fallback rule-based funciona sin LLM (sin API key)
- [ ] `ChainOrchestrator` con `--debug trace` muestra output JSON de cada etapa

---

## 8. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| LLM produce JSON invalido | Alta | Medio | `generate_structured()` con output_schema Pydantic + reparacion automatica |
| Costo de API por prompt encadenado | Media | Alto | Cache de respuestas, fallback local (Ollama), modelo economico (gpt-4o-mini) |
| Latencia: 6 prompts secuenciales | Alta | Medio | Prompts paralelizables (GENERATE + VERIFY), streaming parcial |
| Regresion en tests existentes | Baja | Alto | Fase 3 garantiza compatibilidad hacia atras con flag `--chain` |
| Dependencia de LLM para funcionamiento basico | Media | Alto | Fallback rule-based en cada etapa. Sin LLM el pipeline funciona igual que hoy |
| Prompts no escalan a nuevos dominios | Baja | Bajo | Sistema de versionado de prompts + A/B testing con MetricsStore |

---

## Apendice A: Estructura de Directorios Propuesta

```
compiler-bot/agentic_pipeline/
├── prompt_chain/                  # NUEVO: Prompt Chaining subsystem
│   ├── __init__.py
│   ├── prompt_template.py         # PromptTemplate registry
│   ├── llm_backend.py             # LLM abstraction + providers
│   ├── chain_context.py           # Data bus between prompts
│   ├── orchestrator.py            # ChainOrchestrator
│   ├── fallbacks.py               # Rule-based fallback registry
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── preprocess.py          # Prompt 1
│   │   ├── intent.py             # Prompt 2
│   │   ├── plan.py               # Prompt 3
│   │   ├── generate.py           # Prompt 4
│   │   ├── verify.py             # Prompt 5
│   │   └── format.py             # Prompt 6
│   └── backends/
│       ├── __init__.py
│       ├── openai.py             # OpenAI backend
│       ├── ollama.py             # Ollama backend
│       ├── vllm.py               # vLLM backend
│       └── http.py               # Generic HTTP backend
├── tests/
│   ├── test_prompt_template.py    # Fase 1
│   ├── test_llm_backend.py        # Fase 1
│   ├── test_chain_context.py      # Fase 1
│   ├── test_prompt_preprocess.py  # Fase 2
│   ├── test_prompt_intent.py      # Fase 2
│   ├── test_prompt_plan.py        # Fase 2
│   ├── test_prompt_generate.py    # Fase 2
│   ├── test_prompt_verify.py      # Fase 2
│   ├── test_prompt_format.py      # Fase 2
│   └── test_chain_orchestrator.py # Fase 3
```

## Apendice B: Ejemplo de Ejecucion

```bash
# Pipeline clasico (comportamiento actual)
python compiler-bot/agentic -p "crea un modulo de pagos en NestJS"

# Pipeline con Prompt Chaining (nuevo)
python compiler-bot/agentic -p "crea un modulo de pagos en NestJS" --chain

# Prompt Chaining + debug trace (JSON por etapa)
python compiler-bot/agentic -p "crea modulo" --chain --debug trace

# Sin LLM (solo fallbacks rule-based)
AGENTIC_LLM_PROVIDER=none python compiler-bot/agentic -p "crea modulo" --chain

# Con LLM local (Ollama)
AGENTIC_LLM_PROVIDER=ollama AGENTIC_OLLAMA_MODEL=llama3 \
    python compiler-bot/agentic -p "crea modulo" --chain
```
