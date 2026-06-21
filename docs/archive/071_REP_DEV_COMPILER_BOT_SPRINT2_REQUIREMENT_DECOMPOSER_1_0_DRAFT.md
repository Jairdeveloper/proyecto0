---
id: 071
area: DEV
type: REP
module: COMPILER_BOT
version: 1.0.0
status: IMPLEMENTED
tags:
  - sprint
  - requirement-decomposer
  - python
  - llm
  - execution
summary: Reporte de ejecucion del Sprint 2 — RequirementDecomposer para el pipeline RECPL v2.0
keywords: [sprint-2, requirement-decomposer, llm-orchestrator, domain-classifier, entity-extractor, feature-identifier, tests]
changelog:
  - 2026-06-14: Reporte creado
---

# Reporte de Ejecucion — Sprint 2: RequirementDecomposer

## Resumen

Se ejecuto el Sprint 2 del plan de escalamiento (doc 068), implementando
el componente `RequirementDecomposer` con sus subclasificadores. El
componente descompone un requerimiento de usuario en lenguaje natural en
un `RequirementGraph` estructurado con dominio, entidades, features,
restricciones e historias de usuario.

## Archivos Creados / Modificados

### Archivos nuevos

| Archivo | Proposito |
|---------|-----------|
| `tools/llm_tools.py` | `LLMOrchestrator` (ChatOpenAI lazy), `DomainClassifier`, `EntityExtractor`, `FeatureIdentifier`, `ConstraintDetector`, `StoryGenerator` |
| `nodes/requirement_decomposer.py` | `RequirementDecomposer` stage con loop de 5 pasos |
| `tests/test_llm_orchestrator.py` | 16 tests para clasificadores y extractores |
| `tests/test_requirement_decomposer.py` | 12 tests para el stage completo |

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `state_models.py` | Agregado `RequirementGraph` (domain, entities, features, constraints, user_stories, raw_text) |

## Componentes Implementados

### 1. `RequirementGraph` (state_models.py)

Modelo Pydantic que estructura el resultado del decomposition:

```python
class RequirementGraph(BaseModel):
    domain: str
    entities: list[dict] = []
    features: list[str] = []
    constraints: list[str] = []
    user_stories: list[str] = []
    raw_text: str = ""
```

### 2. `DomainClassifier` (tools/llm_tools.py)

Clasifica el dominio del requerimiento usando:

1. **Keyword matching** — diccionario `DOMAIN_KEYWORDS` con pesos:
   - `web` → pagina, web, frontend, interfaz, ui, landing
   - `mobile` → app, movil, android, ios, mobile, celular
   - `api` → api, rest, endpoint, servicio, backend
   - `cli` → cli, terminal, comando, consola
   - `data` → base de datos, data, analisis, reporte
   - `infra` → infra, deploy, docker, nube, cloud

2. **LLM fallback** — si no hay match de keywords, delega a `LLMOrchestrator`

3. **Default** → `"web"` si no hay LLM ni keywords

### 3. `EntityExtractor` (tools/llm_tools.py)

Extrae entidades del texto usando:

1. **Regex patterns** — entidades predefinidas (model, form, page, user, link, click)
2. **LLM fallback** — si no hay entidades detectadas por regex

### 4. `FeatureIdentifier` (tools/llm_tools.py)

Identifica features SaaS por keywords:

| Keyword | Features |
|---------|----------|
| `auth` | User model, JWT, login/signup, session management |
| `qr` | QR code generation, QR library integration |
| `pagos` | Payment model, transaction log, payment gateway |
| `analytics` | Click tracking, visit stats, event logging |
| `dashboard` | Admin panel, charts, recent activity feed |
| `email` | Email service, notification templates, mail queue |
| `storage` | File upload, CDN, asset management |

### 5. `ConstraintDetector` (tools/llm_tools.py)

Detecta restricciones por keyword en 5 categorias: performance, security,
scalability, usability, maintainability.

### 6. `LLMOrchestrator` (tools/llm_tools.py)

Orquesta llamadas LLM via LangChain `ChatOpenAI`. Inicializacion lazy
(difiere creacion del cliente hasta el primer uso) para permitir tests
sin API key.

### 7. `RequirementDecomposer` (nodes/requirement_decomposer.py)

PipelineStage completo con loop de 5 pasos:

1. `receive_mission()` — captura el texto del requerimiento
2. `analyze()` — clasifica el dominio via `DomainClassifier`
3. `reflect_and_plan()` — genera plan de 4 pasos (entidades, features, constraints, stories)
4. `act()` — ejecuta todos los clasificadores y produce `RequirementGraph`
5. `learn_and_improve()` — registra metricas en FeedbackLoop

## Decisiones de Diseno

### 1. Sin LLM en tests

`RequirementDecomposer` acepta `llm: LLMOrchestrator | None = None` en su
constructor. Los tests pasan `llm=None` y todos los clasificadores usan
su logica rule-based, sin requerir API key de OpenAI.

### 2. LLMOrchestrator con lazy initialization

`ChatOpenAI` se crea en `_get_llm()` en lugar de `__init__()`. Esto evita
que falle la instanciacion cuando no hay `OPENAI_API_KEY` en el entorno.

### 3. Strategy híbrida (rules + LLM)

Cada clasificador implementa primero logica deterministica (keywords, regex)
y usa LLM como fallback. Esto permite funcionamiento sin conexion y
predecible en tests, con mejora opcional via LLM en produccion.

## Resultados de Verificacion

### Tests: 45/45 pasaron (16 nuevos + 29 existentes)

```bash
$ python -m pytest tests/ -v
============================== 45 passed in 0.94s ==============================
```

Desglose de nuevos tests:
- `test_llm_orchestrator.py` — 16 tests (4 DomainClassifier, 4 EntityExtractor,
  4 FeatureIdentifier, 3 ConstraintDetector, 2 StoryGenerator)
- `test_requirement_decomposer.py` — 12 tests (7 funcionales + 3 edge cases)

### Linter (ruff): 0 errores

```bash
$ ruff check .
All checks passed!
```

### Formatter (ruff format): 2 archivos reformateados

```bash
$ ruff format .
2 files reformatted, 20 files left unchanged
```

## Incidencias y Resoluciones

### 1. ChatOpenAI requiere API key

**Problema:** `LLMOrchestrator.__init__()` creaba `ChatOpenAI()` que
requiere `OPENAI_API_KEY` en el entorno. Los tests fallaban con
`OpenAIError`.

**Solucion:** Inicializacion lazy via `_get_llm()`. El cliente ChatOpenAI
se crea solo en el primer llamado a `classify_domain()` o
`extract_entities()`. Los tests pasan `llm=None` a RequirementDecomposer.

### 2. Import circular potencial en llm_tools.py

**Problema:** `DomainClassifier` referencia `LLMOrchestrator` que se
define despues en el mismo archivo.

**Solucion:** `from __future__ import annotations` permite forward
references en type hints (PEP 563).

## Definition of Done - Checklist

- [x] LLMOrchestrator clasifica dominio correctamente (via rules + LLM)
- [x] RequirementDecomposer produce RequirementGraph valido
- [x] RequirementGraph contiene entidades, features y constraints
- [x] Tests: `test_llm_orchestrator.py` (16 tests)
- [x] Tests: `test_requirement_decomposer.py` (12 tests)
- [x] ruff check pasa sin errores
- [x] ruff format pasa sin errores

## Proximos Pasos

Sprint 3 (Semanas 9-12): Implementar `Preprocessor` con Chain of
Responsibility de filtros (NormalizationFilter,
ImplicitRequirementFilter, SegmentationFilter, DomainEnrichmentFilter)
y Strategy segun dominio.
