---
id: ONB-001
area: dev
type: guide
module: onboarding
version: 1.0
status: ACTIVE
tags:
  - onboarding
  - pipeline
  - architecture
summary: "Tutorial 1: entender la arquitectura del pipeline RECPL v2.0 con 10 stages conectados via StateGraph."
---

# Tutorial 1: Entender el Pipeline

## Arquitectura

El pipeline RECPL v2.0 tiene **10 stages** conectados secuencialmente via
LangGraph StateGraph:

```
INPUT → Intent → Preprocessor → Lexer → Parser → Semantic → IR → Planner → Synthesis → UI → Validator → OUTPUT
```

Cada stage implementa la interfaz `PipelineStage` con 5 metodos:

| Metodo | Proposito |
|--------|-----------|
| `receive_mission(input_data)` | Recibe datos del stage anterior |
| `analyze()` | Analiza el estado actual |
| `reflect_and_plan(analysis)` | Decide que accion tomar |
| `act(plan)` | Ejecuta la accion, produce `StageOutput` |
| `learn_and_improve(feedback)` | Ajusta comportamiento futuro |

## Flujo de datos

Cada stage recibe un `dict` via `input_data`. El stage lo procesa y
produce otro `dict` en `StageOutput.output_data`, que pasa al siguiente
stage. El campo `enriched` (con intent, entities, slots, ambiguity) se
propaga a traves de todos los stages.

## Codigo clave

| Archivo | Proposito |
|---------|-----------|
| `orchestrator.py` | StateGraph que conecta los stages |
| `base_stage.py` | Clase base abstracta `PipelineStage` |
| `state_models.py` | `StageContext`, `StageOutput`, `ActionPlan` |
| `contracts.py` | Validacion de contratos por stage |
| `feedback_loop.py` | Metricas y ajuste de pesos |
