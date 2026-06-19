# Reporte de Ejecución — M2: Resiliencia + SOLID Básico

- **ID:** 133_REP_DEV_M2_EXECUTION_REPORT_1_0_DRAFT
- **Tipo:** REP (Reporte)
- **Área:** DEV
- **Módulo:** agentic_pipeline
- **Versión:** 1.0
- **Estado:** DRAFT
- **Tags:** `execution-report`, `m2`, `circuit-breaker`, `exponential-backoff`, `resilience`, `llm-backend`
- **Fuente:** `docs/130_PLAN_DEV_MIGRATION_EXECUTION_1_0_DRAFT.md` (M2.1)
- **Changelog:**
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

## 6. Estado de M2

| Sub-tarea | Estado |
|-----------|--------|
| **M2.1 — CircuitBreaker + ExponentialBackoff (R1)** | **✅ COMPLETADO** |
| M2.2 — StageExecutor aislamiento (R3) | ⏳ Pendiente |
| M2.3 — Modo offline / Graceful degradation (GD) | ⏳ Pendiente |
| M2.4 — StageContext frozen (INM) | ⏳ Pendiente |
