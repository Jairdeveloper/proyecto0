---
id: 189
area: dev
type: rep
module: user_request_layer_f2
version: 1.0
status: DRAFT
tags:
  - report
  - implementation
  - user-request
  - phase-2
  - nlu
  - pipeline
  - classifiers
  - extractors
summary: "Reporte de implementacion de la Fase 2 del plan 187: NLU Pipeline completo con normalizer, classifier chain (semantic→rule), extractor chain (spacy→rule), AmbiguityResolver con preguntas, Enricher, y 93 tests."
keywords:
  - implementation-report
  - nlu
  - normalizer
  - intent-classifier
  - entity-extractor
  - ambiguity-resolution
  - enricher
  - pipeline
changelog:
  - version: 1.0
    date: 2026-06-22
    author: sisyphus
    description: Reporte de implementacion Fase 2 del User Request Layer
---

# Reporte de Implementacion — Fase 2: NLU Pipeline

> **Documento fuente:** `187_PLAN_DEV_USER_REQUEST_LAYER_EXECUTION_1_0_DRAFT.md` §4
> **Version del reporte:** 1.0
> **Fecha:** 2026-06-22
> **Estado:** COMPLETADO

---

## Resumen

La Fase 2 implementa el pipeline NLU completo: desde texto crudo del usuario
hasta un `RequestObject` estructurado con intencion, entidades, slots y
deteccion de ambiguedades. Todo sobre la base de los contratos de Fase 1.

**Componentes creados:** 11 archivos nuevos (9 componentes + 4 suites de test)
**Tests:** 93 totales (53 nuevos en Fase 2 + 40 de Fase 1)
**Regresion:** 0 — todos los tests legacy NLP siguen pasando

---

## 1. Arquitectura del Pipeline

```
texto_bruto
    │
    ▼
┌──────────────────────────────────────────────┐
│              NLUPipeline                      │
│                                                │
│  ┌──────────────┐                              │
│  │  Normalizer   │  Unicode NFKC, lowercase,   │
│  │               │  colapso espacios, strip    │
│  └──────┬───────┘  puntuacion                  │
│         │ normalized_text                      │
│         ▼                                      │
│  ┌──────────────────┐                          │
│  │ ClassifierManager │  Chain of Responsibility │
│  │                   │  semantic → rule         │
│  │  ┌──────────────┐ │                          │
│  │  │ Semantic     │ │  SentenceTransformer     │
│  │  │ (conf≥0.7)   │ │  (si disponible)         │
│  │  └──────┬───────┘ │                          │
│  │         │ fallback │                          │
│  │  ┌──────▼───────┐ │                          │
│  │  │ Rule         │ │  Regex patterns           │
│  │  │ (conf≥0.6)   │ │  + alias mapping          │
│  │  └──────────────┘ │                          │
│  └─────────┬─────────┘                          │
│            │ intent                              │
│            ▼                                     │
│  ┌──────────────────┐                            │
│  │EntityExtractorMgr │  Chain of Responsibility  │
│  │                   │  spacy → rule              │
│  │  ┌──────────────┐ │  + dedup por nombre       │
│  │  │ Spacy        │ │  (si modelo instalado)     │
│  │  └──────┬───────┘ │                          │
│  │         │ fallback │                          │
│  │  ┌──────▼───────┐ │                          │
│  │  │ Rule         │ │  Regex patterns           │
│  │  │              │ │  + whitelist techs        │
│  │  └──────────────┘ │                          │
│  └─────────┬─────────┘                          │
│            │ entities                            │
│            ▼                                     │
│  ┌──────────────────┐                            │
│  │   SlotFiller v2   │  Taxonomia unificada      │
│  │                   │  (desde Fase 1)            │
│  └─────────┬─────────┘                          │
│            │ slots                               │
│            ▼                                     │
│  ┌──────────────────┐                            │
│  │ AmbiguityResolver │  Detecta + genera         │
│  │                   │  preguntas interactivas   │
│  └─────────┬─────────┘                          │
│            │ ambiguity                           │
│            ▼                                     │
│  ┌──────────────────┐                            │
│  │    Enricher      │  Contexto sesion,          │
│  │                  │  defaults, historial       │
│  └─────────┬─────────┘                          │
│            │ RequestObject                       │
└────────────┼─────────────────────────────────────┘
             ▼
      RequestObject (completo)
```

---

## 2. Tareas ejecutadas

### T2.1 — Normalizer

**Archivo:** `user_request/nlu/normalizer.py`

Migrado desde el `NormalizationFilter` en `nodes/preprocessor.py`.

| Operacion | Descripcion |
|-----------|-------------|
| Unicode NFKC | Normaliza caracteres compuestos (ñ, ü, acentos) |
| Lowercase | Todo a minusculas |
| Strip punctuation | Elimina todo lo que no sea \w, \s o letras acentuadas |
| Collapse spaces | Multiples espacios → uno |

**Tests:** 7 casos (lowercase, espacios, puntuacion, unicode, vacio, whitespace, mixto)

### T2.2 — classifiers/base.py

**Archivo:** `user_request/nlu/classifiers/base.py`

```python
class IntentClassifier(ABC):
    min_confidence: float
    @abstractmethod
    def classify(self, text: str) -> IntentResult: ...
```

### T2.3 — RuleIntentClassifier

**Archivo:** `user_request/nlu/classifiers/rule.py`

Migrado desde `agentic_pipeline.nlp.intent_classifier.IntentClassifier`.

**Cambios clave respecto al original:**
- Retorna `IntentType` enum en lugar de string legacy
- Usa `IntentType.from_alias()` para mapear SCAFFOLD→CREATE, QUERY→READ, etc.
- Detecta intencion secundaria cuando scores son cercanos (< 0.1 diff)
- Misma taxonomia de 7 categorias (SCAFFOLD..CLARIFY) + 3 dominios

**Tests:** 10 casos (6 intenciones, dominio, vacio, clasificador, manager)

### T2.4 — SemanticIntentClassifier

**Archivo:** `user_request/nlu/classifiers/semantic.py`

Migrado desde `SentenceTransformerClassifier` en `perception_unit.py`.

**Cambios:**
- Implementa `IntentClassifier` ABC con `min_confidence = 0.7`
- Retorna `IntentType` enum (no string legacy)
- Carga lazy del modelo — no afecta import
- `is_available()` classmethod para verificar disponibilidad

**Manejador de errores:** si `sentence-transformers` no esta instalado,
`classify()` retorna `confidence=0.0` → el chain delega al rule classifier.

### T2.5 — ClassifierManager

**Archivo:** `user_request/nlu/classifiers/__init__.py`

Chain of Responsibility con orden: **semantic → rule**.

```python
class ClassifierManager:
    def classify(self, text: str) -> IntentResult:
        for classifier in self._chain:
            result = classifier.classify(text)
            if result.confidence >= classifier.min_confidence:
                return result
        return self._chain[-1].classify(text)  # fallback
```

**Decision:** Semantic primero porque ofrece mayor precision (embeddings
multilingue). Rule como fallback deterministico. LLM se agregara en fase
posterior como primer eslabon.

### T2.6 — extractors/base.py

```python
class EntityExtractor(ABC):
    min_confidence: float
    @abstractmethod
    def extract(self, text: str) -> Entities: ...
```

### T2.7 — RuleEntityExtractor

**Archivo:** `user_request/nlu/extractors/rule.py`

Migrado desde `agentic_pipeline.nlp.ner_extractor.NERExtractor`.

**Contenido identico:** patrones regex, TECH_WHITELIST (32 tecnologias),
REQUIREMENT_PATTERNS (8 patrones), STOP_WORDS.

**Tests:** 7 casos (modulo, tech, multiple tech, requisito, negacion, vacio, falso positivo)

### T2.8 — SpacyEntityExtractor

**Archivo:** `user_request/nlu/extractors/spacy.py`

Migrado desde `SpacyProcessor` en `nodes/preprocessor.py`.

**Cambios clave:**
- Implementa `EntityExtractor` ABC (antes era clase standalone)
- `extract()` retorna `Entities` en lugar de `dict`
- Filtra entidades NER por label (ORG, PRODUCT, MISC, WORK_OF_ART, EVENT)
- Carga lazy del modelo spaCy
- `is_available()` classmethod
- Fallback silencioso a `Entities()` vacio si modelo no instalado

**Tests:** No se requieren tests especificos (depende de modelo es_core_news_sm
que no esta instalado en CI). El extractor se prueba indirectamente via
`EntityExtractorManager` con dedup.

### T2.9 — AmbiguityResolver

**Archivo:** `user_request/nlu/ambiguity.py`

Extension del legacy `AmbiguityDetector` con nuevas capacidades:

| Funcionalidad | Legacy | Nueva |
|---------------|--------|-------|
| Detectar baja confianza | ✓ | ✓ |
| Detectar multi-intencion | ✓ | ✓ |
| Detectar slots faltantes | ✓ | ✓ |
| Detectar pronombres | ✓ | ✓ |
| Operar sobre RequestObject | ✗ | ✓ (resolve()) |
| Generar preguntas | ✗ | ✓ (generate_questions()) |
| Preguntas por slot | ✗ | ✓ (SLOT_QUESTIONS map) |

**Mapping de slots a preguntas:**
```python
SLOT_QUESTIONS = {
    "nombre": "Como se llama el componente?",
    "tipo": "Que tipo de componente quieres? (modulo, entidad, proyecto)",
    "tech": "En que tecnologia? (NestJS, Prisma, React...)",
    # ... 9 slots mapeados
}
```

**Tests:** 10 casos (6 deteccion + 3 generacion preguntas + 1 resolve)

### T2.10 — Enricher

**Archivo:** `user_request/nlu/enricher.py`

Centraliza informacion contextual que antes estaba dispersa entre
`ContextState` y `perception_unit.py`.

```python
class Enricher:
    def enrich(self, request, session_id="", defaults=None) -> RequestObject:
        # Anade RequestContext con session_id, defaults, channel
```

Acepta un `context_store` opcional (callable) para integracion con
sistemas externos de estado de sesion.

### T2.11 — NLUPipeline (orquestador)

**Archivo:** `user_request/nlu/pipeline.py`

```python
class NLUPipeline:
    def process(self, raw, context=None, channel=CLI, metadata=None) -> RequestObject:
        # 1. Normalizar
        # 2. Clasificar intencion (semantic → rule)
        # 3. Extraer entidades (spacy → rule)
        # 4. Rellenar slots (taxonomia unificada)
        # 5. Detectar ambiguedad + generar preguntas
        # 6. Enriquecer con contexto
        # 7. Retornar RequestObject completo
```

**Inyectable:** Todos los componentes (normalizer, classifier, extractor,
slot_filler, ambiguity, enricher) tienen defaults pero son inyectables
en el constructor.

**Tests:** 10 casos (create, tech, channel, context, metadata, query, delete, ambiguity, normalization, empty)

---

## 3. Verificacion

### 3.1 Ruff

```
$ ruff check compiler-bot/user_request/
All checks passed!
```

### 3.2 Tests nuevos (Fase 2)

| Suite | Tests | Estado |
|-------|-------|--------|
| `test_normalizer.py` | 7 | ✅ PASS |
| `test_classifiers.py` | 14 | ✅ PASS |
| `test_extractors.py` | 12 | ✅ PASS |
| `test_ambiguity.py` | 10 | ✅ PASS |
| `test_nlu_pipeline.py` | 10 | ✅ PASS |
| **Total nuevos** | **53** | **✅ PASS** |

### 3.3 Tests totales (Fase 1 + Fase 2)

```
$ pytest compiler-bot/user_request/tests/ -v
============================== 93 passed in 0.83s ==============================
```

### 3.4 Regresion legacy

```
$ pytest .../test_nlp_slots.py .../test_nlp_classifier.py .../test_nlp_ner.py .../test_nlp_ambiguity.py
============================== 25 passed ==============================
```

### 3.5 Backward compat

```python
from agentic_pipeline.nlp import IntentClassifier
# IntentClassifier ahora es RuleIntentClassifier (v2)
assert IntentClassifier.__module__ == "user_request.nlu.classifiers.rule"

# Old direct imports siguen funcionando
from agentic_pipeline.nlp.intent_classifier import IntentClassifier as Old
assert Old.__module__ == "agentic_pipeline.nlp.intent_classifier"
```

---

## 4. Artefactos producidos

### Archivos nuevos (11)

| Archivo | Lineas | Proposito |
|---------|--------|-----------|
| `user_request/nlu/normalizer.py` | 30 | Normalizacion de texto |
| `user_request/nlu/classifiers/base.py` | 23 | ABC para clasificadores |
| `user_request/nlu/classifiers/rule.py` | 115 | RuleIntentClassifier v2 |
| `user_request/nlu/classifiers/semantic.py` | 110 | SemanticIntentClassifier |
| `user_request/nlu/classifiers/__init__.py` | 55 | ClassifierManager (chain) |
| `user_request/nlu/extractors/base.py` | 23 | ABC para extractores |
| `user_request/nlu/extractors/rule.py` | 132 | RuleEntityExtractor |
| `user_request/nlu/extractors/spacy.py` | 70 | SpacyEntityExtractor |
| `user_request/nlu/extractors/__init__.py` | 88 | EntityExtractorManager (chain) |
| `user_request/nlu/ambiguity.py` | 168 | AmbiguityResolver con preguntas |
| `user_request/nlu/enricher.py` | 58 | Enriquecimiento contextual |
| `user_request/nlu/pipeline.py` | 120 | NLUPipeline orquestador |
| `user_request/tests/test_normalizer.py` | 33 | 7 tests |
| `user_request/tests/test_classifiers.py` | 90 | 14 tests |
| `user_request/tests/test_extractors.py` | 83 | 12 tests |
| `user_request/tests/test_ambiguity.py` | 151 | 10 tests |
| `user_request/tests/test_nlu_pipeline.py` | 92 | 10 tests |

### Archivos modificados (1)

| Archivo | Cambio |
|---------|--------|
| `agentic_pipeline/nlp/__init__.py` | Re-exporta `RuleIntentClassifier` como `IntentClassifier`, `RuleEntityExtractor` como `NERExtractor` |

---

## 5. Decisiones tecnicas

### 5.1 Chain of Responsibility en ambos pipelines

Tanto clasificadores como extractores usan el patron Chain of Responsibility.
El orden es **mayor capacidad primero**:
- **Classifiers:** semantic (embeddings, si disponible) → rule (regex deterministico)
- **Extractors:** spacy (NER estadistico, si disponible) → rule (regex deterministico)

Si el primer componente no alcanza su umbral de confianza, se delega al siguiente.
El ultimo componente es siempre el fallback deterministico.

### 5.2 Dedup en EntityExtractorManager

Cuando multiples extractores producen entidades, el manager:
1. Estima confianza basada en cantidad de entidades extraidas
2. Si la confianza >= min_confidence del extractor, incluye el resultado
3. Deduplica por nombre de entidad (primer extractor gana)

### 5.3 AmbiguityResolver separado del pipeline

El `AmbiguityResolver` NO esta en la cadena de extractores. Opera como una
capa separada que analiza el `RequestObject` completo (intent + entities +
slots) para detectar problemas transversales.

### 5.4 SlotFiller no se modifica

El `SlotFiller` v2 de Fase 1 se integra directamente en el pipeline sin
modificaciones. Su taxonomia unificada funciona con `IntentType` enum.

### 5.5 _ALIAS_MAP extendido con nombres canonicos

En Fase 2 se descubrio que `from_alias()` no tenia entradas para los nombres
canonicos mismos ("delete", "configure", etc.), causando que el
`RuleIntentClassifier` resolviera DELETE y CONFIGURE incorrectamente a CREATE.
Se agregaron las 6 identidades canonicas + "clarify" al `_ALIAS_MAP`.

---

## 6. Preparacion para Fase 3

La Fase 3 (NLG Pipeline) no depende de Fase 2 — solo de Fase 1 (contratos).
Ambas fases son paralelizables segun el plan original.

| Dependencia | Satisfecha |
|-------------|------------|
| `user_request/contracts/response.py` | ✅ Fase 1 |
| `user_request/contracts/enums.py` (RequestChannel) | ✅ Fase 1 |

La Fase 4 (Integracion CLI) depende de Fase 2 + Fase 3, y ahora tiene:

| Dependencia | Satisfecha |
|-------------|------------|
| `NLUPipeline.process(raw) → RequestObject` | ✅ Fase 2 |
| `AmbiguityResolver.generate_questions()` | ✅ Fase 2 |
| `SlotFiller v2` | ✅ Fase 1 |
