---
id: 106
area: dev
type: plan
module: prompt_chain_exec
version: 1.0
status: IMPLEMENTED
tags:
  - plan
  - execution
  - prompt-chaining
  - refactor
  - pipeline
  - implementation
summary: "Plan de ejecucion detallado para el refactor del pipeline RECPL al patron Prompt Chaining. Describe fase por fase los archivos a crear/modificar, clases, funciones, tests y criterios de aceptacion."
keywords:
  - plan
  - execution
  - prompt-chain
  - implementation
  - tasks
  - milestones
changelog:
  - version: 1.0
    date: 2026-06-16
    author: workflow-agent
    description: Creacion del plan de ejecucion detallado para Prompt Chaining
---

# Plan de Ejecucion: Prompt Chaining Refactor

> **Documento fuente:** `105_PROP_DEV_PROMPT_CHAIN_REFACTOR_1_0_DRAFT.md`
> **Version del plan:** 1.0
> **Estado:** DRAFT
> **Total de fases:** 5
> **Total de tareas:** 26
> **Total de archivos nuevos:** ~22
> **Total de tests nuevos:** ~40

---

## Tabla de Contenidos

1. [Dependencias entre Fases](#1-dependencias)
2. [Fase 1 — Infraestructura Base](#2-fase-1--infraestructura-base)
3. [Fase 2 — Prompts Core](#3-fase-2--prompts-core)
4. [Fase 3 — Chain Orchestrator](#4-fase-3--chain-orchestrator)
5. [Fase 4 — Sistema Multi-Agente Prompt-Driven](#5-fase-4--sistema-multi-agente-prompt-driven)
6. [Fase 5 — Feedback Loop + Optimizacion](#6-fase-5--feedback-loop--optimizacion)
7. [Glosario de Archivos](#7-glosario-de-archivos)

---

## 1. Dependencias entre Fases

```
Fase 1 ─────────────────────────────────────────────
  Infraestructura Base (PromptTemplate, LLMBackend,
  ChainContext, Fallbacks, Tests)
    │
    ▼
Fase 2 ─────────────────────────────────────────────
  Prompts Core (6 prompts individuales con tests)
    │
    ▼
Fase 3 ─────────────────────────────────────────────
  Chain Orchestrator (grafo, CLI, flag --chain)
    │
    ├──────────────────────────────────────┐
    ▼                                      ▼
Fase 4                               Fase 5
  Sistema Multi-Agente                 Feedback Loop +
  Prompt-Driven                        Optimizacion
```

**Secuenciales:** F1 → F2 → F3
**Paralelizables:** F4 y F5 pueden iniciar despues de F3

---

## 2. Fase 1 — Infraestructura Base

### Objetivo

Crear el subsistema `prompt_chain/` con los componentes base:
`PromptTemplate`, `LLMBackend`, `ChainContext`, y `FallbackRegistry`.

### Arbol de directorios resultante

```
compiler-bot/agentic_pipeline/
├── prompt_chain/
│   ├── __init__.py
│   ├── prompt_template.py
│   ├── llm_backend.py
│   ├── chain_context.py
│   ├── fallbacks.py
│   └── contracts.py
```

---

### Tarea 1.1 — `prompt_chain/__init__.py` + `prompt_chain/prompt_template.py`

#### Archivo: `prompt_chain/__init__.py`

```python
"""Prompt Chaining subsystem for RECPL v2.0+."""
```

#### Archivo: `prompt_chain/prompt_template.py`

**Clases a implementar:**

```python
@dataclass
class PromptTemplate:
    """Una plantilla de prompt con schema de entrada/salida."""

    name: str                           # nombre unico (ej: "preprocess")
    system_prompt: str                  # system prompt del LLM
    template: str                       # template con {variables}
    input_schema: type[BaseModel]       # Pydantic model para validar entrada
    output_schema: type[BaseModel]      # Pydantic model para validar salida
    fallback_name: str | None = None    # nombre en FallbackRegistry
    temperature: float = 0.3
    model: str = "gpt-4o-mini"
    provider: str = "openai"
    version: str = "1.0"

    def render(self, **kwargs) -> str:
        """Rellena el template con kwargs y valida contra input_schema."""
        ...


class PromptRegistry:
    """Registro central de plantillas de prompt."""

    _templates: dict[str, PromptTemplate] = {}

    @classmethod
    def register(cls, template: PromptTemplate) -> None:
        """Registra un template. Lanza si ya existe con mismo nombre."""
        ...

    @classmethod
    def get(cls, name: str) -> PromptTemplate:
        """Obtiene un template por nombre. Lanza KeyError si no existe."""
        ...

    @classmethod
    def list(cls) -> list[dict]:
        """Lista todos los templates registrados (nombre, version, schema)."""
        ...

    @classmethod
    def validate_output(cls, name: str, data: dict) -> BaseModel:
        """Valida un dict contra el output_schema del template."""
        ...


@dataclass
class ChainStep:
    """Una etapa ejecutada en la cadena, con su output y metadatos."""
    stage: str
    output: dict
    timestamp: str
    duration: float
    success: bool
    error: str | None = None
```

**Funcion helper:**

```python
def register_prompt(template: PromptTemplate) -> PromptTemplate:
    """Decorator/helper para registrar y retornar un template."""
    PromptRegistry.register(template)
    return template
```

**Criterios de aceptacion:**
- [ ] `PromptTemplate.render()` reemplaza variables correctamente
- [ ] `PromptTemplate.render()` valida contra `input_schema` (Pydantic)
- [ ] `PromptRegistry.register()` almacena y `get()` recupera
- [ ] `PromptRegistry.get()` lanza `KeyError` si no existe
- [ ] `PromptRegistry.list()` retorna lista con todos los templates
- [ ] `PromptRegistry.validate_output()` valida contra `output_schema`
- [ ] `ChainStep` se construye con todos los campos

---

### Tarea 1.2 — `prompt_chain/llm_backend.py`

**Clases a implementar:**

```python
class LLMResult(BaseModel):
    """Resultado de una llamada al LLM."""
    content: str
    structured: BaseModel | None = None
    provider: str
    model: str
    duration: float
    success: bool
    error: str | None = None


class LLMBackend(ABC):
    """Abstraccion sobre proveedores de LLM."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResult:
        """Genera texto libre."""
        ...

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        system: str = "",
        output_schema: type[BaseModel] = None,
        temperature: float = 0.3,
    ) -> LLMResult:
        """Genera output estructurado validado contra schema."""
        ...


class OpenAIBackend(LLMBackend):
    """OpenAI / Azure OpenAI backend via langchain-openai ChatOpenAI.

    Config:
        AGENTIC_OPENAI_API_KEY (str)
        AGENTIC_OPENAI_MODEL (str)  — defecto: "gpt-4o-mini"
        AGENTIC_OPENAI_BASE_URL (str)  — opcional (para Azure/compatibles)
    """
    ...


class OllamaBackend(LLMBackend):
    """Ollama backend para modelos locales.

    Config:
        AGENTIC_OLLAMA_URL (str)   — defecto: "http://localhost:11434"
        AGENTIC_OLLAMA_MODEL (str) — defecto: "llama3"
    """
    ...


class VLLMBackend(LLMBackend):
    """vLLM backend (API compatible OpenAI).

    Config:
        AGENTIC_VLLM_URL (str)
        AGENTIC_VLLM_MODEL (str)
    """
    ...


class HTTPBackend(LLMBackend):
    """Generic HTTP backend compatible con API OpenAI.

    Config:
        AGENTIC_LLM_URL (str)
        AGENTIC_LLM_API_KEY (str)
        AGENTIC_LLM_MODEL (str)
    """
    ...


class FailoverLLMBackend(LLMBackend):
    """Wrapper que intenta multiples backends en orden y cae a fallback.

    Strategy:
        1. Probar backends configurados en orden de prioridad
        2. Si todos fallan, retornar LLMResult con success=False
        3. El llamante decide si usar fallback rule-based
    """

    def __init__(self, backends: list[LLMBackend]):
        self._backends = backends

    async def generate(self, ...) -> LLMResult:
        for backend in self._backends:
            try:
                return await backend.generate(...)
            except Exception:
                continue
        return LLMResult(success=False, error="all backends failed")
    ...


def build_llm_backend() -> LLMBackend:
    """Factory: construye FailoverLLMBackend segun variables de entorno.

    Orden de prioridad por env vars:
        AGENTIC_LLM_PROVIDER=openai|ollama|vllm|http
        Si no se define, intenta OpenAI primero, luego Ollama.
    """
    ...


class LLMConfig:
    """Configuracion por prompt.

    Se carga desde `prompt_chain/config.yaml` o defaults.
    """
    provider: str
    model: str
    temperature: float
    max_tokens: int
```

**Criterios de aceptacion:**
- [ ] `OpenAIBackend.generate()` retorna `LLMResult` con contenido
- [ ] `OpenAIBackend.generate_structured()` retorna JSON validado contra schema
- [ ] `FailoverLLMBackend` prueba backends en orden
- [ ] `FailoverLLMBackend` retorna `success=False` cuando todos fallan
- [ ] `build_llm_backend()` respeta variables de entorno
- [ ] Tests con LLM mockeado (no requieren API key real)

---

### Tarea 1.3 — `prompt_chain/chain_context.py`

**Clases a implementar:**

```python
class ChainContext:
    """Bus de datos entre etapas del prompt chain con validacion de contratos.

    Cada etapa publica su salida via set_output(), y las etapas siguientes
    solo toman los campos que necesitan via get_fields().
    """

    def __init__(self):
        self._data: dict[str, dict] = {}
        self._history: list[ChainStep] = []

    def set_output(self, stage: str, data: dict,
                   contract: type[BaseModel] | None = None) -> None:
        """Publica salida de una etapa. Valida contra contrato si existe.

        Args:
            stage: Nombre de la etapa (ej: "preprocess")
            data:  Datos de salida (debe coincidir con contract si se provee)
            contract: Pydantic model opcional para validar

        Raises:
            ValidationError: si data no cumple contract
        """
        if contract:
            contract.model_validate(data)
        self._data[stage] = data
        self._history.append(ChainStep(
            stage=stage, output=data, timestamp=datetime.now().isoformat(),
            duration=0.0, success=True,
        ))

    def get_fields(self, stage: str, fields: list[str]) -> dict:
        """Obtiene campos especificos de una etapa anterior.

        Args:
            stage:  Nombre de la etapa origen
            fields: Lista de campos a extraer

        Returns:
            Dict con solo los campos solicitados

        Raises:
            KeyError: si la etapa o algun campo no existe
        """
        if stage not in self._data:
            raise KeyError(f"Stage '{stage}' not found in context")
        output = self._data[stage]
        missing = [f for f in fields if f not in output]
        if missing:
            raise KeyError(f"Fields {missing} not found in stage '{stage}'")
        return {f: output[f] for f in fields}

    def render_template(self, template: str, stage: str,
                        fields: list[str]) -> str:
        """Rellena un template con campos de una etapa anterior.

        Ejemplo:
            ctx.render_template("Texto: {normalized}", "preprocess",
                                ["normalized"])
            → "Texto: crea un modulo de pagos en nestjs"
        """
        context = self.get_fields(stage, fields)
        return template.format(**context)

    def get_history(self, limit: int | None = None) -> list[ChainStep]:
        """Retorna historial de etapas ejecutadas."""
        if limit:
            return self._history[-limit:]
        return self._history.copy()

    def get_all_outputs(self) -> dict[str, dict]:
        """Retorna todas las salidas publicadas (solo lectura)."""
        return dict(self._data)
```

**Criterios de aceptacion:**
- [ ] `set_output()` almacena datos y los valida contra contract
- [ ] `set_output()` lanza `ValidationError` si no cumple contract
- [ ] `get_fields()` retorna solo los campos solicitados
- [ ] `get_fields()` lanza `KeyError` si etapa o campo no existen
- [ ] `render_template()` reemplaza `{variables}` correctamente
- [ ] `get_history()` retorna historial en orden de insercion
- [ ] `get_all_outputs()` retorna snapshot de todos los datos

---

### Tarea 1.4 — `prompt_chain/fallbacks.py`

**Funciones a implementar:**

```python
_FALLBACKS: dict[str, Callable] = {}


def register_fallback(name: str, fn: Callable) -> None:
    """Registra una funcion de fallback rule-based."""
    _FALLBACKS[name] = fn


def get_fallback(name: str) -> Callable | None:
    """Obtiene funcion de fallback por nombre. None si no existe."""
    return _FALLBACKS.get(name)


def execute_fallback(name: str, **kwargs) -> dict:
    """Ejecuta un fallback por nombre con kwargs.

    Raises:
        KeyError: si el fallback no esta registrado
    """
    fn = get_fallback(name)
    if fn is None:
        raise KeyError(f"Fallback '{name}' not registered")
    return fn(**kwargs)


# ============================================================
# Fallbacks pre-registrados (wrappers sobre componentes legacy)
# ============================================================

def _preprocess_fallback(raw_text: str) -> dict:
    """Wrapper sobre NormalizationFilter + SegmentationFilter.

    Retorna mismo schema que PreprocessorContract.
    """
    from agentic_pipeline.nodes.preprocessor import (
        NormalizationFilter, SegmentationFilter,
    )
    nf = NormalizationFilter()
    sf = SegmentationFilter()
    normalized = nf.process(raw_text)
    segments = sf.process(normalized)
    return {
        "normalized": normalized,
        "domain": "backend",
        "language": "es",
        "segments": segments,
        "has_ambiguity": False,
        "confidence": 0.5,
    }


def _intent_fallback(normalized_text: str, domain: str = "backend") -> dict:
    """Wrapper sobre IntentClassifier + NERExtractor + SlotFiller.

    Retorna mismo schema que NLPContract.
    """
    from agentic_pipeline.nlp.intent_classifier import IntentClassifier
    from agentic_pipeline.nlp.ner_extractor import NERExtractor
    from agentic_pipeline.nlp.slot_filler import SlotFiller
    clf = IntentClassifier()
    ner = NERExtractor()
    filler = SlotFiller()
    intent = clf.classify(normalized_text)
    entities = ner.extract(normalized_text)
    slots = filler.fill(intent, entities)
    return {
        "intent": intent.primary,
        "confidence": intent.confidence,
        "module": entities.modulos[0].nombre if entities.modulos else None,
        "entity": None,
        "tech": [e.nombre for e in entities.techs],
        "features": [],
        "is_ambiguous": False,
        "missing_info": [],
    }


def _plan_fallback(intent: str, module: str | None = None,
                   tech: list[str] | None = None,
                   features: list[str] | None = None) -> dict:
    """Wrapper sobre GoalTreePlanner.

    Retorna mismo schema que PlannerContract.
    """
    from agentic_pipeline.nodes.reasoning_engine import GoalTreePlanner
    planner = GoalTreePlanner()
    # ... adaptar a la interfaz existente
    return {"tasks": [], "execution_order": [], "complexity": "low",
            "estimated_files": 0}


def _generate_fallback(tasks: list[dict],
                       existing_files: list[str] | None = None) -> dict:
    """Wrapper sobre GeneratorFactory + templates.

    Retorna mismo schema que SynthesisContract.
    """
    from agentic_pipeline.generators.generator_factory import GeneratorFactory
    # ... adaptar
    return {"files": [], "errors": []}


def _verify_fallback(requirements: dict,
                     files: list[dict],
                     criteria: list[str] | None = None) -> dict:
    """Wrapper sobre ValidatorPipeline."""
    from agentic_pipeline.nodes.validator import ValidatorPipeline
    # ... adaptar
    return {"valid": True, "checks": [], "should_retry": False,
            "suggestions": []}


def _format_fallback(original_request: str, plan: dict,
                     generated_files: list[dict],
                     validation: dict) -> dict:
    """Wrapper sobre ExplainTool."""
    return {
        "summary": f"Procesado: {original_request[:50]}...",
        "files_created": [f["path"] for f in generated_files],
        "warnings": [],
        "next_steps": ["Revisa los archivos generados"],
        "success": True,
    }


# ============================================================
# Auto-registro al importar el modulo
# ============================================================

def _init_fallbacks() -> None:
    register_fallback("preprocessor_filters", _preprocess_fallback)
    register_fallback("intent_classifier", _intent_fallback)
    register_fallback("goal_tree_planner", _plan_fallback)
    register_fallback("generator_factory", _generate_fallback)
    register_fallback("validator_pipeline", _verify_fallback)
    register_fallback("explain_tool", _format_fallback)


_init_fallbacks()
```

**Criterios de aceptacion:**
- [ ] `register_fallback()` y `get_fallback()` funcionan
- [ ] `execute_fallback()` ejecuta la funcion registrada
- [ ] `execute_fallback()` lanza `KeyError` si no existe
- [ ] Cada fallback pre-registrado retorna dict con schema correcto
- [ ] Fallbacks no lanzan excepciones con input valido

---

### Tarea 1.5 — Tests de Fase 1

#### Archivo: `tests/test_prompt_template.py`

| Test | Descripcion |
|------|-------------|
| `test_template_render` | `render()` reemplaza variables correctamente |
| `test_template_render_validates_input` | `render()` lanza ValidationError si falta campo |
| `test_registry_register_and_get` | `register()` + `get()` recupera template |
| `test_registry_get_unknown` | `get()` con nombre inexistente lanza KeyError |
| `test_registry_list` | `list()` retorna todos los registrados |
| `test_registry_validate_output` | `validate_output()` valida contra schema |
| `test_chain_step_dataclass` | `ChainStep` se construye con todos los campos |

#### Archivo: `tests/test_llm_backend.py`

| Test | Descripcion |
|------|-------------|
| `test_openai_generate` | Mockea ChatOpenAI, verifica LLMResult (sin API key real) |
| `test_openai_generate_structured` | Mockea generate_structured, verifica salida validada |
| `test_failover_all_backends_fail` | Todos los backends fallan, retorna success=False |
| `test_failover_first_succeeds` | Primer backend exito, no llama a los demas |
| `test_build_llm_backend_default` | Sin env vars, construye con defaults |
| `test_build_llm_backend_provider_env` | Con AGENTIC_LLM_PROVIDER, construye backend correcto |

#### Archivo: `tests/test_chain_context.py`

| Test | Descripcion |
|------|-------------|
| `test_set_output_and_get_fields` | Publicar y recuperar campos |
| `test_get_fields_missing_stage` | KeyError si etapa no existe |
| `test_get_fields_missing_field` | KeyError si campo no existe en etapa |
| `test_set_output_validates_contract` | ValidationError si data no cumple contract |
| `test_render_template` | Rellena template con variables de etapa anterior |
| `test_get_history_order` | Historial en orden de insercion |
| `test_get_history_limit` | Limit funciona correctamente |

---

## 3. Fase 2 — Prompts Core

### Objetivo

Implementar los 6 prompts individuales. Cada prompt sigue la misma
estructura: definir un `PromptTemplate`, registrarlo en `PromptRegistry`,
e implementar un `*_prompt_handler()` que orquesta LLM + fallback.

### Estructura de cada prompt

```
prompt_chain/prompts/
├── __init__.py              # importa y registra todos
├── preprocess.py
├── intent.py
├── plan.py
├── generate.py
├── verify.py
└── format.py
```

### Patron comun para cada prompt

```python
# prompts/preprocess.py
from agentic_pipeline.prompt_chain.prompt_template import (
    PromptTemplate, register_prompt,
)
from agentic_pipeline.prompt_chain.llm_backend import (
    build_llm_backend, LLMBackend,
)
from agentic_pipeline.prompt_chain.chain_context import ChainContext
from agentic_pipeline.prompt_chain.fallbacks import execute_fallback
from agentic_pipeline.prompt_chain.contracts import PreprocessorContract

# 1. Definir template
PREPROCESS_TEMPLATE = PromptTemplate(
    name="preprocess",
    system_prompt=(
        "Eres un asistente que normaliza instrucciones de desarrollo "
        "de software. Analiza el texto y extrae informacion estructurada."
    ),
    template="Normaliza el siguiente texto:\n\n{raw_text}",
    input_schema=...,       # Pydantic model de entrada
    output_schema=PreprocessorContract,
    fallback_name="preprocessor_filters",
    temperature=0.1,
)
register_prompt(PREPROCESS_TEMPLATE)

# 2. Handler que orquesta LLM + fallback
async def preprocess_handler(raw_text: str,
                              llm: LLMBackend | None = None,
                              ctx: ChainContext | None = None) -> dict:
    """Ejecuta PREPROCESS prompt con fallback rule-based."""
    if llm is None:
        llm = build_llm_backend()

    template = PromptRegistry.get("preprocess")
    prompt = template.render(raw_text=raw_text)

    result = await llm.generate_structured(
        prompt=prompt,
        system=template.system_prompt,
        output_schema=template.output_schema,
        temperature=template.temperature,
    )

    if not result.success:
        # Fallback rule-based
        output = execute_fallback("preprocessor_filters", raw_text=raw_text)
    else:
        output = result.structured.model_dump()

    if ctx:
        ctx.set_output("preprocess", output, contract=PreprocessorContract)

    return output
```

---

### Tarea 2.1 — Prompt PREPROCESS

**Archivo:** `prompt_chain/prompts/preprocess.py`

```
System: Eres un asistente que normaliza instrucciones de desarrollo
de software. Analiza el texto y extrae informacion estructurada.

Reglas:
- Corrige errores ortograficos obvios
- Segmenta en oraciones
- Identifica el dominio principal
- Si el texto es ambiguo, marcalo

Input: {raw_text}

Output STRICT JSON:
{
  "normalized": "<texto limpio>",
  "domain": "backend" | "frontend" | "infra" | "general",
  "language": "es" | "en",
  "segments": ["<oracion 1>", "<oracion 2>"],
  "has_ambiguity": true | false,
  "confidence": 0.0-1.0
}
```

**Input schema:** `raw_text: str`
**Output contract:** `PreprocessorContract`
**Fallback:** `preprocessor_filters` (NormalizationFilter + SegmentationFilter)

**Tests** (`tests/test_prompt_preprocess.py`):

| Test | Descripcion |
|------|-------------|
| `test_preprocess_llm_success` | LLM responde OK, output validado contra contrato |
| `test_preprocess_llm_fails_fallback` | LLM falla, cae a fallback rule-based |
| `test_preprocess_handles_empty_input` | Texto vacio retorna con confianza baja |
| `test_preprocess_extracts_domain` | Detecta dominio backend/infra/etc |
| `test_preprocess_segments_sentences` | Segmenta correctamente oraciones multiples |

---

### Tarea 2.2 — Prompt INTENT

**Archivo:** `prompt_chain/prompts/intent.py`

```
System: Eres un analista de requisitos de software. Del texto dado,
identifica que accion se pide y con que detalles.

Acciones disponibles:
- CREATE: crear modulo, entidad, proyecto, crud
- READ: consultar, listar, mostrar, leer archivos
- UPDATE: modificar, actualizar, agregar campo, cambiar
- DELETE: eliminar, borrar, quitar, remover
- EXPLAIN: explicar, describir, como funciona

Input: {normalized_text}

Output STRICT JSON:
{
  "intent": "CREATE" | "READ" | "UPDATE" | "DELETE" | "EXPLAIN",
  "confidence": 0.0-1.0,
  "module": "<nombre del modulo>" | null,
  "entity": "<nombre de entidad>" | null,
  "tech": ["nestjs", "prisma", "react", ...],
  "features": ["autenticacion", "crud", "email", ...],
  "is_ambiguous": true | false,
  "missing_info": ["<que falta para completar la instruccion>"]
}
```

**Input schema:** `normalized_text: str, domain: str = "backend"`
**Output contract:** `NLPContract`
**Fallback:** `intent_classifier` (IntentClassifier + NERExtractor + SlotFiller)

**Tests** (`tests/test_prompt_intent.py`):

| Test | Descripcion |
|------|-------------|
| `test_intent_create_module` | "crea modulo pagos" → CREATE, module="pagos" |
| `test_intent_delete` | "elimina modulo auth" → DELETE |
| `test_intent_read` | "muestra el contenido" → READ |
| `test_intent_ambiguous_no_module` | "crea algo" → is_ambiguous=true |
| `test_intent_extracts_tech` | "en NestJS" → tech=["nestjs"] |
| `test_intent_llm_fails_fallback` | LLM falla, cae a IntentClassifier regex |
| `test_intent_low_confidence` | Texto irrelevante → confidence baja |

---

### Tarea 2.3 — Prompt PLAN

**Archivo:** `prompt_chain/prompts/plan.py`

```
System: Eres un arquitecto de software. Dado un objetivo y requisitos,
genera un plan de tareas ejecutable con dependencias.

Cada tarea debe tener:
- id unico (ej: "t1", "t2")
- tipo de accion
- target (modulo, archivo, entidad)
- parametros especificos
- dependencias (task ids que deben completarse antes)

Tipos de tarea disponibles:
- scaffold_module: crear estructura de modulo NestJS
- create_entity: crear entidad/schema Prisma
- generate_code: generar archivo de codigo especifico
- configure: modificar configuracion existente
- verify: verificar que todo este correcto

Input:
{
  "intent": "...",
  "module": "..." | null,
  "entity": "..." | null,
  "tech": [...],
  "features": [...]
}

Output STRICT JSON:
{
  "tasks": [
    {
      "id": "t1",
      "type": "scaffold_module" | "create_entity" |
             "generate_code" | "configure" | "verify",
      "target": "<nombre del modulo/entidad>",
      "params": {
        "tech": "<tecnologia>",
        "features": ["<feature>"]
      },
      "dependencies": []
    }
  ],
  "execution_order": ["t1", "t2", "t3"],
  "complexity": "low" | "medium" | "high",
  "estimated_files": <numero estimado de archivos>
}
```

**Input schema:** `intent: str, module: str | None = None, entity: str | None = None, tech: list[str] = [], features: list[str] = []`
**Output contract:** `PlannerContract`
**Fallback:** `goal_tree_planner` (GoalTreePlanner con templates)

**Tests** (`tests/test_prompt_plan.py`):

| Test | Descripcion |
|------|-------------|
| `test_plan_create_module` | CREATE + module → scaffold_module task |
| `test_plan_create_entity` | CREATE + entity → create_entity task |
| `test_plan_create_crud` | CREATE + module + features:crud → scaffold + generate_code tasks |
| `test_plan_no_tasks_read` | READ intent → tasks vacio |
| `test_plan_dependencies_ordered` | Dependencias forman DAG valido |
| `test_plan_llm_fails_fallback` | LLM falla, cae a GoalTreePlanner |

---

### Tarea 2.4 — Prompt GENERATE

**Archivo:** `prompt_chain/prompts/generate.py`

```
System: Eres un generador de codigo NestJS + Prisma.
Genera el codigo completo para cada tarea del plan.

Convenciones:
- NestJS: modulo, controller, service, DTO, entity
- Prisma: schema con modelo, campos, relaciones
- Typescript: tipado estricto, decoradores
- Incluye imports completos

Input:
{
  "tasks": [...],
  "existing_files": ["<archivos existentes en el proyecto>"]
}

Output STRICT JSON:
{
  "files": [
    {
      "path": "modules/<name>/<name>.module.ts",
      "content": "<codigo completo>",
      "type": "module" | "controller" | "service" |
              "entity" | "schema" | "dto" | "test",
      "overwrite": false
    }
  ],
  "errors": ["<error si algo fallo>"]
}
```

**Input schema:** `tasks: list[dict], existing_files: list[str] = []`
**Output contract:** `SynthesisContract`
**Fallback:** `generator_factory` (GeneratorFactory + templates)

**Tests** (`tests/test_prompt_generate.py`):

| Test | Descripcion |
|------|-------------|
| `test_generate_module_files` | Scaffold task genera .module.ts + .controller.ts + .service.ts |
| `test_generate_entity_schema` | Entity task genera schema.prisma |
| `test_generate_parallel_tasks` | Tareas independientes se procesan sin conflictos |
| `test_generate_no_overwrite` | Si archivo existe, overwrite=false |
| `test_generate_errors_reported` | Tarea invalida → errors list no vacio |
| `test_generate_llm_fails_fallback` | LLM falla, cae a GeneratorFactory |

---

### Tarea 2.5 — Prompt VERIFY

**Archivo:** `prompt_chain/prompts/verify.py`

```
System: Eres un revisor de codigo NestJS/Prisma. Verifica que los
archivos generados cumplan los requisitos y las mejores practicas.

Criterios:
- Estructura de archivos correcta (modulo, controller, etc.)
- Imports necesarios presentes
- Naming conventions (PascalCase, camelCase)
- Relaciones Prisma correctas
- Decoradores NestJS correctos

Input:
{
  "requirements": { "intent": "...", "module": "...", ... },
  "files": [ { "path": "...", "content": "..." } ],
  "criteria": ["estructura", "imports", "naming"]
}

Output STRICT JSON:
{
  "valid": true | false,
  "checks": [
    {
      "check": "estructura",
      "passed": true | false,
      "detail": "<explicacion si fallo>"
    }
  ],
  "should_retry": true | false,
  "suggestions": ["<mejora 1>", "<mejora 2>"]
}
```

**Input schema:** `requirements: dict, files: list[dict], criteria: list[str] = []`
**Output contract:** `ValidatorContract`
**Fallback:** `validator_pipeline` (ValidatorPipeline)

**Tests** (`tests/test_prompt_verify.py`):

| Test | Descripcion |
|------|-------------|
| `test_verify_valid_files` | Archivos correctos → valid=true |
| `test_verify_missing_imports` | Falta import → check falla con detalle |
| `test_verify_should_retry` | Errores graves → should_retry=true |
| `test_verify_suggestions` | Archivos correctos pero mejorables → suggestions |
| `test_verify_llm_fails_fallback` | LLM falla, cae a ValidatorPipeline |

---

### Tarea 2.6 — Prompt FORMAT

**Archivo:** `prompt_chain/prompts/format.py`

```
System: Eres un asistente de desarrollo. Genera un resumen claro
de lo que se ha creado o modificado para el usuario.

Input:
{
  "original_request": "...",
  "plan": { "tasks": [...], "complexity": "..." },
  "generated_files": [{"path": "...", "type": "..."}],
  "validation": { "valid": true, "checks": [...], "suggestions": [...] }
}

Output STRICT JSON:
{
  "summary": "<resumen en lenguaje natural, 2-3 oraciones>",
  "files_created": ["<path relativo 1>", "<path relativo 2>"],
  "warnings": ["<advertencia 1>"],
  "next_steps": [
    "Ejecuta npm install",
    "Revisa el archivo <path>"
  ],
  "success": true | false
}
```

**Input schema:** `original_request: str, plan: dict, generated_files: list[dict], validation: dict`
**Output contract:** `OutputContract` (nuevo Pydantic model)
**Fallback:** `explain_tool` (ExplainTool)

**Tests** (`tests/test_prompt_format.py`):

| Test | Descripcion |
|------|-------------|
| `test_format_summary_mentions_files` | Resumen incluye nombres de archivos |
| `test_format_success_true` | Todo OK → success=true |
| `test_format_warnings_from_verify` | Warnings de VERIFY se propagan |
| `test_format_llm_fails_fallback` | LLM falla, cae a ExplainTool |

---

### Tarea 2.7 — Contracts (nuevos y extendidos)

**Archivo:** `prompt_chain/contracts.py`

```python
"""Modelos Pydantic para validacion de entrada/salida de prompts."""

from pydantic import BaseModel
from typing import Optional


class PreprocessorContract(BaseModel):
    normalized: str
    domain: str
    language: str
    segments: list[str]
    has_ambiguity: bool
    confidence: float


class NLPContract(BaseModel):
    intent: str
    confidence: float
    module: Optional[str] = None
    entity: Optional[str] = None
    tech: list[str] = []
    features: list[str] = []
    is_ambiguous: bool = False
    missing_info: list[str] = []


class PlannerContract(BaseModel):
    tasks: list[dict]
    execution_order: list[str]
    complexity: str
    estimated_files: int = 0


class SynthesisContract(BaseModel):
    files: list[dict]
    errors: list[str] = []


class ValidatorContract(BaseModel):
    valid: bool
    checks: list[dict]
    should_retry: bool = False
    suggestions: list[str] = []


class OutputContract(BaseModel):
    summary: str
    files_created: list[str]
    warnings: list[str] = []
    next_steps: list[str] = []
    success: bool
```

---

## 4. Fase 3 — Chain Orchestrator

### Objetivo

Construir el orquestador que ejecuta los 6 prompts en secuencia,
maneja el grafo de ejecucion (condicional, iterativo), y se integra
con el CLI existente via flag `--chain`.

---

### Tarea 3.1 — `prompt_chain/orchestrator.py`

**Clase principal:**

```python
class ChainOrchestrator:
    """Orquestador del prompt chain con LangGraph.

    Flujo:
        preprocess → intent → plan → generate → verify → format
                                    ↑          │
                                    └── retry ──┘  (si should_retry y attempts < 3)
    """

    def __init__(
        self,
        llm: LLMBackend | None = None,
        tool_registry: ToolRegistry | None = None,
        memory: ConversationalMemory | None = None,
        world: WorldModel | None = None,
        debug_callback: Callable | None = None,
        max_retries: int = 3,
    ):
        self._llm = llm or build_llm_backend()
        self._tool_registry = tool_registry or ToolRegistry.build_default()
        self._memory = memory
        self._world = world
        self._debug_callback = debug_callback
        self._max_retries = max_retries
        self._graph = self._build_graph()

    async def run(self, raw_input: str) -> dict:
        """Ejecuta el prompt chain completo.

        Args:
            raw_input: Texto del usuario (ej: "crea un modulo de pagos")

        Returns:
            Dict con output final del prompt FORMAT
        """
        ctx = ChainContext()
        state = {
            "raw_input": raw_input,
            "ctx": ctx,
            "attempt_count": 0,
            "errors": [],
        }
        result = await self._graph.ainvoke(state)
        return result.get("final_output", {})

    def _build_graph(self) -> StateGraph:
        """Construye el grafo LangGraph con 6 nodos y routing condicional."""
        graph = StateGraph(ChainState)

        graph.add_node("preprocess", self._node_preprocess)
        graph.add_node("intent", self._node_intent)
        graph.add_node("plan", self._node_plan)
        graph.add_node("generate", self._node_generate)
        graph.add_node("verify", self._node_verify)
        graph.add_node("format", self._node_format)

        graph.set_entry_point("preprocess")
        graph.add_edge("preprocess", "intent")
        graph.add_edge("intent", "plan")
        graph.add_edge("plan", "generate")
        graph.add_edge("generate", "verify")
        graph.add_conditional_edges(
            "verify",
            self._router_verify,
            {"retry": "generate", "format": "format", "abort": END},
        )
        graph.set_finish_point("format")

        return graph.compile()

    async def _node_preprocess(self, state: ChainState) -> dict:
        """Ejecuta prompt PREPROCESS."""
        from .prompts.preprocess import preprocess_handler
        output = await preprocess_handler(
            raw_text=state["raw_input"],
            llm=self._llm,
            ctx=state["ctx"],
        )
        if self._debug_callback:
            self._debug_callback("preprocess", output)
        return {"preprocess_output": output}

    async def _node_intent(self, state: ChainState) -> dict:
        """Ejecuta prompt INTENT."""
        from .prompts.intent import intent_handler
        pre = state["ctx"].get_fields("preprocess", ["normalized", "domain"])
        output = await intent_handler(
            normalized_text=pre["normalized"],
            domain=pre.get("domain", "backend"),
            llm=self._llm,
            ctx=state["ctx"],
        )
        if self._debug_callback:
            self._debug_callback("intent", output)
        return {"intent_output": output}

    # ... similar para plan, generate, verify, format

    def _router_verify(self, state: ChainState) -> str:
        """Router condicional post-verificacion.

        - "retry":  si should_retry y attempt_count < max_retries
        - "format": si valid=true o attempt_count >= max_retries
        - "abort":  si error critico
        """
        verify = state.get("verify_output", {})
        if verify.get("should_retry") and state["attempt_count"] < self._max_retries:
            return "retry"
        if verify.get("valid", False):
            return "format"
        return "abort"
```

**Estado del grafo (TypedDict):**

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

**Criterios de aceptacion:**
- [ ] `ChainOrchestrator.run("crea modulo pagos")` retorna dict con output final
- [ ] Flujo condicional: verify → retry generate hasta 3 veces
- [ ] Flujo condicional: verify → format cuando valid=true
- [ ] `debug_callback` recibe output de cada nodo
- [ ] `ChainOrchestrator` usa `ChainContext` como bus de datos
- [ ] Sin LLM (fallback activado), produce output valido

---

### Tarea 3.2 — `prompt_chain/cli.py`

```python
"""CLI handler para el flag --chain."""

import argparse


def add_chain_args(parser: argparse.ArgumentParser) -> None:
    """Anade argumentos de prompt chain al parser."""
    parser.add_argument(
        "--chain", action="store_true",
        help="Usar pipeline Prompt Chaining (en vez del clasico)",
    )


async def run_chain(
    prompt: str,
    output_dir: str = "modules",
    debug_mode: str | None = None,
    show_output: bool = False,
) -> dict:
    """Ejecuta el pipeline Prompt Chaining completo.

    Args:
        prompt: Texto del usuario
        output_dir: Directorio de salida para archivos generados
        debug_mode: "trace" | "step" | "timing" | "inspect" | None
        show_output: Mostrar output_data completo

    Returns:
        Dict con resultado final
    """
    from agentic_pipeline.prompt_chain.orchestrator import ChainOrchestrator

    debug_callback = None
    if debug_mode:
        from agentic_pipeline.debugger import PipelineDebugger
        # Reutilizar PipelineDebugger para mostrar output de cada nodo
        debugger = PipelineDebugger(mode=debug_mode, show_output=show_output)
        debug_callback = debugger._make_stream_callback()

    orchestrator = ChainOrchestrator(
        debug_callback=debug_callback,
    )
    result = await orchestrator.run(prompt)
    return {"output": result, "success": True}
```

---

### Tarea 3.3 — Integracion en `compiler-bot/agentic`

**Modificar el CLI existente** para aceptar `--chain`:

```python
# En compiler-bot/agentic (main)
import argparse
from agentic_pipeline.prompt_chain.cli import add_chain_args, run_chain

parser = argparse.ArgumentParser(...)
# ... argumentos existentes ...
add_chain_args(parser)  # <-- NUEVO

args = parser.parse_args()

if args.chain:
    # Usar Prompt Chaining pipeline
    result = asyncio.run(run_chain(
        prompt=prompt,
        output_dir=args.output,
        debug_mode=args.debug,
        show_output=args.show_output,
    ))
else:
    # Pipeline clasico (comportamiento actual)
    ...
```

**Criterios de aceptacion:**
- [ ] `python compiler-bot/agentic -p "crea modulo pagos" --chain` funciona
- [ ] `--chain --debug trace` muestra output JSON de cada etapa
- [ ] Sin `--chain`, el comportamiento es identico al actual
- [ ] `--chain` funciona sin API key (fallback rule-based)

---

### Tarea 3.4 — Tests de Fase 3

**Archivo:** `tests/test_chain_orchestrator.py`

| Test | Descripcion |
|------|-------------|
| `test_orchestrator_full_flow` | Ejecuta cadena completa, retorna output valido |
| `test_orchestrator_verify_retry` | VERIFY retorna should_retry → GENERATE se re-ejecuta |
| `test_orchestrator_max_retries` | Despues de N retrys, continua a FORMAT |
| `test_orchestrator_fallback_only` | Sin LLM, toda la cadena usa fallbacks |
| `test_orchestrator_debug_callback` | Callback recibe output de cada etapa |
| `test_orchestrator_invalid_input` | Input vacio → manejo de error graceful |
| `test_cli_chain_flag` | `--chain` invoca ChainOrchestrator (mockeado) |
| `test_cli_no_chain_classic` | Sin `--chain`, pipeline clasico (compatibilidad) |

---

## 5. Fase 4 — Sistema Multi-Agente Prompt-Driven

### Objetivo

Reemplazar la logica rule-based de los 5 agentes con llamadas a los
prompts del chain. Cada agente se convierte en un wrapper delgado
que invoca su prompt correspondiente.

---

### Tarea 4.1 — SupervisorAgent Prompt-Driven

**Archivo:** `agents/supervisor_agent.py` (modificar)

```python
class SupervisorAgent:
    """SupervisorAgent ahora usa ChainOrchestrator internamente.

    En vez de _decompose() rule-based, invoca el prompt chain completo
    y decide retry/clarify/abort basado en el resultado.
    """

    def __init__(self, context: SharedContext, agents: dict[str, Agent],
                 llm: LLMBackend | None = None):
        self._orchestrator = ChainOrchestrator(llm=llm)
        # ... resto

    async def process(self, task: Task) -> TaskResult:
        # Usa ChainOrchestrator en vez de los 4 agentes internos
        result = await self._orchestrator.run(task.input)
        if not result.get("success", False):
            return TaskResult(task.id, False, ...)
        return TaskResult(task.id, True, data=result)
```

### Tarea 4.2 — PerceptionAgent → Prompt INTENT

```python
# agents/perception_agent.py (modificar)
class PerceptionAgent(Agent):
    async def process(self, task: Task) -> TaskResult:
        # Usa intent_handler en vez de SentenceTransformerClassifier
        from agentic_pipeline.prompt_chain.prompts.intent import intent_handler
        output = await intent_handler(task.input)
        # Publica a SharedContext como antes
        self.context.publish("perception_result", output)
        return TaskResult(task.id, True, data=output)
```

### Tarea 4.3 — ReasoningAgent → Prompt PLAN

```python
# agents/reasoning_agent.py (modificar)
class ReasoningAgent(Agent):
    async def process(self, task: Task) -> TaskResult:
        from agentic_pipeline.prompt_chain.prompts.plan import plan_handler
        perception = self.context.subscribe("perception_result")
        output = await plan_handler(**perception)
        self.context.publish("reasoning_result", output)
        return TaskResult(task.id, True, data=output)
```

### Tarea 4.4 — ExecutionAgent → Prompt GENERATE

```python
# agents/execution_agent.py (modificar)
class ExecutionAgent(Agent):
    async def process(self, task: Task) -> TaskResult:
        from agentic_pipeline.prompt_chain.prompts.generate import generate_handler
        plan = self.context.subscribe("reasoning_result")
        output = await generate_handler(tasks=plan["tasks"])
        # Aplica acciones al WorldModel
        for f in output.get("files", []):
            self.world.apply_action({"type": "write", "path": f["path"]})
        self.context.publish("execution_result", output)
        return TaskResult(task.id, True, data=output)
```

### Tarea 4.5 — ValidatorAgent → Prompt VERIFY

```python
# agents/validator_agent.py (modificar)
class ValidatorAgent(Agent):
    async def process(self, task: Task) -> TaskResult:
        from agentic_pipeline.prompt_chain.prompts.verify import verify_handler
        execution = self.context.subscribe("execution_result")
        reasoning = self.context.subscribe("reasoning_result")
        output = await verify_handler(
            requirements=reasoning,
            files=execution.get("files", []),
        )
        self.context.publish("validation_result", output)
        return TaskResult(task.id, output.get("valid", False), data=output)
```

### Criterios de aceptacion (Fase 4):

- [ ] `SupervisorAgent` usa `ChainOrchestrator` internamente
- [ ] Cada agente individual usa su prompt correspondiente
- [ ] `test_multiagent.py` (15 tests) sigue pasando con modificaciones minimas
- [ ] Agentes funcionan con LLM y con fallback rule-based

---

## 6. Fase 5 — Feedback Loop + Optimizacion

### Objetivo

Registrar metricas de cada etapa del prompt chain, ajustar parametros
automaticamente, y cachear respuestas del LLM.

---

### Tarea 5.1 — Metricas por Prompt

Extender `MetricsStore` (existente en `feedback_loop.py`) para registrar:

```python
# En MetricsStore.record_stage() — ampliar para prompt chain
def record_prompt(self, prompt_name: str, metrics: dict) -> None:
    """Registra metricas de una etapa del prompt chain.

    metrics:
        - success: bool
        - duration: float (segundos)
        - llm_provider: str
        - llm_model: str
        - temperature: float
        - fallback_used: bool
        - output_size: int (bytes)
        - tokens_used: int (estimado)
    """
    self._record("prompt_chain", prompt_name, metrics)
```

**Nuevas consultas:**

```python
def get_prompt_success_rate(self, prompt_name: str) -> float:
    """Tasa de exito del prompt en las ultimas N ejecuciones."""
    ...

def get_prompt_avg_duration(self, prompt_name: str) -> float:
    """Duracion promedio del prompt."""
    ...
```

### Tarea 5.2 — Ajuste Automatico de Parametros

```python
class PromptOptimizer:
    """Ajusta temperatura/few-shot segun metricas historicas.

    Reglas:
        - Si success_rate < 0.8 en ultimas 20 ejecuciones:
          → reducir temperatura en 0.1 (min 0.0)
        - Si avg_duration > 5s:
          → cambiar a modelo mas rapido
        - Si fallback_used > 50%:
          → reducir temperatura, simplificar prompt
    """

    def __init__(self, metrics_store: MetricsStore):
        self._store = metrics_store

    def optimize(self, prompt_name: str) -> dict:
        """Retorna parametros optimizados para el prompt."""
        rate = self._store.get_prompt_success_rate(prompt_name)
        duration = self._store.get_prompt_avg_duration(prompt_name)

        params = {}
        if rate < 0.8:
            params["temperature"] = max(0.0, 0.3 - 0.1)
        if duration > 5.0:
            params["model"] = "gpt-4o-mini"  # mas rapido
        return params
```

### Tarea 5.3 — Cache de Respuestas del LLM

```python
class LLMCache:
    """Cache AST-level de respuestas del LLM.

    NO cachea texto crudo — cachea el hash del prompt + schema,
    para que variaciones cosmeticas no invaliden el cache.
    """

    def __init__(self, backend: str = "sqlite"):
        self._store = {}  # o SQLite via MetricsStore

    def _make_key(self, prompt: str, schema: str) -> str:
        """Hash deterministico del prompt normalizado + schema."""
        import hashlib
        normalized = " ".join(prompt.lower().split())
        raw = f"{normalized}||{schema}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def get(self, prompt: str, schema: str) -> dict | None:
        key = self._make_key(prompt, schema)
        return self._store.get(key)

    async def set(self, prompt: str, schema: str, response: dict) -> None:
        key = self._make_key(prompt, schema)
        self._store[key] = response
```

### Tarea 5.4 — Dashboard via `--metrics`

Extender el comando `--metrics` del CLI para mostrar metricas del prompt chain:

```bash
python compiler-bot/agentic --metrics table

=== Pipeline Metrics Summary ===
Total records: 142
Total errors:  3
Success rate:  97.9%

Prompt Chain per-stage:
  preprocess: 22 calls, 95.5% success, avg 0.8s
  intent:     22 calls, 100% success, avg 1.2s
  plan:       20 calls, 90.0% success, avg 2.1s
  generate:   40 calls, 97.5% success, avg 4.5s
  verify:     22 calls, 100% success, avg 1.0s
  format:     20 calls, 100% success, avg 0.9s

Cache hit rate: 34.2%
Fallback rate:  5.6%
```

### Criterios de aceptacion (Fase 5):

- [ ] `MetricsStore.record_prompt()` registra metricas por etapa
- [ ] `PromptOptimizer` ajusta temperatura segun success_rate
- [ ] `LLMCache` reduce llamadas repetidas al LLM
- [ ] `--metrics` muestra tabla del prompt chain
- [ ] Cache hit rate >30% en prompts repetidos

---

## 7. Glosario de Archivos

### Archivos Nuevos (22)

| # | Archivo | Fase | Proposito |
|---|---------|------|-----------|
| 1 | `prompt_chain/__init__.py` | F1 | Init del subsistema |
| 2 | `prompt_chain/prompt_template.py` | F1 | PromptTemplate + PromptRegistry + ChainStep |
| 3 | `prompt_chain/llm_backend.py` | F1 | LLMBackend ABC + 4 providers + FailoverLLM |
| 4 | `prompt_chain/chain_context.py` | F1 | ChainContext (bus de datos entre etapas) |
| 5 | `prompt_chain/fallbacks.py` | F1 | FallbackRegistry + 6 fallbacks pre-registrados |
| 6 | `prompt_chain/contracts.py` | F2 | 6 Pydantic contracts + OutputContract nuevo |
| 7 | `prompt_chain/prompts/__init__.py` | F2 | Import y registro de todos los prompts |
| 8 | `prompt_chain/prompts/preprocess.py` | F2 | Prompt PREPROCESS + handler |
| 9 | `prompt_chain/prompts/intent.py` | F2 | Prompt INTENT + handler |
| 10 | `prompt_chain/prompts/plan.py` | F2 | Prompt PLAN + handler |
| 11 | `prompt_chain/prompts/generate.py` | F2 | Prompt GENERATE + handler |
| 12 | `prompt_chain/prompts/verify.py` | F2 | Prompt VERIFY + handler |
| 13 | `prompt_chain/prompts/format.py` | F2 | Prompt FORMAT + handler |
| 14 | `prompt_chain/orchestrator.py` | F3 | ChainOrchestrator con LangGraph |
| 15 | `prompt_chain/cli.py` | F3 | CLI handler para --chain |
| 16 | `tests/test_prompt_template.py` | F1 | 7 tests |
| 17 | `tests/test_llm_backend.py` | F1 | 6 tests |
| 18 | `tests/test_chain_context.py` | F1 | 7 tests |
| 19 | `tests/test_prompt_preprocess.py` | F2 | 5 tests |
| 20 | `tests/test_prompt_intent.py` | F2 | 7 tests |
| 21 | `tests/test_prompt_plan.py` | F2 | 6 tests |
| 22 | `tests/test_prompt_generate.py` | F2 | 6 tests |
| 23 | `tests/test_prompt_verify.py` | F2 | 5 tests |
| 24 | `tests/test_prompt_format.py` | F2 | 4 tests |
| 25 | `tests/test_chain_orchestrator.py` | F3 | 8 tests |

### Archivos Modificados (6)

| # | Archivo | Fase | Cambio |
|---|---------|------|--------|
| 1 | `agents/supervisor_agent.py` | F4 | Usa ChainOrchestrator internamente |
| 2 | `agents/perception_agent.py` | F4 | Usa intent_handler |
| 3 | `agents/reasoning_agent.py` | F4 | Usa plan_handler |
| 4 | `agents/execution_agent.py` | F4 | Usa generate_handler |
| 5 | `agents/validator_agent.py` | F4 | Usa verify_handler |
| 6 | `compiler-bot/agentic` | F3 | Flag --chain |
| 7 | `agentic_pipeline/feedback_loop.py` | F5 | record_prompt() + PromptOptimizer |
| 8 | `agentic_pipeline/metrics_store.py` | F5 | get_prompt_success_rate() |

---

## Apendice A: Resumen de Tests

| Fase | Archivo | Tests |
|------|---------|-------|
| F1 | `test_prompt_template.py` | 7 |
| F1 | `test_llm_backend.py` | 6 |
| F1 | `test_chain_context.py` | 7 |
| F2 | `test_prompt_preprocess.py` | 5 |
| F2 | `test_prompt_intent.py` | 7 |
| F2 | `test_prompt_plan.py` | 6 |
| F2 | `test_prompt_generate.py` | 6 |
| F2 | `test_prompt_verify.py` | 5 |
| F2 | `test_prompt_format.py` | 4 |
| F3 | `test_chain_orchestrator.py` | 8 |
| **Total** | | **61 tests nuevos** |

## Apendice B: Diagrama de Dependencias entre Tareas

```
F1.1 (prompt_template)
  ├── F1.2 (llm_backend)    ── depende de F1.1
  ├── F1.3 (chain_context)   ── depende de F1.1
  └── F1.4 (fallbacks)       ── depende de F1.1
       │
       └── F1.5 (tests F1)   ── depende de F1.1-F1.4
            │
            ▼
       F2.1-F2.7 (prompts)   ── depende de F1.5
            │
            ▼
       F3.1-F3.4 (orchestrator) ── depende de F2
            │
            ├── F4.1-F4.5 (agentes) ── depende de F3
            │
            └── F5.1-F5.4 (feedback) ── depende de F3
```

## Apendice C: Checklist de Verificacion Pre-commit

Antes de commitear cada fase:

- [ ] `ruff check compiler-bot/agentic_pipeline/` — 0 errores
- [ ] `ruff format compiler-bot/agentic_pipeline/` — formateado
- [ ] `pytest tests/ -q --tb=short` — tests nuevos + existentes pasan
- [ ] Tests nuevos incluidos en el commit
- [ ] Sin `print()` statements de debug (usar logging)
- [ ] Type hints en todas las funciones nuevas
- [ ] Docstrings en clases y funciones publicas
