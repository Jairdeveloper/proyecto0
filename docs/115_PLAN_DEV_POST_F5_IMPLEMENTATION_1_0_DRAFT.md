---
id: "115"
area: dev
type: plan
module: post_f5_implementation
version: "1.0"
status: "DRAFT"
tags:
  - "plan"
  - "prompt-chain"
  - "llm-cache"
  - "optimizer"
  - "dashboard"
  - "chore"
summary: "Plan de implementacion post-F5: integracion de LLMCache en LLMBackend, PromptOptimizer en ChainOrchestrator, backend Redis, y dashboard web"
keywords:
  - "post-f5"
  - "implementation plan"
  - "llm-cache integration"
  - "prompt-optimizer integration"
  - "redis backend"
  - "web dashboard"
changelog:
  - "2026-06-17: Plan inicial post-F5 con 4 tareas tecnicas"
---

# 115-PLAN-DEV-POST-F5-IMPLEMENTATION-1-0-DRAFT

> **Documento fuente:** `111_REP_DEV_PROMPT_CHAIN_F5_1_0_DRAFT.md` (seccion Proximos pasos)
> **Arquitectura de referencia:** `105_PROP_DEV_PROMPT_CHAIN_REFACTOR_1_0_DRAFT.md`
> **Estado de bugs:** `112_REP_DEV_BUGS_FIXES_1_0_DRAFT.md` (7 bugs fixeados)
> **Estado del codigo:** `113_REP_DEV_STATE_VS_LESSONS_1_0_DRAFT.md`
> **Version del plan:** 1.0
> **Fecha:** 2026-06-17

## Resumen

Plan de implementacion para los 4 proximos pasos post-F5:

1. Integrar `LLMCache` en `LLMBackend.generate_structured()` — cache
   automatico para todas las llamadas LLM
2. Integrar `PromptOptimizer.optimize()` en `ChainOrchestrator` — ajuste
   dinamico de temperatura por etapa
3. `LLMCache` con backend Redis — soporte multi-instancia
4. Dashboard web con graficos de evolucion de metricas

### Dependencias entre tareas

```
T1 (LLMCache → LLMBackend) ← ninguno
T2 (Optimizer → Orchestrator) ← T1 (opcional: usa cache para reducir ruido)
T3 (Redis backend) ← T1 (extiende LLMCache)
T4 (Web dashboard) ← T2 (necesita metricas del optimizer)
```

T1 y T2 son independientes y pueden ejecutarse en paralelo.
T3 depende de T1 (misma clase).
T4 depende de T2 (datos del optimizer).

---

## Tarea 1 — Integrar LLMCache en LLMBackend

**Archivos afectados:** `llm_backend.py`, `llm_cache.py`
**Dependencias:** Ninguna
**Estimacion:** 1 sesion
**Tests existentes:** 8 (test_llm_cache.py), 6 (test_llm_backend.py)
**Tests nuevos:** +4 (cache integration)

### Objetivo

Todas las llamadas a `LLMBackend.generate_structured()` deben pasar por
`LLMCache` automaticamente. En cache hit, retornar respuesta cacheada sin
invocar al LLM. En cache miss, invocar al LLM, almacenar resultado, y
retornar.

### Especificacion

#### 1.1 Inyectar LLMCache en LLMBackend

**Archivo:** `llm_backend.py`

- `LLMBackend.__init__()` acepta `cache: LLMCache | None = None`
- Si no se provee cache, `LLMCache(backend="memory")` por defecto (ya
  existe, zero-config)
- `FailoverLLMBackend` delega el cache a cada backend interno

#### 1.2 Cache en `generate_structured()`

**Archivo:** `llm_backend.py:OpenAIBackend.generate_structured()` (+
OllamaBackend, VLLMBackend)

Flujo modificado:

```python
async def generate_structured(self, prompt, system, output_schema, temperature):
    # 1. Construir key del cache
    cache_key_prompt = f"{system}\n\n{prompt}" if system else prompt
    schema_name = output_schema.__name__ if output_schema else "none"

    # 2. Cache hit → return inmediato
    cached = await self._cache.get(cache_key_prompt, schema_name)
    if cached is not None:
        return LLMResult(
            content=cached.get("content", ""),
            structured=cached.get("structured"),
            provider="cache",
            model="cache",
            duration=0.0,
            success=True,
        )

    # 3. Cache miss → invocar LLM (codigo existente)
    ...

    # 4. Si la llamada fue exitosa, almacenar en cache
    if result.success and result.structured:
        await self._cache.set(cache_key_prompt, schema_name, {
            "content": result.content,
            "structured": result.structured,
        })

    return result
```

#### 1.3 Cache en `generate()` (texto libre)

Opcional. El cache estructurado es prioritario porque:
- El output estructurado es deterministico (mismo prompt → mismo schema
  → mismo JSON esperado)
- El texto libre tiene mas variacion y menos beneficio de cache

#### 1.4 Tests nuevos

| Test | Descripcion |
|------|-------------|
| `test_cache_hit_returns_cached` | Llamada con mismo prompt+schema retorna cache sin invocar LLM |
| `test_cache_miss_invokes_llm` | Primera llamada invoca LLM, segunda usa cache |
| `test_cache_skipped_on_error` | LLM falla → no almacenar en cache |
| `test_cache_different_schema_different_key` | Mismo prompt, distinto schema → keys diferentes |

#### 1.5 Criterios de aceptacion

- [ ] `LLMBackend.generate_structured()` con cache habilitado retorna
      resultado cacheado en <1ms (vs 1-10s sin cache)
- [ ] Cache miss + LLM success → resultado almacenado automaticamente
- [ ] Cache miss + LLM failure → no almacenar, retornar error
- [ ] Backward compatible: `LLMBackend()` sin argumentos funciona igual
      (cache memory por defecto)
- [ ] `FailoverLLMBackend` tambien pasa por cache

---

## Tarea 2 — Integrar PromptOptimizer en ChainOrchestrator

**Archivos afectados:** `orchestrator.py`, `feedback_loop.py`
**Dependencias:** Ninguna (independiente de T1)
**Estimacion:** 1 sesion
**Tests existentes:** 5 (test_prompt_optimizer.py), 8 (test_chain_orchestrator.py)
**Tests nuevos:** +4 (optimizer integration)

### Objetivo

`ChainOrchestrator` debe consultar `PromptOptimizer` antes de ejecutar
cada etapa del chain y aplicar los parametros sugeridos (temperatura,
modelo) al `PromptTemplate` correspondiente.

### Especificacion

#### 2.1 Inicializar PromptOptimizer en ChainOrchestrator

**Archivo:** `orchestrator.py`

```python
class ChainOrchestrator:
    def __init__(self, llm=None, debug_callback=None, max_retries=3):
        ...
        self._optimizer = PromptOptimizer(metrics_store)
```

#### 2.2 Ajustar temperatura antes de cada etapa

En cada nodo (`_node_preprocess`, `_node_intent`, `_node_plan`, etc.),
antes de llamar al handler:

```python
async def _node_preprocess(self, state):
    params = self._optimizer.optimize("preprocess")
    # params → {"temperature": 0.15, "model": "gpt-4o-mini"}
    template = PromptRegistry.get("preprocess")
    if "temperature" in params:
        template.temperature = params["temperature"]
    if "model" in params:
        # self._llm puede necesitar reconexion con nuevo modelo
        ...
```

**Alternativa:** Pasar `temperature` como parametro adicional al handler
en vez de mutar el template global. Esto evita efectos secundarios entre
ejecuciones concurrentes.

```python
output = await preprocess_handler(
    raw_text=state["raw_input"],
    llm=self._llm,
    ctx=state["ctx"],
    temperature=params.get("temperature"),  # override opcional
)
```

#### 2.3 Modificar handlers para aceptar temperature override

Cada handler (`preprocess_handler`, `intent_handler`, etc.) debe aceptar
`temperature: float | None = None` como parametro opcional.

Si se provee, usarlo en `llm.generate_structured(temperature=...)`.
Si no se provee, usar `template.temperature` (comportamiento actual).

#### 2.4 Metricas post-ejecucion

Despues de cada etapa, registrar metricas:

```python
async def _node_preprocess(self, state):
    t0 = time.time()
    output = await preprocess_handler(...)
    duration = time.time() - t0
    self._optimizer.metrics.record_prompt("preprocess", {
        "success": output is not None,
        "duration": duration,
        "fallback_used": output is None or ...,
    })
```

#### 2.5 Tests nuevos

| Test | Descripcion |
|------|-------------|
| `test_optimizer_lowers_temperature` | PromptOptimizer reduce temperatura tras fallos |
| `test_orchestrator_uses_optimizer_params` | ChainOrchestrator aplica params del optimizer |
| `test_temperature_override_in_handler` | Handler usa temperatura pasada como override |
| `test_optimizer_no_data_no_change` | Sin datos historicos, optimizer no modifica nada |

#### 2.6 Criterios de aceptacion

- [ ] `ChainOrchestrator` consulta `PromptOptimizer.optimize()` antes
      de cada etapa
- [ ] La temperatura del handler se ajusta segun las recomendaciones
      del optimizer
- [ ] Metricas de cada etapa se registran post-ejecucion
- [ ] Sin datos historicos, el comportamiento es identico al actual
- [ ] Backward compatible: `PromptOptimizer(store)` sin store funciona

---

## Tarea 3 — LLMCache con backend Redis

**Archivos afectados:** `llm_cache.py` (nuevo backend), `pyproject.toml` (opcional: redis-py)
**Dependencias:** Tarea 1 (extiende misma clase)
**Estimacion:** 0.5 sesion
**Tests existentes:** 8 (test_llm_cache.py)
**Tests nuevos:** +3 (redis backend)

### Objetivo

Agregar backend `"redis"` a `LLMCache` para soporte multi-instancia
(mismos contenedores comparten cache via Redis).

### Especificacion

#### 3.1 Backend Redis

```python
class LLMCache:
    def __init__(self, backend="memory", redis_url=None, ttl=3600):
        if backend == "redis":
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(redis_url or "redis://localhost:6379")
            self._ttl = ttl
        elif backend == "sqlite":
            ...
        else:
            self._store = {}
```

#### 3.2 Metodos async

```python
async def get(self, prompt, schema):
    key = self._make_key(prompt, schema)
    if self._backend == "redis":
        data = await self._redis.get(key)
        return json.loads(data) if data else None
    ...

async def set(self, prompt, schema, response):
    key = self._make_key(prompt, schema)
    if self._backend == "redis":
        await self._redis.setex(key, self._ttl, json.dumps(response))
    ...

async def clear(self):
    if self._backend == "redis":
        keys = await self._redis.keys(f"{self._prefix}*")
        if keys:
            await self._redis.delete(*keys)
    ...

def stats(self):
    if self._backend == "redis":
        info = await self._redis.info()
        return {"backend": "redis", "used_memory": info["used_memory_human"], ...}
    ...
```

#### 3.3 Tests nuevos

| Test | Descripcion |
|------|-------------|
| `test_redis_set_and_get` | Set y get con Redis (requiere mock Redis) |
| `test_redis_ttl_expiry` | TTL vence -> get retorna None |
| `test_redis_clear` | Clear elimina todas las keys |

**Nota:** Los tests Redis deben usar `fakeredis` o `mock` para no
requerir una instancia Redis real en CI.

#### 3.4 Criterios de aceptacion

- [ ] `LLMCache(backend="redis")` funciona con URL configurable
- [ ] TTL configurable (default 3600s = 1 hora)
- [ ] Misma API que backend memory (get, set, clear, stats)
- [ ] Tests pasan sin Redis real (usando mock/fakeredis)
- [ ] redis-py no es dependencia obligatoria (import diferido)

---

## Tarea 4 — Dashboard web con graficos

**Archivos afectados:** Nuevo modulo `dashboard/`
**Dependencias:** Tarea 2 (metricas del optimizer)
**Estimacion:** 2 sesiones
**Tests:** N/A (UI)

### Objetivo

Dashboard web local que muestra evolucion de metricas del pipeline
(prompt chain + clasico) con graficos temporales.

### Especificacion

#### 4.1 Stack propuesto

- **Backend:** FastAPI (ya existe en `compiler-bot/agentic_pipeline/web/`)
  o servidor minimalista integrado en el CLI
- **Frontend:** HTML + Chart.js (sin build step, CDN)
- **Datos:** Lee del `MetricsStore` existente (SQLite o JSON)

#### 4.2 Endpoints de la API

| Endpoint | Datos |
|----------|-------|
| `GET /api/metrics/summary` | Resumen global (total records, errors, success rate) |
| `GET /api/metrics/per-stage` | Records por etapa del pipeline clasico |
| `GET /api/metrics/prompt-chain` | Prompt chain per-stage (calls, success_rate, avg_duration) |
| `GET /api/metrics/timeline?hours=24` | Evolucion temporal de metricas |
| `GET /api/metrics/prompt-chain/timeline?hours=24` | Evolucion temporal de prompt chain |

#### 4.3 Vistas del dashboard

```
=== Dashboard RECPL ===
[Summary] [Pipeline] [Prompt Chain] [Timeline]

Summary:
  Total records: 1,234
  Success rate:  96.7%
  Active stages: 10

Pipeline (bar chart):
  preprocess  ████████████ 120
  lexer       ██████████   100
  parser      ████████     80
  ...

Prompt Chain (bar chart):
  preprocess  ████████████████ 95.5% success
  intent      ████████████████ 100%
  plan        ██████████████   90%
  ...

Timeline (line chart):
  Success rate over last 24h
  ──────────────────────────────
  ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁
```

#### 4.4 Comando para iniciar dashboard

```bash
python compiler-bot/agentic --dashboard
# Server running on http://localhost:8080
```

#### 4.5 Criterios de aceptacion

- [ ] `--dashboard` inicia servidor web en puerto configurable
- [ ] 5 endpoints API devuelven datos del MetricsStore
- [ ] Graficos de barras para stages del pipeline clasico
- [ ] Graficos de barras para prompt chain per-stage
- [ ] Timeline de 24h con success rate y errores
- [ ] Pagina HTML estatica servida desde el CLI
- [ ] Sin dependencias externas (Chart.js via CDN)

---

## Roadmap

```
Sesion 1:
  T1: Integrar LLMCache en LLMBackend.generate_structured()
  T2: Integrar PromptOptimizer en ChainOrchestrator

Sesion 2:
  T3: Backend Redis para LLMCache
  T4: Dashboard web (endpoints API + HTML)

Sesion 3 (opcional):
  T4: Graficos de timeline 24h
  T4: Pull request + documentacion
```

### Verificacion

```bash
# Tests post-implementacion
python -m pytest compiler-bot/agentic_pipeline/tests/ -v -k "chain or prompt or metric or optimizer or cache" -q
# Expected: ~93 tests (75 existentes + ~11 nuevos)

# Ruff
ruff check compiler-bot/agentic_pipeline/ && ruff format --check compiler-bot/agentic_pipeline/

# Smoke test
python compiler-bot/agentic -p "crea modulo" --chain
python compiler-bot/agentic --metrics table
python compiler-bot/agentic --dashboard  # si T4 implementado
```
