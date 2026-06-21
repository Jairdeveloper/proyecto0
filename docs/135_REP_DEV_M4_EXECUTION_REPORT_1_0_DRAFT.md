---
area: dev
type: REP
module: M4
version: 1.0
status: IMPLEMENTED
---
# Reporte de Ejecución — M4: Rendimiento + Seguridad

- **ID:** 135_REP_DEV_M4_EXECUTION_REPORT_1_0_DRAFT
- **Tipo:** REP (Reporte)
- **Área:** DEV
- **Módulo:** agentic_pipeline
- **Versión:** 1.3
- **Estado:** DRAFT
- **Tags:** `execution-report`, `m4`, `fixtures`, `conftest`, `testing`, `security`, `bandit`, `blocked-patterns`, `rate-limiter`, `token-bucket`, `stage-models`
- **Fuente:** `docs/130_PLAN_DEV_MIGRATION_EXECUTION_1_0_DRAFT.md` (M4.1–M4.4)
- **Changelog:**
  - 1.3 — 2026-06-19: Añadido M4.4 — Modelos LLM diferenciados por stage
  - 1.2 — 2026-06-19: Añadido M4.3 — TokenBucket rate limiter
  - 1.1 — 2026-06-19: Añadido M4.2 — SecurityScanner + BanditScanner
  - 1.0 — 2026-06-19: Versión inicial — M4.1 Fixtures compartidas

---

## 1. Resumen

| Aspecto | Valor |
|---------|-------|
| Sprint | M4 — Rendimiento + Seguridad |
| Tarea | M4.1 — Fixtures compartidas (T2) |
| Esfuerzo estimado | 4.5h |
| Esfuerzo ejecutado | ~0.3h |
| Estado | **COMPLETADO** |

---

## 2. Motivo del cambio

Los tests existentes definían sus propios prompts, contexts y directorios temporales de forma ad-hoc. No había fixtures compartidas, lo que generaba duplicación y dificultaba la escritura de nuevos tests. Se agregaron fixtures reutilizables en `conftest.py`.

---

## 3. Archivos modificados

| Acción | Archivo | Cambio |
|--------|---------|--------|
| 🔧 Modificar | `tests/conftest.py` | Agregadas 5 fixtures compartidas |

### Fixtures agregadas

| Fixture | Tipo | Descripción |
|---------|------|-------------|
| `mock_context` | `StageContext` | Contexto con `Stage.PREPROCESSOR`, `input_data="test input"` |
| `mock_ir_project` | `IRProject` | Proyecto IR con una entidad `User` hija |
| `temp_output_dir` | `Path` | Directorio temporal (`tmp_path/output`) |
| `sample_prompts` | `dict[str, str]` | Prompts de prueba: create_payments_module, create_user_entity, create_crud_product, explain_pipeline, empty |
| `expected_dashboard_files` | `list[str]` | Archivos esperados tras scaffold: `.module.ts`, `.controller.ts`, `.service.ts`, `.prisma` |

---

## 4. Verificación

```bash
$ ruff check tests/conftest.py
# EXIT: 0

$ pytest tests/conftest.py --fixtures -o "addopts=" | grep -E "mock_|sample_|temp_"
# mock_context, mock_ir_project, temp_output_dir, sample_prompts

$ pytest tests/test_base_stage.py tests/test_integration.py tests/test_orchestrator_empty.py -v --tb=short -o "addopts="
# 11 passed
```

| Verificación | Resultado |
|-------------|-----------|
| `ruff check` — 0 errores | ✅ PASS |
| `mock_context` fixture listada | ✅ PASS |
| `mock_ir_project` fixture listada | ✅ PASS |
| `temp_output_dir` fixture listada | ✅ PASS |
| `sample_prompts` fixture listada | ✅ PASS |
| `expected_dashboard_files` fixture listada | ✅ PASS |
| Tests existentes siguen pasando (11 tests) | ✅ PASS |

---

## 5. M4.2 — SecurityScanner + BanditScanner (S1)

### Motivo

El pipeline generaba código NestJS/Prisma sin verificar que no contuviera constructos peligrosos (`eval`, `exec`, `os.system`, etc.). Un prompt malicioso o un modelo comprometido podría inyectar código inseguro en los archivos generados. Se implementó un doble mecanismo de defensa:
1. `BanditScanner(StageObserver)` — reacciona a eventos del pipeline (synthesis)
2. `SecurityScanner(Validator)` — escanea directorios de salida como eslabón final de Chain of Responsibility

Ambos usan `BLOCKED_PATTERNS` del módulo `security/policies.py`.

### Archivos creados/modificados

| Acción | Archivo | Cambio |
|--------|---------|--------|
| 📄 Crear | `security/__init__.py` | Init del módulo security |
| 📄 Crear | `security/policies.py` | `BLOCKED_PATTERNS` — 6 regex para eval, exec, os.system, subprocess.call, pickle.loads, __import__ |
| 📄 Crear | `security/bandit_scanner.py` | `BanditScanner(StageObserver)` — escanea archivos generados en evento `synthesis` |
| 🔧 Modificar | `nodes/validator.py` | `SecurityScanner` ahora también verifica `BLOCKED_PATTERNS` |

### BanditScanner

```python
class BanditScanner(StageObserver):
    def on_event(self, event: StageEvent) -> None:
        if event.stage != "synthesis":
            return
        for filepath in event.output.get("generated_files", []):
            content = Path(filepath).read_text()
            for pattern in BLOCKED_PATTERNS:
                if pattern.search(content):
                    event.metadata["security_alert"] = f"Blocked pattern in {filepath}"
```

### SecurityScanner (modificado)

El `SecurityScanner` existente en `validator.py` ya era el eslabón final de la cadena CoR (`syntax → types → security`). Se modificó su método `validate()` para también iterar sobre `BLOCKED_PATTERNS` y reportar hallazgos como errores.

```python
# Dentro de SecurityScanner.validate():
for blocked in _BLOCKED_PATTERNS:
    if blocked.search(content):
        rel = filepath.relative_to(output_dir)
        findings.append(f"Blocked pattern in {rel}")
```

### Verificación

```bash
$ ruff check security/ nodes/validator.py
# EXIT: 0

$ python -c "
from agentic_pipeline.security.bandit_scanner import BanditScanner
from agentic_pipeline.security.policies import BLOCKED_PATTERNS
from agentic_pipeline.nodes.validator import SecurityScanner
assert len(BLOCKED_PATTERNS) == 6
print('OK')
"

$ pytest tests/test_validator_chain.py tests/test_observer_pattern.py tests/test_integration.py -v --tb=short -o "addopts="
# 36 passed (11 validator + 19 observer + 6 integration)
```

| Verificación | Resultado |
|-------------|-----------|
| `ruff check` — 0 errores | ✅ PASS |
| `BLOCKED_PATTERNS` tiene 6 patrones | ✅ PASS |
| `BanditScanner` se instancia correctamente | ✅ PASS |
| `SecurityScanner` importa sin errores | ✅ PASS |
| Validator chain tests (11 tests) | ✅ PASS |
| Observer pattern tests (19 tests) | ✅ PASS |
| Integration tests (6 tests) | ✅ PASS |

---

## 6. M4.3 — TokenBucket rate limiter (S4)

### Motivo

Las llamadas a la API del LLM no tenían control de tasa. En pipelines con múltiples stages que llaman al LLM en paralelo, era posible exceder los rate limits de OpenAI (ej. 5000 RPM en gpt-4o-mini) y recibir errores 429. Se implementó un TokenBucket thread-safe para limitar la tasa de llamadas.

### Archivos creados/modificados

| Acción | Archivo | Cambio |
|--------|---------|--------|
| 📄 Crear | `security/token_bucket.py` | `TokenBucket` thread-safe con `consume()` y `available` |
| 🔧 Modificar | `prompt_chain/llm_backend.py` | `_rate_limiter` + `set_rate_limiter()` + integración en `_call_with_retry()` |

### TokenBucket

```python
class TokenBucket:
    def __init__(self, capacity: int = 60, refill_rate: float = 1.0):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
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

- `capacity`: máximo de tokens acumulables (burst)
- `refill_rate`: tokens/segundo que se regeneran
- `consume()`: thread-safe via `threading.Lock`

### Integración en LLMBackend

Se agregó al `LLMBackend` base:
- `_rate_limiter: TokenBucket | None`
- `set_rate_limiter(limiter)` — setter para inyectar

En `OpenAIBackend._call_with_retry()`, antes de ejecutar la función se verifica el rate limiter:
```python
if self._rate_limiter is not None:
    while not self._rate_limiter.consume():
        await asyncio.sleep(0.1)
```

Si el bucket está vacío, espera 100ms y reintenta hasta conseguir un token. Esto garantiza que nunca se supere la tasa configurada.

### Verificación

```bash
$ ruff check security/token_bucket.py prompt_chain/llm_backend.py
# EXIT: 0

$ python -c "
from agentic_pipeline.security.token_bucket import TokenBucket
tb = TokenBucket(capacity=10, refill_rate=10.0)
assert tb.consume(5) == True
assert tb.consume(5) == True
assert tb.consume(1) == False
print('OK')
"

$ pytest tests/test_llm_backend.py -v --tb=short -o "addopts="
# 8 passed
```

| Verificación | Resultado |
|-------------|-----------|
| `ruff check` — 0 errores | ✅ PASS |
| `TokenBucket.consume()` retorna True con tokens disponibles | ✅ PASS |
| `TokenBucket.consume()` retorna False sin tokens | ✅ PASS |
| `set_rate_limiter()` acepta `TokenBucket | None` | ✅ PASS |
| LLMBackend tests (8 tests) | ✅ PASS |

---

## 7. M4.4 — Modelos LLM diferenciados por stage (E2)

### Motivo

Todos los stages del pipeline usaban el mismo modelo LLM (`gpt-4o-mini` por defecto). Tareas simples como preprocesamiento o formateo no necesitan un modelo grande, mientras que tareas complejas como planificación o generación se benefician de `gpt-4o`. Se agregó un mapa `stage_models` en la configuración para asignar modelos específicos por stage, y se añadió soporte para override de modelo por llamada en `LLMBackend`.

### Archivos modificados

| Acción | Archivo | Cambio |
|--------|---------|--------|
| 🔧 Modificar | `config.py` | Agregado `stage_models: dict[str, str]` con 7 entradas |
| 🔧 Modificar | `prompt_chain/llm_backend.py` | Parámetro `model` opcional en `generate()`, `generate_structured()`, y `_ensure_llm()` |

### Config

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

- `gpt-4o-mini` para tareas ligeras (preprocess, format)
- `gpt-4o` para tareas que requieren razonamiento (intent, plan, reasoning, generate, verify)

### LLMBackend model override

Se agregó el parámetro opcional `model: str | None` a:
- `LLMBackend.generate()` (abstracto)
- `LLMBackend.generate_structured()` (abstracto)
- `OpenAIBackend.generate()` — si se provee, recrea el cliente con el modelo indicado
- `OpenAIBackend.generate_structured()` — ídem
- `OpenAIBackend._ensure_llm()` — recrea `self._llm` si el modelo cambia

El override permite que los handlers del prompt chain seleccionen el modelo según `config.stage_models[stage_name]` al llamar a `generate()`.

### Verificación

```bash
$ ruff check config.py prompt_chain/llm_backend.py
# EXIT: 0

$ python -c "
from agentic_pipeline.config import PipelineConfig
c = PipelineConfig()
assert 'preprocess' in c.stage_models
assert c.stage_models['intent'] == 'gpt-4o'
print('M4.4 OK')
"

$ pytest tests/test_llm_backend.py -v --tb=short -o "addopts="
# 8 passed
```

| Verificación | Resultado |
|-------------|-----------|
| `ruff check` — 0 errores | ✅ PASS |
| `PipelineConfig.stage_models` tiene 7 entradas | ✅ PASS |
| `stage_models["preprocess"] == "gpt-4o-mini"` | ✅ PASS |
| `stage_models["intent"] == "gpt-4o"` | ✅ PASS |
| `generate()` acepta `model` keyword | ✅ PASS |
| `generate_structured()` acepta `model` keyword | ✅ PASS |
| LLMBackend tests (8 tests) | ✅ PASS |

---

## 8. Estado de M4

| Sub-tarea | Estado |
|-----------|--------|
| **M4.1 — Fixtures compartidas (T2)** | **✅ COMPLETADO** |
| **M4.2 — SecurityScanner + BanditScanner (S1)** | **✅ COMPLETADO** |
| **M4.3 — TokenBucket rate limiter (S4)** | **✅ COMPLETADO** |
| **M4.4 — Modelos LLM diferenciados (E2)** | **✅ COMPLETADO** |
