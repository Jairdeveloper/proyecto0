---
id: "112"
area: "DEV"
type: "REP"
module: "BUGS_FIXES"
version: "1.0"
status: "DRAFT"
tags:
  - "bugs"
  - "fixes"
  - "prompt-chain"
  - "pipeline"
summary: "Reporte de bugs encontrados en el pipeline --chain y sus soluciones documentadas"
keywords:
  - "prompt chain"
  - "bugs"
  - "fix"
  - "ctx.set_output"
  - "segmentation filter"
  - "openai sentinel"
changelog:
  - "2026-06-17: Reporte inicial con 5 bugs y sus fixes"
---

# 112-REP-DEV-BUGS-FIXES-1-0-DRAFT

## Reporte de Bugs y Fixes — Pipeline Prompt Chaining (`--chain`)

### Contexto

Al ejecutar `python compiler-bot/agentic -p "crea modulo" --chain --debug step`,
se detectaron 5 bugs que causaban una cascada de fallos en el pipeline
completo. Este documento describe cada bug, su sintoma, causa raiz y la
solucion aplicada.

### Prueba de regresion

```bash
python compiler-bot/agentic -p "crea modulo" --chain --debug step
```

Output original:
```
_sqlite3 C module not available; falling back to JSON file store
OpenAI backend init failed: .../libcudart.so.13: file too short
OpenAI generate_structured failed: 'object' object has no attribute 'ainvoke'
Ollama generate failed: All connection attempts failed
preprocess failed: 1 validation error for PreprocessorContract
  segments: Input should be a valid list [input_value='crea modulo', input_type=str]
intent failed: "Stage 'preprocess' not found in context"
plan failed: "Stage 'intent' not found in context"
generate failed: "Stage 'plan' not found in context"
verify failed: "Stage 'intent' not found in context"
format failed: "Stage 'plan' not found in context"
{
  "output": { "success": false, ... },
  "success": true
}
```

---

## Bug #1 — SegmentationFilter retorna string, no lista

| Campo | Valor |
|---|---|
| **Archivo** | `compiler-bot/agentic_pipeline/prompt_chain/fallbacks.py` |
| **Sintoma** | `Input should be a valid list [input_value='crea modulo', input_type=str]` |
| **Causa raiz** | `SegmentationFilter.process()` en `preprocessor.py:77` retorna `" [SEG] ".join(segments)` (string), pero `PreprocessorContract.segments` espera `list[str]`. El fallback `_preprocess_fallback` pasa el string directamente sin conversion. |

### Fix aplicado

En `fallbacks.py:_preprocess_fallback`, convertir el output de
`SegmentationFilter.process()` a lista:

```python
segments_raw = sf.process(normalized)
if isinstance(segments_raw, str):
    segments = [s.strip() for s in segments_raw.split("[SEG]") if s.strip()]
else:
    segments = segments_raw
```

---

## Bug #2 — OpenAI sentinel `object()` sin metodo `ainvoke`

| Campo | Valor |
|---|---|
| **Archivo** | `compiler-bot/agentic_pipeline/prompt_chain/llm_backend.py` |
| **Sintoma** | `OpenAI generate_structured failed: 'object' object has no attribute 'ainvoke'` |
| **Causa raiz** | En `_ensure_llm()`, al fallar la inicializacion de `ChatOpenAI` (CUDA corrupto `libcudart.so.13`), se asigna `self._llm = object()` como centinela. Luego `generate()` y `generate_structured()` llaman `self._llm.ainvoke(messages)` sobre un `object()` generico. |

### Fix aplicado

En `llm_backend.py`, anadir guard clause en `generate()` y
`generate_structured()` de `OpenAIBackend`:

```python
self._ensure_llm()
if not hasattr(self._llm, "ainvoke"):
    return LLMResult(
        provider="openai", model=self._model,
        success=False, error="OpenAI backend unavailable (init failed)",
    )
```

---

## Bug #3 — ValidationError en `ctx.set_output` elimina la etapa del `ChainContext`

| Campo | Valor |
|---|---|
| **Archivo** | `compiler-bot/agentic_pipeline/prompt_chain/prompts/preprocess.py` (y todos los handlers) |
| **Sintoma** | `intent failed: "Stage 'preprocess' not found in context"` (cascada a todas las etapas siguientes) |
| **Causa raiz** | Cuando `ctx.set_output("preprocess", output, contract=PreprocessorContract)` lanza `ValidationError` (por Bug #1), la excepcion se propaga fuera del handler. `ctx._data["preprocess"]` nunca se escribe. Las etapas siguientes llaman `ctx.get_fields("preprocess", ...)` y obtienen `KeyError`. |

### Fix aplicado

En cada handler (`preprocess.py`, `intent.py`, `plan.py`, `generate.py`,
`verify.py`, `format.py`), envolver `ctx.set_output()` en try/except:

```python
if ctx:
    try:
        ctx.set_output("stage", output, contract=SomeContract)
    except Exception as exc:
        logger.warning("stage ctx.set_output failed: %s", exc)
```

Archivos modificados:
- `prompts/preprocess.py`
- `prompts/intent.py`
- `prompts/plan.py`
- `prompts/generate.py`
- `prompts/verify.py`
- `prompts/format.py`

---

## Bug #4 — `--chain` retorna `success: true` aunque todo falle

| Campo | Valor |
|---|---|
| **Archivo** | `compiler-bot/agentic_pipeline/prompt_chain/cli.py` |
| **Sintoma** | Output JSON: `"output": { "success": false }, "success": true` |
| **Causa raiz** | `cli.py:53` hardcodea `"success": True` en el wrapper de respuesta: `return {"output": result, "success": True}` |

### Fix aplicado

En `cli.py:run_chain()`, leer `success` del resultado de la chain:

```python
success = result.get("success", True) if isinstance(result, dict) else True
return {"output": result, "success": success}
```

---

## Bug #5 — Fallback del preprocessor no validado contra contrato

| Campo | Valor |
|---|---|
| **Archivo** | `compiler-bot/agentic_pipeline/prompt_chain/prompts/preprocess.py` |
| **Sintoma** | El output del fallback rule-based no cumple `PreprocessorContract` |
| **Causa raiz** | Los fallbacks del pipeline clasico retornan datos en formato legacy (strings donde se esperan listas). No hay validacion intermedia entre el fallback y `ctx.set_output()`. |

Este bug se resuelve indirectamente con el Fix #1 (convertir segments a
lista) y el Fix #3 (try/except en ctx.set_output). La combinacion asegura
que:

1. El fallback produce datos compatibles con el contrato (Fix #1)
2. Si aun asi falla la validacion, no mata la etapa (Fix #3)

---

## Bug #6 — `_plan_fallback` usa keyword arg `description` inexistente

| Campo | Valor |
|---|---|
| **Archivo** | `compiler-bot/agentic_pipeline/prompt_chain/fallbacks.py` |
| **Sintoma** | `GoalTreePlanner.decompose() got an unexpected keyword argument 'description'` |
| **Causa raiz** | El metodo `GoalTreePlanner.decompose()` espera `objective` como primer parametro, pero `_plan_fallback` pasa `description=module or ""` por keyword. Bug pre-existente oculto por la cascada de Bug #3. |

### Fix aplicado

```python
objective = module or ""
goal = planner.decompose(
    objective=objective,
    intent=intent,
    entities=entities,
)
```

---

## Bug #7 — `_generate_fallback` usa import y API incorrectos

| Campo | Valor |
|---|---|
| **Archivo** | `compiler-bot/agentic_pipeline/prompt_chain/fallbacks.py` |
| **Sintoma** | `No module named 'agentic_pipeline.generators.generator_factory'` |
| **Causa raiz** | Dos problemas: (1) importa `generator_factory` en vez de `base_generator`; (2) llama `factory.generate(task)` pero `GeneratorFactory` solo tiene `get_generator(target)`. Bug pre-existente oculto por la cascada. |

### Fix aplicado

```python
from agentic_pipeline.generators.base_generator import GeneratorFactory
...
generator = GeneratorFactory.get_generator(target)
created = generator.generate(task, Path("modules"))
```

---

### Resumen de archivos modificados

| Archivo | Cambio |
|---|---|
| `fallbacks.py` | Convertir segments de string a lista; corregir `description`→`objective`; corregir import + API de GeneratorFactory |
| `llm_backend.py` | Guard clause `hasattr(self._llm, "ainvoke")` en OpenAIBackend |
| `prompts/preprocess.py` | try/except en ctx.set_output |
| `prompts/intent.py` | try/except en ctx.set_output |
| `prompts/plan.py` | try/except en ctx.set_output |
| `prompts/generate.py` | try/except en ctx.set_output |
| `prompts/verify.py` | try/except en ctx.set_output |
| `prompts/format.py` | try/except en ctx.set_output |
| `cli.py` | Leer `success` del resultado de la chain |
| `test_chain_orchestrator.py` | Actualizar test `test_orchestrator_fallback_only` a 6 LLM calls + assert success=True |

### Estado post-fix

```bash
# Verify el pipeline --chain arranca sin cascada de errores
python compiler-bot/agentic -p "crea modulo" --chain --debug step
# Expected: preprocess succeed via fallback, pipeline continua
```

### Lecciones aprendidas

1. **Contract-driven development**: Los contratos Pydantic deben estar
   alineados con el output real de los fallbacks rule-based. La conversion
   debe ser explicita.
2. **Graceful degradation**: Cada etapa debe poder fallar sin matar las
   siguientes. `ctx.set_output` no debe ser un bottleneck critico.
3. **Sentinel objects**: Usar `object()` como centinela requiere check
   de capacidades (`hasattr`) antes de invocar metodos.
4. **Success propagation**: El estado de exito debe propagarse desde el
   nivel mas interno hasta el wrapper CLI sin hardcodeos.
