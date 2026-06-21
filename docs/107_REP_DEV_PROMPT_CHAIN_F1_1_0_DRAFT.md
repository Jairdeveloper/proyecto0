---
id: 107
area: dev
type: rep
module: prompt_chain_f1
version: 1.0
status: IMPLEMENTED
tags:
  - report
  - prompt-chaining
  - phase-1
  - infrastructure
  - implementation
summary: "Reporte de la Fase 1 — Infraestructura Base del refactor a Prompt Chaining. Se crearon 5 modulos base (PromptTemplate, LLMBackend, ChainContext, Fallbacks) y 30 tests. Todos los componentes pasan ruff y pytest."
keywords:
  - report
  - phase-1
  - infrastructure
  - prompt-template
  - llm-backend
  - chain-context
  - fallbacks
  - tests
changelog:
  - version: 1.0
    date: 2026-06-16
    author: workflow-agent
    description: Reporte de implementacion de Fase 1 — Infraestructura Base
---

# Reporte: Fase 1 — Infraestructura Base

> **Plan fuente:** `docs/106_PLAN_DEV_PROMPT_CHAIN_EXECUTION_1_0_DRAFT.md`
> **Version del reporte:** 1.0
> **Estado:** DRAFT
> **Fecha de ejecucion:** 2026-06-16

---

## Resumen

Se implemento la infraestructura base del subsistema `prompt_chain/`:

| Componente | Archivo | Proposito |
|-----------|---------|-----------|
| `PromptTemplate` | `prompt_chain/prompt_template.py` | Plantilla de prompt con schema de entrada/salida |
| `PromptRegistry` | `prompt_chain/prompt_template.py` | Registro central de plantillas |
| `ChainStep` | `prompt_chain/prompt_template.py` | Dataclass de una etapa ejecutada |
| `LLMBackend` (ABC) | `prompt_chain/llm_backend.py` | Abstraccion de proveedores LLM |
| `OpenAIBackend` | `prompt_chain/llm_backend.py` | Backend OpenAI via langchain-openai |
| `OllamaBackend` | `prompt_chain/llm_backend.py` | Backend Ollama para modelos locales |
| `VLLMBackend` | `prompt_chain/llm_backend.py` | Backend vLLM (API compatible OpenAI) |
| `FailoverLLMBackend` | `prompt_chain/llm_backend.py` | Failover entre backends en orden de prioridad |
| `build_llm_backend()` | `prompt_chain/llm_backend.py` | Factory segun variables de entorno |
| `ChainContext` | `prompt_chain/chain_context.py` | Bus de datos entre etapas con validacion de contratos |
| `FallbackRegistry` | `prompt_chain/fallbacks.py` | Registro de funciones rule-based por etapa |
| 6 fallbacks | `prompt_chain/fallbacks.py` | `_preprocess_fallback`, `_intent_fallback`, `_plan_fallback`, `_generate_fallback`, `_verify_fallback`, `_format_fallback` |

**Metricas:**

| Metrica | Valor |
|---------|-------|
| Archivos nuevos | 5 |
| Lineas de codigo | ~450 |
| Tests | 30 |
| Tests pasados | 30/30 |
| Errores ruff | 0 |

---

## Estructura del Directorio

```
compiler-bot/agentic_pipeline/
├── prompt_chain/
│   ├── __init__.py
│   ├── prompt_template.py
│   ├── llm_backend.py
│   ├── chain_context.py
│   └── fallbacks.py
```

---

## Detalle por Tarea

### Tarea 1.1 — `prompt_chain/__init__.py` + `prompt_chain/prompt_template.py`

**Archivos creados:**

- `compiler-bot/agentic_pipeline/prompt_chain/__init__.py` — Docstring del subsistema
- `compiler-bot/agentic_pipeline/prompt_chain/prompt_template.py`

**Clases implementadas:**

| Clase | Tipo | Funciones clave |
|-------|------|-----------------|
| `PromptTemplate` | `@dataclass` | `render(**kwargs)` — rellena template y valida contra `input_schema` |
| `PromptRegistry` | class with `@classmethod`s | `register()`, `get()`, `list()`, `validate_output()`, `clear()` |
| `ChainStep` | `@dataclass` | Almacena stage, output, timestamp, duration, success, error |
| `register_prompt()` | function | Helper que registra y retorna el template |

**Detalles de implementacion:**

- `PromptTemplate.render()` usa Pydantic `model_validate` para validar inputs antes del formateo
- `PromptRegistry` usa diccionario de clase (singleton) compartido entre modulos
- `register_prompt()` permite uso como decorator o llamada directa
- `ChainStep` genera timestamp automaticamente con `datetime.now(timezone.utc)`

### Tarea 1.2 — `prompt_chain/llm_backend.py`

**Clases implementadas:**

| Clase | Proposito | Configuracion via env var |
|-------|-----------|--------------------------|
| `LLMBackend` (ABC) | Metodos `generate()` y `generate_structured()` abstractos | — |
| `OpenAIBackend` | ChatOpenAI de langchain | `AGENTIC_OPENAI_API_KEY`, `AGENTIC_OPENAI_MODEL`, `AGENTIC_OPENAI_BASE_URL` |
| `OllamaBackend` | HTTP a Ollama API | `AGENTIC_OLLAMA_URL` (defecto localhost:11434), `AGENTIC_OLLAMA_MODEL` |
| `VLLMBackend` | HTTP a vLLM API (compatible OpenAI) | `AGENTIC_VLLM_URL`, `AGENTIC_VLLM_MODEL` |
| `FailoverLLMBackend` | Prueba backends en orden, retorna el primero exitoso | — |
| `LLMResult` (Pydantic) | `content`, `structured`, `provider`, `model`, `duration`, `success`, `error` | — |

**Funciones:**

| Funcion | Proposito |
|---------|-----------|
| `build_llm_backend()` | Factory que construye `FailoverLLMBackend` segun `AGENTIC_LLM_PROVIDER` |

**Detalles de implementacion:**

- `OpenAIBackend._ensure_llm()` usa carga lazy con manejo de errores para importar `langchain_openai`
- `generate_structured()` envia el JSON Schema del Pydantic model como instruccion al system prompt
- Todos los backends capturan excepcion y retornan `LLMResult(success=False, error=...)` sin crashear
- `FailoverLLMBackend` requiere al menos un backend (lanza `ValueError` si lista vacia)
- `build_llm_backend()` orden: `AGENTIC_LLM_PROVIDER` explicito → OpenAI → Ollama

### Tarea 1.3 — `prompt_chain/chain_context.py`

**Clase implementada:**

`ChainContext` — bus de datos entre etapas del prompt chain.

| Metodo | Entrada | Salida | Validacion |
|--------|---------|--------|------------|
| `set_output(stage, data, contract=None)` | stage name, dict, opcional Pydantic model | None | Si contract existe, valida data contra el |
| `get_fields(stage, fields)` | stage name, lista de campos | dict parcial | KeyError si stage o campo no existe |
| `render_template(template, stage, fields)` | string template, stage, fields | string formateado | KeyError si campos faltan |
| `get_history(limit=None)` | opcional int | list[ChainStep] | — |
| `get_all_outputs()` | — | dict[str, dict] | snapshot shallow copy |

**Flujo de datos tipico:**

```python
ctx = ChainContext()
ctx.set_output("preprocess", {"normalized": "texto", "domain": "backend"},
               contract=PreprocessorContract)
# ...
fields = ctx.get_fields("preprocess", ["normalized"])
prompt = ctx.render_template("Texto: {normalized}", "preprocess", ["normalized"])
# → "Texto: texto"
```

### Tarea 1.4 — `prompt_chain/fallbacks.py`

**Funciones del registro:**

| Funcion | Proposito |
|---------|-----------|
| `register_fallback(name, fn)` | Registra funcion rule-based |
| `get_fallback(name)` | Obtiene funcion por nombre (None si no existe) |
| `execute_fallback(name, **kwargs)` | Ejecuta funcion registrada (KeyError si no existe) |

**Fallbacks pre-registrados (6):**

| Nombre | Funcion | Componentes legacy que wrappea |
|--------|---------|-------------------------------|
| `preprocessor_filters` | `_preprocess_fallback` | `NormalizationFilter` + `SegmentationFilter` |
| `intent_classifier` | `_intent_fallback` | `IntentClassifier` + `NERExtractor` + `SlotFiller` |
| `goal_tree_planner` | `_plan_fallback` | `GoalTreePlanner` |
| `generator_factory` | `_generate_fallback` | `GeneratorFactory` |
| `validator_pipeline` | `_verify_fallback` | stub (retorna valid=True siempre) |
| `explain_tool` | `_format_fallback` | stub (retorna resumen basico) |

Los fallbacks se auto-registran al importar el modulo via `_init_fallbacks()` + llamada al final del archivo.

### Tarea 1.5 — Tests (30 tests)

| Test file | Clase | Tests | Temas |
|-----------|-------|-------|-------|
| `test_prompt_template.py` | `TestPromptTemplate` | 3 | render variables, validacion input, campos extra |
| `test_prompt_template.py` | `TestPromptRegistry` | 7 | register/get, KeyError, duplicados, list, validate, helper |
| `test_prompt_template.py` | `TestChainStep` | 1 | construccion basica |
| `test_llm_backend.py` | `TestFailoverLLMBackend` | 5 | failover all fail, first succeeds, structured fail, empty, structured success |
| `test_llm_backend.py` | `TestOpenAIBackend` | 2 | generate/structured con API key invalida (falla graceful) |
| `test_llm_backend.py` | `TestBuildLLMBackend` | 1 | factory retorna FailoverLLMBackend |
| `test_chain_context.py` | `TestChainContext` | 10 | set/get_fields, missing key errors, contract validation, render_template, history, all outputs |

Todos los tests usan mocks para LLM (no requieren API key real).

---

## Decisiones Tecnicas

### 1. Failover silencioso vs ruidoso

**Decision:** Silencioso — `FailoverLLMBackend` prueba backends en orden sin loguear errores intermedios. Solo se registra el error final si todos fallan.

**Motivo:** Si OpenAI falla y Ollama funciona, no hay razon para alertar al usuario. El error se propaga via `LLMResult.success=False` para que el llamante decida.

### 2. Carga lazy de `langchain-openai`

**Decision:** `OpenAIBackend._ensure_llm()` importa `langchain_openai` solo en la primera llamada, no en `__init__`.

**Motivo:** La importacion de `langchain_openai` desencadena una cascada que termina importando `torch` (con bug CUDA en este entorno). La carga lazy permite que el resto del modulo funcione aunque OpenAI no este disponible.

### 3. `ChainContext.get_fields()` retorna dict parcial vs completo

**Decision:** `get_fields(stage, fields)` retorna SOLO los campos solicitados (dict parcial), no el output completo.

**Motivo:** Cada etapa solo debe consumir los datos que necesita. Esto hace explicitas las dependencias entre etapas y previene acoplamientos ocultos.

### 4. Fallbacks como funciones independientes vs metodos de clase

**Decision:** Funciones sueltas con prefijo `_`, registradas por nombre en el `FallbackRegistry`.

**Motivo:** Permite registrar fallbacks desde cualquier modulo sin acoplamiento de herencia. El nombre del fallback se declara en el `PromptTemplate.fallback_name` como string.

---

## Problemas Encontrados y Soluciones

| Problema | Causa | Solucion |
|----------|-------|----------|
| `flake8/ruff` importaciones sin usar | `ValidationError` importado pero no referenciado directamente | Eliminar import. Pydantic lanza `ValidationError` implicitamente via `model_validate()` |
| Tests async fallaban | Faltaba `@pytest.mark.asyncio` en metodos async | Anadir decorador a cada metodo |
| Tests mock fallaban por firma | `FailoverLLMBackend` pasa args posicionales pero mocks usaban `**kwargs` | Cambiar mocks a firma explicita `(self, prompt, system="", temperature=0.3, max_tokens=4096)` |
| `langchain_openai` crashea por torch/CUDA | Bug en libcudart.so.13 en el entorno | Broad except en `_ensure_llm()` + sentinel `object()` para evitar reintento |

---

## Integridad del Plan vs Ejecucion

| Item del plan | Estado | Notas |
|---------------|--------|-------|
| `prompt_chain/__init__.py` | ✅ | Creado |
| `prompt_chain/prompt_template.py` | ✅ | `PromptTemplate`, `PromptRegistry`, `ChainStep`, `register_prompt()` |
| `prompt_chain/llm_backend.py` | ✅ | `LLMBackend` ABC + 4 backends + `FailoverLLMBackend` + `build_llm_backend()` |
| `prompt_chain/chain_context.py` | ✅ | `ChainContext` completo |
| `prompt_chain/fallbacks.py` | ✅ | `FallbackRegistry` + 6 fallbacks pre-registrados |
| Tests (F1.5) | ✅ | 30 tests, 3 test files |
| ruff 0 errores | ✅ | `ruff check` pasa |
| pytest pasa | ✅ | 30/30 |

---

## Proximos Pasos

Continuar con **Fase 2 — Prompts Core**:

- `prompt_chain/contracts.py` — 6 modelos Pydantic de contrato
- `prompt_chain/prompts/__init__.py` + 6 prompts (PREPROCESS, INTENT, PLAN, GENERATE, VERIFY, FORMAT)
- Cada prompt con handler async que orquesta LLM + fallback
- 33 tests nuevos (6 test files)
