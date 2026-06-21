---
area: dev
type: rep
module: m2
version: 1.0
status: IMPLEMENTED
---
# Reporte de Ejecución — M2: Resiliencia + SOLID Básico

- **ID:** 133_REP_DEV_M2_EXECUTION_REPORT_1_0_DRAFT
- **Tipo:** REP (Reporte)
- **Área:** DEV
- **Módulo:** agentic_pipeline
- **Versión:** 1.3
- **Estado:** DRAFT
- **Tags:** `execution-report`, `m2`, `circuit-breaker`, `exponential-backoff`, `stage-executor`, `offline-mode`, `resilience`, `graceful-degradation`, `frozen-context`, `immutability`
- **Fuente:** `docs/130_PLAN_DEV_MIGRATION_EXECUTION_1_0_DRAFT.md` (M2.1–M2.4)
- **Changelog:**
  - 1.3 — 2026-06-19: Añadido M2.4 — StageContext frozen con with_update()
  - 1.2 — 2026-06-19: Añadido M2.3 — Modo offline con graceful degradation
  - 1.1 — 2026-06-19: Añadido M2.2 — StageExecutor para aislamiento por stage
  - 1.0 — 2026-06-19: Versión inicial — M2.1 CircuitBreaker + ExponentialBackoff

---

## 1. Resumen

| Aspecto | Valor |
|---------|-------|
| Sprint | M2 — Resiliencia + SOLID Básico |
| Tarea | M2.1 — CircuitBreaker + ExponentialBackoff (R1) |
| Esfuerzo estimado | 9.5h |
| Esfuerzo ejecutado | ~1.5h |
| Estado | **COMPLETADO** |

---

## 2. Motivo del cambio

`OpenAIBackend.generate()` y `generate_structured()` no tenían protección ante fallos transitorios de la API del LLM. Un timeout o error 5xx causaba fallo inmediato sin reintento. Tampoco existía un mecanismo para evitar llamadas a una API que está fallando repetidamente (circuit breaker). Se implementó CircuitBreaker + ExponentialBackoff para:

- Detectar fallos consecutivos y abrir el circuito (rechazar llamadas rápidamente)
- Reintentar con backoff exponencial + jitter para evitar tormentas de reintentos
- Sonda periódica (half-open) para detectar recuperación del servicio

---

## 3. Archivos creados/modificados

| Acción | Archivo | Cambio |
|--------|---------|--------|
| 📄 Crear | `circuit_breaker.py` | `CircuitBreaker` + `ExponentialBackoff` + `CircuitBreakerOpenError` |
| 📄 Crear | `tests/test_circuit_breaker.py` | 15 tests unitarios |
| 🔧 Modificar | `prompt_chain/llm_backend.py` | Integración: `set_circuit_breaker()`, `_call_with_retry()`, protección en `generate()` y `generate_structured()` |

---

## 4. Componentes

### CircuitBreaker

```
CLOSED ──(threshold failures)──→ OPEN ──(timeout)──→ HALF_OPEN ──(success)──→ CLOSED
                                                         │
                                                         └──(failure)──→ OPEN
```

- `threshold`: número de fallos consecutivos para abrir (default: 5)
- `timeout`: tiempo en OPEN antes de pasar a HALF_OPEN (default: 30s)
- `call(fn)`: ejecución síncrona protegida
- `call_async(fn)`: ejecución asíncrona protegida
- `reset()`: reinicia a CLOSED

### ExponentialBackoff

```
delay(attempt) = min(min_backoff * factor^attempt, max_backoff) + jitter
```

- `min_backoff`: 1.0s (default)
- `max_backoff`: 60.0s (default)
- `factor`: 2.0 (default)
- `jitter`: 0.1 (10% aleatorio)

### Integración en LLMBackend

Se agregaron al `LLMBackend` base:
- `_circuit_breaker: CircuitBreaker | None`
- `_backoff: ExponentialBackoff | None`
- `set_circuit_breaker(cb, backoff)` — setter para inyectar

Se agregó a `OpenAIBackend`:
- `_call_with_retry(fn, max_retries=3)` — método helper que envuelve la llamada API con CB + backoff

`OpenAIBackend.generate()` y `generate_structured()` usan `_call_with_retry()` en lugar de `self._llm.ainvoke()` directo. Si el CB está OPEN, retornan `LLMResult(success=False, error="Circuit breaker OPEN...")` sin llamar a la API.

Los otros backends (`OllamaBackend`, `VLLMBackend`) heredan `set_circuit_breaker()` y `_call_with_retry()` pero aún no implementan protección activa. Se hará en M2.2 si es necesario.

---

## 5. Verificación

```bash
$ ruff check circuit_breaker.py test_circuit_breaker.py prompt_chain/llm_backend.py
# EXIT: 0 — all checks passed

$ pytest tests/test_circuit_breaker.py tests/test_llm_backend.py -v --tb=short -o "addopts="
# 23 passed (15 CB + 8 backend)
```

| Verificación | Resultado |
|-------------|-----------|
| `ruff check` — 0 errores | ✅ PASS |
| CircuitBreaker tests (11 tests) | ✅ PASS |
| ExponentialBackoff tests (4 tests) | ✅ PASS |
| LLMBackend tests (8 tests) | ✅ PASS |
| CB OPEN rejection sin llamada API | ✅ PASS |
| CB HALF_OPEN probe + recuperación | ✅ PASS |
| CB reset | ✅ PASS |
| Backoff jitter aleatorio | ✅ PASS |

---

## 6. M2.2 — StageExecutor aislamiento (R3)

### Motivo

`_make_node()` en `orchestrator.py` llamaba `instance.execute(ctx.input_data)` directamente sin try/except. Si un stage lanzaba una excepción (ej. TypeError, KeyError, ConnectionError), ésta se propagaba sin control hasta el StateGraph, abortando todo el pipeline sin un mensaje de error claro. El `StageExecutor` añade una barrera de error que atrapa cualquier excepción y la convierte en un `StageOutput(success=False)` limpio.

### Archivos creados/modificados

| Acción | Archivo | Cambio |
|--------|---------|--------|
| 📄 Crear | `stage_executor.py` | `StageExecutor` con método `execute()` async + try/except |
| 🔧 Modificar | `orchestrator.py` | Import + uso de `StageExecutor` en `_make_node()` |

### StageExecutor

```python
class StageExecutor:
    async def execute(self, stage: PipelineStage, input_data: object) -> StageOutput:
        try:
            return stage.execute(input_data)
        except Exception as exc:
            logger.exception("Stage %s failed: %s", stage.name, exc)
            return StageOutput(
                stage=stage.context.stage,
                output_data={},
                success=False,
                error=str(exc),
                metrics={"exception": type(exc).__name__},
            )
```

### Cambio en _make_node()

| Antes | Después |
|-------|---------|
| `def node_fn(ctx)` (sync) | `async def node_fn(ctx)` |
| `instance.execute(ctx.input_data)` | `await executor.execute(instance, ctx.input_data)` |
| Sin protección | Error boundary por stage |

### Verificación

```bash
$ ruff check stage_executor.py orchestrator.py
# EXIT: 0 — all checks passed

$ pytest tests/test_orchestrator_empty.py tests/test_integration.py tests/test_chain_orchestrator.py -v --tb=short -o "addopts="
# 16 passed
```

| Verificación | Resultado |
|-------------|-----------|
| `ruff check` — 0 errores | ✅ PASS |
| Orchestrator test (2 tests) | ✅ PASS |
| Integration tests (6 tests) | ✅ PASS |
| Chain orchestrator tests (8 tests) | ✅ PASS |
| Import correcto (`from agentic_pipeline.stage_executor import StageExecutor`) | ✅ PASS |

---

## 7. M2.3 — Modo offline / Graceful degradation (GD)

### Motivo

El pipeline dependía de componentes opcionales (SentenceTransformers, LLM) incluso para tareas que podían resolverse con lógica determinista. En entornos sin conectividad o recursos limitados, estos componentes fallaban ruidosamente. El modo offline provee una ruta de ejecución 100% determinista que degrada gracefulmente: salta enriquecimiento semántico y fuerza planificación heurística.

### Archivos modificados/creados

| Acción | Archivo | Cambio |
|--------|---------|--------|
| 🔧 Modificar | `config.py` | Agregado `offline: bool = False` a `PipelineConfig` |
| 🔧 Modificar | `nodes/perception_unit.py` | Salta SentenceTransformer si `config.offline` |
| 🔧 Modificar | `nodes/reasoning_engine.py` | Fuerza estrategia `"heuristic"` si `config.offline` |
| 🔧 Modificar | `compiler-bot/agentic` (CLI) | Nuevo flag `--offline` setea `pipeline_config.offline = True` |
| 📄 Crear | `docs/offline_mode.md` | Documentación del modo offline |

### Detalle de cambios

**config.py** — `PipelineConfig.offline: bool = False` (seteable vía `AGENTIC_OFFLINE` env var o flag CLI)

**perception_unit.py** — En `act()`, el enriquecimiento con SentenceTransformers se salta si `config.offline` está activo:
```python
clf = None if config.offline else self._get_semantic_classifier()
```

**reasoning_engine.py** — En `reflect_and_plan()`, la estrategia se fuerza a `"heuristic"` si `config.offline`:
```python
strategy = "heuristic" if config.offline or complexity in ("simple", "moderate") else "llm"
```

**CLI** — Nuevo flag `--offline`:
```python
parser.add_argument("--offline", action="store_true", help="Run in offline mode")
```

**offline_mode.md** — Documenta qué stages funcionan y cómo usar `--offline`.

### Stages no afectados

| Stage | Razón |
|-------|-------|
| Preprocessor | Siempre determinista |
| Lexer | Siempre DFA |
| Parser | Siempre Lark |
| Semantic | Siempre Visitor |
| IR Generator | Siempre determinista |
| Synthesis | Siempre scaffold |
| UI Generator | Siempre con guarda |
| Validator | Siempre Chain of Responsibility |

### Verificación

```bash
$ ruff check config.py nodes/perception_unit.py nodes/reasoning_engine.py compiler-bot/agentic
# EXIT: 0

$ python -c "
from agentic_pipeline.config import config
assert config.offline == False
config.offline = True
assert config.offline == True
print('Config offline mode OK')
"

$ pytest tests/test_integration.py tests/test_orchestrator_empty.py -v --tb=short -o "addopts="
# 8 passed
```

| Verificación | Resultado |
|-------------|-----------|
| `ruff check` — 0 errores | ✅ PASS |
| `config.offline` default `False` | ✅ PASS |
| `config.offline = True` funcional | ✅ PASS |
| Integration tests (6 tests) | ✅ PASS |
| Orchestrator tests (2 tests) | ✅ PASS |
| `docs/offline_mode.md` creado | ✅ PASS |

---

## 8. M2.4 — StageContext frozen (INM)

### Motivo

`StageContext` era un `BaseModel` mutable: cualquier node_fn en el StateGraph podía modificar `ctx.stage`, `ctx.input_data`, `ctx.config_overrides` o `ctx.last_error` por efecto secundario. Esto dificultaba el razonamiento sobre el flujo de datos (quién modifica qué y cuándo) y abría la puerta a bugs por mutación compartida entre stages. Se hizo frozen para garantizar inmutabilidad.

### Archivos modificados

| Acción | Archivo | Cambio |
|--------|---------|--------|
| 🔧 Modificar | `state_models.py` | `ConfigDict(frozen=True)` + `with_update()` |
| 🔧 Modificar | `orchestrator.py` | Mutaciones reemplazadas por `with_update()` en `_make_node()` y `_make_adapter_node()` |

### Cambios en state_models.py

```python
class StageContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    mission_id: str = Field(default_factory=lambda: datetime.now().isoformat())
    stage: Stage
    input_data: Any
    previous_output: Any | None = None
    config_overrides: dict = {}
    last_error: str | None = None

    def with_update(self, **kwargs: Any) -> "StageContext":
        return self.model_copy(update=kwargs)
```

### Cambios en orchestrator.py

**Antes** (mutación directa):
```python
ctx.stage = stage
ctx.config_overrides["output_dir"] = self._output_dir
instance = cls(ctx)
# ...
ctx.last_error = output.error
```

**Después** (inmutable):
```python
instance_ctx = ctx.with_update(
    stage=stage,
    config_overrides={**ctx.config_overrides, "output_dir": self._output_dir},
)
instance = cls(instance_ctx)
# ...
updates["last_error"] = output.error
```

El patrón clave es que las actualizaciones se devuelven en el dict de retorno del nodo, que StateGraph mergea automáticamente en una nueva copia frozen de StageContext. No se requiere `ctx = ctx.with_update(...)` dentro de node_fn.

### Verificación

```bash
$ ruff check state_models.py orchestrator.py
# EXIT: 0

$ python -c "
from agentic_pipeline.state_models import StageContext, Stage
from pydantic import ValidationError
ctx = StageContext(stage=Stage.INTENT, input_data='hola')
try:
    ctx.stage = Stage.PREPROCESSOR
    assert False, 'should be frozen'
except (TypeError, ValidationError):
    print('frozen')
new_ctx = ctx.with_update(input_data='mundo')
assert new_ctx.input_data == 'mundo'
assert ctx.input_data == 'hola'
print('with_update works')
"

$ pytest tests/test_integration.py tests/test_orchestrator_empty.py tests/test_chain_orchestrator.py tests/test_state_models.py -v --tb=short -o "addopts="
# 23 passed
```

| Verificación | Resultado |
|-------------|-----------|
| `ruff check` — 0 errores | ✅ PASS |
| `StageContext` frozen (TypeError/ValidationError al mutar) | ✅ PASS |
| `with_update()` crea nueva instancia sin mutar original | ✅ PASS |
| Integration tests (6 tests) | ✅ PASS |
| Orchestrator tests (2 tests) | ✅ PASS |
| Chain orchestrator tests (8 tests) | ✅ PASS |
| State model tests (7 tests) | ✅ PASS |

---

## 9. Estado de M2

| Sub-tarea | Estado |
|-----------|--------|
| **M2.1 — CircuitBreaker + ExponentialBackoff (R1)** | **✅ COMPLETADO** |
| **M2.2 — StageExecutor aislamiento (R3)** | **✅ COMPLETADO** |
| **M2.3 — Modo offline / Graceful degradation (GD)** | **✅ COMPLETADO** |
| **M2.4 — StageContext frozen (INM)** | **✅ COMPLETADO** |
