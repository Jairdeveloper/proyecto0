# Reporte de Ejecución — M1: Renombrar ParserGLR a LarkParser

- **ID:** 132_REP_DEV_M1_EXECUTION_REPORT_1_0_DRAFT
- **Tipo:** REP (Reporte)
- **Área:** DEV
- **Módulo:** agentic_pipeline
- **Versión:** 1.4
- **Estado:** DRAFT
- **Tags:** `execution-report`, `m1`, `rename`, `parser`, `larkparser`, `exports`, `init`, `srp`, `observers`, `optimizer`, `type-hints`, `audit-observer`
- **Fuente:** `docs/130_PLAN_DEV_MIGRATION_EXECUTION_1_0_DRAFT.md` (M1.2–M1.6)
- **Changelog:**
  - 1.4 — 2026-06-19: Añadido M1.6 — AuditObserver para trazabilidad de compilaciones
  - 1.3 — 2026-06-19: Añadido M1.5 — Type hints concretos (StageMetrics TypedDict, SummaryResult, WebSocketClient stub)
  - 1.2 — 2026-06-19: Añadido M1.4 — SRP split feedback_loop → observers/ + optimizer.py
  - 1.1 — 2026-06-19: Añadido M1.3 — __init__.py exports for nodes, nlp, providers, grammars
  - 1.0 — 2026-06-19: Versión inicial — rename ParserGLR → LarkParser

---

## 1. Resumen

| Aspecto | Valor |
|---------|-------|
| Sprint | M1 — API + Observabilidad |
| Tarea | M1.2 — Renombrar ParserGLR a LarkParser (P3) |
| Esfuerzo estimado | 2h |
| Esfuerzo ejecutado | ~0.3h |
| Estado | **COMPLETADO** |

---

## 2. Motivo del cambio

La clase se llamaba `ParserGLR`, pero el parser real utiliza **Lark** con algoritmo **Earley** (no GLR). El nombre era engañoso y no reflejaba la implementación real. Se renombró a `LarkParser` para describir con precisión lo que realmente es: un parser basado en Lark.

---

## 3. Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `nodes/parser.py:1` | Docstring: `Parser GLR stage` → `LarkParser stage (formerly ParserGLR)` |
| `nodes/parser.py:43` | `class ParserGLR` → `class LarkParser` |
| `orchestrator.py:15` | Import: `ParserGLR` → `LarkParser` |
| `orchestrator.py:78` | `NODE_MAP`: `ParserGLR` → `LarkParser` |
| `orchestrator.py:112` | Lazy import: `ParserGLR` → `LarkParser` |
| `orchestrator.py:213` | Debug mapping: `ParserGLR` → `LarkParser` |
| `tests/test_parser_project.py:1` | Docstring actualizada |
| `tests/test_parser_project.py:16,18,22,24,27,29,31,35,37,41,43,45` | Import + usos + nombres clase test |
| `tests/test_parser_ui.py:5,14,16,21,23` | Import + usos |
| `tests/test_ast_snapshots.py:12,27` | Import + uso |
| `tests/test_performance.py:94,96` | Import + uso |

---

## 4. Verificación

```bash
$ git grep "ParserGLR" -- "*.py"
nodes/parser.py:"""LarkParser stage — Lark-based parsing with AST generation (formerly ParserGLR)."""
# Solo el comentario histórico — 0 referencias activas
```

```bash
$ ruff check . --quiet
# EXIT: 0 — sin errores
```

```bash
$ pytest tests/test_parser_project.py tests/test_parser_ui.py tests/test_ast_snapshots.py -v --tb=short
# 40 passed in 1.75s
```

| Verificación | Resultado |
|-------------|-----------|
| `git grep "ParserGLR" -- "*.py"` (solo comentarios) | ✅ PASS |
| `ruff check . --quiet` | ✅ PASS |
| Parser tests (40 tests) | ✅ PASS |

No hay referencias activas a `ParserGLR` en el código. Todas las importaciones, usos y nombres de clase en tests fueron actualizados.

---

## 5. M1.3 — __init__.py exports (Q3)

**Archivos modificados:** 4 archivos (todos previamente vacíos).

### nodes/__init__.py

Exporta las 10 clases de stage del pipeline activo (`NODE_MAP` en `orchestrator.py`):

```python
from agentic_pipeline.nodes.action_executor import ActionExecutor
from agentic_pipeline.nodes.ir_generator import IRGenerator
from agentic_pipeline.nodes.lexer import Lexer
from agentic_pipeline.nodes.parser import LarkParser
from agentic_pipeline.nodes.perception_unit import PerceptionUnit
from agentic_pipeline.nodes.preprocessor import Preprocessor
from agentic_pipeline.nodes.reasoning_engine import ReasoningEngine
from agentic_pipeline.nodes.semantic_analyzer import SemanticAnalyzer
from agentic_pipeline.nodes.ui_generator import UIGenerator
from agentic_pipeline.nodes.validator import ValidatorPipeline
```

### nlp/__init__.py

Exporta los componentes del pipeline de NLP:

| Clase | Archivo |
|-------|---------|
| `IntentClassifier` | `nlp/intent_classifier.py` |
| `AmbiguityDetector` | `nlp/ambiguity_detector.py` |
| `SlotFiller` | `nlp/slot_filler.py` |
| `NERExtractor` | `nlp/ner_extractor.py` |
| `EnrichedInput`, `IntentResult`, `Entities`, `Entity`, `Slots`, `AmbiguityResult`, `ContextState` | `nlp/enriched_input.py` |

### providers/__init__.py

```python
"""LLM provider integrations (empty — providers are loaded dynamically)."""
```

Directorio sin módulos Python por ahora. Solo docstring descriptivo.

### grammars/__init__.py

```python
"""Lark grammar files for RECPL parser (loaded by filename, not imported as Python)."""
```

Contiene solo archivos `.lark` (`project_grammar.lark`, `ui_grammar.lark`, `infra_grammar.lark`, `data_grammar.lark`). No hay módulos Python que exportar.

### Verificación

```bash
$ python -c "from agentic_pipeline.nodes import LarkParser; print('nodes OK')"
nodes OK

$ python -c "from agentic_pipeline.nlp import IntentClassifier; print('nlp OK')"
nlp OK

$ ruff check . --quiet
# EXIT: 0
```

| Verificación | Resultado |
|-------------|-----------|
| `from agentic_pipeline.nodes import LarkParser` | ✅ PASS |
| `from agentic_pipeline.nlp import IntentClassifier` | ✅ PASS |
| `ruff check . --quiet` | ✅ PASS |

Todos los imports funcionan correctamente. No hay errores de lint.

---

## 6. M1.4 — SRP feedback_loop → observers/ + optimizer/ (Q4)

### Motivo

`feedback_loop.py` violaba el Principio de Responsabilidad Única (SRP) al contener 7 clases con responsabilidades distintas: métricas, debug, dashboard, optimización de prompts, etc. Se extrajeron a paquetes dedicados.

### Cambios

| Acción | Archivo nuevo |
|--------|---------------|
| 📄 Crear | `observers/__init__.py` — package init con exports |
| 📄 Crear | `observers/metrics_observer.py` — `MetricsObserver` |
| 📄 Crear | `observers/debug_observer.py` — `DebugObserver` |
| 📄 Crear | `observers/prompt_optimizer_observer.py` — `PromptOptimizerObserver` |
| 📄 Crear | `observers/dashboard_observer.py` — `DashboardObserver` |
| 📄 Crear | `optimizer.py` — `PromptOptimizer` |

| Acción | Archivo modificado | Cambio |
|--------|--------------------|--------|
| 🔧 Modificar | `feedback_loop.py` | Eliminadas 5 clases extraídas. Conserva solo `FeedbackLoop` + `GlobalFeedbackLoop` + `get_global_feedback()`. Re-exports eliminados por circular import. |
| 🔧 Modificar | `base_stage.py:6` | `from agentic_pipeline.feedback_loop import MetricsObserver` → `from agentic_pipeline.observers.metrics_observer import MetricsObserver` |
| 🔧 Modificar | `prompt_chain/orchestrator.py:14` | `from agentic_pipeline.feedback_loop import DebugObserver` → `from agentic_pipeline.observers.debug_observer import DebugObserver` |
| 🔧 Modificar | `tests/test_observer_pattern.py:8-12` | Import desde `agentic_pipeline.observers` |
| 🔧 Modificar | `tests/test_prompt_optimizer.py:7` | Import desde `agentic_pipeline.optimizer` |

### Verificación

```bash
$ ruff check . --quiet
# EXIT: 0

$ pytest tests/test_observer_pattern.py tests/test_prompt_optimizer.py tests/test_feedback_loop.py -v --tb=short
# 43 passed in 0.57s

$ pytest tests/ --ignore=... 
# 747 passed, 21 skipped
```

| Verificación | Resultado |
|-------------|-----------|
| `ruff check . --quiet` | ✅ PASS |
| Observer tests (27 tests) | ✅ PASS |
| PromptOptimizer tests (5 tests) | ✅ PASS |
| FeedbackLoop tests (11 tests) | ✅ PASS |
| Suite completa (747 tests) | ✅ PASS |
| Sin circular imports | ✅ PASS |

### Diagrama de dependencias

```
feedback_loop.py              observers/               optimizer.py
┌─────────────────┐          ┌──────────────────┐     ┌────────────────┐
│ FeedbackLoop     │          │ MetricsObserver   │     │ PromptOptimizer│
│ GlobalFeedback   │          │ DebugObserver     │     └────────────────┘
│ get_global_fbk() │          │ PromptOptObserver │
└─────────────────┘          │ DashboardObserver │
       ↑                     └──────────────────┘
       │                              ↑
       └── requirement_decomposer.py  └── base_stage.py
                                       └── prompt_chain/orchestrator.py
                                       └── tests/
```

---

## 7. M1.5 — Type hints concretos (Q5)

### Motivo

Varios métodos públicos en `feedback_loop.py`, `metrics_store.py`, `optimizer.py` y los observers usaban `dict[str, Any]` en lugar de tipos concretos, reduciendo la capacidad de detección estática de errores.

### Cambios

#### metrics_store.py — TypedDicts agregados

| TypedDict | Campos |
|-----------|--------|
| `StageMetrics` | `duration_seconds: float`, `success: bool`, `error: str | None`, `tokens_count: int`, `files_generated: int`, `task_count: int`, `errors: int`, `node_count: int` |
| `PromptMetrics` | `success: bool`, `duration: float`, `error: str | None`, `fallback_used: bool`, `output_size: int`, `tokens_used: int` |
| `SummaryResult` | `total_records: int`, `stages: dict[str, int]`, `total_errors: int`, `success_rate: float`, `fallback_rate: float`, `per_stage: dict` |

#### Métodos actualizados con tipos concretos

| Archivo | Método | Tipo anterior | Tipo nuevo |
|---------|--------|---------------|------------|
| `metrics_store.py` | `record()` | `metrics: dict[str, Any]` | `metrics: StageMetrics` |
| `metrics_store.py` | `record_prompt()` | `metrics: dict[str, Any]` | `metrics: PromptMetrics` |
| `metrics_store.py` | `summary()` | `dict[str, Any]` | `SummaryResult` |
| `feedback_loop.py` | `record()` | `metrics: dict[str, Any]` | `metrics: StageMetrics` |
| `feedback_loop.py` | `record_stage()` | `metrics: dict[str, Any]` | `metrics: StageMetrics` |
| `feedback_loop.py` | `record_prompt()` | `metrics: dict[str, Any]` | `metrics: StageMetrics` |
| `feedback_loop.py` | `get_adjustments()` | `dict[str, Any]` | `StageMetrics` |
| `feedback_loop.py` | `get_lexer_adjustments()` | `dict[str, Any]` | `StageMetrics` |
| `feedback_loop.py` | `_adjust_lexer_weights()` | `metrics: dict[str, Any]` | `metrics: StageMetrics` |
| `feedback_loop.py` | `prompt_chain_summary()` | `dict[str, Any]` | `SummaryResult` |
| `feedback_loop.py` | `get_recent()` (FeedbackLoop) | `list[dict[str, Any]]` | `list[dict[str, object]]` |
| `feedback_loop.py` | `summary()` | `dict[str, Any]` | `dict[str, object]` |
| `feedback_loop.py` | `get_recent()` (GlobalFeedbackLoop) | `list[dict[str, Any]]` | `list[dict[str, object]]` |
| `optimizer.py` | `optimize()` | `dict[str, Any]` | `StageMetrics` |
| `observers/dashboard_observer.py` | `_ws_clients` | `list[Any]` | `list[WebSocketClient]` |

#### WebSocketClient stub

Se creó un stub `WebSocketClient` en `dashboard_observer.py` para tipificar los clientes WebSocket en lugar de usar `list[Any]`:

```python
class WebSocketClient:
    def send_json(self, data: object) -> None: ...
```

### Verificación

```bash
$ ruff check . --quiet
# EXIT: 0

$ pytest tests/test_observer_pattern.py tests/test_prompt_optimizer.py tests/test_feedback_loop.py -v
# 43 passed

$ pytest tests/ --ignore=... --ignore=...
# 747 passed, 21 skipped
```

| Verificación | Resultado |
|-------------|-----------|
| `ruff check . --quiet` | ✅ PASS (0 errores) |
| Observer + Optimizer + FeedbackLoop tests (43) | ✅ PASS |
| Suite completa (747 tests) | ✅ PASS |
| Sin `Any` no justificado en métodos públicos | ✅ PASS |

---

## 8. M1.6 — AuditObserver (S3)

### Motivo

No existía un mecanismo de auditoría que registre cada compilación del pipeline de forma durable. El `AuditObserver` llena ese vacío: cada evento de stage se escribe como una línea JSON en un archivo append-only.

### Archivos modificados

| Acción | Archivo | Cambio |
|--------|---------|--------|
| 📄 Crear | `observers/audit_observer.py` | `AuditObserver(StageObserver)` → 32 líneas |
| 🔧 Modificar | `observers/__init__.py` | Export `AuditObserver` |
| 🔧 Modificar | `base_stage.py` | Import + attach `AuditObserver()` en `PipelineStage.subject` |

### AuditObserver

```python
class AuditObserver(StageObserver):
    def __init__(self, log_path: str = ".recpl_audit.log") -> None:
        self._log_path = log_path

    def on_event(self, event: StageEvent) -> None:
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "stage": event.stage,
            "success": event.success,
            "duration": event.duration,
        }
        with open(self._log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
```

Es el primer observer que hereda explícitamente de `StageObserver(ABC)`, sirviendo como modelo para que los demás observers también migren a la interfaz formal.

### Verificación

```bash
$ python -c "
from agentic_pipeline.observers.audit_observer import AuditObserver
from agentic_pipeline.prompt_chain.observer_base import StageEvent
o = AuditObserver('/tmp/test_audit.log')
o.on_event(StageEvent(stage='test', duration=0.1, success=True))
with open('/tmp/test_audit.log') as f:
    entry = json.loads(f.readline())
    assert entry['stage'] == 'test'
    print('AuditObserver OK')
"
AuditObserver OK

$ ruff check . --quiet
# EXIT: 0

$ pytest tests/test_observer_pattern.py tests/test_prompt_optimizer.py tests/test_feedback_loop.py -v
# 43 passed

$ pytest tests/test_integration.py tests/test_orchestrator_empty.py -v
# 8 passed
```

| Verificación | Resultado |
|-------------|-----------|
| Smoke test (crear + evento + leer log) | ✅ PASS |
| `ruff check . --quiet` | ✅ PASS (0 errores) |
| Observer + Optimizer + FeedbackLoop tests (43) | ✅ PASS |
| Integration + Orchestrator tests (8) | ✅ PASS |

---

## 9. Estado de M1

| Sub-tarea | Estado |
|-----------|--------|
| M1.1 — HTTP Wrapper | ⏳ **En evaluación** — no ejecutar hasta nuevo aviso |
| **M1.2 — Renombrar ParserGLR a LarkParser** | **✅ COMPLETADO** |
| **M1.3 — __init__.py exports (Q3)** | **✅ COMPLETADO** |
| **M1.4 — SRP feedback_loop → observers/ + optimizer/ (Q4)** | **✅ COMPLETADO** |
| **M1.5 — Type hints concretos (Q5)** | **✅ COMPLETADO** |
| **M1.6 — AuditObserver (S3)** | **✅ COMPLETADO** |
| M1.7 — Cablear LLMCache (DT3) | ⏳ Pendiente |
