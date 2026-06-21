---
id: 109
area: dev
type: rep
module: prompt_chain_f3
version: 1.0
status: IMPLEMENTED
tags:
  - report
  - prompt-chaining
  - fase-3
  - orchestrator
  - implementation
summary: "Reporte de implementacion de la Fase 3 (Chain Orchestrator) del refactor a Prompt Chaining. ChainOrchestrator con LangGraph StateGraph, CLI --chain flag, 8 tests, 71 tests totales F1+F2+F3."
keywords:
  - report
  - fase-3
  - chain-orchestrator
  - langgraph
  - stategraph
  - cli
  - tests
changelog:
  - version: 1.0
    date: 2026-06-16
    author: workflow-agent
    description: Reporte de Fase 3 completada
---

# Reporte de Fase 3 — Chain Orchestrator

> **Documento fuente:** `106_PLAN_DEV_PROMPT_CHAIN_EXECUTION_1_0_DRAFT.md`
> **Documento de referencia:** `105_PROP_DEV_PROMPT_CHAIN_REFACTOR_1_0_DRAFT.md`
> **Version del reporte:** 1.0
> **Fecha:** 2026-06-16

---

## Resumen

Fase 3 del refactor a Prompt Chaining completada. Se implemento el
orquestador de la cadena de prompts con LangGraph StateGraph, el CLI
handler para el flag `--chain`, y la integracion en el entrypoint
`compiler-bot/agentic`.

### Cambios respecto al plan original

- **`ChainOrchestrator`:** No incluye `tool_registry`, `memory`, ni `world`
  como dependencias directas (no necesarios para la cadena basica). Se
  anadiran en Fase 4 cuando se integren los agentes.
- **Router `_router_verify`:** El plan original enviaba "abort" a `END`
  (terminacion sin output). Se cambio a "format" para que la cadena
  siempre produzca un `final_output`, incluso en caso de error. La
  validacion fallida se refleja en `success: False` del OutputContract.
- **`_preprocess_fallback`:** Retorna `segments` como string en vez de
  `list[str]`, lo que causa error de validacion contra `PreprocessorContract`.
  Esto impide que la cadena complete exitosamente cuando todos los LLM
  fallan (F3 workaround: el error se maneja gracefulmente via el handler
  de excepciones del nodo format). La correccion de este bug corresponde
  a F1 maintenance.

### Metricas

| Metrica | Valor |
|---------|-------|
| Archivos modificados (fuente) | 3 |
| Archivos nuevos (tests) | 1 |
| Total lineas de codigo (nuevas) | ~260 |
| Tests nuevos | 8 |
| Tests totales (F1+F2+F3) | 71/71 |
| Errores ruff | 0 |

### Archivos modificados/creados

| Archivo | Cambio | Proposito |
|---------|--------|-----------|
| `prompt_chain/orchestrator.py` | Modificado | ChainOrchestrator con LangGraph StateGraph |
| `prompt_chain/cli.py` | Existente (F3) | CLI handler: `add_chain_args()` + `run_chain()` |
| `compiler-bot/agentic` | Modificado | Flag `--chain` + routing |
| `tests/test_chain_orchestrator.py` | Nuevo | 8 tests para F3 |

---

## Tarea 3.1 — `prompt_chain/orchestrator.py`

**Archivo:** `prompt_chain/orchestrator.py` (314 lines)

### ChainState (TypedDict)

```python
class ChainState(TypedDict):
    raw_input: str
    ctx: ChainContext
    preprocess_output: dict | None
    intent_output: dict | None
    plan_output: dict | None
    generate_output: dict | None
    verify_output: dict | None
    format_output: dict | None
    final_output: dict | None
    attempt_count: int
    errors: list[str]
```

### ChainOrchestrator

```python
class ChainOrchestrator:
    def __init__(self, llm=None, debug_callback=None, max_retries=3)
    async def run(raw_input: str) -> dict
    def _build_graph() -> StateGraph
```

### Grafo LangGraph

```
preprocess → intent → plan → generate → verify → format
                                    ↑          │
                                    └── retry ──┘
                                               │
                                          abort → format (error output)
```

6 nodos, routing condicional post-verify:
- `retry` → regenerate (si `should_retry` y `attempt_count < max_retries`)
- `format` → continuar a formato (si `valid=True` o `attempt_count >= max_retries`)
- `abort` → formato con error (si `valid=False` y no retry posible)

### Nodos

Cada nodo:
1. Importa su handler correspondiente (lazy import dentro del metodo)
2. Ejecuta el handler con `ctx.get_fields()` del estado anterior
3. Publica en `ctx` via el handler
4. Captura excepciones y retorna `None` para el stage + log del error

### Router condicional

```python
def _router_verify(self, state: ChainState) -> str:
    verify = state.get("verify_output") or {}
    if verify.get("should_retry") and state["attempt_count"] < self._max_retries:
        return "retry"
    if verify.get("valid", False) or state["attempt_count"] >= self._max_retries:
        return "format"
    return "format"  # abort → format (siempre produce output)
```

### Aseguramiento de registro de prompts

`_ensure_prompts_registered()` con flag global `_PROMOTES_REGISTERED`
para garantizar que los 6 templates esten en `PromptRegistry` antes de
ejecutar cualquier nodo. Idempotente.

---

## Tarea 3.2 — `prompt_chain/cli.py`

**Archivo:** `prompt_chain/cli.py` (53 lines)

### `add_chain_args(parser)`

Anade `--chain` como `store_true` al parser de argparse.

### `run_chain(prompt, output_dir, debug_mode, show_output)`

1. Construye `ChainOrchestrator` con `debug_callback` opcional
   (reutiliza `PipelineDebugger` si debug_mode esta activo)
2. Ejecuta `orchestrator.run(prompt)`
3. Retorna `{"output": result, "success": True}`

---

## Tarea 3.3 — Integracion en `compiler-bot/agentic`

**Archivo:** `compiler-bot/agentic` (109 lines)

### Cambios

1. **Import:** `from agentic_pipeline.prompt_chain.cli import add_chain_args, run_chain`
2. **Parser:** `add_chain_args(parser)` despues de argumentos existentes
3. **Routing:** `if args.chain:` → `await run_chain(...)` antes del pipeline clasico

### Orden de evaluacion

```
if args.chain:
    → Prompt Chaining (nuevo)
elif args.debug:
    → PipelineDebugger (existente)
else:
    → PipelineOrchestrator (existente, clasico)
```

Sin `--chain`, el comportamiento es identico al anterior (compatibilidad
total hacia atras).

---

## Tarea 3.4 — Tests

**Archivo:** `tests/test_chain_orchestrator.py` (~330 lines)

| Test | Descripcion | Estado |
|------|-------------|--------|
| `test_orchestrator_full_flow` | Cadena completa con LLM mockeado, 6 llamadas, output valido | PASS |
| `test_orchestrator_verify_retry` | VERIFY retorna should_retry → GENERATE se re-ejecuta (8 llamadas) | PASS |
| `test_orchestrator_max_retries` | max_retries=2, verify siempre retry → format despues de 2 intentos | PASS |
| `test_orchestrator_fallback_only` | Todos los LLM fallan → error graceful via format handler | PASS |
| `test_orchestrator_debug_callback` | Callback recibe nombre y output de cada etapa (6 calls) | PASS |
| `test_orchestrator_invalid_input` | Input vacio → no crash, resultado dict | PASS |
| `test_cli_chain_flag` | `run_chain()` instancia ChainOrchestrator y llama `.run()` | PASS |
| `test_cli_no_chain_classic` | `add_chain_args()`: `--chain` default False, `--chain` True | PASS |

### Patron de setup

```python
def setup_method(self) -> None:
    import agentic_pipeline.prompt_chain.prompts as _pkg
    _ = _pkg
    PromptRegistry.clear()
    for mod_name in ["preprocess", "intent", "plan", "generate", "verify",
                      "format"]:
        mod = importlib.import_module(
            f"agentic_pipeline.prompt_chain.prompts.{mod_name}",
        )
        importlib.reload(mod)
    import agentic_pipeline.prompt_chain.orchestrator as orch_mod
    orch_mod._PROMOTES_REGISTERED = False
```

### Resultado global

```
F1+F2+F3: 71 passed in 2.03s
ruff: 0 errors
```

---

## Problemas conocidos

1. **Fallback de preprocess incompatible con contrato:** `_preprocess_fallback`
   retorna `segments` como string, pero `PreprocessorContract` espera
   `list[str]`. Esto causa que la cadena falle al validar el output del
   fallback. Workaround: el error es capturado por el handler de
   excepciones del nodo format, que produce un output de error con
   `success: False`. La correccion definitiva requiere modificar
   `_preprocess_fallback` en `fallbacks.py` (F1).

2. **Dependencia `torch` corrupta:** `test_llm_orchestrator.py` y
   `test_requirement_decomposer.py` no colectan por `libcudart.so.13`
   corrupto. Pre-existente, no afecta los tests de prompt chain.

---

## Proximos pasos (Fase 4 + Fase 5)

- **Fase 4:** Convertir los 5 agentes (Supervisor, Perception, Reasoning,
  Execution, Validator) en wrappers que usen los prompts del chain.
  Paralelizable con Fase 5.
- **Fase 5:** Feedback loop con auto-optimizacion de prompts basada en
  metricas de exito/falla de cada etapa. Paralelizable con Fase 4.
