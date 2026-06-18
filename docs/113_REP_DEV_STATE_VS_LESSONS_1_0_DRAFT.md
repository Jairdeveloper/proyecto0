---
id: "113"
area: "DEV"
type: "REP"
module: "STATE_VS_LESSONS"
version: "1.0"
status: "DRAFT"
tags:
  - "state"
  - "lessons"
  - "audit"
  - "prompt-chain"
summary: "Estado actual del codigo base comparado contra las 4 lecciones aprendidas del reporte 112"
keywords:
  - "lessons learned"
  - "codebase audit"
  - "prompt chain"
  - "contract-driven"
  - "graceful degradation"
  - "sentinel"
  - "success propagation"
changelog:
  - "2026-06-17: Reporte inicial de estado vs lecciones aprendidas"
---

# 113-REP-DEV-STATE-VS-LESSONS-1-0-DRAFT

## Estado del Codigo Base vs Lecciones Aprendidas

### Contexto

El reporte `112_REP_DEV_BUGS_FIXES_1_0_DRAFT.md` documento 7 bugs
encontrados en el pipeline `--chain` (Prompt Chaining) y sus soluciones.
De ahi se extrajeron 4 lecciones aprendidas. Este reporte audita el
codigo base actual (commit `583a7ec`) contra cada leccion, identificando
que se ha implementado, que falta, y riesgos residuales.

---

## Leccion 1: Contract-driven development

> "Los contratos Pydantic deben estar alineados con el output real de los
> fallbacks rule-based. La conversion debe ser explicita."

### Estado actual: ✅ Implementado (con riesgos menores)

| Fallback | Contrato | Compatible? |
|---|---|---|
| `_preprocess_fallback` | `PreprocessorContract` | ✅ Si (conversion explicita `str`→`list` via `split("[SEG]")`) |
| `_intent_fallback` | `NLPContract` | ✅ Si |
| `_plan_fallback` | `PlannerContract` | ✅ Si |
| `_generate_fallback` | `SynthesisContract` | ✅ Si |
| `_verify_fallback` | `ValidatorContract` | ✅ Si |
| `_format_fallback` | `OutputContract` | ✅ Si |

**Conversion explicita:** La unica conversion necesaria era en
`_preprocess_fallback` (Bug #1): `SegmentationFilter.process()` retorna
`str` pero `PreprocessorContract.segments` espera `list[str]`. El fix
aplicado usa `isinstance()` + `split("[SEG]")` para convertir.

**Riesgo residual:** Si en el futuro se anaden nuevos fallbacks o se
modifican los contratos, no hay un test de integracion que verifique
automaticamente que el output del fallback cumple el contrato. La
verificacion es manual (via `ctx.set_output` con `contract=`).

**Recomendacion:** Agregar test parametrizado que ejecute cada fallback
con input tipico y valide contra su contrato Pydantic via
`Contract.model_validate(fallback(**input))`.

---

## Leccion 2: Graceful degradation

> "Cada etapa debe poder fallar sin matar las siguientes. `ctx.set_output`
> no debe ser un bottleneck critico."

### Estado actual: ⚠️ Parcialmente implementado

**Logrado:**
- Todos los 6 handlers envuelven `ctx.set_output()` en try/except:
  `prompts/preprocess.py:79`, `prompts/intent.py:83`,
  `prompts/plan.py:110`, `prompts/generate.py:88`,
  `prompts/verify.py:95`, `prompts/format.py:93`
- Todos los nodos del orquestador envuelven el handler en try/except:
  `orchestrator.py:_node_preprocess:168`, `_node_intent:188`,
  `_node_plan:213`, `_node_generate:235`, `_node_verify:258`,
  `_node_format:287`

**Problema residual 1 — `_node_verify` error path no escribe en ctx:**
(`orchestrator.py:263-270`)
```python
return {
    "verify_output": {
        "valid": False,
        "should_retry": False,
        "checks": [],
        "suggestions": [],
    }
}
```
Este return dict **no llama `ctx.set_output("verify", ...)`**. Si
`_node_format` llama `ctx.get_fields("verify", ...)`, obtiene `KeyError`
que propaga al except del format node, resultando en el mensaje generico
"Error al generar el resumen final." sin datos de validacion.

**Problema residual 2 — Falla silenciosa de `ctx.set_output` pierde datos:**
Cuando el try/except atrapa un error en `ctx.set_output`, el handler
retorna el output sin validar. El stage "completa" pero `ctx._data` no
tiene la entrada. La siguiente etapa que llame `get_fields()` fallara
con `KeyError`, atrapado por el orquestador.

**Impacto:** En el peor caso, una etapa falla silenciosamente en
`ctx.set_output` y las N etapas siguientes fallan con `KeyError` hasta
llegar a format que produce el mensaje de error generico. La cadena de
errores reales se pierde en logs.

**Recomendacion:**
1. En `_node_verify`, agregar `ctx.set_output("verify", ...)` en el error path
2. Considerar un mecanismo de "best effort" donde `_node_format` intente
   recopilar datos parciales de `ctx` (los que existan) en vez de
   depender de que todas las etapas esten presentes

---

## Leccion 3: Sentinel objects

> "Usar `object()` como centinela requiere check de capacidades
> (`hasattr`) antes de invocar metodos."

### Estado actual: ✅ Completamente implementado

| Archivo | Linea | Pattern |
|---|---|---|
| `llm_backend.py` | 91 | `self._llm = object()` — sentinel assignment |
| `llm_backend.py` | 101 | `if not hasattr(self._llm, "ainvoke"):` — guard `generate()` |
| `llm_backend.py` | 145 | `if not hasattr(self._llm, "ainvoke"):` — guard `generate_structured()` |

**Detalle:** `_ensure_llm()` (line 72) setea `self._llm = object()` si
`ChatOpenAI(**kwargs)` falla. Esto evita reintentar la inicializacion en
cada llamada (pues `self._llm is not None` → `True`). Los metodos
`generate()` y `generate_structured()` checkean `hasattr(self._llm,
"ainvoke")` antes de llamar a `self._llm.ainvoke(messages)`. Si es el
sentinel, retornan `LLMResult(success=False, error="OpenAI backend
unavailable (init failed)")`.

**Sin riesgo:** El patron es completo y correcto. No hay otros backends
(Ollama, vLLM) que usen sentinel — solo OpenAI por la dependencia
problematica con CUDA.

---

## Leccion 4: Success propagation

> "El estado de exito debe propagarse desde el nivel mas interno hasta el
> wrapper CLI sin hardcodeos."

### Estado actual: ⚠️ Parcialmente implementado

**Cadena de propagacion actual:**

```
Handler (retorna dict sin success)
  → Orchestrator node (try/except, retorna output o None)
    → _node_format (retorna final_output con success=True/False)
      → ChainOrchestrator.run() (retorna result.get("final_output", {}))
        → cli.py:run_chain() (lee success del resultado)
```

**Logrado:**
- CLI `cli.py:53` ya no hardcodea `"success": True`:
  ```python
  success = result.get("success", True) if isinstance(result, dict) else True
  ```

**Problema residual 1 — Default optimista `True`:**
Si `result` no tiene key `"success"` (posible si `_node_format` retorna
un formato inesperado), el default es `True`. Esto es optimista y puede
ocultar fallos.

**Problema residual 2 — Sin estado de exito agregado:**
No hay logica que compute `success` dinamicamente basado en el exito de
todas las etapas anteriores. Solo existen dos puntos donde se setea
`success`:
- `_format_fallback`: hardcodea `"success": True` (`fallbacks.py:174`)
- `_node_format` except path: hardcodea `"success": False`
  (`orchestrator.py:302`)

Si el formateador (LLM o fallback) produce `success: False`, se
propaga. Pero si produce `success: True` a pesar de que etapas
anteriores fallaron (posible con el fallback `_format_fallback` que
siempre retorna True), el CLI reporta exito.

**Recomendacion:**
1. En `_node_format`, antes de llamar al handler, inspeccionar
   `state["errors"]`. Si hay errores, forzar `success=False` en el
   output final independientemente de lo que retorne el handler.
2. Cambiar el default en CLI de `True` a `False`:
   `result.get("success", False)`

---

## Resumen de acciones recomendadas

| # | Accion | Archivo | Prioridad |
|---|---|---|---|
| 1 | Agregar test parametrizado que valide cada fallback contra su contrato Pydantic | `tests/` | Media |
| 2 | Agregar `ctx.set_output("verify", ...)` en `_node_verify` error path | `orchestrator.py:263-270` | Alta |
| 3 | En `_node_format`, inspeccionar `state["errors"]` y forzar `success=False` si hay errores | `orchestrator.py` (antes de llamar format_handler) | Alta |
| 4 | Cambiar default de CLI de `success=True` a `success=False` | `cli.py:54` | Baja |
| 5 | Considerar recopilacion parcial de datos en `_node_format` si faltan etapas en ctx | `orchestrator.py:_node_format` | Baja |

### Estado actual de tests

```bash
python -m pytest compiler-bot/agentic_pipeline/tests/ \
  -k "chain or prompt or metric or optimizer or cache or multiagent" -q
# 75 passed
ruff check . && ruff format --check .
# 0 errores
```
