---
id: 193
area: DEV
type: REP
module: USER_REQUEST_LAYER
version: 1.0
status: DRAFT
tags:
  - user-request
  - cleanup
  - legacy
  - deprecation
  - migration
  - documentation
summary: Reporte de implementacion de la Fase 6 — Limpieza post-migracion
keywords:
  - cleanup
  - legacy
  - deprecation
  - imports
  - intent_stage
  - documentation
  - backward-compat
changelog:
  - 2026-06-22: Creacion del reporte Fase 6
---

# Reporte Fase 6 — Limpieza post-migracion

## Resumen

Se realizo la limpieza del codigo legacy tras la migracion a la capa
User Request. Se elimino el shim `intent_stage.py`, se actualizaron los
imports en el orquestador y el test de performance, y se actualizo la
documentacion en `README.md`.

## Componentes Modificados

### T6.1 — Deprecacion de `nlp/` como re-exportador

YA COMPLETADO en Fase 1. El archivo `nlp/__init__.py` ya incluye:
- `warnings.warn()` con `DeprecationWarning` en `stacklevel=2`
- Re-exports de `user_request.nlu` bajo nombres legacy (`IntentClassifier`, `NERExtractor`, etc.)
- Re-exports de `user_request.contracts` (`RequestObject`, `ResponseObject`, etc.)

### T6.2 — Eliminacion de `intent_stage.py`

El archivo `agentic_pipeline/nodes/intent_stage.py` era un shim de 3
lineas que re-exportaba `PerceptionUnit as IntentStage`:

```python
from agentic_pipeline.nodes.perception_unit import PerceptionUnit as IntentStage
```

Se elimino porque:
- Era redundante (solo re-exportaba otro modulo)
- Anyadia complejidad innecesaria al arbol de modulos
- El unico consumidor directo (`orchestrator.py`) ya se actualizo

### T6.3 — Actualizacion de imports

Se actualizaron 2 archivos que importaban desde `intent_stage.py`:

| Archivo | Cambio |
|---------|--------|
| `orchestrator.py` | `from nodes.intent_stage import IntentStage` → `from nodes.perception_unit import PerceptionUnit` en `_stage_to_enum()` y mapping |
| `test_performance.py` | Mismo cambio, mas reordenamiento de imports (ruff --fix) |

**Nota:** Los archivos restantes que importan desde `agentic_pipeline.nlp.*`
(`perception_unit.py`, `fallbacks.py`, tests legacy) usan las interfaces
DE LOS MODELOS LEGACY, que son diferentes de las nuevas interfaces en
`user_request.nlu` (p.ej. `Entities.modulos` de tipo `list[Entity]` vs
`Entities.modulos: list[str]`). No se pueden migrar sin cambiar la
logica interna. Permanecen funcionales a traves de backward compat.

### T6.4 — Actualizacion de documentacion (`README.md`)

- `intent_stage.py` → `perception_unit.py` en el diagrama de arquitectura
- Anadida seccion completa para `user_request/` en el arbol de directorios
  (contracts, nlu, nlg, api, layer.py, tests)

### T6.5 — Verificacion de regresion

| Gate | Resultado |
|------|-----------|
| `ruff check` — archivos modificados | **0 errores** |
| `python -c compile(agentic)` | **Syntax OK** |
| Suite `user_request/` (192 tests) | **192/192 PASS** |
| Suite legacy (782 tests) | **782 PASS**, 21 skipped (CUDA pre-existente) |
| Sin regresiones | ✅ |

## Cambios por archivo

| Archivo | Accion |
|---------|--------|
| `agentic_pipeline/nodes/intent_stage.py` | **Eliminado** (shim redundante) |
| `agentic_pipeline/orchestrator.py` | Modificado (import PerceptionUnit directo) |
| `agentic_pipeline/tests/test_performance.py` | Modificado (import PerceptionUnit + ruff) |
| `README.md` | Modificado (diagrama + user_request/) |

## Backward Compatibility

- `from agentic_pipeline.nlp import *` sigue funcionando (con warnings)
- `from agentic_pipeline.nlp.intent_classifier import IntentClassifier` sigue funcionando (archivo legacy intacto)
- `from agentic_pipeline.nodes.perception_unit import PerceptionUnit` funcionaba antes y sigue funcionando
- El unico cambio breaking es la eliminacion de `intent_stage.py` —
  verificado que ningun otro archivo lo importa.

## Proximos Pasos

Las 6 fases del plan de migracion estan completas. Pendiente:

- Revision global de los criterios de aceptacion
- Potencial integracion del servidor API con el dashboard existente
- Mejora del formateo de salida en el entrypoint (alinear claves de datos
  entre orchestrator y NLG formatters)
