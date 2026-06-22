---
id: 187
area: dev
type: plan
module: user_request_layer_execution
version: 1.0
status: DRAFT
tags:
  - plan
  - execution
  - user-request
  - nlu
  - nlg
  - migration
  - modularization
summary: "Plan de ejecucion detallado para la migracion a User Request Layer definida en doc 186. Desglosa las 6 fases en tareas atomicas con dependencias, esfuerzo estimado, criterios de exito y verificacion."
keywords:
  - execution-plan
  - migration
  - nlu-pipeline
  - nlg-pipeline
  - contracts
  - taxonomy
  - phases
  - tasks
  - dependencies
  - success-criteria
changelog:
  - version: 1.0
    date: 2026-06-22
    author: sisyphus
    description: Creacion del plan de ejecucion para la migracion a User Request Layer
---

# Plan de Ejecucion: User Request Layer

> **Documento fuente:** `186_PROP_DEV_USER_REQUEST_LAYER_1_0_DRAFT.md`
> **Version del plan:** 1.0
> **Fecha:** 2026-06-22
> **Estado:** BORRADOR

---

## Tabla de Contenidos

1. [Resumen ejecutivo](#1-resumen-ejecutivo)
2. [Dependencias entre fases](#2-dependencias-entre-fases)
3. [Fase 1: Contratos y taxonomia unificada](#3-fase-1-contratos-y-taxonomia-unificada)
4. [Fase 2: NLU Pipeline](#4-fase-2-nlu-pipeline)
5. [Fase 3: NLG Pipeline](#5-fase-3-nlg-pipeline)
6. [Fase 4: Integracion en CLI](#6-fase-4-integracion-en-cli)
7. [Fase 5: Canales adicionales](#7-fase-5-canales-adicionales)
8. [Fase 6: Limpieza](#8-fase-6-limpieza)
9. [Riesgos y mitigacion](#9-riesgos-y-mitigacion)
10. [Criterios de aceptacion globales](#10-criterios-de-aceptacion-globales)

---

## 1. Resumen ejecutivo

### 1.1 Proposito

Este plan desglosa las 6 fases de migracion definidas en la [propuesta 186](186_PROP_DEV_USER_REQUEST_LAYER_1_0_DRAFT.md) en tareas atomicas ejecutables, con dependencias, esfuerzo estimado, criterios de exito y verificacion para cada una.

### 1.2 Fases y esfuerzo estimado

| Fase | Descripcion | Archivos | Esfuerzo estimado | Depende de |
|------|-------------|----------|-------------------|------------|
| F1 | Contratos y taxonomia unificada | ~8 archivos | 3-4h | Ninguna |
| F2 | NLU Pipeline (refactor) | ~15 archivos | 5-7h | F1 |
| F3 | NLG Pipeline (nuevo) | ~15 archivos | 4-6h | F1 |
| F4 | Integracion CLI | ~3 archivos | 3-4h | F2, F3 |
| F5 | Canales adicionales | ~6 archivos | 4-5h | F4 |
| F6 | Limpieza post-migracion | ~20 archivos | 2-3h | F4 |
| | **Total estimado** | **~67 archivos** | **21-29h** | |

### 1.3 Modo de ejecucion

Cada fase se ejecuta en orden. Cada tarea dentro de una fase produce un artefacto verificable (archivo creado/modificado + tests pasando). No se avanza a la siguiente tarea hasta que la actual esta completa y verificada.

### 1.4 Convenciones

- **Taxonomia de intenciones unificada:** CREATE, READ, UPDATE, DELETE, EXPLAIN, CONFIGURE
- **Alias:** CREATE←SCAFFOLD, READ←QUERY/EXPLORE, UPDATE←MODIFY, DELETE←REMOVE, EXPLAIN←HELP
- **Canal default:** CLI
- **Formato de contratos:** Pydantic v2 (BaseModel, inmutables)
- **Tests:** pytest, minimo 1 test por componente publico
- **Backward compat:** `nlp/__init__.py` re-exporta desde `user_request/` durante F1-F4

---

## 2. Dependencias entre fases

```
F1 (Contratos + Taxonomia)
 │
 ├──▶ F2 (NLU Pipeline)
 │       │
 │       └──▶ F4 (Integracion CLI)
 │               │
 │               ├──▶ F5 (Canales adicionales)
 │               └──▶ F6 (Limpieza)
 │
 └──▶ F3 (NLG Pipeline)
         │
         └──▶ F4 (Integracion CLI)
```

**Reglas:**
- F1 siempre primero (define contratos que todos consumen)
- F2 y F3 son paralelizables (independientes entre si, ambas dependen solo de F1)
- F4 requiere F2 + F3 completas
- F5 requiere F4 (entrypoint modificado)
- F6 requiere F4 (todos los imports migrados)

---

## 3. Fase 1: Contratos y taxonomia unificada

**Esfuerzo estimado:** 3-4h
**Objetivo:** Definir contratos Pydantic compartidos y unificar taxonomia de intenciones.

### 3.1 Tareas

#### T1.1 — Crear estructura de directorios

- `user_request/`
- `user_request/__init__.py`
- `user_request/contracts/`
- `user_request/contracts/__init__.py`

**Verificacion:** `python -c "from user_request.contracts import *"` sin errores.

#### T1.2 — Definir `user_request/contracts/enums.py`

- `IntentType(str, Enum)`: CREATE, READ, UPDATE, DELETE, EXPLAIN, CONFIGURE
- `RequestChannel(str, Enum)`: CLI, WEBUI, API, EDITOR, AGENT
- `Language(str, Enum)`: ES, EN
- `SlotName(str, Enum)`: ACCION, TIPO, NOMBRE, TECH, ATRIBUTOS, DOMINIO, OBJETIVO, FILTRO, LIMITE, CAMBIO, VALOR, TOPICO, PROFUNDIDAD, PARAMETRO

**Verificacion:** Test que enumere todos los valores y verifique que no hay colisiones.

#### T1.3 — Definir `user_request/contracts/request.py`

Basado en `nlp/enriched_input.py` actual mas las ampliaciones propuestas:

```python
@dataclass(frozen=True)
class IntentResult:
    primary: IntentType
    secondary: IntentType | None
    confidence: float
    classifier: str  # "llm" | "semantic" | "rule"

@dataclass(frozen=True)
class Entities:
    modules: list[str]
    techs: list[str]
    requirements: list[str]

@dataclass(frozen=True)
class Slots:
    accion: str | None
    tipo: str | None
    nombre: str | None
    tech: str | None
    atributos: list[tuple[str, str]] = field(default_factory=list)
    ...

@dataclass(frozen=True)
class RequestContext:
    session_id: str
    history: list[dict]
    defaults: dict
    channel: RequestChannel

class RequestObject(BaseModel):
    raw: str
    normalized: str
    intent: IntentResult
    entities: Entities
    slots: Slots
    ambiguity: AmbiguityResult | None
    channel: RequestChannel
    context: RequestContext | None
    metadata: dict
```

**Verificacion:** Test de serializacion/deserializacion con datos de ejemplo.

#### T1.4 — Definir `user_request/contracts/response.py`

```python
class ResponseObject(BaseModel):
    success: bool
    data: dict | None = None
    message: str | None = None
    error: str | None = None
    suggestions: list[str] = []
    channel: RequestChannel = RequestChannel.CLI
    metadata: dict = {}
```

#### T1.5 — Reescribir `SlotFiller` con taxonomia unificada

- Crear `user_request/nlu/slot_filler.py`
- Implementar `UNIFIED_TAXONOMY` con mapeo de alias (CREATE←SCAFFOLD, etc.)
- `SlotFiller.fill(intent: IntentResult, entities: Entities) -> Slots`
- Test: cada intent type produce slots correctos
- Test: alias se resuelven al tipo canonico

**Archivo:** `user_request/nlu/slot_filler.py`

#### T1.6 — Mantener backward compat en `nlp/__init__.py`

```python
# nlp/__init__.py — v2 transicional
from user_request.contracts.request import RequestObject, IntentResult, Entities
from user_request.contracts.enums import IntentType, RequestChannel
from user_request.nlu.classifiers.rule import RuleIntentClassifier as IntentClassifier
# ...
```

**Verificacion:** Los imports antiguos (`from nlp import IntentClassifier`) siguen funcionando.

#### T1.7 — Tests de contratos

- `user_request/tests/test_contracts.py`
- Test: RequestObject se construye con argumentos minimos
- Test: ResponseObject serializa/deserializa a JSON
- Test: IntentType.from_alias("SCAFFOLD") → IntentType.CREATE
- Test: Enums no tienen valores duplicados
- Test: Slots se construye con validacion de tipos

**Archivo:** `user_request/tests/test_contracts.py`
**Verificacion:** `pytest user_request/tests/test_contracts.py -v` → PASS

### 3.2 Artefactos producidos

| Archivo | Tipo |
|---------|------|
| `user_request/__init__.py` | Nuevo |
| `user_request/contracts/__init__.py` | Nuevo |
| `user_request/contracts/enums.py` | Nuevo |
| `user_request/contracts/request.py` | Nuevo |
| `user_request/contracts/response.py` | Nuevo |
| `user_request/nlu/slot_filler.py` | Nuevo (reescritura) |
| `user_request/tests/test_contracts.py` | Nuevo |
| `nlp/__init__.py` | Modificado (re-export) |

### 3.3 Criterios de exito

- [ ] Todos los tests de contratos pasan
- [ ] Los imports legacy desde `nlp/` funcionan sin cambios en consumidores
- [ ] `SlotFiller` entiende las 6 intenciones canonicas + alias
- [ ] `ruff check .` sin errores en `user_request/`
- [ ] `mypy --strict` sin errores en `user_request/contracts/`

---

## 4. Fase 2: NLU Pipeline

**Esfuerzo estimado:** 5-7h
**Objetivo:** Refactorizar NLP actual en pipeline modular con estrategia de fallback chain.

### 4.1 Dependencias internas

```
normalizer.py (independiente)
    │
classifiers/              extractors/              ambiguity.py
  base.py                    base.py                  │
  rule.py ← intent_cls.py   rule.py  ← ner_extr.py   │
  semantic.py               spacy.py ← spacy_proc.py │
    │                        │                        │
    ▼                        ▼                        ▼
┌──────────────────────────────────────────────────────────┐
│              NLUPipeline (orquestador)                    │
│  normalizer → classifier_chain → extractor_chain →       │
│  slot_filler → ambiguity_resolver → enricher             │
└──────────────────────────────────────────────────────────┘
```

### 4.2 Tareas

#### T2.1 — Crear `Normalizer`

Migrar desde `compiler-bot/agentic_pipeline/nodes/preprocessor.py` la logica de normalizacion.

```python
class Normalizer:
    def normalize(self, raw: str) -> str:
        """NFKC normalize, lowercase, collapse spaces, strip punct."""
```

**Archivo:** `user_request/nlu/normalizer.py`
**Test:** 3-4 casos: unicode, puntuacion redundante, whitespace, texto vacio.

#### T2.2 — Crear `classifiers/base.py`

Interfaz abstracta `IntentClassifier`:

```python
class IntentClassifier(ABC):
    min_confidence: float = 0.0

    @abstractmethod
    def classify(self, text: str) -> IntentResult: ...
```

**Archivo:** `user_request/nlu/classifiers/base.py`

#### T2.3 — Migrar `intent_classifier.py` → `classifiers/rule.py`

- Heredar de `IntentClassifier`
- Mantener regex patterns actuales
- Mapear salidas legacy (SCAFFOLD, QUERY, etc.) a taxonomia unificada via alias
- `min_confidence = 0.6`

**Archivo:** `user_request/nlu/classifiers/rule.py`
**Origen:** `nlp/intent_classifier.py`
**Test:** Mismas cobertura que test actual + verificacion de alias.

#### T2.4 — Migrar `semantic` → `classifiers/semantic.py`

Extaer la logica de SentenceTransformer que actualmente esta en `perception_unit.py`.

```python
class SemanticIntentClassifier(IntentClassifier):
    min_confidence = 0.7

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self._model = SentenceTransformer(model_name)
```

**Archivo:** `user_request/nlu/classifiers/semantic.py`
**Test:** Similitud coseno, fallback cuando confianza < threshold.

#### T2.5 — Crear `ClassifierManager`

Implementar cadena de responsabilidad:

```python
class ClassifierManager:
    def __init__(self, classifiers: list[IntentClassifier]):
        self._chain = classifiers

    def classify(self, text: str) -> IntentResult:
        for classifier in self._chain:
            result = classifier.classify(text)
            if result.confidence >= classifier.min_confidence:
                return result
        return self._chain[-1].classify(text)
```

**Archivo:** `user_request/nlu/classifiers/__init__.py`
**Test:** Cadena completa (LLM fallback → semantic → rule), cadena vacia.

#### T2.6 — Crear `extractors/base.py`

```python
class EntityExtractor(ABC):
    min_confidence: float = 0.0

    @abstractmethod
    def extract(self, text: str) -> Entities: ...
```

**Archivo:** `user_request/nlu/extractors/base.py`

#### T2.7 — Migrar `ner_extractor.py` → `extractors/rule.py`

```python
class RuleEntityExtractor(EntityExtractor):
    min_confidence = 0.6
    # regex patterns actuales de NERExtractor
```

**Archivo:** `user_request/nlu/extractors/rule.py`
**Origen:** `nlp/ner_extractor.py`

#### T2.8 — Migrar `spacy_processor.py` → `extractors/spacy.py`

```python
class SpacyEntityExtractor(EntityExtractor):
    min_confidence = 0.8
    # modelo spaCy existente, integrado como extractor en la cadena
```

**Archivo:** `user_request/nlu/extractors/spacy.py`
**Test:** Carga condicional del modelo (no falla si modelo no instalado).

#### T2.9 — Migrar `ambiguity_detector.py` → `ambiguity.py`

Extender con generacion de preguntas:

```python
class AmbiguityResolver:
    def __init__(self, slot_filler: SlotFiller):
        self._slot_filler = slot_filler

    def resolve(self, request: RequestObject) -> RequestObject:
        ...

    def generate_questions(self, request: RequestObject) -> list[str]:
        """Genera pregunta en LN para cada slot faltante."""
        ...

    def detect(self, request: RequestObject) -> AmbiguityResult:
        """Compatibilidad backward: delegado interno."""
        ...
```

**Archivo:** `user_request/nlu/ambiguity.py`

#### T2.10 — Crear `Enricher`

```python
class Enricher:
    def __init__(self, context_store: Callable | None = None):
        self._store = context_store

    def enrich(self, request: RequestObject) -> RequestObject:
        """Anade contexto de sesion, historial, defaults."""
```

**Archivo:** `user_request/nlu/enricher.py`

#### T2.11 — Crear `pipeline.py` (orquestador)

```python
class NLUPipeline:
    def __init__(self, classifiers=None, extractors=None, ...):
        self.normalizer = Normalizer()
        self.classifier = ClassifierManager(classifiers or DEFAULT_CLASSIFIERS)
        self.extractor = EntityExtractorManager(extractors or DEFAULT_EXTRACTORS)
        self.slot_filler = SlotFiller()
        self.ambiguity = AmbiguityResolver(self.slot_filler)
        self.enricher = Enricher()

    def process(self, raw: str, context: RequestContext | None = None) -> RequestObject:
        """Pipeline completo: normalizar → clasificar → extraer → slots → ambiguedad → enriquecer."""
```

**Archivo:** `user_request/nlu/pipeline.py`
**Test de integracion:** Pipeline completo con entrada real.

#### T2.12 — Tests de componentes NLU

- `user_request/tests/test_classifiers.py` — cada clasificador individual + ClassifierManager
- `user_request/tests/test_extractors.py` — cada extractor + manager
- `user_request/tests/test_ambiguity.py` — AmbiguityResolver con varios escenarios
- `user_request/tests/test_enricher.py` — enriquecimiento contextual
- `user_request/tests/test_nlu_pipeline.py` — integracion completa

### 4.3 Artefactos producidos

| Archivo | Origen |
|---------|--------|
| `user_request/nlu/normalizer.py` | Nuevo (desde preprocessor.py) |
| `user_request/nlu/classifiers/base.py` | Nuevo |
| `user_request/nlu/classifiers/rule.py` | Desde `nlp/intent_classifier.py` |
| `user_request/nlu/classifiers/semantic.py` | Desde `perception_unit.py` |
| `user_request/nlu/classifiers/__init__.py` | ClassifierManager |
| `user_request/nlu/extractors/base.py` | Nuevo |
| `user_request/nlu/extractors/rule.py` | Desde `nlp/ner_extractor.py` |
| `user_request/nlu/extractors/spacy.py` | Desde `spacy_processor.py` |
| `user_request/nlu/ambiguity.py` | Desde `nlp/ambiguity_detector.py` |
| `user_request/nlu/enricher.py` | Nuevo (desde ContextState) |
| `user_request/nlu/pipeline.py` | Nuevo (orquestador) |
| `user_request/tests/test_*.py` | 5 archivos nuevos |

### 4.4 Criterios de exito

- [ ] Tests unitarios por componente pasan
- [ ] Test de integracion NLU pipeline produce `RequestObject` valido
- [ ] Fallback chain funciona: LLM no disponible → semantic → rule
- [ ] `ruff check .` 0 errores en `user_request/nlu/`
- [ ] `mypy --strict` sin errores
- [ ] Cobertura de tests > 80% en `user_request/nlu/`

---

## 5. Fase 3: NLG Pipeline

**Esfuerzo estimado:** 4-6h
**Objetivo:** Crear pipeline de generacion de respuesta en lenguaje natural.

### 5.1 Arquitectura

```
ResponseObject
    │
    ▼
Formatter (selecciona segun tipo: success/error/ir/metrics)
    │
    ▼ content string
Translator (template-based, es↔en)
    │
    ▼ translated string
ChannelAdapter (CLI/JSON/HTML segun canal)
    │
    ▼ string final
```

### 5.2 Tareas

#### T3.1 — Crear `formatters/base.py`

```python
class NLGFormatter(ABC):
    @abstractmethod
    def format(self, response: ResponseObject) -> str: ...

class SuccessFormatter(NLGFormatter):
    def format(self, response: ResponseObject) -> str:
        """'Creado modulo pagos en NestJS. Archivos: controller, service...'"""

class ErrorFormatter(NLGFormatter):
    def format(self, response: ResponseObject) -> str:
        """'No se pudo crear el modulo: el nombre ya existe.'"""

class IRFormatter(NLGFormatter):
    def format(self, response: ResponseObject) -> str:
        """Muestra IR de forma legible."""

class MetricFormatter(NLGFormatter):
    def format(self, response: ResponseObject) -> str:
        """'Pipeline: 8 stages, 0 errores, 0.255s total.'"""
```

**Archivos:** `user_request/nlg/formatters/base.py`, `success.py`, `error.py`, `ir_display.py`, `metrics.py`

#### T3.2 — Crear `Translator`

```python
class NLGTranslator:
    _templates: dict[str, dict[str, str]] = {
        "created_module": {"es": "Creado modulo {name}", "en": "Module {name} created"},
        ...
    }

    def translate(self, text: str, target_lang: str = "es") -> str:
        """Template-based; fallback LLM si no hay template."""

    def _llm_translate(self, text: str, lang: str) -> str:
        """Solo si LLM disponible y no es template conocido."""
```

**Archivo:** `user_request/nlg/translator.py`

#### T3.3 — Crear `adapters/base.py`

```python
class ChannelAdapter(ABC):
    @abstractmethod
    def adapt(self, content: str, response: ResponseObject) -> str: ...

class CLIAdapter(ChannelAdapter):
    """Texto plano, max 80 chars/linea, sin adornos."""

class APIAdapter(ChannelAdapter):
    """JSON puro con field message."""

class WebUIAdapter(ChannelAdapter):
    """HTML fragments."""

class EditorAdapter(ChannelAdapter):
    """Snippets cortos."""

class AgentAdapter(ChannelAdapter):
    """Dict estructurado."""
```

**Archivos:** `user_request/nlg/adapters/base.py`, `cli.py`, `api.py`, `webui.py`, `editor.py`, `agent.py`

#### T3.4 — Crear `pipeline.py` (orquestador NLG)

```python
class NLGPipeline:
    def __init__(self, channel: RequestChannel = RequestChannel.CLI):
        self._channel = channel
        self._formatters: dict[str, NLGFormatter] = {
            "success": SuccessFormatter(),
            "error": ErrorFormatter(),
            "ir": IRFormatter(),
            "metrics": MetricFormatter(),
        }
        self._translator = NLGTranslator()
        self._adapters: dict[RequestChannel, ChannelAdapter] = {
            RequestChannel.CLI: CLIAdapter(),
            RequestChannel.API: APIAdapter(),
            RequestChannel.WEBUI: WebUIAdapter(),
            RequestChannel.EDITOR: EditorAdapter(),
            RequestChannel.AGENT: AgentAdapter(),
        }

    def process(self, response: ResponseObject) -> str:
        """Formatter → Translator → Adapter."""
```

**Archivo:** `user_request/nlg/pipeline.py`

#### T3.5 — Tests NLG

- `user_request/tests/test_formatters.py`
- `user_request/tests/test_translator.py`
- `user_request/tests/test_nlg_pipeline.py`

### 5.3 Artefactos producidos

| Archivo | Tipo |
|---------|------|
| `user_request/nlg/__init__.py` | Nuevo |
| `user_request/nlg/pipeline.py` | Nuevo |
| `user_request/nlg/formatters/base.py` | Nuevo |
| `user_request/nlg/formatters/__init__.py` | Nuevo |
| `user_request/nlg/formatters/success.py` | Nuevo |
| `user_request/nlg/formatters/error.py` | Nuevo |
| `user_request/nlg/formatters/ir_display.py` | Nuevo |
| `user_request/nlg/formatters/metrics.py` | Nuevo |
| `user_request/nlg/translator.py` | Nuevo |
| `user_request/nlg/adapters/__init__.py` | Nuevo |
| `user_request/nlg/adapters/base.py` | Nuevo |
| `user_request/nlg/adapters/cli.py` | Nuevo |
| `user_request/nlg/adapters/api.py` | Nuevo |
| `user_request/nlg/adapters/webui.py` | Nuevo |
| `user_request/nlg/adapters/editor.py` | Nuevo |
| `user_request/nlg/adapters/agent.py` | Nuevo |
| `user_request/tests/test_formatters.py` | Nuevo |
| `user_request/tests/test_translator.py` | Nuevo |
| `user_request/tests/test_nlg_pipeline.py` | Nuevo |

### 5.4 Criterios de exito

- [ ] Cada formatter produce texto legible para una `ResponseObject` dada
- [ ] Translator resuelve templates es/en correctamente
- [ ] CLIAdapter produce texto <= 80 chars/linea
- [ ] APIAdapter produce JSON valido
- [ ] NLGPipeline completa el ciclo completo
- [ ] `ruff check .` 0 errores en `user_request/nlg/`

---

## 6. Fase 4: Integracion en CLI

**Esfuerzo estimado:** 3-4h
**Objetivo:** Conectar `UserRequestLayer` con el entrypoint `agentic`.

### 6.1 Tareas

#### T4.1 — Crear `UserRequestLayer` facade

```python
class UserRequestLayer:
    def __init__(self, channel: RequestChannel = RequestChannel.CLI):
        self.channel = channel
        self.nlu = NLUPipeline()
        self.nlg = NLGPipeline(channel)

    async def process_input(self, raw: str) -> RequestObject:
        return self.nlu.process(raw)

    async def format_output(self, response: ResponseObject) -> str:
        return self.nlg.process(response)

    def set_channel(self, channel: RequestChannel) -> None:
        self.channel = channel
        self.nlg.set_channel(channel)
```

**Archivo:** `user_request/__init__.py` (o `user_request/layer.py`)

#### T4.2 — Modificar `agentic` entrypoint

```python
# En agentic
from user_request import UserRequestLayer

layer = UserRequestLayer()
request = layer.nlu.process(prompt)          # RequestObject
result = await orchestrator.run(request)      # ResponseObject
response = layer.nlg.process(result)          # string formateado
print(response)
```

**Archivo:** `compiler-bot/agentic`

**Cambios especificos:**
- Reemplazar `json.dumps(result, indent=2, default=str)` por llamada a `NLGPipeline`
- Anadir flag `--output-format text|json` (default: text)
- Modo `--json` fuerza `APIAdapter`
- Modo `--ir-only` usa `IRFormatter`

#### T4.3 — Modo dialogo con AmbiguityResolver

Si `AmbiguityResolver.generate_questions()` devuelve preguntas, el CLI entra en modo interactivo:

```
$ agentic --prompt "crea un modulo"
? ?Que nombre quieres para el modulo? ► [user escribe "pagos"]
? ?En que tecnologia? (default: NestJS) ► [user escribe "NestJS"]
Creado modulo pagos en NestJS.
```

**Archivo:** `user_request/nlu/ambiguity.py` (ya tiene generate_questions)
**Integracion:** en `agentic`, loop de preguntas/respuestas antes de enviar al pipeline.

#### T4.4 — Tests end-to-end

- Test: `agentic --prompt "crea modulo test"` produce salida en lenguaje natural
- Test: `agentic --prompt "crea modulo test" --json` produce JSON valido
- Test: `agentic --prompt "crea modulo test" --ir-only` produce IR formateado
- Test: entrada ambigua entra en modo dialogo

### 6.2 Artefactos modificados

| Archivo | Accion |
|---------|--------|
| `user_request/__init__.py` | Anadir UserRequestLayer |
| `compiler-bot/agentic` | Modificar entrypoint |
| (nuevo) | Tests e2e |

### 6.3 Criterios de exito

- [ ] `agentic` produce mensajes legibles (no JSON crudo) por defecto
- [ ] `--json` produce JSON valido con field `message`
- [ ] Modo dialogo interactivo funciona para entradas ambiguas
- [ ] Todos los tests existentes del pipeline siguen pasando (regresion)
- [ ] `agentic --help` documenta los nuevos flags

---

## 7. Fase 5: Canales adicionales

**Esfuerzo estimado:** 4-5h
**Objetivo:** Soportar WebUI y API como canales de entrada/salida.

### 7.1 Tareas

#### T5.1 — Adapter WebUI

```python
class WebUIAdapter(ChannelAdapter):
    def adapt(self, content: str, response: ResponseObject) -> str:
        """HTML fragmento o JSON enriquecido con enlaces."""
```

**Archivo:** `user_request/nlg/adapters/webui.py`

#### T5.2 — Endpoint HTTP `/api/nlu`

```python
# POST /api/nlu
# Body: {"text": "crea modulo pagos"}
# Response: RequestObject (JSON)
```

**Framework:** Usar `aiohttp` o FastAPI si ya disponible. Si no, modulo minimal con `http.server`.

#### T5.3 — Endpoint HTTP `/api/chat`

```python
# POST /api/chat
# Body: {"text": "crea modulo pagos", "channel": "api"}
# Response: {"success": true, "message": "Creado modulo pagos", "data": {...}}
```

**Archivo:** Nuevo servidor HTTP o integracion en dashboard existente.

#### T5.4 — Tests de canales

- Test: WebUIAdapter produce HTML valido
- Test: Endpoint `/api/nlu` devuelve RequestObject valido
- Test: Endpoint `/api/chat` completa ciclo NLU → pipeline → NLG

### 7.2 Artefactos

| Archivo | Accion |
|---------|--------|
| `user_request/nlg/adapters/webui.py` | Implementar |
| `user_request/api/server.py` | Nuevo (servidor HTTP) |
| `user_request/api/__init__.py` | Nuevo |
| `user_request/tests/test_api.py` | Nuevo |

### 7.3 Criterios de exito

- [ ] Adapter WebUI produce HTML valido
- [ ] `/api/nlu` accepta POST y devuelve JSON con RequestObject
- [ ] `/api/chat` completa ciclo completo
- [ ] Servidor HTTP arranca sin errores

---

## 8. Fase 6: Limpieza

**Esfuerzo estimado:** 2-3h
**Objetivo:** Remover codigo legacy, actualizar imports y documentacion.

### 8.1 Tareas

#### T6.1 — Deprecar `nlp/` como re-exportador

- Marcar `nlp/__init__.py` con `DeprecationWarning`
- No eliminar hasta confirmar que no hay imports directos

```python
import warnings
warnings.warn(
    "nlp module is deprecated. Use user_request.nlu instead.",
    DeprecationWarning,
    stacklevel=2,
)
```

#### T6.2 — Remover `intent_stage.py`

- Verificar que nadie importa desde `nodes/intent_stage.py`
- Eliminar archivo

#### T6.3 — Actualizar imports en todo el codebase

```
grep -rn "from nlp import" compiler-bot/ --include="*.py"
grep -rn "from nodes.perception_unit import" compiler-bot/ --include="*.py"
grep -rn "from nodes.intent_stage import" compiler-bot/ --include="*.py"
```

Cada match → actualizar a `from user_request.nlu import ...`

**Archivos tipicos a modificar:**
- `compiler-bot/agentic_pipeline/orchestrator.py`
- `compiler-bot/agentic_pipeline/nodes/perception_unit.py` (si se mantiene)
- Cualquier test que importe directamente de `nlp/`

#### T6.4 — Actualizar documentacion

- `README.md`: actualizar descripcion de arquitectura
- `docs/` si referencia `nlp/` como modulo activo

#### T6.5 — Verificar regresion

- `pytest compiler-bot/agentic_pipeline/tests/ -v --tb=short` → todos PASS
- `ruff check .` → 0 errores
- `bash -n compiler-bot/agentic` → sin errores sintacticos

### 8.2 Criterios de exito

- [ ] No hay imports directos a `nlp/` desde el pipeline
- [ ] `intent_stage.py` eliminado
- [ ] Tests de regresion pasan (699 tests)
- [ ] `ruff check .` 0 errores
- [ ] `mypy --strict` sin errores

---

## 9. Riesgos y mitigacion

| # | Riesgo | Fase | Impacto | Prob | Mitigacion |
|---|--------|------|---------|------|------------|
| R1 | Taxonomia unificada rompe clasificadores existentes | F1 | Alto | Media | Tests de regresion en F1.6. Mapeo de alias en SlotFiller. |
| R2 | Duplicacion temporal nlp/ + user_request/ causa confusion | F1-F5 | Medio | Alta | Documentar en `nlp/__init__.py` que es transicional. |
| R3 | Dependencia LLM en clasificacion aumenta latencia | F2, F4 | Medio | Media | Fallback chain: LLM → semantic → rule. Modo offline = rule. |
| R4 | NLG aumenta latencia de salida | F3, F4 | Bajo | Baja | Formatters ligeros (sin LLM). Translator template-first. |
| R5 | SpacyProcessor duplica funcionalidad de NERExtractor | F2 | Bajo | Alta | Ambos en la cadena; spacy es extractor opcional. |
| R6 | Modo dialogo interactivo cambia UX del CLI | F4 | Medio | Media | Solo se activa si AmbiguityResolver detecta ambiguedad. Flag `--no-dialog` para desactivar. |
| R7 | Servidor HTTP duplica funcionalidad del dashboard | F5 | Bajo | Baja | Reutilizar puerto y servidor existente del dashboard si es posible. |
| R8 | Cambio de imports masivo introduce errores | F6 | Alto | Media | `grep` sistematico + CI pipeline antes del commit. |

### 9.1 Plan de contingencia por riesgo

| Riesgo | Accion si se materializa |
|--------|--------------------------|
| R1 | Rollback del SlotFiller a version anterior. Mantener ambos en paralelo. |
| R3 | Desconectar LLMClassifier en configuracion. El sistema funciona solo con rule + semantic. |
| R6 | Desactivar modo dialogo por defecto. Solo activo con flag `--dialog`. |
| R8 | Revertir commit de limpieza. Hacer migracion de imports en PR separado. |

---

## 10. Criterios de aceptacion globales

### 10.1 Funcionales

- [ ] El CLI produce mensajes en lenguaje natural (no JSON crudo) por defecto
- [ ] El CLI acepta `--json` para salida JSON
- [ ] El CLI acepta `--ir-only` para mostrar solo el IR
- [ ] Entradas ambiguas provocan preguntas declarativas
- [ ] Endpoint `/api/nlu` devuelve `RequestObject`
- [ ] Endpoint `/api/chat` completa ciclo NLU → pipeline → NLG
- [ ] Taxonomia unificada: CREATE, READ, UPDATE, DELETE, EXPLAIN, CONFIGURE

### 10.2 Tecnicos

- [ ] 699 tests de regresion pasan
- [ ] `ruff check .` → 0 errores
- [ ] `mypy --strict` → 0 errores en `user_request/`
- [ ] Backward compat: `from nlp import *` sigue funcionando (con warnings)
- [ ] Cobertura de tests en `user_request/` > 80%

### 10.3 De codigo

- [ ] Sin `as any`, `@ts-ignore`, `except: pass`
- [ ] Type hints en todas las funciones publicas
- [ ] Logging con `%s`, no f-strings en logger calls
- [ ] Excepciones explicitas, no codigos de retorno
- [ ] Pydantic v2 para modelos en boundaries del sistema

---

## Apendice A: Diagrama de Gantt estimado

```
Semana 1          Semana 2          Semana 3          Semana 4
├── F1 (3-4h) ──▶ │                 │                 │
│                 ├── F2 (5-7h) ───▶│                 │
│                 ├── F3 (4-6h) ───▶│                 │
│                 │                 ├── F4 (3-4h) ───▶│
│                 │                 │                 ├── F5 (4-5h) ──▶
│                 │                 │                 ├── F6 (2-3h) ──▶
```

F2 y F3 son paralelizables (ejecutores distintos pueden tomarlos simultaneamente).

## Apendice B: Comandos de verificacion rapida

```bash
# Por fase
F1: pytest user_request/tests/test_contracts.py -v && ruff check user_request/contracts/
F2: pytest user_request/tests/test_nlu_pipeline.py -v && ruff check user_request/nlu/
F3: pytest user_request/tests/test_nlg_pipeline.py -v && ruff check user_request/nlg/
F4: ./compiler-bot/agentic --prompt "crea modulo test" --dry-run
F5: curl -X POST http://localhost:8765/api/chat -d '{"text":"crea modulo pagos"}'
F6: pytest compiler-bot/agentic_pipeline/tests/ -v --tb=short && ruff check .

# Global
ruff check user_request/ && mypy --strict user_request/ && pytest user_request/tests/ -v
```
