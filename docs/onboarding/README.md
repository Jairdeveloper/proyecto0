---
id: ONB-000
area: dev
type: guide
module: onboarding
version: 1.0
status: ACTIVE
tags:
  - onboarding
  - tutorial
  - index
summary: "Indice de tutoriales de onboarding para el pipeline RECPL v2.0."
---

# Onboarding — RECPL Pipeline v2.0

Tutoriales progresivos para entender y extender el pipeline compilador.

## Tutoriales

| # | Tutorial | Tiempo | Descripcion |
|---|----------|--------|-------------|
| 1 | [Entender el pipeline](01_pipeline.md) | 5 min | Arquitectura, stages, flujo de datos |
| 2 | [Anadir un nuevo stage](02_new_stage.md) | 10 min | Crear un PipelineStage y conectarlo |
| 3 | [Escribir tests](03_testing.md) | 10 min | Tests unitarios e integracion |
| 4 | [Depurar con --debug](04_debugging.md) | 5 min | Modos trace, step, timing, inspect |

## Prerequisitos

- Python 3.11+
- `pip install -e compiler-bot/agentic_pipeline/`
- `pytest`, `ruff` instalados
