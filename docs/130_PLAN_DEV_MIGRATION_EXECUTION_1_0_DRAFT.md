# Plan de Ejecución — Migración Arquitectónica RECPL v2.0+

- **ID:** 130_PLAN_DEV_MIGRATION_EXECUTION_1_0_DRAFT
- **Tipo:** PLAN (Plan de ejecución)
- **Área:** DEV
- **Módulo:** agentic_pipeline (arquitectura completa)
- **Versión:** 1.0
- **Estado:** DRAFT
- **Tags:** `execution-plan`, `migration`, `sprint-tasks`, `actionable`
- **Fuente:** `docs/129_PROP_DEV_ARCHITECTURAL_MIGRATION_1_0_DRAFT.md`
- **Dependencias:** Debe ejecutarse después de aprobación de 129_PROP
- **Changelog:**
  - 1.0 — 2026-06-18: Versión inicial — plan de ejecución detallado por sprint, con commits y verificaciones

---

## 1. Estructura del Plan

Cada sprint contiene:

- **Objetivo**: qué se logra al final del sprint
- **Tareas secuenciales**: cada una con archivo(s), comando(s), y verificación
- **Commits sugeridos**: agrupación lógica para git history limpio
- **Criterio de aceptación del sprint**: cómo verificar que el sprint está completo

**Convenciones:**

| Símbolo | Significado |
|---------|-------------|
| `🔧` | Modificar archivo existente |
| `📄` | Crear archivo nuevo |
| `🗑️` | Eliminar archivo |
| `▶️` | Ejecutar comando |
| `✅` | Criterio de verificación |

---

## 2. M0 — Fundaciones + Fixes Críticos (14h)

> **Duración:** ~2 días  
> **Objetivo:** Pipeline produce scaffolding correcto + calidad base configurada

### M0.1 — Ruff config (`pyproject.toml`) [0.5h]

**🔧 Archivo:** `compiler-bot/agentic_pipeline/pyproject.toml`

Agregar al final del archivo:

```toml
[tool.ruff]
line-length = 100
indent-width = 4
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "lf"
```

**▶️ Comandos:**
```bash
cd compiler-bot/agentic_pipeline
ruff check . --fix
ruff format .
```

**✅ Verificación:** `ruff check . --quiet` → exit 0, `ruff format --check . --quiet` → exit 0

**📝 Commit sugerido:** `chore: add ruff config and auto-format codebase`

---

### M0.2 — Pytest config (`pyproject.toml`) [0.5h]

**🔧 Archivo:** `compiler-bot/agentic_pipeline/pyproject.toml`

Agregar:

```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
asyncio_mode = "auto"
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = ["-v", "--tb=short", "--cov=agentic_pipeline", "--cov-report=term-missing"]
```

**▶️ Comando:** `pytest tests/ --collect-only | tail -3`

**✅ Verificación:** pytest descubre tests correctamente

**📝 Commit sugerido:** (incluir en commit anterior o separado) `chore: add pytest config`

---

### M0.3 — Fix 2.5: Parser fallback produce ActionNode [1h]

**🔧 Archivo:** `compiler-bot/agentic_pipeline/nodes/parser.py` — método `_build_ast_from_tokens()` (línea 440)

**Cambio:** Reemplazar producción de dictos planos por instancias de `ActionNode` dentro de un `ProjectNode`, serializando con `IRExportVisitor`.

```python
def _build_ast_from_tokens(self, tokens: list[dict]) -> dict:
    from agentic_pipeline.nodes.ast_nodes import ActionNode, ProjectNode
    project = ProjectNode("project")
    for t in tokens:
        cat = t.get("category", "")
        if cat == "action":
            project.add(ActionNode(
                action_type=t.get("type", "").lower(),
                target=t.get("value", ""),
            ))
        elif cat in ("entity", "domain"):
            entity_name = t.get("value", "")
            ent = EntityNode(entity_name)
            project.add(ent)
    return project.accept(IRExportVisitor())
```

**⚠️ Requiere:** Agregar import de `EntityNode` si no está importado (línea 18 ya importa `EntityNode`).

**✅ Verificación:**
```python
python -c "
from agentic_pipeline.nodes.parser import ParserGLR
from agentic_pipeline.state_models import StageContext, Stage
ctx = StageContext(stage=Stage.PARSER, input_data={})
p = ParserGLR.__new__(ParserGLR)
p._tokens = [{'category': 'action', 'type': 'CREATE', 'value': 'crea'}]
result = p._build_ast_from_tokens(p._tokens)
assert result['node_type'] == 'project'
assert result['children'][0]['node_type'] == 'action'
print('M0.3 OK')
"
```

---

### M0.4 — Fix 2.3: SemanticVisitor.visit_action() [0.5h]

**🔧 Archivo:** `compiler-bot/agentic_pipeline/nodes/semantic_analyzer.py` — clase `SemanticVisitor` (línea 108)

**Cambio:** Agregar método `visit_action()` en `SemanticVisitor` (dict-based):

```python
def visit_action(self, node: dict[str, Any]) -> None:
    target = node.get("target", "")
    if not target:
        self.errors.append(f"Action '{node.get('value', '')}' has no target")
    self.symbols.define(
        f"action:{node.get('value', 'unnamed')}",
        {"type": "action", "target": target},
    )
```

**✅ Verificación:**
```bash
python -c "
from agentic_pipeline.nodes.semantic_analyzer import SemanticVisitor
from agentic_pipeline.nodes.symbol_table import SymbolTable
v = SemanticVisitor(SymbolTable())
v.visit({'node_type': 'action', 'value': 'crea', 'target': 'modulo'})
assert len(v.warnings) == 0
print('M0.4 OK')
"
```

---

### M0.5 — Fix 2.4: IRBuilder branch "action" [0.5h]

**🔧 Archivo:** `compiler-bot/agentic_pipeline/nodes/ir_builder.py` — método `_build_node()` (línea 106)

**Cambio:** Agregar branch para `node_type == "action"`:

```python
if node_type == "action":
    target = data.get("target", "")
    comp = IRComponent(name=name if name != "unnamed" else data.get("value", "action"), component_type="action")
    return comp
```

**✅ Verificación:**
```bash
python -c "
from agentic_pipeline.nodes.ir_builder import IRBuilder
b = IRBuilder()
node = b._build_node({'value': 'crea', 'target': 'modulo', 'name': 'crea'}, 'action')
assert node is not None
assert node.component_type == 'action'
print('M0.5 OK')
"
```

---

### M0.6 — Fix 3.4: ActionExecutor propaga ir_tree + tasks [0.5h]

**🔧 Archivo:** `compiler-bot/agentic_pipeline/nodes/action_executor.py` — `act()` output_data (línea 117)

**Cambio:** Agregar `"ir_tree": ir_tree, "tasks": tasks` al dict `output_data`:

```python
output_data={
    "generated_files": generated_files,
    "errors": errors,
    "warnings": warnings,
    "task_count": len(tasks),
    "ir_tree": ir_tree,           # <-- NUEVO
    "tasks": tasks,               # <-- NUEVO
    "enriched": self._enriched or None,
},
```

---

### M0.7 — Fix 3.5: ActionExecutor fallback cuando tasks vacío [1h]

**🔧 Archivo:** `compiler-bot/agentic_pipeline/nodes/action_executor.py` — `act()` inicio (línea 65)

**Cambio:** Agregar fallback al inicio de `act()`:

```python
def act(self, plan: ActionPlan) -> StageOutput:
    ir_tree = self._input_data.get("ir_tree") if self._input_data else None
    commands = self._input_data.get("commands", []) if self._input_data else []
    tasks = self._input_data.get("tasks", []) if self._input_data else []
    enriched = self._input_data.get("enriched", {}) if self._input_data else {}
    goal_tree = self._input_data.get("goal_tree") if self._input_data else None

    # Fallback: construir tareas desde goal_tree si tasks vacío
    if not tasks and goal_tree:
        subtasks = goal_tree.get("subtasks", [])
        tasks = [{
            "id": s["id"],
            "description": s["description"],
            "target": "nestjs",
        } for s in subtasks]
        commands = [{
            "task_id": s["id"],
            "type": "scaffold",
            "path": f"modules/{enriched.get('slots', {}).get('nombre', 'app')}",
        } for s in subtasks]

    # ... resto del método igual
```

---

### M0.8 — Import consistency (Q6) + ruff [3.5h]

**▶️ Comandos:**
```bash
cd compiler-bot/agentic_pipeline
# Ordenar imports automáticamente
ruff check . --fix --select I
# Reemplazar imports relativos por absolutos en nodes/*.py (manual)
# ruff ya ordena, pero no convierte relativos → absolutos automáticamente
# Revisar cada archivo en nodes/ y reemplazar:
#   from .lexer import Lexer  →  from agentic_pipeline.nodes.lexer import Lexer
#   from ..base_stage import  →  from agentic_pipeline.base_stage import
```

**🔧 Archivos a modificar:** ~15 archivos en `nodes/`, `agents/`, `prompt_chain/`
**⚠️ Excepción:** `__init__.py` de subpaquetes puede mantener relativos

**✅ Verificación:** `ruff check . --quiet` → exit 0, `git grep "from \." -- "*.py" | grep -v __init__` → 0 matches

---

### M0.9 — Eliminar dead code (P2) [1.5h]

**🗑️ Eliminar:** `compiler-bot/agentic_pipeline/nodes/requirement_decomposer.py`
**🔧 Modificar:** `compiler-bot/agentic_pipeline/state_models.py` — eliminar `REQUIREMENT_DECOMPOSER` del enum `Stage`
**🔧 Modificar:** `compiler-bot/agentic_pipeline/nodes/__init__.py` — eliminar import si existe

**✅ Verificación:**
```bash
git grep "requirement_decomposer" | grep -v test | grep -v "\.git"
# Debe mostrar 0 resultados (o solo referencias en git history)
ruff check . --quiet
pytest tests/ -v --tb=short | tail -5
```

**📝 Commit sugerido para M0:**
```
feat: complete pipeline fixes (ActionNode, SemanticVisitor, IRBuilder, ActionExecutor)
chore: add ruff and pytest config
chore: enforce absolute imports
chore: remove requirement_decomposer dead code
```

### ✅ Criterio de aceptación M0

```bash
ruff check . --quiet && echo "ruff OK"
ruff format --check . --quiet && echo "format OK"
pytest tests/ -v --tb=short --cov=agentic_pipeline | tail -10
# Output: 463+ tests passed, 0 errors, >80% coverage

python -m agentic_pipeline.main -p "crea modulo pagos en nestjs" --debug 2>&1 | grep -E "tokens_count=|files_generated=|task_count="
# Output esperado:
# tokens_count >= 3 (CREATE + PAYMENT + NESTJS)
# task_count > 0
# files_generated > 0
```

---

## 3. M1 — API + Observabilidad (22h)

> **Duración:** ~3 días  
> **Objetivo:** Pipeline expuesto vía HTTP + calidad de código + auditoría

### M1.1 — HTTP Wrapper (127_PROP) [6h]

**📄 Crear:** `compiler-bot/agentic_pipeline/http_handler.py`

Contenido: clases `PipelineInput`, `PipelineResult`, `StageInfo`, `PipelineRequestHandler` con métodos:
- `_parse_request(req) → PipelineInput`
- `_execute(inp) → PipelineResult` (3 modos: full, loop, debug)
- `handle(req) → PipelineResult`
- `handle_request(req, res) → None`

**📄 Crear:** `compiler-bot/agentic_pipeline/api/fastapi_app.py`

```python
from fastapi import FastAPI, Request
from agentic_pipeline.http_handler import PipelineRequestHandler

app = FastAPI(title="RECPL Compiler API")
handler = PipelineRequestHandler()

@app.post("/api/pipeline")
async def run_pipeline(request: Request):
    return await handler.handle(request)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0"}
```

**🔧 Modificar:** `pyproject.toml` — agregar dependencia `"fastapi>=0.115.0"` y `"uvicorn>=0.30.0"`

**✅ Verificación:**
```bash
python -c "
from agentic_pipeline.http_handler import PipelineRequestHandler
h = PipelineRequestHandler()
result = h.handle({'prompt': 'crea modulo'})
print(f'success={result.success}, files={len(result.data.get(\"generated_files\",[]))}}')
"
```

**📝 Commit:** `feat: add HTTP request handler wrapper for RECPL pipeline`

---

### M1.2 — Renombrar ParserGLR a LarkParser (P3) [2h]

**🔧 Modificar:** `compiler-bot/agentic_pipeline/nodes/parser.py` — `class ParserGLR` → `class LarkParser`
**🔧 Modificar:** `compiler-bot/agentic_pipeline/orchestrator.py` — `NODE_MAP` y import
**🔧 Modificar:** tests que referencien `ParserGLR`

**▶️ Comando:**
```bash
git grep "ParserGLR" -- "*.py" | grep -v __pycache__
# Reemplazar todas las ocurrencias
```

**✅ Verificación:** `git grep "ParserGLR" -- "*.py"` → 0 matches

**📝 Commit:** `refactor: rename ParserGLR to LarkParser (Earley algorithm, not GLR)`

---

### M1.3 — __init__.py exports (Q3) [3h]

**🔧 Modificar** `compiler-bot/agentic_pipeline/nodes/__init__.py`:

```python
from agentic_pipeline.nodes.lexer import Lexer
from agentic_pipeline.nodes.parser import LarkParser
from agentic_pipeline.nodes.semantic_analyzer import SemanticAnalyzer
from agentic_pipeline.nodes.ir_generator import IRGenerator
from agentic_pipeline.nodes.reasoning_engine import ReasoningEngine
from agentic_pipeline.nodes.action_executor import ActionExecutor
from agentic_pipeline.nodes.ui_generator import UIGenerator
from agentic_pipeline.nodes.validator import ValidatorPipeline

__all__ = [
    "Lexer", "LarkParser", "SemanticAnalyzer", "IRGenerator",
    "ReasoningEngine", "ActionExecutor", "UIGenerator", "ValidatorPipeline",
]
```

**🔧 Modificar** `compiler-bot/agentic_pipeline/nlp/__init__.py`, `providers/__init__.py`, `grammars/__init__.py` — similar

**✅ Verificación:**
```bash
python -c "from agentic_pipeline.nodes import LarkParser; print('OK')"
python -c "from agentic_pipeline.nlp import IntentClassifier; print('OK')" 2>/dev/null || echo "NLP no tiene aun"
```

**📝 Commit:** `chore: add __init__.py exports for all subpackages`

---

### M1.4 — SRP feedback_loop → observers/ + optimizer/ (Q4) [6h]

**📄 Crear directorio:** `compiler-bot/agentic_pipeline/observers/`
**📄 Crear:** `compiler-bot/agentic_pipeline/observers/__init__.py`
**📄 Crear:** `compiler-bot/agentic_pipeline/observers/metrics_observer.py`
**📄 Crear:** `compiler-bot/agentic_pipeline/observers/debug_observer.py`
**📄 Crear:** `compiler-bot/agentic_pipeline/observers/prompt_optimizer_observer.py`
**📄 Crear:** `compiler-bot/agentic_pipeline/observers/dashboard_observer.py`
**📄 Crear:** `compiler-bot/agentic_pipeline/optimizer.py`
**🔧 Modificar:** `compiler-bot/agentic_pipeline/feedback_loop.py` — conservar solo `FeedbackLoop` y `GlobalFeedbackLoop`
**🔧 Modificar:** `compiler-bot/agentic_pipeline/base_stage.py` — actualizar import de `MetricsObserver`

**Estrategia:**
1. Crear archivos nuevos con el contenido de cada clase (extraído de feedback_loop.py)
2. En feedback_loop.py, eliminar las clases movidas y dejar imports de redirección O eliminar las clases y dejar solo FeedbackLoop/GlobalFeedbackLoop
3. Actualizar imports en base_stage.py y otros archivos que importen desde feedback_loop

**✅ Verificación:**
```bash
ruff check . --quiet
pytest tests/ -v --tb=short | tail -10
# Todos los tests deben pasar (los imports actualizados)
```

**📝 Commit:** `refactor: split feedback_loop.py into observers/ package and optimizer.py (SRP)`

---

### M1.5 — Type hints concretos (Q5) [4h]

**🔧 Modificar:** `compiler-bot/agentic_pipeline/feedback_loop.py`, `observers/*.py`, `optimizer.py`

**Cambio:** Reemplazar `Any` con tipos concretos en métodos públicos:

```python
# En lugar de:
def record(self, stage: str, metrics: dict[str, Any]) -> None:

# Usar TypedDict:
from typing import TypedDict

class StageMetrics(TypedDict, total=False):
    duration_seconds: float
    success: bool
    error: str | None
    tokens_count: int
    files_generated: int
    task_count: int

def record(self, stage: str, metrics: StageMetrics) -> None:
```

**🔧 Crear (o modificar):** `compiler-bot/agentic_pipeline/metrics_store.py` — agregar `StageMetrics(TypedDict)`

**▶️ Comandos:**
```bash
mypy compiler-bot/agentic_pipeline/feedback_loop.py --ignore-missing-imports --strict
# Debe reportar 0 errores de Any no justificados (o lista documentada)
```

**📝 Commit:** `chore: add concrete type hints in feedback_loop and observers`

---

### M1.6 — AuditObserver (S3) [3h]

**📄 Crear:** `compiler-bot/agentic_pipeline/observers/audit_observer.py`

```python
from agentic_pipeline.prompt_chain.observer_base import StageObserver, StageEvent

class AuditObserver(StageObserver):
    """Registra cada compilacion en un archivo JSON append-only."""

    def __init__(self, log_path: str = ".recpl_audit.log"):
        self._log_path = log_path

    def on_event(self, event: StageEvent) -> None:
        import json
        from datetime import datetime
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "stage": event.stage,
            "success": event.success,
            "duration": event.duration,
        }
        with open(self._log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
```

**🔧 Modificar:** `compiler-bot/agentic_pipeline/base_stage.py` — registrar `AuditObserver` en `PipelineStage.subject`

**✅ Verificación:**
```bash
python -c "
from agentic_pipeline.observers.audit_observer import AuditObserver
o = AuditObserver('/tmp/test_audit.log')
from agentic_pipeline.prompt_chain.observer_base import StageEvent
o.on_event(StageEvent(stage='test', duration=0.1, success=True))
import json
with open('/tmp/test_audit.log') as f:
    entry = json.loads(f.readline())
    assert entry['stage'] == 'test'
    print('AuditObserver OK')
"
```

**📝 Commit:** `feat: add AuditObserver for compile traceability`

---

### M1.7 — Cablear LLMCache (DT3) [4h]

**🔧 Modificar:** `compiler-bot/agentic_pipeline/prompt_chain/llm_backend.py` — método `generate()`

```python
async def generate(self, prompt: str, **kwargs) -> CommandResult:
    # Check cache first
    cache_key = hashlib.md5(prompt.encode()).hexdigest()
    if hasattr(self, '_cache') and self._cache:
        cached = self._cache.get(cache_key)
        if cached:
            return cached

    # ... llamada API existente ...

    # Store in cache
    if hasattr(self, '_cache') and self._cache:
        self._cache.set(cache_key, result)
    return result
```

**🔧 Modificar:** `compiler-bot/agentic_pipeline/prompt_chain/llm_cache.py` — verificar que tenga interfaz `get(key)`/`set(key, value)`/clear

**📝 Commit:** `feat: wire LLMCache into LLMBackend.generate()`

### ✅ Criterio de aceptación M1

```bash
# HTTP wrapper funcional
curl -X POST http://localhost:8000/api/pipeline \
  -H "Content-Type: application/json" \
  -d '{"prompt": "crea modulo usuarios"}' 2>/dev/null | python -m json.tool
# → Debe responder con success: true

# Observadores funcionando
python -c "
from agentic_pipeline.observer_base import StageSubject
# Solo debe existir un mecanismo pub/sub
from agentic_pipeline.prompt_chain.observer_base import StageSubject
print('StageSubject disponible')
"

# Tests pasando
pytest tests/ -v --tb=short --cov=agentic_pipeline | tail -5
```

---

## 4. M2 — Resiliencia + SOLID Básico (24h)

> **Duración:** ~3 días  
> **Objetivo:** Pipeline tolerante a fallos + contexto inmutable + modo offline

### M2.1 — CircuitBreaker + ExponentialBackoff (R1) [9.5h]

**📄 Crear:** `compiler-bot/agentic_pipeline/circuit_breaker.py`

```python
from enum import Enum
import time
from typing import Any, Callable

class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreakerOpenError(Exception):
    pass

class CircuitBreaker:
    def __init__(self, threshold: int = 5, timeout: float = 30.0):
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.threshold = threshold
        self.timeout = timeout
        self.last_failure_time: float = 0.0

    def call(self, fn: Callable) -> Any:
        if self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError()
        try:
            result = fn()
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.threshold:
                self.state = CircuitBreakerState.OPEN
            raise e

class ExponentialBackoff:
    def __init__(self, min_backoff: float = 1.0, max_backoff: float = 60.0, factor: float = 2.0, jitter: float = 0.1):
        self.min_backoff = min_backoff
        self.max_backoff = max_backoff
        self.factor = factor
        self.jitter = jitter

    def delay(self, attempt: int) -> float:
        import random
        backoff = min(self.min_backoff * (self.factor ** attempt), self.max_backoff)
        jitter = random.uniform(0, backoff * self.jitter)
        return backoff + jitter
```

**📄 Crear:** `compiler-bot/agentic_pipeline/tests/test_circuit_breaker.py` (tests unitarios)

**🔧 Modificar:** `compiler-bot/agentic_pipeline/prompt_chain/llm_backend.py` — integrar CircuitBreaker

**📝 Commit:** `feat: add CircuitBreaker and ExponentialBackoff for LLM resilience`

---

### M2.2 — StageExecutor aislamiento (R3) [5h]

**📄 Crear:** `compiler-bot/agentic_pipeline/stage_executor.py`

```python
import logging
from agentic_pipeline.base_stage import PipelineStage
from agentic_pipeline.state_models import StageOutput

logger = logging.getLogger(__name__)

class StageExecutor:
    async def execute(self, stage: PipelineStage, input_data: object) -> StageOutput:
        try:
            return stage.execute(input_data)
        except Exception as exc:
            logger.exception("Stage %s failed", stage.name)
            return StageOutput(
                stage=stage.context.stage,
                output_data={},
                success=False,
                error=str(exc),
                metrics={"exception": type(exc).__name__},
            )
```

**🔧 Modificar:** `compiler-bot/agentic_pipeline/orchestrator.py` — en `_make_node()`, usar `StageExecutor` en lugar de llamar `instance.execute()` directamente

```python
def _make_node(self, stage: Stage):
    executor = StageExecutor()
    cls = NODE_MAP[stage]
    async def node_fn(ctx: StageContext) -> dict:
        ctx.stage = stage
        ctx.config_overrides["output_dir"] = self._output_dir
        instance = cls(ctx)
        output = await executor.execute(instance, ctx.input_data)
        # ... resto igual
    return node_fn
```

**📝 Commit:** `feat: add StageExecutor for per-stage isolation`

---

### M2.3 — Modo offline / Graceful degradation (GD) [7h]

**🔧 Modificar:** `compiler-bot/agentic_pipeline/config.py` — agregar `offline: bool = False`
**🔧 Modificar:** `compiler-bot/agentic_pipeline/nodes/perception_unit.py` — modo offline: clasificar intent por reglas, no LLM
**🔧 Modificar:** `compiler-bot/agentic_pipeline/nodes/reasoning_engine.py` — modo offline: solo GoalTreePlanner heurístico
**🔧 Modificar:** CLI — agregar flag `--offline`

**📄 Crear:** `docs/offline_mode.md`

```markdown
# Modo Offline RECPL v2.0+

## ¿Qué funciona sin LLM?

| Stage | Con LLM | Sin LLM (offline) |
|-------|---------|-------------------|
| Intent classification | PerceptionUnit (LLM) | Reglas DFA (heurístico) |
| Planning | ReasoningEngine (LLM) | GoalTreePlanner (heurístico) |
| Preprocesador | — | Siempre determinista |
| Lexer | — | Siempre DFA |
| Parser | — | Siempre Lark |
| Semantic | — | Siempre Visitor |
| IR Generator | — | Siempre determinista |
| Synthesis | — | Siempre scaffold |
| UI Generator | — | Siempre con guarda |
| Validator | — | Siempre Chain of Responsibility |

## ¿Cómo usarlo?

```bash
python compiler-bot/agentic -p "crea modulo pagos" --offline
```
```

**📝 Commit:** `feat: add offline mode with graceful degradation`

---

### M2.4 — StageContext frozen (INM) [6.5h]

**🔧 Modificar:** `compiler-bot/agentic_pipeline/state_models.py`

```python
class StageContext(BaseModel):
    model_config = ConfigDict(frozen=True)
    mission_id: str = Field(default_factory=lambda: datetime.now().isoformat())
    stage: Stage
    input_data: Any
    previous_output: Optional[Any] = None
    config_overrides: dict = Field(default_factory=dict)
    last_error: Optional[str] = None

    def with_update(self, **kwargs) -> "StageContext":
        return self.model_copy(update=kwargs)
```

**🔧 Modificar** ~10 archivos en `nodes/*.py` que hacen `ctx.input_data = ...`:

```python
# Reemplazar:
ctx.stage = stage
ctx.input_data = nuevo_valor
ctx.config_overrides["output_dir"] = self._output_dir
ctx.last_error = error

# Por:
ctx = ctx.with_update(
    stage=stage,
    input_data=nuevo_valor,
    config_overrides={**ctx.config_overrides, "output_dir": self._output_dir},
)
```

**▶️ Verificación:**
```bash
python -c "
from agentic_pipeline.state_models import StageContext, Stage
ctx = StageContext(stage=Stage.INTENT, input_data='hola')
try:
    ctx.stage = Stage.PREPROCESSOR
    assert False, 'should be frozen'
except TypeError:
    print('M2.4 OK: frozen')

new_ctx = ctx.with_update(input_data='mundo')
assert new_ctx.input_data == 'mundo'
assert ctx.input_data == 'hola'
print('M2.4 OK: with_update works')
"
```

**📝 Commit:** `refactor: make StageContext frozen with with_update()`

### ✅ Criterio de aceptación M2

```bash
# Circuit breaker funcional
python -c "
from agentic_pipeline.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
cb = CircuitBreaker(threshold=3, timeout=0.1)
for i in range(3):
    try: cb.call(lambda: (_ for _ in ()).throw(Exception('fail')))
    except Exception: pass
assert cb.state.name == 'OPEN'
print('M2 OK: circuit breaker opens after 3 failures')
"

# StageContext frozen
python -c "
from agentic_pipeline.state_models import StageContext, Stage
from pydantic import ValidationError
ctx = StageContext(stage=Stage.INTENT, input_data='test')
try: ctx.stage = Stage.PREPROCESSOR
except TypeError: print('M2 OK: context frozen')
"

# Modo offline documentado
test -f docs/offline_mode.md && echo "M2 OK: offline docs exist"

# Todos los tests pasan
pytest tests/ -v --tb=short | tail -5
```

---

## 5. M3 — Arquitectura + Testing (24h)

> **Duración:** ~3 días  
> **Objetivo:** Interfaces segregadas + event bus unificado + tests de integración

### M3.1 — Interface Segregation (ISP) [8h]

**🔧 Modificar:** `compiler-bot/agentic_pipeline/base_stage.py`

```python
from abc import ABC, abstractmethod
from agentic_pipeline.state_models import AnalysisResult, ActionPlan, StageOutput

class Analyzable(ABC):
    @abstractmethod
    def analyze(self) -> AnalysisResult: ...

class Plannable(ABC):
    @abstractmethod
    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan: ...

class Executable(ABC):
    @abstractmethod
    def act(self, plan: ActionPlan) -> StageOutput: ...

class PipelineStage(Analyzable, Plannable, Executable, ABC):
    """Base class: all three interfaces for backward compatibility."""
    name: str = ""
    ...
```

**🔧 Modificar** 10 subclasses en `nodes/*.py` — implementar solo las interfaces que necesiten:

```python
# stages sin analyze (ej: lexer, parser) pueden implementar solo Executable
class Lexer(PipelineStage):
    # hereda analyze/reflect_and_plan de PipelineStage (default vacío)
    ...
```

**✅ Verificación:**
```bash
python -c "
from agentic_pipeline.base_stage import PipelineStage, Analyzable, Plannable, Executable
assert issubclass(PipelineStage, Analyzable)
assert issubclass(PipelineStage, Plannable)
assert issubclass(PipelineStage, Executable)
print('M3.1 OK: ISP interfaces defined')
"
```

**📝 Commit:** `refactor: add Analyzable, Plannable, Executable interfaces (ISP)`

---

### M3.2 — Unificar event buses (P5) [9h]

**🔧 Modificar:** `compiler-bot/agentic_pipeline/prompt_chain/observer_base.py` — `StageSubject` delega en `EventBus`

```python
from agentic_pipeline.agents.event_bus import EventBus

class StageSubject:
    def __init__(self):
        self._observers: list[StageObserver] = []
        self._bus = EventBus()

    def attach(self, observer: StageObserver) -> None:
        self._observers.append(observer)

    def detach(self, observer: StageObserver) -> None:
        self._observers.remove(observer)

    def notify(self, event: StageEvent) -> None:
        # Notificar observers locales
        for observer in self._observers:
            observer.on_event(event)
        # Publicar en EventBus global
        self._bus.publish(event.stage, event)
```

**🔧 Modificar:** imports en `feedback_loop.py`, `base_stage.py`, `handler_base.py`, `orchestrator.py`

**✅ Verificación:**
```bash
python -c "
from agentic_pipeline.prompt_chain.observer_base import StageSubject
from agentic_pipeline.agents.event_bus import EventBus
subject = StageSubject()
# subject internamente usa EventBus
assert hasattr(subject, '_bus')
assert isinstance(subject._bus, EventBus)
print('M3.2 OK: event buses unified')
"
```

**📝 Commit:** `refactor: unify StageSubject and EventBus into single pub/sub mechanism`

---

### M3.3 — Tests integración agent-pipeline (T1) [7h]

**📄 Crear:** `compiler-bot/agentic_pipeline/tests/conftest.py` — fixture `full_pipeline`
**📄 Crear:** `compiler-bot/agentic_pipeline/tests/test_agent_pipeline_integration.py`

```python
import pytest
from agentic_pipeline.orchestrator import AgentOrchestrator

@pytest.fixture
def full_pipeline():
    return AgentOrchestrator()

@pytest.mark.asyncio
async def test_direct_mode_produces_output(full_pipeline):
    result = await full_pipeline.run("crea modulo usuarios")
    assert result.get("success", False)
    output = result.get("output", {})
    assert isinstance(output, dict)

@pytest.mark.asyncio
async def test_same_prompt_consistent_output(full_pipeline):
    result1 = await full_pipeline.run("crea modulo pagos")
    result2 = await full_pipeline.run("crea modulo pagos")
    # El output debe ser determinista (mismos archivos generados)
    assert result1.get("success") == result2.get("success")
```

**✅ Verificación:** `pytest tests/test_agent_pipeline_integration.py -v --tb=short`

**📝 Commit:** `test: add integration tests for agent-pipeline modes`

### ✅ Criterio de aceptación M3

```bash
# ISP implementado
python -c "
from agentic_pipeline.nodes.lexer import Lexer
from agentic_pipeline.base_stage import Analyzable, Plannable, Executable
assert isinstance(Lexer.__new__(Lexer), Executable)
print('M3 OK: Lexer implements Executable')
"

# Event bus unificado
python -c "
from agentic_pipeline.prompt_chain.observer_base import StageSubject
from agentic_pipeline.agents.event_bus import EventBus
# No debe haber StageSubject sin EventBus
"

# Tests de integración
pytest tests/test_agent_pipeline_integration.py -v --tb=short
# Output: 2+ passed
```

---

## 6. M4 — Rendimiento + Seguridad (14h)

> **Duración:** ~2 días  
> **Objetivo:** Fixtures compartidas + seguridad + modelos diferenciados

### M4.1 — Fixtures compartidas (T2) [4.5h]

**🔧 Modificar:** `compiler-bot/agentic_pipeline/tests/conftest.py`

Agregar fixtures:
- `mock_context` — `StageContext(stage=Stage.INTENT, input_data="test")`
- `mock_ir_project` — `IRProject("test")` con hijos
- `temp_output_dir` — `tmp_path` de pytest
- `sample_prompts` — dict con prompts de prueba
- `expected_dashboard_files` — lista de archivos esperados

**✅ Verificación:** `pytest tests/ --fixtures | grep -E "mock_|sample_|temp_"` → fixtures listadas

**📝 Commit:** `test: add shared fixtures in conftest.py`

---

### M4.2 — SecurityScanner (S1) [8.5h]

**📄 Crear:** `compiler-bot/agentic_pipeline/security/policies.py`

```python
BLOCKED_PATTERNS = [
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\bos\.system\s*\(",
    r"\bsubprocess\.call\s*\(",
    r"\bpickle\.loads\s*\(",
    r"\b__import__\s*\(",
]
```

**📄 Crear:** `compiler-bot/agentic_pipeline/security/bandit_scanner.py`

```python
class BanditScanner(StageObserver):
    def on_event(self, event: StageEvent) -> None:
        if event.stage == "synthesis":
            for filepath in event.output.get("generated_files", []):
                content = Path(filepath).read_text()
                for pattern in BLOCKED_PATTERNS:
                    if re.search(pattern, content):
                        event.metadata["security_alert"] = f"Blocked pattern in {filepath}"
```

**🔧 Modificar:** `compiler-bot/agentic_pipeline/nodes/validator.py` — integrar SecurityScanner como eslabón final de Chain of Responsibility

**📝 Commit:** `feat: add SecurityScanner with bandit integration`

---

### M4.3 — TokenBucket rate limiter (S4) [3h]

**📄 Crear:** `compiler-bot/agentic_pipeline/security/token_bucket.py`

```python
import time
import threading

class TokenBucket:
    def __init__(self, capacity: int = 60, refill_rate: float = 1.0):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = threading.Lock()

    def consume(self, tokens: int = 1) -> bool:
        with self._lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
```

**🔧 Modificar:** `compiler-bot/agentic_pipeline/prompt_chain/llm_backend.py` — integrar TokenBucket

**📝 Commit:** `feat: add TokenBucket rate limiter for LLM API calls`

---

### M4.4 — Modelos LLM diferenciados (E2) [3h]

**🔧 Modificar:** `compiler-bot/agentic_pipeline/config.py`

```python
stage_models: dict[str, str] = {
    "preprocess": "gpt-4o-mini",
    "intent": "gpt-4o",
    "plan": "gpt-4o",
    "reasoning": "gpt-4o",
    "generate": "gpt-4o",
    "verify": "gpt-4o",
    "format": "gpt-4o-mini",
}
```

**🔧 Modificar:** `compiler-bot/agentic_pipeline/prompt_chain/llm_backend.py` — aceptar `model` override por llamada

**📝 Commit:** `feat: add differentiated LLM models per pipeline stage`

### ✅ Criterio de aceptación M4

```bash
# SecurityScanner detecta código malicioso
python -c "
from agentic_pipeline.security.policies import BLOCKED_PATTERNS
import re
code = 'eval(x)'
assert any(re.search(p, code) for p in BLOCKED_PATTERNS)
print('M4 OK: bloquea eval()')
"

# TokenBucket funcional
python -c "
from agentic_pipeline.security.token_bucket import TokenBucket
b = TokenBucket(capacity=5, refill_rate=10)
for i in range(5):
    assert b.consume(1)
assert not b.consume(1)  # vacio
print('M4 OK: token bucket')
"

# Modelos diferenciados
python -c "
from agentic_pipeline.config import PipelineConfig
c = PipelineConfig()
print(f'M4 OK: stage_models={c.stage_models}')
"

# Smoke test final
pytest tests/ -v --tb=short --cov=agentic_pipeline | tail -10
```

---

## 7. Resumen de Commits por Sprint

### M0 (7 commits)
```
1. chore: add ruff config and auto-format codebase
2. chore: add pytest config
3. feat: complete pipeline fixes (parser ActionNode, SemanticVisitor, IRBuilder, ActionExecutor)
4. chore: enforce absolute imports across codebase
5. chore: remove requirement_decomposer dead code
6. test: verify pipeline produces scaffolding with "crea modulo"
```

### M1 (8 commits)
```
1. feat: add HTTP request handler wrapper (PipelineRequestHandler)
2. feat: add FastAPI app for RECPL pipeline API
3. refactor: rename ParserGLR to LarkParser
4. chore: add __init__.py exports for all subpackages
5. refactor: split feedback_loop.py into observers/ package (SRP)
6. chore: add concrete type hints
7. feat: add AuditObserver for compile traceability
8. feat: wire LLMCache into LLMBackend.generate()
```

### M2 (5 commits)
```
1. feat: add CircuitBreaker and ExponentialBackoff
2. feat: add StageExecutor for per-stage isolation
3. feat: add offline mode with graceful degradation
4. refactor: make StageContext frozen with with_update()
5. docs: add offline_mode.md
```

### M3 (3 commits)
```
1. refactor: add Analyzable, Plannable, Executable interfaces (ISP)
2. refactor: unify StageSubject and EventBus
3. test: add integration tests for agent-pipeline modes
```

### M4 (5 commits)
```
1. test: add shared fixtures in conftest.py
2. feat: add SecurityScanner with bandit integration
3. feat: add TokenBucket rate limiter
4. feat: add differentiated LLM models per stage
5. chore: update CHANGELOG.md
```

---

## 8. Checklist de Verificación Progresiva

Ejecutar después de CADA commit:

```bash
# Calidad
ruff check . --quiet || echo "FAIL: ruff"
ruff format --check . --quiet || echo "FAIL: format"

# Tests
pytest tests/ -v --tb=short --cov=agentic_pipeline --cov-report=term-missing 2>&1 | tail -10

# Smoke (después de M0)
python -m agentic_pipeline.main -p "crea modulo" --debug 2>&1 | grep -E "tokens_count=|files_generated=|task_count="
```

---

## 9. Matriz de Responsabilidades

| Sprint | Backend Python | DevOps/CI | QA/Tests |
|--------|---------------|-----------|----------|
| M0 | Parser, IRBuilder, SemanticVisitor fixes | Ruff config, pytest config | Verificar smoke test |
| M1 | HTTP wrapper, rename, SRP | Dependencias FastAPI | Verificar endpoint HTTP |
| M2 | CircuitBreaker, StageExecutor, INM | CI pipeline con --offline | Test modo offline |
| M3 | ISP interfaces, EventBus unification | — | Tests integración |
| M4 | SecurityScanner, TokenBucket | — | Fixtures, benchmarks |

---

## 10. Notas de Ejecución

### Errores comunes y soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| `ruff check` falla después de M0.3-M0.5 | Los cambios en parser/semantic/IR pueden introducir violaciones | Ejecutar `ruff check . --fix` después de cada cambio |
| `pytest` falla después de M3.2 (event buses) | Los imports de `StageSubject` cambiaron | Buscar `from.*observer_base import` y actualizar |
| `ImportError` después de M1.4 (SRP) | `base_stage.py` importa `MetricsObserver` desde `feedback_loop` | Actualizar import a `from agentic_pipeline.observers import MetricsObserver` |
| Tests lentos después de M2.1 | CircuitBreaker con timeout de 30s en tests | Usar timeout bajo (0.1s) en tests |

### Orden de merge

```
main ← M0 ← M1 ← M2 ← M3 ← M4
       └── Commits atómicos (no squash)
```

Cada sprint se mergea a `main` cuando su criterio de aceptación está verde. No se requiere esperar al sprint siguiente para mergear.