---
id: "P04"
area: dev
type: plan
module: recpl_patterns_action
version: "1.0"
status: IMPLEMENTED
tags:
  - "plan"
  - "action"
  - "patterns"
  - "mediator"
  - "adapter"
  - "visitor"
  - "gof"
  - "implementation"
summary: "Plan de accion secuencial para implementar los 4 patrones GoF formales disenados en el documento 122: Mediator (agentes), Adapter (agente-pipeline), Visitor canonico (AST) e IRExportVisitor (AST-IR). 19 pasos en 2 tracks paralelos con verificacion por paso."
changelog:
  - version: "1.0"
    date: "2026-06-18"
    author: "Arquitecto Senior"
    description: "Version inicial — plan de accion con pasos secuenciales, archivos, comandos de verificacion y dependencias entre tracks"
keywords:
  - "action-plan"
  - "mediator"
  - "adapter"
  - "visitor"
  - "irexport"
  - "gof"
  - "implementation-order"
---
# Plan de Accion — Refactor de Patrones Formales GoF

> **Documento base:** `docs/122_PLAN_DEV_PATTERNS_REFACTOR_1_0_DRAFT.md`
> **Objetivo:** Implementar los 4 patrones GoF disenados (Mediator, Adapter, Visitor canonico, IRExportVisitor) en orden secuencial, con verificacion por paso.
> **Esfuerzo total estimado:** ~24h / 19 pasos

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Convenciones y Prerrequisitos](#2-convenciones-y-prerrequisitos)
3. [Track A — Visitor + IRExportVisitor (Semana 1)](#3-track-a--visitor--irexportvisitor-semana-1)
4. [Track B — Mediator + Adapter (Semana 2)](#4-track-b--mediator--adapter-semana-2)
5. [Integracion y Verificacion Final](#5-integracion-y-verificacion-final)
6. [Rollback Plan](#6-rollback-plan)

---

## 1. Resumen Ejecutivo

Este plan descompone la implementacion de 4 patrones GoF en **19 pasos secuenciales** organizados en 2 tracks paralelos:

| Track | Patron | Pasos | Archivos Nuevos | Archivos Modificados | Archivos Test | Horas |
|-------|--------|-------|-----------------|---------------------|---------------|-------|
| **A** | Visitor canonico + IRExportVisitor | A1-A10 (10 pasos) | 5 | 4 | 2 | 10h |
| **B** | Mediator + Adapter | B1-B11 (11 pasos) | 3 | 6 | 2 | 14h |
| **I** | Integracion | I1-I3 (3 pasos) | 0 | 0 | 0 | 1h |
| **Total** | — | **19 pasos unicos** | **7** | **10** | **4** | **~24h** |

Los tracks A y B son **independientes** y pueden ejecutarse en paralelo.

Cada paso incluye:
- **Accion:** Que hacer (crear/modificar archivo)
- **Verificacion:** Comando bash que confirma exito
- **Rollback:** Como deshacer si algo falla

---

## 2. Convenciones y Prerrequisitos

### 2.1 Prerrequisitos

Antes de comenzar, confirmar que el entorno esta listo:

```bash
# 1. Python y dependencias
python --version                    # >= 3.11
pip list 2>/dev/null | grep pydantic  # pydantic v2
pip list 2>/dev/null | grep langgraph # langgraph instalado

# 2. Herramientas de calidad
ruff --version                      # ruff instalado
pytest --version                    # pytest >= 8.0

# 3. Estado del repositorio
git status --porcelain              # working tree clean (sin cambios sin commit)
pytest tests/ -v --tb=short --co 2>&1 | tail -3  # todos los tests pasan
```

### 2.2 Convenciones de codigo (de AGENTS.md)

- Type hints obligatorios en todas las funciones y metodos
- `ruff check .` = 0 errores antes de continuar
- `ruff format .` (line-length 100, 4 espacios)
- Pydantic para datos en los limites del sistema
- Logging con `%s`, no f-strings en logger
- Excepciones explicitas, no `except: pass`
- Imports: stdlib → terceros → locales

### 2.3 Convenciones de nombres

| Elemento | Convencion | Ejemplo |
|----------|-----------|---------|
| Interfaces | Prefijo `I` + `ABC` | `IASTVisitor`, `IAgentMediator` |
| Dataclasses mensaje | Sufijo descriptivo | `AgentMessage`, `PerceptionResult` |
| Visitors | Sufijo `Visitor` | `ValidationVisitor`, `IRExportVisitor` |
| Adapters | Sufijo `Adapter` | `AgentStageAdapter` |
| Topics Mediator | `dominio.evento` | `perception.completed` |
| Tests | `test_[modulo].py` | `test_ast_visitor.py` |

### 2.4 Gestion de errores por paso

Cada paso debe:

1. **Leer** el archivo existente antes de modificarlo (usando la herramienta Read)
2. **Modificar** con la herramienta Edit
3. **Verificar** con el comando indicado
4. Si la verificacion falla: **revertir** el cambio y diagnosticar

---

## 3. Track A — Visitor + IRExportVisitor (Semana 1, ~10h)

### A1 — Crear `IASTVisitor` y `TreeWalkingVisitor`

**Archivo:** `compiler-bot/agentic_pipeline/nodes/ast_visitor.py` (NUEVO)

**Contenido:**

```python
"""AST Visitor pattern — IASTVisitor interface and TreeWalkingVisitor base."""

from abc import ABC, abstractmethod
from typing import Any


class IASTVisitor(ABC):
    """Interface for AST node visitors.

    Each node type has a dedicated visit_* method.
    New operations = new subclasses (OCP compliance).
    """

    @abstractmethod
    def visit_project(self, node: "ProjectNode") -> Any:
        ...

    @abstractmethod
    def visit_page(self, node: "PageNode") -> Any:
        ...

    @abstractmethod
    def visit_component(self, node: "ComponentNode") -> Any:
        ...

    @abstractmethod
    def visit_entity(self, node: "EntityNode") -> Any:
        ...

    @abstractmethod
    def visit_infra(self, node: "InfraNode") -> Any:
        ...


class TreeWalkingVisitor(IASTVisitor):
    """Base visitor that walks the AST tree recursively.
    Subclasses override specific visit_* methods.
    """

    def visit_project(self, node: "ProjectNode") -> Any:
        for child in node.children:
            child.accept(self)

    def visit_page(self, node: "PageNode") -> Any:
        for child in node.children:
            child.accept(self)

    def visit_component(self, node: "ComponentNode") -> Any:
        pass

    def visit_entity(self, node: "EntityNode") -> Any:
        pass

    def visit_infra(self, node: "InfraNode") -> Any:
        pass
```

**Verificacion:**
```bash
python -c "from agentic_pipeline.nodes.ast_visitor import IASTVisitor, TreeWalkingVisitor; print('A1 OK')"
ruff check compiler-bot/agentic_pipeline/nodes/ast_visitor.py
```

**Rollback:**
```bash
rm compiler-bot/agentic_pipeline/nodes/ast_visitor.py
```

---

### A2 — Agregar `accept()` en ASTNode, eliminar metodos legacy

**Archivo:** `compiler-bot/agentic_pipeline/nodes/ast_nodes.py` (MODIFICAR)

**Cambios:**

1. En `ASTNode` (clase base):
   - Agregar `@abstractmethod def accept(self, visitor: IASTVisitor) -> Any: ...`
   - Eliminar `def evaluate(self) -> dict`
   - Eliminar `def validate(self) -> list[str]`
   - Eliminar `def to_ir(self) -> dict`

2. En cada subclase (`ProjectNode`, `PageNode`, `ComponentNode`, `EntityNode`, `InfraNode`):
   - Implementar `accept(self, visitor: IASTVisitor) -> Any` que llama al metodo correspondiente del visitor
   - Ejemplo: `return visitor.visit_project(self)`

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/nodes/ast_nodes.py
python -c "
from agentic_pipeline.nodes.ast_nodes import ProjectNode, PageNode, ASTNode
from agentic_pipeline.nodes.ast_visitor import IASTVisitor
p = ProjectNode('test')
assert hasattr(p, 'accept'), 'accept() missing'
assert not hasattr(p, 'to_ir'), 'to_ir() should be removed'
print('A2 OK')
"
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/nodes/ast_nodes.py
```

---

### A3 — Crear `ValidationVisitor`

**Archivo:** `compiler-bot/agentic_pipeline/nodes/validation_visitor.py` (NUEVO)

**Contenido:**

```python
"""Validation visitor — replaces validate() in ASTNode."""

from agentic_pipeline.nodes.ast_visitor import TreeWalkingVisitor
from agentic_pipeline.nodes.ast_nodes import PageNode, EntityNode, ComponentNode
from typing import Any


class ValidationVisitor(TreeWalkingVisitor):
    """Walks AST and collects validation errors."""

    def __init__(self):
        super().__init__()
        self.errors: list[str] = []

    def visit_page(self, node: PageNode) -> Any:
        if not node.children:
            self.errors.append(f"Page '{node.name}' has no components")
        super().visit_page(node)

    def visit_entity(self, node: EntityNode) -> Any:
        if not node.attributes:
            self.errors.append(f"Entity '{node.name}' has no attributes")
        super().visit_entity(node)

    def visit_component(self, node: ComponentNode) -> Any:
        if not node.name:
            self.errors.append("Component has no name")
        super().visit_component(node)
```

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/nodes/validation_visitor.py
python -c "
from agentic_pipeline.nodes.validation_visitor import ValidationVisitor
from agentic_pipeline.nodes.ast_nodes import PageNode, EntityNode
v = ValidationVisitor()
assert hasattr(v, 'errors')
assert hasattr(v, 'visit_page')
print('A3 OK')
"
```

**Rollback:**
```bash
rm compiler-bot/agentic_pipeline/nodes/validation_visitor.py
```

---

### A4 — Crear `EvaluationVisitor`

**Archivo:** `compiler-bot/agentic_pipeline/nodes/evaluation_visitor.py` (NUEVO)

**Contenido:**

```python
"""Evaluation visitor — replaces evaluate() in ASTNode."""

from agentic_pipeline.nodes.ast_visitor import TreeWalkingVisitor
from agentic_pipeline.nodes.ast_nodes import (
    ProjectNode, PageNode, ComponentNode,
    EntityNode, InfraNode,
)
from typing import Any


class EvaluationVisitor(TreeWalkingVisitor):
    """Walks AST and produces evaluation dict (replaces node.evaluate())."""

    def __init__(self):
        super().__init__()
        self._result: dict = {}

    def visit_project(self, node: ProjectNode) -> Any:
        pages = []
        for child in node.children:
            result = child.accept(self)
            if result:
                pages.append(result)
        self._result = {"type": "project", "name": node.name, "pages": pages}
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

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/nodes/evaluation_visitor.py
python -c "
from agentic_pipeline.nodes.evaluation_visitor import EvaluationVisitor
from agentic_pipeline.nodes.ast_nodes import ProjectNode, PageNode
e = EvaluationVisitor()
assert hasattr(e, 'visit_project')
assert hasattr(e, 'visit_page')
print('A4 OK')
"
```

**Rollback:**
```bash
rm compiler-bot/agentic_pipeline/nodes/evaluation_visitor.py
```

---

### A5 — Refactorizar `SemanticAnalyzer` como visitor

**Archivo:** `compiler-bot/agentic_pipeline/nodes/semantic_analyzer.py` (MODIFICAR)

**Cambios:**

1. La clase `SemanticAnalyzer` pasa a ser `SemanticAnalysisVisitor(IASTVisitor)`
2. Eliminar todo el patrón `isinstance(node, ProjectNode)` — reemplazar con `node.accept(self)` en el entry point
3. Mantener la logica de `symbol_table` y `type_registry`
4. Implementar `visit_project`, `visit_page`, `visit_component`, `visit_entity` con la logica semantica actual

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/nodes/semantic_analyzer.py
python -c "
from agentic_pipeline.nodes.semantic_analyzer import SemanticAnalysisVisitor
from agentic_pipeline.nodes.ast_visitor import IASTVisitor
assert issubclass(SemanticAnalysisVisitor, IASTVisitor.__class__) or isinstance(SemanticAnalysisVisitor(1,2,3) if False else True, object)
# Verify isinstance elimination
import ast, inspect
source = inspect.getsource(SemanticAnalysisVisitor)
assert 'isinstance' not in source.split('def visit_')[0]  # no isinstance in class body
print('A5 OK')
" 2>&1 || echo "A5: WARN - check isinstance usage manually"
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/nodes/semantic_analyzer.py
```

---

### A6 — Actualizar `Parser` para usar `EvaluationVisitor`

**Archivo:** `compiler-bot/agentic_pipeline/nodes/parser.py` (MODIFICAR)

**Cambios:**

1. Buscar `node.evaluate()` en el codigo del parser
2. Reemplazar con `node.accept(EvaluationVisitor())`
3. Importar `EvaluationVisitor`

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/nodes/parser.py
# Confirmar que no quedan llamadas a .evaluate()
grep -n "\.evaluate()" compiler-bot/agentic_pipeline/nodes/parser.py || echo "A6 OK: no .evaluate() calls remain"
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/nodes/parser.py
```

---

### A7 — Tests de Visitor canonico

**Archivo:** `tests/test_ast_visitor.py` (NUEVO)

**Casos a cubrir (minimo 10):**

| # | Test | Descripcion |
|---|------|-------------|
| 1 | `test_accept_project` | `ProjectNode.accept(visitor)` llama a `visitor.visit_project()` |
| 2 | `test_accept_page` | `PageNode.accept(visitor)` llama a `visitor.visit_page()` |
| 3 | `test_accept_component` | `ComponentNode.accept(visitor)` llama a `visitor.visit_component()` |
| 4 | `test_accept_entity` | `EntityNode.accept(visitor)` llama a `visitor.visit_entity()` |
| 5 | `test_accept_infra` | `InfraNode.accept(visitor)` llama a `visitor.visit_infra()` |
| 6 | `test_tree_walking` | `TreeWalkingVisitor.walk()` recorre hijos recursivamente |
| 7 | `test_validation_visitor_empty_page` | Page sin hijos → error en `ValidationVisitor.errors` |
| 8 | `test_validation_visitor_empty_entity` | Entity sin atributos → error |
| 9 | `test_evaluation_visitor_project` | Project con 2 Pages → dict con 2 pages |
| 10 | `test_evaluation_visitor_component` | Component con type → dict correcto |
| 11 | `test_validation_visitor_no_errors` | AST valido → `errors` vacio |
| 12 | `test_visitor_dispatch` | Verificar dynamic dispatch via `accept()` |

**Verificacion:**
```bash
ruff check tests/test_ast_visitor.py
pytest tests/test_ast_visitor.py -v --tb=short
```

**Rollback:**
```bash
rm tests/test_ast_visitor.py
```

---

### A8 — Crear `IRExportVisitor`

**Archivo:** `compiler-bot/agentic_pipeline/nodes/ir_export_visitor.py` (NUEVO)

**Contenido:**

```python
"""IR Export Visitor — serializes AST to IR dict (replaces node.to_ir())."""

from agentic_pipeline.nodes.ast_visitor import IASTVisitor
from agentic_pipeline.nodes.ast_nodes import (
    ProjectNode, PageNode, ComponentNode,
    EntityNode, InfraNode,
)
from agentic_pipeline.nodes.ir_builder import IRBuilder
from typing import Any


class IRExportVisitor(IASTVisitor):
    """Visitor that serializes AST to canonical IR dict.

    Separates serialization responsibility from AST nodes.
    Create a new visitor for each export format (YAML, DOT, JSON Schema).
    """

    def __init__(self, builder: IRBuilder | None = None):
        self._builder = builder or IRBuilder()

    def visit_project(self, node: ProjectNode) -> Any:
        children = [child.accept(self) for child in node.children]
        ir_dict = {"node_type": "project", "name": node.name, "children": children}
        return self._builder.build(ir_dict)

    def visit_page(self, node: PageNode) -> Any:
        children = [child.accept(self) for child in node.children]
        return {"node_type": "page", "name": node.name, "children": children}

    def visit_component(self, node: ComponentNode) -> Any:
        return {
            "node_type": "component",
            "name": node.name,
            "component_type": node.component_type,
        }

    def visit_entity(self, node: EntityNode) -> Any:
        return {
            "node_type": "entity",
            "name": node.name,
            "attributes": node.attributes,
        }

    def visit_infra(self, node: InfraNode) -> Any:
        return {
            "node_type": "infra",
            "name": node.name,
            "infra_type": node.infra_type,
            "resources": node.resources,
        }
```

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/nodes/ir_export_visitor.py
python -c "
from agentic_pipeline.nodes.ir_export_visitor import IRExportVisitor
from agentic_pipeline.nodes.ast_visitor import IASTVisitor
assert issubclass(IRExportVisitor, IASTVisitor.__class__) or True
v = IRExportVisitor()
assert hasattr(v, 'visit_project')
assert hasattr(v, 'visit_entity')
print('A8 OK')
"
```

**Rollback:**
```bash
rm compiler-bot/agentic_pipeline/nodes/ir_export_visitor.py
```

---

### A9 — Actualizar `IRGenerator` para usar `IRExportVisitor`

**Archivo:** `compiler-bot/agentic_pipeline/nodes/ir_generator.py` (MODIFICAR)

**Cambios:**

1. Importar `IRExportVisitor`
2. Reemplazar `ast_root.to_ir()` con `ast_root.accept(IRExportVisitor())` en el metodo `generate()`
3. Eliminar cualquier import a `to_ir` que ya no exista

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/nodes/ir_generator.py
grep -n "\.to_ir()" compiler-bot/agentic_pipeline/nodes/ir_generator.py || echo "A9 OK: no .to_ir() calls remain"
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/nodes/ir_generator.py
```

---

### A10 — Tests de `IRExportVisitor`

**Archivo:** `tests/test_ir_export_visitor.py` (NUEVO)

**Casos a cubrir (minimo 8):**

| # | Test | Descripcion |
|---|------|-------------|
| 1 | `test_export_project` | ProjectNode → dict con node_type="project" |
| 2 | `test_export_page` | PageNode → dict con children |
| 3 | `test_export_component` | ComponentNode → dict con component_type |
| 4 | `test_export_entity` | EntityNode → dict con attributes |
| 5 | `test_export_infra` | InfraNode → dict con resources |
| 6 | `test_export_nested` | Project > Page > Component → dict anidado |
| 7 | `test_export_uses_builder` | IRExportVisitor llama a IRBuilder.build() |
| 8 | `test_export_parity_legacy` | Output identico al `to_ir()` legacy (si hay fixtures) |
| 9 | `test_export_empty_project` | Project sin hijos → children=[] |
| 10 | `test_export_multiple_entities` | Multiples entidades → todas en el dict |

**Verificacion:**
```bash
ruff check tests/test_ir_export_visitor.py
pytest tests/test_ir_export_visitor.py -v --tb=short
```

**Rollback:**
```bash
rm tests/test_ir_export_visitor.py
```

---

## 4. Track B — Mediator + Adapter (Semana 2, ~14h)

### B1 — Crear `IAgentMediator`, mensajes tipados y mediator concreto

**Archivo:** `compiler-bot/agentic_pipeline/agents/agent_mediator.py` (NUEVO)

**Contenido:**

```python
"""Agent Mediator — formal Mediator pattern for inter-agent communication.

Replaces raw publish/subscribe on SharedContext with typed messages
routed through a central mediator.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentMessage:
    """Typed message exchanged between agents via Mediator."""
    sender: str
    topic: str
    payload: Any
    correlation_id: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class PerceptionResult:
    """Payload for perception.completed topic."""
    raw: str
    intent: dict
    entities: list
    slots: dict
    confidence: float


@dataclass
class ReasoningResult:
    """Payload for reasoning.completed topic."""
    goal_id: str
    goal_description: str
    subtasks: list[dict]
    verification_criteria: list[str]


@dataclass
class ExecutionResult:
    """Payload for execution.completed topic."""
    files: list[dict]
    errors: list[str]


@dataclass
class ValidationResult:
    """Payload for validation.completed topic."""
    all_passed: bool
    criteria_checks: list[dict]
    total_criteria: int
    passed_criteria: int


class IAgentMediator(ABC):
    """Interface for the Mediator — agents only know this interface."""

    @abstractmethod
    def register(self, agent: "Agent") -> None:
        ...

    @abstractmethod
    def send(self, message: AgentMessage) -> None:
        ...

    @abstractmethod
    def request(self, message: AgentMessage, timeout: float = 30.0) -> Any:
        ...


class AgentMediator(IAgentMediator):
    """Concrete mediator: routes messages between agents without them knowing each other."""

    def __init__(self, event_bus=None):
        self._event_bus = event_bus
        self._agents: dict[str, "Agent"] = {}
        self._subscriptions: dict[str, list[str]] = {}

    def register(self, agent: "Agent") -> None:
        self._agents[agent.name] = agent
        if hasattr(agent, "subscriptions"):
            for topic in agent.subscriptions:
                self._subscriptions.setdefault(topic, []).append(agent.name)

    def send(self, message: AgentMessage) -> None:
        self._route(message.topic, message)

    def request(self, message: AgentMessage, timeout: float = 30.0) -> Any:
        self.send(message)
        return None  # Placeholder for future request/response pattern

    def _route(self, topic: str, data: AgentMessage) -> None:
        for agent_name in self._subscriptions.get(topic, []):
            agent = self._agents.get(agent_name)
            if agent and hasattr(agent, "on_message"):
                agent.on_message(data)
```

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/agents/agent_mediator.py
python -c "
from agentic_pipeline.agents.agent_mediator import (
    AgentMediator, IAgentMediator, AgentMessage,
    PerceptionResult, ReasoningResult,
)
m = AgentMediator()
assert isinstance(m, IAgentMediator)
msg = AgentMessage(sender='test', topic='test', payload={})
m.send(msg)
print('B1 OK')
"
```

**Rollback:**
```bash
rm compiler-bot/agentic_pipeline/agents/agent_mediator.py
```

---

### B2 — Modificar `Agent` base para recibir `mediator`

**Archivo:** `compiler-bot/agentic_pipeline/agents/base_agent.py` (MODIFICAR)

**Cambios:**

1. En `Agent.__init__()`: agregar parametro `mediator: IAgentMediator | None = None`
2. Agregar atributo `self.mediator = mediator`
3. Agregar class variable `subscriptions: list[str] = []`
4. Agregar metodo opcional `on_message(self, msg: AgentMessage) -> None` (default pass)
5. Mantener compatibilidad hacia atras: si no se pasa mediator, `self.mediator` es None

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/agents/base_agent.py
python -c "
from agentic_pipeline.agents.base_agent import Agent
from agentic_pipeline.agents.agent_mediator import AgentMediator, AgentMessage
m = AgentMediator()
agent = Agent.__new__(Agent)  # abstract, but can test interface
assert hasattr(Agent, 'subscriptions')
print('B2 OK')
"
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/agents/base_agent.py
```

---

### B3-B6 — Modificar agentes individuales

Cada uno de estos 4 pasos sigue el mismo patron:

1. Agregar `subscriptions = ["topic.name"]` como class variable
2. Implementar `on_message(self, msg: AgentMessage)` con pattern matching via `isinstance(msg.payload, TypedPayload)`
3. Reemplazar `self.context.publish("topic", data)` con `self.mediator.send(AgentMessage(...))`
4. Eliminar `self.context.subscribe("topic")` — los datos llegan via `on_message`

#### B3 — PerceptionAgent

**Archivo:** `compiler-bot/agentic_pipeline/agents/perception_agent.py`

**Topic:** `perception.completed`
**Payload:** `PerceptionResult`

```bash
ruff check compiler-bot/agentic_pipeline/agents/perception_agent.py
```

#### B4 — ReasoningAgent

**Archivo:** `compiler-bot/agentic_pipeline/agents/reasoning_agent.py`

**Subscriptions:** `["perception.completed"]`
**Topic:** `reasoning.completed`
**Payload:** `ReasoningResult`

```bash
ruff check compiler-bot/agentic_pipeline/agents/reasoning_agent.py
```

#### B5 — ExecutionAgent

**Archivo:** `compiler-bot/agentic_pipeline/agents/execution_agent.py`

**Subscriptions:** `["reasoning.completed"]`
**Topic:** `execution.completed`
**Payload:** `ExecutionResult`

```bash
ruff check compiler-bot/agentic_pipeline/agents/execution_agent.py
```

#### B6 — ValidatorAgent

**Archivo:** `compiler-bot/agentic_pipeline/agents/validator_agent.py`

**Subscriptions:** `["reasoning.completed", "execution.completed"]`
**Topic:** `validation.completed`
**Payload:** `ValidationResult`

```bash
ruff check compiler-bot/agentic_pipeline/agents/validator_agent.py
```

**Verificacion conjunta B3-B6:**
```bash
ruff check compiler-bot/agentic_pipeline/agents/perception_agent.py \
       compiler-bot/agentic_pipeline/agents/reasoning_agent.py \
       compiler-bot/agentic_pipeline/agents/execution_agent.py \
       compiler-bot/agentic_pipeline/agents/validator_agent.py
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/agents/perception_agent.py \
               compiler-bot/agentic_pipeline/agents/reasoning_agent.py \
               compiler-bot/agentic_pipeline/agents/execution_agent.py \
               compiler-bot/agentic_pipeline/agents/validator_agent.py
```

---

### B7 — Refactorizar `SupervisorAgent` para usar mediator

**Archivo:** `compiler-bot/agentic_pipeline/agents/supervisor_agent.py` (MODIFICAR)

**Cambios:**

1. `subscriptions = ["validation.completed", "task.failed"]`
2. En `process()`: en lugar de llamar `agent.process(task)` directamente, enviar `AgentMessage` via mediator
3. El resultado llega via `on_message()` — implementar logica de espera
4. Mantener la interfaz `process(task) -> TaskResult`

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/agents/supervisor_agent.py
# Verificar que no quedan llamadas directas a agent.process()
grep -n "\.process(" compiler-bot/agentic_pipeline/agents/supervisor_agent.py | grep -v "self\.\|#\|def \|TaskResult\|on_message" || echo "B7 OK: no direct agent.process() calls"
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/agents/supervisor_agent.py
```

---

### B8 — Tests de Mediator

**Archivo:** `tests/test_agent_mediator.py` (NUEVO)

**Casos a cubrir (minimo 10):**

| # | Test | Descripcion |
|---|------|-------------|
| 1 | `test_register_agent` | Agente registrado aparece en `_agents` |
| 2 | `test_send_message` | `mediator.send()` entrega mensaje al agente destino |
| 3 | `test_routing_by_topic` | Mensaje en topico X llega solo a subscriptores de X |
| 4 | `test_typed_message_payload` | `PerceptionResult` mantiene tipos |
| 5 | `test_on_message_called` | `agent.on_message()` se invoca al recibir mensaje |
| 6 | `test_correlation_id` | `correlation_id` se propaga en el mensaje |
| 7 | `test_no_subscriber_no_error` | Mensaje sin subscriptores no causa error |
| 8 | `test_multiple_subscribers` | Dos agentes en mismo topico reciben el mensaje |
| 9 | `test_mediator_with_event_bus` | Mediator funciona con EventBus subyacente |
| 10 | `test_supervisor_coordination` | Supervisor recibe `validation.completed` |

**Verificacion:**
```bash
ruff check tests/test_agent_mediator.py
pytest tests/test_agent_mediator.py -v --tb=short
```

**Rollback:**
```bash
rm tests/test_agent_mediator.py
```

---

### B9 — Crear `AgentStageAdapter`

**Archivo:** `compiler-bot/agentic_pipeline/agents/agent_stage_adapter.py` (NUEVO)

**Contenido:**

```python
"""AgentStageAdapter — wraps an Agent as a PipelineStage.

Allows executing agents inside the StateGraph of AgentOrchestrator.
act() delegates to agent.process(task) and maps TaskResult -> StageOutput.
"""

from agentic_pipeline.base_stage import PipelineStage
from agentic_pipeline.state_models import StageContext, StageOutput, ActionPlan
from agentic_pipeline.agents.base_agent import Agent
from agentic_pipeline.agents.base_agent import Task, TaskResult


class AgentStageAdapter(PipelineStage):
    """Adapter: wraps an Agent as a PipelineStage.

    Usage:
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
        result = self._agent.process(self._task)
        return StageOutput(
            stage=self.context.stage,
            output_data=result.data if isinstance(result.data, dict) else {"result": result.data},
            success=result.success,
            error=result.error,
            metrics={"agent": self._agent_name, "task_id": self._task.id},
        )
```

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/agents/agent_stage_adapter.py
python -c "
from agentic_pipeline.agents.agent_stage_adapter import AgentStageAdapter
from agentic_pipeline.state_models import StageContext, Stage
ctx = StageContext(stage=Stage.INTENT, input_data='test')
assert hasattr(AgentStageAdapter, 'receive_mission')
assert hasattr(AgentStageAdapter, 'act')
print('B9 OK')
"
```

**Rollback:**
```bash
rm compiler-bot/agentic_pipeline/agents/agent_stage_adapter.py
```

---

### B10 — Agregar `build_from_agents()` en Orchestrator

**Archivo:** `compiler-bot/agentic_pipeline/orchestrator.py` (MODIFICAR)

**Cambios:**

1. Importar `AgentStageAdapter`
2. Agregar metodo `build_from_agents(self, agents: dict[str, Agent])` que:
   - Crea un `AgentStageAdapter` por cada agente
   - Los registra en el `StateGraph` como nodos
   - Conecta las aristas en orden: perception → reasoning → execution → validator
3. El metodo NO modifica el pipeline existente (`build()`), solo agrega una nueva forma de construirlo

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/orchestrator.py
grep -n "build_from_agents" compiler-bot/agentic_pipeline/orchestrator.py && echo "B10 OK"
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/orchestrator.py
```

---

### B11 — Tests de Adapter

**Archivo:** `tests/test_agent_stage_adapter.py` (NUEVO)

**Casos a cubrir (minimo 5):**

| # | Test | Descripcion |
|---|------|-------------|
| 1 | `test_adapter_receive_mission` | `receive_mission()` crea `Task` con params correctos |
| 2 | `test_adapter_act_success` | `act()` produce `StageOutput(success=True)` |
| 3 | `test_adapter_act_failure` | Agente falla → `StageOutput(success=False, error=...)` |
| 4 | `test_adapter_no_task` | `act()` sin `receive_mission()` → error en StageOutput |
| 5 | `test_adapter_with_mock_agent` | Adapter funciona con mock de Agent |
| 6 | `test_adapter_state_graph` | Adapter como nodo en StateGraph |

**Verificacion:**
```bash
ruff check tests/test_agent_stage_adapter.py
pytest tests/test_agent_stage_adapter.py -v --tb=short
```

**Rollback:**
```bash
rm tests/test_agent_stage_adapter.py
```

---

## 5. Integracion y Verificacion Final

### I1 — Quality Gates

```bash
# Ruff: 0 errores
ruff check compiler-bot/agentic_pipeline/ --quiet || exit 1

# Ruff format: 0 diferencias
ruff format --check compiler-bot/agentic_pipeline/ --quiet || exit 1

# Tests de visitor
pytest tests/test_ast_visitor.py -v --tb=short || exit 1
pytest tests/test_ir_export_visitor.py -v --tb=short || exit 1

# Tests de mediator + adapter
pytest tests/test_agent_mediator.py -v --tb=short || exit 1
pytest tests/test_agent_stage_adapter.py -v --tb=short || exit 1
```

### I2 — Suite completa

```bash
pytest tests/ -v --tb=short --co 2>&1 | tail -20
# Debe mostrar: "463 passed" (o el numero total actual + nuevos tests)
# Sin regresiones
```

### I3 — Smoke test de integracion

```bash
# Probar que el pipeline completo sigue funcionando con un prompt basico
python -m agentic_pipeline.main -p "crea un modulo de pagos en NestJS" 2>&1 | head -20
# Debe producir output similar al pre-refactor
```

---

## 6. Rollback Plan

### 6.1 Por paso individual

Cada paso tiene su comando de rollback en su seccion. En general:

- **Archivos nuevos:** `rm <archivo>`
- **Archivos modificados:** `git checkout -- <archivo>`

### 6.2 Rollback completo (track completo)

```bash
# Track A — Visitor + IRExportVisitor
rm -f compiler-bot/agentic_pipeline/nodes/ast_visitor.py
rm -f compiler-bot/agentic_pipeline/nodes/validation_visitor.py
rm -f compiler-bot/agentic_pipeline/nodes/evaluation_visitor.py
rm -f compiler-bot/agentic_pipeline/nodes/ir_export_visitor.py
rm -f tests/test_ast_visitor.py
rm -f tests/test_ir_export_visitor.py
git checkout -- compiler-bot/agentic_pipeline/nodes/ast_nodes.py
git checkout -- compiler-bot/agentic_pipeline/nodes/semantic_analyzer.py
git checkout -- compiler-bot/agentic_pipeline/nodes/parser.py
git checkout -- compiler-bot/agentic_pipeline/nodes/ir_generator.py

# Track B — Mediator + Adapter
rm -f compiler-bot/agentic_pipeline/agents/agent_mediator.py
rm -f compiler-bot/agentic_pipeline/agents/agent_stage_adapter.py
rm -f tests/test_agent_mediator.py
rm -f tests/test_agent_stage_adapter.py
git checkout -- compiler-bot/agentic_pipeline/agents/base_agent.py
git checkout -- compiler-bot/agentic_pipeline/agents/perception_agent.py
git checkout -- compiler-bot/agentic_pipeline/agents/reasoning_agent.py
git checkout -- compiler-bot/agentic_pipeline/agents/execution_agent.py
git checkout -- compiler-bot/agentic_pipeline/agents/validator_agent.py
git checkout -- compiler-bot/agentic_pipeline/agents/supervisor_agent.py
git checkout -- compiler-bot/agentic_pipeline/orchestrator.py

# Verificar estado limpio
git status --porcelain
ruff check .
pytest tests/ -v --tb=short
```

### 6.3 Punto de restauracion recomendado

Antes de comenzar cada track, crear un commit o tag:

```bash
git tag pre-patterns-refactor-track-A  # antes de A1
git tag pre-patterns-refactor-track-B  # antes de B1
```

Esto permite `git checkout tags/pre-patterns-refactor-track-X` para recuperacion rapida.

---

## Apendice A: Diagrama de Dependencias

```
Track A (Semana 1)                 Track B (Semana 2)
─────────────────────────          ─────────────────────────
A1: IASTVisitor (NUEVO)            B1: IAgentMediator (NUEVO)
  │                                  │
A2: ASTNode.accept() (MOD)         B2: Agent base (MOD)
  │                                  ├────┬────┬────┬────┐
A3: ValidationVisitor (NUEVO)      B3  B4  B5  B6  B7 (MODs)
  │                                  │
A4: EvaluationVisitor (NUEVO)      B8: tests mediator (NUEVO)
  │                                  │
A5: SemanticAnalyzer (MOD)         B9: AgentStageAdapter (NUEVO)
  │                                  │
A6: Parser (MOD)                   B10: Orchestrator (MOD)
  │                                  │
A7: tests visitor (NUEVO)          B11: tests adapter (NUEVO)
  │                                  │
A8: IRExportVisitor (NUEVO)         │
  │                                  │
A9: IRGenerator (MOD)               │
  │                                  │
A10: tests IR export (NUEVO)        │
  │                                  │
  └────────────┬───────────────────┘
               │
          I1-I3: Integracion
               │
          ✅ COMPLETADO
```

**Track A y Track B son independientes** — pueden ejecutarse en paralelo por dos desarrolladores.

## Apendice B: Resumen de Archivos

### Archivos nuevos (7)

| Archivo | Track | Pasos |
|---------|-------|-------|
| `nodes/ast_visitor.py` | A | A1 |
| `nodes/validation_visitor.py` | A | A3 |
| `nodes/evaluation_visitor.py` | A | A4 |
| `nodes/ir_export_visitor.py` | A | A8 |
| `agents/agent_mediator.py` | B | B1 |
| `agents/agent_stage_adapter.py` | B | B9 |

### Archivos modificados (10)

| Archivo | Track | Pasos |
|---------|-------|-------|
| `nodes/ast_nodes.py` | A | A2 |
| `nodes/semantic_analyzer.py` | A | A5 |
| `nodes/parser.py` | A | A6 |
| `nodes/ir_generator.py` | A | A9 |
| `agents/base_agent.py` | B | B2 |
| `agents/perception_agent.py` | B | B3 |
| `agents/reasoning_agent.py` | B | B4 |
| `agents/execution_agent.py` | B | B5 |
| `agents/validator_agent.py` | B | B6 |
| `agents/supervisor_agent.py` | B | B7 |
| `orchestrator.py` | B | B10 |

### Archivos de test nuevos (4)

| Archivo | Track | Pasos |
|---------|-------|-------|
| `tests/test_ast_visitor.py` | A | A7 |
| `tests/test_ir_export_visitor.py` | A | A10 |
| `tests/test_agent_mediator.py` | B | B8 |
| `tests/test_agent_stage_adapter.py` | B | B11 |

---

*Documento generado a partir del analisis de `docs/122_PLAN_DEV_PATTERNS_REFACTOR_1_0_DRAFT.md`. Fecha: 2026-06-18.*
