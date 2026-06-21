---
area: dev
type: prop
module: agentic_pipeline
version: 1.0
status: DRAFT
---
# Propuesta de Migración — Arquitectura RECPL v2.0+ (basado en 121_PLAN)

- **ID:** 129_PROP_DEV_ARCHITECTURAL_MIGRATION_1_0_DRAFT
- **Tipo:** PROP (Propuesta)
- **Área:** DEV
- **Módulo:** agentic_pipeline (arquitectura completa)
- **Versión:** 1.0
- **Estado:** DRAFT
- **Tags:** `migration`, `architectural-refactor`, `solid`, `technical-debt`, `sprint-plan`, `vision`, `agentic-system`, `code-assistant`
- **Fuente base:** `docs/121_PLAN_DEV_ARCHITECTURAL_REFACTOR_1_0_DRAFT.md`
- **Contexto derivado:**
  - `docs/126_PLAN_DEV_PIPELINE_FIXES_1_0_DRAFT.md` (plan de fixes)
  - `docs/128_REP_DEV_PIPELINE_FIXES_VERIFICATION_1_0_DRAFT.md` (verificación de fixes vs. código base)
  - `docs/127_PROP_DEV_PIPELINE_HTTP_WRAPPER_1_0_DRAFT.md` (propuesta HTTP wrapper)
- **Changelog:**
  - 1.0 — 2026-06-18: Versión inicial — propuesta de migración con priorización ajustada
  - 1.1 — 2026-06-18: Agregada sección 11 — Visión de producto: proyección del sistema agéntico para asistente de código

---

## 1. Contexto y Propósito

### 1.1 ¿Qué es este documento?

El documento `121_PLAN_DEV_ARCHITECTURAL_REFACTOR_1_0_DRAFT.md` detalla ~127h de refactor arquitectónico distribuido en 6 sprints. Este documento **analiza, ajusta y prioriza** ese plan para convertirlo en una hoja de ruta migratoria ejecutable, considerando:

- El estado actual real del código base (verificado en `docs/128_REP_DEV_...`)
- Las dependencias reales entre los cambios
- Los fixes críticos del pipeline principal (Fixes 1-4 de 126_PLAN)
- La propuesta HTTP wrapper (127_PROP)
- El chain path (Fix 5 de 126_PLAN) se mantiene para implementación futura (M5)

### 1.2 Principios rectores de la migración

1. **Primero arreglar el pipeline principal** — los Fixes 2 y 3 son requisito para cualquier otra mejora
2. **Cero regresiones** — todos los refactors deben mantener los 463 tests pasando
3. **Incrementos atómicos** — cada cambio debe ser desplegable independientemente
4. **El HTTP wrapper es el entregable externo** — la migración debe priorizar que el pipeline funcione correctamente vía HTTP

### 1.3 Resumen de cambios respecto al plan original

| Aspecto | Plan 121 original | Propuesta migración |
|---------|------------------|---------------------|
| Sprints | 6 (0-5) | 5 (M0-M4) |
| Esfuerzo total | ~156.5h | **~98h** |
| Archivos a crear | 55h en nuevos | **~38h** |
| Chain path (Fix 5) | Incluido (P1-P6) | **Mantenido (M5)** |
| HTTP Wrapper | No contemplado | **Priorizado (M1)** |
| Orden de ejecución | Fijo por sprint | **Ajustado por dependencias reales** |

---

## 2. Línea Base: Estado Actual vs. Plan 121

### 2.1 Porcentaje de implementación por sección

| Sección 121 | Tareas totales | Ya implementadas | % | Notas |
|-------------|---------------|-----------------|---|-------|
| P1 — Agentes desconectados | 4 tareas | 0 | 0% | No hay `AgentPipelineAdapter` |
| P2 — Dead code | 3 tareas | 0 | 0% | `requirement_decomposer.py` sigue existiendo |
| P3 — ParserGLR rename | 3 tareas | 0 | 0% | Clase sigue llamándose `ParserGLR`, Lark usa `earley` |
| P4 — Thread safety | 3 tareas | 0 | 0% | `StageSubject` sin lock |
| P5 — Dos event buses | 4 tareas | 0 | 0% | `StageSubject` + `EventBus` coexisten |
| P6 — PipelineMacroCommand | 3 tareas | 0 | 0% | MacroCommand duplica StateGraph |
| Q1 — Ruff config | 4 tareas | 0 | 0% | `pyproject.toml` sin `[tool.ruff]` |
| Q2 — Pytest config | 3 tareas | 0 | 0% | `pyproject.toml` sin `[tool.pytest]` |
| Q3 — `__init__.py` | 4 tareas | 0 | 0% | Todos vacíos |
| Q4 — SRP feedback_loop | 6 tareas | 0 | 0% | 7 clases en 302 líneas |
| Q5 — Type hints | 3 tareas | 0 | 0% | `Any` excesivo |
| Q6 — Import consistency | 3 tareas | 0 | 0% | Mezcla relativos/absolutos |
| T1-T4 — Testing | 10 tareas | 0 | 0% | Sin fixtures compartidas, benchmarks, etc. |
| DT3 — LLMCache | 3 tareas | 0 | 0% | Cache existe pero no cableado |
| R1 — Circuit Breaker | 4 tareas | 0 | 0% | No implementado |
| R2 — Checkpoint | 3 tareas | 0 | 0% | No implementado |
| R3 — StageExecutor | 2 tareas | 0 | 0% | No implementado |
| R6 — GraphBackend | 5 tareas | 0 | 0% | LangGraph directo |
| OC — StageRegistry | 4 tareas | 0 | 0% | NODE_MAP hardcodeado |
| ISP — Interfaces | 5 tareas | 0 | 0% | PipelineStage monolítico |
| INM — Inmutabilidad | 4 tareas | 0 | 0% | StageContext mutable |
| GD — Graceful degradation | 4 tareas | 0 | 0% | Sin modo offline |
| S1-S4 — Seguridad | 8 tareas | 0 | 0% | No implementado |
| E1-E2 — Rendimiento | 5 tareas | 0 | 0% | No implementado |
| **Porcentaje general** | **~100 tareas** | **0** | **0%** | **Nada implementado del plan 121** |

### 2.2 Lo que SÍ está implementado (de otros planes)

| Origen | Implementación | Prioridad |
|--------|---------------|-----------|
| Fix 1 (126) — EntityDFA | ✅ `sub_dfa.py:293`, `lexer.py:119` | Alta |
| Fix 2 parcial (126) — ActionNode + visitors | ✅ `ast_nodes.py:82`, visitors | Alta |
| Fix 3 parcial (126) — Planner fallback | ✅ `reasoning_engine.py:433-469` | Alta |
| Fix 4 (126) — UI guardas | ✅ `ui_generator.py:73-96` | Alta |
| Chain path (Fix 5 126) | ❌ No implementado (planificado para M5) | — |

---

## 3. Propuesta de Migración

### 3.1 Mapa de ruta ajustado

```
M0: FUNDACIONES + FIXES CRITICOS  (14h)
├── Fix 2 restante: SemanticVisitor.visit_action  (0.5h)
├── Fix 2 restante: IRBuilder branch "action"      (0.5h)
├── Fix 2 restante: Parser fallback a ActionNode   (1h)
├── Fix 3 restante: ActionExecutor propaga ir_tree (0.5h)
├── Fix 3 restante: ActionExecutor fallback        (1h)
├── Q1: Ruff config + --fix                        (3.5h)
├── Q2: Pytest config                              (2h)
├── Q6: Import consistency                         (3.5h)
├── P2: Eliminar dead code                         (1.5h)

M1: API + OBSERVABILIDAD  (22h)
├── HTTP Wrapper (127_PROP)                        (6h)
│   ├── PipelineRequestHandler + PipelineInput/Result
│   └── FastAPI app
├── P3: Renombrar ParserGLR a LarkParser           (2h)
├── Q3: __init__.py con exports                    (3h)
├── Q4: SRP feedback_loop → observers/ + optimizer (6h)
├── Q5: Type hints concretos                       (4h)
├── S3: AuditObserver                              (3h)
└── DT3: Cablear LLMCache                          (4h)

M2: RESILIENCIA + SOLID BASICO  (24h)
├── R1: CircuitBreaker + ExponentialBackoff        (9.5h)
├── R3: StageExecutor aislamiento                  (5h)
├── GD: Graceful degradation (offline mode)        (7h)
└── INM: StageContext frozen                       (6.5h)

M3: ARQUITECTURA + TESTING  (24h)
├── ISP: Interface Segregation                     (8h)
│   ├── Analyzable, Plannable, Executable
│   └── Refactor PipelineStage + 10 subclasses
├── P5: Unificar event buses                       (9h)
├── T1: Tests integracion agent-pipeline           (7h)

M4: RENDIMIENTO + SEGURIDAD  (14h)
├── T2: Fixtures compartidas                       (4.5h)
├── S1: SecurityScanner (bandit)                   (8.5h)
├── S4: Rate Limiting (TokenBucket)                (3h)
└── E2: Modelos LLM diferenciados                  (3h)

BACKLOG (diferido, ~28h)
├── P1: AgentPipelineAdapter                       (20h)
├── P6: PipelineMacroCommand refactor              (4h)
├── R2: Checkpoint/resume                          (8h)
├── T3: Benchmarks                                 (4h)
├── T4: Tests LLM real                             (5.5h)
├── OC: PipelineStageRegistry (YAML)               (11h)
├── S2: Autenticacion                              (6h)
├── R6: GraphBackend abstraction                   (10h)
├── E1: Paralelizacion stages                      (5.5h)
└── B1-B3: Bottlenecks                             (9h)
```

### 3.2 Justificación del orden

**M0 va primero** porque sin arreglar el pipeline principal (tokens perdidos, nodos action ignorados, IR vacío, synthesis sin output), cualquier refactor arquitectónico es irrelevante. El pipeline no produce scaffolding correcto hoy.

**M1 va segundo** porque:
- El HTTP wrapper es el entregable con valor externo inmediato
- Observabilidad (auditoría) y calidad (ruff, pytest, imports) son prerequisites para CI/CD
- SRP feedback_loop reduce el archivo más violado

**M2 va tercero** porque:
- Circuit breaker protege contra fallos de LLM (el riesgo operacional más probable)
- StageExecutor evita que un stage falle todo el pipeline
- Graceful degradation permite operar sin LLM
- StageContext frozen elimina bugs por mutación inesperada

**M3 va cuarto** porque la Interface Segregation y unificación de event buses son refactors profundos que tocan muchos archivos y deben hacerse sobre una base ya estable.

**M4 va quinto** porque seguridad y rendimiento son mejoras, no necessities.

---

## 4. Sección por Sección: Análisis y Ajustes

### 4.1 P1 — Agentes desconectados → BACKLOG (ESTIMACIÓN REDUCIDA)

| Aspecto | Plan 121 | Propuesta |
|---------|----------|-----------|
| Tareas | P1.1-P1.4 (4 tareas) | P1.1-P1.4 (4 tareas) |
| Esfuerzo | 20h | **20h** |
| Prioridad | Alta | **Baja (backlog)** |
| Justificación | — | El sistema multi-agente (`agents/`) no tiene código ejecutable ni tests. El pipeline StateGraph funciona independientemente. Invertir 20h en integrar dos sistemas incompletos no produce valor inmediato. **Diferir hasta que el sistema multi-agente tenga funcionalidad propia.** |

**Ajuste:** Mover P1 a backlog. El `AgentPipelineAdapter` no tiene sentido mientras los agentes no produzcan outputs equivalentes al StateGraph.

---

### 4.2 P2 — Dead code → M0 (SIN CAMBIOS)

| Tarea | Esfuerzo | Notas |
|-------|----------|-------|
| P2.1 — Verificar referencias | 0.5h | Ya verificado: solo en `requirement_decomposer.py` y `state_models.py` |
| P2.2 — Eliminar archivo | 0.5h | |
| P2.3 — Eliminar del enum Stage | 0.5h | |

**Confirmación:** `grep` muestra solo 2 referencias (el propio archivo y el enum). **Ejecutar inmediatamente en M0.**

---

### 4.3 P3 — ParserGLR rename → M1 (SIN CAMBIOS)

| Tarea | Esfuerzo | Notas |
|-------|----------|-------|
| P3.1 — Renombrar clase | 0.5h | `ParserGLR` → `LarkParser` |
| P3.2 — Actualizar referencias | 1h | `NODE_MAP`, imports, tests |
| P3.3 — Docstring | 0.5h | |

**Ajuste:** Mover a M1 porque depende de M0 (ruff config + imports consistentes). Clase renombrada = todos los imports deben actualizarse, mejor hacerlo cuando ya hay ruff configurado.

---

### 4.4 P4 — Thread safety → M2 (REDUCCIÓN PROPUESTA)

| Aspecto | Plan 121 | Propuesta |
|---------|----------|-----------|
| Tareas | P4.1-P4.3 | P4.1 + P4.3 |
| Esfuerzo | 4h | **3h** |
| Justificación | — | P4.2 (verificar) es innecesario como tarea separada. Se verifica automáticamente con P4.3 (test de concurrencia). |

**Propuesta:** Implementar `threading.Lock` con copy-on-write en `StageSubject.notify()`. El test de concurrencia (P4.3) verifica la implementación. Mover a M2 porque no es crítico para el pipeline (el sistema no es multi-thread hoy).

---

### 4.5 P5 — Dos event buses → M3 (SIN CAMBIOS)

| Aspecto | Plan 121 | Propuesta |
|---------|----------|-----------|
| Tareas | P5.1-P5.4 | P5.1-P5.4 |
| Esfuerzo | 9h | **9h** |
| Prioridad | Media | **Media (M3)** |

**Análisis:** `StageSubject` (prompt_chain/observer_base.py) y `EventBus` (agents/event_bus.py) tienen APIs diferentes:

- `StageSubject`: `attach(StageObserver)` / `detach(StageObserver)` / `notify(StageEvent)`
- `EventBus`: `subscribe(topic, callback)` / `unsubscribe(topic, callback)` / `publish(topic, data)`

**Estrategia:** `EventBus` es más general (basado en topics y callbacks). La propuesta es hacer que `StageSubject` delegue internamente en `EventBus`, de modo que `StageSubject.notify(event)` internamente haga `_bus.publish(event.stage, event)`. Esto preserva la API de `StageSubject` (no rompe clientes) mientras unifica el bus subyacente.

---

### 4.6 P6 — PipelineMacroCommand → BACKLOG (REDUCCIÓN PROPUESTA)

| Aspecto | Plan 121 | Propuesta |
|---------|----------|-----------|
| Tareas | P6.1-P6.3 | P6.1 |
| Esfuerzo | 4h | **2h** |
| Prioridad | Media | **Baja (backlog)** |

**Justificación:** `PipelineMacroCommand` es usado por `CommandHistory.replay_failures()`. No es crítico ni bloqueante. La refactorización propuesta (P6.1) es simple: delegate en `AgentOrchestrator.run()` en lugar del loop manual. P6.2 y P6.3 son verificación automática.

**Propuesta:** Implementar solo P6.1 (delegación) en backlog, sin eliminar `_stage_to_enum()` ni el loop manual hasta que se verifique que `CommandHistory` funciona correctamente con la delegación.

---

### 4.7 Q1 — Ruff config → M0 (SIN CAMBIOS)

**Confirmación:** `pyproject.toml` no tiene `[tool.ruff]`. Es la configuración más crítica porque afecta a todo el código.

**Propuesta adicional:** Agregar también:

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]  # line-length ya controlado por formatter

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "lf"
```

**Ejecución:** `ruff check . --fix && ruff format .`

---

### 4.8 Q2 — Pytest config → M0 (SIN CAMBIOS)

**Config propuesta:**

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

---

### 4.9 Q3 — `__init__.py` exports → M1 (REDUCCIÓN PROPUESTA)

| Tarea | Esfuerzo | Propuesta |
|-------|----------|-----------|
| Q3.1 — `nodes/__init__.py` | 1.5h | Exportar solo clases usadas externamente: `LarkParser`, `Lexer`, `SemanticAnalyzer`, `IRGenerator`, `ReasoningEngine`, `ActionExecutor`, `UIGenerator`, `ValidatorPipeline` |
| Q3.2 — `nlp/__init__.py` | 0.5h | Igual |
| Q3.3 — `providers/__init__.py` | 0.5h | Igual |
| Q3.4 — `grammars/__init__.py` | 0.5h | Exportar constantes con nombres de gramáticas |

**Total:** 3h (sin cambios respecto al plan)

---

### 4.10 Q4 — SRP feedback_loop → M1 (SIN CAMBIOS)

**Estrategia de migración:**

```
feedback_loop.py (302 líneas, 7 clases)
  │
  ├── FeedbackLoop → feedback_loop.py (se queda)
  ├── GlobalFeedbackLoop → feedback_loop.py (se queda)
  ├── MetricsObserver → observers/metrics_observer.py
  ├── DebugObserver → observers/debug_observer.py
  ├── PromptOptimizerObserver → observers/prompt_optimizer_observer.py
  ├── DashboardObserver → observers/dashboard_observer.py
  └── PromptOptimizer → optimizer.py
```

**Archivo nuevo `observers/__init__.py`:**

```python
from .metrics_observer import MetricsObserver
from .debug_observer import DebugObserver
from .prompt_optimizer_observer import PromptOptimizerObserver
from .dashboard_observer import DashboardObserver

__all__ = [
    "MetricsObserver",
    "DebugObserver",
    "PromptOptimizerObserver",
    "DashboardObserver",
]
```

**Riesgo:** `base_stage.py` línea 86 importa `MetricsObserver` desde `feedback_loop`. Habrá que actualizar el import.

---

### 4.11 Q5 — Type hints → M1 (REDUCCIÓN PROPUESTA)

| Tarea | Esfuerzo | Propuesta |
|-------|----------|-----------|
| Q5.1 — feedback_loop/observers | 2h | Reemplazar `Any` con tipos concretos en métodos públicos |
| Q5.2 — metrics_store TypedDict | 1h | Crear `StageMetrics(TypedDict)` con campos tipados |
| Q5.3 — mypy | 1h | Ejecutar y documentar violaciones (no blocker) |

**Propuesta:** No exigir `mypy --strict` porque hay muchas librerías sin stubs (langgraph, lark). Usar `mypy agentic_pipeline/ --ignore-missing-imports`.

---

### 4.12 Q6 — Import consistency → M0 (SIN CAMBIOS)

**Propuesta:** Estandarizar a imports absolutos DENTRO del paquete:

```python
# En lugar de:
from .lexer import Lexer
from ..base_stage import PipelineStage

# Usar:
from agentic_pipeline.nodes.lexer import Lexer
from agentic_pipeline.base_stage import PipelineStage
```

**Excepción:** `__init__.py` de subpaquetes puede usar relativos.

**Ejecución:** `ruff check . --fix --select I` ordena imports. Luego reemplazar manualmente los relativos por absolutos en todo el paquete.

---

### 4.13 T1-T4 — Testing → M3-M4-BACKLOG

| Sprint | Tareas | Esfuerzo | Justificación |
|--------|--------|----------|---------------|
| M3 | T1 (integración) + T2 (fixtures) | 11.5h | Necesario para verificar P5 (event buses) |
| M4 | S1-S4 tests asociados | — | Se integran con implementación |
| BACKLOG | T3 (benchmarks) + T4 (LLM real) | 9.5h | Bajo valor inmediato |

---

### 4.14 DT3 — LLMCache → M1 (SIN CAMBIOS)

**Análisis:** El archivo `prompt_chain/llm_backend.py` existe. El cache (`LLMCache`) probablemente existe como clase pero no se usa en `LLMBackend.generate()`.

**Propuesta:** Cablear cache en `generate(): check cache before API, store after API`. Agregar métricas de hit/miss a `MetricsStore`.

---

### 4.15 R1 — Circuit Breaker → M2 (SIN CAMBIOS)

| Aspecto | Plan 121 | Propuesta |
|---------|----------|-----------|
| Tareas | R1.1-R1.4 | R1.1-R1.4 |
| Esfuerzo | 9.5h | **9.5h** |
| Prioridad | Alta | **Alta (M2)** |

**Diseño propuesto:**

```python
class CircuitBreakerState(Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject fast
    HALF_OPEN = "half_open" # Testing if recovered

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
```

---

### 4.16 R3 — StageExecutor → M2 (SIN CAMBIOS)

**Propuesta:** `StageExecutor` envuelve cada stage con try/except:

```python
class StageExecutor:
    async def execute(self, stage: PipelineStage, input_data: Any) -> StageOutput:
        try:
            return stage.execute(input_data)
        except Exception as exc:
            return StageOutput(
                stage=stage.context.stage,
                output_data={},
                success=False,
                error=str(exc),
                metrics={"exception": type(exc).__name__},
            )
```

**En AgentOrchestrator:** Cada nodo del StateGraph ejecuta via `StageExecutor` en lugar de llamar `instance.execute()` directamente.

---

### 4.17 INM — StageContext frozen → M2 (SIN CAMBIOS)

**Propuesta (ajustada):**

```python
class StageContext(BaseModel):
    model_config = ConfigDict(frozen=True)
    mission_id: str = Field(default_factory=lambda: datetime.now().isoformat())
    stage: Stage
    input_data: Any
    previous_output: Optional[Any] = None
    config_overrides: dict = Field(default_factory=dict)
    last_error: Optional[str] = None

    def with_update(self, **kwargs) -> StageContext:
        return self.model_copy(update=kwargs)
```

**Impacto:** ~10 archivos en `nodes/*.py` modifican `ctx.input_data = ...`. Todos deben cambiarse a `ctx = ctx.with_update(input_data=...)`.

---

### 4.18 ISP — Interface Segregation → M3 (REDUCCIÓN PROPUESTA)

| Aspecto | Plan 121 | Propuesta |
|---------|----------|-----------|
| Tareas | ISP1-ISP5 (5 tareas) | ISP1-ISP5 (5 tareas) |
| Esfuerzo | 8h | **8h** |
| Prioridad | Media | **Media (M3)** |

**Propuesta de interfaces:**

```python
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
    """Backward-compatible base class that implements all three."""
    ...
```

**Estrategia:** PipelineStage mantiene herencia múltiple por compatibilidad. Stages individuales que no necesiten analyze/plan pueden implementar solo `Executable` directamente. Esto es compatible hacia atrás (no rompe clientes existentes).

---

### 4.19 OC — PipelineStageRegistry → BACKLOG

| Aspecto | Plan 121 | Propuesta |
|---------|----------|-----------|
| Tareas | OC1-OC4 | OC1-OC4 |
| Esfuerzo | 11h | **11h** |
| Prioridad | Media | **Baja (backlog)** |

**Justificación:** El `NODE_MAP` hardcodeado no es un problema hoy. La flexibilidad de cargar stages desde YAML es una mejora de mantenibilidad, no una necesidad. OCP puede implementarse más adelante sin romper nada.

---

### 4.20 GD — Graceful degradation → M2 (SIN CAMBIOS)

**Alineación con chain path:** El modo offline (sin LLM) es exactamente el modo en que el pipeline StateGraph ya opera — usa DFAs, reglas heurísticas y plantillas deterministas. Los únicos stages que requieren LLM son `PerceptionUnit` (intent classification) y `ReasoningEngine` (planner avanzado), y ambos ya tienen fallbacks heurísticos.

**Propuesta:** Agregar flag `--offline` que fuerce el uso exclusivo de fallbacks deterministas en todos los stages. Documentar qué stages funcionan sin LLM.

---

### 4.21 S1-S4 — Seguridad → M3-M4

| ID | Tarea | Esfuerzo | Sprint | Nota |
|----|-------|----------|--------|------|
| S1 | SecurityScanner + bandit | 8.5h | M4 | Se integra como StageObserver en ValidatorPipeline |
| S2 | Autenticación (JWT) | 6h | BACKLOG | Depende del HTTP wrapper (M1) |
| S3 | AuditObserver | 3h | M1 | Se integra con Q4 (observers/) |
| S4 | TokenBucket rate limiter | 3h | M4 | Se integra con R1 (CircuitBreaker) |

**Ajuste:** S3 (AuditObserver) se mueve a M1 porque depende de Q4 (SRP feedback_loop) y produce valor inmediato (trazabilidad de compilaciones).

---

### 4.22 E1-E2 — Rendimiento → M4

| ID | Esfuerzo | Justificación |
|----|----------|---------------|
| E1 (paralelización) | 5.5h | Bajo impacto hoy. El pipeline es I/O-bound por LLM. Paralelizar stages sin LLM no reduce latencia significativamente. → BACKLOG |
| E2 (modelos diferenciados) | 3h | Mejora tangible: mini para preprocess/intent, 4o para generate. **MANTENER EN M4** |

---

## 5. Dependencias Reales entre Cambios

```
M0:
  Q1 (ruff) ─┐
  Q2 (pytest)┤
  Q6 (imports)┤
              │
              ├──► Fix 2 restante (toca parser/ir/semantic)
              │       └──► Fix 3 restante (toca action_executor)
              │               └──► Fix 4 ya funciona
              │
              └──► P2 (dead code, simple)

M1:
  M0 ──► Q3 (__init__)
  M0 ──► P3 (rename ParserGLR) ──► requiere Q1+Q6 para imports
  M0 ──► Q4 (SRP) ──► Q5 (type hints)
  M0 ──► DT3 (LLMCache) ──► HTTP wrapper (para métricas de cache)
  Q4 ──► S3 (AuditObserver, nuevo archivo en observers/)
  HTTP wrapper ──► independiente

M2:
  M1 ──► R1 (CircuitBreaker) ──► se integra con LLMBackend
  M1 ──► R3 (StageExecutor) ──► modifica AgentOrchestrator
  M0 ──► INM (StageContext frozen) ──► toca nodes/*.py
  M1 ──► GD (offline mode) ──► modifica config

M3:
  M2 ──► ISP (interfaces) ──► toca PipelineStage + subclasses
  M1 ──► P5 (event buses) ──► toca observer_base + event_bus + imports
  M3 ──► T1 (integration tests) ──► verifica P5

M4:
  M3 ──► S1 (SecurityScanner) ──► se integra con ValidatorPipeline
  M4 ──► S4 (TokenBucket) ──► se integra con R1
  M4 ──► E2 (models) ──► modifica config + LLMBackend
  M4 ──► T2 (fixtures) ──► conftest.py
```

---

## 6. Presupuesto Ajustado por Sprint

| Sprint | Horas | Semanas | Dependencias |
|--------|-------|---------|-------------|
| **M0: Fundaciones + Fixes críticos** | **14h** | 0.5 | — |
| **M1: API + Observabilidad** | **22h** | 1 | M0 |
| **M2: Resiliencia + SOLID básico** | **24h** | 1 | M1 |
| **M3: Arquitectura + Testing** | **24h** | 1 | M2 |
| **M4: Rendimiento + Seguridad** | **14h** | 0.5 | M3 |
| **BACKLOG: Diferido** | **~28h** | — | — |
| **Total migración** | **~98h** | **~4 semanas** | |

### Carga por desarrollador

| Rol | M0 | M1 | M2 | M3 | M4 | Total |
|-----|----|----|----|----|----|-------|
| Backend Python | 14h | 14h | 18h | 18h | 10h | **74h** |
| DevOps/CI | 6h | 4h | — | — | — | **10h** |
| QA/Tests | — | 4h | 6h | 6h | 4h | **20h** |

> **Nota:** 1 desarrollador a tiempo completo (~35h/semana) completa la migración en ~3 semanas. Con 2 desarrolladores, ~2 semanas (paralelizando M1-M2).

---

## 7. Comparación Plan 121 vs. Propuesta

| Aspecto | Plan 121 original | Propuesta migración | Diferencia |
|---------|------------------|---------------------|------------|
| **Sprints** | 6 (Sprint 0-5) | 5 (M0-M4) + backlog | −1 sprint |
| **Esfuerzo total** | ~156.5h | **~98h** | −58h (−37%) |
| **Chain path** | Incluido (en P1-P6) | **Mantenido para M5 (futuro)** | 0h |
| **P1 (agent adapter)** | Sprint 3 (alta prioridad) | **Backlog** | −20h |
| **OC (stage registry)** | Sprint 4 | **Backlog** | −11h |
| **R6 (GraphBackend)** | Sprint 4 | **Backlog** | −10h |
| **E1 (paralelización)** | Sprint 4 | **Backlog** | −5.5h |
| **Fixes pipeline (126)** | No contemplado | **Prioritario (M0)** | +6h |
| **HTTP wrapper (127)** | No contemplado | **Prioritario (M1)** | +6h |
| **S3 (auditoría)** | Sprint 3 | **Movido a M1** | 0h |
| **S2 (autenticación)** | Sprint 3 | **Backlog** | −6h |

---

## 8. Riesgos y Mitigaciones

| Riesgo | Impacto | Prob. | Mitigación |
|--------|---------|-------|------------|
| **M0 fixes rompen tests existentes** | Regresión | Alta | Ejecutar `pytest tests/ -v` tras cada cambio. No commitear hasta que todos pasen. |
| **Q1 (ruff --fix) cambia formato masivamente** | Ruido en git diff | Alta | Ejecutar en commit separado con mensaje claro: `chore: apply ruff formatting`. Ignorar en blame. |
| **INM (StageContext frozen) rompe 10 archivos** | Pipeline no compila | Media | Implementar INM inmediatamente después de M0, no mezclar con otros cambios. CI debe verificar compilación. |
| **Q4 (SRP) cambia imports en muchos archivos** | ImportErrors | Alta | Actualizar imports en el mismo commit. `ruff check .` detecta imports no resueltos. |
| **P5 (event buses) toca ~10 archivos** | Regresión | Media | Tests de integración (T1) deben ejecutarse antes y después. |
| **HTTP wrapper requiere FastAPI no instalado** | Bloqueante | Baja | Agregar dependencia en pyproject.toml, `pip install .` |

---

## 9. Entregables por Sprint

### M0: Fundaciones + Fixes críticos

```
✅ Ruff config + --fix (pyproject.toml)
✅ Pytest config (pyproject.toml)
✅ Imports consistentes (todos los archivos)
✅ RequirementDecomposer eliminado
✅ SemanticVisitor.visit_action() agregada
✅ IRBuilder branch "action" agregado
✅ Parser fallback produce ActionNode
✅ ActionExecutor propaga ir_tree + tasks
✅ ActionExecutor fallback desde goal_tree
✅ CI/CD pipeline con ruff + pytest
```

### M1: API + Observabilidad

```
✅ PipelineRequestHandler + contratos (PipelineInput, PipelineResult, StageInfo)
✅ FastAPI app (api/fastapi_app.py)
✅ ParserGLR → LarkParser renombrado
✅ __init__.py con exports en nodes, nlp, providers, grammars
✅ SRP feedback_loop → observers/ + optimizer/
✅ Type hints concretos en feedback_loop/observers
✅ LLMCache cableado en LLMBackend.generate()
✅ AuditObserver registrando compilaciones
```

### M2: Resiliencia + SOLID básico

```
✅ CircuitBreaker + ExponentialBackoff
✅ StageExecutor con try/except per-stage
✅ Modo offline (--offline flag)
✅ StageContext frozen con with_update()
✅ Modo offline documentado
```

### M3: Arquitectura + Testing

```
✅ Analyzable, Plannable, Executable interfaces
✅ PipelineStage refactorizado (hereda interfaces)
✅ 10 subclasses actualizadas
✅ EventBus unificado (StageSubject delega en EventBus)
✅ Tests integración agent-pipeline (3 modos)
```

### M4: Rendimiento + Seguridad

```
✅ SecurityScanner + bandit en ValidatorPipeline
✅ TokenBucket rate limiter
✅ Modelos LLM diferenciados por stage
✅ Fixtures compartidas en conftest.py
✅ Políticas de seguridad (eval, exec, etc.)
```

### Backlog (no comprometido)

```
⏳ AgentPipelineAdapter (P1)
⏳ PipelineMacroCommand refactor (P6)
⏳ Checkpoint/resume (R2)
⏳ Benchmarks (T3)
⏳ Tests LLM real (T4)
⏳ PipelineStageRegistry YAML (OC)
⏳ Autenticación JWT (S2)
⏳ GraphBackend abstraction (R6)
⏳ Paralelización stages (E1)
⏳ Bottlenecks (B1-B3)
```

---

## 10. Conclusión y Recomendación

### Decisión tomada

1. **Chain path mantenido** — el flag `--chain` se conserva para implementación futura. Los 6 handlers (preprocess, intent, plan, generate, verify, format) se construirán en M5 cuando el sistema multi-agente esté listo. Mientras tanto, el pipeline principal StateGraph es el path recomendado.
2. **HTTP wrapper priorizado** — se implementa en M1 como entregable externo.
3. **Fixes críticos del pipeline primero** — M0 es requisito para todo lo demás.

### Recomendación de ejecución

1. **Ejecutar M0 inmediatamente** (~1 semana): arreglar el pipeline, configurar calidad, eliminar dead code.
2. **Paralelizar M1 y M2** si hay 2 desarrolladores (semana 2-3): HTTP wrapper + observabilidad + resiliencia.
3. **M3 y M4 secuenciales** (semana 3-4): arquitectura + seguridad.
4. **Backlog planificado** para futuros sprints según necesidad.

### Pipeline final después de migración

```
                      ┌──────────────┐
  HTTP POST /pipeline │ HTTP Wrapper │ (M1)
       ──────────────►│ FastAPI      │
                      └──────┬───────┘
                             │
                      ┌──────▼───────┐
                      │ AgentOrch.  │ (M2 → R3: StageExecutor)
                      │ R1: Circuit │ (M2)
                      │ Breaker     │
                      └──────┬───────┘
                             │
                ┌────────────┼────────────┐
                ▼            ▼            ▼
        ┌───────────┐ ┌──────────┐ ┌──────────┐
        │ INTENT    │ │ LEXER   │ │ PARSER   │ ← M0: Fix 2 completo
        │ (Percept.)│ │ (DFA)   │ │ (Lark)   │
        └───────────┘ └──────────┘ └──────────┘
                │            │            │
                ▼            ▼            ▼
        ┌───────────┐ ┌──────────┐ ┌──────────┐
        │ SEMANTIC  │ │ IR BUILD│ │ PLANNER  │ ← M0: Fix 2+3
        │ (Visitor) │ │ (action)│ │ (hybrid) │
        └───────────┘ └──────────┘ └──────────┘
                │            │            │
                ▼            ▼            ▼
        ┌───────────┐ ┌──────────┐ ┌──────────┐
        │ SYNTHESIS │ │ UI GEN  │ │VALIDATOR │ ← M0: Fix 3+4
        │ (propaga) │ │ (gate)  │ │(Security)│ ← M4: S1
        └───────────┘ └──────────┘ └──────────┘
                │            │            │
                └────────────┼────────────┘
                             │
                      ┌──────▼───────┐
                      │Observability │ ← M1: S3 (Audit)
                      │Q4: observers │
                      └──────────────┘
```

**El resultado es un pipeline que:**

1. **Funciona correctamente** (M0) — produce scaffolding NestJS/Prisma desde input natural
2. **Se expone vía HTTP** (M1) — usable desde cualquier cliente
3. **Es resiliente** (M2) — sobrevive a fallos de LLM, stages individuales
4. **Es mantenible** (M3) — interfaces segregadas, event bus unificado
5. **Es seguro y observable** (M4) — auditoría, sanitización, rate limiting

---

## 11. Visión de Producto: Sistema Agéntico para Asistente de Código

> Esta sección describe la proyección a largo plazo del proyecto, considerando que el pipeline, sus paths, tools y agentes servirán como base para un **sistema agéntico de/para un asistente de código**.

### 11.1 ¿Qué es el sistema hoy?

| Componente | Propósito | Estado |
|------------|-----------|--------|
| **StateGraph pipeline** | Compila lenguaje natural → scaffolding NestJS/Prisma | ✅ Funcional (463 tests) |
| **Chain path** (`--chain`) | Path alternativo con handlers LLM por etapa | ❌ Sin handlers |
| **Agents** (`agents/`) | PerceptionAgent, ReasoningAgent, ExecutionAgent, ValidatorAgent, SupervisorAgent | ❌ Sin código ejecutable |
| **Tools** (`tools/`) | ReadFile, WriteFile, RunCommand, SearchCode, GenerateCode, AskUser, Explain | ✅ Implementadas |
| **AgentLoop** (`agent_loop.py`) | Bucle percibe→razona→ejecuta→observa | ✅ Funcional |
| **ToolRegistry** | Registro central de herramientas | ✅ Funcional |
| **HTTP wrapper** | API REST para el pipeline | 🚧 Propuesto (M1) |

### 11.2 Arquitectura destino: Sistema Agéntico para Asistente de Código

La visión es que el sistema opere en **3 modos complementarios**, cada uno con su caso de uso:

```
┌──────────────────────────────────────────────────────────────────────┐
│                        ENTRY POINTS                                 │
│                                                                      │
│  CLI (agentic -p)    HTTP API (/v1/compile)    IDE Plugin (LSP)     │
│       │                    │                         │               │
└───────┼────────────────────┼─────────────────────────┼───────────────┘
        │                    │                         │
        ▼                    ▼                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    ROUTER (OrchestratorRouter)                       │
│                                                                      │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ Modo     │  │ Modo         │  │ Modo         │  │ Modo       │  │
│  │ DIRECT   │  │ CHAIN        │  │ AGENT        │  │ HYBRID     │  │
│  │ (rapido) │  │ (preciso)    │  │ (autonomo)   │  │ (balance)  │  │
│  └────┬─────┘  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘  │
│       │               │                 │                │         │
│       ▼               ▼                 ▼                ▼         │
│  ┌────────────┐ ┌────────────┐ ┌──────────────┐ ┌─────────────┐   │
│  │ StateGraph │ │ LLM Chain  │ │ Multi-Agent  │ │ StateGraph  │   │
│  │ ~1s        │ │ ~5-10s     │ │ System       │ │ + Agent     │   │
│  │ (M0)       │ │ (M5)       │ │ ~15-30s (M5) │ │ s (M5)      │   │
│  └────────────┘ └────────────┘ └──────────────┘ └─────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

### 11.3 Los 3 modos de ejecución

#### Modo DIRECT (rápido, determinista)

```
Input → StateGraph → Output
        10 stages
        ~1 segundo
        Sin LLM requirement
```

**Cuándo usarlo:** Comandos simples ("crea módulo usuarios", "genera entidad producto"). Scaffolding rápido donde la precisión determinista del DFA es suficiente.

**Pipeline:** INTENT → PREPROCESSOR → LEXER → PARSER → SEMANTIC → IR → PLANNER → SYNTHESIS → UI → VALIDATOR

**Dependencia LLM:** Ninguna. Todo es DFA + Lark + reglas heurísticas.

#### Modo CHAIN (preciso, con LLM)

```
Input → PreprocessHandler → IntentHandler → PlanHandler → GenerateHandler → VerifyHandler → FormatHandler → Output
        (LLM)               (LLM)          (LLM)        (LLM)             (LLM)          (LLM)
        ~5-10 segundos
```

**Cuándo usarlo:** Prompts complejos ("crea un sistema de e-commerce con autenticación JWT, panel admin y pasarela de pagos"). La entrada tiene entidades, relaciones, y reglas de negocio que requieren comprensión semántica.

**Pipeline:** Cada handler es un prompt LLM independiente con contexto del handler anterior.

**Dependencia LLM:** Total. Sin LLM, los handlers operan con fallbacks mínimos (ver Fix 5 en 126_PLAN).

**Estado:** ❌ Sin implementar. Se planifica para M5.

#### Modo AGENT (autónomo, multi-paso)

```
Input → SupervisorAgent
           ├── PerceptionAgent (clasifica intent)
           ├── ReasoningAgent (descompone en subtareas)
           ├── ExecutionAgent (ejecuta cada subtarea usando tools)
           │     ├── tool_read_file
           │     ├── tool_write_file
           │     ├── tool_run_command
           │     ├── tool_search_code
           │     ├── tool_generate_code
           │     ├── tool_ask_user
           │     └── tool_explain
           ├── ValidatorAgent (verifica resultado)
           └── AgentLoop (itera hasta max_iterations)
```

**Cuándo usarlo:** Tareas que requieren múltiples pasos con feedback del entorno. Por ejemplo, "refactoriza el módulo de pagos para usar Stripe en lugar de PayPal" → leer código actual, planificar cambios, ejecutarlos, verificar.

**Dependencia LLM:** Alta. Los agentes usan LLM para razonar y decidir qué tool llamar.

**Estado:** ❌ Parcial. Los agentes existen como clases sin código ejecutable. El `AgentLoop` y `ToolRegistry` están implementados y funcionales.

### 11.4 Proyección: Hoja de ruta evolutiva

```
AHORA (M0-M4)              M5 (+6h)                M6+ (futuro)
───────────────            ─────────               ─────────────
✅ DIRECT mode             🚧 CHAIN mode            🌟 AGENT mode
✅ Tools implementadas     🚧 Chain handlers        🌟 AgentPipelineAdapter
✅ ToolRegistry            🚧 LLM fallbacks         🌟 SupervisorAgent real
✅ AgentLoop               🚧 Verify criteria       🌟 Multi-turn conversations
✅ HTTP wrapper (M1)       🚧 Format handler        🌟 IDE Plugin (LSP)
✅ Observability (M1)                              🌟 Tool embeddings
✅ Resilience (M2)                                 🌟 RAG sobre codebase
✅ Arquitectura (M3)                               🌟 Feedback learning
✅ Seguridad (M4)                                  🌟 Code review agent
```

### 11.5 Proyección: Madurez por capa

| Capa | Hoy (M0) | M5 | M6+ |
|------|----------|----|-----|
| **Pipeline compilador** (StateGraph) | ✅ 10 stages, produce scaffolding | ✅ Igual + fixes completos | ✅ Igual + paralelización |
| **Chain path** (LLM handlers) | ❌ No implementado | ✅ 6 handlers funcionales + cada uno con fallback | ✅ Igual + optimización automática de prompts (F5) |
| **Sistema multi-agente** | ❌ Clases vacías | ✅ AgentPipelineAdapter implementado | ✅ SupervisorAgent con planificación dinámica |
| **Tools** | ✅ 7 herramientas | ✅ Igual + tool_llm | ✅ Igual + tool_rag + tool_execute |
| **AgentLoop** | ✅ Bucle básico | ✅ Igual + memoria persistente | ✅ Igual + aprendizaje por refuerzo |
| **HTTP API** | 🚧 En M1 | ✅ Endpoints para DIRECT + CHAIN | ✅ Endpoints para AGENT + WebSockets para streaming |

### 11.6 Principios de evolución sostenible

Para que el sistema sea mantenible y realizable a lo largo del tiempo:

1. **DIRECT mode es la base.** Cualquier mejora en CHAIN o AGENT debe producir el mismo output que DIRECT mode para el mismo input. Esto garantiza que siempre hay un fallback determinista.

2. **Los 3 modos comparten la misma capa de tools.** `ToolRegistry`, `ToolResult`, y las 7 tools concretas son el interfaz común. No importa qué modo ejecute, las tools subyacentes son las mismas.

3. **Cada modo es autónomo.** No hay dependencias entre DIRECT y CHAIN, ni entre CHAIN y AGENT. Se pueden construir y desplegar independientemente.

4. **El chain path no reemplaza al StateGraph.** Ambos son complementarios: DIRECT para respuestas rápidas (scaffolding), CHAIN para prompts complejos (planificación), AGENT para tareas autónomas (refactorización multi-paso).

5. **Toda la complejidad LLM está aislada en handlers.** El StateGraph no depende de LLM. Si el backend LLM no está disponible, el sistema sigue funcionando en modo DIRECT con fallbacks deterministas.

6. **Cada sprint debe entregar valor tangible.** No hay sprints de "refactor puro". Cada sprint produce un entregable verificable (funcionalidad, test, o configuración).

7. **La observabilidad es obligatoria desde el día 1.** AuditObserver, MetricsStore y logging son prerequisites para todos los modos, no features opcionales.

### 11.7 Riesgos de crecimiento

| Riesgo | Síntoma | Mitigación |
|--------|---------|------------|
| **Modo CHAIN duplica lógica del StateGraph** | Handlers replican reglas DFA/heurísticas | Asegurar que los handlers LLM usen los mismos contracts (STAGE_CONTRACTS) |
| **Modo AGENT sin supervisión humana** | El agente ejecuta tools destructivas sin validación | `AskUserTool` siempre pregunta antes de escribir/eliminar archivos |
| **Dependencia excesiva de LLM** | El sistema no funciona sin API key | Graceful degradation (M2): modo offline con fallbacks deterministas |
| **Deuda técnica no pagada** | Cada sprint nuevo añade complejidad sin limpiar | Mantener backlog de deuda. Cada 3 sprints, dedicar 1 sprint a limpieza |
| **Tests insuficientes en CHAIN/AGENT** | Modo DIRECT tiene 463 tests, CHAIN tiene 0 | No promocionar CHAIN/AGENT a producción sin cobertura mínima de tests |

### 11.8 Decisión: Chain path se mantiene

Contrario a la recomendación original de deprecarlo, el chain path se **mantiene y planifica para M5** por las siguientes razones:

1. **Complementariedad:** StateGraph es rápido y determinista. Chain path es preciso y adaptable. Ambos son necesarios para un asistente de código completo.
2. **Preparación para modo AGENT:** Los handlers del chain path son los bloques de construcción del sistema multi-agente. Cada handler es un "micro-agente" especializado.
3. **No hay duplicación funcional:** El StateGraph opera sobre tokens (DFA + Lark). El chain path opera sobre prompts LLM. Son tecnologías diferentes con el mismo objetivo.
4. **Inversión mínima:** Implementar el chain path requiere ~6h (los 6 handlers). No es un esfuerzo significativo comparado con el valor que aporta como alternativa LLM-based.

**Cuándo implementar M5:** Cuando:
- Los Fixes 1-4 del pipeline estén completos (M0)
- El HTTP wrapper esté operativo (M1)
- El sistema sea resiliente (M2)
- La arquitectura esté saneada (M3-M4)
- Haya un backend LLM funcional (Ollama, OpenAI, etc.)

Solo entonces tendrá sentido añadir el modo CHAIN como alternativa al modo DIRECT.
