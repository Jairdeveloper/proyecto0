---
id: 108
area: dev
type: rep
module: prompt_chain_f2
version: 1.0
status: IMPLEMENTED
tags:
  - report
  - prompt-chaining
  - fase-2
  - prompts-core
  - implementation
summary: "Reporte de implementacion de la Fase 2 (Prompts Core) del refactor a Prompt Chaining. 8 archivos fuente, 6 test files, 33 tests, 1802 lineas totales."
keywords:
  - report
  - fase-2
  - prompts
  - prompt-template
  - handlers
  - tests
changelog:
  - version: 1.0
    date: 2026-06-16
    author: workflow-agent
    description: Reporte de Fase 2 completada
---

# Reporte de Fase 2 — Prompts Core

> **Documento fuente:** `106_PLAN_DEV_PROMPT_CHAIN_EXECUTION_1_0_DRAFT.md`
> **Documento de referencia:** `105_PROP_DEV_PROMPT_CHAIN_REFACTOR_1_0_DRAFT.md`
> **Version del reporte:** 1.0
> **Fecha:** 2026-06-16

---

## Resumen

Fase 2 del refactor a Prompt Chaining completada. Se implementaron los
6 prompts individuales del pipeline (PREPROCESS, INTENT, PLAN, GENERATE,
VERIFY, FORMAT) mas los contratos Pydantic y 33 tests.

### Metricas

| Metrica | Valor |
|---------|-------|
| Archivos nuevos (fuente) | 8 |
| Archivos nuevos (tests) | 6 |
| Total lineas de codigo | 1,802 |
| Tests | 33 |
| Tests pasados | 33/33 |
| Errores ruff | 0 |

### Archivos creados

| Archivo | Lineas | Proposito |
|---------|--------|-----------|
| `prompt_chain/contracts.py` | 105 | 12 Pydantic models (6 input + 6 output) |
| `prompt_chain/prompts/__init__.py` | 26 | Import y registro de todos los prompts |
| `prompt_chain/prompts/preprocess.py` | 78 | Prompt PREPROCESS + handler async |
| `prompt_chain/prompts/intent.py` | 82 | Prompt INTENT + handler async |
| `prompt_chain/prompts/plan.py` | 109 | Prompt PLAN + handler async |
| `prompt_chain/prompts/generate.py` | 87 | Prompt GENERATE + handler async |
| `prompt_chain/prompts/verify.py` | 96 | Prompt VERIFY + handler async |
| `prompt_chain/prompts/format.py` | 92 | Prompt FORMAT + handler async |
| `tests/test_prompt_preprocess.py` | 172 | 5 tests para PREPROCESS |
| `tests/test_prompt_intent.py` | 246 | 7 tests para INTENT |
| `tests/test_prompt_plan.py` | 204 | 6 tests para PLAN |
| `tests/test_prompt_generate.py` | 195 | 6 tests para GENERATE |
| `tests/test_prompt_verify.py` | 162 | 5 tests para VERIFY |
| `tests/test_prompt_format.py` | 148 | 4 tests para FORMAT |

---

## Tarea 2.1 — `prompt_chain/contracts.py`

### Contratos de salida (Output contracts)

Cada prompt produce JSON validado contra su Pydantic model:

| Clase | Campos | Prompt destino |
|-------|--------|----------------|
| `PreprocessorContract` | normalized, domain, language, segments, has_ambiguity, confidence | PREPROCESS |
| `NLPContract` | intent, confidence, module, entity, tech, features, is_ambiguous, missing_info | INTENT |
| `PlannerContract` | tasks, execution_order, complexity, estimated_files | PLAN |
| `SynthesisContract` | files, errors | GENERATE |
| `ValidatorContract` | valid, checks, should_retry, suggestions | VERIFY |
| `OutputContract` | summary, files_created, warnings, next_steps, success | FORMAT |

### Contratos de entrada (Input contracts)

Cada prompt template valida sus kwargs contra su input schema:

| Clase | Campos |
|-------|--------|
| `PreprocessorInput` | raw_text: str |
| `NLPInput` | normalized_text: str, domain: str = "backend" |
| `PlannerInput` | intent: str, module, entity, tech, features (opcionales) |
| `SynthesisInput` | tasks: list[dict], existing_files: list[str] |
| `ValidatorInput` | requirements: dict, files: list[dict], criteria: list[str] |
| `OutputInput` | original_request: str, plan: dict, generated_files: list[dict], validation: dict |

---

## Tarea 2.2 — `prompt_chain/prompts/__init__.py`

Importa los 6 submodulos con alias privados (`_preprocess`, `_intent`, etc.)
para que `register_prompt()` en cada modulo se ejecute al importar el
paquete `prompts`. Usa `# noqa: F401` para suprimir advertencia de import
no utilizado (efecto colateral intencional).

Expone `__all__` con los 6 nombres de modulo.

---

## Tarea 2.3 — Prompt PREPROCESS

**Archivo:** `prompt_chain/prompts/preprocess.py`

Template registrado con `register_prompt()`:
- **System prompt:** Normalizacion de instrucciones de desarrollo
- **Template:** `Normaliza el siguiente texto:\n\n{raw_text}`
- **Input schema:** `PreprocessorInput` (raw_text: str)
- **Output contract:** `PreprocessorContract`
- **Fallback:** `preprocessor_filters` (NormalizationFilter + SegmentationFilter)
- **Temperature:** 0.1

Handler `preprocess_handler(raw_text, llm=None, ctx=None)`:
1. Renderiza template con `raw_text`
2. Llama a `llm.generate_structured()` con schema de salida
3. Si LLM falla → `execute_fallback("preprocessor_filters", raw_text=raw_text)`
4. Publica en `ChainContext` si `ctx` no es None

**Tests (5):** LLM success, fallback, empty input, domain extraction, sentence segmentation

---

## Tarea 2.4 — Prompt INTENT

**Archivo:** `prompt_chain/prompts/intent.py`

Template:
- **System prompt:** Analisis de requisitos, 5 acciones (CREATE/READ/UPDATE/DELETE/EXPLAIN)
- **Template:** `Texto normalizado: {normalized_text}\nDominio: {domain}`
- **Input schema:** `NLPInput` (normalized_text, domain)
- **Output contract:** `NLPContract`
- **Fallback:** `intent_classifier` (IntentClassifier + NERExtractor + SlotFiller)
- **Temperature:** 0.2

Handler `intent_handler(normalized_text, domain="backend", llm=None, ctx=None)`:
Mismo patron que PREPROCESS.

**Tests (7):** CREATE module, DELETE, READ, ambiguous (no module), tech extraction, LLM fallback, low confidence

---

## Tarea 2.5 — Prompt PLAN

**Archivo:** `prompt_chain/prompts/plan.py`

Template:
- **System prompt:** Arquitecto de software, 5 tipos de tarea (scaffold_module, create_entity, generate_code, configure, verify)
- **Template:** `Intencion: {intent}\nModulo: {module}\nEntidad: {entity}\nTecnologias: {tech}\nFeatures: {features}`
- **Input schema:** `PlannerInput` (intent, module, entity, tech, features)
- **Output contract:** `PlannerContract`
- **Fallback:** `goal_tree_planner` (GoalTreePlanner)
- **Temperature:** 0.3

**Tests (6):** CREATE module, CREATE entity, CREATE CRUD, READ (no tasks), dependencies ordered, LLM fallback

---

## Tarea 2.6 — Prompt GENERATE

**Archivo:** `prompt_chain/prompts/generate.py`

Template:
- **System prompt:** Generador de codigo NestJS + Prisma
- **Template:** `Tareas: {tasks}\nArchivos existentes: {existing_files}`
- **Input schema:** `SynthesisInput` (tasks, existing_files)
- **Output contract:** `SynthesisContract`
- **Fallback:** `generator_factory` (GeneratorFactory + templates)
- **Temperature:** 0.4

**Tests (6):** Module scaffold files, entity schema, parallel tasks, overwrite flag, errors reported, LLM fallback

---

## Tarea 2.7 — Prompt VERIFY

**Archivo:** `prompt_chain/prompts/verify.py`

Template:
- **System prompt:** Revisor de codigo NestJS/Prisma, 5 criterios
- **Template:** `Requisitos: {requirements}\n\nArchivos: {files}\n\nCriterios: {criteria}`
- **Input schema:** `ValidatorInput` (requirements, files, criteria)
- **Output contract:** `ValidatorContract`
- **Fallback:** `validator_pipeline` (ValidatorPipeline)
- **Temperature:** 0.1

**Tests (5):** Valid files, missing imports, should_retry true, suggestions, LLM fallback

---

## Tarea 2.8 — Prompt FORMAT

**Archivo:** `prompt_chain/prompts/format.py`

Template:
- **System prompt:** Asistente de desarrollo, resumen claro
- **Template:** `Solicitud original: {original_request}\n\nPlan: {plan}\n\nArchivos generados: {generated_files}\n\nValidacion: {validation}`
- **Input schema:** `OutputInput` (original_request, plan, generated_files, validation)
- **Output contract:** `OutputContract`
- **Fallback:** `explain_tool` (ExplainTool)
- **Temperature:** 0.5

**Tests (4):** Summary mentions files, success=true, warnings propagated, LLM fallback

---

## Issues encontrados y soluciones

### Problema: `PromptRegistry` singleton y tests

**Sintoma:** Al ejecutar tests de Fase 2, el primer test de cada clase
fallaba con `KeyError: "PromptTemplate 'X' already registered"`.

**Causa raiz:**
- `PromptRegistry._templates` es un dict a nivel de clase (singleton)
- Cada prompt module llama a `register_prompt()` en el momento de import
- Python cachea modulos en `sys.modules`, asi que las importaciones
  subsequentes no re-ejecutan el codigo de registro
- Los tests limpian el registry con `PromptRegistry.clear()`, pero el
  modulo ya esta cacheado y no puede re-registrar sin `importlib.reload`

**Solucion:** En `setup_method()` de cada test class:
1. Importar `prompts` (ejecuta `__init__.py` que registra los 6 templates)
2. Limpiar registry con `PromptRegistry.clear()`
3. Recargar el modulo especifico con `importlib.reload()` para re-registrar
   solo el template necesario

```python
def setup_method(self):
    import agentic_pipeline.prompt_chain.prompts as _pkg
    _ = _pkg
    PromptRegistry.clear()
    _mod = importlib.import_module(
        "agentic_pipeline.prompt_chain.prompts.preprocess",
    )
    importlib.reload(_mod)
```

### Problema: Input schemas como Pydantic models

**Sintoma:** `PromptTemplate.render()` validaba kwargs contra
`input_schema(**kwargs)` y luego usaba `model_dump()` para format.

**Decision:** Se definieron 6 input contracts adicionales en `contracts.py`
junto con los output contracts, en lugar de definirlos privados en cada
prompt file, para mantener consistencia y reusabilidad en tests.

---

## Estado del subsistema `prompt_chain/`

```
prompt_chain/
├── __init__.py              # (F1) Init del subsistema
├── prompt_template.py       # (F1) PromptTemplate + PromptRegistry
├── llm_backend.py           # (F1) LLMBackend ABC + 4 providers
├── chain_context.py         # (F1) ChainContext (bus de datos)
├── fallbacks.py             # (F1) FallbackRegistry + 6 fallbacks
├── contracts.py             # (F2) 12 Pydantic models (NUEVO)
└── prompts/
    ├── __init__.py          # (F2) Import y registro (NUEVO)
    ├── preprocess.py        # (F2) Prompt 1 + handler (NUEVO)
    ├── intent.py            # (F2) Prompt 2 + handler (NUEVO)
    ├── plan.py              # (F2) Prompt 3 + handler (NUEVO)
    ├── generate.py          # (F2) Prompt 4 + handler (NUEVO)
    ├── verify.py            # (F2) Prompt 5 + handler (NUEVO)
    └── format.py            # (F2) Prompt 6 + handler (NUEVO)
```

Total Fase 1 + Fase 2: **13 archivos fuente, ~1,200 lineas, 63 tests**

---

## Tests: resumen detallado

| Test file | Tests | Descripcion |
|-----------|-------|-------------|
| `test_prompt_preprocess.py` | 5 | LLM success, fallback, empty input, domain, segments |
| `test_prompt_intent.py` | 7 | CREATE/DELETE/READ, ambiguous, tech, fallback, low conf |
| `test_prompt_plan.py` | 6 | Module/entity/crud tasks, READ empty, dependencies, fallback |
| `test_prompt_generate.py` | 6 | Module files, entity schema, parallel, overwrite, errors, fallback |
| `test_prompt_verify.py` | 5 | Valid, missing imports, retry, suggestions, fallback |
| `test_prompt_format.py` | 4 | Summary, success, warnings, fallback |
| **Total** | **33** | |

Todos los tests usan `AsyncMock` para mockear `LLMBackend.generate_structured()`,
y `patch()` para mockear `execute_fallback()` en los tests de fallback.
No requieren API key real ni conexion a internet.

---

## Proximos pasos (Fase 3)

- `prompt_chain/orchestrator.py` — ChainOrchestrator con LangGraph StateGraph
- `prompt_chain/cli.py` — CLI handler para flag `--chain`
- Modificar `compiler-bot/agentic` para aceptar `--chain`
- Tests de integracion (8 tests)
