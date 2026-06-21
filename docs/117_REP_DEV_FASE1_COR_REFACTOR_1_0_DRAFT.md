---
id: 117
area: DEV
type: REP
module: FASE1_COR
version: 1.0
status: IMPLEMENTED
tags: [refactor, chain-of-responsibility, behavioral-patterns, fase-1]
summary: Reporte de la Fase 1 del refactor de patrones GoF — Chain of Responsibility
keywords: [CoR, PromptHandler, handler_base, PipelineStage, orchestrator]
changelog:
  - version: 1.0
    date: 2026-06-18
    author: bot
    description: Reporte inicial Fase 1 completada
---

# Fase 1: Chain of Responsibility — Reporte de Acciones

## Resumen

Se implementó el patrón **Chain of Responsibility (GoF)** en el prompt chain
del pipeline RECPL v2.0+, eliminando ~200 líneas de código duplicado en
handlers, simplificando `PipelineStage` con defaults Template Method, y
reduciendo `ChainOrchestrator` de 321 → ~95 líneas al reemplazar LangGraph
StateGraph por una cadena CoR directa.

## Archivos creados

| Archivo | Descripción |
|---------|-------------|
| `prompt_chain/handler_base.py` | Clase base `PromptHandler` (ABC), `PromptRequest`, `PromptResponse`. Implementa `set_next()` para encadenamiento, `handle()` con ciclo LLM→fallback→ctx→delegación |
| `tests/test_handler_chain.py` | 10 tests: CoR chain building, delegación, safety net, set_next fluent API |

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `prompt_chain/prompts/preprocess.py` | `preprocess_handler()` → `PreprocessHandler(PromptHandler)`. Template registration preserved |
| `prompt_chain/prompts/intent.py` | `intent_handler()` → `IntentHandler(PromptHandler)` |
| `prompt_chain/prompts/plan.py` | `plan_handler()` → `PlanHandler(PromptHandler)` |
| `prompt_chain/prompts/generate.py` | `generate_handler()` → `GenerateHandler(PromptHandler)` |
| `prompt_chain/prompts/verify.py` | `verify_handler()` → `VerifyHandler(PromptHandler)` |
| `prompt_chain/prompts/format.py` | `format_handler()` → `FormatHandler(PromptHandler)` |
| `prompt_chain/prompts/__init__.py` | Exporta clases handler en vez de módulos |
| `prompt_chain/__init__.py` | Exporta PromptHandler, PromptRequest, PromptResponse |
| `prompt_chain/orchestrator.py` | Simplificado de 321→95 líneas. Eliminado LangGraph StateGraph. Usa cadena CoR directa con retry loop |
| `base_stage.py` | `analyze()`, `reflect_and_plan()`, `learn_and_improve()` ahora tienen defaults no-abstract. Subclases solo necesitan `receive_mission()` + `act()` |
| `tests/test_prompt_preprocess.py` | Adaptado a API clase-handler |
| `tests/test_prompt_intent.py` | Adaptado a API clase-handler |
| `tests/test_prompt_plan.py` | Adaptado a API clase-handler |
| `tests/test_prompt_generate.py` | Adaptado a API clase-handler |
| `tests/test_prompt_verify.py` | Adaptado a API clase-handler |
| `tests/test_prompt_format.py` | Adaptado a API clase-handler |

## Detalles técnicos

### PromptHandler (CoR base)

```python
class PromptHandler(ABC):
    name: str
    output_contract: type[BaseModel] | None
    input_fields: list[str]

    def set_next(self, handler: PromptHandler) -> PromptHandler
    async def handle(self, request: PromptRequest, ctx: ChainContext) -> PromptResponse
    def _build_prompt_kwargs(self, request, ctx_data) -> dict  # abstract
    def _get_ctx_data(self, ctx) -> dict
```

Cada handler concreto define `name`, `output_contract`, `input_fields`, e
implementa `_build_prompt_kwargs()` para mapear datos del contexto a los
argumentos del template.

### PipelineStage simplificado

`analyze()`, `reflect_and_plan()` y `learn_and_improve()` ahora tienen
implementaciones por defecto, permitiendo que subclases implementen solo
`receive_mission()` y `act()`.

### ChainOrchestrator simplificado

- Eliminado: `ChainState` (TypedDict), `_node_*` methods, `_router_verify`, LangGraph `StateGraph`
- Nuevo: cadena CoR `pre→intent→plan→gen→verify` + retry loop + format final
- Misma API pública: `ChainOrchestrator(llm, debug_callback, max_retries)` + `run(raw_input)`

## Tests

- **54 tests** (10 nuevos + 44 existentes adaptados) — **PASS**
- **ruff check** — 0 errores
- **ruff format** — aplicado automáticamente

## Próximos pasos

- Fase 2: Command Pattern (encapsular generadores como comandos)
- Fase 3: Observer Pattern (eventos de pipeline)
