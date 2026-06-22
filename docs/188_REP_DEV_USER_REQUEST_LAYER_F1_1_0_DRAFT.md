---
id: 188
area: dev
type: rep
module: user_request_layer_f1
version: 1.0
status: DRAFT
tags:
  - report
  - implementation
  - user-request
  - phase-1
  - contracts
  - taxonomy
  - slot-filler
summary: "Reporte de implementacion de la Fase 1 del plan 187: contratos Pydantic, taxonomia unificada de intenciones, SlotFiller v2, backward compat y 40 tests."
keywords:
  - implementation-report
  - contracts
  - pydantic
  - taxonomy
  - enums
  - slot-filler
  - backward-compat
  - tests
changelog:
  - version: 1.0
    date: 2026-06-22
    author: sisyphus
    description: Reporte de implementacion Fase 1 del User Request Layer
---

# Reporte de Implementacion — Fase 1: Contratos y taxonomia unificada

> **Documento fuente:** `187_PLAN_DEV_USER_REQUEST_LAYER_EXECUTION_1_0_DRAFT.md` §3
> **Version del reporte:** 1.0
> **Fecha:** 2026-06-22
> **Estado:** COMPLETADO

---

## Resumen

La Fase 1 establece los contratos compartidos (Pydantic) y la taxonomia unificada
de intenciones que serviran como base para todas las fases siguientes del
User Request Layer.

**Componentes creados:**
- Paquete `user_request/` con 12 archivos nuevos
- Taxonomia unificada con 6 intenciones canonicas + 13 alias legacy
- SlotFiller v2 con soporte de taxonomia unificada
- Backward compat via `agentic_pipeline.nlp.__init__`
- 40 tests de contratos, todos pasando

**Regresion:**
- 25 tests legacy NLP pasan sin cambios
- 0 errores ruff
- SlotFiller v2 es la implementacion activa desde `nlp.__init__`

---

## 1. Tareas ejecutadas

### T1.1 — Estructura de directorios

```
compiler-bot/user_request/
├── __init__.py              # Re-export de contratos publicos
├── contracts/
│   ├── __init__.py          # Init de subpaquete
│   ├── enums.py             # IntentType, RequestChannel, Language, SlotName
│   ├── request.py           # IntentResult, Entities, Slots, AmbiguityResult, RequestContext, RequestObject
│   └── response.py          # ResponseObject
├── nlu/
│   ├── __init__.py          # Init de subpaquete
│   └── slot_filler.py       # SlotFiller v2 (taxonomia unificada)
└── tests/
    ├── __init__.py
    └── test_contracts.py    # 40 tests
```

**Modificaciones a archivos existentes:**
- `compiler-bot/agentic_pipeline/nlp/__init__.py` — re-export transicional con `DeprecationWarning`
- `compiler-bot/agentic_pipeline/pyproject.toml` — anadido `user_request` a package discovery

### T1.2 — Enumeraciones (`contracts/enums.py`)

| Enum | Valores | Proposito |
|------|---------|-----------|
| `IntentType` | CREATE, READ, UPDATE, DELETE, EXPLAIN, CONFIGURE | Taxonomia canonica de 6 intenciones |
| `RequestChannel` | CLI, WEBUI, API, EDITOR, AGENT | Canales de entrada/salida |
| `Language` | ES, EN | Idiomas soportados |
| `SlotName` | 14 slots normalizados | Nombres de slots para validacion |

**Metodos de IntentType:**
- `from_alias(alias)` — resuelve alias legacy (SCAFFOLD → CREATE, QUERY → READ, etc.)
- `known_aliases()` — lista completa de alias conocidos
- `aliases_for(intent)` — alias que resuelven a una intencion dada

**Mapeo de alias (13 entradas):**

| Alias legacy | Resuelve a |
|-------------|------------|
| scaffold, generate, new | CREATE |
| query, explore, get | READ |
| modify, edit, change | UPDATE |
| remove | DELETE |
| help | EXPLAIN |
| set, config | CONFIGURE |

### T1.3 — Modelos de entrada (`contracts/request.py`)

| Modelo | Tipo | Campos clave |
|--------|------|-------------|
| `IntentResult` | dataclass(frozen) | primary, secondary, confidence, classifier, scores, domain |
| `Entity` | dataclass(frozen) | nombre, tipo, rol, negado |
| `Entities` | dataclass(frozen) | modulos[], techs[], requisitos[] |
| `Slots` | dataclass(frozen) | accion, tipo, nombre, tech, dominio, atributos, completado, faltantes |
| `AmbiguityResult` | dataclass(frozen) | detected, elementos[] |
| `RequestContext` | dataclass(frozen) | session_id, history[], defaults{}, channel |
| `RequestObject` | BaseModel | raw, normalized, intent, entities, slots, ambiguity, channel, context, metadata |

**Decision de diseno:** Los sub-componentes (`IntentResult`, `Entities`, etc.) son
`dataclass(frozen)` en lugar de `BaseModel` por dos razones:

1. **Rendimiento:** Se construyen una vez y no requieren validacion adicional
   (la validacion ocurre en el boundary `RequestObject`)
2. **Inmutabilidad:** La interfaz `dataclass(frozen)` + `BaseModel` previene
   mutacion accidental del RequestObject tras su creacion

### T1.4 — Modelo de salida (`contracts/response.py`)

| Modelo | Campos clave |
|--------|-------------|
| `ResponseObject` | success, data, message, error, suggestions[], channel, metadata |

### T1.5 — SlotFiller v2 (`nlu/slot_filler.py`)

Reescritura completa del `SlotFiller` legacy:

- **Taxonomia unificada:** `UNIFIED_TAXONOMY` con 6 entradas, cada una con
  `aliases`, `required_slots`, `optional_slots`
- **ACTION_MAP:** IntentType.value → accion string ("create", "read", ...)
- **Manejo de alias:** El SlotFiller acepta tanto `IntentType` enum como strings legacy
- **Validacion de slots faltantes:** Por intencion, basado en required_slots

```python
UNIFIED_TAXONOMY = {
    "create": {
        "aliases": ["SCAFFOLD", "GENERATE", "NEW"],
        "required_slots": ["accion", "tipo", "nombre"],
        "optional_slots": ["tech", "atributos", "dominio"],
    },
    "read": {
        "aliases": ["QUERY", "EXPLORE", "GET"],
        "required_slots": ["accion", "objetivo"],
        "optional_slots": ["filtro", "limite"],
    },
    # ... update, delete, explain, configure
}
```

### T1.6 — Backward compat

`agentic_pipeline/nlp/__init__.py` ahora:

1. Emite `DeprecationWarning` al importar
2. Re-exporta `SlotFiller` desde `user_request.nlu.slot_filler` (v2)
3. Re-exporta contratos desde `user_request.contracts`
4. Mantiene exports legacy (`IntentClassifier`, `NERExtractor`, etc.) desde sus
   ubicaciones originales (se migraran en Fase 2)

**pyproject.toml:** Anadido `user_request` y `user_request.*` a `packages.find.include`.

### T1.7 — Tests (40 tests)

| Suite | Tests | Cobertura |
|-------|-------|-----------|
| `TestIntentType` | 13 | Creacion, alias, unicidad |
| `TestRequestChannel` | 3 | Valores, default CLI |
| `TestLanguage` | 1 | ES/EN |
| `TestSlotName` | 1 | Unicidad |
| `TestIntentResult` | 3 | Minimo, completo, inmutable |
| `TestEntity` | 2 | Minimo, negado |
| `TestEntities` | 2 | Vacio, con items |
| `TestSlots` | 2 | Defaults, completo |
| `TestAmbiguityResult` | 2 | No detectado, detectado |
| `TestRequestContext` | 2 | Defaults, custom |
| `TestRequestObject` | 4 | Minimo, completo, serializacion, deserializacion |
| `TestResponseObject` | 5 | Success, error, data, roundtrip, suggestions |

---

## 2. Verificacion

### 2.1 Ruff

```
$ ruff check compiler-bot/user_request/
All checks passed!
```

### 2.2 Tests nuevos

```
$ pytest compiler-bot/user_request/tests/ -v
============================== 40 passed in 0.10s ==============================
```

### 2.3 Regresion legacy

```
$ pytest .../test_nlp_slots.py .../test_nlp_classifier.py
$ pytest .../test_nlp_ner.py .../test_nlp_ambiguity.py
============================== 25 passed in 0.09s ==============================
```

### 2.4 Backward compat verificada

```python
from agentic_pipeline.nlp import SlotFiller
assert SlotFiller.__module__ == "user_request.nlu.slot_filler"  # ← v2 activo
```

---

## 3. Artefactos producidos

### Archivos nuevos (12)

| Archivo | Lineas | Proposito |
|---------|--------|-----------|
| `compiler-bot/user_request/__init__.py` | 25 | Re-export publico |
| `compiler-bot/user_request/contracts/__init__.py` | 1 | Init paquete |
| `compiler-bot/user_request/contracts/enums.py` | 79 | 4 Enums + alias map |
| `compiler-bot/user_request/contracts/request.py` | 136 | 7 modelos de entrada |
| `compiler-bot/user_request/contracts/response.py` | 34 | ResponseObject |
| `compiler-bot/user_request/nlu/__init__.py` | 1 | Init paquete |
| `compiler-bot/user_request/nlu/slot_filler.py` | 155 | SlotFiller v2 |
| `compiler-bot/user_request/tests/__init__.py` | 1 | Init tests |
| `compiler-bot/user_request/tests/test_contracts.py` | 248 | 40 tests |

### Archivos modificados (2)

| Archivo | Cambio |
|---------|--------|
| `compiler-bot/agentic_pipeline/nlp/__init__.py` | Re-export transicional + DeprecationWarning |
| `compiler-bot/agentic_pipeline/pyproject.toml` | Anadido user_request a package discovery |

---

## 4. Decisiones tecnicas

### 4.1 Ubicacion del paquete

Se ubico `user_request/` dentro de `compiler-bot/` (no en la raiz del proyecto)
por consistencia con la estructura de imports existente. El conftest de tests ya
anade `compiler-bot/` a `sys.path`, y el entrypoint `agentic` depende de que
los paquetes esten instalados via `pip install -e`.

### 4.2 _ALIAS_MAP fuera de la clase Enum

El mapeo de alias se definio como variable de modulo (no como atributo de clase)
porque Python 3.11's `EnumMeta` trata las anotaciones de tipo dentro del cuerpo
de la clase como posibles miembros, causando colision con el dict. Ver `enums.py:50`.

### 4.3 dataclass(frozen) vs BaseModel

Los sub-componentes (`IntentResult`, `Entities`, `Slots`, etc.) usan
`dataclass(frozen)` en lugar de `BaseModel` para maximizar rendimiento
y garantizar inmutabilidad. Solo `RequestObject` y `ResponseObject` son
`BaseModel` porque actuan como boundaries del sistema (requieren validacion
y serializacion).

### 4.4 SlotFiller v2 mantiene API publica

`SlotFiller.fill(intent, entities) -> Slots` mantiene la misma firma que
la version legacy, pero internamente usa la taxonomia unificada. El SlotFiller
legacy en `agentic_pipeline/nlp/slot_filler.py` permanece intacto (sin usarse
desde `nlp.__init__`) hasta su eliminacion en Fase 6.

---

## 5. Preparacion para Fase 2

La Fase 2 (NLU Pipeline) puede comenzar. Dependencias satisfechas:

- [x] `user_request/contracts/enums.py` → F2 `classifiers/` importaran `IntentType`
- [x] `user_request/contracts/request.py` → F2 `pipeline.py` construira `RequestObject`
- [x] `user_request/nlu/slot_filler.py` → F2 `NLUPipeline` lo usara como componente
- [x] `nlp/__init__.py` re-exporta → F2 puede migrar clasificadores sin romper consumidores
