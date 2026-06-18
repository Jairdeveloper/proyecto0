---
id: "P03"
area: "DEV"
type: "PLAN"
module: "RECPL_PATTERNS"
version: "1.0"
status: "DRAFT"
tags: ["plan", "refactor", "patterns", "mediator", "adapter", "visitor", "gof"]
summary: "Plan de implementacion para formalizar 4 patrones GoF en el sistema RECPL: Mediator (agentes), Adapter (agente↔pipeline), Visitor canónico (AST), y Strategy/Visitor (AST→IR)"
changelog:
  - version: "1.0"
    date: "2026-06-18"
    author: "Arquitecto Senior"
    description: "Version inicial — plan de refactor de patrones formales para Agentes, AST y comunicacion Agente↔Pipeline"
---

# Plan de Implementacion — Refactor de Patrones Formales (Mediator, Adapter, Visitor)

> **Base:** Analisis de codigo fuente en `agents/` (6 archivos), `nodes/ast_nodes.py`, `nodes/parser.py`, `nodes/semantic_analyzer.py`  
> **Problema:** 4 patrones GoF existen como implementaciones parciales/ad-hoc — sin interfaz formal, sin contratos, con acoplamiento entre nodos y serializacion  
> **Objetivo:** Formalizar Mediator, Adapter, Visitor canonico, y Strategy/Visitor para exportacion IR  
> **Esfuerzo total estimado:** ~24h / 2 semanas

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Mediator — Comunicacion entre Agentes](#2-mediator--comunicacion-entre-agentes)
3. [Adapter — Agente como PipelineStage](#3-adapter--agente-como-pipelinestage)
4. [Visitor Canonico — AST Nodes](#4-visitor-canonico--ast-nodes)
5. [IRExportVisitor — AST a IR via Visitor](#5-irexportvisitor--ast-a-ir-via-visitor)
6. [Roadmap y Dependencias](#6-roadmap-y-dependencias)
7. [Presupuesto Total](#7-presupuesto-total)

---

## 1. Resumen Ejecutivo

Actualmente 4 componentes del sistema tienen patrones GoF incompletos o ad-hoc:

| Componente | Estado Actual | Problema | Patron Propuesto |
|-----------|--------------|----------|-----------------|
| Agentes (`agents/`) | Pub/sub via `SharedContext.publish("topic_string", data)` | Agentes conocen strings de otros agentes, sin contratos ni tipos | **Mediator** — `IAgentMediator` con `send()`, `register()`, mensajes tipados |
| Agente↔Pipeline | `SupervisorAgent._process_with_chain()` llama a `ChainOrchestrator.run()` directamente | Unico puente, no integrado con StateGraph | **Adapter** — `AgentStageAdapter(PipelineStage)` envuelve Agent como Stage |
| AST (`ast_nodes.py`) | Visitor implicito via `isinstance` en `SemanticAnalyzer` | Violacion OCP: nuevo visitor requiere modificar el analizador | **Visitor canonico** — `ASTNode.accept(visitor)`, `IASTVisitor` |
| AST→IR (`to_ir()`) | `to_ir()` inline en cada ASTNode | SRP violation, nuevo formato = modificar N nodos | **Visitor** — `IRExportVisitor(IASTVisitor)` separa serializacion |

---

## 2. Mediator — Comunicacion entre Agentes

### 2.1 Diagnostico

**Flujo actual de comunicacion entre agentes:**

```
PerceptionAgent ──publish("perception_result")──→ SharedContext
                                                      │
ReasoningAgent  ──subscribe("perception_result")──┘  │
                  ──publish("reasoning_result")───────┤
                                                      │
ExecutionAgent  ──subscribe("reasoning_result")─────┘ │
                  ──publish("execution_result")────────┤
                                                       │
ValidatorAgent  ──subscribe("reasoning_result")──────┘ │
                  ──subscribe("execution_result")───────┘
                  ──publish("validation_result")
```

**Problemas:**
1. Cada agente conoce los topic strings de otros agentes (`"perception_result"`)
2. No hay contrato de tipos — `payload` es `dict[str, Any]` sin estructura
3. No hay trazabilidad — no hay `correlation_id` para seguir un request completo
4. `SharedContext` mezcla pub/sub con almacenamiento de datos (CQRS violation)

### 2.2 Solucion: AgentMediator

#### 2.2.1 Interfaz y Mensajes

```python
# agents/agent_mediator.py — NUEVO

from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Any


@dataclass
class AgentMessage:
    """Mensaje tipado entre agentes via Mediator."""
    sender: str
    topic: str
    payload: Any
    correlation_id: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class PerceptionResult:
    raw: str
    intent: dict
    entities: list
    slots: dict
    confidence: float


@dataclass
class ReasoningResult:
    goal_id: str
    goal_description: str
    subtasks: list[dict]
    verification_criteria: list[str]


@dataclass
class ExecutionResult:
    files: list[dict]
    errors: list[str]


@dataclass
class ValidationResult:
    all_passed: bool
    criteria_checks: list[dict]
    total_criteria: int
    passed_criteria: int


class IAgentMediator(ABC):
    """Interface del Mediator — agentes solo conocen esta interfaz."""

    @abstractmethod
    def register(self, agent: "Agent") -> None: ...

    @abstractmethod
    def send(self, message: AgentMessage) -> None: ...

    @abstractmethod
    def request(self, message: AgentMessage, timeout: float = 30.0) -> Any: ...
```

#### 2.2.2 Mediator Concreto

```python
class AgentMediator(IAgentMediator):
    """Mediator concreto: enruta mensajes entre agentes sin que se conozcan."""

    def __init__(self, event_bus: EventBus | None = None):
        self._event_bus = event_bus or EventBus()
        self._agents: dict[str, Agent] = {}
        self._subscriptions: dict[str, list[str]] = {}  # topic -> [agent_names]

    def register(self, agent: Agent) -> None:
        self._agents[agent.name] = agent
        if hasattr(agent, "subscriptions"):
            for topic in agent.subscriptions:
                self._subscriptions.setdefault(topic, []).append(agent.name)
                self._event_bus.subscribe(topic, lambda t, d: self._route(t, d))

    def send(self, message: AgentMessage) -> None:
        self._event_bus.publish(message.topic, message)

    def _route(self, topic: str, data: Any) -> None:
        for agent_name in self._subscriptions.get(topic, []):
            agent = self._agents.get(agent_name)
            if agent and hasattr(agent, "on_message"):
                agent.on_message(data)
```

#### 2.2.3 Cambios en Agentes

**Cada agente ahora:**
- Recibe `mediator: IAgentMediator` en lugar de `context: SharedContext`
- Declara `subscriptions: list[str]` como class variable — topics que escucha
- Implementa `on_message(msg: AgentMessage)` para recibir mensajes
- Usa `self.mediator.send(AgentMessage(...))` en lugar de `self.context.publish(...)`

```python
# Antes (PerceptionAgent)
self.context.publish("perception_result", analysis)

# Despues
self.mediator.send(AgentMessage(
    sender="perception_agent",
    topic="perception.completed",
    payload=PerceptionResult(
        raw=text,
        intent=analysis.get("intent", {}),
        entities=analysis.get("entities", []),
        slots=analysis.get("slots", {}),
        confidence=analysis.get("confidence", 0.0),
    ),
    correlation_id=task.id,
))
```

```python
# Antes (ReasoningAgent)
perception = self.context.subscribe("perception_result") or {}

# Despues
class ReasoningAgent(Agent):
    subscriptions = ["perception.completed"]
    
    def on_message(self, msg: AgentMessage) -> None:
        if isinstance(msg.payload, PerceptionResult):
            self._last_perception = msg.payload
```

#### 2.2.4 Topics Estandarizados

| Topic | Payload Type | Producer | Consumer(s) |
|-------|-------------|----------|-------------|
| `perception.completed` | `PerceptionResult` | PerceptionAgent | ReasoningAgent |
| `reasoning.completed` | `ReasoningResult` | ReasoningAgent | ExecutionAgent, ValidatorAgent |
| `execution.completed` | `ExecutionResult` | ExecutionAgent | ValidatorAgent |
| `validation.completed` | `ValidationResult` | ValidatorAgent | SupervisorAgent |
| `task.failed` | `dict` (error info) | Cualquiera | SupervisorAgent |

#### 2.2.5 SupervisorAgent Refactorizado

```python
class SupervisorAgent(Agent):
    subscriptions = ["validation.completed", "task.failed"]

    async def process(self, task: Task) -> TaskResult:
        # Ya no llama agent.process() directamente
        # Envia mensajes via mediator y reacciona a respuestas
        self.mediator.send(AgentMessage(
            sender="supervisor",
            topic="task.assigned",
            payload={"task": task.description},
            correlation_id=task.id,
        ))
        # El mediator enruta al agente correcto
        # El resultado llega via on_message()
        return await self._wait_for_result(task.id)
```

#### 2.2.6 Archivos Afectados

| Archivo | Accion | Cambio |
|---------|--------|--------|
| `agents/agent_mediator.py` | **NUEVO** | `IAgentMediator`, `AgentMediator`, `AgentMessage`, dataclasses tipadas |
| `agents/base_agent.py` | **MODIFICAR** | Agent recibe `mediator` en init, agrega `subscriptions`, `on_message()` opcional |
| `agents/perception_agent.py` | **MODIFICAR** | `publish()` → `mediator.send()`, eliminar referencias a `context.publish` |
| `agents/reasoning_agent.py` | **MODIFICAR** | `subscribe()` → `on_message()`, usar `PerceptionResult` tipado |
| `agents/execution_agent.py` | **MODIFICAR** | igual que reasoning_agent |
| `agents/validator_agent.py` | **MODIFICAR** | igual, recibe `ReasoningResult` + `ExecutionResult` tipados |
| `agents/supervisor_agent.py` | **MODIFICAR** | usar mediator para orquestar, eliminar llamadas directas a `agent.process()` |
| `tests/test_agent_mediator.py` | **NUEVO** | 10+ tests: registro, envio, enrutamiento, mensajes tipados |
| `tests/test_agent_communication.py` | **NUEVO** | 5+ tests: integracion completa con mediator |

#### 2.2.7 Esfuerzo: **10h**

---

## 3. Adapter — Agente como PipelineStage

### 3.1 Diagnostico

**Unico puente actual:** `SupervisorAgent._process_with_chain()` llama a `ChainOrchestrator.run()`. No hay manera de ejecutar un Agent dentro del `StateGraph` de `AgentOrchestrator`. Las dos arquitecturas estan desconectadas (problema P1 del reporte de arquitectura).

### 3.2 Solucion: AgentStageAdapter

```python
# agents/agent_stage_adapter.py — NUEVO

from ..base_stage import PipelineStage
from ..state_models import StageContext, StageOutput, ActionPlan


class AgentStageAdapter(PipelineStage):
    """Adapter: envuelve un Agent como PipelineStage.

    Permite ejecutar agentes dentro del StateGraph de AgentOrchestrator.
    act() delega en agent.process(task) y mapea TaskResult → StageOutput.

    Uso:
        adapter = AgentStageAdapter(ctx, perception_agent)
        output = await adapter.execute(input_data)
    """

    name = "agent_adapter"

    def __init__(
        self,
        context: StageContext,
        agent: Agent,
        agent_name: str = "",
    ):
        super().__init__(context)
        self._agent = agent
        self._agent_name = agent_name or agent.name
        self._task: Task | None = None

    def receive_mission(self, input_data: object) -> None:
        # Convierte StageContext.input_data en Task.params
        params = {"input_data": input_data}
        if isinstance(input_data, dict):
            params.update(input_data)
        self._task = Task(
            id=f"{self._agent_name}_{id(self)}",
            description=str(input_data)[:200],
            agent=self._agent_name,
            params=params,
        )

    def act(self, plan: ActionPlan) -> StageOutput:
        if not self._task:
            return StageOutput(
                stage=self.context.stage,
                output_data={},
                success=False,
                error="No task created in receive_mission",
            )

        result = await self._agent.process(self._task)
        return StageOutput(
            stage=self.context.stage,
            output_data=result.data if isinstance(result.data, dict) else {"result": result.data},
            success=result.success,
            error=result.error,
            metrics={"agent": self._agent_name, "task_id": self._task.id},
        )
```

### 3.3 Uso en Orchestrator

```python
# En orchestrator.py, modo agente:
perception_adapter = AgentStageAdapter(ctx, perception_agent)
reasoning_adapter = AgentStageAdapter(ctx, reasoning_agent)
execution_adapter = AgentStageAdapter(ctx, execution_agent)
validator_adapter = AgentStageAdapter(ctx, validator_agent)

# Se registran en el StateGraph como nodos
orchestrator.add_node("perception", perception_adapter.execute)
orchestrator.add_node("reasoning", reasoning_adapter.execute)
# ...
```

### 3.4 Archivos Afectados

| Archivo | Accion | Cambio |
|---------|--------|--------|
| `agents/agent_stage_adapter.py` | **NUEVO** | `AgentStageAdapter(PipelineStage)` |
| `orchestrator.py` | **MODIFICAR** | Agregar metodo `build_from_agents()` que construye StateGraph usando adapters |
| `tests/test_agent_stage_adapter.py` | **NUEVO** | Adapter produce StageOutput correcto, mapea errores, test con agente mock |

### 3.5 Esfuerzo: **4h**

---

## 4. Visitor Canonico — AST Nodes

### 4.1 Diagnostico

**Estado actual de ASTNode:**

```python
class ASTNode(ABC):
    def evaluate(self) -> dict: ...     # logica de negocio
    def validate(self) -> list[str]: ... # validacion
    def to_ir(self) -> dict: ...        # serializacion

# SemanticAnalyzer usa visitor implicito:
if isinstance(node, ProjectNode):
    self._visit_project(node)
elif isinstance(node, PageNode):
    self._visit_page(node)
```

**Problemas:**
1. **SRP:** Cada nodo combina evaluacion, validacion y serializacion
2. **OCP:** Nuevo visitor (ej. `CodeGenerationVisitor`) requiere modificar `semantic_analyzer.py` o agregar metodo a cada nodo
3. **Acoplamiento:** `to_ir()` en cada nodo impide cambiar formato de exportacion sin modificar todos los nodos
4. **`isinstance`:** El visitor implicito en SemanticAnalyzer usa pattern matching en tiempo de ejecucion

### 4.2 Solucion: Visitor Canonico de GoF

#### 4.2.1 Interfaz del Visitor

```python
# nodes/ast_visitor.py — NUEVO

from abc import ABC, abstractmethod
from typing import Any


class IASTVisitor(ABC):
    """Interface del Visitor para AST nodes.

    Cada subclase implementa visit_* para cada tipo de nodo.
    Nuevos visitors = nuevas subclases, sin modificar nodos (OCP).
    """

    @abstractmethod
    def visit_project(self, node: "ProjectNode") -> Any: ...

    @abstractmethod
    def visit_page(self, node: "PageNode") -> Any: ...

    @abstractmethod
    def visit_component(self, node: "ComponentNode") -> Any: ...

    @abstractmethod
    def visit_entity(self, node: "EntityNode") -> Any: ...

    @abstractmethod
    def visit_infra(self, node: "InfraNode") -> Any: ...


class TreeWalkingVisitor(IASTVisitor):
    """Base para visitors que recorren el arbol recursivamente."""

    def visit_project(self, node: "ProjectNode") -> Any:
        for child in node.children:
            child.accept(self)

    def visit_page(self, node: "PageNode") -> Any:
        for child in node.children:
            child.accept(self)

    def visit_component(self, node: "ComponentNode") -> Any:
        pass  # leaf

    def visit_entity(self, node: "EntityNode") -> Any:
        pass  # leaf

    def visit_infra(self, node: "InfraNode") -> Any:
        pass  # leaf
```

#### 4.2.2 ASTNode Modificado

```python
# nodes/ast_nodes.py — MODIFICAR

class ASTNode(ABC):
    def __init__(self, name: str = ""):
        self.name = name
        self.children: list[ASTNode] = []
        self.parent: ASTNode | None = None

    def add(self, child: ASTNode) -> None:
        self.children.append(child)
        child.parent = self

    @abstractmethod
    def accept(self, visitor: IASTVisitor) -> Any: ...
    # Eliminar: evaluate(), validate(), to_ir()


class ProjectNode(ASTNode):
    def accept(self, visitor: IASTVisitor) -> Any:
        return visitor.visit_project(self)


class PageNode(ASTNode):
    def accept(self, visitor: IASTVisitor) -> Any:
        return visitor.visit_page(self)


class ComponentNode(ASTNode):
    def __init__(self, name: str, component_type: str):
        super().__init__(name)
        self.component_type = component_type

    def accept(self, visitor: IASTVisitor) -> Any:
        return visitor.visit_component(self)


class EntityNode(ASTNode):
    def __init__(self, name: str):
        super().__init__(name)
        self.attributes: list[dict[str, str]] = []

    def add_attribute(self, attr_name: str, attr_type: str) -> None:
        self.attributes.append({"name": attr_name, "type": attr_type})

    def accept(self, visitor: IASTVisitor) -> Any:
        return visitor.visit_entity(self)


class InfraNode(ASTNode):
    def __init__(self, name: str, infra_type: str):
        super().__init__(name)
        self.infra_type = infra_type
        self.resources: list[dict[str, Any]] = []

    def add_resource(self, resource: dict[str, Any]) -> None:
        self.resources.append(resource)

    def accept(self, visitor: IASTVisitor) -> Any:
        return visitor.visit_infra(self)
```

#### 4.2.3 Visitors Concretos

```python
# nodes/validation_visitor.py — NUEVO

class ValidationVisitor(TreeWalkingVisitor):
    """Reemplaza validate() en cada ASTNode."""

    def __init__(self):
        self.errors: list[str] = []

    def visit_page(self, node: PageNode) -> Any:
        if not node.children:
            self.errors.append(f"Page '{node.name}' has no components")
        super().visit_page(node)

    def visit_entity(self, node: EntityNode) -> Any:
        if not node.attributes:
            self.errors.append(f"Entity '{node.name}' has no attributes")
        super().visit_entity(node)


# nodes/evaluation_visitor.py — NUEVO

class EvaluationVisitor(TreeWalkingVisitor):
    """Reemplaza evaluate() en cada ASTNode."""

    def __init__(self):
        self._result: dict = {}

    def visit_project(self, node: ProjectNode) -> Any:
        pages = []
        for child in node.children:
            result = child.accept(self)
            if result:
                pages.append(result)
        self._result = {"type": "project", "pages": pages}
        return self._result

    def visit_page(self, node: PageNode) -> Any:
        components = []
        for child in node.children:
            result = child.accept(self)
            if result:
                components.append(result)
        return {"type": "page", "name": node.name, "components": components}

    def visit_component(self, node: ComponentNode) -> Any:
        return {"type": "component", "name": node.name, "component_type": node.component_type}

    def visit_entity(self, node: EntityNode) -> Any:
        return {"type": "entity", "name": node.name, "attributes": node.attributes}

    def visit_infra(self, node: InfraNode) -> Any:
        return {"type": "infra", "name": node.name, "infra_type": node.infra_type}
```

#### 4.2.4 SemanticAnalyzer Refactorizado

```python
# nodes/semantic_analyzer.py — MODIFICAR

class SemanticAnalysisVisitor(TreeWalkingVisitor):
    """Visitor que reemplaza el analizador semantico actual.
    
    Antes: isinstance checks + metodos sueltos
    Ahora: visitor canonico con visit_* por tipo de nodo.
    """

    def __init__(self, symbol_table: SymbolTable, type_registry: TypeRegistry):
        super().__init__()
        self.symbols = symbol_table
        self.types = type_registry

    def visit_project(self, node: ProjectNode) -> Any:
        self.symbols.define("$project", {"name": node.name})
        super().visit_project(node)

    def visit_page(self, node: PageNode) -> Any:
        self.symbols.enter_scope()
        self.types.validate("ui", "page", node)
        super().visit_page(node)
        self.symbols.exit_scope()

    def visit_component(self, node: ComponentNode) -> Any:
        self.symbols.define(node.name, {"type": "component", "component_type": node.component_type})
        self.types.validate("ui", "component", node)

    def visit_entity(self, node: EntityNode) -> Any:
        self.symbols.define(node.name, {"type": "entity", "attributes": node.attributes})
        self.types.validate("data", "entity", node)
```

#### 4.2.5 Archivos Afectados

| Archivo | Accion | Cambio |
|---------|--------|--------|
| `nodes/ast_visitor.py` | **NUEVO** | `IASTVisitor`, `TreeWalkingVisitor` |
| `nodes/validation_visitor.py` | **NUEVO** | `ValidationVisitor(TreeWalkingVisitor)` |
| `nodes/evaluation_visitor.py` | **NUEVO** | `EvaluationVisitor(TreeWalkingVisitor)` |
| `nodes/ast_nodes.py` | **MODIFICAR** | Agregar `accept(visitor)`, eliminar `evaluate()`, `validate()`, `to_ir()` |
| `nodes/semantic_analyzer.py` | **MODIFICAR** | `SemanticAnalysisVisitor(IASTVisitor)` reemplaza `isinstance` logic |
| `nodes/parser.py` | **MODIFICAR** | Usar `EvaluationVisitor` en lugar de `node.evaluate()` |
| `tests/test_ast_visitor.py` | **NUEVO** | 10+ tests: accept, tree walking, validation, evaluation |

### 4.3 Esfuerzo: **6h**

---

## 5. IRExportVisitor — AST a IR via Visitor

### 5.1 Diagnostico

Actualmente cada ASTNode tiene `to_ir()` que sabe convertir su propio estado a un dict IR. Esto:
1. Viola SRP — el nodo sabe de si mismo Y de como serializarse a IR
2. Viola OCP — nuevo formato de exportacion (YAML, DOT, JSON Schema) requiere modificar cada nodo
3. Duplica logica — `to_ir()` en ProjectNode y `to_ir()` en PageNode tienen estrutura similar

### 5.2 Solucion: IRExportVisitor

```python
# nodes/ir_export_visitor.py — NUEVO

class IRExportVisitor(IASTVisitor):
    """Visitor que serializa AST a dict IR (reemplaza to_ir()).
    
    Separa la responsabilidad de serializacion de los nodos.
    Para exportar a otro formato, crear otro visitor.
    """

    def __init__(self, builder: IRBuilder | None = None):
        self._builder = builder or IRBuilder()

    def visit_project(self, node: ProjectNode) -> dict:
        children = [child.accept(self) for child in node.children]
        ir_dict = {"node_type": "project", "children": children}
        return self._builder.build(ir_dict)

    def visit_page(self, node: PageNode) -> dict:
        children = [child.accept(self) for child in node.children]
        return {"node_type": "page", "name": node.name, "children": children}

    def visit_component(self, node: ComponentNode) -> dict:
        return {
            "node_type": "component",
            "name": node.name,
            "component_type": node.component_type,
        }

    def visit_entity(self, node: EntityNode) -> dict:
        return {
            "node_type": "entity",
            "name": node.name,
            "attributes": node.attributes,
        }

    def visit_infra(self, node: InfraNode) -> dict:
        return {
            "node_type": "infra",
            "name": node.name,
            "infra_type": node.infra_type,
            "resources": node.resources,
        }


# Uso en IRGenerator:
visitor = IRExportVisitor()
ir_dict = ast_root.accept(visitor)
```

### 5.3 Futuros Visitors de Exportacion

```python
class DOTExportVisitor(IASTVisitor):
    """Exporta AST a formato DOT para visualizacion con Graphviz."""

    def __init__(self):
        self._lines = ["digraph AST {"]

    def visit_project(self, node: ProjectNode) -> Any:
        for child in node.children:
            child_id = child.accept(self)
            self._lines.append(f'  "{node.name}" -> "{child_id}";')
        return node.name

    def visit_page(self, node: PageNode) -> Any:
        # ...
        pass


class JSONSchemaExportVisitor(IASTVisitor):
    """Exporta entidades a JSON Schema."""
    # ...
```

### 5.4 Archivos Afectados

| Archivo | Accion | Cambio |
|---------|--------|--------|
| `nodes/ir_export_visitor.py` | **NUEVO** | `IRExportVisitor(IASTVisitor)` |
| `nodes/ast_nodes.py` | **MODIFICAR** | Solo queda `accept(visitor)`, se elimina `to_ir()` |
| `nodes/ir_generator.py` | **MODIFICAR** | `IRExportVisitor` en lugar de `node.to_ir()` |
| `tests/test_ir_export_visitor.py` | **NUEVO** | 8+ tests: exportacion produce dict identico al `to_ir()` anterior |

### 5.5 Esfuerzo: **4h**

---

## 6. Roadmap y Dependencias

### 6.1 Grafo de Dependencias

```
Visitor Canonico (6h)
  │
  ├──→ IRExportVisitor (4h)        [depende de IASTVisitor]
  │
  └──→ ValidationVisitor +         [depende de IASTVisitor]
       EvaluationVisitor (incluido en 6h)
       
Mediator (10h)                      [independiente de Visitor]
  │
  └──→ Adapter (4h)                [depende de PipelineStage, no de Visitor]

Tests Integracion (4h)              [depende de Mediator + Adapter + Visitor]
```

### 6.2 Secuencia Recomendada

```
Semana 1                    Semana 2
┌──────────────────────┐   ┌──────────────────────┐
│ Visitor Canonico      │   │ Mediator              │
│  (6h)                 │   │  (10h)                │
│                       │   │                       │
│  1. ast_visitor.py    │   │  1. agent_mediator.py │
│  2. ast_nodes.py mod  │   │  2. base_agent.py mod │
│  3. validation_visitor│   │  3. agent*.py mods    │
│  4. evaluation_visitor│   │  4. test_mediator.py  │
│  5. semantic mod      │   │                       │
│  6. parser mod        │   ├──────────────────────┤
│  7. test_ast_visitor  │   │ Adapter (4h)          │
│                       │   │                       │
├──────────────────────┤   │  1. agent_stage_adapt. │
│ IRExportVisitor (4h)  │   │  2. orchestrator mod  │
│                       │   │  3. test_adapter.py   │
│  1. ir_export_visitor │   │                       │
│  2. ir_generator mod  │   ├──────────────────────┤
│  3. test_ir_export    │   │ Tests Integracion     │
│                       │   │  (4h)                 │
└──────────────────────┘   │                       │
                           │  1. test_full_pipeline │
                           │  2. ruff + pytest      │
                           └──────────────────────┘
```

### 6.3 Hitos

| Hito | Semana | Entregable | Verificacion |
|------|--------|-----------|--------------|
| H1 | 1 | Visitor implementado | `ASTNode.accept(visitor)` funciona, `isinstance` eliminado de SemanticAnalyzer |
| H2 | 1 | IRExportVisitor | `IRExportVisitor` produce mismo dict que `to_ir()` anterior |
| H3 | 2 | Mediator implementado | Agentes se comunican via `mediator.send()`, topics tipados, zero `publish("string")` |
| H4 | 2 | Adapter implementado | `AgentStageAdapter` se ejecuta dentro de StateGraph |
| H5 | 2 | Integracion completa | `ruff check .` = 0, `pytest tests/` = todos pasan |

---

## 7. Presupuesto Total

### 7.1 Por Componente

| Componente | Archivos Nuevos | Archivos Modificados | Horas | % |
|-----------|----------------|---------------------|-------|---|
| Mediator | 2 | 6 | 10h | 42% |
| Adapter | 1 | 1 | 4h | 17% |
| Visitor Canonico | 3 | 3 | 6h | 25% |
| IRExportVisitor | 1 | 2 | 4h | 17% |
| **Total** | **7** | **12** | **24h** | **100%** |

### 7.2 Por Tipo de Trabajo

| Tipo | Horas | % |
|------|-------|---|
| Interfaces y clases nuevas | 10h | 42% |
| Refactor de archivos existentes | 8h | 33% |
| Tests | 6h | 25% |

### 7.3 Relacion con el Plan Arquitectonico Mayor

Este plan es un subconjunto de las tareas del [Plan de Refactor Arquitectonico](121_PLAN_DEV_ARCHITECTURAL_REFACTOR_1_0_DRAFT.md):

| Tarea Mayor | Ref | Se Cubre En | Horas |
|------------|-----|------------|-------|
| P1 — Agentes desconectados | P1.1-P1.4 | **Adapter** (4h) + Mediator parcial | 4/20h |
| P5 — Dos event buses | P5.1-P5.4 | **Mediator** usa EventBus unificado | 10/9h* |
| ISP — Interface Segregation | ISP1-ISP5 | **Visitor** elimina metodos sobrantes de ASTNode | 6/8h |
| OCP — Open/Closed | OC1-OC4 | **Visitor** + **IRExportVisitor** permiten extension sin modificar nodos | 4/11h |

*\*Mediator (10h) absorbe y expande P5 (9h)*

---

## Apendice A: Comparacion Antes/Despues

### A.1 Comunicacion de Agentes

```python
# ANTES
class PerceptionAgent(Agent):
    async def process(self, task):
        # ...
        self.context.publish("perception_result", {"raw": text, ...})
        
class ReasoningAgent(Agent):
    async def process(self, task):
        perception = self.context.subscribe("perception_result") or {}
        # agentes conocen el string "perception_result"

# DESPUES
class PerceptionAgent(Agent):
    async def process(self, task):
        # ...
        self.mediator.send(AgentMessage(
            sender="perception_agent",
            topic="perception.completed",
            payload=PerceptionResult(raw=text, ...),
        ))
        # no sabe quien recibe

class ReasoningAgent(Agent):
    subscriptions = ["perception.completed"]
    
    def on_message(self, msg: AgentMessage):
        if isinstance(msg.payload, PerceptionResult):
            self._last_perception = msg.payload
            # no sabe quien envio
```

### A.2 Visitor en AST

```python
# ANTES
node = ProjectNode("proyecto")
result = node.evaluate()          # SRP violation
errors = node.validate()          # SRP violation
ir = node.to_ir()                 # SRP violation

# DESPUES
node = ProjectNode("proyecto")
result = node.accept(EvaluationVisitor())
errors = node.accept(ValidationVisitor()).errors
ir = node.accept(IRExportVisitor())

# Nuevo formato? Solo nuevo visitor:
dot = node.accept(DOTExportVisitor())
```

### A.3 Adapter Agente↔Pipeline

```python
# ANTES
# No existe. Solo SupervisorAgent._process_with_chain() como bridge.

# DESPUES
ctx = StageContext(stage=Stage.INTENT, input_data="crea modulo")
adapter = AgentStageAdapter(ctx, perception_agent)
output = await adapter.execute("crea modulo")
# output es StageOutput — compatible con StateGraph
```

---

*Documento generado a partir del analisis de codigo fuente en `agents/` y `nodes/ast_nodes.py`. Fecha: 2026-06-18.*
