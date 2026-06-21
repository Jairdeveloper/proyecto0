---
id: "P05"
area: dev
type: plan
module: pipeline_fixes
version: "1.1"
status: IMPLEMENTED
tags:
  - "plan"
  - "action"
  - "fixes"
  - "lexer"
  - "parser"
  - "semantic"
  - "ir"
  - "synthesis"
  - "ui-generator"
  - "pipeline"
  - "chain"
summary: "Plan de accion para corregir 5 problemas estructurales del pipeline RECPL v2.0: (1) lexer no tokeniza 'modulo' como MODULE, (2) gap de tipos entre parser fallback y semantic/IR, (3) synthesis no ejecuta tareas del planner, (4) UI generator sin guardas de dominio, (5) chain path: generate no itera tasks del planner + handlers sin ubicacion. 21 pasos, ~14h estimadas."
changelog:
  - version: "1.1"
    date: "2026-06-18"
    author: "Arquitecto Senior"
    description: "Agregado Fix 5 — chain path: conectar generate con planner, health check LLM, populate params, verify con criterios, ubicaciones de handlers"
  - version: "1.0"
    date: "2026-06-18"
    author: "Arquitecto Senior"
    description: "Version inicial — plan de correccion basado en debug output del pipeline con input 'crea modulo'"
keywords:
  - "action-plan"
  - "fixes"
  - "lexer"
  - "parser"
  - "semantic"
  - "ir"
  - "synthesis"
  - "ui-generator"
  - "data-flow"
  - "chain"
---

# Plan de Accion — 4 Correcciones Prioritarias al Pipeline RECPL v2.0

> **Origen:** Debug output de `python compiler-bot/agentic -p "crea modulo" --debug step`
> **Problema raiz:** El pipeline ejecuta 10 etapas sin excepciones, reporta `success: true`, pero el scaffolding real (archivos NestJS/Prisma) no se materializa. `files_generated=0`, `task_count=0`.
> **Estimacion total:** ~8.5h / 15 pasos
> **Archivos afectados:** 11 (3 nuevos, 8 modificados)

---

## Tabla de Contenidos

1. [Diagnostico General](#1-diagnostico-general)
2. [Fix 1 — Lexer: Agregar EntityDFA](#2-fix-1--lexer-agregar-entitydfa)
3. [Fix 2 — Cerrar Gap de Tipos Parser/Semantic/IR](#3-fix-2--cerrar-gap-de-tipos-parsersemanticir)
4. [Fix 3 — Conectar Synthesis con Planner](#4-fix-3--conectar-synthesis-con-planner)
5. [Fix 4 — Guardas de Dominio en UI Generator](#5-fix-4--guardas-de-dominio-en-ui-generator)
6. [Fix 5 — Chain Path: Conectar Generate con Planner](#6-fix-5--chain-path-conectar-generate-con-planner)
7. [Dependencias entre Pasos](#7-dependencias-entre-pasos)
8. [Verificacion de Integracion](#8-verificacion-de-integracion)
9. [Rollback Plan](#9-rollback-plan)

---

## 1. Diagnostico General

### 1.1 La cadena de errores completa

```
Input: "crea modulo"
          │
          ▼
LEXER (sub_dfa.py)
  "crea"   → ActionDFA: Token(type="CREATE", category="action")
  "modulo" → NO MATCH en ninguna sub-DFA → DESAPARECE
          │
          ▼
PARSER (parser.py)
  _try_lark_parse() → FAILS
  _build_ast_from_tokens() → FALLBACK:
    Token "crea" (action) → {"node_type": "action", "value": "crea"}  ← TIPO INVALIDO
          │
          ▼
SEMANTIC ANALYZER (semantic_analyzer.py:122)
  WARNING: "Unknown node type: 'action'"  ← NO HAY visit_action()
          │
          ▼
IR BUILDER (ir_builder.py:135)
  WARNING: "Unknown IR node type: action"  ← NO HAY if "action" branch
  → retorna None → nodo ELIMINADO del arbol
          │
          ▼
PLANNER (reasoning_engine.py)
  ir_tree.children = [] → _build_tasks_from_ir() produce 0 tasks
  → goal_tree se genera (heuristica), pero NADIE lo lee
          │
          ▼
SYNTHESIS (action_executor.py)
  tasks=[], ir_tree sin hijos → 0 archivos generados
  → output_data NO incluye ir_tree ni tasks
          │
          ▼
UI GENERATOR (ui_generator.py)
  Sin ir_tree ni tasks (handoff roto), genera 4 CSS/JSON incondicionalmente
  → SOBREESCRIBE generated_files, pierde archivos de synthesis
          │
          ▼
VALIDATOR (validator.py)
  Valida solo CSS/JSON (lo unico que llega)
  → success: true, pero 0 archivos NestJS generados
```

### 1.2 Los 4 problemas estructurales

| # | Problema | Evidencia | Impacto |
|---|----------|-----------|---------|
| 1 | **Lexer pierde tokens** | `tokens_count=1` — "modulo" no esta en ninguna sub-DFA | El parser recibe 1 token, AST incompleto |
| 2 | **Mismatch de tipos AST** | Semantic: "Unknown node type: 'action'"; IR: "Unknown IR node type: action" | El nodo action se pierde entre parser e IR |
| 3 | **Synthesis no ejecuta** | Planner produce 4 subtareas, synthesis produce `files_generated=0` | El scaffolding real no se materializa |
| 4 | **UI Generator sin compuerta** | Genera 4 CSS/JSON para input backend. Sobreescribe `generated_files` | Falso positivo, contamina salida |

---

## 2. Fix 1 — Lexer: Agregar EntityDFA

### Diagnostico

La palabra "modulo" aparece en la gramatica Lark (`MODULE_KEYWORD: "modulo"i`) pero NO en ninguna de las 5 sub-DFAs del lexer. El DFA actual tiene 5 categorias: domain, action, tech, ui, quality — pero no un DFA para entidades/modulos/recursos del dominio del usuario.

Cuando el lexer procesa `"crea modulo"`:
- `"crea"` → ActionDFA: `Token(type="CREATE", category="action")`
- `"modulo"` → **ningun DFA matchea** → no se tokeniza
- Resultado: `tokens_count=1`, "modulo" desaparece del pipeline

### Solucion

#### Paso 1.1 — Crear EntityDFA(BaseDFA)

**Archivo:** `nodes/sub_dfa.py` (MODIFICAR)

Agregar nueva sub-DFA con palabras del dominio de entidades del usuario:

| Palabra | Token Type |
|---------|-----------|
| `modulo`, `module` | `MODULE` |
| `entidad`, `entity` | `ENTITY` |
| `modelo`, `model` | `MODEL` |
| `pagos` | `PAYMENT` |
| `auth`, `autenticacion` | `AUTH` |
| `usuario`, `user` | `USER` |
| `producto` | `PRODUCT` |
| `orden` | `ORDER` |
| `factura` | `INVOICE` |
| `catalogo` | `CATALOG` |

```python
class EntityDFA(BaseDFA):
    """Matches entity/module names in the domain of the user's application."""

    def __init__(self):
        words = [
            ("modulo", "MODULE"), ("module", "MODULE"),
            ("entidad", "ENTITY"), ("entity", "ENTITY"),
            ("modelo", "MODEL"), ("model", "MODEL"),
            ("pagos", "PAYMENT"),
            ("auth", "AUTH"), ("autenticacion", "AUTH"),
            ("usuario", "USER"), ("user", "USER"),
            ("producto", "PRODUCT"),
            ("orden", "ORDER"),
            ("factura", "INVOICE"),
            ("catalogo", "CATALOG"),
        ]
        super().__init__(words, "entity")
```

**Verificacion:**
```bash
python -c "
from agentic_pipeline.nodes.sub_dfa import EntityDFA
d = EntityDFA()
tokens = d.tokenize('modulo')
assert len(tokens) == 1
assert tokens[0].type == 'MODULE'
assert tokens[0].category == 'entity'
print('Paso 1.1 OK')
"
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/nodes/sub_dfa.py
```

#### Paso 1.2 — Registrar EntityDFA en el LexerOrchestrator

**Archivo:** `nodes/lexer.py` (MODIFICAR)

Agregar `EntityDFA` a la lista de DFAs que el orquestador ejecuta:

```python
# En LexerOrchestrator.__init__() o donde se registren los DFAs
from .sub_dfa import ActionDFA, TechDFA, DomainDFA, UIDFA, QualityDFA, EntityDFA

self._dfas = [
    ActionDFA(),
    TechDFA(),
    DomainDFA(),
    UIDFA(),
    QualityDFA(),
    EntityDFA(),        # <-- NUEVO
]
```

Si el orquestador tiene un registro por tipo, agregar categoria `"entity"` al dispatch.

**Verificacion:**
```bash
python -c "
from agentic_pipeline.nodes.lexer import LexerOrchestrator
l = LexerOrchestrator()
tokens = l.tokenize('crea modulo')
assert any(t.type == 'MODULE' for t in tokens)
assert any(t.type == 'CREATE' for t in tokens)
print('Paso 1.2 OK:', [t.value for t in tokens])
"
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/nodes/lexer.py
```

#### Paso 1.3 — Agregar MODULE al mapeo de post-processamiento

**Archivo:** `nodes/lexer.py` (MODIFICAR)

Si existe `post_process_tokens()` o un mapeo de tipos de entidad, agregar `"MODULE"` a la lista de tipos reconocidos para la categoria `"entity"`.

```python
# En el mapeo entity_token_types o similar
ENTITY_TOKEN_TYPES = {"MODULE", "ENTITY", "MODEL", "USER", "PAYMENT", ...}
```

**Verificacion:**
```bash
pytest tests/test_lexer_sub_dfas.py -v --tb=short
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/nodes/lexer.py
```

---

## 3. Fix 2 — Cerrar Gap de Tipos Parser/Semantic/IR

### Diagnostico

El fallback `_build_ast_from_tokens()` en `parser.py` produce dictos con `node_type: "action"` y `node_type: "entity"`. Sin embargo:

- `SemanticVisitor.visit()` (semantic_analyzer.py) solo reconoce: `project`, `page`, `component`, `entity`, `infra`
- `IRBuilder._build_node()` (ir_builder.py) solo reconoce: `page`, `component`, `entity`, `infra`, `api`, `config`
- `IASTVisitor` (ast_visitor.py) solo tiene 5 metodos: `visit_project/page/component/entity/infra`

El tipo `"action"` no existe como nodo AST, como visitor method, ni como IR node type. Se produce en el parser, se ignora en semantic, se elimina en IR.

### Solucion

#### Paso 2.1 — Agregar ActionNode al AST

**Archivo:** `nodes/ast_nodes.py` (MODIFICAR)

```python
class ActionNode(ASTNode):
    """Represents an action command (create, read, update, delete) with its target."""

    def __init__(self, action_type: str, target: str = ""):
        super().__init__(name=action_type)
        self.action_type: str = action_type
        self.target: str = target

    def accept(self, visitor: IASTVisitor) -> Any:
        return visitor.visit_action(self)
```

**Verificacion:**
```bash
python -c "
from agentic_pipeline.nodes.ast_nodes import ActionNode
n = ActionNode('create', 'modulo')
assert n.action_type == 'create'
assert n.target == 'modulo'
assert hasattr(n, 'accept')
print('Paso 2.1 OK')
"
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/nodes/ast_nodes.py
```

#### Paso 2.2 — Agregar visit_action() a IASTVisitor y todos los visitors

**Archivo:** `nodes/ast_visitor.py` (MODIFICAR)

En `IASTVisitor`:
```python
@abstractmethod
def visit_action(self, node: ActionNode) -> Any:
    ...
```

En `TreeWalkingVisitor`:
```python
def visit_action(self, node: ActionNode) -> Any:
    pass
```

**Archivos:** `nodes/validation_visitor.py`, `nodes/evaluation_visitor.py`, `nodes/ir_export_visitor.py`, `nodes/semantic_analyzer.py` (MODIFICAR)

Agregar `visit_action()` en cada visitor concreto:

- `ValidationVisitor`: validar que `target` no este vacio
- `EvaluationVisitor`: retornar `{"type": "action", "action": node.action_type, "target": node.target}`
- `IRExportVisitor`: retornar `{"node_type": "action", "name": node.name, "target": node.target}`
- `SemanticAnalysisVisitor`: registrar en symbol table, verificar target

**Verificacion:**
```bash
ruff check nodes/ast_visitor.py nodes/validation_visitor.py nodes/evaluation_visitor.py nodes/ir_export_visitor.py nodes/semantic_analyzer.py
python -c "
from agentic_pipeline.nodes.ast_visitor import IASTVisitor, TreeWalkingVisitor
assert hasattr(IASTVisitor, 'visit_action')
assert hasattr(TreeWalkingVisitor, 'visit_action')
print('Paso 2.2 OK')
"
```

**Rollback:**
```bash
git checkout -- nodes/ast_visitor.py nodes/validation_visitor.py nodes/evaluation_visitor.py nodes/ir_export_visitor.py nodes/semantic_analyzer.py
```

#### Paso 2.3 — Agregar visit_action() en SemanticVisitor (dict-based)

**Archivo:** `nodes/semantic_analyzer.py` (MODIFICAR)

El `SemanticVisitor` existente (dict-based, para nodos planos) necesita reconocer `node_type == "action"`:

```python
def visit_action(self, ir_node: dict) -> None:
    target = ir_node.get("target", "")
    if not target:
        self.warnings.append("Action has no target")
    # Registrar en symbol table
    self.symbol_table[f"$action_{ir_node.get('value', 'unnamed')}"] = {
        "type": "action",
        "target": target,
    }
```

**Verificacion:**
```bash
python -c "
from agentic_pipeline.nodes.semantic_analyzer import SemanticVisitor
v = SemanticVisitor()
v.visit({'node_type': 'action', 'value': 'crea', 'target': 'modulo'})
assert len(v.warnings) == 0
print('Paso 2.3 OK')
"
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/nodes/semantic_analyzer.py
```

#### Paso 2.4 — Agregar IRAction o mapeo en IRBuilder

**Archivo:** `nodes/ir_builder.py`, `nodes/ir_nodes.py` (MODIFICAR)

**Opcion A (recomendada):** Mapear action → IRComponent con `component_type="action"`. No requiere nuevo IRNode.

```python
# En IRBuilder._build_node():
if node_type == "action":
    return IRComponent(
        name=data.get("value", "unnamed"),
        component_type=data.get("action_type", "action"),
    )
```

**Opcion B:** Crear `IRAction(IRNode)` — mas canonico pero mas archivos.

**Verificacion:**
```bash
python -c "
from agentic_pipeline.nodes.ir_builder import IRBuilder
b = IRBuilder()
node = b._build_node({'value': 'crea', 'target': 'modulo', 'action_type': 'create'}, 'action')
assert node is not None
print('Paso 2.4 OK:', type(node).__name__)
"
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/nodes/ir_builder.py
```

#### Paso 2.5 — Actualizar _build_ast_from_tokens() a ActionNode

**Archivo:** `nodes/parser.py` (MODIFICAR)

Reemplazar la produccion de dictos planos por instancias de `ActionNode`:

```python
def _build_ast_from_tokens(self, tokens):
    from agentic_pipeline.nodes.ast_nodes import ActionNode
    actions = []
    entities = []
    for t in tokens:
        cat = t.get("category", "")
        if cat == "action":
            actions.append(ActionNode(
                action_type=t.get("type", "").lower(),
                target=t.get("value", ""),
            ))
        elif cat in ("entity", "domain"):
            entities.append(t.get("value", ""))
    # Construir arbol con ActionNodes
    project = ProjectNode("project")
    for a in actions:
        project.add(a)
    return project
```

**Verificacion:**
```bash
ruff check nodes/parser.py
grep -n '"node_type": "action"' nodes/parser.py || echo "Paso 2.5 OK: no dict-based action nodes"
pytest tests/test_parser_project.py -v --tb=short | tail -5
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/nodes/parser.py
```

---

## 4. Fix 3 — Conectar Synthesis con Planner

### Diagnostico

El pipeline planner→synthesis tiene 3 puntos de falla:

1. `_build_tasks_from_ir()` produce 0 tareas porque `ir_tree.children` esta vacio (los nodos action se perdieron en IR)
2. El `target` en Task objects es `""` (default), synthesis no sabe que generador usar
3. `ActionExecutor.act()` no propaga `ir_tree` ni `tasks` en su `output_data`, rompiendo el handoff a UI generator

### Solucion

#### Paso 3.1 — Fallback a goal_tree cuando IR tree vacio

**Archivo:** `nodes/reasoning_engine.py` (MODIFICAR)

En `_build_tasks_from_ir()`, si `ir_tree` no tiene hijos, construir tareas desde el goal_tree heuristico:

```python
def _build_tasks_from_ir(self) -> None:
    ir_tree = self._input_data.get("ir_tree")
    if ir_tree and hasattr(ir_tree, "children") and ir_tree.children:
        # Path normal: construir desde IR
        for child in ir_tree.children:
            task = self._ir_node_to_task(child)
            if task:
                self._task_graph.add_task(task)
    else:
        # Fallback: construir desde enriched slots y goal_tree
        slots = self._enriched.get("slots", {}) if self._enriched else {}
        nombre = slots.get("nombre", "app")
        self._build_tasks_from_slots(nombre)
```

Agregar `_build_tasks_from_slots()`:

```python
def _build_tasks_from_slots(self, nombre: str) -> None:
    """Build scaffold tasks from enriched slots when IR tree is empty."""
    tasks_data = [
        ("create_dir", f"Crear directorio modules/{nombre}", "scaffold"),
        ("create_module_file", f"Crear archivo {nombre}.module.ts", "nestjs"),
        ("create_controller", f"Crear archivo {nombre}.controller.ts", "nestjs"),
        ("create_service", f"Crear archivo {nombre}.service.ts", "nestjs"),
    ]
    for tid, desc, gen in tasks_data:
        task = Task(id=tid, description=desc, generator=gen, target="nestjs")
        self._task_graph.add_task(task)
```

**Verificacion:**
```bash
python -c "
from agentic_pipeline.nodes.reasoning_engine import ReasoningEngine
# Mock input sin IR tree
engine = ReasoningEngine.__new__(ReasoningEngine)
# Verificar que _build_tasks_from_slots existe
assert hasattr(engine, '_build_tasks_from_slots')
print('Paso 3.1 OK')
"
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/nodes/reasoning_engine.py
```

#### Paso 3.2 — Agregar task_count en output_data

**Archivo:** `nodes/reasoning_engine.py` (MODIFICAR)

```python
# En el output_data del return:
output_data={
    "tasks": [t.model_dump() for t in ordered],
    "task_count": len(ordered),   # <-- NUEVO (antes solo en metrics)
    "task_graph": ordered,
    # ... resto igual
}
```

**Verificacion:**
```bash
grep -n '"task_count"' compiler-bot/agentic_pipeline/nodes/reasoning_engine.py
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/nodes/reasoning_engine.py
```

#### Paso 3.3 — Poblar target en Task segun dominio

**Archivo:** `nodes/reasoning_engine.py` (MODIFICAR)

En `_ir_node_to_task()` o donde se creen los Task, poblar `target` dinamicamente:

```python
def _detect_target(self, ir_node) -> str:
    """Detect target framework from node type and enriched domain."""
    domain = "backend"
    if self._enriched:
        domain = self._enriched.get("intent", {}).get("domain", "backend")
    
    node_type = type(ir_node).__name__
    target_map = {
        "IREntity": "prisma",
        "IRAPI": "nestjs",
        "IRComponent": "react" if domain != "backend" else "nestjs",
        "IRPage": "react",
        "IRInfra": "docker",
    }
    result = target_map.get(node_type, "generic")
    # Fallback heuristico por dominio
    if result == "generic" and domain == "backend":
        result = "nestjs"
    elif result == "generic" and domain in ("web", "frontend"):
        result = "react"
    return result
```

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/nodes/reasoning_engine.py
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/nodes/reasoning_engine.py
```

#### Paso 3.4 — Propagar ir_tree y tasks en ActionExecutor output

**Archivo:** `nodes/action_executor.py` (MODIFICAR)

```python
# En ActionExecutor.act(), return de StageOutput:
return StageOutput(
    output_data={
        "generated_files": generated_files,
        "errors": errors,
        "warnings": warnings,
        "task_count": len(tasks),
        "ir_tree": self._input_data.get("ir_tree") if self._input_data else None,  # <-- NUEVO
        "tasks": self._input_data.get("tasks", []) if self._input_data else [],    # <-- NUEVO
        "enriched": self._enriched or None,
    },
    # ... resto igual
)
```

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/nodes/action_executor.py
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/nodes/action_executor.py
```

#### Paso 3.5 — Fallback en synthesis cuando tasks estan vacios

**Archivo:** `nodes/action_executor.py` (MODIFICAR)

En `act()`, si `tasks` esta vacio e `ir_tree` no tiene hijos, intentar construir tareas desde `goal_tree` que el planner dejo en enriched:

```python
def act(self, plan: ActionPlan) -> StageOutput:
    ir_tree = self._input_data.get("ir_tree") if self._input_data else None
    commands = self._input_data.get("commands", []) if self._input_data else []
    tasks = self._input_data.get("tasks", []) if self._input_data else []
    enriched = self._input_data.get("enriched", {}) if self._input_data else {}
    goal_tree = self._input_data.get("goal_tree") if self._input_data else None

    # Fallback: si no hay tareas pero hay goal_tree, construir desde ahi
    if not tasks and goal_tree:
        subtasks = goal_tree.get("subtasks", [])
        tasks = [{
            "id": s["id"],
            "description": s["description"],
            "target": "nestjs",  # default para scaffolding
        } for s in subtasks]
        commands = [{
            "task_id": s["id"],
            "type": "scaffold",
            "path": f"modules/{enriched.get('slots', {}).get('nombre', 'app')}",
        } for s in subtasks]
    # ... resto del metodo
```

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/nodes/action_executor.py
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/nodes/action_executor.py
```

---

## 5. Fix 4 — Guardas de Dominio en UI Generator

### Diagnostico

`UIGenerator.act()` genera 4 archivos CSS/JSON incondicionalmente para cualquier input, incluso cuando `domain=backend`. Ademas, sobreescribe `generated_files`, borrando los archivos que synthesis produjo previamente.

### Solucion

#### Paso 4.1 — Guarda de dominio al inicio de act()

**Archivo:** `nodes/ui_generator.py` (MODIFICAR)

```python
def act(self, plan: ActionPlan) -> StageOutput:
    ir_tree = self._input_data.get("ir_tree") if self._input_data else None
    tasks = self._input_data.get("tasks", []) if self._input_data else []
    enriched = self._input_data.get("enriched", {}) if self._input_data else {}
    generated_files: list[str] = []
    errors: list[str] = []

    # --- GUARDA DE DOMINIO ---
    domain = enriched.get("intent", {}).get("domain", "backend")
    if domain != "ui":
        # Verificar si hay componentes UI en IR tree o tasks
        ui_components = self._detect_ui_components(ir_tree, tasks)
        if not ui_components:
            # No hay nada UI que generar — propagar archivos del stage anterior
            previous_files = self._input_data.get("generated_files", []) if self._input_data else []
            return StageOutput(
                stage=self.context.stage,
                output_data={
                    "generated_files": previous_files,
                    "errors": [],
                    "task_count": len(tasks),
                    "enriched": enriched or None,
                },
                metrics={"files_generated": len(previous_files), "errors": 0, "components": 0},
                success=True,
            )
```

**Verificacion:**
```bash
python -c "
from agentic_pipeline.nodes.ui_generator import UIGenerator
# Verificar que la guarda existe
import inspect
source = inspect.getsource(UIGenerator.act)
assert 'domain' in source
print('Paso 4.1 OK: domain gate found')
"
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/nodes/ui_generator.py
```

#### Paso 4.2 — Fusionar generated_files en lugar de sobreescribir

**Archivo:** `nodes/ui_generator.py` (MODIFICAR)

```python
# Al inicio de act(), antes de generar UI files:
previous_files = self._input_data.get("generated_files", []) if self._input_data else []

# Al final, antes del return:
all_files = list(previous_files) + generated_files
# Eliminar duplicados preservando orden
seen = set()
deduped = []
for f in all_files:
    if f not in seen:
        seen.add(f)
        deduped.append(f)

return StageOutput(
    output_data={
        "generated_files": deduped,   # <-- fusionados
        "errors": errors,
        "task_count": len(tasks),
        "enriched": enriched or None,
    },
    # ... resto igual
)
```

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/nodes/ui_generator.py
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/nodes/ui_generator.py
```

#### Paso 4.3 — Usar ir_tree y tasks del input_data

**Archivo:** `nodes/ui_generator.py` (MODIFICAR)

`_detect_ui_components()` ya acepta `ir_tree` y `tasks`. Con el fix 3.4, estos datos llegan correctamente. Verificar que el metodo itera sobre ambos:

```python
@staticmethod
def _detect_ui_components(ir_tree, tasks):
    components = []
    seen = set()
    if ir_tree is not None:
        for child in getattr(ir_tree, "children", []):
            child_type = type(child).__name__
            child_name = getattr(child, "name", "").lower()
            # Detectar por tipo IR
            if child_type in ("IRComponent", "IRPage"):
                component = ...  # construir via ComponentFactory
                components.append(component)
            # Detectar por nombre
            if any(kw in child_name for kw in ("form", "table", "list", "card")):
                ...
    for task in tasks:
        task_name = task.get("id", "").lower() if isinstance(task, dict) else ""
        if any(kw in task_name for kw in ("form", "table", "card")):
            ...
    return components
```

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/nodes/ui_generator.py
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/nodes/ui_generator.py
```

#### Paso 4.4 — Agregar metrics de dominio y deteccion

**Archivo:** `nodes/ui_generator.py` (MODIFICAR)

```python
# En el return:
return StageOutput(
    output_data={...},
    metrics={
        "files_generated": len(generated_files),
        "errors": len(errors),
        "components": len(ui_components),
        "domain": domain,                              # <-- NUEVO
        "ui_components_detected": len(ui_components),  # <-- NUEVO
        "domain_gate_triggered": domain != "ui",        # <-- NUEVO
    },
    ...
)
```

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/nodes/ui_generator.py
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/nodes/ui_generator.py
```

---

## 6. Fix 5 — Chain Path: Conectar Generate con Planner

> **Origen:** Debug output de `python compiler-bot/agentic -p "crea modulo" --chain --debug step`
> **Problema raiz:** El path `--chain` depende de LLM en todas las etapas. Sin Ollama/OpenAI, todo cae a fallbacks que producen 0 archivos. Pero incluso con LLM, generate no itera las tareas del planner.

### Diagnostico

El path `--chain` usa 6 handlers: preprocess → intent → plan → generate → verify → format. A diferencia del path `--step` (StateGraph deterministico), cada handler depende de un LLM call. Sin backend LLM funcional, todos fallan a `Ollama generate failed` y operan con fallbacks minimos.

Problemas especificos:

| # | Problema | Evidencia | Impacto |
|---|----------|-----------|---------|
| 5.1 | **LLM caido en todas las etapas** | `Ollama generate failed` × 6 | Pipeline entero en modo fallback. Sin logica real de LLM |
| 5.2 | **Planner produce tareas sin params** | 4 tareas identicas: `target: "modulo"`, `type: "generate_code"`, `params: {}` | Generate no recibe contexto para decidir que codigo crear |
| 5.3 | **Generate no itera tasks del planner** | `files: []`, `errors: []` — output flat sin relacion con las tareas | El planificador planifica 4 tareas, generate las ignora |
| 5.4 | **Verify sin criterios** | `checks: []`, `valid: true` | Validacion nula. `success=true` es falso positivo |
| 5.5 | **Handlers sin ubicacion** | `← ?:?` en 5 de 6 handlers | `_resolve_stage_locations()` solo mapea nodos de `NODE_MAP` (StateGraph), no los handlers del chain |
| 5.6 | **Format handler ignora generate** | `files_created: []`, `summary: "0 archivos generados"` | El handler final no refleja los archivos que generate produjo |

### Solucion

#### Paso 5.1 — Agregar health check de backend LLM

**Archivo:** `prompt_chain/cli.py` (MODIFICAR)

Agregar health check al inicio del chain que verifique disponibilidad del backend configurado:

```python
async def check_llm_backend() -> bool:
    """Health check: verifica que el backend LLM configurado responda."""
    try:
        backend = get_llm_backend()
        result = await backend.generate("test", max_tokens=1)
        return result.success
    except Exception as exc:
        logger.warning("LLM backend health check failed: %s", exc)
        return False
```

Si el health check falla, advertir al usuario y sugerir `ollama serve` o verificar `OPENAI_API_KEY`:

```python
if not await check_llm_backend():
    print(
        "ADVERTENCIA: Backend LLM no disponible. "
        "Usa 'ollama serve' o configura OPENAI_API_KEY.\n"
        "Los handlers usaran fallbacks deterministicos.",
        file=sys.stderr,
    )
```

**Verificacion:**
```bash
python -c "
from agentic_pipeline.prompt_chain.cli import check_llm_backend
import asyncio
result = asyncio.run(check_llm_backend())
print(f'Health check: {result}')
"
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/prompt_chain/cli.py
```

#### Paso 5.2 — Poblar params en tareas del planner

**Archivo:** `prompt_chain/handlers/plan_handler.py` (MODIFICAR)

En el handler `plan`, poblar `params` de cada tarea con datos del intent y preprocess:

```python
# En PlanHandler.handle(), despues del LLM call
if isinstance(output, dict) and "tasks" in output:
    intent_data = ctx.get_output("intent", {})
    for task in output["tasks"]:
        task["params"] = {
            "module_name": intent_data.get("module", "app"),
            "entity_name": intent_data.get("entity"),
            "tech_stack": intent_data.get("tech", ["nestjs"]),
            "features": intent_data.get("features", []),
        }
```

Tarea enriquecida resultante:

```python
{
    "id": "create_module_file",
    "type": "generate_code",
    "target": "modulo",
    "template": "nestjs-module",
    "params": {
        "module_name": "modulo",
        "tech_stack": ["nestjs"],
        "output_path": "modules/modulo",
    },
    "dependencies": ["create_dir"],
}
```

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/prompt_chain/handlers/plan_handler.py
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/prompt_chain/handlers/plan_handler.py
```

#### Paso 5.3 — Generate itera sobre tareas del planner

**Archivo:** `prompt_chain/handlers/generate_handler.py` (MODIFICAR)

En `GenerateHandler.handle()`, leer las tareas del contexto del plan y generar una por una:

```python
async def handle(self, request, ctx):
    plan_output = ctx.get_output("plan", {})
    tasks = plan_output.get("tasks", [])
    generated_files = []
    errors = []

    for task in tasks:
        template = task.get("template", "generic")
        params = task.get("params", {})
        target = task.get("target", "output")

        gen_prompt = self._build_task_prompt(template, params)
        result = await self._generate_file(gen_prompt, params)
        if result.success:
            generated_files.extend(result.files)
        else:
            errors.append(f"Task {task['id']} failed: {result.error}")

    return {
        "files": generated_files,
        "errors": errors,
        "task_count": len(tasks),
    }
```

Para modo sin LLM, agregar template engine basico (scaffolding deterministico):

```python
def _scaffold_file(self, template: str, params: dict) -> list[dict]:
    """Generate files from templates without LLM (fallback deterministico)."""
    template_map = {
        "nestjs-module": {
            "path": f"modules/{params['module_name']}/{params['module_name']}.module.ts",
            "content": (
                f"@Module({{ imports: [], controllers: [], providers: [] }})\n"
                f"export class {params['module_name'].title()}Module {{}}\n"
            ),
        },
        "nestjs-controller": {
            "path": f"modules/{params['module_name']}/{params['module_name']}.controller.ts",
            "content": (
                f"@Controller('{params['module_name']}')\n"
                f"export class {params['module_name'].title()}Controller {{}}\n"
            ),
        },
        "nestjs-service": {
            "path": f"modules/{params['module_name']}/{params['module_name']}.service.ts",
            "content": (
                f"@Injectable()\n"
                f"export class {params['module_name'].title()}Service {{}}\n"
            ),
        },
    }
    tmpl = template_map.get(template)
    if tmpl:
        return [{"path": tmpl["path"], "content": tmpl["content"]}]
    return []
```

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/prompt_chain/handlers/generate_handler.py
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/prompt_chain/handlers/generate_handler.py
```

#### Paso 5.4 — Poblar criterios de verificacion en Verify

**Archivo:** `prompt_chain/handlers/verify_handler.py` (MODIFICAR)

```python
async def handle(self, request, ctx):
    generate_output = ctx.get_output("generate", {})
    files = generate_output.get("files", [])
    plan_output = ctx.get_output("plan", {})
    tasks = plan_output.get("tasks", [])

    checks = []
    for task in tasks:
        expected_files = self._expected_files_for_task(task)
        for ef in expected_files:
            exists = any(ef in f.get("path", "") for f in files)
            checks.append({
                "check": f"File {ef} exists",
                "passed": exists,
            })

    all_passed = all(c["passed"] for c in checks)
    return {
        "valid": all_passed,
        "checks": checks,
        "should_retry": not all_passed and len(checks) > 0,
        "suggestions": [] if all_passed else ["Regenerar archivos faltantes"],
    }
```

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/prompt_chain/handlers/verify_handler.py
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/prompt_chain/handlers/verify_handler.py
```

#### Paso 5.5 — Registrar ubicaciones de chain handlers en debugger

**Archivo:** `compiler-bot/agentic_pipeline/debugger.py` (MODIFICAR)

Extender `_resolve_stage_locations()` para incluir los handlers del chain ademas de los nodos del StateGraph:

```python
def _resolve_stage_locations() -> dict[str, str]:
    locations: dict[str, str] = {}
    # StateGraph nodes (existente)
    for stage, cls in NODE_MAP.items():
        try:
            module = inspect.getmodule(cls)
            rel = (
                os.path.relpath(module.__file__, start=os.getcwd())
                if module and module.__file__
                else "?"
            )
            _, line = inspect.getsourcelines(cls)
            locations[stage.value] = f"{rel}:{line}"
        except (OSError, TypeError):
            locations[stage.value] = "?:?"

    # Chain handlers (NUEVO)
    chain_handlers = {
        "preprocess": "prompt_chain/handlers/preprocess_handler.py",
        "intent": "prompt_chain/handlers/intent_handler.py",
        "plan": "prompt_chain/handlers/plan_handler.py",
        "generate": "prompt_chain/handlers/generate_handler.py",
        "verify": "prompt_chain/handlers/verify_handler.py",
        "format": "prompt_chain/handlers/format_handler.py",
    }
    base = Path(os.getcwd())
    for handler_name, rel_path in chain_handlers.items():
        if handler_name not in locations:
            full_path = base / rel_path
            if full_path.exists():
                locations[handler_name] = f"{rel_path}:1"
            else:
                locations[handler_name] = f"{rel_path}:?"

    return locations
```

**Verificacion:**
```bash
python -c "
from agentic_pipeline.debugger import _resolve_stage_locations
loc = _resolve_stage_locations()
assert 'preprocess' in loc
assert 'intent' in loc
assert 'plan' in loc
print('Paso 5.5 OK:', {k: v for k, v in loc.items() if k in ('preprocess','intent','plan','generate','verify','format')})
"
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/debugger.py
```

#### Paso 5.6 — Fix format handler: files_created desde generate

**Archivo:** `prompt_chain/handlers/format_handler.py` (MODIFICAR)

```python
async def handle(self, request, ctx):
    generate_output = ctx.get_output("generate", {})
    files = generate_output.get("files", [])

    return {
        "summary": f"Procesado. {len(files)} archivos generados.",
        "files_created": files,
        "warnings": [],
        "next_steps": [
            "Revisa los archivos generados en el directorio de salida"
        ],
        "success": len(files) > 0,
    }
```

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/prompt_chain/handlers/format_handler.py
```

**Rollback:**
```bash
git checkout -- compiler-bot/agentic_pipeline/prompt_chain/handlers/format_handler.py
```

---

## 7. Dependencias entre Pasos

```
Fix 1 (Lexer)          Fix 2 (Tipos)
  Paso 1.1 ───┐          Paso 2.1 ───┐
  Paso 1.2 ───┤          Paso 2.2 ───┤
  Paso 1.3 ───┤          Paso 2.3 ───┤
              │          Paso 2.4 ───┤
              │          Paso 2.5 ───┤
              └────┬────────────┬────┘
                   │            │
                   ▼            ▼
              Fix 3 (Synthesis)
              Paso 3.1 ───┐
              Paso 3.2 ───┤
              Paso 3.3 ───┤
              Paso 3.4 ───┤
              Paso 3.5 ───┤
                          │
                          ▼
                     Fix 4 (UI Gate)
                     Paso 4.1 ───┐
                     Paso 4.2 ───┤
                     Paso 4.3 ───┤
                     Paso 4.4 ───┘
                                       
                     Fix 5 (Chain Path)  (independiente de Fix 1-4)
                     Paso 5.1 ───┐
                     Paso 5.2 ───┤
                     Paso 5.3 ───┤
                     Paso 5.4 ───┤
                     Paso 5.5 ───┤
                     Paso 5.6 ───┘
```

Los Fixes 1 y 2 son independientes entre si. Ambos habilitan el Fix 3. El Fix 4 depende del paso 3.4 (data flow synthesis→UI). **Fix 5 es independiente** de Fixes 1-4 porque opera sobre el path `--chain` (prompt chain handlers), un pipeline completamente distinto al StateGraph.

---

## 8. Verificacion de Integracion

### 8.1 Por fix

```bash
# Fix 1 — Lexer
pytest tests/test_lexer_sub_dfas.py -v --tb=short
python -m agentic_pipeline.main -p "crea modulo" --debug 2>&1 | grep "tokens_count="
# Debe mostrar: tokens_count >= 2 (CREATE + MODULE)

# Fix 2 — Tipos
ruff check nodes/ast_nodes.py nodes/ast_visitor.py nodes/semantic_analyzer.py nodes/ir_builder.py nodes/parser.py
python -c "
from agentic_pipeline.nodes.ast_nodes import ActionNode, ProjectNode
from agentic_pipeline.nodes.ast_visitor import TreeWalkingVisitor
from agentic_pipeline.nodes.ir_export_visitor import IRExportVisitor
p = ProjectNode('test')
p.add(ActionNode('create', 'modulo'))
result = p.accept(IRExportVisitor())
assert result['children'][0]['node_type'] == 'action'
print('Fix 2 OK')
"

# Fix 3 — Synthesis
python -m agentic_pipeline.main -p "crea modulo" --debug 2>&1 | grep "files_generated="
# Debe mostrar: files_generated > 0

# Fix 4 — UI Gate
python -m agentic_pipeline.main -p "crea modulo" --debug step 2>&1 | grep -A5 "ui_generator"
# Debe mostrar: domain=backend, ui_components_detected=0, files_generated incluidos de synthesis
```

### 8.2 Quality gates

```bash
# Ruff 0 errores
ruff check compiler-bot/agentic_pipeline/ --quiet || exit 1

# Tests existentes sin regresion
pytest tests/test_lexer_sub_dfas.py tests/test_parser_project.py tests/test_semantic_visitor.py -v --tb=short || exit 1
pytest tests/test_ir_builder.py tests/test_ir_nodes.py tests/test_synthesis.py -v --tb=short || exit 1
pytest tests/test_ui_builder.py tests/test_validator_chain.py -v --tb=short || exit 1
```

### 8.3 Smoke test final

```bash
python -m agentic_pipeline.main -p "crea modulo pagos en nestjs" --debug 2>&1 | grep -E "tokens_count=|files_generated=|task_count=|error="
# Output esperado:
# tokens_count >= 3 (CREATE + PAYMENT + NESTJS)
# task_count > 0
# files_generated > 0
# Sin "Unknown node type" ni "Unknown IR node type"
```

---

## 9. Rollback Plan

### 9.1 Por paso

Cada paso especifica su comando de rollback. En general:

- **Archivos nuevos:** `rm <archivo>`
- **Archivos modificados:** `git checkout -- <archivo>`

### 9.2 Rollback completo

```bash
# Fix 1
git checkout -- compiler-bot/agentic_pipeline/nodes/sub_dfa.py
git checkout -- compiler-bot/agentic_pipeline/nodes/lexer.py

# Fix 2
git checkout -- compiler-bot/agentic_pipeline/nodes/ast_nodes.py
git checkout -- compiler-bot/agentic_pipeline/nodes/ast_visitor.py
git checkout -- compiler-bot/agentic_pipeline/nodes/validation_visitor.py
git checkout -- compiler-bot/agentic_pipeline/nodes/evaluation_visitor.py
git checkout -- compiler-bot/agentic_pipeline/nodes/ir_export_visitor.py
git checkout -- compiler-bot/agentic_pipeline/nodes/semantic_analyzer.py
git checkout -- compiler-bot/agentic_pipeline/nodes/ir_builder.py
git checkout -- compiler-bot/agentic_pipeline/nodes/parser.py

# Fix 3
git checkout -- compiler-bot/agentic_pipeline/nodes/reasoning_engine.py
git checkout -- compiler-bot/agentic_pipeline/nodes/action_executor.py

# Fix 4
git checkout -- compiler-bot/agentic_pipeline/nodes/ui_generator.py

# Fix 5
git checkout -- compiler-bot/agentic_pipeline/debugger.py
git checkout -- compiler-bot/agentic_pipeline/prompt_chain/cli.py
git checkout -- compiler-bot/agentic_pipeline/prompt_chain/handlers/plan_handler.py
git checkout -- compiler-bot/agentic_pipeline/prompt_chain/handlers/generate_handler.py
git checkout -- compiler-bot/agentic_pipeline/prompt_chain/handlers/verify_handler.py
git checkout -- compiler-bot/agentic_pipeline/prompt_chain/handlers/format_handler.py

# Verificar
git status --porcelain
ruff check . && pytest tests/ -v --tb=short
```

---

## Apendice A: Resumen de Archivos

### Archivos a modificar (8)

| Archivo | Fix | Cambio |
|---------|-----|--------|
| `nodes/sub_dfa.py` | 1 | Agregar `EntityDFA(BaseDFA)` |
| `nodes/lexer.py` | 1 | Registrar EntityDFA, agregar ENTITY_TOKEN_TYPES |
| `nodes/ast_nodes.py` | 2 | Agregar `ActionNode(ASTNode)` |
| `nodes/ast_visitor.py` | 2 | Agregar `visit_action()` abstracto |
| `nodes/validation_visitor.py` | 2 | Agregar `visit_action()` |
| `nodes/evaluation_visitor.py` | 2 | Agregar `visit_action()` |
| `nodes/ir_export_visitor.py` | 2 | Agregar `visit_action()` |
| `nodes/semantic_analyzer.py` | 2 | Agregar `visit_action()` en ambos visitors |
| `nodes/ir_builder.py` | 2 | Agregar branch "action" en `_build_node()` |
| `nodes/parser.py` | 2 | Reemplazar dictos por `ActionNode` en fallback |
| `nodes/reasoning_engine.py` | 3 | Fallback goal_tree, target heuristico, task_count en output |
| `nodes/action_executor.py` | 3 | Propagar ir_tree/tasks, fallback goal_tree |
| `nodes/ui_generator.py` | 4 | Guarda de dominio, fusionar files, metrics |
| `prompt_chain/cli.py` | 5 | Health check LLM al inicio |
| `prompt_chain/handlers/plan_handler.py` | 5 | Poblar params en tareas |
| `prompt_chain/handlers/generate_handler.py` | 5 | Iterar tasks, template engine fallback |
| `prompt_chain/handlers/verify_handler.py` | 5 | Checks basados en tareas planificadas |
| `prompt_chain/handlers/format_handler.py` | 5 | files_created desde generate |
| `debugger.py` | 5 | Ubicaciones de chain handlers |

### Archivos nuevos (0)

Ningun archivo nuevo — todos los cambios son modificaciones a archivos existentes.

---

## Apendice B: Estimacion de esfuerzo

| Fix | Pasos | Archivos | Esfuerzo |
|-----|-------|----------|----------|
| Fix 1 — Lexer EntityDFA | 1.1-1.3 (3) | 2 | ~1h |
| Fix 2 — Gap de tipos | 2.1-2.5 (5) | 8 | ~3h |
| Fix 3 — Synthesis | 3.1-3.5 (5) | 2 | ~3h |
| Fix 4 — UI guardas | 4.1-4.4 (4) | 1 | ~1.5h |
| Fix 5 — Chain path | 5.1-5.6 (6) | 6 | ~5.5h |
| **Total** | **21 pasos unicos** | **19 archivos (14 unicos)** | **~14h** |

---

*Documento generado a partir del analisis de debug output del pipeline RECPL v2.0 con input "crea modulo". Fecha: 2026-06-18.*
