---
id: 067
area: DEV
type: PLAN
module: COMPILER_BOT
version: 1.0.0
status: IMPLEMENTED
tags:
  - plan
  - implementation
  - scaling
  - pipeline
  - langchain
  - langgraph
summary: Plan de implementacion detallado para el escalamiento del pipeline RECPL v2.0
keywords: [implementation-plan, tasks, milestones, architecture]
changelog:
  - 2026-06-13: Documento creado
---

# Plan de Implementacion — RECPL Compiler Bot v2.0

## Resumen

Este plan detalla la implementacion de las decisiones adoptadas del
documento `066_PROP_DEV_COMPILER_BOT_SCALE_VISION_1_0_DRAFT.md`:

- **Scaffold**: Eliminado. Reemplazado por generadores AST-based.
- **Framework**: LangChain + LangGraph como orquestador.
- **Pipeline**: 8 etapas + 3 componentes nuevos.
- **Patrones**: 18 patrones de diseno aplicados.
- **Estimacion**: 12 meses, 4 fases, ~200 tareas.

---

## Indice de Implementacion

Cada seccion detalla: objetivos, estructura de archivos, tareas,
dependencias, criterios de aceptacion, y estrategia de tests.

---

## FASE 0 — Fundacion Tecnica (Semanas 1-4)

### 0.1 Configurar Proyecto LangChain + LangGraph

**Objetivo:** Establecer el entorno de desarrollo multi-agente.

**Estructura de archivos:**
```
compiler-bot/
  pyproject.toml           # Python project config (Poetry / pip)
  requirements.txt         # langchain, langgraph, httpx, pydantic
  agentic_pipeline/
    __init__.py
    orchestrator.py        # StateGraph principal
    state_models.py        # Tipos compartidos (Pydantic)
    nodes/                 # Nodos del grafo
      __init__.py
    tools/                 # Herramientas registradas
      __init__.py
    config.py              # Settings, env vars, LLM config
```

**Tareas:**

| # | Tarea | Depende de | Estimacion |
|---|-------|-----------|------------|
| 0.1.1 | Crear proyecto Python con pyproject.toml | — | 2h |
| 0.1.2 | Instalar langchain, langgraph, httpx, pydantic, pytest | 0.1.1 | 1h |
| 0.1.3 | Definir state_models.py (Pydantic BaseModel para cada etapa) | 0.1.1 | 4h |
| 0.1.4 | Crear config.py con settings de LLM, env vars | 0.1.1 | 2h |
| 0.1.5 | Implementar esqueleto de orchestrator.py con StateGraph vacio | 0.1.3 | 4h |
| 0.1.6 | Implementar paso 5 (Aprender y mejorar) como logger central | 0.1.5 | 3h |

**Criterios de aceptacion:**
- `pytest` corre sin errores
- StateGraph se compila con nodos placeholder
- Config carga variables de entorno correctamente

**Tests:** `test_config.py`, `test_state_models.py`, `test_orchestrator_empty.py`

### 0.2 Implementar Loop de 5 Pasos como Clase Base

**Objetivo:** Crear una clase abstracta `PipelineStage` que todas las
etapas hereden, con el loop de 5 pasos incorporado.

**Archivo:** `agentic_pipeline/base_stage.py`

```python
class PipelineStage(ABC):
    name: str
    context: StageContext

    @abstractmethod
    def receive_mission(self, input_data: Any) -> None: ...
    @abstractmethod
    def analyze(self) -> AnalysisResult: ...
    @abstractmethod
    def reflect_and_plan(self) -> ActionPlan: ...
    @abstractmethod
    def act(self) -> StageOutput: ...
    @abstractmethod
    def learn_and_improve(self, feedback: Feedback) -> None: ...

    def execute(self, input_data: Any) -> StageOutput:
        self.receive_mission(input_data)
        analysis = self.analyze()
        plan = self.reflect_and_plan(analysis)
        output = self.act(plan)
        self.learn_and_improve(output.feedback)
        return output
```

**Tareas:**

| # | Tarea | Depende de | Estimacion |
|---|-------|-----------|------------|
| 0.2.1 | Definir clases StageContext, AnalysisResult, ActionPlan, StageOutput en state_models.py | 0.1.3 | 3h |
| 0.2.2 | Implementar PipelineStage abstracta en base_stage.py | 0.2.1 | 3h |
| 0.2.3 | Implementar FeedbackLoop para paso 5 (log + metricas) | 0.2.1 | 2h |
| 0.2.4 | Test unitario de base_stage con mock stage | 0.2.2 | 2h |

**Patron:** **Template Method** — `execute()` define el esqueleto,
subclases implementan los 5 hooks.

---

## FASE 1 — Preprocessor + Lexer + Descomponedor (Semanas 5-12)

### 1.1 RequirementDecomposer (Nuevo Componente)

**Objetivo:** Traducir prompt de alto nivel a estructura formal.

**Archivos:**
```
agentic_pipeline/
  nodes/
    requirement_decomposer.py
  tools/
    llm_tools.py            # Prompts + parsing de respuestas LLM
```

**Arquitectura:**
- **Patron Facade**: `RequirementDecomposer` oculta la complejidad del
  LLM. Internamente usa un `LLMOrchestrator` que maneja prompts,
  temperature, y parsing JSON.
- Entrada: Texto crudo del usuario.
- Salida: `RequirementGraph` (JSON con dominio, entidades, features,
  constraints, user stories priorizadas).

**Tareas:**

| # | Tarea | Depende de | Estimacion |
|---|-------|-----------|------------|
| 1.1.1 | Definir modelo RequirementGraph (Pydantic) | 0.2.1 | 2h |
| 1.1.2 | Implementar LLMOrchestrator con prompts de clasificacion | 0.1.4 | 6h |
| 1.1.3 | Implementar DomainClassifier (web, mobile, CLI, API) | 1.1.2 | 4h |
| 1.1.4 | Implementar EntityExtractor (extrae User, Link, Click, etc.) | 1.1.2 | 4h |
| 1.1.5 | Implementar FeatureIdentifier (auth, QR, analytics, etc.) | 1.1.2 | 4h |
| 1.1.6 | Implementar ConstraintDetector (responsive, accessible, fast) | 1.1.2 | 3h |
| 1.1.7 | Implementar UserStoryGenerator | 1.1.3-1.1.6 | 6h |
| 1.1.8 | Integrar RequirementDecomposer como nodo LangGraph | 0.1.5, 1.1.7 | 4h |
| 1.1.9 | Loop de 5 pasos en RequirementDecomposer | 0.2.2 | 3h |

**Criterios de aceptacion:**
- Dado el prompt del acortador, produce RequirementGraph con:
  - Dominio: web
  - Entidades: User, Link, Click
  - Features: auth, link_shortening, qr_generation, analytics, dashboard
  - Constraints: responsive, accessible
  - User stories: al menos 8
- El grafo es validable con JSON Schema

**Tests:** `test_requirement_decomposer.py`, `test_domain_classifier.py`,
`test_entity_extractor.py`

### 1.2 Preprocessor

**Objetivo:** Normalizar, segmentar y enriquecer el prompt.

**Archivo:** `agentic_pipeline/nodes/preprocessor.py`

**Implementacion:**
- **Patron Chain of Responsibility**: Cadena de filtros:
  1. `NormalizationFilter` — trim, lowercase, colapso de puntuacion
  2. `DomainEnrichmentFilter` — agrega contexto segun dominio
  3. `ImplicitRequirementFilter` — "auth" → User model + JWT + session
  4. `SegmentationFilter` — divide en sub-intenciones
  5. `EmbeddingEnricher` — similaridad con ejemplos previos
- **Patron Strategy**: Diferentes cadenas segun dominio (web, CLI, API)

**Tareas:**

| # | Tarea | Depende de | Estimacion |
|---|-------|-----------|------------|
| 1.2.1 | Definir modelos PreprocessorInput, PreprocessorOutput en state_models.py | 0.2.1 | 1h |
| 1.2.2 | Implementar abstract class PreprocessingFilter (Chain of Responsibility base) | 0.2.2 | 2h |
| 1.2.3 | Implementar NormalizationFilter | 1.2.2 | 1h |
| 1.2.4 | Implementar DomainEnrichmentFilter con tabla de contexto por dominio | 1.2.2, 1.1.3 | 3h |
| 1.2.5 | Implementar ImplicitRequirementFilter | 1.2.2 | 4h |
| 1.2.6 | Implementar SegmentationFilter | 1.2.2 | 3h |
| 1.2.7 | Implementar EmbeddingEnricher (vector store con ejemplos) | 1.2.2 | 6h |
| 1.2.8 | Implementar Preprocessor (arma cadena segun Strategy) | 1.2.3-1.2.7 | 4h |
| 1.2.9 | Integrar como nodo LangGraph | 0.1.5, 1.2.8 | 2h |
| 1.2.10 | Loop de 5 pasos en Preprocessor | 0.2.2 | 3h |

**Criterios de aceptacion:**
- Dado un prompt raw, produce texto normalizado + dominio + entidades
  implicitas
- "autenticacion de usuarios" → entidad User + JWT + login/signup
- "codigos QR" → feature QR + libreria qrcode

**Tests:** `test_preprocessor_filters.py`, `test_preprocessor_chain.py`

### 1.3 Lexer

**Objetivo:** Tokenizar el texto normalizado en ~120+ tokens
organizados por categorias.

**Archivo:** `agentic_pipeline/nodes/lexer.py`

**Implementacion:**
- **Patron State**: DFA dinamico. Cada categoria (Domain, Action, Tech,
  UI, Quality) es un sub-estado con sus transiciones. El lexer salta
  entre sub-DFAs segun el contexto.
- **Patron Flyweight**: Los tokens se comparten. `Token` es inmutable
  y se cachea por (type, value).
- **Token metadata**: `Token(pos, value, type, category, confidence,
  context)`
- **Soporte multi-palabra**: Trie para frases como "panel de control",
  "codigo QR", "acortamiento de enlaces"

**Tareas:**

| # | Tarea | Depende de | Estimacion |
|---|-------|-----------|------------|
| 1.3.1 | Definir modelo Token (Pydantic) con metadata | 0.2.1 | 2h |
| 1.3.2 | Implementar TokenFlyweightRegistry (cache de tokens) | 1.3.1 | 2h |
| 1.3.3 | Implementar sub-DFA para Domain tokens | 1.3.1 | 3h |
| 1.3.4 | Implementar sub-DFA para Action tokens | 1.3.1 | 2h |
| 1.3.5 | Implementar sub-DFA para Tech tokens | 1.3.1 | 3h |
| 1.3.6 | Implementar sub-DFA para UI tokens | 1.3.1 | 3h |
| 1.3.7 | Implementar sub-DFA para Quality tokens | 1.3.1 | 2h |
| 1.3.8 | Implementar MultiWordTrie para frases multi-palabra | 1.3.1 | 4h |
| 1.3.9 | Implementar Lexer (orquesta sub-DFAs segun contexto) | 1.3.2-1.3.8 | 6h |
| 1.3.10 | Integrar como nodo LangGraph | 0.1.5, 1.3.9 | 2h |
| 1.3.11 | Loop de 5 pasos en Lexer | 0.2.2 | 3h |

**Criterios de aceptacion:**
- "crea modulo pagos en nestjs con autenticacion jwt" →
  `[ACTION_CREATE, MODULE, ENTITY_PAGOS, TECH_NESTJS, PREP_CON,
   AUTH, TECH_JWT]`
- "panel de control" → token `DASHBOARD` (no `PANEL`, `DE`, `CONTROL`)
- Cada token tiene confidence score

**Tests:** `test_lexer_sub_dfas.py`, `test_lexer_multitoken.py`,
`test_lexer_full.py`

---

## FASE 2 — Parser + Semantic + IR (Semanas 13-24)

### 2.1 Parser

**Objetivo:** Construir AST tipado desde la secuencia de tokens.

**Archivo:** `agentic_pipeline/nodes/parser.py`

**Implementacion:**
- **Parser GLR** (usando `lark` o `sly` como libreria base) para
  manejar gramaticas ambiguas.
- **Gramatica multi-dominio** cargada desde archivo `.lark`:
  - `project_grammar.lark` — reglas de proyecto, paginas, modulos
  - `ui_grammar.lark` — componentes UI, layouts, routing
  - `data_grammar.lark` — entidades, atributos, relaciones
  - `infra_grammar.lark` — servicios, despliegue, CI/CD
- **Patron Composite**: Nodos AST:
  - `ASTNode` (abstracto): `evaluate()`, `validate()`, `toIR()`
  - `ProjectNode`, `PageNode`, `ComponentNode`, `EntityNode`, etc.
- **Patron Interpreter**: Cada nodo sabe interpretarse a si mismo.
- **Recuperacion de errores**: Panic mode + LLM repair assistant.

**Tareas:**

| # | Tarea | Depende de | Estimacion |
|---|-------|-----------|------------|
| 2.1.1 | Definir nodos AST base (ASTNode, CompositeNode, LeafNode) | 0.2.1 | 3h |
| 2.1.2 | Definir ProjectNode, PageNode, ComponentNode | 2.1.1 | 3h |
| 2.1.3 | Definir EntityNode, AttributeNode, RelationNode | 2.1.1 | 3h |
| 2.1.4 | Definir EndpointNode, MiddlewareNode, RouteNode | 2.1.1 | 3h |
| 2.1.5 | Definir InfraNode, ServiceNode, PipelineStepNode | 2.1.1 | 2h |
| 2.1.6 | Crear gramatica `.lark` para estructura de proyecto | 1.3.9 | 6h |
| 2.1.7 | Crear gramatica `.lark` para UI | 2.1.2 | 6h |
| 2.1.8 | Crear gramatica `.lark` para datos/entidades | 2.1.3 | 4h |
| 2.1.9 | Implementar ParserGLR con Lark | 2.1.6-2.1.8 | 8h |
| 2.1.10 | Implementar ErrorRecovery (panic mode + LLM repair) | 2.1.9 | 6h |
| 2.1.11 | Integrar como nodo LangGraph | 0.1.5, 2.1.9 | 2h |
| 2.1.12 | Loop de 5 pasos en Parser | 0.2.2 | 3h |

**Criterios de aceptacion:**
- "pagina de login con formulario de email y password" → AST con
  `PageNode(Login) → ComponentNode(Form) → [Field(email), Field(password)]`
- Tokens malformados producen error recoverable con sugerencia LLM
- AST es serializable a JSON

**Tests:** `test_parser_project.py`, `test_parser_ui.py`,
`test_parser_data.py`, `test_parser_error_recovery.py`

### 2.2 Semantic Analyzer

**Objetivo:** Type checking multi-dominio y construccion del grafo de
dependencias semanticas.

**Archivo:** `agentic_pipeline/nodes/semantic_analyzer.py`

**Implementacion:**
- **SymbolTable**: Memoria principal con persistencia opcional (Memento)
- **Type System**:
  - `UITypeSystem` — Component, Page, Layout, Widget
  - `DataTypeSystem` — Entity, Attribute, Relation, Constraint
  - `InfraTypeSystem` — Service, Middleware, Route, Migration
  - `CrossDomainTypeChecker` — frontend-backend consistency
- **Scope analysis**: Scope global + scopes locales por modulo/pagina
- **Patron Visitor**: `SemanticVisitor` recorre AST y recolecta/
  valida tipos
- **Patron Memento**: Snapshot del estado semantico para rollback
- **Patron Prototype**: Clonar contexto semantico para analisis
  paralelo de ramas

**Tareas:**

| # | Tarea | Depende de | Estimacion |
|---|-------|-----------|------------|
| 2.2.1 | Implementar SymbolTable con operaciones CRUD | 0.2.1 | 4h |
| 2.2.2 | Implementar TypeRegistry (registra tipos por dominio) | 2.2.1 | 3h |
| 2.2.3 | Implementar UITypeSystem + validaciones | 2.2.2, 2.1.2 | 6h |
| 2.2.4 | Implementar DataTypeSystem + validaciones | 2.2.2, 2.1.3 | 6h |
| 2.2.5 | Implementar InfraTypeSystem + validaciones | 2.2.2, 2.1.4 | 4h |
| 2.2.6 | Implementar CrossDomainTypeChecker | 2.2.3-2.2.5 | 8h |
| 2.2.7 | Implementar ScopeAnalyzer | 2.2.1 | 4h |
| 2.2.8 | Implementar Memento para snapshots | 2.2.1 | 3h |
| 2.2.9 | Implementar SemanticVisitor (Visitor sobre AST) | 2.2.3-2.2.5 | 6h |
| 2.2.10 | Integrar SemanticAnalyzer como nodo LangGraph | 0.1.5, 2.2.9 | 2h |
| 2.2.11 | Loop de 5 pasos en SemanticAnalyzer | 0.2.2 | 3h |

**Criterios de aceptacion:**
- "User tiene links" → valida que Link exista como entidad y tenga
  relacion con User
- "Dashboard muestra tabla de links" → valida que Link tenga los
  atributos que la tabla necesita
- API route `GET /links` → debe existir entidad Link con controller
- Error: "Login page usa auth, pero no hay modelo User" → error
  semantico

**Tests:** `test_type_systems.py`, `test_semantic_visitor.py`,
`test_cross_domain_checker.py`, `test_scope_analyzer.py`

### 2.3 IR (Intermediate Representation)

**Objetivo:** Construir el grafo de dependencias multicapa que conecta
el modelo de dominio con la generacion de codigo.

**Archivo:** `agentic_pipeline/nodes/ir_generator.py`

**Implementacion:**
- **Patron Composite**: `IRNode` abstracto:
  ```python
  class IRNode(ABC):
      def to_code(self, target: Target) -> str: ...
      def validate(self) -> List[ValidationError]: ...
      def dependencies(self) -> List[IRNode]: ...
      def accept(self, visitor: IRVisitor): ...
  ```
- **5 capas**: Config, DomainModel, UIModel, APIModel, InfraModel
- **Patron Builder**: `IRBuilder.build()` construye step-by-step con
  validacion intermedia
- **Patron Bridge**: `IRSerializer` serializa a JSON/YAML/Graphviz
- **Grafo de dependencias**: `dependencies()` devuelve lista de nodos
  requeridos (para orden topologico del planner)

**Tareas:**

| # | Tarea | Depende de | Estimacion |
|---|-------|-----------|------------|
| 2.3.1 | Definir IRNode abstracto con metodos to_code, validate, dependencies | 0.2.1 | 3h |
| 2.3.2 | Implementar IRConfig (framework, DB, deploy, testing) | 2.3.1 | 4h |
| 2.3.3 | Implementar IRDomainModel con IREntity, IRAttribute, IRLlation | 2.3.1, 2.2.4 | 6h |
| 2.3.4 | Implementar IRUIModel con IRPage, IRComponent, IRRoute | 2.3.1, 2.2.3 | 6h |
| 2.3.5 | Implementar IRAPIModel con IREndpoint, IRMiddleware | 2.3.1, 2.2.5 | 6h |
| 2.3.6 | Implementar IRInfraModel con IRDockerService, IRPipelineStep | 2.3.1 | 4h |
| 2.3.7 | Implementar IRBuilder con validacion intermedia | 2.3.2-2.3.6 | 8h |
| 2.3.8 | Implementar IRSerializer (JSON, YAML, Graphviz DOT) | 2.3.7 | 4h |
| 2.3.9 | Implementar DependencyGraph (resolucion topologica) | 2.3.1 | 4h |
| 2.3.10 | Integrar como nodo LangGraph | 0.1.5, 2.3.7 | 2h |
| 2.3.11 | Loop de 5 pasos en IR | 0.2.2 | 3h |

**Criterios de aceptacion:**
- IR valido produce grafo aciclico de ~40-80 nodos
- Cada nodo conoce sus dependencias
- Se puede serializar a JSON y re-importar (roundtrip)
- `dependencies()` del nodo "Login page" incluye "Auth API" y
  "User entity"

**Tests:** `test_ir_nodes.py`, `test_ir_builder.py`,
`test_ir_dependencies.py`, `test_ir_serialization.py`

---

## FASE 3 — Planner + Synthesis (Semanas 25-36)

### 3.1 Planner

**Objetivo:** Descomponer el IR en tareas ordenadas y ejecutables.

**Archivo:** `agentic_pipeline/nodes/planner.py`

**Implementacion:**
- **Planner hibrido**:
  - Heuristico: para casos simples (1-3 tareas, sin dependencias)
  - LLM-based: para >3 tareas o con dependencias complejas
- **Grafo de tareas**: `TaskGraph` donde cada tarea es un nodo con:
  ```python
  class Task:
      id: str
      description: str
      dependencies: List[str]
      generator: str       # "react", "prisma", "docker", etc.
      target: Target
      state: TaskState     # pending, ready, running, done, failed
      output_path: str
      validation_rules: List[str]
  ```
- **Patron Command**: Cada tarea es `TaskCommand.execute()` /
  `undo()`. Permite rollback parcial.
- **Patron Template Method**: `PlanExecutor` define el esqueleto de
  ejecucion con hooks: `pre_execute`, `post_execute`, `on_error`,
  `validate_output`.
- **Patron Observer**: `PlanObserver` notifica cambios de estado
  (para UI, logs, metricas).
- **Plan executor**: Ejecuta en orden topologico usando `queue`
  con reintentos (max 3) y rollback parcial.

**Tareas:**

| # | Tarea | Depende de | Estimacion |
|---|-------|-----------|------------|
| 3.1.1 | Definir modelos Task, TaskGraph, TaskState | 0.2.1 | 3h |
| 3.1.2 | Implementar TaskCommand (execute/undo) | 3.1.1 | 4h |
| 3.1.3 | Implementar HeuristicPlanner (casos sencillos) | 3.1.1 | 4h |
| 3.1.4 | Implementar LLMPlanner con prompt engineering | 3.1.1, 1.1.2 | 8h |
| 3.1.5 | Implementar HybridPlanner (decide heuristico vs LLM) | 3.1.3, 3.1.4 | 4h |
| 3.1.6 | Implementar TopologicalSorter | 3.1.1 | 3h |
| 3.1.7 | Implementar PlanExecutor con Template Method | 3.1.1, 3.1.6 | 8h |
| 3.1.8 | Implementar PlanObserver (logging + metricas) | 3.1.1 | 3h |
| 3.1.9 | Implementar rollback parcial (undo chain) | 3.1.2, 3.1.7 | 6h |
| 3.1.10 | Integrar como nodo LangGraph | 0.1.5, 3.1.7 | 2h |
| 3.1.11 | Loop de 5 pasos en Planner | 0.2.2 | 3h |

**Criterios de aceptacion:**
- Prompt del acortador produce ~30-50 tareas ordenadas
- "Generar modelo User" antes de "Generar API auth" antes de
  "Generar Login page"
- Si una tarea falla, las dependientes se marcan como blocked
- Rollback deshace tareas en orden inverso

**Tests:** `test_heuristic_planner.py`, `test_llm_planner.py`,
`test_plan_executor.py`, `test_rollback.py`

### 3.2 Synthesis (Generacion Multi-Target)

**Objetivo:** Generar codigo real desde el IR usando generadores
AST-based.

**Archivo:** `agentic_pipeline/nodes/synthesis.py`

**Implementacion:**
- **Patron Abstract Factory**: `GeneratorFactory` crea familias de
  generadores:
  - `WebFrontendFactory` → ReactGenerator + TailwindGenerator
  - `BackendFactory` → NestJSGenerator + PrismaGenerator
  - `InfraFactory` → DockerGenerator + CIGenerator
- **Patron Factory Method**: Cada generador concreto (ReactGenerator,
  PrismaGenerator) se crea via metodo factory.
- **AST-based**: Cada generador construye un AST del lenguaje target
  (usando `ast` module o libreria especifica) y lo serializa con un
  `CodeFormatter` (Prettier, ESLint, Black).
- **Patron Visitor**: `CodeGenVisitor` recorre el IR y llama al
  generador correspondiente para cada nodo.
- **Patron Decorator**: `LoggingGenerator`, `ValidationGenerator`,
  `CacheGenerator` envuelven generadores concretos.

**Generadores a implementar:**

| Generador | Lenguaje Target | Depende de |
|-----------|----------------|-----------|
| ReactGenerator | JSX/TSX + CSS | 2.3.4 (IRUIModel) |
| NextJSGenerator | Next.js pages + API routes | ReactGenerator |
| TailwindGenerator | tailwind.config + classes | ReactGenerator |
| PrismaGenerator | schema.prisma | 2.3.3 (IRDomainModel) |
| NestJSGenerator | TypeScript (controllers, services) | PrismaGenerator |
| DockerGenerator | Dockerfile, docker-compose.yml | Todos los anteriores |

**Tareas:**

| # | Tarea | Depende de | Estimacion |
|---|-------|-----------|------------|
| 3.2.1 | Implementar GeneratorFactory (Abstract Factory) | 0.2.1 | 4h |
| 3.2.2 | Implementar CodeGenVisitor (Visitor sobre IR) | 2.3.1, 3.2.1 | 6h |
| 3.2.3 | Implementar ReactGenerator (AST-based JSX) | 3.2.2, 2.3.4 | 12h |
| 3.2.4 | Implementar NextJSGenerator (pages + API routes) | 3.2.3 | 8h |
| 3.2.5 | Implementar TailwindGenerator (config + classes) | 3.2.3 | 6h |
| 3.2.6 | Implementar PrismaGenerator (schema + migrations) | 3.2.2, 2.3.3 | 8h |
| 3.2.7 | Implementar NestJSGenerator (controllers, services) | 3.2.6 | 10h |
| 3.2.8 | Implementar DockerGenerator | 3.2.3-3.2.7 | 6h |
| 3.2.9 | Implementar CodeFormatter (Prettier wrapper) | 3.2.3 | 3h |
| 3.2.10 | Implementar LoggingDecorator, CacheDecorator | 3.2.1 | 3h |
| 3.2.11 | Integrar Synthesis como nodo LangGraph | 0.1.5, 3.2.2 | 2h |
| 3.2.12 | Loop de 5 pasos en Synthesis | 0.2.2 | 3h |

**Criterios de aceptacion:**
- IR → archivos reales compilables
- ReactGenerator produce componentes JSX con Tailwind classes
- PrismaGenerator produce schema validable con `prisma validate`
- NestJSGenerator produce controladores con decoradores correctos
- DockerGenerator produce docker-compose que levanta el stack
- Codigo formateado con Prettier

**Tests:** `test_react_generator.py`, `test_prisma_generator.py`,
`test_nestjs_generator.py`, `test_docker_generator.py`,
`test_code_formatter.py`, `test_generator_factory.py`

### 3.3 Eliminar Scaffold

**Objetivo:** Deprecar `scaffold.sh` y `templates/`.

**Tareas:**

| # | Tarea | Depende de | Estimacion |
|---|-------|-----------|------------|
| 3.3.1 | Verificar que todos los templates actuales tienen equivalente en generadores | 3.2.3-3.2.8 | 2h |
| 3.3.2 | Mover templates legacy a `templates/archive/` | 3.3.1 | 1h |
| 3.3.3 | Agregar warning en scaffold.sh: "DEPRECATED — use synthesis" | — | 1h |
| 3.3.4 | Actualizar tests que usan scaffold para que usen synthesis | 3.3.1 | 4h |

---

## FASE 4 — Output Validator + UI Generator + Refinamiento (Semanas 37-48)

### 4.1 Output Validator

**Objetivo:** Verificar codigo generado antes de entregar al usuario.

**Archivo:** `agentic_pipeline/nodes/validator.py`

**Implementacion:**
- **Patron Chain of Responsibility**: Cadena de validadores:
  1. `SyntaxValidator` — linter especifico (eslint, prisma validate)
  2. `TypeChecker` — TypeScript strict mode / pyright
  3. `IntegrationValidator` — imports correctos, no missing deps
  4. `SecurityScanner` — detecta secretos, SQL injection, XSS
  5. `FormatValidator` — Prettier dry-run
- Cada validador puede producir: `PASS`, `WARNING`, `ERROR`
- Si cualquier validador produce `ERROR`, la entrega se detiene y se
  retroalimenta al synthesis para regenerar.

**Tareas:**

| # | Tarea | Depende de | Estimacion |
|---|-------|-----------|------------|
| 4.1.1 | Definir ValidationResult, ValidationLevel | 0.2.1 | 1h |
| 4.1.2 | Implementar abstract class Validator (Chain of Responsibility base) | 0.2.2 | 2h |
| 4.1.3 | Implementar SyntaxValidator (wraps eslint, prettier --check) | 4.1.2 | 4h |
| 4.1.4 | Implementar TypeChecker (wraps tsc --noEmit) | 4.1.2 | 4h |
| 4.1.5 | Implementar IntegrationValidator (check imports) | 4.1.2 | 3h |
| 4.1.6 | Implementar SecurityScanner (regex + trufflehog wrapper) | 4.1.2 | 6h |
| 4.1.7 | Implementar OutputValidator (arma cadena y ejecuta) | 4.1.3-4.1.6 | 4h |
| 4.1.8 | Integrar como nodo LangGraph | 0.1.5, 4.1.7 | 2h |
| 4.1.9 | Loop de 5 pasos en Validator | 0.2.2 | 2h |

**Criterios de aceptacion:**
- Codigo con error sintactico → ERROR → se rechaza entrega
- Codigo valido → PASS → se entrega
- Modo warning permite entrega con advertencia

**Tests:** `test_syntax_validator.py`, `test_type_checker.py`,
`test_security_scanner.py`, `test_validator_chain.py`

### 4.2 UI Generator

**Objetivo:** Generar componentes frontend con diseno responsive,
accesible y animado.

**Archivo:** `agentic_pipeline/nodes/ui_generator.py`

**Implementacion:**
- **Patron Builder**: `UIComponentBuilder` construye paso a paso:
  1. `buildStructure()` → HTML/JSX structure
  2. `applyStyles()` → Tailwind classes + CSS custom
  3. `addBehavior()` → event handlers, state hooks
  4. `addAccessibility()` → ARIA labels, roles, focus
  5. `addAnimations()` → CSS transitions, Framer Motion
- **Design System Token Registry**: colores, tipografia, spacing,
  breakpoints predefinidos (paleta moderna SaaS)
- **Responsive Engine**: genera clases responsive (sm:, md:, lg:) y
  CSS Grid/Flexbox layouts

**Tareas:**

| # | Tarea | Depende de | Estimacion |
|---|-------|-----------|------------|
| 4.2.1 | Definir DesignTokens (colores, tipografia, spacing, breakpoints) | 0.2.1 | 3h |
| 4.2.2 | Implementar UIComponentBuilder con 5 pasos | 4.2.1 | 8h |
| 4.2.3 | Implementar ResponsiveEngine | 4.2.2 | 6h |
| 4.2.4 | Implementar AccessibilityInjector | 4.2.2 | 4h |
| 4.2.5 | Implementar AnimationInjector (CSS transitions + Framer Motion) | 4.2.2 | 6h |
| 4.2.6 | Implementar template components: Form, Table, Chart, Navbar, Sidebar, Modal | 4.2.2-4.2.5 | 12h |
| 4.2.7 | Integrar UI Generator con ReactGenerator (Synthesis) | 3.2.3, 4.2.6 | 4h |
| 4.2.8 | Loop de 5 pasos en UIGenerator | 0.2.2 | 2h |

**Criterios de aceptacion:**
- Componente "Login Form" → JSX con inputs, boton, validacion,
  ARIA labels, y animacion de submit
- Componente "Stats Table" → tabla responsive con sort, estilo SaaS
- Paleta de colores moderna y coherente entre componentes

**Tests:** `test_ui_builder.py`, `test_responsive_engine.py`,
`test_accessibility_injector.py`, `test_component_templates.py`

### 4.3 Feedback Loop y Aprendizaje

**Objetivo:** Implementar el ciclo de mejora continua (paso 5 de cada
etapa + circuito global entre sesiones).

**Archivo:** `agentic_pipeline/feedback_loop.py`

**Implementacion:**
- Cada etapa registra metricas en `StageMetrics`: tiempo, errores,
  confianza, patrones detectados
- `GlobalFeedbackLoop` consolida metricas entre sesiones:
  - Ajusta pesos del lexer (palabras frecuentes → mayor prioridad)
  - Refina reglas gramaticales (patrones nuevos)
  - Cachea IRs exitosos
  - Ajusta prompt del LLM planner

**Tareas:**

| # | Tarea | Depende de | Estimacion |
|---|-------|-----------|------------|
| 4.3.1 | Implementar StageMetrics collector | 0.2.2 | 3h |
| 4.3.2 | Implementar GlobalFeedbackLoop | 4.3.1 | 6h |
| 4.3.3 | Implementar persistencia de metricas (SQLite o JSON) | 4.3.2 | 4h |

---

## FASE 5 — Integracion y Beta (Semanas 49-52)

### 5.1 Integracion Final del Pipeline

**Tareas:**

| # | Tarea | Depende de | Estimacion |
|---|-------|-----------|------------|
| 5.1.1 | Conectar todos los nodos en el StateGraph | 0.1.5, todos los anteriores | 8h |
| 5.1.2 | Implementar entrada CLI (`./agentic --prompt "...") | 5.1.1 | 4h |
| 5.1.3 | Implementar streaming de progreso (cada etapa notifica) | 5.1.1 | 6h |
| 5.1.4 | Implementar output formatter (JSON, terminal, archivos) | 5.1.1 | 4h |

### 5.2 Beta Testing con el Prompt del Acortador

**Tareas:**

| # | Tarea | Depende de | Estimacion |
|---|-------|-----------|------------|
| 5.2.1 | Ejecucion completa del pipeline con el prompt objetivo | 5.1.1 | 1d |
| 5.2.2 | Validacion manual del codigo generado | 5.2.1 | 2d |
| 5.2.3 | Iteracion de ajustes (bugs, calidad de codigo) | 5.2.2 | 1s |
| 5.2.4 | Documentacion de lecciones aprendidas | 5.2.3 | 1d |

### 5.3 Documentacion Final

| # | Tarea | Depende de | Estimacion |
|---|-------|-----------|------------|
| 5.3.1 | Documentar API completa del pipeline | 5.1.1 | 4h |
| 5.3.2 | Escribir guia de uso con ejemplos | 5.1.1 | 4h |
| 5.3.3 | Escribir guia para crear nuevos generadores | 3.2.1 | 3h |

---

## Mapa de Dependencias entre Componentes

```
RequirementDecomposer (1.1)
  ↓
Preprocessor (1.2) ← depende de dominio detectado
  ↓
Lexer (1.3)
  ↓
Parser (2.1)
  ↓
SemanticAnalyzer (2.2) ← usa SymbolTable
  ↓
IRGenerator (2.3) ← Composite, Builder
  ↓
Planner (3.1) ← Command, Template Method
  ↓
Synthesis (3.2) ← Abstract Factory, Visitor
  ├── ReactGenerator
  ├── NextJSGenerator
  ├── TailwindGenerator
  ├── PrismaGenerator
  ├── NestJSGenerator
  └── DockerGenerator
  ↓
UIGenerator (4.2) ← Builder (integra con ReactGenerator)
  ↓
OutputValidator (4.1) ← Chain of Responsibility
  ↓
OutputFormatter (5.1.4)
```

Dependencias clave:
- Fase 1 debe completarse antes de Fase 2 (Lexer → Parser)
- Fase 2 debe completarse antes de Fase 3 (IR → Planner → Synthesis)
- Fase 3 debe completarse antes de Fase 4 (Synthesis → Validator)
- UI Generator (4.2) puede empezar en paralelo con Fase 3

---

## Resumen de Esfuerzo

| Fase | Componentes | Tareas | Estimacion | Tests |
|------|------------|--------|------------|-------|
| 0 | Fundacion tecnica | 10 | 4 semanas | 5 |
| 1 | RequirementDecomposer + Preprocessor + Lexer | 30 | 8 semanas | 12 |
| 2 | Parser + Semantic + IR | 33 | 12 semanas | 16 |
| 3 | Planner + Synthesis + Scaffold removal | 27 | 12 semanas | 12 |
| 4 | Validator + UI Generator + Feedback | 19 | 12 semanas | 10 |
| 5 | Integracion + Beta + Docs | 8 | 4 semanas | — |
| **Total** | | **127** | **52 semanas** | **55+** |

**Nota:** Las tareas dentro de cada fase pueden paralelizarse. Por
ejemplo, Semantic Analyzer y Parser pueden desarrollarse en paralelo
dentro de Fase 2, reduciendo el tiempo total estimado.

---

## Riesgos y Planes de Contingencia

| Riesgo | Plan de Contingencia |
|--------|---------------------|
| LangGraph no escala al grafo completo | Dividir en sub-grafos por fase con orquestador padre |
| LLM Planner produce planes invalidos | HeuristicPlanner como fallback obligatorio; validacion post-plan |
| Generacion codigo con errores sintacticos | Validador de output detiene entrega; loop de regeneracion (max 3) |
| UI Generator diseno antiestetico | Design tokens configurables; tema claro/oscuro por defecto |
| Scope creep | Congelar dominio web SaaS los primeros 12 meses; backlog separado |
| Costo API LLM alto | Cache de planes; modelo pequeno (GPT-4o-mini) para tareas rutinarias |

---

## Checklist de Calidad por Componente

Cada componente debe cumplir antes de considerarse completo:

- [ ] Syntax check / linter pasa
- [ ] Type hints correctos
- [ ] Tests unitarios (cobertura >80%)
- [ ] Tests de integracion con mock del stage anterior/siguiente
- [ ] Loop de 5 pasos implementado
- [ ] Errores manejados gracefulmente (sin crashes)
- [ ] Logging de entrada/salida
- [ ] Documentacion basica (docstring + README)
- [ ] Integracion con LangGraph StateGraph probada
