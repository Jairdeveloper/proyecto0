---
id: 186
area: dev
type: prop
module: user_request_layer
version: 1.0
status: DRAFT
tags:
  - proposal
  - architecture
  - user-request
  - nlu
  - nlg
  - modularization
  - nlp
  - platform
summary: "Propuesta de capa 'User Request' como interfaz agnostica de entrada/salida para el sistema RECPL y futura Code Assistant Agentic Platform. Define NLU pipeline de entrada, NLG pipeline de salida, y la modularizacion del modulo nlp/ actual."
keywords:
  - user-request
  - nlu
  - nlg
  - modularization
  - intent-classification
  - ner
  - slot-filling
  - ambiguity
  - response-generation
  - architecture
  - platform
  - code-assistant
changelog:
  - version: 1.0
    date: 2026-06-21
    author: workflow-agent
    description: Creacion de propuesta de capa User Request con NLU/NLG
---

# Propuesta: User Request Layer — NLU, NLG y modularizacion del sistema

> **Version del documento:** 1.0
> **Fecha:** 2026-06-21
> **Pre-requisito:** Cambio de concepto a IR completado (v2.9.0), propuesta `179_PROP_DEV_CODE_ASSISTANT_AGENTIC_PLATFORM_1_0_DRAFT.md`
> **Estado:** PROPUESTA

---

## Tabla de Contenidos

1. [Executive Summary](#1-executive-summary)
2. [Estado actual del modulo nlp/](#2-estado-actual-del-modulo-nlp)
3. [Problemas identificados](#3-problemas-identificados)
4. [Vision: User Request Layer](#4-vision-user-request-layer)
5. [NLU Pipeline (entrada)](#5-nlu-pipeline-entrada)
6. [NLG Pipeline (salida)](#6-nlg-pipeline-salida)
7. [Estrategia de modularizacion](#7-estrategia-de-modularizacion)
8. [Integracion con el sistema actual](#8-integracion-con-el-sistema-actual)
9. [Plan de migracion](#9-plan-de-migracion)
10. [Riesgos y mitigacion](#10-riesgos-y-mitigacion)
11. [Conclusion](#11-conclusion)

---

## 1. Executive Summary

### Que propone este documento

Una capa **User Request** que abstrae toda interaccion usuario/sistema detras de una interfaz limpia,
independiente del canal (CLI, WebUI, API REST, plugin de editor, agente externo).
La capa se compone de dos pipelines simetricos:

```
User Input ──▶ [NLU Pipeline] ──▶ RequestObject ──▶ (sistema)
                                                      │
User Output ◀── [NLG Pipeline] ◀── ResponseObject ◀──┘
```

- **NLU (Natural Language Understanding):** transforma texto libre del usuario en un
  `RequestObject` estructurado con intencion, entidades, slots, contexto y ambiguedades.
- **NLG (Natural Language Generation):** transforma la salida del sistema (`ResponseObject`)
  en texto legible para el usuario, adaptado al canal y al estado de la conversacion.

El modulo `nlp/` actual se refactoriza para ser la implementacion concreta del pipeline NLU,
extrayendo responsabilidades mezcladas (perception_unit mezcla rule-based + semantic embedding).

### Relacion con otras propuestas

| Propuesta | Relacion |
|---|---|
| `179_PROP_DEV_CODE_ASSISTANT_AGENTIC_PLATFORM` | Esta capa User Request es el **primer ladrillo** de esa arquitectura. Sin una interfaz agnostica no se puede construir el Intent Router que ahi se describe. |
| `183_PROP_DEV_CONCEPT_SHIFT` | El cambio de concepto a IR hace que la capa de salida (NLG) sea mas importante: el IR es maquina-legible, el NLG lo humaniza. |

---

## 2. Estado actual del modulo nlp/

### 2.1 Inventario de archivos

| Archivo | Lineas | Proposito | Depende de |
|---|---|---|---|
| `nlp/__init__.py` | 29 | Re-exporta componentes publicos | Todo el modulo |
| `nlp/intent_classifier.py` | 108 | Clasificador rule-based con regex | `enriched_input.py` |
| `nlp/ner_extractor.py` | 121 | Extraccion de entidades (modulos, techs, requisitos) | `enriched_input.py` |
| `nlp/slot_filler.py` | 56 | Mapea intent+entidades a slots estructurados | `enriched_input.py` |
| `nlp/ambiguity_detector.py` | 73 | Detecta ambiguedades en la entrada | `enriched_input.py` |
| `nlp/enriched_input.py` | 54 | Modelos Pydantic (IntentResult, Entities, Slots, etc.) | Pydantic |
| `nodes/perception_unit.py` | 191 | PipelineStage que orquesta NLP completo + semantic | `nlp/*`, sentence-transformers |
| `nodes/intent_stage.py` | 3 | Backward compat (re-export) | `perception_unit.py` |

### 2.2 Flujo actual de procesamiento de entrada

```
texto_bruto
    │
    ▼
IntentClassifier.classify()       ← rule-based (regex), taxonomia de 7 intents
    │
    ▼
NERExtractor.extract()            ← regex, whitelist techs, stop words
    │
    ▼
SlotFiller.fill()                 ← mapea intent+entities a slots (accion, tipo, nombre, tech)
    │
    ▼
AmbiguityDetector.detect()        ← detecta: UNKNOWN, baja confianza, multi-intencion, slots faltantes
    │
    ▼
SentenceTransformerClassifier     ← enrichment semantico (opcional, offline=False)
    │
    ▼
EnrichedInput (Pydantic)          ← modelo unificado de entrada enriquecida
```

### 2.3 Flujo actual de salida

No existe un pipeline NLG. La salida es JSON crudo del pipeline:

```
resultado del pipeline (dict) ──▶ json.dumps() ──▶ stdout
```

El usuario recibe JSON tecnico. No hay adaptacion al canal, al contexto
de la conversacion, ni al nivel de detalle deseado.

---

## 3. Problemas identificados

### 3.1 Dos sistemas de clasificacion compitiendo

| Sistema | Ubicacion | Tecnica | Intents |
|---|---|---|---|
| Rule-based | `nlp/intent_classifier.py` | Regex | SCAFFOLD, QUERY, MODIFY, DELETE, EXPLORE, CONFIGURE, CLARIFY |
| Semantico | `perception_unit.py` (SentenceTransformer) | Embeddings cos-sim | CREATE, READ, UPDATE, DELETE, EXPLAIN |

**Problema:** `IntentClassifier` produce `SCAFFOLD`, el semantico produce `CREATE`.
El `SlotFiller` solo entiende la taxonomia rule-based (`SCAFFOLD`).
Si el semantico gana (porque tiene mayor confianza), los slots no se llenan correctamente.

### 3.2 Acoplamiento PerceptionUnit ↔ nlp/

`PerceptionUnit` (un PipelineStage) instancia directamente `IntentClassifier`,
`NERExtractor`, `SlotFiller`, `AmbiguityDetector`. No hay interfaz abstracta.
No se puede:
- Usar el NLP fuera del pipeline (ej. en el dashboard, en una API)
- Intercambiar implementaciones (ej. rule-based → LLM-based → hibrido)
- Testear el NLP aislado del Stage

### 3.3 Sin pipeline de salida (NLG)

El sistema produce JSON. Para un usuario humano, no hay:
- Resumen en lenguaje natural de lo que se hizo
- Explicacion de errores en lenguaje natural
- Adaptacion del tono/estilo al canal (CLI escueto, WebUI conversacional, API verboso)
- Soporte multilingue
- Historial de conversacion formateado

### 3.4 Modelos de datos fragmentados

- `nlp/enriched_input.py` define modelos Pydantic para NLP
- `state_models.py` define modelos para el StateGraph
- `generators/enriched_input.py` tiene sus propios modelos
- No hay herencia ni reutilizacion

### 3.5 Taxonomia de intenciones no unificada

| Donde aparece | Valores |
|---|---|
| `intent_classifier.py` | SCAFFOLD, QUERY, MODIFY, DELETE, EXPLORE, CONFIGURE, CLARIFY |
| `perception_unit.py` | CREATE, READ, UPDATE, DELETE, EXPLAIN |
| `slot_filler.py` | SCAFFOLD, MODIFY, DELETE, QUERY, EXPLORE, CONFIGURE |
| `llm_classifier.sh` (shell) | scaffold_module, scaffold_entity |
| `grammars/` (parser Lark) | CREATE, DELETE, UPDATE, READ |

---

## 4. Vision: User Request Layer

### 4.1 Arquitectura general

```
┌──────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACES                              │
│   ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐      │
│   │  CLI   │  │ WebUI  │  │  API   │  │ Editor │  │ Agent  │      │
│   └────┬───┘  └────┬───┘  └────┬───┘  └────┬───┘  └────┬───┘      │
│        │           │           │           │           │          │
│        └───────────┴───────────┴───────────┴───────────┘          │
│                          │  Request                                │
│                          ▼                                         │
├──────────────────────────────────────────────────────────────────────┤
│                     USER REQUEST LAYER                              │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    NLU Pipeline                             │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │   │
│  │  │ Normalize│→│ Classify │→│  Extract  │→│Resolve   │   │   │
│  │  │ (texto)  │  │ (intent) │  │(entities)│  │(ambig.)  │   │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │   │
│  │                                     │                      │   │
│  │                                     ▼                      │   │
│  │                              ┌──────────┐                 │   │
│  │                              │ Enrich   │                 │   │
│  │                              │ (semantic│                 │   │
│  │                              │ /LLM)    │                 │   │
│  │                              └──────────┘                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                          │  RequestObject                          │
│                          ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    System Boundary                          │   │
│  │  (Pipeline / Agents / SDLC / etc.)                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                          │  ResponseObject                         │
│                          ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    NLG Pipeline                             │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │   │
│  │  │  Format  │→│ Translate│→│  Adapt   │→│  Output  │   │   │
│  │  │ (content)│  │ (lang)   │  │ (channel)│  │ (string) │   │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                          │  Response                               │
│                          ▼                                         │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.2 RequestObject — contrato de entrada

Un objeto Pydantic inmutable que representa la intencion del usuario ya procesada:

```python
class RequestObject(BaseModel):
    raw: str                                    # texto original
    normalized: str                             # texto normalizado
    intent: IntentResult                        # intencion primaria + secundaria + scores
    entities: Entities                          # entidades extraidas
    slots: Slots                                # slots rellenos
    ambiguity: AmbiguityResult                  # ambiguedades detectadas
    channel: RequestChannel                     # enum: CLI, WEBUI, API, EDITOR, AGENT
    context: RequestContext                     # historial, sesion, defaults
    metadata: dict                              # timestamp, version, flags
```

### 4.3 ResponseObject — contrato de salida

```python
class ResponseObject(BaseModel):
    success: bool                               # estado global
    data: dict | None                           # datos estructurados (IR, comandos, etc.)
    message: str | None                         # mensaje en lenguaje natural
    error: str | None                           # mensaje de error human-readable
    suggestions: list[str]                      # sugerencias de seguimiento
    channel: RequestChannel                     # canal destino
    metadata: dict                              # timestamp, duracion, stages
```

### 4.4 RequestChannel — enum de canales

```python
class RequestChannel(str, Enum):
    CLI = "cli"           # terminal, escueto, sin adornos
    WEBUI = "webui"       # navegador, rich text, enlaces
    API = "api"           # JSON puro, sin mensajes humanos
    EDITOR = "editor"     # plugin de IDE, respuestas cortas
    AGENT = "agent"       # otro agente, formato optimizado para parsing
```

---

## 5. NLU Pipeline (entrada)

### 5.1 Arquitectura propuesta

Estrategia **multinivel** con fallback: intentos de mayor a menor costo.

```
                    texto_bruto
                         │
                    ┌────▼────┐
                    │Normalizer│
                    │(unicode, │
                    │lowercase,│
                    │punct)    │
                    └────┬────┘
                         │ normalized_text
                         │
              ┌──────────▼──────────┐
              │  ClassifierManager  │
              │                     │
              │  ┌─────────────────┐│
              │  │ 1. LLM Classif.││  ← si hay LLM y no offline
              │  │    (gpt-4o,    ││
              │  │     Claude)    ││
              │  └────────┬────────┘│
              │           │ fallback│
              │  ┌─────────────────┐│
              │  │2. Semantic Class││  ← sentence-transformers
              │  │  (embeddings)   ││
              │  └────────┬────────┘│
              │           │ fallback│
              │  ┌─────────────────┐│
              │  │3. Rule-based    ││  ← regex (actual)
              │  │  (TAXONOMY)     ││
              │  └────────┬────────┘│
              │           │         │
              └───────────┼─────────┘
                         │ intent
                         │
              ┌──────────▼──────────┐
              │  EntityExtractor    │
              │  manager (misma     │
              │  estrategia de      │
              │  fallback)          │
              └──────────┬──────────┘
                         │ entities
                         │
              ┌──────────▼──────────┐
              │  SlotFiller v2     │
              │  (taxonomia unica)  │
              └──────────┬──────────┘
                         │ slots
                         │
              ┌──────────▼──────────┐
              │ AmbiguityResolver   │
              │ (detecta + sugiere  │
              │  preguntas)         │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │   Enricher          │
              │ (semantic / contexto│
              │  / historial)       │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │ RequestObject       │
              │ (output unificado)  │
              └─────────────────────┘
```

### 5.2 Normalizer

```python
class Normalizer:
    """Limpieza y normalizacion del texto de entrada."""

    def normalize(self, raw: str) -> str:
        ...
```

Operaciones:
- Unicode NFKC normalization
- Lowercase
- Colapso de espacios multiples
- Eliminacion de puntuacion redundante
- Deteccion de idioma (opcional)
- Expansion de abreviaciones (opcional)

### 5.3 ClassifierManager

Reemplaza el actual `IntentClassifier` concreto por una cadena de clasificadores
(Chain of Responsibility) que intenta en orden decreciente de capacidad:

```python
class ClassifierManager:
    def __init__(self, classifiers: list[IntentClassifier]):
        self._chain = classifiers

    def classify(self, text: str) -> IntentResult:
        for classifier in self._chain:
            result = classifier.classify(text)
            if result.confidence >= classifier.min_confidence:
                return result
        return self._chain[-1].classify(text)  # ultimo recurso
```

Cada clasificador implementa una interfaz comun:

```python
class IntentClassifier(ABC):
    min_confidence: float

    @abstractmethod
    def classify(self, text: str) -> IntentResult: ...
```

Implementaciones concretas:
- `LLMIntentClassifier` — via LLM call con system prompt + tool schema
- `SemanticIntentClassifier` — SentenceTransformer embeddings (actual)
- `RuleIntentClassifier` — regex patterns (actual `IntentClassifier`)

### 5.4 EntityExtractorManager

Misma estrategia de cadena que ClassifierManager:

```python
class EntityExtractor(ABC):
    min_confidence: float

    @abstractmethod
    def extract(self, text: str) -> Entities: ...
```

Implementaciones:
- `LLMEntityExtractor` — via LLM con schema de entidades
- `RuleEntityExtractor` — regex actual (`NERExtractor`)
- `SpacyEntityExtractor` — modelo spaCy (N2.1a existente en `spacy_processor.py`)

### 5.5 SlotFiller v2

Unificado con una sola taxonomia de intenciones. El slot filler actual
solo entiende `SCAFFOLD`. La version propuesta entiende la taxonomia unificada:

```python
UNIFIED_TAXONOMY = {
    "CREATE": {
        "aliases": ["SCAFFOLD", "GENERATE", "NEW"],
        "required_slots": ["accion", "tipo", "nombre"],
        "optional_slots": ["tech", "atributos", "dominio"],
    },
    "READ": {
        "aliases": ["QUERY", "EXPLORE", "GET"],
        "required_slots": ["accion", "objetivo"],
        "optional_slots": ["filtro", "limite"],
    },
    "UPDATE": {
        "aliases": ["MODIFY", "EDIT", "CHANGE"],
        "required_slots": ["accion", "nombre", "cambio"],
        "optional_slots": ["valor"],
    },
    "DELETE": {
        "aliases": ["REMOVE"],
        "required_slots": ["accion", "nombre"],
        "optional_slots": [],
    },
    "EXPLAIN": {
        "aliases": ["QUERY", "HELP"],
        "required_slots": ["accion", "topico"],
        "optional_slots": ["profundidad"],
    },
    "CONFIGURE": {
        "aliases": ["SET", "CONFIG"],
        "required_slots": ["parametro", "valor"],
        "optional_slots": [],
    },
}
```

### 5.6 AmbiguityResolver

Extension del actual `AmbiguityDetector`. Anade:

- Preguntas generativas: si falta un slot, genera una pregunta en lenguaje natural
- Desambiguacion interactiva: soporta `--dialog` mode con preguntas/respuestas
- Sugerencias: basadas en contexto e historial

```python
class AmbiguityResolver:
    def resolve(self, request: RequestObject) -> RequestObject:
        ...

    def generate_questions(self, request: RequestObject) -> list[str]:
        """Genera preguntas en lenguaje natural para slots faltantes."""
        ...
```

### 5.7 Enricher

Anade informacion contextual al RequestObject:

- Historial de la sesion (dialogo multi-turno)
- Defaults del usuario (tech preferida, output dir)
- Entidades de sesiones anteriores (resolucion de pronombres "lo", "eso")
- Estado del sistema (modo online/offline, LLM disponible)

Actualmente esto esta disperso en `ContextState` y `perception_unit.py`.
El Enricher lo centraliza.

---

## 6. NLG Pipeline (salida)

### 6.1 Ausencia actual

Hoy: `json.dumps(result, indent=2, default=str)` en `agentic:183`.
El usuario recibe JSON tecnico del pipeline.

### 6.2 Arquitectura propuesta

```
ResponseObject (del sistema)
    │
    ▼
┌──────────────────────────────────────────────────┐
│                 NLG Pipeline                     │
│                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │ Formatter│──▶│ Translator│──▶│  Adapter │    │
│  │(content) │   │ (lang)    │   │ (channel)│    │
│  └──────────┘   └──────────┘   └──────────┘    │
│       │              │              │           │
│       ▼              ▼              ▼           │
│  Markdown/      traduccion      CLI: texto     │
│  JSON/texto     multi-lang      WebUI: HTML    │
│  segun tipo                      API: JSON     │
│                                  Editor: snippet│
│                                  Agent: dict    │
└──────────────────────────────────────────────────┘
    │
    ▼
string (segun canal)
```

### 6.3 Formatter

Transforma `ResponseObject` en contenido estructurado segun el tipo:

```python
class NLGFormatter(ABC):
    @abstractmethod
    def format(self, response: ResponseObject) -> str: ...

class SuccessFormatter(NLGFormatter):
    """'Creado modulo pagos en NestJS. Archivos: controller, service...'"""

class ErrorFormatter(NLGFormatter):
    """'No se pudo crear el modulo: el nombre ya existe.'"""

class IRFormatter(NLGFormatter):
    """Muestra el IR de forma legible (no JSON crudo)."""

class MetricFormatter(NLGFormatter):
    """'Pipeline: 8 stages, 0 errores, 0.255s total.'"""
```

### 6.4 Translator

Capa de internacionalizacion. Inicialmente soporta espanol (default) e ingles.

```python
class NLGTranslator:
    def translate(self, text: str, target_lang: str) -> str:
        ...
```

Estrategia: template-based para mensajes conocidos, LLM-based para mensajes
generativos (solo si hay LLM disponible).

### 6.5 ChannelAdapter

Adapta el contenido al canal destino:

```python
class ChannelAdapter(ABC):
    @abstractmethod
    def adapt(self, content: str, response: ResponseObject) -> str: ...

class CLIAdapter(ChannelAdapter):
    """Texto plano, max 80 cols, sin adornos."""

class WebUIAdapter(ChannelAdapter):
    """HTML fragments o JSON enriquecido."""

class APIAdapter(ChannelAdapter):
    """JSON puro, mensajes en message field."""

class EditorAdapter(ChannelAdapter):
    """Snippets de codigo, mensajes cortos."""

class AgentAdapter(ChannelAdapter):
    """Dict estructurado para consumo por otros agentes."""
```

---

## 7. Estrategia de modularizacion

### 7.1 Estructura propuesta de directorios

```
user_request/                       # nuevo paquete raiz
├── __init__.py
├── contracts/                      # contratos compartidos (antes nlp/enriched_input.py)
│   ├── __init__.py
│   ├── request.py                  # RequestObject, RequestChannel, RequestContext
│   ├── response.py                 # ResponseObject
│   └── enums.py                    # IntentType, Channel, Language
│
├── nlu/                            # Natural Language Understanding
│   ├── __init__.py
│   ├── pipeline.py                 # NLUPipeline (orquestador)
│   ├── normalizer.py               # Normalizer
│   ├── classifiers/                # clasificadores de intencion
│   │   ├── __init__.py
│   │   ├── base.py                 # IntentClassifier ABC
│   │   ├── rule.py                 # RuleIntentClassifier (desde nlp/intent_classifier.py)
│   │   ├── semantic.py             # SemanticIntentClassifier (desde SentenceTransformer)
│   │   └── llm.py                  # LLMIntentClassifier (nuevo)
│   ├── extractors/                 # extractores de entidades
│   │   ├── __init__.py
│   │   ├── base.py                 # EntityExtractor ABC
│   │   ├── rule.py                 # RuleEntityExtractor (desde nlp/ner_extractor.py)
│   │   ├── spacy.py                # SpacyEntityExtractor (desde spacy_processor.py)
│   │   └── llm.py                  # LLMEntityExtractor (nuevo)
│   ├── slot_filler.py              # SlotFiller v2 (taxonomia unificada)
│   ├── ambiguity.py                # AmbiguityResolver
│   └── enricher.py                 # Enricher (contexto, historial, defaults)
│
├── nlg/                            # Natural Language Generation
│   ├── __init__.py
│   ├── pipeline.py                 # NLGPipeline (orquestador)
│   ├── formatters/                 # formateadores de contenido
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── success.py
│   │   ├── error.py
│   │   ├── ir_display.py
│   │   └── metrics.py
│   ├── translator.py               # NLGTranslator (i18n)
│   └── adapters/                   # adaptadores de canal
│       ├── __init__.py
│       ├── base.py
│       ├── cli.py
│       ├── webui.py
│       ├── api.py
│       ├── editor.py
│       └── agent.py
│
└── tests/
    ├── test_nlu_pipeline.py
    ├── test_nlg_pipeline.py
    ├── test_classifiers.py
    ├── test_extractors.py
    ├── test_slot_filler.py
    ├── test_ambiguity.py
    └── test_formatters.py
```

### 7.2 Migracion del codigo existente

| Archivo actual | Migra a | Accion |
|---|---|---|
| `nlp/intent_classifier.py` | `user_request/nlu/classifiers/rule.py` | Refactorizar a herencia de base.py |
| `nlp/ner_extractor.py` | `user_request/nlu/extractors/rule.py` | Igual |
| `nlp/slot_filler.py` | `user_request/nlu/slot_filler.py` | Reescribir con taxonomia unificada |
| `nlp/ambiguity_detector.py` | `user_request/nlu/ambiguity.py` | Extender a AmbiguityResolver |
| `nlp/enriched_input.py` | `user_request/contracts/` | Dividir en request.py + enums.py |
| `nodes/perception_unit.py` | `user_request/nlu/pipeline.py` | Extraer logica de orquestacion |
| `spacy_processor.py` | `user_request/nlu/extractors/spacy.py` | Mover e integrar |

### 7.3 Backward compatibility

El modulo `nlp/` actual se mantiene como re-exportador transicional:

```python
# nlp/__init__.py (v2 transicional)
from user_request.nlu.classifiers.rule import RuleIntentClassifier as IntentClassifier
from user_request.nlu.extractors.rule import RuleEntityExtractor as NERExtractor
from user_request.contracts.request import EnrichedInput, IntentResult, Entities
# ...
```

---

## 8. Integracion con el sistema actual

### 8.1 En el pipeline (modo actual)

```
CLI ──▶ UserRequestLayer ──▶ PipelineOrchestrator ──▶ ResponseObject ──▶ UserRequestLayer ──▶ stdout
              │                                                              │
              ▼                                                              ▼
         RequestObject                                                  NLG pipeline
         (intent, entities, slots)                                      (formateo + canal)
```

La integracion minima:

```python
# En agentic
from user_request import UserRequestLayer

layer = UserRequestLayer()
request = layer.nlu.process(prompt)        # RequestObject
result = await orchestrator.run(request)    # el pipeline recibe RequestObject
response = layer.nlg.process(result)        # ResponseObject formateado
print(response.message or json.dumps(response.data))
```

### 8.2 En el sistema multi-agente (futuro, doc 179)

```
UserRequestLayer
    │
    ▼  RequestObject
Intent Router (doc 179)
    │
    ├──▶ Planning Agent
    ├──▶ Repository Intelligence
    ├──▶ Coding Agent
    ...
    │
    ▼  ResponseObject
UserRequestLayer (NLG)
    │
    ▼
Output por canal
```

### 8.3 Interfaz UserRequestLayer

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

---

## 9. Plan de migracion

### Fase 1: Contratos y taxonomia unificada

**Objetivo:** Definir los contratos compartidos y unificar la taxonomia de intenciones.

- [ ] Crear `user_request/contracts/` con RequestObject, ResponseObject, enums
- [ ] Definir `IntentType` enum unificado (CREATE, READ, UPDATE, DELETE, EXPLAIN, CONFIGURE)
- [ ] Reescribir `SlotFiller` con taxonomia unificada
- [ ] Mantener backward compat via `nlp/__init__.py`
- [ ] Tests de contratos

**Artefactos:** `user_request/contracts/`, `user_request/nlu/slot_filler.py`

### Fase 2: NLU Pipeline

**Objetivo:** Refactorizar el NLP actual en pipeline modular con estrategia de fallback.

- [ ] Migrar `intent_classifier.py` → `classifiers/rule.py` (herencia de base.py)
- [ ] Migrar `ner_extractor.py` → `extractors/rule.py`
- [ ] Migrar `ambiguity_detector.py` → `ambiguity.py` (extender con preguntas)
- [ ] Crear `NLUPipeline` como orquestador
- [ ] Integrar semantic classifier como segunda capa
- [ ] Integrar spacy_processor como extractor opcional
- [ ] Tests por componente y de integracion

**Artefactos:** `user_request/nlu/`

### Fase 3: NLG Pipeline

**Objetivo:** Crear el pipeline de generacion de respuesta.

- [ ] Crear `NLGPipeline` con formatters, translator, adapters
- [ ] Formatters: success, error, ir_display, metrics
- [ ] Adapter CLI (texto plano, compacto)
- [ ] Adapter JSON (para API/agent)
- [ ] Translator template-based (es ↔ en)
- [ ] Tests

**Artefactos:** `user_request/nlg/`

### Fase 4: Integracion en CLI

**Objetivo:** Conectar la capa UserRequest con el entrypoint `agentic`.

- [ ] Modificar `agentic` para usar `UserRequestLayer`
- [ ] Output canal CLI: mensajes legibles + JSON segun flag
- [ ] Flag `--output-format text|json`
- [ ] Modo dialogo interactivo via AmbiguityResolver
- [ ] Tests end-to-end

### Fase 5: Canales adicionales

**Objetivo:** Soportar WebUI y API como canales.

- [ ] Adapter WebUI (respuestas HTML o JSON enriquecido)
- [ ] Adapter API (JSON puro con field message)
- [ ] Endpoint HTTP `/api/nlu` (procesar texto, devolver RequestObject)
- [ ] Endpoint HTTP `/api/chat` (NLU → pipeline → NLG)

### Fase 6: Limpieza

- [ ] Deprecar `nlp/` como re-exportador
- [ ] Remover `intent_stage.py` backward compat
- [ ] Actualizar imports en todo el codebase
- [ ] Actualizar documentacion

---

## 10. Riesgos y mitigacion

| Riesgo | Impacto | Probabilidad | Mitigacion |
|---|---|---|---|
| Taxonomia unificada rompe clasificadores existentes | Alto | Media | Mapeo de aliases (CREATE←SCAFFOLD), tests de regresion |
| NLG aumenta latencia de salida | Medio | Baja | NLG pipeline sync, formatters lightweight, translator template-first |
| Duplicacion temporal nlp/ + user_request/ | Bajo | Alta | Aceptado: fase transicional de 1-2 sprints |
| Dependencia de LLM en clasificacion aumenta costos | Medio | Media | Fallback chain: LLM → semantic → rule-based. Offline mode siempre rule-based |
| SpacyProcessor duplica funcionalidad de NERExtractor | Bajo | Alta | Unificar en Fase 2: SpacyEntityExtractor es un extractor mas en la cadena |

---

## 11. Conclusion

La capa User Request es el primer paso arquitectonico hacia la vision de
"Code Assistant Agentic Platform" (doc 179). Sin ella:

- Cada nuevo canal (WebUI, API, Editor) requiere duplicar logica de parsing
- El sistema solo habla JSON tecnico, no lenguaje natural
- La taxonomia de intenciones sigue fragmentada en 4 lugares distintos
- No hay manera de intercambiar implementaciones NLP segun contexto

Con ella:

- Cualquier interfaz (CLI, WebUI, API REST, plugin VSCode, agente externo)
  produce el mismo `RequestObject` y consume el mismo `ResponseObject`
- El NLG humaniza la salida: el usuario recibe mensajes, no JSON crudo
- La arquitectura de clasificacion multinivel (LLM → semantic → rule-based)
  maximiza precision donde hay recursos y minimiza costos donde no los hay
- El modulo `nlp/` actual se refactoriza sin perder backward compat

**Proximo paso:** Fase 1 — definir contratos y taxonomia unificada en una
sesion de implementacion.
