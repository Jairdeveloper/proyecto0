---
id: 099
area: DEV
type: PROP
module: AGENT_CORE
version: 2.0
status: IMPLEMENTED
tags:
  - proposal
  - agent-vision
  - nivel-0
  - nivel-1
  - nivel-2
  - nivel-3
  - multiagente
  - nlp-local
  - tool-registry
  - world-model
summary: >-
  Propuesta de realineamiento conceptual de RECPL organizada por niveles
  de capacidad agente (N0-N3). Cada nivel define comportamientos concretos,
  componentes a construir y criterios de aceptacion. N0 es el pipeline
  actual (simbolico-determinista). N1 anade herramientas, memoria y loop.
  N2 anade NLP profundo (spaCy, SentenceTransformers, WordNet), GoalTree
  Planner y WorldModel. N3 es la vision multiagente colaborativa.
keywords:
  - proposal
  - agent-vision
  - nivel-0
  - nivel-1
  - nivel-2
  - nivel-3
  - multiagente
  - nlp-local
  - spacy
  - sentence-transformers
  - wordnet
  - tool-registry
  - world-model
  - goal-tree-planner
  - agente-autonomo
changelog:
  - version: '2.0'
    date: 2026-06-16
    description: >-
      Reestructuracion completa organizada por niveles agente N0-N3.
      Cada nivel especifica comportamiento esperado, componentes a
      construir y criterios de aceptacion verificables.
  - version: '1.0'
    date: 2026-06-16
    description: Propuesta de realineamiento conceptual a sistema agente autonomo
---

# 099_PROP_DEV_AGENT_VISION_1_0_DRAFT v2.0

## Resumen

Realineamiento conceptual de RECPL organizado por **niveles de capacidad
agente** (N0 → N1 → N2 → N3). Cada nivel define:

1. **Comportamiento esperado** — que debe poder hacer el sistema
2. **Componentes a construir** — que archivos/clases se anaden o modifican
3. **Criterios de aceptacion** — pruebas concretas que verifican el nivel
4. **Estado actual** — que partes ya existen vs. que falta

El cambio es de *frame* y de capacidades, no de reescritura. La
arquitectura actual del pipeline (10 stages, StateGraph) se mantiene y
se profundiza en cada nivel.

```
N0 ── Motor Central de Razonamiento (simbolico-determinista)
 │     10 stages, 4 gramaticas, 6 herramientas de generacion
 │
N1 ── Solucionador Conectado (herramientas + memoria + loop)
 │     ToolRegistry, ConversationalMemory, AgentLoop
 │
N2 ── Solucionador Estrategico (NLP profundo + planificacion)
 │     spaCy, SentenceTransformers, WordNet, GoalTreePlanner, WorldModel
 │
N3 ── Sistema Multiagente Colaborativo (especializacion)
       Agentes especializados, supervisor, bus de contexto compartido
```

Cada nivel se prueba y valida antes de pasar al siguiente. El proyecto
avanza solo cuando el nivel actual cumple todos sus criterios.

---

## Principios de construccion

1. **NLP local sin APIs externas** — cero dependencia de Anthropic,
   OpenAI o cualquier servicio cloud. Todo corre en CPU local.
2. **Hibrido simbolico-estadistico** — gramaticas Lark para sintaxis
   determinista, embeddings para semantica estadistica, spaCy para
   anotacion linguistica.
3. **Tool set generico** — el agente opera sobre el sistema de archivos
   y puede extenderse a otros entornos (APIs, DBs, navegador) mediante
   ToolRegistry.
4. **Scaffolding es una herramienta mas, no el proposito** — la
   generacion de codigo NestJS/Prisma se mantiene como
   `tool_generate` para test E2E y utilidad practica.
5. **Cada nivel es autonomo** — N1 funciona sin N2, N2 funciona sin N3.
   Se puede hacer release al completar cada nivel.

---

## Nivel 0: Motor Central de Razonamiento

### Comportamiento esperado

El sistema procesa una instruccion en lenguaje natural y produce una
salida estructurada usando solo reglas deterministicas (gramaticas,
patrones, templates). Opera sin herramientas externas, sin memoria
conversacional y sin interaccion con el entorno mas alla de leer la
entrada y escribir la salida.

```
INPUT: "crea un modulo de pagos con NestJS"
  ↓
[ Perception ]  → intent classifier (regex) + preprocessor (filtros)
[ Reasoning  ]  → lexer (DFA) + parser (Lark) + semantic (symbol table)
                   + IR generator (canonical IR) + planner (pasos fijos)
[ Execution  ]  → synthesis (orchestrator) + generators (6 targets)
                   + validator (chain of responsibility)
  ↓
OUTPUT: archivos scaffolding en modules/pagos/
```

### Componentes existentes

| Componente | Archivo | Estado |
|-----------|---------|--------|
| Intent stage | `nodes/intent_stage.py` | COMPLETO — clasificador por keywords |
| Preprocessor | `nodes/preprocessor.py` | COMPLETO — 7 filtros en cadena |
| Lexer | `nodes/lexer.py` | COMPLETO — DFA + trie multi-word |
| Parser | `nodes/parser.py` | COMPLETO — Lark + fallback AST plano |
| Semantic analyzer | `nodes/semantic_analyzer.py` | COMPLETO — visitor + symbol table |
| IR generator | `nodes/ir_generator.py` | COMPLETO — IR tree + 3 serializadores |
| Planner | `nodes/planner.py` | COMPLETO — plan fijo por tipo de comando |
| Synthesis | `nodes/synthesis.py` | COMPLETO — GeneratorFactory + orchestrator |
| UI generator | `nodes/ui_generator.py` | COMPLETO — builder pattern |
| Validator | `nodes/validator.py` | COMPLETO — chain of responsibility |
| Feedback loop | `feedback_loop.py` | COMPLETO — metricas + ajuste |
| 4 gramaticas Lark | `grammars/` | COMPLETO — project, ui, data, infra |
| 6 generadores | `generators/` | COMPLETO — NestJS, Prisma, React, NextJS, Tailwind, Docker |
| Tests | `tests/` | 524 tests, todos pasando |

### Capacidades comprobadas

- Parsear patrones conocidos de lenguaje natural (4 dominios)
- Validar semanticamente el AST (symbol table, type checking)
- Generar scaffolding NestJS/Prisma/React/etc. desde IR
- Producir metricas por stage (via feedback_loop)
- 524 tests, ruff 0 errores, pipeline < 2s en prompt tipico

### Limitaciones

- No recuerda conversaciones anteriores
- Una sola entrada → una sola salida (sin loop)
- Clasificador por regex: no detecta parafrasis, no mide confianza
- Sin POS tagging, sin dependencias gramaticales
- Plan fijo por tipo de comando, sin verificacion post-ejecucion
- Sin representacion del estado del entorno (filesystem, etc.)

### Criterios de aceptacion (YA CUMPLIDOS)

- [x] `ruff check compiler-bot/agentic_pipeline/` = 0 errores
- [x] `python -m pytest tests/ -q` = 524+ tests pasando
- [x] `agentic --prompt "crea un modulo de pagos"` produce salida estructurada
- [x] `agentic --metrics table` muestra resumen del pipeline

---

## Nivel 1: Solucionador de Problemas Conectado

### Comportamiento esperado

El sistema se convierte en un agente funcional al conectarse y utilizar
herramientas externas. Ya no esta limitado a su conocimiento interno:
puede ejecutar una secuencia de acciones para recopilar y procesar
informacion del entorno (sistema de archivos, shell, dialogos con el
usuario).

El agente recibe una instruccion, la procesa, ejecuta acciones
(leyendo/escribiendo archivos, ejecutando comandos, preguntando al
usuario), observa los resultados y decide si necesita mas iteraciones.

```
INPUT: "crea un modulo de autenticacion"
  ↓
AgentLoop.iteracion 1:
  percibe → razona → planifica → ejecuta(tool_generate)
  ↓ observa: archivos creados en modules/auth/
  ↓ ¿objetivo cumplido? → si → responde
  ↓ no → refina plan → iteracion 2
```

### Lo que distingue N1 de N0

| Aspecto | N0 | N1 |
|---------|----|----|
| Herramientas | Solo generadores de codigo | ToolRegistry con herramientas extensibles |
| Memoria | Ninguna | ConversationalMemory (persistente JSON) |
| Loop | Una pasada lineal | AgentLoop (percibe → ejecuta → observa → decide) |
| Dialogo | Sin interaccion | `ask_user` tool para clarificacion |
| Renombres | Nombres de compilador | Nombres de agente (perception_unit, reasoning_engine, action_executor) |

### Que construir

#### 1.1 Renombrar componentes (alineacion conceptual)

| Actual | Nuevo | Justificacion |
|--------|-------|---------------|
| `intent_stage.py` | `perception_unit.py` | Percibe la intencion del usuario |
| `planner.py` | `reasoning_engine.py` | Razona sobre el IR |
| `synthesis.py` | `action_executor.py` | Ejecuta acciones |
| `PipelineOrchestrator` | `AgentOrchestrator` | El orquestador es el agente |
| `generators/` | `tools/` | Son herramientas, no solo generadores |

**Detalle:** Solo renombres de archivos, clases y referencias. La logica
interna NO cambia. Los imports se actualizan. Se anaden imports
compatibles hacia atras donde sea necesario.

#### 1.2 ToolRegistry y tools portables

**Problema:** Hoy las herramientas de generacion estan acopladas al
pipeline. No hay forma de que el agente decida "que herramienta usar"
en tiempo de ejecucion.

**Solucion:** Portar el patron `ToolRegistry` del shell
(`agent-robot/tools/tool_registry.sh`) a Python.

```python
class Tool(ABC):
    """Una herramienta que el agente puede ejecutar."""
    name: str
    description: str
    parameters: list[Parameter]

    @abstractmethod
    async def execute(self, params: dict, world: WorldModel) -> ToolResult: ...

class ToolRegistry:
    """Registro central de herramientas. Inspirado en tool_registry.sh."""
    _tools: dict[str, Tool]

    def register(self, tool: Tool) -> None: ...
    def get_tool(self, name: str) -> Tool: ...
    def list_available(self, context: str) -> list[Tool]: ...
    async def execute(self, name: str, params: dict) -> ToolResult: ...
```

**Herramientas iniciales a portar del shell:**

| Tool | Shell origen | Funcion |
|------|-------------|---------|
| `generate_code` | `generators/` (existente) | Genera scaffolding NestJS/Prisma/etc. |
| `read_file` | `tool_read_file.sh` | Lee contenido de archivos |
| `write_file` | `tool_write_file.sh` | Escribe/modifica archivos |
| `run_command` | `tool_run_command.sh` | Ejecuta comandos shell |
| `search_code` | `tool_search_code.sh` | Busca patrones en el codigo |
| `ask_user` | (dialogo en agent.sh) | Pide clarificacion al usuario |
| `explain` | `tool_respond.sh` | Explica conceptos del sistema |

#### 1.3 ConversationalMemory

**Problema:** El shell `memory.sh` persiste contexto en JSON pero el
pipeline Python no tiene memoria entre invocaciones.

**Solucion:** Portar `memory.sh` a Python.

```python
class ConversationalMemory:
    """Memoria persistente del agente. Inspirada en memory.sh."""

    def __init__(self, storage_dir: str = ".recpl_memory"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.current_session = self._load_or_create()

    def remember(self, key: str, value: Any) -> None: ...
    def recall(self, key: str) -> Any: ...
    def get_recent(self, limit: int = 10) -> list[dict]: ...
    def list_sessions(self) -> list[str]: ...
    def export(self, fmt: str = "json") -> str: ...
```

**Decision de implementacion:** Formato JSON (como shell), no SQLite.
Razon: simplicidad, portabilidad, compatibilidad con sesiones existentes
del shell.

#### 1.4 AgentLoop

**Problema:** El pipeline ejecuta una sola pasada. No hay iteracion.

**Solucion:** Portar el loop principal de `recpl.sh` a Python.

```python
class AgentLoop:
    """Loop agente: percibe → razona → ejecuta → observa → decide."""

    def __init__(self):
        self.orchestrator = AgentOrchestrator(...)
        self.tools = ToolRegistry()
        self.memory = ConversationalMemory()
        self.max_iterations = 5

    async def run(self, prompt: str) -> AgentOutput:
        iteration = 0
        context = {"history": self.memory.get_recent()}

        while iteration < self.max_iterations:
            output = await self.orchestrator.run(prompt, context)

            if output.status == "completed":
                self.memory.record(prompt, output)
                return output

            if output.status == "needs_clarification":
                prompt = await self.tools.execute(
                    "ask_user", {"question": output.clarification_prompt},
                )
                context["history"].append(
                    {"role": "user", "content": prompt},
                )
                iteration += 1
                continue

            if output.status == "action_executed":
                observation = self._observe(output.action_result)
                if observation["success"] and not output.needs_followup:
                    self.memory.record(prompt, output)
                    return output
                prompt = self._refine_plan(output, observation)
                iteration += 1

        return AgentOutput(status="max_iterations_reached", ...)
```

**Referencia directa:** `compiler-bot/recpl.sh` lines 70-130 (loop
principal con `do ... while`, `recpl_loop()`, manejo de errores).
`compiler-bot/agent-robot/agent.sh` lines 40-80 (ciclo
`classify → execute → respond → log`).

### Criterios de aceptacion N1

- [ ] `ToolRegistry` registra y ejecuta minimo 5 herramientas
- [ ] `tool_read_file` lee archivos del sistema de archivos
- [ ] `tool_write_file` escribe archivos en el sistema de archivos
- [ ] `ask_user` permite dialogo bidireccional cuando el score de
      clasificacion es < 0.6
- [ ] `ConversationalMemory` persiste y recupera contexto entre
      invocaciones (verificable via `list_sessions`)
- [ ] `AgentLoop` ejecuta hasta N iteraciones y termina con
      `completed` o `max_iterations_reached`
- [ ] `ruff check .` = 0 errores
- [ ] Test suite: 540+ tests

---

## Nivel 2: Solucionador Estrategico de Problemas

### Comportamiento esperado

En este nivel, las capacidades del agente se expanden a planificacion
estrategica, asistencia proactiva y auto-mejora. La ingenieria de
contexto —seleccionar, empaquetar y gestionar la informacion mas
relevante para cada paso— es la habilidad fundamental.

- **Percepcion enriquecida:** spaCy anade POS tagging, dependencias
  gramaticales, lemmas y NER a los tokens. El AST ya no es solo
  texto plano, sino texto anotado linguisticamente.
- **Clasificacion semantica:** SentenceTransformers reemplaza regex.
  Detecta intenciones por similitud de embeddings, no por palabras
  exactas. Mide confianza y pide clarificacion cuando es baja.
- **Desambiguacion:** WordNet + algoritmo de Lesk resuelve significados
  ambiguos ("modulo" = software vs. matematica).
- **Planificacion estrategica:** GoalTreePlanner descompone objetivos
  complejos en subobjetivos con verificacion post-ejecucion y
  replanificacion automatica en caso de fallo.
- **WorldModel:** El agente mantiene una representacion interna del
  estado del entorno (archivos, decisiones, restricciones) que
  actualiza con cada accion.
- **Ingenieria de contexto:** Cada etapa recibe solo la informacion
  relevante para su funcion. El agente decide que contexto empaquetar
  y pasar a cada herramienta.

```
INPUT: "crea un sistema de autenticacion"
  ↓
[ Percepcion enriquecida ]
  spaCy → tokens con POS/dep/lemma/NER
  SentenceTransformers → intent=CREATE (score=0.94)
  WordNet → desambiguacion: "autenticacion" → security.domain
  ↓
[ Razonamiento ]
  GoalTreePlanner.decompose("sistema de autenticacion", world)
    Goal: build_auth_system
      → crear_entidad_usuario (verify: schema tiene User)
      → crear_modulo_auth     (verify: existe auth.module.ts)
      → crear_controlador_login (verify: login endpoint)
  WorldModel.query("existe modules/auth/?") → No
  ↓
[ Ejecucion con ingenieria de contexto ]
  iteration 1: tool_generate({"target": "prisma", "entity": "User"})
    → WorldModel.apply_action({"type": "create", "path": "schema.prisma"})
    → verify: schema.prisma contiene "model User" → OK
  iteration 2: tool_generate({"target": "nestjs", "module": "auth"})
    → WorldModel.apply_action({"type": "create", "path": "modules/auth/"})
    → verify: auth.module.ts existe → OK
  ↓
[ Respuesta ]
  "Sistema de autenticacion creado. Archivos generados:
   - schema.prisma (modelo User con campos)
   - modules/auth/auth.module.ts
   - modules/auth/auth.controller.ts
   - modules/auth/auth.service.ts"
```

### Que construir

#### 2.1 spaCy como preprocesador semantico

**Donde:** `nodes/preprocessor.py` — los filtros actuales se mantienen,
spaCy se anade como etapa opcional que enriquece el output.

```python
class SpacyProcessor:
    """Procesador NLP con spaCy. Carga lazy: no afecta inicio si no se usa."""
    _nlp = None

    @classmethod
    def get_nlp(cls):
        if cls._nlp is None:
            import spacy
            cls._nlp = spacy.load("es_core_news_sm")
        return cls._nlp

    def process(self, text: str) -> dict:
        doc = self.get_nlp()(text)
        return {
            "tokens": [
                {"text": t.text, "pos": t.pos_, "lemma": t.lemma_,
                 "dep": t.dep_, "head": t.head.text}
                for t in doc
            ],
            "entities": [
                {"text": ent.text, "label": ent.label_}
                for ent in doc.ents
            ],
            "sentences": [str(s) for s in doc.sents],
        }
```

**Anotaciones que aporta:**

| Anotacion | Utilidad |
|-----------|----------|
| `pos_` (VERB, NOUN, PROPN) | Distinguir acciones de entidades |
| `dep_` (dobj, nsubj) | Relaciones: "crea" VERBO → "modulo" OBJETO |
| `lemma_` | Normalizar: "crea/crear/creado" → "crear" |
| `ent_type_` (ORG, PRODUCT) | Detectar NestJS, Prisma, PostgreSQL |
| `doc.sents` | Dividir comandos multi-oracion |

#### 2.2 Clasificador con SentenceTransformers

**Donde:** Reemplaza el clasificador por regex en `intent_stage.py`
(renombrado a `perception_unit.py` en N1).

**Modelo:** `paraphrase-multilingual-MiniLM-L12-v2` (80MB, 512-dim)

**Arquitectura:**

```
SentenceTransformers (clasificador primario)
    ↓ score > 0.7
Valida con gramatica Lark
    ↓ valido
Planifica y ejecuta
    ↓
Si score < 0.6 → ask_user("No entendi completamente. Querias decir...?")
Si 0.6 ≤ score ≤ 0.7 → ejecuta pero informa confianza baja
```

**Beneficios sobre regex:**
- Detecta parafrasis ("haz un modulo" = "crea un modulo")
- Mide confianza numerica
- Soporta N idiomas sin cambiar codigo
- Nueva intencion = 3-4 ejemplos, no nueva regex
- Inference < 50ms en CPU

#### 2.3 Desambiguacion con WordNet

**Donde:** `nodes/parser.py` — cuando un token aparece en multiples
gramaticas, se desambigua antes de seleccionar gramatica.

```python
def disambiguate_term(term: str, context: list[str]) -> dict:
    """Algoritmo de Lesk: synset mas probable segun contexto."""
    sentence = " ".join(context)
    synset = lesk(sentence, term, lang="spa")
    if synset:
        return {
            "term": term,
            "synset": synset.name(),
            "definition": synset.definition(),
            "domain": infer_domain(synset),  # software | mathematics | legal
        }
    return {"term": term, "synset": None, "domain": "unknown"}
```

#### 2.4 GoalTreePlanner (planificacion estrategica)

**Donde:** Reemplaza o extiende `nodes/planner.py` (renombrado a
`reasoning_engine.py` en N1).

```python
@dataclass
class Goal:
    id: str
    description: str
    status: Literal["pending", "in_progress", "completed", "failed", "blocked"]
    dependencies: list[str]
    subtasks: list[Goal]
    verification_criteria: list[str]  # condiciones que prueban exito
    result: Any = None

class GoalTreePlanner:
    """Planificador estrategico con descomposicion y verificacion."""

    def decompose(self, objective: str, world: WorldModel) -> Goal:
        """Objetivo abstracto → arbol de subobjetivos con dependencias."""
        plan = self._retrieve_similar_plan(objective)
        if plan:
            return self._instantiate(plan, world)
        return self._plan_from_scratch(objective, ...)

    def verify(self, goal: Goal, world: WorldModel) -> bool:
        """Verifica post-ejecucion contra criteria."""
        return all(self._check_criterion(c, world) for c in goal.verification_criteria)

    def replan(self, goal: Goal, world: WorldModel, error: str) -> Goal:
        """Si un subobjetivo falla, replanifica automaticamente."""
```

**Diferencia con planner actual:**

| Actual (N0 planner) | GoalTreePlanner (N2) |
|---------------------|----------------------|
| Plan fijo por tipo de comando | Plan dinamico + busqueda en memoria de planes exitosos |
| Pasos secuenciales sin verificacion | Cada paso tiene verification_criteria |
| No maneja fallos | Replanificacion en fallo |
| Sin dependencias entre pasos | DAG de dependencias |
| Sin criterio de finalizacion | Verificacion explicita post-ejecucion |

#### 2.5 WorldModel

**Donde:** Archivo nuevo `agentic_pipeline/world_model.py`.

```python
@dataclass
class FileNode:
    path: str
    file_type: Literal["file", "directory"]
    hash: str | None = None
    created_by: str | None = None  # goal_id que lo creo
    timestamp: str | None = None

@dataclass
class DecisionRecord:
    goal_id: str
    action: str
    rationale: str
    timestamp: str

@dataclass
class WorldModel:
    files: dict[str, FileNode]
    decisions: list[DecisionRecord]
    goals: list[Goal]
    constraints: list[dict]  # preferencias aprendidas del usuario

    def initialize(self, scan_path: str = ".") -> None:
        """Escanea el directorio de trabajo y construye estado inicial."""

    def apply_action(self, action: ExecutedAction) -> "WorldDelta":
        """Actualiza estado segun accion ejecutada. Retorna el cambio."""

    def query(self, question: str) -> str:
        """Responde preguntas sobre el estado: 'existe modules/auth/?'"""

    def snapshot(self) -> dict:
        """Estado actual para serializar a JSON (memoria/debug)."""
```

**Ciclo de vida:**

1. **Inicializacion:** al iniciar sesion, escanea el directorio de
   trabajo y construye `files` y `project_tree`
2. **Actualizacion:** cada accion reporta un delta que `apply_action()`
   incorpora. El WorldModel siempre refleja el estado real del entorno
3. **Consulta:** el `reasoning_engine` pregunta al WorldModel antes de
   planificar para evitar redundancias o conflictos
4. **Persistencia:** se serializa junto con `ConversationalMemory` para
   preservar estado entre sesiones

#### 2.6 Ingenieria de contexto

**Concepto:** No toda la informacion disponible es relevante para cada
paso. El agente selecciona, empaqueta y gestiona el contexto optimo
para cada etapa del pipeline.

**Implementacion:** Cada stage recibe un `context_window` que contiene
solo la informacion relevante para su funcion:

```python
@dataclass
class ContextWindow:
    """Contexto optimizado para un stage especifico."""
    relevant_history: list[dict]   # solo historial pertinente
    world_snapshot: dict           # estado actual relevante
    task_focus: str                # el objetivo especifico de este paso

def build_context(stage: str, full_context: dict, world: WorldModel) -> ContextWindow:
    """Construye el contexto optimo para cada stage."""
    if stage == "perception":
        return ContextWindow(
            relevant_history=full_context["history"][-3:],
            world_snapshot={},
            task_focus="parse user intent",
        )
    elif stage == "reasoning":
        return ContextWindow(
            relevant_history=[],
            world_snapshot=world.snapshot(),
            task_focus="decompose goal and verify constraints",
        )
    elif stage == "execution":
        return ContextWindow(
            relevant_history=[],
            world_snapshot=world.query_filesystem(),
            task_focus="generate code per plan",
        )
```

### Criterios de aceptacion N2

- [ ] spaCy anade POS, dependencias, lemmas y NER al output del
      preprocessor. Verificable via debugger trace.
- [ ] SentenceTransformers clasifica intencion con score > 0.7 para
      prompts tipicos. Verificable con 10 parafrasis de cada intencion.
- [ ] WordNet desambigua terminos ambiguos ("modulo", "entidad",
      "interfaz") con al menos 80% de precision en tests.
- [ ] GoalTreePlanner descompone "crea un sistema de autenticacion"
      en ≥ 3 subobjetivos con verification_criteria.
- [ ] GoalTreePlanner replanifica cuando un subobjetivo falla
      (ej: falta dependencia npm).
- [ ] WorldModel.initialize() escanea el directorio y reporta
      archivos existentes.
- [ ] WorldModel.apply_action() actualiza estado y el cambio es
      visible en WorldModel.query().
- [ ] ContextWindow entrega contexto distinto y optimizado por stage.
- [ ] `ruff check .` = 0 errores
- [ ] Test suite: 570+ tests

---

## Nivel 3: Sistema Multiagente Colaborativo

### Comportamiento esperado

En este nivel se produce un cambio de paradigma: de un unico agente
generalista a un **equipo de especialistas que trabajan de forma
coordinada**, reflejando la estructura de una organizacion humana.

Cada agente tiene un rol especifico y un conjunto de herramientas
adaptadas a su funcion. Un agente supervisor coordina, delega tareas
y resuelve conflictos.

```
Usuario: "crea un sistema de autenticacion"
  ↓
[ Supervisor Agent ]
  ↓ analiza requerimiento
  ↓ delega sub-tareas a especialistas

┌── Perception Agent ──┐    ┌── Parser Agent ──┐
│  spaCy + ST + WordNet│    │  Lark + Semantic  │
│  "autenticacion" →   │    │  "entity User" →  │
│  security intent     │    │  valid AST        │
└────────┬─────────────┘    └────────┬──────────┘
         │                           │
         ↓                           ↓
┌── Planner Agent ──────┐    ┌── Execution Agent ──┐
│  GoalTreePlanner      │    │  ToolRegistry       │
│  descompone objetivo  │    │  genera archivos    │
└────────┬─────────────┘    └────────┬─────────────┘
         │                           │
         └──────────┬───────────────┘
                    ↓
┌── Validator Agent ────┐
│  verifica cada archivo│
│  contra criteria      │
└────────┬─────────────┘
         │
         ↓
[ Supervisor Agent ]
  ↓ consolida resultados
  ↓ responde al usuario
```

### Que construir

#### 3.1 Agentes especializados

Cada agente extiende una clase base `Agent`:

```python
class Agent(ABC):
    name: str
    role: str
    tools: ToolRegistry  # subconjunto del ToolRegistry global

    @abstractmethod
    async def process(self, task: Task, context: SharedContext) -> TaskResult: ...

class PerceptionAgent(Agent):
    name = "perception"
    role = "analizar y clasificar la entrada del usuario"
    tools = ToolRegistry(["spacy_processor", "sentence_classifier", "wordnet"])

class PlannerAgent(Agent):
    name = "planner"
    role = "descomponer objetivos en planes ejecutables"
    tools = ToolRegistry(["goal_tree_planner", "world_model_query"])

class ExecutionAgent(Agent):
    name = "execution"
    role = "ejecutar herramientas sobre el entorno"
    tools = ToolRegistry(["generate_code", "read_file", "write_file", "run_command"])

class ValidatorAgent(Agent):
    name = "validator"
    role = "verificar que las acciones cumplen los criterios"
    tools = ToolRegistry(["file_checker", "syntax_validator"])

class SupervisorAgent(Agent):
    name = "supervisor"
    role = "coordinar, delegar y consolidar"
    tools = ToolRegistry(["task_delegator", "conflict_resolver"])
```

#### 3.2 SharedContext bus

Los agentes se comunican a traves de un bus de contexto compartido:

```python
@dataclass
class SharedContext:
    """Estado compartido entre agentes del sistema multiagente."""
    original_prompt: str
    world: WorldModel
    conversation: ConversationalMemory
    task_queue: list[Task]
    results: dict[str, TaskResult]
    conflicts: list[Conflict]

    def publish(self, agent: str, topic: str, data: Any) -> None: ...
    def subscribe(self, agent: str, topic: str) -> AsyncIterator: ...
    def get_snapshot(self) -> dict: ...
```

### Criterios de aceptacion N3

- [ ] SupervisorAgent delega tareas a ≥ 3 agentes especializados
- [ ] PerceptionAgent + PlannerAgent + ExecutionAgent completan un
      goal complejo en equipo
- [ ] SharedContext propaga estado entre agentes correctamente
- [ ] ValidatorAgent detecta fallos y SupervisorAgent replanifica
- [ ] `ruff check .` = 0 errores
- [ ] Test suite: 600+ tests

---

## Hoja de ruta

| Nivel | Sprint | Objetivo | Entregables | Tests |
|-------|--------|----------|-------------|-------|
| **N0** | S16 (completado) | Motor de Razonamiento | Pipeline 10 stages, 4 gramaticas, 6 generadores | 524 |
| **N1** | S17 | Solucionador Conectado | Renombres + ToolRegistry + ConversationalMemory + AgentLoop | 540+ |
| **N2.1** | S18 | Percepcion Enriquecida | spaCy + SentenceTransformers + WordNet | 555+ |
| **N2.2** | S19 | Planificacion Estrategica | GoalTreePlanner + WorldModel + Context Engineering | 570+ |
| **N3** | S20 | Sistema Multiagente | Agentes especializados + Supervisor + SharedContext | 600+ |

---

## Preguntas de alineacion resueltas

### 1. Output scaffolding — mantener o eliminar?

**Mantener** como `tool_generate` dentro del ToolRegistry. Es util para
test E2E, demo tangible, y como una herramienta mas del agente. La
generacion de codigo es una accion entre muchas, no el proposito.

### 2. Enfoque hibrido o puramente simbolico?

**Hibrido.** Cada capa del sistema usa la tecnologia adecuada:

| Capa | Tecnologia | Por que |
|------|-----------|---------|
| Sintaxis superficial | spaCy (POS, dependencias) | Reglas linguisticas comprobadas |
| Clasificacion semantica | SentenceTransformers | Embeddings capturan significado, no solo palabras |
| Desambiguacion | WordNet + Lesk | Conocimiento lexico estructurado |
| Estructura formal | Lark grammars | Garantizan validez sintactica |
| Razonamiento | GoalTreePlanner + reglas | Planificacion verificable, no estadistica |

### 3. Tool set generico o solo filesystem?

**Generico.** ToolRegistry permite registrar herramientas para cualquier
entorno. Inicialmente: filesystem + shell + dialogo. Arquitectura lista
para: HTTP, DBs, navegador, Docker en el futuro.

---

## Resumen del esfuerzo

| Componente | Archivos | Nivel | Esfuerzo |
|-----------|----------|-------|----------|
| Renombrar componentes | ~15 archivos | N1 | 0.5 dias |
| ToolRegistry + tools | 5-7 archivos nuevos | N1 | 2 dias |
| ConversationalMemory | 1 archivo nuevo | N1 | 0.5 dias |
| AgentLoop | 1 archivo nuevo | N1 | 1 dia |
| spaCy preprocessor | Modificar preprocessor.py | N2 | 1 dia |
| SentenceTransformers classifier | Modificar perception_unit.py | N2 | 1 dia |
| WordNet disambiguation | Modificar parser.py | N2 | 1 dia |
| GoalTreePlanner | 2 archivos nuevos | N2 | 3 dias |
| WorldModel | 1-2 archivos nuevos | N2 | 2 dias |
| Context engineering | Modificar orchestrator.py | N2 | 1.5 dias |
| Multiagente (Supervisor + especialistas) | 5-7 archivos nuevos | N3 | 4 dias |
| SharedContext bus | 1 archivo nuevo | N3 | 1 dia |
| **Total** | | | **~18.5 dias** |
